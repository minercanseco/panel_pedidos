from datetime import datetime

from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.util import Utilerias


class ModeloPanelPedidos:
    def __init__(self, interfaz, parametros):
        self.parametros = parametros
        self.interfaz = interfaz
        self.base_de_datos = ComandosBaseDatos(self.parametros.cadena_conexion)
        self.utilerias = Utilerias()
        self.consulta_pedidos = []

        self.consulta_productos = []
        self.consulta_productos_ofertados = []
        self.consulta_productos_ofertados_btn = []
        self.products_ids_ofertados = []

        valores_puntualidad = self.obtener_valores_de_puntualidad()

        self.valor_a_tiempo = valores_puntualidad['ATiempo']
        self.valor_en_tiempo = valores_puntualidad['EnTiempo']

        self.hoy = datetime.now().date()
        self.hora_actual = self.utilerias.hora_actual()
        self.usuario_operador_panel = ''

        self.pedidos_en_tiempo = 0
        self.pedidos_a_tiempo = 0
        self.pedidos_retrasados = 0

    def buscar_pedidos(self, fecha_entrega):
        return self.base_de_datos.buscar_pedidos_panel_captura_cayal(fecha_entrega)

    def buscar_pedidos_sin_procesar(self):
        return self.base_de_datos.pedidos_sin_procesar('pedidos')

    def buscar_pedidos_cliente_sin_fecha(self, criteria):
        return self.base_de_datos.buscar_pedidos_cliente_sin_fecha_panel_pedidos(criteria)

    def obtener_valores_de_puntualidad(self):
        consulta = self.base_de_datos.obtener_valores_de_puntualidad_pedidos_cayal('timbrado')
        if not consulta:
            return
        return consulta[0]

    def buscar_nombre_usuario_operador_panel(self, user_id):
        return self.base_de_datos.buscar_nombre_de_usuario(user_id)

    def buscar_partidas_pedido(self, order_document_id):
        consulta = self.base_de_datos.buscar_partidas_pedidos_produccion_cayal(order_document_id= order_document_id,
                                                                                partidas_producidas=True,
                                                                                partidas_eliminadas=True)
        if not consulta:
            return
        return consulta

    def buscar_productos_ofertados_cliente(self):

        consulta_productos_ofertados = self.base_de_datos.buscar_productos_en_oferta()
        productos_ids = [reg['ProductID'] for reg in consulta_productos_ofertados]

        productos_ids = list(set(productos_ids))

        consulta_productos = self.buscar_info_productos_por_ids(productos_ids)
        consulta_procesada = self.agregar_impuestos_productos(consulta_productos)
        self.consulta_productos_ofertados = consulta_productos_ofertados
        self.consulta_productos = consulta_procesada
        self.consulta_productos_ofertados_btn = consulta_procesada
        self.products_ids_ofertados = productos_ids

        return consulta_procesada

    def buscar_productos(self, termino_buscado, tipo_busqueda):

        if termino_buscado != '' and termino_buscado:

            if tipo_busqueda == 'Término':
                return self.base_de_datos.buscar_product_id_termino(termino_buscado)

            if tipo_busqueda == 'Línea':
                return self.base_de_datos.buscar_product_id_linea(termino_buscado)

            return False

    def obtener_product_ids_consulta(self, consulta_productos):
        product_ids = [producto['ProductID'] for producto in consulta_productos]

        if len(product_ids) == 1:
            return product_ids[0]

        return product_ids

    def buscar_info_productos_por_ids(self, productos_ids, no_en_venta=None):

        if no_en_venta:
            return self.base_de_datos.buscar_info_productos(productos_ids,
                                                            no_en_venta=True)
        return self.base_de_datos.buscar_info_productos(productos_ids)

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