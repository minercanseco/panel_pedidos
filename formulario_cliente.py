import tkinter as tk
import ttkbootstrap as ttk
import ttkbootstrap.dialogs
import pyperclip

from cayal.util import Utilerias
from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.cliente import Cliente
from cayal.ventanas  import Ventanas

from buscar_info_cif import BuscarInfoCif
from direcciones_adicionales import DireccionesAdicionales
from panel_direcciones import PanelDirecciones


class FormularioCliente:

    def __init__(self, master, parametros, parametros_cliente, instancia_cliente):

        self._parametros = parametros
        self._parametros_captura = parametros_cliente
        self._cliente = instancia_cliente
        self._master = master

        self._ventanas = Ventanas(self._master)
        self._instanciar_clases_de_apoyo()
        self._inicializar_variables_de_instancia()
        self._cargar_componentes_forma()
        self._cargar_eventos_componentes_forma()
        self._cargar_info_componentes_forma()

        self._ventanas.configurar_ventana_ttkbootstrap('Formulario cliente')
        self._parent = self._utilerias.obtener_master(self._componentes_forma['tbx_cliente'])

    def _instanciar_clases_de_apoyo(self):
        self._utilerias = Utilerias()
        self._base_de_datos = ComandosBaseDatos(self._parametros.cadena_conexion)

    def _inicializar_variables_de_instancia(self):

        self._tipo_captura = self._parametros_captura['TipoCaptura']

        self._componentes_forma = {}
        self._direcciones_adicionales = []

        self._consulta_direcciones_adicionales = []
        self._consulta_uso_cfdi = []
        self._consulta_formas_pago = []
        self._consulta_metodos_pago = []
        self._consulta_regimenes = []
        self._consulta_colonias = []
        self._consulta_rutas = []
        self._actualizacion_desde_cif = 0

        consulta = self._base_de_datos.fetchall('SELECT ZoneID FROM zvwzonasmayoreo', ())
        self._rutas_mayoreo = [ruta['ZoneID'] for ruta in consulta]

        self._usuario_nombre = self._base_de_datos.fetchone('SELECT UserName FROM engUser WHERE UserID = ?',
                                                            (self._parametros.id_usuario))

    def _cargar_componentes_forma(self):
        frame_principal = ttk.LabelFrame(self._master, text='Datos cliente:')
        frame_principal.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)

        frame_generales = ttk.LabelFrame(frame_principal, text='Generales:')
        frame_generales.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)

        frame_fiscal = ttk.LabelFrame(frame_principal, text='Fiscales')
        frame_fiscal.grid(row=0, column=1,  padx=5, pady=5, sticky=tk.NSEW)

        frame_botones = ttk.Frame(frame_principal)
        frame_botones.grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)

        nombres_componentes = {
            'tbx_cliente': ('Entry', frame_generales, None),
            'tbx_ncomercial': ('Entry', frame_generales, None),
            'tbx_telefono': ('Entry', frame_generales, None),
            'tbx_celular': ('Entry', frame_generales, None),
            'tbx_calle': ('Entry', frame_generales, None),
            'tbx_numero': ('Entry', frame_generales, None),
            'txt_comentario': ('Text', frame_generales, None),
            'tbx_cp': ('Entry', frame_generales, None),
            'lbl_estado': ('Label', frame_generales, None),
            'lbl_municipio': ('Label', frame_generales, None),
            'cbx_colonia': ('Combobox', frame_generales, 'readonly'),
            'btn_domicilios': ('Button', frame_generales, 'success'),
            'tbx_domicilios': ('Entry', frame_generales, None),
            'tbx_envio': ('Entry', frame_generales, None),
            'cbx_ruta': ('Combobox', frame_generales, 'readonly'),
            'tbx_rfc': ('Entry', frame_fiscal, None),
            'tbx_cif': ('Entry', frame_fiscal, None),
            'btn_cif': ('Button', frame_fiscal, 'info'),
            'cbx_regimen': ('Combobox', frame_fiscal, 'readonly'),
            'cbx_formapago': ('Combobox', frame_fiscal, 'readonly'),
            'cbx_metodopago': ('Combobox', frame_fiscal, 'readonly'),
            'cbx_usocfdi': ('Combobox', frame_fiscal , 'readonly'),
            'txt_correo': ('Text', frame_fiscal, None),
            'btn_guardar': ('Button', frame_botones, None),
            'btn_cancelar': ('Button', frame_botones, 'danger'),
            'btn_copiar': ('Button', frame_botones, 'warning')
        }
        for i, (nombre, (tipo, frame, estado)) in enumerate(nombres_componentes.items()):
            lbl_texto = nombre[4:].capitalize()

            if tipo == 'Combobox':
                componente = ttk.Combobox(frame, state=estado)
            elif tipo == 'Label':
                componente = ttk.Label(frame, state=estado)
            elif tipo == 'Entry':
                if 'cliente' in nombre or 'calle' in nombre or 'ncomercial' in nombre:
                    componente = ttk.Entry(frame, width=47)
                else:
                    componente = ttk.Entry(frame)

            elif tipo == 'Button':
                if lbl_texto not in ('Cif', 'Domicilios'):
                    componente = ttk.Button(frame, text=lbl_texto, style=estado if estado else None)
                    componente.grid(row=0, column=i, padx=5, pady=5, sticky=tk.W)

                if lbl_texto == 'Cif':
                    componente = ttk.Button(frame, text='Act. CIF', style=estado if estado else None)
                    componente.grid(row=i, column=1, padx=5, pady=5, sticky=tk.W)

                if lbl_texto == 'Domicilios':
                    componente = ttk.Button(frame, text='Domicilios', style=estado if estado else None)
                    componente.grid(row=i, column=1, padx=5, pady=5, sticky=tk.W)

            elif tipo == 'Text':
                componente = ttk.Text(frame, width=47, height=2)

            if tipo != 'Button':
                lbl = ttk.Label(frame, text=lbl_texto)
                lbl.grid(row=i, column=0, pady=5, padx=5, sticky=tk.W)

                componente.grid(row=i, column=1, padx=5, pady=5, sticky=tk.W)

            self._componentes_forma[nombre] = componente

    def _cargar_eventos_componentes_forma(self):

        def agregar_validacion_tbx(nombre_tbx, tipo_validacion):
            tbx = self._componentes_forma[nombre_tbx]
            tbx.config(validate='focus',
                                validatecommand=(self._master.register(
                                    lambda text: self._ventanas.validar_entry(tbx, tipo_validacion)), '%P'))

        agregar_validacion_tbx('tbx_telefono', 'telefono')
        agregar_validacion_tbx('tbx_celular', 'telefono')
        agregar_validacion_tbx('tbx_cp', 'codigo_postal')
        agregar_validacion_tbx('tbx_rfc', 'rfc')
        agregar_validacion_tbx('tbx_cif', 'cif')

        tbx_cp = self._componentes_forma['tbx_cp']
        tbx_cp.bind('<Return>', lambda event: self._cargar_info_por_cp())

        cbx_colonia = self._componentes_forma['cbx_colonia']
        cbx_colonia.bind('<<ComboboxSelected>>', lambda event: self._cargar_info_por_colonia())

        btn_cancelar = self._componentes_forma['btn_cancelar']
        btn_cancelar.config(command=lambda: self._master.destroy())

        btn_guardar = self._componentes_forma['btn_guardar']
        btn_guardar.config(command=lambda: self._validar_inputs_formulario())

        # copia info del formulario al portapapeles
        btn_copiar = self._componentes_forma['btn_copiar']
        btn_copiar.config(command=lambda : self._copiar_info_formulario())

        btn_cif = self._componentes_forma['btn_cif']
        btn_cif.config(command = lambda : self._actualizar_por_cif())

        btn_domicilios = self._componentes_forma['btn_domicilios']
        btn_domicilios.config(command = lambda : self._validar_cliente_con_adicionales())

    def _cargar_info_por_cp(self):
        tbx_cp = self._componentes_forma['tbx_cp']
        cp = tbx_cp.get()

        if not self._utilerias.es_codigo_postal(cp):
            ttkbootstrap.dialogs.Messagebox.show_error(parent=self._parent,
                                                       message='Debe introducir un código postal, válido')
            return

        if self._rellena_cbx_colonia_por_cp(cp):
            cbx_colonia = self._componentes_forma['cbx_colonia']
            colonias = cbx_colonia['values']
            cbx_colonia.set(colonias[1])

            self._actualizar_estado_municipio()
            self._actualizar_cbx_ruta()

    def _cargar_info_por_colonia(self):
        cbx_colonia = self._componentes_forma['cbx_colonia']
        seleccion = cbx_colonia.get()

        if seleccion == 'Seleccione':
            self._rellenar_cbx_colonia()
        else:
            self._actualizar_estado_municipio()
            self._actualizar_tbx_cp()
            self._actualizar_cbx_ruta()

    def _buscar_idx_colonia_seleccionada(self):
        cbx_colonia = self._componentes_forma['cbx_colonia']
        colonia = cbx_colonia.get()
        colonias = [colonia['City'] for colonia in self._consulta_colonias]

        try:
            return colonias.index(colonia)
        except:
            return 0

    def _actualizar_tbx_cp(self):
        tbx_cp = self._componentes_forma['tbx_cp']
        idx = self._buscar_idx_colonia_seleccionada()
        cp = self._consulta_colonias[idx]['ZipCode']

        tbx_cp.delete(0, tk.END)
        tbx_cp.insert(0, cp)

    def _actualizar_cbx_ruta(self):
        cbx_ruta = self._componentes_forma['cbx_ruta']

        cbx_colonia = self._componentes_forma['cbx_colonia']
        seleccion_colonia = cbx_colonia.get()

        if seleccion_colonia != 'Seleccione':
            idx = self._buscar_idx_colonia_seleccionada()
            zone_id_colonia = self._consulta_colonias[idx]['ZoneID']

            self._rutas_mayoreo.append(1040)
            if self._cliente.zone_id == 0 or self._cliente.zone_id not in self._rutas_mayoreo:

                if zone_id_colonia:
                    ruta = [ruta['ZoneName'] for ruta in self._consulta_rutas
                            if int(zone_id_colonia) == int(ruta['ZoneID'])][0]
                else:
                    ruta = [ruta['ZoneName'] for ruta in self._consulta_rutas
                            if int(ruta['ZoneID'] == 1030)][0]

                rutas_cbx = cbx_ruta['values']
                idx_ruta = rutas_cbx.index(ruta)
                cbx_ruta.set(rutas_cbx[idx_ruta])

    def _actualizar_tbx_domicilios(self, numero_direcciones):
        self._ventanas.insertar_input_componente('tbx_domicilios', numero_direcciones)

    def _validar_cliente_con_adicionales(self):

        # inicializa la captura de direccion directamente si no tiene direcciones adicionales sino elije
        # dentro del popup realizar cualquier crud
        ventana = self._ventanas.crear_popup_ttkbootstrap()

        if int(self._cliente.depots) > 0 or int(self._cliente.addresses) > 1 or self._direcciones_adicionales:

            instancia = PanelDirecciones(ventana, self._parametros, self._cliente)
            ventana.wait_window()

            self._actualizar_tbx_domicilios(instancia.numero_direcciones)

        else:

            instancia = DireccionesAdicionales(ventana,
                                               self._parametros,
                                               self._direcciones_adicionales,
                                               'agregar',
                                               business_entity_id=self._cliente.business_entity_id
                                               )
            ventana.wait_window()

            self._actualizar_tbx_domicilios(instancia.numero_direcciones)

    def _cargar_info_componentes_forma(self):

        def rellenar_componente(nombre_componente, valor):
            valor = '' if not valor else valor

            if 'txt' in nombre_componente:
                txt = self._componentes_forma[nombre_componente]
                txt.insert('1.0', valor)
                return
            elif 'lbl' in nombre_componente:
                lbl = self._componentes_forma[nombre_componente]
                lbl.config(text=valor)
            else:
                valor = '' if valor == 0 else valor
                tbx = self._componentes_forma[nombre_componente]
                tbx.insert(0, valor)

                return tbx

        tbx_cliente = rellenar_componente('tbx_cliente', self._cliente.official_name)
        tbx_domicilios = rellenar_componente('tbx_domicilios', self._cliente.addresses)
        tbx_rfc = rellenar_componente('tbx_rfc', self._cliente.official_number)
        tbx_cif = rellenar_componente('tbx_cif', self._cliente.cif)

        rellenar_componente('tbx_ncomercial', self._cliente.commercial_name)
        rellenar_componente('tbx_telefono', self._cliente.phone)
        rellenar_componente('tbx_celular', self._cliente.cellphone)
        rellenar_componente('tbx_numero', self._cliente.address_fiscal_ext_number)
        rellenar_componente('tbx_calle', self._cliente.address_fiscal_street)
        rellenar_componente('txt_comentario', self._cliente.address_fiscal_comments)
        rellenar_componente('tbx_cp', self._cliente.address_fiscal_zip_code)
        rellenar_componente('txt_correo', self._cliente.email)
        rellenar_componente('lbl_estado', self._cliente.address_fiscal_state_province)
        rellenar_componente('lbl_municipio', self._cliente.address_fiscal_municipality)

        envio_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(self._cliente.delivery_cost)
        envio_moneda = self._utilerias.convertir_decimal_a_moneda(envio_decimal)
        tbx_envio = rellenar_componente('tbx_envio', envio_moneda)

        if self._cliente.business_entity_id > 0 or self._parametros_captura['TipoCaptura'] == 'CIF':
            self._rellena_cbx_colonia_por_cp(self._cliente.address_fiscal_zip_code)
            self._settear_colonia_cliente()
            self._actualizar_estado_municipio()
        else:
            self._rellenar_cbx_colonia(colonias=None)
            self._settear_colonia_cliente()

        self._cargar_info_cbx_fiscales()
        self._rellenar_cbx_regimenes()
        self._rellenar_cbx_rutas()


        # deshabilita los controles segun sea el caso
        tbx_domicilios.config(state='disabled')
        tbx_cliente.config(state='disabled')
        tbx_envio.config(state='disabled')

        if tbx_cif.get():
            tbx_rfc.config(state='disabled')
            tbx_cif.config(state='disabled')

        cbx_ruta = self._componentes_forma['cbx_ruta']
        cbx_ruta.config(state='disabled')

    def _rellena_cbx_colonia_por_cp(self, cp):
        self._consulta_colonias = self._base_de_datos.fetchall("""
                            SELECT CountryAddressID, State, Municipality, MunicipalityCode, StateCode, AutonomiaCode, 
                                    CountryID, CountryCode, Pais, CityCode, Autonomia, City, ZoneID, ZipCode
                            FROM engRefCountryAddress
                            WHERE ZipCode = ? AND ZoneID IS NOT NULL
                            ORDER BY City
                        """, (cp))

        if not self._consulta_colonias:
            self._consulta_colonias = self._base_de_datos.fetchall("""
                                        SELECT CountryAddressID, State, Municipality, MunicipalityCode, StateCode,
                                                AutonomiaCode, 
                                                CountryID, CountryCode, Pais, CityCode, Autonomia, City, ZoneID, ZipCode
                                        FROM engRefCountryAddress
                                        WHERE ZipCode = ?
                                        ORDER BY City
                                    """, (cp))

        if not self._consulta_colonias:
            ttkbootstrap.dialogs.Messagebox.show_error(parent=self._parent,
                                                       message='El código postal proporcionado no devolvió resultados.')
            return False

        colonias = [colonia['City'] for colonia in self._consulta_colonias]
        self._rellenar_cbx_colonia(colonias)

        return True

    def _actualizar_estado_municipio(self):

        idx = self._buscar_idx_colonia_seleccionada()

        lbl_estado = self._componentes_forma['lbl_estado']
        lbl_municipio = self._componentes_forma['lbl_municipio']

        estado = self._consulta_colonias[idx]['State']
        municipio = self._consulta_colonias[idx]['Municipality']

        lbl_estado.config(text=estado)
        lbl_municipio.config(text=municipio)

    def _rellenar_cbx_colonia(self, colonias=None):

        if not colonias:
            self._consulta_colonias = self._base_de_datos.fetchall("""
                                SELECT CountryAddressID, State, Municipality, MunicipalityCode, StateCode, 
                                        AutonomiaCode, 
                                        CountryID, CountryCode, Pais, CityCode, Autonomia, City, ZoneID, ZipCode
                                FROM engRefCountryAddress
                                WHERE ZoneID IS NOT NULL
                                ORDER BY City
                            """, ())

            colonias = [colonia['City'] for colonia in self._consulta_colonias]

        cbx_colonia = self._componentes_forma['cbx_colonia']

        colonias.insert(0,'Seleccione')
        cbx_colonia['values'] = colonias

    def _settear_colonia_cliente(self):
        cbx_colonia = self._componentes_forma['cbx_colonia']
        colonia = self._cliente.address_fiscal_city
        colonias = cbx_colonia['values']

        try:
            idx = colonias.index(colonia)
            cbx_colonia.set(colonias[idx])
        except:
            cbx_colonia.set(colonias[0])

    def _rellenar_cbx_rutas(self):

        cbx_ruta = self._componentes_forma['cbx_ruta']

        if not self._consulta_rutas:
            self._consulta_rutas = self._base_de_datos.fetchall("""
                                        SELECT ZoneID, ZoneName 
                                        FROM zvwTodasRutasCayal
                                        WHERE ZoneID NOT IN (1039, 1049)
                                        ORDER BY ZoneName
                                        """, ())

        rutas = [ruta['ZoneName'] for ruta in self._consulta_rutas]
        rutas.insert(0, 'Seleccione')
        cbx_ruta['values'] = rutas

        if self._actualizacion_desde_cif == 0:

            ruta = self._cliente.zone_name
            if ruta != '':
                idx = rutas.index(ruta)
                cbx_ruta.set(rutas[idx])
            else:
                cbx_ruta.set(rutas[0])

        if self._parametros_captura['TipoCaptura'] == 'CIF':
            self._settear_ruta_mayoreo_defecto()

    def _settear_ruta_mayoreo_defecto(self):
        cbx_ruta = self._componentes_forma['cbx_ruta']

        if not self._consulta_rutas:
            self._consulta_rutas = self._base_de_datos.fetchall("""
                                        SELECT ZoneID, ZoneName 
                                        FROM zvwTodasRutasCayal
                                        WHERE ZoneID NOT IN (1048, 1039, 1049)
                                        ORDER BY ZoneName
                                        """, ())

        rutas = [ruta['ZoneName'] for ruta in self._consulta_rutas]
        rutas.insert(0, 'Seleccione')
        cbx_ruta['values'] = rutas

        grupo_usuario = self._base_de_datos.fetchone(
            'SELECT UserGroupID FROM engUser WHERE UserID = ?',(self._parametros.id_usuario))
        ruta_id = 1033 if grupo_usuario == 4 else 1030
        ruta = [ruta['ZoneName'] for ruta in self._consulta_rutas if ruta['ZoneID'] == ruta_id][0]
        idx = rutas.index(ruta)
        cbx_ruta.set(rutas[idx])

    def _cargar_info_cbx_fiscales(self):

        self._consulta_uso_cfdi = self._base_de_datos.fetchall("""
            -- omite usos de cfdi no validos para cayal
            SELECT * FROM vwcboAnexo20v40_UsoCFDI WHERE ID NOT IN (12, 23) ORDER BY ID
            """, ())
        self._consulta_formas_pago = self._base_de_datos.fetchall("""
            -- formas de pago aceptadas por cayal
            SELECT * FROM vwcboAnexo20v33_FormaPago WHERE ID IN (1, 2, 3, 4, 28, 99)
            """, ())
        self._consulta_metodos_pago = self._base_de_datos.fetchall("""
            SELECT * FROM vwcboAnexo20v33_MetodoDePago
            """,())

        def rellenar_cbx_fiscal(consulta, nombre_cbx, propiedad_clase):
            cbx = self._componentes_forma[nombre_cbx]
            consulta_filtrada = [reg['Value'] for reg in consulta]
            consulta_filtrada.insert(0, 'Seleccione')
            cbx['values'] = consulta_filtrada

            if propiedad_clase == '':
                cbx.set(consulta_filtrada[0])
            else:
                idx = [i  for i, reg in enumerate(consulta) if reg['Clave'] == propiedad_clase]
                if not idx:
                    cbx.set(consulta_filtrada[0])
                else:
                    idx = idx[0]
                    cbx.set(consulta[idx]['Value'])

        rellenar_cbx_fiscal(self._consulta_uso_cfdi, 'cbx_usocfdi', self._cliente.receptor_uso_cfdi)
        rellenar_cbx_fiscal(self._consulta_formas_pago, 'cbx_formapago', self._cliente.forma_pago)
        rellenar_cbx_fiscal(self._consulta_metodos_pago, 'cbx_metodopago', self._cliente.metodo_pago)

    def _rellenar_cbx_regimenes(self):
        cbx_regimen = self._componentes_forma['cbx_regimen']

        if self._parametros_captura['TipoCaptura'] == 'CIF':
            regimenes = self._parametros_captura['Regimenes']

            if regimenes:
                if len(regimenes) > 1:
                    regimenes.insert(0, 'Seleccione')

                cbx_regimen['values'] = regimenes
                cbx_regimen.set(regimenes[0])
        else:
            self._consulta_regimenes = self._base_de_datos.fetchall("""
                        SELECT * FROM vwcboAnexo20v40_RegimenFiscal WHERE ID NOT IN (3,4)
                    """, ())

            regimenes = [regimen['Value'] for regimen in self._consulta_regimenes]
            regimenes.insert(0, 'Seleccione')
            cbx_regimen['values'] = regimenes
            cbx_regimen.set(regimenes[0] if self._cliente.company_type_name == '' else self._cliente.company_type_name)

    def _validar_inputs_formulario(self):

        validar_texto = ['tbx_calle', 'tbx_numero', 'txt_comentario',
                         'txt_correo', 'tbx_cp', 'tbx_rfc',
                         'tbx_cif', 'tbx_telefono', 'tbx_celular'
                         ]
        telefonos = {}
        parametros_fiscales = {}

        for nombre, detalles in self._componentes_forma.items():

            componente = self._componentes_forma[nombre]
            etiqueta_componente = nombre[4::]

            if nombre in validar_texto:
                valor = componente.get() if 'tbx' in nombre else componente.get('1.0', tk.END)
                valor = valor if valor else ''
                valor = valor.strip()

                if 'correo' in nombre:
                    if valor != '':
                        if not self._utilerias.validar_cadena_correos(valor):
                            ttkbootstrap.dialogs.Messagebox.show_error(
                                parent=self._parent,
                                message='La cadena de correos proporcionada es inválida'
                                                                       ' debe corregirla.')
                            return

                    parametros_fiscales['email'] = valor

                if etiqueta_componente in ('calle', 'numero', 'comentario'):
                    if len(valor) < 2:
                        ttkbootstrap.dialogs.Messagebox.show_error(
                            parent=self._parent,
                            message=f'Debe abundar en el contenido del campo'
                                                                   f' {etiqueta_componente}')
                        return

                if 'cp' in nombre:
                    if not self._utilerias.es_codigo_postal(valor):
                        ttkbootstrap.dialogs.Messagebox.show_error(
                            parent=self._parent,
                            message='El código postal es inválido.')

                        return

                if 'rfc' in nombre:
                    if not self._utilerias.es_rfc(valor):
                        ttkbootstrap.dialogs.Messagebox.show_error(
                            parent=self._parent,
                            message='El rfc es inválido.')
                        return
                    else:
                        parametros_fiscales['rfc'] = valor

                if 'cif' in nombre:
                    if valor != '':
                        if not self._utilerias.es_cif(valor):
                            ttkbootstrap.dialogs.Messagebox.show_error(
                                parent=self._parent,
                                message='El cif es inválido.')
                            return
                    parametros_fiscales['cif'] = valor

                if etiqueta_componente in ('telefono', 'celular'):
                    if valor != '':
                        if not self._utilerias.es_numero_de_telefono(valor):
                            ttkbootstrap.dialogs.Messagebox.show_error(
                                parent=self._parent,
                                message=f'El {etiqueta_componente} proporcionado es inválido.')
                            return

                    if valor != '':
                        telefonos[etiqueta_componente] = valor

            if 'cbx' in nombre:
                seleccion = componente.get()
                if not seleccion or seleccion == 'Seleccione':
                    ttkbootstrap.dialogs.Messagebox.show_error(
                        parent=self._parent,
                        message=f'Debe seleccionar un valor para {etiqueta_componente}.')
                    return

                if etiqueta_componente in ('metodopago', 'formapago', 'usocfdi', 'regimen'):
                    parametros_fiscales[etiqueta_componente] = seleccion

        if not self._validar_reglas_de_negocio(parametros_fiscales, telefonos):
            return

        self._asigna_parametros_a_cliente()

    def _validar_reglas_de_negocio(self, parametros_fiscales, telefonos):

        # valida la configuracion fiscal

        forma_pago = str(parametros_fiscales['formapago'][0:2])
        metodo_pago = parametros_fiscales['metodopago'][0:3]
        uso_cfdi = parametros_fiscales['usocfdi'][0:3]
        regimen = parametros_fiscales['regimen'][0:3]
        rfc = parametros_fiscales['rfc']
        cif = parametros_fiscales['cif']
        email = parametros_fiscales['email']

        # caso remision
        if uso_cfdi == 'S01' or rfc == 'XAXX010101000' or regimen == '616':
            if not(uso_cfdi == 'S01' and rfc == 'XAXX010101000' and regimen == '616'):
                ttkbootstrap.dialogs.Messagebox.show_error(
                    parent=self._parent,
                    message=
                    f'La cofiguración válida para un cliente que remisiona es la siguiente:\n' \
                    f'Forma de pago: 01 , 04, 28\n' \
                    f'Método de pago: PUE - Pago en una sola exhibición.\n' \
                    f'Uso de CFDI: S01 - Sin efectos fiscales.\n' \
                    f'Régimen: 616 - Sin obligaciones fiscales.\n' \
                    f'Favor de validar y corregir.'
                    )
                return False

        # caso 99 ppd
        if forma_pago == '99' or metodo_pago == 'PPD':

            if not (forma_pago == '99' and metodo_pago == 'PPD'):
                ttkbootstrap.dialogs.Messagebox.show_error(
                    parent=self._parent,
                    message=
                    f'La forma de pago: 99 - Por definir\n' \
                    f'Debe configurarse solamente con \n' \
                    f'El método de pago: PPD - Pago en parcialidades o diferido.\n' \
                    f'Favor de validar y corregir.'
                )
                return False

        # caso cif
        if rfc == 'XAXX010101000' and cif:
            ttkbootstrap.dialogs.Messagebox.show_error(
                parent=self._parent,
                message='La captura del CIF sólo es válida para un cliente que factura.')
            return False

        # valida correos
        if (not email or email == '') and rfc != 'XAXX010101000':
            ttkbootstrap.dialogs.Messagebox.show_error(
                parent=self._parent,
                message='La captura de un email válido es obligatoria para un cliente'
                                                       ' que factura.')
            return False

        # valida telefonos
        if len(telefonos) == 0:
            ttkbootstrap.dialogs.Messagebox.show_error(
                parent=self._parent,
                message='Debe capturar por lo menos un número telefónico.')
            return False

        return True

    def _asigna_parametros_a_cliente(self):

        parametros = {'tbx_cliente': 'official_name',
                      'tbx_ncomercial': 'commercial_name',
                      'tbx_calle': 'address_fiscal_street',
                      'tbx_numero': 'address_fiscal_ext_number',
                      'txt_comentario': 'address_fiscal_comments',
                      'txt_correo': 'email',
                      'tbx_cp': 'address_fiscal_zip_code',
                      'tbx_rfc': 'official_number',
                      'tbx_cif': 'cif',
                      'tbx_telefono': 'phone',
                      'tbx_celular': 'cellphone',
                      'tbx_domicilios': 'addresses',
                      'lbl_estado': 'address_fiscal_state_province',
                      'lbl_municipio': 'address_fiscal_municipality',
                      'cbx_colonia': 'address_fiscal_city',
                      'cbx_regimen': 'company_type_name',
                      'cbx_formapago': 'forma_pago',
                      'cbx_metodopago': 'metodo_pago',
                      'cbx_usocfdi': 'receptor_uso_cfdi',
                      'cbx_ruta': 'zone_id'
                      }

        def buscar_clave_cbx_fiscal(seleccion, consulta):
            return [reg['Clave'] for reg in consulta if reg['Value'] == seleccion][0]

        execepciones_mayusculas = ('lbl_estado', 'lbl_municipio', 'txt_correo', 'cbx_regimen', 'cbx_colonia',
                                   'cbx_formapago', 'cbx_metodopago', 'cbx_usocfdi')

        for nombre, componente in self._componentes_forma.items():
            tipo_componente = nombre[0:3]

            if tipo_componente in ('cbx', 'txt', 'tbx', 'lbl'):

                if tipo_componente == 'lbl':
                    valor_attributo = componente.cget("text")

                if tipo_componente in ('cbx', 'txt', 'tbx'):
                    valor_attributo = componente.get('1.0', tk.END) if 'txt' in nombre else componente.get()

                valor_attributo = valor_attributo if valor_attributo else ''
                valor_attributo = valor_attributo.strip()
                valor_attributo = valor_attributo.upper() if nombre not in execepciones_mayusculas else valor_attributo

                etiqueta_componente = nombre[4::]

                if etiqueta_componente == 'colonia':

                    info_colonia = [colonia for colonia in self._consulta_colonias if colonia['City'] == valor_attributo][0]

                    self._cliente.state_code = info_colonia['StateCode']
                    self._cliente.city_code = info_colonia['CityCode']
                    self._cliente.municipality_code = info_colonia['MunicipalityCode']

                if etiqueta_componente == 'formapago':
                    valor_attributo = buscar_clave_cbx_fiscal(valor_attributo, self._consulta_formas_pago)

                if etiqueta_componente == 'metodopago':
                    valor_attributo = buscar_clave_cbx_fiscal(valor_attributo, self._consulta_metodos_pago)

                if etiqueta_componente == 'usocfdi':
                    valor_attributo = buscar_clave_cbx_fiscal(valor_attributo, self._consulta_uso_cfdi)

                if etiqueta_componente == 'ruta':
                    valor_attributo = [ruta['ZoneID'] for ruta in self._consulta_rutas
                                       if ruta['ZoneName'] == valor_attributo][0]

                parametro = parametros.get(nombre, None)
                if parametro:
                    setattr(self._cliente, parametro, valor_attributo)

        if self._parametros.id_principal == -1:
            print('creando cliente')
            self._crear_cliente()

        if self._parametros.id_principal > 0:
            print('actualizando cliente')
            self._actualizar_cliente()

    def _crear_cliente(self):

        if self._cliente.official_number == 'XAXX010101000':
            self._cliente.business_entity_type_id = 2
            self._cliente.category_type_id = 2
            self._cliente.cif = None
            self._cliente.official_number_backup = None
            self._cliente.email = None
        else:
            self._cliente.business_entity_type_id = 2 if self._utilerias.tipo_rfc(self._cliente.official_number) == 1 else 1
            self._cliente.category_type_id = 1

        business_entity_id = self._base_de_datos.crear_cliente(self._cliente, self._parametros.id_usuario)

        if business_entity_id:
            ttkbootstrap.dialogs.Messagebox.show_info(parent=self._master,
                                                      message='¡Cliente agregado satisfactoriamente!')
        self._master.destroy()

    def _actualizar_cliente(self):

        # crea otras instancia de cliente con los valores extraidos desde la bd y comparalos en cada caso para
        # actualizar dicha info o no segun sea el caso

        info_cliente = self._base_de_datos.fetchall("""
                    	SELECT * FROM [dbo].[zvwBuscarInfoCliente-BusinessEntityID](?)
                """, (self._cliente.business_entity_id))

        cliente_bd = Cliente()
        cliente_bd.consulta = info_cliente
        cliente_bd.settear_valores_consulta()

        datos_modificados = {}

        atributos = {
        'tbx_cliente': ('official_name', 'NOMBRE CLIENTE', 'orgBusinessEntity', 'OfficialName'),
        'tbx_ncomercial': ('commercial_name', 'NOMBRE COMERCIAL', 'orgBusinessEntity', 'CommercialName'),
        'tbx_calle': ('address_fiscal_street', 'CALLE', 'orgBusinessEntityMainInfo', 'AddressFiscalStreet'),
        'tbx_numero': ('address_fiscal_ext_number', 'NUMERO', 'orgBusinessEntityMainInfo', 'AddressFiscalExtNumber'),
        'txt_comentario': ('address_fiscal_comments', 'COMENTARIOS DIRECCIÓN', 'orgBusinessEntityMainInfo', 'AddressFiscalComments'),
        'txt_correo': ('email', 'CORREO', 'orgBusinessEntityMainInfo', 'BusinessEntityEMail'),
        'tbx_cp': ('address_fiscal_zip_code', 'CODIGO POSTAL', 'orgBusinessEntityMainInfo', 'AddressFiscalZipCode'),
        'tbx_rfc': ('official_number', 'RFC', 'orgBusinessEntityMainInfo', 'OfficialNumber'),
        'tbx_cif': ('cif', 'CIF', 'orgBusinessEntity', 'CIDCayal'),
        'tbx_telefono': ('phone','TELÉFONO', 'orgBusinessEntityMainInfo', 'BusinessEntityPhone'),
        'tbx_celular': ('cellphone', 'CELULAR', 'orgCommunicationChannel', None),
        'lbl_estado': ('address_fiscal_state_province', 'ESTADO', 'orgBusinessEntityMainInfo', 'AddressFiscalStateProvince'),
        'lbl_municipio': ('address_fiscal_municipality', 'MUNICIPIO', 'orgBusinessEntityMainInfo', 'AddressFiscalMunicipality'),
        'cbx_colonia': ('address_fiscal_city', 'COLONIA', 'orgBusinessEntityMainInfo', 'AddressFiscalCity'),
        'cbx_regimen': ('company_type_name','REGIMEN FISCAL', 'orgBusinessEntity', 'CompanyTypeName'),
        'cbx_formapago': ('forma_pago', 'FORMA PAGO', 'orgCustomer', 'FormaPago'),
        'cbx_metodopago': ('metodo_pago','METODO PAGO', 'orgCustomer', 'MetodoPago'),
        'cbx_usocfdi': ('receptor_uso_cfdi', 'USO CFDI', 'orgCustomer', 'ReceptorUsoCFDI'),
        'cbx_ruta': ('zone_id', 'RUTA', 'orgCustomer', 'ZoneID')
        }

        campos_orgAddressDetail = {'calle': 'Street', 'numero': 'ExtNumber', 'estado': 'StateProvince',
                                   'municipio': 'Municipality', 'cp': 'ZipCode', 'colonia':'City'}

        for i, (nombre, (atributo, nombre_atributo, tabla, campo_tabla)) in enumerate(atributos.items()):
            valor_previo = getattr(cliente_bd, atributo)
            valor_nuevo = getattr(self._cliente, atributo)
            valor_nuevo = None if not valor_nuevo else valor_nuevo

            if valor_nuevo:
                execepciones_mayusculas = ('lbl_estado','lbl_municipio','txt_correo', 'cbx_regimen', 'cbx_colonia')
                valor_nuevo = str(valor_nuevo)
                valor_nuevo = valor_nuevo.upper() if nombre not in execepciones_mayusculas  else valor_nuevo

            if valor_previo:
                valor_previo = str(valor_previo)

            nombre_parametro = nombre[4::]

            if valor_nuevo != valor_previo:
                valor_nuevo = '' if not valor_nuevo else valor_nuevo
                datos_modificados[nombre_parametro] = (valor_previo, valor_nuevo, nombre_atributo, tabla, campo_tabla)

        for i, (campo, (valor_previo, valor_nuevo, nombre_atributo, tabla, campo_tabla)) in enumerate(datos_modificados.items()):

            if campo not in ('celular'):
                self._actualiza_tabla(tabla, campo_tabla, 'BusinessEntityID', valor_nuevo,
                                      self._cliente.business_entity_id)

            if campo == 'telefono':

                self._base_de_datos.actualiza_orgCommunicationChannel(
                    self._cliente.business_entity_id, 2, valor_previo, valor_nuevo)

            if campo == 'celular':
                self._base_de_datos.actualiza_orgCommunicationChannel(
                    self._cliente.business_entity_id, 3, valor_previo, valor_nuevo)

            if campo == 'correo':
                self._base_de_datos.actualiza_orgCommunicationChannel(
                    self._cliente.business_entity_id, 1, valor_previo, valor_nuevo)

            if campo in campos_orgAddressDetail.keys():

                self._actualiza_tabla('orgAddressDetail', campos_orgAddressDetail[campo], 'AddressDetailID', valor_nuevo,
                                      self._cliente.address_fiscal_detail_id)

            self._actualizar_bitacora_clientes(nombre_atributo, valor_previo, valor_nuevo)

        self._master.destroy()

    def _actualizar_bitacora_clientes(self, nombre_campo, valor_anterior, valor_nuevo):

        incidencia = f'ACTUALIZACIÓN EN {nombre_campo}'

        parametros = (self._cliente.business_entity_id, self._cliente.official_name, incidencia,
                      valor_anterior, valor_nuevo, self._cliente.zone_name, self._usuario_nombre)

        self._base_de_datos.command("""
            INSERT INTO zvwBitacoraCambiosClientesT
                (IDEmpresa, Fecha, Cliente, Incidencia, 
                ValorAnterior, ValorNuevo, Ruta, Usuario)
			VALUES(?, GETDATE(), ?, ?,
			        ?, ?, ?, ?)
        """,(parametros))

    def _copiar_info_formulario(self):
        business_entity_id = self._cliente.business_entity_id
        address_detail_id = self._cliente.address_fiscal_detail_id
        informacion = self._base_de_datos.buscar_informacion_direccion_whatsapp(address_detail_id, business_entity_id)
        pyperclip.copy(informacion)
        self._ventanas.mostrar_mensaje(mensaje="Dirección copiada al portapapeles.", master=self._master, tipo='info')

    def _actualizar_por_cif(self):

        tbx_rfc = self._componentes_forma['tbx_rfc']
        rfc = tbx_rfc.get()

        tbx_cif = self._componentes_forma['tbx_cif']
        cif = tbx_cif.get()

        if not cif or not rfc:
            ttkbootstrap.dialogs.Messagebox.show_error(
                parent=self._parent,
                message='Debe capturar un CIF y un RFC válidos.')
            return

        if rfc == 'XAXX010101000':
            ttkbootstrap.dialogs.Messagebox.show_error(
                parent=self._parent,
                message='La captura del CIF sólo es válida para un cliente con RFC.')
            return

        business_entity_id = self._base_de_datos.rfc_existente(rfc)

        if business_entity_id > 0 and business_entity_id != self._cliente.business_entity_id:
            validacion = ttkbootstrap.dialogs.Messagebox.yesno(
                parent=self._parent,
                message='¿El rfc ya existe en la base de datos desea continuar?')
            if validacion == 'No':
                return

        if business_entity_id == 0:
            business_entity_id = self._base_de_datos.rfc_borrado(rfc)

            if business_entity_id > 0 and business_entity_id != self._cliente.business_entity_id:
                validacion = ttkbootstrap.dialogs.Messagebox.yesno(
                    parent=self._parent,
                    message='¿El rfc ya existe en la base de datos pero está borrado desea continuar?')
                if validacion == 'No':
                    return

        # carga la clase encargada de buscar la informacion del cif y el rfc
        ventana = ttk.Toplevel()
        buscar_info_cif = BuscarInfoCif(ventana,
                                        self._parametros,
                                        rfc,
                                        cif,
                                        self._cliente)
        ventana.wait_window()

        informacion_captura = buscar_info_cif.informacion_captura

        # si se recupera informacion recupera la instancia rellenada por la clase buscarinfocif
        if informacion_captura:
            self._actualizacion_desde_cif = 1
            self._cliente.phone = ''
            self._cliente.cellphone = ''
            self._cliente.address_fiscal_street = ''

            limpiar_componentes = ['tbx_cliente', 'tbx_numero', 'tbx_cp', 'tbx_rfc', 'tbx_cif']
            for nombre in limpiar_componentes:
                componente = self._componentes_forma[nombre]
                componente.config(state='enabled')
                componente.delete(0, tk.END)

            txt_correo = self._componentes_forma['txt_correo']
            txt_correo.insert('1.0', ',')

            instancia_cliente = buscar_info_cif.cliente

            self._cliente = instancia_cliente
            self._parametros_captura = informacion_captura

            # limpiar campos de formulario

            self._cargar_info_componentes_forma()
            self._actualizacion_desde_cif = 0

    def _actualiza_tabla(self, tabla, campo, campo_llave, valor, valor_llave):
        sql = f"UPDATE {tabla} SET {campo} = '{valor}' WHERE  {campo_llave} = {valor_llave}"
        self._base_de_datos.command(sql, ())

