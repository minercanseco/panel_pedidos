import os
import platform
import tempfile
from datetime import datetime

from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.util import Utilerias


class ModeloPanelPedidos:
    def __init__(self, interfaz, parametros):
        self.parametros = parametros
        self.interfaz = interfaz
        self.base_de_datos = ComandosBaseDatos(self.parametros.cadena_conexion)
        self.utilerias = Utilerias()
        self.consulta_pedidos = []

        self.consulta_productos = []
        self.consulta_productos_ofertados = []
        self.consulta_productos_ofertados_btn = []
        self.products_ids_ofertados = []

        self.user_id = self.parametros.id_usuario
        self.user_name = self.base_de_datos.buscar_nombre_de_usuario(self.user_id)
        self.user_group_id = self.base_de_datos.fetchone(
            'SELECT UserGroupID FROM engUser WHERE UserID = ?', (self.user_id,))

        valores_puntualidad = self.obtener_valores_de_puntualidad()

        self.valor_a_tiempo = valores_puntualidad['ATiempo']
        self.valor_en_tiempo = valores_puntualidad['EnTiempo']

        self.hoy = datetime.now().date()
        self.hora_actual = self.utilerias.hora_actual()
        self.usuario_operador_panel = ''

        self.pedidos_en_tiempo = 0
        self.pedidos_a_tiempo = 0
        self.pedidos_retrasados = 0

    def buscar_pedidos(self, fecha_entrega):
        return self.base_de_datos.buscar_pedidos_panel_captura_cayal(fecha_entrega)

    def buscar_pedidos_sin_procesar(self):
        return self.base_de_datos.pedidos_sin_procesar('pedidos')

    def buscar_pedidos_cliente_sin_fecha(self, criteria):
        return self.base_de_datos.buscar_pedidos_cliente_sin_fecha_panel_pedidos(criteria)

    def obtener_valores_de_puntualidad(self):
        consulta = self.base_de_datos.obtener_valores_de_puntualidad_pedidos_cayal('timbrado')
        if not consulta:
            return

        return consulta[0]

    def buscar_partidas_pedido(self, order_document_id):
        consulta = self.base_de_datos.buscar_partidas_pedidos_produccion_cayal(order_document_id= order_document_id,
                                                                                partidas_producidas=True,
                                                                                partidas_eliminadas=True)
        if not consulta:
            return
        return consulta

    def buscar_productos_ofertados_cliente(self):

        consulta_productos_ofertados = self.base_de_datos.buscar_productos_en_oferta()
        productos_ids = [reg['ProductID'] for reg in consulta_productos_ofertados]

        productos_ids = list(set(productos_ids))

        consulta_productos = self.buscar_info_productos_por_ids(productos_ids)
        consulta_procesada = self.agregar_impuestos_productos(consulta_productos)
        self.consulta_productos_ofertados = consulta_productos_ofertados
        self.consulta_productos = consulta_procesada
        self.consulta_productos_ofertados_btn = consulta_procesada
        self.products_ids_ofertados = productos_ids

        return consulta_procesada

    def buscar_productos(self, termino_buscado, tipo_busqueda):

        if termino_buscado != '' and termino_buscado:

            if tipo_busqueda == 'Término':
                return self.base_de_datos.buscar_product_id_termino(termino_buscado)

            if tipo_busqueda == 'Línea':
                return self.base_de_datos.buscar_product_id_linea(termino_buscado)

            return False

    def obtener_product_ids_consulta(self, consulta_productos):
        product_ids = [producto['ProductID'] for producto in consulta_productos]

        if len(product_ids) == 1:
            return product_ids[0]

        return product_ids

    def buscar_info_productos_por_ids(self, productos_ids, no_en_venta=None):

        if no_en_venta:
            return self.base_de_datos.buscar_info_productos(productos_ids,
                                                            no_en_venta=True)
        return self.base_de_datos.buscar_info_productos(productos_ids)

    def agregar_impuestos_productos(self, consulta_productos):
        consulta_procesada = []
        for producto in consulta_productos:
            producto_procesado = self.utilerias.calcular_precio_con_impuesto_producto(producto)
            consulta_procesada.append(producto_procesado)
        return consulta_procesada

    def buscar_informacion_producto(self, product_id):
        info_producto = [producto for producto in self.consulta_productos
                         if product_id == producto['ProductID']]

        return info_producto[0] if info_producto else {}

    def confirmar_transferencia(self, user_id, order_document_id):
        self.base_de_datos.command(
            """
            UPDATE docDocumentOrderCayal 
            SET 
                PaymentConfirmedID = 3,
                PaymentConfirmedAt = GETDATE(),
                PaymentConfirmedBy = ?
            WHERE OrderDocumentID = ?
            """,
            (user_id, order_document_id)
        )

    def afectar_bitacora(self, order_document_id, user_id, comentario, change_type_id):

        self.base_de_datos.insertar_registro_bitacora_pedidos(order_document_id=order_document_id,
                                                               change_type_id=change_type_id,
                                                               user_id=user_id,
                                                               comments=comentario)

    def obtener_comentario_pedido(self, order_document_id):
        return self.base_de_datos.fetchone(
            'SELECT CommentsOrder FROM docDocumentOrderCayal WHERE OrderDocumentID = ?',
            (order_document_id,))

    def actualizar_comentario_document_id(self, comentario_a_insertar, document_id):
        self.base_de_datos.command(
            'UPDATE docDocument SET Comments = ?, UserID = NULL WHERE DocumentID =?',
            (comentario_a_insertar, document_id)
        )

    def obtener_info_taras_pedido(self, order_document_id):
        return self.base_de_datos.fetchall("""
                        SELECT ISNULL(P.FolioPrefix,'') + ISNULL(P.Folio,'') AS PedFolio, 
                               TP.Prefix AS TaraPrefix, 
                               T.NumberTara
                        FROM docDocumentOrderCayal P
                        INNER JOIN docDocumentTarasOrdersCayal T ON P.OrderDocumentID = T.OrderDocumentID
                        INNER JOIN OrderTarasCayal TP ON T.TaraTypeID = TP.TaraTypeID
                        WHERE P.OrderDocumentID = ?
                    """, (order_document_id,))

    def obtener_status_entrega_pedido(self, order_document_id):
        consulta = self.base_de_datos.fetchall("""
                        SELECT
                            CASE
                            WHEN DeliveryPromise IS NULL THEN 0 ELSE 1 END StatusEntrega,
                            DeliveryPromise FechaEntrega,
                            ISNULL(FolioPrefix,'')+ISNULL(Folio,'') DocFolio,
                            StatusID
                        FROM docDocumentOrderCayal 
                        WHERE OrderDocumentID = ?
                        """, (order_document_id,))
        if not consulta:
            return {}

        return {
            'status_entrega': consulta[0]['StatusEntrega'],
            'fecha_entrega': consulta[0]['FechaEntrega'],
            'doc_folio': consulta[0]['DocFolio'],
            'status_id': consulta[0]['StatusID'],
        }

    def obtener_areas_imprimibles(self, order_document_id):
        return set(self.base_de_datos.fetchone("""
                                    SELECT PT.Value
                                    FROM docDocumentOrderCayal P INNER JOIN
                                        OrdersProductionTypesCayal PT ON P.ProductionTypeID = PT.ProductionTypesID
                                    WHERE P.OrderDocumentID = ?
                                """, (order_document_id,)))

    def obtener_directorio_reportes(self):

        sistema = platform.system()

        if sistema == "Windows":
            directorio = os.path.join(os.getenv("USERPROFILE"), "Documents")

        elif sistema in ["Darwin", "Linux"]:  # macOS y Linux
            directorio = os.path.join(os.getenv("HOME"), "Documents")

        else:
            directorio = tempfile.gettempdir()  # como último recurso

        if not os.path.exists(directorio):
            os.makedirs(directorio)

        return directorio

    def obtener_partidas_pedido(self, order_document_id):
        return self.base_de_datos.buscar_partidas_pedidos_produccion_cayal(
            order_document_id, partidas_eliminadas=False, partidas_producidas=True)

    def obtener_ruta_y_colonia_pedido(self, order_document_id):
        consulta = self.base_de_datos.fetchall(
            """
            SELECT Z.ZoneName, DT.City
            FROM docDocumentOrderCayal D INNER JOIN
                orgZone Z ON D.ZoneID = D.ZoneID INNER JOIN
                orgAddressDetail DT ON D.AddressDetailID = DT.AddressDetailID
            WHERE OrderDocumentID = ? AND D.ZoneID = Z.ZoneID
            """,
            (order_document_id,)
        )
        if consulta:
            valores = consulta[0]
            ruta = valores.get('ZoneName', '')
            ruta = self.utilerias.limitar_caracteres(ruta, 22)

            colonia = valores.get('City', '')

            return ruta, colonia

        return '', ''

    def afectar_bitacora_impresion(self, ticket, order_document_id):

        change_type_id = 12
        user_name = self.base_de_datos.buscar_nombre_de_usuario(self.user_id)
        comentario = f"{user_name}-{ticket.pedido}-{ticket.areas}"

        self.base_de_datos.insertar_registro_bitacora_pedidos(order_document_id,
                                                              change_type_id=change_type_id,
                                                              comments=comentario,
                                                              user_id=self.user_id)

    def actualizar_tablas_impresion(self, ticket, order_document_id):

        areas = ticket.areas

        if 'Minisuper' in areas:
            self.base_de_datos.command(
                'UPDATE docDocumentOrderCayal SET StorePrintedOn=GETDATE(), StorePrintedBy=? WHERE OrderDocumentID = ?',
                (self.user_id, order_document_id)
            )

        if 'Almacen' in areas:
            self.base_de_datos.command(
                'UPDATE docDocumentOrderCayal SET WarehousePrintedOn=GETDATE(), WarehousePrintedBy=? WHERE OrderDocumentID = ?',
                (self.user_id, order_document_id)
            )

        if 'Produccion' in areas:
            self.base_de_datos.command(
                'UPDATE docDocumentOrderCayal SET ProductionPrintedOn=GETDATE(), ProductionPrintedBy=? WHERE OrderDocumentID = ?',
                (self.user_id, order_document_id)
            )

    def mandar_pedido_a_producir(self, order_document_id):
        self.base_de_datos.command("""
                             UPDATE docDocumentOrderCayal SET SentToPrepare = GETDATE(),
                                                            SentToPrepareBy = ?,
                                                            StatusID = 2,
                                                            UserID = NULL
                            WHERE OrderDocumentID = ?
                        """, (self.user_id, order_document_id,))

        comentario = f'Enviado a producir por {self.user_name}.'
        self.base_de_datos.insertar_registro_bitacora_pedidos(order_document_id=order_document_id,
                                                              change_type_id=2,
                                                              user_id=self.user_id,
                                                              comments=comentario)

    def insertar_pedido_a_recalcular(self, document_id, order_document_id):
        self.base_de_datos.exec_stored_procedure('zvwRecalcularPedidos', (document_id, order_document_id))

    def afectar_bitacora_de_cambios_en_pedidos(self, document_id, order_document_ids):

        folio = self.base_de_datos.fetchone(
            "SELECT ISNULL(FolioPrefix,'')+ISNULL(Folio,'') DocFolio FROM docDocument WHERE DocumentID = ?",
            (document_id,))
        comentario = f"Documento creado por {self.user_name} - {folio}"

        for order_document_id in order_document_ids:
            self.base_de_datos.insertar_registro_bitacora_pedidos(order_document_id,
                                                                  change_type_id=4,
                                                                  comments=comentario,
                                                                  user_id=self.user_id)

            self.base_de_datos.command(
                """
                UPDATE docDocumentOrderCayal 
                SET 
                    SentToInvoice = CASE 
                        WHEN SentToInvoice IS NULL THEN GETDATE() 
                        ELSE SentToInvoice 
                    END,
                    SentToInvoiceBy = CASE 
                        WHEN SentToInvoiceBy > 0 THEN SentToInvoiceBy 
                        ELSE ? 
                    END
                WHERE OrderDocumentID = ?;
                """,
                (self.user_id, order_document_id)
            )

    def crear_cabecera_factura_mayoreo(self, document_type_id, way_to_pay_id, fila):
        document_id = self.base_de_datos.crear_documento(
            document_type_id,
            'FM',  # prefijo mayoreo
            fila['BusinessEntityID'],
            21,  # modulo facturas mayoreo
            fila['CaptureBy'],  # valor de quien captura el pedido
            fila['DepotID'],
            fila['AddressDetailID'],
            self.user_id,  # valor de quien crea el documento (envía a timbrar)
            way_to_pay_id
        )

        order_document_id = fila['OrderDocumentID']

        # este valor hace que para los doctos de mayoreo no sean recalculables
        self.base_de_datos.command('UPDATE docDocument SET ExportID = 6, OrderDocumentID = ? WHERE DocumentID = ?',
                                   (order_document_id, document_id))

        return document_id

    def insertar_partidas_documento(self, order_document_id, document_id, partidas, total_documento, address_detail_id):
        if total_documento < 200:
            order_delivery_type_id = self.base_de_datos.fetchone(
                'SELECT OrderDeliveryTypeID FROM docDocumentOrderCayal WHERE OrderDocumentID = ?',
                                         (order_document_id,))

            # si el cliente viene omite el servicio a domicilio
            if order_delivery_type_id == 1:
                self.insertar_servicio_a_docimicilio(document_id, address_detail_id)

        for partida in partidas:
            parametros = (
                document_id,
                partida['ProductID'],
                2,  # depot_id
                partida['Quantity'],
                partida['UnitPrice'],
                0,  # costo,
                partida['Subtotal'],
                partida['TipoCaptura'],  # tipo captura
                21,  # modulo
                partida['Comments']
            )
            self.base_de_datos.insertar_partida_documento_cayal(parametros)

    def insertar_servicio_a_docimicilio(self, document_id, address_detail_id):
        precio_servicio = self.base_de_datos.fetchone(
            'SELECT * FROM [dbo].[zvwBuscarCargoEnvio-AddressDetailID](?)',
            (address_detail_id,))

        precio_servicio_sin_impuesto = self.utilerias.calcular_monto_sin_iva(precio_servicio)
        parametros = (
            document_id,
            5606,  # product_id
            2,  # depot_id
            1,
            precio_servicio_sin_impuesto,
            0,  # costo,
            precio_servicio_sin_impuesto,
            0,  # tipo captura
            21  # modulo
        )
        self.base_de_datos.insertar_partida_documento_cayal(parametros)

    def crear_comentario_taras(self, order_document_ids):
        comentario = ''

        for order in order_document_ids:
            consulta = self.obtener_info_taras_pedido(order)

            if not consulta:
                continue

            # Obtener el folio del pedido
            folio = consulta[0]['PedFolio']
            taras = []

            # Generar la lista de taras
            for tara in consulta:
                tara_type = tara['TaraPrefix']
                number_tara = tara['NumberTara']
                taras.append(f"{tara_type}{number_tara}")

            # Crear la cadena para este pedido
            taras_str = ",".join(taras)  # Concatenar las taras separadas por comas
            comentario += f"{folio}->{taras_str}; "

        # Eliminar el último espacio y punto y coma si existe
        comentario = comentario.strip("; ")
        return comentario

    def crear_comentario_entrega(self, order_document_ids):
        comentario = ''  # Inicia el comentario vacío
        delivery_forms = []
        info_delivery = {}
        for pedido in order_document_ids:
            consulta = self.base_de_datos.buscar_info_documento_pedido_cayal(pedido)
            if consulta:
                info_pedido = consulta[0]
                # Extraer la información necesaria
                order_delivery_type_id = info_pedido['OrderDeliveryTypeID']
                if order_delivery_type_id == 1:
                    continue

                doc_folio = info_pedido['DocFolio']
                delivery_form = 'VIENE' if order_delivery_type_id == 2 else ''

                delivery_forms.append(delivery_form)
                info_delivery[doc_folio] = delivery_form

        if len(delivery_forms) == 1:
            return list(delivery_forms)[0]

        else:
            comentarios = []
            for folio, delivery_form in info_delivery.items():
                comentarios.append(f"{folio} {delivery_form}")

            comentario = ", ".join(comentarios)
            return comentario

    def crear_comentario_horarios(self, order_document_ids):
        comentario = ''  # Inicia el comentario vacío

        for pedido in order_document_ids:
            consulta = self.base_de_datos.buscar_info_documento_pedido_cayal(pedido)
            if consulta:
                info_pedido = consulta[0]

                # Extraer la información necesaria
                folio = info_pedido['DocFolio']
                he = info_pedido['DeliveryTime']
                hv = info_pedido['CreatedOnTime']

                # Agregar al comentario en el formato deseado
                comentario += f"HE:{he}\n"

        # Opcionalmente, eliminar el salto de línea final
        return comentario.strip()

    def crear_comentario_forma_pago(self, order_document_ids):
        comentario = ''  # Inicia el comentario vacío

        payment_forms = []
        info_payment = {}
        for pedido in order_document_ids:
            consulta = self.base_de_datos.buscar_info_documento_pedido_cayal(pedido)
            if consulta:
                info_pedido = consulta[0]
                # Extraer la información necesaria
                doc_folio = info_pedido['DocFolio']
                payment_form = info_pedido['WayToPayID']
                total = info_pedido['Total']

                payment_forms.append(payment_form)
                info_payment[doc_folio] = (payment_form, total)

        payment_forms = set(payment_forms)

        if len(payment_forms) == 1:

            way_to_pay_id = list(payment_forms)[0]
            if way_to_pay_id == 5:
                return ''

            return self.base_de_datos.fetchone(
                'SELECT Comments FROM OrdersPaymentTermCayal WHERE PaymentTermID = ?',
                (list(payment_forms)[0])
            )
        else:
            comentarios = []
            for folio, (payment_form, total) in info_payment.items():
                if payment_form == 5:
                    continue

                comentario_pago = self.base_de_datos.fetchone(
                    'SELECT Comments FROM OrdersPaymentTermCayal WHERE PaymentTermID = ?',
                    (payment_form,)
                )
                if comentario_pago:
                    comentarios.append(f"{folio} {comentario_pago}")

            comentario = ", ".join(comentarios)
            return comentario

    def validar_credito_documento_cliente(self, business_entity_id, comentarios_documento, total_documento):

        info_cliente = self.base_de_datos.fetchall('SELECT * FROM [dbo].[zvwBuscarInfoCliente-BusinessEntityID](?)',
                                                   (business_entity_id,))
        credito_autorizado = self.utilerias.redondear_valor_cantidad_a_decimal(info_cliente[0]['AuthorizedCredit'])
        ruta = int(info_cliente[0]['ZoneID'])
        comentario_crediticio = ''
        if credito_autorizado > 0 and ruta == 1040:
            bloqueo_crediticio = int(info_cliente[0]['CreditBlock'])

            if bloqueo_crediticio == 1:
                comentario_crediticio = '--NO TIENE CRÉDITO SU COMPRA ES DE CONTADO.-- '
            else:
                credito_restante = self.utilerias.redondear_valor_cantidad_a_decimal(info_cliente[0]['RemainingCredit'])
                debe = credito_autorizado - credito_restante

                if credito_restante > 0:
                    comentario_crediticio = f'--DEBE: {debe}. CRÉDITO DISPONIBLE: {credito_restante}-- '
                else:
                    credito_restante_real = credito_restante + total_documento

                    if credito_restante_real <= 0:
                        comentario_crediticio = '--NO TIENE CRÉDITO SU COMPRA ES DE CONTADO.-- '

                    elif credito_restante_real > 0 and credito_restante_real < total_documento:
                        obligatorio = total_documento - credito_restante_real
                        comentario_crediticio = f'--DEBE PAGAR OBLIGATORIAMENTE: {obligatorio}-- '

                    elif credito_restante_real == total_documento:
                        comentario_crediticio = f'--DEBE: {debe}. CRÉDITO DISPONIBLE: 0-- '

            return f'{comentario_crediticio} {comentarios_documento}'

        return comentarios_documento

    def relacionar_pedidos_con_facturas(self, document_id, order_document_id):
        self.base_de_datos.command(
            """
            DECLARE @DocumentID INT = ?
            DECLARE @OrderDocumentID INT  = ?

            -- Actualizar la tabla docDocumentOrderCayal
            UPDATE docDocumentOrderCayal
                    StatusID = CASE WHEN StatusID = 3 AND OutputToDeliveryBy = 0 AND AssignedBy = 0 THEN 4
                                    ELSE StatusID 
                                    END,
                    DocumentID = @DocumentID
            WHERE OrderDocumentID = @OrderDocumentID;

            -- Insertar en la tabla OrderInvoiceDocumentCayal
            INSERT INTO OrderInvoiceDocumentCayal (OrderDocumentID, DocumentID)
            VALUES (@OrderDocumentID, @DocumentID);

            """,
            (document_id, order_document_id)
        )

    def relacionar_pedido_con_pedidos(self, order_document_id, order):
        self.base_de_datos.command(
            """
            UPDATE docDocumentOrderCayal SET RelatedOrderID = ?,
                    StatusID = CASE WHEN StatusID = 3 AND OutputToDeliveryBy = 0 AND AssignedBy = 0 THEN 4
                                    ELSE StatusID 
                                    END
            WHERE OrderDocumentID = ?
            """,
            (order_document_id, order)
        )

    def actualizar_totales_pedido(self, order_document_id, sin_servicio_domicilio=True):
        consulta_partidas = self.base_de_datos.buscar_partidas_pedidos_produccion_cayal(
            order_document_id, partidas_producidas=True)

        consulta_partidas_con_impuestos = self.utilerias.agregar_impuestos_productos(consulta_partidas)
        subtotal = 0
        total_tax = 0
        totales = 0

        for producto in consulta_partidas_con_impuestos:
            precio = producto['precio']
            cantidad_decimal = producto['cantidad']
            total = producto['total']
            product_id = producto['ProductID']

            if int(product_id) == 5606 and sin_servicio_domicilio:
                continue

            subtotal += (precio * cantidad_decimal)
            total_tax += (precio - precio)
            totales += total

        self.base_de_datos.command(
            'UPDATE docDocumentOrderCayal SET SubTotal = ?, Total = ?, TotalTax = ? WHERE OrderDocumentID = ?',
            (subtotal, totales, total_tax, order_document_id)
        )

    def obtener_numero_pedidos_fecha(self, fecha):
        return int(self.base_de_datos.fetchone(
            """
            SELECT COUNT(1)
            FROM docDocumentOrderCayal P
            INNER JOIN docDocument D ON P.OrderDocumentID = D.DocumentID
            WHERE P.StatusID IN (1,2,3)
              AND D.PrintedOn IS NOT NULL
              AND CAST(P.DeliveryPromise AS date) = CAST(? AS date)
            """,
            (fecha,)))

    def obtener_numero_pedidos_transferencia_fecha(self, fecha):
        return int(self.base_de_datos.fetchone(
            """
            SELECT COUNT(1)
            FROM docDocumentOrderCayal
            WHERE PaymentConfirmedID = 2
              AND CAST(DeliveryPromise AS date) = CAST(? AS date)
            """,
            (fecha,)))

    def obtener_pedidos_por_puntualidad_fecha(self, fecha):
        # 3) Buckets de puntualidad (<=15, 16-30, >30)
        return  self.base_de_datos.fetchall(
            """
              ;WITH Base AS (
                SELECT
                    P.OrderDocumentID,
                    ScheduledDT =
                        CAST(CAST(P.DeliveryPromise AS date) AS datetime)
                        + CAST(TRY_CONVERT(time(0), H.Value) AS datetime)
                FROM dbo.docDocumentOrderCayal AS P
                INNER JOIN dbo.OrderSchedulesCayal AS H
                    ON P.ScheduleID = H.ScheduleID
                WHERE CAST(P.DeliveryPromise AS date) = CAST(? AS date)
                  AND P.StatusID IN (2, 16, 17, 18)  -- panel logística; ajusta si aplica
                  AND TRY_CONVERT(time(0), H.Value) IS NOT NULL
            )
            SELECT
                SUM(CASE WHEN DATEDIFF(MINUTE, GETDATE(), ScheduledDT) <= 15 THEN 1 ELSE 0 END) AS RestLeq15,
                SUM(CASE WHEN DATEDIFF(MINUTE, GETDATE(), ScheduledDT) BETWEEN 16 AND 30 THEN 1 ELSE 0 END) AS Rest16to30,
                SUM(CASE WHEN DATEDIFF(MINUTE, GETDATE(), ScheduledDT) < -30 THEN 1 ELSE 0 END) AS LateGt30
            FROM Base;
            """,
            (fecha,)
        )

    def buscar_info_cliente_seleccionado(self, business_entity_id):
        return self.base_de_datos.fetchall("""
              SELECT *
              FROM [dbo].[zvwBuscarInfoCliente-BusinessEntityID](?)
            """, (business_entity_id,))

