import unittest

from herramientas.herramientas_panel.ticket_pedido_cliente import (
    TicketPedidoCliente,
)


class TicketPedidoClienteTest(unittest.TestCase):
    def setUp(self):
        self.partidas = [
            {'ProductID': 100, 'ProductName': 'Producto'},
            {'ProductID': 5606, 'ProductName': 'Servicio a domicilio'},
        ]

    def test_entrega_a_domicilio_conserva_servicio(self):
        resultado = TicketPedidoCliente._filtrar_partidas_por_tipo_entrega(
            self.partidas,
            1,
        )

        self.assertEqual([100, 5606], [p['ProductID'] for p in resultado])

    def test_cliente_viene_excluye_servicio(self):
        resultado = TicketPedidoCliente._filtrar_partidas_por_tipo_entrega(
            self.partidas,
            2,
        )

        self.assertEqual([100], [p['ProductID'] for p in resultado])

    def test_tipo_entrega_invalido_no_genera_total_ambiguo(self):
        with self.assertRaisesRegex(ValueError, 'forma de entrega válida'):
            TicketPedidoCliente._filtrar_partidas_por_tipo_entrega(
                self.partidas,
                None,
            )


if __name__ == '__main__':
    unittest.main()
