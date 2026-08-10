import logging
import os
import re
import threading

from cayal.util import Utilerias

from herramientas.capturar_documento.herramientas.imprimir_modulo.imprimir_modulo import (
    ImprimirModulo,
)
from herramientas.capturar_documento.plantillas.cfdi_ticket import CFDITicket
from herramientas.capturar_documento.selector_modulo.servicio_impresion_ticket import (
    ServicioImpresionTicket,
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
                ruta_html, cantidad_partidas = self.generar(document_id)
                ServicioImpresionTicket(
                    self.base_de_datos
                ).imprimir_en_segundo_plano(
                    ruta_html=ruta_html,
                    cantidad_partidas=cantidad_partidas,
                    document_id=document_id,
                    user_id=self.user_id,
                    altura_base_mm=self.ALTURA_BASE_CFDI_MM,
                )
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

    def generar(self, document_id):
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
        ticket = CFDITicket()
        ticket.set_plantilla(plantilla)
        ticket.set_marca_agua(motivo_id=1)

        nombre_archivo = (
            f'ORIGINAL-{self.identificador_ejecucion}-{document_id}'
        )
        ticket.set_datos(**placeholders, uuid=nombre_archivo)
        ticket.set_partidas(detalle)
        html = ticket.generar_html()

        descuento = proveedor_datos._utilerias.redondear_valor_cantidad_a_decimal(
            placeholders.get('DescuentoCayal', 0)
        )
        if descuento == 0:
            html = re.sub(
                r'<!--IF_DESCUENTO-->.*?<!--END_IF-->\s*',
                '',
                html,
                flags=re.DOTALL,
            )

        es_factura = placeholders.get('TipoCFD', 'FACTURA') == 'FACTURA'
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
        return ruta, len(detalle)

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
