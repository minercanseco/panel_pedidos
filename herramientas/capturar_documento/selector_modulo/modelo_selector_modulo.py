from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.impuestos import Impuestos

class ModeloSelectorModulo:
    USUARIO_SISTEMA_ID = 90

    def __init__(self, parametros):
        self.parametros = parametros
        self.base_de_datos = ComandosBaseDatos()
        self.user_id = self.parametros.id_usuario
        self.user_name = self.obtener_nombre_usuario()


    def obtener_nombre_usuario(self):
        return self.base_de_datos.buscar_nombre_de_usuario(self.user_id)

    def obtener_modulo_documento(self, document_id):
        return int(self.base_de_datos.fetchone(
            '''
            SELECT ModuleID
            FROM dbo.docDocument
            WHERE DocumentID = ?
              AND DeletedOn IS NULL
            ''',
            (int(document_id),),
        ) or 0)

    def obtener_estado_edicion_factura(self, document_id):
        registros = self.base_de_datos.fetchall(
            """
            SELECT TOP 1
                ISNULL(M.CFDStatusName, '') AS CFDStatusName,
                ISNULL(M.CancelledIcon, 0) AS CanceladoIcon
            FROM vwLBSDocCustomerInvoiceList1400 M
            WHERE M.DocumentID = ?
            """,
            (int(document_id),),
        )
        return registros[0] if registros else None

    def obtener_estado_division_documento(self, document_id):
        """Valida en base de datos si un ticket o factura puede dividirse."""
        registros = self.base_de_datos.fetchall(
            '''
            SELECT TOP 1
                D.DocumentID,
                D.ModuleID,
                D.BusinessEntityID,
                D.Folio,
                D.FolioPrefix,
                D.Title,
                D.Comments,
                CASE
                    WHEN D.ModuleID NOT IN (1400, 21, 1319, 50) THEN 1
                    ELSE ISNULL(D.ExportID, 0)
                END AS ExportID,
                CASE WHEN D.CancelledOn IS NULL THEN 0 ELSE 1 END
                    AS Cancelado,
                ISNULL(CFD.CFDStatusID, 0) AS CFDStatusID,
                CASE WHEN D.DeletedOn IS NULL THEN 0 ELSE 1 END AS Borrado
            FROM dbo.docDocument D
            INNER JOIN dbo.docDocumentCFD CFD
                ON CFD.DocumentID = D.DocumentID
            WHERE D.DocumentID = ?
              AND D.ModuleID IN (158, 1400)
            ''',
            (int(document_id),),
        )
        return registros[0] if registros else None

    def obtener_estados_timbrado(self, documentos):
        """Consulta el estado vigente antes de solicitar el timbrado."""
        documentos = sorted(set(
            int(document_id) for document_id in documentos if document_id
        ))
        if not documentos:
            return []

        marcas = ', '.join('?' for _ in documentos)
        return self.base_de_datos.fetchall(
            '''
            SELECT D.DocumentID,
                   D.ModuleID,
                   ISNULL(D.InvoiceID, 0) AS InvoiceID,
                   CASE WHEN D.CancelledOn IS NULL THEN 0 ELSE 1 END
                       AS Cancelado,
                   CASE WHEN D.DeletedOn IS NULL THEN 0 ELSE 1 END
                       AS Borrado,
                   ISNULL(CFD.CFDStatusID, 0) AS CFDStatusID,
                   CASE
                       WHEN D.ModuleID = 1400
                           THEN ISNULL(F.CFDStatusName, '')
                       WHEN D.ModuleID = 50
                           THEN ISNULL(G.CFDStatusName, '')
                       ELSE ''
                   END AS CFDStatusName
            FROM dbo.docDocument D
            LEFT JOIN dbo.docDocumentCFD CFD
                ON CFD.DocumentID = D.DocumentID
            LEFT JOIN dbo.vwLBSDocCustomerInvoiceList1400 F
                ON F.DocumentID = D.DocumentID
               AND D.ModuleID = 1400
            LEFT JOIN dbo.vwLBSDocCustomerInvoiceGlobalList2 G
                ON G.DocumentID = D.DocumentID
               AND D.ModuleID = 50
            WHERE D.DocumentID IN ({})
            '''.format(marcas),
            tuple(documentos),
        )

    def obtener_folios_documentos(self, documentos):
        """Relaciona DocumentID con el folio que reconoce el usuario."""
        documentos = sorted(set(
            int(document_id) for document_id in documentos if document_id
        ))
        if not documentos:
            return {}

        marcas = ', '.join('?' for _ in documentos)
        registros = self.base_de_datos.fetchall(
            '''
            SELECT D.DocumentID,
                   LTRIM(RTRIM(
                       ISNULL(D.FolioPrefix, '') + ISNULL(D.Folio, '')
                   )) AS Folio
            FROM dbo.docDocument D
            WHERE D.DocumentID IN ({})
            '''.format(marcas),
            tuple(documentos),
        )
        return {
            int(fila['DocumentID']): (
                str(fila.get('Folio') or fila['DocumentID']).strip()
            )
            for fila in registros
        }

    def solicitar_timbrado(self, documentos, usuario_id):
        """Cambia a estado pendiente sólo si todo el grupo sigue siendo válido."""
        usuario_id = int(usuario_id or 0)
        if usuario_id <= 0:
            raise ValueError('El usuario que solicita el timbrado no es válido.')

        documentos = sorted(set(
            int(document_id) for document_id in documentos if document_id
        ))
        if not documentos:
            raise ValueError('Debe seleccionar por lo menos un documento.')

        marcas = ', '.join('?' for _ in documentos)
        sql = '''
        SET NOCOUNT ON;
        SET XACT_ABORT ON;
        BEGIN TRANSACTION;

        UPDATE D WITH (UPDLOCK, HOLDLOCK)
           SET InvoiceID = 1,
                SentInvoiceUserID = ?
        FROM dbo.docDocument D
        WHERE D.DocumentID IN ({marcas})
          AND D.ModuleID IN (1400, 50)
          AND ISNULL(D.InvoiceID, 0) = 0
          AND D.CancelledOn IS NULL
          AND D.DeletedOn IS NULL
          AND NOT EXISTS (
              SELECT 1
              FROM dbo.docDocumentCFD CFD
              WHERE CFD.DocumentID = D.DocumentID
                AND ISNULL(CFD.CFDStatusID, 0) = 3
          )
          AND (
              (D.ModuleID = 1400 AND EXISTS (
                  SELECT 1
                  FROM dbo.vwLBSDocCustomerInvoiceList1400 F
                  WHERE F.DocumentID = D.DocumentID
                    AND ISNULL(F.CFDStatusName, '') IN ('No enviado', 'Error')
              ))
              OR
              (D.ModuleID = 50 AND EXISTS (
                  SELECT 1
                  FROM dbo.vwLBSDocCustomerInvoiceGlobalList2 G
                  WHERE G.DocumentID = D.DocumentID
                    AND ISNULL(G.CFDStatusName, '') IN ('No enviado', 'Error')
              ))
          );

        DECLARE @Afectados int = @@ROWCOUNT;
        IF @Afectados <> ?
        BEGIN
            ROLLBACK TRANSACTION;
            SELECT CAST(-1 AS int);
            RETURN;
        END;

        COMMIT TRANSACTION;
        SELECT @Afectados;
        '''.format(marcas=marcas)

        parametros = (
            (usuario_id,)
            + tuple(documentos)
            + (len(documentos),)
        )
        afectados = int(self.base_de_datos.fetchone(sql, parametros) or 0)
        if afectados != len(documentos):
            raise ValueError(
                'El estado de uno o más documentos cambió durante la '
                'operación. No se envió ninguno; actualice e intente de nuevo.'
            )
        return afectados

    def obtener_cliente_documento(self, document_id):
        return int(self.base_de_datos.fetchone(
            '''
            SELECT CASE
                       WHEN D.BusinessEntityID IN (6208, 9277) THEN 0
                       WHEN D.BusinessEntityID = 8179 THEN X.CustomerID
                       ELSE ISNULL(BusinessEntityID, 0)
                   END
            FROM dbo.docDocument D LEFT JOIN
                docDocumentExt X ON D.DocumentID = X.IDExtra
            WHERE D.DocumentID = ?
              AND D.ModuleID = 1400
            ''',
            (int(document_id),),
        ) or 0)

    def obtener_tickets_pendientes_globalizar(self):
        """Devuelve todos los tickets vigentes del día que aún no se globalizan."""
        registros = self.base_de_datos.fetchall(
            '''
            SELECT D.DocumentID
            FROM dbo.docDocument D
            WHERE D.ModuleID = 158
              AND D.CreatedBy = ?
              AND CAST(D.CreatedOn AS date) = CAST(GETDATE() AS date)
              AND D.CancelledOn IS NULL
              AND D.DeletedOn IS NULL
              AND ISNULL(D.Globalized, 0) = 0
              AND ISNULL(D.DestinationDocumentID, 0) = 0
            ORDER BY D.DocumentID
            ''',
            (self.user_id,),
        )
        return [int(fila['DocumentID']) for fila in registros]

    def obtener_tickets_no_saldados(self, documentos):
        """Devuelve los folios cuyo saldo o estado de pago no está cerrado."""
        documentos = sorted(set(
            int(valor) for valor in (documentos or []) if valor
        ))
        if not documentos:
            return []

        marcas = ', '.join(str(document_id) for document_id in documentos)
        registros = self.base_de_datos.fetchall(
            '''
            SELECT D.DocumentID,
                   ISNULL(D.FolioPrefix, '') + ISNULL(D.Folio, '') AS Folio,
                   ISNULL(D.TotalPaid, 0) AS TotalPaid,
                   ISNULL(D.Balance, ISNULL(D.Total, 0)) AS Balance,
                   ISNULL(D.StatusPaidID, 3) AS StatusPaidID
            FROM dbo.docDocument D
            WHERE D.DocumentID IN ({})
              AND D.ModuleID = 158
              AND (
                    CAST(ROUND(ISNULL(D.Balance, ISNULL(D.Total, 0)), 2)
                         AS decimal(18, 2)) <> 0
                    OR ISNULL(D.StatusPaidID, 3) <> 1
              )
            ORDER BY D.DocumentID
            '''.format(marcas),
        )
        return registros

    @staticmethod
    def _mensaje_tickets_no_saldados(registros):
        folios = [
            str(fila.get('Folio') or fila.get('DocumentID'))
            for fila in registros
        ]
        return (
            'No es posible globalizar porque los siguientes tickets no '
            'están saldados: {}.'.format(', '.join(folios))
        )

    def globalizar_tickets(self, documentos):
        """Consolida tickets del módulo 158 en una factura global módulo 50."""
        documentos = sorted(set(int(valor) for valor in documentos if valor))
        if not documentos:
            raise ValueError('Debe seleccionar por lo menos un ticket.')

        no_saldados = self.obtener_tickets_no_saldados(documentos)
        if no_saldados:
            raise ValueError(self._mensaje_tickets_no_saldados(no_saldados))

        # Los valores ya fueron normalizados a int. Incluirlos directamente
        # evita que ODBC falle con 07002 cuando se globalizan cientos de
        # tickets en una sola ejecución.
        marcas = ', '.join(str(document_id) for document_id in documentos)
        registros = self.base_de_datos.fetchall(
            '''
            SELECT D.DocumentID,
                   ISNULL(D.FolioPrefix, '') + ISNULL(D.Folio, '') AS Folio,
                   CAST(D.CreatedOn AS date) AS Fecha,
                   ISNULL(D.SubTotal, 0) AS SubTotal,
                   ISNULL(D.TotalTax, 0) AS TotalTax,
                   ISNULL(D.Total, 0) AS Total,
                   ISNULL(D.Globalized, 0) AS Globalized,
                   ISNULL(D.DestinationDocumentID, 0) AS DestinationDocumentID,
                   CASE WHEN D.CancelledOn IS NULL THEN 0 ELSE 1 END AS Cancelado,
                   CASE WHEN D.DeletedOn IS NULL THEN 0 ELSE 1 END AS Eliminado,
                   CASE WHEN EXISTS (
                       SELECT 1 FROM dbo.docDocumentTaxDetail TD
                       WHERE TD.DocumentID = D.DocumentID
                   ) AND EXISTS (
                       SELECT 1 FROM dbo.docDocumentTaxSum TS
                       WHERE TS.DocumentID = D.DocumentID
                   ) AND EXISTS (
                       SELECT 1 FROM dbo.docDocumentTax T
                       WHERE T.DocumentID = D.DocumentID
                   ) THEN 1 ELSE 0 END AS ImpuestosAfectados
                   ,CASE WHEN EXISTS (
                       SELECT 1 FROM dbo.docDocumentItem I
                       WHERE I.DocumentID = D.DocumentID
                         AND I.DeletedOn IS NULL
                         AND ISNULL(I.Total, 0) > 0
                   ) THEN 1 ELSE 0 END AS TienePartidas
            FROM dbo.docDocument D
            WHERE D.ModuleID = 158
              AND D.DocumentID IN ({})
            '''.format(marcas),
        )

        encontrados = dict((int(fila['DocumentID']), fila) for fila in registros)
        errores = []
        fechas = set()
        for document_id in documentos:
            fila = encontrados.get(document_id)
            if not fila:
                errores.append('{}: no pertenece al módulo 158'.format(document_id))
                continue
            folio = fila['Folio'] or str(document_id)
            if fila['Cancelado'] or fila['Eliminado']:
                errores.append('{}: está cancelado o eliminado'.format(folio))
            if fila['Globalized'] or fila['DestinationDocumentID']:
                errores.append('{}: ya fue globalizado'.format(folio))
            if fila['SubTotal'] <= 0 or fila['Total'] <= 0:
                errores.append('{}: subtotal o total en cero'.format(folio))
            if not fila['ImpuestosAfectados']:
                errores.append('{}: impuestos sin afectar'.format(folio))
            if not fila['TienePartidas']:
                errores.append('{}: no contiene partidas válidas'.format(folio))
            fechas.add(fila['Fecha'])

        if len(fechas) > 1:
            errores.append('Los tickets seleccionados pertenecen a fechas distintas.')
        if errores:
            raise ValueError('\n'.join(errores))

        factura_id = self.base_de_datos.crear_documento(
            1, 'FNV', 8179, 50, self.user_id, 2, 0,
        )
        if not factura_id:
            raise RuntimeError('No fue posible crear la cabecera de la factura global.')

        factura_ieps_cuota_id = 0
        self._factura_ieps_cuota_en_proceso = 0
        try:
            # Se utiliza una tabla temporal para mantener una sola transacción
            # sin construir SQL con los identificadores seleccionados.
            sql = [
                'SET NOCOUNT ON; SET XACT_ABORT ON;',
                'BEGIN TRY BEGIN TRANSACTION;',
                'CREATE TABLE #Documentos (DocumentID int NOT NULL PRIMARY KEY);',
            ]
            # SQL Server admite como máximo 1000 filas por constructor
            # VALUES; se divide para conservar el comportamiento aun en días
            # con un volumen superior.
            for inicio in range(0, len(documentos), 1000):
                bloque = documentos[inicio:inicio + 1000]
                valores = ', '.join(
                    '({})'.format(document_id) for document_id in bloque
                )
                sql.append(
                    'INSERT INTO #Documentos (DocumentID) VALUES {};'.format(
                        valores
                    )
                )
            parametros = []

            sql.extend((
                '''
                IF EXISTS (
                    SELECT 1
                    FROM #Documentos S
                    LEFT JOIN dbo.docDocument D WITH (UPDLOCK, HOLDLOCK)
                      ON D.DocumentID = S.DocumentID
                    WHERE D.DocumentID IS NULL
                       OR D.ModuleID <> 158
                       OR D.CancelledOn IS NOT NULL
                       OR D.DeletedOn IS NOT NULL
                       OR CAST(ROUND(
                              ISNULL(D.Balance, ISNULL(D.Total, 0)), 2
                          ) AS decimal(18, 2)) <> 0
                       OR ISNULL(D.StatusPaidID, 3) <> 1
                       OR ISNULL(D.Globalized, 0) <> 0
                       OR ISNULL(D.DestinationDocumentID, 0) <> 0
                )
                BEGIN
                    ;THROW 50001,
                        N'Uno o más tickets dejaron de estar saldados, vigentes o disponibles.',
                        1;
                END;
                ''',
                '''
                ;WITH Partidas AS (
                    SELECT D.DocumentID AS SourceDocumentID,
                           ISNULL(D.FolioPrefix, '') + ISNULL(D.Folio, '') AS Folio,
                           ISNULL(Primera.TaxTypeID, 10) AS TaxTypeID,
                           ISNULL(Primera.TaxPerc, 0) AS TaxPerc,
                           CAST(ISNULL(D.SubTotal, 0) AS decimal(28, 8)) AS Importe
                    FROM #Documentos S
                    INNER JOIN dbo.docDocument D ON D.DocumentID = S.DocumentID
                    OUTER APPLY (
                        SELECT TOP 1 I.TaxTypeID, I.TaxPerc
                        FROM dbo.docDocumentItem I
                        WHERE I.DocumentID = D.DocumentID
                          AND I.DeletedOn IS NULL
                        ORDER BY ISNULL(CAST(I.LineNumber AS int), 2147483647),
                                 I.DocumentItemID
                    ) Primera
                ), Numeradas AS (
                    SELECT *, ROW_NUMBER() OVER (
                        ORDER BY SourceDocumentID
                    ) AS LineNumber
                    FROM Partidas
                )
                INSERT INTO dbo.docDocumentItem (
                    DocumentID, Quantity, ProductID, Description,
                    DiscountPerc, TaxTypeID, TaxPerc, RetentionPerc,
                    UnitPrice, Total, MustBeDelivered, CostPrice,
                    LineNumber, ApplyGlobalDiscount, ProductKey,
                    SourceDocumentID, ObjetoImpuesto, TipoCaptura,
                    DatastoreID
                )
                SELECT ?, 1, NULL, N'Venta',
                       0, TaxTypeID, TaxPerc, 0,
                       Importe, Importe, 0, 0,
                       LineNumber, 0, Folio,
                       SourceDocumentID, N'02', 0, 0
                FROM Numeradas;
                ''',
                '''
                UPDATE D
                SET D.Globalized = 1,
                    D.DestinationDocumentID = ?
                FROM dbo.docDocument D
                INNER JOIN #Documentos S ON S.DocumentID = D.DocumentID;
                ''',
                'COMMIT TRANSACTION;',
                'END TRY BEGIN CATCH',
                'IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;',
                'THROW; END CATCH;',
            ))
            parametros.extend((factura_id, factura_id))
            self.base_de_datos.command('\n'.join(sql), tuple(parametros))

            factura_ieps_cuota_id = self._separar_tickets_ieps_cuota(
                factura_id,
                documentos,
                next(iter(fechas)),
            )

            conceptos_normales = self.base_de_datos.fetchone(
                '''
                SELECT COUNT(*)
                FROM dbo.docDocumentItem
                WHERE DocumentID = ? AND DeletedOn IS NULL
                ''',
                (factura_id,),
            )
            if int(conceptos_normales or 0) == 0:
                self.base_de_datos.command(
                    '''
                    UPDATE dbo.docDocument
                    SET CancelledOn = GETDATE(), CancelledBy = ?,
                        Comments = N'Global vacía: todos los tickets fueron '
                                   N'separados por IEPS cuota'
                    WHERE DocumentID = ? AND CancelledOn IS NULL;
                    ''',
                    (self.USUARIO_SISTEMA_ID, factura_id),
                )
                return [factura_ieps_cuota_id]

            Impuestos.afectar_impuestos_documento(
                self.base_de_datos,
                factura_id,
            )
            self._afectar_impuestos_conceptos_globales(factura_id)

            conceptos_sin_impuestos = self.base_de_datos.fetchall(
                '''
                SELECT I.DocumentItemID, I.ProductKey, I.TaxTypeID,
                       I.ObjetoImpuesto
                FROM dbo.docDocumentItem I
                WHERE I.DocumentID = ?
                  AND I.DeletedOn IS NULL
                  AND I.ObjetoImpuesto = N'02'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM dbo.docDocumentTaxDetail TD
                      WHERE TD.DocumentID = I.DocumentID
                        AND TD.DocumentItemID = I.DocumentItemID
                  )
                  OR I.DocumentID = ?
                  AND I.DeletedOn IS NULL
                  AND I.ObjetoImpuesto = N'02'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM dbo.docDocumentItemTax IT
                      WHERE IT.DocumentID = I.DocumentID
                        AND IT.DocumentItemID = I.DocumentItemID
                  )
                ''',
                (factura_id, factura_id),
            )
            if conceptos_sin_impuestos:
                detalle = ', '.join(
                    '{} (TaxTypeID {})'.format(
                        fila.get('ProductKey') or fila['DocumentItemID'],
                        fila.get('TaxTypeID'),
                    )
                    for fila in conceptos_sin_impuestos
                )
                raise RuntimeError(
                    'Hay conceptos ObjetoImpuesto 02 sin detalle fiscal: {}'.format(
                        detalle
                    )
                )

            self.base_de_datos.command(
                '''
                ;WITH Totales AS (
                    SELECT ROUND(SUM(CAST(ISNULL(O.SubTotal, 0)
                                              AS decimal(28, 8))), 2) AS SubTotal,
                           ROUND(SUM(CAST(ISNULL(O.TotalTax, 0)
                                              AS decimal(28, 8))), 2) AS TotalTax,
                           ROUND(SUM(CAST(ISNULL(O.TotalRetention, 0)
                                              AS decimal(28, 8))), 2)
                               AS TotalRetention,
                           ROUND(SUM(CAST(ISNULL(O.Total, 0)
                                              AS decimal(28, 8))), 2) AS Total
                    FROM dbo.docDocument O
                    WHERE O.DestinationDocumentID = ?
                      AND O.Globalized = 1
                      AND O.CancelledOn IS NULL
                      AND O.DeletedOn IS NULL
                )
                UPDATE D
                SET D.SubTotal = T.SubTotal,
                    D.SubTotalWithDiscount = T.SubTotal,
                    D.TotalTax = T.TotalTax,
                    D.TotalRetention = T.TotalRetention,
                    D.TotalDiscount = 0,
                    D.Total = T.Total,
                    D.TotalPaid = 0,
                    D.Balance = T.Total,
                    D.StatusPaidID = 3
                FROM dbo.docDocument D
                CROSS JOIN Totales T
                WHERE D.DocumentID = ?;
                ''',
                (factura_id, factura_id),
            )
            fecha_global = next(iter(fechas))
            self.base_de_datos.command(
                '''
                UPDATE dbo.docDocument
                SET PeriodicityGlobalInfoID = N'01',
                    MonthGlobalInfoID = (
                        SELECT TOP 1 Clave
                        FROM dbo.vwcboAnexo20v40_Meses
                        WHERE ID = MONTH(?)
                    ),
                    YearGlobalInfo = YEAR(?)
                WHERE DocumentID = ?;

                UPDATE dbo.docDocumentCFD
                SET CFDStatusID = 0,
                    ReceptorUsoCFDI = N'S01',
                    MetodoPago = N'PUE',
                    FormaPago = N'01'
                WHERE DocumentID = ?;
                ''',
                (fecha_global, fecha_global, factura_id, factura_id),
            )
            validacion = self.base_de_datos.fetchall(
                '''
                ;WITH TotalesOrigen AS (
                    SELECT COUNT(*) AS Documentos,
                           CAST(ROUND(SUM(CAST(ISNULL(O.SubTotal, 0)
                                                   AS decimal(28, 8))), 2)
                                AS decimal(18, 2)) AS SubTotal,
                           CAST(ROUND(SUM(CAST(ISNULL(O.TotalTax, 0)
                                                   AS decimal(28, 8))), 2)
                                AS decimal(18, 2)) AS TotalTax,
                           CAST(ROUND(SUM(CAST(ISNULL(O.TotalRetention, 0)
                                                   AS decimal(28, 8))), 2)
                                AS decimal(18, 2)) AS TotalRetention,
                           CAST(ROUND(SUM(CAST(ISNULL(O.Total, 0)
                                                   AS decimal(28, 8))), 2)
                                AS decimal(18, 2)) AS Total
                    FROM dbo.docDocument O
                    WHERE O.DestinationDocumentID = ?
                      AND O.Globalized = 1
                      AND O.CancelledOn IS NULL
                      AND O.DeletedOn IS NULL
                ), ConceptosGlobal AS (
                    SELECT COUNT(*) AS Conceptos
                    FROM dbo.docDocumentItem I
                    WHERE I.DocumentID = ?
                      AND I.DeletedOn IS NULL
                )
                SELECT D.DocumentID,
                       CAST(ISNULL(D.SubTotal, 0) AS decimal(18, 2)) AS SubTotal,
                       CAST(ISNULL(D.TotalTax, 0) AS decimal(18, 2)) AS TotalTax,
                       CAST(ISNULL(D.TotalRetention, 0) AS decimal(18, 2))
                           AS TotalRetention,
                       CAST(ISNULL(D.Total, 0) AS decimal(18, 2)) AS Total,
                       CAST(ISNULL(D.Balance, 0) AS decimal(18, 2)) AS Balance
                FROM dbo.docDocument D
                CROSS JOIN TotalesOrigen O
                CROSS JOIN ConceptosGlobal G
                WHERE D.DocumentID = ?
                  AND EXISTS (
                      SELECT 1 FROM dbo.docDocumentTaxDetail TD
                      WHERE TD.DocumentID = D.DocumentID
                  )
                  AND EXISTS (
                      SELECT 1 FROM dbo.docDocumentTaxSum TS
                      WHERE TS.DocumentID = D.DocumentID
                  )
                  AND EXISTS (
                      SELECT 1 FROM dbo.docDocumentTax T
                      WHERE T.DocumentID = D.DocumentID
                  )
                  AND EXISTS (
                      SELECT 1 FROM dbo.docDocumentItemTax IT
                      WHERE IT.DocumentID = D.DocumentID
                  )
                  AND NOT EXISTS (
                      SELECT 1
                      FROM dbo.docDocumentItem I
                      WHERE I.DocumentID = D.DocumentID
                        AND I.DeletedOn IS NULL
                        AND I.ObjetoImpuesto = N'02'
                        AND NOT EXISTS (
                            SELECT 1
                            FROM dbo.docDocumentTaxDetail TD
                            WHERE TD.DocumentID = I.DocumentID
                              AND TD.DocumentItemID = I.DocumentItemID
                        )
                  )
                  AND NOT EXISTS (
                      SELECT 1
                      FROM dbo.docDocumentItem I
                      WHERE I.DocumentID = D.DocumentID
                        AND I.DeletedOn IS NULL
                        AND I.ObjetoImpuesto = N'02'
                        AND NOT EXISTS (
                            SELECT 1
                            FROM dbo.docDocumentItemTax IT
                            WHERE IT.DocumentID = I.DocumentID
                              AND IT.DocumentItemID = I.DocumentItemID
                        )
                  )
                  AND O.Documentos > 0
                  AND G.Conceptos = O.Documentos
                  AND CAST(ISNULL(D.SubTotal, 0) AS decimal(18, 2)) = O.SubTotal
                  AND CAST(ISNULL(D.TotalTax, 0) AS decimal(18, 2)) = O.TotalTax
                  AND CAST(ISNULL(D.TotalRetention, 0) AS decimal(18, 2)) =
                      O.TotalRetention
                  AND CAST(ISNULL(D.Total, 0) AS decimal(18, 2)) = O.Total
                  AND CAST(ISNULL(D.Balance, 0) AS decimal(18, 2)) =
                      O.Total
                ''',
                (factura_id, factura_id, factura_id),
            )
            if not validacion:
                raise RuntimeError(
                    'La factura se creó, pero no coinciden sus conceptos, '
                    'impuestos o totales con los tickets de origen.'
                )
            facturas = [factura_id]
            if factura_ieps_cuota_id:
                facturas.append(factura_ieps_cuota_id)
            return facturas
        except Exception:
            factura_ieps_cuota_id = int(
                factura_ieps_cuota_id
                or getattr(self, '_factura_ieps_cuota_en_proceso', 0)
                or 0
            )
            # Compensación: la cabecera se crea mediante un procedimiento que
            # usa su propia conexión, por eso no forma parte del batch anterior.
            self.base_de_datos.command(
                '''
                UPDATE dbo.docDocument
                SET Globalized = 0, DestinationDocumentID = 0
                WHERE DocumentID IN ({});
                UPDATE dbo.docDocument
                SET CancelledOn = GETDATE(), CancelledBy = ?,
                    Comments = N'Error al construir factura global'
                WHERE DocumentID = ? AND CancelledOn IS NULL;
                UPDATE dbo.docDocument
                SET CancelledOn = GETDATE(), CancelledBy = ?,
                    Comments = N'Error al construir factura global IEPS cuota'
                WHERE DocumentID = ? AND CancelledOn IS NULL;
                '''.format(marcas),
                (
                    self.USUARIO_SISTEMA_ID,
                    factura_id,
                    self.USUARIO_SISTEMA_ID,
                    int(factura_ieps_cuota_id or 0),
                ),
            )
            raise

    def _afectar_impuestos_conceptos_globales(self, factura_id):
        """Consolida por ticket el desglose fiscal que consume el CFDI global.

        Cada partida de la factura global representa un ticket completo y no
        un producto. Por ello puede contener simultaneamente bases de IVA 0,
        IVA 16 e IEPS. La afectacion generica basada en TaxTypeID solamente
        puede representar uno de esos impuestos; esta consolidacion conserva
        todas las bases de las partidas originales del ticket.
        """
        self.base_de_datos.command(
            '''
            SET NOCOUNT ON;
            SET XACT_ABORT ON;
            BEGIN TRY
                BEGIN TRANSACTION;

                DELETE FROM dbo.docDocumentItemTax
                WHERE DocumentID = ?;

                INSERT INTO dbo.docDocumentItemTax (
                    DocumentID, DocumentItemID, TaxItemName, TaxTypeID,
                    TaxName, IVASobreIEPS, TaxPerc, TaxAmount, BaseAmount,
                    TotalIVA, TotalIEPS
                )
                SELECT ?, G.DocumentItemID,
                       O.TaxItemName,
                       CASE
                           WHEN UPPER(ISNULL(O.TaxItemName, N'')) = N'IEPS'
                               THEN 4
                           WHEN UPPER(ISNULL(O.TaxItemName, N'')) = N'IVA'
                                AND ISNULL(O.TaxPerc, 0) <> 0
                               THEN 3
                           WHEN UPPER(ISNULL(O.TaxItemName, N'')) = N'IVA'
                               THEN 2
                           ELSE O.TaxTypeID
                       END AS TaxTypeID,
                       O.TaxName,
                       O.IVASobreIEPS,
                       O.TaxPerc,
                       0 AS TaxAmount,
                       SUM(CAST(ISNULL(O.BaseAmount, 0)
                                AS decimal(28, 8))) AS BaseAmount,
                       SUM(CAST(ISNULL(O.TotalIVA, 0)
                                AS decimal(28, 8))) AS TotalIVA,
                       SUM(CAST(ISNULL(O.TotalIEPS, 0)
                                AS decimal(28, 8))) AS TotalIEPS
                FROM dbo.docDocumentItem G
                INNER JOIN dbo.docDocumentItem S
                    ON S.DocumentID = G.SourceDocumentID
                   AND S.DeletedOn IS NULL
                INNER JOIN dbo.docDocumentItemTax O
                    ON O.DocumentID = S.DocumentID
                   AND O.DocumentItemID = S.DocumentItemID
                WHERE G.DocumentID = ?
                  AND G.DeletedOn IS NULL
                GROUP BY G.DocumentItemID, O.TaxItemName,
                         CASE
                             WHEN UPPER(ISNULL(O.TaxItemName, N'')) = N'IEPS'
                                 THEN 4
                             WHEN UPPER(ISNULL(O.TaxItemName, N'')) = N'IVA'
                                  AND ISNULL(O.TaxPerc, 0) <> 0
                                 THEN 3
                             WHEN UPPER(ISNULL(O.TaxItemName, N'')) = N'IVA'
                                 THEN 2
                             ELSE O.TaxTypeID
                         END,
                         O.TaxName, O.IVASobreIEPS, O.TaxPerc;

                IF EXISTS (
                    SELECT 1
                    FROM dbo.docDocumentItem G
                    WHERE G.DocumentID = ?
                      AND G.DeletedOn IS NULL
                      AND G.ObjetoImpuesto = N'02'
                      AND NOT EXISTS (
                          SELECT 1
                          FROM dbo.docDocumentItemTax IT
                          WHERE IT.DocumentID = G.DocumentID
                            AND IT.DocumentItemID = G.DocumentItemID
                      )
                )
                BEGIN
                    THROW 50002,
                        N'Un ticket no contiene impuestos de origen para consolidar.',
                        1;
                END;

                COMMIT TRANSACTION;
            END TRY
            BEGIN CATCH
                IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
                THROW;
            END CATCH;
            ''',
            (factura_id, factura_id, factura_id, factura_id),
        )

    def _separar_tickets_ieps_cuota(
            self, factura_global_id, documentos, fecha_global,
    ):
        """Crea la global especial que Comercial requiere para IEPS cuota."""
        marcas = ', '.join(str(int(valor)) for valor in documentos)
        tickets = self.base_de_datos.fetchall(
            '''
            SELECT DISTINCT D.DocumentID
            FROM dbo.docDocument D
            INNER JOIN dbo.docDocumentItem I ON I.DocumentID = D.DocumentID
            WHERE D.DocumentID IN ({})
              AND D.ModuleID = 158
              AND D.CancelledOn IS NULL
              AND D.DeletedOn IS NULL
              AND I.DeletedOn IS NULL
              AND I.TaxTypeID IN (18, 19, 20)
            ORDER BY D.DocumentID
            '''.format(marcas),
        )
        ticket_ids = [int(fila['DocumentID']) for fila in tickets]
        if not ticket_ids:
            return 0

        factura_id = self.base_de_datos.crear_documento(
            1, 'FNV', 8179, 1319, self.user_id, 2, 0,
        )
        if not factura_id:
            raise RuntimeError(
                'No fue posible crear la factura especial para IEPS cuota.'
            )
        self._factura_ieps_cuota_en_proceso = int(factura_id)

        marcas_cuota = ', '.join(str(valor) for valor in ticket_ids)
        partidas = self.base_de_datos.fetchall(
            '''
            SELECT I.DocumentItemID
            FROM dbo.docDocumentItem I
            WHERE I.DocumentID IN ({})
              AND I.DeletedOn IS NULL
            ORDER BY I.DocumentID,
                     ISNULL(CAST(I.LineNumber AS int), 2147483647),
                     I.DocumentItemID
            '''.format(marcas_cuota),
        )
        if not partidas:
            raise RuntimeError(
                'Los tickets con IEPS cuota no contienen partidas vigentes.'
            )

        for partida in partidas:
            self.base_de_datos.copiar_partida(
                factura_id,
                int(partida['DocumentItemID']),
                1319,
            )

        # Se mueve el ticket completo, no solamente la partida con cuota.
        self.base_de_datos.command(
            '''
            UPDATE dbo.docDocument
            SET DestinationDocumentID = ?
            WHERE DocumentID IN ({});

            UPDATE dbo.docDocumentItem
            SET DeletedOn = GETDATE(), DeletedBy = ?
            WHERE DocumentID = ?
              AND SourceDocumentID IN ({});

            UPDATE dbo.docDocumentItem
            SET ObjetoImpuesto = N'02'
            WHERE DocumentID = ? AND DeletedOn IS NULL;
            '''.format(marcas_cuota, marcas_cuota),
            (factura_id, self.user_id, factura_global_id, factura_id),
        )

        Impuestos.afectar_impuestos_documento(
            self.base_de_datos,
            factura_id,
        )

        self.base_de_datos.command(
            '''
            ;WITH Totales AS (
                SELECT ROUND(SUM(CAST(ISNULL(O.SubTotal, 0)
                                          AS decimal(28, 8))), 2) AS SubTotal,
                       ROUND(SUM(CAST(ISNULL(O.TotalTax, 0)
                                          AS decimal(28, 8))), 2) AS TotalTax,
                       ROUND(SUM(CAST(ISNULL(O.TotalRetention, 0)
                                          AS decimal(28, 8))), 2)
                           AS TotalRetention,
                       ROUND(SUM(CAST(ISNULL(O.Total, 0)
                                          AS decimal(28, 8))), 2) AS Total
                FROM dbo.docDocument O
                WHERE O.DestinationDocumentID = ?
                  AND O.Globalized = 1
                  AND O.CancelledOn IS NULL
                  AND O.DeletedOn IS NULL
            )
            UPDATE D
            SET D.SubTotal = T.SubTotal,
                D.SubTotalWithDiscount = T.SubTotal,
                D.TotalTax = T.TotalTax,
                D.TotalRetention = T.TotalRetention,
                D.TotalDiscount = 0,
                D.Total = T.Total,
                D.TotalPaid = 0,
                D.Balance = T.Total,
                D.StatusPaidID = 3,
                D.PeriodicityGlobalInfoID = N'01',
                D.MonthGlobalInfoID = (
                    SELECT TOP 1 Clave
                    FROM dbo.vwcboAnexo20v40_Meses
                    WHERE ID = MONTH(?)
                ),
                D.YearGlobalInfo = 2000
            FROM dbo.docDocument D
            CROSS JOIN Totales T
            WHERE D.DocumentID = ?;

            UPDATE dbo.docDocumentCFD
            SET CFDStatusID = 0,
                ReceptorUsoCFDI = N'S01',
                MetodoPago = N'PUE',
                FormaPago = N'01'
            WHERE DocumentID = ?;
            ''',
            (factura_id, fecha_global, factura_id, factura_id),
        )

        # El ERP la crea como 1319 para aceptar productos reales y después
        # la reconoce como global al convertirla a módulo 50 y asignar FNV.
        self.base_de_datos.command(
            '''
            SET XACT_ABORT ON;
            BEGIN TRANSACTION;
            DECLARE @Folio bigint;
            SELECT @Folio = CASE
                WHEN MAX(ISNULL(TRY_CAST(D.Folio AS bigint), 0)) < F.DocNumberFrom
                    THEN F.DocNumberFrom
                ELSE MAX(ISNULL(TRY_CAST(D.Folio AS bigint), 0)) + 1
                END
            FROM dbo.engDocumentFolio F WITH (UPDLOCK, HOLDLOCK)
            LEFT JOIN dbo.docDocument D ON D.ModuleID = F.ModuleID
            WHERE F.ModuleID = 50
            GROUP BY F.DocNumberFrom;

            UPDATE dbo.docDocument
            SET ModuleID = 50, FolioPrefix = N'FNV', Folio = @Folio
            WHERE DocumentID = ?;
            COMMIT TRANSACTION;
            ''',
            (factura_id,),
        )

        conceptos_incompletos = self.base_de_datos.fetchone(
            '''
            SELECT COUNT(*)
            FROM dbo.docDocumentItem I
            WHERE I.DocumentID = ?
              AND I.DeletedOn IS NULL
              AND I.ObjetoImpuesto = N'02'
              AND (NOT EXISTS (
                    SELECT 1 FROM dbo.docDocumentTaxDetail TD
                    WHERE TD.DocumentID = I.DocumentID
                      AND TD.DocumentItemID = I.DocumentItemID
                  ) OR NOT EXISTS (
                    SELECT 1 FROM dbo.docDocumentItemTax IT
                    WHERE IT.DocumentID = I.DocumentID
                      AND IT.DocumentItemID = I.DocumentItemID
                  ))
            ''',
            (factura_id,),
        )
        if int(conceptos_incompletos or 0):
            raise RuntimeError(
                'La factura especial de IEPS cuota quedó fiscalmente incompleta.'
            )
        return int(factura_id)

    def obtener_columnas(self, tabla):

        modulos = {
            'tbv_tickets': 158,
            'tbv_facturas': 1400,
            'tbv_depositos': 1664

        }

        modulo = modulos.get(tabla, 0)
        if modulo == 0:
            return None, None, None

        info_columnas = self.base_de_datos.fetchall("""
            SELECT TOP 1
                    UV.Columns, UV.ColumnsSize, MP.[Value] PrimaryKey
            FROM	engDrlGridViews GV INNER JOIN
                        engDrlGridUserViews UV ON GV.ViewID=UV.ViewID INNER JOIN
                        engUser U ON UV.UserID=U.UserID INNER JOIN
                        engModuleParameter MP ON GV.ModuleID = MP.ModuleID
            WHERE GV.ModuleID=? AND UserGroupID = 11 AND ParameterKey = 'PrimaryKey'
        """, (modulo,))

        if not info_columnas:
            return None, None, None

        # agregamos el primary key de la consulta sobre la que se realizará el procesamiento de la info
        columnas = info_columnas[0]['Columns']
        anchos_columnas = info_columnas[0]['ColumnsSize']
        primary_key = info_columnas[0]['PrimaryKey']

        columnas = f"{columnas}, [{primary_key}]"
        anchos_columnas = f"{anchos_columnas}, 0"

        return columnas, anchos_columnas, primary_key

    def obtener_cortes_caja(self):
        """Consulta los cortes pertenecientes al usuario del selector."""
        return self.base_de_datos.fetchall(
            '''
            SELECT *
            FROM dbo.zvwCortesDeCajaMenu2
            WHERE CreatedBy = ?
            ''',
            (self.user_id,),
        )

    def obtener_facturas_globales(self):
        """Consulta las facturas globales capturadas por el usuario actual."""
        return self.base_de_datos.fetchall(
            '''
            SELECT DocumentID, BusinessEntityName, DocFolio, DateDocument,
                   CancelledIcon, CFDStatusID, CFDStatusName,
                   CFDStatusCancelledName,
                   CFDStatusError, CFDCancelledStatusID, Usuario,
                   TimbradoPor, HoraVenta, Comentarios, CanceladoPor, CreatedBy
            FROM dbo.vwLBSDocCustomerInvoiceGlobalList2
            WHERE CreatedBy = ?
            ORDER BY DateDocument DESC, HoraVenta DESC, DocumentID DESC
            ''',
            (self.user_id,),
        )

    def obtener_registros(self, tabla, columnas_str, primary_key):
        consultas = {
            'tbv_tickets': (
                'vwLBSDocCustomerSaleList',
                '''M.CreatedBy = ?
                AND ISNULL(M.CanceladoIcon, 0) <> 1
                AND EXISTS (
                    SELECT 1
                    FROM dbo.docDocument D
                    WHERE D.DocumentID = M.DocumentID
                      AND D.CancelledOn IS NULL
                      AND D.DeletedOn IS NULL
                      AND ISNULL(D.Globalized, 0) = 0
                      AND ISNULL(D.DestinationDocumentID, 0) = 0
                )''',
                (self.user_id,),
            ),
            'tbv_facturas': (
                'vwLBSDocCustomerInvoiceList1400',
                'M.CreatedBy = ?',
                (self.user_id,),
            ),
            'tbv_depositos': (
                'zvwDepositosDiariosCayalMenu',
                '''(
                    M.CreatedBy = ?
                    OR EXISTS (
                        SELECT 1
                        FROM zvwDepositosDiariosCayal D
                        WHERE D.ID = M.ID
                          AND D.ReceptorUserID = ?
                    )
                )''',
                (self.user_id, self.user_id),
            ),
        }

        configuracion = consultas.get(tabla)
        if not configuracion:
            return []
        consulta, filtro_usuario, parametros = configuracion

        query = f"""
                SELECT {columnas_str}
                FROM {consulta} M
                WHERE {filtro_usuario}
                AND CAST(M.Fecha as date) = CAST(GETDATE() as date)
                ORDER BY {primary_key} DESC
            """

        return self.base_de_datos.fetchall(query, parametros)
