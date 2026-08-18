import gzip
import html
import json
import tempfile
from pathlib import Path

MODULO_CORTE_CAJA = -1


class ImpresionCorteCaja:
    """Adapta el generador original de cortes al flujo de imprimir módulo."""

    def __init__(self, parametros, base_de_datos):
        self._parametros = parametros
        self._base_de_datos = base_de_datos

    def generar(self, corte_id, directorio=None):
        corte_id = int(corte_id or 0)
        if corte_id <= 0:
            raise ValueError('El identificador del corte no es válido.')

        info = self._buscar_informacion_corte(corte_id)
        if not info['info_corte']:
            raise LookupError(f'No se encontró el corte {corte_id}.')

        contenido = self._ruta_plantilla().read_text(encoding='utf-8')
        for clave, valor in dict(info['info_corte'][0]).items():
            contenido = contenido.replace(
                f'{{{clave}}}', html.escape(str(valor or ''))
            )

        tablas = {
            'depositos_relacionados': (
                info['depositos_relacionados'], 'DEPOSITOS RELACIONADOS'
            ),
            'transferencias': (
                info['transferencias_corte'], 'TRANSFERENCIAS'
            ),
            'cheques': (info['cheques_corte'], 'CHEQUES'),
            'gastos': (info['gastos_cajero'], 'GASTOS'),
            'anticipos': (info['anticipos_cajero'], 'ANTICIPOS'),
            'rubros_corte': (info['rubros_corte'], 'GENERALES CORTE'),
            'relacion_efectivo': (
                info['efectivo_corte'], 'RELACION EFECTIVO'
            ),
        }
        for marcador, (registros, titulo) in tablas.items():
            contenido = contenido.replace(
                f'{{{marcador}}}', self._crear_tabla(registros, titulo)
            )

        if directorio is None:
            uuid_impresion = str(getattr(self._parametros, 'uuid', '') or '')
            directorio = (
                Path(tempfile.gettempdir()) / uuid_impresion
                if uuid_impresion
                else Path(tempfile.gettempdir()) / 'cayal_cortes_caja'
            )
        directorio = Path(directorio)
        directorio.mkdir(parents=True, exist_ok=True)
        ruta = directorio / f'CC{corte_id}.html'
        ruta.write_text(contenido, encoding='utf-8')
        return ruta

    @staticmethod
    def _crear_tabla(registros, titulo):
        registros = list(registros or [])
        if not registros:
            return ''

        columnas = list(dict(registros[0]).keys())
        encabezados = ''.join(
            f'<th class="numero">{html.escape(str(columna))}</th>'
            for columna in columnas
        )
        filas = []
        for registro in registros:
            datos = dict(registro)
            celdas = ''.join(
                '<td class="numero">{}</td>'.format(
                    html.escape(str(datos.get(columna, '') or ''))
                )
                for columna in columnas
            )
            filas.append(f'<tr>{celdas}</tr>')

        return (
            f'<caption>{html.escape(titulo)}</caption>'
            '<table border="0" class="dataframe table">'
            f'<thead><tr>{encabezados}</tr></thead>'
            f'<tbody>{"".join(filas)}</tbody></table>'
        )

    def imprimir(self, corte_id):
        ruta = self.generar(corte_id)
        impresora = self._impresora_configurada()
        if not impresora:
            raise RuntimeError(
                'No hay una impresora secundaria configurada en imprimir módulo.'
            )

        from capturar_documento.selector_modulo.servicio_impresion_ticket import (
            ServicioImpresionTicket,
        )

        ServicioImpresionTicket().imprimir_html_en_impresora(
            ruta_html=ruta,
            impresora=impresora,
            cantidad_partidas=0,
            altura_base_mm=297,
            ancho_papel_mm=210,
        )
        return ruta

    def _buscar_informacion_corte(self, corte_id):
        db = self._base_de_datos
        return {
            'info_corte': db.fetchall(
                '''
                SELECT CAST(Fecha as date) Fecha,
                       FORMAT(Fecha, 'HH:mm') AS Hora,
                       Cajero,
                       'CC' + CAST(DATEPART(YEAR, GETDATE()) AS VARCHAR)
                            + CAST(ID AS VARCHAR) AS Folio
                FROM zvwCortesDeCaja
                WHERE ID = ?
                ''',
                (corte_id,),
            ),
            'depositos_relacionados': db.fetchall(
                '''
                SELECT DP.UsuarioDesposito AS Emisor,
                       FORMAT(SUM(DP.MontoDeposito), 'C', 'es-MX') AS Monto
                FROM zvwCortesDeCaja CT
                INNER JOIN zvwDepositosCortesDeCaja DP
                    ON CT.ID = DP.CorteID
                WHERE DP.CorteID = ?
                GROUP BY DP.UsuarioDesposito
                ''',
                (corte_id,),
            ),
            'transferencias_corte': db.fetchall(
                '''
                SELECT OfficialName Cliente,
                       FORMAT(SUM(Amount), 'C', 'es-MX') Cobro
                FROM zvwCortesCajaItemDetalle
                WHERE CorteID = ? AND PaymentMethodID = 3
                GROUP BY FinancialOperationID, OfficialName
                ORDER BY OfficialName
                ''',
                (corte_id,),
            ),
            'cheques_corte': db.fetchall(
                '''
                SELECT OfficialName Cliente,
                       FORMAT(SUM(Amount), 'C', 'es-MX') Cobro
                FROM zvwCortesCajaItemDetalle
                WHERE CorteID = ? AND PaymentMethodID = 2
                GROUP BY FinancialOperationID, OfficialName
                ORDER BY OfficialName
                ''',
                (corte_id,),
            ),
            'gastos_cajero': db.fetchall(
                '''
                SELECT ReceptorGasto Receptor,
                       FORMAT(MontoGasto, 'C', 'es-MX') Monto
                FROM zvwGastosCorteDeCaja WHERE CorteID = ?
                ''',
                (corte_id,),
            ),
            'anticipos_cajero': db.fetchall(
                '''
                SELECT EmisorAnticipo Emisor,
                       FORMAT(MontoAnticipo, 'C', 'es-MX') Monto
                FROM zvwAnticiposCorteDeCaja WHERE CorteID = ?
                ''',
                (corte_id,),
            ),
            'rubros_corte': db.fetchall(
                'EXEC ConsultarCortes @CorteID = ?', (corte_id,)
            ),
            'efectivo_corte': db.fetchall(
                'EXEC ObtenerEfectivoPorCorteID @CorteID = ?', (corte_id,)
            ),
        }

    @staticmethod
    def _ruta_plantilla():
        return (
            Path(__file__).resolve().parents[2]
            / 'plantillas'
            / 'plantilla_corte_caja.html'
        )

    @staticmethod
    def _impresora_configurada():
        ruta = Path(__file__).resolve().parent / 'impresoras.gz'
        if not ruta.is_file():
            return None
        with gzip.open(ruta, 'rt', encoding='utf-8') as archivo:
            return (json.load(archivo).get('secundaria') or '').strip()
