from cayal.ventanas import Ventanas


class CancelarPedido:
    def __init__(self, master, parametros_contpaqi, base_de_datos):
        self._master = master

        self._ventanas = Ventanas(self._master)
        self._parametros = parametros_contpaqi
        self._base_de_datos = base_de_datos

        self._user_id = self._parametros.id_usuario
        self._order_document_id = self._parametros.id_principal
        self._info_pedido = None
        self._consulta_motivos_cancelacion = []

        self._ventanas.configurar_ventana_ttkbootstrap('Cancelar pedido')

        self._crear_componentes_forma()
        self._cargar_eventos()
        self._buscar_info_pedido()
        self._buscar_motivos_cancelacion()
        self._rellenar_componentes_forma()

    def _crear_componentes_forma(self):
        componentes = [
            ('tbx_cliente', 'Cliente:'),
            ('tbx_folio', 'Folio:'),
            ('den_fecha', 'Fecha:'),
            ('cbx_motivos', 'Motivo:'),
            ('txt_comentario', 'Comentario:'),
            ('btn_guardar', 'Guardar'),
        ]
        self._ventanas.crear_formulario_simple(componentes)

        self._ventanas.ajustar_ancho_componente('tbx_cliente', 46)

    def _cargar_eventos(self):
        eventos = {
            'btn_guardar': self._guardar_cancelacion,
            'btn_cancelar': self._master.destroy
        }
        self._ventanas.cargar_eventos(eventos)

    def _buscar_info_pedido(self):
        consulta = self._base_de_datos.buscar_info_documento_pedido_cayal(self._order_document_id)
        if consulta:
            self._info_pedido = consulta[0]

    def _buscar_motivos_cancelacion(self):
        self._consulta_motivos_cancelacion = self._base_de_datos.fetchall(
            'SELECT ID, Value FROM OrderCancelReasons WHERE Status = 0',
            ()
        )

    def _pedido_esta_cancelado(self):

        cancelado = self._info_pedido['CancelledOn']

        if not cancelado:
            return False

        return True

    def _rellenar_componentes_forma(self):
        self._ventanas.insertar_input_componente('tbx_cliente', self._info_pedido['OfficialName'])
        self._ventanas.insertar_input_componente('tbx_folio', self._info_pedido['DocFolio'])
        self._ventanas.insertar_input_componente('den_fecha', self._info_pedido['CreatedOn'])

        motivos_cancelacion = [motivo['Value'] for motivo in self._consulta_motivos_cancelacion]
        motivos_cancelacion.sort()
        self._ventanas.rellenar_cbx('cbx_motivos', motivos_cancelacion)

        componentes = ['tbx_cliente', 'tbx_folio', 'den_fecha']
        for componente in componentes:
            self._ventanas.bloquear_componente(componente)

        if self._pedido_esta_cancelado():
            cancelled_comment = self._info_pedido['CancelledComment']
            self._ventanas.insertar_input_componente('txt_comentario', cancelled_comment)

            cancelled_reason = self._info_pedido['CancelledReason']
            self._ventanas.insertar_input_componente('cbx_motivos', cancelled_reason)

            self._ventanas.bloquear_componente('txt_comentario')
            self._ventanas.bloquear_componente('cbx_motivos')
            self._ventanas.bloquear_componente('btn_guardar')



    def _validar_inputs_componentes(self):
        motivo_cancelacion = self._ventanas.obtener_input_componente('cbx_motivos')
        comentario_cancelacion = self._ventanas.obtener_input_componente('txt_comentario')

        if motivo_cancelacion == 'Seleccione':
            self._ventanas.mostrar_mensaje('Debe seleccionar un motivo de cancelación.')
            return

        if not comentario_cancelacion:
            self._ventanas.mostrar_mensaje('Debe proporcionar un comentario para la cancelación del pedido.')
            return

        if len(comentario_cancelacion) < 10:
            self._ventanas.mostrar_mensaje('Debe abundar en el comentario de la cancelación del pedido.')
            return

        return True

    def _actualizar_base_de_datos(self, parametros):

        if self._info_pedido['UserID'] != 0:
            nombre_usuario = self._base_de_datos.buscar_nombre_de_usuario(self._info_pedido['UserID'])
            self._ventanas.mostrar_mensaje(f'El documento está en uso por {nombre_usuario}.')
            self._master.destroy()

        self._base_de_datos.marcar_documento_en_uso(self._order_document_id,
                                                    self._user_id,
                                                    pedido=True
                                                    )
        self._base_de_datos.command("""
            DECLARE @OrderDocumentID INT = ?
            DECLARE @UserID INT = ?
            DECLARE @CancelledComment NVARCHAR(MAX) = ?
            DECLARE @CancelledReasonID INT = ?
            
            UPDATE docDocumentOrderCayal SET CancelledOn = GETDATE(),
                                            CancelledBy = @UserID,
                                            CancelledComment = @CancelledComment,
                                            CancelledReasonID = @CancelledReasonID,
                                            StatusID = 10
                            WHERE OrderDocumentID = @OrderDocumentID
        """, (parametros[0],
              parametros[1],
              parametros[2],
              parametros[3]
              ))

        self._base_de_datos.insertar_registro_bitacora_pedidos(
            order_document_id=self._order_document_id,
            change_type_id=10,
            user_id=self._user_id,
            comments=parametros[2]
        )

    def _guardar_cancelacion(self):
        if self._validar_inputs_componentes():
            cancelled_reason = self._ventanas.obtener_input_componente('cbx_motivos')
            cancelled_reason_id = [motivo['ID'] for motivo in self._consulta_motivos_cancelacion
                                   if motivo['Value'] == cancelled_reason][0]
            cancelled_comment = self._ventanas.obtener_input_componente('txt_comentario').upper()
            parametros = (
                self._order_document_id,
                self._user_id,
                cancelled_comment,
                cancelled_reason_id
            )

            self._actualizar_base_de_datos(parametros)

            self._master.destroy()
