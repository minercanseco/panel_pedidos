import logging
import os
import re
import threading
from types import SimpleNamespace

from cayal.util import Utilerias
from cayal.impuestos import Impuestos

from herramientas.capturar_documento.herramientas.imprimir_modulo.imprimir_modulo import (
    ImprimirModulo,
)
from herramientas.capturar_documento.plantillas.cfdi_ticket import CFDITicket
from herramientas.capturar_documento.selector_modulo.servicio_impresion_silenciosa import (
    ServicioImpresionSilenciosa,
)


logger = logging.getLogger(__name__)


class ServicioGeneracionCFDITicket:
    """Genera e imprime la representación térmica del módulo 1400."""

    MODULO_CFDI = 1400
    # Encabezado, datos fiscales, totales, QR y pie. La altura adicional por
    # partida la calcula ServicioImpresionTicket. Usar 360 mm para cualquier
    # CFDI hacía que Sumatra centrara un documento corto y alimentara cerca de
    # 10 cm de papel antes de comenzar a imprimir.
    ALTURA_BASE_CFDI_MM = 270

    def __init__(
            self, base_de_datos, user_id,
            user_name='', identificador_ejecucion='',
    ):
        self.base_de_datos = base_de_datos
        self.user_id = int(user_id or 0)
        self.user_name = self._normalizar_usuario(user_name)
        self.identificador_ejecucion = str(
            identificador_ejecucion or 'CFDI'
        )

    def generar_e_imprimir_en_segundo_plano(self, document_id):
        document_id = int(document_id or 0)

        def ejecutar():
            try:
                # La afectación fiscal debe terminar antes de consultar los
                # datos del formato o enviar el trabajo a cualquier impresora.
                # Se repite aquí de forma intencional porque este servicio se
                # ejecuta en segundo plano y constituye la última frontera
                # antes de imprimir.
                self._garantizar_impuestos(document_id)
                archivos = self.generar_archivos(document_id)
                parametros_impresion = SimpleNamespace(
                    id_modulo=self.MODULO_CFDI,
                    id_principal=document_id,
                    id_usuario=self.user_id,
                    uuid=self.identificador_ejecucion,
                    impresora='',
                )
                servicio = ServicioImpresionSilenciosa(
                    parametros=parametros_impresion,
                    modelo=self.base_de_datos,
                )
                primaria, secundaria = (
                    servicio._obtener_impresoras_configuradas()
                )
                servicio.imprimir_archivos_generados(
                    [ruta for ruta, _ in archivos],
                    impresora_primaria=primaria,
                    impresora_secundaria=secundaria,
                    cantidades_partidas={
                        ruta: cantidad_partidas
                        for ruta, cantidad_partidas in archivos
                    },
                    datos_enrutamiento=self._datos_enrutamiento,
                )
                self._registrar_impresion(document_id)
            except Exception:
                logger.exception(
                    'No fue posible generar el CFDI ticket del documento %s.',
                    document_id,
                )

        hilo = threading.Thread(
            target=ejecutar,
            name=f'generacion-cfdi-ticket-{document_id}',
            daemon=False,
        )
        hilo.start()
        return hilo

    def _garantizar_impuestos(self, document_id):
        Impuestos.afectar_impuestos_documento(
            self.base_de_datos,
            int(document_id),
        )

        conceptos_incompletos = self.base_de_datos.fetchall(
            '''
            SELECT I.DocumentItemID
            FROM dbo.docDocumentItem I
            WHERE I.DocumentID = ?
              AND I.DeletedOn IS NULL
              AND I.ObjetoImpuesto = N'02'
              AND (
                    NOT EXISTS (
                        SELECT 1
                        FROM dbo.docDocumentTaxDetail TD
                        WHERE TD.DocumentID = I.DocumentID
                          AND TD.DocumentItemID = I.DocumentItemID
                    )
                    OR NOT EXISTS (
                        SELECT 1
                        FROM dbo.docDocumentItemTax IT
                        WHERE IT.DocumentID = I.DocumentID
                          AND IT.DocumentItemID = I.DocumentItemID
                    )
              )
            ''',
            (int(document_id),),
        )
        if conceptos_incompletos:
            ids = ', '.join(
                str(fila['DocumentItemID'])
                for fila in conceptos_incompletos
            )
            raise RuntimeError(
                'No se imprimirá el documento {} porque sus impuestos '
                'quedaron incompletos en las partidas: {}.'.format(
                    document_id,
                    ids,
                )
            )

    def generar(self, document_id):
        """Conserva la interfaz anterior devolviendo el primer archivo."""
        archivos = self.generar_archivos(document_id)
        if not archivos:
            raise RuntimeError(
                f'No se generaron archivos para el CFDI {document_id}.'
            )
        return archivos[0]

    def generar_archivos(self, document_id):
        if int(document_id or 0) <= 0:
            raise ValueError('El CFDI ticket requiere un DocumentID válido.')

        proveedor_datos = ImprimirModulo.__new__(ImprimirModulo)
        proveedor_datos._base_de_datos = self.base_de_datos
        proveedor_datos._utilerias = Utilerias()
        proveedor_datos._user_name = self.user_name
        info = proveedor_datos._buscar_info_factura(int(document_id))

        placeholders = dict(info.get('placeholders') or {})
        detalle = list(info.get('detalle') or [])
        if not placeholders:
            raise ValueError(
                f'No se encontraron datos para el CFDI {document_id}.'
            )

        # La consulta de ImprimirModulo ya resuelve correctamente el cliente
        # real, incluyendo documentos capturados con BusinessEntityID 8179 y
        # CustomerID en docDocumentExt. Se conserva esta información para no
        # reclasificar el destino con una consulta menos completa.
        self._datos_enrutamiento = {
            int(document_id): {
                'RutaID': placeholders.get('ZoneID', 0),
                'Impresiones': placeholders.get('Impresiones', 1),
            }
        }

        # TotalLetter puede no haberse actualizado todavía al cerrar la
        # captura. Igual que ticket_158, generamos el texto desde el total
        # numérico para que la impresión no dependa de ese campo persistido.
        placeholders['CantidadConLetra'] = self._cantidad_con_letra(
            int(document_id),
            proveedor_datos._utilerias,
        )

        plantilla = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'plantillas',
            'cfdi_ticket.html',
        )
        cancelado = self._documento_cancelado(document_id)
        tiene_historial = self._documento_tiene_historial(document_id)
        proveedor_datos._seleccionados_cancelados = (
            [document_id] if cancelado else []
        )
        proveedor_datos._seleccionados_historial = (
            [document_id] if tiene_historial else []
        )
        cantidad = proveedor_datos._determinar_cantidad_impresiones(
            placeholders,
            motivo_id=1,
            document_id=document_id,
        )

        descuento = proveedor_datos._utilerias.redondear_valor_cantidad_a_decimal(
            placeholders.get('DescuentoCayal', 0)
        )
        es_factura = placeholders.get('TipoCFD', 'FACTURA') == 'FACTURA'
        archivos_generados = []

        for copia_idx in range(cantidad):
            texto, marca_id = proveedor_datos._determinar_texto_marca(
                cantidad=cantidad,
                motivo_id=1,
                copia_idx=copia_idx,
                esta_cancelado=cancelado,
            )
            ticket = CFDITicket()
            ticket.set_plantilla(plantilla)
            ticket.set_marca_agua(motivo_id=marca_id)

            # El DocumentID queda al final para que el enrutador consulte la
            # ruta y el número de impresiones del cliente.
            nombre_archivo = (
                f'{texto}-{self.identificador_ejecucion}-'
                f'{copia_idx}({cantidad})_{document_id}'
            )
            ticket.set_datos(**placeholders, uuid=nombre_archivo)
            ticket.set_partidas(detalle)
            html = ticket.generar_html()

            if descuento == 0:
                html = re.sub(
                    r'<!--IF_DESCUENTO-->.*?<!--END_IF-->\s*',
                    '',
                    html,
                    flags=re.DOTALL,
                )

            if es_factura:
                html = html.replace('<!--IF_REMISION-->', '')
                html = html.replace('<!--END_IF-->', '')
            else:
                html = re.sub(
                    r'<!--IF_REMISION-->.*?<!--END_IF-->\s*',
                    '',
                    html,
                    flags=re.DOTALL,
                )

            directorio = ticket._obtener_directorio_salida(temporal=False)
            ruta = os.path.join(directorio, f'{nombre_archivo}.html')
            with open(ruta, 'w', encoding='utf-8') as archivo:
                archivo.write(html)
            archivos_generados.append((ruta, len(detalle)))

        return archivos_generados

    def _documento_cancelado(self, document_id):
        return bool(self.base_de_datos.fetchone(
            'SELECT CASE WHEN CancelledOn IS NULL THEN 0 ELSE 1 END '
            'FROM docDocument WHERE DocumentID = ?',
            (int(document_id),),
        ))

    def _documento_tiene_historial(self, document_id):
        return bool(self.base_de_datos.fetchone(
            'SELECT CASE WHEN EXISTS ('
            'SELECT 1 FROM zvwhistorialimpresiones WHERE DocumentID = ?'
            ') THEN 1 ELSE 0 END',
            (int(document_id),),
        ))

    def _registrar_impresion(self, document_id):
        """Registra una sola operación aunque se hayan generado dos copias."""
        self.base_de_datos.command(
            'INSERT INTO zvwhistorialimpresiones '
            '(DocumentID, Impreso, ImpresoPor, ModuloID, MotivoID) '
            'VALUES (?, GETDATE(), ?, ?, 1); '
            'UPDATE docDocument SET PrintedOn = GETDATE(), PrintedBy = ? '
            'WHERE DocumentID = ?',
            (
                int(document_id),
                self.user_id,
                self.MODULO_CFDI,
                self.user_id,
                int(document_id),
            ),
        )

    def _cantidad_con_letra(self, document_id, utilerias):
        total = self.base_de_datos.fetchone(
            'SELECT ISNULL(Total, 0) AS Total '
            'FROM docDocument WHERE DocumentID = ?',
            (int(document_id),),
        )
        if total is None:
            raise ValueError(
                f'No se encontró el total del CFDI {document_id}.'
            )
        total = utilerias.redondear_valor_cantidad_a_decimal(total)
        return utilerias.cantidad_con_letra(total)

    def _normalizar_usuario(self, user_name):
        if isinstance(user_name, dict):
            return str(user_name.get('UserName', '') or '')
        if isinstance(user_name, (tuple, list)):
            return str(user_name[0] if user_name else '')
        if user_name:
            return str(user_name)
        resultado = self.base_de_datos.fetchone(
            'SELECT UserName FROM engUser WHERE UserID = ?',
            (self.user_id,),
        )
        if isinstance(resultado, dict):
            return str(resultado.get('UserName', '') or '')
        if isinstance(resultado, (tuple, list)):
            return str(resultado[0] if resultado else '')
        return str(resultado or '')
