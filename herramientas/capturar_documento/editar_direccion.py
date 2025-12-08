from cayal.ventanas import Ventanas


class EditarDireccionDocumento:
    def __init__(self, master, cliente, documento, modelo):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self.cliente = cliente
        self.documento = documento
        self._modelo = modelo
        self._direcciones_cliente = []

        self._cargar_componentes()
        self._rellenar_componentes()
        self._cargar_eventos()

    def _cargar_componentes(self):
        componentes = [
            ('cbx_direcciones', 'Direcciones:'),
            ('btn_actualizar', 'Actualizar'),
        ]
        self._ventanas.crear_formulario_simple(componentes)

    def _rellenar_componentes(self):
        if not self.cliente.addresses_details:
            direcciones = self._modelo.settear_info_direcciones_cliente(self.cliente.business_entity_id)
            nombres = [direccion['AddressName'] for direccion in direcciones]
            self._direcciones_cliente = direcciones
        else:
            nombres = [direccion['AddressName'] for direccion in self.cliente.addresses_details]

        self._ventanas.rellenar_cbx('cbx_direcciones', nombres)

    def _cargar_eventos(self):
        eventos = {
            'btn_cancelar':self._master.destroy,
            'btn_actualizar': self._actualizar_direccion
        }
        self._ventanas.cargar_eventos(eventos)

    def _actualizar_direccion(self):

        address_name = self._ventanas.obtener_input_componente('cbx_direcciones')
        if address_name == 'Seleccione':
            self._ventanas.mostrar_mensaje('Debe seleccionar una direccion válida.')
            return

        consulta = [reg for reg in self._direcciones_cliente
                    if reg['AddressName'] == address_name]
        if consulta:
            address_detail = consulta[0]
            self.documento.address_details = address_detail

            address_detail_id = address_detail['AddressDetailID']
            self.documento.address_detail_id = address_detail_id


        self._master.destroy()
