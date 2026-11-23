import unittest
from datetime import date, datetime
from unittest.mock import Mock
from herramientas.herramientas_panel.historial_terminales import (
    consultar_historial_terminales, resumir_terminales, formato_hora, HistorialTerminales)


def salida(terminal=4,usuario=64,liquidacion=100,numero=1):
    return dict(TerminalID=terminal,VendorUserID=usuario,LiquidationID=liquidacion,DeliveryNumber=numero,
                Referencia='CAJA2',Barcode='00123',Colaborador='NOMBRE PRUEBA',
                FechaSalida=datetime(2026,11,21,8,30),Asignaciones=3)


class HistorialTerminalesTests(unittest.TestCase):
    def test_fecha_parametrizada_y_rango_de_un_dia(self):
        db=Mock();db.fetchall.return_value=[]
        consultar_historial_terminales(db,'2026-11-21')
        sql,params=db.fetchall.call_args.args
        self.assertEqual(params,(date(2026,11,21),date(2026,11,22)))
        self.assertIn('D.DepartureToDelivery >= ?',sql)
        self.assertIn('D.DepartureToDelivery < ?',sql)
        self.assertIn('A.DeliveryNumber = S.DeliveryNumber',sql)
        self.assertNotIn('L.Status = 0',sql)
        self.assertNotIn('TPVCurrentAssignmentsCayal',sql)
        self.assertNotIn('T.DeletedOn IS NULL',sql)
        self.assertNotIn('D.DeletedOn IS NULL',sql)

    def test_fecha_invalida_no_consulta(self):
        db=Mock()
        with self.assertRaises(ValueError):consultar_historial_terminales(db,'fecha invalida')
        db.fetchall.assert_not_called()

    def test_resumen_cuenta_usuarios_y_salidas_sin_duplicar(self):
        filas=[salida(),salida(),salida(numero=2),salida(usuario=65,liquidacion=101)]
        resultado=resumir_terminales(filas)
        self.assertEqual(resultado[0]['Salidas'],3)
        self.assertEqual(resultado[0]['Colaboradores'],2)
        self.assertEqual(resumir_terminales([]),[])

    def test_detalle_se_filtra_por_terminal_id_no_por_nombre(self):
        ui=object.__new__(HistorialTerminales);ui.v=Mock()
        tabla=Mock();tabla.selection.return_value=('fila',);tabla.index.return_value=0
        ui.v.componentes_forma={'tvw_terminales':tabla};ui.columnas_detalle=[]
        ui.filas=[salida(terminal=1),salida(terminal=4)]
        ui.terminales=resumir_terminales(ui.filas)
        ui.mostrar_detalle()
        datos=ui.v.rellenar_treeview.call_args.args[2]
        self.assertEqual(len(datos),1)
        self.assertEqual(datos[0]['Colaborador'],'NOMBRE PRUEBA')
        self.assertEqual(datos[0]['Salida a reparto'],'21/11/2026 08:30:00')

    def test_fechas_sin_inventar_horas(self):
        self.assertEqual(formato_hora(None),'Sin registro')
        self.assertEqual(formato_hora(datetime(2026,11,21,8,30,15)),'21/11/2026 08:30:15')

    def test_busqueda_vacia_limpia_el_detalle_anterior(self):
        from unittest.mock import patch
        ui=object.__new__(HistorialTerminales);ui.v=Mock();ui.db=Mock()
        ui.columnas_terminales=[];ui.columnas_detalle=[]
        ui.v.obtener_input_componente.return_value='2026-11-21'
        with patch('herramientas.herramientas_panel.historial_terminales.consultar_historial_terminales',return_value=[]):
            ui.buscar()
        self.assertEqual(ui.filas,[]);self.assertEqual(ui.terminales,[])
        ui.v.rellenar_treeview.assert_any_call('tvw_detalle',[],[])

    def test_fecha_no_dispara_consulta_automatica_como_en_reportes(self):
        from unittest.mock import patch
        v=Mock();v.componentes_forma={'tvw_terminales':Mock(),'tvw_detalle':Mock()}
        db=Mock();db.fetchall.return_value=[]
        v.obtener_input_componente.return_value='2026-11-23'
        with patch('herramientas.herramientas_panel.historial_terminales.Ventanas',return_value=v):
            ui=HistorialTerminales(Mock(),db)
        eventos=v.cargar_eventos.call_args.args[0]
        self.assertNotIn('den_fecha',eventos)
        self.assertEqual(eventos['btn_buscar'],ui.buscar)
        self.assertEqual(db.fetchall.call_count,1)
        eventos['btn_buscar']()
        self.assertEqual(db.fetchall.call_count,2)


if __name__=='__main__':unittest.main()
