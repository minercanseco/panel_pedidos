import tkinter as tk
from datetime import datetime, timedelta

from cayal.util import Utilerias
from cayal.ventanas import Ventanas


class ConfigurarPedido:
    def __init__(self, master, parametros_contpaqi, base_de_datos, cliente, documento):
        self._master = master
        self._base_de_datos = base_de_datos
        self._cliente = cliente
        self._documento = documento
        self._utilerias = Utilerias()
        self._parametros_contpaqi = parametros_contpaqi
        self._ventanas = Ventanas(self._master)
        self._created_on = datetime.now()
        self.parametros_pedido = {}
        self.pedido_configurado = False
        self._hoy = datetime.now().date()

        self._inicializar_variables_de_instancia()
        self._cargar_componentes_forma()
        self._filtrar_horario_disponibles(self._hoy)
        self._rellenar_componentes_forma()
        self._cargar_eventos_componentes()

        self._ventanas.bloquear_componente('tbx_relacionado')
        self._ventanas.centrar_ventana_ttkbootstrap(self._master)
        self._ventanas.enfocar_componente('cbx_tipo')

    def _hora_actual_mas_hora_y_media(self):
        ahora = datetime.now()
        nueva_hora = ahora + timedelta(hours=1, minutes=30)

        return nueva_hora.time()

    def _hora_actual(self):
        ahora = datetime.now()
        hora_actual_str = f'{ahora.hour:02}:{ahora.minute:02}'
        return datetime.strptime(hora_actual_str, "%H:%M").time()

    def _filtrar_hora_actual(self):
        fecha_pedido = self._ventanas.obtener_input_componente('den_fecha')
        if fecha_pedido != self._hoy:
            return

        tipo_pedido = self._ventanas.obtener_input_componente('cbx_tipo')

        hora_actual = self._hora_actual_mas_hora_y_media() if tipo_pedido != 'Cambio' else self._hora_actual()

        horas = [hora for hora in self._consulta_horarios if
                 datetime.strptime(hora['Value'], "%H:%M").time() > hora_actual]

        self._consulta_horarios = horas

    def _inicializar_variables_de_instancia(self):
        self._consulta_tipos_pedidos = self._base_de_datos.buscar_tipos_pedidos_cayal()
        self._consulta_formas_pago = self._base_de_datos.buscar_formas_pago_pedido_cayal()
        self._consulta_tipos_entrega = self._base_de_datos.buscar_tipos_entrega_pedido_cayal()
        self._consulta_prioridad_pedidos = self._base_de_datos.buscar_tipos_prioridad_pedidos_cayal()
        self._consulta_origen_pedidos = self._base_de_datos.buscar_tipo_origen_pedidos_cayal()
        self._consulta_pedidos_relacionables = self._base_de_datos.buscar_pedidos_relacionables(self._cliente.business_entity_id)
        self._consulta_horarios = None

    def _validar_fecha_pedido(self):

        fecha_pedido = self._ventanas.obtener_input_componente('den_fecha')
        if fecha_pedido < self._hoy:

            return False

        return True

    def _filtrar_horario_disponibles(self, fecha):

        if self._validar_fecha_pedido():
            consulta = self._base_de_datos.buscar_numero_pedidos_por_horario(fecha)

            consulta_filtrada = [horario for horario in consulta
                                 if horario['OrdersNumber'] < horario['Quantity']]

            self._consulta_horarios = consulta_filtrada
            self._filtrar_hora_actual()

            valores = [horario['Value'] for horario in self._consulta_horarios]

            if valores:
                self._ventanas.rellenar_cbx('cbx_horario', valores)
                self._ventanas.insertar_input_componente('cbx_horario', 'Seleccione')

    def _crear_columnas_tabla(self):
        return [
            {"text": "Folio", "stretch": False, 'width': 80, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Tipo", "stretch": False, 'width': 90, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Entrega", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Hora", "stretch": False, 'width': 60, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Status", "stretch": False, 'width': 120, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "OrderDocumentID", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "MinutosTranscurridos", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
        ]

    def _cargar_componentes_forma(self):
        componentes = [
            ('cbx_tipo', 'Tipo:'),
            ('cbx_prioridad', 'Prioridad:'),
            ('den_fecha', 'Entrega:'),
            ('cbx_horario', 'Horario:'),
            ('cbx_origen', 'Origen:'),
            ('cbx_entrega', 'Entrega:'),
            ('cbx_forma_pago', 'F.Pago:'),
            ('txt_comentario', 'Com.:'),
            ('tvw_pedidos', self._crear_columnas_tabla()),
            ('btn_guardar', 'Guardar')
        ]

        self._ventanas.crear_formulario_simple(componentes, 'Detalles Pedido:', 'Pedidos:')
        self._ventanas.ajustar_ancho_componente('txt_comentario',63)

    def _rellenar_componentes_forma(self):
        componentes = {
            'cbx_tipo': (self._consulta_tipos_pedidos, 'Value'),
            'cbx_origen': (self._consulta_origen_pedidos, 'Value'),
            'cbx_horario': (self._consulta_horarios, 'Value'),
            'cbx_entrega': (self._consulta_tipos_entrega, 'DeliveryTypesName'),
            'cbx_forma_pago': (self._consulta_formas_pago, 'PaymentTermName'),
            'cbx_prioridad': (self._consulta_prioridad_pedidos, 'Value'),
        }
        for nombre, (consulta, campo_consulta) in componentes.items():
            valores = [reg[campo_consulta] for reg in consulta]
            if nombre == 'cbx_prioridad':
                self._ventanas.rellenar_cbx(nombre, valores, 'sin_seleccione')
                continue

            self._ventanas.rellenar_cbx(nombre, valores)

        self._ventanas.rellenar_treeview('tvw_pedidos',
                                         self._crear_columnas_tabla(),
                                         self._consulta_pedidos_relacionables)

    def _cargar_eventos_componentes(self):
        eventos = {
            'btn_guardar': self._guardar_parametros_pedido,
            'btn_cancelar': self._cancelar_configurar_pedido,
            'tvw_pedidos': (lambda event: self._relacionar_a_pedido(), 'doble_click'),
            'den_fecha': lambda event: self._filtrar_horario_disponibles(
                self._ventanas.obtener_input_componente('den_fecha')),
            'cbx_tipo': lambda event: self._filtrar_horario_disponibles(
                self._ventanas.obtener_input_componente('den_fecha'))
        }

        self._ventanas.cargar_eventos(eventos)

    def _cancelar_configurar_pedido(self):
        self.pedido_configurado = False
        self.parametros_pedido = {}
        self._master.destroy()

    def _buscar_pedidos_relacionables(self):
        self._base_de_datos.buscar_pedidos_relacionables(self._cliente.business_entity_id)

    def _relacionar_a_pedido(self):

        tipo_pedido = self._ventanas.obtener_input_componente('cbx_tipo')

        if tipo_pedido in ('Seleccione', 'Pedido'):
            self._ventanas.mostrar_mensaje('Esta opción es solo válida para anexos y cambios.')
            return

        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_pedidos')
        if len(fila) > 1 or len(fila) < 1:
            self._ventanas.mostrar_mensaje('Debe seleccionar solo un registro.')
            return

        valores_fila = self._ventanas.obtener_valores_fila_treeview('tvw_pedidos', fila)

        if tipo_pedido == 'Anexo':
            fecha_entrega_str = valores_fila[2]
            fecha_entrega = self._utilerias.convertir_fecha_str_a_datetime(fecha_entrega_str)
            fecha_pedido = self._ventanas.obtener_input_componente('den_fecha')
            minutos_transcurridos = valores_fila[6]

            if not self._validar_fecha_pedido():
                self._ventanas.mostrar_mensaje('La fecha no puede ser menor al día de hoy.')
                return

            if fecha_entrega < self._hoy:
                self._ventanas.mostrar_mensaje('Solo puede relacionar anexos a pedidos del mismo día.')
                return

            if tipo_pedido == 'Anexo' and minutos_transcurridos > 30:
                self._ventanas.mostrar_mensaje('Solo puede capturar anexos dentro de los 30 primeros minutos'
                                               'después de la captura del pedido.')
                return

            if fecha_pedido < self._hoy:
                self._ventanas.mostrar_mensaje('Los anexos solo se pueden asignar a pedidos del día.')
                return

        folio_pedido = valores_fila[0]
        respuesta = self._ventanas.mostrar_mensaje_pregunta(f'Desea relacionar el {tipo_pedido} con el pedido {folio_pedido}')

        if not respuesta:
            return

        order_document_id = valores_fila[5]

        self._asignar_valores_pedido_a_anexo_o_cambio(order_document_id, tipo_pedido)

    def _buscar_parametros_pedido_asignable(self, order_document_id):
        consulta = self._base_de_datos.buscar_parametros_pedido(order_document_id)

        if not consulta:
            return False

        consulta = consulta[0]
        self.parametros_pedido = consulta

        return consulta

    def _asignar_valores_pedido_a_anexo_o_cambio(self, order_document_id, tipo_pedido):

        consulta_order_document_id = self._buscar_parametros_pedido_asignable(order_document_id)

        if not consulta_order_document_id:
            return

        componentes_actualizables_anexo = ['cbx_tipo', 'cbx_origen', 'cbx_horario', 'cbx_entrega',
                                           'cbx_prioridad', 'cbx_forma_pago']

        componentes_actualizables_cambio_hoy = ['cbx_tipo', 'cbx_origen', 'cbx_horario', 'cbx_entrega',
                                                 'cbx_forma_pago']

        componentes_actualizables_cambio_otros_dias = ['cbx_tipo', 'cbx_prioridad', 'cbx_forma_pago']

        # asginar valores de la consulta de la bd a los componentes de la forma
        componentes = {
                'cbx_tipo': (self._consulta_tipos_pedidos, 'ID', 'Value', 'OrderTypeID'),
                'cbx_origen': (self._consulta_origen_pedidos, 'ID', 'Value', 'OrderTypeOriginID'),
                'cbx_horario': (self._consulta_horarios, 'ScheduleID', 'Value', 'ScheduleID'),
                'cbx_entrega': (self._consulta_tipos_entrega,
                                'DeliveryTypesID',
                                'DeliveryTypesName',
                                'OrderDeliveryTypeID'),
                'cbx_prioridad': (self._consulta_prioridad_pedidos, 'ID', 'Value', 'PriorityID'),
                'cbx_forma_pago': (self._consulta_formas_pago, 'PaymentTermID', 'PaymentTermName', 'WayToPayID')
            }

        for nombre, (consulta, campo_consulta, seleccion_consulta, campo_tabla) in componentes.items():
            valor_bd = self.parametros_pedido[campo_tabla]

            #  setear el tipo de pedido segun el caso
            if tipo_pedido == 'Anexo':
                if nombre == 'cbx_tipo':
                    valor_bd = 2

            if tipo_pedido == 'Cambio':
                if nombre == 'cbx_tipo':
                    valor_bd = 3

                if nombre == 'cbx_forma_pago':
                    valor_bd = 8

            valor_componente = [reg[seleccion_consulta] for reg in consulta if reg[campo_consulta] == valor_bd]

            if valor_componente:

                if tipo_pedido == 'Anexo':
                    if nombre in componentes_actualizables_anexo:
                        self._ventanas.insertar_input_componente(nombre, valor_componente[0])

                if tipo_pedido == 'Cambio':
                    fecha_pedido_original = consulta_order_document_id['CreatedOn']

                    if fecha_pedido_original != self._hoy:
                        if nombre in componentes_actualizables_cambio_otros_dias:
                            self._ventanas.insertar_input_componente(nombre, valor_componente[0])

                    if fecha_pedido_original == self._hoy:
                        if nombre in componentes_actualizables_cambio_hoy:
                            self._ventanas.insertar_input_componente(nombre, valor_componente[0])

        self._documento.order_parameters = self.parametros_pedido
        self._bloquear_componentes_segun_tipo_pedido(tipo_pedido)
        self._actualizar_parametros_nuevos_anexo_o_cambio(order_document_id, tipo_pedido)

    def _actualizar_parametros_nuevos_anexo_o_cambio(self, order_document_id, tipo_pedido):
        self.parametros_pedido['OrderTypeID'] = 2 if tipo_pedido == 'Anexo' else 3
        self.parametros_pedido['RelatedOrderID'] = order_document_id
        self.parametros_pedido['CreatedOn'] = datetime.now()
        self.parametros_pedido['CreatedBy'] = self._parametros_contpaqi.id_usuario
        self.parametros_pedido['HostName'] = self._utilerias.obtener_hostname()

    def _bloquear_componentes_segun_tipo_pedido(self, tipo_pedido):
        # bloquear los componentes
        componentes_a_bloquear_anexo = ['den_fecha', 'cbx_tipo', 'cbx_horario', 'cbx_origen', 'cbx_entrega',
                                        'cbx_forma_pago', 'cbx_prioridad' ]

        componentes_a_bloquear_cambio = ['den_fecha', 'cbx_tipo',
                                         'cbx_forma_pago', 'cbx_prioridad']

        componentes_a_bloquear = componentes_a_bloquear_anexo if tipo_pedido == 'Anexo' else componentes_a_bloquear_cambio

        for nombre in componentes_a_bloquear:
            self._ventanas.bloquear_componente(nombre)

    def _validar_inputs_formulario(self):
        for nombre, componente in self._ventanas.componentes_forma.items():

            tipo = nombre[0:3]

            if tipo == 'den':
                fecha_entrega = self._ventanas.obtener_input_componente('den_fecha')

                if fecha_entrega < self._hoy:
                    self._ventanas.mostrar_mensaje('La fecha de entrega no puede ser menor a la fecha actual.')
                    return False

            if tipo in 'cbx':
                seleccion =self._ventanas.obtener_input_componente(nombre)

                if nombre == 'cbx_tipo' and seleccion not in ('Seleccione', 'Pedido'):
                    comentario = self._ventanas.obtener_input_componente('txt_comentario')
                    if not comentario:
                        self._ventanas.mostrar_mensaje('Para los anexos y cambios el comentario debe ser obligatorio.')
                        return False

                    if len(comentario) < 2:
                        self._ventanas.mostrar_mensaje('Para los anexos y cambios el comentario debe ser obligatorio.')
                        return False

                    if len(comentario) < 5:
                        self._ventanas.mostrar_mensaje('Debe abundar en el texto del comentario')
                        return False

                if seleccion == 'Seleccione':
                    etiqueta = nombre[4::]
                    etiqueta = etiqueta.capitalize()

                    self._ventanas.mostrar_mensaje(f'Debe seleccionar una opción válida para {etiqueta}')
                    return False

        if not self._validar_fecha_pedido():
            return False

        return True

    def _procesar_seleccion_usuario(self):

        tipo_pedido = self._ventanas.obtener_input_componente('tbx_tipo')
        if tipo_pedido in ('Anexo', 'Cambio'):
            return

        componentes = {
            'cbx_tipo': (self._consulta_tipos_pedidos, 'ID', 'Value', 'OrderTypeID'),
            'cbx_origen': (self._consulta_origen_pedidos, 'ID', 'Value', 'OrderTypeOriginID'),
            'cbx_horario': (self._consulta_horarios, 'ScheduleID', 'Value', 'ScheduleID'),
            'cbx_entrega': (self._consulta_tipos_entrega, 'DeliveryTypesID', 'DeliveryTypesName', 'OrderDeliveryTypeID'),
            'cbx_prioridad': (self._consulta_prioridad_pedidos, 'ID', 'Value', 'PriorityID'),
            'cbx_forma_pago': (self._consulta_formas_pago, 'PaymentTermID', 'PaymentTermName', 'WayToPayID')
        }
        valores_pedido = {}
        for nombre, (consulta, campo_consulta, seleccion_consulta, campo_tabla) in componentes.items():
            seleccion = self._ventanas.obtener_input_componente(nombre)

            valor = [reg[campo_consulta] for reg in consulta if seleccion == reg[seleccion_consulta]][0]
            valores_pedido[campo_tabla] = valor

        valores_pedido['CreatedBy'] = self._parametros_contpaqi.id_usuario
        valores_pedido['DeliveryPromise'] = self._ventanas.obtener_input_componente('den_fecha')
        valores_pedido['CreatedOn'] = self._created_on
        comentario_pedido = self._ventanas.obtener_input_componente('txt_comentario')
        valores_pedido['CommentsOrder'] = comentario_pedido.upper()
        valores_pedido['BusinessEntityID'] = self._cliente.business_entity_id

        related_order_id = self.parametros_pedido.get('RelatedOrderID', 0)
        valores_pedido['RelatedOrderID'] = related_order_id
        valores_pedido['ZoneID'] = self._cliente.zone_id
        valores_pedido['SubTotal'] = 0
        valores_pedido['TotalTax'] = 0
        valores_pedido['Total'] = 0
        valores_pedido['HostName'] = self._utilerias.obtener_hostname()
        valores_pedido['AddressDetailID'] = self._documento.address_detail_id
        valores_pedido['DocumentTypeID'] = self._documento.cfd_type_id
        valores_pedido['OrderDeliveryCost'] = self._documento.delivery_cost
        valores_pedido['DepotID'] = self._documento.depot_id

        way_to_pay_id = valores_pedido.get('WayToPayID', 1)
        payment_confirmed_id = 1
        delivery_type_id = valores_pedido.get('OrderDeliveryTypeID', 1)

        # si la forma de pago es transferencia el id es transferencia no confirmada
        if way_to_pay_id == 6:
            payment_confirmed_id = 2

        # si el tipo de entrga es viene y la fomra de pago NO es transferencia entonces la forma de pago es en tienda
        if delivery_type_id == 2 and way_to_pay_id != 6:
            payment_confirmed_id = 4

        valores_pedido['PaymentConfirmedID'] = payment_confirmed_id

        self.parametros_pedido = valores_pedido
        self._documento.order_parameters = valores_pedido

    def _guardar_parametros_pedido(self):
        if self._validar_inputs_formulario():
            self._procesar_seleccion_usuario()

            order_related_id = self.parametros_pedido['RelatedOrderID']
            tipo_pedido = self._ventanas.obtener_input_componente('cbx_tipo')

            if tipo_pedido in ('Anexo', 'Cambio') and order_related_id == 0:
                self._ventanas.mostrar_mensaje('Debe relacionar el anexo o el cambio con un pedido.')
                self.parametros_pedido = {}
                self._documento.order_parameters = {}
            else:
                self.pedido_configurado = True
                self._master.destroy()

