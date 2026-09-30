import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'herramientas'))

from capturar_documento.herramientas.prorrateo_maniobras import (
    ProrrateoManiobras,
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
