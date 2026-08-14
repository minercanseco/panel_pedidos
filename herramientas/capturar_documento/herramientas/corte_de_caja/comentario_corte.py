from cayal.ventanas import Ventanas

class ComentarioCorte:
    def __init__(self, master, utilerias, comentarios, user_group_id):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._utilerias = utilerias

        self._user_group_id = user_group_id
        # comentarios = {'comentario':None, 'comentario_cobranza': None}
        self.comentarios = comentarios
        self.actualizar_comentario = False

        self._crear_componentes()
        self._cargar_eventos()
        self._rellenar_componentes()

    def _crear_componentes(self):
        componentes = [
            ('txt_cajero', 'Cajero:'),
            ('txt_cobranza', 'Cobranza:'),
            ('btn_guardar', 'Guardar')
        ]
        self._ventanas.crear_formulario_simple(componentes)

        if self._user_group_id != 6:
            self._ventanas.bloquear_componente('txt_cobranza')

    def _cargar_eventos(self):
        eventos = {
            'btn_guardar': self._guardar_comentarios,
            'btn_cancelar':self._master.destroy
        }
        self._ventanas.cargar_eventos(eventos)

    def _procesar_comentario(self, comentario):
        comentario = comentario.strip()
        if not comentario:
            return comentario

        comentario = comentario.upper()
        return comentario

    def _guardar_comentarios(self):
        comentario_cajero = self._ventanas.obtener_input_componente('txt_cajero')
        comentario_cobranza = self._ventanas.obtener_input_componente('txt_cobranza')

        if not comentario_cajero and not comentario_cobranza:
            self._master.destroy()
            return

        if comentario_cajero:
            comentario_cajero = self._procesar_comentario(comentario_cajero)

        if comentario_cobranza:
            comentario_cobranza = self._procesar_comentario(comentario_cobranza)

        # comentarios = {'comentario':None, 'comentario_cobranza': None}
        self.comentarios['comentario'] = comentario_cajero if comentario_cajero else None
        self.comentarios['comentario_cobranza'] = comentario_cobranza if comentario_cobranza else None

        self.actualizar_comentario = True
        self._master.destroy()

    def _rellenar_componentes(self):
        if self.comentarios:
            self._ventanas.insertar_input_componente('txt_cajero', self.comentarios['comentario'])
            self._ventanas.insertar_input_componente('txt_cobranza', self.comentarios['comentario_cobranza'])