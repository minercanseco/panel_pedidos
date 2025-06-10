import tkinter as tk
from cayal.ventanas import Ventanas


class InterfazVerificador:
    def __init__(self, master):
        self.master = master
        self.ventanas =  Ventanas(self.master)
        self._crear_frames()
        self._crear_componentes()
        self._ajustar_componentes()
        self._rellenar_componentes()
        self._agregar_validaciones()
        self.configurar_posicion_frames()

        self.ventanas.configurar_ventana_ttkbootstrap(titulo='Verificador de precios')
        self.ventanas.enfocar_componente('tbx_buscar')

    def _crear_frames(self):

        frames = {
            'frame_principal': ('master', 'Verificador de precios',
                                {'row': 0, 'column': 0, 'pady': 5, 'padx': 5,'sticky': tk.NSEW}),

            'frame_componentes': ('frame_principal', None,
                               {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                'sticky': tk.NSEW}),

            'frame_busqueda': ('frame_componentes', None,
                                  {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                   'sticky': tk.NSEW}),

            'frame_chk_busqueda': ('frame_busqueda', None,
                               {'row': 0, 'column': 2,  'pady': 2, 'padx': 2,
                                'sticky': tk.NSEW}),

            'frame_cantidad': ('frame_componentes', None,
                               {'row': 4, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                'sticky': tk.NSEW}),

            'frame_chk_monto': ('frame_cantidad', None,
                                   {'row': 4, 'column': 2, 'pady': 2, 'padx': 2,
                                    'sticky': tk.NSEW}),


            'frame_botones': ('frame_principal', None,
                                 {'row': 5, 'column': 0,  'pady': 2, 'padx': 2,
                                  'sticky': tk.NSEW}),

            'frame_etiqueta_producto': ('frame_principal', None,
                              {'row': 6, 'column': 0, 'columnspan': 2, 'pady': 0, 'padx': 0,
                               'sticky': tk.NSEW}),

            'frame_detalles_oferta': ('frame_principal', None,
                              {'row': 7, 'column': 0, 'columnspan': 2, 'pady': 0, 'padx': 0,
                               'sticky': tk.NSEW}),

            'frame_detalles': ('frame_principal', None,
                               {'row': 8, 'column': 0, 'columnspan': 2, 'pady': 0, 'padx': 0,
                                'sticky': tk.NSEW}),
        }
        self.ventanas.crear_frames(frames)

    def _crear_componentes(self):
        estilo_lbl_roja = {
            'width': 44,
            'foreground': 'white',
            'background': '#E30421',
            'font': ('consolas', 12, 'bold'),
            'anchor': 'center'
        }

        estilo_lbl_azul = {
            'width': 22,
            'foreground': 'white',
            'background': '#2A569A',
            'font': ('consolas', 25, 'bold'),
            'anchor': 'center'
        }

        estilo_lbl_naranja = {
            'width': 22,
            'foreground': 'white',
            'background': '#FE7F00',
            'font': ('consolas', 25, 'bold'),
            'anchor': 'center'
        }

        componentes = {

            'tbx_buscar': ('frame_busqueda', None, 'Buscar:', None),
            'chk_linea': ('frame_chk_busqueda', None, None, None),

            'cbx_resultado': ('frame_componentes', None, 'Result: ', None),
            'cbx_lista': ('frame_componentes', None, 'Lista:', None),

            'tbx_cantidad': ('frame_cantidad', None, 'Cant.:  ', None),
            'chk_monto': ('frame_chk_monto', None, None, None),

            'btn_copiar': ('frame_botones', 'PRIMARY', 'Copiar', None),
            'chk_copiar': ('frame_botones', None, 'Todo', None),
            'btn_ofertas': ('frame_botones', 'DANGER', 'Ofertas', None),
            'btn_info': ('frame_botones', 'INFO', 'Info', None),

            'lbl_producto': ('frame_etiqueta_producto',
                                estilo_lbl_roja,
                                {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                None),

            'lbl_precio': ('frame_detalles',
                             estilo_lbl_azul,
                             {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                             None),

            'lbl_clave': ('frame_detalles',
                               estilo_lbl_azul,
                               {'row': 1, 'column': 0, 'columnspan': 2, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                               None),

            'lbl_existencia': ('frame_detalles',
                             estilo_lbl_azul,
                             {'row': 2, 'column': 0, 'columnspan': 2, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                             None),

            'lbl_existencia_texto': ('frame_detalles',
                             estilo_lbl_azul,
                             {'row': 3, 'column': 0, 'columnspan': 2, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                             None),

            'lbl_oferta_texto': ('frame_detalles_oferta',
                                     estilo_lbl_naranja,
                                     {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                     None),
            'lbl_tipo_oferta': ('frame_detalles_oferta',
                                 estilo_lbl_naranja,
                                 {'row': 1, 'column': 0, 'columnspan': 2, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                 None),
            'lbl_validez_oferta': ('frame_detalles_oferta',
                                estilo_lbl_naranja,
                                {'row': 2, 'column': 0, 'columnspan': 2, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                None),
            'lbl_precio_oferta': ('frame_detalles_oferta',
                                   estilo_lbl_naranja,
                                   {'row': 3, 'column': 0, 'columnspan': 2, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                   None),
        }

        self.ventanas.crear_componentes(componentes)

    def _ajustar_componentes(self):
        self.ventanas.ajustar_ancho_componente('tbx_buscar', 20)
        self.ventanas.ajustar_ancho_componente('tbx_cantidad', 10)
        self.ventanas.ajustar_ancho_componente('cbx_resultado', 60)
        self.ventanas.ajustar_ancho_componente('cbx_lista', 10)

        self.ventanas.ajustar_label_en_frame('lbl_producto', 'frame_etiqueta_producto')
        self.ventanas.ajustar_label_en_frame('lbl_precio', 'frame_detalles')
        self.ventanas.ajustar_label_en_frame('lbl_oferta_texto', 'frame_detalles_oferta')

        etiquetas = ['lbl_tipo_oferta', 'lbl_validez_oferta']
        for etiqueta in etiquetas:
            componente = self.ventanas.componentes_forma[etiqueta]
            componente.config(font=('consolas', 12, 'bold'))

    def _rellenar_componentes(self):
        self.ventanas.insertar_input_componente('lbl_existencia_texto', 'EXISTENCIA')
        self.ventanas.insertar_input_componente('lbl_oferta_texto', 'OFERTA')

    def configurar_posicion_frames(self, estado='inicial'):

        def _posicion_inicial():
            self.ventanas.ocultar_frame('frame_etiqueta_producto')
            self.ventanas.ocultar_frame('frame_detalles')
            self.ventanas.ocultar_frame('frame_detalles_oferta')

        if estado == 'inicial':
            _posicion_inicial()

        if estado == 'oferta':
            _posicion_inicial()
            self.ventanas.posicionar_frame('frame_etiqueta_producto')
            self.ventanas.posicionar_frame('frame_detalles')
            self.ventanas.posicionar_frame('frame_detalles_oferta')

        if estado == 'producto':
            _posicion_inicial()
            self.ventanas.posicionar_frame('frame_etiqueta_producto')
            self.ventanas.posicionar_frame('frame_detalles')

        self.ventanas.configurar_ventana_ttkbootstrap(titulo='Verificador de precios')

    def _agregar_validaciones(self):
        self.ventanas.agregar_validacion_tbx('tbx_cantidad', 'cantidad')