

class FormularioClienteModelo:
    def __init__(self, parametros, utilerias=None, base_de_datos=None, cliente = None):

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
        self.user_group_id = self.base_de_datos.fetchone(
            'SELECT UserGroupID FROM engUser WHERE UserID = ?',
            (self.user_id,))
        self.user_name = self.base_de_datos.buscar_nombre_de_usuario(self.user_id)

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

        # 1) Si viene address_detail_id, tiene prioridad
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
                        CA.State,
                        Z.ZoneName
                FROM engRefCountryAddress CA
                    INNER JOIN orgAddressDetail AD ON CA.ZipCode = AD.ZipCode
                    LEFT OUTER JOIN orgZone Z ON CA.ZoneID = Z.ZoneID
                WHERE AD.AddressDetailID = ?
            """, (address_detail_id,))

            # Si es Campeche, filtrar solo las que tengan ZoneID (no nulo / no cero)
            if consulta:
                municipality = consulta[0]['Municipality']
                if municipality and municipality.lower() == 'campeche':
                    consulta = [reg for reg in consulta if reg['ZoneID']]

        # 2) Si no hay address_detail_id pero sí zip_code → buscar por CP
        elif zip_code:
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
                        CA.State,
                        Z.ZoneName
                FROM engRefCountryAddress CA
                    LEFT OUTER JOIN orgZone Z ON CA.ZoneID = Z.ZoneID
                WHERE CA.ZipCode = ?
            """, (zip_code,))

        # 3) Sin address_detail_id ni zip_code → todas las colonias con ZoneID
        else:
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
                        CA.State,
                        Z.ZoneName
                FROM engRefCountryAddress CA
                    LEFT OUTER JOIN orgZone Z ON CA.ZoneID = Z.ZoneID
                WHERE CA.ZoneID IS NOT NULL
            """)

        self.consulta_colonias = consulta
        return self.consulta_colonias

    def obtener_envio_por_colonia(self, colonia):
        consulta = self.base_de_datos.fetchall("""
            SELECT TOP 1 ISNULL(Z.CargoEnvio, 20) AS DeliveryCost
            FROM engRefCountryAddress EF
                INNER JOIN orgZone Z ON EF.ZoneID = Z.ZoneID 
            WHERE 
                EF.State = 'Campeche'
                AND EF.City = ?
        """,(colonia,))

        if not consulta:
            return self.utilerias.redondear_valor_cantidad_a_decimal(20)

        if consulta:
            return self.utilerias.redondear_valor_cantidad_a_decimal(consulta[0]['DeliveryCost'])

    def obtener_cp_por_colonia(self, colonia, estado, municipio):
        consulta = self.base_de_datos.fetchall("""
                    SELECT TOP 1 ZipCode
                    FROM engRefCountryAddress EF
                    WHERE 
                        EF.State = ?
                        AND EF.Municipality = ?
                        AND EF.City = ?
                """, (estado, municipio, colonia,))
        if consulta:
            return consulta[0]['ZipCode']

    def obtener_info_colonia(self, colonia, estado, municipio):
        consulta = self.base_de_datos.fetchall("""
                            SELECT TOP 1 StateCode,	AutonomiaCode,	CountryID,	CountryCode,	Pais,	CityCode
                            FROM engRefCountryAddress EF
                            WHERE 
                                EF.State = ?
                                AND EF.Municipality = ?
                                AND EF.City = ?
                        """, (estado, municipio, colonia,))
        if consulta:
            return consulta[0]

        return {}

    def obtener_estado_y_municipio_colonia(self, colonia):
        consulta = [reg for reg in self.consulta_colonias if reg['City'] == colonia]
        if consulta:
            return consulta[0]['State'], consulta[0]['Municipality']
        if not consulta:
            return 'Campeche', 'Campeche'

    def buscar_tipo_ruta_id(self, nombre_ruta):
        consulta = [ruta['TipoRutaID'] for ruta in self.consulta_rutas
                    if nombre_ruta == ruta['ZoneName']]
        # 1 = domicilio (por defecto si no la encuentra)
        return consulta[0] if consulta else 1

    def buscar_ruta_id(self, nombre_ruta):
        consulta = [ruta['ZoneID'] for ruta in self.consulta_rutas
                    if nombre_ruta == ruta['ZoneName']]
        # 0 = sin ruta encontrada
        return consulta[0] if consulta else 0