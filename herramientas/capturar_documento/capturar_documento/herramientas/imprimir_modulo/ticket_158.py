import os
import re
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

    def set_copia(self, es_copia=True, texto="COPIA"):
        """
        Activa/desactiva la marca de agua de 'COPIA' en el ticket.
        - es_copia=True mostrará el bloque IF_COPIA.
        - texto define el contenido del placeholder [TextoMarcaAgua].
        """
        self._datos['ES_COPIA'] = bool(es_copia)
        # Solo define un valor por defecto si no lo han pasado antes
        if texto and not self._datos.get('TextoMarcaAgua'):
            self._datos['TextoMarcaAgua'] = str(texto)

    def _aplicar_condicional_copia(self, html):
        """
        Si ES_COPIA es falso o no está definido, elimina el bloque <!--IF_COPIA-->...<!--END_IF_COPIA--> del HTML.
        Si ES_COPIA es verdadero, deja el bloque y garantiza un valor por defecto para [TextoMarcaAgua].
        """
        es_copia = bool(self._datos.get('ES_COPIA', False))

        if not es_copia:
            # Eliminar por completo la sección condicional de COPIA
            return re.sub(r"<!--IF_COPIA-->.*?<!--END_IF_COPIA-->\s*", "", html, flags=re.DOTALL)

        # Si sí es copia, asegurar texto por defecto si no se definió
        if not self._datos.get('TextoMarcaAgua'):
            # Renderiza solo ese placeholder sin re-render global
            html = html.replace("[TextoMarcaAgua]", "COPIA")
        return html

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

    def _obtener_directorio_salida(self, temporal=False, uuid=None):
        """
        Devuelve la ruta al directorio de documentos del usuario.
        Si temporal=True → devuelve la carpeta temporal del sistema.
        Si uuid se proporciona, se crea/subcarpeta dentro del directorio.
        Crea el directorio si no existe.
        """
        base_dir = None

        # --- Carpeta temporal ---
        if temporal:
            base_dir = tempfile.gettempdir()
            if uuid:
                base_dir = os.path.join(base_dir, str(uuid))
        else:
            sistema = platform.system()
            home = os.path.expanduser("~")

            # Windows y macOS → ~/Documents
            if sistema in ("Windows", "Darwin"):
                base_dir = os.path.join(home, "Documents")
            else:
                # Linux u otros: Documents o Documentos
                posibles = [
                    os.path.join(home, "Documents"),
                    os.path.join(home, "Documentos")
                ]
                base_dir = next((ruta for ruta in posibles if os.path.exists(ruta)), posibles[0])

            # Si se especificó un UUID → subcarpeta
            if uuid:
                base_dir = os.path.join(base_dir, str(uuid))

        # --- Crear directorio si no existe ---
        try:
            os.makedirs(base_dir, exist_ok=True)
        except Exception as e:
            # fallback: carpeta temporal si falla
            fallback = os.path.join(tempfile.gettempdir(), str(uuid or "Ticket158"))
            os.makedirs(fallback, exist_ok=True)
            base_dir = fallback

        return base_dir

    def _nombre_archivo(self):
        uuid = self._datos.get("uuid", "SIN_FOLIO")
        # limpiar nombre
        return f"{uuid}.html"

    # ---- API principal ----
    def generar_html(self):
        """
        Carga la plantilla, inserta datos globales y repite el bloque <DETAIL> para cada partida.
        Aplica la lógica condicional de COPIA (marca de agua).
        Devuelve el HTML final como string.
        """
        html = self._leer_plantilla()
        html_sin, bloque = self._extraer_bloque_detalle(html)

        # Asegura valor por defecto para texto de marca si el flag viene activo
        if self._datos.get('ES_COPIA', False) and not self._datos.get('TextoMarcaAgua'):
            self._datos['TextoMarcaAgua'] = "COPIA"

        # 1) Render global (sustituye todos los [Clave] del documento)
        html_global = self._render_placeholders(html_sin, self._datos)

        # 2) Render detalle (una fila por partida)
        filas = []
        for p in self._partidas:
            filas.append(self._render_placeholders(bloque, p))
        detalle_html = "".join(filas)

        # 3) Insertar el detalle donde quedó el marcador
        html_final = html_global.replace("{detalle}", detalle_html)

        # 4) Aplicar bloque condicional de COPIA
        html_final = self._aplicar_condicional_copia(html_final)

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