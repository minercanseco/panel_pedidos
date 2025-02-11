import copy

from cayal.ventanas import Ventanas

from controlador_captura import ControladorCaptura
from interfaz_captura import InterfazCaptura
from modelo_captura import ModeloCaptura
from configurar_pedido import ConfigurarPedido


class LlamarInstanciaCaptura:
    def __init__(self, cliente, documento, base_de_datos, parametros, utilerias, master):
        self._master = master
        self._cliente = cliente
        self._documento = documento
        self._base_de_datos = base_de_datos
        self._parametros_contpaqi = parametros

        self._utilerias = utilerias
        self._ventanas = Ventanas(self._master)

        self._procesando_documento = False
        self._editando_documento = False
        self._info_documento = {}

        self._settear_valores_principales()
        self._determinar_si_se_inicia_captura_o_edicion()

    def _llamar_instancia_captura(self):

        if self._parametros_contpaqi.id_principal not in (0, -1):
            self._rellenar_instancias_importadas()

        if not self._documento.cancelled_on:

            pregunta = '¿Desea guardar el documento?'
            ventana = self._ventanas.crear_popup_ttkbootstrap(master=self._master,
                                                              titulo='Capturar pedido',
                                                              ocultar_master=True,
                                                              ejecutar_al_cierre=self._procesar_documento,
                                                              preguntar=pregunta)
            ventana.grab_release()

        if self._documento.cancelled_on:
            ventana = self._ventanas.crear_popup_ttkbootstrap(self._master,
                                                              titulo='Capturar pedido',
                                                              ocultar_master=True,
                                                              ejecutar_al_cierre=self._procesar_documento)
            ventana.grab_release()

        # llamamos a la instancia de la interfaz

        interfaz = InterfazCaptura(ventana, self._parametros_contpaqi.id_modulo)

        # llamos a la instancia del modelo
        modelo = ModeloCaptura(self._base_de_datos,
                               interfaz.ventanas,
                               self._utilerias,
                               self._cliente,
                               self._parametros_contpaqi,
                               self._documento,
                               )

        # llamamos a la instancia del controlador
        controlador = ControladorCaptura(interfaz,
                                         modelo,
                                         )

        # esperamos la ventana para recibir las partidas
        ventana.wait_window()

        # asigna el valor del documento por posibles cambios que haya habido en el proceso de captura
        # y las partidas recien capturadas
        self._documento = controlador.documento

        if self._module_id == 1687:
            self._base_de_datos.desmarcar_documento_en_uso(self._documento.document_id,
                                                           pedido=True)
        if self._module_id != 1687:
            self._base_de_datos.desmarcar_documento_en_uso(self._documento.document_id,
                                                           pedido=False)

    def _solo_existe_servicio_domicilio_en_documento(self):

        existe = [producto for producto in self._documento.items if producto['ProductID'] == 5606]

        if existe and len(self._documento.items) == 1:
            return True

        return False

    def _procesar_documento(self):
        if not self._procesando_documento:
            # actualiza bandera de procesamiento
            self._procesando_documento = True

            # nuevos documentos
            if self._documento.document_id == 0:

                if self._parametros_contpaqi.id_modulo == 1687:
                    if self._solo_existe_servicio_domicilio_en_documento():
                        return

                    if not self._documento.items:
                        return

                    self._documento.document_id = self._crear_cabecera_pedido_cayal()

            # el procedimiento almacenado es un merge preparado para actualizar o insertar segun sea el caso
            self._insertar_partidas_documento(self._documento.document_id)
            self._insertar_partidas_extra_documento(self._documento.document_id)

            self._actualizar_totales_documento(self._documento.document_id)



            production_type_id = self._determinar_tipo_de_orden_produccion()
            self._base_de_datos.command('UPDATE docDocumentOrderCayal SET ProductionTypeID = ? WHERE OrderDocumentID = ?',
                                        (production_type_id, self._documento.document_id))

    def _determinar_tipo_de_orden_produccion(self):

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

    def _crear_cabecera_pedido_cayal(self):

        # aplica insercion especial a tabla de sistema de pedidos cayal

        document_id = 0

        parametros_pedido = self._documento.order_parameters
        production_type_id = self._determinar_tipo_de_orden_produccion()
        if parametros_pedido:
            parametros = (
                parametros_pedido.get('RelatedOrderID',0),
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

    def _insertar_partidas_documento(self, document_id):

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

    def _insertar_partidas_extra_documento(self, document_id):

        def _buscar_document_item_id(uuid_partida):
            return [
                partida['DocumentItemID']
                for partida in self._documento.items
                if partida['uuid'] == uuid_partida
            ][0]


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

    def _actualizar_totales_documento(self, document_id):
        total = self._documento.total
        subtotal = self._documento.subtotal
        total_tax = self._documento.total_tax

        if self._parametros_contpaqi.id_modulo == 1687:
            self._base_de_datos.actualizar_totales_pedido_cayal(document_id,
                                                                subtotal,
                                                                total_tax,
                                                                total)

    def _rellenar_instancias_importadas(self):

        # rellena la informacion relativa al cliente
        busines_entity_id = self._buscar_business_entity_id(self._documento.document_id)
        info_cliente = self._buscar_info_cliente(busines_entity_id)

        self._cliente.consulta = info_cliente
        self._cliente.settear_valores_consulta()

        info_pedido = self._info_documento

        self._documento.depot_id = info_pedido.get('DepotID', 0)
        self._documento.depot_name = info_pedido.get('DepotName', '')
        self._documento.created_by = info_pedido.get('CreatedBy', 0)
        self._documento.address_detail_id = info_pedido.get('AddressDetailID', 0)
        self._documento.cancelled_on = info_pedido.get('CancelledOn', None)
        self._documento.docfolio = info_pedido.get('DocFolio', '')
        self._documento.comments = info_pedido.get('CommentsOrder', '')

        direccion = self._base_de_datos.buscar_detalle_direccion_formateada(self._documento.address_detail_id)
        self._documento.address_details = direccion

        self._documento.address_name = info_pedido.get('AddressName', '')
        self._documento.business_entity_id = self._cliente.business_entity_id
        self._documento.customer_type_id = self._cliente.cayal_customer_type_id

        if self._module_id == 1687:

            self._base_de_datos.marcar_documento_en_uso(self._documento.document_id,
                                                        self._user_id,
                                                        pedido=True
                                                        )
        if self._module_id != 1687:
            self._base_de_datos.marcar_documento_en_uso(self._documento.document_id,
                                                        self._user_id,
                                                        pedido=False
                                                        )

        self._editando_documento = True

    def _buscar_business_entity_id(self, document_id):
        return self._base_de_datos.buscar_business_entity_id_documento(
            document_id,
            self._parametros_contpaqi.id_modulo
        )

    def _buscar_info_cliente(self, business_entity_id):
        return self._base_de_datos.buscar_info_cliente(business_entity_id)

    def _determinar_si_se_inicia_captura_o_edicion(self):

        if self._module_id == 1687:

            if self._documento.document_id > 0:
                order_type_id = self._info_documento['OrderTypeID']

                if order_type_id != 1 and self._user_group_id == 11:
                    self._ventanas.mostrar_mensaje('No se pueden editar los anexos o cambios por cajeros.')
                    return

        self._llamar_instancia_captura()

    def _buscar_informacion_documento_existente(self):
        # rellena la informacion relativa al documento
        consulta_info_pedido = self._base_de_datos.buscar_info_documento_pedido_cayal(
            self._documento.document_id
        )
        info_pedido = consulta_info_pedido[0]
        self._info_documento = info_pedido

    def _settear_valores_principales(self):

        self._module_id = self._parametros_contpaqi.id_modulo
        self._user_id = self._parametros_contpaqi.id_usuario
        self._user_group_id = self._base_de_datos.fetchone(
            'SELECT UserGroupID FROM engUser WHERE UserID = ?',
            (self._user_id,))
        self._parametros_contpaqi.nombre_usuario = self._base_de_datos.buscar_nombre_de_usuario(self._user_id)

        if self._parametros_contpaqi.id_principal > 0:
            self._documento.document_id = self._parametros_contpaqi.id_principal
            self._buscar_informacion_documento_existente()


