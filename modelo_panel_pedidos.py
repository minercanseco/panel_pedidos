from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.util import Utilerias


class ModeloPanelPedidos:
    def __init__(self, interfaz, parametros):
        self.parametros = parametros
        self.interfaz = interfaz
        self.base_de_datos = ComandosBaseDatos(self.parametros.cadena_conexion)
        self.utilerias = Utilerias()
        self.consulta_pedidos = []

    def buscar_pedidos(self):
        fecha_entrega = self.interfaz.ventanas.obtener_input_componente('den_fecha')
        self.consulta_pedidos = self.base_de_datos.buscar_pedidos_panel_captura_cayal(fecha_entrega)
        return self.consulta_pedidos