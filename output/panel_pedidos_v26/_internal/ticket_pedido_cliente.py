
import os
import platform
import tempfile

from generador_ticket_cliente import GeneradorTicketCliente


class TicketPedidoCliente:
    def __init__(self, base_de_datos, utilerias, parametros):
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._parametros = parametros
        self._user_id = self._parametros.id_usuario
        self._order_document_id = self._parametros.id_principal

        self._ticket = GeneradorTicketCliente(32)
        self._ticket.ruta_archivo = self._obtener_directorio_reportes()
        self._info_cliente = None
        self._info_pedido = None

        self._generar_ticket()
        self._afectar_bitacora()

    def _generar_ticket(self):
        self._info_pedido = self._buscar_info_pedido()
        self._settear_valores_ticket(self._info_pedido)
        self._ticket.guardar_archivo()


    def _obtener_directorio_reportes(self):
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

    def _settear_valores_ticket(self, info_pedido):

        self._ticket.cliente = info_pedido.get('OfficialName', '')#.strip().replace('\n', '').replace(' ', '')
        self._ticket.pedido = info_pedido.get('DocFolio', '')
        self._ticket.tipo = info_pedido.get('DocumentType', '')
        self._ticket.forma_pago_id = info_pedido.get('WayToPayID',1)

        fecha_captura = info_pedido.get('CreatedOn', '')
        hora_captura = info_pedido.get('CreatedOnTime', '')
        captura = f'{fecha_captura}-{hora_captura}'
        self._ticket.venta = captura
        self._ticket._forma_pago = info_pedido.get('PaymentTermName','')
        fecha_entrega = info_pedido.get('DeliveryPromise', '')
        hora_entrega = info_pedido.get('DeliveryTime', '')
        entrega = f'{fecha_entrega}-{hora_entrega}'
        self._ticket.entrega = entrega

        self._ticket.capturista = info_pedido.get('CreatedByUserName', '')
        self._ticket.comentario = info_pedido.get('CommentsOrder','')

        consulta = self._base_de_datos.fetchall(
            """
            SELECT Z.ZoneName, DT.City, DT.Street, DT.ExtNumber
            FROM docDocumentOrderCayal D INNER JOIN
                orgZone Z ON D.ZoneID = D.ZoneID INNER JOIN
                orgAddressDetail DT ON D.AddressDetailID = DT.AddressDetailID
            WHERE OrderDocumentID = ? AND D.ZoneID = Z.ZoneID
            """,
            (self._order_document_id,)
        )
        if consulta:
            valores = consulta[0]

            colonia = valores.get('City', '')
            colonia = colonia.upper()
            calle = valores.get('Street', '')
            numero = valores.get('ExtNumber', '')

            self._ticket.calle = calle if calle else ''
            self._ticket.numero = numero if numero else ''
            self._ticket.colonia = colonia if colonia else ''

        consulta_partidas = self._base_de_datos.buscar_partidas_pedidos_produccion_cayal(
            self._order_document_id, partidas_eliminadas=False, partidas_producidas=True)


        self._procesar_partidas(consulta_partidas)

    def _buscar_info_pedido(self):
        consulta = self._base_de_datos.buscar_info_documento_pedido_cayal(self._order_document_id)
        if consulta:
            return consulta[0]

    def _procesar_partidas(self, partidas):
        partidas_con_impuestos = []
        total_documento = 0
        for partida in partidas:
            cantidad = self._utilerias.redondear_valor_cantidad_a_decimal(partida['Quantity'])
            partida_con_impuesto  = self._utilerias.crear_partida(partida, cantidad)
            partidas_con_impuestos.append(partida_con_impuesto)
            total_documento += partida_con_impuesto['total']

        self._ticket.productos = partidas_con_impuestos
        self._ticket.total = total_documento

    def _afectar_bitacora(self):
        user_name = self._base_de_datos.buscar_nombre_de_usuario(self._user_id)
        comentario = f'Ticket cliente generado por: {user_name}'
        self._base_de_datos.insertar_registro_bitacora_pedidos(self._order_document_id,
                                                               11,
                                                               self._user_id,
                                                               comments=comentario)