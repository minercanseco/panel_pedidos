
import re
import os, json, gzip, datetime

from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from cayal.util import Utilerias
from cayal.documento import Documento
from cayal.cliente import Cliente
from cayal.comandos_base_datos import ComandosBaseDatos

from capturar_documento.controlador_captura import ControladorCaptura
from capturar_documento.interfaz_captura import InterfazCaptura
from capturar_documento.modelo_captura import ModeloCaptura
from capturar_documento.plantillas.ticket_158 import Ticket158
from capturar_documento.herramientas.servicio_ofertas_cliente import GestorOfertasCliente
from capturar_documento.selector_modulo.servicio_impresion_ticket import (
    ServicioImpresionTicket,
)
from capturar_documento.selector_modulo.servicio_generacion_cfdi_ticket import (
    ServicioGeneracionCFDITicket,
)


MODULO_TICKET = 158
MODULOS_VENTAS = (21,1400,1316,158, 1319)
MODULO_COMPRAS = 152

class LlamarInstanciaCaptura:
    def __init__(self,master, parametros):
        self._master = master
        self._parametros_contpaqi = parametros

        self._declarar_clases_auxiliares()
        self._declarar_variables_instancia()
        self._llamar_instancia_nuevo_documento() if self._document_id == 0 else self._llamar_instancia_documento_existente()

    def _declarar_clases_auxiliares(self):
        self._documento = Documento()
        self._cliente = Cliente()
        self._base_de_datos = ComandosBaseDatos()
        self._utilerias = Utilerias()

    def _declarar_variables_instancia(self):
        self._document_id = self._parametros_contpaqi.id_principal
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
        self._modelo_captura = None
        self._documento.cobrado_en_captura = False

    def _buscar_ofertas(self):

        if self._cliente.customer_type_id in self._customer_types_ids_ofertas:
            return

        self._gestor_ofertas = GestorOfertasCliente(self._base_de_datos, self._utilerias)

    def _settear_valores_cliente(self):
        info_cliente = self._cargar_info_cliente_gzip()

        self._cliente.consulta = info_cliente
        self._cliente.settear_valores_consulta()

    def _settear_valores_direccion_documento(self):

        address_detail_id = 15317 if self._module_id == MODULO_TICKET else self._documento.address_detail_id


        info_direccion = self._cargar_info_direccion_gzip(address_detail_id = address_detail_id)
        self._documento.address_detail_id = info_direccion['address_detail_id']
        self._documento.address_details = info_direccion

    def _settear_valores_documento(self):
        info_documento = self._base_de_datos.buscar_info_documento(self._document_id)
        self._documento.consulta = info_documento
        self._documento.settear_valores_consulta()

        if self._module_id == MODULO_COMPRAS:
            info_prorrateo =self._base_de_datos.cargar_prorrateo_maniobras(self._documento.document_id)

            if info_prorrateo:
                self._documento.cargar_prorrateo_maniobras(info_prorrateo)

    def _cargar_info_direccion_gzip(self,
                                    address_detail_id=15317,
                                    carpeta_base="cache/direcciones",
                                    force_refresh=False):
        """
        Obtiene y guarda en caché (GZIP) la info de dirección por FECHA (igual que ofertas).
        - Lee primero el archivo del día: cache/direcciones/{address_detail_id}/YYYY-MM-DD.json.gz
        - Si no existe (o force_refresh=True), consulta la BD y lo guarda comprimido.
        - Devuelve el objeto (lista/dict) y la ruta del archivo de caché.
        """


        # ------- helpers embebidos -------
        def _hoy():
            return datetime.now().date().isoformat()

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
        if address_detail_id == 15317:
            return {
                "address_detail_id": 15317,
                "address_name": "Dirección fiscal",
                "depot_id": 0,
                "telefono": None,
                "celular": "",
                "calle": "AV Gustavo Diaz Ordaz",
                "numero": "N207",
                "comentario": None,
                "cp": "24020",
                "colonia": "La Ermita",
                "estado": "Campeche",
                "municipio": "Campeche"
            }

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

    def _cargar_info_cliente_gzip(self,
                                  cliente_id=9277,
                                  carpeta_base="cache/clientes",
                                  force_refresh=False):
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

        if cliente_id == 9277:
            return [
            {
                "BusinessEntityID": 9277,
                "CustomerID": 5334,
                "CommercialName": None,
                "OfficialName": "PG",
                "ZoneName": "PG PUBLICO EN GENERAL",
                "FormaPago": "01",
                "MetodoPago": "PUE",
                "ReceptorUsoCFDI": "S01",
                "OfficialNumber": "XAXX010101000",
                "OfficialNumberBackup": None,
                "Cif": None,
                "Reference": "REMISIÓN",
                "Debt": 0.0,
                "ZoneID": 1048,
                "CustomerTypeID": 2,
                "CustomerTypeName": "Precio02",
                "PaymentTermID": None,
                "OldestPurchaseFolio": "",
                "OldestPurchaseDays": 0,
                "StoreCredit": 0,
                "CompanyTypeName": "616 - Sin obligaciones fiscales",
                "AuthorizedCredit": 0.0,
                "RemainingCredit": 0.0,
                "CreditComments": "",
                "CayalCustomerTypeID": 0,
                "CreditBlock": 0,
                "PaymentTermName": "NO DEFINIDO",
                "AddressFiscalDetailID": 15317,
                "AddressFiscalCity": "La Ermita",
                "AddressFiscalZipCode": "24020",
                "AddressFiscalMunicipality": "Campeche",
                "AddressFiscalStateProvince": "Campeche",
                "AddressFiscalStreet": "AV Gustavo Diaz Ordaz",
                "AddressFiscalExtNumber": "N207",
                "AddressFiscalComments": "",
                "Email": "facturascayal@hotmail.com",
                "Phone": "9818154441",
                "CellPhone": None,
                "CustomerCategory": "VENTA DE MOSTRADOR",
                "DeliveryTypeID": None,
                "Addresses": 1,
                "Depots": 0,
                "DocumentsWithBalance": 0,
                "DeliveryCost": 20.0,
                "Coupons": 0,
                "CouponsMountDebt": 0.0,
                "CouponsMount": 0.0,
                "RemainingCoupons": 0.0,
                "CouponsBlock": 0
            }
        ]

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

        return data

    def _llamar_instancia_nuevo_documento(self):
        guardar_documento = False
        try:
            self._settear_valores_cliente()
            self._settear_valores_direccion_documento()

            solicitar_guardado = False if self._module_id in MODULOS_VENTAS else True

            # llama a la instancia de captura
            interfaz = InterfazCaptura(self._master, self._parametros_contpaqi.id_modulo, solicitar_guardado=solicitar_guardado)

            modelo = ModeloCaptura(self._base_de_datos,
                                   self._utilerias,
                                   self._cliente,
                                   self._documento,
                                   self._parametros_contpaqi,
                                   #self._ofertas
                                   )
            self._modelo_captura = modelo

            controlador = ControladorCaptura(interfaz, modelo)

            self._master.wait_window()

            guardar_documento = (
                not solicitar_guardado
                or interfaz.guardar_documento is True
            )

        finally:
            if guardar_documento:
                self._tareas_finales_de_afectacion_de_documentos()

    def _llamar_instancia_documento_existente(self):
        guardar_documento = False
        try:
            self._settear_valores_cliente()
            self._settear_valores_documento()
            self._settear_valores_direccion_documento()

            interfaz = InterfazCaptura(
                self._master,
                self._parametros_contpaqi.id_modulo,
                solicitar_guardado=True,
            )

            modelo = ModeloCaptura(
                self._base_de_datos,
                self._utilerias,
                self._cliente,
                self._documento,
                self._parametros_contpaqi,
            )
            self._modelo_captura = modelo

            controlador = ControladorCaptura(interfaz, modelo)
            self._master.wait_window()

            if interfaz.guardar_documento is not True:
                return

            guardar_documento = True

            # Los demás módulos conservan su flujo actual de persistencia.
            if self._module_id != MODULO_COMPRAS:
                return

            for partida in self._documento.items:
                document_item_id = int(
                    partida.get('DocumentItemID', 0) or 0
                )
                estado_modificacion = int(
                    partida.get(
                        'ItemProductionStatusModified',
                        0,
                    ) or 0
                )

                es_partida_nueva = document_item_id == 0
                es_partida_editada = (
                        document_item_id != 0
                        and estado_modificacion == 2
                )

                if estado_modificacion == 3:
                    # Una partida nueva eliminada (como Maniobras después de
                    # prorratearse) nunca debe llegar a la base de datos. Las
                    # existentes sí requieren ejecutar su borrado lógico.
                    if document_item_id != 0:
                        self._base_de_datos.exec_stored_procedure(
                            'zvwBorrarPartidasDocumentoCayal',
                            (
                                self._documento.document_id,
                                self._module_id,
                                document_item_id,
                                self._user_id,
                            ),
                        )
                    continue

                # Las partidas existentes sin modificaciones no se procesan.
                if not es_partida_nueva and not es_partida_editada:
                    continue

                cantidad = partida.get(
                    'cantidad',
                    partida.get('Quantity', 0),
                )
                precio = partida.get(
                    'UnitPrice',
                    partida.get('precio', 0),
                )
                costo = partida.get('CostPrice', 0)
                subtotal = partida.get(
                    'subtotal',
                    partida.get('SubtotalBruto', 0),
                )

                parametros = (
                    self._documento.document_id,
                    partida.get('ProductID', 0),
                    partida.get('DepotID', 2) or 2,
                    cantidad,
                    precio,
                    costo,
                    subtotal,
                    partida.get('TipoCaptura', 0),
                    self._module_id,
                    partida.get('Comments', ''),
                    partida.get('DiscountPerc', 0),
                    partida.get('ApplyGlobalDiscount', 0),
                    partida.get('ProductSupplierKey'),
                    partida.get('SupplierBusinessEntityID', 0),
                    partida.get('ExpenseTypeID', 0),
                    partida.get('DateItem'),
                    document_item_id,
                )

                self._base_de_datos.insertar_partida_documento_cayal(
                    parametros
                )

                # La operación terminó correctamente; la partida ya no está
                # pendiente de actualización durante esta ejecución.
                partida['ItemProductionStatusModified'] = 0

        finally:
            if guardar_documento:
                self._tareas_finales_de_afectacion_de_documentos()

    def _tareas_finales_de_afectacion_de_documentos(self):
        if self._documento.document_id != 0:
            if self._module_id == MODULO_COMPRAS:
                registros = self._documento.prorrateo_maniobras
                if registros:

                    self._base_de_datos.guardar_prorrateo_maniobras(self._documento.document_id, self._user_id, registros)

            # Las partidas ya están persistidas. A partir de ellas se
            # reconstruyen detalle, resumen fiscal y resumen por impuesto
            # antes de actualizar el encabezado o generar salidas fiscales.
            if self._modelo_captura is not None:
                self._modelo_captura.afectar_impuestos_documento(
                    self._documento.document_id
                )

            # Antes del cobro los totales ya fueron preparados. No deben
            # reinicializarse después, porque se perderían TotalPaid,
            # Balance y StatusPaidID calculados por Cobros.
            if (
                    self._modelo_captura is not None
                    and not getattr(
                        self._documento,
                        'cobrado_en_captura',
                        False,
                    )
            ):
                self._modelo_captura.actualizar_totales_documento(
                    self._documento.document_id
                )

            if self._module_id == MODULO_TICKET:
                ruta_html = self._crear_ticket_de_venta()
                partidas_vigentes = [
                    partida for partida in self._documento.items
                    if int(partida.get(
                        'ItemProductionStatusModified', 0
                    ) or 0) != 3
                ]
                ServicioImpresionTicket(
                    self._base_de_datos
                ).imprimir_en_segundo_plano(
                    ruta_html=ruta_html,
                    cantidad_partidas=len(partidas_vigentes),
                    document_id=self._documento.document_id,
                    user_id=self._user_id,
                )
            elif self._module_id == 1400:
                ServicioGeneracionCFDITicket(
                    base_de_datos=self._base_de_datos,
                    user_id=self._user_id,
                    user_name=getattr(
                        self._parametros_contpaqi,
                        'nombre_usuario',
                        '',
                    ),
                    identificador_ejecucion=getattr(
                        self._parametros_contpaqi,
                        'uuid',
                        '',
                    ),
                ).generar_e_imprimir_en_segundo_plano(
                    self._documento.document_id
                )


    def _crear_ticket_de_venta(self):
        redondear = self._utilerias.redondear_valor_cantidad_a_decimal
        ticket = Ticket158()

        plantilla = Path(__file__).parent / "plantillas" / "ticket_modulo_158.html"
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
