from cayal.ventanas import Ventanas


class EditarPartidaProduccion:
    def __init__(self, master, base_de_datos, utilerias, valores_partida):
        self._master = master
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._ventanas = Ventanas(self._master)

        self.valores_partida = list(valores_partida)
        self.actualizar_cantidad = False

        self._cargar_componentes()
        self._cargar_eventos()
        self._rellenar_componentes()
        self._ventanas.enfocar_componente('tbx_cantidad_nueva')

    def _cargar_componentes(self):
        componentes = [
            ('tbx_cantidad_actual', 'Actual:'),
            ('tbx_cantidad_nueva', 'Nueva:'),
            ('btn_actualizar', 'Actualizar'),
        ]
        self._ventanas.crear_formulario_simple(componentes)

        self._ventanas.agregar_validacion_tbx('tbx_cantidad_nueva', 'cantidad')

    def _cargar_eventos(self):
        eventos = {
            'tbx_cantidad_nueva': lambda event:self._actualizar_partida(),
            'btn_actualizar': self._actualizar_partida,
            'btn_cancelar': self._master.destroy
        }
        self._ventanas.cargar_eventos(eventos)

    def _rellenar_componentes(self):
        cantidad = self.valores_partida[0]
        self._ventanas.insertar_input_componente('tbx_cantidad_actual', cantidad)
        self._ventanas.insertar_input_componente('tbx_cantidad_nueva', cantidad)

        self._ventanas.bloquear_componente('tbx_cantidad_actual')
        self._ventanas.enfocar_componente('tbx_cantidad_nueva')

    def _actualizar_partida(self):
        cantidad = self._ventanas.obtener_input_componente('tbx_cantidad_nueva')
        if not cantidad:
            self._ventanas.mostrar_mensaje('Debe ingresar una cantidad.')
            return
        if not self._utilerias.es_cantidad(cantidad):
            self._ventanas.mostrar_mensaje('Debe ingresar una cantidad válidad.')
            return

        cantidad_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(cantidad)
        clave_unidad = self.valores_partida[9]
        unit = 'KILO' if clave_unidad == 'KGM' else 'PIEZA'

        if not self._utilerias.validar_unidad(cantidad_decimal, unit):
            self._ventanas.mostrar_mensaje('Los productos con unidad no pueden tener cantidades fraccionarias.')
            return

        precio = self.valores_partida[3]
        precio_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(precio)

        total = precio_decimal*cantidad_decimal
        total = f"{total:.2f}"

        self.valores_partida[0] = cantidad_decimal
        self.valores_partida[4] = total
        print(self.valores_partida)
        self.actualizar_cantidad = True

        self._master.destroy()