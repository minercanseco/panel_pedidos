from cayal.comandos_base_datos import ComandosBaseDatos


class ModeloEditarDocumento:

    BUSINESS_ENTITY_REMISION = 8179
    CAYAL_CUSTOMER_TYPE_FACTURA = 2

    def __init__(self, parametros):
        self.parametros = parametros
        self.base_de_datos = ComandosBaseDatos()

        self.document_id = parametros.id_principal
        self.business_entity_id = self.obtener_business_entity_id()
        self.user_id = getattr(parametros, 'id_usuario', None)

        self._info_cliente = None

    def obtener_business_entity_id(self):
        return self.base_de_datos.fetchone('SELECT * from [dbo].[zvwBuscarBusinessEntityID-DocumentID](?)', (self.document_id,))

    def obtener_info_cliente(self):
        if self._info_cliente is not None:
            return self._info_cliente

        if not self.business_entity_id:
            self._info_cliente = None
            return None

        consulta = self.base_de_datos.buscar_info_cliente(
            self.business_entity_id
        )

        if not consulta:
            self._info_cliente = None
            return None

        self._info_cliente = consulta[0]
        return self._info_cliente

    def cliente_tiene_datos_facturacion(self):
        info_cliente = self.obtener_info_cliente()
        print(info_cliente)
        if not info_cliente:
            return False

        return int(info_cliente.get('CayalCustomerTypeID', 0) or 0) == self.CAYAL_CUSTOMER_TYPE_FACTURA

    def convertir_en_remision(self, forma_pago):
        info_cliente = self.obtener_info_cliente()

        if not info_cliente:
            return {
                'ok': False,
                'mensaje': 'No se encontró la información del cliente.'
            }

        zone_id = info_cliente.get('ZoneID', None)

        sql = """
            IF NOT EXISTS (
                SELECT CustomerID
                FROM docDocumentExt
                WHERE IDExtra = ?
            )
            BEGIN
                INSERT INTO docDocumentExt (
                    IDExtra,
                    CustomerID
                )
                VALUES (
                    ?,
                    ?
                )
            END
            ELSE
            BEGIN
                UPDATE docDocumentExt
                SET CustomerID = ?
                WHERE IDExtra = ?
            END;

            UPDATE docDocument
            SET
                BusinessEntityID = ?,
                chkCustom1 = 1,
                Custom3 = ?
            WHERE DocumentID = ?;

            UPDATE docDocumentCFD
            SET
                MetodoPago = 'PUE',
                FormaPago = CASE
                    WHEN ? NOT IN ('01', '04', '28') THEN '01'
                    ELSE ?
                END,
                ReceptorUsoCFDI = 'S01'
            WHERE DocumentID = ?;
        """

        parametros = [
            self.document_id,
            self.document_id,
            self.business_entity_id,
            self.business_entity_id,
            self.document_id,
            self.BUSINESS_ENTITY_REMISION,
            zone_id,
            self.document_id,
            forma_pago,
            forma_pago,
            self.document_id
        ]

        self.base_de_datos.command(sql, parametros)

        return {
            'ok': True,
            'mensaje': 'Documento convertido en remisión correctamente.'
        }

    def convertir_en_factura(self):
        if not self.cliente_tiene_datos_facturacion():
            return {
                'ok': False,
                'mensaje': (
                    'El cliente no cuenta con datos de facturación guardados, '
                    'actualícelos e inténtelo de nuevo.'
                )
            }

        info_cliente = self.obtener_info_cliente()

        sql = """
            UPDATE docDocument
            SET
                BusinessEntityID = ?,
                chkCustom1 = 0,
                Custom3 = ?
            WHERE DocumentID = ?;

            UPDATE docDocumentExt
            SET CustomerID = 0
            WHERE IDExtra = ?;

            UPDATE docDocumentCFD
            SET
                MetodoPago = ?,
                FormaPago = ?,
                ReceptorUsoCFDI = ?
            WHERE DocumentID = ?;
        """

        parametros = [
            self.business_entity_id,
            info_cliente.get('ZoneID', None),
            self.document_id,
            self.document_id,
            info_cliente.get('MetodoPago', ''),
            info_cliente.get('FormaPago', ''),
            info_cliente.get('ReceptorUsoCFDI', ''),
            self.document_id
        ]

        self.base_de_datos.command(sql, parametros)

        return {
            'ok': True,
            'mensaje': 'Documento convertido en factura correctamente.'
        }

    def guardar_documento(self, comentario, metodo_pago, forma_pago, uso_cfdi):
        sql = """
            UPDATE docDocument
            SET Comments = ?
            WHERE DocumentID = ?;

            UPDATE docDocumentCFD
            SET
                MetodoPago = ?,
                FormaPago = ?,
                ReceptorUsoCFDI = ?
            WHERE DocumentID = ?;
        """

        parametros = [
            comentario,
            self.document_id,
            metodo_pago,
            forma_pago,
            uso_cfdi,
            self.document_id
        ]

        return self.base_de_datos.command(sql, parametros)

    def obtener_formas_pago(self):
        sql = """
            SELECT
                ID,
                Value,
                Clave
            FROM vwcboAnexo20v33_FormaPago
            WHERE ID IN (1, 2, 3, 4, 28, 99)
            ORDER BY Value;
        """

        return self.base_de_datos.fetchall(sql)

    def obtener_metodos_pago(self):
        sql = """
            SELECT
                ID,
                Value,
                Clave
            FROM vwcboAnexo20v33_MetodoDePago
            ORDER BY Value;
        """

        return self.base_de_datos.fetchall(sql)

    def obtener_usos_cfdi(self):
        sql = """
            SELECT
                ID,
                Value,
                Clave
            FROM vwcboAnexo20v40_UsoCFDI
            ORDER BY Value;
        """

        return self.base_de_datos.fetchall(sql)

    def obtener_documento(self):
        sql = """
            SELECT
                D.DocumentID,
                BE_DOC.BusinessEntityID AS BusinessEntityID,
                BE.OfficialName AS Cliente,
                D.FolioPrefix + CAST(D.Folio AS VARCHAR(20)) AS Folio,
                ISNULL(D.Comments, '') AS Comentario,
                ISNULL(CFD.MetodoPago, '') AS MetodoPago,
                ISNULL(CFD.FormaPago, '') AS FormaPago,
                ISNULL(CFD.ReceptorUsoCFDI, '') AS UsoCFDI,
                ISNULL(D.chkCustom1, 0) AS EsRemision,
                CFD.CFDStatusID,
                CASE WHEN D.CancelledOn IS NULL THEN 0 ELSE 1 END Cancelled
            FROM docDocument D
            CROSS APPLY [dbo].[zvwBuscarBusinessEntityID-DocumentID](D.DocumentID) BE_DOC
            INNER JOIN orgBusinessEntity BE
                ON BE.BusinessEntityID = BE_DOC.BusinessEntityID
            LEFT JOIN docDocumentCFD CFD
                ON CFD.DocumentID = D.DocumentID
            WHERE D.DocumentID = ?;
        """

        consulta = self.base_de_datos.fetchall(sql, [self.document_id])

        if not consulta:
            return None

        documento = consulta[0]

        self.business_entity_id = documento.get('BusinessEntityID')

        return documento

    def guardar_como_remision(self, comentario, forma_pago):
        resultado = self.convertir_en_remision(
            forma_pago=forma_pago
        )

        if isinstance(resultado, dict) and not resultado.get('ok', True):
            return resultado

        self.guardar_documento(
            comentario=comentario,
            metodo_pago='PUE',
            forma_pago=forma_pago,
            uso_cfdi='S01'
        )

        return {
            'ok': True,
            'mensaje': 'Documento actualizado como remisión correctamente.'
        }

    def guardar_como_factura(self, comentario, metodo_pago, forma_pago, uso_cfdi):
        if not self.cliente_tiene_datos_facturacion():
            return {
                'ok': False,
                'mensaje': (
                    'El cliente no cuenta con datos de facturación guardados. '
                    'No es posible guardar el documento como factura.'
                )
            }

        info_cliente = self.obtener_info_cliente()

        sql = """
            UPDATE docDocument
            SET
                BusinessEntityID = ?,
                chkCustom1 = 0,
                Custom3 = ?
            WHERE DocumentID = ?;

            UPDATE docDocumentExt
            SET CustomerID = 0
            WHERE IDExtra = ?;

            UPDATE docDocument
            SET Comments = ?
            WHERE DocumentID = ?;

            UPDATE docDocumentCFD
            SET
                MetodoPago = ?,
                FormaPago = ?,
                ReceptorUsoCFDI = ?
            WHERE DocumentID = ?;
        """

        parametros = [
            self.business_entity_id,
            info_cliente.get('ZoneID', None),
            self.document_id,
            self.document_id,
            comentario,
            self.document_id,
            metodo_pago,
            forma_pago,
            uso_cfdi,
            self.document_id
        ]

        self.base_de_datos.command(sql, parametros)

        return {
            'ok': True,
            'mensaje': 'Documento actualizado como factura correctamente.'
        }

