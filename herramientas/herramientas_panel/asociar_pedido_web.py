from cayal.ventanas import Ventanas



class AsociarPedidoWeb:
    def __init__(self, master, base_de_datos, utilerias, info_pedido):
        self._master = master
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._ventanas = Ventanas(self._master)

        self._info_pedido = info_pedido
        self._crear_componentes()

        self._ventanas.configurar_ventana_ttkbootstrap()


    def _crear_componentes(self):
        componentes = [
            ('cbx_accion', 'Acción:'),
            ('tbv_historial', self._crear_columnas_tabla()),
        ]

        self._ventanas.crear_formulario_simple(componentes)

    def _crear_columnas_tabla(self):
        return [
            {"text": "BusinessEntityID", "stretch": False, "width": 0},
            {"text": "Cliente", "stretch": False, "width": 350},
            {"text": "Teléfono", "stretch": False, "width": 120},
            {"text": 'Correo', "stretch": False, "width": 170},
        ]