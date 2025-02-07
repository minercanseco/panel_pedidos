from cayal.ventanas import Ventanas


class SelectorTipoDocumento:
    def __init__(self, master):
        self._master = master
        self._ventanas = Ventanas(self._master)

        self.tipo_documento = -1

        self._cargar_componentes()
        self._rellenar_componentes()
        self._cargar_eventos()

    def _cargar_componentes(self):
        componentes = [
            ('cbx_tipo', 'Tipo:'),
            ('btn_aceptar', 'Aceptar'),
                       ]
        self._ventanas.crear_formulario_simple(componentes)

    def _rellenar_componentes(self):
        tipos = ['Remisión', 'Factura']
        self._ventanas.rellenar_cbx('cbx_tipo', tipos)

    def _cargar_eventos(self):
        eventos = {
            'btn_aceptar': self._seleccionar_documento,
            'btn_cancelar': self._master.destroy,
        }
        self._ventanas.cargar_eventos(eventos)

    def _seleccionar_documento(self):
        seleccion = self._ventanas.obtener_input_componente('cbx_tipo')
        if seleccion == 'Seleccione':
            return

        if seleccion == 'Remisión':
            self.tipo_documento = 1

        if seleccion == 'Factura':
            self.tipo_documento = 0

        self._master.destroy()