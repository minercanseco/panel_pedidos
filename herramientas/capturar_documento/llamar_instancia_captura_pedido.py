import copy

from cayal.cliente import Cliente
from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.documento import Documento
from cayal.util import Utilerias

from herramientas.capturar_documento.controlador_captura import ControladorCaptura
from herramientas.capturar_documento.interfaz_captura import InterfazCaptura
from herramientas.capturar_documento.modelo_captura import ModeloCaptura


MODULO_PEDIDOS = 1687
PRODUCTO_SERVICIO_DOMICILIO = 5606


class LlamarInstanciaCapturaPedido:
    """Prepara, muestra y persiste exclusivamente la captura de pedidos."""

    def __init__(
            self,
            master,
            parametros,
            cliente=None,
            documento=None,
            ofertas=None,
            base_de_datos=None,
            utilerias=None,
            abrir_interfaz=True,
            esperar_cierre=True,
            al_finalizar=None,
    ):
        self._master = master
        self._parametros_contpaqi = parametros
        self._module_id = int(getattr(parametros, 'id_modulo', 0) or 0)
        self._user_id = int(getattr(parametros, 'id_usuario', 0) or 0)
        self._esperar_cierre = esperar_cierre
        self._al_finalizar = al_finalizar

        self._declarar_clases_auxiliares(
            cliente,
            documento,
            base_de_datos,
            utilerias,
        )
        self._declarar_variables_instancia(ofertas)

        if self._module_id != MODULO_PEDIDOS:
            raise ValueError(
                'LlamarInstanciaCapturaPedido solamente admite el módulo 1687.'
            )

        if abrir_interfaz:
            self.ejecutar_captura()

    def _declarar_clases_auxiliares(
            self,
            cliente=None,
            documento=None,
            base_de_datos=None,
            utilerias=None,
    ):
        self._documento = documento if documento is not None else Documento()
        self._cliente = cliente if cliente is not None else Cliente()
        self._base_de_datos = (
            base_de_datos if base_de_datos is not None
            else ComandosBaseDatos()
        )
        self._utilerias = (
            utilerias if utilerias is not None else Utilerias()
        )

    def _declarar_variables_instancia(self, ofertas=None):
        document_id_parametro = int(
            getattr(self._parametros_contpaqi, 'id_principal', 0) or 0
        )
        if not int(getattr(self._documento, 'document_id', 0) or 0):
            self._documento.document_id = document_id_parametro

        self._ofertas = ofertas or {}
        self._procesando_documento = False
        self._editando_documento = False
        self.nuevo_pedido = False

        self._locked_doc_id = 0
        self._locked_is_pedido = False
        self._locked_active = False

        self._interfaz_captura = None
        self._modelo_captura = None
        self._controlador_captura = None
        self._preparado = False
        self._finalizado = False

    def _homologar_direccion_fiscal(self, business_entity_id):
        if int(business_entity_id or 0) <= 0:
            return

        self._base_de_datos.command(
            """
            DECLARE @BusinessEntityID INT = ?;

            UPDATE ADT
               SET ADT.StateProvince = EM.AddressFiscalStateProvince,
                   ADT.City = EM.AddressFiscalCity,
                   ADT.Municipality = EM.AddressFiscalMunicipality,
                   ADT.Street = EM.AddressFiscalStreet,
                   ADT.Comments = EM.AddressFiscalComments,
                   ADT.CountryCode = EM.AddressFiscalCountryCode,
                   ADT.CityCode = EM.AddressFiscalCityCode,
                   ADT.MunicipalityCode = EM.AddressFiscalMunicipalityCode,
                   ADT.Telefono = EM.BusinessEntityPhone
              FROM orgBusinessEntityMainInfo EM
              JOIN orgAddressDetail ADT
                ON EM.AddressFiscalDetailID = ADT.AddressDetailID
             WHERE EM.BusinessEntityID = @BusinessEntityID
               AND (
                    ISNULL(ADT.StateProvince, '') <>
                        ISNULL(EM.AddressFiscalStateProvince, '')
                 OR ISNULL(ADT.City, '') <> ISNULL(EM.AddressFiscalCity, '')
                 OR ISNULL(ADT.Municipality, '') <>
                        ISNULL(EM.AddressFiscalMunicipality, '')
                 OR ISNULL(ADT.Street, '') <>
                        ISNULL(EM.AddressFiscalStreet, '')
                 OR ISNULL(ADT.Comments, '') <>
                        ISNULL(EM.AddressFiscalComments, '')
                 OR ISNULL(ADT.CountryCode, '') <>
                        ISNULL(EM.AddressFiscalCountryCode, '')
                 OR ISNULL(ADT.CityCode, '') <>
                        ISNULL(EM.AddressFiscalCityCode, '')
                 OR ISNULL(ADT.MunicipalityCode, '') <>
                        ISNULL(EM.AddressFiscalMunicipalityCode, '')
                 OR ISNULL(ADT.Telefono, '') <>
                        ISNULL(EM.BusinessEntityPhone, '')
               );
            """,
            (business_entity_id,),
        )

    def _settear_cliente_y_direcciones(self, business_entity_id):
        business_entity_id = int(business_entity_id or 0)
        if not business_entity_id:
            return

        self._homologar_direccion_fiscal(business_entity_id)
        info_cliente = self._base_de_datos.fetchall(
            """
            SELECT *
              FROM [dbo].[zvwBuscarInfoCliente-BusinessEntityID](?)
            """,
            (business_entity_id,),
        )
        self._cliente.consulta = info_cliente
        self._cliente.settear_valores_consulta()

        self._cliente.addresses_details = []
        for direccion in (
                self._base_de_datos.buscar_direcciones_cliente(
                    business_entity_id
                ) or []):
            self._cliente.add_address_detail(direccion)

    def _settear_documento_existente(self):
        consulta = self._base_de_datos.buscar_info_documento_pedido_cayal(
            self._documento.document_id
        ) or []
        if not consulta:
            raise ValueError('No se encontró la información del pedido.')

        self._documento.consulta = consulta
        self._documento.settear_valores_consulta_pedido()
        self._editando_documento = True

        self._settear_cliente_y_direcciones(
            self._documento.business_entity_id
        )

    def _settear_direccion_documento(self):
        direcciones = getattr(self._cliente, 'addresses_details', []) or []
        address_detail_id = int(
            getattr(self._documento, 'address_detail_id', 0) or 0
        )

        if not address_detail_id and direcciones:
            fiscal = next(
                (
                    direccion for direccion in direcciones
                    if int(direccion.get('AddressTypeID', 0) or 0) == 1
                ),
                direcciones[0],
            )
            address_detail_id = int(fiscal.get('AddressDetailID', 0) or 0)

        direccion = next(
            (
                registro for registro in direcciones
                if int(registro.get('AddressDetailID', 0) or 0)
                == address_detail_id
            ),
            None,
        )
        if direccion is None:
            self._documento.address_details = {}
            self._documento.depot_id = 0
            self._documento.depot_name = ''
            return

        depot_id = int(direccion.get('DepotID', 0) or 0)
        depot_name = ''
        if depot_id:
            fila = self._base_de_datos.fetchone(
                'SELECT DepotName FROM orgDepot WHERE DepotID = ?',
                (depot_id,),
            )
            if isinstance(fila, dict):
                depot_name = fila.get('DepotName', '') or ''
            elif fila:
                depot_name = fila[0] if isinstance(fila, (tuple, list)) else fila

        self._documento.address_details = direccion
        self._documento.address_detail_id = address_detail_id
        self._documento.address_name = direccion.get('AddressName', '') or ''
        self._documento.depot_id = depot_id
        self._documento.depot_name = depot_name
        self._documento.business_entity_id = self._cliente.business_entity_id
        self._documento.customer_type_id = self._cliente.customer_type_id
        self._documento.delivery_cost = (
            self._utilerias.redondear_valor_cantidad_a_decimal(
                direccion.get('DeliveryCost', 20)
            )
        )

    @property
    def documento(self):
        return self._documento

    @property
    def cliente(self):
        return self._cliente

    @property
    def ofertas(self):
        return self._ofertas

    @property
    def es_nuevo(self):
        return not self._editando_documento

    def preparar(self):
        """Carga y bloquea el pedido; funciona para alta y para edición."""
        if self._preparado:
            return self

        if int(self._documento.document_id or 0):
            self._settear_documento_existente()
        else:
            business_entity_id = int(
                getattr(self._cliente, 'business_entity_id', 0) or 0
            )
            if business_entity_id and not getattr(
                    self._cliente, 'addresses_details', None):
                self._settear_cliente_y_direcciones(business_entity_id)

        self._settear_direccion_documento()
        if self._preparar_bloqueo():
            usuario = self._base_de_datos.esta_documento_en_uso(
                self._documento.document_id,
                pedido=True,
            )
            usuario = str(usuario or 'otro usuario').strip()
            raise ValueError(
                f'No es posible editar el pedido porque está en uso por {usuario}.'
            )
        self._preparado = True
        return self

    def ejecutar_captura(self):
        """Ejecuta el aplicativo común y aplica el tratamiento del pedido."""
        if not self._esperar_cierre:
            return self._ejecutar_captura_asincrona()

        try:
            self.preparar()
            self._interfaz_captura = InterfazCaptura(
                self._master,
                self._module_id,
                solicitar_guardado=True
            )
            self._modelo_captura = ModeloCaptura(self._base_de_datos,
                                   self._utilerias,
                                   self._cliente,
                                   self._documento,
                                   self._parametros_contpaqi,
                                   #self._ofertas

            )
            self._controlador_captura = ControladorCaptura(
                self._interfaz_captura,
                self._modelo_captura,
            )
            self._master.wait_window()

            if self._interfaz_captura.guardar_documento is True:
                self.guardar()

            return self._documento.document_id
        finally:
            self.finalizar()

    def _ejecutar_captura_asincrona(self):
        """Finaliza la captura al cerrar su ventana sin bloquear el panel."""
        self.preparar()
        completada = False

        def completar():
            nonlocal completada
            if completada:
                return
            completada = True
            try:
                if (
                        self._interfaz_captura is not None
                        and self._interfaz_captura.guardar_documento is True
                ):
                    self.guardar()
            finally:
                self.finalizar()
                if callable(self._al_finalizar):
                    self._al_finalizar(self._documento.document_id)

        def al_destruir(event):
            if event.widget is self._master:
                completar()

        try:
            self._master.bind('<Destroy>', al_destruir, add='+')
            self._interfaz_captura = InterfazCaptura(
                self._master,
                self._module_id,
                solicitar_guardado=True,
            )
            self._modelo_captura = ModeloCaptura(
                self._base_de_datos,
                self._utilerias,
                self._cliente,
                self._documento,
                self._parametros_contpaqi,
            )
            self._controlador_captura = ControladorCaptura(
                self._interfaz_captura,
                self._modelo_captura,
            )
        except Exception:
            completada = True
            self.finalizar()
            raise

        return self._documento.document_id

    def guardar(self):
        """Crea o actualiza el pedido según el estado del Documento."""
        self.preparar()
        self._procesar_documento_pedido()
        return self._documento.document_id

    def finalizar(self):
        """Libera una sola vez los recursos exclusivos del pedido."""
        if self._finalizado:
            return
        self._desmarcar_en_uso()
        self._finalizado = True

    def _preparar_bloqueo(self):
        document_id = int(self._documento.document_id or 0)
        if not document_id:
            return False

        status, motivo, locked_user_id = (
            self._base_de_datos.obtener_status_bloqueo_pedido(
                order_document_id=document_id,
                user_id=self._user_id,
            )
        )
        bloquear = status != 'Desbloqueado'
        locked_user_id = int(locked_user_id or 0)

        if locked_user_id not in (0, self._user_id):
            return True

        self._marcar_en_uso(document_id, pedido=True)
        try:
            status, motivo, locked_user_id = (
                self._base_de_datos.obtener_status_bloqueo_pedido(
                    order_document_id=document_id,
                    user_id=self._user_id,
                )
            )
        except Exception:
            self._desmarcar_en_uso()
            raise

        if int(locked_user_id or 0) != self._user_id:
            self._desmarcar_en_uso()
            return True
        return bloquear

    def _marcar_en_uso(self, document_id, pedido=True):
        document_id = int(document_id or 0)
        if not document_id:
            return
        self._base_de_datos.marcar_documento_en_uso(
            document_id,
            self._user_id,
            pedido=pedido,
        )
        self._locked_doc_id = document_id
        self._locked_is_pedido = bool(pedido)
        self._locked_active = True

    def _desmarcar_en_uso(self):
        if not self._locked_active or not self._locked_doc_id:
            return
        try:
            self._base_de_datos.desmarcar_documento_en_uso(
                self._locked_doc_id,
                pedido=self._locked_is_pedido,
                user_id=self._user_id,
            )
        finally:
            self._locked_doc_id = 0
            self._locked_is_pedido = False
            self._locked_active = False

    def _solo_existe_servicio_domicilio(self):
        partidas = getattr(self._documento, 'items', []) or []
        return len(partidas) == 1 and int(
            partidas[0].get('ProductID', 0) or 0
        ) == PRODUCTO_SERVICIO_DOMICILIO

    def _determinar_tipo_orden_produccion(self):
        tipos = {
            int(partida.get('ProductTypeIDCayal', 0) or 0)
            for partida in self._documento.items
            if int(partida.get('ProductID', 0) or 0)
            != PRODUCTO_SERVICIO_DOMICILIO
            and int(partida.get('ItemProductionStatusModified', 0) or 0) != 3
        }
        mapa = {
            frozenset({0}): 2,
            frozenset({1}): 1,
            frozenset({2}): 3,
            frozenset({0, 1}): 4,
            frozenset({1, 2}): 5,
            frozenset({0, 2}): 6,
            frozenset({0, 1, 2}): 7,
        }
        return mapa.get(frozenset(tipos), 1)

    def _crear_cabecera_pedido(self):
        parametros = self._documento.order_parameters or {}
        if not parametros:
            return 0

        valores = (
            parametros.get('RelatedOrderID', 0),
            parametros.get('BusinessEntityID'),
            parametros.get('CreatedBy'),
            self._documento.comments,
            parametros.get('ZoneID'),
            parametros.get('AddressDetailID'),
            parametros.get('DocumentTypeID'),
            parametros.get('OrderTypeID'),
            parametros.get('OrderDeliveryTypeID'),
            parametros.get('SubTotal'),
            parametros.get('TotalTax'),
            parametros.get('Total'),
            self._determinar_tipo_orden_produccion(),
            parametros.get('HostName'),
            parametros.get('ScheduleID', 1),
            parametros.get('OrderDeliveryCost'),
            parametros.get('DepotID', 0),
        )
        document_id = int(
            self._base_de_datos.crear_pedido_cayal2(valores) or 0
        )
        if not document_id:
            return 0

        self._base_de_datos.insertar_registro_bitacora_pedidos(
            document_id,
            1,
            parametros.get('CreatedBy', self._user_id),
            parametros.get('CommentsOrder', ''),
        )
        if int(parametros.get('OrderTypeID', 0) or 0) in (2, 3):
            self._base_de_datos.command(
                """
                DECLARE @OrderID INT = ?;
                UPDATE docDocumentOrderCayal
                   SET NumberAdditionalOrders = (
                           SELECT COUNT(OrderDocumentID)
                             FROM docDocumentOrderCayal
                            WHERE RelatedOrderID = @OrderID
                              AND CancelledOn IS NULL
                       ),
                       StatusID = 2
                 WHERE OrderDocumentID = @OrderID;
                """,
                (parametros.get('RelatedOrderID', 0),),
            )
        return document_id

    def _guardar_partidas(self, document_id):
        for partida in self._documento.items:
            copia = copy.deepcopy(partida)
            estado_modificacion = int(
                copia.get('ItemProductionStatusModified', 0) or 0
            )
            document_item_id = int(
                copia.get('DocumentItemID', 0) or 0
            )

            # Una partida eliminada ya no forma parte del pedido vigente. No
            # debe enviarse otra vez al procedimiento de alta/actualizacion,
            # porque al reabrir y guardar el pedido puede reactivarse. Se
            # conserva el renglon como baja logica para historial y bitacora.
            if estado_modificacion == 3:
                if document_item_id:
                    self._base_de_datos.command(
                        """
                        UPDATE docDocumentItemOrderCayal
                           SET DeletedOn = COALESCE(DeletedOn, GETDATE()),
                               DeletedBy = ?,
                               ItemProductionStatusModified = 3
                         WHERE DocumentID = ?
                           AND DocumentItemID = ?
                        """,
                        (self._user_id, document_id, document_item_id),
                    )
                continue

            product_id = int(copia.get('ProductID', 0) or 0)
            if (
                    copia.get('Unit', 'KILO') != 'KILO'
                    and not self._utilerias.equivalencias_productos_especiales(
                        product_id
                    )):
                copia['CayalPiece'] = 0

            parametros = (
                document_id,
                product_id,
                copia.get('DepotID', 2) or 2,
                copia.get('cantidad', copia.get('Quantity', 0)),
                copia.get('precio', copia.get('UnitPrice', 0)),
                copia.get('CostPrice', 0),
                copia.get('subtotal', 0),
                document_item_id,
                copia.get('TipoCaptura', 0),
                copia.get('CayalPiece', 0),
                copia.get('CayalAmount', 0),
                copia.get('ItemProductionStatusModified', 0),
                copia.get('Comments', ''),
                (
                    self._user_id
                    if estado_modificacion in (1, 2)
                    else copia.get('CreatedBy', self._user_id)
                ),
                (
                    str(copia.get('uuid'))
                    if copia.get('uuid') else None
                ),
            )
            partida['DocumentItemID'] = (
                self._base_de_datos.insertar_partida_pedido_cayal(parametros)
            )

    def _obtener_estado_pedido(self, document_id):
        estado = self._base_de_datos.fetchone(
            'SELECT ISNULL(StatusID, 0) '
            'FROM docDocumentOrderCayal WHERE OrderDocumentID = ?',
            (document_id,),
        )
        return int(estado or 0)

    def _guardar_respaldos_partidas(self, document_id):
        # En estado abierto las modificaciones se guardan directamente en la
        # tabla principal. El procedimiento Extra repite esta validacion, pero
        # se evita llamarlo para no generar trabajo innecesario.
        if self._obtener_estado_pedido(document_id) == 1:
            return

        items_extra = getattr(self._documento, 'items_extra', []) or []
        ids_por_uuid = {
            str(partida.get('uuid')): int(
                partida.get('DocumentItemID', 0) or 0
            )
            for partida in self._documento.items
            if partida.get('uuid')
        }

        for partida in items_extra:
            estado_modificacion = int(
                partida.get('ItemProductionStatusModified', 0) or 0
            )
            if estado_modificacion not in (1, 2, 3):
                continue

            document_item_id = int(
                partida.get('DocumentItemID', 0) or 0
            )
            if not document_item_id and partida.get('uuid'):
                document_item_id = ids_por_uuid.get(
                    str(partida.get('uuid')),
                    0,
                )

            parametros = (
                document_id,
                int(partida.get('ProductID', 0) or 0),
                partida.get('DepotID', 2) or 2,
                partida.get('cantidad', partida.get('Quantity', 0)),
                partida.get('precio', partida.get('UnitPrice', 0)),
                partida.get('CostPrice', 0),
                partida.get('subtotal', 0),
                document_item_id,
                partida.get('TipoCaptura', 0),
                partida.get('CayalPiece', 0),
                partida.get('CayalAmount', 0),
                estado_modificacion,
                partida.get('Comments', ''),
                self._user_id,
            )
            self._base_de_datos.respaldar_partida_pedido_cayal(
                parametros
            )

    def _guardar_bitacora_partidas(self, document_id):
        items_extra = getattr(self._documento, 'items_extra', []) or []
        ids_por_uuid = {
            partida.get('uuid'): int(partida.get('DocumentItemID', 0) or 0)
            for partida in self._documento.items
            if partida.get('uuid')
        }
        acciones = {
            1: (15, 'Agregado'),
            2: (16, 'Editado'),
            3: (17, 'Eliminado'),
        }
        for partida in items_extra:
            estado = int(
                partida.get('ItemProductionStatusModified', 0) or 0
            )
            if estado not in acciones:
                continue
            if estado == 1:
                partida['DocumentItemID'] = ids_por_uuid.get(
                    partida.get('uuid'), 0
                )

            change_type_id, accion = acciones[estado]
            comentario = partida.get('Comments', '') if estado == 2 else (
                f"{accion} {partida.get('ProductName', '')} - "
                f"Cant.{partida.get('cantidad', 0)}"
            )
            self._base_de_datos.insertar_registro_bitacora_pedidos(
                order_document_id=document_id,
                change_type_id=change_type_id,
                user_id=self._user_id,
                comments=comentario,
            )

    def _actualizar_cabecera(self, document_id):
        self._base_de_datos.actualizar_totales_pedido_cayal(
            document_id,
            self._documento.subtotal,
            self._documento.total_tax,
            self._documento.total,
        )
        self._base_de_datos.command(
            """
            DECLARE @ProductionTypeID INT = ?;
            DECLARE @CommentsOrder NVARCHAR(MAX) = ?;
            DECLARE @AddressDetailID INT = ?;
            DECLARE @Total FLOAT = ?;
            DECLARE @OrderDocumentID INT = ?;

            UPDATE docDocumentOrderCayal
               SET CommentsOrder = @CommentsOrder,
                   AddressDetailID = @AddressDetailID,
                   ProductionTypeID = @ProductionTypeID
             WHERE OrderDocumentID = @OrderDocumentID
               AND StatusID IN (1, 2, 3, 4, 11, 12, 13, 16, 17, 18);
            """,
            (
                self._determinar_tipo_orden_produccion(),
                self._documento.comments or '',
                int(self._documento.address_detail_id or 0),
                float(self._documento.total or 0),
                document_id,
            ),
        )
        self._actualizar_comentarios_pedido()

    def _procesar_documento_pedido(self):
        if self._procesando_documento:
            return
        self._procesando_documento = True

        try:
            if not int(self._documento.document_id or 0):
                if not self._documento.items or self._solo_existe_servicio_domicilio():
                    return
                self._documento.document_id = self._crear_cabecera_pedido()
                if not int(self._documento.document_id or 0):
                    raise RuntimeError('No fue posible crear la cabecera del pedido.')
                self.nuevo_pedido = True

            document_id = int(self._documento.document_id)
            self._guardar_partidas(document_id)
            self._guardar_respaldos_partidas(document_id)
            self._guardar_bitacora_partidas(document_id)
            self._actualizar_cabecera(document_id)

        except Exception:
            self._procesando_documento = False
            raise

    def _actualizar_comentarios_pedido(self):
        document_id = int(self._documento.document_id or 0)
        if not document_id:
            return
        self._base_de_datos.command(
            """
            UPDATE docDocumentOrderCayal
               SET CommentsOrder = ?
             WHERE OrderDocumentID = ?
            """,
            (self._documento.comments or '', document_id),
        )
