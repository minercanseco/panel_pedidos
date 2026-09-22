import unittest
from types import SimpleNamespace

from herramientas.herramientas_panel.editar_nombre_pedido import EditarNombrePedido


class BaseDeDatosFalsa:
    def __init__(self):
        self.comandos = []

    def fetchone(self, consulta, parametros):
        return 25

    def command(self, consulta, parametros):
        self.comandos.append((consulta, parametros))


class EditarNombrePedidoTest(unittest.TestCase):
    def test_actualiza_la_sucursal_seleccionada_en_el_pedido(self):
        editor = object.__new__(EditarNombrePedido)
        editor._instancia_llamada = False
        editor._documento_seleccionado = lambda: True
        editor._validar_restriccion_por_cliente = lambda: True
        editor._base_de_datos = BaseDeDatosFalsa()
        editor._cliente = SimpleNamespace(business_entity_id=101, zone_id=7)
        editor._documento = SimpleNamespace(
            address_detail_id=202,
            depot_id=303,
            cfd_type_id=1,
            address_name='Sucursal Centro',
        )
        editor._valores_fila = {
            'OrderDocumentID': 404,
            'DocumentTypeID': 1,
        }
        editor._ventanas = SimpleNamespace(
            obtener_input_componente=lambda nombre: {
                'tbx_nombre_actual': 'Cliente anterior',
                'tbx_direccion_actual': 'Sucursal Centro',
            }[nombre]
        )
        editor._modelo = SimpleNamespace(
            user_name='Usuario',
            afectar_bitacora=lambda *args, **kwargs: None,
        )
        editor._user_id = 9
        editor._master = SimpleNamespace(destroy=lambda: None)

        editor._llamar_instancia()

        consulta, parametros = editor._base_de_datos.comandos[0]
        self.assertIn('DepotID = ?', consulta)
        self.assertEqual(parametros, (101, 202, 303, 7, 1, 25, 404))


if __name__ == '__main__':
    unittest.main()
