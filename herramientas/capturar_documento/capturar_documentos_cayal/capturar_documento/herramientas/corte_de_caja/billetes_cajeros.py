import tkinter as tk
from cayal.ventanas import Ventanas

from .agregar_cheque import AgregarCheque
from .contador_divisa import ContadorBilletes


class BilletesCajeros:
    def __init__(self, master, parametros, base_de_datos, utilerias):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._parametros = parametros
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias

        self._procesando_denominacion = False

        self.billetes_capturados = {
            20: {'cantidad': 0, 'monto': 0},
            50: {'cantidad': 0, 'monto': 0},
            100: {'cantidad': 0, 'monto': 0},
            200: {'cantidad': 0, 'monto': 0},
            500: {'cantidad': 0, 'monto': 0},
            1000: {'cantidad': 0, 'monto': 0}
        }

        self.monto_total_billetes = 0
        self.monto_total_cheques = 0
        self.cheques_capturados = []

        self._crear_frames()
        self._crear_componentes()
        self._crear_barra_denominaciones_1()
        self._crear_barra_denominaciones_2()
        self._cargar_eventos()

        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Contador billetes')

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

            'lbl_billetes_texto': ('frame_monto',
                                   {'width': 10, 'text': 'Billetes:',
                                    'font': ('Consolas', 12, 'bold')},
                                   {'row': 0, 'column': 2, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                   None),

            'lbl_billetes': ('frame_monto',
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
            'btn_guardar': self._guardar_billetes_corte,
            'btn_cancelar': self._master.destroy,
        }
        self._ventanas.cargar_eventos(eventos)

    def _crear_barra_denominaciones_1(self):
        self.barra_herramientas = [
            {'nombre_icono': 'Billete20.ico', 'etiqueta': '', 'nombre': 'denominacion_20',
             'hotkey': '', 'comando': self._denominacion_20},
            {'nombre_icono': 'Billete50.ico', 'etiqueta': '', 'nombre': 'denominacion_50',
             'hotkey': '', 'comando': self._denominacion_50},
            {'nombre_icono': 'Billete100.ico', 'etiqueta': '', 'nombre': 'denominacion_100',
             'hotkey': '', 'comando': self._denominacion_100},

        ]

        self.elementos_barra_herramientas = self._ventanas.crear_barra_herramientas(self.barra_herramientas,
                                                                                    'frame_denominaciones1')
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]

    def _crear_barra_denominaciones_2(self):
        self.barra_herramientas2 = [
            {'nombre_icono': 'Billete200.ico', 'etiqueta': '', 'nombre': 'denominacion_200',
             'hotkey': '', 'comando': self._denominacion_200},
            {'nombre_icono': 'Billete500.ico', 'etiqueta': '', 'nombre': 'denominacion_500',
             'hotkey': '', 'comando': self._denominacion_500},
            {'nombre_icono': 'Billete1000.ico', 'etiqueta': '', 'nombre': 'denominacion_1000',
             'hotkey': '', 'comando': self._denominacion_1000},
        ]

        self.elementos_barra_herramientas2 = self._ventanas.crear_barra_herramientas(self.barra_herramientas2,
                                                                                     'frame_denominaciones2')
        self.etiquetas_barra_herramientas2 = self.elementos_barra_herramientas2[2]
        self.hotkeys_barra_herramientas2 = self.elementos_barra_herramientas2[1]

    def _llamar_contador_billetes(self, denominacion):

        if not self._procesando_denominacion:
            try:
                self._procesando_denominacion = True
                ventana = self._ventanas.crear_popup_ttkbootstrap(self._master, 'Valorizar')
                instancia = ContadorBilletes(ventana, self._utilerias, denominacion)
                ventana.wait_window()

                self._actualizar_etiqueta_denominacion(denominacion, instancia.monto, instancia.cantidad)
                self._actualizar_deposito_acumulado(denominacion, instancia.monto, instancia.cantidad)
            finally:
                self._procesando_denominacion = False

    def _actualizar_etiqueta_denominacion(self, denominacion, monto, cantidad):
        denominaciones = {
            20: self.etiquetas_barra_herramientas[0],
            50: self.etiquetas_barra_herramientas[1],
            100: self.etiquetas_barra_herramientas[2],
            200: self.etiquetas_barra_herramientas2[0],
            500: self.etiquetas_barra_herramientas2[1],
            1000: self.etiquetas_barra_herramientas2[2]
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
        self.billetes_capturados[denominacion]['monto'] = monto
        self.billetes_capturados[denominacion]['cantidad'] = cantidad

        total_billetes = sum(billete['cantidad'] for billete in self.billetes_capturados.values())
        total_monto = sum(billete['monto'] for billete in self.billetes_capturados.values())

        self._monto_total_deposito = total_monto
        self._actualizar_etiquetas_totales(total_billetes, total_monto)

    def _actualizar_etiquetas_totales(self, total_billetes, total_monto):

        total_monto_moneda = self._utilerias.convertir_decimal_a_moneda(total_monto)
        self._ventanas.insertar_input_componente('lbl_total', total_monto_moneda)

        self._ventanas.insertar_input_componente('lbl_billetes', int(total_billetes))

    def _denominacion_20(self):
        self._llamar_contador_billetes(20)

    def _denominacion_50(self):
        self._llamar_contador_billetes(50)

    def _denominacion_100(self):
        self._llamar_contador_billetes(100)

    def _denominacion_200(self):
        self._llamar_contador_billetes(200)

    def _denominacion_500(self):
        self._llamar_contador_billetes(500)

    def _denominacion_1000(self):
        self._llamar_contador_billetes(1000)

    def _denominacion_cheque(self):
        ventana = self._ventanas.crear_popup_ttkbootstrap(titulo='Agregar cheque')
        instancia = AgregarCheque(ventana, self._parametros, self._base_de_datos, self._utilerias,
                                  self.cheques_capturados)
        ventana.wait_window()

        self.cheques_capturados = instancia.cheques_capturados
        self._procesar_cheques()

    def _procesar_cheques(self):
        etiqueta_cheques = self.etiquetas_barra_herramientas[0]

        cantidad_cheques = len(self.cheques_capturados)
        montos_cheques = [self._utilerias.redondear_valor_cantidad_a_decimal(cheque['Total'])
                          for cheque in self.cheques_capturados]
        total_cheques = 0
        if montos_cheques:
            total_cheques = sum(montos_cheques)
            self.monto_total_cheques = total_cheques

        if cantidad_cheques > 0:
            total_cheques = f"{total_cheques:.2f}"
            texto = f"{cantidad_cheques}={total_cheques}"

            etiqueta_cheques.config(text=texto, font=('Consolas', 12, 'bold'))

        if cantidad_cheques < 0:
            etiqueta_cheques.config(text='')
            self.monto_total_cheques = 0

    def _guardar_billetes_corte(self):
        if not self._validar_inputs_deposito():
            return

        # obten la cantidad de los billetes que componen el deposito
        b_cantidad = {20: 0, 50: 0, 100: 0, 200: 0, 500: 0, 1000: 0}

        for denominacion, valores in self.billetes_capturados.items():
            cantidad_billetes = valores['cantidad']
            monto = valores['monto']
            if denominacion in b_cantidad:
                b_cantidad[denominacion] = cantidad_billetes
                self.monto_total_billetes += monto

        self._master.destroy()

    def _validar_inputs_deposito(self):
        if (self._monto_total_deposito + self.monto_total_cheques) <= 0:
            self._ventanas.mostrar_mensaje('El valor del depósito no puede ser zero.')
            return

        return True
