import tkinter as tk
from cayal.ventanas import Ventanas


class InterfazCobroRapido:
    def __init__(self, master):
        self.master = master
        self.ventanas = Ventanas(self.master)

        self._crear_frames()
        self._cargar_componentes_forma()
        self._rellenar_etiquetas()
        self._ajustar_etiquetas()
        self._agregar_validaciones()


        self.ventanas.configurar_ventana_ttkbootstrap("Cobro rápido")

    def _crear_frames(self):

        self._frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_info': ('frame_principal', None,
                           {'row': 0, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW}),

            'frame_cambio': ('frame_principal', None,
                             {'row': 1, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW}),

            'frame_restante': ('frame_principal', None,
                               {'row': 2, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW}),

            'frame_cobro': ('frame_principal', None,
                            {'row': 3, 'column': 0, 'columnspan': 2, 'pady': 5, 'sticky': tk.W}),

            'frame_monto': ('frame_principal', None,
                            {'row': 4, 'column': 0, 'columnspan': 2, 'sticky': tk.W}),

            'frame_tarjeta': ('frame_principal', None,
                              {'row': 5, 'column': 0, 'columnspan': 2, 'sticky': tk.W}),


            'frame_herramientas': ('frame_principal', None,
                              {'row': 6, 'column': 1, 'padx': 25, 'pady': 5, 'sticky': tk.E}),

            'frame_tabla_dividido': ('frame_principal', None,
                                     {'row': 7, 'column': 1, 'padx': 5, 'columnspan': 2, 'sticky': tk.NSEW}),
        }

        self.ventanas.crear_frames(self._frames)

    def _cargar_componentes_forma(self):

        estilo_auxiliar_danger = {
            'foreground': 'white',
            'background': '#E30421',
            'font': ('Consolas', 16, 'bold'),
            'text': '$0.00',
            'anchor': 'center'
        }

        estilo_auxiliar_warning = {
            'bootstyle':'inverse-warning',
            'font': ('Consolas', 16, 'bold'),
            'text': '$0.00',
            'anchor': 'center'
        }

        estilo_total_danger = {
            'foreground': 'white',
            'background': '#E30421',
            'font': ('consolas', 29, 'bold'),
            'text': '$0.00',
            'anchor': 'center'
        }

        estilo_total_warning = {
            'bootstyle':'inverse-warning',
            'font': ('consolas', 29, 'bold'),
            'text': '$0.00',
            'anchor': 'center'
        }

        posicion = {
            'sticky': tk.NSEW, 'pady':0, 'padx':0,
        }


        componentes = {
            'lbl_saldo_texto': ('frame_info', estilo_auxiliar_danger, posicion, None),
            'lbl_saldo': ('frame_info', estilo_total_danger, posicion, None),
            'lbl_cambio_texto': ('frame_cambio', estilo_auxiliar_danger, posicion, None),
            'lbl_cambio': ('frame_cambio', estilo_total_danger, posicion, None),
            'lbl_restante_texto': ('frame_restante', estilo_auxiliar_warning, posicion, None),
            'lbl_restante': ('frame_restante', estilo_total_warning, posicion, None),

            'cbx_tipo': ('frame_cobro', None, 'F.Cobro', None),
            'tbx_monto_cobro': ('frame_monto', None, 'Monto:', None),
            'tbx_recibido': ('frame_monto', None, 'Recibido:', None),
            'lbl_banco': ('frame_tarjeta', estilo_auxiliar_danger,
                          {
                             'columnspan':2, 'column':0, 'sticky': tk.NSEW, 'pady': 0, 'padx': 0,
                          }
                          ,None),
            'tbx_barcode': ('frame_tarjeta', None, 'C.Barras:', None),
            'cbx_terminal': ('frame_tarjeta', None, 'Terminal:', None),

            'tvw_cobros': ('frame_tabla_dividido', self._crear_columnas_tabla(), None, None)
        }

        self.ventanas.crear_componentes(componentes)

    def _crear_columnas_tabla(self):
        return [
                {'text': 'Monto', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                 'hide': 0},
                {'text': 'Forma de Pago', "stretch": False, 'width': 185, 'column_anchor': tk.W, 'heading_anchor': tk.W,
                 'hide': 0},
                {'text': 'Restante', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                 'hide': 1},
                {'text': 'FinancialEntityID', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                 'hide': 1},
                {'text': 'Afiliacion', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                 'hide': 1},
                {'text': 'Barcode', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                 'hide': 1},
                {'text': 'PaymentMethodID', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                'hide': 1}
                ]

    def _ajustar_etiquetas(self):
        self.ventanas.ajustar_label_en_frame('lbl_saldo', 'frame_info')
        self.ventanas.ajustar_label_en_frame('lbl_restante', 'frame_restante')
        self.ventanas.ajustar_label_en_frame('lbl_cambio_texto', 'frame_cambio')
        self.ventanas.ajustar_label_en_frame('lbl_banco', 'frame_tarjeta')

    def _rellenar_etiquetas(self):
        self.ventanas.insertar_input_componente('lbl_saldo_texto', 'Saldo')
        self.ventanas.insertar_input_componente('lbl_restante_texto', 'Crédito restante')
        self.ventanas.insertar_input_componente('lbl_cambio_texto', 'Cambio')
        self.ventanas.insertar_input_componente('lbl_banco', 'Banco')

    def _agregar_validaciones(self):
        self.ventanas.agregar_validacion_tbx('tbx_monto_cobro', 'cantidad')
        self.ventanas.agregar_validacion_tbx('tbx_barcode', 'cantidad')
        self.ventanas.agregar_validacion_tbx('tbx_recibido', 'cantidad')