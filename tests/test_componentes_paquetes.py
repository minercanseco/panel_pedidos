import unittest

from panel.panel_pedidos_modelo import ModeloPanelPedidos


class BaseDeDatosPaquetes:
    def __init__(self, pendientes=None):
        self.pendientes = pendientes or []
        self.parametros_insertados = []

    def fetchall(self, consulta, parametros):
        if 'INNER JOIN dbo.orgProduct P' in consulta and 'ProductTypeID = 3' in consulta:
            return [{'DocumentItemID': 10}]
        if 'SuppliedQuantity IS NULL' in consulta:
            return self.pendientes
        if 'SuppliedQuantity > 0' in consulta:
            return [{'DocumentItemID': 10}]
        return []

    def insertar_partida_documento_cayal(self, parametros):
        self.parametros_insertados.append(parametros)


class ComponentesPaquetesTest(unittest.TestCase):
    def crear_modelo(self, pendientes=None):
        modelo = object.__new__(ModeloPanelPedidos)
        modelo.base_de_datos = BaseDeDatosPaquetes(pendientes)
        return modelo

    def test_conserva_paquete_en_documento_despues_de_validar_surtido(self):
        modelo = self.crear_modelo()
        partidas = [
            {'DocumentItemID': 10, 'ProductID': 4431},
            {'DocumentItemID': 11, 'ProductID': 100, 'ProductName': 'NORMAL'},
        ]
        resultado = modelo.validar_paquetes_surtidos(169564, partidas)
        self.assertEqual([p['ProductID'] for p in resultado], [4431, 100])
        self.assertNotIn('IsComponent', resultado[0])
        self.assertNotIn('OrderComponentTransactionID', resultado[0])

    def test_rechaza_paquete_con_componentes_pendientes(self):
        modelo = self.crear_modelo([{'DocumentItemID': 10}])
        with self.assertRaisesRegex(ValueError, 'pendientes de surtir'):
            modelo.validar_paquetes_surtidos(169564, [{'DocumentItemID': 10}])

    def test_insercion_conserva_campos_de_trazabilidad(self):
        modelo = self.crear_modelo()
        partida = {
            'ProductID': 4431, 'Quantity': 1, 'UnitPrice': 540.8,
            'Subtotal': 540.8, 'TipoCaptura': 1, 'Comments': 'PAQUETE',
        }
        modelo.insertar_partidas_documento(169564, 900, [partida], 200, 1)
        parametros = modelo.base_de_datos.parametros_insertados[0]
        self.assertEqual(parametros[-2:], (0, None))


if __name__ == '__main__':
    unittest.main()
