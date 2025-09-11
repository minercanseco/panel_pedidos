import tkinter as tk
from cayal.ventanas import Ventanas


class InterfazSaldarCartera:
    def __init__(self, master):

        self.master = master
        self.ventanas = Ventanas(self.master)

        self._crear_frames()
        self._cargar_componentes_forma()
        self._agregar_validaciones_tbx()
        self.ventanas.ocultar_frame('frame_cambio')
        self.ventanas.ocultar_frame('frame_terminal')
        self.ventanas.configurar_ventana_ttkbootstrap('Saldar cartera')
        self.ventanas.situar_ventana_arriba(self.master)

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', 'Cobrar cartera',
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),  # <- NSEW

            'frame_datos_generales': ('frame_principal', None,
                                      {'row': 0, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.W}),

            'frame_datos': ('frame_datos_generales', None,
                            {'row': 0, 'column': 0, 'columnspan': 2, 'padx': 2, 'pady': 5, 'sticky': tk.W}),

            'frame_cambio': ('frame_datos_generales', None,
                             {'row': 1, 'column': 0, 'padx': 12, 'pady': 5, 'sticky': tk.W}),

            'frame_terminal': ('frame_datos_generales', None,
                               {'row': 2, 'column': 0, 'padx': 12, 'pady': 5, 'sticky': tk.W}),

            'frame_herramientas': ('frame_principal', 'Opciones',
                                      {'row': 1, 'column': 0, 'columnspan': 3, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_chk': ('frame_herramientas', None,
                               {'row': 1, 'column': 3, 'padx': 5, 'pady': 5, 'sticky': tk.W}),

            'frame_botones_aplicar': ('frame_herramientas', None,
                                      {'row': 1, 'column': 0, 'columnspan': 2, 'padx': 5, 'pady': 5, 'sticky': tk.W}),

            'frame_tabla': ('frame_principal', 'Documentos',
                            {'row': 2, 'column': 0, 'columnspan': 3, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_acciones': ('frame_principal', None,
                               {'row': 3, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.W}),

            'frame_totales': ('frame_principal', None,
                              {'row': 0, 'column': 2, 'columnspan': 1, 'sticky': tk.NE}),

        }

        self.ventanas.crear_frames(frames)

    def _cargar_componentes_forma(self):
        componentes = {
            'den_fecha_afectacion': ('frame_datos', None, 'Fecha:', None),
            'cbx_forma_cobro': ('frame_datos', None, 'F.Cobro:', None),
            'cbx_modalidad_cobro': ('frame_datos', None, 'Modalidad:', None),
            'tbx_monto': ('frame_datos', None, 'Monto:', None),
            'tbx_recibido': ('frame_cambio', None, 'Recibido:', None),
            'lbl_banco': ('frame_terminal',  {'anchor': 'center',
                }, {'row': 0, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW, }, None),
            'tbx_terminal': ('frame_terminal', None, 'Barcode:', None),
            'cbx_terminal': ('frame_terminal', None, 'Terminal:', None),
            'chk_cerrar': ('frame_chk', None, 'No cerrar al cobrar', None),
            'tvw_tabla_documentos': ('frame_tabla', self._columnas_tabla(), 10, None),
        }

        self.ventanas.crear_componentes(componentes)
        self._rellenar_frame_totales()

    def _rellenar_frame_totales(self):
        estilo_rojo = {
            'foreground': 'white',
            'background': '#E30421',
            'font': ('Consolas', 20, 'bold'),
        }

        componentes = {
            'lbl_nombre_cliente': ('frame_totales', estilo_rojo,
                                   {'row': 0, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW}, None),

            'lbl_cartera_txt': ('frame_totales', estilo_rojo, {'row': 1, 'column': 0, 'sticky': tk.NSEW}, None),
            'lbl_monto_txt':   ('frame_totales', estilo_rojo, {'row': 2, 'column': 0, 'sticky': tk.NSEW}, None),
            'lbl_restante_txt':('frame_totales', estilo_rojo, {'row': 3, 'column': 0, 'sticky': tk.NSEW}, None),
            'lbl_cambio_txt':  ('frame_totales', estilo_rojo, {'row': 4, 'column': 0, 'sticky': tk.NSEW}, None),

            'lbl_cartera':  ('frame_totales', estilo_rojo, {'row': 1, 'column': 1, 'sticky': tk.NSEW}, None),
            'lbl_monto':    ('frame_totales', estilo_rojo, {'row': 2, 'column': 1, 'sticky': tk.NSEW}, None),
            'lbl_restante': ('frame_totales', estilo_rojo, {'row': 3, 'column': 1, 'sticky': tk.NSEW}, None),
            'lbl_cambio':   ('frame_totales', estilo_rojo, {'row': 4, 'column': 1, 'sticky': tk.NSEW}, None),
        }
        self.ventanas.crear_componentes(componentes)

        # Textos por defecto (como en la captura)
        self.ventanas.insertar_input_componente('lbl_nombre_cliente', 'CLIENTE')
        self.ventanas.insertar_input_componente('lbl_cartera_txt', 'CARTERA:')
        self.ventanas.insertar_input_componente('lbl_monto_txt',   'MONTO:')
        self.ventanas.insertar_input_componente('lbl_restante_txt','RESTANTE:')
        self.ventanas.insertar_input_componente('lbl_cambio_txt',  'CAMBIO:')

        self.ventanas.insertar_input_componente('lbl_cartera',  '$0.00')
        self.ventanas.insertar_input_componente('lbl_monto',    '$0.00')
        self.ventanas.insertar_input_componente('lbl_restante', '$0.00')
        self.ventanas.insertar_input_componente('lbl_cambio',   '$0.00')

    def _columnas_tabla(self):
         return [
            {'text': 'N', "stretch": False, 'width': 30, 'column_anchor': tk.E, 'heading_anchor': tk.E, 'hide': 0},
            {"text": "Fecha", "stretch": False, 'width': 90, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {"text": "Tipo", "stretch": False, 'width': 80, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {"text": "Folio", "stretch": False, 'width': 90, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {"text": "FP", "stretch": False, 'width': 30, 'column_anchor': tk.W, 'heading_anchor': tk.W, 'hide': 0},
            {"text": "Total", "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {"text": "Pagado", "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {"text": "Saldo", "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {"text": "Sucursal", "stretch": False, 'width': 90, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {"text": "DocumentID", "stretch": False, 'width': 0, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
             {"text": "OrderDocumentID", "stretch": False, 'width': 0, 'column_anchor': tk.E, 'heading_anchor': tk.E,
              'hide': 1},
             {"text": "BusinessEntityID", "stretch": False, 'width': 0, 'column_anchor': tk.E, 'heading_anchor': tk.E,
              'hide': 1},
             {"text": "LiquidationID", "stretch": False, 'width': 0, 'column_anchor': tk.E, 'heading_anchor': tk.E,
              'hide': 1},
             {"text": "LiquidationStatus", "stretch": False, 'width': 0, 'column_anchor': tk.E, 'heading_anchor': tk.E,
              'hide': 1}
        ]

    def _agregar_validaciones_tbx(self):
        self.ventanas.agregar_validacion_tbx('tbx_terminal', 'cantidad')
        self.ventanas.agregar_validacion_tbx('tbx_monto', 'cantidad')
        self.ventanas.agregar_validacion_tbx('tbx_recibido', 'cantidad')

    def ajustar_apariencia_terminal(self):
        seleccion = self.ventanas.obtener_input_componente('cbx_forma_cobro')
        tipo = seleccion[0:2]

        if tipo == '01':
            self.ventanas.posicionar_frame('frame_cambio')
            self.ventanas.ocultar_frame('frame_terminal')

            self.ventanas.limpiar_componentes(['tbx_terminal', 'cbx_terminal'])
        if tipo in ('04', '28'):
            self.ventanas.ocultar_frame('frame_cambio')
            self.ventanas.posicionar_frame('frame_terminal')
            self.ventanas.limpiar_componentes(['tbx_terminal', 'cbx_terminal', 'lbl_banco'])
            self.ventanas.insertar_input_componente('lbl_banco', 'BANCO')

        if tipo not in ('01', '04', '28') or seleccion == 'Seleccione':
            self.ventanas.ocultar_frame('frame_cambio')
            self.ventanas.ocultar_frame('frame_terminal')
            self.ventanas.limpiar_componentes(['tbx_terminal', 'cbx_terminal'])

        self.ventanas.refrescar_tamano_forma()

    def rellenar_tabla(self, consulta):
        self.ventanas.rellenar_treeview('tvw_tabla_documentos', self._columnas_tabla(), consulta)

    def actualizar_color_etiquetas(self, estado):

        naranja = "#FFA500"
        rojo = '#E30421'
        color = naranja if estado == 'bloqueo'else rojo

        for clave, valor in self.ventanas.componentes_forma.items():
            if clave[0:3] == 'lbl':
                valor.config(foreground='white', background=color)

