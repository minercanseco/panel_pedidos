import copy

from cayal.ventanas import Ventanas

from controlador_captura import ControladorCaptura
from interfaz_captura import InterfazCaptura
from modelo_captura import ModeloCaptura


class LlamarInstanciaCaptura:
    def __init__(self, cliente, documento, base_de_datos, parametros, utilerias, master, ofertas = None):
        self._master = master
        self._cliente = cliente
        self._ofertas = ofertas
        self.documento = documento
        self._base_de_datos = base_de_datos
        self._parametros_contpaqi = parametros

        self._utilerias = utilerias
        self._ventanas = Ventanas(self._master)

        self._procesando_documento = False
        self._editando_documento = False
        self._info_documento = {}

        self._locked_doc_id = 0
        self._locked_is_pedido = False
        self._locked_active = False

        self._settear_valores_principales()
        self._determinar_si_se_inicia_captura_o_edicion()

    def _llamar_instancia_captura(self):

        if self._parametros_contpaqi.id_principal not in (0, -1):
            self._rellenar_instancias_importadas()

        # --- callback que SIEMPRE guarda (si procede) y DESMARCA el bloqueo ---
        def _on_close():
            try:
                self._procesar_documento()
            finally:
                # usa helper si existe; si no, fallback directo
                if hasattr(self, "_unmark_in_use"):
                    self._unmark_in_use()
                else:
                    try:
                        doc_id = int(getattr(self.documento, "document_id", 0) or 0)
                        if doc_id > 0:
                            pedido_flag = (self._module_id == 1687)
                            self._base_de_datos.desmarcar_documento_en_uso(doc_id, pedido=pedido_flag)
                    except Exception:
                        pass



        # --- crea el popup como antes, pero usando _on_close ---
        if not self.documento.cancelled_on:
            pregunta = '¿Desea guardar el documento?'
            ventana = self._ventanas.crear_popup_ttkbootstrap(
                master=self._master,
                titulo='Capturar pedido',
                ocultar_master=True,
                ejecutar_al_cierre=_on_close,
                preguntar=pregunta
            )
        else:
            ventana = self._ventanas.crear_popup_ttkbootstrap(
                self._master,
                titulo='Capturar pedido',
                ocultar_master=True,
                ejecutar_al_cierre=_on_close
            )



        # ----- Resto de tu flujo intacto -----
        interfaz = InterfazCaptura(ventana, self._parametros_contpaqi.id_modulo)

        modelo = ModeloCaptura(self._base_de_datos,
                               interfaz.ventanas,
                               self._utilerias,
                               self._cliente,
                               self._parametros_contpaqi,
                               self.documento,
                               self._ofertas
                               )

        controlador = ControladorCaptura(interfaz, modelo)

        # asigna el valor del documento por posibles cambios que haya habido en el proceso de captura
        self.documento = controlador.documento

    def _solo_existe_servicio_domicilio_en_documento(self):

        existe = [producto for producto in self.documento.items if producto['ProductID'] == 5606]

        if existe and len(self.documento.items) == 1:
            return True

        return False

    def _procesar_documento(self):
        if self._procesando_documento:
            return  # ya se está procesando / se procesó

        self._procesando_documento = True
        try:
            # 1) Documento nuevo: crear cabecera si aplica
            if int(self.documento.document_id or 0) == 0:
                if self._parametros_contpaqi.id_modulo == 1687:
                    # Si solo hay servicio a domicilio o no hay partidas, no hay nada que guardar
                    if self._solo_existe_servicio_domicilio_en_documento():
                        return
                    if not self.documento.items:
                        return

                    # Crear cabecera
                    self.documento.document_id = int(self._crear_cabecera_pedido_cayal() or 0)

                    # Si se generó ID, opcionalmente marca en uso ahora para evitar colisiones
                    if self.documento.document_id > 0:
                        if hasattr(self, "_mark_in_use") and callable(self._mark_in_use):
                            self._mark_in_use(self.documento.document_id, pedido=True)
                        else:
                            # Fallback directo si no tienes helper
                            self._base_de_datos.marcar_documento_en_uso(self.documento.document_id,
                                                                        self._user_id, pedido=True)
                else:
                    # Otros módulos (no 1687): deja el camino preparado por si agregas creación aquí
                    pass

            # Si después de la fase anterior seguimos sin ID, no se puede persistir nada
            if int(self.documento.document_id or 0) == 0:
                return

            # 2) Insert/merge de partidas
            self._insertar_partidas_documento(self.documento.document_id)
            self._insertar_partidas_extra_documento(self.documento.document_id)

            # 3) Totales
            self._actualizar_totales_documento(self.documento.document_id)

            # 4) Actualizaciones finales en cabecera (ProductionType y campos editables)
            production_type_id = int(self._determinar_tipo_de_orden_produccion() or 1)
            comments = self.documento.comments or ''
            address_detail_id = int(self.documento.address_detail_id or 0)
            total = float(self.documento.total or 0)

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
                        AddressDetailID = @AddressDetailID
                    WHERE OrderDocumentID = @OrderDocumentID
                END

                UPDATE docDocumentOrderCayal 
                SET ProductionTypeID = @ProductionTypeID
                WHERE OrderDocumentID = @OrderDocumentID
            """, (production_type_id, comments, address_detail_id, total, self.documento.document_id))

        except Exception as e:
            # Log simple; evita romper el cierre de la ventana.
            try:
                print(f"[procesar_documento] Error: {e}")
            except Exception:
                pass
            # Puedes relanzar si quieres que se vea arriba:
            # raise
        finally:
            # NO desmarques aquí. El desmarcado debe suceder en el callback de cierre del popup
            # (p.ej., _on_close) para garantizar que se libere incluso si hubo excepciones.
            pass

    def _determinar_tipo_de_orden_produccion(self):

        partidas = self.documento.items
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

        parametros_pedido = self.documento.order_parameters
        production_type_id = self._determinar_tipo_de_orden_produccion()
        if parametros_pedido:
            parametros = (
                parametros_pedido.get('RelatedOrderID',0),
                parametros_pedido.get('BusinessEntityID'),
                parametros_pedido.get('CreatedBy'),
                self.documento.comments,
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

            for partida in self.documento.items:
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
            for partida in self.documento.items:
                if partida.get('uuid') == uuid_partida:
                    return int(partida.get('DocumentItemID', 0))
            return 0  # o puedes lanzar una excepción controlada si prefieres


        if not self.documento.items_extra:
            return

        if self._parametros_contpaqi.id_modulo == 1687:

            for partida in self.documento.items_extra:

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
        total = self.documento.total
        subtotal = self.documento.subtotal
        total_tax = self.documento.total_tax

        if self._parametros_contpaqi.id_modulo == 1687:
            self._base_de_datos.actualizar_totales_pedido_cayal(document_id,
                                                                subtotal,
                                                                total_tax,
                                                                total)

    def _rellenar_instancias_importadas(self):

        # 1) Cliente
        busines_entity_id = self._buscar_business_entity_id(self.documento.document_id)
        info_cliente = self._buscar_info_cliente(busines_entity_id) or []
        self._cliente.consulta = info_cliente
        self._cliente.settear_valores_consulta()

        # 2) Datos del pedido/documento
        info_pedido = self._info_documento or {}

        self.documento.depot_id = info_pedido.get('DepotID', 0)
        self.documento.depot_name = info_pedido.get('DepotName', '')
        self.documento.created_by = info_pedido.get('CreatedBy', 0)
        self.documento.address_detail_id = info_pedido.get('AddressDetailID', 0)
        self.documento.cancelled_on = info_pedido.get('CancelledOn', None)
        self.documento.docfolio = info_pedido.get('DocFolio', '')
        self.documento.comments = info_pedido.get('CommentsOrder', '')
        self.documento.address_name = info_pedido.get('AddressName', '')
        self.documento.business_entity_id = self._cliente.business_entity_id
        self.documento.customer_type_id = self._cliente.cayal_customer_type_id

        # 3) Dirección formateada (solo si hay ID válido)
        if int(self.documento.address_detail_id or 0) > 0:
            direccion = self._base_de_datos.buscar_detalle_direccion_formateada(self.documento.address_detail_id)
        else:
            direccion = {}
        self.documento.address_details = direccion

        # 4) Marcar en uso (solo si hay document_id > 0). Evita doble marcado en la misma instancia.
        doc_id = int(self.documento.document_id or 0)
        if doc_id > 0:
            pedido_flag = (self._module_id == 1687)

            # Si ya está marcado por esta misma instancia, no lo marques de nuevo
            already_locked_same_doc = getattr(self, "_locked_active", False) and \
                                      getattr(self, "_locked_doc_id", 0) == doc_id

            if not already_locked_same_doc:
                # Usa helper si existe; si no, usa la BD directamente
                if hasattr(self, "_mark_in_use") and callable(self._mark_in_use):
                    self._mark_in_use(doc_id, pedido=pedido_flag)
                else:
                    self._base_de_datos.marcar_documento_en_uso(doc_id, self._user_id, pedido=pedido_flag)

        # 5) Bandera de estado
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

            if self.documento.document_id > 0:
                order_type_id = self._info_documento['OrderTypeID']

                if order_type_id != 1 and self._user_group_id == 11:
                    self._ventanas.mostrar_mensaje('No se pueden editar los anexos o cambios por cajeros.')
                    return

        self._llamar_instancia_captura()

    def _buscar_informacion_documento_existente(self):
        # rellena la informacion relativa al documento
        consulta_info_pedido = self._base_de_datos.buscar_info_documento_pedido_cayal(
            self.documento.document_id
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
            self.documento.document_id = self._parametros_contpaqi.id_principal
            self._buscar_informacion_documento_existente()

    def _mark_in_use(self, document_id, pedido: bool):
        self._locked_doc_id = int(document_id or 0)
        self._locked_is_pedido = bool(pedido)
        self._locked_active = self._locked_doc_id > 0
        if self._locked_active:
            self._base_de_datos.marcar_documento_en_uso(self._locked_doc_id, self._user_id,
                                                        pedido=self._locked_is_pedido)

    def _unmark_in_use(self):
        # idempotente, por si se llama más de una vez
        if getattr(self, "_locked_active", False) and getattr(self, "_locked_doc_id", 0):
            try:
                self._base_de_datos.desmarcar_documento_en_uso(self._locked_doc_id, pedido=self._locked_is_pedido)
            finally:
                self._locked_active = False
                self._locked_doc_id = 0
                self._locked_is_pedido = False

