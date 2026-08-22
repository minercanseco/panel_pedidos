import tkinter as tk
from cayal.ventanas import Ventanas


class TablaDetalles:
    def __init__(self, master, utilerias, consulta, tipo=None):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._utilerias = utilerias

        self._tipo = tipo

        self._consulta = self._procesar_consulta(consulta)
        self._crear_frames()

        self._ventanas.crear_table_view(nombre='tbv_tabla',
                                        frame='frame_tabla',
                                        columnas=self._crear_columnas_tabla(),
                                        filas=10,
                                        stripecolor=True
                                        )
        self._ventanas.rellenar_table_view('tbv_tabla',self._crear_columnas_tabla(), self._consulta)

        texto, titulo = self._crear_titulo_y_etiqueta()

        self._ventanas.configurar_ventana_ttkbootstrap(titulo=titulo)
        self._ventanas.actualizar_etiqueta_externa_tabla_view('tbv_tabla', texto)

    def _crear_titulo_y_etiqueta(self):
        if not self._tipo:
            cobros = len(set([reg['financial_operation_id'] for reg in self._consulta]))
            return f"Documentos: {len(self._consulta)} Cobros: {cobros}", 'Detalle documentos'

        if self._tipo == 'depositos':
            return f"Depósitos: {len(self._consulta)}", 'Detalle depósitos'

        if self._tipo == 'cancelados':
            return f"Cancelados: {len(self._consulta)}", 'Detalle cancelados'

        if self._tipo == 'anticipos':
            return f"Anticipos: {len(self._consulta)}", 'Detalle anticipos'

        if self._tipo == 'gastos':
            return f"Gastos: {len(self._consulta)}", 'Detalle gastos'

    def _ordenar_por_financial_operation_id(self, lista):
        return sorted(lista, key=lambda x: x['financial_operation_id'])

    def _procesar_consulta(self, consulta):
        conversion = self._utilerias.convertir_decimal_a_moneda
        nueva_consulta = []

        if not self._tipo:
            for reg in consulta:
                fila = {
                    'folio': reg['Folio'],
                    'official_name': reg['OfficialName'],
                    'forma_pago': reg['PaymentMethodID'],
                    'total': conversion(reg['Total']),
                    'total_paid': conversion(reg['TotalPaid']),
                    'balance': conversion(reg['Balance']),
                    'financial_operation_id':reg['FinancialOperationID']
                }
                nueva_consulta.append(fila)

            return self._ordenar_por_financial_operation_id(nueva_consulta)

        if self._tipo  == 'depositos':

            for reg in consulta:
                fila = {
                    'emisor': reg['Emisor'],
                    'total': conversion(reg['Total'])
                }
                nueva_consulta.append(fila)

        if self._tipo == 'gastos':

            for reg in consulta:
                fila = {
                    'emisor': reg['receptor_gasto'],
                    'total': conversion(reg['monto_gasto'])
                }
                nueva_consulta.append(fila)

        if self._tipo == 'anticipos':

            for reg in consulta:
                fila = {
                    'emisor': reg['emisor_anticipo'],
                    'total': conversion(reg['monto_anticipo'])
                }
                nueva_consulta.append(fila)

        if self._tipo == 'cancelados':
            for reg in consulta:
                fila = {
                    'cancelado':reg['Cancelado'],
                    'folio': reg['Folio'],
                    'sustituye':reg['Sustituye'],
                    'captura':reg['Captura'],
                    'cancela':reg['Cancela'],
                    'total': conversion(reg['Total']),
                    'saldo': conversion(reg['Balance']),
                    'motivo': reg['Motivo'],
                    'comentario':reg['Comentario']
                }
                nueva_consulta.append(fila)

        return nueva_consulta

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.W}),

            'frame_tabla': ('frame_principal', 'Documentos:',
                                  {'row': 0, 'column': 0, 'columnspan':2, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),


        }
        self._ventanas.crear_frames(frames)

    def _crear_columnas_tabla(self):
        if not self._tipo:
            return [
                {'text': 'Folio', 'stretch': True, 'width': 95},
                {'text': 'Cliente', 'stretch': True, 'width': 230},
                {'text': 'FP', 'stretch': True, 'width': 40},
                {'text': 'Total', 'stretch': True, 'width': 95},
                {'text': 'Pagado', 'stretch': True, 'width': 95},
                {'text': 'Saldo', 'stretch': True, 'width': 95},
                {'text': 'ID', 'stretch': True, 'width': 75},

            ]
        elif self._tipo == 'depositos':
            return [
                {'text': 'Emisor', 'stretch': True, 'width': 95},
                {'text': 'Total', 'stretch': True, 'width': 95},
            ]

        elif self._tipo == 'gastos':
            return [
                {'text': 'Receptor', 'stretch': True, 'width': 95},
                {'text': 'Total', 'stretch': True, 'width': 95},
            ]

        elif self._tipo == 'anticipos':
            return [
                {'text': 'Emisor', 'stretch': True, 'width': 95},
                {'text': 'Total', 'stretch': True, 'width': 95},
            ]

        elif self._tipo == 'cancelados':
            return [
                {'text': 'Cancelado', 'stretch': True, 'width': 95},
                {'text': 'Folio', 'stretch': True, 'width': 95},
                {'text': 'Sustituye', 'stretch': True, 'width': 95},
                {'text': 'Captura', 'stretch': True, 'width': 95},
                {'text': 'Cancela', 'stretch': True, 'width': 95},
                {'text': 'Total', 'stretch': True, 'width': 95},
                {'text': 'Saldo', 'stretch': True, 'width': 95},
                {'text': 'Motivo', 'stretch': True, 'width': 95},
                {'text': 'Comentario', 'stretch': True, 'width': 230},
            ]