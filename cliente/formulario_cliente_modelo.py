

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
