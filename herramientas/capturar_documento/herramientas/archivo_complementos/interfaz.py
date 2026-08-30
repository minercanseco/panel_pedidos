
import tkinter as tk

from cayal.ventanas import Ventanas


class Interfaz:
    def __init__(self, master):
        self._master = master
        self.ventanas = Ventanas(master)
        self.columnas = self._crear_columnas()
        self._crear_frames()
        self._crear_componentes()
        #self._ajustar_layout()
        self.ventanas.configurar_ventana_ttkbootstrap(
            titulo='Archivo de complementos de pago',
            nombre_icono='Finance32.ico',
        )

    @staticmethod
    def _crear_columnas():
        datos = [
            ('Num', 210, tk.W,0),
            ('Fecha', 105, tk.CENTER,0),
            ('Usuario', 105, tk.CENTER, 0)
        ]
        return [
            {'text': nombre, 'stretch': nombre == 'CobradoEn', 'width': ancho,
             'column_anchor': ancla, 'heading_anchor': ancla, 'hide': oculto}
            for nombre, ancho, ancla, oculto in datos
        ]

    def _crear_frames(self):
        self.ventanas.crear_frames({
            'frame_principal': ('master', None, {'row': 0, 'column': 0, 'sticky': tk.NSEW}),
            'frame_filtros': ('frame_principal', 'Rango de timbrado',
                              {'row': 0, 'column': 0, 'sticky': tk.EW, 'padx': 8, 'pady': (8, 4)}),
            'frame_tabla': ('frame_principal', 'Complementos',
                            {'row': 1, 'column': 0, 'sticky': tk.NSEW, 'padx': 8, 'pady': 4}),
            'frame_estado': ('frame_principal', None,
                             {'row': 2, 'column': 0, 'sticky': tk.EW, 'padx': 8}),
            'frame_botones': ('frame_principal', None,
                              {'row': 3, 'column': 0, 'sticky': tk.E, 'padx': 8, 'pady': (4, 8)}),
        })

    def _crear_componentes(self):
        self.ventanas.crear_componentes({
            'den_fecha_inicial': ('frame_filtros',
                                  {'row': 0, 'column': 1, 'sticky': tk.W, 'padx': 5, 'pady': 5},
                                  'Desde:', None),
            'den_fecha_final': ('frame_filtros',
                                {'row': 0, 'column': 3, 'sticky': tk.W, 'padx': 5, 'pady': 5},
                                'Hasta:', None),
            'tvw_complementos': ('frame_tabla', self.columnas, 18, 'primary'),
            'lbl_estado': ('frame_estado', {'text': '0 complementos', 'anchor': tk.W},
                           {'row': 0, 'column': 0, 'sticky': tk.EW}, None),
            'btn_imprimir': ('frame_botones', 'primary', 'Imprimir', None),
            'btn_cancelar': ('frame_botones', 'danger', 'Cancelar', None),
        })

    def _ajustar_layout(self):
        self.ventanas.ajustar_componente_en_frame('tvw_complementos', 'frame_tabla', expandir=True)
        self.ventanas.ajustar_label_en_frame('lbl_estado', 'frame_estado')
