import unittest
from decimal import Decimal
from types import SimpleNamespace

from cayal.util import Utilerias
from herramientas.capturar_documento.llamar_instancia_captura_pedido import LlamarInstanciaCapturaPedido
from panel.panel_pedidos_modelo import ModeloPanelPedidos


class BaseDeDatosFalsa:
    def __init__(self, status=4, direccion=True):
        self.status = status
        self.direccion = direccion

    def fetchone(self, sql, parametros):
        return 8 if self.direccion else None

    def fetchall(self, sql, parametros):
        if 'docDocumentOrderCayal' in sql:
            return [{
                'StatusID': self.status,
                'OrderTypeID': 1,
                'BusinessEntityID': 7,
                'AddressDetailID': 8,
                'DocumentTypeID': 1,
                'CommentsOrder': 'Entregar completo',
            }]
        return [
            {'ProductID': 11, 'Quantity': 3, 'ItemProductionStatusModified': 4},
            {'ProductID': 5606, 'Quantity': 1, 'ItemProductionStatusModified': 0},
            {'ProductID': 12, 'Quantity': 2, 'ItemProductionStatusModified': 3},
        ]


class CopiarPedidoTest(unittest.TestCase):
    def test_ultimo_producto_no_se_marca_omitido_si_reemplaza_el_envio(self):
        captura = object.__new__(LlamarInstanciaCapturaPedido)
        captura._partidas_iniciales = [
            {'ProductID': 11, 'Quantity': 1.0},
            {'ProductID': 12, 'Quantity': 1.0},
        ]
        captura._documento = SimpleNamespace(document_id=0, items=[])
        captura._utilerias = Utilerias()
        mensajes = []
        captura._interfaz_captura = SimpleNamespace(
            ventanas=SimpleNamespace(mostrar_mensaje=mensajes.append)
        )
        captura._modelo_captura = SimpleNamespace(
            buscar_info_productos_por_ids=lambda product_id: [{
                'ProductID': product_id,
                'ProductName': 'Producto',
                'ProductKey': f'P{product_id}',
                'SalePrice': Decimal('120'),
                'Equivalencia': Decimal('1'),
                'TaxTypeID': 10,
                'ClaveUnidad': 'KGM',
            }]
        )

        def agregar(partida, **kwargs):
            if partida['ProductID'] == 12:
                captura._documento.items = [
                    item for item in captura._documento.items
                    if item['ProductID'] != 5606
                ]
            captura._documento.items.append(partida)
            if partida['ProductID'] == 11:
                captura._documento.items.append({'ProductID': 5606})

        captura._controlador_captura = SimpleNamespace(_agregar_partida_tabla=agregar)

        omitidas = captura._precargar_partidas()

        self.assertEqual(omitidas, [])
        self.assertEqual(mensajes, [])
        self.assertEqual([p['ProductID'] for p in captura._documento.items], [11, 12])

    def test_producto_no_vigente_no_impide_abrir_ni_copiar_los_demas(self):
        captura = object.__new__(LlamarInstanciaCapturaPedido)
        captura._partidas_iniciales = [
            {'ProductID': 99, 'ProductName': 'Anterior', 'Quantity': 1.0},
            {'ProductID': 11, 'ProductName': 'Vigente', 'Quantity': 2.0},
        ]
        captura._documento = SimpleNamespace(document_id=0, items=[])
        captura._utilerias = Utilerias()
        mensajes = []
        captura._interfaz_captura = SimpleNamespace(
            ventanas=SimpleNamespace(mostrar_mensaje=mensajes.append)
        )
        captura._modelo_captura = SimpleNamespace(
            buscar_info_productos_por_ids=lambda product_id: [] if product_id == 99 else [{
                'ProductID': product_id,
                'ProductName': 'Vigente',
                'ProductKey': 'P11',
                'SalePrice': Decimal('10'),
                'Equivalencia': Decimal('2'),
                'TaxTypeID': 10,
                'ClaveUnidad': 'KGM',
            }]
        )
        captura._controlador_captura = SimpleNamespace(
            _agregar_partida_tabla=lambda partida, **kwargs:
                captura._documento.items.append(partida)
        )

        omitidas = captura._precargar_partidas()

        self.assertEqual([p['ProductID'] for p in captura._documento.items], [11])
        self.assertEqual(len(omitidas), 1)
        self.assertIn('Anterior (ID 99)', mensajes[0])

    def test_precarga_convierte_cantidad_float_a_decimal(self):
        captura = object.__new__(LlamarInstanciaCapturaPedido)
        captura._partidas_iniciales = [{'ProductID': 11, 'Quantity': 3.0}]
        captura._documento = SimpleNamespace(document_id=0, items=[])
        captura._utilerias = Utilerias()
        captura._modelo_captura = SimpleNamespace(
            buscar_info_productos_por_ids=lambda product_id: [{
                'ProductID': product_id,
                'ProductName': 'Producto',
                'ProductKey': 'P11',
                'SalePrice': Decimal('10'),
                'Equivalencia': Decimal('2'),
                'TaxTypeID': 10,
                'ClaveUnidad': 'KGM',
            }]
        )
        captura._controlador_captura = SimpleNamespace(
            _agregar_partida_tabla=lambda partida, **kwargs:
                captura._documento.items.append(partida)
        )

        captura._precargar_partidas()

        partida = captura._documento.items[0]
        self.assertEqual(partida['cantidad_piezas'], Decimal('1.5'))

    def test_conserva_cantidad_solicitada_y_recalcula_envio(self):
        modelo = object.__new__(ModeloPanelPedidos)
        modelo.base_de_datos = BaseDeDatosFalsa()

        origen, partidas = modelo.preparar_copia_pedido(42)

        self.assertEqual(origen['BusinessEntityID'], 7)
        self.assertEqual([(p['ProductID'], p['Quantity']) for p in partidas], [(11, 3)])

    def test_rechaza_pedido_abierto(self):
        modelo = object.__new__(ModeloPanelPedidos)
        modelo.base_de_datos = BaseDeDatosFalsa(status=1)

        with self.assertRaisesRegex(ValueError, 'no esté abierto'):
            modelo.preparar_copia_pedido(42)


if __name__ == '__main__':
    unittest.main()
