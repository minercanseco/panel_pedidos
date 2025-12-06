import tkinter as tk
from cayal.ventanas import Ventanas


class HistorialPedido:
    def __init__(self, master, parametros, base_de_datos):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._base_de_datos = base_de_datos
        self._ventanas.configurar_ventana_ttkbootstrap('Historial pedido')

        self._consulta_log_pedido = []
        self._info_pedido = None
        self._order_document_id = parametros.id_principal

        self._crear_componentes_forma()
        self._buscar_log_pedido()
        self._buscar_info_pedido()
        self._rellenar_componentes()
        self._cargar_eventos()
        self._ventanas.centrar_ventana_ttkbootstrap(self._master)

    def _crear_componentes_forma(self):
        componentes = [
            ('tbx_cliente', 'Cliente:'),
            ('tbx_folio', 'Folio:'),
            ('den_fecha', 'Fecha:'),
            ('txt_comentario', 'Comentario:'),
            ('tvw_historial', self._crear_columnas()),
            ('btn_guardar', 'Guardar'),
        ]
        self._ventanas.crear_formulario_simple(componentes)

        self._ventanas.ajustar_ancho_componente('tbx_cliente', 46)

    def _cargar_eventos(self):
        eventos = {
            'btn_guardar': self._master.destroy,
            'btn_cancelar': self._master.destroy,
            'tvw_historial': (lambda event: self._seleccionar_fila(), 'seleccion')
        }
        self._ventanas.cargar_eventos(eventos)

    def _crear_columnas(self):
        return [
            {'text': 'Evento', "stretch": False, 'width': 150, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'Comentario', "stretch": False, 'width': 320, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'Fecha', "stretch": False, 'width': 80, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'Hora', "stretch": False, 'width': 70, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'Usuario', "stretch": False, 'width': 80, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
        ]

    def _buscar_log_pedido(self):
        self._consulta_log_pedido = self._base_de_datos.fetchall("""
                                SELECT 
                                    LO.ChangeType,
                                    LO.ChangeDetails,
                                    CAST(LO.CreatedOn as date) CreatedOn,
                                    dbo.FORMAT(LO.CreatedOn, N'HH:mm') AS Hora,
                                    U.UserName
                                FROM CayalOrdersChangeLog LO INNER JOIN
                                    engUser U ON LO.CreatedBy = U.UserID
                                WHERE LO.OrderDocumentID = ?
                            """, (self._order_document_id,))

    def _buscar_info_pedido(self):
        consulta = self._base_de_datos.buscar_info_documento_pedido_cayal(self._order_document_id)
        if consulta:
            self._info_pedido = consulta[0]

    def _rellenar_componentes(self):
        self._ventanas.insertar_input_componente('tbx_cliente', self._info_pedido['OfficialName'])
        self._ventanas.insertar_input_componente('tbx_folio', self._info_pedido['DocFolio'])
        self._ventanas.insertar_input_componente('den_fecha', self._info_pedido['CreatedOn'])

        self._ventanas.rellenar_treeview('tvw_historial',
                                         self._crear_columnas(),
                                         self._consulta_log_pedido,
                                         valor_barra_desplazamiento=3)

        self._ventanas.bloquear_componente('tbx_cliente')
        self._ventanas.bloquear_componente('tbx_folio')
        self._ventanas.bloquear_componente('den_fecha')

    def _seleccionar_fila(self, event=None):
        if self._ventanas.validar_seleccion_una_fila_treeview('tvw_historial'):
            fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_historial')
            valores = self._ventanas.procesar_fila_treeview('tvw_historial', fila)
            comentario = valores['Comentario']
            self._ventanas.insertar_input_componente('txt_comentario', comentario)


