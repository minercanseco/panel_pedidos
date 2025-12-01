from cayal.ventanas import Ventanas

class NombreDireccion:
    def __init__(self, master):
        self.nombre_direccion = None

        self._master = master
        self._ventanas = Ventanas(self._master)
        self._cargar_componentes()
        self._cargar_eventos()
        self._ventanas.enfocar_componente('tbx_nombre')

    def _cargar_componentes(self):
        componentes = [
            ('tbx_nombre','Nombre:'),
            ('btn_aceptar', 'Aceptar')
        ]
        self._ventanas.crear_formulario_simple(componentes)

    def _cargar_eventos(self):
        eventos = {
            'btn_aceptar':self._guardar_nombre_direccion,
            'btn_cancelar':self._master.destroy,
            'tbx_nombre':lambda event:self._guardar_nombre_direccion()
        }
        self._ventanas.cargar_eventos(eventos)

    def _guardar_nombre_direccion(self):
        nombre = self._ventanas.obtener_input_componente('tbx_nombre')
        if not nombre:
            self._ventanas.mostrar_mensaje('Debe introducir un nombre para la nueva dirección.')
            return

        if len(nombre) < 3:
            self._ventanas.mostrar_mensaje('Debe abundar en el nombre para la nueva dirección.')
            return
        if len(nombre) > 20:
            self._ventanas.mostrar_mensaje('Debe elegir un nombre cortorpara la nueva dirección.')
            return

        self.nombre_direccion = nombre.strip()
        self._master.destroy()