"""Misma matriz de impresión para las tres distribuciones, sin abrir ventanas."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
if (ROOT / 'imprimir_modulo/herramientas/impresion.py').is_file():
    SERVICIO = ROOT / 'imprimir_modulo/herramientas/impresion.py'
    VISTA = ROOT / 'imprimir_modulo/vista.py'
else:
    CAPTURA = ROOT / ('herramientas/capturar_documento' if (ROOT / 'panel').is_dir() else 'capturar_documento')
    SERVICIO = CAPTURA / 'selector_modulo/servicio_impresion_silenciosa.py'
    VISTA = CAPTURA / 'herramientas/imprimir_modulo/imprimir_modulo.py'


def clase_metodos(path, nombres, atributos=None):
    arbol = ast.parse(path.read_text())
    nodos = [n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef) and n.name in nombres]
    clase = ast.ClassDef(name='BajoPrueba', bases=[], keywords=[], body=nodos, decorator_list=[])
    modulo = ast.fix_missing_locations(ast.Module(body=[clase], type_ignores=[]))
    contexto = {}
    exec(compile(modulo, str(path), 'exec'), contexto)
    resultado = contexto['BajoPrueba']
    for k, v in (atributos or {}).items():
        setattr(resultado, k, v)
    return resultado


Servicio = clase_metodos(SERVICIO, {'_resolver_impresora', '_consultar_contexto_documento',
    '_fuente_base_de_datos', '_obtener_datos_documento', '_extraer_cantidad', '_extraer_document_id'},
    dict(MODULOS_CON_RUTA=(21, 1400, 1692), MODULOS_SECUNDARIA_DIRECTO=(967, 1692, 1316, 1319)))
Vista = clase_metodos(VISTA, {'_determinar_cantidad_impresiones', '_es_contado_por_pedido', '_empleado_solo_ticket'})


class RegresionImpresorasTest(unittest.TestCase):
    def setUp(self):
        self.v = Vista()
        self.v._module_id = 21
        self.v._seleccionados_historial = []
        self.v._seleccionados_cancelados = []
        self.v._base_de_datos = Mock()
        self.s = Servicio()
        self.s.parametros = SimpleNamespace(id_modulo=21)
        self.s.modelo = Mock()

    def destino(self, **cambios):
        r = dict(RutaID=1040, Impresiones=1, Saldo=100, WayToPayID=5,
                 CreditBlock=0, AuthorizedCredit=1000, RemainingCredit=500)
        cantidad = cambios.pop('cantidad', 1)
        archivo = cambios.pop('archivo', f'ORIGINAL-prueba-0({cantidad})_456.html')
        r.update(cambios)
        self.s.modelo.fetchall.return_value = [r]
        return self.s._resolver_impresora(archivo, 'Principal configurada', 'Secundaria configurada')

    def cantidad(self, **cambios):
        p = dict(ZoneID=1040, OrderDocumentID=123, WayToPayID=5, Impresiones=2,
                 Saldo=100, CreditoRestringido=False)
        motivo = cambios.pop('motivo', 1)
        p.update(cambios)
        return self.v._determinar_cantidad_impresiones(p, motivo, 456)

    def test_firma_credito_saldo_pendiente_va_a_secundaria(self):
        self.assertEqual(self.destino(), 'Secundaria configurada')
        self.assertEqual(self.cantidad(), 2)

    def test_empleado_contado_solo_ticket_aunque_tenga_dos_impresiones(self):
        self.assertEqual(self.destino(Impresiones=2, WayToPayID=2), 'Principal configurada')
        self.assertEqual(self.cantidad(WayToPayID=2), 1)

    def test_empleado_efectivo_omite_copia_generada_por_version_anterior(self):
        self.assertEqual(self.destino(cantidad=2, Impresiones=2, WayToPayID=2),
                         'Principal configurada')
        self.assertIsNone(self.destino(archivo='COPIA-prueba-1(2)_456.html',
                                      Impresiones=2, WayToPayID=2))

    def test_contado_minisuper_no_adquiere_regla_de_mayoreo(self):
        self.s.parametros.id_modulo = 1400
        self.assertEqual(self.destino(cantidad=2, Impresiones=2, WayToPayID=2),
                         'Secundaria configurada')
        self.v._module_id = 1400
        self.assertEqual(self.cantidad(WayToPayID=2), 2)

    def test_contado_una_impresion_usa_principal_configurada(self):
        self.assertEqual(self.destino(WayToPayID=2), 'Principal configurada')
        self.assertEqual(self.cantidad(WayToPayID=2, Impresiones=1), 1)

    def test_pagado_una_impresion_sin_credito_o_suspendido_usa_principal(self):
        for cambios in (dict(Saldo=0), dict(CreditBlock=1), dict(RemainingCredit=-1), dict(AuthorizedCredit=0)):
            with self.subTest(cambios=cambios):
                self.assertEqual(self.destino(**cambios), 'Principal configurada')

    def test_evaluacion_guardada_prevalece_sobre_consulta_actual(self):
        self.assertEqual(self.destino(CreditBlock=1, Comentarios='--CRÉDITO VÁLIDO | DEBE: 500--'),
                         'Secundaria configurada')
        self.assertEqual(self.destino(Comentarios='--CRÉDITO RESTRINGIDO | DEBE: 1500--'),
                         'Principal configurada')

    def test_original_y_copia_conservan_destinos(self):
        self.assertEqual(self.destino(cantidad=2, Impresiones=2), 'Secundaria configurada')
        self.assertEqual(self.destino(archivo='COPIA-prueba-1(2)_456.html', Impresiones=2), 'Principal configurada')

    def test_mayoreo_ruta_1066_dos_impresiones_separan_original_y_copia(self):
        # Caso FM837984: transferencia, saldo pendiente, ajeno a empleados.
        contexto = dict(RutaID=1066, Impresiones=2, WayToPayID=6,
                        Saldo='3535.14', AuthorizedCredit=0, RemainingCredit='-18324.51')
        self.assertEqual(self.destino(cantidad=2, **contexto), 'Secundaria configurada')
        self.assertEqual(self.destino(archivo='COPIA-prueba-1(2)_269918.html', **contexto),
                         'Principal configurada')

    def test_mayoreo_reimpresion_ruta_1066_conserva_secundaria(self):
        self.assertEqual(self.destino(RutaID=1066, Impresiones=2, WayToPayID=6),
                         'Secundaria configurada')

    def test_mayoreo_sin_configuracion_doble_conserva_destino_anterior(self):
        self.assertEqual(self.destino(RutaID=1066, Impresiones=1,
                                     archivo='COPIA-prueba-1(2)_456.html'),
                         'Secundaria configurada')

    def test_minisuper_omite_copia_empleado(self):
        self.s.parametros.id_modulo = 1400
        self.assertIsNone(self.destino(archivo='COPIA-prueba-1(2)_456.html', Impresiones=2))
        self.assertEqual(self.destino(Impresiones=1), 'Secundaria configurada')

    def test_pagado_reimpresion_cancelacion_restriccion_reducen_cantidad(self):
        self.assertEqual(self.cantidad(Saldo=0), 1)
        self.assertEqual(self.cantidad(motivo=3), 1)
        self.assertEqual(self.cantidad(CreditoRestringido=True), 1)
        self.v._seleccionados_cancelados = [456]
        self.assertEqual(self.cantidad(), 1)
        self.v._seleccionados_cancelados = []
        self.v._seleccionados_historial = [456]
        self.assertEqual(self.cantidad(), 1)

    def test_credito_consulta_cliente_del_documento_en_vez_de_zona(self):
        self.v._base_de_datos.fetchone.return_value = 'Desbloqueado'
        self.assertEqual(self.cantidad(CreditoRestringido=False), 2)
        self.assertEqual(self.v._base_de_datos.fetchone.call_args.args[1], (456,))
        p = dict(ZoneID=1040, OrderDocumentID=123, WayToPayID=5, Impresiones=2, Saldo=100)
        self.assertEqual(self.v._determinar_cantidad_impresiones(p, 1, 456), 2)
        self.assertEqual(self.v._base_de_datos.fetchone.call_args.args[1], (456,))

    def test_empleado_sin_credito_solo_original_en_primaria(self):
        for forma in (5, 6, 2):
            with self.subTest(forma=forma):
                contexto = dict(Impresiones=2, AuthorizedCredit=0, RemainingCredit=0,
                                WayToPayID=forma, cantidad=2)
                self.assertEqual(self.destino(**contexto), 'Principal configurada')
                contexto.pop('cantidad')
                self.assertIsNone(self.destino(archivo='COPIA-prueba-1(2)_456.html', **contexto))
        self.v._base_de_datos.fetchone.return_value = 1
        self.assertEqual(self.cantidad(), 1)
        self.assertEqual(self.cantidad(WayToPayID=6), 1)

    def test_empleado_sin_limite_no_se_habilita_por_leyenda_guardada(self):
        self.assertEqual(self.destino(AuthorizedCredit=0, Impresiones=2,
                                     Comentarios='--CRÉDITO VÁLIDO | DEBE: 0--'),
                         'Principal configurada')

    def test_empleado_suspendido_o_excedido_omite_hoja(self):
        for contexto in (dict(CreditBlock=1), dict(RemainingCredit=-1),
                         dict(Comentarios='--CRÉDITO RESTRINGIDO | DEBE: 1500--')):
            with self.subTest(contexto=contexto):
                self.assertEqual(self.destino(Impresiones=2, cantidad=2, **contexto),
                                 'Principal configurada')
                self.assertIsNone(self.destino(Impresiones=2,
                    archivo='COPIA-prueba-1(2)_456.html', **contexto))

    def test_otra_ruta_sin_credito_conserva_original_y_copia(self):
        contexto = dict(RutaID=1066, AuthorizedCredit=0, Impresiones=2)
        self.assertEqual(self.destino(cantidad=2, **contexto), 'Secundaria configurada')
        self.assertEqual(self.destino(archivo='COPIA-prueba-1(2)_456.html', **contexto),
                         'Principal configurada')
        self.v._base_de_datos.fetchone.return_value = 1
        self.assertEqual(self.cantidad(ZoneID=1066), 2)
        self.v._base_de_datos.fetchone.assert_not_called()

    def test_modelo_directo_y_modelo_envuelto_se_resuelven(self):
        self.s.modelo.fetchall.return_value = [dict(RutaID=1040, Impresiones=2)]
        self.assertEqual(self.s._obtener_datos_documento(456), (1040, 2))
        db = self.s.modelo
        self.s.modelo = SimpleNamespace(base_de_datos=db)
        self.assertEqual(self.s._obtener_datos_documento(456), (1040, 2))
        db.base_de_datos = 'NombreBD'
        self.s.modelo = db
        self.assertEqual(self.s._obtener_datos_documento(456), (1040, 2))
        sql = db.fetchall.call_args.args[0]
        self.assertIn('E2.Impresiones', sql)
        self.assertIn('X.CustomerID', sql)


if __name__ == '__main__':
    unittest.main()
