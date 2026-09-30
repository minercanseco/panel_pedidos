import os
import shutil

from capturar_documento.herramientas.enviar_correos.generar_pdf_factura import (
    GenerarPDFFactura,
)


class CrearPDF:
    def __init__(
            self, parametros_contpaqi, base_de_datos, utilerias,
            path_documentos_timbrados,
    ):
        self._base_de_datos = base_de_datos
        self._path_documentos_timbrados = path_documentos_timbrados
        self._generador_factura = GenerarPDFFactura(
            parametros_contpaqi, base_de_datos, utilerias
        )

    def crear_pdf_documento(self, nombre_pdf, document_id, valores_documento):
        nombre_pdf = os.path.basename(nombre_pdf)
        base_nombre, _ = os.path.splitext(nombre_pdf)
        saldo = valores_documento.get('balance', 0)
        zone_id = int(valores_documento.get('zone_id', 0))

        self._generador_factura.marca_de_agua_id = 1 if saldo == 0 else 4
        if zone_id == 1043:
            self._generador_factura.marca_de_agua_id = 5

        self._generador_factura.nombre_archivo = base_nombre
        self._generador_factura.document_id = document_id
        ruta_html = self._generador_factura.generar_archivo_cfdi(motivo_id=7)
        base_html, extension_html = os.path.splitext(ruta_html)
        if extension_html.lower() == '.hmtl':
            ruta_html = base_html + '.html'

        carpeta = os.path.dirname(os.path.abspath(ruta_html))
        ruta_pdf = os.path.join(carpeta, base_nombre + '.pdf')
        self._generador_factura.html_a_pdf(ruta_html, ruta_pdf)
        _, destino_pdf = self._mover_a_documentos_timbrados(
            ruta_html, ruta_pdf
        )
        self._base_de_datos.command(
            'UPDATE docDocumentCFD SET PDFGenerado = 1 WHERE DocumentID = ?',
            (document_id,),
        )
        return destino_pdf

    def _mover_a_documentos_timbrados(self, ruta_html, ruta_pdf):
        os.makedirs(self._path_documentos_timbrados, exist_ok=True)
        destino_html = os.path.join(
            os.path.abspath(self._path_documentos_timbrados),
            os.path.basename(ruta_html),
        )
        destino_pdf = os.path.join(
            os.path.abspath(self._path_documentos_timbrados),
            os.path.basename(ruta_pdf),
        )
        shutil.move(os.path.abspath(ruta_html), destino_html)
        shutil.move(os.path.abspath(ruta_pdf), destino_pdf)
        return destino_html, destino_pdf
