import unittest

from panel.panel_pedidos_modelo import ModeloPanelPedidos


class BaseDeDatosPrueba:
    def __init__(self, resultado):
        self.resultado = resultado
        self.consulta = None
        self.parametros = None

    def fetchone(self, consulta, parametros):
        self.consulta = consulta
        self.parametros = parametros
        return self.resultado


class UsuarioTicketProduccionTest(unittest.TestCase):
    def crear_modelo(self, resultado):
        modelo = object.__new__(ModeloPanelPedidos)
        modelo.base_de_datos = BaseDeDatosPrueba(resultado)
        return modelo

    def test_obtiene_autor_de_la_ultima_modificacion(self):
        modelo = self.crear_modelo('MODIFICADOR')

        usuario = modelo.obtener_ultimo_usuario_modificacion(123)

        self.assertEqual(usuario, 'MODIFICADOR')
        self.assertEqual(modelo.base_de_datos.parametros[0], 123)
        self.assertIn('LO.ChangeTypeID IN', modelo.base_de_datos.consulta)
        self.assertIn('ORDER BY LO.CreatedOn DESC', modelo.base_de_datos.consulta)
        self.assertIn(15, modelo.base_de_datos.parametros)
        self.assertIn(59, modelo.base_de_datos.parametros)

    def test_sin_modificaciones_devuelve_valor_vacio(self):
        modelo = self.crear_modelo(None)

        self.assertIsNone(modelo.obtener_ultimo_usuario_modificacion(123))


if __name__ == '__main__':
    unittest.main()
