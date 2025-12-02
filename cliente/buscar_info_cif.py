import threading
import tkinter as tk

import ttkbootstrap as ttk
from ttkbootstrap import dialogs
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from fuzzywuzzy import fuzz

from cayal.datos import BaseDatos
from cayal.util import Utilerias
from cayal.ventanas import Ventanas


class BuscarInfoCif:
    """
    Clase encargada de:
      - Consultar información de CIF/RFC en el portal del SAT.
      - Parsear el HTML con BeautifulSoup.
      - Armar los datos de identificación, ubicación y regímenes.
      - Volcar esos datos en la instancia de cliente recibida.
      - Mostrar una ventana con barra de progreso mientras se realiza el proceso.
    """

    def __init__(self, master, parametros, rfc, cif, instancia_cliente):
        self._master = master
        self._parametros = parametros
        self._rfc = (rfc or "").strip().upper()
        self._cif = (cif or "").strip().upper()
        self.cliente = instancia_cliente

        self._base_de_datos = BaseDatos(self._parametros.cadena_conexion)
        self._utilerias = Utilerias()
        self._ventanas = Ventanas(self._master)

        # Estados internos / cachés
        self._regimenes_base_datos = None
        self._soup = None
        self._respuesta = None

        self._informacion_identificacion = {}
        self._informacion_ubicacion = {}
        self._regimenes_sin_filtrar = []
        self._regimenes_filtrados = []
        self._colonias_direccion = None
        self._consulta_colonias = None

        # Componentes UI
        self._componentes_forma = {}
        self._crear_ui()

    # ----------------------------------------------------------------------
    # UI y flujo principal
    # ----------------------------------------------------------------------
    def _crear_ui(self):
        """Crea la ventana mínima con la barra de progreso y arranca el flujo."""
        frame_principal = ttk.Labelframe(master=self._master, text='Buscando información:')
        frame_principal.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)

        barra_progreso = ttk.Progressbar(
            master=frame_principal,
            bootstyle="danger-striped",
            length=142,
            mode='indeterminate'
        )
        barra_progreso.grid(row=0, column=0, pady=5, padx=5)

        self._componentes_forma['barra_progreso'] = barra_progreso

        # Configurar ventana
        self._ventanas.configurar_ventana_ttkbootstrap("Buscar", "163x55")

        # Usamos el master "real" como padre para diálogos
        self._parent = self._utilerias.obtener_master(barra_progreso)

        # Arrancar barra y scraping en segundo plano
        self._master.after(0, self._iniciar_busqueda_async)

    def _iniciar_busqueda_async(self):
        """Inicia la barra en el hilo principal y lanza el scraping en un hilo aparte."""
        barra_progreso = self._componentes_forma['barra_progreso']
        barra_progreso.start()

        hilo = threading.Thread(target=self._buscar_informacion_web, daemon=True)
        hilo.start()

    def _buscar_informacion_web(self):
        """Hilo en segundo plano que hace el scraping y luego agenda el procesamiento."""
        self._scrap_informacion_web()
        # Ejecutar procesamiento en el hilo principal de Tk
        self._master.after(0, self._procesar_informacion_and_destroy)

    # ----------------------------------------------------------------------
    # Web scraping y parsing
    # ----------------------------------------------------------------------
    def _scrap_informacion_web(self):
        """Obtiene el HTML desde el validador del SAT usando Selenium."""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')

        driver = webdriver.Chrome(options=chrome_options)

        url = (
            "https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf"
            f"?D1=10&D2=1&D3={self._cif}_{self._rfc}"
        )

        try:
            driver.get(url)
            driver.implicitly_wait(1)  # pequeño tiempo de espera
            self._respuesta = driver.page_source

        except WebDriverException as e:
            error_message = str(e)
            # Importante: mostrar el error en el hilo principal
            self._master.after(
                0,
                lambda: dialogs.Messagebox.show_error(
                    parent=self._parent,
                    message=f'Ocurrió un error al consultar el SAT:\n{error_message}'
                )
            )
            self._respuesta = None
        finally:
            driver.quit()

    def _procesar_respuesta(self):
        """Valida y procesa la respuesta HTML: identificación, ubicación, regímenes."""
        if not self._respuesta:
            return False

        self._soup = BeautifulSoup(self._respuesta, 'html.parser')

        if not self._buscar_mensaje_de_ok():
            dialogs.Messagebox.show_error(
                parent=self._parent,
                message='No se encontró información. Favor de validar el RFC y el CIF.'
            )
            return False

        # Procesar secciones
        self._procesar_datos_identificacion()
        self._procesar_datos_ubicacion()
        self._procesar_datos_fiscales()
        self._buscar_regimenes_fiscales_base_datos()
        self._filtrar_regimenes_fiscales()
        return True

    def _buscar_mensaje_de_ok(self):
        """Verifica que la página tenga el mensaje de éxito esperado."""
        mensaje_ok = f'El RFC: {self._rfc}, tiene asociada la siguiente información.'
        mensaje_element = self._soup.find(string=mensaje_ok)
        return bool(mensaje_element)

    def _procesar_datos_identificacion(self):
        info_identificacion = {
            'Denominación o Razón Social:': '',
            'Nombre:': '',
            'Apellido Paterno:': '',
            'Apellido Materno:': '',
        }

        datos_identificacion = self._soup.find('li', string='Datos de Identificación')
        if not datos_identificacion:
            self._informacion_identificacion = info_identificacion
            return

        table_identificacion = datos_identificacion.find_next('table')
        if not table_identificacion:
            self._informacion_identificacion = info_identificacion
            return

        for row in table_identificacion.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) != 2:
                continue
            label = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)
            if label in info_identificacion:
                info_identificacion[label] = value

        self._informacion_identificacion = info_identificacion

    def _procesar_datos_ubicacion(self):
        info_ubicacion = {
            'Entidad Federativa:': '',
            'Municipio o delegación:': '',
            'Colonia:': '',
            'Tipo de vialidad:': '',
            'Nombre de la vialidad:': '',
            'Número exterior:': '',
            'CP:': '',
            'Correo electrónico:': '',
        }

        datos_ubicacion = self._soup.find(
            'li',
            string='Datos de Ubicación (domicilio fiscal, vigente)'
        )
        if not datos_ubicacion:
            self._informacion_ubicacion = info_ubicacion
            return

        table_ubicacion = datos_ubicacion.find_next('table')
        if not table_ubicacion:
            self._informacion_ubicacion = info_ubicacion
            return

        for row in table_ubicacion.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) != 2:
                continue
            label = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)
            if label in info_ubicacion:
                info_ubicacion[label] = value

        self._informacion_ubicacion = info_ubicacion

    def _procesar_datos_fiscales(self):
        caracteristicas_fiscales = self._soup.find(
            'li',
            string='Características fiscales (vigente)'
        )
        if not caracteristicas_fiscales:
            self._regimenes_sin_filtrar = []
            return

        table_caracteristicas = caracteristicas_fiscales.find_next('table')
        if not table_caracteristicas:
            self._regimenes_sin_filtrar = []
            return

        regimenes = []
        for row in table_caracteristicas.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) != 2:
                continue
            label = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)
            if label == 'Régimen:':
                regimenes.append(value)

        self._regimenes_sin_filtrar = regimenes

    # ----------------------------------------------------------------------
    # Regímenes fiscales y fuzzy matching
    # ----------------------------------------------------------------------
    def _buscar_regimenes_fiscales_base_datos(self):
        if self._regimenes_base_datos is None:
            consulta = self._base_de_datos.fetchall(
                'SELECT Value FROM vwcboAnexo20v40_RegimenFiscal',
                ()
            )
            self._regimenes_base_datos = [regimen['Value'] for regimen in consulta]

    @staticmethod
    def _encontrar_coincidencia(cadena, lista_cadenas):
        mejor_coincidencia = None
        mejor_puntaje = 0

        for candidata in lista_cadenas:
            puntaje = fuzz.ratio(cadena, candidata)
            if puntaje > mejor_puntaje:
                mejor_puntaje = puntaje
                mejor_coincidencia = candidata

        return mejor_coincidencia

    def _filtrar_regimenes_fiscales(self):
        regimenes_mapeados = []
        for regimen in self._regimenes_sin_filtrar:
            regimen_filtrado = self._encontrar_coincidencia(
                regimen,
                self._regimenes_base_datos or []
            )
            if regimen_filtrado:
                regimenes_mapeados.append(regimen_filtrado)

        regimenes_descartados = [
            '606 - Arrendamiento',
            '616 - Sin obligaciones fiscales',
            '605 - Sueldos y Salarios e Ingresos Asimilados a Salarios',
        ]

        self._regimenes_filtrados = [
            regimen for regimen in regimenes_mapeados
            if regimen not in regimenes_descartados
        ]

    # ----------------------------------------------------------------------
    # Aplicar información al cliente
    # ----------------------------------------------------------------------
    def _procesar_informacion(self):
        # Nombre / razón social según tipo de RFC
        if self._utilerias.tipo_rfc(self._rfc) == 1:
            # Persona física
            nombre = self._informacion_identificacion.get('Nombre:', '')
            apellido_paterno = self._informacion_identificacion.get('Apellido Paterno:', '')
            apellido_materno = self._informacion_identificacion.get('Apellido Materno:', '')
            nombre_completo = f'{nombre} {apellido_paterno} {apellido_materno}'.strip()
        else:
            # Persona moral
            nombre_completo = self._informacion_identificacion.get(
                'Denominación o Razón Social:',
                ''
            )

        codigo_postal = self._informacion_ubicacion.get('CP:', '')
        colonia_id = self._buscar_colonia_por_cp(codigo_postal)
        info_colonia = self._buscar_colonia_por_id(colonia_id)
        calle = self._crear_calle_cliente()

        self.cliente.address_fiscal_zip_code = codigo_postal
        self.cliente.official_name = nombre_completo
        self.cliente.email = self._informacion_ubicacion.get('Correo electrónico:', '')
        self.cliente.address_fiscal_ext_number = self._informacion_ubicacion.get('Número exterior:', '')
        self.cliente.address_fiscal_street = calle
        self.cliente.official_number = self._rfc
        self.cliente.cif = self._cif
        self.cliente.zone_name = info_colonia.get('nombre_ruta') or ''
        self.cliente.address_fiscal_city = info_colonia.get('nombre_colonia') or ''
        self.cliente.address_fiscal_municipality = info_colonia.get('municipio') or ''
        self.cliente.address_fiscal_state_province = info_colonia.get('estado') or ''
        self.cliente.company_type_names = self._regimenes_filtrados

    # ----------------------------------------------------------------------
    # Búsqueda y mapeo de colonia
    # ----------------------------------------------------------------------
    def _buscar_colonia_por_id(self, colonia_id):
        info_colonia = {
            'nombre_ruta': None,
            'nombre_colonia': None,
            'estado': None,
            'municipio': None,
        }

        if colonia_id == 0:
            return info_colonia

        consulta = self._base_de_datos.fetchall(
            """
            SELECT A.City, Z.ZoneName, A.State, A.Municipality
            FROM engRefCountryAddress A
            LEFT OUTER JOIN orgZone Z ON A.ZoneID = Z.ZoneID
            WHERE CountryAddressID = ?
            """,
            (colonia_id,)   # <-- CORREGIDO: debe ser tupla
        )

        if consulta:
            info_colonia['nombre_ruta'] = consulta[0].get('ZoneName')
            info_colonia['nombre_colonia'] = consulta[0].get('City')
            info_colonia['estado'] = consulta[0].get('State')
            info_colonia['municipio'] = consulta[0].get('Municipality')

        return info_colonia

    def _crear_calle_cliente(self):
        tipo_vialidad = self._informacion_ubicacion.get('Tipo de vialidad:', '')
        nombre_vialidad = self._informacion_ubicacion.get('Nombre de la vialidad:', '')
        return f'{tipo_vialidad} {nombre_vialidad}'.strip()

    def _buscar_colonia_por_cp(self, cp):
        """
        Carga las colonias del CP si aún no se han cargado
        y devuelve el CountryAddressID de la colonia que mejor coincida.
        """
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
            self._colonias_direccion = [colonia['City'] for colonia in self._consulta_colonias]

        return self._filtrar_colonia()

    def _filtrar_colonia(self):
        colonia = self._informacion_ubicacion.get('Colonia:', '')
        if not colonia or not self._colonias_direccion:
            return 0

        colonia_filtrada = self._encontrar_coincidencia(colonia, self._colonias_direccion)
        if not colonia_filtrada:
            return 0

        for valor in self._consulta_colonias:
            if valor['City'] == colonia_filtrada:
                return valor['CountryAddressID']

        return 0

    # ----------------------------------------------------------------------
    # Cierre de flujo
    # ----------------------------------------------------------------------
    def _procesar_informacion_and_destroy(self):
        """Procesa la respuesta (si es válida) y cierra la ventana."""
        if self._procesar_respuesta():
            self._procesar_informacion()
        self._master.destroy()