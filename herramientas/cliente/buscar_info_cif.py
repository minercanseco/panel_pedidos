import time
import random
import subprocess
from urllib.parse import quote
import os
import ssl

import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings
from fuzzywuzzy import fuzz

from cayal.datos import BaseDatos
from cayal.util import Utilerias


class BuscarInfoCif:
    """
    Consulta SAT por QR (CIF+RFC), parsea XHTML/HTML con BeautifulSoup,
    mapea regímenes y actualiza la instancia de cliente.

    - SIN Tkinter (no master, no eventos, no ventanas)
    - SÍNCRONO: run() bloquea hasta terminar y regresa True/False
    - Diagnóstico: siempre genera sat_validadorqr_debug.html
      y genera sat_validadorqr_debug.txt si no detecta estructura.

    Señalización:
    - self.ok / self.done / self.error
    """

    _CACHE_HTML = {}  # (rfc, cif) -> {"ts": float, "html": str}
    _CACHE_TTL_SECONDS = 6 * 60 * 60  # 6 horas

    def __init__(self, parametros, rfc, cif, instancia_cliente):
        self._parametros = parametros
        self._rfc = (rfc or "").strip().upper()
        self._cif = (cif or "").strip().upper()
        self.cliente = instancia_cliente

        self._base_de_datos = BaseDatos()
        self._utilerias = Utilerias()

        # Estados internos
        self._regimenes_base_datos = None
        self._soup = None
        self._respuesta = None

        self._informacion_identificacion = {}
        self._informacion_ubicacion = {}
        self._regimenes_sin_filtrar = []
        self._regimenes_filtrados = []
        self._colonias_direccion = None
        self._consulta_colonias = None

        # Estado público
        self.error = None
        self.done = False
        self.ok = False

        # Debug
        self._debug_html_path = "sat_validadorqr_debug.html"
        self._debug_txt_path = "sat_validadorqr_debug.txt"

    # ----------------------------
    # API pública
    # ----------------------------
    def run(self) -> bool:
        """
        Ejecuta TODO el flujo en modo síncrono.
        Regresa True si logró obtener/parsear/aplicar información.
        """
        self.error = None
        self.done = False
        self.ok = False

        try:
            self._scrap_informacion_web()
            if not self._respuesta:
                self.ok = False
                return False

            if not self._procesar_respuesta():
                self.ok = False
                if not self.error:
                    self.error = "No se detectó estructura esperada en la respuesta del SAT."
                return False

            self._procesar_informacion()
            self.ok = True
            return True

        except Exception as e:
            self.ok = False
            self.error = str(e)
            return False

        finally:
            self.done = True

    # ----------------------------
    # URL / Cache
    # ----------------------------
    def _build_url_sat(self) -> str:
        d3 = f"{self._cif}_{self._rfc}"
        d3_enc = quote(d3, safe="")
        return (
            "https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf"
            f"?D1=10&D2=1&D3={d3_enc}"
        )

    def _get_cached_html(self):
        key = (self._rfc, self._cif)
        item = self._CACHE_HTML.get(key)
        if not item:
            return None
        ts = item.get("ts") or 0
        if (time.time() - ts) > self._CACHE_TTL_SECONDS:
            try:
                del self._CACHE_HTML[key]
            except Exception:
                pass
            return None
        return item.get("html")

    def _set_cached_html(self, html: str):
        key = (self._rfc, self._cif)
        self._CACHE_HTML[key] = {"ts": time.time(), "html": html}

    # ----------------------------
    # Transporte (requests legacy SSL + fallback curl)
    # ----------------------------
    def _scrap_informacion_web(self):
        cached = self._get_cached_html()
        if cached:
            self._respuesta = cached
            return

        url = self._build_url_sat()

        html = self._scrap_via_requests_legacy_ssl(url)

        if not self._html_usable(html):
            html2 = self._scrap_via_curl(url)
            if self._html_usable(html2):
                html = html2

        self._guardar_debug_html(html or "")

        if not self._html_usable(html):
            self._respuesta = None
            self.error = (
                "No fue posible consultar el SAT (no se obtuvo HTML/XHTML usable). "
                "Revisa sat_validadorqr_debug.html para diagnóstico."
            )
            return

        self._respuesta = html
        self._set_cached_html(html)

    def _headers(self):
        return {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://siat.sat.gob.mx/",
        }

    def _html_usable(self, html: str) -> bool:
        if not html or len(html) < 200:
            return False
        señales = (
            "Datos de Identificación",
            "Datos de Ubicación",
            "Características fiscales",
            "El RFC:",
            "validadorqr",
        )
        return any(s in html for s in señales) or (self._rfc in html)

    def _scrap_via_requests_legacy_ssl(self, url: str) -> str:
        class _LegacySSLAdapter(HTTPAdapter):
            def __init__(self, ssl_context: ssl.SSLContext, **kwargs):
                self._ssl_context = ssl_context
                super().__init__(**kwargs)

            def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
                pool_kwargs["ssl_context"] = self._ssl_context
                self.poolmanager = PoolManager(
                    num_pools=connections, maxsize=maxsize, block=block, **pool_kwargs
                )

        max_intentos = 3
        last_err = None

        try:
            ctx = ssl.create_default_context()
            # Baja el seclevel para evitar DH_KEY_TOO_SMALL en OpenSSL 3.x
            ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
        except Exception as e:
            ctx = None
            last_err = f"No se pudo crear SSLContext legacy: {e}"

        for intento in range(1, max_intentos + 1):
            try:
                s = requests.Session()
                if ctx is not None:
                    s.mount("https://", _LegacySSLAdapter(ctx))

                resp = s.get(url, headers=self._headers(), timeout=25, allow_redirects=True)
                text = resp.text or ""

                print("[SAT] requests intento:", intento,
                      "status:", resp.status_code,
                      "len:", len(text),
                      "final_url:", str(resp.url))
                return text

            except Exception as e:
                last_err = str(e)
                print("[SAT] requests error intento", intento, ":", last_err)
                if intento < max_intentos:
                    time.sleep((0.8 * intento) + random.random() * 0.6)

        print("[SAT] requests FALLA FINAL:", last_err)
        return ""

    def _scrap_via_curl(self, url: str) -> str:
        max_intentos = 3
        last_err = None
        is_windows = (os.name == "nt")

        for intento in range(1, max_intentos + 1):
            try:
                base_cmd = [
                    "curl",
                    "-L",
                    "-sS",
                    "--compressed",
                    "--max-time", "25",
                    "-A", self._headers()["User-Agent"],
                    url
                ]

                cmd_variantes = [base_cmd]
                if not is_windows:
                    cmd_variantes = [
                        ["curl", "-L", "-sS", "--compressed", "--max-time", "25",
                         "--ciphers", "DEFAULT@SECLEVEL=1",
                         "-A", self._headers()["User-Agent"], url],
                        base_cmd
                    ]

                for cmd in cmd_variantes:
                    res = subprocess.run(cmd, capture_output=True, text=True)

                    print("[SAT] curl intento:", intento,
                          "returncode:", res.returncode,
                          "stdout_len:", len(res.stdout or ""),
                          "stderr_len:", len(res.stderr or ""))

                    if res.stderr:
                        print("[SAT] curl stderr (head):", (res.stderr[:300]).replace("\n", " "))

                    if res.returncode != 0:
                        last_err = res.stderr.strip() or f"curl returncode={res.returncode}"
                        continue

                    return res.stdout or ""

                raise RuntimeError(last_err or "curl sin salida usable")

            except Exception as e:
                last_err = str(e)
                print("[SAT] curl error intento", intento, ":", last_err)
                if intento < max_intentos:
                    time.sleep((0.8 * intento) + random.random() * 0.6)

        print("[SAT] curl FALLA FINAL:", last_err)
        return ""

    # ----------------------------
    # Debug
    # ----------------------------
    def _guardar_debug_html(self, html: str):
        try:
            with open(self._debug_html_path, "w", encoding="utf-8") as f:
                f.write(html or "")
            print(f"[CIF] Se generó {self._debug_html_path} para diagnóstico.")
        except Exception as e:
            print("[CIF] No se pudo escribir debug html:", str(e))

    def _guardar_debug_txt(self, soup: BeautifulSoup):
        try:
            text = soup.get_text("\n", strip=True)
            with open(self._debug_txt_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"[CIF] Se generó {self._debug_txt_path} para diagnóstico.")
        except Exception as e:
            print("[CIF] No se pudo escribir debug txt:", str(e))

    # ----------------------------
    # Parsing robusto (XHTML/XML)
    # ----------------------------
    def _crear_soup_robusta(self, html: str) -> BeautifulSoup:
        warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

        try:
            soup = BeautifulSoup(html, "lxml-xml")
            print("[SAT] parser usado: lxml-xml")
            return soup
        except Exception:
            pass

        try:
            soup = BeautifulSoup(html, "xml")
            print("[SAT] parser usado: xml")
            return soup
        except Exception:
            pass

        soup = BeautifulSoup(html, "html.parser")
        print("[SAT] parser usado: html.parser (fallback)")
        return soup

    def _texto_normalizado(self, s: str) -> str:
        return " ".join((s or "").replace("\xa0", " ").split()).strip()

    def _contiene_texto(self, texto_completo: str, needle: str) -> bool:
        return self._texto_normalizado(needle) in self._texto_normalizado(texto_completo)

    def _procesar_respuesta(self) -> bool:
        if not self._respuesta:
            return False

        self._soup = self._crear_soup_robusta(self._respuesta)

        if not self._buscar_mensaje_de_ok():
            self._guardar_debug_txt(self._soup)
            head = (self._texto_normalizado(self._soup.get_text(" ", strip=True)) or "")[:400]
            print("[SAT] No se detectó estructura OK. Texto plano (head):", head.replace("\n", " | "))
            return False

        self._procesar_datos_identificacion()
        self._procesar_datos_ubicacion()
        self._procesar_datos_fiscales()
        self._buscar_regimenes_fiscales_base_datos()
        self._filtrar_regimenes_fiscales()
        return True

    def _buscar_mensaje_de_ok(self) -> bool:
        txt = self._soup.get_text(" ", strip=True) or ""
        return self._contiene_texto(txt, "Datos de Identificación") and self._contiene_texto(txt, "Características fiscales")

    def _find_section_anchor(self, titulo: str):
        titulo_n = self._texto_normalizado(titulo)
        for tag_name in ("li", "span", "label", "div", "td"):
            for t in self._soup.find_all(tag_name):
                if self._texto_normalizado(t.get_text(" ", strip=True)) == titulo_n:
                    return t
        return None

    def _extract_kv_from_table(self, table, keys_set):
        out = {k: "" for k in keys_set}
        if not table:
            return out

        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue
            label = self._texto_normalizado(cells[0].get_text(" ", strip=True))
            value = self._texto_normalizado(cells[1].get_text(" ", strip=True))
            if label and (label[-1] != ":") and (label + ":") in out:
                label = label + ":"
            if label in out:
                out[label] = value
        return out

    def _procesar_datos_identificacion(self):
        keys = {
            "Denominación o Razón Social:",
            "Nombre:",
            "Apellido Paterno:",
            "Apellido Materno:",
        }

        anchor = self._find_section_anchor("Datos de Identificación")
        if not anchor:
            self._informacion_identificacion = {k: "" for k in keys}
            return

        table = anchor.find_next("table")
        self._informacion_identificacion = self._extract_kv_from_table(table, keys)

    def _procesar_datos_ubicacion(self):
        keys = {
            "Entidad Federativa:",
            "Municipio o delegación:",
            "Colonia:",
            "Tipo de vialidad:",
            "Nombre de la vialidad:",
            "Número exterior:",
            "CP:",
            "Correo electrónico:",
        }

        anchor = self._find_section_anchor("Datos de Ubicación (domicilio fiscal, vigente)")
        if not anchor:
            anchor = self._find_section_anchor("Datos de Ubicación")
        if not anchor:
            self._informacion_ubicacion = {k: "" for k in keys}
            return

        table = anchor.find_next("table")
        self._informacion_ubicacion = self._extract_kv_from_table(table, keys)

    def _procesar_datos_fiscales(self):
        anchor = self._find_section_anchor("Características fiscales (vigente)")
        if not anchor:
            anchor = self._find_section_anchor("Características fiscales")
        if not anchor:
            self._regimenes_sin_filtrar = []
            return

        table = anchor.find_next("table")
        if not table:
            self._regimenes_sin_filtrar = []
            return

        regimenes = []
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) < 2:
                continue
            label = self._texto_normalizado(cells[0].get_text(" ", strip=True))
            value = self._texto_normalizado(cells[1].get_text(" ", strip=True))
            if label in ("Régimen:", "Regimen:") and value:
                regimenes.append(value)

        self._regimenes_sin_filtrar = regimenes

    # ----------------------------
    # Regímenes fiscales
    # ----------------------------
    def _buscar_regimenes_fiscales_base_datos(self):
        if self._regimenes_base_datos is None:
            consulta = self._base_de_datos.fetchall(
                "SELECT Value FROM vwcboAnexo20v40_RegimenFiscal",
                ()
            )
            self._regimenes_base_datos = [r["Value"] for r in consulta]

    @staticmethod
    def _encontrar_coincidencia(cadena, lista_cadenas):
        mejor = None
        mejor_puntaje = 0
        for candidata in (lista_cadenas or []):
            puntaje = fuzz.ratio(cadena, candidata)
            if puntaje > mejor_puntaje:
                mejor_puntaje = puntaje
                mejor = candidata
        return mejor

    def _filtrar_regimenes_fiscales(self):
        mapeados = []
        for regimen in self._regimenes_sin_filtrar:
            r = self._encontrar_coincidencia(regimen, self._regimenes_base_datos or [])
            if r:
                mapeados.append(r)

        descartados = {
            "606 - Arrendamiento",
            "616 - Sin obligaciones fiscales",
            "605 - Sueldos y Salarios e Ingresos Asimilados a Salarios",
        }
        self._regimenes_filtrados = [r for r in mapeados if r not in descartados]

    # ----------------------------
    # Aplicar info al cliente
    # ----------------------------
    def _procesar_informacion(self):
        if self._utilerias.tipo_rfc(self._rfc) == 1:
            nombre = self._informacion_identificacion.get("Nombre:", "")
            ap = self._informacion_identificacion.get("Apellido Paterno:", "")
            am = self._informacion_identificacion.get("Apellido Materno:", "")
            nombre_completo = f"{nombre} {ap} {am}".strip()
        else:
            nombre_completo = self._informacion_identificacion.get("Denominación o Razón Social:", "")

        codigo_postal = self._informacion_ubicacion.get("CP:", "")
        colonia_id = self._buscar_colonia_por_cp(codigo_postal)
        info_colonia = self._buscar_colonia_por_id(colonia_id)
        calle = self._crear_calle_cliente()

        self.cliente.address_fiscal_zip_code = codigo_postal
        self.cliente.official_name = nombre_completo
        self.cliente.email = self._informacion_ubicacion.get("Correo electrónico:", "")
        self.cliente.address_fiscal_ext_number = self._informacion_ubicacion.get("Número exterior:", "")
        self.cliente.address_fiscal_street = calle
        self.cliente.official_number = self._rfc
        self.cliente.cif = self._cif
        self.cliente.zone_name = info_colonia.get("nombre_ruta") or ""
        self.cliente.address_fiscal_city = info_colonia.get("nombre_colonia") or ""
        self.cliente.address_fiscal_municipality = info_colonia.get("municipio") or ""
        self.cliente.address_fiscal_state_province = info_colonia.get("estado") or ""
        self.cliente.company_type_names = self._regimenes_filtrados

    # ----------------------------
    # Colonias
    # ----------------------------
    def _buscar_colonia_por_id(self, colonia_id):
        info = {"nombre_ruta": None, "nombre_colonia": None, "estado": None, "municipio": None}
        if colonia_id == 0:
            return info

        consulta = self._base_de_datos.fetchall(
            """
            SELECT A.City, Z.ZoneName, A.State, A.Municipality
            FROM engRefCountryAddress A
            LEFT OUTER JOIN orgZone Z ON A.ZoneID = Z.ZoneID
            WHERE CountryAddressID = ?
            """,
            (colonia_id,)
        )

        if consulta:
            info["nombre_ruta"] = consulta[0].get("ZoneName")
            info["nombre_colonia"] = consulta[0].get("City")
            info["estado"] = consulta[0].get("State")
            info["municipio"] = consulta[0].get("Municipality")

        return info

    def _crear_calle_cliente(self):
        tipo = self._informacion_ubicacion.get("Tipo de vialidad:", "")
        nombre = self._informacion_ubicacion.get("Nombre de la vialidad:", "")
        return f"{tipo} {nombre}".strip()

    def _buscar_colonia_por_cp(self, cp):
        if not cp:
            return 0

        if self._colonias_direccion is None:
            self._consulta_colonias = self._base_de_datos.fetchall(
                """
                SELECT CountryAddressID, State, Municipality, MunicipalityCode,
                       StateCode, AutonomiaCode, CountryID, CountryCode, Pais,
                       CityCode, Autonomia, City, ZoneID
                FROM engRefCountryAddress
                WHERE ZipCode = ?
                """,
                (cp,)
            )
            self._colonias_direccion = [c["City"] for c in self._consulta_colonias]

        return self._filtrar_colonia()

    def _filtrar_colonia(self):
        colonia = self._informacion_ubicacion.get("Colonia:", "")
        if not colonia or not self._colonias_direccion:
            return 0

        colonia_filtrada = self._encontrar_coincidencia(colonia, self._colonias_direccion)
        if not colonia_filtrada:
            return 0

        for valor in self._consulta_colonias:
            if valor["City"] == colonia_filtrada:
                return valor["CountryAddressID"]
        return 0