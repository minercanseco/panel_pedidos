import unittest

from panel.panel_pedidos_modelo import ModeloPanelPedidos


class BaseDeDatosPaquetes:
    def __init__(self, pendientes=None):
        self.pendientes = pendientes or []
        self.parametros_insertados = []

    def fetchall(self, consulta, parametros):
        if 'WITH PackageItems AS' in consulta:
            return [
                {'ParentDocumentItemID': 10, 'ProductID': 250},
                {'ParentDocumentItemID': 10, 'ProductID': 1429},
            ]
        if 'zvwBuscarPartidasPedidoCayal-DocumentID' in consulta:
            return [{
                'DocumentItemID': 10,
                'ProductID': 4431,
                'ProductTypeID': 3,
                'Quantity': 1,
                'UnitPrice': 540.8,
                'Subtotal': 540.8,
                'TipoCaptura': 1,
                'Comments': 'PAQUETE POZOLE',
            }]
        if 'TransactionComponentID AS DetailItemID' in consulta:
            return [
                {
                    'DetailItemID': 77,
                    'ParentDocumentItemID': 10,
                    'ProductID': 250,
                    'RequestedQuantity': 0.6,
                    'ProducedQuantity': 0.5,
                },
                {
                    'DetailItemID': 78,
                    'ParentDocumentItemID': 10,
                    'ProductID': 1429,
                    'RequestedQuantity': 2,
                    'ProducedQuantity': 2,
                },
            ]
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
            {'DocumentItemID': 10, 'ProductID': 250},
            {'DocumentItemID': 11, 'ProductID': 100, 'ProductName': 'NORMAL'},
        ]
        resultado = modelo.validar_paquetes_surtidos(169564, partidas)
        self.assertEqual([p['ProductID'] for p in resultado], [100, 4431])
        self.assertEqual(resultado[1]['UnitPrice'], 540.8)
        self.assertEqual(resultado[1]['Subtotal'], 540.8)
        self.assertNotIn('IsComponent', resultado[1])
        self.assertNotIn('OrderComponentTransactionID', resultado[1])

    def test_detalle_recupera_todos_los_ingredientes_del_paquete(self):
        modelo = self.crear_modelo()

        resultado = modelo.buscar_componentes_paquete_pedido(169564)

        self.assertEqual([fila['ProductID'] for fila in resultado], [250, 1429])
        self.assertEqual(resultado[0]['RequestedQuantity'], 0.6)
        self.assertEqual(resultado[0]['ProducedQuantity'], 0.5)

    def test_ticket_reemplaza_paquete_por_todos_sus_ingredientes(self):
        modelo = self.crear_modelo()
        partidas = [
            {'DocumentItemID': 10, 'ProductID': 4431},
            {'DocumentItemID': 11, 'ProductID': 100},
        ]

        resultado = modelo.desglosar_paquetes_para_ticket(169564, partidas)

        self.assertEqual([fila['ProductID'] for fila in resultado], [100, 250, 1429])

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
