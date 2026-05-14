from cayal.ventanas import Ventanas
from cayal.cliente import Cliente


class AsociarPedidoWeb:
    def __init__(self, master, base_de_datos, utilerias, info_pedido):
        self._master = master
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._ventanas = Ventanas(self._master)

        self._info_pedido = info_pedido

        self._crear_componentes()
        self._rellenar_cbx_acciones()
        self._rellenar_tabla()
        self._cargar_eventos()

        self._ventanas.configurar_ventana_ttkbootstrap()

    def _crear_componentes(self):
        componentes = [
            ('tbx_nombre', 'Nombre:'),
            ('tbx_telefono', 'Teléfono:'),
            ('tbx_correo', 'Correo:'),
            ('cbx_accion', 'Acción:'),
            ('tbv_clientes', self._crear_columnas_tabla()),
            ('btn_guardar', 'Guardar')
        ]

        self._ventanas.crear_formulario_simple(componentes)
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

        self._info_pedido['UUID'] = uuid

        if info:
            componentes  = {
                'tbx_nombre': nombre,
                'tbx_telefono': telefono,
                'tbx_correo': correo
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
            (self._info_pedido['OrderDocumentID'])
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

        info['UUID'] = uuid

        return info[0] if info else {}

    def _buscar_clientes_probables(self, nombre, telefono, correo):
        return  self._base_de_datos.fetchall("""
            DECLARE @NombreBuscado   NVARCHAR(200) = ?;
            DECLARE @TelefonoBuscado NVARCHAR(50)  = ?;
            DECLARE @CorreoBuscado   NVARCHAR(200) = ?;
            
            SELECT 
                E.BusinessEntityID,
                E.OfficialName,
                E.CommercialName,
                Correo.ChannelValue   AS Correo,
                Telefono.ChannelValue AS Telefono
                
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

        info_complementaria = self._base_de_datos.fetchall("""
            SELECT CustomerTypeID, CayalCustomerTypeID FROM [zvwBuscarInfoCliente-BusinessEntityID](?)
        """,(business_entity_id,))

        if not info_complementaria:
            return

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
                        WHERE UUID = @UUID 
           """,(business_entity_id, uuid, invoice, customer_type_id))



    def _obtener_valores_fila_pedido_seleccionado(self, valor=None):
        if not self._ventanas.validar_seleccion_una_fila_table_view('tbv_clientes'):
            return
        valores_fila = self._ventanas.procesar_filas_table_view('tbv_clientes', seleccionadas=True)[0]
        if not valor:
            return valores_fila
        return valores_fila[valor]

    def _crear_cliente_desde_web(self):
        business_entity_id = 0

        cliente = Cliente()
        self._settear_valores_formulario_a_cliente(cliente)

        cliente.business_entity_id = 0

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

        zone_id = self._base_de_datos.fetchone(
            'SELECT ZoneID FROM zvwColoniasCampeche WHERE Colonia = ?',
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


