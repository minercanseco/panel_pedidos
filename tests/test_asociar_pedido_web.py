import unittest
from unittest.mock import MagicMock

from herramientas.herramientas_panel.asociar_pedido_web import AsociarPedidoWeb


class AsociarPedidoWebTests(unittest.TestCase):
    def setUp(self):
        self.ventana = AsociarPedidoWeb.__new__(AsociarPedidoWeb)
        self.ventana._base_de_datos = MagicMock()
        self.ventana._info_pedido = {'OrderDocumentID': 77}

    def test_obtiene_usuario_por_relacion_del_pedido(self):
        esperado = {
            'UserClientID': 12,
            'UUID': 'pedido-uuid',
            'AddressDetailID': 1,
            'FiscalZipCode': '24020',
        }
        self.ventana._base_de_datos.fetchall.return_value = [esperado]

        resultado = self.ventana._obtener_info_usuario()

        self.assertEqual(resultado, esperado)
        sql, parametros = self.ventana._base_de_datos.fetchall.call_args.args
        self.assertIn('C.UserClientID = D.UserClientID', sql)
        self.assertIn('C.FirstOrderUUID = D.UUID', sql)
        self.assertIn('CROSS APPLY', sql)
        self.assertIn('U.FiscalZipCode', sql)
        self.assertEqual(parametros, (77,))

    def test_direccion_cedis_se_busca_por_address_detail_id(self):
        self.ventana._base_de_datos.buscar_detalle_de_direccion.return_value = [
            {'AddressDetailID': 1, 'Street': 'AV. GUSTAVO DIAZ ORDAZ'}
        ]

        resultado = self.ventana._obtener_info_direccion({
            'AddressDetailID': 1,
            'UUID': 'pedido-uuid',
        })

        self.assertEqual(resultado['AddressDetailID'], 1)
        self.ventana._base_de_datos.buscar_detalle_de_direccion.assert_called_once_with(
            address_detail_id=1,
            uuid=None,
        )

    def test_asociacion_se_limita_a_pedido_y_usuario(self):
        self.ventana._info_pedido = {
            'OrderDocumentID': 77,
            'UserClientID': 12,
            'UUID': 'pedido-uuid',
        }
        self.ventana._base_de_datos.fetchall.return_value = [{
            'CustomerTypeID': 2,
            'CayalCustomerTypeID': 1,
        }]

        self.ventana._asociar_informacion_y_pedido_cliente_existente(900)

        sql, parametros = self.ventana._base_de_datos.command.call_args.args
        self.assertIn('OrderDocumentID = @OrderDocumentID', sql)
        self.assertIn('UserClientID = @UserClientID', sql)
        self.assertIn('UserClientID IS NULL OR UserClientID = 0', sql)
        self.assertEqual(parametros, (900, 77, 12, 'pedido-uuid', 0, 2))


if __name__ == '__main__':
    unittest.main()
