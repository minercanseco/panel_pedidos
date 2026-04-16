import re
import tkinter as tk

from cayal.documento import Documento
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

    def _filtro_post_captura(self):
        fn = self._callbacks_autorefresco.get("postcaptura")
        if fn:
            fn()

    def _rellenar_tabla(self):
        fn = self._callbacks_autorefresco.get("rellenar_tabla")
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
        business_entity_id = fila['BusinessEntityID']

        #  cancelado, modificando, surtido parcialmente minisuper, produccion, almacen, entregado, cobrado o cartera
        if status_id in (10, 12, 16, 17, 18, 15):
            self._interfaz.ventanas.mostrar_mensaje('El pedido no tiene un estatus válido para ser editado.')
            return

        try:
            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(titulo='Pedido', nombre_icono='icono_logo.ico')
            if status_id < 3:
                self._parametros.id_principal = order_document_id
                documento = Documento()
                documento.document_id = order_document_id
                documento.business_entity_id = business_entity_id

                _ = LlamarInstanciaCaptura(
                    ventana,
                    self._parametros,
                    documento=documento
                )

            elif status_id  >= 3:
                _ = EditarPedido(ventana, self._base_de_datos, self._utilerias, self._parametros, fila)

            else:
                self._interfaz.ventanas.mostrar_mensaje(
                    'No hay acción válida para un pedido en este estado.'
                )

            ventana.wait_window()

        finally:
            self._modelo.actualizar_totales_pedido(order_document_id)
            self._rellenar_tabla()
            if status_id == 1:
                self._filtro_post_captura()

    def _facturar(self):
        import re

        pedidos_fuera_status_timbrado = []
        pedidos_fuera_status_timbrado_ids = []

        # --------------------------------------------------------------------------------------------------------------
        def normalizar_order_id(valor):
            """
            Convierte IDs relacionados a int cuando sea posible.
            Soporta valores como:
            - 115963
            - '115963'
            - 'PD115963'
            """
            if valor in (None, '', '0', 0):
                return None

            if isinstance(valor, str):
                valor = valor.strip()
                if not valor:
                    return None

                match = re.search(r'(\d+)$', valor)
                if match:
                    try:
                        return int(match.group(1))
                    except (TypeError, ValueError):
                        return None

            try:
                return int(valor)
            except (TypeError, ValueError):
                return None

        def obtener_order_document_id_de_fila(fila):
            valor = fila.get('OrderDocumentID')

            if valor in (None, '', '0', 0):
                return None

            return normalizar_order_id(valor)

        def obtener_order_relacionado(fila):
            """
            Obtiene el pedido relacionado usando distintas llaves posibles.
            """
            posibles_llaves = (
                'RelatedOrderID',
                'Relacion',
                'RelatedOrderDocumentID',
                'RetailatedOrderID',
                'RetaledOrderID',
            )

            for llave in posibles_llaves:
                valor = normalizar_order_id(fila.get(llave))
                if valor:
                    return valor

            return None

        def buscar_fila_por_order_document_id(order_document_id, filas_base=None, validar_con=None):
            order_document_id = normalizar_order_id(order_document_id)
            if not order_document_id:
                return None

            def _fecha_fila(fila):
                for llave in ('DeliveryPromise', 'F.Entrega', 'FechaEntrega', 'Fecha'):
                    valor = fila.get(llave)
                    if valor:
                        try:
                            return self._utilerias.convertir_fecha_str_a_datetime(valor)
                        except Exception:
                            pass
                return None

            # 1) Buscar en selección
            if filas_base:
                for fila in filas_base:
                    if obtener_order_document_id_de_fila(fila) == order_document_id:
                        return fila

            # 2) Buscar en tabla (solo si trae OrderDocumentID real)
            filas_tabla = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos')
            for fila_tabla in filas_tabla:
                fila_id = fila_tabla.get('OrderDocumentID')
                if not fila_id:
                    continue

                if normalizar_order_id(fila_id) != order_document_id:
                    continue

                if validar_con:
                    cliente_origen = validar_con.get('BusinessEntityID')
                    cliente_destino = fila_tabla.get('BusinessEntityID')

                    if cliente_origen and cliente_destino and cliente_origen != cliente_destino:
                        continue

                    fecha_origen = _fecha_fila(validar_con)
                    fecha_destino = _fecha_fila(fila_tabla)

                    if fecha_origen and fecha_destino and fecha_origen != fecha_destino:
                        continue

                return fila_tabla

            # 3) 🔥 SI NO ESTÁ EN UI → BD OBLIGATORIO
            fila_bd = self._modelo.buscar_pedido_por_id(order_document_id)
            if fila_bd:
                return fila_bd

            return None


        def buscar_pedido_base_en_seleccion(fila_objetivo, filas_base):
            """
            Deshabilitado por seguridad.
            No se debe inferir el pedido base solo por cliente,
            porque puede tomar un pedido incorrecto.
            """
            return None

        def validar_relacion_pedido_base(fila_origen, fila_pedido):
            if not fila_origen or not fila_pedido:
                return False

            try:
                cliente_origen = fila_origen.get('BusinessEntityID')
                cliente_pedido = fila_pedido.get('BusinessEntityID')

                if cliente_origen and cliente_pedido and cliente_origen != cliente_pedido:
                    return False
            except Exception:
                return False

            if int(fila_pedido.get('OrderTypeID') or 0) != 1:
                return False

            def _fecha_fila_normalizada(fila):
                for llave in ('DeliveryPromise', 'F.Entrega', 'FechaEntrega', 'Fecha'):
                    valor = fila.get(llave)
                    if valor:
                        try:
                            dt = self._utilerias.convertir_fecha_str_a_datetime(valor)
                            return dt.date()  # 🔥 SOLO FECHA, sin hora
                        except Exception:
                            pass
                return None

            fecha_origen = _fecha_fila_normalizada(fila_origen)
            fecha_pedido = _fecha_fila_normalizada(fila_pedido)

            # 🔥 comparar solo si ambas existen
            if fecha_origen and fecha_pedido and fecha_origen != fecha_pedido:
                return False

            return True

        def filtrar_filas_facturables_por_status(filas):
            filas_filtradas = []

            for fila in filas:
                status_id = int(fila.get('TypeStatusID') or 0)
                cliente = fila.get('Cliente', '')
                order_id = obtener_order_document_id_de_fila(fila)

                if status_id in (1, 2, 10, 12, 16, 17, 18):
                    referencia = order_id or 'Sin referencia'
                    pedidos_fuera_status_timbrado.append(f'{referencia} - {cliente}')
                    if order_id:
                        pedidos_fuera_status_timbrado_ids.append(order_id)
                    continue

                filas_filtradas.append(fila)

            return filas_filtradas

        def buscar_pedidos_en_proceso_del_mismo_cliente(fila):
            fila_base = fila[0] if isinstance(fila, list) else fila
            business_entity_id = fila_base['BusinessEntityID']
            order_document_id = obtener_order_document_id_de_fila(fila_base)

            pedidos_del_mismo_cliente = 0
            filas_tabla = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos')

            for fila_tabla in filas_tabla:
                business_entity_id_fila = fila_tabla['BusinessEntityID']
                order_document_id_fila = obtener_order_document_id_de_fila(fila_tabla)
                status_id = fila_tabla['TypeStatusID']

                if order_document_id_fila == order_document_id:
                    continue

                if business_entity_id_fila == business_entity_id:
                    if status_id in (2, 3, 16, 17, 18):
                        pedidos_del_mismo_cliente += 1

            return pedidos_del_mismo_cliente > 0

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
                subtotal = producto['subtotal']
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
            total_acumulado = 0
            filas_filtradas = []
            partidas_pedidos = {}

            for fila in filas:
                order_document_id = obtener_order_document_id_de_fila(fila)
                if not order_document_id:
                    continue

                total_documento, partidas_con_impuesto = calcular_total_pedido(order_document_id)
                partidas_pedidos[order_document_id] = (total_documento, partidas_con_impuesto)

                if mismo_cliente:
                    total_acumulado += total_documento
                    continue

                if total_documento < 200:
                    cliente = fila['Cliente']
                    respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                        f'El total de la orden {order_document_id} del cliente {cliente} '
                        f'es de {total_documento}, ¿Desea omitir este pedido del proceso?'
                    )
                    if respuesta:
                        continue
                    filas_filtradas.append(fila)
                    continue

                filas_filtradas.append(fila)

            if mismo_cliente:
                if total_acumulado < 200:
                    cliente = filas[0]['Cliente']
                    respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                        f'El total acumulado de las ordenes seleccionadas del cliente {cliente}'
                        f'es de {total_acumulado}, ¿Desea consultar incremento?'
                    )
                    if respuesta:
                        return [], partidas_pedidos
                    return filas, partidas_pedidos

                return filas, partidas_pedidos

            return filas_filtradas, partidas_pedidos

        def actualizar_forma_de_pago_documento(info_documento):
            way_to_pay_cfd = {
                2: 1,  # efectivo
                3: 28,  # tdb
                4: 4,  # tbc
                6: 3,  # transferencia
                7: 2  # cheque
            }

            way_to_pay_id = int(info_documento['WayToPayID'])

            if way_to_pay_id in (2, 3, 4, 6, 7):
                return way_to_pay_cfd[way_to_pay_id]

            return 0

        def crear_cabecera_documento(document_type_id, fila):
            way_to_pay_id = 0

            if document_type_id == 0:
                way_to_pay_id = actualizar_forma_de_pago_documento(info_documento=fila)

            return self._modelo.crear_cabecera_factura_mayoreo(document_type_id, way_to_pay_id, fila)

        def filtrar_comentario_documento(comentario):
            palabras_a_eliminar = [
                r'\bes un anexo\b',
                r'\banexo\b', r'\banexos\b',
                r'\bes anexoo\b',
                r'\banexoo\b',
                r'\bllevar terminal\b',
                r'\btransferencia\b', r'\btransf\b', r'\bestransferencia\b',
                r'\bcheque\b',
                r'\bfolio\b',
                r'\bllevar a\b',
                r'\bes folio\b',
                r'\bcredito\b',
                r'\bes credito\b',
            ]

            patron_palabras = re.compile(r"(,?\s*)?(" + "|".join(palabras_a_eliminar) + r")(,?\s*)?", re.IGNORECASE)
            patron_guiones = re.compile(r'-{2,}')

            comentario_filtrado = patron_palabras.sub("", comentario)
            comentario_filtrado = patron_guiones.sub("-", comentario)

            comentario_filtrado = re.sub(r'\s*,\s*', ', ', comentario_filtrado)
            comentario_filtrado = re.sub(r',\s*$', '', comentario_filtrado)
            comentario_filtrado = comentario_filtrado.strip()

            return comentario_filtrado

        def crear_comentario_documento(order_document_ids, document_id, business_entity_id, total_documento, ruta):
            comentarios_pedidos = []

            for order in order_document_ids:
                comentario = self._modelo.obtener_comentario_pedido(order)
                if comentario:
                    comentarios_pedidos.append(comentario)

            comentarios = [f"{comentario}," for comentario in comentarios_pedidos]
            comentario_a_insertar = '\n'.join(comentarios)
            comentario_a_insertar = filtrar_comentario_documento(comentario_a_insertar)

            comentarios_taras = self._modelo.crear_comentario_taras(order_document_ids)
            comentarios_horarios = self._modelo.crear_comentario_horarios(order_document_ids)
            comentarios_forma_pago = self._modelo.crear_comentario_forma_pago(order_document_ids)
            comentarios_entrega = self._modelo.crear_comentario_entrega(order_document_ids)

            comentario_a_insertar = (
                f"{ruta}\n {comentario_a_insertar}\n {comentarios_taras}\n "
                f"{comentarios_horarios}\n {comentarios_forma_pago}\n {comentarios_entrega}"
            ).upper()

            comentario_a_insertar = self._modelo.validar_credito_documento_cliente(
                business_entity_id,
                comentario_a_insertar,
                total_documento
            )

            self._modelo.actualizar_comentario_document_id(comentario_a_insertar, document_id)

        def resolver_order_document_id_principal(fila):
            """
            Reglas:
            - Pedido (1): se relaciona consigo mismo.
            - Anexo (2) o cambio (3): se relacionan con el pedido base.
            """
            order_type_id = int(fila.get('OrderTypeID') or 0)
            order_document_id = obtener_order_document_id_de_fila(fila)
            related_order_id = obtener_order_relacionado(fila)

            if order_type_id == 1:
                return order_document_id

            if order_type_id in (2, 3):
                return related_order_id

            return order_document_id

        def preparar_fila_para_creacion_documento(fila):
            """
            Prepara una copia segura de la fila para crear el documento SIEMPRE
            usando como origen el pedido base, aunque la selección haya sido un anexo/cambio.
            """
            fila_documento = dict(fila)

            order_document_id_original = obtener_order_document_id_de_fila(fila)
            order_document_id_principal = resolver_order_document_id_principal(fila)

            if not order_document_id_principal:
                return None

            fila_documento['OrderDocumentIDOriginal'] = order_document_id_original
            fila_documento['OrderDocumentID'] = order_document_id_principal

            return fila_documento

        def crear_documento(filas, combinado=False, mismo_cliente=False):
            tipo_documento = 1  # remision

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

            filas_valorizadas, partidas_pedidos = cuantificar_valor_partidas_documento(filas, mismo_cliente)
            if not filas_valorizadas:
                self._interfaz.ventanas.mostrar_mensaje('No hay ningún documento que generar.')
                return

            document_id = 0
            total_acumulado = 0
            partidas_acumuladas = []

            for fila in filas_valorizadas:
                order_document_id_original = obtener_order_document_id_de_fila(fila)
                order_principal = resolver_order_document_id_principal(fila)

                if not order_document_id_original or not order_principal:
                    continue

                fila_documento = preparar_fila_para_creacion_documento(fila)
                if not fila_documento:
                    continue

                address_detail_id = fila['AddressDetailID']
                business_entity_id = fila['BusinessEntityID']
                ruta = fila['Ruta']

                info_documento = partidas_pedidos.get(order_document_id_original, None)
                if not info_documento:
                    continue

                total_documento = info_documento[0]
                partidas = info_documento[1]

                if not combinado:
                    tipo_documento = fila['DocumentTypeID']

                    # 1) Crear cabecera usando SIEMPRE el pedido base como origen
                    document_id = crear_cabecera_documento(tipo_documento, fila_documento)

                    # 2) Blindaje adicional por si crear_cabecera_factura_mayoreo internamente
                    #    tomó el OrderDocumentID incorrecto
                    self._modelo.corregir_origen_documento_a_pedido_base(document_id, order_principal)

                    self._modelo.insertar_partidas_documento(
                        order_principal,
                        document_id,
                        partidas,
                        total_documento,
                        address_detail_id
                    )

                    crear_comentario_documento(
                        [order_principal],
                        document_id,
                        business_entity_id,
                        total_documento,
                        ruta
                    )

                    self._modelo.relacionar_pedidos_con_facturas(document_id, order_principal)
                    self._modelo.insertar_pedido_a_recalcular(document_id, order_principal)
                    self._modelo.afectar_bitacora_de_cambios_en_pedidos(document_id, [order_principal])

                else:
                    partidas_acumuladas.extend(partidas)
                    total_acumulado += total_documento

            if not combinado:
                return

            all_order_document_ids = list({
                resolver_order_document_id_principal(fila)
                for fila in filas
                if resolver_order_document_id_principal(fila)
            })

            order_document_ids = sorted(
                {
                    resolver_order_document_id_principal(fila)
                    for fila in filas
                    if resolver_order_document_id_principal(fila)
                },
                reverse=True
            )

            if not order_document_ids:
                self._interfaz.ventanas.mostrar_mensaje(
                    'No fue posible resolver el pedido base de las órdenes seleccionadas.'
                )
                return

            # el documento combinado debe nacer del pedido base real
            order_document_id = order_document_ids[0]
            address_detail_id = filas[0]['AddressDetailID']
            business_entity_id = filas[0]['BusinessEntityID']

            fila_documento = preparar_fila_para_creacion_documento(filas[0])
            if not fila_documento:
                self._interfaz.ventanas.mostrar_mensaje(
                    'No fue posible resolver el pedido base para crear el documento.'
                )
                return

            document_id = crear_cabecera_documento(tipo_documento, fila_documento)

            # blindaje adicional
            self._modelo.corregir_origen_documento_a_pedido_base(document_id, order_document_id)

            self._modelo.insertar_partidas_documento(
                order_document_id,
                document_id,
                partidas_acumuladas,
                total_acumulado,
                address_detail_id
            )

            crear_comentario_documento(
                all_order_document_ids,
                document_id,
                business_entity_id,
                total_acumulado,
                filas[0]['Ruta']
            )

            for order in all_order_document_ids:
                self._modelo.relacionar_pedidos_con_facturas(document_id, order)

            self._modelo.insertar_pedido_a_recalcular(document_id, order_document_id)
            self._modelo.afectar_bitacora_de_cambios_en_pedidos(document_id, all_order_document_ids)

        def validar_si_se_pueden_combinar(filas):
            clientes = {fila['BusinessEntityID'] for fila in filas}
            if len(clientes) != 1:
                return False

            pedidos = [fila for fila in filas if int(fila.get('OrderTypeID') or 0) == 1]

            # no mezclar dos pedidos reales
            if len(pedidos) > 1:
                return False

            return True

        def excluir_pedidos_con_ordenes_en_proceso_del_mismo_cliente(filas):
            filas_filtradas = []
            clientes_en_proceso = []

            order_document_ids = []
            if filas:
                primer_id = obtener_order_document_id_de_fila(filas[0])
                if primer_id:
                    order_document_ids.append(primer_id)

            for fila in filas:
                hay_pedidos_del_mismo_cliente_en_proceso = buscar_pedidos_en_proceso_del_mismo_cliente(fila)
                if not hay_pedidos_del_mismo_cliente_en_proceso:
                    filas_filtradas.append(fila)
                else:
                    order_document_id = obtener_order_document_id_de_fila(fila)
                    if order_document_id not in order_document_ids:
                        clientes_en_proceso.append(fila['Cliente'])

            texto = ''
            if clientes_en_proceso:
                clientes_en_proceso = set(clientes_en_proceso)
                for cliente in clientes_en_proceso:
                    texto = f'{texto} {cliente},'
                self._interfaz.ventanas.mostrar_mensaje(
                    f'Los clientes: {texto} tienen más órdenes en proceso o por timbrar.'
                )

            return filas_filtradas

        def mostrar_pedidos_refacturados(pedidos_refacturados):
            if not pedidos_refacturados:
                return

            pedidos_texto = '\n'.join(f'• {pedido}' for pedido in pedidos_refacturados)

            self._interfaz.ventanas.mostrar_mensaje(
                tipo='info',
                mensaje=f'Pedidos omitidos por status distinto de 3:\n{pedidos_texto}'
            )

        def normalizar_filas_para_facturar(filas):
            """
            Reglas seguras:
            - Pedido (1): sigue normal.
            - Anexo (2) / cambio (3):
                * debe tener RelatedOrderID válido
                * debe resolverse a un pedido real (OrderTypeID = 1)
                * debe coincidir en cliente
                * debe coincidir en fecha/contexto
                * si no se encuentra de forma consistente, se aborta
            """
            if not filas:
                return []

            filas_normalizadas = list(filas)

            # --------------------------
            # Caso: selección única
            # --------------------------
            if len(filas_normalizadas) == 1:
                fila = filas_normalizadas[0]
                order_type_id = int(fila.get('OrderTypeID') or 0)

                if order_type_id in (2, 3):
                    related_order_id = obtener_order_relacionado(fila)

                    if not related_order_id:
                        self._interfaz.ventanas.mostrar_mensaje(
                            'La orden seleccionada no tiene un pedido relacionado válido. No se puede facturar.'
                        )
                        return []

                    fila_pedido = buscar_fila_por_order_document_id(
                        related_order_id,
                        filas_base=filas_normalizadas,
                        validar_con=fila
                    )

                    if not fila_pedido:
                        fila_pedido = buscar_fila_por_order_document_id(
                            related_order_id,
                            validar_con=fila
                        )

                    if not fila_pedido:
                        self._interfaz.ventanas.mostrar_mensaje(
                            f'No se encontró un pedido base válido ({related_order_id}) para una de las órdenes seleccionadas.'
                        )
                        return []

                    if not validar_relacion_pedido_base(fila, fila_pedido):
                        self._interfaz.ventanas.mostrar_mensaje(
                            'La orden relacionada apunta a un pedido inconsistente en cliente o fecha. No se puede facturar.'
                        )
                        return []

                    respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                        'La orden seleccionada es un anexo o cambio relacionado a un pedido.\n'
                        '¿Desea mezclarla automáticamente con su pedido relacionado para facturar?'
                    )
                    if not respuesta:
                        return []

                    filas_normalizadas = [fila_pedido, fila]

            # --------------------------
            # Caso: selección múltiple
            # --------------------------
            order_document_ids_actuales = {
                obtener_order_document_id_de_fila(fila)
                for fila in filas_normalizadas
                if obtener_order_document_id_de_fila(fila)
            }

            filas_a_agregar = []

            for fila in filas_normalizadas:
                order_type_id = int(fila.get('OrderTypeID') or 0)

                if order_type_id not in (2, 3):
                    continue

                related_order_id = obtener_order_relacionado(fila)

                if not related_order_id:
                    pedido = fila.get('Pedido', fila.get('OrderDocumentID'))
                    self._interfaz.ventanas.mostrar_mensaje(
                        f'La orden {pedido} no tiene un pedido relacionado válido. No se puede facturar.'
                    )
                    return []

                if related_order_id in order_document_ids_actuales:
                    fila_existente = next(
                        (f for f in filas_normalizadas if obtener_order_document_id_de_fila(f) == related_order_id),
                        None
                    )
                    if not validar_relacion_pedido_base(fila, fila_existente):
                        self._interfaz.ventanas.mostrar_mensaje(
                            'La selección contiene una relación anexo/pedido inconsistente en cliente o fecha.'
                        )
                        return []
                    continue

                fila_pedido = buscar_fila_por_order_document_id(
                    related_order_id,
                    filas_base=filas_normalizadas,
                    validar_con=fila
                )

                if not fila_pedido:
                    fila_pedido = buscar_fila_por_order_document_id(
                        related_order_id,
                        validar_con=fila
                    )

                if not fila_pedido:
                    self._interfaz.ventanas.mostrar_mensaje(
                        f'No se encontró un pedido base válido ({related_order_id}) para una de las órdenes seleccionadas.'
                    )
                    return []

                if not validar_relacion_pedido_base(fila, fila_pedido):
                    self._interfaz.ventanas.mostrar_mensaje(
                        'Una orden seleccionada apunta a un pedido inconsistente en cliente o fecha. No se puede facturar.'
                    )
                    return []

                pedido_base_id = obtener_order_document_id_de_fila(fila_pedido)

                if pedido_base_id in order_document_ids_actuales:
                    continue

                filas_a_agregar.append(fila_pedido)
                if pedido_base_id:
                    order_document_ids_actuales.add(pedido_base_id)

            if filas_a_agregar:
                filas_normalizadas = filas_a_agregar + filas_normalizadas

            return filas_normalizadas

        # --------------------------------------------------------------------------------------------------------------
        try:
            filas = self._obtener_valores_filas_pedidos_seleccionados()

            if not filas:
                return

            filas = normalizar_filas_para_facturar(filas)
            if not filas:
                return

            filas_filtradas = filtrar_filas_facturables_por_status(filas)

            if not filas_filtradas:
                if pedidos_fuera_status_timbrado:
                    mostrar_pedidos_refacturados(pedidos_fuera_status_timbrado)
                self._interfaz.ventanas.mostrar_mensaje('No hay pedidos con status válido para facturar')
                return

            if any(int(f.get('OrderTypeID') or 0) in (2, 3) for f in filas_filtradas):
                crear_documento(filas_filtradas, combinado=True, mismo_cliente=True)
                if pedidos_fuera_status_timbrado:
                    mostrar_pedidos_refacturados(pedidos_fuera_status_timbrado)
                return

            if len(filas_filtradas) == 1:
                hay_pedidos_del_mismo_cliente = buscar_pedidos_en_proceso_del_mismo_cliente(filas_filtradas)

                if not hay_pedidos_del_mismo_cliente:
                    crear_documento(filas_filtradas)
                    if pedidos_fuera_status_timbrado:
                        mostrar_pedidos_refacturados(pedidos_fuera_status_timbrado)

                if hay_pedidos_del_mismo_cliente:
                    respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                        'Hay otro pedido del mismo cliente en proceso o por timbrar. ¿Desea continuar?'
                    )
                    if respuesta:
                        crear_documento(filas_filtradas)
                        if pedidos_fuera_status_timbrado:
                            mostrar_pedidos_refacturados(pedidos_fuera_status_timbrado)
                return

            se_pueden_combinar = validar_si_se_pueden_combinar(filas_filtradas)
            if se_pueden_combinar:
                respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                    'Las órdenes son del mismo cliente y pueden combinarse. ¿Desea combinarlas?'
                )
                if respuesta:
                    crear_documento(filas_filtradas, combinado=True, mismo_cliente=True)
                    if pedidos_fuera_status_timbrado:
                        mostrar_pedidos_refacturados(pedidos_fuera_status_timbrado)
                    return

            filas_filtradas = excluir_pedidos_con_ordenes_en_proceso_del_mismo_cliente(filas_filtradas)
            if not filas_filtradas:
                if pedidos_fuera_status_timbrado:
                    mostrar_pedidos_refacturados(pedidos_fuera_status_timbrado)
                return

            crear_documento(filas_filtradas)
            if pedidos_fuera_status_timbrado:
                mostrar_pedidos_refacturados(pedidos_fuera_status_timbrado)
            return

        finally:
            self._rellenar_tabla()
            self._reanudar_autorefresco()



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

