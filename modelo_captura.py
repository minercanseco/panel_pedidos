import copy
import uuid
from datetime import datetime


class ModeloCaptura:
    def __init__(self, base_de_datos, ventanas, utilerias, cliente, parametros_contpaqi, documento):
        self.base_de_datos = base_de_datos
        self._ventanas = ventanas
        self.utilerias = utilerias
        self.cliente = cliente

        self.parametros_contpaqi = parametros_contpaqi
        self._module_id = self.parametros_contpaqi.id_modulo
        self._usuario_id = self.parametros_contpaqi.id_usuario
        self._user_name = self.parametros_contpaqi.nombre_usuario

        self.documento = documento

        self.consulta_productos = []
        self.consulta_productos_ofertados = []

        self._customer_type_id = self.cliente.customer_type_id
        self.costo_servicio_a_domicilio = self.utilerias.redondear_valor_cantidad_a_decimal(20)
        self.servicio_a_domicilio_agregado = False
        self._agregando_partida = False
        self.partida_servicio_domicilio = {}

        self.MODIFICACIONES_PEDIDO = {
            'Agregado': 1,  # partida añadida al pedido
            'Editado': 2,  # partida eliminada del pedido
            'Eliminado': 3  # parida eliminada del pedido
        }

    def buscar_productos(self, termino_buscado, tipo_busqueda):

        if termino_buscado != '' and termino_buscado:

            if tipo_busqueda == 'Término':
                return self.base_de_datos.buscar_product_id_termino(termino_buscado)

            if tipo_busqueda == 'Línea':
                return self.base_de_datos.buscar_product_id_linea(termino_buscado)

            return False

    def mensajes_de_error(self, numero_mensaje, master=None):

        mensajes = {
            0: 'El valor de la cantidad no puede ser menor o igual a zero',
            1: 'El valor de la pieza no puede ser numero fracionario.',
            2: 'El monto no puede ser menor o igual a 1',
            3: 'El producto no tiene una equivalencia válida',
            4: 'No se puede calcular el monto de un producto cuya unidad sea pieza.',
            5: 'Solo puede elegir o monto o pieza en productos que tengan equivalencia.',
            6: 'El término de búsqueda no arrojó ningún resultado.',
            7: 'La el código de barras es inválido.',
            8: 'La consulta por código no devolvió ningún resultado.',
            9: 'La consulta a la base de datos del código proporcionado no devolvió resultados.',
            10: 'El producto no está disponible a la venta favor de validar.',
            11: 'El producto no tiene existencia favor de validar.',
            12: 'El cliente solo tiene una direccion agreguela desde editar cliente.',
            13: 'En el módulo de pedidos no se puede eliminar el servicio a domicilio manualmente.'
        }

        self._ventanas.mostrar_mensaje(mensajes[numero_mensaje], master)

    def obtener_product_ids_consulta(self, consulta_productos):
        product_ids = [producto['ProductID'] for producto in consulta_productos]

        if len(product_ids) == 1:
            return product_ids[0]

        return product_ids

    def buscar_info_productos_por_ids(self, productos_ids, no_en_venta=None):

        if no_en_venta:
            return self.base_de_datos.buscar_info_productos(productos_ids,
                                                            self._customer_type_id,
                                                            no_en_venta=True)
        return self.base_de_datos.buscar_info_productos(productos_ids, self._customer_type_id)

    def agregar_impuestos_productos(self, consulta_productos):
        consulta_procesada = []
        for producto in consulta_productos:
            producto_procesado = self.utilerias.calcular_precio_con_impuesto_producto(producto)
            consulta_procesada.append(producto_procesado)
        return consulta_procesada

    def buscar_informacion_producto(self, product_id):
        info_producto = [producto for producto in self.consulta_productos
                         if product_id == producto['ProductID']]

        return info_producto[0] if info_producto else {}

    def buscar_productos_ofertados_cliente(self):

        consulta_productos_ofertados = self.base_de_datos.buscar_productos_en_oferta(self._customer_type_id)
        productos_ids = [producto['ProductID'] for producto in consulta_productos_ofertados]

        consulta_productos = self.buscar_info_productos_por_ids(productos_ids)
        consulta_procesada = self.agregar_impuestos_productos(consulta_productos)
        self.consulta_productos_ofertados = consulta_productos_ofertados
        self.consulta_productos = consulta_procesada

        return consulta_procesada

    def agregar_partida_tabla(self, partida, document_item_id, tipo_captura, unidad_cayal=0, monto_cayal=0):

        if not self._agregando_partida:
            try:
                self._agregando_partida = True
                cantidad = self.utilerias.redondear_valor_cantidad_a_decimal(partida['cantidad'])
                comments = partida.get('Comments', '')
                producto = partida.get('ProductName', '')
                partida['TipoCaptura'] = tipo_captura
                partida['DocumentItemID'] = document_item_id
                partida['CayalAmount'] = monto_cayal
                partida['uuid'] = uuid.uuid4()

                if self.documento.document_id > 0 and document_item_id == 0:
                    partida['ItemProductionStatusModified'] = 1
                    partida['CreatedBy'] = self._usuario_id

                    comentario = f'AGREGADO POR {self._user_name}'
                    self.agregar_partida_items_documento_extra(partida, 'agregar', comentario, partida['uuid'])

                # en caso que el modulo se use para capturar otro tipo de documentos que no sean pedidos el valor por defecto
                # debe ser 0 y para las subsecuentes modificaciones segun aplique
                # en funcion del diccionario modificaciones_pedido
                item_production_status_modified = partida.get('ItemProductionStatusModified', 0)
                partida['ItemProductionStatusModified'] = item_production_status_modified
                partida['CreatedBy'] = self._usuario_id

                cantidad_piezas = 0 if unidad_cayal == 0 else self.utilerias.redondear_valor_cantidad_a_decimal(partida['CayalPiece'])

                equivalencia = self.base_de_datos.fetchone(
                    'SELECT ISNULL(Equivalencia,0) Equivalencia FROM orgProduct WHERE ProductID = ?'
                    , partida.get('ProductID', 0))
                equivalencia = 0 if not equivalencia else equivalencia
                equivalencia_decimal = self.utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

                if equivalencia_decimal > 0 and unidad_cayal == 1:
                    cantidad_piezas = int((cantidad/equivalencia_decimal))

                partida['CayalPiece'] = cantidad_piezas

                partida_tabla = (cantidad,
                                 cantidad_piezas,
                                 partida['ProductKey'],
                                 producto,
                                 partida['Unit'],
                                 self.utilerias.redondear_valor_cantidad_a_decimal(partida['precio']),
                                 self.utilerias.redondear_valor_cantidad_a_decimal(partida['subtotal']),
                                 self.utilerias.redondear_valor_cantidad_a_decimal(partida['impuestos']),
                                 self.utilerias.redondear_valor_cantidad_a_decimal(partida['total']),
                                 partida['ProductID'],
                                 partida['DocumentItemID'],
                                 partida['TipoCaptura'],  # Tipo de captura 1 para manual y 0 para captura por pistola
                                 cantidad_piezas,  # Viene del control de captura manual
                                 partida['CayalAmount'],  # viene del control de tipo monto
                                 partida['uuid'],
                                 partida['ItemProductionStatusModified'],
                                 comments,
                                 partida['CreatedBy']
                                 )
                # agregar tipo de captura
                tabla_captura = self._ventanas.componentes_forma['tvw_productos']
                self._ventanas.insertar_fila_treeview(tabla_captura, partida_tabla, al_principio=True)
                self.actualizar_totales_documento(partida)
                self.agregar_partida_items_documento(partida)

                # si aplica remueve el servicio a domicilio
                if self._module_id == 1687 and self.servicio_a_domicilio_agregado == True:
                    if self.documento.total - self.costo_servicio_a_domicilio >= 200:
                        self.remover_servicio_a_domicilio()

            finally:
                self._agregando_partida = False



    def agregar_partida_items_documento(self, partida):
        self.documento.items.append(partida)

    def actualizar_totales_documento(self, partida, decrementar=None):

        subtotal_partida = partida.get('subtotal', 0)
        subtotal_documento = self.utilerias.redondear_valor_cantidad_a_decimal(self.documento.subtotal)

        total_partida = partida.get('total', 0)
        total_documento = self.utilerias.redondear_valor_cantidad_a_decimal(self.documento.total)

        total_impuestos_partida = partida.get('impuestos', 0)
        total_impuestos_documento = self.utilerias.redondear_valor_cantidad_a_decimal(self.documento.total_tax)

        if decrementar:
            subtotal_documento -= subtotal_partida
            total_documento -= total_partida
            total_impuestos_documento -= total_impuestos_partida

        if not decrementar:
            subtotal_documento += subtotal_partida
            total_documento += total_partida
            total_impuestos_documento += total_impuestos_partida

        self.documento.total = total_documento
        total_documento_moneda = self.utilerias.convertir_decimal_a_moneda(total_documento)
        self._ventanas.insertar_input_componente('lbl_total', total_documento_moneda)

        self.documento.total_tax = total_impuestos_documento
        self.documento.subtotal = subtotal_documento

        self._ventanas.insertar_input_componente('lbl_articulos',
                                                 self._ventanas.numero_filas_treeview('tvw_productos'))

        if self.cliente.cayal_customer_type_id in (1,2) and self.cliente.credit_block == 0:
            debe = self.cliente.debt
            debe = self.utilerias.redondear_valor_cantidad_a_decimal(debe)

            debe += total_documento
            debe_moneda = self.utilerias.convertir_decimal_a_moneda(debe)
            self._ventanas.insertar_input_componente('lbl_debe', debe_moneda)

            disponible = self.cliente.remaining_credit
            disponible = self.utilerias.redondear_valor_cantidad_a_decimal(disponible)

            disponible = disponible - total_documento
            disponible_moneda = self.utilerias.convertir_decimal_a_moneda(disponible)
            self._ventanas.insertar_input_componente('lbl_restante', disponible_moneda)

    def remover_servicio_a_domicilio(self):

        if self.documento.document_id > 0:
            return

        self.servicio_a_domicilio_agregado = False
        self.remover_partida_items_documento(5606)
        self.remover_product_id_tabla(5606)
        self.actualizar_totales_documento(self.partida_servicio_domicilio, decrementar=True)

    def agregar_servicio_a_domicilio(self, partida_eliminada=None):
        if self._module_id != 1687:
            return

        existe_servicio_a_domicilio = [producto for producto in self.documento.items
                                       if producto['ProductID'] == 5606]

        if existe_servicio_a_domicilio:
            return

        if self.documento.document_id > 0 and not partida_eliminada:
            return

        if self._module_id == 1687:
            parametros_pedido = self.documento.order_parameters
            order_type_id = parametros_pedido.get('OrderTypeID', 1)
            if order_type_id in (2,3):
                return

        delivery_cost_iva = self.base_de_datos.buscar_costo_servicio_domicilio(self.documento.address_detail_id)
        self.costo_servicio_a_domicilio = self.utilerias.redondear_valor_cantidad_a_decimal(delivery_cost_iva)
        delivery_cost = self.utilerias.calcular_monto_sin_iva(delivery_cost_iva)

        info_producto = self.buscar_info_productos_por_ids(5606, no_en_venta=True)

        if info_producto:
            info_producto = info_producto[0]

            info_producto['SalePrice'] = delivery_cost

            partida = self.utilerias.crear_partida(info_producto, cantidad=1)

            self.partida_servicio_domicilio = partida
            partida['Comments'] = ''
            self.agregar_partida_tabla(partida, document_item_id=0, tipo_captura=2, unidad_cayal=1, monto_cayal=0)

            self.servicio_a_domicilio_agregado = True

    def remover_product_id_tabla(self, product_id):
        filas = self._ventanas.obtener_filas_treeview('tvw_productos')

        for fila in filas:
            valores = self._ventanas.procesar_fila_treeview('tvw_productos', fila)
            product_id_tabla = int(valores['ProductID'])
            if product_id_tabla == product_id:
                self._ventanas.remover_fila_treeview('tvw_productos', fila)

    def remover_partida_items_documento(self, product_id):
        partidas = self.documento.items

        partidas_filtradas = [partida for partida in partidas if partida['ProductID'] != product_id]

        self.documento.items = partidas_filtradas

    def crear_texto_existencia_producto(self, info_producto):
        product_id = info_producto.get('ProductID',0)
        unidad = info_producto.get('Unit', 'PIEZA')
        consulta = self.base_de_datos.buscar_existencia_productos(product_id)
        existencia = 0.0
        if consulta:
           existencia = consulta[0].get('Existencia', 0.0)

        existencia = 0 if existencia < 0 else existencia

        unidad_producto = self.utilerias.abreviatura_unidad_producto(unidad)

        producto_especial = self.utilerias.equivalencias_productos_especiales(product_id)
        if producto_especial:
            unidad_producto = producto_especial[0]
            existencia = existencia / producto_especial[1]

        existencia_decimal = self.utilerias.redondear_valor_cantidad_a_decimal(existencia)

        return f'{existencia_decimal} {unidad_producto}'

    def crear_texto_cantidad_producto(self, cantidad, unidad, product_id):
        unidad_producto = self.utilerias.abreviatura_unidad_producto(unidad)

        producto_especial = self.utilerias.equivalencias_productos_especiales(product_id)
        if producto_especial:
            unidad_producto = producto_especial[0]

        return f'{cantidad:.2f} {unidad_producto}'

    def agregar_partida_items_documento_extra(self, partida, accion, comentario, uuid_tabla):
        # esta funcion procesa las partidas extra (agregadas, eliminadas, editadas) despues de la creación del docto
        # para inserción en tabla de respaldo, para procesamiento en panel de producción
        # considerando que las partidas editadas pueden ser editadas multiples veces
        # considerando que las partidas agregadas pueden ser agregadas, editadas y eliminadas
        # considerando que las partidas eliminadas pueden ser solo eliminadas

        partida_copia = copy.deepcopy(partida)
        partida_copia['uuid'] = uuid_tabla

        # agrega el comentario a la partida despues de agregarle la hora de procesamiento
        ahora = datetime.now().strftime('%Y-%m-%d a las %H:%M')
        comentario = f'{comentario} ({ahora})'
        partida_copia['Comments'] = comentario

        partidas_extra = self.documento.items_extra
        nuevas_partidas = [
                partida_extra for partida_extra in partidas_extra
                if str(partida_extra['uuid']) != str(uuid_tabla)
            ]

        # procesa la partida y agregala

        if accion == 'eliminar':
            partida_copia['ItemProductionStatusModified'] = 3

        if accion == 'editar':
            partida_copia['ItemProductionStatusModified'] = 2

        if accion == 'agregar':
            partida_copia['ItemProductionStatusModified'] = 1

        nuevas_partidas.append(partida_copia)

        self.documento.items_extra = nuevas_partidas



