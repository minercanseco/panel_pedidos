import tkinter as tk
from datetime import datetime, timedelta, date

from cayal.ventanas import Ventanas


class EditarCaracteristicasPedido:
    def __init__(self, master, parametros, base_de_datos, utilerias):
        self._master = master
        self._parametros = parametros
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._ventanas = Ventanas(self._master)

        self._hoy = datetime.now().date()
        self._order_document_id = self._parametros.id_principal
        self._user_id = self._parametros.id_usuario
        self._business_entity_id = self._base_de_datos.fetchone(
            'SELECT BusinessEntityID FROM docDocumentOrderCayal WHERE OrderDocumentID = ?',
            (self._order_document_id,))

        self.info_pedido = self._base_de_datos.buscar_info_documento_pedido_cayal(self._order_document_id)[0]
        comments = self.info_pedido['CommentsOrder']
        comments = comments.upper().strip() if comments else comments

        self.info_pedido['CommentsOrder'] = comments

        self.parametros_pedido = {}

        self._cargar_componentes_forma()
        self._inicializar_variables_de_instancia()

        fecha_entrega = self.info_pedido['DeliveryPromise']
        self._filtrar_horario_disponibles(fecha_entrega)


        self._rellenar_componentes()
        self._cargar_eventos()

        self._settear_valores_pedido_desde_base_de_datos()

        if self.info_pedido['RelatedOrderID'] != 0:
            self._bloquear_componentes_segun_tipo_pedido(self._ventanas.obtener_input_componente('cbx_tipo'))
            self._ventanas.bloquear_componente('btn_guardar')


        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Editar caracteristicas', master=self._master)

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
            ('cbx_documento', 'Documento:'),
            ('cbx_direccion', 'Dirección:'),
            ('cbx_sucursal', 'Sucursal:'),
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
        self._ventanas.ajustar_ancho_componente('txt_comentario', 63)

    def _cargar_eventos(self):
        eventos = {
            'btn_guardar': self._guardar_parametros_pedido,
            'btn_cancelar': self._master.destroy,
            'tvw_pedidos': (lambda event: self._relacionar_a_pedido(), 'doble_click'),
            'den_fecha': lambda event: self._filtrar_horario_disponibles(
                self._ventanas.obtener_input_componente('den_fecha')),
            'cbx_tipo': lambda event: self._filtrar_horario_disponibles(
                self._ventanas.obtener_input_componente('den_fecha')),

        }
        self._ventanas.cargar_eventos(eventos)

    def _actualizar_horario_de_viene(self):

        fecha_entrega = self.info_pedido['DeliveryPromise']
        if fecha_entrega != self._hoy:
            return

        hora_actual_mas_hora = self._hora_actual_mas_hora()
        consulta = self._base_de_datos.buscar_numero_pedidos_por_horario(fecha_entrega)

        horas = [hora for hora in consulta if
         datetime.strptime(hora['Value'], "%H:%M").time() > hora_actual_mas_hora]

        hora_mas_cercana = horas[0]
        self.info_pedido['ScheduleID'] = hora_mas_cercana['ScheduleID']

    def _rellenar_componentes(self):
        componentes = {
            'cbx_tipo': (self._consulta_tipos_pedidos, 'Value'),
            'cbx_direccion': (self._consulta_direcciones, 'AddressName'),
            'cbx_documento': (self._consulta_tipo_documentos, 'Value'),

            'cbx_origen': (self._consulta_origen_pedidos, 'Value'),
            'cbx_horario': (self._consulta_horarios, 'Value'),
            'cbx_entrega': (self._consulta_tipos_entrega, 'DeliveryTypesName'),
            'cbx_forma_pago': (self._consulta_formas_pago, 'PaymentTermName'),
            'cbx_prioridad': (self._consulta_prioridad_pedidos, 'Value'),
            'cbx_sucursal': (self._consulta_sucursales, 'DepotName'),


        }
        try:
            for nombre, (consulta, campo_consulta) in componentes.items():
                valores = [reg[campo_consulta] for reg in consulta]
                if nombre == 'cbx_prioridad':
                    self._ventanas.rellenar_cbx(nombre, valores, 'sin_seleccione')
                    continue

                self._ventanas.rellenar_cbx(nombre, valores)

            self._ventanas.rellenar_treeview('tvw_pedidos',
                                             self._crear_columnas_tabla(),
                                             self._consulta_pedidos_relacionables)
            if not self._consulta_sucursales:
                self._ventanas.rellenar_cbx('cbx_sucursal', ['No aplica'], sin_seleccione=True)
                self._ventanas.bloquear_componente('cbx_sucursal')

            self._ventanas.insertar_input_componente('txt_comentario', self.info_pedido['CommentsOrder'])

        except:
            print(nombre)

    def _hora_actual_mas_hora(self):
        ahora = datetime.now()
        nueva_hora = ahora + timedelta(hours=1, minutes=00)

        return nueva_hora.time()

    def _hora_actual_mas_hora_y_media(self):
        ahora = datetime.now()
        nueva_hora = ahora + timedelta(hours=1, minutes=30)

        return nueva_hora.time()

    def _hora_actual(self):
        ahora = datetime.now()
        hora_actual_str = f'{ahora.hour:02}:{ahora.minute:02}'
        return datetime.strptime(hora_actual_str, "%H:%M").time()

    def _filtrar_hora_actual(self, consulta):

        tipo_pedido = self._ventanas.obtener_input_componente('cbx_tipo')
        hora_actual = self._hora_actual_mas_hora_y_media() if tipo_pedido != 'Cambio' else self._hora_actual()
        return [hora for hora in consulta if
                     datetime.strptime(hora['Value'], "%H:%M").time() > hora_actual]

    def _inicializar_variables_de_instancia(self):
        self._consulta_tipos_pedidos = self._base_de_datos.buscar_tipos_pedidos_cayal()
        self._consulta_formas_pago = self._base_de_datos.buscar_formas_pago_pedido_cayal()
        self._consulta_tipos_entrega = self._base_de_datos.buscar_tipos_entrega_pedido_cayal()
        self._consulta_prioridad_pedidos = self._base_de_datos.buscar_tipos_prioridad_pedidos_cayal()
        self._consulta_origen_pedidos = self._base_de_datos.buscar_tipo_origen_pedidos_cayal()

        consulta_pedidos_relacionables = self._base_de_datos.buscar_pedidos_relacionables(self._business_entity_id)
        self._consulta_pedidos_relacionables = [ reg for reg in consulta_pedidos_relacionables
                                                 if reg['OrderDocumentID'] != self._order_document_id]

        self._consulta_horarios = None
        self._consulta_direcciones = self._base_de_datos.buscar_direcciones(self._business_entity_id)
        self._consulta_sucursales = self._base_de_datos.buscar_sucursales(self._business_entity_id)
        self._consulta_tipo_documentos = [{'ID':0, 'Value':'FACTURA'},{'ID':1, 'Value':'REMISIÓN'}]

    def _validar_fecha_pedido(self):

        fecha_pedido = self._ventanas.obtener_input_componente('den_fecha')
        if fecha_pedido < self._hoy:
            return False

        return fecha_pedido

    def _normalizar_a_date(self, f):
        if f is None:
            return None
        if isinstance(f, date) and not isinstance(f, datetime):
            return f
        if isinstance(f, datetime):
            return f.date()
        if isinstance(f, str):
            # Ajusta a tu utilería si ya tienes una
            try:
                # intenta formatos comunes
                try:
                    return datetime.strptime(f, "%Y-%m-%d").date()
                except ValueError:
                    return datetime.strptime(f, "%Y-%m-%d %H:%M:%S").date()
            except ValueError:
                # como último recurso
                return self._utilerias.convertir_fecha_str_a_datetime(f)
        return None

    def _filtrar_horario_disponibles(self, fecha):
        # 1) Trae SIEMPRE la lista completa
        consulta_completa = self._base_de_datos.buscar_horarios_pedido_cayal()

        # 2) Normaliza la fecha recibida o usa la del control si no viene
        fecha_entrega = self._normalizar_a_date(fecha) or self._validar_fecha_pedido() or self._hoy

        # 3) Si NO es hoy -> todos los horarios (sin filtrar por disponibilidad del día ni hora actual)
        if fecha_entrega != self._hoy:
            self._consulta_horarios = list(consulta_completa)  # copia nueva
        else:
            # 4) Si ES hoy -> aplica disponibilidad y quita horas pasadas (según tu lógica)
            consulta = self._base_de_datos.buscar_numero_pedidos_por_horario(fecha_entrega)
            disponibles = [h for h in consulta if int(h['OrdersNumber']) < int(h['Quantity'])]
            self._consulta_horarios = self._filtrar_hora_actual(disponibles)

        # 5) Arma los valores a mostrar
        valores = [reg['Value'] for reg in self._consulta_horarios]

        # 6) Si el pedido ya tenía horario y es HOY, anteponer el horario original para permitir conservarlo
        if self.info_pedido.get('DeliveryPromise') and fecha_entrega == self._hoy:
            schedule_order_id = self.info_pedido['ScheduleID']
            try:
                horario_pedido = next(r for r in consulta_completa if int(r['ScheduleID']) == int(schedule_order_id))
                if horario_pedido['Value'] not in valores:
                    valores.insert(0, horario_pedido['Value'])
                    self._consulta_horarios.insert(0, horario_pedido)
            except StopIteration:
                pass

        # 7) Rellenar el combo SIEMPRE desde la lista recién construida
        self._ventanas.rellenar_cbx('cbx_horario', valores)

    def _settear_valores_pedido_desde_base_de_datos(self):


        if not self.info_pedido['DeliveryPromise']:

            priority_id = self.info_pedido['PriorityID']

            priority = [tipo['Value'] for tipo in self._consulta_prioridad_pedidos
                          if priority_id == tipo['ID']][0]

            address_detail_id = self.info_pedido['AddressDetailID']
            address_name = [tipo['AddressName'] for tipo in self._consulta_direcciones
                          if address_detail_id == tipo['AddressDetailID']][0]

            if self._consulta_sucursales:
                depot_id = self.info_pedido['DepotID']

                if depot_id != 0:
                    depot_name = [tipo['DepotName'] for tipo in self._consulta_sucursales
                              if depot_id == tipo['DepotID']][0]
                    self._ventanas.insertar_input_componente('cbx_sucursal', depot_name)




            self._ventanas.insertar_input_componente('cbx_documento', self.info_pedido['DocumentType'])
            self._ventanas.insertar_input_componente('cbx_direccion', address_name)
            self._ventanas.insertar_input_componente('cbx_prioridad', priority)

            return

        payment_term_name = self.info_pedido['PaymentTermName']
        comments = self.info_pedido['CommentsOrder']
        comments = comments.upper() if comments else ''

        order_type_id = self.info_pedido['OrderTypeID']
        order_type = [tipo['Value'] for tipo in self._consulta_tipos_pedidos
                      if order_type_id == tipo['ID']][0]

        order_type_origin_id = self.info_pedido['OrderTypeOriginID']
        order_type_origin = [tipo['Value'] for tipo in self._consulta_origen_pedidos
                             if order_type_origin_id == tipo['ID']][0]

        order_delivery_type_id = self.info_pedido['OrderDeliveryTypeID']

        order_delivery_type = [tipo['DeliveryTypesName'] for tipo in self._consulta_tipos_entrega
                               if order_delivery_type_id == tipo['DeliveryTypesID']][0]

        priority_id = self.info_pedido['PriorityID']

        priority = [tipo['Value'] for tipo in self._consulta_prioridad_pedidos
                    if priority_id == tipo['ID']][0]

        address_detail_id = self.info_pedido['AddressDetailID']
        address_name = [tipo['AddressName'] for tipo in self._consulta_direcciones
                        if address_detail_id == tipo['AddressDetailID']][0]


        delivery_promise = self.info_pedido['DeliveryPromise']

        self._ventanas.insertar_input_componente('cbx_documento', self.info_pedido['DocumentType'])
        self._ventanas.insertar_input_componente('cbx_direccion', address_name)
        self._ventanas.insertar_input_componente('cbx_prioridad', priority)
        self._ventanas.insertar_input_componente('den_fecha', delivery_promise)
        self._ventanas.insertar_input_componente('cbx_entrega', order_delivery_type)
        self._ventanas.insertar_input_componente('cbx_origen', order_type_origin)
        self._ventanas.insertar_input_componente('cbx_tipo', order_type)
        self._ventanas.insertar_input_componente('txt_comentario', comments)
        self._ventanas.insertar_input_componente('cbx_forma_pago', payment_term_name)



        schedule_order_id = self.info_pedido['ScheduleID']
        if self._consulta_horarios:
            schedule_order = [tipo['Value'] for tipo in self._consulta_horarios
                              if int(schedule_order_id) == int(tipo['ScheduleID'])][0]
            if schedule_order:
                self._ventanas.insertar_input_componente('cbx_horario', schedule_order)

        if self._consulta_sucursales:
            depot_id = self.info_pedido['DepotID']

            if depot_id != 0:
                depot_name = [tipo['DepotName'] for tipo in self._consulta_sucursales
                              if depot_id == tipo['DepotID']][0]
                self._ventanas.insertar_input_componente('cbx_sucursal', depot_name)

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
            minutos_transcurridos = int(valores_fila[6])

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
        respuesta = self._ventanas.mostrar_mensaje_pregunta(
            f'Desea relacionar el {tipo_pedido} con el pedido {folio_pedido}')

        if not respuesta:
            return

        order_document_id = int(valores_fila[5])

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

        self._bloquear_componentes_segun_tipo_pedido(tipo_pedido)
        self._actualizar_parametros_nuevos_anexo_o_cambio(order_document_id, tipo_pedido)

    def _actualizar_parametros_nuevos_anexo_o_cambio(self, order_document_id, tipo_pedido):
        self.parametros_pedido['OrderTypeID'] = 2 if tipo_pedido == 'Anexo' else 3
        self.parametros_pedido['RelatedOrderID'] = order_document_id
        self.parametros_pedido['CreatedOn'] = datetime.now()
        self.parametros_pedido['CreatedBy'] = self._parametros.id_usuario
        self.parametros_pedido['HostName'] = self._utilerias.obtener_hostname()

    def _bloquear_componentes_segun_tipo_pedido(self, tipo_pedido):
        # bloquear los componentes
        componentes_a_bloquear_anexo = ['den_fecha', 'cbx_tipo', 'cbx_horario', 'cbx_origen', 'cbx_entrega',
                                        'cbx_forma_pago', 'cbx_prioridad']

        componentes_a_bloquear_cambio = ['den_fecha', 'cbx_tipo',
                                         'cbx_prioridad']

        componentes_a_bloquear = componentes_a_bloquear_anexo if tipo_pedido == 'Anexo' else componentes_a_bloquear_cambio

        for nombre in componentes_a_bloquear:
            self._ventanas.bloquear_componente(nombre)

    def _validar_inputs_formulario(self):
        for nombre, componente in self._ventanas.componentes_forma.items():

            tipo = nombre[:3]  # 'den' o 'cbx'

            if tipo == 'den':
                fecha_entrega = self._ventanas.obtener_input_componente('den_fecha')
                # valida que exista y no sea menor a hoy
                if not fecha_entrega or fecha_entrega < self._hoy:
                    self._ventanas.mostrar_mensaje('La fecha de entrega no puede ser menor a la fecha actual.')
                    return False

            if tipo == 'cbx':
                seleccion = self._ventanas.obtener_input_componente(nombre)

                if nombre == 'cbx_documento' and seleccion == 'Seleccione':
                    self._ventanas.mostrar_mensaje('Debe seleccionar un tipo de documento válido.')
                    return False

                if nombre == 'cbx_sucursal' and seleccion == 'Seleccione':
                    self._ventanas.mostrar_mensaje('Debe seleccionar una sucursal válida.')
                    return False

                if nombre == 'cbx_direccion' and seleccion == 'Seleccione':
                    self._ventanas.mostrar_mensaje('Debe seleccionar una dirección válida.')
                    return False

                if nombre == 'cbx_tipo' and seleccion not in ('Seleccione', 'Pedido'):
                    comentario = (self._ventanas.obtener_input_componente('txt_comentario') or '').strip()
                    if len(comentario) < 5:
                        self._ventanas.mostrar_mensaje(
                            'Para anexos y cambios el comentario es obligatorio (mínimo 5 caracteres).'
                        )
                        return False

                if seleccion == 'Seleccione':
                    etiqueta = nombre[4:].replace('_', ' ').capitalize()
                    self._ventanas.mostrar_mensaje(f'Debe seleccionar una opción válida para {etiqueta}.')
                    return False

        if not self._validar_fecha_pedido():
            return False

        return True

    def _procesar_seleccion_usuario(self):

        tipo_pedido = self._ventanas.obtener_input_componente('tbx_tipo')
        if tipo_pedido in ('Anexo', 'Cambio'):
            return

        componentes = {
            'cbx_direccion': (self._consulta_direcciones, 'AddressDetailID', 'AddressName', 'AddressDetailID'),
            'cbx_tipo': (self._consulta_tipos_pedidos, 'ID', 'Value', 'OrderTypeID'),
            'cbx_documento': (self._consulta_tipo_documentos, 'ID', 'Value', 'DocumentTypeID'),

            'cbx_origen': (self._consulta_origen_pedidos, 'ID', 'Value', 'OrderTypeOriginID'),
            'cbx_horario': (self._consulta_horarios, 'ScheduleID', 'Value', 'ScheduleID'),
            'cbx_entrega': (
            self._consulta_tipos_entrega, 'DeliveryTypesID', 'DeliveryTypesName', 'OrderDeliveryTypeID'),
            'cbx_prioridad': (self._consulta_prioridad_pedidos, 'ID', 'Value', 'PriorityID'),
            'cbx_forma_pago': (self._consulta_formas_pago, 'PaymentTermID', 'PaymentTermName', 'WayToPayID')
        }
        valores_pedido = {}
        for nombre, (consulta, campo_consulta, seleccion_consulta, campo_tabla) in componentes.items():
            seleccion = self._ventanas.obtener_input_componente(nombre)

            valor = [reg[campo_consulta] for reg in consulta if seleccion == reg[seleccion_consulta]][0]
            valores_pedido[campo_tabla] = valor

        valores_pedido['DeliveryPromise'] = self._ventanas.obtener_input_componente('den_fecha')
        comentario_pedido = self._ventanas.obtener_input_componente('txt_comentario')
        valores_pedido['CommentsOrder'] = comentario_pedido.upper().strip() if comentario_pedido else ''
        valores_pedido['BusinessEntityID'] = self._business_entity_id

        related_order_id = self.parametros_pedido.get('RelatedOrderID', 0)
        valores_pedido['RelatedOrderID'] = related_order_id
        valores_pedido['ZoneID'] = self.info_pedido['ZoneID']
        valores_pedido['OrderDeliveryCost'] = self._base_de_datos.buscar_costo_servicio_domicilio(valores_pedido['AddressDetailID'])

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

        #caso especial sucursales
        if not self._consulta_sucursales:
            valores_pedido['DepotID'] = self.info_pedido['DepotID']
        else:
            depot_name = self._ventanas.obtener_input_componente('cbx_sucursal')
            depot_id = [tipo['DepotID'] for tipo in self._consulta_sucursales
                          if depot_name == tipo['DepotName']][0]
            valores_pedido['DepotID'] = depot_id

        self.parametros_pedido = valores_pedido

    def _guardar_parametros_pedido(self):
        if self._validar_inputs_formulario():
            self._procesar_seleccion_usuario()

            order_related_id = self.parametros_pedido['RelatedOrderID']
            tipo_pedido = self._ventanas.obtener_input_componente('cbx_tipo')

            if tipo_pedido in ('Anexo', 'Cambio') and order_related_id == 0:
                self._ventanas.mostrar_mensaje('Debe relacionar el anexo o el cambio con un pedido.')
                self.parametros_pedido = {}
            else:

                # aqui actualiza el horario de un pedido de viene a hora de entrega a 1 hora despues de procesado
                order_delivery_type_id = self.parametros_pedido['OrderDeliveryTypeID']
                if order_delivery_type_id == 2:
                    self._actualizar_horario_de_viene()

                self._actualizar_docdocument_order_cayal(self._order_document_id, self.parametros_pedido)

                # para el caso de anexo o cambio hay que marcarlos como urgentes en el horario mas cercano a realizar
                # en caso que la orden sea un anexo o un pedido hay que actualizar dicho documento
                if tipo_pedido in ('Anexo', 'Cambio'):
                    consulta_completa = self._base_de_datos.buscar_horarios_pedido_cayal()

                    horario_disponible = [hora for hora in consulta_completa if
                                          datetime.strptime(hora['Value'], "%H:%M").time() > self._hora_actual()]
                    schedule_id = 1

                    order_type_id = 2 if tipo_pedido == 'Anexo' else 3

                    if horario_disponible:
                        schedule_id = horario_disponible[0]['ScheduleID']
                        schedule_id_order_related = [hora['ScheduleID'] for hora in consulta_completa
                                                     if self._ventanas.obtener_input_componente('cbx_horario') == hora['Value']
                                                    ][0]
                        schedule_id = schedule_id_order_related if schedule_id <= schedule_id_order_related else schedule_id

                    self._base_de_datos.command(
                        """
                        DECLARE @OrderID INT = ?
                        UPDATE docDocumentOrderCayal
                        SET NumberAdditionalOrders = (SELECT Count(OrderDocumentID)
                                                     FROM docDocumentOrderCayal
                                                     WHERE RelatedOrderID = @OrderID AND CancelledOn IS NULL),
                            StatusID = 2,
                            ScheduleID = ?, 
                            PriorityID = 2,
                            OrderTypeID = ?
                        WHERE OrderDocumentID = @OrderID
                        """,
                        (self._order_document_id, schedule_id, order_type_id)
                    )

                self._master.destroy()

    def _actualizar_docdocument_order_cayal(self, order_document_id, valores_actualizacion):
        """
        Actualiza la tabla 'docdocumentordercayal' con los valores proporcionados en el diccionario.

        :param order_document_id: ID del documento de pedido a actualizar.
        :param valores_actualizacion: Diccionario con los campos y valores a actualizar.
        """
        # Crear la parte dinámica del SET en el query
        campos_set = ", ".join([f"{campo} = ?" for campo in valores_actualizacion.keys()])

        # Crear el query SQL dinámico
        query = f"""
            UPDATE docDocumentOrderCayal
            SET {campos_set}
            WHERE OrderDocumentID = ?
        """

        # Preparar los valores en el orden correcto
        valores = list(valores_actualizacion.values()) + [order_document_id]

        # Ejecutar el comando
        self._base_de_datos.command(query, tuple(valores))

        # Actualiza la bitacora de cambios
        self._actualizar_bitacora(valores_actualizacion)

    def _actualizar_bitacora(self, valores_actualizacion):
        claves_bitacora = self._encontrar_claves_diferentes(self.info_pedido, valores_actualizacion)

        valores_bitacora = {

            'AddressDetailID':  (26, 'Dirección actualizada:', self._consulta_direcciones, 'AddressName', 'AddressDetailID'),
            'OrderTypeID': (44,'Tipo de orden cambiada:', self._consulta_tipos_pedidos, 'Value', 'ID'),
            'OrderTypeOriginID': (28,'Origen de orden actualizada:', self._consulta_origen_pedidos, 'Value', 'ID'),
            'ScheduleID': (21,'Horario actualizado:', self._consulta_horarios, 'Value', 'ScheduleID'),
            'OrderDeliveryTypeID': (25,'Forma de entrega actualizada:', self._consulta_tipos_entrega, 'DeliveryTypesName', 'DeliveryTypesID'),
            'PriorityID': (29,'Prioridad actualizada:', self._consulta_prioridad_pedidos, 'Value','ID'),
            'WayToPayID': (24,'Forma de pago actualizada:', self._consulta_formas_pago, 'PaymentTermName', 'PaymentTermID'),
            'DeliveryPromise': (22,'Promesa de entrega actualizada:', None, None),
            'CommentsOrder': (30,'Comentario modificado:', None, None),
            'RelatedOrderID': (45,'Relación agregada:', None, None),
            'DocumentTypeID': (46,'Tipo documento actualizado:', self._consulta_tipo_documentos, 'Value', 'ID'),
            'OrderDeliveryCost': (47,'Costo de envío actualizado'),
            'DepotID': (27, 'Sucursal actualizada:', self._consulta_sucursales, 'DepotName', 'DepotID')
        }
        user_name = self._base_de_datos.buscar_nombre_de_usuario(self._user_id)

        for clave in claves_bitacora:
            try:
                change_type_id = valores_bitacora[clave][0]
                comentario = valores_bitacora[clave][1]

                valor_nuevo = ''
                valor_anterior = ''
                consulta = valores_bitacora[clave][2]
                valor_buscado = ''
                valor_buscado_id = 0

                if clave not in ('DeliveryPromise', 'CommentsOrder', 'RelatedOrderID'):
                    valor_buscado = valores_bitacora[clave][3]
                    valor_buscado_id = valores_bitacora[clave][4]

                if clave not in ('ScheduleID','DepotID','DeliveryPromise', 'CommentsOrder', 'RelatedOrderID'):
                    valor_nuevo = [reg[valor_buscado] for reg in consulta if  reg[valor_buscado_id] == valores_actualizacion[clave]][0]
                    valor_anterior = [reg[valor_buscado] for reg in consulta if reg[valor_buscado_id] == self.info_pedido[clave]][0]

                if clave == 'ScheduleID':
                    valor_nuevo = [reg[valor_buscado] for reg in consulta if reg[valor_buscado_id] == valores_actualizacion[clave]][0]

                if clave == 'DepotID' and self._consulta_sucursales:
                    valor_nuevo = [reg[valor_buscado] for reg in consulta if reg[valor_buscado_id] == valores_actualizacion[clave]][0]
                    if self.info_pedido[clave] != 0:
                        valor_anterior = [reg[valor_buscado] for reg in consulta if reg[valor_buscado_id] == self.info_pedido[clave]][0]

                if clave in ('CommentsOrder', 'DeliveryPromise'):
                    valor_nuevo = valores_actualizacion[clave]
                    valor_anterior = self.info_pedido[clave]

                if clave ==  'RelatedOrderID':
                    nueva_consulta =  self._base_de_datos.buscar_info_documento_pedido_cayal(valores_actualizacion[clave])
                    if consulta:
                        info_pedido = nueva_consulta[0]
                        valor_nuevo = info_pedido['DocFolio']

                comentario = f"{comentario} {user_name} - {valor_anterior} --> {valor_nuevo}"
                self._base_de_datos.insertar_registro_bitacora_pedidos(self._order_document_id,
                                                                       change_type_id=change_type_id,
                                                                       comments=comentario,
                                                                       user_id=self._user_id)
            except:
                print(clave)

    def _encontrar_claves_diferentes(self, dict1, dict2):
        """
        Compara dos diccionarios y devuelve una lista de claves con valores diferentes.
        :param dict1: Primer diccionario.
        :param dict2: Segundo diccionario.
        :return: Lista de claves con valores diferentes.
        """
        # Verificar las claves compartidas entre ambos diccionarios
        claves_comunes = set(dict1.keys()).intersection(set(dict2.keys()))
        # Encontrar las claves con valores diferentes
        claves_diferentes = [
            clave for clave in claves_comunes if dict1[clave] != dict2[clave]
        ]
        return claves_diferentes