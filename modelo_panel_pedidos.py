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

        valores_puntualidad = self.obtener_valores_de_puntualidad()

        self.valor_a_tiempo = valores_puntualidad['ATiempo']
        self.valor_en_tiempo = valores_puntualidad['EnTiempo']

        self.hoy = datetime.now().date()
        self.hora_actual = self.utilerias.hora_actual()
        self.usuario_operador_panel = ''

        self.consulta_pedidos_entrega = []

        self.pedidos_en_tiempo = 0
        self.pedidos_a_tiempo = 0
        self.pedidos_retrasados = 0

    def buscar_pedidos(self, fecha_entrega):
        self.consulta_pedidos = self.base_de_datos.buscar_pedidos_panel_captura_cayal(fecha_entrega)
        return self.consulta_pedidos

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
