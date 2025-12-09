import re
import tkinter as tk

from cayal.ventanas import Ventanas

from herramientas.capturar_documento.llamar_instancia_captura import LlamarInstanciaCaptura
from herramientas.herramientas_compartidas.capturado_vs_producido import CapturadoVsProducido
from herramientas.herramientas_panel.editar_pedido import EditarPedido
from herramientas.herramientas_panel.selector_tipo_documento import SelectorTipoDocumento


class HerramientasTimbrado:
    def __init__(self, master, modelo, interfaz, callbacks_autorefresco):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._modelo = modelo
        self._interfaz = interfaz
        self._callbacks_autorefresco = callbacks_autorefresco or {}


        self._base_de_datos = self._modelo.base_de_datos
        self._parametros = self._modelo.parametros
        self._utilerias = self._modelo.utilerias

        self._crear_frames()
        self._crear_barra_herramientas()

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'pady': 5, 'padx': 5, 'sticky': tk.NSEW}),

            'frame_componentes': ('frame_principal', None,
                                  {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                   'sticky': tk.NSEW})
        }
        self._ventanas.crear_frames(frames)

    def _crear_barra_herramientas(self):
        self.barra_herramientas_pedido = [

            {'nombre_icono': 'lista-de-verificacion.ico', 'etiqueta': 'Editar', 'nombre': 'editar',
             'hotkey': None, 'comando': self._editar_pedido},

            {'nombre_icono': 'Invoice32.ico', 'etiqueta': 'Facturar', 'nombre': 'facturar',
             'hotkey': None, 'comando': self._facturar},

            {'nombre_icono': 'PrintSelectedItems.ico', 'etiqueta': 'Producido', 'nombre': 'capturado_vs_producido',
             'hotkey': None, 'comando': self._capturado_vs_producido}

        ]

        self.elementos_barra_herramientas = self._ventanas.crear_barra_herramientas(self.barra_herramientas_pedido,
                                                                                   'frame_componentes')
        self.iconos_barra_herramientas = self.elementos_barra_herramientas[0]
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]

    def _pausar_autorefresco(self):
        fn = self._callbacks_autorefresco.get("pausar")
        if fn:
            fn()

    def _reanudar_autorefresco(self):
        fn = self._callbacks_autorefresco.get("reanudar")
        if fn:
            fn()

    def _obtener_valores_fila_pedido_seleccionado(self, valor = None):
        if not self._interfaz.ventanas.validar_seleccion_una_fila_table_view('tbv_pedidos'):
            return

        valores_fila = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)[0]
        if not valor:
            return valores_fila

        return valores_fila[valor]

    def _obtener_valores_filas_pedidos_seleccionados(self):
        # si imprimir en automatico esta desactivado la seleccion de filas solo aplica a la seleccion
        filas = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)

        if not filas:
            self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar por lo menos un pedido.')
            return

        return filas

    def _editar_pedido(self):

        fila = self._obtener_valores_fila_pedido_seleccionado()
        if not fila:
            self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar un pedido.')
            return

        status_id = fila['TypeStatusID']
        order_document_id = fila['OrderDocumentID']

        try:
            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
            if status_id < 3:
                self._parametros.id_principal = order_document_id

                _ = LlamarInstanciaCaptura(
                    ventana,
                    self._parametros,
                )

            elif status_id == 3:
                _ = EditarPedido(ventana, self._base_de_datos, self._utilerias, self._parametros, fila)

            else:  # status_id > 3
                self._interfaz.ventanas.mostrar_mensaje(
                    'No se pueden editar en este módulo documentos que no estén en status Por Timbrar.'
                )

            ventana.wait_window()

        finally:
            self._modelo.actualizar_totales_pedido(order_document_id)

    def _facturar(self):
        # --------------------------------------------------------------------------------------------------------------
        def filtrar_filas_facturables_por_status(filas):
            filas_filtradas = []
            # filtrar por status
            for fila in filas:
                status_id = fila['TypeStatusID']

                #  abierto, en proceso, cancelado, surtido parcialmente minisuper, produccion, almacen
                if status_id not in (1, 2, 10, 12, 16, 17, 18):
                    continue

                filas_filtradas.append(fila)

            return filas_filtradas

        def buscar_pedidos_en_proceso_del_mismo_cliente(fila):
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

        def calcular_total_pedido(order_document_id):

            consulta_partidas = self._modelo.base_de_datos.buscar_partidas_pedidos_produccion_cayal(
                order_document_id, partidas_producidas=True)

            consulta_partidas_con_impuestos = self._modelo.utilerias.agregar_impuestos_productos(consulta_partidas)
            total_subtotal = 0
            total_tax = 0
            total_total = 0
            nuevas_partidas = []
            for producto in consulta_partidas_con_impuestos:
                impuestos = producto['impuestos']
                subtotal =  producto['subtotal']
                total = producto['total']
                product_id = producto['ProductID']

                if product_id == 5606:
                    continue

                total_subtotal += subtotal
                total_tax += impuestos
                total_total += total

                nuevas_partidas.append(producto)


            return total_total, nuevas_partidas

        def cuantificar_valor_partidas_documento(filas, mismo_cliente=False):
            # validar que el monto sea superior a 180 debito a que el cliente podria anexar un producto y con ello
            # evitar generar la factura correspondiente

            total_acumulado = 0
            filas_filtradas = []
            partidas_pedidos = {}
            for fila in filas:
                order_document_id = fila['OrderDocumentID']
                total_documento, partidas_con_impuesto = calcular_total_pedido(order_document_id)
                partidas_pedidos[order_document_id] = (total_documento, partidas_con_impuesto)

                if total_documento < 200 and not mismo_cliente:
                    cliente = fila['Cliente']
                    pedido = fila['Pedido']

                    respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                        f'El total de la orden {pedido} del cliente {cliente} '
                        f'es de {total_documento}, ¿Desea omitir este pedido del proceso para consultar con el cliente un posible incremento en su pedido?'
                        )
                    if respuesta:
                        continue

                    filas_filtradas.append(fila)
                    continue

                if mismo_cliente:
                    total_acumulado += total_documento
                    continue

                if total_documento > 199:
                    filas_filtradas.append(fila)
                    continue

            if mismo_cliente and total_acumulado < 200:
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

            return filas_filtradas, partidas_pedidos

        def actualizar_forma_de_pago_documento(info_documento):

            # equivalencias de forma de pago de pedidos
            way_to_pay_cfd = {
                2: 1,  # efectivo
                3: 28,  # tdb
                4: 4,  # tbc
                6: 3,  # transferencia
                7: 2  # cheque
            }

            way_to_pay_id = int(info_documento['WayToPayID'])

            # si la forma de pago entra entre tdc,tdb, efectivo, transferencia o cheque, actualizala
            """
            1	Por Definir	El pago se definirá en el cobro
            2	Efectivo	Efectivo
            3	Tarjeta Debito	Llevar terminal
            4	Tarjeta Crédito	Llevar terminal
            5	Firma	Es a crédito
            6	Transferencia	Transferencia
            7	Cheque	Cheque
            8	No aplica	No cobrar 
            """
            if way_to_pay_id in (2, 3, 4, 6, 7):
                return way_to_pay_cfd[way_to_pay_id]

            return 0

        def crear_cabecera_documento(document_type_id, fila):
            # este valor hace que se inserte la configuracion del cliente que esta predeterminada
            way_to_pay_id = 0

            # solo si el documento es factura realiza la actualización de tipo de pago
            if document_type_id == 0:
                way_to_pay_id = actualizar_forma_de_pago_documento(info_documento=fila)

            return self._modelo.crear_cabecera_factura_mayoreo(document_type_id, way_to_pay_id, fila)

        def filtrar_comentario_documento(comentario):

            palabras_a_eliminar = [
                r'\bes un anexo\b',  # Nueva frase a eliminar
                r'\banexo\b', r'\banexos\b',
                r'\bllevar terminal\b',
                # r'\bviene\b',
                # r'\bes viene\b',
                r'\btransferencia\b', r'\btransf\b', r'\bestransferencia\b',
                r'\bcheque\b',
                r'\bfolio\b',
                r'\bllevar a\b',
                r'\bes folio\b',
                r'\bcredito\b',
                r'\bes credito\b',
            ]

            # Expresión regular para eliminar frases no deseadas
            patron_palabras = re.compile(r"(,?\s*)?(" + "|".join(palabras_a_eliminar) + r")(,?\s*)?", re.IGNORECASE)

            # Expresión regular para reemplazar múltiples guiones por un solo guion
            patron_guiones = re.compile(r'-{2,}')  # Busca "--", "---", etc.

            # Eliminar palabras/frases no deseadas
            comentario_filtrado = patron_palabras.sub("", comentario)

            # Reemplazar múltiples guiones por un solo guion
            comentario_filtrado = patron_guiones.sub("-", comentario_filtrado)

            # Limpiar espacios y comas innecesarias después de la sustitución
            comentario_filtrado = re.sub(r'\s*,\s*', ', ', comentario_filtrado)  # Espacios alrededor de comas
            comentario_filtrado = re.sub(r',\s*$', '', comentario_filtrado)  # Coma al final
            comentario_filtrado = comentario_filtrado.strip()  # Eliminar espacios en los extremos

            return comentario_filtrado

        def crear_comentario_documento(order_document_ids, document_id, business_entity_id, total_documento,
                                        ruta):
            comentarios_pedidos = []
            comentario_a_insertar = ''
            for order in order_document_ids:
                comentario = self._modelo.obtener_comentario_pedido(order)

                if comentario:
                    comentarios_pedidos.append(comentario)

            comentarios = [f"{comentario}," for comentario in comentarios_pedidos]
            comentario_a_insertar = '\n'.join(comentarios)
            comentario_a_insertar = filtrar_comentario_documento()

            comentarios_taras = self._modelo.crear_comentario_taras(order_document_ids)
            comentarios_horarios = self._modelo.crear_comentario_horarios(order_document_ids)
            comentarios_forma_pago = self._modelo.crear_comentario_forma_pago(order_document_ids)
            comentarios_entrega = self._modelo.crear_comentario_entrega(order_document_ids)

            comentario_a_insertar = f"{ruta}\n {comentario_a_insertar}\n {comentarios_taras}\n {comentarios_horarios}\n {comentarios_forma_pago}\n {comentarios_entrega}".upper()
            comentario_a_insertar = self._modelo.validar_credito_documento_cliente(business_entity_id, comentario_a_insertar,
                                                                            total_documento)

            self._modelo.actualizar_comentario_document_id(comentario_a_insertar, document_id)

        def crear_documento(filas, combinado=False, mismo_cliente=False):

            tipo_documento = 1  # remision

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

            filas_valorizadas, partidas_pedidos = cuantificar_valor_partidas_documento(filas, mismo_cliente)
            if not filas_valorizadas:
                self._interfaz.ventanas.mostrar_mensaje('No hay ningún documento que generar.')
                return

            # aqui creamos el o los documentos pertinentes
            # si es un documento por cada orden no hay problema se toma el tipo desde la fila
            document_id = 0
            total_acumulado = 0
            partidas_acumuladas = []

            for fila in filas_valorizadas:
                order_document_id = fila['OrderDocumentID']
                address_detail_id = fila['AddressDetailID']
                business_entity_id = fila['BusinessEntityID']
                ruta = fila['Ruta']

                info_documento = partidas_pedidos.get(order_document_id, None)
                if not info_documento:
                    continue

                # info documento es una tupla donde el primer elemento es el total del documento y el segundo las partidas
                # en este punto los documentos valorizados ya estan filtrado despues de n validaciones
                total_documento = info_documento[0]
                partidas = info_documento[1]

                if not combinado:
                    tipo_documento = fila['DocumentTypeID']

                    document_id = crear_cabecera_documento(tipo_documento, fila)
                    self._modelo.insertar_partidas_documento(order_document_id, document_id, partidas, total_documento,
                                                      address_detail_id)

                    # insertar comentarios desde el pedido
                    crear_comentario_documento([order_document_id],
                                                     document_id,
                                                     business_entity_id,
                                                     total_documento,
                                                     ruta
                                                     )

                    # relacionar documenrtosa con pedidos
                    self._modelo.relacionar_pedidos_con_facturas(document_id, order_document_id)

                    # agregar documento para recalculo
                    self._modelo.insertar_pedido_a_recalcular(document_id, order_document_id)

                    # afectar bitacora
                    self._modelo.afectar_bitacora_de_cambios_en_pedidos(document_id, [order_document_id])

                else:
                    partidas_acumuladas.extend(partidas)
                    total_acumulado += total_documento

            # proceso concluido si no fue combinado el documento
            if not combinado:
                return

            # aplica para documentos combinados
            all_order_document_ids = [fila['OrderDocumentID'] for fila in filas]
            order_document_ids = sorted([fila['OrderDocumentID'] for fila in filas if fila['OrderTypeID'] == 1],
                                        reverse=True)
            if not order_document_ids:
                self._interfaz.ventanas.mostrar_mensaje(
                    'Debe por lo menos haber un pedido dentro de las ordenes seleccionadas.')
                return

            order_document_id = order_document_ids[0]
            address_detail_id = filas[0]['AddressDetailID']
            business_entity_id = filas[0]['BusinessEntityID']

            # crea cabecera y bloqueala para evitar ediciones
            document_id = self._modelo.crear_cabecera_documento(tipo_documento, filas[0])

            self._modelo.insertar_partidas_documento(order_document_id, document_id, partidas_acumuladas, total_acumulado,
                                              address_detail_id)

            # insertar comentario de los pedidos
            self._modelo.crear_comentario_documento(all_order_document_ids,
                                             document_id,
                                             business_entity_id,
                                             total_acumulado,
                                             filas[0]['Ruta']
                                             )

            # relacionar pedidos con factura
            for order in all_order_document_ids:
                self._modelo.relacionar_pedidos_con_facturas(document_id, order)

            # relacionar pedido principal con pedidos
            for order in all_order_document_ids:
                if order != order_document_id:
                    self._modelo.relacionar_pedido_con_pedidos(order_document_id, order)

            # agregar documento para recalculo
            self._modelo.insertar_pedido_a_recalcular(document_id, order_document_id)

            # afectar la bitacora de cambios
            self._modelo.afectar_bitacora_de_cambios_en_pedidos(document_id, all_order_document_ids)

        def validar_si_los_pedidos_son_del_mismo_cliente(filas):
            business_entity_ids = []
            for fila in filas:
                business_entity_id = fila['BusinessEntityID']
                business_entity_ids.append(business_entity_id)

            business_entity_ids = list(set(business_entity_ids))
            if len(business_entity_ids) == 1:
                return True
            return False

        def excluir_pedidos_con_ordenes_en_proceso_del_mismo_cliente(filas):

            filas_filtradas = []
            clientes_en_proceso = []
            order_document_ids = [filas[0]['OrderDocumentID']]  # agrega el primer pedido a la lista para comparaciones
            for fila in filas:
                hay_pedidos_del_mismo_cliente_en_proceso = buscar_pedidos_en_proceso_del_mismo_cliente(fila)
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
                self._interfaz.ventanas.mostrar_mensaje(
                    f'Los clientes: {texto} tienen más órdenes en proceso o por timbrar.')
            return filas_filtradas

        # --------------------------------------------------------------------------------------------------------------
        filas = self._obtener_valores_filas_pedidos_seleccionados()

        if not filas:
            return

        # filtra por status no considerados válidos para generar el documento o documentos del cliente
        filas_filtradas = filtrar_filas_facturables_por_status(filas)

        if not filas_filtradas:
            self._interfaz.ventanas.mostrar_mensaje('No hay pedidos con un status válido para facturar')
            return

        #--------------------------------------------------------------------------------------------------------------
        # aqui comenzamos el procesamiento de las filas a facturar
        # si es una seleccion unica valida primero si no hay otros pendientes del mimsmo cliente
        if len(filas) == 1:
            hay_pedidos_del_mismo_cliente = buscar_pedidos_en_proceso_del_mismo_cliente(filas)

            if not hay_pedidos_del_mismo_cliente:
                crear_documento(filas)

            if hay_pedidos_del_mismo_cliente:
                respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta('Hay otro pedido del mismo cliente en proceso o por timbrar.'
                                                                             '¿Desea continuar?')
                if respuesta:
                    crear_documento(filas)
            return

        # si hay mas de una fila primero valida que estas filas no tengan solo el mismo cliente
        # si lo tuvieran hay que ofrecer combinarlas en un documento
        tienen_el_mismo_cliente = validar_si_los_pedidos_son_del_mismo_cliente(filas)
        if tienen_el_mismo_cliente:
            respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta('Los pedidos son del mismo cliente.'
                                                                         '¿Desea combinarlos?')
            if respuesta:
                crear_documento(filas, combinado=True, mismo_cliente=True)
                return

        # del mismo modo que para una fila valida que no existan otras ordenes de un cliente en proceso
        # si lo hay para un cliente ese cliente debe excluirse de la seleccion
        filas_filtradas = excluir_pedidos_con_ordenes_en_proceso_del_mismo_cliente(filas)
        if not filas_filtradas:
            return

        crear_documento(filas_filtradas)
        return

    def _capturado_vs_producido(self):
        fila = self._obtener_valores_fila_pedido_seleccionado()
        if not fila:
            return

        try:
            status_id = int(fila['TypeStatusID'])
            order_document_id = int(fila['OrderDocumentID'])

            if status_id in (2, 16, 17, 18):
                self._interfaz.ventanas.mostrar_mensaje('El pedido aún no se ha terminado de producir.')
                return

            self._parametros.id_principal = order_document_id
            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(titulo='Capturado vs Producido')
            instancia = CapturadoVsProducido(ventana, self._parametros, self._base_de_datos, self._utilerias, fila)
            ventana.wait_window()
        finally:
            self._parametros.id_principal = 0

