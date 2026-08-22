import tkinter as tk
from cayal.ventanas import Ventanas


class InterfazHistorialQuejas:
    def __init__(self, master):
        self._master = master
        self.ventanas = Ventanas(self._master)

        self._crear_frames()
        self._crear_componentes()
        self._ajustar_componentes()

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
                'Quejas',
                {'row': 0, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            ),

            'frame_componentes': (
                'frame_principal',
                None,
                {'row': 1, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            ),

            'frame_datos_documento': (
                'frame_componentes',
                'Documento',
                {'row': 0, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            ),

            'frame_datos_queja': (
                'frame_componentes',
                'Detalle',
                {'row': 1, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            ),

            'frame_check': (
                'frame_datos_queja',
                None,
                {'row': 10, 'column': 1, 'columnspan':2, 'sticky': tk.SW, 'padx': 5, 'pady': 5}
            ),

            'frame_textos': (
                'frame_componentes',
                'Seguimiento',
                {'row': 3, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            ),


            'frame_botones': (
                'frame_principal',
                None,
                {'row': 4, 'column': 0, 'sticky': tk.W, 'padx': 5, 'pady': 5}
            ),
        }

        self.ventanas.crear_frames(frames)

    def _crear_componentes(self):
        componentes = {
            'tvw_historial': (
                'frame_tabla',
                self.crear_columnas_tabla(),
                None,
                None
            ),

            'tbx_fecha': (
                'frame_datos_documento',
                None,
                'Fecha:',
                None
            ),

            'tbx_documento': (
                'frame_datos_documento',
                None,
                'Documento:',
                None
            ),

            'tbx_cliente': (
                'frame_datos_documento',
                None,
                'Cliente:',
                None
            ),

            'tbx_usuario': (
                'frame_datos_documento',
                None,
                'Usuario:',
                None
            ),

            'tbx_tipo_queja': (
                'frame_datos_queja',
                None,
                'Tipo de Queja:',
                None
            ),

            'tbx_producto': (
                'frame_datos_queja',
                None,
                'Producto:',
                None
            ),

            'tbx_responsable': (
                'frame_datos_queja',
                None,
                'Responsable:',
                None
            ),

            'tbx_area': (
                'frame_datos_queja',
                None,
                'Área:',
                None
            ),

            'tbx_sub_area': (
                'frame_datos_queja',
                None,
                'Sub Área:',
                None
            ),

            'chk_salio': (
                'frame_check',
                None,
                'Salió',
                None
            ),

            'txt_comentario': (
                'frame_textos',
                None,
                'Comentario:',
                None
            ),

            'txt_seguimiento': (
                'frame_textos',
                None,
                'Seguimiento:',
                None
            ),


        }

        self.ventanas.crear_componentes(componentes)

    def _ajustar_componentes(self):
        anchos = {
            'tbx_fecha': 20,
            'tbx_documento': 15,
            'tbx_cliente': 50,
            'tbx_usuario': 25,
            'tbx_tipo_queja': 40,
            'tbx_producto': 50,
            'tbx_responsable': 40,
            'tbx_area': 35,
            'tbx_sub_area': 35,

        }

        for componente, ancho in anchos.items():
            self.ventanas.ajustar_ancho_componente(componente, ancho)

        self.ventanas.ajustar_alto_componente('txt_comentario', 4)
        self.ventanas.ajustar_alto_componente('txt_seguimiento', 4)

    def crear_columnas_tabla(self):
        return [
            {'text': 'Fecha', 'stretch': False, 'width': 70,
             'column_anchor': tk.CENTER, 'heading_anchor': tk.CENTER,
             'hide': 0},

            {'text': 'Documento', 'stretch': False, 'width': 90,
             'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},

            {'text': 'Cliente', 'stretch': False, 'width': 260,
             'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 1},

            {'text': 'Tipo de Queja', 'stretch': False, 'width': 220,
             'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},

            {'text': 'Producto', 'stretch': False, 'width': 180,
             'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 1},

            {'text': 'Responsable', 'stretch': False, 'width': 180,
             'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 1},

            {'text': 'Área', 'stretch': False, 'width': 150,
             'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 1},

            {'text': 'Sub Área', 'stretch': False, 'width': 150,
             'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},

            {'text': 'Usuario', 'stretch': False, 'width': 150,
             'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 1},

            {'text': 'Comentario', 'stretch': False, 'width': 350,
             'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 1},

            {'text': 'Seguimiento', 'stretch': False, 'width': 350,
             'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 1},

            {'text': 'Salió', 'stretch': False, 'width': 60,
             'column_anchor': tk.CENTER, 'heading_anchor': tk.CENTER,
             'hide': 1},

            {'text': 'QuejaID', 'stretch': False, 'width': 80,
             'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},

            {'text': 'UsuarioID', 'stretch': False, 'width': 80,
             'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
        ]

