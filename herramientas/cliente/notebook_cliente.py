import tkinter as tk
from cayal.ventanas import Ventanas
from formulario_cliente_interfaz import FormularioClienteInterfaz
from formulario_cliente_modelo import FormularioClienteModelo
from formulario_cliente_controlador import FormularioClienteControlador
from direccion_adicional import DireccionAdicional

class NoteBookCliente:
    def __init__(self, master, base_de_datos, parametros, utilerias, cliente):
        self._master = master
        self._ventanas = Ventanas(self._master)

        self._cliente = cliente
        self._base_de_datos = base_de_datos
        self._parametros = parametros
        self._utilerias = utilerias

        self._business_entity_id = self._parametros.id_principal
        self._direcciones_adicionales = []

        self._homologar_direccion_fiscal(self._business_entity_id)
        self._settar_info_cliente()

        self._crear_frames()
        self._cargar_componentes()
        self._ventanas.configurar_ventana_ttkbootstrap('Cliente')

    def _crear_frames(self):
        frames = {
            'frame_principal': (
                'master',
                'Direcciones:',
                {'row': 0, 'column': 0, 'padx': 2, 'pady': 2, 'sticky': tk.NSEW}
            ),

            'frame_notebook': (
                'frame_principal',
                None,
                {'row': 1, 'column': 0, 'padx': 2, 'pady': 2, 'sticky': tk.NSEW}
            ),
        }
        self._ventanas.crear_frames(frames)

        frame_principal = self._ventanas.componentes_forma['frame_principal']
        frame_principal.rowconfigure(1, weight=1)
        frame_principal.columnconfigure(0, weight=1)

    def _cargar_componentes(self):
        info_pestanas = {
            # Texto de la pestaña con emoji de dirección fiscal
            'tab_direccion_fiscal': ('Dirección fiscal 🧾📍', None),
        }

        if self._cliente.business_entity_id > 0 and self._cliente.addresses > 1:
            info_pestanas = self._crear_tabs_direcciones_adicionales(info_pestanas)

        nombre_notebook = 'nbk_formulario_cliente'
        notebook = self._ventanas.crear_notebook(
            nombre_notebook=nombre_notebook,
            info_pestanas=info_pestanas,
            nombre_frame_padre='frame_notebook',
            config_notebook={
                'row': 0,
                'column': 0,
                'sticky': tk.NSEW,
                'padx': 5,
                'pady': 5,
                'bootstyle': 'primary',
            }
        )

        # Crear frames base para cada pestaña
        frames_tabs = {}
        for clave, valor in info_pestanas.items():
            tab_name = clave  # p.ej. 'tab_direccion_fiscal'
            frame_name = clave.replace('tab_', 'frm_')  # 'frm_direccion_fiscal'
            frames_tabs[frame_name] = (
                tab_name,
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            )

        self._ventanas.crear_frames(frames_tabs)

        # ----------------------------------------------------------------------
        # 1) DIRECCIÓN FISCAL (pestaña principal)
        # ----------------------------------------------------------------------
        frame_direccion_fiscal = self._ventanas.componentes_forma['frm_direccion_fiscal']

        # Diccionario base con info del notebook (NO uses el widget como nombre)
        info_notebook_base = {
            'notebook': notebook,  # widget
            'nombre_notebook': nombre_notebook,  # string: clave en componentes_forma
        }

        # Info específica para la pestaña de dirección fiscal
        info_notebook_fiscal = {
            **info_notebook_base,
            'nombre_tab': 'tab_direccion_fiscal',
            'tab_notebook': frame_direccion_fiscal,  # frame de la pestaña en el notebook
        }

        self._interfaz = FormularioClienteInterfaz(frame_direccion_fiscal, info_notebook_fiscal)
        self._modelo = FormularioClienteModelo(
            self._parametros,
            self._utilerias,
            self._base_de_datos,
            self._cliente
        )
        self._controlador = FormularioClienteControlador(
            self._interfaz,
            self._modelo
        )

        # ----------------------------------------------------------------------
        # 2) DIRECCIONES ADICIONALES (pestañas extra)
        # ----------------------------------------------------------------------
        if self._cliente.addresses > 1:
            for tab, (nombre_tab, configuracion) in info_pestanas.items():
                if tab == 'tab_direccion_fiscal':
                    continue

                # El texto visible puede traer " 🏠", se limpia
                nombre_limpio = (nombre_tab or '').replace(' 🏠', '').strip()

                consulta_direccion = [
                    reg for reg in self._direcciones_adicionales
                    if reg['AddressName'] == nombre_limpio
                ]
                if not consulta_direccion:
                    continue

                info_direccion = consulta_direccion[0]

                # Completar con valores por defecto
                info_direccion = self._acompletar_valores_direccion(info_direccion)

                frame_name = tab.replace('tab_', 'frm_')
                frame_widget = self._ventanas.componentes_forma[frame_name]

                # Crear un diccionario NUEVO para cada pestaña adicional
                info_notebook_extra = {
                    **info_notebook_base,
                    'nombre_tab': tab,  # ej. 'tab_direccion_sucursal_1'
                    'tab_notebook': frame_widget,
                }

                DireccionAdicional(
                    frame_widget,
                    self._modelo,
                    info_direccion,
                    info_notebook_extra
                )

    def _buscar_info_cliente(self):
        return self._base_de_datos.fetchall("""
                SELECT * FROM [dbo].[zvwBuscarInfoCliente-BusinessEntityID](?)
            """, (self._business_entity_id,))

    def _settar_info_cliente(self):
        if self._business_entity_id <= 0:
            return

        info_cliente = self._buscar_info_cliente()
        info_cliente[0]['DeliveryCost'] = self._utilerias.redondear_valor_cantidad_a_decimal(info_cliente[0]['DeliveryCost'])
        self._cliente.consulta = info_cliente
        self._cliente.settear_valores_consulta()

    def _homologar_direccion_fiscal(self, business_entity_id):
        if business_entity_id <= 0:
            return
        # esta funcion es deuda tecnica de la homologacion entre la direccion fiscal
        # y orgbusinessentitymaininfo que es la tabla donde nace los parametros
        # de la direccion fiscal del cliente, esto es necesario para coherencia en
        # la información y la impresion de los formatos del cliente

        self._base_de_datos.command("""
           DECLARE @business_entity_id INT = ?;
        
            DECLARE @CH TABLE
            (
                BusinessEntityID       INT PRIMARY KEY,
                BusinessEntityEMail    NVARCHAR(255) NULL,
                BusinessEntityPhone    NVARCHAR(50)  NULL,
                Celular                NVARCHAR(50)  NULL
            );
            
            INSERT INTO @CH (BusinessEntityID, BusinessEntityEMail, BusinessEntityPhone, Celular)
            SELECT
                oc.BusinessEntityID,
            
                COALESCE(
                    MAX(CASE WHEN oc.ChannelTypeID = 1 AND oc.IsMainChannel = 1
                             THEN NULLIF(LTRIM(RTRIM(oc.ChannelValue)), '') END),
                    MAX(CASE WHEN oc.ChannelTypeID = 1
                             THEN NULLIF(LTRIM(RTRIM(oc.ChannelValue)), '') END)
                ) AS BusinessEntityEMail,
            
                COALESCE(
                    MAX(CASE WHEN oc.ChannelTypeID = 2 AND oc.IsMainChannel = 1
                             THEN NULLIF(LTRIM(RTRIM(oc.ChannelValue)), '') END),
                    MAX(CASE WHEN oc.ChannelTypeID = 2
                             THEN NULLIF(LTRIM(RTRIM(oc.ChannelValue)), '') END)
                ) AS BusinessEntityPhone,
            
                COALESCE(
                    MAX(CASE WHEN oc.ChannelTypeID = 3 AND oc.IsMainChannel = 1
                             THEN NULLIF(LTRIM(RTRIM(oc.ChannelValue)), '') END),
                    MAX(CASE WHEN oc.ChannelTypeID = 3
                             THEN NULLIF(LTRIM(RTRIM(oc.ChannelValue)), '') END)
                ) AS Celular
            FROM orgCommunicationChannel oc
            WHERE oc.BusinessEntityID = @business_entity_id
              AND oc.DeletedOn IS NULL
            GROUP BY oc.BusinessEntityID;
            
            -- 1) Refrescar orgBusinessEntityMainInfo
            UPDATE EM
            SET
                EM.BusinessEntityEMail = COALESCE(CH.BusinessEntityEMail, EM.BusinessEntityEMail),
                EM.BusinessEntityPhone = COALESCE(CH.BusinessEntityPhone, EM.BusinessEntityPhone),
                EM.Celular             = COALESCE(CH.Celular, EM.Celular)
            FROM orgBusinessEntityMainInfo EM
            LEFT JOIN @CH CH
                ON CH.BusinessEntityID = EM.BusinessEntityID
            WHERE EM.BusinessEntityID = @business_entity_id
              AND (
                    ISNULL(EM.BusinessEntityEMail,'')  <> ISNULL(CH.BusinessEntityEMail,'')
                 OR ISNULL(EM.BusinessEntityPhone,'') <> ISNULL(CH.BusinessEntityPhone,'')
                 OR ISNULL(EM.Celular,'')             <> ISNULL(CH.Celular,'')
              );
            
            -- 2) Refrescar dirección fiscal + teléfono
            UPDATE ADT
            SET
                ADT.StateProvince      = EM.AddressFiscalStateProvince,
                ADT.City               = EM.AddressFiscalCity,
                ADT.Municipality       = EM.AddressFiscalMunicipality,
                ADT.Street             = EM.AddressFiscalStreet,
                ADT.Comments           = EM.AddressFiscalComments,
                ADT.CountryCode        = EM.AddressFiscalCountryCode,
                ADT.CityCode           = EM.AddressFiscalCityCode,
                ADT.MunicipalityCode   = EM.AddressFiscalMunicipalityCode,
                ADT.Telefono           = COALESCE(CH.BusinessEntityPhone, CH.Celular, ADT.Telefono)
            FROM orgBusinessEntityMainInfo EM
            INNER JOIN orgAddressDetail ADT
                ON EM.AddressFiscalDetailID = ADT.AddressDetailID
            LEFT JOIN @CH CH
                ON CH.BusinessEntityID = EM.BusinessEntityID
            WHERE EM.BusinessEntityID = @business_entity_id
              AND ADT.AddressDetailID = EM.AddressFiscalDetailID
              AND (
                    ISNULL(ADT.StateProvince, '')    <> ISNULL(EM.AddressFiscalStateProvince, '') OR
                    ISNULL(ADT.City, '')             <> ISNULL(EM.AddressFiscalCity, '') OR
                    ISNULL(ADT.Municipality, '')     <> ISNULL(EM.AddressFiscalMunicipality, '') OR
                    ISNULL(ADT.Street, '')           <> ISNULL(EM.AddressFiscalStreet, '') OR
                    ISNULL(ADT.Comments, '')         <> ISNULL(EM.AddressFiscalComments, '') OR
                    ISNULL(ADT.CountryCode, '')      <> ISNULL(EM.AddressFiscalCountryCode, '') OR
                    ISNULL(ADT.CityCode, '')         <> ISNULL(EM.AddressFiscalCityCode, '') OR
                    ISNULL(ADT.MunicipalityCode, '') <> ISNULL(EM.AddressFiscalMunicipalityCode, '') OR
                    ISNULL(ADT.Telefono, '')         <> ISNULL(COALESCE(CH.BusinessEntityPhone, CH.Celular, ''), '')
              );
        """, (business_entity_id,))

    def _buscar_direcciones_adicionales(self):
        direcciones_adicionales = self._base_de_datos.buscar_direcciones_adicionales(self._business_entity_id)
        self._cliente.addresses_details_backup = direcciones_adicionales
        self._direcciones_adicionales = direcciones_adicionales

    def _crear_tabs_direcciones_adicionales(self, info_pestanas):
        self._buscar_direcciones_adicionales()

        for direccion in self._direcciones_adicionales:
            nombre = direccion['AddressName']  # texto visible de la pestaña
            nombre = f"{nombre} 🏠"
            tab = nombre.replace(' ', '_').lower()
            tab = f"tab_direccion_{tab}"
            # IMPORTANTE: debe ser (texto_pestana, opciones_extra)
            info_pestanas[tab] = (nombre, None)

        return info_pestanas

    def _acompletar_valores_direccion(self, info_direccion):
        info_direccion['OfficialName'] = self._cliente.official_name
        info_direccion['ComercialName'] = self._cliente.commercial_name
        info_direccion['OfficialNumber'] = self._cliente.official_number
        info_direccion['CIF'] = self._cliente.cif
        info_direccion['IsMainAddress'] = 0

        return info_direccion