import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from panel.panel_pedidos_controlador import ControladorPanelPedidos


class OrdenSinFechaTests(unittest.TestCase):
    def controlador(self):
        c=object.__new__(ControladorPanelPedidos)
        c._interfaz=SimpleNamespace(ventanas=Mock(),crear_columnas_tabla=Mock(return_value=[]))
        c._modelo=Mock();c._colorear_filas_panel_horarios=Mock()
        return c

    def test_busqueda_sin_fecha_ordena_ids_numericos_antes_de_rellenar(self):
        c=self.controlador();c._interfaz.ventanas.obtener_input_componente.return_value=None
        c._modelo.buscar_pedidos_cliente_sin_fecha.return_value=[{'OrderDocumentID':'9'},{'OrderDocumentID':100},{'OrderDocumentID':'20'}]
        c._buscar_pedidos_cliente_sin_fecha('CLIENTE')
        filas=c._interfaz.ventanas.rellenar_table_view.call_args.args[2]
        self.assertEqual([int(f['OrderDocumentID']) for f in filas],[100,20,9])
        self.assertEqual(c._modelo.consulta_pedidos,filas)

    def test_filtros_con_sin_fecha_mantienen_orden_descendente(self):
        c=self.controlador();c._interfaz.ventanas.obtener_input_componente.return_value=1
        filas=[{'OrderDocumentID':2},{'OrderDocumentID':10}]
        c._pintar_tabla_pedidos(filas)
        self.assertEqual([f['OrderDocumentID'] for f in c._interfaz.ventanas.rellenar_table_view.call_args.args[2]],[10,2])
        self.assertEqual(filas[0]['OrderDocumentID'],2)

    def test_con_fecha_conserva_el_orden_existente(self):
        c=self.controlador();c._interfaz.ventanas.obtener_input_componente.return_value=0
        filas=[{'OrderDocumentID':2},{'OrderDocumentID':10}]
        c._pintar_tabla_pedidos(filas)
        self.assertEqual(c._interfaz.ventanas.rellenar_table_view.call_args.args[2],filas)

if __name__=='__main__':unittest.main()
