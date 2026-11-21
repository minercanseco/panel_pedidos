"""Pruebas de los puntos de integración sin abrir ventanas ni conectar al ERP."""
import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
MODELO = next(p for p in (
    ROOT / 'herramientas/capturar_documento/modelo_captura.py',
    ROOT / 'capturar_documento/modelo_captura.py',
) if p.is_file())
HELPER = (ROOT / 'herramientas/credito_documento.py' if (ROOT / 'herramientas').is_dir()
          else ROOT / 'capturar_documento/credito_documento.py')
spec = importlib.util.spec_from_file_location('credito_integracion', HELPER)
credito = importlib.util.module_from_spec(spec)
spec.loader.exec_module(credito)


def metodo(archivo, nombre, **contexto):
    arbol = ast.parse(archivo.read_text())
    funcion = next(n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef) and n.name == nombre)
    modulo = ast.Module(body=[funcion], type_ignores=[])
    exec(compile(modulo, str(archivo), 'exec'), contexto)
    return contexto[nombre]


class IntegracionLeyendaTest(unittest.TestCase):
    def test_antes_de_cobrar_se_guardan_totales_y_despues_leyenda(self):
        eventos = []
        modelo = SimpleNamespace(
            documento=SimpleNamespace(document_id=17),
            afectar_impuestos_documento=lambda doc: eventos.append('impuestos'),
            actualizar_totales_documento=lambda doc: eventos.append('totales') or True,
            actualizar_leyenda_credito=lambda doc: eventos.append('leyenda'),
        )
        self.assertTrue(metodo(MODELO, 'preparar_documento_para_cobro')(modelo))
        self.assertEqual(eventos, ['impuestos', 'totales', 'leyenda'])

    def test_leyenda_se_refleja_en_documento_en_memoria(self):
        modelo = SimpleNamespace(module_id=21, documento=SimpleNamespace(document_id=17), base_de_datos=object())
        guardar = Mock(return_value='--CRÉDITO VÁLIDO | DEBE: 50--\nEntrega')
        resultado = metodo(MODELO, 'actualizar_leyenda_credito', guardar_leyenda_credito=guardar)(modelo)
        self.assertEqual(modelo.documento.comments, resultado)
        guardar.assert_called_once_with(modelo.base_de_datos, 17)

    def test_compras_no_genera_leyenda_crediticia(self):
        guardar = Mock()
        modelo = SimpleNamespace(module_id=152, documento=SimpleNamespace(document_id=17))
        self.assertIsNone(metodo(MODELO, 'actualizar_leyenda_credito', guardar_leyenda_credito=guardar)(modelo))
        guardar.assert_not_called()

    @unittest.skipUnless((ROOT / 'panel/panel_pedidos_modelo.py').is_file(), 'Sólo panel')
    def test_panel_usa_saldo_guardado_y_no_total_previo_pedido(self):
        db = Mock()
        db.fetchall.side_effect = [[dict(ModuleID=21, ZoneID=1040, CreditBlock=0,
                                        AuthorizedCredit=100, SaldoActual=20, DeudaOtros=30)],
                                  [dict(WayToPayID=5, PaymentTermName='Firma')]]
        modelo = SimpleNamespace(base_de_datos=db)
        fn = metodo(ROOT / 'panel/panel_pedidos_modelo.py', 'validar_credito_documento_cliente',
                    evaluar_credito_documento=credito.evaluar_credito_documento,
                    componer_comentarios=credito.componer_comentarios)
        texto = fn(modelo, 10, 'Entregar', 999999, 17, [55])
        self.assertIn('DEBE: 50.00', texto)
        self.assertIn('CRÉDITO DISPONIBLE: 50.00', texto)
        self.assertIn('Entregar', texto)


if __name__ == '__main__':
    unittest.main()
