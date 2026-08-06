import os
import re
import datetime
import platform
import tempfile
from pathlib import Path

class Ticket158:
    def __init__(self):
        self._datos = {}         # datos globales del documento (placeholders [Clave])
        self._partidas = []      # lista de dicts para el bloque <DETAIL>
        self._plantilla = None   # ruta a archivo HTML plantilla

    # ---- setters “estilo CorteDeCaja” ----
    def set_datos(self, **kwargs):
        self._datos.update(kwargs or {})

    def set_partidas(self, partidas):
        if not isinstance(partidas, list):
            raise ValueError("partidas debe ser una lista de diccionarios")
        self._partidas = partidas

    def set_plantilla(self, ruta_html):
        self._plantilla = Path(ruta_html)

    # ---- helpers internos ----
    def _leer_plantilla(self):
        if not self._plantilla:
            raise ValueError("Debes establecer la plantilla con set_plantilla(ruta_html)")
        if not self._plantilla.exists():
            raise FileNotFoundError(f"No se encontró la plantilla: {self._plantilla}")
        return self._plantilla.read_text(encoding="utf-8", errors="ignore")

    def _extraer_bloque_detalle(self, html):
        """
        Extrae el contenido entre <DETAIL> ... </DETAIL>.
        Devuelve (html_sin_detalle, bloque_detalle).
        """
        ini_tag = "<DETAIL>"
        fin_tag = "</DETAIL>"
        ini = html.find(ini_tag)
        fin = html.find(fin_tag)
        if ini == -1 or fin == -1 or fin <= ini:
            raise ValueError("No se localizó correctamente el bloque <DETAIL>...</DETAIL> en la plantilla.")
        bloque = html[ini + len(ini_tag):fin]
        html_sin = html[:ini] + "{detalle}" + html[fin + len(fin_tag):]
        return html_sin, bloque

    def _render_placeholders(self, texto, mapping):
        """
        Reemplaza todos los [Clave] por mapping.get('Clave', '').
        No falla si faltan claves.
        """
        def _repl(m):
            k = m.group(1).strip()
            v = mapping.get(k, "")
            return "" if v is None else str(v)
        return re.sub(r"\[([^\[\]]+)\]", _repl, texto)

    def _obtener_directorio_salida(self):
        sis = platform.system()
        if sis == "Windows":
            base = os.path.join(os.getenv("USERPROFILE") or "", "Documents")
        elif sis in ("Darwin", "Linux"):
            base = os.path.join(os.getenv("HOME") or "", "Documents")
        else:
            base = tempfile.gettempdir()
        if not os.path.isdir(base):
            os.makedirs(base, exist_ok=True)
        return base

    def _nombre_archivo(self):
        uuid = self._datos.get("uuid", "SIN_FOLIO")
        # limpiar nombre
        return f"{uuid}.html"

    # ---- API principal ----
    def generar_html(self):
        """
        Carga la plantilla, inserta datos globales y repite el bloque <DETAIL> para cada partida.
        Devuelve el HTML final como string.
        """
        html = self._leer_plantilla()
        html_sin, bloque = self._extraer_bloque_detalle(html)

        # 1) Render global (sustituye todos los [Clave] del documento)
        html_global = self._render_placeholders(html_sin, self._datos)

        # 2) Render detalle (una fila por partida)
        filas = []
        for p in self._partidas:
            filas.append(self._render_placeholders(bloque, p))
        detalle_html = "".join(filas)

        # 3) Insertar el detalle donde quedó el marcador
        html_final = html_global.replace("{detalle}", detalle_html)
        return html_final

    def guardar_html(self, directorio=None):
        """
        Genera y guarda el HTML en un archivo. Devuelve la ruta.
        """
        html = self.generar_html()
        base = directorio or self._obtener_directorio_salida()
        nombre = self._nombre_archivo()
        ruta = os.path.join(base, nombre)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(html)
        return ruta