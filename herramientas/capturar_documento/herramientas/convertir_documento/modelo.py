from cayal.comandos_base_datos import ComandosBaseDatos


class ModeloConvertirDocumento:
    MODULO_FACTURAS = 1400
    MODULO_NOTAS_ENTREGADAS = 1316
    MODULO_PEDIDOS_MAYOREO = 967

    def __init__(self, parametros):
        self.parametros = parametros
        self.base_de_datos = ComandosBaseDatos()
        self.document_id = int(parametros.id_principal or 0)
        self.user_id = int(parametros.id_usuario or 0)

    def obtener_documento(self):
        registros = self.base_de_datos.fetchall(
            """
            SELECT TOP 1
                D.DocumentID,
                D.ModuleID,
                D.BusinessEntityID,
                ISNULL(CONVERT(nvarchar(50), D.Folio), '') AS Folio,
                ISNULL(E.OfficialName, '') AS Cliente,
                CONCAT(ISNULL(D.FolioPrefix, ''), ISNULL(D.Folio, ''))
                    AS DocFolio,
                ISNULL(D.Title, '') AS Title,
                ISNULL(CONVERT(nvarchar(max), D.Comments), '') AS Comments,
                ISNULL(X.BusinessEntityDepotID, 0) AS DepotID,
                ISNULL(A.DepotName, '') AS Sucursal,
                ISNULL(D.ExportID, 0) AS ExportID,
                ISNULL(D.InvoiceID, 0) AS InvoiceID,
                ISNULL(CFD.CFDStatusID, 0) AS CFDStatusID,
                CASE WHEN D.CancelledOn IS NULL THEN 0 ELSE 1 END AS Cancelado,
                CASE WHEN D.DeletedOn IS NULL THEN 0 ELSE 1 END AS Borrado
            FROM dbo.docDocument D
            INNER JOIN dbo.orgBusinessEntity E
                ON E.BusinessEntityID = D.BusinessEntityID
            LEFT JOIN dbo.docDocumentCFD CFD
                ON CFD.DocumentID = D.DocumentID
            LEFT JOIN dbo.docDocumentExtra X
                ON X.DocumentID = D.DocumentID
            LEFT JOIN dbo.orgDepot A
                ON A.DepotID = X.BusinessEntityDepotID
               AND A.DeletedOn IS NULL
            WHERE D.DocumentID = ?
            """,
            (self.document_id,),
        )
        if not registros:
            return None

        documento = registros[0]
        if int(documento.get('BusinessEntityID', 0) or 0) == 8179:
            business_entity_id_real = self.base_de_datos.fetchone(
                'SELECT * FROM '
                '[dbo].[zvwBuscarBusinessEntityID-DocumentID](?)',
                (self.document_id,),
            )
            if business_entity_id_real:
                nombre_real = self.base_de_datos.fetchone(
                    'SELECT OfficialName FROM dbo.orgBusinessEntity '
                    'WHERE BusinessEntityID = ?',
                    (business_entity_id_real,),
                )
                if nombre_real:
                    documento['Cliente'] = nombre_real
                documento['BusinessEntityIDReal'] = business_entity_id_real

        return documento

    def validar_documento(self):
        documento = self.obtener_documento()
        if not documento:
            return None, 'No se encontró el documento seleccionado.'
        if int(documento.get('ModuleID', 0) or 0) != self.MODULO_FACTURAS:
            return None, 'El documento ya no pertenece al módulo 1400.'
        if int(documento.get('Cancelado', 0) or 0) == 1:
            return None, 'La factura está cancelada.'
        if int(documento.get('Borrado', 0) or 0) == 1:
            return None, 'La factura está borrada.'
        if int(documento.get('CFDStatusID', 0) or 0) == 3:
            return None, 'La factura ya está timbrada.'
        if int(documento.get('InvoiceID', 0) or 0) in (1, 2, 4):
            return None, 'La factura está en proceso de timbrado o timbrada.'
        if int(documento.get('ExportID', 0) or 0) != 1:
            return None, (
                'La factura está en proceso de actualización; espere a que '
                'concluya antes de convertirla.'
            )
        return documento, None

    def convertir(self, tipo):
        documento, error = self.validar_documento()
        if error:
            return {'ok': False, 'mensaje': error}

        if tipo == 'Nota entregada':
            return self._convertir_nota_entregada(documento)
        if tipo == 'Pedido mayoreo':
            return self._convertir_pedido_mayoreo(documento)
        return {'ok': False, 'mensaje': 'Tipo de conversión no válido.'}

    def _comentarios_con_sucursal(self, documento):
        comentarios = str(documento.get('Comments') or '').strip()
        sucursal = str(documento.get('Sucursal') or '').strip()
        if sucursal:
            sufijo = 'Sucursal: {}'.format(sucursal)
            comentarios = '{} -{}'.format(comentarios, sufijo) if comentarios else sufijo
        return comentarios

    def _convertir_pedido_mayoreo(self, documento):
        folio_siguiente = self.base_de_datos.fetchone(
            'SELECT * FROM [dbo].[zvwBuscarFolioSiguienteCayal-ModuloID](?)',
            (self.MODULO_PEDIDOS_MAYOREO,),
        )
        if folio_siguiente is None:
            return {'ok': False, 'mensaje': 'No fue posible obtener el siguiente folio PM.'}

        comentarios = self._comentarios_con_sucursal(documento)
        titulo = str(documento.get('Title') or '')
        folio_original = str(documento.get('Folio') or '')

        self.base_de_datos.command(
            """
            IF EXISTS (
                SELECT 1
                FROM dbo.docDocument D
                WHERE D.DocumentID = ?
                  AND D.ModuleID = 1400
                  AND D.CancelledOn IS NULL
                  AND D.DeletedOn IS NULL
                  AND ISNULL(D.ExportID, 0) = 1
                  AND ISNULL(D.InvoiceID, 0) NOT IN (1, 2, 4)
                  AND NOT EXISTS (
                      SELECT 1
                      FROM dbo.docDocumentCFD CFD
                      WHERE CFD.DocumentID = D.DocumentID
                        AND ISNULL(CFD.CFDStatusID, 0) = 3
                  )
            )
            BEGIN
                IF ? = 8179
                BEGIN
                    UPDATE D
                       SET BusinessEntityID = X.CustomerID
                    FROM dbo.docDocumentExt X
                    INNER JOIN dbo.docDocument D
                        ON X.IDExtra = D.DocumentID
                    WHERE X.IDExtra = ?;

                    UPDATE dbo.docDocumentExt
                       SET CustomerID = 0
                    WHERE IDExtra = ?;
                END;

                UPDATE dbo.docDocument
                   SET PrintedOn = GETDATE(),
                       Comments = ?,
                       Title = ?,
                       ModuleID = 967,
                       DocumentTypeID = 40,
                       DateDelivery = NULL,
                       CreatedBy = ?,
                       FolioPrefix = 'PM',
                       Folio = ?,
                       SalesRepContactID = 0,
                       TotalCost = 0,
                       StatusPaidID = 0,
                       PaymentTermID = 0,
                       StatusDeliveryID = 3,
                       UserID = 0,
                       DateCost = CAST(GETDATE() AS date)
                 WHERE DocumentID = ?;

                DELETE FROM dbo.orgProductKardex WHERE DocumentID = ?;
            END;
            """,
            (
                self.document_id,
                int(documento.get('BusinessEntityID', 0) or 0),
                self.document_id,
                self.document_id,
                ' Folio Original: FM{}-{}'.format(
                    folio_original,
                    comentarios,
                ),
                '{}-FM{}'.format(titulo, folio_original),
                self.user_id,
                folio_siguiente,
                self.document_id,
                self.document_id,
            ),
        )
        if self._obtener_modulo_actual() != self.MODULO_PEDIDOS_MAYOREO:
            return {
                'ok': False,
                'mensaje': (
                    'El estado de la factura cambió antes de completar la '
                    'conversión.'
                ),
            }
        return {
            'ok': True,
            'mensaje': 'El folio convertido es PM{}'.format(folio_siguiente),
        }

    def _convertir_nota_entregada(self, documento):
        folio_siguiente = self.base_de_datos.fetchone(
            'SELECT Folio FROM dbo.zvwSiguientesFoliosCayal WHERE ModuleID = ?',
            (self.MODULO_NOTAS_ENTREGADAS,),
        )
        if folio_siguiente is None:
            return {'ok': False, 'mensaje': 'No fue posible obtener el siguiente folio NVR.'}

        comentarios = self._comentarios_con_sucursal(documento)
        folio_original = str(documento.get('DocFolio') or '')
        nuevo_comentario = 'Folio Original: {}-{}'.format(
            folio_original,
            comentarios,
        )

        self.base_de_datos.command(
            """
            UPDATE dbo.docDocument
               SET PrintedOn = GETDATE(),
                   PrintedBy = ?,
                   Comments = ?,
                   ModuleID = 1316,
                   DocumentTypeID = 2,
                   DateDelivery = GETDATE(),
                   CreatedBy = ?,
                   FolioPrefix = 'NVR',
                   Folio = ?,
                   SalesRepContactID = 0,
                   TotalCost = 0,
                   StatusPaidID = 0,
                   PaymentTermID = 0,
                   StatusDeliveryID = 3,
                   UserID = NULL,
                   DateCost = GETDATE()
             WHERE DocumentID = ?
               AND ModuleID = 1400
               AND CancelledOn IS NULL
               AND DeletedOn IS NULL
               AND ISNULL(ExportID, 0) = 1
               AND ISNULL(InvoiceID, 0) NOT IN (1, 2, 4)
               AND NOT EXISTS (
                   SELECT 1
                   FROM dbo.docDocumentCFD CFD
                   WHERE CFD.DocumentID = docDocument.DocumentID
                     AND ISNULL(CFD.CFDStatusID, 0) = 3
               );
            """,
            (
                self.user_id,
                nuevo_comentario,
                self.user_id,
                folio_siguiente,
                self.document_id,
            ),
        )
        if self._obtener_modulo_actual() != self.MODULO_NOTAS_ENTREGADAS:
            return {
                'ok': False,
                'mensaje': (
                    'El estado de la factura cambió antes de completar la '
                    'conversión.'
                ),
            }
        return {
            'ok': True,
            'mensaje': 'El folio convertido es NVR{}'.format(folio_siguiente),
        }

    def _obtener_modulo_actual(self):
        return int(self.base_de_datos.fetchone(
            'SELECT ModuleID FROM dbo.docDocument WHERE DocumentID = ?',
            (self.document_id,),
        ) or 0)
