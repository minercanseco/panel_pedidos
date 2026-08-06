import tkinter as tk
from cayal.ventanas import Ventanas


class DepositosRecibitos:
    def __init__(self, master, base_de_datos, utilerias, parametros):

        self._master =  master
        self._ventanas = Ventanas(self._master)
        self._base_de_datos = base_de_datos
        self._utilerias =  utilerias
        self._parametros = parametros

        self._user_id = self._parametros.id_usuario
        self._user_name = self._base_de_datos.buscar_nombre_de_usuario(self._user_id)
        self._user_group_id = self._base_de_datos.fetchone(
        'SELECT UserGroupID FROM engUser WHERE UserID = ?', (self._user_id,))

        self._crear_frames()
        self._cargar_componentes()
        self._rellenar_tabla()
        self._cargar_eventos()
        self._actualizar_total_depositos()
        self._ventanas.configurar_ventana_ttkbootstrap('Depósitos recibidos')

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.W}),

            'frame_tabla': ('frame_principal', 'Depósitos',
                                  {'row': 0, 'column': 0, 'columnspan':2, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),


        }
        self._ventanas.crear_frames(frames)

    def _cargar_componentes(self):
        self._ventanas.crear_table_view(
            nombre='tbv_depositos',
            frame='frame_tabla',
            columnas=self._crear_columnas_tabla(),
            filas=15,
            stripecolor=True
                                        )

    def _crear_columnas_tabla(self):
        return [
                {"text": "Fecha", "stretch": False, "width": 95},
                {"text": "Entrega", "stretch": False, "width": 95},
                {"text": "Recibe", "stretch": False, "width": 95},
                {"text": "Total", "stretch": False, "width": 95},
                {"text": "Cheques", "stretch": False, "width": 75},
                {"text": "B.50", "stretch": False, "width": 75},
                {"text": "B.100", "stretch": False, "width": 75},
                {"text": "B.200", "stretch": False, "width": 75},
                {"text": "B.500", "stretch": False, "width": 75},
                {"text": "B.1000", "stretch": False, "width": 75},
                {"text": "Billetes", "stretch": False, "width": 75},
            ]

    def _consulta_depositos_recibidos(self):

        if self._user_group_id in (1,5,22,25,18,20,31):
            sql = """
                SELECT Fecha,Captura,Recibe,Total,
                        Cheques,Billetes50,Billetes100,
                        Billetes200,Billetes500,Billetes1000,Billetes
                FROM zvwDepositosDiariosCayalMenu M INNER JOIN
                    engUser EM ON M.Recibe =EM.UserName
                WHERE M.Fecha = CAST(GETDATE() as date) 
                        AND EM.UserGroupID IN (5,22,18,20,31)
                """

            return self._base_de_datos.fetchall(sql,())

        else:
            return self._base_de_datos.fetchall("""
                    SELECT Fecha,Captura,Recibe,Total,
                            Cheques,Billetes50,Billetes100,
                            Billetes200,Billetes500,Billetes1000,Billetes
                    FROM zvwDepositosDiariosCayalMenu M INNER JOIN
                        engUser EM ON M.Captura =EM.UserName
                    WHERE M.Recibe = ? AND M.Fecha = CAST(GETDATE() as date)
                    """, (self._user_name,))

    def _rellenar_tabla(self):
        self._ventanas.rellenar_table_view('tbv_depositos',
                                         self._crear_columnas_tabla(),
                                         self._procesar_depositos_recibidos(),
                                         )
        self._actualizar_total_depositos()

    def _procesar_depositos_recibidos(self):
        consulta = self._consulta_depositos_recibidos()

        contadores = {
            50: 0,
            100: 0,
            200: 0,
            500: 0,
            1000: 0,
            'total': 0,
            'billetes': 0,
            'cheques': 0
        }

        for deposito in consulta:
            for denominacion, numero in deposito.items():
                if denominacion in ('Billetes50', 'Billetes100', 'Billetes200', 'Billetes500', 'Billetes1000'):
                    valor = int(denominacion[8::])
                    contadores[valor] += numero

                if denominacion == 'Total':
                    contadores['total'] += numero
                    total_moneda = self._utilerias.convertir_decimal_a_moneda(numero)
                    deposito['Total'] = total_moneda

                if denominacion == 'Billetes':
                    contadores['billetes'] += numero

                if denominacion == 'Cheques':
                    contadores['cheques'] += numero

        fila_total = {'Fecha':'',
                      'Entrega':'',
                      'Recibe': 'TOTALES:',
                      'Total':self._utilerias.convertir_decimal_a_moneda(contadores['total']),
                      'Cheques': contadores['cheques'],
                      'Billetes50': contadores[50],
                      'Billetes100':contadores[100],
                      'Billetes200':contadores[200],
                      'Billetes500':contadores[500],
                      'Billetes1000':contadores[1000],
                      'Billetes': contadores['billetes']
                      }

        consulta.append(fila_total)

        return consulta

    def _cargar_eventos(self):
        eventos = {
            'tbv_depositos': (lambda event: self._actualizar_total_depositos(),'seleccion')
        }
        self._ventanas.cargar_eventos(eventos)

    def _actualizar_total_depositos(self):
        filas = self._ventanas.procesar_filas_table_view('tbv_depositos', seleccionadas=True)

        if not filas:
            filas = self._ventanas.procesar_filas_table_view('tbv_depositos')

        if not filas:
            texto = f"Cant. Billetes: 0, Monto: $0.00"
            self._ventanas.actualizar_etiqueta_externa_tabla_view('tbv_depositos', texto)
            return

        total_billetes = 0
        monto_total = 0
        for valores_filas in filas:
            if valores_filas['Recibe'] == 'TOTALES:':
                continue

            total, billetes =  valores_filas['Total'], valores_filas['Billetes']
            total_decimal = self._utilerias.convertir_moneda_a_decimal(total)

            total_billetes += int(billetes)
            monto_total += total_decimal

        monto_total_moneda =  self._utilerias.convertir_decimal_a_moneda(monto_total)

        texto = f"Billetes: {total_billetes}, Monto:{monto_total_moneda}"
        self._ventanas.actualizar_etiqueta_externa_tabla_view('tbv_depositos', texto)