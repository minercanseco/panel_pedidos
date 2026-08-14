
import tkinter as tk
from cayal.ventanas import Ventanas


class InterfazModificacionesQuejas:
    def __init__(self, master):
        self._master = master
        self.ventanas = Ventanas(self._master)

        self._crear_frames()
        self._crear_tabla()
        self.ventanas.configurar_ventana_ttkbootstrap('Historial de quejas')

    def _crear_frames(self):
        frames = {
            'frame_principal': (
                'master',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW}
            ),

            'frame_tabla': (
                'frame_principal',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            ),

            'frame_componentes': (
                'frame_principal',
                None,
                {'row': 1, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            ),

            'frame_botones': (
                'frame_principal',
                None,
                {'row': 2, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            ),
        }

        self.ventanas.crear_frames(frames)

    def _crear_tabla(self):

        componentes = {
            'tvw_historial':('frame_tabla', self.crear_columnas_tabla(), None, None),
            'txt_valor_anterior': ('frame_componentes', None, 'V.Anterior:', None),
            'txt_valor_nuevo': ('frame_componentes', None, 'V.Nuevo:', None),
        }

        self.ventanas.crear_componentes(componentes)

    def crear_columnas_tabla(self):
        return [
            {'text': 'Fecha', 'stretch': False, 'width': 140,
             'column_anchor': tk.CENTER, 'heading_anchor': tk.CENTER,
             'hide': 0},

            {'text': 'Incidencia', 'stretch': False, 'width': 220,
             'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},

            {'text': 'Usuario', 'stretch': False, 'width': 170,
             'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},

            {'text': 'ValorAnterior', 'stretch': False, 'width': 260,
             'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 1},

            {'text': 'ValorNuevo', 'stretch': False, 'width': 260,
             'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 1},

            {'text': 'DocumentID', 'stretch': False, 'width': 80,
             'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},

            {'text': 'UsuarioID', 'stretch': False, 'width': 80,
             'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
        ]
