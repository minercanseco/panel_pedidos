import tkinter as tk
from cayal.ventanas import Ventanas

class CapturadoVsProducido:
    def __init__(self, master, parametros, base_de_datos, utilerias):
        self._master = master
        self._parametros = parametros
        self._order_document_id = self._parametros.id_principal

        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._ventanas = Ventanas(self._master)

        self._partidas_capturadas = []
        self._partidas_editadas = []
        self._partidas_producidas = []

        self._crear_frames()
        self._crear_componetes()
        self._rellenar_tablas()
        self._ventanas.configurar_ventana_ttkbootstrap()

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_componentes': ('frame_principal', None,
                                  {'row': 0, 'column': 0, 'pady': 2, 'padx': 2,
                                   'sticky': tk.NSEW}),

            'frame_comentario': ('frame_componentes', 'Comentario',
                                 {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                  'sticky': tk.NSEW}),

            'frame_tabla1': ('frame_componentes', 'Remisión',
                             {'row': 1, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                              'sticky': tk.NSEW}),

            'frame_total1': ('frame_tabla1', 'Total Remisión',
                             {'row': 1, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                              'sticky': tk.NSEW}),

            'frame_tabla2': ('frame_componentes', 'Factura',
                             {'row': 2, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                              'sticky': tk.NSEW}),

            'frame_total2': ('frame_tabla2', 'Total Factura:',
                             {'row': 1, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                              'sticky': tk.NSEW}),

            'frame_monto': ('frame_componentes', None,
                            {'row': 3, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                             'sticky': tk.NSEW}),

            'frame_botones': ('frame_monto', None,
                              {'row': 5, 'column': 1, 'padx': 0, 'pady': 5, 'sticky': tk.W}),

        }
        self._ventanas.crear_frames(frames)

    def _crear_componetes(self):
        componentes = {
            'txt_comentario': ('frame_comentario', None, ' ', None),
            'tbx_total_pedido': ('frame_total1',
                                   {'row': 0, 'column': 1, 'pady': 2, 'padx': 2, 'sticky': tk.NE},
                                   ' ', None),
            'tvw_pedido': ('frame_tabla1', self._crear_columnas_tabla(), 10, None),
            'tbx_total_producido': ('frame_total2',
                                  {'row': 0, 'column': 1, 'pady': 2, 'padx': 2, 'sticky': tk.NE},
                                  ' ', None),
            'tvw_producido': ('frame_tabla2', self._crear_columnas_tabla(), 10, 'danger'),
        }
        self._ventanas.crear_componentes(componentes)

        self._ventanas.ajustar_componente_en_frame('txt_comentario', 'frame_comentario')

    def _crear_columnas_tabla(self):
        return [
            {'text': 'N', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E, 'hide': 1},
            {'text': 'Cantidad', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {'text': 'Clave', "stretch": False, 'width': 110, 'column_anchor': tk.W, 'heading_anchor': tk.W, 'hide': 0},
            {'text': 'Producto', "stretch": False, 'width': 260, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'Precio', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E, 'hide': 0},
            {'text': 'Subtotal', "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {'text': 'TaxTypeID', "stretch": False, 'width': 0, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {'text': 'ProductID', "stretch": False, 'width': 0, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {'text': 'ClaveUnidad', "stretch": False, 'width': 0, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {'text': 'Impuestos', "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {'text': 'Total', "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E, 'hide': 0},
            {'text': 'DocumentItemID', "stretch": False, 'width': 0, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1}
        ]

    def _rellenar_tablas(self):
        self._consultar_info_partidas()

        print(self._partidas_capturadas, self._partidas_editadas, self._partidas_producidas)

    def _consultar_info_partidas(self):
        self._partidas_capturadas = self._base_de_datos.fetchall("""
                            DECLARE @OrderDocumentID INT = ?
                            SELECT * FROM [dbo].[zvwBuscarPartidasPedidoCayal-DocumentID](@OrderDocumentID)
                            """, (self._order_document_id,))

        self._partidas_editadas = self._base_de_datos.fetchall("""
                            DECLARE @OrderDocumentID INT = ?
                            SELECT * FROM [dbo].[zvwBuscarPartidasPedidoCayalExtra-DocumentID](@OrderDocumentID)
                            """, (self._order_document_id,))

        self._partidas_producidas = self._base_de_datos.fetchall("""
                            DECLARE @OrderDocumentID INT = ?
                            SELECT * FROM [dbo].[zvwBuscarPartidasFinalizadasPedidoCayal-DocumentID](@OrderDocumentID)
                            """, (self._order_document_id,))

