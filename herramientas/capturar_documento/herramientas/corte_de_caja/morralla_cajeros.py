import tkinter as tk
from cayal.ventanas import Ventanas

from .contador_divisa import ContadorBilletes


class MorrallaCajeros:
    def __init__(self, master, parametros, base_de_datos, utilerias):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._parametros = parametros
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias

        self._procesando_denominacion = False

        self.monedas_capturadas = {
            1: {'cantidad': 0, 'monto': 0},
            2: {'cantidad': 0, 'monto': 0},
            20: {'cantidad': 0, 'monto': 0},
            50: {'cantidad': 0, 'monto': 0},
            5: {'cantidad': 0, 'monto': 0},
            10: {'cantidad': 0, 'monto': 0}
        }

        self.monto_total_monedas = 0

        self._crear_frames()
        self._crear_componentes()
        self._crear_barra_denominaciones_1()
        self._crear_barra_denominaciones_2()
        self._cargar_eventos()

        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Contador monedas')

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.W}),

            'frame_info': ('frame_principal', 'Acciones',
                           {'row': 1, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_deposito': ('frame_principal', 'Total',
                               {'row': 0, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),
            'frame_monto': ('frame_deposito', None,
                            {'row': 0, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.W}),

            'frame_botones': ('frame_info', None,
                              {'row': 3, 'column': 1, 'pady': 5, 'sticky': tk.NSEW}),
            'frame_denominaciones': ('frame_principal', 'Denominaciones',
                                     {'row': 3, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),
            'frame_denominaciones1': ('frame_denominaciones', None,
                                      {'row': 0, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),
            'frame_denominaciones2': ('frame_denominaciones', None,
                                      {'row': 1, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),
        }
        self._ventanas.crear_frames(frames)

    def _crear_componentes(self):
        componentes = {
            'lbl_total_texto': ('frame_monto',
                                {'width': 10, 'text': 'Monto:',
                                 'font': ('Consolas', 12, 'bold')},
                                {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                None),

            'lbl_total': ('frame_monto',
                          {'width': 10, 'text': '$0.00',
                           'font': ('Consolas', 18, 'bold')},
                          {'row': 0, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                          None),

            'lbl_monedas_texto': ('frame_monto',
                                   {'width': 10, 'text': 'Monedas:',
                                    'font': ('Consolas', 12, 'bold')},
                                   {'row': 0, 'column': 2, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                   None),

            'lbl_monedas': ('frame_monto',
                             {'width': 10, 'text': '0',
                              'font': ('Consolas', 18, 'bold')},
                             {'row': 0, 'column': 3, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                             None),

            'btn_guardar': ('frame_botones', 'Primary', 'Guardar', None),
            'btn_cancelar': ('frame_botones', 'Danger', 'Cancelar', None),

        }
        self._ventanas.crear_componentes(componentes)

    def _cargar_eventos(self):
        eventos = {
            'btn_guardar': self._guardar_monedas_corte,
            'btn_cancelar': self._master.destroy,
        }
        self._ventanas.cargar_eventos(eventos)

    def _crear_barra_denominaciones_1(self):
        self.barra_herramientas = [
            {'nombre_icono': 'Moneda20.ico', 'etiqueta': '', 'nombre': 'denominacion_20',
             'hotkey': '', 'comando': self._denominacion_20},
            {'nombre_icono': 'Moneda50.ico', 'etiqueta': '', 'nombre': 'denominacion_50',
             'hotkey': '', 'comando': self._denominacion_50},
            {'nombre_icono': 'Moneda1.ico', 'etiqueta': '', 'nombre': 'denominacion_1',
             'hotkey': '', 'comando': self._denominacion_1},

        ]

        self.elementos_barra_herramientas = self._ventanas.crear_barra_herramientas(self.barra_herramientas,
                                                                                    'frame_denominaciones1')
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]

    def _crear_barra_denominaciones_2(self):
        self.barra_herramientas2 = [
            {'nombre_icono': 'Moneda2.ico', 'etiqueta': '', 'nombre': 'denominacion_2',
             'hotkey': '', 'comando': self._denominacion_2},
            {'nombre_icono': 'Moneda5.ico', 'etiqueta': '', 'nombre': 'denominacion_5',
             'hotkey': '', 'comando': self._denominacion_5},
            {'nombre_icono': 'Moneda10.ico', 'etiqueta': '', 'nombre': 'denominacion_10',
             'hotkey': '', 'comando': self._denominacion_10},
        ]

        self.elementos_barra_herramientas2 = self._ventanas.crear_barra_herramientas(self.barra_herramientas2,
                                                                                     'frame_denominaciones2')
        self.etiquetas_barra_herramientas2 = self.elementos_barra_herramientas2[2]
        self.hotkeys_barra_herramientas2 = self.elementos_barra_herramientas2[1]

    def _llamar_contador_monedas(self, denominacion):

        if not self._procesando_denominacion:
            try:
                self._procesando_denominacion = True
                ventana = self._ventanas.crear_popup_ttkbootstrap(self._master, 'Valorizar')
                instancia = ContadorBilletes(ventana, self._utilerias, denominacion)
                ventana.wait_window()

                if denominacion in(20,50):
                    nuevo_monto = instancia.monto / 100
                    instancia.monto = nuevo_monto

                self._actualizar_etiqueta_denominacion(denominacion, instancia.monto, instancia.cantidad)
                self._actualizar_deposito_acumulado(denominacion, instancia.monto, instancia.cantidad)
            finally:
                self._procesando_denominacion = False

    def _actualizar_etiqueta_denominacion(self, denominacion, monto, cantidad):
        denominaciones = {
            20: self.etiquetas_barra_herramientas[0],
            50: self.etiquetas_barra_herramientas[1],
            1: self.etiquetas_barra_herramientas[2],
            2: self.etiquetas_barra_herramientas2[0],
            5: self.etiquetas_barra_herramientas2[1],
            10: self.etiquetas_barra_herramientas2[2]
        }
        etiqueta = denominaciones[denominacion]
        cantidad = int(cantidad)

        if cantidad > 0:
            monto = f"{monto:.2f}"
            texto = f"{cantidad}={monto}"

            etiqueta.config(text=texto, font=('Consolas', 12, 'bold'))

        if cantidad < 0:
            etiqueta.config(text='')

    def _actualizar_deposito_acumulado(self, denominacion, monto, cantidad):
        self.monedas_capturadas[denominacion]['monto'] = monto
        self.monedas_capturadas[denominacion]['cantidad'] = cantidad

        total_monedas = sum(moneda['cantidad'] for moneda in self.monedas_capturadas.values())
        total_monto = sum(moneda['monto'] for moneda in self.monedas_capturadas.values())

        self._monto_total_deposito = total_monto
        self._actualizar_etiquetas_totales(total_monedas, total_monto)

    def _actualizar_etiquetas_totales(self, total_billetes, total_monto):

        total_monto_moneda = self._utilerias.convertir_decimal_a_moneda(total_monto)
        self._ventanas.insertar_input_componente('lbl_total', total_monto_moneda)

        self._ventanas.insertar_input_componente('lbl_monedas', int(total_billetes))

    def _denominacion_20(self):
        self._llamar_contador_monedas(20)

    def _denominacion_50(self):
        self._llamar_contador_monedas(50)

    def _denominacion_1(self):
        self._llamar_contador_monedas(1)

    def _denominacion_2(self):
        self._llamar_contador_monedas(2)

    def _denominacion_5(self):
        self._llamar_contador_monedas(5)

    def _denominacion_10(self):
        self._llamar_contador_monedas(10)

    def _guardar_monedas_corte(self):
        if not self._validar_inputs_deposito():
            return

        # obten la cantidad de las monedas que componen el deposito
        b_cantidad = {20: 0,
                      50: 0,
                      1: 0,
                      2: 0,
                      5: 0,
                      10: 0
                      }

        for denominacion, valores in self.monedas_capturadas.items():
            cantidad_monedas = valores['cantidad']
            monto = valores['monto']
            if denominacion in b_cantidad:
                b_cantidad[denominacion] = cantidad_monedas
                self.monto_total_monedas += monto

        self._master.destroy()

    def _validar_inputs_deposito(self):
        if (self._monto_total_deposito + self.monto_total_monedas) <= 0:
            self._ventanas.mostrar_mensaje('El valor del depósito no puede ser zero.')
            return

        return True
