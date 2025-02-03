from buscar_pedido import BuscarPedido
from cayal.login import Login
from buscar_generales_cliente import BuscarGeneralesCliente

class ControladorPanelPedidos:
    def __init__(self, modelo):
        self._modelo = modelo
        self._interfaz = modelo.interfaz
        self._base_de_datos = self._modelo.base_de_datos
        self._utilerias = self._modelo.utilerias
        self._parametros = self._modelo.parametros

        self._crear_tabla_pedidos()
        self._rellenar_cbx_horarios()
        self._rellenar_tabla_pedidos(self._fecha_seleccionada())
        self._crear_barra_herramientas()

        self._cargar_eventos()
        self._interfaz.ventanas.configurar_ventana_ttkbootstrap(titulo='Panel pedidos')

    def _cargar_eventos(self):
        eventos = {

            'den_fecha': lambda event: self._rellenar_tabla_pedidos(self._fecha_seleccionada())
        }
        self._interfaz.ventanas.cargar_eventos(eventos)
        """
        evento_adicional = {
            'tbv_pedidos': (lambda event: self._actualizar_comentario_pedido(), 'seleccion')
        }
        self._interfaz.ventanas.cargar_eventos(evento_adicional)
        """

    def _fecha_seleccionada(self):
        return str(self._interfaz.ventanas.obtener_input_componente('den_fecha'))

    def _crear_tabla_pedidos(self):
        componente = {
                'tbv_pedidos': (
                'frame_captura', self._interfaz.crear_columnas_tabla(), None, None) #[self._colorear_filas_panel_horarios]),
        }
        self._interfaz.ventanas.crear_componentes(componente)

    def _rellenar_tabla_pedidos(self, fecha):
        consulta = self._modelo.buscar_pedidos(fecha)
        self._interfaz.ventanas.rellenar_table_view('tbv_pedidos',
                                                    self._interfaz.crear_columnas_tabla(),
                                                    consulta
                                                    )

    def _capturar_nuevo(self):
        ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
        self._parametros.id_principal = -1
        instancia = BuscarGeneralesCliente(ventana, self._parametros)
        ventana.wait_window()
        self._parametros.id_principal = 0

    def _editar_caracteristicas(self):
        pass

    def _crear_ticket(self):
        pass

    def _mandar_a_producir(self):
        pass

    def _confirmar_transferencia(self):
        pass

    def _combinar_envio(self):
        pass

    def _facturar(self):
        pass

    def _agregar_queja(self):
        pass

    def _cancelar_pedido(self):
        pass

    def _buscar_pedido(self):
        ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(titulo='Buscar pedido')
        instancia = BuscarPedido(ventana, self._base_de_datos, self._utilerias, self._parametros)
        ventana.wait_window()
        self._parametros.id_principal = 0

    def _rellenar_operador(self):
        operador_panel = self._modelo.buscar_nombre_usuario_operador_panel(self._parametros.id_usuario)
        texto = f'PANEL: producción OPERADOR: {operador_panel}'
        self._interfaz.ventanas.actualizar_etiqueta_externa_tabla_view('tbv_pedidos', texto)
        self._user_id = self._parametros.id_usuario

    def _cambiar_usuario(self):
        def si_acceso_exitoso(parametros=None, master=None):
            self._parametros = parametros
            self._rellenar_operador()

        ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
        instancia = Login(ventana, self._parametros, si_acceso_exitoso)
        ventana.wait_window()

    def _crear_barra_herramientas(self):
        self.barra_herramientas_pedido = [
            {'nombre_icono': 'HeaderFooter32.ico', 'etiqueta': 'Nuevo', 'nombre': 'capturar_nuevo',
             'hotkey': None, 'comando': self._capturar_nuevo},

            {'nombre_icono': 'EditBusinessEntity32.ico', 'etiqueta': 'E.Caracteristicas', 'nombre': 'editar_caracteristicas',
             'hotkey': None, 'comando': self._editar_caracteristicas},

            {'nombre_icono': 'DocumentGenerator32.ico', 'etiqueta': 'Ticket', 'nombre': 'crear_ticket',
             'hotkey': None, 'comando': self._crear_ticket},

            {'nombre_icono': 'Manufacture32.ico', 'etiqueta': 'M.Producir', 'nombre': 'mandar_producir',
             'hotkey': None, 'comando': self._mandar_a_producir},

            {'nombre_icono': 'BankAccountAdd32.ico', 'etiqueta': 'C.Transf.', 'nombre': 'confirmar_transferencia',
             'hotkey': None, 'comando': self._confirmar_transferencia},

            {'nombre_icono': 'Partner32.ico', 'etiqueta': 'C.Envio', 'nombre': 'combinar_envio',
             'hotkey': None, 'comando': self._combinar_envio},

            {'nombre_icono': 'Invoice32.ico', 'etiqueta': 'Facturar', 'nombre': 'facturar',
             'hotkey': None, 'comando': self._facturar},

            {'nombre_icono': 'warning.ico', 'etiqueta': 'A.Queja', 'nombre': 'agregar_queja',
             'hotkey': None, 'comando': self._agregar_queja},


            {'nombre_icono': 'History21.ico', 'etiqueta': 'Historial', 'nombre': 'historial_pedido',
             'hotkey': None, 'comando': self._capturar_nuevo},

            {'nombre_icono': 'Printer21.ico', 'etiqueta': 'Imprimir', 'nombre': 'imprimir_pedido',
             'hotkey': None, 'comando': self._capturar_nuevo},


            {'nombre_icono': 'SwitchUser32.ico', 'etiqueta': 'C.Usuario', 'nombre': 'cambiar_usuario',
             'hotkey': None, 'comando': self._cambiar_usuario},



        ]

        self.elementos_barra_herramientas = self._interfaz.ventanas.crear_barra_herramientas(self.barra_herramientas_pedido,
                                                                                   'frame_herramientas')
        self.iconos_barra_herramientas = self.elementos_barra_herramientas[0]
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]

    def _rellenar_cbx_horarios(self):
        # horarios_ids = [pedido['ScheduleID'] for pedido in self._modelo.consulta_pedidos_entrega]
        horarios_disponibles = [horario['Value'] for horario in self._modelo.consulta_horarios_pedidos
                                if horario['ScheduleID']]

        self._interfaz.ventanas.rellenar_cbx('cbx_horarios', horarios_disponibles, sin_seleccione=False)