import importlib.util
from pathlib import Path
import sqlite3
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
HELPER = next(p for p in (
    ROOT / 'herramientas/credito_documento.py',
    ROOT / 'capturar_documento/credito_documento.py',
    ROOT / 'imprimir_modulo/credito_documento.py',
) if p.is_file())
spec = importlib.util.spec_from_file_location('credito_bajo_prueba', HELPER)
credito = importlib.util.module_from_spec(spec)
spec.loader.exec_module(credito)


class LeyendaCreditoTest(unittest.TestCase):
    def registro(self, **cambios):
        r = dict(AuthorizedCredit=1000, SaldoActual=200, DeudaOtros=300,
                 CreditBlock=0, ZoneID=1040, ModuleID=21, Comments='Entrega en puerta')
        r.update(cambios)
        return r

    def test_cuenta_saldo_pendiente_y_no_total(self):
        resultado = credito.resolver_credito(self.registro(Total=900), [])
        self.assertEqual(resultado['Deuda'], 500)
        self.assertEqual(resultado['Disponible'], 500)
        self.assertIn('CRÉDITO VÁLIDO', resultado['Leyenda'])

    def test_pagado_no_agrega_importe(self):
        r = credito.resolver_credito(self.registro(SaldoActual=0), [])
        self.assertEqual(r['Deuda'], 300)

    def test_limite_exacto_sin_exceso(self):
        r = credito.resolver_credito(self.registro(DeudaOtros=800), [])
        self.assertFalse(r['Restringido'])
        self.assertEqual(r['Disponible'], 0)

    def test_exceso_indica_solo_diferencia(self):
        r = credito.resolver_credito(self.registro(DeudaOtros='800.01'), [])
        self.assertTrue(r['Restringido'])
        self.assertIn('DEBE PAGAR CONTADO: 0.01', r['Leyenda'])

    def test_suspension_prevalece_aunque_quede_credito(self):
        r = credito.resolver_credito(self.registro(CreditBlock=1), [])
        self.assertTrue(r['Restringido'])
        self.assertIn('SUSPENSIÓN CREDITICIA', r['Leyenda'])

    def test_contado_usa_nombre_no_comentarios_y_omite_restriccion(self):
        for forma in (1, 2, 3, 4, 6, 7, 8):
            r = credito.resolver_credito(self.registro(CreditBlock=1), [dict(
                WayToPayID=forma, PaymentTermName='Tarjeta Debito', Comments='Llevar terminal')])
            self.assertFalse(r['Restringido'])
            self.assertEqual(r['Leyenda'], '--SE ELIGIO FORMA DE PAGO: Tarjeta Debito--')

    def test_firma_no_omite_suspension(self):
        r = credito.resolver_credito(self.registro(CreditBlock=1), [dict(WayToPayID=5)])
        self.assertTrue(r['Restringido'])

    def test_nombre_inexistente_se_reporta(self):
        with self.assertRaises(ValueError):
            credito.resolver_credito(self.registro(), [dict(WayToPayID=2)])

    def test_actualizar_leyenda_no_duplica_y_conserva_texto_usuario(self):
        r = credito.resolver_credito(self.registro(), [])
        original = '--DEBE: 900. CRÉDITO DISPONIBLE: 100-- Entrega en puerta'
        una = credito.componer_comentarios(r, original)
        self.assertEqual(credito.componer_comentarios(r, una), una)
        self.assertIn('Entrega en puerta', una)
        self.assertNotIn('DEBE: 900', una)
        self.assertTrue(credito.tiene_evaluacion(una))

    def test_lectura_usa_documento_actual_y_pedidos_explicitos(self):
        db = Mock()
        db.fetchall.side_effect = [[self.registro()], [dict(WayToPayID=2, PaymentTermName='Efectivo')]]
        r = credito.evaluar_credito_documento(db, 123, [8, 8, 9])
        self.assertTrue(r['Contado'])
        self.assertEqual(db.fetchall.call_args_list[0].args[1], (123,))
        self.assertEqual(db.fetchall.call_args_list[1].args[1], (8, 9))

    def test_filtros_sql_no_duplican_documentos_ni_relaciones(self):
        db = Mock()
        db.fetchall.side_effect = [[self.registro()], []]
        credito.evaluar_credito_documento(db, 1)
        sql = db.fetchall.call_args_list[0].args[0]
        # Ejecutar los filtros reales sobre una base local; las conversiones
        # MONEY son específicas de SQL Server y no intervienen en el filtro.
        where = sql.split('WHERE P.DocumentID <> D.DocumentID', 1)[1].split(') AS Deuda', 1)[0]
        consulta = 'SELECT SUM(P.Balance) FROM docDocument P, docDocument D, Receptor WHERE D.DocumentID=1 AND P.DocumentID <> D.DocumentID' + where
        c = sqlite3.connect(':memory:')
        c.executescript('''
            CREATE TABLE docDocument(DocumentID INT, Balance NUMERIC, CancelledOn TEXT, StatusPaidID INT, ModuleID INT, BusinessEntityID INT);
            CREATE TABLE docDocumentExt(IDExtra INT, CustomerID INT);
            CREATE TABLE Receptor(ID INT);
            INSERT INTO Receptor VALUES(10);
            INSERT INTO docDocument VALUES
            (1,200,NULL,3,21,10), (2,300,NULL,3,21,10),
            (3,400,NULL,1,21,10), (4,500,'cancelado',3,21,10),
            (5,600,NULL,3,1687,10), (6,700,NULL,3,21,99),
            (7,50,NULL,2,1400,8179);
            INSERT INTO docDocumentExt VALUES(7,10),(7,10);
        ''')
        self.assertEqual(c.execute(consulta).fetchone()[0], 350)
        c.close()

    def test_guardar_es_idempotente(self):
        db = Mock()
        registro = self.registro()
        db.fetchall.side_effect = lambda sql, params: [registro] if 'AS DeudaOtros' in sql else []
        primero = credito.guardar_leyenda_credito(db, 123)
        registro['Comments'] = primero
        segundo = credito.guardar_leyenda_credito(db, 123)
        self.assertEqual(primero, segundo)
        self.assertEqual(db.command.call_args.args[1], (primero, 123))


if __name__ == '__main__':
    unittest.main()
