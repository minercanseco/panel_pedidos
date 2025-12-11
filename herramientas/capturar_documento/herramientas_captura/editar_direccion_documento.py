from cayal.ventanas import Ventanas


class EditarDireccionDocumento:
    def __init__(self, master, modelo, interfaz):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._modelo = modelo
        self._interfaz = interfaz
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
        if not self._modelo.cliente.addresses_details:
            direcciones = self._modelo.settear_info_direcciones_cliente(self._modelo.cliente.business_entity_id)
            nombres = [direccion['AddressName'] for direccion in direcciones]
            self._direcciones_cliente = direcciones
        else:
            nombres = [direccion['AddressName'] for direccion in self._modelo.cliente.addresses_details]

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
            self._modelo.documento.address_details = address_detail

            address_detail_id = address_detail['AddressDetailID']
            self._modelo.documento.address_detail_id = address_detail_id

        self._cargar_nombre_cliente()
        self._cargar_direccion_cliente()

        self._master.destroy()

    def _cargar_nombre_cliente(self):
        nombre = self._modelo.cliente.official_name
        nombre_comercial = self._modelo.cliente.commercial_name
        sucursal = self._modelo.documento.depot_name
        nombre_direccion = self._modelo.documento.address_name

        sucursal = f'({nombre_direccion})' if not sucursal else f'({sucursal})'
        nombre_comercial = '' if not nombre_comercial else f'-{nombre_comercial}-'

        nombre_cliente = f'{nombre} {nombre_comercial} {sucursal}'
        self._interfaz.ventanas.insertar_input_componente('tbx_cliente', nombre_cliente)
        self._interfaz.ventanas.bloquear_componente('tbx_cliente')

    def _cargar_direccion_cliente(self):
        datos_direccion = self._modelo.documento.address_details

        self._modelo.documento.address_detail_id = datos_direccion['AddressDetailID']
        if self._modelo.module_id == 1687: # modulo de pedidos
            self._modelo.documento.order_parameters['AddressDetailID'] = datos_direccion['AddressDetailID']

        calle = datos_direccion.get('Street', '')
        numero = datos_direccion.get('ExtNumber', '')
        colonia = datos_direccion.get('City', '')
        cp = datos_direccion.get('ZipCode', '')
        municipio = datos_direccion.get('Municipality', '')
        estado = datos_direccion.get('StateProvince', '')
        comentario = datos_direccion.get('Comments', '')

        texto_direccion = f'{calle} NUM.{numero}, COL.{colonia}, MPIO.{municipio}, EDO.{estado}, C.P.{cp}'
        texto_direccion = texto_direccion.upper()

        self._interfaz.ventanas.insertar_input_componente('tbx_direccion', texto_direccion)
        self._interfaz.ventanas.bloquear_componente('tbx_direccion')

        self._interfaz.ventanas.insertar_input_componente('tbx_comentario', comentario)
        self._interfaz.ventanas.bloquear_componente('tbx_comentario')
