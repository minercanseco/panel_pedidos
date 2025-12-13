import copy

from datetime import datetime
from cayal.impuestos import Impuestos


class ModeloCaptura:
    def __init__(self, base_de_datos, utilerias, cliente, parametros_contpaqi, documento, ofertas = None, bloquear=False):
        self.base_de_datos = base_de_datos
        self.utilerias = utilerias
        self.documento = documento
        self.cliente = cliente
        self._ofertas = ofertas
        self.impuestos = Impuestos()

        self.parametros = parametros_contpaqi
        self.module_id = self.parametros.id_modulo
        self.user_id = self.parametros.id_usuario
        self.user_name = self.obtener_user_name()
        self.bloquear_documento = bloquear


        self.consulta_productos = []
        self.consulta_productos_ofertados = []
        self.consulta_productos_ofertados_btn = []
        self.products_ids_ofertados = []

        self.consulta_uso_cfdi = []
        self.consulta_formas_pago = []
        self.consulta_metodos_pago = []
        self.consulta_regimenes = []

        self.LINEAS_PRODUCTOS_PERMITIDOS_VALES = [
            'RES LOCAL', 'CERDO', 'POLLO', 'VERDURAS', 'LISTAS PARA COCINAR', 'HUEVO'
        ]

        self.partida_servicio_domicilio = {}

        self.MODIFICACIONES_PEDIDO = {
            'Agregado': 1,  # partida añadida al pedido
            'Editado': 2,  # partida eliminada del pedido
            'Eliminado': 3  # parida eliminada del pedido
        }

    def obtener_user_name(self):
        if self.documento.document_id > 0:
            return self.base_de_datos.buscar_nombre_de_usuario(self.documento.created_by)
        if self.documento.document_id < 1:
            return self.base_de_datos.buscar_nombre_de_usuario(self.user_id)

    def obtener_nombre_y_prefijo_segun_modulo(self):
        nombre_modulo = {
            1687: 'PEDIDOS',
            21: 'MAYOREO',
            1400: 'MINISUPER',
            158: 'VENTAS',
            1316: 'NOTAS',
            1319: 'GLOBAL',
            202: 'ENTRADA',
            203: 'SALIDA',
            1692: 'C.EMPLEADOS'

        }
        return nombre_modulo.get(self.module_id, 'CAYAL')

    def buscar_productos(self, termino_buscado, tipo_busqueda):

        if termino_buscado != '' and termino_buscado:

            if tipo_busqueda == 'Término':
                return self.base_de_datos.buscar_product_id_termino(termino_buscado)

            if tipo_busqueda == 'Línea':
                return self.base_de_datos.buscar_product_id_linea(termino_buscado)

            if tipo_busqueda == 'Clave':
                return self.base_de_datos.buscar_product_id_clave(termino_buscado)

            return False

    def obtener_product_ids_consulta(self, consulta_productos):
        product_ids = [producto['ProductID'] for producto in consulta_productos]

        if len(product_ids) == 1:
            return product_ids[0]

        return product_ids

    def buscar_info_productos_por_ids(self, productos_ids, no_en_venta=None):

        if no_en_venta:
            return self.base_de_datos.buscar_info_productos(productos_ids,
                                                            self.cliente.customer_type_id,
                                                            no_en_venta=True)
        return self.base_de_datos.buscar_info_productos(productos_ids, self.cliente.customer_type_id)

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
        consulta_procesada = self._ofertas['consulta_productos_ofertados']

        self.consulta_productos_ofertados = consulta_procesada
        self.consulta_productos = consulta_procesada
        self.consulta_productos_ofertados_btn = self._ofertas['consulta_productos_ofertados_btn']
        self.products_ids_ofertados = self._ofertas['products_ids_ofertados']

        return consulta_procesada

    def dividir_partida(self, partida, monto_limite):
        tax_type_id = partida.get('TaxTypeID', 10)
        clave_unidad = partida.get('ClaveUnidad', 'H87')
        clave_sat = partida.get('ClaveProdServ')

        nueva_partida = copy.deepcopy(partida)
        cantidad_previa = self.utilerias.convertir_valor_a_decimal(partida.get('cantidad', 0))
        total_partida = partida.get('total', 0)
        sale_price = self.utilerias.convertir_valor_a_decimal(partida.get('SalePrice', 0))

        # Cantidad que permanece en el documento actual (lo permitido por cupones)
        # Derivación algebraica: cantidad = (coupons_mount - total_actual_sin_partida) / precio
        # Aquí recibes 'monto_limite' = total_real - coupons_mount  -> exceso
        # Por tanto: cantidad_permitida = (total_partida - monto_limite) / precio
        if sale_price > 0:
            cantidad_permitida = (total_partida - monto_limite) / sale_price
        else:
            cantidad_permitida = cantidad_previa  # evita división si precio 0

        # Sanea por redondeos/floating:
        if cantidad_permitida < 0:
            cantidad_permitida = 0
        if cantidad_permitida > cantidad_previa:
            cantidad_permitida = cantidad_previa

        cantidad_restante = self.utilerias.convertir_valor_a_decimal(cantidad_previa - cantidad_permitida)

        # Recalcula totales de ambas
        valores_partida_perm = self.utilerias.calcular_totales_partida(sale_price,
                                                                       cantidad_permitida,
                                                                       tax_type_id,
                                                                       clave_unidad,
                                                                       clave_sat
                                                                       )
        partida.update(valores_partida_perm)

        valores_partida_rest = self.utilerias.calcular_totales_partida(sale_price,
                                                                       cantidad_restante,
                                                                       tax_type_id,
                                                                       clave_unidad,
                                                                       clave_sat
                                                                       )
        nueva_partida.update(valores_partida_rest)

        return partida, nueva_partida

    def obtener_folio_documento(self,document_id =0, order_document_id=0):
        folio = ''
        if document_id != 0:
            folio = self.base_de_datos.fetchone('SELECT Folio FROM docDocument WHERE DocumentID = ?', (document_id,))
        if order_document_id != 0:
            folio = self.base_de_datos.fetchone('SELECT Folio FROM docDocumentOrderCayal WHERE DocumentID = ?',
                                                (order_document_id,))

        return folio

    def crear_cabecera_documento(self, module_id = 0, prefix=None):

        module_id = self.module_id if module_id == 0 else module_id
        prefix = self.documento.prefix if not prefix else prefix

        document_id = self.base_de_datos.crear_documento(
                            self.documento.cfd_type_id,
                             prefix,
                            self.cliente.business_entity_id,
                            module_id,
                            self.user_id,
                            self.documento.depot_id,
                            self.documento.address_detail_id
        )
        return document_id

    def crear_cabecera_documento_relacionado(self):
        if self.module_id == 1692: # la compra por vales va relacionada a una salida de almacén
            #crear_movimiento_de_almacen(self, tipo, numero, usuario, almacen, comentario_usuario=None):
            document_id = self.base_de_datos.crear_movimiento_de_almacen(
                'salida',
                30, # movimiento de compra empleados
                90,  # usuario sistema
                2  # almacen
            )
            self.base_de_datos.relacionar_documentos(document_id, origen=self.documento.document_id)
            self.base_de_datos.relacionar_documentos(self.documento.document_id, destino=document_id)

            self.documento.destination_document_id = document_id

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

        existencia_decimal = self.utilerias.convertir_valor_a_decimal(existencia)

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

    def actualizar_info_cliente(self):
        business_entity_id = self.cliente.business_entity_id
        if business_entity_id == 0:
            return

        consulta = self.base_de_datos.buscar_info_cliente(business_entity_id)
        if not consulta:
            return
        info_cliente = consulta[0]
        self.cliente.consulta = info_cliente
        self.cliente.settear_valores_consulta()

    def settear_info_direcciones_cliente(self, business_entity_id):
        self.cliente.addresses_details = []
        direcciones_cliente = self.obtener_direcciones_cliente(business_entity_id)
        for direccion in direcciones_cliente:
            self.cliente.add_address_detail(direccion)
        return direcciones_cliente

    def obtener_direcciones_cliente(self, business_entity_id):
        return self.base_de_datos.buscar_direcciones_cliente(business_entity_id)

    def obtener_status_bloqueo_pedido(self, order_document_id, user_id):
        return self.base_de_datos.obtener_status_bloqueo_pedido(order_document_id, user_id)

    def obtener_existencia_producto(self, product_id):
        return self.base_de_datos.buscar_existencia_productos(product_id)

    def obtener_partidas_pedido(self, order_document_id):
        return self.base_de_datos.buscar_partidas_pedidos_produccion_cayal(order_document_id,
                                                                           partidas_producidas=True)

    def obtener_metodos_de_pago(self):
        if not self.consulta_metodos_pago:
            self.consulta_metodos_pago = self.base_de_datos.buscar_metodos_de_pago
        return self.consulta_metodos_pago

    def obtener_formas_de_pago(self):
        if not self.consulta_formas_pago:
            self.consulta_formas_pago = self.base_de_datos.buscar_formas_de_pago
        return self.consulta_formas_pago

    def obtener_usos_de_cfdi(self):
        if not self.consulta_uso_cfdi:
            self.consulta_uso_cfdi = self.base_de_datos.buscar_usos_de_cfdi
        return self.consulta_uso_cfdi

    def obtener_regimenes_fiscales(self):
        if not self.consulta_regimenes:
            self.consulta_regimenes = self.base_de_datos.buscar_regimenes_ficales
        return self.consulta_regimenes

    def obtener_equivalencia(self, product_id):
        return self.base_de_datos.fetchone(
            'SELECT ISNULL(Equivalencia,0) Equivalencia FROM orgProduct WHERE ProductID = ?'
            , (product_id,))

    def insertar_partida_documento(self, parametros):
        self.base_de_datos.insertar_partida_documento_cayal(parametros)

    def eliminar_partida_documento(self, document_item_id):
        self.base_de_datos.exec_stored_procedure(
            'zvwBorrarPartidasDocumentoCayal', (self.documento.document_id,
                                                self.module_id,
                                                document_item_id,
                                                self.user_id)
        )



