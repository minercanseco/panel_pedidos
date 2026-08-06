from cayal.util import Utilerias
from cayal.comandos_base_datos import ComandosBaseDatos


class ModeloVerificador:
    EQUIVALENCIA_UNIDADES = {
        'PIEZA': 'Pz',
        'KILO': 'Kg',
        'LITRO': 'Lt',
        'PAQUETE': 'Pq'
    }

    PRODUCTOS_ESPECIALES = {
        1162: {
            'unidad': 'Pz',
            'factor': 15
        },
        1165: {
            'unidad': 'Cj',
            'factor': 360
        },
        1166: {
            'unidad': 'Rj',
            'factor': 30
        }
    }

    def __init__(
            self,
            parametros=None,
            base_de_datos=None,
            utilerias=None
    ):
        self.parametros = parametros
        self.base_de_datos = (
            base_de_datos
            if base_de_datos is not None
            else ComandosBaseDatos()
        )
        self.utilerias = (
            utilerias
            if utilerias is not None
            else Utilerias()
        )

        self._productos = []
        self._listas_precios = []
        self._productos_ofertados = []
        self._productos_ofertados_ids = set()
        self._productos_ofertados_nombres = set()

        self._ultimo_termino = None
        self._ultima_busqueda_por_linea = None

        self.cargar_datos_iniciales()

    # ------------------------------------------------------------------
    # Inicialización
    # ------------------------------------------------------------------

    def cargar_datos_iniciales(self):
        self.cargar_listas_precios()
        self.cargar_productos_ofertados()

    def cargar_listas_precios(self):
        self._listas_precios = self.base_de_datos.fetchall(
            """
            SELECT
                CustomerTypeID,
                CustomerTypeName
            FROM orgCustomerType
            WHERE CustomerTypeID BETWEEN 2 AND 10
            ORDER BY CustomerTypeID
            """,
            ()
        )

        return list(self._listas_precios)

    def cargar_productos_ofertados(self):
        consulta = self.base_de_datos.buscar_productos_en_oferta()
        self._productos_ofertados = list(consulta or [])

        self._productos_ofertados_ids = {
            int(producto['ProductID'])
            for producto in self._productos_ofertados
            if producto.get('ProductID') is not None
        }

        self._productos_ofertados_nombres = {
            producto['ProductName']
            for producto in self._productos_ofertados
            if producto.get('ProductName')
        }

        return list(self._productos_ofertados)

    # ------------------------------------------------------------------
    # Propiedades de consulta
    # ------------------------------------------------------------------

    @property
    def productos(self):
        return list(self._productos)

    @property
    def listas_precios(self):
        return list(self._listas_precios)

    @property
    def productos_ofertados(self):
        return list(self._productos_ofertados)

    @property
    def nombres_productos_ofertados(self):
        return sorted(self._productos_ofertados_nombres)

    @property
    def nombres_productos(self):
        return [
            producto['ProductName']
            for producto in self._productos
            if producto.get('ProductName')
        ]

    @property
    def nombres_listas_precios(self):
        return [
            lista['CustomerTypeName']
            for lista in self._listas_precios
            if lista.get('CustomerTypeName')
        ]

    # ------------------------------------------------------------------
    # Validaciones
    # ------------------------------------------------------------------

    @staticmethod
    def validar_termino_busqueda(termino):
        if termino is None:
            return False, 'Debe introducir un término a buscar.'

        termino = str(termino).strip()

        if not termino:
            return False, 'Debe introducir un término a buscar.'

        if len(termino) < 4:
            return False, 'Debe abundar en el término a buscar.'

        return True, ''

    def validar_cantidad(self, cantidad):
        if cantidad is None or cantidad == '':
            return False, None, 'Debe introducir un valor.'

        if not self.utilerias.es_cantidad(cantidad):
            return (
                False,
                None,
                'Debe introducir una cantidad válida.'
            )

        cantidad = (
            self.utilerias.redondear_valor_cantidad_a_decimal(
                cantidad
            )
        )

        if cantidad <= 0:
            return (
                False,
                None,
                'Debe introducir un valor mayor a cero.'
            )

        return True, cantidad, ''

    # ------------------------------------------------------------------
    # Búsqueda de productos
    # ------------------------------------------------------------------

    def es_busqueda_repetida(self, termino, buscar_linea):
        termino = str(termino).strip()
        buscar_linea = int(buscar_linea or 0)

        return (
            termino == self._ultimo_termino
            and buscar_linea == self._ultima_busqueda_por_linea
        )

    def buscar_productos(self, termino, buscar_linea=False):
        termino = str(termino).strip()
        buscar_linea = int(buscar_linea or 0)

        if self.es_busqueda_repetida(termino, buscar_linea):
            return list(self._productos)

        self._ultimo_termino = termino
        self._ultima_busqueda_por_linea = buscar_linea

        if buscar_linea:
            coincidencias = (
                self.base_de_datos.buscar_product_id_linea(
                    termino
                )
            )
        else:
            coincidencias = (
                self.base_de_datos.buscar_product_id_termino(
                    termino
                )
            )

        if not coincidencias:
            self._productos = []
            return []

        product_ids = self._extraer_product_ids(coincidencias)

        if not product_ids:
            self._productos = []
            return []

        consulta = self.base_de_datos.buscar_info_productos(
            product_ids
        )

        self._productos = list(consulta or [])
        return list(self._productos)

    def cargar_informacion_productos(self, product_ids):
        product_ids = list({
            int(product_id)
            for product_id in product_ids
            if product_id is not None
        })

        if not product_ids:
            self._productos = []
            return []

        consulta = self.base_de_datos.buscar_info_productos(
            product_ids
        )

        self._productos = list(consulta or [])
        return list(self._productos)

    def cargar_productos_en_oferta(self):
        return self.cargar_informacion_productos(
            self._productos_ofertados_ids
        )

    @staticmethod
    def _extraer_product_ids(registros):
        product_ids = []

        for registro in registros:
            product_id = registro.get('ProductID')

            if product_id is None:
                continue

            product_ids.append(int(product_id))

        return list(set(product_ids))

    # ------------------------------------------------------------------
    # Obtención de registros
    # ------------------------------------------------------------------

    def obtener_producto_por_nombre(self, nombre_producto):
        for producto in self._productos:
            if producto.get('ProductName') == nombre_producto:
                return producto

        return None

    def obtener_producto_por_id(self, product_id):
        product_id = int(product_id)

        for producto in self._productos:
            if int(producto.get('ProductID', 0)) == product_id:
                return producto

        return None

    def obtener_product_id(self, nombre_producto):
        producto = self.obtener_producto_por_nombre(
            nombre_producto
        )

        if producto is None:
            return None

        return int(producto['ProductID'])

    def obtener_customer_type_id(self, nombre_lista):
        for lista in self._listas_precios:
            if lista.get('CustomerTypeName') == nombre_lista:
                return int(lista['CustomerTypeID'])

        return None

    # ------------------------------------------------------------------
    # Precios y ofertas
    # ------------------------------------------------------------------

    def obtener_precio_producto(
            self,
            product_id,
            customer_type_id
    ):
        product_id = int(product_id)
        customer_type_id = int(customer_type_id)

        oferta = self._buscar_oferta(
            product_id,
            customer_type_id
        )

        if oferta is not None:
            return self._crear_datos_oferta(oferta)

        precio = self._buscar_precio_lista(
            product_id,
            customer_type_id
        )

        if precio is None:
            raise ValueError(
                'No se encontró un precio para el producto '
                'en la lista seleccionada.'
            )

        return {
            'ofertado': False,
            'precio': precio
        }

    def _buscar_oferta(self, product_id, customer_type_id):
        for producto in self._productos_ofertados:
            if (
                    int(producto.get('ProductID', 0))
                    == int(product_id)
                    and int(producto.get('Lista', 0))
                    == int(customer_type_id)
            ):
                return producto

        return None

    def _buscar_precio_lista(
            self,
            product_id,
            customer_type_id
    ):
        consulta = self.base_de_datos.buscar_precios_producto(
            product_id
        )

        for precio in consulta or []:
            if (
                    int(precio.get('CustomerTypeID', 0))
                    == int(customer_type_id)
            ):
                return precio.get('SalePrice')

        return None

    @staticmethod
    def _crear_datos_oferta(oferta):
        fecha_inicio = oferta.get('FechaAlta')
        fecha_termino = oferta.get('FechaBaja')

        return {
            'ofertado': True,
            'precio_previo': oferta.get('SalePriceBefore', 0),
            'precio_oferta': oferta.get('SalePrice', 0),
            'vigencia_inicio': (
                str(fecha_inicio)[:10]
                if fecha_inicio is not None
                else ''
            ),
            'vigencia_termino': (
                str(fecha_termino)[:10]
                if fecha_termino is not None
                else ''
            ),
            'tipo_oferta': oferta.get('Tipo', '')
        }

    def producto_esta_ofertado(self, nombre_producto):
        return nombre_producto in self._productos_ofertados_nombres

    # ------------------------------------------------------------------
    # Consolidación del producto
    # ------------------------------------------------------------------

    def obtener_informacion_producto(
            self,
            product_id,
            customer_type_id
    ):
        producto = self.obtener_producto_por_id(product_id)

        if producto is None:
            raise ValueError(
                'No se encontró el producto seleccionado.'
            )

        precios = self.obtener_precio_producto(
            product_id,
            customer_type_id
        )

        return self._consolidar_producto(
            producto,
            precios
        )

    def _consolidar_producto(self, producto, precios):
        informacion = dict(producto)

        cantidad = 1
        tax_type_id = informacion.get('TaxTypeID')
        clave_sat = informacion.get('ClaveProdServ')
        clave_unidad = informacion.get('ClaveUnidad')
        ofertado = bool(precios.get('ofertado'))

        informacion['ofertado'] = ofertado
        informacion['existencia'] = (
            self._calcular_existencia(informacion)
        )

        if ofertado:
            totales = self._calcular_totales(
                precios.get('precio_previo', 0),
                cantidad,
                tax_type_id,
                clave_unidad,
                clave_sat
            )

            totales_oferta = self._calcular_totales(
                precios.get('precio_oferta', 0),
                cantidad,
                tax_type_id,
                clave_unidad,
                clave_sat
            )

            informacion.update({
                'total': totales['total'],
                'total_oferta': totales_oferta['total'],
                'vigencia_inicio': precios.get(
                    'vigencia_inicio',
                    ''
                ),
                'vigencia_termino': precios.get(
                    'vigencia_termino',
                    ''
                ),
                'tipo_oferta': precios.get(
                    'tipo_oferta',
                    ''
                )
            })

            return informacion

        totales = self._calcular_totales(
            precios.get('precio', 0),
            cantidad,
            tax_type_id,
            clave_unidad,
            clave_sat
        )

        informacion['total'] = totales['total']
        return informacion

    def _calcular_totales(
            self,
            precio,
            cantidad,
            tax_type_id,
            clave_unidad,
            clave_sat
    ):
        return self.utilerias.calcular_totales_partida(
            precio,
            cantidad,
            tax_type_id,
            clave_unidad,
            clave_sat
        )

    # ------------------------------------------------------------------
    # Existencias y unidades especiales
    # ------------------------------------------------------------------

    def _calcular_existencia(self, producto):
        product_id = int(producto.get('ProductID', 0))

        cantidad_presente = producto.get('QtyPresent', 0) or 0
        cantidad_ajustes = producto.get(
            'CantidadAjustes',
            0
        ) or 0

        existencia = cantidad_presente - cantidad_ajustes

        existencia = (
            self.utilerias.redondear_valor_cantidad_a_decimal(
                existencia
            )
        )

        configuracion_especial = (
            self.PRODUCTOS_ESPECIALES.get(product_id)
        )

        if configuracion_especial is not None:
            existencia /= configuracion_especial['factor']

            existencia = (
                self.utilerias
                .redondear_valor_cantidad_a_decimal(
                    existencia
                )
            )

            return {
                'cantidad': existencia,
                'unidad': configuracion_especial['unidad']
            }

        unidad_producto = str(
            producto.get('Unit', '')
        ).upper()

        unidad = self.EQUIVALENCIA_UNIDADES.get(
            unidad_producto,
            producto.get('Unit', '')
        )

        return {
            'cantidad': existencia,
            'unidad': unidad
        }

    def ajustar_precio_presentacion(
            self,
            product_id,
            precio
    ):
        product_id = int(product_id)

        configuracion_especial = (
            self.PRODUCTOS_ESPECIALES.get(product_id)
        )

        precio = (
            self.utilerias.redondear_valor_cantidad_a_decimal(
                precio
            )
        )

        if configuracion_especial is not None:
            precio *= configuracion_especial['factor']

        return (
            self.utilerias.redondear_valor_cantidad_a_decimal(
                precio
            )
        )

    # ------------------------------------------------------------------
    # Cálculo por cantidad o monto
    # ------------------------------------------------------------------

    def calcular_importes(
            self,
            product_id,
            customer_type_id,
            cantidad,
            calcular_por_monto=False
    ):
        informacion = self.obtener_informacion_producto(
            product_id,
            customer_type_id
        )

        resultado = {
            'ofertado': informacion['ofertado'],
            'regular': self._calcular_detalle_importe(
                precio=informacion['total'],
                valor=cantidad,
                calcular_por_monto=calcular_por_monto
            )
        }

        if informacion['ofertado']:
            resultado['oferta'] = (
                self._calcular_detalle_importe(
                    precio=informacion['total_oferta'],
                    valor=cantidad,
                    calcular_por_monto=calcular_por_monto
                )
            )

        return resultado

    def _calcular_detalle_importe(
            self,
            precio,
            valor,
            calcular_por_monto
    ):
        precio = (
            self.utilerias.redondear_valor_cantidad_a_decimal(
                precio
            )
        )

        valor = (
            self.utilerias.redondear_valor_cantidad_a_decimal(
                valor
            )
        )

        if calcular_por_monto:
            total = valor
            cantidad = total / precio if precio else 0
        else:
            cantidad = valor
            total = precio * cantidad

        cantidad = (
            self.utilerias.redondear_valor_cantidad_a_decimal(
                cantidad
            )
        )

        return {
            'precio': precio,
            'cantidad': cantidad,
            'total': total
        }

    def obtener_producto_mapa_carnico(
            self,
            product_id: int
    ):
        """
        Devuelve el producto junto con las zonas anatómicas
        que deben pintarse.

        Retorna:

        {
            "producto": {...},
            "zonas": [...]
        }
        """

        consulta = self.base_de_datos.fetchall(
            """
            SELECT
                P.ProductID,
                P.ProductName AS Producto,
                Z.Category1,
                Z.ZoneID,
                Z.ZoneName,
                Z.Coordinates
            FROM dbo.MapeoProductosCarnicosImagenCayal MP
            INNER JOIN dbo.MapeoZonasCarnicosImagenCayal Z
                ON MP.ZoneID = Z.ZoneID
            INNER JOIN dbo.orgProduct P
                ON MP.ProductID = P.ProductID
            WHERE MP.ProductID = ?
            ORDER BY
                Z.ZoneName
            """,
            (
                int(product_id),
            )
        )

        if not consulta:
            return None

        producto = {
            "ProductID": consulta[0]["ProductID"],
            "Producto": consulta[0]["Producto"],
            "Category1": consulta[0]["Category1"],
        }

        zonas = []

        for fila in consulta:
            zonas.append({
                "ZoneID": fila["ZoneID"],
                "ZoneName": fila["ZoneName"],
                "Category1": fila["Category1"],
                "Coordinates": fila["Coordinates"],
            })

        return {
            "producto": producto,
            "zonas": zonas,
        }
    # ------------------------------------------------------------------
    # Formatos de presentación
    # ------------------------------------------------------------------

    def formatear_moneda(self, valor):
        valor = (
            self.utilerias.redondear_valor_cantidad_a_decimal(
                valor
            )
        )

        return self.utilerias.convertir_decimal_a_moneda(valor)

    @staticmethod
    def formatear_cantidad(cantidad):
        try:
            if cantidad == int(cantidad):
                return int(cantidad)
        except (TypeError, ValueError):
            pass

        return cantidad

    def formatear_detalle_importe(self, detalle):
        precio = self.formatear_moneda(detalle['precio'])
        total = self.formatear_moneda(detalle['total'])
        cantidad = self.formatear_cantidad(
            detalle['cantidad']
        )

        return '{0} x {1} = {2}'.format(
            precio,
            cantidad,
            total
        )

    def formatear_precio_producto(
            self,
            product_id,
            precio
    ):
        precio = self.ajustar_precio_presentacion(
            product_id,
            precio
        )

        return self.formatear_moneda(precio)

    # ------------------------------------------------------------------
    # Información adicional
    # ------------------------------------------------------------------

    def buscar_informacion_usos_producto(self, product_id):
        consulta = (
            self.base_de_datos
            .buscar_informacion_usos_producto(product_id)
        )

        return list(consulta or [])