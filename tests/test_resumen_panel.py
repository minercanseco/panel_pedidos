import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock

from cayal.util import Utilerias
from panel.panel_pedidos_controlador import ControladorPanelPedidos
from panel.panel_pedidos_modelo import ModeloPanelPedidos


class ResumenPanelTest(unittest.TestCase):
    def setUp(self):
        self.modelo = object.__new__(ModeloPanelPedidos)
        self.modelo.utilerias = Utilerias()
        self.modelo.valor_en_tiempo = 30
        self.modelo.valor_a_tiempo = 15
        self.ahora = datetime(2026, 11, 17, 12)

    def pedido(self, **cambios):
        fila = dict(OrderTypeID=1, TypeStatusID=2, Cancelado=0,
                    FechaEntrega='17-11-26', HoraEntrega='12:30',
                    HoraCaptura='08:00', PriorityID=1, PaymentConfirmedID=1)
        fila.update(cambios)
        return fila

    def resumir(self, filas):
        return self.modelo.resumir_pedidos(filas, self.ahora)

    def test_categorias_excluyentes_no_restan_cancelados_dos_veces(self):
        filas = [self.pedido(), self.pedido(OrderTypeID=2),
                 self.pedido(OrderTypeID=3), self.pedido(Cancelado=1),
                 self.pedido(OrderTypeID=2, Cancelado=1),
                 self.pedido(OrderTypeID=3, TypeStatusID=10)]
        resumen = self.resumir(filas)
        self.assertEqual([resumen[k] for k in ('total', 'pedidos', 'anexos', 'cambios', 'cancelados')],
                         [6, 1, 1, 1, 3])
        self.assertEqual(resumen['pedidos'], resumen['total'] - resumen['cancelados']
                         - resumen['anexos'] - resumen['cambios'])
        self.assertEqual(resumen['pendientes'], 3)

    def test_usa_entrega_y_limites_configurados_para_todos_los_tipos(self):
        filas = [self.pedido(HoraEntrega='12:30'),
                 self.pedido(OrderTypeID=2, HoraEntrega='12:15'),
                 self.pedido(OrderTypeID=3, HoraEntrega='12:14'),
                 self.pedido(HoraEntrega='11:59')]
        resumen = self.resumir(filas)
        self.assertEqual([resumen[k] for k in ('en_tiempo', 'proximos', 'retrasados')], [1, 1, 2])
        self.modelo.valor_en_tiempo = 45
        self.modelo.valor_a_tiempo = 20
        resumen = self.resumir(filas)
        self.assertEqual([resumen[k] for k in ('en_tiempo', 'proximos', 'retrasados')], [0, 1, 3])

    def test_pago_prioridad_y_tipo_entrega_no_sustituyen_la_puntualidad(self):
        filas = [self.pedido(PaymentConfirmedID=2), self.pedido(PaymentConfirmedID=3),
                 self.pedido(PriorityID=2), self.pedido(OrderDeliveryTypeID=2)]
        resumen = self.resumir(filas)
        self.assertEqual(resumen['en_tiempo'], 4)
        self.assertEqual(resumen['pendientes'], 4)

    def test_finalizados_y_en_ruta_cuentan_como_pedidos_pero_no_pendientes(self):
        resumen = self.resumir([self.pedido(TypeStatusID=s) for s in (9, 13, 14, 15)])
        self.assertEqual(resumen['pedidos'], 4)
        self.assertEqual(resumen['pendientes'], 0)
        self.assertEqual(resumen['retrasados'], 0)

    def test_sin_horario_no_se_presenta_como_en_tiempo(self):
        filas = [self.pedido(FechaEntrega=None), self.pedido(HoraEntrega=None),
                 self.pedido(HoraEntrega='None'), self.pedido(FechaEntrega='fecha inválida')]
        resumen = self.resumir(filas)
        self.assertEqual(resumen['sin_horario'], 4)
        self.assertEqual(resumen['pendientes'], 4)
        self.assertEqual(resumen['en_tiempo'], 0)

    def test_cancelacion_con_valores_de_texto_y_status_prevalece(self):
        resumen = self.resumir([self.pedido(Cancelado='1'),
                               self.pedido(TypeStatusID='10', Cancelado='0'),
                               self.pedido(Cancelado=True)])
        self.assertEqual(resumen['cancelados'], 3)
        self.assertEqual(resumen['pendientes'], 0)

    def test_fechas_futuras_y_pasadas(self):
        resumen = self.resumir([self.pedido(FechaEntrega='18-11-26'),
                               self.pedido(FechaEntrega='16-11-26')])
        self.assertEqual(resumen['en_tiempo'], 1)
        self.assertEqual(resumen['retrasados'], 1)

    def test_consulta_vacia_limpia_todos_los_contadores(self):
        self.assertTrue(all(valor == 0 for valor in self.resumir([]).values()))
        self.assertTrue(all(valor == 0 for valor in self.resumir(None).values()))

    def test_filtro_sin_resultados_conserva_resumen_global_y_consulta_vacia_lo_limpia(self):
        controlador = object.__new__(ControladorPanelPedidos)
        controlador._modelo = self.modelo
        ventanas = Mock()
        tabla = Mock()
        ventanas.componentes_forma = {'tbv_pedidos': tabla}
        controlador._interfaz = SimpleNamespace(ventanas=ventanas)
        self.modelo.consulta_pedidos = [self.pedido(Cancelado=1)]
        controlador._pintar_tabla_pedidos([])
        ventanas.insertar_input_componente.assert_any_call('lbl_resumen_total', 'Registros: 1')
        ventanas.insertar_input_componente.assert_any_call('lbl_resumen_cancelados', 'Cancelados: 1')
        self.modelo.consulta_pedidos = []
        ventanas.reset_mock()
        controlador._limpiar_tabla()
        ventanas.insertar_input_componente.assert_any_call('lbl_resumen_total', 'Registros: 0')
        ventanas.insertar_input_componente.assert_any_call('lbl_resumen_cancelados', 'Cancelados: 0')


if __name__ == '__main__':
    unittest.main()
