import tkinter as tk
from cayal.ventanas import Ventanas


class InterfaceDividirFacturas:
    def __init__(self, master):
        self.master = master
        self.ventanas = Ventanas(self.master)
        self._crear_frames()
        self._cargar_componentes()
        self.ventanas.configurar_ventana_ttkbootstrap('Dividir Facturas')


    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.W}),

            'frame_componentes': ('frame_principal', 'Dividir documentos:',
                                  {'row': 1, 'column': 0,'padx': 5, 'pady': 5, 'sticky': tk.W}),
            'frame_tbx': ('frame_componentes', None,
                          {'row': 8, 'column': 0,'columnspan': 2, 'sticky': tk.W}),
            'frame_chk': ('frame_componentes', None,
                              {'row': 9, 'column': 1, 'sticky': tk.W}),

            'frame_factura': ('frame_componentes', 'Documento:',
                              {'row': 10, 'column': 0, 'padx': 5, 'columnspan': 3, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_factura_total': ('frame_factura', None,
                                    {'row': 0, 'column': 0, 'padx': 0, 'pady': 0, 'sticky': tk.EW}),

            'frame_factura_tabla': ('frame_factura', None,
                                    {'row': 1, 'column': 0, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW}),

            'frame_botones': ('frame_componentes', None,
                                  {'row': 11, 'column': 1,  'sticky': tk.NSEW}),

        }

        self.ventanas.crear_frames(frames)

    def _cargar_componentes(self):
        componentes = {
            'tbx_cliente': ('frame_componentes', None, 'Cliente:', None),
            'tbx_folio': ('frame_componentes', None, 'Folio:', None),
            'tbx_tipo_cfd': ('frame_componentes', None, 'Tipo:', None),
            'tbx_total': ('frame_componentes', None, 'Total:', None),
            'txt_comentarios': ('frame_componentes', None, 'Comens:', None),
            'cbx_dividir': ('frame_componentes', None, 'Dividir:', None),
            'tbx_monto': ('frame_tbx', None, 'Monto:               ', None),
            'chk_exacto': ('frame_chk', None, 'Al centavo', None),
            'chk_remisiones': ('frame_chk', None, 'Remisiones', None),
            'tvw_factura': ('frame_factura_tabla', self.columnas(), 10, 'Danger'),

            'btn_dividir': ('frame_botones', None, 'Dividir', None),
            'btn_cancelar': ('frame_botones', 'Danger', 'Cancelar', None),
        }
        self.ventanas.crear_componentes(componentes)
        #self.ventanas.ajustar_ancho_componente('txt_comentarios',35)


    def columnas(self):
        return [
            {"text": "Cantidad", "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.W,
             'hide': 0},
            {"text": "ProductID", "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.W,
             'hide': 1},
            {"text": "Clave", "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.W,
             'hide': 0},
            {"text": "Producto", "stretch": False, 'width': 163, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {"text": "Precio", "stretch": False, 'width': 55, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {"text": "Subtotal", "stretch": False, 'width': 90, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {"text": "Total", "stretch": False, 'width': 90, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {"text": "TaxTypeID", "stretch": False, 'width': 55, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {"text": "ClaveProdServ", "stretch": False, 'width': 55, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {"text": "ClaveUnidad", "stretch": False, 'width': 55, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {"text": "UUID", "stretch": False, 'width': 55, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1}
        ]
