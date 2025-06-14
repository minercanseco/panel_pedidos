import ttkbootstrap as ttk
import tkinter as tk
import ttkbootstrap.dialogs

from buscar_info_cif import BuscarInfoCif
from formulario_cliente import FormularioCliente
from cayal.cliente import Cliente
from cayal.ventanas import Ventanas

class PanelPrincipal:
    def __init__(self, master, parametros, base_de_datos, utilerias):

        self._parametros = parametros
        self._utilerias = utilerias
        self._cliente = Cliente()
        self._base_de_datos = base_de_datos

        self._master = master
        self._ventanas = Ventanas(self._master)
        self._ventanas.configurar_ventana_ttkbootstrap('Nuevo:')

        self.componentes_forma = {}
        self._cargar_componentes_forma()
        self._cargar_info_componentes_forma()
        self._cargar_eventos_componentes_forma()

    def _cargar_componentes_forma(self):
        frame_principal = ttk.LabelFrame(self._master, text='Seleccion')
        frame_principal.grid(row=0, column=0, columnspan=2, pady=5, padx=5, sticky=tk.NSEW)

        frame_manual = ttk.LabelFrame(self._master, text='Manual')
        frame_cedula = ttk.LabelFrame(self._master, text='Cedula')
        frame_factura = ttk.Frame(frame_manual)

        frame_botones = ttk.Frame(self._master)
        frame_botones.grid(row=3, column=1, pady=5, padx=5, sticky=tk.E)

        self.componentes_forma['frame_cedula'] = frame_cedula
        self.componentes_forma['frame_manual'] = frame_manual
        self.componentes_forma['frame_factura'] = frame_factura

        nombres_componentes = {
            'cbx_tipo': ('Combobox', frame_principal, 'readonly'),
            'tbx_cliente': ('Entry', frame_manual, None),
            'cbx_documento': ('Combobox', frame_manual, 'readonly'),
            'tbx_cif': ('Entry', frame_cedula, None),
            'tbx_rfc': ('Entry', frame_cedula, None),
            'tbx_rfc2': ('Entry', frame_factura, None),
            'btn_aceptar': ('Button', frame_botones, None),
            'btn_cancelar': ('Button', frame_botones, 'danger')

        }

        for i, (nombre, (tipo, frame, estado)) in enumerate(nombres_componentes.items()):
            lbl_texto = nombre[4:].capitalize() if 'rfc2' not in nombre else 'Rfc'

            if tipo == 'Combobox':
                componente = ttk.Combobox(frame, state=estado)
            elif tipo == 'Entry':
                if nombre == 'cliente':
                    componente = ttk.Entry(frame, width=77)
                elif 'rfc2' in nombre:
                    componente = ttk.Entry(frame, width=20)
                else:
                    componente = ttk.Entry(frame)
            elif tipo == 'Button':
                componente = ttk.Button(frame, text=lbl_texto, style=estado if estado else None)
                componente.grid(row=0, column=i, padx=5, pady=5, sticky=tk.W)

            if tipo != 'Button':
                if 'rfc2' in nombre:
                    lbl = ttk.Label(frame, text=lbl_texto, width=11)
                else:
                    lbl = ttk.Label(frame, text=lbl_texto)

                lbl.grid(row=i, column=0, pady=5, padx=5, sticky=tk.W)
                componente.grid(row=i, column=1, padx=5, pady=5, sticky=tk.W)

            self.componentes_forma[nombre] = componente

    def _cargar_info_componentes_forma(self):
        cbx_tipo = self.componentes_forma['cbx_tipo']
        tipos_captura = ['Seleccione', 'Manual', 'Cédula fiscal']
        cbx_tipo['values'] = tipos_captura
        cbx_tipo.set(tipos_captura[0])

        cbx_documento = self.componentes_forma['cbx_documento']
        tipos_clientes = ['Seleccione', 'Remisión', 'Factura']
        cbx_documento['values'] = tipos_clientes
        cbx_documento.set(tipos_clientes[0])

    def _cargar_eventos_componentes_forma(self):

        tbx_cif = self.componentes_forma['tbx_cif']
        tbx_cif.config(validate = 'focus',
                        validatecommand = (self._master.register(
                                    lambda text: self._ventanas.validar_entry(tbx_cif, 'cif')), '%P'))

        tbx_rfc = self.componentes_forma['tbx_rfc']
        tbx_rfc.config(validate = 'focus',
                        validatecommand = (self._master.register(
                                    lambda text: self._ventanas.validar_entry(tbx_rfc, 'rfc')), '%P'))

        tbx_rfc2 = self.componentes_forma['tbx_rfc2']
        tbx_rfc2.config(validate='focus',
                       validatecommand=(self._master.register(
                           lambda text: self._ventanas.validar_entry(tbx_rfc2, 'rfc')), '%P'))

        btn_cancelar = self.componentes_forma['btn_cancelar']
        btn_cancelar.config(command = lambda : self._master.destroy())

        cbx_tipo = self.componentes_forma ['cbx_tipo']
        cbx_tipo.bind('<<ComboboxSelected>>', lambda event : self._cambiar_apariencia_forma())

        cbx_documento = self.componentes_forma['cbx_documento']
        cbx_documento.bind('<<ComboboxSelected>>', lambda event: self._cambiar_apariencia_forma())

        btn_aceptar = self.componentes_forma['btn_aceptar']
        btn_aceptar.config(command=lambda: self._validaciones_inputs())

    def _cambiar_apariencia_forma(self):

        cbx_documento = self.componentes_forma['cbx_documento']
        seleccion_documento = cbx_documento.get()

        cbx_tipo = self.componentes_forma['cbx_tipo']
        seleccion = cbx_tipo.get()

        frame_cedula = self.componentes_forma['frame_cedula']
        frame_manual = self.componentes_forma['frame_manual']
        frame_factura = self.componentes_forma['frame_factura']

        if seleccion != 'Manual' or seleccion_documento == 'Seleccione':
            self._limpiar_controles()

        if seleccion == 'Manual' and seleccion_documento in ('Remisión', 'Seleccione'):
            frame_cedula.grid_forget()
            frame_factura.grid_forget()
            frame_manual.grid(row=1, column=0, columnspan=2, pady=5, padx=5, sticky=tk.NSEW)

        if seleccion == 'Manual' and seleccion_documento == 'Factura':
            frame_cedula.grid_forget()
            frame_manual.grid(row=1, column=0, columnspan=2, pady=5, padx=5, sticky=tk.NSEW)
            frame_factura.grid(row=3, column=0, columnspan=2, pady=5, sticky=tk.W)

        if seleccion == 'Cédula fiscal':
            frame_manual.grid_forget()
            frame_factura.grid_forget()
            frame_cedula.grid(row=2, column=0, columnspan=2, pady=5, padx=5, sticky=tk.NSEW)

        if seleccion == 'Seleccione':
            frame_manual.grid_forget()
            frame_cedula.grid_forget()
            frame_factura.grid_forget()

    def _limpiar_controles(self):
        for nombre, componente in self.componentes_forma.items():
            if 'tbx' in nombre:
                componente.delete(0, tk.END)

    def _validaciones_inputs(self):
        pass
        cbx_tipo = self.componentes_forma['cbx_tipo']
        seleccion = cbx_tipo.get()

        cbx_documento = self.componentes_forma['cbx_documento']
        seleccion_documento = cbx_documento.get()

        if seleccion == 'Seleccione':
            ttkbootstrap.dialogs.Messagebox.show_error(parent=self._master,message='Debe seleccionar una opción válida.')
            return

        if seleccion_documento == 'Seleccione' and seleccion == 'Manual':
            ttkbootstrap.dialogs.Messagebox.show_error(parent=self._master,message='Debe seleccionar un documento preferente.')
            return

        if seleccion == 'Manual':
            tbx_cliente = self.componentes_forma['tbx_cliente']
            cliente = tbx_cliente.get()

            if not self._validar_cliente(cliente):
                return
            else:
                business_entity_id = self._base_de_datos.cliente_existente(cliente)

                if business_entity_id > 0:
                    validacion = ttkbootstrap.dialogs.Messagebox.yesno(parent=self._master,message=
                        '¿El cliente ya existe en la base de datos desea continuar?')

                    if validacion == 'No':
                        return

                if business_entity_id == 0:
                    business_entity_id = self._base_de_datos.cliente_borrado(cliente)

                    if business_entity_id > 0:
                        validacion = ttkbootstrap.dialogs.Messagebox.yesno(parent=self._master,message=
                            '¿El cliente ya existe en la base de datos pero esta borrado desea continuar?')

                        if validacion == 'No':
                            return
                        else:
                            self._restaurar_cliente_borrado(business_entity_id)
                            self._master.destroy()

                if seleccion_documento == 'Factura':

                    tbx_rfc2 = self.componentes_forma['tbx_rfc2']
                    rfc2 = tbx_rfc2.get()

                    if not self._validar_seleccion_factura(rfc2):
                        return

                self._llamar_forma_segun_tipo_captura(seleccion_documento)

        if seleccion == 'Cédula fiscal':
            tbx_rfc = self.componentes_forma['tbx_rfc']
            rfc = tbx_rfc.get()

            if not self._validar_seleccion_factura(rfc):
                return

            tbx_cif = self.componentes_forma['tbx_cif']
            cif = tbx_cif.get()

            if not self._validar_cif(cif):
                return

            self._llamar_forma_segun_tipo_captura(seleccion)

    def _validar_seleccion_factura(self, rfc):

        if self._validar_rfc(rfc):
            business_entity_id = self._base_de_datos.rfc_existente(rfc)

            if business_entity_id > 0:
                validacion = ttkbootstrap.dialogs.Messagebox.yesno(parent=self._master,message=
                    '¿El rfc ya existe en la base de datos desea continuar?')

                if validacion == 'No':
                    return False

            if business_entity_id == 0:
                business_entity_id = self._base_de_datos.rfc_borrado(rfc)

                if business_entity_id > 0:
                    validacion = ttkbootstrap.dialogs.Messagebox.yesno(parent=self._master,message=
                        '¿El rfc ya existe en la base de datos pero está borrado desea continuar?')

                    if validacion == 'No':
                        return False

            return True

    def _validar_cliente(self, cliente):
        if not cliente:
            ttkbootstrap.dialogs.Messagebox.show_error(parent=self._master,message='Debe agregar un nombre para el cliente.')
            return False

        if len(cliente) < 5:
            ttkbootstrap.dialogs.Messagebox.show_error(parent=self._master,message='Debe agregar un nombre más largo.')
            return False

        return True

    def _validar_cif(self, cif):

        if not cif:
            ttkbootstrap.dialogs.Messagebox.show_error(parent=self._master,message='Debe introducir información en los campos requeridos.')
            return False

        if not self._utilerias.es_cif(cif):
            ttkbootstrap.dialogs.Messagebox.show_error(parent=self._master,message='El cif es es inválido favor de validar.')
            return False

        return True

    def _validar_rfc(self, rfc):

        if not rfc:
            ttkbootstrap.dialogs.Messagebox.show_error(parent=self._master,message='Debe introducir información en los campos requeridos.')
            return False

        if not self._utilerias.es_rfc(rfc):
            ttkbootstrap.dialogs.Messagebox.show_error(parent=self._master,message='El rfc es inválido favor de validar.')
            return False

        return True

    def _llamar_forma_segun_tipo_captura(self, tipo_captura):

        # tipos de seleccion 'Cédula fiscal' 'Factura' 'Remisión'

        if tipo_captura == 'Remisión':
            self._settear_valores_cliente_remision()

        if tipo_captura in ('Factura', 'Cédula fiscal'):
            self._settear_valores_cliente_factura()

        if tipo_captura in ('Factura', 'Remisión'):
            self._master.withdraw()

            informacion_captura = {'TipoCaptura': tipo_captura}
            ventana = self._ventanas.crear_popup_ttkbootstrap_sin_bloqueo('Formulario cliente')
            instancia = FormularioCliente(ventana, self._parametros, informacion_captura, self._cliente)
            ventana.wait_window()
            self._master.destroy()

        if tipo_captura == 'Cédula fiscal':
            self._master.withdraw()

            ventana = ttk.Toplevel()
            buscar_info_cif = BuscarInfoCif(ventana,
                                            self._parametros,
                                            self._cliente.official_number,
                                            self._cliente.cif,
                                            self._cliente)
            ventana.wait_window()

            informacion_captura = buscar_info_cif.informacion_captura

            if informacion_captura:
                self._master.withdraw()

                instancia_cliente = buscar_info_cif.cliente
                ventana = self._ventanas.crear_popup_ttkbootstrap()
                instancia = FormularioCliente(ventana,
                                              self._parametros,
                                              informacion_captura,
                                              instancia_cliente)
                ventana.wait_window()
                self._master.destroy()

    def _restaurar_cliente_borrado(self, business_entity_id):
        self._base_de_datos.command("""
               --Declara variables a usar
                DECLARE @IDEMPR bigint = ?
                DECLARE @DFiscalID bigint
                DECLARE @Control int
                
                --REACTIVA EL CLIENTE SELECCIONADO
                
                SET @Control=(SELECT CASE WHEN DeletedOn IS NULL THEN 0 ELSE 1 END FROM orgBusinessEntity WHERE BusinessEntityID=@IDEMPR)
                
                IF @Control=1
                BEGIN
                
                    UPDATE orgBusinessEntity SET DeletedOn=NULL, DeletedBy=NULL 
                    WHERE BusinessEntityID=@IDEMPR
                
                    UPDATE orgCustomer SET CustomerTypeID=2,DeletedOn=NULL, DeletedBy=NULL, ZoneID=1033 
                    WHERE BusinessEntityID=@IDEMPR
                
                
                    --HOMOLOGACION DE DATOS DE DIRECCIÓN DE CLIENTE 
                
                    --Busca si existe o no la dirección fiscal en la tabla orgaddress
                    SET @DFiscalID=(SELECT AddressFiscalDetailID FROM orgBusinessEntityMainInfo WHERE BusinessEntityID=@IDEMPR)
                    SET @DFiscalID=(SELECT AddressDetailID FROM orgAddress WHERE AddressDetailID=@DFiscalID)
                
                    -- Si la dirección fiscal no existe, INSERT, de lo contrario, actualiza
                    MERGE INTO orgAddressDetail AS target
                    USING (VALUES (@DFiscalID)) AS source (AddressDetailID)
                    ON target.AddressDetailID = source.AddressDetailID
                    WHEN NOT MATCHED BY TARGET THEN
                        INSERT (AddressDetailID, CountryID, StateProvince, City, ZipCode, Municipality, Street, ExtNumber, Comments, CreatedOn, CreatedBy, DeletedBy, UserID, CountryCode, StateProvinceCode, CityCode, MunicipalityCode, IsFiscalAddress)
                        SELECT 
                            ee.AddressFiscalDetailID, 
                            412, 
                            ee.AddressFiscalStateProvince, 
                            ee.AddressFiscalCity, 
                            ee.AddressFiscalZipCode, 
                            ee.AddressFiscalMunicipality, 
                            ee.AddressFiscalStreet, 
                            ee.AddressFiscalExtNumber, 
                            ee.AddressFiscalComments, 
                            ee.CreatedOn, 
                            ee.CreatedBy, 
                            ee.DeletedBy, 
                            0, 
                            ee.AddressFiscalCountryCode, 
                            ee.AddressFiscalStateProvinceCode, 
                            ee.AddressFiscalCityCode, 
                            ee.AddressFiscalMunicipalityCode, 
                            0
                        FROM orgBusinessEntityMainInfo AS ee
                        INNER JOIN orgBusinessEntity AS e ON ee.BusinessEntityID = e.BusinessEntityID
                        WHERE ee.AddressFiscalDetailID = @DFiscalID
                    WHEN MATCHED AND (target.AddressDetailID = @DFiscalID) THEN -- Aquí se agrega la condición de coincidencia
                        UPDATE 
                        SET 
                            target.CountryID = 412, 
                            target.StateProvince = ee.AddressFiscalStateProvince,
                            target.City = ee.AddressFiscalCity,
                            target.ZipCode = ee.AddressFiscalZipCode,
                            target.Municipality = ee.AddressFiscalMunicipality,
                            target.Street = ee.AddressFiscalStreet,
                            target.ExtNumber = ee.AddressFiscalExtNumber,
                            target.Comments = ee.AddressFiscalComments,
                            target.CreatedOn = ee.CreatedOn,
                            target.CreatedBy = ee.CreatedBy,
                            target.DeletedBy = ee.DeletedBy,
                            target.UserID = 0,
                            target.CountryCode = ee.AddressFiscalCountryCode,
                            target.StateProvinceCode = ee.AddressFiscalStateProvinceCode,
                            target.CityCode = ee.AddressFiscalCityCode,
                            target.MunicipalityCode = ee.AddressFiscalMunicipalityCode,
                            target.IsFiscalAddress = 0;
                END

            """, (business_entity_id))

    def _settear_valores_cliente_remision(self):

        tbx_cliente = self.componentes_forma['tbx_cliente']
        cliente = tbx_cliente.get()

        self._cliente.official_name = cliente.upper()
        self._cliente.company_type_name = '616 - Sin obligaciones fiscales'
        self._cliente.official_number = 'XAXX010101000'
        self._cliente.forma_pago = '01'
        self._cliente.metodo_pago = 'PUE'
        self._cliente.receptor_uso_cfdi = 'S01'
        self._cliente.reference = 'REMISIÓN'
        self._cliente.customer_type_id = 2

    def _settear_valores_cliente_factura(self):

        tbx_cliente = self.componentes_forma['tbx_cliente']
        cliente = tbx_cliente.get()

        tbx_rfc = self.componentes_forma['tbx_rfc']
        rfc = tbx_rfc.get()
        rfc = rfc.upper() if rfc else rfc

        tbx_rfc2 = self.componentes_forma['tbx_rfc2']
        rfc2 = tbx_rfc2.get()
        rfc2 = rfc2.upper() if rfc2 else rfc2

        tbx_cif = self.componentes_forma['tbx_cif']
        cif = tbx_cif.get()

        self._cliente.official_name = cliente.upper() if cliente else ''
        self._cliente.forma_pago = '99'
        self._cliente.metodo_pago = 'PPD'
        self._cliente.reference = 'FACTURA'
        self._cliente.customer_type_id = 2
        self._cliente.official_number = rfc if rfc else rfc2
        self._cliente.cif = cif



