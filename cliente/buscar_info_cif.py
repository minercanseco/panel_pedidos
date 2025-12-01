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
    def __init__(self, master, parametros, rfc, cif, instancia_cliente):

        self._parametros = parametros
        self._base_de_datos = BaseDatos(self._parametros.cadena_conexion)
        self._utilerias = Utilerias()

        self._regimenes_base_datos = None
        self._soup = None
        self._respuesta = None
        self._informacion_identificacion = {}
        self._informacion_ubicacion = {}
        self._regimenes_sin_filtrar = []
        self._regimenes_filtrados = []
        self._colonias_direccion = None
        self._consulta_colonias = None

        self._rfc = rfc
        self._cif = cif

        self.informacion_captura = {}
        self.cliente = instancia_cliente

        self._master = master
        self._ventanas = Ventanas(self._master)

        self._componentes_forma = {}
        self.inicializar_componentes_forma()
        self._ventanas.configurar_ventana_ttkbootstrap("Buscar", "163x55")

        self._parent = self._utilerias.obtener_master(self._componentes_forma['barra_progreso'])

    def inicializar_componentes_forma(self):
        frame_principal = ttk.LabelFrame(master=self._master, text='Buscando información:')
        frame_principal.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)

        barra_progreso = ttk.Progressbar(master=frame_principal, bootstyle="danger-striped", length=142,
                                              mode='indeterminate')
        barra_progreso.grid(row=0, column=0, pady=5, padx=5)

        self._componentes_forma['barra_progreso'] = barra_progreso

        # Iniciar el temporizador de 0 segundos
        timer_thread = threading.Timer(0, self._buscar_informacion_web)
        timer_thread.daemon = True  # Marcar el hilo como daemon
        timer_thread.start()

    def _scrap_informacion_web(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Ejecuta en modo headless
        chrome_options.add_argument('--disable-gpu')  # Deshabilita la aceleración de gráficos

        # Crea una instancia del navegador en modo headless
        driver = webdriver.Chrome(options=chrome_options)

        # Abre la URL
        url = f'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={self._cif}_{self._rfc}'
        driver.get(url)

        try:
            # Espera a que la página cargue y ejecute JavaScript
            driver.implicitly_wait(1)  # Espera hasta 10 segundos para que se ejecuten scripts

            # Obtiene la respuesta del navegador después de ejecutar JavaScript
            self._respuesta = driver.page_source

        except WebDriverException as e:
            # Manejo de excepción en caso de error al cargar la página
            error_message = str(e)
            dialogs.Messagebox.show_error(
                parent=self._parent, message=f'Ocurrió un error: {error_message}')
            self._master.destroy()
        finally:
            # Cierra el navegador
            driver.quit()

    def _procesar_respuesta(self):
        # crea un objeto BeautifulSoup para procesar el HTML
        self._soup = BeautifulSoup(self._respuesta, 'html.parser')

        if not self._buscar_mensaje_de_ok():
            dialogs.Messagebox.show_error(
                parent=self._parent, message='No se encontró información favor de validar el RFC y el CIF')
            return False
        else:
            self._procesar_datos_identificacion()
            self._procesar_datos_ubicacion()
            self._procesar_datos_fiscales()
            self._buscar_regimenes_fiscales_base_datos()
            self._filtrar_regimenes_fiscales()
            return True

    def _buscar_mensaje_de_ok(self):
        # Busca el elemento que contiene el mensaje de error en el objeto self.soup
        mensaje_ok = f'El RFC: {self._rfc}, tiene asociada la siguiente información.'
        mensaje_element = self._soup.find(string=mensaje_ok)
        return True if mensaje_element else False

    def _procesar_datos_identificacion(self):
        # crea el diccionario que contendrá los parametros buscados
        info_identificacion = {'Denominación o Razón Social:': '',
                               'Nombre:': '', 'Apellido Paterno:': '', 'Apellido Materno:': ''}

        # encuentra el elemento que contiene los datos de identificación
        datos_identificacion = self._soup.find('li', text='Datos de Identificación')
        table_identificacion = datos_identificacion.find_next('table')

        # procesa los datos de identificacion
        for row in table_identificacion.find_all('tr'):

            cells = row.find_all('td')
            if len(cells) == 2:
                label = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                if label not in info_identificacion.keys():
                    continue
                else:
                    info_identificacion[label] = value

        self._informacion_identificacion = info_identificacion

    def _procesar_datos_ubicacion(self):
        info_ubicacion = {'Entidad Federativa:': '', 'Municipio o delegación:': '', 'Colonia:': '',
                          'Tipo de vialidad:': '', 'Nombre de la vialidad:': '', 'Número exterior:': '',
                          'CP:': '', 'Correo electrónico:': ''}

        # encuentra el elemento que contiene los datos de ubicación
        datos_ubicacion = self._soup.find('li', text='Datos de Ubicación (domicilio fiscal, vigente)')
        table_ubicacion = datos_ubicacion.find_next('table')

        # extrae los datos de ubicación
        for row in table_ubicacion.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) == 2:
                label = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                if label not in info_ubicacion.keys():
                    continue
                else:
                    info_ubicacion[label] = value
        self._informacion_ubicacion = info_ubicacion

    def _procesar_datos_fiscales(self):
        # encuentra el elemento que contiene las características fiscales
        caracteristicas_fiscales = self._soup.find('li', text='Características fiscales (vigente)')
        table_caracteristicas = caracteristicas_fiscales.find_next('table')

        # define la lista que guardara los resultados
        regimenes = []

        # extrae y muestra las características fiscales
        for row in table_caracteristicas.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) == 2:
                label = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                if label != 'Régimen:':
                    continue
                else:
                    regimenes.append(value)

        self._regimenes_sin_filtrar = regimenes

    def _buscar_regimenes_fiscales_base_datos(self):
        if not self._regimenes_base_datos:
            consulta = self._base_de_datos.fetchall('SELECT Value FROM vwcboAnexo20v40_RegimenFiscal', ())
            self._regimenes_base_datos = [regimen['Value'] for regimen in consulta]

    def _encontrar_coincidencia(self, cadena, lista_cadenas):
        mejor_coincidencia = None
        mejor_puntaje = 0

        for candidata in lista_cadenas:
            puntaje = fuzz.ratio(cadena, candidata)
            if puntaje > mejor_puntaje:
                mejor_puntaje = puntaje
                mejor_coincidencia = candidata

        return mejor_coincidencia

    def _filtrar_regimenes_fiscales(self):

        regimenes = []

        for regimen in self._regimenes_sin_filtrar:
            regimen_filtrado = self._encontrar_coincidencia(regimen, self._regimenes_base_datos)
            regimenes.append(regimen_filtrado)

        regimenes_descartados = ['606 - Arrendamiento', '616 - Sin obligaciones fiscales',
                                '605 - Sueldos y Salarios e Ingresos Asimilados a Salarios']

        regimenes_filtrados = [regimen for regimen in regimenes if regimen not in regimenes_descartados]
        self._regimenes_filtrados = regimenes_filtrados

    def _procesar_informacion(self):

        # persona fisica
        if self._utilerias.tipo_rfc(self._rfc) == 1:
            nombre = self._informacion_identificacion['Nombre:']
            apellido_paterno = self._informacion_identificacion['Apellido Paterno:']
            apellido_materno = self._informacion_identificacion['Apellido Materno:']

            nombre = f'{nombre} {apellido_paterno} {apellido_materno}'

        else:
            # persona moral
            nombre =  self._informacion_identificacion['Denominación o Razón Social:']

        codigo_postal = self._informacion_ubicacion['CP:']
        colonia_id = self._buscar_colonia_por_cp(codigo_postal)
        info_colonia = self._buscar_colonia_por_id(colonia_id)
        calle = self._crear_calle_cliente()

        self.cliente.address_fiscal_zip_code = codigo_postal
        self.cliente.official_name = nombre
        self.cliente.email = self._informacion_ubicacion['Correo electrónico:']
        self.cliente.address_fiscal_ext_number = self._informacion_ubicacion['Número exterior:']
        self.cliente.address_fiscal_street = calle
        self.cliente.official_number = self._rfc
        self.cliente.cif = self._cif
        self.cliente.zone_name = info_colonia['nombre_ruta'] if info_colonia['nombre_ruta'] else ''
        self.cliente.address_fiscal_city = info_colonia['nombre_colonia'] if info_colonia['nombre_colonia'] else ''
        self.cliente.address_fiscal_municipality = info_colonia['municipio']
        self.cliente.address_fiscal_state_province = info_colonia['estado']

        self.informacion_captura['TipoCaptura'] = 'CIF'
        self.informacion_captura['Regimenes'] = self._regimenes_filtrados

    def _buscar_colonia_por_id(self, colonia_id):
        info_colonia = {}
        if colonia_id == 0:
            info_colonia['nombre_ruta'] = None
            info_colonia['nombre_colonia'] = None
            info_colonia['estado'] = None
            info_colonia['municipio'] = None
        else:
            consulta = self._base_de_datos.fetchall("""
                SELECT A.City, Z.ZoneName, A.State, A.Municipality
                FROM engRefCountryAddress A LEFT OUTER JOIN
                    orgZone Z ON A.ZoneID = Z.ZoneID
                WHERE CountryAddressID = ?
            """, (colonia_id))

            info_colonia['nombre_ruta'] = consulta[0]['ZoneName']
            info_colonia['nombre_colonia'] = consulta[0]['City']
            info_colonia['estado'] = consulta[0]['State']
            info_colonia['municipio'] = consulta[0]['Municipality']

        return info_colonia

    def _crear_calle_cliente(self):

        tipo_vialidad = self._informacion_ubicacion['Tipo de vialidad:']
        nombre_vialidad = self._informacion_ubicacion['Nombre de la vialidad:']

        return f'{tipo_vialidad} {nombre_vialidad}'

    def _buscar_colonia_por_cp(self, cp):
        if not self._colonias_direccion:
            self._consulta_colonias = self._base_de_datos.fetchall("""
                SELECT CountryAddressID, State, Municipality, MunicipalityCode, StateCode, AutonomiaCode, 
                        CountryID, CountryCode, Pais, CityCode, Autonomia, City, ZoneID
                FROM engRefCountryAddress
                WHERE ZipCode = ?
            """, (cp))
            self._colonias_direccion = [colonia['City'] for colonia in self._consulta_colonias]
            return self._filtrar_colonia()

    def _filtrar_colonia(self):
        colonia  = self._informacion_ubicacion['Colonia:']
        colonia_filtrada = self._encontrar_coincidencia(colonia, self._colonias_direccion)

        colonia_id = 0
        for valor in self._consulta_colonias:
            if valor['City'] == colonia_filtrada:
                colonia_id = valor['CountryAddressID']
                break
        return colonia_id

    def _buscar_informacion_web(self):

        barra_progreso = self._componentes_forma['barra_progreso']
        barra_progreso.start()

        self._scrap_informacion_web()
        self._master.after(0, self._procesar_informacion_and_destroy)

    def _procesar_informacion_and_destroy(self):
        if self._procesar_respuesta():
            self._procesar_informacion()
        self._master.destroy()
