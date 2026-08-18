class Consignacion:
    """
    Generador de HTML para Formato de Consigna, usando una plantilla con:
      - Bloque <DETAIL>...</DETAIL> para las partidas.
      - Bloque condicional de marca de agua:
            <!--IF_COPIA--> ... <!--END_IF_COPIA-->
      - Bloque condicional para precios:
            <!--IF_MOSTRAR_PRECIOS--> ... <!--END_IF_MOSTRAR_PRECIOS-->
      - Bloque condicional para descuento:
            <!--IF_DESCUENTO--> ... <!--END_IF_DESCUENTO-->
    Los placeholders son del estilo [Clave].
    """

    def __init__(self):
        self._datos = {}       # Placeholders globales
        self._partidas = []    # Lista de dicts para <DETAIL>
        self._plantilla = None # Path a la plantilla HTML

    # ---------------- Setters públicos ----------------

    def set_datos(self, **kwargs):
        """
        Acepta claves del documento de consigna:
        Ej: [EmisorNombre], [EmisorRFC], [Cliente], [Fecha], [Total], etc.
        También puede recibir [FechaImpresion] y [HoraImpresion]; si no, se autogeneran.
        """
        self._datos.update(kwargs or {})

    def set_partidas(self, partidas):
        """
        Lista de dicts que mapean los placeholders del bloque <DETAIL>,
        por ejemplo:
          [{'Clave': '001', 'Descripcion': 'Producto X', 'Cantidad': '10',
            'PrecioUnitario': '100.00', 'Importe': '1000.00'}, ...]
        """
        if not isinstance(partidas, list):
            raise ValueError("partidas debe ser una lista de diccionarios")
        self._partidas = partidas

    def set_plantilla(self, ruta_html):
        """
        Establece la ruta a la plantilla HTML de consigna.
        """
        from pathlib import Path
        self._plantilla = Path(ruta_html)

    def set_marca_agua(self, motivo_id=1):
        """
        Define la marca de agua del documento de consigna.
          motivo_id:
            1 -> ORIGINAL
            2 -> CANCELADO
            otro -> COPIA

        Usa:
          [TextoMarcaAgua]
        y bloque:
          <!--IF_COPIA--> ... <!--END_IF_COPIA-->
        """
        self._datos['ES_COPIA'] = True
        if motivo_id == 1:
            self._datos['TextoMarcaAgua'] = "ORIGINAL"
        elif motivo_id == 2:
            self._datos['TextoMarcaAgua'] = "CANCELADO"
        elif motivo_id == 3:
            self._datos['TextoMarcaAgua'] = "REIMPRESO"
        else:
            self._datos['TextoMarcaAgua'] = "COPIA"

    def set_mostrar_precios(self, mostrar=True):
        """
        Controla el bloque <!--IF_MOSTRAR_PRECIOS-->.
          mostrar=True  -> se muestran columnas y totales
          mostrar=False -> se ocultan precios/importe/totales
        """
        self._datos["MOSTRAR_PRECIOS"] = bool(mostrar)

    def set_descuento_activo(self, activo=True):
        """
        Permite forzar la visibilidad del bloque <!--IF_DESCUENTO-->.
        Si no se establece, se inferirá a partir de 'DescuentoCayal'.
        """
        self._datos["MOSTRAR_DESCUENTO"] = bool(activo)

    # ---------------- Helpers internos de plantilla ----------------

    def _leer_plantilla(self):
        if not self._plantilla:
            raise ValueError("Debes establecer la plantilla con set_plantilla(ruta_html)")
        if not self._plantilla.exists():
            raise FileNotFoundError("No se encontró la plantilla: {0}".format(self._plantilla))
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
        Reemplaza todos los [Clave] usando mapping.get('Clave', '').
        """
        import re

        def _repl(m):
            k = m.group(1).strip()
            v = mapping.get(k, "")
            return "" if v is None else str(v)

        return re.sub(r"\[([^\[\]]+)\]", _repl, texto)

    # ---------------- Bloques condicionales ----------------

    def _aplicar_condicional_copia(self, html):
        """
        Maneja el bloque <!--IF_COPIA--> ... <!--END_IF_COPIA-->.
        Si ES_COPIA es False, elimina el bloque completo.
        Si ES_COPIA es True y no hay TextoMarcaAgua, usa "COPIA" por defecto.
        """
        import re

        es_copia = bool(self._datos.get('ES_COPIA', False))
        if not es_copia:
            # Eliminar todo el bloque de copia
            return re.sub(r"<!--IF_COPIA-->.*?<!--END_IF_COPIA-->\s*", "", html, flags=re.DOTALL)

        # Si es copia, asegurar texto por defecto si no se definió
        if not self._datos.get('TextoMarcaAgua'):
            html = html.replace("[TextoMarcaAgua]", "COPIA")
        return html

    def _aplicar_condicional_generico(self, html, nombre_bloque, activo):
        """
        Aplica un bloque condicional genérico:
          <!--IF_NOMBRE--> ... <!--END_IF_NOMBRE-->
        Si activo=True  -> conserva el contenido interno y quita las marcas.
        Si activo=False -> elimina todo el bloque.
        """
        import re

        patron = r"<!--IF_{0}-->(.*?)<!--END_IF_{0}-->".format(nombre_bloque)

        def _repl(m):
            return m.group(1) if activo else ""

        return re.sub(patron, _repl, html, flags=re.DOTALL)

    def _preparar_flags_condicionales(self):
        """
        - MOSTRAR_PRECIOS: por defecto True.
        - MOSTRAR_DESCUENTO: si no viene, se infiere a partir de 'DescuentoCayal'.
        """
        self._datos.setdefault("MOSTRAR_PRECIOS", True)

        if "MOSTRAR_DESCUENTO" not in self._datos:
            try:
                desc = self._datos.get("DescuentoCayal", 0) or 0
                val = float(str(desc).replace(",", ""))  # por si viene '1,234.50'
                self._datos["MOSTRAR_DESCUENTO"] = (abs(val) > 0.000001)
            except Exception:
                self._datos["MOSTRAR_DESCUENTO"] = False

    def _aplicar_condicionales_consignacion(self, html):
        """
        Aplica los condicionales propios:
          - <!--IF_MOSTRAR_PRECIOS--> ... <!--END_IF_MOSTRAR_PRECIOS-->
          - <!--IF_DESCUENTO--> ... <!--END_IF_DESCUENTO-->
        """
        mostrar_precios = bool(self._datos.get("MOSTRAR_PRECIOS", True))
        mostrar_desc = bool(self._datos.get("MOSTRAR_DESCUENTO", False))

        # Bloque de precios
        html = self._aplicar_condicional_generico(html, "MOSTRAR_PRECIOS", mostrar_precios)
        # Bloque de descuento
        html = self._aplicar_condicional_generico(html, "DESCUENTO", mostrar_desc)

        return html

    # ---------------- Helpers generales ----------------

    def _autocompletar_impresion(self):
        """
        Si no vienen en _datos, llena [FechaImpresion] y [HoraImpresion]
        con la fecha/hora actuales (locales).
        Formatos: YYYY-MM-DD y HH:MM (24h).
        """
        from datetime import datetime
        ahora = datetime.now()
        self._datos.setdefault("FechaImpresion", ahora.strftime("%Y-%m-%d"))
        self._datos.setdefault("HoraImpresion",  ahora.strftime("%H:%M"))

    def _set_titulo(self, titulo):
        self._datos.setdefault('TituloFormato', titulo)

    def _obtener_directorio_salida(self, temporal=False, uuid=None):
        """
        - temporal=True  -> carpeta temporal del sistema (con subcarpeta uuid si se da).
        - temporal=False -> ~/Documents (o ~/Documentos en Linux) con subcarpeta uuid si se da.
        """
        import os
        import platform
        import tempfile

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
            fallback = os.path.join(tempfile.gettempdir(), str(uuid or "Consignacion"))
            os.makedirs(fallback, exist_ok=True)
            base_dir = fallback
        return base_dir

    def _nombre_archivo(self):
        """
        Genera nombre preferente con UUID; si no hay, usa Serie+Folio; en último caso, CONSIGNA.html
        Placeholders esperados:
          [uuid] o [UUID] (para nombre directo)
          [Serie], [Folio]
        """
        uuid = (self._datos.get("uuid") or self._datos.get("UUID") or "").strip()
        if uuid:
            return "{0}.html".format(uuid)
        serie = (self._datos.get("Serie") or "").strip()
        folio = (self._datos.get("Folio") or "").strip()
        if serie or folio:
            return "{0}{1}.html".format(serie, folio or "SIN_FOLIO")
        return "CONSIGNA.html"

    # ---------------- API principal ----------------

    def generar_html(self):
        """
        Carga la plantilla, inserta datos globales, repite el bloque <DETAIL> por partida
        y aplica los bloques condicionales:
          - Marca de agua / copia
          - Mostrar / ocultar precios
          - Mostrar / ocultar descuento
        Devuelve el HTML final como string.
        """
        # 1) Asegurar datos de impresión
        self._autocompletar_impresion()

        # 2) Preparar flags de condicionales
        self._preparar_flags_condicionales()

        # 3) Leer plantilla y separar bloque de detalle
        html = self._leer_plantilla()
        html_sin, bloque = self._extraer_bloque_detalle(html)

        # 4) Si viene ES_COPIA activo y no hay texto de marca de agua, define uno por defecto
        if self._datos.get('ES_COPIA', False) and not self._datos.get('TextoMarcaAgua'):
            self._datos['TextoMarcaAgua'] = "COPIA"

        # 5) Render global
        html_global = self._render_placeholders(html_sin, self._datos)

        # 6) Render de cada partida dentro de <DETAIL>
        filas = []
        for p in self._partidas:
            filas.append(self._render_placeholders(bloque, p))
        detalle_html = "".join(filas)

        # 7) Insertar detalle
        html_final = html_global.replace("{detalle}", detalle_html)

        # 8) Aplicar condicionales propios de consigna (precios, descuento)
        html_final = self._aplicar_condicionales_consignacion(html_final)

        # 9) Aplicar condicional de copia / marca de agua
        html_final = self._aplicar_condicional_copia(html_final)

        return html_final

    def guardar_html(self, directorio=None, temporal=False, uuid=None):
        """
        Genera y guarda el HTML en disco.
          - Si directorio es None, usa _obtener_directorio_salida(temporal, uuid).
        Devuelve la ruta del archivo escrito.
        """
        import os

        html = self.generar_html()
        base = directorio or self._obtener_directorio_salida(
            temporal=temporal,
            uuid=uuid or self._datos.get("uuid")
        )
        nombre = self._nombre_archivo()
        ruta = os.path.join(base, nombre)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(html)
        return ruta