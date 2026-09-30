import os
import subprocess


def obtener_ruta_xml_documento(base_de_datos, document_id):
    document_id = int(document_id or 0)
    if document_id <= 0:
        raise ValueError('El documento seleccionado no es válido.')

    valores = base_de_datos.validar_documento(document_id)
    if not valores:
        raise ValueError('No se encontró el documento seleccionado.')
    if valores.get('deleted'):
        raise ValueError('El documento seleccionado está eliminado.')
    if int(valores.get('status_cfdi', 0) or 0) != 3:
        raise ValueError(
            'El XML sólo puede abrirse cuando la factura está timbrada.'
        )

    folio = str(valores.get('doc_folio') or '').strip()
    if not folio:
        raise ValueError('La factura no tiene folio para localizar el XML.')
    rfc = base_de_datos.fetchone(
        'SELECT RFC FROM docDocumentCFD WHERE DocumentID = ?',
        (document_id,),
    )
    rfc = str(rfc or '').strip()
    if not rfc:
        raise ValueError('La factura timbrada no tiene RFC asociado.')

    directorio = base_de_datos.fetchone(
        'SELECT CFDDocumentsPath FROM orgBusinessEntityCFD '
        'WHERE BusinessEntityID = 1'
    )
    directorio = str(directorio or '').strip()
    if not directorio:
        raise ValueError(
            'No está configurada la ruta de documentos timbrados.'
        )

    nombre = f'CCA030210S3A_FACTURA_CFDi-{folio}_{rfc}.xml'
    ruta_xml = os.path.abspath(os.path.join(directorio, nombre))
    if not os.path.isfile(ruta_xml):
        raise FileNotFoundError(
            f'No se encontró el XML timbrado:\n{ruta_xml}'
        )
    return ruta_xml


def abrir_xml_documento(base_de_datos, document_id):
    ruta_xml = obtener_ruta_xml_documento(base_de_datos, document_id)
    subprocess.Popen(['notepad.exe', ruta_xml])
    return ruta_xml
