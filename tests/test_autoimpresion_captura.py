import ast
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
import os
import re
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
import uuid

ROOT=Path(__file__).resolve().parents[1]
CAPTURA=ROOT/('herramientas/capturar_documento' if (ROOT/'panel').is_dir() else 'capturar_documento')


def metodo(path,nombre,contexto):
    nodo=next(n for n in ast.walk(ast.parse(path.read_text())) if isinstance(n,ast.FunctionDef) and n.name==nombre)
    contexto['__file__']=str(path)
    exec(compile(ast.Module(body=[nodo],type_ignores=[]),str(path),'exec'),contexto)
    return contexto[nombre]


class AutoimpresionCapturaTest(unittest.TestCase):
    def test_minisuper_inicializa_modulo_antes_de_aplicar_reglas(self):
        class ReglasVerificadas(Exception):
            pass
        class Proveedor:
            def _buscar_info_factura(self,doc):
                return dict(placeholders=dict(Saldo=100,ZoneID=1040,Impresiones=2))
            def _determinar_cantidad_impresiones(self,*args,**kwargs):
                if self._module_id != 1400:
                    raise AssertionError('Módulo incorrecto')
                raise ReglasVerificadas()
        contexto=dict(ImprimirModulo=Proveedor,Utilerias=Mock(),os=os)
        fn=metodo(CAPTURA/'selector_modulo/servicio_generacion_cfdi_ticket.py','generar_archivos',contexto)
        s=SimpleNamespace(MODULO_CFDI=1400,base_de_datos=Mock(),user_name='Usuario',
            _cantidad_con_letra=Mock(return_value='CIEN'),_documento_cancelado=Mock(return_value=False),
            _documento_tiene_historial=Mock(return_value=False))
        with self.assertRaises(ReglasVerificadas):
            fn(s,123)

    def test_ticket_sin_uuid_genera_nombres_unicos_y_con_documento(self):
        with tempfile.TemporaryDirectory() as tmp:
            ticket=SimpleNamespace(set_plantilla=Mock(),set_datos=Mock(),set_partidas=Mock(),generar_html=Mock(return_value='<html><body>Ticket</body></html>'))
            ticket.guardar_html=lambda: str(Path(tmp)/(ticket.set_datos.call_args.kwargs['uuid']+'.html'))
            c=dict(re=re,Path=Path,datetime=datetime,Decimal=Decimal,InvalidOperation=InvalidOperation,
                   uuid=uuid,Ticket158=Mock(return_value=ticket))
            fn=metodo(CAPTURA/'llamar_instancia_captura.py','_crear_ticket_de_venta',c)
            s=SimpleNamespace(_documento=SimpleNamespace(document_id=123,folio='NV123',amount_received=0,
                subtotal=100,ieps=0,iva=0,total=100,items=[],customer_change=0),
                _parametros_contpaqi=SimpleNamespace(uuid=None),
                _utilerias=SimpleNamespace(redondear_valor_cantidad_a_decimal=lambda v:v,cantidad_con_letra=lambda v:'CIEN'))
            primero,segundo=fn(s),fn(s)
            self.assertNotEqual(primero,segundo)
            for nombre in (primero,segundo):
                self.assertTrue(Path(nombre).name.startswith('ticket-123-'))
                self.assertNotIn('None',nombre)
                self.assertTrue(Path(nombre).is_file())

    def test_ticket_sigue_solicitando_impresion_al_finalizar(self):
        impresor=Mock()
        c=dict(MODULO_COMPRAS=152,MODULO_TICKET=158,ServicioImpresionTicket=Mock(return_value=impresor))
        fn=metodo(CAPTURA/'llamar_instancia_captura.py','_tareas_finales_de_afectacion_de_documentos',c)
        s=SimpleNamespace(_module_id=158,_documento=SimpleNamespace(document_id=123,cobrado_en_captura=False,items=[]),
            _modelo_captura=Mock(),_crear_ticket_de_venta=Mock(return_value='/tmp/ticket.html'),_base_de_datos=Mock(),_user_id=1)
        fn(s)
        impresor.imprimir_en_segundo_plano.assert_called_once()

    def test_error_ticket_se_notifica_si_no_hay_callback(self):
        hilo=Mock()
        def crear_hilo(**kwargs):
            hilo.start=kwargs['target']
            return hilo
        c=dict(threading=SimpleNamespace(Thread=crear_hilo),logger=Mock())
        fn=metodo(CAPTURA/'selector_modulo/servicio_impresion_ticket.py','imprimir_en_segundo_plano',c)
        s=SimpleNamespace(imprimir=Mock(side_effect=RuntimeError('Impresora no disponible')),
            _guardar_error_impresion=Mock(),_notificar_error_impresion=Mock())
        fn(s,'/tmp/ticket.html',1,123,1)
        s._guardar_error_impresion.assert_called_once()
        s._notificar_error_impresion.assert_called_once()
        self.assertEqual(s._notificar_error_impresion.call_args.args[0],123)


if __name__=='__main__':
    unittest.main()
