from cayal.ventanas import Ventanas



class AsociarPedidoWeb:
    def __init__(self, master, base_de_datos, utilerias, info_pedido):
        self._master = master
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._ventanas = Ventanas(self._master)

        self._info_pedido = info_pedido
        self._ventanas.configurar_ventana_ttkbootstrap()