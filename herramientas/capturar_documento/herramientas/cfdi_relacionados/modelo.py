
from cayal.comandos_base_datos import ComandosBaseDatos


class ModeloRelacionarFactura:
    def __init__(self, parametros):
        self._parametros = parametros
        self.user_id = self._parametros.id_usuario
        self.module_id =self._parametros.id_modulo
        self.document_id = self._parametros.id_principal

        self.base_de_datos = ComandosBaseDatos()


    def obtener_info_documento(self,document_id):
        return self.base_de_datos.buscar_info_documento(document_id)

    def obtener_documentos_relacionables(self, document_id):
        return self.base_de_datos.fetchall("""
            DECLARE @DocumentID INT = ?
            DECLARE @BusinessEntityID INT = (SELECT BusinessEntityID FROM docDocument WHERE DocumentID = @DocumentID) 
        
            SELECT 
                D.DocumentID,
                ROW_NUMBER() OVER (ORDER BY D.DocumentID DESC) AS N,
                CAST(D.CreatedOn AS date) AS Fecha,
                CASE
                    WHEN D.chkCustom1 = 1 THEN 'Remisión'
                    ELSE 'Factura'
                END AS Tipo,
                ISNULL(D.FolioPrefix, '') + ISNULL(D.Folio, '') AS Folio,
                CFD.FormaPago AS FP,
                ISNULL(A.DepotName, '') AS Sucursal,
                CFD.CFDIFolioFiscal AS UUID
			FROM docDocument D INNER JOIN
				docDocumentExtra X ON D.DocumentID=X.DocumentID LEFT OUTER JOIN
				orgDepot A ON X.BusinessEntityDepotID=A.DepotID INNER JOIN
				docDocumentCFD CFD ON D.DocumentID=CFD.DocumentID INNER JOIN
				vwcboAnexo20v33_FormaPago FP ON CFD.FormaPago=FP.Clave
			WHERE D.BusinessEntityID=@BusinessEntityID 
			    AND D.ModuleID IN (21,1400,1319,50) 
			    AND D.chkCustom1 = 0
			    AND D.DocumentID <> @DocumentID
			    AND CFD.CFDStatusID=3
			ORDER BY D.DocumentID DESC
        """,(document_id,))

    def obtener_info_documento_folio_cfd(self, folio_fiscal):
        return self.base_de_datos.fetchall("""
            SELECT 
                D.DocumentID,
                ROW_NUMBER() OVER (ORDER BY D.DocumentID DESC) AS N,
                CAST(D.CreatedOn AS date) AS Fecha,
                CASE
                    WHEN D.chkCustom1 = 1 THEN 'Remisión'
                    ELSE 'Factura'
                END AS Tipo,
                ISNULL(D.FolioPrefix, '') + ISNULL(D.Folio, '') AS Folio,
                CFD.FormaPago AS FP,
                ISNULL(A.DepotName, '') AS Sucursal,
                CFD.CFDIFolioFiscal AS UUID
			FROM docDocument D INNER JOIN
				docDocumentExtra X ON D.DocumentID=X.DocumentID LEFT OUTER JOIN
				orgDepot A ON X.BusinessEntityDepotID=A.DepotID INNER JOIN
				docDocumentCFD CFD ON D.DocumentID=CFD.DocumentID INNER JOIN
				vwcboAnexo20v33_FormaPago FP ON CFD.FormaPago=FP.Clave
			WHERE CFD.CFDIFolioFiscal = ?
        """, (folio_fiscal,))

    def obtener_tipos_relacion_fiscal(self):
        return self.base_de_datos.fetchall("""
            SELECT ID,Value,Clave FROM vwcboAnexo20v33_TipoRelacion C WHERE ID=4 
        """)

    def guardar_relacion(
            self,
            cfd_folios_fiscales,
            documentos,
            clave_relacion
    ):
        query = """
            UPDATE docDocumentCFD
            SET
                CFDTipoRelacion = ?,
                CFDUUIDRelacionados = ?
            WHERE DocumentID = ?;

            INSERT INTO docDocumentCFDIRelacionados (
                DocumentID,
                SourceDocumentID,
                UserID,
                CFDTipoRelacion
            )
            VALUES (?, ?, ?, ?);
        """

        for documento_id in documentos:
            parametros = (
                clave_relacion,
                cfd_folios_fiscales,
                self.document_id,
                self.document_id,
                documento_id,
                self.user_id,
                clave_relacion
            )

            self.base_de_datos.command(query, parametros)

    def obtener_documentos_relacionados(self, document_id):
        cfd_folios_fiscales = self.base_de_datos.fetchone(
            """
            SELECT CFDUUIDRelacionados
            FROM docDocumentCFD
            WHERE documentID = ?
            """,
            (document_id,)
        )
        if not cfd_folios_fiscales:
            return

        info_documentos = []
        folios_fiscales = cfd_folios_fiscales.split(',')
        if folios_fiscales:
            for folios_fiscal in folios_fiscales:
                consulta = self.obtener_info_documento_folio_cfd(folios_fiscal)
                if consulta:
                    info_documentos.append(consulta[0])

        return info_documentos

    def obtener_documentos_relacionados_cancelados(self, document_id):
        cfd_folios_fiscales = self.base_de_datos.fetchone(
            """
            SELECT CFDiCancellationReplacementFolio
            FROM docDocumentCFD
            WHERE documentID = ?
            """,
            (document_id,)
        )
        if not cfd_folios_fiscales:
            return
        info_documentos = []
        folios_fiscales = cfd_folios_fiscales.split(',')
        if folios_fiscales:
            for folios_fiscal in folios_fiscales:
                consulta = self.obtener_info_documento_folio_cfd(folios_fiscal)
                if consulta:
                    info_documentos.append(consulta[0])

        return info_documentos
