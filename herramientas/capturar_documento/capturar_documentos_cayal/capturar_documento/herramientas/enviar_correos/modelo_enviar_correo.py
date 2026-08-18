import os
import shutil

from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.documento import Documento
from cayal.util import Utilerias
from cayal.correo import Correo
from capturar_documento.herramientas.enviar_correos.generar_pdf_factura import (
    GenerarPDFFactura,
)
from cayal.servicio_configuracion_correo import ServicioConfiguracionCorreo


class ModeloEnviarCorreo:

    def __init__(self, parametros, funcionamiento_prueba=None):
        self.parametros = parametros
        self.base_de_datos = ComandosBaseDatos()
        self.documento = Documento()
        self.utilerias = Utilerias()
        self.correo = Correo()

        self.funcionamiento_prueba = funcionamiento_prueba
        self.ultimo_error_pdf = ''

        self.module_id = int(self.parametros.id_modulo)
        self.user_id = self.parametros.id_usuario or 90
        self.user_name = self.base_de_datos.buscar_nombre_de_usuario(self.user_id)

        self.items_seleccionados = list(set(self.parametros.id_seleccionados))

        self.path_documentos_timbrados = self.base_de_datos.fetchone(
            'SELECT CFDDocumentsPath FROM orgBusinessEntityCFD WHERE BusinessEntityID=1'
        )

        self.generar_documento_factura = GenerarPDFFactura(
            self.parametros,
            self.base_de_datos,
            self.utilerias
        )

        self.servicio_configuracion_correo = ServicioConfiguracionCorreo(
            self.base_de_datos
        )

    # =========================================================
    # CONFIGURACIÓN DE CORREO
    # =========================================================

    def setear_parametros_correo(self, correo_id=7):
        parametros = self.servicio_configuracion_correo.obtener_configuracion_correo(
            correo_id=correo_id
        )

        if not parametros:
            return False

        if not all(parametros.values()):
            return False

        self.correo.remitente = parametros['remitente']
        self.correo.contrasena = parametros['password']
        self.correo.servidor_smtp = parametros['servidor_smtp']
        self.correo.puerto = parametros['puerto_smtp']

        return True

    # =========================================================
    # PENDIENTES
    # =========================================================

    def buscar_pendientes_envio_documentos(self):
        if self.module_id in (1400, 21, 1319):
            return list(set(self.items_seleccionados))

        if self.user_id != 90:
            return []

        sql = """
        SELECT D.DocumentID
        FROM dbo.docDocument D
        JOIN dbo.docDocumentCFD CFD
          ON D.DocumentID = CFD.DocumentID
        WHERE 
          D.chkCustom1 = 0
          AND D.CancelledOn IS NULL
          AND ISNULL(D.EmailSend,0) = 0
          AND D.ModuleID IN (1319, 1400, 21)

        UNION ALL

        SELECT D.DocumentID
        FROM dbo.docDocument D
        JOIN dbo.docDocumentCFD CFD
          ON D.DocumentID = CFD.DocumentID
        WHERE 
          D.ModuleID IN (1400, 21,1319)
          AND D.chkCustom1 = 1
          AND D.CancelledOn IS NULL
          AND ISNULL(D.EmailSend,0) = 0
          AND ISNULL(D.Custom3, 0) = 1040

        UNION ALL

        SELECT D.DocumentID
        FROM dbo.docDocument D
        JOIN dbo.docDocumentCFD CFD
          ON D.DocumentID = CFD.DocumentID
        JOIN dbo.orgBusinessEntity E
          ON D.BusinessEntityID = E.BusinessEntityID
        WHERE 
          D.ModuleID IN (1400, 21,1319)
          AND D.chkCustom1 = 1
          AND D.CancelledOn IS NULL
          AND D.EmailSend = 0
          AND ISNULL(E.EnviarRemisiones, 0) = 1
        """

        consulta = self.base_de_datos.fetchall(sql)
        return list(set([reg['DocumentID'] for reg in consulta]))

    def buscar_pendientes_envio_complementos(self):
        if self.module_id == 248:
            return list(set(self.items_seleccionados))

        if self.user_id != 90:
            return []

        sql = """
        SELECT CFD.FinancialOperationID
        FROM docDocumentCFD CFD
        INNER JOIN docFinancialOperation DF
            ON CFD.FinancialOperationID = DF.FinancialOperationID
        WHERE 
          CFDIFolioFiscal IS NOT NULL
          AND CFD.DocumentID = 0
          AND ISNULL(DF.EmailSend,0) = 0
          AND ModuleID = 248
          AND CFDiCancellationReasonID IS NULL
          AND DF.DeletedOn IS NULL
        """

        consulta = self.base_de_datos.fetchall(sql)
        return list(set([reg['FinancialOperationID'] for reg in consulta]))

    # =========================================================
    # VALIDACIONES BASE
    # =========================================================

    def validar_complemento(self, financial_operation_id):
        return self.base_de_datos.validar_complemento(financial_operation_id)

    def validar_documento(self, document_id):
        return self.base_de_datos.validar_documento(document_id)

    def obtener_documento_por_complemento(self, financial_operation_id):
        return self.base_de_datos.fetchone(
            """
            SELECT DocumentID
            FROM docDocumentPayment
            WHERE FinancialOperationID = ?
              AND DeletedOn IS NULL
            ORDER BY Amount DESC
            """,
            (financial_operation_id,)
        )

    def obtener_correos_cliente(self, business_entity_id, depot_id=0):
        if depot_id:
            return self.base_de_datos.fetchone(
                'SELECT Correos FROM orgDepot WHERE DepotID = ?',
                (depot_id,)
            )

        return self.base_de_datos.fetchone(
            'SELECT BusinessEntityEmail FROM orgBusinessEntityMainInfo WHERE BusinessEntityID = ?',
            (business_entity_id,)
        )

    def obtener_rfc_timbrado(self, document_id):
        return self.base_de_datos.fetchone(
            'SELECT RFC FROM docDocumentCFD WHERE DocumentID = ?',
            (document_id,)
        )

    def obtener_nombre_depot(self, depot_id):
        if not depot_id:
            return ''

        return self.base_de_datos.fetchone(
            'SELECT DepotName FROM orgDepot WHERE DepotID = ?',
            (depot_id,)
        ) or ''

    def obtener_nombre_cliente(self, business_entity_id):
        official_name = self.base_de_datos.fetchone(
            'SELECT OfficialName FROM orgBusinessEntity WHERE BusinessEntityID = ?',
            (business_entity_id,)
        )

        official_name = (official_name or '').strip()
        return self.utilerias.limitar_caracteres(official_name, 30)

    # =========================================================
    # ARCHIVOS
    # =========================================================

    def comprobar_path_archivo(self, nombre_archivo):
        path_archivo = os.path.join(self.path_documentos_timbrados, nombre_archivo)

        if not os.path.exists(path_archivo):
            return False

        return path_archivo

    def crear_nombre_archivo_factura(self, tipo_archivo, rfc_timbrado, doc_folio):
        if tipo_archivo == 'xml':
            return f'CCA030210S3A_FACTURA_CFDi-{doc_folio}_{rfc_timbrado}.xml'

        if tipo_archivo == 'pdf':
            return f'CCA030210S3A_FACTURA_CFDi-{doc_folio}_{rfc_timbrado}.pdf'

        return ''

    def crear_nombre_archivo_complemento(self, tipo_archivo, financial_operation_id, rfc_timbrado):
        if tipo_archivo == 'xml':
            return f'CCA030210S3A_COBRO_CLIENTE_CFDi-ID{financial_operation_id}_{rfc_timbrado}.xml'

        if tipo_archivo == 'pdf':
            return f'CCA030210S3A_COBRO_CLIENTE_CFDi-ID{financial_operation_id}_{rfc_timbrado}.pdf'

        return ''

    def crear_pdf_documento(self, nombre_pdf, document_id, valores_documento):
        self.ultimo_error_pdf = ''
        try:
            nombre_pdf = os.path.basename(nombre_pdf)
            base_nombre, _ = os.path.splitext(nombre_pdf)

            saldo = valores_documento.get('balance', 0)
            zone_id = int(valores_documento.get('zone_id', 0))

            self.generar_documento_factura.marca_de_agua_id = (
                1 if saldo == 0 else 4
            )

            if zone_id == 1043:
                self.generar_documento_factura.marca_de_agua_id = 5

            self.generar_documento_factura.nombre_archivo = base_nombre
            self.generar_documento_factura.document_id = document_id

            print(f'[PDF] Generando HTML del documento {document_id}...')

            ruta_html = self.generar_documento_factura.generar_archivo_cfdi(
                motivo_id=7
            )

            if not ruta_html or not os.path.exists(ruta_html):
                print(f'[PDF] No se generó el HTML del documento {document_id}.')
                return False

            base_html, extension_html = os.path.splitext(ruta_html)

            if extension_html.lower() == ".hmtl":
                ruta_html = base_html + ".html"

            carpeta = os.path.dirname(os.path.abspath(ruta_html))
            ruta_pdf = os.path.join(
                carpeta,
                base_nombre + ".pdf"
            )

            print(f'[PDF] Convirtiendo HTML a PDF ({document_id})...')

            self.generar_documento_factura.html_a_pdf(
                ruta_html=ruta_html,
                ruta_pdf=ruta_pdf
            )

            if not os.path.exists(ruta_pdf):
                print(f'[PDF] No fue posible generar el PDF del documento {document_id}.')
                return False

            print(f'[PDF] Moviendo archivos a documentos timbrados ({document_id})...')

            self.mover_a_documentos_timbrados(
                ruta_html,
                ruta_pdf,
                self.path_documentos_timbrados
            )

            print(f'[PDF] Marcando PDF como generado ({document_id})...')

            self.marcar_pdf_como_generado(document_id)

            print(f'[PDF] Documento {document_id} generado correctamente.')

            return True

        except Exception as ex:
            self.ultimo_error_pdf = str(ex)
            print(f'[PDF] Error generando PDF del documento {document_id}: {ex}')
            return False

    def mover_a_documentos_timbrados(self, ruta_html, ruta_pdf, path_destino):
        os.makedirs(path_destino, exist_ok=True)

        destino_html = os.path.join(path_destino, os.path.basename(ruta_html))
        destino_pdf = os.path.join(path_destino, os.path.basename(ruta_pdf))

        shutil.move(os.path.abspath(ruta_html), destino_html)
        shutil.move(os.path.abspath(ruta_pdf), destino_pdf)

        return destino_html, destino_pdf

    def marcar_pdf_como_generado(self, document_id):
        self.base_de_datos.command(
            'UPDATE docDocumentCFD SET PDFGenerado = 1 WHERE DocumentID = ?',
            (document_id,)
        )

    # =========================================================
    # ENVÍO / BITÁCORA
    # =========================================================

    def enviar_correo(self):
        if self.funcionamiento_prueba:
            print(self.correo.archivo_adjunto)
            print(self.correo.asunto)
            print(self.correo.destinatario)
            print(self.correo.cuerpo)
            return True, 'PRUEBA'

        return self.correo.enviar_correo()

    def actualizar_bitacora_correos_enviados(
            self,
            documento,
            tipo_de_envio,
            correos,
            doc_folio,
            official_name
    ):
        parametros_bitacora = (
            official_name,
            self.user_name,
            documento,
            tipo_de_envio,
            correos,
            doc_folio
        )

        self.base_de_datos.exec_stored_procedure(
            'InsertarEnHistorialEnvioCorreos',
            parametros_bitacora
        )

    def status_credito(self, business_entity_id):

        def _ultimo_documento_en_cartera(business_entity_id):
            info = self.base_de_datos.fetchall("""
                WITH CTE AS (
                    SELECT
                        D.DocumentID,
                        CAST(D.CreatedOn AS date) AS Fecha,
                        ISNULL(D.FolioPrefix,'') + ISNULL(D.Folio,'') AS Folio,
                        FORMAT(D.Balance,'C','es-MX') AS Saldo,
                        DATEDIFF(DAY, CAST(D.CreatedOn AS date), GETDATE()) AS Dias
                    FROM docDocument D
                    WHERE
                        D.CancelledOn IS NULL
                        AND D.StatusPaidID <> 1
                        AND D.BusinessEntityID = ?
                        AND D.Balance <> 0
                        AND D.ModuleID IN (21,1400)
                )
                SELECT TOP 1 *
                FROM CTE
                ORDER BY DocumentID ASC;
            """, (business_entity_id,))

            if not info:
                return "—"

            i = info[0]

            return f"{i['Folio']} | Saldo {i['Saldo']} | {i['Dias']} días"

        def _buscar_documentos_con_saldo(business_entity_id):
            return self.base_de_datos.fetchall("""
                SELECT
                    CAST(D.CreatedOn AS date) AS Fecha,
                    CASE 
                        WHEN D.chkCustom1 = 1 THEN 'Remisión' 
                        ELSE 'Factura' 
                    END AS Tipo,
                    ISNULL(D.FolioPrefix,'') + ISNULL(D.Folio,'') AS Folio,
                    FORMAT(D.Total,'C','es-MX') AS Total,
                    FORMAT(D.TotalPaid,'C','es-MX') AS Pagado,
                    FORMAT(D.Balance,'C','es-MX') AS Saldo
                FROM docDocument D
                WHERE
                    D.CancelledOn IS NULL
                    AND D.StatusPaidID <> 1
                    AND D.BusinessEntityID = ?
                    AND D.Balance <> 0
                    AND D.ModuleID IN (21,1400)
                ORDER BY D.CreatedOn;
            """, (business_entity_id,))

        if not business_entity_id:
            return ""

        cliente = self.base_de_datos.fetchall("""
            SELECT *
            FROM [dbo].[zvwBuscarInfoCliente-BusinessEntityID](?)
        """, (business_entity_id,))

        if not cliente:
            return ""

        c = cliente[0]

        if c['CreditBlock'] == 1:
            return (
                "🚫 *Crédito bloqueado*\n\n"
                "Actualmente la cuenta presenta bloqueo de crédito.\n"
                "Favor de comunicarse con el área administrativa."
            )

        documentos = _buscar_documentos_con_saldo(business_entity_id)
        ultimo = _ultimo_documento_en_cartera(business_entity_id)

        texto = (
            "📊 *ESTADO DE CUENTA*\n\n"
            "💼 *Resumen de crédito*\n"
            "```\n"
            f"Crédito autorizado : {c['AuthorizedCredit']}\n"
            f"Adeudo total       : {c['Debt']}\n"
            f"Crédito disponible : {c['RemainingCredit']}\n"
            f"Condición de pago  : {c['PaymentTermName']}\n"
            "```\n\n"
            "📌 *Último documento en cartera*\n"
            f"➡️ {ultimo}\n\n"
        )

        if documentos:
            texto += (
                "🧾 *Documentos con saldo pendiente*\n"
                "```\n"
                "Fecha       Folio           Total        Pagado       Saldo\n"
                "-----------------------------------------------------------\n"
            )

            for d in documentos:
                texto += (
                    f"{str(d['Fecha'])[:10]:<11}"
                    f"{d['Folio']:<15}"
                    f"{d['Total']:<12}"
                    f"{d['Pagado']:<12}"
                    f"{d['Saldo']}\n"
                )

            texto += "```\n"
        else:
            texto += "✅ No existen documentos con saldo pendiente.\n\n"

        texto += (
            "⚙️ *Nota*\n"
            "Este estado de cuenta se genera automáticamente con la información "
            "más reciente del sistema.\n"
        )

        return texto
