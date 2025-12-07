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

    def afectar_bitacora(self, order_document_id, user_id, comentario):

        self.base_de_datos.insertar_registro_bitacora_pedidos(order_document_id=order_document_id,
                                                               change_type_id=19,
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