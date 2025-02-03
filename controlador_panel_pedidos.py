from datetime import datetime
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
        self._number_orders = 0


        self._crear_tabla_pedidos()
        self._rellenar_tabla_pedidos(self._fecha_seleccionada())
        self._crear_barra_herramientas()

        self._cargar_eventos()
        self._interfaz.ventanas.configurar_ventana_ttkbootstrap(titulo='Panel pedidos')

    def _cargar_eventos(self):
        eventos = {

            'den_fecha': lambda event: self._rellenar_tabla_pedidos(self._fecha_seleccionada())
        }
        self._interfaz.ventanas.cargar_eventos(eventos)

        evento_adicional = {
            'tbv_pedidos': (lambda event: self._actualizar_comentario_pedido(), 'seleccion')
        }
        self._interfaz.ventanas.cargar_eventos(evento_adicional)

        self._interfaz.ventanas.agregar_callback_table_view_al_actualizar('tbv_pedidos',self._colorear_filas_panel_horarios)

    def _limpiar_componentes(self):
        self._interfaz.ventanas.limpiar_componentes(['tbx_comentarios'])

    def _buscar_nuevos_registros(self):
        self._limpiar_componentes()
        number_orders = self._base_de_datos.fetchone(
            """
            SELECT COUNT(OrderDocumentID) Numero
            FROM docDocumentOrderCayal
            WHERE 
                StatusID IN(1, 2, 16, 17, 18)
                AND  CAST(DeliveryPromise AS date) = CAST(? AS date)
            """,
            (datetime.now().date()))

        if self._number_orders != number_orders:
            self._rellenar_tabla_pedidos(self._fecha_seleccionada())
            self._number_orders = number_orders

    def _actualizar_comentario_pedido(self):
        fila = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)
        if not fila:
            return
        if len(fila) > 1:
            return

        comentario = fila[0]['Comentarios']
        comentario = comentario.strip().upper() if comentario else ''
        comentario = f"{fila[0]['Pedido']}-->{comentario}"
        self._interfaz.ventanas.insertar_input_componente('tbx_comentarios', comentario)

    def _fecha_seleccionada(self):
        return str(self._interfaz.ventanas.obtener_input_componente('den_fecha'))

    def _crear_tabla_pedidos(self):
        componente = {
                'tbv_pedidos': (
                'frame_captura', self._interfaz.crear_columnas_tabla(), None, [self._colorear_filas_panel_horarios])
        }
        self._interfaz.ventanas.crear_componentes(componente)

    def _colorear_filas_panel_horarios(self, actualizar_meters=None):
        """
        esta funcion colorea las filas de la tabla segun los horarios, se dispara desde dentro del
        tableview sin embargo si se pasa el argumento actualizar meters procesa los contadores
        la diferencia es que los meters no se actualizan en la misma pasada por rendimiento y solo
        se actualizan cuando se recarga la tabla
        """

        def _procesar_fila(valores_fila):
            priority_id = valores_fila['PriorityID']
            cancelled = valores_fila['Cancelled']
            fecha_entrega_str = valores_fila['FechaEntrega']
            hora_entrega = valores_fila['HoraEntrega']
            schedule_id = valores_fila['StatusScheduleID']

            # 1 en tiempo -- verde
            # 0 retrasado -- rojo
            # 2 a tiempo --- naranja
            # 3 cancelado -- rojo
            fecha_entrega = self._utilerias.convertir_fecha_str_a_datetime(fecha_entrega_str, ['%d/%m/%y', '%d-%m-%y'])

            # los pedidos de fechas posteriores se consideran en tiempo
            if fecha_entrega > self._modelo.hoy:
                return 1

            if fecha_entrega < self._modelo.hoy:
                return 0

            # indistintamente de su horario de entrega los urgentes y cancelados se marcan con rojo
            if priority_id == 2:
                return 0

            if cancelled == 1:
                return 3

            # encuentra la diferencia en minutos entre la hora actual y la hora de entrega del pedido
            #minutos_para_entrega = self._calcular_tiempos_restante_para_entrega(hora_entrega)

            if schedule_id == 0:
                return 1

            if schedule_id == 1:
                return 2

            if schedule_id == 2:
                return 0

        filas = []
        if not actualizar_meters:
            filas = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', visibles=True)

        if actualizar_meters:
            filas = self._modelo.consulta_pedidos_entrega

        self._modelo.pedidos_retrasados = 0
        self._modelo.pedidos_en_tiempo = 0
        self._modelo.pedidos_a_tiempo = 0

        if not filas:
            return

        colores = {
            0: 'red', 1: 'green', 2: 'orange', 3: 'red'
        }

        for i, fila in enumerate(filas):
            priority_id = fila['PriorityID']
            cancelled = fila['Cancelado']
            fecha_entrega_str = fila['F.Entrega'] if not actualizar_meters else fila['FechaEntrega']
            hora_entrega = fila['H.Entrega'] if not actualizar_meters else fila['HoraEntrega']
            schedule_id = fila['StatusScheduleID']



            valores_fila = {
                'PriorityID': priority_id,
                'Cancelled': cancelled,
                'FechaEntrega': fecha_entrega_str,
                'HoraEntrega': hora_entrega,
                'StatusScheduleID': schedule_id
            }
            status_pedido = _procesar_fila(valores_fila)
            color = colores[status_pedido]

            if not actualizar_meters:
                self._interfaz.ventanas.colorear_filas_table_view('tbv_pedidos', [i], color)

            if actualizar_meters:
                if color == 'green':
                    self._modelo.pedidos_en_tiempo += 1
                if color == 'red':
                    self._modelo.pedidos_retrasados += 1
                if color == 'orange':
                    self._modelo.pedidos_a_tiempo += 1
        if actualizar_meters:
            self._rellenar_meters()

    def _rellenar_tabla_pedidos(self, fecha):
        consulta = self._modelo.buscar_pedidos(fecha)

        if not consulta:
            tabla = self._interfaz.ventanas.componentes_forma['tbv_pedidos']
            self._interfaz.ventanas.insertar_input_componente('mtr_total', (1, 0))
            self._interfaz.ventanas.insertar_input_componente('mtr_en_tiempo', (1, 0))
            self._interfaz.ventanas.insertar_input_componente('mtr_a_tiempo', (1, 0))
            self._interfaz.ventanas.insertar_input_componente('mtr_retrasado', (1, 0))
            tabla.delete_rows()
            return

        self._interfaz.ventanas.rellenar_table_view('tbv_pedidos',
                                                        self._interfaz.crear_columnas_tabla(),
                                                        consulta
                                                        )
        self._rellenar_cbx_captura(consulta)
        self._rellenar_cbx_horarios(consulta)
        self._rellenar_cbx_status(consulta)

        self._modelo.consulta_pedidos_entrega = consulta
        self._colorear_filas_panel_horarios(actualizar_meters=True)

    def _capturar_nuevo(self):
        ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
        self._parametros.id_principal = -1
        instancia = BuscarGeneralesCliente(ventana, self._parametros)
        #ventana.wait_window()
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
        texto = f'PANEL: pedidos OPERADOR: {operador_panel}'
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

    def _rellenar_cbx_captura(self, consulta):
        capturo = [reg['CapturadoPor'] for reg in consulta]
        capturo = sorted(list(set(capturo)))
        self._interfaz.ventanas.rellenar_cbx('cbx_capturista', capturo)

    def _rellenar_cbx_status(self, consulta):
        status = [reg['Status'] for reg in consulta]
        status = sorted(list(set(status)))
        self._interfaz.ventanas.rellenar_cbx('cbx_status', status)

    def _rellenar_cbx_horarios(self, consulta):
        horas = [reg['HoraEntrega'] for reg in consulta]
        horas = sorted(list(set(horas)))
        self._interfaz.ventanas.rellenar_cbx('cbx_horarios', horas)

    def _rellenar_meters(self):

        pedidos_entrega = len(self._modelo.consulta_pedidos_entrega)
        if pedidos_entrega == 0:
            self._interfaz.ventanas.insertar_input_componente('mtr_total', (1, pedidos_entrega))
            self._interfaz.ventanas.insertar_input_componente('mtr_en_tiempo', (1, pedidos_entrega))
            self._interfaz.ventanas.insertar_input_componente('mtr_a_tiempo', (1, pedidos_entrega))
            self._interfaz.ventanas.insertar_input_componente('mtr_retrasado', (1, pedidos_entrega))
            return

        self._interfaz.ventanas.insertar_input_componente('mtr_total', (pedidos_entrega, pedidos_entrega))
        self._interfaz.ventanas.insertar_input_componente('mtr_en_tiempo',
                                                          (pedidos_entrega, self._modelo.pedidos_en_tiempo))
        self._interfaz.ventanas.insertar_input_componente('mtr_a_tiempo',
                                                          (pedidos_entrega, self._modelo.pedidos_a_tiempo))
        self._interfaz.ventanas.insertar_input_componente('mtr_retrasado',
                                                          (pedidos_entrega, self._modelo.pedidos_retrasados))

        en_tiempo = f">={self._modelo.valor_en_tiempo}min."
        a_tiempo = f">={self._modelo.valor_a_tiempo}min."
        retrasado = f"<{self._modelo.valor_a_tiempo}min."

        self._interfaz.ventanas.actualizar_etiqueta_meter('mtr_en_tiempo', en_tiempo)
        self._interfaz.ventanas.actualizar_etiqueta_meter('mtr_a_tiempo', a_tiempo)
        self._interfaz.ventanas.actualizar_etiqueta_meter('mtr_retrasado', retrasado)