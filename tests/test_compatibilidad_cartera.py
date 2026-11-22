"""Cartera cobrable y crédito utilizado son montos distintos."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
CAPTURA = ROOT / ('herramientas/capturar_documento' if (ROOT / 'panel').is_dir() else 'capturar_documento')
ARCHIVO = CAPTURA / 'herramientas/cobrar_cartera/buscar_generales_cliente_cartera.py'


class CompatibilidadCarteraTest(unittest.TestCase):
    def llamar(self, deuda, deuda_crediticia):
        arbol = ast.parse(ARCHIVO.read_text())
        fn = next(n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef) and n.name == '_llamar_instancia')
        interfaz, controlador = Mock(), Mock()
        contexto = dict(InterfazSaldarCartera=interfaz, ControladorSaldarCartera=controlador)
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(ARCHIVO), 'exec'), contexto)
        obj = SimpleNamespace(
            _instancia_llamada=False,
            _info_cliente_seleccionado=[dict(Debt=deuda, CreditDebt=deuda_crediticia)],
            _ventanas=Mock(), _cliente=Mock(), _master=Mock(), _base_de_datos=Mock(),
            _parametros_contpaqi=SimpleNamespace(id_principal=0),
        )
        contexto['_llamar_instancia'](obj)
        return obj, controlador

    def test_solo_contado_pendiente_permite_abrir_y_cobrar(self):
        obj, controlador = self.llamar(200, 0)
        controlador.assert_called_once()
        obj._ventanas.mostrar_mensaje.assert_not_called()
        obj._ventanas.crear_popup_ttkbootstrap.assert_called_once()

    def test_cartera_mixta_permite_abrir_por_todos_los_pendientes(self):
        obj, controlador = self.llamar(400, 200)
        controlador.assert_called_once()
        obj._ventanas.mostrar_mensaje.assert_not_called()

    def test_sin_pendientes_no_abre_cartera(self):
        obj, controlador = self.llamar(0, 0)
        controlador.assert_not_called()
        obj._ventanas.mostrar_mensaje.assert_called_once()


if __name__ == '__main__':
    unittest.main()
