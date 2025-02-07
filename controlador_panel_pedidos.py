from datetime import datetime
from buscar_pedido import BuscarPedido
from cayal.login import Login
from buscar_generales_cliente import BuscarGeneralesCliente
from editar_caracteristicas_pedido import EditarCaracteristicasPedido
from historial_pedido import HistorialPedido
from ticket_pedido_cliente import TicketPedidoCliente
from panel_principal_cliente import PanelPrincipal
from selector_tipo_documento import SelectorTipoDocumento


class ControladorPanelPedidos:
    def __init__(self, modelo):
        self._modelo = modelo
        self._interfaz = modelo.interfaz
        self._base_de_datos = self._modelo.base_de_datos
        self._utilerias = self._modelo.utilerias
        self._parametros = self._modelo.parametros
        self._number_orders = 0
        self._user_id = self._parametros.id_usuario
        self._user_name = self._base_de_datos.buscar_nombre_de_usuario(self._user_id)
        self._partidas_pedidos = {}


        self._crear_tabla_pedidos()
        self._rellenar_tabla_pedidos(self._fecha_seleccionada())
        self._crear_barra_herramientas()

        self._cargar_eventos()
        self._interfaz.ventanas.configurar_ventana_ttkbootstrap(titulo='Panel pedidos')

    def _cargar_eventos(self):
        eventos = {

            'den_fecha': lambda event: self._rellenar_tabla_pedidos(self._fecha_seleccionada()),
            'tbv_pedidos': (lambda event: self._rellenar_tabla_detalle(), 'doble_click'),
            'cbx_capturista': lambda event: self._filtrar_por_capturados_por(),
            'cbx_status': lambda event: self._filtrar_por_status(),
            'cbx_horarios': lambda event: self._filtrar_por_horas()

        }
        self._interfaz.ventanas.cargar_eventos(eventos)

        evento_adicional = {
            'tbv_pedidos': (lambda event: self._actualizar_comentario_pedido(), 'seleccion')
        }
        self._interfaz.ventanas.cargar_eventos(evento_adicional)

        self._interfaz.ventanas.agregar_callback_table_view_al_actualizar('tbv_pedidos',self._colorear_filas_panel_horarios)

    def _limpiar_componentes(self):
        self._interfaz.ventanas.limpiar_componentes(['tbx_comentarios', 'tvw_detalle'])

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
        self._limpiar_componentes()
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
            if not fecha_entrega_str:
                return 1

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
                return 0

            if schedule_id == 1:
                return 1

            if schedule_id == 2:
                return 2

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

    def _capturar_nuevo_cliente(self):
        ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
        instancia = PanelPrincipal(ventana, self._parametros, self._base_de_datos, self._utilerias)
        ventana.wait_window()

    def _capturar_nuevo(self):
        ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
        self._parametros.id_principal = -1
        instancia = BuscarGeneralesCliente(ventana, self._parametros)
        #ventana.wait_window()
        self._parametros.id_principal = 0

    def _editar_caracteristicas(self):
        fila = self._seleccionar_una_fila()
        if not fila:
            return

        status = fila[0]['TypeStatusID']

        if status == 10:
            self._interfaz.ventanas.mostrar_mensaje('NO se pueden editar pedidos cancelados.')
            return

        elif status >= 4:
            self._interfaz.ventanas.mostrar_mensaje('Sólo se pueden afectar las caracteristicas de un pedido hasta el status  Por timbrar.')
            return
        else:
            order_document_id = fila[0]['OrderDocumentID']
            self._parametros.id_principal = order_document_id

            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
            instancia = EditarCaracteristicasPedido(ventana, self._parametros, self._base_de_datos, self._utilerias)
            ventana.wait_window()
            self._parametros.id_principal = 0

            self._rellenar_tabla_pedidos(self._fecha_seleccionada())

    def _crear_ticket(self):

        fila = self._seleccionar_una_fila()
        if not fila:
            return

        order_document_id = fila[0]['OrderDocumentID']
        consulta = self._base_de_datos.fetchall("""
            SELECT
             CASE WHEN DeliveryPromise IS NULL THEN 0 ELSE 1 END StatusEntrega,
                DeliveryPromise FechaEntrega
            FROM docDocumentOrderCayal 
            WHERE OrderDocumentID = ?
            """,(order_document_id,))
        status_entrega = consulta[0]['StatusEntrega']


        if status_entrega == 0:
            self._interfaz.ventanas.mostrar_mensaje('Debe definir la forma de pago del cliente antes de generar el ticket.')
            return
        else:
            fecha_entrega = self._utilerias.convertir_fecha_str_a_datetime(str(consulta[0]['FechaEntrega'])[0:10])
            if fecha_entrega > self._modelo.hoy:
                respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                    'EL pedido es para una fecha de entrega posterior, ¿Desea actualizar los precios antes de generar el ticket?')

                if respuesta:
                    self._base_de_datos.actualizar_precios_pedido(order_document_id)

            self._parametros.id_principal = order_document_id
            instancia = TicketPedidoCliente(self._base_de_datos, self._utilerias, self._parametros)

            self._parametros.id_principal = 0
            self._interfaz.ventanas.mostrar_mensaje('Comprobante generado.')

    def _mandar_a_producir(self):

        filas = self._validar_seleccion_multiples_filas()
        if not filas:
            return

        for fila in filas:
            order_document_id = fila['OrderDocumentID']
            consulta = self._base_de_datos.fetchall("""
                SELECT StatusID, 
                    CASE WHEN DeliveryPromise IS NULL THEN 0 ELSE 1 END Entrega,
                    ISNULL(FolioPrefix,'')+ISNULL(Folio,'') DocFolio
                FROM docDocumentOrderCayal 
                WHERE OrderDocumentID = ?
            """,(order_document_id,))

            status = consulta[0]['StatusID']
            entrega = consulta[0]['Entrega']
            folio = consulta[0]['DocFolio']

            if entrega == 0:
                self._interfaz.ventanas.mostrar_mensaje(
                    f'Debe usar la herramienta de editar características para el pedido {folio}.')
                continue

            if status == 1:
                self._base_de_datos.command("""
                     UPDATE docDocumentOrderCayal SET SentToPrepare = GETDATE(),
                                                    SentToPrepareBy = ?,
                                                    StatusID = 2,
                                                    UserID = NULL
                    WHERE OrderDocumentID = ?
                """,(self._user_id, order_document_id,))

                comentario = f'Enviado a producir por {self._user_name}.'
                self._base_de_datos.insertar_registro_bitacora_pedidos(order_document_id=order_document_id,
                                                                       change_type_id=2,
                                                                       user_id=self._user_id,
                                                                       comments=comentario)

        self._rellenar_tabla_pedidos(self._fecha_seleccionada())

    def _confirmar_transferencia(self):
        fila = self._seleccionar_una_fila()
        if not fila:
            return

        way_to_pay_id = fila[0]['WayToPayID']
        if way_to_pay_id != 6:
            self._interfaz.ventanas.mostrar_mensaje('Solo aplica para formas de pago transferencia.')
            return

        order_document_id = fila[0]['OrderDocumentID']
        document_id = self._base_de_datos.fetchone(
            'SELECT DocumentID FROM docDocumentOrderCayal WHERE OrderDocumentID = ?', (order_document_id,)
                                                  )
        if document_id == 0:
            self._interfaz.ventanas.mostrar_mensaje(
                'Solo puede confirmar transferencias cuando el documento a sido generado.')
            return

        consulta = self._base_de_datos.fetchall("""
            SELECT Balance, StatusPaidID FROM docDocument WHERE DocumentID = ?
        """,(document_id,))

    def _combinar_envio(self):
        pass

    def _inciar_facturacion(self):
        self._facturar()
        self._rellenar_tabla_pedidos(self._fecha_seleccionada())

    def _facturar(self):

        filas = self._validar_seleccion_multiples_filas()

        if not filas:
            return

        filas_filtradas_por_status = self._filtrar_filas_facturables_por_status(filas)

        # filtra por status 3 que es por timbrar
        if not filas_filtradas_por_status:
            self._interfaz.ventanas.mostrar_mensaje('No hay pedidos con un status válido para facturar')
            return

        #--------------------------------------------------------------------------------------------------------------
        # aqui comenzamos el procesamiento de las filas a facturar
        # si es una seleccion unica valida primero si no hay otros pendientes del mimsmo cliente
        if len(filas) == 1:
            hay_pedidos_del_mismo_cliente = self._buscar_pedidos_en_proceso_del_mismo_cliente(filas)

            if not hay_pedidos_del_mismo_cliente:
                self._crear_documento(filas)

            if hay_pedidos_del_mismo_cliente:
                respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta('Hay otro pedido del mismo cliente en proceso o por timbrar.'
                                                                             '¿Desea continuar?')
                if respuesta:
                    self._crear_documento(filas)
            return

        # si hay mas de una fila primero valida que estas filas no tengan solo el mismo cliente
        # si lo tuvieran hay que ofrecer combinarlas en un documento
        tienen_el_mismo_cliente = self._validar_si_los_pedidos_son_del_mismo_cliente(filas)
        if tienen_el_mismo_cliente:
            respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta('Los pedidos son del mismo cliente.'
                                                                         '¿Desea combinarlos?')
            if respuesta:
                self._crear_documento(filas, combinado=True, mismo_cliente=True)
                return

        # del mismo modo que para una fila valida que no existan otras ordenes de un cliente en proceso
        # si lo hay para un cliente ese cliente debe excluirse de la seleccion
        filas_filtradas = self._excluir_pedidos_con_ordenes_en_proceso_del_mismo_cliente(filas)
        if not filas_filtradas:
            return

        self._crear_documento(filas_filtradas)
        return

    def _crear_documento(self, filas, combinado=False, mismo_cliente=False):

        tipo_documento = 1 # remision

        # determina el tipo de documento que se generará ya sea remision y/o factura
        if len(filas) > 1 and combinado:
            tipos_documento = list(set([fila['DocumentTypeID'] for fila in filas]))
            if len(tipos_documento) == 1:
                tipo_documento = tipos_documento[0]
            else:
                tipo_documento = -1
                while tipo_documento == -1:
                    ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
                    instancia = SelectorTipoDocumento(ventana)
                    ventana.wait_window()
                    tipo_documento = instancia.tipo_documento


        # cuantificamos el valor de todas las partidas involucradas excluyendo el servicio a domicilio
        # y determinamos si superan el valor 200

        filas_valorizadas = self._cuantificar_valor_partidas_documento(filas, mismo_cliente)
        if not filas_valorizadas:
            self._interfaz.ventanas.mostrar_mensaje('No hay ningún documento que generar.')
            return

        # aqui creamos el o los documentos pertinentes
        # si es un documento por cada orden no hay problema se toma el tipo desde la fila
        document_id = 0
        total_acumulado = 0
        partidas_acumuladas = []
        for fila in filas_valorizadas:
            order_document_id =  fila['OrderDocumentID']
            address_detail_id = fila['AddressDetailID']

            info_documento = self._partidas_pedidos.get(order_document_id, None)
            if not info_documento:
                continue

            # info documento es una tupla donde el primer elemento es el total del documento y el segundo las partidas
            # en este punto los documentos valorizados ya estan filtrado despues de n validaciones
            total_documento = info_documento[0]
            partidas = info_documento[1]

            if not combinado:
                tipo_documento = fila['DocumentTypeID']
                document_id = self._crear_cabecera_documento(tipo_documento, fila)
                self._insertar_partidas_documento(order_document_id, document_id, partidas, total_documento, address_detail_id)

                # relacionar documenrtosa con pedidos
                self._actualizar_status_y_relacionar(document_id, order_document_id)

                # agregar documento para recalculo
                self._base_de_datos.exec_stored_procedure('zvwRecalcularPedidos', (document_id, order_document_id))

                # afectar bitacora
                self._afectar_bitacora_de_cambios(document_id, [order_document_id])


            else:
                partidas_acumuladas.extend(partidas)
                total_acumulado += total_documento

        # proceso concluido si no fue combinado el documento
        if not combinado:
            return

        # aplica para documentos combinados
        order_document_ids = sorted([fila['OrderDocumentID'] for fila in filas if fila['OrderTypeID'] == 1], reverse=True)
        if not order_document_ids:
            self._interfaz.ventanas.mostrar_mensaje('Debe por lo menos haber un pedido dentro de las ordenes seleccionadas.')
            return

        order_document_id = order_document_ids[0]
        address_detail_id = filas[0]['AddressDetailID']

        # crea cabecera y bloqueala para evitar ediciones
        document_id = self._crear_cabecera_documento(tipo_documento, filas[0])


        self._insertar_partidas_documento(order_document_id, document_id, partidas_acumuladas, total_acumulado, address_detail_id)

        # relacionar pedidos con factura
        for order in order_document_ids:
            self._actualizar_status_y_relacionar(document_id, order)

        # relacionar pedido principal con pedidos
        for order in order_document_ids:
            if order != order_document_id:
                self._base_de_datos.command(
                    'UPDATE docDocumentOrderCayal SET RelatedOrderID = ? WHERE OrderDocumentID = ?',
                    (order_document_id, order)
                )

        # agregar documento para recalculo
        self._base_de_datos.exec_stored_procedure('zvwRecalcularPedidos', (document_id, order_document_id))

        # afectar la bitacora de cambios
        self._afectar_bitacora_de_cambios(document_id, order_document_ids)

    def _afectar_bitacora_de_cambios(self, document_id, order_document_ids):

        folio = self._base_de_datos.fetchone(
            "SELECT ISNULL(FolioPrefix,'')+ISNULL(Folio,'') DocFolio FROM docDocument WHERE DocumentID = ?",
            (document_id,))
        comentario = f"Documento creado por {self._user_name} - {folio}"

        for order_document_id in order_document_ids:
            self._base_de_datos.insertar_registro_bitacora_pedidos(order_document_id,
                                                                   change_type_id=4,
                                                                   comments=comentario,
                                                                   user_id=self._user_id)

            self._base_de_datos.command(
                """
                UPDATE docDocumentOrderCayal 
                SET 
                    SentToInvoice = CASE 
                        WHEN SentToInvoice IS NULL THEN GETDATE() 
                        ELSE SentToInvoice 
                    END,
                    SentToInvoiceBy = CASE 
                        WHEN SentToInvoiceBy > 0 THEN SentToInvoiceBy 
                        ELSE ? 
                    END
                WHERE OrderDocumentID = ?;
                """,
                (self._user_id, order_document_id)
            )

    def _actualizar_status_y_relacionar(self, document_id, order_document_id):
        self._base_de_datos.command(
            """
            DECLARE @DocumentID INT = ?
            DECLARE @OrderDocumentID INT  = ?

            -- Actualizar la tabla docDocumentOrderCayal
            UPDATE docDocumentOrderCayal
            SET StatusID = 4, DocumentID = @DocumentID
            WHERE OrderDocumentID = @OrderDocumentID;

            -- Insertar en la tabla OrderInvoiceDocumentCayal
            INSERT INTO OrderInvoiceDocumentCayal (OrderDocumentID, DocumentID)
            VALUES (@OrderDocumentID, @DocumentID);
            
            """,
            (document_id, order_document_id)
        )

    def _insertar_partidas_documento(self, order_document_id, document_id, partidas, total_documento, address_detail_id):
        if total_documento < 200:
            self._insertar_servicio_a_docimicilio(document_id, address_detail_id)

        for partida in partidas:
            parametros = (
                document_id,
                partida['ProductID'],
                2,  # depot_id
                partida['Quantity'],
                partida['UnitPrice'],
                0,  # costo,
                partida['Subtotal'],
                partida['TipoCaptura'],  # tipo captura
                21  # modulo
            )
            self._base_de_datos.insertar_partida_documento_cayal(parametros)

    def _insertar_servicio_a_docimicilio(self, document_id, address_detail_id):
        precio_servicio = self._base_de_datos.fetchone(
            'SELECT * FROM [dbo].[zvwBuscarCargoEnvio-AddressDetailID](?)',
            (address_detail_id,))

        precio_servicio_sin_impuesto = self._utilerias.calcular_monto_sin_iva(precio_servicio)
        parametros = (
            document_id,
            5606,  # product_id
            2,  # depot_id
            1,
            precio_servicio_sin_impuesto,
            0,  # costo,
            precio_servicio_sin_impuesto,
            0,  # tipo captura
            21  # modulo
        )
        self._base_de_datos.insertar_partida_documento_cayal(parametros)

    def _crear_cabecera_documento(self, document_type_id, fila):
        document_id = self._base_de_datos.crear_documento(
            document_type_id,
            'FM', # prefijo mayoreo
            fila['BusinessEntityID'],
            21, # modulo facturas mayoreo
            self._user_id,
            fila['DepotID']
        )

        order_document_id = fila['OrderDocumentID']

        self._base_de_datos.command('UPDATE docDocument SET ExportID = 6, OrderDocumentID = ? WHERE DocumentID = ?',
                                    (order_document_id, document_id))

        return document_id

    def _cuantificar_valor_partidas_documento(self, filas, mismo_cliente=False):
        # validar que el monto sea superior a 180 debito a que el cliente podria anexar un producto y con ello
        # evitar generar la factura correspondiente

        total_acumulado = 0
        filas_filtradas = []
        for fila in filas:
            order_document_id = fila['OrderDocumentID']
            total_documento = self._calcular_total_pedido(order_document_id)
            print(total_documento, mismo_cliente)
            if total_documento < 181 and not mismo_cliente:
                cliente = fila['Cliente']
                pedido = fila['Pedido']

                respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(f'El total de la orden {pedido} del cliente {cliente}'
                                                                 f'es de {total_documento}, ¿Desea omitir este pedido del proceso para consultar con el cliente un posible incremento en su pedido?'
                                                                 )
                if respuesta:
                    continue

                filas_filtradas.append(fila)
                continue

            if mismo_cliente:
                total_acumulado += total_documento
                continue

            if total_documento >  200:
                filas_filtradas.append(fila)
                continue

        if mismo_cliente and total_acumulado < 181:
            cliente = filas[0]['Cliente']

            respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                f'El total acumulado de las ordenes seleccionadas del cliente {cliente}'
                f'es de {total_acumulado}, ¿Desea consultar con el cliente un posible incremento en su pedido?'
                )

            if respuesta:
                return []

            return filas

        if mismo_cliente and total_acumulado > 180:
            return filas

        return filas_filtradas

    def _calcular_total_pedido(self, order_document_id):

        consulta_partidas = self._modelo.base_de_datos.buscar_partidas_pedidos_produccion_cayal(
           order_document_id, partidas_producidas=True)

        consulta_partidas_con_impuestos = self._modelo.utilerias.agregar_impuestos_productos(consulta_partidas)
        subtotal = 0
        total_tax = 0
        totales = 0
        nuevas_partidas = []
        for producto in consulta_partidas_con_impuestos:
            precio = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(producto['UnitPrice'])
            precio_con_impuestos = producto['SalePriceWithTaxes']
            cantidad_decimal = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(producto['Quantity'])
            total = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(precio_con_impuestos * cantidad_decimal)
            product_id = producto['ProductID']

            if product_id == 5606:
                continue

            subtotal += (precio * cantidad_decimal)
            total_tax += (precio_con_impuestos - precio)
            totales += total

            nuevas_partidas.append(producto)

        self._partidas_pedidos[order_document_id] = (totales, nuevas_partidas)

        return totales

    def _validar_si_los_pedidos_son_del_mismo_cliente(self, filas):
        business_entity_ids = []
        for fila in filas:
            business_entity_id = fila['BusinessEntityID']
            business_entity_ids.append(business_entity_id)

        business_entity_ids = list(set(business_entity_ids))
        if len(business_entity_ids) == 1:
            return True
        return False

    def _excluir_pedidos_con_ordenes_en_proceso_del_mismo_cliente(self, filas):


        filas_filtradas = []
        clientes_en_proceso = []
        order_document_ids = [filas[0]['OrderDocumentID']] # agrega el primer pedido a la lista para comparaciones
        for fila in filas:
            hay_pedidos_del_mismo_cliente_en_proceso = self._buscar_pedidos_en_proceso_del_mismo_cliente(fila)
            if not hay_pedidos_del_mismo_cliente_en_proceso:
                filas_filtradas.append(fila)
            else:
                order_document_id = fila['OrderDocumentID']
                if order_document_id not in order_document_ids:
                    clientes_en_proceso.append(fila['Cliente'])
        texto = ''
        if clientes_en_proceso:
            clientes_en_proceso = set(clientes_en_proceso)
            for cliente in clientes_en_proceso:
                texto = f'{texto} {cliente},'
            self._interfaz.ventanas.mostrar_mensaje(f'Los clientes: {texto} tienen más órdenes en proceso o por timbrar.')
        return filas_filtradas

    def _buscar_pedidos_en_proceso_del_mismo_cliente(self, fila):
        business_entity_id = fila[0]['BusinessEntityID'] if isinstance(fila, list) else fila['BusinessEntityID']
        order_document_id = fila[0]['OrderDocumentID'] if isinstance(fila, list) else fila['OrderDocumentID']

        pedidos_del_mismo_cliente = 0

        filas = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos')

        for fila in filas:
            business_entity_id_fila = fila['BusinessEntityID']
            order_document_id_fila = fila['OrderDocumentID']
            status_id = fila['TypeStatusID']

            if order_document_id_fila == order_document_id:
                continue
            if business_entity_id_fila == business_entity_id:
                if status_id in (2, 3, 16, 17, 18):
                    pedidos_del_mismo_cliente += 1
                    continue

        if pedidos_del_mismo_cliente > 0:
            return True

        return False

    def _filtrar_filas_facturables_por_status(self, filas):
        filas_filtradas = []

        # filtrar por status
        for fila in filas:
            status_id = fila['TypeStatusID']
            # pedido por timbrar es status 3
            if status_id != 3:
                continue

            filas_filtradas.append(fila)

        return filas_filtradas

    def _editar_pedido(self):
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

    def _validar_seleccion_una_fila(self):
        if not self._interfaz.ventanas.validar_seleccion_una_fila_table_view('tbv_pedidos'):
            return

        return self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)[0]

    def _historial_pedido(self):
        valores_fila = self._validar_seleccion_una_fila()
        if not valores_fila:
            return
        order_document_id = valores_fila['OrderDocumentID']

        ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(titulo='Historial pedido')
        self._parametros.id_principal = order_document_id
        instancia = HistorialPedido(ventana, self._parametros, self._base_de_datos)
        ventana.wait_window()
        self._parametros.id_principal = 0

    def _cambiar_usuario(self):
        def si_acceso_exitoso(parametros=None, master=None):
            self._parametros = parametros
            self._rellenar_operador()

        ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
        instancia = Login(ventana, self._parametros, si_acceso_exitoso)
        ventana.wait_window()

    def _crear_barra_herramientas(self):
        self.barra_herramientas_pedido = [

            {'nombre_icono': 'Customer32.ico', 'etiqueta': 'Nuevo', 'nombre': 'nuevo_cliente',
             'hotkey': None, 'comando': self._capturar_nuevo_cliente},

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

            {'nombre_icono': 'lista-de-verificacion.ico', 'etiqueta': 'Editar', 'nombre': 'editar',
             'hotkey': None, 'comando': self._editar_pedido},

            {'nombre_icono': 'Invoice32.ico', 'etiqueta': 'Facturar', 'nombre': 'facturar',
             'hotkey': None, 'comando': self._inciar_facturacion},

            {'nombre_icono': 'warning.ico', 'etiqueta': 'A.Queja', 'nombre': 'agregar_queja',
             'hotkey': None, 'comando': self._agregar_queja},

            {'nombre_icono': 'History21.ico', 'etiqueta': 'Historial', 'nombre': 'historial_pedido',
             'hotkey': None, 'comando': self._historial_pedido},

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

    def _seleccionar_una_fila(self):
        fila = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)
        if not fila:
            return
        if len(fila) > 1:
            return
        return fila

    def _rellenar_tabla_detalle(self):
        fila = self._seleccionar_una_fila()
        if not fila:
            return

        order_document_id = fila[0]['OrderDocumentID']
        partidas = self._modelo.buscar_partidas_pedido(order_document_id)
        partidas_procesadas = self._procesar_partidas_pedido(partidas)

        for partida in partidas_procesadas:
            self._interfaz.ventanas.insertar_fila_treeview('tvw_detalle', partida)

        self._colorear_partidas_detalle()

    def _colorear_partidas_detalle(self):
        filas = self._interfaz.ventanas.obtener_filas_treeview('tvw_detalle')
        if not filas:
            return

        for fila in filas:
            valores_fila = self._interfaz.ventanas.procesar_fila_treeview('tvw_detalle', fila)

            estado_produccion_modificado = valores_fila['ItemProductionStatusModified']
            if estado_produccion_modificado == 0:
                continue

            # fila borrada
            if estado_produccion_modificado == 3:
                self._interfaz.ventanas.colorear_fila_seleccionada_treeview('tvw_detalle', fila, color='danger')

            # fila agregada
            if estado_produccion_modificado == 1:
                self._interfaz.ventanas.colorear_fila_seleccionada_treeview('tvw_detalle', fila, color='info')

            # fila editada
            if estado_produccion_modificado == 2:
                self._interfaz.ventanas.colorear_fila_seleccionada_treeview('tvw_detalle', fila,
                                                                            color='warning')

    def _procesar_partidas_pedido(self, partidas):
        if not partidas:
            return
        consulta_partidas_con_impuestos = self._modelo.utilerias.agregar_impuestos_productos(partidas)

        partidas_procesadas = []
        for producto in consulta_partidas_con_impuestos:
            precio_con_impuestos = producto['SalePriceWithTaxes']
            cantidad_decimal = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(producto['Quantity'])
            total = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(precio_con_impuestos * cantidad_decimal)
            product_id = producto['ProductID']

            if product_id == 5606:
                continue

            datos_fila = (
                cantidad_decimal,
                producto['ProductKey'],
                producto['ProductName'],
                precio_con_impuestos,
                total,
                producto['Esp'],
                producto['ProductID'],
                producto['DocumentItemID'],
                producto['ItemProductionStatusModified'],
                producto['ClaveUnidad'],
                0,  # status surtido
                producto['UnitPrice'],
                producto['CayalPiece'],
                producto['CayalAmount'],
                producto['Comments'],
                producto['ProductTypeIDCayal']
            )
            partidas_procesadas.append(datos_fila)
        return partidas_procesadas

    def _filtrar_por_capturados_por(self):

        seleccion = self._interfaz.ventanas.obtener_input_componente('cbx_capturista')
        if seleccion == 'Seleccione':
            self._rellenar_tabla_pedidos(self._fecha_seleccionada())
            self._interfaz.ventanas.limpiar_seleccion_table_view('tbv_pedidos')
            return

        self._interfaz.ventanas.filtrar_table_view(_table_view='tbv_pedidos',
                                                       columna=6,
                                                       valor=[seleccion],
                                                       )

    def _filtrar_por_status(self):
        seleccion = self._interfaz.ventanas.obtener_input_componente('cbx_status')
        if seleccion == 'Seleccione':
            self._rellenar_tabla_pedidos(self._fecha_seleccionada())
            self._interfaz.ventanas.limpiar_seleccion_table_view('tbv_pedidos')
            return

        self._interfaz.ventanas.filtrar_table_view(_table_view='tbv_pedidos',
                                                   columna=13,
                                                   valor=[seleccion],
                                                   )

    def _filtrar_por_horas(self):
        seleccion = self._interfaz.ventanas.obtener_input_componente('cbx_horarios')
        if seleccion == 'Seleccione':
            self._rellenar_tabla_pedidos(self._fecha_seleccionada())
            self._interfaz.ventanas.limpiar_seleccion_table_view('tbv_pedidos')
            return

        self._interfaz.ventanas.filtrar_table_view(_table_view='tbv_pedidos',
                                                   columna=8,
                                                   valor=[seleccion],
                                                   )

    def _filtrar_por_no_impresos(self):

        valor_chk = self._interfaz.ventanas.obtener_input_componente('chk_no_impresos')

        if valor_chk == 1:
            self._interfaz.ventanas.filtrar_table_view(_table_view='tbv_pedidos',
                                                       columna=37,
                                                       valor=[""],
                                                       )
        if valor_chk == 0:
            self._interfaz.ventanas.limpiar_seleccion_table_view('tbv_pedidos')

    def _validar_seleccion_multiples_filas(self):
        # si imprimir en automatico esta desactivado la seleccion de filas solo aplica a la seleccion
        filas = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)

        if not filas:
            self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar por lo menos un pedido.')
            return

        return filas
