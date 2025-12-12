import copy
import os.path
import os
import gzip
import pickle
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from cayal.util import Utilerias
from cayal.documento import Documento
from cayal.cliente import Cliente
from cayal.comandos_base_datos import ComandosBaseDatos

from herramientas.capturar_documento.ventana_captura.captura_controlador import ControladorCaptura
from herramientas.capturar_documento.ventana_captura.captura_interfaz import InterfazCaptura
from herramientas.capturar_documento.ventana_captura.captura_modelo import ModeloCaptura
from herramientas.capturar_documento.impresion_captura.ticket_158 import Ticket158


class LlamarInstanciaCaptura:
    def __init__(self, master, parametros, cliente=None, documento=None, ofertas=None):
        """
        master:   Toplevel / Frame / Window donde se monta la UI.
        parametros: objeto con al menos id_modulo, id_usuario.
        cliente, documento: instancias opcionales a reutilizar.
        ofertas: dict opcional con info de productos ofertados.
        """
        self._master = master
        self._parametros_contpaqi = parametros

        self._module_id = getattr(self._parametros_contpaqi, "id_modulo", None)
        self._user_id = getattr(self._parametros_contpaqi, "id_usuario", None)

        self._declarar_clases_auxiliares(cliente, documento)
        self._declarar_variables_instancia(ofertas)

        if self._module_id == 158:
            self._llamar_instancia_158()

        elif self._module_id == 1687:
            self._llamar_instancia_pedidos()

        else:
            self._llamar_instancia_contpaq()

    #----------------------------------------------------------------------
    # Inicialización de las variables iniciales de la forma
    #----------------------------------------------------------------------
    def _declarar_clases_auxiliares(self, cliente=None, documento=None):
        """
        Inicializa clases auxiliares. Si se proporcionan cliente/documento,
        se reutilizan; de lo contrario se crean instancias nuevas.
        """
        self._documento = documento if documento is not None else Documento()
        self._cliente = cliente if cliente is not None else Cliente()
        self._base_de_datos = ComandosBaseDatos()
        self._utilerias = Utilerias()

    def _declarar_variables_instancia(self, ofertas=None):
        """
        Inicializa variables de instancia relacionadas con parámetros y ofertas.
        """
        # --- parámetros base ---
        self._module_id = getattr(self._parametros_contpaqi, "id_modulo", None)
        self._user_id = getattr(self._parametros_contpaqi, "id_usuario", None)
        self._documento.document_id = getattr(self._parametros_contpaqi, "id_principal", 0)

        self._procesando_documento = False
        self._editando_documento = False
        self._info_documento = {}

        self._locked_doc_id = 0
        self._locked_is_pedido = False
        self._locked_active = False

        self._monto_recibido = self._utilerias.redondear_valor_cantidad_a_decimal(0)
        self._cambio_cliente = self._utilerias.redondear_valor_cantidad_a_decimal(0)

        # --- colecciones / estado interno ---
        self._customer_types_ids_ofertas = set()

        self.consulta_productos = []

        # Ofertas: si te pasan un dict, úsalo; si no, deja listas vacías
        self.consulta_productos_ofertados = []
        self.consulta_productos_ofertados_btn = []
        self.products_ids_ofertados = []

        if ofertas:
            self.consulta_productos_ofertados = ofertas.get("consulta_productos_ofertados", []) or []
            self.consulta_productos_ofertados_btn = ofertas.get("consulta_productos_ofertados_btn", []) or []
            self.products_ids_ofertados = ofertas.get("products_ids_ofertados", []) or []

        # Si luego vas a guardar estructura de ofertas más compleja:
        self._ofertas = ofertas or {}
        self._ofertas_por_lista = {}

    # ----------------------------------------------------------------------
    # Helpers relacionados con busqueda de ofertas
    # ----------------------------------------------------------------------
    def _buscar_productos_ofertados_cliente(self):
        try:
            from zoneinfo import ZoneInfo  # Py>=3.9
            tz = ZoneInfo("America/Merida")
        except Exception:
            tz = None  # fallback sin zona (no debería pasar en Py>=3.9)

        def _today_str():
            now = datetime.now(tz) if tz else datetime.now()
            return now.strftime("%Y%m%d")

        def _cache_dir() -> Path:
            base = getattr(self, "_offers_cache_dir", None)
            if base is None:
                base = Path(".offers_cache")
                setattr(self, "_offers_cache_dir", base)
            base.mkdir(parents=True, exist_ok=True)
            return base

        def _cache_path(ctid: int, day: str) -> Path:
            # nombre con fecha para validar día y facilitar limpieza
            safe = f"ofertas_{ctid}_{day}.pkl.gz"
            return _cache_dir() / safe

        def _cache_load_if_today(ctid: int):
            day = _today_str()
            p = _cache_path(ctid, day)
            if not p.exists():
                return None
            try:
                with gzip.open(p, "rb") as fh:
                    return pickle.load(fh)
            except Exception:
                try:
                    p.unlink(missing_ok=True)
                except Exception:
                    pass
                return None

        def _cache_save_today(ctid: int, data: dict):
            day = _today_str()
            p = _cache_path(ctid, day)
            tmp = p.with_suffix(".tmp")
            with gzip.open(tmp, "wb") as fh:
                pickle.dump(data, fh, protocol=pickle.HIGHEST_PROTOCOL)
            os.replace(tmp, p)

        def _cache_cleanup_not_today():
            day = _today_str()
            base = _cache_dir()
            # Borra cualquier archivo que no termine en _YYYYMMDD.pkl.gz (día actual)
            for f in base.glob("ofertas_*.pkl.gz"):
                if not f.name.endswith(f"_{day}.pkl.gz"):
                    try:
                        f.unlink(missing_ok=True)
                    except Exception:
                        pass

        customer_type_id = self._cliente.customer_type_id

        # 1) Memoria
        ofertas_mem = self._ofertas_por_lista.get(customer_type_id)
        if ofertas_mem is not None:
            self._customer_types_ids_ofertas.add(customer_type_id)
            return ofertas_mem

        # 2) Cache local (solo si es de HOY)
        ofertas_disk = _cache_load_if_today(customer_type_id)
        if ofertas_disk is not None:
            self._ofertas_por_lista[customer_type_id] = ofertas_disk
            self._customer_types_ids_ofertas.add(customer_type_id)
            _cache_cleanup_not_today()
            return ofertas_disk

        # 3) Consulta BD + proceso
        consulta_productos_ofertados = self._base_de_datos.buscar_productos_en_oferta(
            lista_precios=customer_type_id
        )
        productos_ids = list({reg['ProductID'] for reg in consulta_productos_ofertados})

        consulta_productos = self._buscar_info_productos_por_ids(productos_ids)
        consulta_procesada = self._agregar_impuestos_productos(consulta_productos)

        ofertas = {
            'consulta_productos': consulta_procesada,
            'consulta_productos_ofertados': consulta_productos_ofertados,
            'consulta_productos_ofertados_btn': consulta_procesada,  # ajusta si necesitas otro set
            'products_ids_ofertados': productos_ids
        }

        # Guarda en memoria y en disco (para HOY)
        self._ofertas_por_lista[customer_type_id] = ofertas
        self._customer_types_ids_ofertas.add(customer_type_id)
        _cache_save_today(customer_type_id, ofertas)

        # 4) Limpieza de archivos no correspondientes a HOY
        _cache_cleanup_not_today()

        return ofertas

    def _buscar_info_productos_por_ids(self, productos_ids, no_en_venta=None):

        if no_en_venta:
            return self._base_de_datos.buscar_info_productos(productos_ids,
                                                            no_en_venta=True)
        return self._base_de_datos.buscar_info_productos(productos_ids)

    def _agregar_impuestos_productos(self, consulta_productos):
        consulta_procesada = []
        for producto in consulta_productos:
            producto_procesado = self._utilerias.calcular_precio_con_impuesto_producto(producto)
            consulta_procesada.append(producto_procesado)
        return consulta_procesada

    def _buscar_ofertas(self):

        if self._cliente.customer_type_id in self._customer_types_ids_ofertas:
            return

        self._buscar_productos_ofertados_cliente()

    # ----------------------------------------------------------------------
    # setteos especiales para modulo de tickets
    # ----------------------------------------------------------------------
    def _settear_valores_cliente_pg(self):
        info_cliente = self._cargar_info_cliente_gzip()

        self._cliente.consulta = info_cliente
        self._cliente.settear_valores_consulta()

    def _settear_valores_documento_pg(self):
        info_direccion = self._cargar_info_direccion_gzip()
        self._documento.address_detail_id = info_direccion['address_detail_id']
        self._documento.address_details = info_direccion
        self._documento.prefix = 'NV'


    # ----------------------------------------------------------------------
    # Carga de cache
    # ----------------------------------------------------------------------
    def _cargar_info_direccion_gzip(self, address_detail_id=15317, carpeta_base="cache/direcciones",
                                   force_refresh=False):
        """
        Obtiene y guarda en caché (GZIP) la info de dirección por FECHA (igual que ofertas).
        - Lee primero el archivo del día: cache/direcciones/{address_detail_id}/YYYY-MM-DD.json.gz
        - Si no existe (o force_refresh=True), consulta la BD y lo guarda comprimido.
        - Devuelve el objeto (lista/dict) y la ruta del archivo de caché.
        """
        import os, json, gzip, datetime

        # ------- helpers embebidos -------
        def _hoy():
            return datetime.date.today().isoformat()

        def _asegurar_directorio(ruta):
            os.makedirs(ruta, exist_ok=True)
            return ruta

        def _ruta_cache(base, detalle_id, fecha):
            base = _asegurar_directorio(os.path.join(base, str(detalle_id)))
            return os.path.join(base, f"{fecha}.json.gz")

        def _leer_gzip_json(ruta):
            if not os.path.exists(ruta):
                return None
            try:
                with gzip.open(ruta, "rt", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None

        def _escribir_gzip_json(ruta, data):
            tmp = ruta + ".tmp"
            with gzip.open(tmp, "wt", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"), default=str)
            os.replace(tmp, ruta)

        def _normalizar(obj):
            if obj is None:
                return {}
            if isinstance(obj, dict):
                return obj
            # fallback: convertir objeto/tupla a dict por índice
            try:
                return dict(enumerate(obj))
            except Exception:
                return {"value": str(obj)}

        # ------- fin helpers -------

        fecha = _hoy()
        ruta = _ruta_cache(carpeta_base, address_detail_id, fecha)

        # 1) Intentar caché
        if not force_refresh:
            cache = _leer_gzip_json(ruta)
            if cache is not None:
                return cache  # ← antes: return cache, ruta

        # 2) Consultar BD y guardar
        info = self._base_de_datos.buscar_detalle_direccion_formateada(address_detail_id)
        data = _normalizar(info)
        _escribir_gzip_json(ruta, data)

        return data  # ← antes: return data, ruta

    def _cargar_info_cliente_gzip(self, cliente_id=9277, carpeta_base="cache/clientes", force_refresh=False):
        """
        Obtiene y guarda en caché (GZIP) la info del cliente por FECHA (igual que ofertas).
        - Lee primero el archivo del día: cache/clientes/{cliente_id}/YYYY-MM-DD.json.gz
        - Si no existe (o force_refresh=True), consulta la BD y lo guarda comprimido.
        - Devuelve el objeto (lista/dict) y la ruta del archivo de caché.
        """
        import os, datetime

        # ------- helpers embebidos -------
        def _hoy():
            # ISO 8601 YYYY-MM-DD, suficiente para cache diario
            return datetime.date.today().isoformat()

        def _asegurar_directorio(ruta):
            os.makedirs(ruta, exist_ok=True)
            return ruta

        def _ruta_cache(base, cliente, fecha):
            base = _asegurar_directorio(os.path.join(base, str(cliente)))
            return os.path.join(base, f"{fecha}.json.gz")

        def _escribir_gzip_json(ruta, data):
            tmp = ruta + ".tmp"

            def encoder(obj):
                if isinstance(obj, Decimal):
                    # convertir a float para no perder naturaleza numérica
                    return float(obj)
                raise TypeError

            import gzip, json
            with gzip.open(tmp, "wt", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"), default=encoder)
            os.replace(tmp, ruta)

        def _leer_gzip_json(ruta):
            import gzip, json, os
            if not os.path.exists(ruta):
                return None
            try:
                with gzip.open(ruta, "rt", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None

        def _normalizar_filas(rows):
            """
            Convierte el resultado de fetchall a lista de dicts si hiciera falta.
            Si ya viene como lista de dicts, lo deja igual.
            """
            if not rows:
                return []
            if isinstance(rows[0], dict):
                return rows
            # Fallback: convierte tuplas a dict con índices como claves
            return [dict(enumerate(r)) for r in rows]

        # ------- fin helpers -------

        fecha = _hoy()
        ruta = _ruta_cache(carpeta_base, cliente_id, fecha)

        # 1) Intentar caché (si no se fuerza refresco)
        if not force_refresh:
            cache = _leer_gzip_json(ruta)
            if cache is not None:
                return cache  # ← antes: return cache, ruta

        # 2) Consultar BD y guardar
        filas = self._base_de_datos.fetchall(
            "SELECT * FROM [dbo].[zvwBuscarInfoCliente-BusinessEntityID](?)",
            (cliente_id,)
        )
        data = _normalizar_filas(filas)
        _escribir_gzip_json(ruta, data)

        return data  # ← antes: return data, ruta

    # ----------------------------------------------------------------------
    # Llamada de instancia segun sea el caso
    # ----------------------------------------------------------------------
    def _llamar_instancia_158(self):

        def _crear_ticket_de_venta():
            redondear = self._utilerias.redondear_valor_cantidad_a_decimal
            ticket = Ticket158()

            plantilla = Path(__file__).parent / "ticket_modulo_158.html"
            ticket.set_plantilla(plantilla)
            # O si el HTML está en memoria:
            # ticket.set_plantilla_html(html_string)

            # ---- Fecha (compacta) ----
            fecha_expedicion = datetime.now().strftime("%Y-%m-%d %H:%M")

            # ---- Decidir si se muestra sección PAGO/CAMBIO (Decimal) ----
            amt_raw = getattr(self._documento, "amount_received", Decimal("0"))
            try:
                amount_received = amt_raw if isinstance(amt_raw, Decimal) else Decimal(str(amt_raw or "0"))
            except (InvalidOperation, TypeError, ValueError):
                amount_received = Decimal("0")

            mostrar_pago = (amount_received != Decimal("0"))

            # ---- Datos para placeholders ----
            ticket.set_datos(
                folio=self._documento.folio,
                uuid=self._parametros_contpaqi.uuid,
                FechaExpedicion=fecha_expedicion,
                SubTotal=redondear(self._documento.subtotal),
                IEPS=redondear(self._documento.ieps),
                IVA=redondear(self._documento.iva),
                Total=redondear(self._documento.total),
                cliente_pago_ticket="PAGO" if mostrar_pago else "",
                pagado_ticket=amount_received if mostrar_pago else "",
                cliente_cambio_ticket="CAMBIO" if mostrar_pago else "",
                cambio_venta=self._documento.customer_change if mostrar_pago else "",
                TotalPzas=len(self._documento.items),
                CantidadConLetra=self._utilerias.cantidad_con_letra(self._documento.total)
            )

            # ---- Partidas ----
            partidas = []
            for partida in self._documento.items:
                partidas.append({
                    "Cantidad": redondear(partida["cantidad"]),
                    "Descripcion": partida["ProductName"],
                    "PrecioUnCIVA": redondear(partida["precio"]),
                    "ImporteCIVA": redondear(partida["total"]),
                })
            ticket.set_partidas(partidas)

            # ---- Generar HTML base ----
            html = ticket.generar_html()

            # ---- Limpiar bloque PAGO/CAMBIO si no corresponde mostrarlo ----
            if not mostrar_pago:
                # 1) Si tu plantilla tiene marcadores condicionales:
                #    <!--IF_PAGADO--> ... <!--END_IF-->
                if "<!--IF_PAGADO-->" in html:
                    html = re.sub(r"<!--IF_PAGADO-->.*?<!--END_IF-->", "", html, flags=re.S)
                else:
                    # 2) Sin marcadores: elimina las filas <tr> que contienen esas dos secciones
                    #    Buscamos filas donde aparezcan los labels/valores de pago y cambio.
                    #    Es robusto a atributos y espacios.
                    patron_pago = r"<tr[^>]*>\s*<td[^>]*>[^<]*PAGO[^<]*</td>.*?</tr>"
                    patron_cambio = r"<tr[^>]*>\s*<td[^>]*>[^<]*CAMBIO[^<]*</td>.*?</tr>"
                    html = re.sub(patron_pago, "", html, flags=re.S | re.I)
                    html = re.sub(patron_cambio, "", html, flags=re.S | re.I)

            # ---- Compactar espacios/saltos innecesarios para que quede “pegado” ----
            html = re.sub(r">\s+<", "><", html)  # colapsa huecos entre etiquetas
            html = re.sub(r"[ \t]{2,}", " ", html)  # espacios repetidos
            html = html.strip()

            # ---- Guardar ----
            # Si tu Ticket158 guarda el último HTML interno, setéalo antes de guardar:
            if hasattr(ticket, "_ultimo_html"):
                ticket._ultimo_html = html
                ruta = ticket.guardar_html()
            else:
                # Si no, escribe tú el archivo en la misma carpeta de salida de ticket.guardar_html()
                ruta = ticket.guardar_html()  # crea carpeta/ruta base
                # Sobrescribe con nuestro html limpio:
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(html)

            return ruta

        try:
            self._settear_valores_cliente_pg()
            self._settear_valores_documento_pg()

            self._buscar_productos_ofertados_cliente()

            # empaquetar ofertas del cliente
            self._ofertas = self._ofertas_por_lista[self._cliente.customer_type_id]

            # llama a la instancia de captura
            interfaz = InterfazCaptura(self._master, self._parametros_contpaqi.id_modulo)

            modelo = ModeloCaptura(self._base_de_datos,
                                   self._utilerias,
                                   self._cliente,
                                   self._parametros_contpaqi,
                                   self._documento,
                                   self._ofertas
                                   )
            controlador = ControladorCaptura(interfaz, modelo)
            self._master.wait_window()

        finally:

            if self._documento.document_id != 0:
                self._base_de_datos.registrar_documento_a_recalcular(
                    self._documento.document_id,
                    self._documento.document_id,
                    self._parametros_contpaqi.uuid
                )

                # en caso de algun modulo especial donde la captura tenga que estar relacionada a un proceso de salida
                # o documento adicional
                if self._documento.destination_document_id != 0:
                    self._base_de_datos.registrar_documento_a_recalcular(
                        self._documento.destination_document_id,
                        self._documento.destination_document_id,
                        self._parametros_contpaqi.uuid
                    )

                if self._documento.adicional_document_id != 0:
                    self._base_de_datos.registrar_documento_a_recalcular(
                        self._documento.adicional_document_id,
                        self._documento.adicional_document_id,
                        self._parametros_contpaqi.uuid
                    )

                if self._module_id == 158:
                    _crear_ticket_de_venta()

    def _llamar_instancia_contpaq(self):

        def _actualizar_excedente_crediticio():
            self._base_de_datos.command(
                'UPDATE docDocument SET CreditExceededAmount = ? WHERE DocumentID = ?',
                (self._documento.credit_exceeded_amount, self._documento.document_id)
            )

        def _actualizar_forma_pago_documento():
            self._base_de_datos.command(
                'UPDATE docDocumentCFD SET FormaPago = ? WHERE DocumentID = ?',
                (
                    self._documento.forma_pago,
                    self._documento.document_id)
            )

        def _actualizar_comentario_documento():
            self._base_de_datos.command(
                'UPDATE docDocument SET Comments = ? WHERE DocumentID = ?',
                (self._documento.comments, self._documento.document_id)
            )

        try:
            self._instancia_llamada = True

            # 1) Nombre de usuario si hay documento existente
            if self._documento.document_id != 0:
                self._parametros_contpaqi.nombre_usuario = self._base_de_datos.buscar_nombre_de_usuario(self._user_id)

            # 2) Empaquetar ofertas del cliente
            #    Prioridad:
            #    - Si self._ofertas ya trae algo (e.g. pasado en __init__), lo respetamos.
            #    - Si no, intentamos construirlo desde _ofertas_por_lista según el tipo de cliente.
            if not self._ofertas:
                ct_id = getattr(self._cliente, "customer_type_id", None)
                if ct_id is not None and self._ofertas_por_lista:
                    self._ofertas = self._ofertas_por_lista.get(ct_id, {})
                else:
                    self._ofertas = {}

            # 3) Llamar a interfaz / modelo / controlador de captura
            interfaz = InterfazCaptura(self._master, self._parametros_contpaqi.id_modulo)

            modelo = ModeloCaptura(
                self._base_de_datos,
                self._utilerias,
                self._cliente,
                self._parametros_contpaqi,
                self._documento,
                self._ofertas,
            )

            controlador = ControladorCaptura(interfaz, modelo)

        finally:
            # 4) Registro de documentos a recalcular y actualizaciones varias
            if self._documento.document_id != 0 and self._module_id != 1687: # proceso no válido para pedidos
                self._base_de_datos.registrar_documento_a_recalcular(
                    self._documento.document_id,
                    self._documento.document_id,
                    self._parametros_contpaqi.uuid
                )

                if self._documento.destination_document_id != 0:
                    self._base_de_datos.registrar_documento_a_recalcular(
                        self._documento.destination_document_id,
                        self._documento.destination_document_id,
                        self._parametros_contpaqi.uuid
                    )

                if self._documento.adicional_document_id != 0:
                    self._base_de_datos.registrar_documento_a_recalcular(
                        self._documento.adicional_document_id,
                        self._documento.adicional_document_id,
                        self._parametros_contpaqi.uuid
                    )

                if self._module_id in (1400, 21, 1319):
                    _actualizar_forma_pago_documento()
                    _actualizar_excedente_crediticio()

                _actualizar_comentario_documento()

    def _llamar_instancia_pedidos(self):

        def _homologar_direccion_fiscal(business_entity_id):
            if business_entity_id <= 0:
                return
            # esta funcion es deuda tecnica de la homologacion entre la direccion fiscal
            # y orgbusinessentitymaininfo que es la tabla donde nace los parametros
            # de la direccion fiscal del cliente, esto es necesario para coherencia en
            # la información y la impresion de los formatos del cliente

            self._base_de_datos.command("""
               DECLARE @business_entity_id INT = ?
               UPDATE ADT
                SET
                    ADT.StateProvince      = EM.AddressFiscalStateProvince, 
                    ADT.City               = EM.AddressFiscalCity,
                    ADT.Municipality       = EM.AddressFiscalMunicipality,
                    ADT.Street             = EM.AddressFiscalStreet,
                    ADT.Comments           = EM.AddressFiscalComments,
                    ADT.CountryCode        = EM.AddressFiscalCountryCode,
                    ADT.CityCode           = EM.AddressFiscalCityCode, 
                    ADT.MunicipalityCode   = EM.AddressFiscalMunicipalityCode, 
                    ADT.Telefono           = EM.BusinessEntityPhone
                FROM orgBusinessEntityMainInfo EM
                INNER JOIN orgAddressDetail ADT 
                    ON EM.AddressFiscalDetailID = ADT.AddressDetailID
                WHERE
                    ADT.AddressDetailID = (
                        SELECT AddressFiscalDetailID
                        FROM orgBusinessEntityMainInfo
                        WHERE BusinessEntityID = @business_entity_id
                    )
                    AND (
                        ISNULL(ADT.StateProvince, '')       <> ISNULL(EM.AddressFiscalStateProvince, '') OR
                        ISNULL(ADT.City, '')                <> ISNULL(EM.AddressFiscalCity, '') OR
                        ISNULL(ADT.Municipality, '')        <> ISNULL(EM.AddressFiscalMunicipality, '') OR
                        ISNULL(ADT.Street, '')              <> ISNULL(EM.AddressFiscalStreet, '') OR
                        ISNULL(ADT.Comments, '')            <> ISNULL(EM.AddressFiscalComments, '') OR
                        ISNULL(ADT.CountryCode, '')         <> ISNULL(EM.AddressFiscalCountryCode, '') OR
                        ISNULL(ADT.CityCode, '')            <> ISNULL(EM.AddressFiscalCityCode, '') OR
                        ISNULL(ADT.MunicipalityCode, '')    <> ISNULL(EM.AddressFiscalMunicipalityCode, '') OR
                        ISNULL(ADT.Telefono, '')            <> ISNULL(EM.BusinessEntityPhone, '')
                    );
            """, (business_entity_id,))

        def _buscar_info_cliente_seleccionado(business_entity_id):
            _homologar_direccion_fiscal(business_entity_id)
            if business_entity_id != 0:
                return self._base_de_datos.fetchall("""
                  SELECT *
                  FROM [dbo].[zvwBuscarInfoCliente-BusinessEntityID](?)
                """, (business_entity_id,))

        def _buscar_info_direcciones_cliente_seleccionado(business_entity_id):
            return self._base_de_datos.buscar_direcciones_cliente(business_entity_id)

        def _settear_info_cliente_y_direcciones_pedido(business_entity_id):
            """
            Busca la información del cliente por BusinessEntityID,
            la carga en self.cliente y prepara documentos/ofertas.
            """

            # 1) Buscar info del cliente
            _info_cliente_seleccionado = _buscar_info_cliente_seleccionado(business_entity_id)

            # 2) Pasar la consulta al objeto Cliente y setear sus atributos
            self._cliente.consulta = _info_cliente_seleccionado
            self._cliente.settear_valores_consulta()

            # 3) Cargar la informacion de las direcciones del cliente
            self._cliente.addresses_details = []
            direcciones_cliente = _buscar_info_direcciones_cliente_seleccionado(business_entity_id)
            for direccion in direcciones_cliente:
                self._cliente.add_address_detail(direccion)

        def _asignar_parametros_a_documento_pedido():

            if not getattr(self._documento, "address_detail_id", 0):
                direcciones = getattr(self._cliente, "addresses_details", []) or []

                if direcciones:
                    direccion_defecto = None

                    for d in direcciones:
                        if d.get('AddressTypeID') == 1:
                            direccion_defecto = d
                            break

                    if direccion_defecto is None:
                        direccion_defecto = direcciones[0]

                    self._documento.address_detail_id = direccion_defecto.get('AddressDetailID', 0)
                else:
                    self._documento.address_details = {}
                    self._documento.depot_id = 0
                    self._documento.depot_name = ''
                    return

            consulta = [
                reg for reg in self._cliente.addresses_details
                if reg['AddressDetailID'] == self._documento.address_detail_id
            ]

            if not consulta:
                self._documento.address_details = {}
                self._documento.depot_id = 0
                self._documento.depot_name = ''
                return

            direccion = consulta[0]

            depot_id = direccion.get('DepotID', 0)
            depot_name = ''
            if depot_id != 0:
                depot_name_row = self._base_de_datos.fetchone(
                    'SELECT DepotName FROM orgDepot WHERE DepotID = ?',
                    (depot_id,)
                )
                depot_name = depot_name_row['DepotName'] if isinstance(depot_name_row, dict) else depot_name_row

            self._documento.address_details = direccion
            self._documento.depot_id = depot_id
            self._documento.depot_name = depot_name
            self._documento.address_detail_id = direccion.get('AddressDetailID', 0)
            self._documento.address_name = direccion.get('AddressName', '')
            self._documento.business_entity_id = self._cliente.business_entity_id
            self._documento.customer_type_id = self._cliente.customer_type_id
            self._documento.delivery_cost = self._utilerias.redondear_valor_cantidad_a_decimal(
                direccion.get('DeliveryCost', 20)
            )

        def _buscar_informacion_documento_existente():
            consulta_info_pedido = self._base_de_datos.buscar_info_documento_pedido_cayal(
                self._documento.document_id
            )
            return consulta_info_pedido[0]

        def _rellenar_instancias_importadas(info_pedido):

            info_pedido = info_pedido or {}

            self._documento.depot_id = info_pedido.get('DepotID', 0)
            self._documento.depot_name = info_pedido.get('DepotName', '')
            self._documento.created_by = info_pedido.get('CreatedBy', 0)
            self._documento.address_detail_id = info_pedido.get('AddressDetailID', 0)
            self._documento.cancelled_on = info_pedido.get('CancelledOn', None)
            self._documento.docfolio = info_pedido.get('DocFolio', '')
            self._documento.comments = info_pedido.get('CommentsOrder', '')
            self._documento.address_name = info_pedido.get('AddressName', '')
            self._documento.customer_type_id = self._cliente.cayal_customer_type_id

            doc_id = int(self._documento.document_id or 0)
            if doc_id > 0:
                pedido_flag = (self._module_id == 1687)

                already_locked_same_doc = (
                        getattr(self, "_locked_active", False)
                        and getattr(self, "_locked_doc_id", 0) == doc_id
                )

                if not already_locked_same_doc:
                    if hasattr(self, "_mark_in_use") and callable(self._marcar_en_uso):
                        self._marcar_en_uso(doc_id, pedido=pedido_flag)
                    else:
                        self._base_de_datos.marcar_documento_en_uso(
                            doc_id, self._user_id, pedido=pedido_flag
                        )

            self._editando_documento = True

        # --------------------------------------------------------------------------------------------------------------

        if self._documento.document_id != 0:
            info_pedido = _buscar_informacion_documento_existente()
            _rellenar_instancias_importadas(info_pedido)
            _settear_info_cliente_y_direcciones_pedido(self._documento.business_entity_id)
            _asignar_parametros_a_documento_pedido()

        locked_by_me = False
        bloquear = False

        def _on_close():
            try:
                self._procesar_documento_pedido()
            finally:
                if locked_by_me:
                    self._desmarcar_en_uso()
                try:
                    self._master.destroy()
                except Exception:
                    pass

        try:
            status, motivo, locked_user_id = self._base_de_datos.obtener_status_bloqueo_pedido(
                order_document_id=self._documento.document_id,
                user_id=self._user_id
            )

            bloquear = (status != 'Desbloqueado')

            if not bloquear:
                locked_by_me = self._base_de_datos.intentar_marcar_en_uso_pedido_atomico(
                    order_document_id=self._documento.document_id,
                    user_id=self._user_id
                )
                if locked_by_me:
                    # SOLO flags, NO UPDATE adicional (ideal)
                    self._locked_doc_id = int(self._documento.document_id or 0)
                    self._locked_is_pedido = True
                    self._locked_active = True
                else:
                    bloquear = True

            if not self._ofertas:
                self._buscar_ofertas()
                ct_id = getattr(self._cliente, "customer_type_id", None)
                if ct_id is not None and self._ofertas_por_lista:
                    self._ofertas = self._ofertas_por_lista.get(ct_id, {})
                else:
                    self._ofertas = {}

            interfaz = InterfazCaptura(self._master, self._parametros_contpaqi.id_modulo)
            modelo = ModeloCaptura(
                self._base_de_datos,
                self._utilerias,
                self._cliente,
                self._parametros_contpaqi,
                self._documento,
                self._ofertas,
                bloquear=bloquear
            )
            controlador = ControladorCaptura(interfaz, modelo)

            self._master.protocol("WM_DELETE_WINDOW", _on_close)

        finally:
            pass

    # ----------------------------------------------------------------------
    # Helpers relacionados con bloqueo del documento para prevenir colisiones
    # ----------------------------------------------------------------------
    def _marcar_en_uso(self, document_id, pedido: bool):
        self._locked_doc_id = int(document_id or 0)
        self._locked_is_pedido = bool(pedido)
        self._locked_active = self._locked_doc_id > 0
        if self._locked_active:
            self._base_de_datos.marcar_documento_en_uso(self._locked_doc_id, self._user_id,
                                                        pedido=self._locked_is_pedido)

    def _desmarcar_en_uso(self):
        # idempotente, por si se llama más de una vez
        if getattr(self, "_locked_active", False) and getattr(self, "_locked_doc_id", 0):
            try:
                self._base_de_datos.desmarcar_documento_en_uso(self._locked_doc_id,
                                                               pedido=self._locked_is_pedido,
                                                               user_id=self._user_id)
            finally:
                self._locked_active = False
                self._locked_doc_id = 0
                self._locked_is_pedido = False

    # ----------------------------------------------------------------------
    # Funcion principal de merge de captura pedido
    # ----------------------------------------------------------------------
    def _procesar_documento_pedido(self):

        def _solo_existe_servicio_domicilio_en_documento():

            existe = [producto for producto in self._documento.items if producto['ProductID'] == 5606]

            if existe and len(self._documento.items) == 1:
                return True

            return False

        def _determinar_tipo_de_orden_produccion():

            partidas = self._documento.items
            tipos_productos = [partida['ProductTypeIDCayal'] for partida in partidas
                               if partida['ProductID'] != 5606]

            tipos_productos = list(set(tipos_productos))

            if tipos_productos:
                if len(tipos_productos) == 1:
                    tipo_producto = tipos_productos[0]

                    # tipos de producto segun orgproduct
                    orden_type_id = {
                        0: 2,  # 0 tipo minisuper
                        1: 1,  # 1 tipo produccion
                        2: 3  # 2 tipo almacen
                    }
                    return orden_type_id[tipo_producto]

                if len(tipos_productos) == 2:
                    suma = sum(tipos_productos)

                    orden_type_id = {
                        1: 4,  # produccion y minisuper
                        3: 5,  # produccion y almacen
                        2: 6  # minisuper y almacen
                    }
                    return orden_type_id[suma]

                if len(tipos_productos) == 3:
                    return 7

            return 1

        def _crear_cabecera_pedido_cayal():

            # aplica insercion especial a tabla de sistema de pedidos cayal

            document_id = 0

            parametros_pedido = self._documento.order_parameters
            production_type_id = _determinar_tipo_de_orden_produccion()
            if parametros_pedido:
                parametros = (
                    parametros_pedido.get('RelatedOrderID', 0),
                    parametros_pedido.get('BusinessEntityID'),
                    parametros_pedido.get('CreatedBy'),
                    self._documento.comments,
                    parametros_pedido.get('ZoneID'),
                    parametros_pedido.get('AddressDetailID'),
                    parametros_pedido.get('DocumentTypeID'),
                    parametros_pedido.get('OrderTypeID'),
                    parametros_pedido.get('OrderDeliveryTypeID'),
                    parametros_pedido.get('SubTotal'),
                    parametros_pedido.get('TotalTax'),
                    parametros_pedido.get('Total'),
                    production_type_id,
                    parametros_pedido.get('HostName'),
                    parametros_pedido.get('ScheduleID', 1),
                    parametros_pedido.get('OrderDeliveryCost'),
                    parametros_pedido.get('DepotID', 0)

                )

                document_id = self._base_de_datos.crear_pedido_cayal2(parametros)
                if document_id:
                    self._base_de_datos.insertar_registro_bitacora_pedidos(
                        document_id, 1, parametros_pedido['CreatedBy'], parametros_pedido['CommentsOrder']
                    )

                # en caso que la orden sea un anexo o un pedido hay que actualizar dicho documento
                if parametros_pedido['OrderTypeID'] in (2, 3):
                    self._base_de_datos.command(
                        """
                        DECLARE @OrderID INT = ?
                        UPDATE docDocumentOrderCayal
                        SET NumberAdditionalOrders = (SELECT Count(OrderDocumentID)
                                                     FROM docDocumentOrderCayal
                                                     WHERE RelatedOrderID = @OrderID AND CancelledOn IS NULL),
                            StatusID = 2 
                        WHERE OrderDocumentID = @OrderID
                        """,
                        (parametros_pedido['RelatedOrderID'])
                    )

            return document_id

        def _insertar_partidas_documento(document_id):

            if self._parametros_contpaqi.id_modulo == 1687:

                for partida in self._documento.items:
                    # Crear una copia profunda para evitar referencias compartidas
                    partida_copia = copy.deepcopy(partida)

                    unidad = partida_copia.get('Unit', 'KILO')
                    product_id = partida_copia.get('ProductID', 0)

                    if unidad != 'KILO' and not self._utilerias.equivalencias_productos_especiales(product_id):
                        partida_copia['CayalPiece'] = 0

                    parametros = (
                        document_id,
                        partida_copia['ProductID'],
                        2,  # DepotID
                        partida_copia['cantidad'],
                        partida_copia['precio'],
                        partida_copia['CostPrice'],
                        partida_copia['subtotal'],
                        partida_copia['DocumentItemID'],
                        partida_copia['TipoCaptura'],  # CaptureTypeID 0 lector, 1 manual, 2 automático
                        partida_copia['CayalPiece'],  # Viene del control de captura manual
                        partida_copia['CayalAmount'],  # Viene del control de tipo monto
                        partida_copia['ItemProductionStatusModified'],  # Viene del status de edición de la partida
                        partida_copia['Comments'],
                        partida_copia['CreatedBy']
                    )

                    document_item_id = self._base_de_datos.insertar_partida_pedido_cayal(parametros)

                    # Actualizar el objeto original solo con el nuevo ID generado
                    partida['DocumentItemID'] = document_item_id

            if self._parametros_contpaqi.id_modulo != 1687:
                print('agrgar proceso de insercion convencional')

        def _insertar_partidas_extra_documento(document_id):

            def _buscar_document_item_id(uuid_partida):
                for partida in self._documento.items:
                    if partida.get('uuid') == uuid_partida:
                        return int(partida.get('DocumentItemID', 0))
                return 0  # o puedes lanzar una excepción controlada si prefieres

            if not self._documento.items_extra:
                return

            if self._parametros_contpaqi.id_modulo == 1687:

                for partida in self._documento.items_extra:

                    accion_id = partida['ItemProductionStatusModified']
                    change_type_id = 0
                    comentario = ''
                    uuid_partida = partida['uuid']

                    # partida agregada
                    if accion_id == 1:
                        document_item_id = _buscar_document_item_id(uuid_partida)
                        partida['DocumentItemID'] = document_item_id

                        change_type_id = 15
                        comentario = f"Agregado {partida['ProductName']} - Cant.{partida['cantidad']}"

                    # partida editada
                    if accion_id == 2:
                        change_type_id = 16
                        comentario = partida['Comments']

                    # partida eliminada
                    if accion_id == 3:
                        change_type_id = 17
                        comentario = f"Eliminado {partida['ProductName']} - Cant.{partida['cantidad']}"

                    self._base_de_datos.insertar_registro_bitacora_pedidos(order_document_id=document_id,
                                                                           change_type_id=change_type_id,
                                                                           user_id=self._user_id,
                                                                           comments=comentario)

        def _actualizar_totales_documento(document_id):
            total = self._documento.total
            subtotal = self._documento.subtotal
            total_tax = self._documento.total_tax

            if self._module_id == 1687:
                self._base_de_datos.actualizar_totales_pedido_cayal(document_id,
                                                                    subtotal,
                                                                    total_tax,
                                                                    total)

        def _actualizar_parametros_cabecera_pedido(parametros):
            self._base_de_datos.command("""
                                DECLARE @ProductionTypeID INT = ?
                                DECLARE @CommentsOrder NVARCHAR(MAX) = ?
                                DECLARE @AddressDetailID INT = ?
                                DECLARE @Total FLOAT = ?
                                DECLARE @OrderDocumentID INT = ?

                                DECLARE @StatusID INT = (SELECT StatusID
                                                         FROM docDocumentOrderCayal 
                                                         WHERE OrderDocumentID = @OrderDocumentID)

                                IF @StatusID IN (1,2,3,4,11,12,16,17,18,13)
                                BEGIN
                                    UPDATE docDocumentOrderCayal 
                                    SET CommentsOrder = @CommentsOrder,
                                        AddressDetailID = @AddressDetailID,
                                        ProductionTypeID = @ProductionTypeID
                                    WHERE OrderDocumentID = @OrderDocumentID
                                END

                            """, parametros)

        #-------------------------------------------------------------------------------------------------
        if self._procesando_documento:
            return  # ya se está procesando / se procesó

        self._procesando_documento = True

        try:
            # 1) Documento nuevo: crear cabecera si aplica
            if int(self._documento.document_id or 0) == 0:
                if self._parametros_contpaqi.id_modulo == 1687:
                    # Si solo hay servicio a domicilio o no hay partidas, no hay nada que guardar
                    if _solo_existe_servicio_domicilio_en_documento():
                        return

                    if not self._documento.items:
                        return

                    # Crear cabecera
                    self._documento.document_id = int(_crear_cabecera_pedido_cayal() or 0)

                    # Si se generó ID, opcionalmente marca en uso ahora para evitar colisiones
                    if self._documento.document_id > 0:
                        if hasattr(self, "_mark_in_use") and callable(self._marcar_en_uso):
                            self._marcar_en_uso(self._documento.document_id, pedido=True)
                        else:
                            # Fallback directo si no tienes helper
                            self._base_de_datos.marcar_documento_en_uso(self._documento.document_id,
                                                                        self._user_id, pedido=True)

            # Si después de la fase anterior seguimos sin ID, no se puede persistir nada
            if int(self._documento.document_id or 0) == 0:
                return

            # 2) Insert/merge de partidas
            _insertar_partidas_documento(self._documento.document_id)
            _insertar_partidas_extra_documento(self._documento.document_id)

            # 3) Totales
            _actualizar_totales_documento(self._documento.document_id)

            # 4) Actualizaciones finales en cabecera (ProductionType y campos editables)
            production_type_id = int(_determinar_tipo_de_orden_produccion() or 1)
            comments = self._documento.comments or ''
            address_detail_id = int(self._documento.address_detail_id or 0)
            total = float(self._documento.total or 0)
            parametros = (production_type_id,
                          comments,
                          address_detail_id,
                          total,
                          self._documento.document_id)
            _actualizar_parametros_cabecera_pedido(parametros)

        except Exception as e:
            # Log simple; evita romper el cierre de la ventana.
            try:
                print(f"[procesar_documento] Error: {e}")
            except Exception:
                pass
        finally:
            pass