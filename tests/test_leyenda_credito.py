import importlib.util
from pathlib import Path
import sqlite3
import re
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

    def test_sin_limite_no_tiene_credito_aunque_deuda_sea_cero(self):
        r = credito.resolver_credito(self.registro(AuthorizedCredit=0, DeudaOtros=0, SaldoActual=0), [])
        self.assertTrue(r['Restringido'])
        self.assertIn('CRÉDITO RESTRINGIDO', r['Leyenda'])

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
            CREATE TABLE docDocument(DocumentID INT, Balance NUMERIC, CancelledOn TEXT, StatusPaidID INT, ModuleID INT, BusinessEntityID INT, OrderDocumentID INT);
            CREATE TABLE docDocumentExt(IDExtra INT, CustomerID INT);
            CREATE TABLE Receptor(ID INT);
            INSERT INTO Receptor VALUES(10);
            INSERT INTO docDocument VALUES
            (1,200,NULL,3,21,10,NULL), (2,300,NULL,3,21,10,NULL),
            (3,400,NULL,1,21,10,NULL), (4,500,'cancelado',3,21,10,NULL),
            (5,600,NULL,3,1687,10,NULL), (6,700,NULL,3,21,99,NULL),
            (7,50,NULL,2,1400,8179,NULL),
            (8,100,NULL,3,21,10,80), (9,50,NULL,3,21,10,90),
            (10,25,NULL,3,1400,10,80);
            CREATE TABLE docDocumentOrderCayal(OrderDocumentID INT, WayToPayID INT);
            INSERT INTO docDocumentOrderCayal VALUES (80,2),(90,5);
            INSERT INTO docDocumentExt VALUES(7,10),(7,10);
        ''')
        self.assertEqual(c.execute(consulta).fetchone()[0], 425)
        c.close()

    def test_ejemplo_tres_pedidos_solo_firma_consume_credito(self):
        firma = credito.resolver_credito(self.registro(
            AuthorizedCredit=500, DeudaOtros=100, SaldoActual=100),
            [dict(WayToPayID=5, PaymentTermName='Firma')])
        self.assertEqual(firma['Deuda'], 200)
        self.assertEqual(firma['Disponible'], 300)
        self.assertIn('DEBE: 200.00 | CRÉDITO DISPONIBLE: 300.00', firma['Leyenda'])
        for _ in range(2):
            efectivo = credito.resolver_credito(self.registro(
                AuthorizedCredit=500, DeudaOtros=200, SaldoActual=100),
                [dict(WayToPayID=2, PaymentTermName='Efectivo')])
            self.assertEqual(efectivo['Deuda'], 200)
            self.assertEqual(efectivo['Disponible'], 300)
            self.assertEqual(efectivo['Leyenda'], '--SE ELIGIO FORMA DE PAGO: Efectivo--')

    def test_solo_mayoreo_excluye_saldo_actual_de_contado(self):
        r = credito.resolver_credito(self.registro(ModuleID=1400),
                                    [dict(WayToPayID=2, PaymentTermName='Efectivo')])
        self.assertFalse(r['Contado'])
        self.assertEqual(r['Deuda'], 500)

    def test_filtro_funcion_sql_solo_excluye_contado_del_credito(self):
        sql = (ROOT / 'sql/actualizar_credito_pedidos_contado.sql').read_text()
        bloques = re.findall(r'AND NOT EXISTS \(\s*(SELECT 1\s+FROM dbo.docDocumentOrderCayal AS PedidoContado.*?WayToPayID <> 5)\s*\)', sql, re.S)
        self.assertEqual(len(bloques), 2)
        db = sqlite3.connect(':memory:')
        db.executescript("""
            CREATE TABLE docDocument(DocumentID INT, ModuleID INT, OrderDocumentID INT);
            CREATE TABLE docDocumentOrderCayal(OrderDocumentID INT, WayToPayID INT);
            INSERT INTO docDocument VALUES (1,21,10),(2,21,20),(3,21,NULL),
                (4,1400,20),(5,21,30),(6,21,40);
            INSERT INTO docDocumentOrderCayal VALUES (10,5),(20,2),(30,NULL),(40,0);
        """)
        for bloque in bloques:
            consulta = 'SELECT DocumentID FROM docDocument D WHERE NOT EXISTS (' + bloque.replace('dbo.', '') + ') ORDER BY DocumentID'
            self.assertEqual([r[0] for r in db.execute(consulta)], [1,3,4,5,6])
        db.close()

    def test_funcion_sql_separa_cartera_completa_y_credito_utilizado(self):
        sql = (ROOT / 'sql/actualizar_credito_pedidos_contado.sql').read_text()
        def where_para(alias):
            fin = sql.index(') AS ' + alias + '\n')
            inicio = sql.rfind('    LEFT OUTER JOIN (', 0, fin)
            bloque = sql[inicio:fin]
            return re.search(r'WHERE\s+(.*?)\n\s*\) AS DB', bloque, re.S).group(1).replace('dbo.', '').replace('@BusinessEntityID', ':cliente')
        db = sqlite3.connect(':memory:')
        db.executescript("""
            CREATE TABLE docDocument(DocumentID INT, ModuleID INT, OrderDocumentID INT,
                BusinessEntityID INT, Balance NUMERIC, CancelledOn TEXT, StatusPaidID INT);
            CREATE TABLE docDocumentExt(IDExtra INT, CustomerID INT);
            CREATE TABLE docDocumentOrderCayal(OrderDocumentID INT, WayToPayID INT);
            INSERT INTO docDocument VALUES
                (1,21,NULL,10,100,NULL,3), (2,21,20,10,100,NULL,3),
                (3,21,30,10,100,NULL,3), (4,21,40,10,100,NULL,3),
                (5,21,50,10,100,NULL,1), (6,21,60,10,100,'cancelado',3);
            INSERT INTO docDocumentOrderCayal VALUES (20,5),(30,2),(40,2),(50,5),(60,5);
        """)
        desde = ' FROM docDocument D LEFT JOIN docDocumentExt X ON D.DocumentID=X.IDExtra WHERE '
        deuda, cantidad = db.execute('SELECT SUM(D.Balance),COUNT(D.DocumentID)' + desde + where_para('Debe'), {'cliente':10}).fetchone()
        utilizada = db.execute('SELECT SUM(D.Balance)' + desde + where_para('CreditoUtilizado'), {'cliente':10}).fetchone()[0]
        self.assertEqual((deuda, cantidad, utilizada, 500-utilizada), (400,4,200,300))
        db.execute('UPDATE docDocument SET Balance=0,StatusPaidID=1 WHERE DocumentID IN (1,2)')
        self.assertEqual(db.execute('SELECT SUM(D.Balance)' + desde + where_para('Debe'), {'cliente':10}).fetchone()[0], 200)
        self.assertIsNone(db.execute('SELECT SUM(D.Balance)' + desde + where_para('CreditoUtilizado'), {'cliente':10}).fetchone()[0])
        self.assertIn('Debe.Saldo           AS Debt', sql)
        self.assertIn('CreditoUtilizado.Saldo, 0), 1)', sql)
        self.assertIn('AS CreditDebt', sql)
        db.close()

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
