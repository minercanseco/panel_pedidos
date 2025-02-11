import tkinter as tk
from cayal.util import Utilerias
from cayal.ventanas import Ventanas


class InterfazSaldarCartera:
    def __init__(self, master, controlador):

        self._utilerias = Utilerias()
        self._controlador = controlador
        official_name = self._controlador.buscar_official_name()
        self._official_name = self._utilerias.limitar_caracteres(official_name, 20)

        self._master = master
        self._ventanas = Ventanas(self._master)
        self._componentes_forma = self._ventanas.componentes_forma

        self._crear_frames()
        self._cargar_componentes_forma()
        self._cargar_info_componentes()
        self._agregar_atajos()
        self._agregar_eventos()

        self._ventanas.ocultar_frame('frame_cambio')
        self._ventanas.ocultar_frame('frame_terminal')

        self._ventanas.configurar_ventana_ttkbootstrap('Saldar cartera')
        self._ventanas.enfocar_componente('frame_tabla')

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.W}),

            'frame_datos_generales': ('frame_principal', None,
                                      {'row': 0, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.W}),

            'frame_datos': ('frame_datos_generales', None,
                             {'row': 0, 'column': 0, 'columnspan':2, 'padx': 2, 'pady': 5, 'sticky': tk.W}),

            'frame_cambio': ('frame_datos_generales', None,
                               {'row': 1, 'column': 0, 'padx': 12, 'pady': 5, 'sticky': tk.W}),

            'frame_terminal': ('frame_datos_generales', None,
                                {'row': 2, 'column': 0, 'padx': 12, 'pady': 5, 'sticky': tk.W}),

            'frame_botones_aplicar': ('frame_principal', None,
                                      {'row': 1, 'columnspan': 2, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.W}),

            'frame_tabla': ('frame_principal', None,
                            {'row': 2, 'column': 0, 'columnspan': 3, 'padx': 5, 'pady': 5, 'sticky': tk.W}),

            'frame_acciones': ('frame_principal', None,
                               {'row': 3, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.W, }),

            'frame_totales': ('frame_principal', None,
                              {'row': 0, 'column': 2,  'columnspan': 2,  'sticky': tk.NE}),
        }

        self._ventanas.crear_frames(frames)

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
            'tvw_tabla_documentos': ('frame_tabla', self._columnas_tabla(), None, None),
        }

        self._ventanas.crear_componentes(componentes)

        self._crear_barras_herramientas()
        self._rellenar_frame_totales()

        self._inicializar_controles_en_controlador()

    def _rellenar_frame_totales(self):
        estilo_rojo = {
            'foreground': 'white',
            'background': '#E30421',
            'font': ('Consolas', 16, 'bold')
        }

        componentes = {
            'lbl_nombre_cliente': ('frame_totales', estilo_rojo,
                                   {'row': 0, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW, }, None),
            'lbl_cartera_txt': ('frame_totales', estilo_rojo,
                                {'row': 1, 'column': 0, 'sticky': tk.NSEW, }, None),
            'lbl_monto_txt': ('frame_totales', estilo_rojo,
                              {'row': 2, 'column': 0, 'sticky': tk.NSEW, }, None),
            'lbl_restante_txt': ('frame_totales', estilo_rojo,
                                 {'row': 3, 'column': 0, 'sticky': tk.NSEW, }, None),
            'lbl_cambio_txt': ('frame_totales', estilo_rojo,
                               {'row': 4, 'column': 0, 'sticky': tk.NSEW, }, None),

            'lbl_cartera': ('frame_totales', estilo_rojo,
                            {'row': 1, 'column':1, 'sticky': tk.NSEW, }, None),
            'lbl_monto': ('frame_totales', estilo_rojo,
                          {'row': 2, 'column': 1, 'sticky': tk.NSEW, }, None),
            'lbl_restante': ('frame_totales', estilo_rojo,
                             {'row': 3, 'column': 1, 'sticky': tk.NSEW, }, None),
            'lbl_cambio': ('frame_totales', estilo_rojo,
                           {'row': 4, 'column': 1, 'sticky': tk.NSEW, }, None),
        }
        self._ventanas.crear_componentes(componentes)

    def _crear_barras_herramientas(self):

        self.barra_herramientas2 = [
            {'nombre_icono': 'Validate32.ico', 'etiqueta': 'Saldar', 'nombre': 'saldar', 'hotkey': '[F12]',
             'comando': lambda: self._controlador.saldar()},
            {'nombre_icono': 'Cancelled32.ico', 'etiqueta': 'Deshacer', 'nombre': 'deshacer', 'hotkey': '[Q]',
             'comando': lambda: self._controlador.deshacer_saldado()},
        ]

        self.lista_iconos_barra_herramientas2 = self._utilerias.crear_barra_herramientas(
            self.barra_herramientas2, self._componentes_forma['frame_acciones'])

        self.barra_herramientas = [
            {'nombre_icono': 'Payments32.ico', 'etiqueta': 'Total', 'nombre': 'aplicar_total', 'hotkey': '[F1]',
             'comando': lambda: self._controlador.aplicar_por_documento()},
            {'nombre_icono': 'Payments32.ico', 'etiqueta': 'Automático', 'nombre': 'aplicar_automatico',
             'hotkey': '[F4]', 'comando': lambda: self._controlador.aplicar_por_monto('auto')},
            {'nombre_icono': 'Payments32.ico', 'etiqueta': 'Selección', 'nombre': 'aplicar_seleccion',
             'hotkey': '[F8]', 'comando': lambda: self._controlador.aplicar_por_monto('selección')},
            {'nombre_icono': 'Invoice32.ico', 'etiqueta': 'Remisiones', 'nombre': 'aplicar_remisiones',
             'hotkey': '[R]', 'comando': lambda: self._controlador.aplicar_por_documento('Remisión')},
            {'nombre_icono': 'Invoice32.ico', 'etiqueta': 'Facturas', 'nombre': 'aplicar_facturas',
             'hotkey': '[F]', 'comando': lambda: self._controlador.aplicar_por_documento('Factura')},
        ]
        self.lista_iconos_barra_herramientas = self._utilerias.crear_barra_herramientas(
            self.barra_herramientas, self._componentes_forma['frame_botones_aplicar'])

    def _columnas_tabla(self):
         return [
            {'text': 'N', "stretch": False, 'width': 30, 'column_anchor': tk.E, 'heading_anchor': tk.E, 'hide': 0},
            {"text": "Fecha", "stretch": False, 'width': 70, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {"text": "Tipo", "stretch": False, 'width': 60, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {"text": "Folio", "stretch": False, 'width': 70, 'column_anchor': tk.W, 'heading_anchor': tk.W,
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
             'hide': 1}
        ]

    def _cargar_info_componentes(self):
        self._ventanas.insertar_input_componente('lbl_nombre_cliente', self._official_name)
        self._ventanas.insertar_input_componente('lbl_cartera_txt', 'CARTERA:')
        self._ventanas.insertar_input_componente('lbl_monto_txt', 'MONTO:')
        self._ventanas.insertar_input_componente('lbl_restante_txt', 'RESTANTE:')
        self._ventanas.insertar_input_componente('lbl_cambio_txt', 'CAMBIO:')
        self._ventanas.insertar_input_componente('lbl_cartera', '$0.00')
        self._ventanas.insertar_input_componente('lbl_monto', '$0.00')
        self._ventanas.insertar_input_componente('lbl_restante', '$0.00')
        self._ventanas.insertar_input_componente('lbl_cambio', '$0.00')

        formas_de_cobro = self._controlador.buscar_formas_pago()
        self._ventanas.rellenar_cbx('cbx_forma_cobro', formas_de_cobro)

        terminales = self._controlador.buscar_terminales_bancarias()
        self._ventanas.rellenar_cbx('cbx_terminal', terminales)

        modalidades_de_cobro = ['Un solo cobro', 'Un cobro por documento']
        self._ventanas.rellenar_cbx('cbx_modalidad_cobro', modalidades_de_cobro, 'Sin seleccione')

        tvw_tabla_documentos = self._componentes_forma['tvw_tabla_documentos']
        self._controlador.rellenar_tabla(tvw_tabla_documentos, self._columnas_tabla())
        cantidad_filas = len(tvw_tabla_documentos.get_children())
        if cantidad_filas > 5:
            tvw_tabla_documentos["height"] = 10

        monto_cartera = self._controlador.buscar_monto_cartera()
        self._ventanas.insertar_input_componente('lbl_cartera', monto_cartera)

    def _inicializar_controles_en_controlador(self):
        self._controlador.master = self._master
        self._controlador.componentes_forma = self._componentes_forma
        self._controlador.ventanas = self._ventanas

    def _agregar_atajos(self):
        eventos = {
            'R': lambda: self._controlador.aplicar_por_documento('Remisión'),
            'F': lambda: self._controlador.aplicar_por_documento('Factura'),
            'Q': lambda: self._controlador.deshacer_saldado(),
            'F1': lambda: self._controlador.aplicar_por_documento(),
            'F4': lambda: self._controlador.aplicar_por_monto('auto'),
            'F8': lambda: self._controlador.aplicar_por_monto('selección'),
            'F12': lambda: self._controlador.saldar()
        }
        self._ventanas.agregar_hotkeys_forma(eventos)

    def _agregar_eventos(self):
        eventos = {
            'cbx_forma_cobro': lambda event: self._ajustar_apariencia_terminal(),
            'tbx_recibido': lambda event: self._controlador.calcular_cambio(),
            'cbx_terminal': lambda event: self._controlador._buscar_afiliacion_seleccion(),
            'tbx_terminal': lambda event: self._controlador._buscar_afiliacion()
        }
        self._ventanas.cargar_eventos(eventos)

        tabla_documentos = self._componentes_forma['tvw_tabla_documentos']
        tabla_documentos.bind('<<TreeviewSelect>>',
                                   lambda event: self._controlador.seleccionar_documento())

        self._utilerias.agregar_validacion_tbx(self._master, self._componentes_forma['tbx_terminal'], 'cantidad')
        self._utilerias.agregar_validacion_tbx(self._master, self._componentes_forma['tbx_monto'], 'cantidad')
        self._utilerias.agregar_validacion_tbx(self._master, self._componentes_forma['tbx_recibido'], 'cantidad')

    def _ajustar_apariencia_terminal(self):
        seleccion = self._ventanas.obtener_input_componente('cbx_forma_cobro')
        tipo = seleccion[0:2]

        if tipo == '01':
            self._ventanas.posicionar_frame('frame_cambio')
            self._ventanas.ocultar_frame('frame_terminal')
            self._ventanas.limpiar_componentes(['tbx_terminal', 'cbx_terminal'])
        if tipo in ('04', '28'):
            self._ventanas.ocultar_frame('frame_cambio')
            self._ventanas.posicionar_frame('frame_terminal')
            self._ventanas.limpiar_componentes(['tbx_terminal', 'cbx_terminal', 'lbl_banco'])
            self._ventanas.insertar_input_componente('lbl_banco', 'BANCO')

        if tipo not in ('01', '04', '28') or seleccion == 'Seleccione':
            self._ventanas.ocultar_frame('frame_cambio')
            self._ventanas.ocultar_frame('frame_terminal')
            self._ventanas.limpiar_componentes(['tbx_terminal', 'cbx_terminal'])

