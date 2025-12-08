import copy
import uuid
import gzip, pickle
from pathlib import Path
from datetime import datetime
from cayal.impuestos import Impuestos


class ModeloCaptura:
    def __init__(self, base_de_datos, ventanas, utilerias, cliente, parametros_contpaqi, documento, ofertas = None):
        self.base_de_datos = base_de_datos
        self._ventanas = ventanas
        self.utilerias = utilerias
        self.cliente = cliente
        self._ofertas = ofertas
        self._impuestos = Impuestos()

        self.parametros_contpaqi = parametros_contpaqi
        self._module_id = self.parametros_contpaqi.id_modulo
        self._user_id = self.parametros_contpaqi.id_usuario
        self._user_name = self.parametros_contpaqi.nombre_usuario

        self.documento = documento

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

    def rellenar_cbxs_fiscales(self):


        # ==============
        # Helpers locales
        # ==============
        def _today_str():
            return datetime.now().strftime("%Y%m%d")

        def _cache_dir():
            base = Path.home() / ".cayal_cache"
            base.mkdir(parents=True, exist_ok=True)
            return base

        def _fiscales_cache_path(kind: str, day: str):
            return _cache_dir() / f"fiscales_{kind}_{day}.pkl.gz"

        def _cache_save_today(kind: str, data):
            day = _today_str()
            path = _fiscales_cache_path(kind, day)
            try:
                with gzip.open(path, "wb") as f:
                    pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            except Exception:
                pass

        def _cache_load_if_today(kind: str):
            day = _today_str()
            path = _fiscales_cache_path(kind, day)
            try:
                if path.exists():
                    with gzip.open(path, "rb") as f:
                        return pickle.load(f)
            except Exception:
                return None
            return None

        def _cache_cleanup_not_today():
            day = _today_str()
            for f in _cache_dir().glob("fiscales_*.pkl.gz"):
                if not f.name.endswith(f"_{day}.pkl.gz"):
                    try:
                        f.unlink(missing_ok=True)
                    except Exception:
                        pass

        # ==============
        # Lógica principal
        # ==============
        if not hasattr(self, "_fiscales_cache_mem"):
            self._fiscales_cache_mem = {
                'metodopago': None,
                'formapago': None,
                'regimen': None,
                'usocfdi': None,
            }

        parametros = {
            'cbx_metodopago': ('metodopago', 'consulta_metodos_pago', self.base_de_datos.buscar_metodos_de_pago),
            'cbx_formapago': ('formapago', 'consulta_formas_pago', self.base_de_datos.buscar_formas_de_pago),
            'cbx_regimen': ('regimen', 'consulta_regimenes', self.base_de_datos.buscar_regimenes_ficales),
            'cbx_usocfdi': ('usocfdi', 'consulta_uso_cfdi', self.base_de_datos.buscar_usos_de_cfdi),
        }

        datos_por_tipo = {}
        for componente, (tipo, attr_name, funcion) in parametros.items():
            lista = self._fiscales_cache_mem.get(tipo)
            if lista is None:
                lista = _cache_load_if_today(tipo)
                if lista is not None:
                    self._fiscales_cache_mem[tipo] = lista
                    setattr(self, attr_name, lista)
                    _cache_cleanup_not_today()

            if lista is None:
                lista = funcion()
                self._fiscales_cache_mem[tipo] = lista
                setattr(self, attr_name, lista)
                _cache_save_today(tipo, lista)
                _cache_cleanup_not_today()

            datos_por_tipo[tipo] = lista or []

        for componente, (tipo, attr_name, _) in parametros.items():
            lista = datos_por_tipo.get(tipo, [])
            valores_cbx = [reg.get('Value') for reg in lista]
            self._ventanas.rellenar_cbx(componente, valores_cbx, sin_seleccione=True)

        parametros_cliente = {
            'cbx_metodopago': (datos_por_tipo['metodopago'], getattr(self.cliente, 'metodo_pago', None)),
            'cbx_formapago': (datos_por_tipo['formapago'], getattr(self.cliente, 'forma_pago', None)),
            'cbx_regimen': (datos_por_tipo['regimen'], getattr(self.cliente, 'company_type_name', None)),
            'cbx_usocfdi': (datos_por_tipo['usocfdi'], getattr(self.cliente, 'receptor_uso_cfdi', None)),
        }

        if getattr(self.documento, 'cfd_type_id', None) == 1 or getattr(self.cliente, 'cayal_customer_type_id',
                                                                        None) in (0, 1):
            self._ventanas.insertar_input_componente('cbx_regimen', '616 - Sin obligaciones fiscales')
            self._ventanas.insertar_input_componente('cbx_metodopago', 'PUE - Pago en una sola exhibición')
            self._ventanas.insertar_input_componente('cbx_formapago', '01 - Efectivo')
            self._ventanas.insertar_input_componente('cbx_usocfdi', 'S01 - Sin efectos fiscales.')
            for componente in parametros_cliente.keys():
                self._ventanas.bloquear_componente(componente)
            return

        for componente, (lista, clave) in parametros_cliente.items():
            if not lista:
                continue
            seleccionado = None
            if componente != 'cbx_regimen' and clave is not None:
                _match = [reg.get('Value') for reg in lista if reg.get('Clave') == clave]
                if _match:
                    seleccionado = _match[0]
                    self._ventanas.insertar_input_componente(componente, seleccionado)
                    if componente != 'cbx_formapago':
                        self._ventanas.bloquear_componente(componente)
            if seleccionado is None and clave is not None:
                _match = [reg.get('Value') for reg in lista if reg.get('Value') == clave]
                if _match:
                    seleccionado = _match[0]
                    self._ventanas.insertar_input_componente(componente, seleccionado)
                    self._ventanas.bloquear_componente(componente)
            if componente == 'cbx_formapago':
                if getattr(self.cliente, 'forma_pago', None) == '99':
                    self._ventanas.bloquear_componente(componente)

    def buscar_productos(self, termino_buscado, tipo_busqueda):

        if termino_buscado != '' and termino_buscado:

            if tipo_busqueda == 'Término':
                return self.base_de_datos.buscar_product_id_termino(termino_buscado)

            if tipo_busqueda == 'Línea':
                return self.base_de_datos.buscar_product_id_linea(termino_buscado)

            if tipo_busqueda == 'Clave':
                return self.base_de_datos.buscar_product_id_clave(termino_buscado)

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
            13: 'En el módulo de pedidos no se puede eliminar el servicio a domicilio manualmente.',
            14: 'La captura del producto no está permitida en el módulo de venta actual.',
            15: 'Con la captura de la partida excede el monto autorizado para este modulo.',
            16: 'Con la captura de la partida excede el monto de crédito autorizado.',
            17: 'La captura del documento ha conluido.'
        }

        self._ventanas.mostrar_mensaje(mensajes[numero_mensaje], master)

    def obtener_product_ids_consulta(self, consulta_productos):
        product_ids = [producto['ProductID'] for producto in consulta_productos]

        if len(product_ids) == 1:
            return product_ids[0]

        return product_ids

    def _filtrar_productos_no_permitidos(self, partida):

        if self._module_id == 1692: # restriccion por modulo validar funcionamiento
            linea = partida.get('Category1', '')
            if linea not in self.LINEAS_PRODUCTOS_PERMITIDOS_VALES:
                self.mensajes_de_error(14)
                return

        return partida

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
        consulta_procesada = self._ofertas['consulta_productos_ofertados']

        self.consulta_productos_ofertados = consulta_procesada
        self.consulta_productos = consulta_procesada
        self.consulta_productos_ofertados_btn = self._ofertas['consulta_productos_ofertados_btn']
        self.products_ids_ofertados = self._ofertas['products_ids_ofertados']

        return consulta_procesada

    def validar_restriccion_por_monto(self, partida, tipo_captura):
        total = self.documento.total
        total_partida = partida.get('total', 0)
        total_real = total_partida + total

        if self._module_id in (1400,21,1319):
            if total_real >= 2000 and self.documento.cfd_type_id == 0 and self.documento.forma_pago == '01':
                respuesta = self._ventanas.mostrar_mensaje_pregunta(
                    "Con la captura de la partida excede $2000.00, que es el monto máximo para facturas capturadas en efectivo. "
                    "¿Desea continuar?"
                )
                if not respuesta:
                    return

        # Si ya está completamente cerrado (2), no hacer nada
        if self._module_id == 1692 and self.documento.finish_document == 2:
            # IMPORTANTE: devolver True para no bloquear flujos posteriores
            return True

        if self._module_id == 1692 and self.documento.finish_document == 0:
            # restricción por vales
            if total_real > self.cliente.coupons_mount:

                clave_unidad_partida = partida.get('ClaveUnidad', 'KGM')
                if clave_unidad_partida != 'KGM':
                    self._ventanas.mostrar_mensaje(
                        "Con la captura de la partida excede el monto autorizado para este módulo. "
                        "La partida no se puede dividir debido a que su unidad es distinta de Kilo."
                    )
                    return

                respuesta = self._ventanas.mostrar_mensaje_pregunta(
                    "Con la captura de la partida excede el monto autorizado para este módulo. "
                    "¿Desea capturar la diferencia en un folio Minisuper?"
                )
                if not respuesta:
                    return

                # Calcula cuánto se puede quedar en el doc relacionado (finish_document == 0)
                monto_limite = total_real - self.cliente.coupons_mount
                partida_anterior, partida_nueva = self.dividir_partida(partida, monto_limite)

                # Etiquetas de captura
                partida_anterior['TipoCaptura'] = tipo_captura
                partida_nueva['TipoCaptura'] = tipo_captura

                # 1) INSERTA PRIMERO LA PARTE "PERMITIDA" EN EL DOCUMENTO RELACIONADO
                #    Evitar revalidación: usa document_item_id != 0 para saltar validar_restriccion_por_monto dentro de agregar_partida_tabla
                self.agregar_partida_tabla(partida_anterior, document_item_id=-1, tipo_captura=tipo_captura)

                # 2) AHORA sí marca como "finish_document = 1" y crea el folio Minisúper si no existe
                self.documento.finish_document = 1

                if not getattr(self.documento, 'adicional_document_id', 0):
                    folio_document_id = self.crear_cabecera_documento(1400, 'FG')  # fac minisuper
                    self.documento.adicional_document_id = folio_document_id

                # 3) Inserta la parte restante en el folio Minisúper
                #    Puedes ir directo a items (sin tabla) o usar la tabla con document_item_id != 0 para saltar validación.
                self.agregar_partida_items_documento(partida_nueva)
                # o, si quieres que aparezca en el treeview de la UI:
                # self.agregar_partida_tabla(partida_nueva, document_item_id=-1, tipo_captura=tipo_captura)

                return  # corta el flujo original (ya insertamos ambas partes)

        # crédito empleado Cayal ruta 7
        if self.cliente.zone_id == 1040 and self._module_id in (1400, 21, 1319):
            if total_real > self.cliente.remaining_credit and self.documento.credit_document_available == 1:

                respuesta = self._ventanas.mostrar_mensaje_pregunta(
                    "Con la captura de la partida excede el monto autorizado para este módulo. "
                    "¿Desea continuar?"
                )
                self.documento.credit_document_available = 0
                if not respuesta:
                    return

        return True

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

    def agregar_partida_tabla(self, partida, document_item_id, tipo_captura, unidad_cayal=0, monto_cayal=0):

        if self.documento.finish_document == 2:
            self.mensajes_de_error(17)
            return

        if document_item_id == 0:
            if not self._filtrar_productos_no_permitidos(partida):
                return

            if not self.validar_restriccion_por_monto(partida, tipo_captura):
                return

        if not self._agregando_partida:
            try:
                self._agregando_partida = True

                cantidad = self.utilerias.convertir_valor_a_decimal(partida['cantidad'])
                comments = partida.get('Comments', '')
                producto = partida.get('ProductName', '')
                partida['TipoCaptura'] = tipo_captura
                partida['DocumentItemID'] = document_item_id
                partida['CayalAmount'] = monto_cayal
                partida['uuid'] = uuid.uuid4()

                if self.documento.document_id > 0 and document_item_id == 0:
                    partida['ItemProductionStatusModified'] = 1
                    partida['CreatedBy'] = self._user_id

                    comentario = f'AGREGADO POR {self._user_name}'
                    self.agregar_partida_items_documento_extra(partida, 'agregar', comentario, partida['uuid'])

                # en caso que el modulo se use para capturar otro tipo de documentos que no sean pedidos el valor por defecto
                # debe ser 0 y para las subsecuentes modificaciones segun aplique
                # en funcion del diccionario modificaciones_pedido
                item_production_status_modified = partida.get('ItemProductionStatusModified', 0)
                partida['ItemProductionStatusModified'] = item_production_status_modified
                partida['CreatedBy'] = self._user_id

                cantidad_piezas = 0 if unidad_cayal == 0 else self.utilerias.redondear_valor_cantidad_a_decimal(partida['CayalPiece'])

                equivalencia = self.base_de_datos.fetchone(
                    'SELECT ISNULL(Equivalencia,0) Equivalencia FROM orgProduct WHERE ProductID = ?'
                    , partida.get('ProductID', 0))
                equivalencia = 0 if not equivalencia else equivalencia
                equivalencia_decimal = self.utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

                if equivalencia_decimal > 0 and unidad_cayal == 1:
                    cantidad_piezas = int((cantidad/equivalencia_decimal))

                partida['CayalPiece'] = cantidad_piezas
                cantidad = f"{cantidad:.3f}" if partida['ClaveUnidad'] == 'KGM' else f"{cantidad:.2f}"
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

                if int(partida['ProductID']) == 5606:
                    if self.servicio_a_domicilio_agregado:
                        return
                    else:
                        self.servicio_a_domicilio_agregado = True

                # agregar tipo de captura
                tabla_captura = self._ventanas.componentes_forma['tvw_productos']
                self._ventanas.insertar_fila_treeview(tabla_captura, partida_tabla, al_principio=True)

                self.agregar_partida_items_documento(partida)
                self.actualizar_totales_documento()

                # si aplica remueve el servicio a domicilio
                if self._module_id == 1687 and self.servicio_a_domicilio_agregado == True:
                    if self.documento.total - self.costo_servicio_a_domicilio >= 200:
                        self.remover_servicio_a_domicilio()

            finally:
                self._agregando_partida = False

    def asignar_folio(self, document_id):
        folio = self.base_de_datos.fetchone('SELECT Folio FROM docDocument WHERE DocumentID = ?', (document_id,))
        self.documento.folio = folio
        doc_folio =  f"{self.documento.prefix}{folio}"
        self.documento.doc_folio = doc_folio
        self._ventanas.insertar_input_componente('lbl_folio', doc_folio)

    def agregar_partida_items_documento(self, partida):

        self.documento.items.append(partida)

        if self._module_id != 1687: # si no es el modulo de pedidos inserta la partida
            if self.documento.document_id == 0:
                document_id = self.crear_cabecera_documento()
                self.documento.document_id = document_id

                self.asignar_folio(document_id)

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
                    self._module_id
                )
                self.base_de_datos.insertar_partida_documento_cayal(parametros)

        if self._module_id == 1692:

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
                    203 # salida de inventario
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
                    self._module_id
                )
                self.base_de_datos.insertar_partida_documento_cayal(parametros)

                self.documento.finish_document = 2 # bandera de cierre final del documento

    def crear_cabecera_documento(self, module_id = 0, prefix=None):

        module_id = self._module_id if module_id == 0 else module_id
        prefix = self.documento.prefix if not prefix else prefix

        document_id = self.base_de_datos.crear_documento(
                            self.documento.cfd_type_id,
                             prefix,
                            self.cliente.business_entity_id,
                            module_id,
                            self._user_id,
                            self.documento.depot_id,
                            self.documento.address_detail_id
        )
        return document_id

    def crear_cabecera_documento_relacionado(self):
        if self._module_id == 1692: # la compra por vales va relacionada a una salida de almacén
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

    def actualizar_totales_documento(self):

        impuestos_acumulado = 0
        ieps_acumulado = 0
        iva_acumulado = 0
        sub_total_acumulado = 0

        for producto in self.documento.items:
            ieps_acumulado += producto.get('ieps', 0)
            iva_acumulado += producto.get('iva', 0)
            impuestos_acumulado += producto.get('impuestos',0)
            sub_total_acumulado += producto.get('subtotal', 0)

        totales_documento = self._impuestos.doc_totales_por_documento(self.documento.items)
        self.documento.total = totales_documento['total_doc']


        total_documento_moneda = self.utilerias.convertir_decimal_a_moneda(self.documento.total)
        self._ventanas.insertar_input_componente('lbl_total', total_documento_moneda)

        self.documento.total_tax = impuestos_acumulado
        self.documento.subtotal = sub_total_acumulado
        self.documento.ieps = ieps_acumulado
        self.documento.iva = iva_acumulado

        self._ventanas.insertar_input_componente('lbl_articulos',
                                                 self._ventanas.numero_filas_treeview('tvw_productos'))

        if self.cliente.cayal_customer_type_id in (1,2) and self.cliente.credit_block == 0:
            debe = self.cliente.debt
            debe = self.utilerias.redondear_valor_cantidad_a_decimal(debe)

            debe += self.documento.total
            debe_moneda = self.utilerias.convertir_decimal_a_moneda(debe)
            self._ventanas.insertar_input_componente('lbl_debe', debe_moneda)

            disponible = self.cliente.remaining_credit
            disponible = self.utilerias.redondear_valor_cantidad_a_decimal(disponible)

            disponible = disponible - self.documento.total
            excedido = abs(disponible) if disponible < 0 else 0

            disponible = 0 if disponible <= 0 else disponible
            self.documento.credit_document_available = 0 if disponible == 0 else 1

            disponible_moneda = self.utilerias.convertir_decimal_a_moneda(disponible)
            self._ventanas.insertar_input_componente('lbl_restante', disponible_moneda)

            self.documento.credit_exceeded_amount = excedido

    def remover_servicio_a_domicilio(self):
        self.servicio_a_domicilio_agregado = False
        self.remover_partida_items_documento(5606)
        self.remover_product_id_tabla(5606)
        self.actualizar_totales_documento()

    def agregar_servicio_a_domicilio(self):

        def insertar_partida_servicio_a_domicilio():
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

        # servicio a domicilio solo aplica para pedidos
        if self._module_id != 1687:
            return

        # servicio a domicilio no aplica para anexos o cambios 2 y 3 solo para pedidos 1
        if self._module_id == 1687:
            parametros_pedido = self.documento.order_parameters
            order_type_id = int(parametros_pedido.get('OrderTypeID', 1))

            # anexos o cambios 2 y 3
            if order_type_id in (2,3):
                return

        # no se debe agregar mas de una partida de servicio a domicilio
        existe_servicio_a_domicilio = [producto for producto in self.documento.items
                                       if int(producto['ProductID']) == 5606]

        if existe_servicio_a_domicilio:
            return

        # insertamos el servicio a domicilio
        insertar_partida_servicio_a_domicilio()

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
