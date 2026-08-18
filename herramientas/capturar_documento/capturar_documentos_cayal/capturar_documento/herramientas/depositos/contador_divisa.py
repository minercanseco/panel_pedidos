import tkinter as tk
from cayal.ventanas import Ventanas

class ContadorBilletes:
    def __init__(self, master, utilerias, denominacion):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._utilerias = utilerias

        self._denominacion = self._utilerias.redondear_valor_cantidad_a_decimal(denominacion)
        self.monto = 0
        self.cantidad = 0

        self._cargar_componentes()
        self._cargar_eventos()
        self._ventanas.configurar_ventana_ttkbootstrap()
        self._ventanas.enfocar_componente('tbx_cantidad')

    def _cargar_componentes(self):
        componentes = [
            ('tbx_cantidad', 'Cantidad'),
            ('btn_agregar', 'Agregar')
        ]
        self._ventanas.crear_formulario_simple(componentes)

        frame_adicional = {
            'frame_chk': ('frame_componentes', 'Acciones:',
                          {'row': 3, 'column': 1, 'pady': 5, 'padx': 5, 'sticky': tk.W}
                          )
        }
        self._ventanas.crear_frames(frame_adicional)

        componente_adicional = {
            'chk_monto': ('frame_chk',
                              {'row': 0, 'column': 0, 'pady': 5, 'padx': 5, 'sticky': tk.W},
                              'Monto', None),
        }
        self._ventanas.crear_componentes(componente_adicional)

        self._ventanas.agregar_validacion_tbx('tbx_cantidad', 'cantidad')

    def _cargar_eventos(self):
        eventos = {
            'btn_cancelar': self._cancelar_operacion,
            'btn_agregar': self._valorizar_cantidad,
            'tbx_cantidad': lambda event:self._valorizar_cantidad(event)
        }
        self._ventanas.cargar_eventos(eventos)

    def _valorizar_cantidad(self, event = None):
        # Validar entrada
        if not self._validar_valor():
            return

        monto = self._ventanas.obtener_input_componente('tbx_cantidad')
        monto = self._utilerias.redondear_valor_cantidad_a_decimal(monto)

        chk_monto = self._ventanas.obtener_input_componente('chk_monto')

        # Verificar valorización por monto
        if chk_monto == 1:

            # Actualizar valores de instancia
            self.cantidad = monto / self._denominacion
            self.monto = monto

        else:
            # Valorización normal
            self.monto = int(monto) * self._denominacion
            self.cantidad = monto

        # Cerrar ventana
        self._master.destroy()

    def _validar_valor(self):
        valor = self._ventanas.obtener_input_componente('tbx_cantidad')

        if not valor:  # Validar que monto sea válido
            self._ventanas.mostrar_mensaje("Debe ingresar una cantidad válida.")
            return

        if not self._utilerias.es_cantidad(valor):
            self._ventanas.mostrar_mensaje('El valor no es válido.')
            return

        valor_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(valor)

        if valor_decimal <= 0:
            self._ventanas.mostrar_mensaje('El valor no puede ser cero o menor que cero')
            return

        chk_monto = self._ventanas.obtener_input_componente('chk_monto')

        # Verificar valorización por monto
        if chk_monto == 1:
            if valor_decimal < self._denominacion:
                self._ventanas.mostrar_mensaje(
                    f'La cantidad no puede ser menor a la denominación {self._denominacion}.')
                return

            if valor_decimal % self._denominacion != 0:
                print(valor_decimal / self._denominacion)
                self._ventanas.mostrar_mensaje(
                    f'La cantidad no puede ser fraccionaria.')
                return


        return True

    def _cancelar_operacion(self):
        self.cantidad = 0
        self.monto = 0
        self._master.destroy()
