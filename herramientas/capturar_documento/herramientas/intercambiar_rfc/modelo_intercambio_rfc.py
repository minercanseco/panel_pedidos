from cayal.comandos_base_datos import ComandosBaseDatos


class ModeloIntercambioRFC:
    RFC_GENERICO = 'XAXX010101000'
    REGIMEN_GENERICO = '616 - Sin obligaciones fiscales'
    FORMA_PAGO_GENERICA = '01'
    METODO_PAGO_GENERICO = 'PUE'
    USO_CFDI_GENERICO = 'S01'
    CLIENTES_PROTEGIDOS = {
        8179: 'PUBLICO EN GENERAL',
        9277: 'PG',
    }
    MODULOS_VENTAS = (21,1400,1316,1319)

    def __init__(self, parametros):
        self.parametros = parametros
        self.base_de_datos = ComandosBaseDatos()
        self.user_id = self.parametros.id_usuario
        self.module_id = self.parametros.id_modulo
        self.document_id = self.parametros.id_principal
        self.business_entity_id = self.obtener_business_entity_id_documento(self.document_id) if self.module_id in self.MODULOS_VENTAS else  self.obtener_business_entity_id_orcustomer(self.document_id)

        self.consulta_info_cliente = []
        self.consulta_metodos_pago = []
        self.consulta_formas_pago = []
        self.consulta_uso_cfdi = []

    def obtener_business_entity_id_documento(self, document_id):
        return self.base_de_datos.fetchone(
            'SELECT BusinessEntityID '
            'FROM [dbo].[zvwBuscarBusinessEntityID-DocumentID](?)',
            (document_id,),
        )

    def obtener_business_entity_id_orcustomer(self, customer_id):
        return self.base_de_datos.fetchone(
            'SELECT BusinessEntityID '
            'FROM orgCustomer WHERE CustomerID = ?',
            (customer_id,),
        )

    def obtener_info_cliente(self, business_entity_id, actualizar=False):
        if actualizar:
            self.consulta_info_cliente = []

        if not self.consulta_info_cliente:
            self.consulta_info_cliente = (
                self.base_de_datos.buscar_info_cliente(business_entity_id)
            )
        return self.consulta_info_cliente

    def obtener_formas_pago(self):
        if not self.consulta_formas_pago:
            self.consulta_formas_pago = (
                self.base_de_datos.buscar_formas_de_pago()
            )
        return self.consulta_formas_pago

    def obtener_metodos_pago(self):
        if not self.consulta_metodos_pago:
            self.consulta_metodos_pago = (
                self.base_de_datos.buscar_metodos_de_pago()
            )
        return self.consulta_metodos_pago

    def obtener_usos_cfdi(self):
        if not self.consulta_uso_cfdi:
            self.consulta_uso_cfdi = (
                self.base_de_datos.buscar_usos_de_cfdi()
            )
        return self.consulta_uso_cfdi

    def obtener_respaldos_pago(self):
        consulta = self.base_de_datos.fetchall(
            """
                SELECT
                    ResFormaPago,
                    ResMetodoPago,
                    ResReceptorUsoCFDI
                FROM orgCustomer
                WHERE BusinessEntityID = ?
            """,
            (self.business_entity_id,),
        )
        return consulta[0] if consulta else {}

    def intercambiar_rfc(self, forma_pago, metodo_pago, uso_cfdi):
        cliente_protegido = self.CLIENTES_PROTEGIDOS.get(
            self.business_entity_id
        )
        if cliente_protegido:
            return {
                'ok': False,
                'mensaje': (
                    f'No se deben cambiar los datos del cliente '
                    f'{cliente_protegido}.'
                ),
            }

        consulta = self.obtener_info_cliente(
            self.business_entity_id,
            actualizar=True,
        )
        if not consulta:
            return {
                'ok': False,
                'mensaje': 'No se encontró información relacionada al cliente.',
            }

        cliente = consulta[0]
        rfc_actual = (cliente.get('OfficialNumber') or '').strip()
        regimen_actual = (cliente.get('CompanyTypeName') or '').strip()
        rfc_respaldo = (cliente.get('OfficialNumberBackup') or '').strip()
        regimen_respaldo = (
            cliente.get('CompanyTypeNameBackup') or ''
        ).strip()

        if rfc_actual == self.RFC_GENERICO:
            if not self._rfc_respaldo_valido(rfc_respaldo):
                return {
                    'ok': False,
                    'mensaje': (
                        'El cliente no cuenta con un RFC respaldado válido '
                        'para restaurar.'
                    ),
                }
            if not regimen_respaldo:
                return {
                    'ok': False,
                    'mensaje': (
                        'El cliente no cuenta con un régimen fiscal '
                        'respaldado para restaurar.'
                    ),
                }

            respaldos_pago = self.obtener_respaldos_pago()
            forma_pago_respaldo = (
                respaldos_pago.get('ResFormaPago') or forma_pago
            )
            metodo_pago_respaldo = (
                respaldos_pago.get('ResMetodoPago') or metodo_pago
            )
            uso_cfdi_respaldo = (
                respaldos_pago.get('ResReceptorUsoCFDI') or uso_cfdi
            )

            self._restaurar_datos_fiscales(
                cliente,
                rfc_respaldo,
                regimen_respaldo,
                forma_pago_respaldo,
                metodo_pago_respaldo,
                uso_cfdi_respaldo,
            )
            mensaje = 'RFC y régimen fiscal restaurados correctamente.'
            accion = 'restaurado'
        else:
            if not rfc_actual:
                return {
                    'ok': False,
                    'mensaje': 'El cliente no cuenta con un RFC para respaldar.',
                }
            if not regimen_actual:
                return {
                    'ok': False,
                    'mensaje': (
                        'El cliente no cuenta con un régimen fiscal para '
                        'respaldar.'
                    ),
                }

            # Custom3 recibe el RFC actual. El régimen respaldado solo se
            # inicializa si todavía no contiene un respaldo fiscal válido.
            # Esto incluye expresamente a clientes legacy de tipo 0 y 1.
            self._usar_datos_genericos(
                cliente,
                rfc_actual,
                regimen_actual,
                forma_pago,
                metodo_pago,
                uso_cfdi,
            )
            mensaje = (
                'RFC y régimen fiscal respaldados; se aplicaron los datos '
                'genéricos correctamente.'
            )
            accion = 'respaldado'

        self.consulta_info_cliente = []
        return {'ok': True, 'mensaje': mensaje, 'accion': accion}

    def _usar_datos_genericos(
        self,
        cliente,
        rfc_actual,
        regimen_actual,
        forma_pago,
        metodo_pago,
        uso_cfdi,
    ):
        self._ejecutar_intercambio(
            cliente=cliente,
            rfc_nuevo=self.RFC_GENERICO,
            regimen_nuevo=self.REGIMEN_GENERICO,
            rfc_respaldo=rfc_actual,
            regimen_respaldo=regimen_actual,
            business_entity_type_id=2,
            category_type_id=2,
            forma_pago=self.FORMA_PAGO_GENERICA,
            metodo_pago=self.METODO_PAGO_GENERICO,
            uso_cfdi=self.USO_CFDI_GENERICO,
            respaldar_datos_pago=True,
            forma_pago_respaldo=cliente.get('FormaPago') or forma_pago,
            metodo_pago_respaldo=cliente.get('MetodoPago') or metodo_pago,
            uso_cfdi_respaldo=(
                cliente.get('ReceptorUsoCFDI') or uso_cfdi
            ),
            incidencia_rfc=(
                'ACTUALIZACIÓN DE RFC A PUBLICO EN GENERAL '
                'POR CANCELACION DE DOCTO'
            ),
            incidencia_regimen=(
                'ACTUALIZACIÓN DE REGIMEN FISCAL A PUBLICO EN GENERAL '
                'POR CANCELACION DE DOCTO'
            ),
        )

    def _restaurar_datos_fiscales(
        self,
        cliente,
        rfc_respaldo,
        regimen_respaldo,
        forma_pago,
        metodo_pago,
        uso_cfdi,
    ):
        es_persona_fisica = len(rfc_respaldo) == 13
        tipo_persona = 'FISICA' if es_persona_fisica else 'MORAL'

        self._ejecutar_intercambio(
            cliente=cliente,
            rfc_nuevo=rfc_respaldo,
            regimen_nuevo=regimen_respaldo,
            rfc_respaldo=rfc_respaldo,
            regimen_respaldo=regimen_respaldo,
            business_entity_type_id=2 if es_persona_fisica else 1,
            category_type_id=1,
            forma_pago=forma_pago,
            metodo_pago=metodo_pago,
            uso_cfdi=uso_cfdi,
            respaldar_datos_pago=False,
            forma_pago_respaldo=forma_pago,
            metodo_pago_respaldo=metodo_pago,
            uso_cfdi_respaldo=uso_cfdi,
            incidencia_rfc=(
                f'ACTUALIZACIÓN DE RFC A PERSONA {tipo_persona} '
                'POR CANCELACION DE DOCTO'
            ),
            incidencia_regimen=(
                f'ACTUALIZACIÓN DE REGIMEN FISCAL A PERSONA {tipo_persona} '
                'POR CANCELACION DE DOCTO'
            ),
        )

    def _ejecutar_intercambio(
        self,
        cliente,
        rfc_nuevo,
        regimen_nuevo,
        rfc_respaldo,
        regimen_respaldo,
        business_entity_type_id,
        category_type_id,
        forma_pago,
        metodo_pago,
        uso_cfdi,
        respaldar_datos_pago,
        forma_pago_respaldo,
        metodo_pago_respaldo,
        uso_cfdi_respaldo,
        incidencia_rfc,
        incidencia_regimen,
    ):
        sql = """
            SET NOCOUNT ON;
            SET XACT_ABORT ON;

            BEGIN TRY
                BEGIN TRANSACTION;

                DECLARE @Usuario NVARCHAR(255) = ISNULL(
                    (SELECT UserName FROM engUser WHERE UserID = ?),
                    CONVERT(NVARCHAR(20), ?)
                );

                UPDATE orgBusinessEntity
                SET
                    Custom3 = ?,
                    ResRegimenFiscal = CASE
                        WHEN NULLIF(
                            LTRIM(RTRIM(ResRegimenFiscal)),
                            ''
                        ) IS NULL
                        OR LTRIM(RTRIM(ResRegimenFiscal)) = ?
                        THEN ?
                        ELSE ResRegimenFiscal
                    END,
                    BusinessEntityTypeID = ?,
                    CategoryTypeID = ?,
                    CompanyTypeName = ?
                WHERE BusinessEntityID = ?;

                UPDATE orgBusinessEntityMainInfo
                SET OfficialNumber = ?
                WHERE BusinessEntityID = ?;

                UPDATE orgCustomer
                SET
                    FormaPago = ?,
                    MetodoPago = ?,
                    ReceptorUsoCFDI = ?,
                    ResFormaPago = CASE
                        WHEN ? = 1 THEN ?
                        ELSE ResFormaPago
                    END,
                    ResMetodoPago = CASE
                        WHEN ? = 1 THEN ?
                        ELSE ResMetodoPago
                    END,
                    ResReceptorUsoCFDI = CASE
                        WHEN ? = 1 THEN ?
                        ELSE ResReceptorUsoCFDI
                    END
                WHERE BusinessEntityID = ?;

                INSERT INTO zvwBitacoraCambiosClientesT (
                    IDEmpresa,
                    Fecha,
                    Cliente,
                    Incidencia,
                    ValorAnterior,
                    ValorNuevo,
                    Ruta,
                    Usuario
                )
                VALUES (?, GETDATE(), ?, ?, ?, ?, ?, @Usuario);

                INSERT INTO zvwBitacoraCambiosClientesT (
                    IDEmpresa,
                    Fecha,
                    Cliente,
                    Incidencia,
                    ValorAnterior,
                    ValorNuevo,
                    Ruta,
                    Usuario
                )
                VALUES (?, GETDATE(), ?, ?, ?, ?, ?, @Usuario);

                COMMIT TRANSACTION;
            END TRY
            BEGIN CATCH
                IF @@TRANCOUNT > 0
                    ROLLBACK TRANSACTION;
                THROW;
            END CATCH;
        """

        rfc_anterior = cliente.get('OfficialNumber') or ''
        regimen_anterior = cliente.get('CompanyTypeName') or ''
        business_entity_id = self.business_entity_id
        official_name = cliente.get('OfficialName') or ''
        zone_name = cliente.get('ZoneName') or ''

        parametros = (
            self.user_id,
            self.user_id,
            rfc_respaldo,
            self.REGIMEN_GENERICO,
            regimen_respaldo,
            business_entity_type_id,
            category_type_id,
            regimen_nuevo,
            business_entity_id,
            rfc_nuevo,
            business_entity_id,
            forma_pago,
            metodo_pago,
            uso_cfdi,
            int(respaldar_datos_pago),
            forma_pago_respaldo,
            int(respaldar_datos_pago),
            metodo_pago_respaldo,
            int(respaldar_datos_pago),
            uso_cfdi_respaldo,
            business_entity_id,
            business_entity_id,
            official_name,
            incidencia_rfc,
            rfc_anterior,
            rfc_nuevo,
            zone_name,
            business_entity_id,
            official_name,
            incidencia_regimen,
            regimen_anterior,
            regimen_nuevo,
            zone_name,
        )

        self.base_de_datos.command(sql, parametros)

    @staticmethod
    def _rfc_respaldo_valido(rfc):
        return len(rfc) in (12, 13) and rfc != ModeloIntercambioRFC.RFC_GENERICO
