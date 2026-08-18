import os
import uuid
import shutil
import tempfile
import subprocess
import tkinter as tk

try:
    import win32print
except Exception:
    win32print = None

from herramientas.capturar_documento.herramientas.imprimir_modulo.main import ImprimirModulo
from herramientas.capturar_documento.herramientas.predeterminar_impresora.main import PredeterminarImpresora
from herramientas.capturar_documento.selector_modulo.servicio_impresion_ticket import (
    ServicioImpresionTicket,
)


class ServicioImpresionSilenciosa:
    IMPRESORA_PRINCIPAL = 'Tickets'
    MODULOS_CON_RUTA = (1400, 1692, 21)
    MODULOS_SECUNDARIA_DIRECTO = (-1, 967, 1692, 1316, 1319)

    def __init__(self, parametros, modelo=None):
        self.parametros = parametros
        self.modelo = modelo

    def _diag(self, mensaje):
        print(f"[IMPRESION] {mensaje}")

    def imprimir(self, id_modulo=None, id_principal=None, id_usuario=None):
        impresora_original = self._obtener_impresora_predeterminada()

        self._normalizar_parametros(
            id_modulo=id_modulo,
            id_principal=id_principal,
            id_usuario=id_usuario
        )

        impresora_primaria, impresora_secundaria = self._obtener_impresoras_configuradas()

        try:
            self._generar_archivos_impresion()

            directorio_uuid = self._obtener_directorio_uuid()

            if not os.path.isdir(directorio_uuid):
                raise FileNotFoundError(
                    f"No se generó el directorio de impresión: {directorio_uuid}"
                )

            archivos = os.listdir(directorio_uuid)

            if not archivos:
                raise FileNotFoundError(
                    f"No se generaron archivos de impresión en: {directorio_uuid}"
                )

            for archivo in archivos:
                ruta_archivo = os.path.join(directorio_uuid, archivo)

                if not os.path.isfile(ruta_archivo):
                    continue

                impresora = self._resolver_impresora(
                    archivo=archivo,
                    impresora_primaria=impresora_primaria,
                    impresora_secundaria=impresora_secundaria
                )

                if not impresora:
                    continue

                self._predeterminar_impresora(impresora)
                self._imprimir_archivo(
                    ruta_archivo,
                    impresora=impresora,
                )

        finally:
            if impresora_original:
                self._predeterminar_impresora(impresora_original)

            self._borrar_directorio_uuid()
            self._limpiar_parametros_impresion()

    def _normalizar_parametros(self, id_modulo=None, id_principal=None, id_usuario=None):
        self.parametros.uuid = str(uuid.uuid4())

        if id_modulo is not None:
            self.parametros.id_modulo = int(id_modulo or 0)

        if id_principal is not None:
            self.parametros.id_principal = int(id_principal or 0)

        if id_usuario is not None:
            self.parametros.id_usuario = int(id_usuario or 0)

        id_principal_actual = int(getattr(self.parametros, "id_principal", 0) or 0)

        if id_principal_actual:
            self.parametros.id_seleccionados = [id_principal_actual]
        elif not getattr(self.parametros, "id_seleccionados", None):
            self.parametros.id_seleccionados = []

    def _generar_archivos_impresion(self):
        configuracion = self._obtener_ruta_configuracion_impresoras()

        root = tk.Toplevel()
        root.withdraw()

        try:
            instancia = ImprimirModulo(
                root,
                self.parametros,
                predeterminar=False,
                configuracion=configuracion,
                impresion_silenciosa=False,
            )

            # Si no hay historial, _buscar_motivo_id() retorna 1.
            # Si hay historial, normalmente pediría motivo en UI.
            # Para impresión silenciosa se fuerza ORIGINAL.
            instancia._buscar_motivo_id = lambda: 1

            instancia._procesar_documentos_seleccionados()

            root.update_idletasks()
            root.update()

        finally:
            try:
                root.destroy()
            except Exception:
                pass

    def _resolver_impresora(
            self, archivo, impresora_primaria, impresora_secundaria,
            datos_enrutamiento=None,
    ):
        id_modulo = int(getattr(self.parametros, "id_modulo", 0) or 0)
        cantidad = self._extraer_cantidad(archivo)
        document_id = self._extraer_document_id(archivo)

        ruta_id = 0
        impresiones_cliente = 1

        datos_documento = (datos_enrutamiento or {}).get(document_id)
        if datos_documento:
            ruta_id = int(datos_documento.get('RutaID', 0) or 0)
            impresiones_cliente = int(
                datos_documento.get('Impresiones', 1) or 1
            )
        elif id_modulo in self.MODULOS_CON_RUTA and document_id:
            ruta_id, impresiones_cliente = self._obtener_datos_documento(document_id)

        if cantidad == 2:
            if id_modulo == 1400 or ruta_id == 1040:

                if "COPIA" in archivo and ruta_id == 1040 and id_modulo in (1692, 1400):
                    return None

                if "COPIA" in archivo:
                    return impresora_primaria

                return impresora_secundaria

            return impresora_secundaria

        if id_modulo in self.MODULOS_SECUNDARIA_DIRECTO:
            return impresora_secundaria

        if id_modulo in (21, 1400) and impresiones_cliente == 2:
            return impresora_secundaria

        return impresora_primaria

    def imprimir_archivos_generados(
            self, archivos, impresora_primaria, impresora_secundaria,
            cantidades_partidas=None, datos_enrutamiento=None,
    ):
        """Envía HTML ya validados conservando las reglas de enrutamiento."""
        cantidades_partidas = cantidades_partidas or {}
        impresora_primaria = self._validar_impresora_instalada(
            impresora_primaria,
            'principal',
        )
        impresora_secundaria = self._validar_impresora_instalada(
            impresora_secundaria,
            'secundaria',
        )

        for ruta_archivo in archivos:
            if not os.path.isfile(ruta_archivo):
                continue
            impresora = self._resolver_impresora(
                archivo=os.path.basename(ruta_archivo),
                impresora_primaria=impresora_primaria,
                impresora_secundaria=impresora_secundaria,
                datos_enrutamiento=datos_enrutamiento,
            )
            if not impresora:
                continue

            # Sumatra recibe el destino mediante -print-to. Cambiar además la
            # impresora predeterminada introduce una carrera con el spooler de
            # Windows y puede desviar el trabajo nuevamente a Tickets.
            self._diag(
                f'Archivo: {os.path.basename(ruta_archivo)} -> '
                f'impresora: {impresora}'
            )
            self._imprimir_archivo(
                ruta_archivo,
                impresora=impresora,
                cantidad_partidas=cantidades_partidas.get(
                    ruta_archivo, 0
                ),
            )

    @staticmethod
    def _impresoras_instaladas():
        if win32print is None:
            return {}
        banderas = (
            win32print.PRINTER_ENUM_LOCAL
            | win32print.PRINTER_ENUM_CONNECTIONS
        )
        return {
            str(registro[2]).strip().casefold(): str(registro[2]).strip()
            for registro in win32print.EnumPrinters(banderas)
        }

    def _validar_impresora_instalada(self, nombre, tipo):
        nombre = str(nombre or '').strip()
        if not nombre:
            raise ValueError(f'No hay impresora {tipo} configurada.')
        if win32print is None:
            return nombre

        nombre_real = self._impresoras_instaladas().get(nombre.casefold())
        if not nombre_real:
            raise RuntimeError(
                f'La impresora {tipo} configurada no está instalada en '
                f'Windows: {nombre}'
            )
        return nombre_real

    def _obtener_datos_documento(self, document_id):
        if not self.modelo:
            return 0, 1

        fuente = getattr(self.modelo, 'base_de_datos', self.modelo)
        registros = fuente.fetchall(
            """
            SELECT 
                ISNULL(D.Custom3, 0) AS RutaID,
                ISNULL(E.Impresiones, 1) AS Impresiones
            FROM docDocument D
            INNER JOIN orgBusinessEntity E 
                ON D.BusinessEntityID = E.BusinessEntityID
            WHERE D.DocumentID = ?
            """,
            (document_id,)
        )

        if not registros:
            return 0, 1

        registro = registros[0]
        if isinstance(registro, dict):
            return (
                int(registro.get("RutaID", 0) or 0),
                int(registro.get("Impresiones", 1) or 1)
            )

        return 0, 1

    def _obtener_impresoras_configuradas(self):
        ruta_configuracion = self._obtener_ruta_configuracion_impresoras()

        primaria = ""
        secundaria = ""

        if ruta_configuracion:
            import gzip
            import json

            try:
                with gzip.open(ruta_configuracion, "rt", encoding="utf-8") as archivo:
                    contenido = archivo.read().strip()

                datos = json.loads(contenido)

                primaria = (datos.get("primaria") or "").strip()
                secundaria = (datos.get("secundaria") or "").strip()

                print("CONFIG IMPRESORAS:", datos)

            except Exception as e:
                print(f"No se pudo leer impresoras.gz: {e}")

        primaria = self.IMPRESORA_PRINCIPAL

        if not secundaria:
            raise ValueError(
                'No hay impresora secundaria configurada. Abra Imprimir '
                'módulo, presione Configurar y seleccione ambos destinos.'
            )

        if not primaria:
            raise ValueError(
                "No hay impresora primaria configurada y Windows no tiene impresora predeterminada."
            )

        return primaria, secundaria

    def _predeterminar_impresora(self, nombre_impresora):
        if not nombre_impresora:
            return

        self.parametros.impresora = nombre_impresora

        try:
            PredeterminarImpresora(nombre_impresora)
        except TypeError:
            PredeterminarImpresora(nombre_impresora=nombre_impresora)

    def _imprimir_archivo(
            self, ruta_archivo, impresora=None, cantidad_partidas=0,
    ):
        impresora = impresora or self._obtener_impresora_predeterminada()
        id_modulo = int(getattr(self.parametros, 'id_modulo', 0) or 0)
        alturas_base = {
            -1: 297,
            158: 115,
            21: 270,
            1400: 270,
            1319: 270,
            967: 230,
            1316: 230,
            1692: 230,
        }
        altura_base = alturas_base.get(
            id_modulo,
            270,
        )
        ancho_papel = 210 if id_modulo == -1 else None
        ServicioImpresionTicket().imprimir_html_en_impresora(
            ruta_html=ruta_archivo,
            impresora=impresora,
            cantidad_partidas=cantidad_partidas,
            altura_base_mm=altura_base,
            ancho_papel_mm=ancho_papel,
        )

    def _buscar_navegador_chromium(self):
        rutas = [
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]

        for ruta in rutas:
            if os.path.isfile(ruta):
                return ruta

        return None

    def _obtener_impresora_predeterminada(self):
        try:
            if win32print:
                return win32print.GetDefaultPrinter()
        except Exception:
            return None

        return None

    def _obtener_ruta_configuracion_impresoras(self):
        base_actual = os.getcwd()
        base_servicio = os.path.dirname(os.path.abspath(__file__))
        base_capturar_documento = os.path.dirname(base_servicio)

        rutas = [
            # Ruta real tanto en código fuente como en el paquete instalado.
            os.path.join(
                base_capturar_documento,
                'herramientas',
                'imprimir_modulo',
                'impresoras.gz',
            ),
            # Posibles directorios de ejecución del EXE o del proyecto.
            os.path.join(
                base_actual,
                'capturar_documento',
                'herramientas',
                'imprimir_modulo',
                'impresoras.gz',
            ),
            os.path.join(base_actual, "herramientas", "imprimir_modulo", "impresoras.gz"),
            os.path.join(base_servicio, "herramientas", "imprimir_modulo", "impresoras.gz"),
            os.path.join(base_servicio, "..", "imprimir_modulo", "impresoras.gz"),
        ]

        for ruta in rutas:
            ruta = os.path.abspath(ruta)
            if os.path.isfile(ruta):
                return ruta

        return None

    def _obtener_directorio_uuid(self):
        return os.path.join(
            tempfile.gettempdir(),
            str(self.parametros.uuid)
        )

    def _borrar_directorio_uuid(self):
        directorio = self._obtener_directorio_uuid()

        if os.path.isdir(directorio):
            shutil.rmtree(directorio, ignore_errors=True)

    def _limpiar_parametros_impresion(self):
        self.parametros.id_modulo = 0
        self.parametros.id_principal = 0
        self.parametros.id_seleccionados = []
        self.parametros.uuid = ""
        self.parametros.impresora = ""

    @staticmethod
    def _extraer_cantidad(nombre_archivo):
        try:
            _, derecha = nombre_archivo.rsplit("(", 1)
            numero = derecha.split(")")[0]
            return int(numero)
        except Exception:
            return 1

    @staticmethod
    def _extraer_document_id(nombre_archivo):
        nombre_sin_ext = nombre_archivo.rsplit(".", 1)[0]
        ultimo = nombre_sin_ext.replace("-", "_").split("_")[-1]

        if ultimo.isdigit():
            return int(ultimo)

        return None
