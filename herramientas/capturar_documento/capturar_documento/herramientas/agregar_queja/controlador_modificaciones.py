class ControladorModificacionesQuejas:
    def __init__(self, interfaz, modelo):
        self._interfaz = interfaz
        self._modelo = modelo
        self._ventanas = self._interfaz.ventanas

        self._rellenar_tabla()
        self._cargar_eventos()

    def _cargar_eventos(self):
        eventos = {
            'tvw_historial': ( lambda event:self._rellenar_formulario(), 'seleccion')
        }
        self._ventanas.cargar_eventos(eventos)


    def _rellenar_tabla(self):
        consulta = self._modelo.obtener_modificaciones_quejas()

        self._ventanas.rellenar_treeview(
            'tvw_historial',
            self._interfaz.crear_columnas_tabla(),
            consulta
        )

    def _rellenar_formulario(self):
        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_historial'):
            return

        filas = self._ventanas.obtener_seleccion_filas_treeview('tvw_historial')

        for fila in filas:
            valores_fila = self._ventanas.procesar_fila_treeview('tvw_historial', fila)

            componentes = {
                'txt_valor_anterior': 'ValorAnterior',
                'txt_valor_nuevo': 'ValorNuevo',

            }

            for componente, clave in componentes.items():
                valor = valores_fila.get(clave, '')


                self._ventanas.insertar_input_componente(
                    componente,
                    '' if valor is None else str(valor)
                )
                self._ventanas.bloquear_componente(componente)

