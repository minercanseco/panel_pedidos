import os
import re
import platform
import tempfile
from pathlib import Path
from datetime import datetime

class CFDITicket:
    def __init__(self):
        self._datos = {}         # datos globales del documento (placeholders [Clave])
        self._partidas = []      # lista de dicts para el bloque <DETAIL>
        self._plantilla = None   # ruta a archivo HTML plantilla

    # ---------------- Setters estilo Ticket158 ----------------
    def set_datos(self, **kwargs):
        """
        Acepta claves del documento CFDI (ej. [RfcEmisor], [RfcReceptor],
        [RegimenFiscalReceptor], [UUID], [Serie], [Folio], [SubTotal], [Total], etc.)
        También puedes pasar [FechaImpresion] y [HoraImpresion]; si no, se autogeneran.
        """
        self._datos.update(kwargs or {})

    def set_partidas(self, partidas):
        """
        Lista de dicts que mapean los placeholders del bloque <DETAIL>,
        por ejemplo: [{'Cantidad': '1', 'ClaveProdServ': '01010101', ...}, ...]
        """
        if not isinstance(partidas, list):
            raise ValueError("partidas debe ser una lista de diccionarios")
        self._partidas = partidas

    def set_plantilla(self, ruta_html):
        self._plantilla = Path(ruta_html)

    def set_marca_agua(self, motivo_id=1):
        """
        Define la marca de agua del documento.
        - tipo: puede ser 'ORIGINAL', 'COPIA' o 'CANCELADO'.
          (También acepta cualquier otro texto personalizado.)
        Controla la visibilidad del bloque <!--IF_COPIA-->…<!--END_IF_COPIA-->
        y llena [TextoMarcaAgua] según corresponda.
        """
        if motivo_id == 1:
            self._datos['ES_COPIA'] = True
            self._datos['TextoMarcaAgua'] = "ORIGINAL"

        elif motivo_id == 2:
            self._datos['ES_COPIA'] = True
            self._datos['TextoMarcaAgua'] = "CANCELADO"

        elif motivo_id == 3:
            self._datos['ES_COPIA'] = True
            self._datos['TextoMarcaAgua'] = "REIMPRESO"

        elif motivo_id == 5:
            self._datos['ES_COPIA'] = True
            self._datos['TextoMarcaAgua'] = " "

        else:
            self._datos['ES_COPIA'] = True
            self._datos['TextoMarcaAgua'] = "COPIA"

    # ---------------- Helpers internos ----------------
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
        Reemplaza todos los [Clave] con mapping.get('Clave','').
        """
        def _repl(m):
            k = m.group(1).strip()
            v = mapping.get(k, "")
            return "" if v is None else str(v)
        return re.sub(r"\[([^\[\]]+)\]", _repl, texto)

    def _aplicar_condicional_copia(self, html):
        es_copia = bool(self._datos.get('ES_COPIA', False))
        if not es_copia:
            # Eliminar bloque condicional por completo
            return re.sub(r"<!--IF_COPIA-->.*?<!--END_IF_COPIA-->\s*", "", html, flags=re.DOTALL)
        # Si es copia, asegurar texto por defecto si no se definió
        if not self._datos.get('TextoMarcaAgua'):
            html = html.replace("[TextoMarcaAgua]", "COPIA")
        return html

    def _autocompletar_impresion(self):
        """
        Si no vienen en _datos, llena [FechaImpresion] y [HoraImpresion]
        con la fecha/hora actuales (locales).
        Formatos: YYYY-MM-DD y HH:MM (24h).
        """
        ahora = datetime.now()
        self._datos.setdefault("FechaImpresion", ahora.strftime("%Y-%m-%d"))
        self._datos.setdefault("HoraImpresion",  ahora.strftime("%H:%M"))

    def obtener_directorio_salida(self, temporal=False, uuid=None):
        """
        Igual que en Ticket158:
        - temporal=True  -> carpeta temporal del sistema
        - temporal=False -> ~/Documents (o ~/Documentos en Linux)
        Crea el directorio si no existe. Si se pasa uuid, crea subcarpeta.
        """
        base_dir = None
        if temporal:
            base_dir = tempfile.gettempdir()
            if uuid:
                base_dir = os.path.join(base_dir, str(uuid))
        else:
            sistema = platform.system()
            home = os.path.expanduser("~")
            if sistema in ("Windows", "Darwin"):
                base_dir = os.path.join(home, "Documents")
            else:
                posibles = [os.path.join(home, "Documents"), os.path.join(home, "Documentos")]
                base_dir = next((ruta for ruta in posibles if os.path.exists(ruta)), posibles[0])
            if uuid:
                base_dir = os.path.join(base_dir, str(uuid))
        try:
            os.makedirs(base_dir, exist_ok=True)
        except Exception:
            fallback = os.path.join(tempfile.gettempdir(), str(uuid or "CFDITicket"))
            os.makedirs(fallback, exist_ok=True)
            base_dir = fallback
        return base_dir

    def nombre_archivo(self):
        """
        Genera nombre preferente con UUID; si no hay, usa Serie+Folio; en último caso, CFDI.html
        """
        print(self._datos)
        uuid = (self._datos.get("uuid") or self._datos.get("UUID") or "").strip()
        if uuid:
            return f"{uuid}.html"
        serie = (self._datos.get("Serie") or "").strip()
        folio = (self._datos.get("Folio") or "").strip()
        if serie or folio:
            return f"{serie}{folio or 'SIN_FOLIO'}.html"
        return "CFDI.html"

    # ---------------- API principal ----------------
    def generar_html(self):
        """
        Carga plantilla, inserta datos globales y repite <DETAIL> por partida.
        Maneja bloque condicional de COPIA y autocompleta [FechaImpresion]/[HoraImpresion].
        Devuelve el HTML final.
        """
        # Asegurar datos de impresión si no vinieron
        self._autocompletar_impresion()

        html = self._leer_plantilla()
        html_sin, bloque = self._extraer_bloque_detalle(html)

        # Si ES_COPIA viene activo y no pusieron texto, define uno por defecto
        if self._datos.get('ES_COPIA', False) and not self._datos.get('TextoMarcaAgua'):
            self._datos['TextoMarcaAgua'] = "COPIA"

        # 1) Render global
        html_global = self._render_placeholders(html_sin, self._datos)

        # 2) Render detalle
        filas = []
        for p in self._partidas:
            filas.append(self._render_placeholders(bloque, p))
        detalle_html = "".join(filas)

        # 3) Insertar detalle
        html_final = html_global.replace("{detalle}", detalle_html)

        # 4) Condicional COPIA
        html_final = self._aplicar_condicional_copia(html_final)

        return html_final

    def guardar_html(self, directorio=None, temporal=False, uuid=None):
        """
        Genera y guarda el HTML.
        - Si directorio es None, usa _obtener_directorio_salida(temporal, uuid).
        Devuelve la ruta del archivo escrito.
        """
        html = self.generar_html()
        base = directorio or self.obtener_directorio_salida(temporal=temporal, uuid=uuid or self._datos.get("uuid"))
        nombre = self.nombre_archivo()
        ruta = os.path.join(base, nombre)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(html)
        return ruta