

class FormularioClienteModelo:
    def __init__(self, parametros, utilerias=None, base_de_datos=None, cliente = None):
        """
        Modelo para el formulario de clientes.

        Parámetros
        ----------
        parametros : Any
            Parámetros de contexto (usuario, sucursal, etc.).
        utilerias : Utilerias, opcional
            Instancia de utilerías; si no se proporciona, se crea una nueva.
        base_de_datos : ComandosBaseDatos, opcional
            Instancia de acceso a base de datos; si no se proporciona, se crea una nueva.
        """
        # Importar aquí evita dependencias circulares al importar el módulo
        from cayal.comandos_base_datos import ComandosBaseDatos
        from cayal.util import Utilerias
        from cayal.cliente import Cliente

        # Inyección de dependencias con fallback
        self.base_de_datos = base_de_datos if base_de_datos is not None else ComandosBaseDatos()
        self.utilerias = utilerias if utilerias is not None else Utilerias()
        self.cliente = cliente if cliente is not None else Cliente()
        self.parametros = parametros

        self.user_id = self.parametros.id_usuario
        self.business_entity_id = self.parametros.id_principal
        self.module_id = self.parametros.id_modulo

        self.consulta_uso_cfdi = []
        self.consulta_formas_pago = []
        self.consulta_metodos_pago = []
        self.consulta_regimenes = []
        self.consulta_rutas = []
        self.consulta_colonias = []

    def obtener_todas_las_rutas(self):
        if not self.consulta_rutas:
            self.consulta_rutas = self.base_de_datos.fetchall("""
                SELECT Z.ZoneID, Z.ZoneName, Z.TipoRutaID, Z.CargoEnvio
                FROM orgZone Z
                WHERE Z.CargoEnvio IS NOT NULL
                    AND Z.ZoneID NOT IN (1039) -- Calkini
            """)
        return self.consulta_rutas

    def obtener_info_cliente(self, business_entity_id):
        return self.base_de_datos.fetchall("""
            SELECT * FROM [dbo].[zvwBuscarInfoCliente-BusinessEntityID](?)
        """, (business_entity_id,))

    def obtener_regimenes_fiscales(self):
        if not self.consulta_regimenes:
            self.consulta_regimenes = self.base_de_datos.fetchall('SELECT * FROM vwcboAnexo20v40_RegimenFiscal', ())

        return self.consulta_regimenes

    def obtener_formas_pago(self):
        if not self.consulta_formas_pago:
            self.consulta_formas_pago = self.base_de_datos.fetchall("""
                                -- formas de pago aceptadas por cayal
                                SELECT * FROM vwcboAnexo20v33_FormaPago WHERE ID IN (1, 2, 3, 4, 28, 99)
                                """, ())

        return self.consulta_formas_pago

    def obtener_metodos_pago(self):
        if not self.consulta_metodos_pago:
            self.consulta_metodos_pago = self.base_de_datos.fetchall("""
                        SELECT * FROM vwcboAnexo20v33_MetodoDePago
                        """, ())
        return self.consulta_metodos_pago

    def obtener_uso_cfdi(self):
        if not self.consulta_uso_cfdi:
            self.consulta_uso_cfdi = self.base_de_datos.fetchall("""
                                -- omite usos de cfdi no validos para cayal
                                SELECT * FROM vwcboAnexo20v40_UsoCFDI WHERE ID NOT IN (12, 23) ORDER BY ID
                                """, ())
        return self.consulta_uso_cfdi

    def obtener_colonias(self, address_detail_id=0, zip_code=None):
        consulta = []

        if zip_code:
            consulta = self.base_de_datos.fetchall("""
                           SELECT 
                                   CountryAddressID,
                                   City,
                                   Municipality,
                                   ZipCode,
                                   CountryCode,
                                   CityCode,
                                   MunicipalityCode,
                                   ZoneID,
                                   StateCode,
                                   State
                           FROM engRefCountryAddress
                           WHERE ZipCode = ?
                       """,(zip_code,))

        if address_detail_id != 0:
            consulta = self.base_de_datos.fetchall("""
                    SELECT 
                            CA.CountryAddressID,
                            CA.City,
                            CA.Municipality,
                            CA.ZipCode,
                            CA.CountryCode,
                            CA.CityCode,
                            CA.MunicipalityCode,
                            CA.ZoneID,
                            CA.StateCode,
                            CA.State
                    FROM engRefCountryAddress CA
                        INNER JOIN orgAddressDetail AD ON CA.ZipCode = AD.ZipCode
                    WHERE AD.AddressDetailID = ?
            """,(address_detail_id,))

            if consulta:
                municipality = consulta[0]['Municipality']
                if municipality.lower() == 'campeche':
                    consulta = [reg for reg in consulta if reg['ZoneID']]


        if address_detail_id == 0:
            consulta = self.base_de_datos.fetchall("""
                    SELECT 
                            CountryAddressID,
                            City,
                            Municipality,
                            ZipCode,
                            CountryCode,
                            CityCode,
                            MunicipalityCode,
                            ZoneID,
                            StateCode,
                            State
                    FROM engRefCountryAddress
                    WHERE ZoneID IS NOT NULL
                """)



        self.consulta_colonias = consulta

        return self.consulta_colonias

    def homologar_direccion_fiscal(self, business_entity_id):
        # esta funcion es deuda tecnica de la homologacion entre la direccion fiscal
        # y orgbusinessentitymaininfo que es la tabla donde nace los parametros
        # de la direccion fiscal del cliente, esto es necesario para coherencia en
        # la información y la impresion de los formatos del cliente

        self.base_de_datos.command("""
           DECLARE @business_entity_id INT = ?
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
                ADT.Telefono           = EM.BusinessEntityPhone
            FROM orgBusinessEntityMainInfo EM
            INNER JOIN orgAddressDetail ADT ON EM.AddressFiscalDetailID = ADT.AddressDetailID
            WHERE
                ADT.AddressDetailID = (SELECT AddressFiscalDetailID from orgBusinessEntityMainInfo WHERE BusinessEntityID = @business_entity_id)
                AND (
                    ISNULL(ADT.StateProvince, '')       <> ISNULL(EM.AddressFiscalStateProvince, '') OR
                    ISNULL(ADT.City, '')                <> ISNULL(EM.AddressFiscalCity, '') OR
                    ISNULL(ADT.Municipality, '')        <> ISNULL(EM.AddressFiscalMunicipality, '') OR
                    ISNULL(ADT.Street, '')              <> ISNULL(EM.AddressFiscalStreet, '') OR
                    ISNULL(ADT.Comments, '')            <> ISNULL(EM.AddressFiscalComments, '') OR
                    ISNULL(ADT.CountryCode, '')         <> ISNULL(EM.AddressFiscalCountryCode, '') OR
                    ISNULL(ADT.CityCode, '')            <> ISNULL(EM.AddressFiscalCityCode, '') OR
                    ISNULL(ADT.MunicipalityCode, '')    <> ISNULL(EM.AddressFiscalMunicipalityCode, '') OR
                    ISNULL(ADT.Telefono, '')            <> ISNULL(EM.BusinessEntityPhone, '')
                );

        """,(business_entity_id,))


