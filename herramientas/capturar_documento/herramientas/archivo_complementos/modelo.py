

from datetime import date, datetime
from html import escape
from pathlib import Path
import tempfile
import webbrowser


class Modelo:
    def __init__(self, base_de_datos, plantilla=None):
        self._base_de_datos = base_de_datos
        self._plantilla = Path(plantilla) if plantilla else Path(__file__).with_name(
            'ValidaComplementoCayal.html')

    @staticmethod
    def normalizar_fecha(valor):
        if isinstance(valor, (date, datetime)):
            return valor.strftime('%Y-%m-%d')
        return datetime.strptime(str(valor).strip(), '%Y-%m-%d').strftime('%Y-%m-%d')

    def buscar_user_group_id(self, usuario_id):
        user_group_id = self._base_de_datos.fetchone(
            'SELECT UserGroupID FROM dbo.engUser WHERE UserID = ?',
            (usuario_id,),
        )
        if user_group_id is None:
            raise ValueError(f'No se encontró el grupo del usuario {usuario_id}.')
        return int(user_group_id)

    @staticmethod
    def _filtro_usuario(usuario_id, user_group_id, alias):
        if user_group_id == 11:
            return f' AND {alias}.CreatedBy = ?', (usuario_id,)
        return '', ()

    def buscar_complementos(self, fecha_inicial, fecha_final, usuario_id, user_group_id):
        filtro_usuario, parametros_usuario = self._filtro_usuario(
            usuario_id, user_group_id, 'FO')
        consulta = """
            SELECT
             COUNT(FO.FinancialOperationID) Num, CAST(FO.DateOperation as date) Fecha,
             U.UserName Usuario
            FROM dbo.docFinancialOperation AS FO
            LEFT JOIN dbo.orgBusinessEntity AS BE ON FO.BusinessEntityID = BE.BusinessEntityID
            LEFT JOIN dbo.vwcboCFDPaymentmethod AS PM ON PM.ID = FO.PaymentMethodID
            LEFT JOIN dbo.vwLBSCobroStatusComplementoPago AS CP
                ON CP.FinancialOperationID = FO.FinancialOperationID
            LEFT JOIN dbo.vwLBSDocumentCFDFinancialOperationStatus AS CFD
                ON CFD.FinancialOperationID = FO.FinancialOperationID
            LEFT JOIN dbo.orgFinancialEntity AS FE ON FE.FinancialEntityID = FO.FinancialEntityID
            LEFT JOIN dbo.vwLBSFinancialOperationTotalApplied AS AP
                ON AP.FinancialOperationID = FO.FinancialOperationID
            LEFT JOIN dbo.vwcboAnexo20v33_FormaPago AS FP33 ON FP33.ID = FO.PaymentMethodID
            LEFT JOIN dbo.engUser AS U ON U.UserID = FO.CreatedBy
            LEFT JOIN dbo.engUser AS UV ON UV.UserID = FO.VendorUserID
            WHERE FO.DocRecipientID IN (1, 99) AND FO.DeletedOn IS NULL
              AND CP.ComplementoStatusObligatorio IN ('Obligatorio', 'Timbrado')
              AND FO.DateOperation >= CAST(? AS DATE)
              AND FO.DateOperation < DATEADD(DAY, 1, CAST(? AS DATE))
              {filtro_usuario}
            GROUP BY CAST(FO.DateOperation AS date), U.UserName
            ORDER BY CAST(FO.DateOperation AS date), U.UserName
        """.format(filtro_usuario=filtro_usuario)
        parametros = (
            self.normalizar_fecha(fecha_inicial),
            self.normalizar_fecha(fecha_final),
        ) + parametros_usuario
        return self._base_de_datos.fetchall(consulta, parametros)

    def buscar_detalle_impresion(self, fecha_inicial, fecha_final, usuario_id, user_group_id):
        filtro_usuario, parametros_usuario = self._filtro_usuario(
            usuario_id, user_group_id, 'DF')
        consulta = """
            ;WITH OperacionesFiltradas AS (
                SELECT
                    DF.FinancialOperationID,
                    DF.BusinessEntityID,
                    DF.PaymentMethodID,
                    DF.DateAffectation,
                    DF.Amount,
                    DF.EmailSend,
                    C.ComplementoStatusObligatorio
                FROM dbo.docFinancialOperation AS DF
                LEFT JOIN dbo.vwLBSCobroStatusComplementoPago AS C
                    ON C.FinancialOperationID = DF.FinancialOperationID
                WHERE DF.DocRecipientID IN (1, 99)
                  AND DF.DeletedOn IS NULL
                  AND C.ComplementoStatusObligatorio IN ('Obligatorio', 'Timbrado')
                  AND DF.DateOperation >= CAST(? AS DATE)
                  AND DF.DateOperation < DATEADD(DAY, 1, CAST(? AS DATE))
                  {filtro_usuario}
            )
            SELECT D.DocumentID,
                   ISNULL(D.FolioPrefix, '') + ISNULL(D.Folio, '') AS DocFolio,
                   CONVERT(NVARCHAR(10), D.CreatedOn, 23) AS FechaDocto,
                   CONVERT(NVARCHAR(10), DF.DateAffectation, 23) AS FechaCobro,
                   DF.FinancialOperationID AS IDOperacion, E.OfficialName AS Cliente,
                   DF.ComplementoStatusObligatorio, FP.Value AS FormaPagoCobro,
                   CFD2.RFC, CFD2.MetodoPago, CFD2.FormaPago, CFD2.ReceptorUsoCFDI,
                   CAST(DP.Amount AS DECIMAL(18, 2)) AS Total,
                   CAST(DF.Amount AS DECIMAL(18, 2)) AS TotalCobro,
                   CAST(D.Balance AS DECIMAL(18, 2)) AS Saldo,
                   U.UserName AS TimbradoPor,
                   CONVERT(NVARCHAR(10), CFD.CFDIFechaCertificacion, 23) AS FechaTimbrado,
                   ISNULL(DF.EmailSend, 0) AS EmailSend
            FROM OperacionesFiltradas AS DF
            LEFT JOIN dbo.orgBusinessEntity AS E ON DF.BusinessEntityID = E.BusinessEntityID
            LEFT JOIN dbo.docDocumentPayment AS DP
                ON DF.FinancialOperationID = DP.FinancialOperationID
            LEFT JOIN dbo.docDocument AS D
                ON DP.DocumentID = D.DocumentID
               AND D.chkCustom1 = 0
               AND D.ModuleID IN (21, 1316, 1319, 1400)
            LEFT JOIN dbo.docDocumentCFD AS CFD
                ON DF.FinancialOperationID = CFD.FinancialOperationID
            LEFT JOIN dbo.docDocumentCFD AS CFD2 ON D.DocumentID = CFD2.DocumentID
            LEFT JOIN dbo.engUser AS U ON CFD.UserID = U.UserID
            LEFT JOIN dbo.vwcboAnexo20v33_FormaPago AS FP ON DF.PaymentMethodID = FP.ID
            ORDER BY DF.FinancialOperationID, D.DocumentID
        """.format(filtro_usuario=filtro_usuario)
        parametros = (
            self.normalizar_fecha(fecha_inicial),
            self.normalizar_fecha(fecha_final),
        ) + parametros_usuario
        return self._base_de_datos.fetchall(consulta, parametros)

    @staticmethod
    def _dinero(valor):
        try:
            return f'{float(valor or 0):,.2f}'
        except (TypeError, ValueError):
            return str(valor or '')

    def generar_documento(self, registros, fecha_inicial, fecha_final):
        if not self._plantilla.exists():
            raise FileNotFoundError(f'No se encontró la plantilla: {self._plantilla}')
        grupos = {}
        for registro in registros:
            grupos.setdefault(registro.get('IDOperacion'), []).append(registro)

        bloques = []
        for operacion_id, detalles in grupos.items():
            cabecera = detalles[0]
            filas = []
            for dato in detalles:
                valores = (
                    dato.get('DocFolio'), dato.get('FormaPagoCobro'),
                    dato.get('ComplementoStatusObligatorio'), dato.get('FechaDocto'),
                    dato.get('FechaCobro'), dato.get('FechaTimbrado'), dato.get('RFC'),
                    dato.get('MetodoPago'), dato.get('FormaPago'), dato.get('ReceptorUsoCFDI'),
                    self._dinero(dato.get('Total')), self._dinero(dato.get('Saldo')),
                    'Sí' if bool(dato.get('EmailSend')) else 'No',
                )
                filas.append('<tr>' + ''.join(
                    f'<td>{escape(str(valor or ""))}</td>' for valor in valores) + '</tr>')
            bloques.append(
                '<section class="operacion"><div class="resumen">'
                f'<span><b>Cliente:</b> {escape(str(cabecera.get("Cliente") or ""))}</span>'
                f'<span><b>Timbrado por:</b> {escape(str(cabecera.get("TimbradoPor") or ""))}</span>'
                f'<span><b>Operación:</b> {escape(str(operacion_id or ""))}</span>'
                f'<span><b>Total cobro:</b> {self._dinero(cabecera.get("TotalCobro"))}</span>'
                '</div><table><thead><tr><th>Folio</th><th>Forma cobro</th><th>Estatus</th>'
                '<th>Fecha docto.</th><th>Fecha cobro</th><th>Fecha timbrado</th><th>RFC</th>'
                '<th>Método</th><th>Forma CFDI</th><th>Uso CFDI</th><th>Total</th><th>Saldo</th>'
                '<th>Correo</th></tr></thead><tbody>' + ''.join(filas) + '</tbody></table></section>')

        contenido = self._plantilla.read_text(encoding='utf-8')
        contenido = (contenido.replace('{fecha_inicial}', self.normalizar_fecha(fecha_inicial))
                     .replace('{fecha_final}', self.normalizar_fecha(fecha_final))
                     .replace('{total_operaciones}', str(len(grupos)))
                     .replace('{detalle_complementos}', ''.join(bloques)))
        archivo = Path(tempfile.gettempdir()) / 'complementos_cayal_impresion.html'
        archivo.write_text(contenido, encoding='utf-8')
        return archivo

    @staticmethod
    def imprimir_documento(archivo):
        webbrowser.open(Path(archivo).resolve().as_uri())
