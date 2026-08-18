import glob
import logging
import os
import shutil
import subprocess
import threading
from pathlib import Path

try:
    import win32print
except Exception:
    win32print = None


logger = logging.getLogger(__name__)


class ServicioImpresionTicket:
    """Convierte un ticket HTML a PDF y lo imprime sin interfaz en Windows."""

    NOMBRE_IMPRESORA = 'Tickets'
    ANCHO_PAPEL_MM = 80
    # Equivale aproximadamente a las 0.2 pulgadas configuradas en el antiguo
    # PageSetup de WebBrowser. Deja un ancho útil de 70 mm y evita que el área
    # no imprimible del controlador térmico recorte la columna de importes.
    MARGEN_HORIZONTAL_MM = 5
    ALTURA_BASE_MM = 115
    ALTURA_PARTIDA_MM = 7
    ALTURA_MINIMA_MM = 130
    ALTURA_MAXIMA_MM = 1000
    TIMEOUT_CONVERSION = 30
    TIMEOUT_IMPRESION = 30

    def __init__(self, base_de_datos=None):
        self.base_de_datos = base_de_datos

    def imprimir_en_segundo_plano(
            self, ruta_html, cantidad_partidas,
            document_id, user_id, al_error=None,
            altura_base_mm=None,
    ):
        argumentos = (
            ruta_html,
            cantidad_partidas,
            document_id,
            user_id,
            altura_base_mm,
        )

        def ejecutar():
            try:
                self.imprimir(*argumentos)
            except Exception as error:
                self._guardar_error_impresion(ruta_html, error)
                logger.exception(
                    'No fue posible imprimir silenciosamente el ticket %s: %s',
                    document_id,
                    error,
                )
                if callable(al_error):
                    al_error(error)

        hilo = threading.Thread(
            target=ejecutar,
            name=f'impresion-ticket-{document_id}',
            daemon=False,
        )
        hilo.start()
        return hilo

    @staticmethod
    def _guardar_error_impresion(ruta_html, error):
        """Deja evidencia local junto al HTML para facilitar reimpresión."""
        try:
            ruta_error = Path(ruta_html).with_suffix('.print-error.txt')
            ruta_error.write_text(str(error), encoding='utf-8')
        except OSError:
            logger.exception('No fue posible guardar el diagnóstico de impresión.')

    def imprimir(
            self, ruta_html, cantidad_partidas,
            document_id, user_id, altura_base_mm=None,
    ):
        if os.name != 'nt':
            raise OSError(
                'La impresión silenciosa de tickets sólo está habilitada '
                'en Windows.'
            )

        ruta_html = Path(ruta_html).resolve()
        if not ruta_html.is_file():
            raise FileNotFoundError(
                f'No se encontró el HTML del ticket: {ruta_html}'
            )

        impresora = self._obtener_impresora_tickets()
        wkhtmltopdf = self._buscar_wkhtmltopdf()
        if wkhtmltopdf is None:
            raise FileNotFoundError(
                'No se encontró wkhtmltopdf.exe. Instálelo en su ruta '
                'predeterminada o configure WKHTMLTOPDF_PATH.'
            )

        ruta_pdf = ruta_html.with_suffix('.pdf')
        self._convertir_a_pdf(
            wkhtmltopdf,
            ruta_html,
            ruta_pdf,
            cantidad_partidas,
            altura_base_mm,
        )

        try:
            self._enviar_a_impresora(ruta_pdf, impresora)
            self._marcar_impreso(document_id, user_id)
        except Exception:
            # Se conserva el PDF cuando falla el envío para permitir una
            # reimpresión o diagnóstico manual.
            raise
        else:
            ruta_error = ruta_html.with_suffix('.print-error.txt')
            try:
                ruta_error.unlink(missing_ok=True)
            except OSError:
                pass
            try:
                ruta_pdf.unlink()
            except OSError:
                logger.warning(
                    'No fue posible eliminar el PDF temporal %s', ruta_pdf
                )
        return True

    def imprimir_html_en_impresora(
            self, ruta_html, impresora, cantidad_partidas=0,
            altura_base_mm=None, ancho_papel_mm=None,
            margen_horizontal_mm=None,
    ):
        """Imprime un HTML en la impresora indicada sin modificar la BD."""
        if os.name != 'nt':
            raise OSError(
                'La impresión silenciosa sólo está habilitada en Windows.'
            )
        if not str(impresora or '').strip():
            raise ValueError('No se indicó una impresora de destino.')

        ruta_html = Path(ruta_html).resolve()
        if not ruta_html.is_file():
            raise FileNotFoundError(
                f'No se encontró el HTML para imprimir: {ruta_html}'
            )
        wkhtmltopdf = self._buscar_wkhtmltopdf()
        if wkhtmltopdf is None:
            raise FileNotFoundError(
                'No se encontró wkhtmltopdf.exe.'
            )

        ruta_pdf = ruta_html.with_suffix('.pdf')
        self._convertir_a_pdf(
            wkhtmltopdf,
            ruta_html,
            ruta_pdf,
            cantidad_partidas,
            altura_base_mm,
            ancho_papel_mm,
            margen_horizontal_mm,
        )
        try:
            self._enviar_a_impresora(ruta_pdf, str(impresora).strip())
        finally:
            try:
                ruta_pdf.unlink(missing_ok=True)
            except OSError:
                logger.warning('No fue posible eliminar %s', ruta_pdf)
        return True

    def _obtener_impresora_tickets(self):
        if win32print is None:
            raise RuntimeError(
                'pywin32 es necesario para localizar la impresora Tickets.'
            )

        banderas = (
            win32print.PRINTER_ENUM_LOCAL
            | win32print.PRINTER_ENUM_CONNECTIONS
        )
        impresoras = {
            str(registro[2]).strip().casefold(): str(registro[2]).strip()
            for registro in win32print.EnumPrinters(banderas)
        }
        impresora = impresoras.get(self.NOMBRE_IMPRESORA.casefold())
        if not impresora:
            raise RuntimeError(
                'No está instalada la impresora de Windows llamada Tickets.'
            )
        return impresora

    def _convertir_a_pdf(
            self, ejecutable, ruta_html, ruta_pdf,
            cantidad_partidas, altura_base_mm=None, ancho_papel_mm=None,
            margen_horizontal_mm=None,
    ):
        altura_base = (
            self.ALTURA_BASE_MM
            if altura_base_mm is None
            else int(altura_base_mm)
        )
        altura = altura_base + (
            max(0, int(cantidad_partidas or 0)) * self.ALTURA_PARTIDA_MM
        )
        altura = max(
            self.ALTURA_MINIMA_MM,
            min(altura, self.ALTURA_MAXIMA_MM),
        )
        ancho = (
            self.ANCHO_PAPEL_MM
            if ancho_papel_mm is None
            else int(ancho_papel_mm)
        )
        margen_horizontal = (
            self.MARGEN_HORIZONTAL_MM
            if margen_horizontal_mm is None
            else int(margen_horizontal_mm)
        )
        comando = [
            str(ejecutable),
            '--quiet',
            '--encoding', 'utf-8',
            '--enable-local-file-access',
            # La plantilla original del corte referencia fuentes web. La
            # impresión debe continuar con las fuentes de respaldo cuando el
            # servidor no tenga salida a Internet.
            '--load-error-handling', 'ignore',
            '--load-media-error-handling', 'ignore',
            '--page-width', f'{ancho}mm',
            '--page-height', f'{altura}mm',
            '--margin-top', '0mm',
            '--margin-right', f'{margen_horizontal}mm',
            '--margin-bottom', '0mm',
            '--margin-left', f'{margen_horizontal}mm',
            '--disable-smart-shrinking',
            str(ruta_html),
            str(ruta_pdf),
        ]
        self._ejecutar(
            comando,
            self.TIMEOUT_CONVERSION,
            errores_permitidos=('ContentNotFoundError',),
            archivo_resultado=ruta_pdf,
        )
        if not ruta_pdf.is_file() or ruta_pdf.stat().st_size == 0:
            raise RuntimeError('wkhtmltopdf no generó un PDF válido.')

    def _enviar_a_impresora(self, ruta_pdf, impresora):
        sumatra = self._buscar_sumatra()
        if sumatra is not None:
            self._ejecutar([
                str(sumatra),
                '-print-to', impresora,
                # El controlador térmico tiene un área imprimible menor que
                # los 80 mm físicos. "fit" reduce el PDF uniformemente y
                # evita recortar importes, centavos y el pie derecho.
                '-print-settings', 'fit',
                '-silent',
                str(ruta_pdf),
            ], self.TIMEOUT_IMPRESION)
            return

        gsprint = self._buscar_gsprint()
        ghostscript = self._buscar_ghostscript()
        if gsprint is not None and ghostscript is not None:
            self._ejecutar([
                str(gsprint),
                '-ghostscript', str(ghostscript),
                '-printer', impresora,
                str(ruta_pdf),
            ], self.TIMEOUT_IMPRESION)
            return

        raise FileNotFoundError(
            'No se encontró SumatraPDF.exe ni la combinación '
            'gsprint.exe/Ghostscript para enviar el ticket.'
        )

    def _marcar_impreso(self, document_id, user_id):
        if self.base_de_datos is None:
            return
        self.base_de_datos.command(
            'UPDATE docDocument '
            'SET PrintedOn = GETDATE(), PrintedBy = ? '
            'WHERE DocumentID = ?',
            (int(user_id or 0), int(document_id or 0)),
        )

    @staticmethod
    def _ejecutar(
            comando, timeout, errores_permitidos=(), archivo_resultado=None,
    ):
        resultado = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
            check=False,
        )
        if resultado.returncode != 0:
            detalle = (resultado.stderr or resultado.stdout or '').strip()
            error_permitido = any(
                texto in detalle for texto in errores_permitidos
            )
            resultado_valido = (
                archivo_resultado is not None
                and Path(archivo_resultado).is_file()
                and Path(archivo_resultado).stat().st_size > 0
            )
            if error_permitido and resultado_valido:
                logger.warning(
                    'La conversión terminó con un recurso externo no '
                    'disponible; se usará el PDF generado: %s', detalle,
                )
                return resultado
            raise RuntimeError(
                f'El proceso de impresión terminó con código '
                f'{resultado.returncode}: {detalle}'
            )
        return resultado

    @classmethod
    def _buscar_wkhtmltopdf(cls):
        return cls._buscar_ejecutable(
            'WKHTMLTOPDF_PATH',
            'wkhtmltopdf.exe',
            r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
            r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe',
        )

    @classmethod
    def _buscar_sumatra(cls):
        local_app_data = os.getenv('LOCALAPPDATA', '')
        return cls._buscar_ejecutable(
            'SUMATRA_PDF_PATH',
            'SumatraPDF.exe',
            r'C:\Program Files\SumatraPDF\SumatraPDF.exe',
            r'C:\Program Files (x86)\SumatraPDF\SumatraPDF.exe',
            os.path.join(local_app_data, 'SumatraPDF', 'SumatraPDF.exe'),
        )

    @classmethod
    def _buscar_gsprint(cls):
        return cls._buscar_ejecutable(
            'GSPRINT_PATH', 'gsprint.exe',
            os.path.join(os.getcwd(), 'gsprint.exe'),
        )

    @classmethod
    def _buscar_ghostscript(cls):
        ejecutable = cls._buscar_ejecutable(
            'GHOSTSCRIPT_PATH', 'gswin64c.exe', 'gswin32c.exe'
        )
        if ejecutable is not None:
            return ejecutable
        coincidencias = glob.glob(
            r'C:\Program Files\gs\gs*\bin\gswin64c.exe'
        )
        return Path(sorted(coincidencias)[-1]) if coincidencias else None

    @staticmethod
    def _buscar_ejecutable(variable_entorno, nombre_path, *rutas):
        candidatos = [os.getenv(variable_entorno, ''), *rutas]
        ruta_path = shutil.which(nombre_path)
        if ruta_path:
            candidatos.insert(1, ruta_path)
        for candidato in candidatos:
            if candidato and os.path.isfile(candidato):
                return Path(candidato).resolve()
        return None
