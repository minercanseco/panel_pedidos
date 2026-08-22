import copy

from datetime import datetime
from cayal.impuestos import Impuestos

from capturar_documento.herramientas.servicio_ofertas_cliente import GestorOfertasCliente


class ModeloCaptura:
    MODULO_PEDIDOS = 1687
    MODULO_COMPRAS = 152
    MODULOS_SIN_INSERCION_PARTIDAS = (1687,152)
    MODULOS_VENTAS = (158, 1316, 967, 1400, 21, 1319)
    MODULOS_ACTUALIZACION_TOTALES = (21, 152, 158, 967, 1316, 1319, 1400)
    MODULO_VALES = 1692
    LINEAS_PRODUCTOS_PERMITIDOS_VALES = [
        'RES LOCAL', 'CERDO', 'POLLO', 'VERDURAS', 'LISTAS PARA COCINAR', 'HUEVO'
    ]
    PREFIJOS = {
        967: 'PM', 1692: 'CE', 21: 'FM', 1400: 'FG', 1316: 'NVR', 1319: 'FGR', 158: 'NV'

    }
    def __init__(self, base_de_datos, utilerias, cliente, documento, parametros_contpaqi, ofertas = None):
        self.base_de_datos = base_de_datos
        self.documento = documento
        self.utilerias = utilerias
        self.impuestos = Impuestos()
        self.cliente = cliente
        self.parametros_contpaqi = parametros_contpaqi


        self._ofertas = ofertas
        self._gestor_ofertas = None

        self.document_id = self.documento.document_id
        self.module_id = self.parametros_contpaqi.id_modulo
        self.user_id = self.parametros_contpaqi.id_usuario
        self.user_group_id = self.base_de_datos.obtener_grupo_usuario(self.user_id)
        self.created_by = self.documento.created_by
        self.customer_type_id = self.cliente.customer_type_id

        self.user_name = self.obtener_nombre_usuario(
            self.user_id) if self.document_id < 1 else self.obtener_nombre_usuario(self.created_by)

        self.consulta_productos = []
        self.consulta_productos_ofertados = []
        self.consulta_productos_ofertados_btn = []
        self.products_ids_ofertados = []

        self.consulta_uso_cfdi = []
        self.consulta_formas_pago = []
        self.consulta_metodos_pago = []
        self.consulta_regimenes = []

        self.costo_servicio_a_domicilio = self.utilerias.redondear_valor_cantidad_a_decimal(20)
        self.servicio_a_domicilio_agregado = False
        self.partida_servicio_domicilio = {}
        self.agregando_partida = False

        self.MODIFICACIONES_PARTIDA = {
            'Agregado': 1,  # partida añadida al documento o pedido
            'Editado': 2,  # partida eliminada del documento o pedido
            'Eliminado': 3  # parida eliminada del documento o pedido
        }

    # ------------------------------------------------------------------
    # Acceso a datos requerido por el controlador
    # ------------------------------------------------------------------
    def obtener_direcciones_cliente(self):
        return self.base_de_datos.rellenar_cbx_direcciones(self.cliente.business_entity_id)

    def obtener_nombre_usuario(self, user_id):
        return self.base_de_datos.buscar_nombre_de_usuario(user_id)

    def obtener_estado_pedido(self, document_id):
        if self.module_id != self.MODULO_PEDIDOS:
            return 0

        estado = self.base_de_datos.fetchone(
            'SELECT ISNULL(StatusID, 0) Status '
            'FROM docDocumentOrderCayal WHERE OrderDocumentID = ?',
            (document_id,),
        )
        return 0 if not estado else estado

    def actualizar_proveedor_documento(self, business_entity_id):
        """Cambia el dueño de una compra existente."""
        document_id = int(getattr(self.documento, 'document_id', 0) or 0)
        business_entity_id = int(business_entity_id or 0)

        if self.module_id != self.MODULO_COMPRAS or document_id <= 0:
            return False

        if business_entity_id <= 0:
            raise ValueError('El proveedor seleccionado no es válido.')

        self.base_de_datos.command(
            'UPDATE docDocument SET BusinessEntityID = ? WHERE DocumentID = ?',
            (business_entity_id, document_id),
        )
        return True

    def actualizar_totales_documento(self, document_id=None):
        """Sincroniza los importes que consumen las herramientas de cobro."""
        if self.module_id not in self.MODULOS_ACTUALIZACION_TOTALES:
            return False

        document_id = int(
            document_id or getattr(self.documento, 'document_id', 0) or 0
        )
        if document_id <= 0:
            return False

        subtotal = getattr(self.documento, 'subtotal', 0) or 0
        subtotal_with_discount = getattr(
            self.documento,
            'subtotal_with_discount',
            subtotal,
        )
        total_discount = getattr(self.documento, 'total_discount', 0) or 0
        total_tax = getattr(self.documento, 'total_tax', 0) or 0
        total_retention = getattr(
            self.documento,
            'total_retention',
            0,
        ) or 0
        ieps = getattr(self.documento, 'ieps', 0) or 0
        iva = getattr(self.documento, 'iva', 0) or 0
        total = getattr(self.documento, 'total', 0) or 0

        self.base_de_datos.command(
            '''
            WITH Payments AS (
                SELECT
                    DP.DocumentID,
                    COALESCE(SUM(DP.Amount), 0) AS TotalPaid
                FROM docDocumentPayment DP
                INNER JOIN docFinancialOperation DF
                    ON DF.FinancialOperationID = DP.FinancialOperationID
                WHERE
                    DP.DocumentID = ?
                    AND DF.DeletedOn IS NULL
                GROUP BY DP.DocumentID
            )
            UPDATE D
            SET
                D.SubTotal = ?,
                D.SubTotalWithDiscount = ?,
                D.TotalDiscount = ?,
                D.TotalTax = ?,
                D.TotalRetention = ?,
                D.IEPS = ?,
                D.IVA = ?,
                D.Total = ?,
                D.TotalPaid = COALESCE(P.TotalPaid, 0),

                D.Balance =
                    CASE
                        WHEN ? - COALESCE(P.TotalPaid, 0) > 0
                            THEN ? - COALESCE(P.TotalPaid, 0)
                        ELSE 0
                    END,

                D.StatusPaidID =
                    CASE
                        -- No tiene cobros
                        WHEN COALESCE(P.TotalPaid, 0) <= 0 THEN 3

                        -- Está sobrepagado
                        WHEN CAST(COALESCE(P.TotalPaid, 0) AS DECIMAL(18, 2))
                           > CAST(? AS DECIMAL(18, 2)) THEN 4

                        -- Está totalmente pagado
                        WHEN CAST(COALESCE(P.TotalPaid, 0) AS DECIMAL(18, 2))
                           = CAST(? AS DECIMAL(18, 2)) THEN 1

                        -- Tiene cobros, pero todavía debe dinero
                        ELSE 2
                    END
            FROM docDocument D
            LEFT JOIN Payments P
                ON P.DocumentID = D.DocumentID
            WHERE D.DocumentID = ?
            ''',
            (
                document_id,
                subtotal,
                subtotal_with_discount,
                total_discount,
                total_tax,
                total_retention,
                ieps,
                iva,
                total,
                total,
                total,
                total,
                total,
                document_id,
            ),
        )
        return True

    def preparar_documento_para_cobro(self):
        """Compatibilidad con el flujo existente de cobro inmediato."""
        document_id = int(
            getattr(self.documento, 'document_id', 0) or 0
        )
        if document_id <= 0:
            return False

        self.afectar_impuestos_documento(document_id)
        return self.actualizar_totales_documento(document_id)

    def afectar_impuestos_documento(self, document_id=None):
        """Reconstruye las tablas fiscales después de persistir las partidas."""
        if self.module_id not in self.MODULOS_ACTUALIZACION_TOTALES:
            return None

        document_id = int(
            document_id or getattr(self.documento, 'document_id', 0) or 0
        )
        if document_id <= 0:
            return None

        afectacion = (
            self.impuestos.afectar_y_sincronizar_totales_documento(
                self.base_de_datos,
                document_id,
            )
        )
        totales = afectacion['totales_encabezado']

        self.documento.subtotal = totales['subtotal']
        self.documento.subtotal_with_discount = totales[
            'subtotal_con_descuento'
        ]
        self.documento.total_discount = totales['descuento']
        self.documento.total_tax = totales['impuestos']
        self.documento.total_retention = totales['retenciones']
        self.documento.ieps = totales['ieps']
        self.documento.iva = totales['iva']
        self.documento.total = totales['total']

        return afectacion

    def buscar_partidas_documento(self, module_id, document_id):

        if module_id == self.MODULO_PEDIDOS:
            return self.base_de_datos.buscar_partidas_pedidos_produccion_cayal(
                document_id,
                partidas_producidas=True,
            )

        if module_id == self.MODULO_COMPRAS:
            return self.base_de_datos.buscar_partidas_documento_compras(document_id)

        if module_id in self.MODULOS_VENTAS:
            return self.base_de_datos.buscar_partidas_documento(module_id,document_id)

        return []

    def producto_tiene_existencia(self, product_ids):
        return bool(self.base_de_datos.buscar_existencia_productos(product_ids))

    def direccion_esta_borrada(self, address_detail_id):
        direccion = self.base_de_datos.fetchone(
            'SELECT AddressDetailID FROM orgAddress '
            'WHERE AddressDetailID = ? AND DeletedOn IS NULL',
            (address_detail_id,),
        )
        return not bool(direccion)

    def obtener_direccion_formateada(self, address_detail_id):
        return self.base_de_datos.buscar_detalle_direccion_formateada(address_detail_id)

    def actualizar_direcciones_cliente(self, direcciones_adicionales):
        return self.base_de_datos.actualizar_direcciones_panel_direcciones(
            direcciones_adicionales,
            self.cliente.business_entity_id,
            self.user_id,
        )

    def crear_parametros_pedido(self):
        if self.documento.document_id >= 1:
            return getattr(self.documento, 'order_parameters', {})

        comentario = self.documento.comments
        parametros = {
            'OrderTypeID': 1,
            'CreatedBy': self.user_id,
            'CreatedOn': datetime.now(),
            'CommentsOrder': comentario.upper().strip() if comentario else '',
            'BusinessEntityID': self.cliente.business_entity_id,
            'RelatedOrderID': 0,
            'ZoneID': self.cliente.zone_id,
            'SubTotal': 0,
            'TotalTax': 0,
            'Total': 0,
            'HostName': self.utilerias.obtener_hostname(),
            'AddressDetailID': self.documento.address_detail_id,
            'DocumentTypeID': self.documento.cfd_type_id,
            'OrderDeliveryCost': self.documento.delivery_cost,
            'DepotID': self.documento.depot_id,
        }

        way_to_pay_id = parametros.get('WayToPayID', 1)
        delivery_type_id = parametros.get('OrderDeliveryTypeID', 1)
        payment_confirmed_id = 2 if way_to_pay_id == 6 else 1
        if delivery_type_id == 2 and way_to_pay_id != 6:
            payment_confirmed_id = 4
        parametros['PaymentConfirmedID'] = payment_confirmed_id

        self.documento.order_parameters = parametros
        return parametros

    def buscar_info_fiscal(self, tipo):
        if not tipo:
            return
        tipos = {
            'metodos_de_pago': (self.base_de_datos.buscar_metodos_de_pago, self.consulta_metodos_pago),
            'formas_de_pago':(self.base_de_datos.buscar_formas_de_pago, self.consulta_formas_pago),
            'regimenes_fiscales':(self.base_de_datos.buscar_regimenes_ficales, self.consulta_regimenes),
            'usos_de_cfdi':(self.base_de_datos.buscar_usos_de_cfdi, self.consulta_uso_cfdi)
        }
        funcion = tipos[tipo][0]
        lista = tipos[tipo][1]
        consulta = funcion()

        if consulta:
            lista = consulta
            return lista

        return []

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
        if self.module_id == self.MODULO_COMPRAS:
            no_en_venta = True
        if no_en_venta:
            return self.base_de_datos.buscar_info_productos(productos_ids,
                                                            self.customer_type_id,
                                                            no_en_venta=True,
                                                            business_entity_id=self.documento.business_entity_id
                                                            )
        return self.base_de_datos.buscar_info_productos(productos_ids, self.customer_type_id, business_entity_id=self.documento.business_entity_id)

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

        if not hasattr(self, "_gestor_ofertas") or self._gestor_ofertas is None:
            self._gestor_ofertas = GestorOfertasCliente(
                self.base_de_datos,
                self.utilerias
            )

        self._ofertas = self._gestor_ofertas.obtener_ofertas_cliente(
            self.cliente
        )

        consulta_productos = self._ofertas["consulta_productos"]
        consulta_productos_ofertados = self._ofertas["consulta_productos_ofertados"]

        self.consulta_productos_ofertados = consulta_productos_ofertados
        self.consulta_productos = consulta_productos
        self.consulta_productos_ofertados_btn = self._ofertas["consulta_productos_ofertados_btn"]
        self.products_ids_ofertados = self._ofertas["products_ids_ofertados"]

        return consulta_productos_ofertados

    def dividir_partida(self, partida, monto_limite):
        tax_type_id = partida.get('TaxTypeID', 10)
        clave_unidad = partida.get('ClaveUnidad', 'H87')
        clave_sat = partida.get('ClaveProdServ')

        nueva_partida = copy.deepcopy(partida)
        cantidad_previa = self.utilerias.redondear_valor_cantidad_a_decimal(partida.get('cantidad', 0))
        total_partida = partida.get('total', 0)
        sale_price = self.utilerias.redondear_valor_cantidad_a_decimal(partida.get('SalePrice', 0))

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

        cantidad_restante = self.utilerias.redondear_valor_cantidad_a_decimal(cantidad_previa - cantidad_permitida)

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

    def agregar_partida_base_de_datos(self, partida):



        if self.module_id not in self.MODULOS_SIN_INSERCION_PARTIDAS:

            if self.documento.document_id == 0:
                document_id = self.crear_cabecera_documento()
                self.documento.document_id = document_id



                self.crear_cabecera_documento_relacionado()

            if self.documento.finish_document != 1:

                # agregamos partida al documento de venta
                parametros = (
                    self.documento.document_id,
                    partida['ProductID'],
                    2,  # depot id minisuper
                    partida['cantidad'],
                    partida['precio'],
                    0,  # costo
                    partida['subtotal'],
                    partida['TipoCaptura'],
                    self.module_id,
                    partida['Comments']
                )
                self.base_de_datos.insertar_partida_documento_cayal(parametros)

        if self.module_id == self.MODULO_VALES: # modulo de vales

            if self.documento.finish_document == 0: # aplica para el módulo de vales

                # agregamos partida al documento de salida
                costo = self.utilerias.redondear_valor_cantidad_a_decimal(partida['CostPrice'])
                cantidad = self.utilerias.redondear_valor_cantidad_a_decimal(partida['cantidad'])
                total = costo * cantidad

                parametros = (
                    self.documento.destination_document_id,
                    partida['ProductID'],
                    2,  # depot id minisuper
                    cantidad,
                    0,
                    costo,  # costo
                    total,
                    partida['TipoCaptura'],
                    203, # salida de inventario
                    partida['Comments']
                )
                self.base_de_datos.insertar_partida_documento_cayal(parametros)

            if self.documento.finish_document == 1: # aplica para el restante del módulo vales
                # agregamos partida al documento de venta folio minisuper
                parametros = (
                    self.documento.adicional_document_id,
                    partida['ProductID'],
                    2,  # depot id minisuper
                    partida['cantidad'],
                    partida['precio'],
                    0,  # costo
                    partida['subtotal'],
                    partida['TipoCaptura'],
                    self.module_id,
                    partida['Comments']
                )
                self.base_de_datos.insertar_partida_documento_cayal(parametros)

                self.documento.finish_document = 2 # bandera de cierre final del documento

    def crear_cabecera_documento(self, module_id=0, prefix=None):
        module_id = self.module_id if module_id == 0 else module_id

        if not prefix:
            prefix = self.PREFIJOS.get(module_id, '')

        document_id = self.base_de_datos.crear_documento(
            self.documento.cfd_type_id,
            prefix,
            self.cliente.business_entity_id,
            module_id,
            self.user_id,
            self.documento.depot_id,
            self.documento.address_detail_id,
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

    def obtener_folio_documento(self, document_id):
        return self.base_de_datos.fetchone('SELECT Folio FROM docDocument WHERE DocumentID = ?', (document_id,))

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

    def obtener_equivalencia_producto(self, product_id):
        return self.base_de_datos.fetchone(
                    'SELECT ISNULL(Equivalencia,0) Equivalencia FROM orgProduct WHERE ProductID = ?'
                    , (product_id,))

    def obtener_costo_servicio_documicilio(self, address_detail_id):
        return self.base_de_datos.buscar_costo_servicio_domicilio(address_detail_id)

    def obtener_costo_producto(self, product_id):
        return self.base_de_datos.fetchone('SELECT COALESCE(UltimoCosto,0) FROM zvwUltimoCostoProductosCayal2Final WHERE ProductID = ?',
                                           (product_id,))
