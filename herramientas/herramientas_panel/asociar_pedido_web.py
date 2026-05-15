import tkinter as tk
from cayal.ventanas import Ventanas
from cayal.cliente import Cliente


class AsociarPedidoWeb:
    def __init__(self, master, base_de_datos, utilerias, parametros, info_pedido):
        self._master = master
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._parametros = parametros
        self._ventanas = Ventanas(self._master)

        self._info_pedido = info_pedido
        self._user_id = self._parametros.id_usuario

        self._crear_frames()
        self._crear_componentes()
        self._rellenar_cbx_acciones()
        self._rellenar_tabla()
        self._cargar_eventos()

        self._ventanas.configurar_ventana_ttkbootstrap()
        self._ventanas.situar_ventana_arriba('frame_principal')

    def _crear_frames(self):
        frames = {

            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_cliente': ('frame_principal', 'Prospecto cliente:',
                              {'row': 0,  'column': 0, 'pady': 2, 'padx': 2,
                               'sticky': tk.NSEW}),

            'frame_direccion': ('frame_principal', 'Dirección prospecto:',
            {'row': 0, 'column': 1, 'pady': 2, 'padx': 2,
             'sticky': tk.NSEW}),

            'frame_acciones': ('frame_principal', None,
                              {'row': 2, 'column': 0, 'padx': 0, 'pady': 5, 'sticky': tk.W}),

            'frame_cbx': ('frame_acciones', None,
            {'row': 0, 'column': 0, 'padx': 0, 'pady': 5, 'sticky': tk.W}),

            'frame_botones': ('frame_acciones', None,
                              {'row': 0, 'column': 1, 'padx': 0, 'pady': 5, 'sticky': tk.W}),

            'frame_tabla': ('frame_principal', 'Posibles coincidencias',
                              {'row': 3, 'columnspan': 2, 'column': 0, 'pady': 2, 'padx': 2,
                               'sticky': tk.NSEW}),


        }
        self._ventanas.crear_frames(frames)

    def _crear_componentes(self):

        componentes = {
            'tbv_clientes': ('frame_tabla', self._crear_columnas_tabla(), None, None),
            'tbx_nombre': ('frame_cliente', None, 'Nombre:', None),
            'tbx_telefono': ('frame_cliente', None, 'Teléfono:', None),
            'tbx_correo': ('frame_cliente', None, 'Correo:', None),
            'tbx_direccion': ('frame_direccion', None, 'Dirección:', None),
            'tbx_calle': ('frame_direccion', None, 'Calle:', None),
            'tbx_numero': ('frame_direccion', None, 'Número:', None),
            'txt_comentarios': ('frame_direccion', None, 'Coms:', None),

            'cbx_accion': ('frame_cbx', None, 'Acción:', None),
            'btn_guardar': ('frame_botones', None, 'Guardar', None),
            'btn_cancelar': ('frame_botones', 'danger', 'Cancelar', None),

        }
        self._ventanas.crear_componentes(componentes)

        self._ventanas.ajustar_ancho_componente('tbx_nombre', 45)
        self._ventanas.ajustar_ancho_componente('tbx_correo', 45)

    def _cargar_eventos(self):
        eventos = {
            'btn_guardar':self._guardar_afectacion,
            'btn_cancelar':self._master.destroy
        }
        self._ventanas.cargar_eventos(eventos)

    def _crear_columnas_tabla(self):
        return [
            {"text": "BusinessEntityID", "stretch": False, "width": 0},
            {"text": "Cliente", "stretch": False, "width": 350},
            {"text": "NComercial", "stretch": False, "width": 350},
            {"text": "Teléfono", "stretch": False, "width": 120},
            {"text": 'Correo', "stretch": False, "width": 170}
        ]

    def _rellenar_cbx_acciones(self):
        acciones = ['Asociar', 'Crear cliente']
        self._ventanas.rellenar_cbx('cbx_accion', acciones)

    def _rellenar_tabla(self):
        info = self._obtener_info_usuario()


        nombre = info.get('FullName',None)
        telefono = info.get('Telefono', None)
        correo = info.get('Email', None)
        uuid = info.get('UUID',None)

        info_direccion = self._base_de_datos.buscar_detalle_de_direccion(address_detail_id=0, uuid=uuid)
        if not info_direccion:
            return
        info_direccion =  info_direccion[0]

        self._info_pedido['UUID'] = uuid

        if info:
            componentes  = {
                'tbx_nombre': nombre,
                'tbx_telefono': info_direccion.get('Celular', ''),
                'tbx_correo': correo,
                'tbx_direccion': info_direccion.get('AddressName', ''),
                'tbx_calle': info_direccion.get('Street', ''),
                'tbx_numero': info_direccion.get('ExtNumber', ''),
                'txt_comentarios': info_direccion.get('Comments', ''),

            }
            for componente, valor in componentes.items():
                self._ventanas.insertar_input_componente(componente, valor)
                self._ventanas.bloquear_componente(componente)


            consulta = self._buscar_clientes_probables(nombre, telefono, correo)
            if consulta:
                self._ventanas.rellenar_table_view('tbv_clientes', self._crear_columnas_tabla(), consulta)

    def _obtener_info_usuario(self):

        uuid = self._base_de_datos.fetchone(
            'SELECT UUID FROM docDocumentOrderCayal WHERE OrderDocumentID = ?',
            (self._info_pedido['OrderDocumentID'],)
        )
        if not uuid:
            return {}
        uuid = str(uuid)
        info = self._base_de_datos.fetchall("""
            SELECT 
                FullName, 
                Email,
                NULL Telefono,
                ReceptorUsoCFDI,
                RFC,
                MetodoPago,
                FormaPago,
                CompanyTypeName,
                FiscalZipCode
            FROM engUserClient
            WHERE FirstOrderUUID= ?
        """,(uuid,))
        if not info:
            return {}

        info = info[0]
        info['UUID'] = uuid

        return info

    def _buscar_clientes_probables(self, nombre, telefono, correo):
        return  self._base_de_datos.fetchall("""
            DECLARE @NombreBuscado   NVARCHAR(200) = ?;
            DECLARE @TelefonoBuscado NVARCHAR(50)  = ?;
            DECLARE @CorreoBuscado   NVARCHAR(200) = ?;
            
            SELECT 
                E.BusinessEntityID,
                E.OfficialName,
                E.CommercialName,
                Telefono.ChannelValue AS Telefono,
                Correo.ChannelValue   AS Correo
                
            FROM orgBusinessEntity E
            
            LEFT JOIN (
                SELECT 
                    CH.BusinessEntityID,
                    CH.ChannelValue
                FROM orgCommunicationChannel CH
                WHERE 
                    CH.DeletedOn IS NULL
                    AND CH.ChannelTypeID = 1
            ) Correo 
                ON E.BusinessEntityID = Correo.BusinessEntityID
            
            LEFT JOIN (
                SELECT 
                    CH.BusinessEntityID,
                    CH.ChannelValue
                FROM orgCommunicationChannel CH
                WHERE 
                    CH.DeletedOn IS NULL
                    AND CH.ChannelTypeID = 2
            ) Telefono 
                ON E.BusinessEntityID = Telefono.BusinessEntityID
            
            WHERE 
                E.DeletedOn IS NULL
            
                AND
                (
                    (
                        @NombreBuscado IS NOT NULL
                        AND @NombreBuscado <> ''
                        AND
                        (
                            E.OfficialName LIKE '%' + REPLACE(@NombreBuscado, ' ', '%') + '%'
                            OR E.CommercialName LIKE '%' + REPLACE(@NombreBuscado, ' ', '%') + '%'
                        )
                    )
            
                    OR
            
                    (
                        @TelefonoBuscado IS NOT NULL
                        AND @TelefonoBuscado <> ''
                        AND
                        REPLACE(
                            REPLACE(
                                REPLACE(
                                    REPLACE(ISNULL(Telefono.ChannelValue, ''), ' ', ''),
                                '-', ''),
                            '(', ''),
                        ')', '')
                        LIKE '%' + @TelefonoBuscado + '%'
                    )
            
                    OR
            
                    (
                        @CorreoBuscado IS NOT NULL
                        AND @CorreoBuscado <> ''
                        AND
                        ISNULL(Correo.ChannelValue, '') LIKE '%' + @CorreoBuscado + '%'
                    )
                )
            
            ORDER BY 
                E.OfficialName;
        """,(nombre, telefono, correo))

    def _asociar_informacion_y_pedido_cliente_existente(self, business_entity_id):

        uuid = self._info_pedido.get('UUID',None)
        customer_type_id = 2
        invoice = 0

        info_complementaria = self._base_de_datos.fetchall("""
            SELECT CustomerTypeID, CayalCustomerTypeID FROM [zvwBuscarInfoCliente-BusinessEntityID](?)
        """,(business_entity_id,))

        if info_complementaria:
            customer_type_id = info_complementaria[0]['CustomerTypeID']
            cayal_customer_type_id = info_complementaria[0]['CayalCustomerTypeID']
            invoice = 0 if cayal_customer_type_id == 1 else 1
        if uuid:
            self._base_de_datos.command("""
                DECLARE @BusinessEntityID INT = ?
                DECLARE @UUID NVARCHAR(125) = ?
                DECLARE @Invoice INT = ?
                DECLARE @CustomerTypeID INT = ?
                
                UPDATE docDocumentOrderCayal SET BusinessEntityID = @BusinessEntityID WHERE UUID = @UUID 
                
                UPDATE orgAddress SET BusinessEntityID = @BusinessEntityID WHERE UUID = @UUID
                
                UPDATE engUserClient SET 
                                    BusinessEntityID = @BusinessEntityID,
                                    CustomerTypeID = @CustomerTypeID,
                                    Invoice = @Invoice
                        WHERE FirstOrderUUID = @UUID 
           """,(business_entity_id, uuid, invoice, customer_type_id))


    def _obtener_valores_fila_pedido_seleccionado(self, valor=None):
        if not self._ventanas.validar_seleccion_una_fila_table_view('tbv_clientes'):
            return
        valores_fila = self._ventanas.procesar_filas_table_view('tbv_clientes', seleccionadas=True)[0]
        if not valor:
            return valores_fila
        return valores_fila[valor]

    def _crear_cliente_desde_web(self):
        cliente = Cliente()
        self._settear_valores_formulario_a_cliente(cliente)
        business_entity_id = self._base_de_datos.crear_cliente(cliente, self._user_id, crear_direccion=False)
        cliente.business_entity_id = business_entity_id
        self._merge_direccion(cliente)

        return business_entity_id

    def _guardar_afectacion(self):
        seleccion = self._ventanas.obtener_input_componente('cbx_accion')
        business_entity_id = 0

        if seleccion == 'Seleccione':
            self._ventanas.mostrar_mensaje('Debe seleccionar una opción válida.')
            return

        if seleccion == 'Asociar':
            business_entity_id = self._obtener_valores_fila_pedido_seleccionado(valor='BusinessEntityID')


        if seleccion == 'Crear cliente':
            respuesta = self._ventanas.mostrar_mensaje_pregunta(
                mensaje='Se creará un cliente con la información proporcionada al capturar el pedido,'
                                                   '¿Está seguro de proceder?')
            if not respuesta:
                return

            business_entity_id = self._crear_cliente_desde_web()

        self._asociar_informacion_y_pedido_cliente_existente(business_entity_id)
        self._ventanas.mostrar_mensaje(mensaje='Cliente asociado satisfactoriamente', tipo='info')
        self._master.destroy()

    def _settear_valores_formulario_a_cliente(self, cliente):

        info_usuario = self._obtener_info_usuario()
        nombre_cliente = info_usuario.get('FullName', 'Cliente Nuevo')
        email = info_usuario.get('Email',None)
        telefono = info_usuario.get('Telefono', None)
        uuid_direccion = info_usuario.get('UUID', None)

        uso_cfdi = info_usuario.get('ReceptorUsoCFDI',None)
        rfc = info_usuario.get('RFC', None)
        metodo_pago = info_usuario.get('MetodoPago', None)
        forma_pago = info_usuario.get('FormaPago', None)
        regimen_fiscal = info_usuario.get('CompanyTypeName', None)

        info_direccion = self._base_de_datos.buscar_detalle_de_direccion(address_detail_id=0, uuid=uuid_direccion)
        if not info_direccion:
            return

        info_direccion = info_direccion[0]
        zone_id = self._base_de_datos.fetchone(
            'SELECT Top 1 ZoneID FROM zvwColoniasCampeche WHERE Colonia = ?',
            (info_direccion['City'],)
        )
        zone_name = self._base_de_datos.fetchone(
            'SELECT ZoneName FROM orgZone WHERE ZoneID = ?',
            (zone_id,)
        )

        # -----------------------------------------
        # 1) Atributos de dirección fiscal del cliente
        # -----------------------------------------
        atributos_equivalentes = {
            'official_name': nombre_cliente,
            'commercial_name': '',
            'phone': None,
            'cellphone': telefono,
            'address_fiscal_detail_id': info_direccion.get('AddressDetailID',''),
            'address_fiscal_street': info_direccion.get('Street',''),
            'address_fiscal_ext_number': info_direccion.get('ExtNumber',''),
            'address_fiscal_comments': info_direccion.get('Comments',''),
            'address_fiscal_zip_code': info_direccion.get('ZipCode',''),
            'delivery_cost': info_direccion.get('DeliveryCost',''),
            'zone_name': zone_name,
            'address_fiscal_city': info_direccion.get('Street',''),
            'email': email,
            'address_fiscal_state_province': info_direccion.get('StateProvince',''),
            'address_fiscal_municipality': info_direccion.get('Municipality',''),
            'country_code' : info_direccion.get('CountryCode', ''),
            'state_code' : info_direccion.get('StateCode', ''),
            'city_code' : info_direccion.get('CityCode', ''),
            'municipality_code' : info_direccion.get('MunicipalityCode', ''),

            'zone_id': zone_id,
            'company_type_name': regimen_fiscal,
            'official_number': rfc,
            'cif': None,
            'forma_pago':forma_pago,
            'metodo_pago':metodo_pago,
            'receptor_uso_cfdi':uso_cfdi
        }

        for atributo_cliente, valor in atributos_equivalentes.items():

            # Tratamientos especiales por tipo de dato
            if atributo_cliente == 'delivery_cost':
                # Si viene vacío, asumimos 20
                try:
                    valor = float(valor) if valor not in (None, '') else 20
                except ValueError:
                    valor = 20

            # Asignar al cliente
            setattr(cliente, atributo_cliente, valor)


    def _merge_direccion(self, cliente):
        self._base_de_datos.command("""
                            MERGE INTO orgBusinessEntityMainInfo AS target
                            USING (
                                VALUES (
                                    ?, ?, ?, ?,       -- BusinessEntityID, OfficialNumber, Phone, Email
                                    ?,                -- AddressFiscalDetailID
                                    'Dirección fiscal', 'MEXICO',
                                    ?, ?, ?, ?, ?, ?, ?,          -- State, City, Zip, Municipality, Street, ExtNumber, Comments
                                    'MEX',
                                    ?, ?, ?,          -- StateCode, CityCode, MunicipalityCode
                                    0                 -- AddressDeliveryDetailID
                                )
                            ) AS source (
                                BusinessEntityID,
                                OfficialNumber,
                                BusinessEntityPhone,
                                BusinessEntityEmail,
                                AddressFiscalDetailID,
                                AddressFiscalName,
                                AddressFiscalCountryName,
                                AddressFiscalStateProvince,
                                AddressFiscalCity,
                                AddressFiscalZipCode,
                                AddressFiscalMunicipality,
                                AddressFiscalStreet,
                                AddressFiscalExtNumber,
                                AddressFiscalComments,
                                AddressFiscalCountryCode,
                                AddressFiscalStateProvinceCode,
                                AddressFiscalCityCode,
                                AddressFiscalMunicipalityCode,
                                AddressDeliveryDetailID
                            )
                            ON target.BusinessEntityID = source.BusinessEntityID
                            WHEN MATCHED THEN
                                UPDATE SET
                                    target.OfficialNumber                  = source.OfficialNumber,
                                    target.BusinessEntityPhone             = source.BusinessEntityPhone,
                                    target.BusinessEntityEmail             = source.BusinessEntityEmail,
                                    target.AddressFiscalDetailID           = source.AddressFiscalDetailID,
                                    target.AddressFiscalName               = source.AddressFiscalName,
                                    target.AddressFiscalCountryName        = source.AddressFiscalCountryName,
                                    target.AddressFiscalStateProvince      = source.AddressFiscalStateProvince,
                                    target.AddressFiscalCity               = source.AddressFiscalCity,
                                    target.AddressFiscalZipCode            = source.AddressFiscalZipCode,
                                    target.AddressFiscalMunicipality       = source.AddressFiscalMunicipality,
                                    target.AddressFiscalStreet             = source.AddressFiscalStreet,
                                    target.AddressFiscalExtNumber          = source.AddressFiscalExtNumber,
                                    target.AddressFiscalComments           = source.AddressFiscalComments,
                                    target.AddressFiscalCountryCode        = source.AddressFiscalCountryCode,
                                    target.AddressFiscalStateProvinceCode  = source.AddressFiscalStateProvinceCode,
                                    target.AddressFiscalCityCode           = source.AddressFiscalCityCode,
                                    target.AddressFiscalMunicipalityCode   = source.AddressFiscalMunicipalityCode,
                                    target.AddressDeliveryDetailID         = source.AddressDeliveryDetailID
                            WHEN NOT MATCHED THEN
                                INSERT (
                                    BusinessEntityID,
                                    OfficialNumber,
                                    BusinessEntityPhone,
                                    BusinessEntityEmail,
                                    AddressFiscalDetailID,
                                    AddressFiscalName,
                                    AddressFiscalCountryName,
                                    AddressFiscalStateProvince,
                                    AddressFiscalCity,
                                    AddressFiscalZipCode,
                                    AddressFiscalMunicipality,
                                    AddressFiscalStreet,
                                    AddressFiscalExtNumber,
                                    AddressFiscalComments,
                                    AddressFiscalCountryCode,
                                    AddressFiscalStateProvinceCode,
                                    AddressFiscalCityCode,
                                    AddressFiscalMunicipalityCode,
                                    AddressDeliveryDetailID
                                )
                                VALUES (
                                    source.BusinessEntityID,
                                    source.OfficialNumber,
                                    source.BusinessEntityPhone,
                                    source.BusinessEntityEmail,
                                    source.AddressFiscalDetailID,
                                    source.AddressFiscalName,
                                    source.AddressFiscalCountryName,
                                    source.AddressFiscalStateProvince,
                                    source.AddressFiscalCity,
                                    source.AddressFiscalZipCode,
                                    source.AddressFiscalMunicipality,
                                    source.AddressFiscalStreet,
                                    source.AddressFiscalExtNumber,
                                    source.AddressFiscalComments,
                                    source.AddressFiscalCountryCode,
                                    source.AddressFiscalStateProvinceCode,
                                    source.AddressFiscalCityCode,
                                    source.AddressFiscalMunicipalityCode,
                                    source.AddressDeliveryDetailID
                                );
                        """, (
                cliente.business_entity_id,
                cliente.official_number,
                cliente.phone,
                cliente.email,
                cliente.address_fiscal_detail_id,
                cliente.address_fiscal_state_province,
                cliente.address_fiscal_city,
                cliente.address_fiscal_zip_code,
                cliente.address_fiscal_municipality,
                cliente.address_fiscal_street,
                cliente.address_fiscal_ext_number,
                cliente.address_fiscal_comments,
                cliente.state_code,
                cliente.city_code,
                cliente.municipality_code
            ))

        self._base_de_datos.command(
            'UPDATE orgAddress set AddressTypeID=1, IsMainAddress=1 where BusinessEntityID=?',
            (cliente.business_entity_id,)
        )