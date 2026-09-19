import unittest

from panel.panel_pedidos_modelo import ModeloPanelPedidos


class BaseDeDatosFalsa:
    def __init__(self):
        self.comandos = []
        self.bitacora = []

    def command(self, sql, parametros):
        self.comandos.append((sql, parametros))

    def insertar_registro_bitacora_pedidos(self, **parametros):
        self.bitacora.append(parametros)


class MandarPedidoAProducirTest(unittest.TestCase):
    def test_marca_si_existe_producto_congelado_vigente(self):
        modelo = object.__new__(ModeloPanelPedidos)
        modelo.base_de_datos = BaseDeDatosFalsa()
        modelo.user_id = 7
        modelo.user_name = 'USUARIO'

        modelo.mandar_pedido_a_producir(125)

        sql, parametros = modelo.base_de_datos.comandos[0]
        self.assertIn('WithFrozenProducts = CASE', sql)
        self.assertIn('ISNULL(P.FrozenProduct, 0) = 1', sql)
        self.assertIn('I.DeletedOn IS NULL', sql)
        self.assertEqual(parametros, (125, 125, 7, 125, 125))


if __name__ == '__main__':
    unittest.main()
