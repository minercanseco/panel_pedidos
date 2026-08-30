

from datetime import date


class Controlador:
    def __init__(self, interfaz, modelo, parametros):
        self._interfaz = interfaz
        self._modelo = modelo
        self._parametros = parametros
        self._ventanas = interfaz.ventanas
        self._usuario_id = parametros.id_usuario or 19
        self._user_group_id = self._modelo.buscar_user_group_id(self._usuario_id)
        self._cargar_eventos()
        self._establecer_fechas_iniciales()
        self._cargar_tabla()

    def _cargar_eventos(self):
        self._ventanas.cargar_eventos({
            'den_fecha_inicial': self._cargar_tabla,
            'den_fecha_final': self._cargar_tabla,
            'btn_imprimir': self._imprimir,
            'btn_cancelar': self._cancelar,
        })
        self._ventanas.agregar_hotkeys_forma({'Ctrl+P': self._imprimir})

    def _establecer_fechas_iniciales(self):
        hoy = date.today().strftime('%Y-%m-%d')
        inicial = self._parametros.fecha_inicial or self._parametros.fecha or hoy
        final = self._parametros.fecha_final or self._parametros.fecha or inicial
        self._ventanas.insertar_input_componente('den_fecha_inicial', inicial)
        self._ventanas.insertar_input_componente('den_fecha_final', final)

    def _obtener_rango(self):
        inicial = self._modelo.normalizar_fecha(
            self._ventanas.obtener_input_componente('den_fecha_inicial'))
        final = self._modelo.normalizar_fecha(
            self._ventanas.obtener_input_componente('den_fecha_final'))
        if inicial > final:
            raise ValueError('La fecha inicial no puede ser posterior a la fecha final.')
        return inicial, final

    def _cargar_tabla(self, event=None):
        try:
            inicial, final = self._obtener_rango()
            datos = self._modelo.buscar_complementos(
                inicial, final, self._usuario_id, self._user_group_id)
            self._ventanas.rellenar_treeview(
                'tvw_complementos', self._interfaz.columnas, datos, 18)
            cantidad = len(datos)
            self._ventanas.insertar_input_componente(
                'lbl_estado', f'{cantidad} complemento' + ('' if cantidad == 1 else 's'))
        except Exception as error:
            self._ventanas.mostrar_mensaje(f'No fue posible consultar los complementos:\n{error}')

    def _imprimir(self, event=None):
        try:
            inicial, final = self._obtener_rango()
            datos = self._modelo.buscar_detalle_impresion(
                inicial, final, self._usuario_id, self._user_group_id)
            if not datos:
                self._ventanas.mostrar_mensaje(
                    'No hay complementos timbrados para imprimir en el rango seleccionado.', tipo='info')
                return
            archivo = self._modelo.generar_documento(datos, inicial, final)
            self._modelo.imprimir_documento(archivo)
        except Exception as error:
            self._ventanas.mostrar_mensaje(f'No fue posible generar la impresión:\n{error}')

    def _cancelar(self, event=None):
        self._interfaz._master.destroy()
