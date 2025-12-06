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

from herramientas.capturar_documento.controlador_captura import ControladorCaptura
from herramientas.capturar_documento.interfaz_captura import InterfazCaptura
from herramientas.capturar_documento.modelo_captura import ModeloCaptura


class LlamarInstanciaCaptura:
    def __init__(self,master, parametros):
        self._master = master
        self._parametros_contpaqi = parametros

        self._declarar_clases_auxiliares()
        self._declarar_variables_instancia()

        if self._module_id == 158:
            self._llamar_instancia_158()

    def _declarar_clases_auxiliares(self):
        self._documento = Documento()
        self._cliente = Cliente()
        self._base_de_datos = ComandosBaseDatos()
        self._utilerias = Utilerias()

    def _declarar_variables_instancia(self):

        self._module_id = self._parametros_contpaqi.id_modulo
        self._user_id = self._parametros_contpaqi.id_usuario
        self._monto_recibido = self._utilerias.redondear_valor_cantidad_a_decimal(0)
        self._cambio_cliente = self._utilerias.redondear_valor_cantidad_a_decimal(0)

        self._customer_types_ids_ofertas = set()
        self.consulta_productos = []
        self.consulta_productos_ofertados = []
        self.consulta_productos_ofertados_btn = []
        self.products_ids_ofertados = []
        self._ofertas = {}
        self._ofertas_por_lista = {}

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

    def _settear_valores_cliente_pg(self):
        info_cliente = self._cargar_info_cliente_gzip()

        self._cliente.consulta = info_cliente
        self._cliente.settear_valores_consulta()

    def _settear_valores_documento_pg(self):
        info_direccion = self._cargar_info_direccion_gzip()
        self._documento.address_detail_id = info_direccion['address_detail_id']
        self._documento.address_details = info_direccion
        self._documento.prefix = 'NV'

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

    def _llamar_instancia_158(self):
        try:
            self._settear_valores_cliente_pg()
            self._settear_valores_documento_pg()

            self._buscar_productos_ofertados_cliente()

            # empaquetar ofertas del cliente
            self._ofertas = self._ofertas_por_lista[self._cliente.customer_type_id]

            # llama a la instancia de captura
            interfaz = InterfazCaptura(self._master, self._parametros_contpaqi.id_modulo)

            modelo = ModeloCaptura(self._base_de_datos,
                                   interfaz.ventanas,
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
                    self._crear_ticket_de_venta()

    def _crear_ticket_de_venta(self):
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
            uuid = self._parametros_contpaqi.uuid,
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