import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'herramientas'))

from capturar_documento.herramientas.prorrateo_maniobras import (
    ProrrateoManiobras,
)
from capturar_documento.persistencia_prorrateo import (
    persistir_prorrateo_maniobras,
    revertir_prorrateo_maniobras,
)


def crear_herramienta(partidas):
    herramienta = ProrrateoManiobras.__new__(ProrrateoManiobras)
    herramienta.documento = SimpleNamespace(items=partidas)
    herramienta.product_id_maniobras = 1048
    herramienta.aplicado = False
    herramienta.registros_prorrateo = []
    herramienta.var_costo = Mock()
    herramienta.var_subtotal_factura = Mock()
    herramienta.var_total_factura = Mock()
    herramienta._recalcular_documento = Mock()
    herramienta._actualizar_vista_previa = Mock()
    return herramienta


class EliminarManiobrasTests(TestCase):
    def test_refresca_si_revertir_ya_retiro_la_partida(self):
        maniobras = {'ProductID': 1048, 'DocumentItemID': 0}
        herramienta = crear_herramienta([maniobras])
        herramienta.aplicado = True

        def revertir():
            herramienta.documento.items.remove(maniobras)
            return True

        herramienta.revertir = Mock(side_effect=revertir)

        self.assertTrue(herramienta.eliminar_maniobras())
        herramienta.var_costo.set.assert_called_once_with('0.00')
        herramienta.var_subtotal_factura.set.assert_called_once_with('')
        herramienta.var_total_factura.set.assert_called_once_with('')
        herramienta._recalcular_documento.assert_called_once_with()
        herramienta._actualizar_vista_previa.assert_called_once_with()

    def test_marca_como_eliminada_una_partida_guardada(self):
        maniobras = {'ProductID': 1048, 'DocumentItemID': 25}
        herramienta = crear_herramienta([maniobras])

        self.assertTrue(herramienta.eliminar_maniobras())
        self.assertEqual(maniobras['ItemProductionStatusModified'], 3)
        herramienta._recalcular_documento.assert_called_once_with()
        herramienta._actualizar_vista_previa.assert_called_once_with()


class PersistenciaProrrateoTests(TestCase):
    def test_reversion_escribe_total_y_no_subtotal_de_partida(self):
        base_de_datos = Mock()

        revertir_prorrateo_maniobras(
            base_de_datos,
            230437,
            'operacion-1',
            7,
        )

        sql, parametros = base_de_datos.command.call_args.args
        self.assertIn('I.Total = P.SubTotalBefore', sql)
        self.assertNotIn('I.SubTotal', sql)
        self.assertIn('BEGIN TRANSACTION', sql)
        self.assertEqual(parametros[0:2], (230437, 'operacion-1'))

    def test_persistencia_revierte_antes_de_guardar_bitacora(self):
        base_de_datos = Mock()
        registros = [{
            'OperationID': 'operacion-1',
            'DatabaseAction': 'REVERT',
        }]

        persistir_prorrateo_maniobras(
            base_de_datos,
            230437,
            7,
            registros,
        )

        self.assertEqual(base_de_datos.command.call_count, 1)
        base_de_datos.guardar_prorrateo_maniobras.assert_called_once_with(
            230437,
            7,
            registros,
        )
