from datetime import datetime


class ControladorHistorialQuejas:
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
        consulta = self._modelo.obtener_historial_quejas_cliente()

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
                'tbx_fecha': 'Fecha',
                'tbx_documento': 'Documento',
                'tbx_cliente': 'Cliente',
                'tbx_usuario': 'Usuario',
                'tbx_tipo_queja': 'Tipo de Queja',
                'tbx_producto': 'Producto',
                'tbx_responsable': 'Responsable',
                'tbx_area': 'Área',
                'tbx_sub_area': 'Sub Área',
                'txt_comentario': 'Comentario',
                'txt_seguimiento': 'Seguimiento',
                'tbx_queja_id': 'QuejaID',
                'tbx_usuario_id': 'UsuarioID',
            }

            for componente, clave in componentes.items():
                valor = valores_fila.get(clave, '')

                if clave == 'Fecha' and valor:
                    try:
                        valor = datetime.strptime(
                            str(valor),
                            '%Y-%m-%d %H:%M:%S.%f'
                        ).strftime('%Y-%m-%d %H:%M')
                    except Exception:
                        pass

                self._ventanas.insertar_input_componente(
                    componente,
                    '' if valor is None else str(valor)
                )
                self._ventanas.bloquear_componente(componente)

            self._ventanas.cambiar_estado_checkbutton(
                'chk_salio',
                'seleccionado' if valores_fila.get('Salió') == 1 else 'deseleccionado'
            )