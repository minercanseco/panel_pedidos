from cayal.util import Utilerias

from .crear_pdf import CrearPDF


def generar_pdf_documento(
        parametros_contpaqi, base_de_datos, document_id, utilerias=None,
):
    document_id = int(document_id or 0)
    if document_id <= 0:
        raise ValueError('El documento seleccionado no es válido.')

    valores_documento = base_de_datos.validar_documento(document_id)
    if not valores_documento:
        raise ValueError('No se encontró el documento seleccionado.')
    if valores_documento.get('deleted'):
        raise ValueError('El documento seleccionado está eliminado.')
    if int(valores_documento.get('status_cfdi', 0) or 0) != 3:
        raise ValueError(
            'El PDF sólo puede generarse cuando la factura está timbrada.'
        )

    rfc_timbrado = base_de_datos.fetchone(
        'SELECT RFC FROM docDocumentCFD WHERE DocumentID = ?',
        (document_id,),
    )
    rfc_timbrado = str(rfc_timbrado or '').strip()
    if not rfc_timbrado:
        raise ValueError('La factura timbrada no tiene RFC asociado.')

    doc_folio = str(valores_documento.get('doc_folio') or '').strip()
    if not doc_folio:
        raise ValueError('La factura no tiene folio para nombrar el PDF.')

    directorio = base_de_datos.fetchone(
        'SELECT CFDDocumentsPath FROM orgBusinessEntityCFD '
        'WHERE BusinessEntityID = 1'
    )
    directorio = str(directorio or '').strip()
    if not directorio:
        raise ValueError(
            'No está configurada la ruta de documentos timbrados.'
        )

    nombre_pdf = (
        f'CCA030210S3A_FACTURA_CFDi-{doc_folio}_{rfc_timbrado}.pdf'
    )
    creador = CrearPDF(
        parametros_contpaqi=parametros_contpaqi,
        base_de_datos=base_de_datos,
        utilerias=utilerias or Utilerias(),
        path_documentos_timbrados=directorio,
    )
    return creador.crear_pdf_documento(
        nombre_pdf, document_id, valores_documento
    )
