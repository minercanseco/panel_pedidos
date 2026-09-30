import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'herramientas'))

from capturar_documento.herramientas.abrir_xml_documento.main import (
    abrir_xml_documento,
    obtener_ruta_xml_documento,
)
from capturar_documento.herramientas.crear_pdf_documento.main import (
    generar_pdf_documento,
)


class BaseDatosPrueba:
    def __init__(self, directorio, status_cfdi=3):
        self.directorio = directorio
        self.status_cfdi = status_cfdi

    def validar_documento(self, document_id):
        return {
            'document_id': document_id,
            'doc_folio': 'FG181727',
            'deleted': 0,
            'status_cfdi': self.status_cfdi,
            'balance': 0,
            'zone_id': 0,
        }

    def fetchone(self, consulta, parametros=None):
        if 'SELECT RFC' in consulta:
            return 'XAXX010101000'
        if 'CFDDocumentsPath' in consulta:
            return self.directorio
        return None


class CreadorFalso:
    llamada = None

    def __init__(self, **kwargs):
        pass

    def crear_pdf_documento(self, *args):
        CreadorFalso.llamada = args
        return r'C:\DocumentosTimbrados\factura.pdf'


class HerramientasDocumentosTimbradosTest(unittest.TestCase):
    def test_resuelve_y_abre_xml_del_documento(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta = os.path.join(
                directorio,
                'CCA030210S3A_FACTURA_CFDi-'
                'FG181727_XAXX010101000.xml',
            )
            with open(ruta, 'w', encoding='utf-8') as archivo:
                archivo.write('<xml/>')

            base_de_datos = BaseDatosPrueba(directorio)
            self.assertEqual(
                obtener_ruta_xml_documento(base_de_datos, 181727),
                os.path.abspath(ruta),
            )
            with patch('subprocess.Popen') as abrir:
                abrir_xml_documento(base_de_datos, 181727)
            abrir.assert_called_once_with(
                ['notepad.exe', os.path.abspath(ruta)]
            )

    def test_genera_pdf_con_folio_y_rfc_timbrado(self):
        with patch(
                'capturar_documento.herramientas.crear_pdf_documento.main.CrearPDF',
                CreadorFalso,
        ):
            ruta = generar_pdf_documento(
                SimpleNamespace(id_usuario=7),
                BaseDatosPrueba(r'C:\DocumentosTimbrados'),
                181727,
                utilerias=object(),
            )

        self.assertEqual(ruta, r'C:\DocumentosTimbrados\factura.pdf')
        self.assertEqual(
            CreadorFalso.llamada[0],
            'CCA030210S3A_FACTURA_CFDi-'
            'FG181727_XAXX010101000.pdf',
        )


if __name__ == '__main__':
    unittest.main()
