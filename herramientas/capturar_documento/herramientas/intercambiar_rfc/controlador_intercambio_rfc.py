class ControladorIntercambioRFC:
    TIPOS_CLIENTE = {
        0: 'Cliente solo remisión (legacy tipo 0)',
        1: 'Cliente solo remisión (legacy tipo 1)',
        2: 'Cliente factura y remisión',
    }

    def __init__(self, interfaz, modelo):
        self._interfaz = interfaz
        self._modelo = modelo
        self._ventanas = interfaz.ventanas
        self._master = interfaz._master

        self._cliente = None
        self._formas_pago = []
        self._metodos_pago = []
        self._usos_cfdi = []

        self._cargar_eventos()
        self._rellenar_componentes()
        self._interfaz.bloquear_campos_informativos()

    def _cargar_eventos(self):
        self._ventanas.cargar_eventos({
            'btn_aceptar': self._aceptar,
            'btn_cancelar': self._cerrar,
        })

    def _rellenar_componentes(self):
        consulta = self._modelo.obtener_info_cliente(
            self._modelo.business_entity_id
        )

        if not consulta:
            self._ventanas.mostrar_mensaje(
                'No se encontró la información del cliente.',
                tipo='error',
            )
            self._ventanas.bloquear_componente('btn_aceptar')
            return

        self._cliente = consulta[0]
        tipo_id = int(self._cliente.get('CayalCustomerTypeID', 0) or 0)

        valores_cliente = {
            'tbx_cliente': self._cliente.get('OfficialName') or '',
            'tbx_tipo': self.TIPOS_CLIENTE.get(
                tipo_id,
                f'Tipo de cliente desconocido ({tipo_id})',
            ),
            'tbx_rfc': self._cliente.get('OfficialNumber') or '',
            'tbx_rfc_respaldado': (
                self._cliente.get('OfficialNumberBackup') or ''
            ),
            'tbx_regimen': self._cliente.get('CompanyTypeName') or '',
            'tbx_regimen_respaldado': (
                self._cliente.get('CompanyTypeNameBackup') or ''
            ),
        }

        for componente, valor in valores_cliente.items():
            self._ventanas.insertar_input_componente(componente, valor)

        self._rellenar_catalogos(self._cliente)

    def _rellenar_catalogos(self, cliente):
        self._formas_pago = self._modelo.obtener_formas_pago()
        self._metodos_pago = self._modelo.obtener_metodos_pago()
        self._usos_cfdi = self._modelo.obtener_usos_cfdi()

        catalogos = {
            'cbx_forma_pago': (
                self._formas_pago,
                cliente.get('FormaPago') or '',
            ),
            'cbx_metodo_pago': (
                self._metodos_pago,
                cliente.get('MetodoPago') or '',
            ),
            'cbx_uso_cfdi': (
                self._usos_cfdi,
                cliente.get('ReceptorUsoCFDI') or '',
            ),
        }

        for componente, (consulta, clave_seleccionada) in catalogos.items():
            valores = [registro['Value'] for registro in consulta]
            self._ventanas.rellenar_cbx(componente, valores)
            self._seleccionar_combo_por_clave(
                componente,
                consulta,
                clave_seleccionada,
            )

    def _seleccionar_combo_por_clave(self, componente, consulta, clave):
        valor = next(
            (
                registro['Value']
                for registro in consulta
                if str(registro.get('Clave', '')) == str(clave)
            ),
            None,
        )

        if valor is not None:
            self._ventanas.insertar_input_componente(componente, valor)

    def _obtener_clave_combo(self, componente, consulta):
        valor = self._ventanas.obtener_input_componente(componente)
        registro = next(
            (item for item in consulta if item.get('Value') == valor),
            None,
        )
        return registro.get('Clave') if registro else None

    def _aceptar(self):
        if not self._cliente:
            return

        forma_pago = self._obtener_clave_combo(
            'cbx_forma_pago', self._formas_pago
        )
        metodo_pago = self._obtener_clave_combo(
            'cbx_metodo_pago', self._metodos_pago
        )
        uso_cfdi = self._obtener_clave_combo(
            'cbx_uso_cfdi', self._usos_cfdi
        )

        if not all((forma_pago, metodo_pago, uso_cfdi)):
            self._ventanas.mostrar_mensaje(
                'Seleccione forma de pago, método de pago y uso de CFDI.',
                tipo='error',
            )
            return

        rfc_actual = self._cliente.get('OfficialNumber') or ''
        if rfc_actual == self._modelo.RFC_GENERICO:
            accion = 'restaurar el RFC y el régimen fiscal respaldados'
        else:
            accion = 'respaldar los datos fiscales y usar el RFC genérico'

        if not self._ventanas.mostrar_mensaje_pregunta(
            f'¿Desea {accion} para este cliente?'
        ):
            return

        try:
            resultado = self._modelo.intercambiar_rfc(
                forma_pago=forma_pago,
                metodo_pago=metodo_pago,
                uso_cfdi=uso_cfdi,
            )
        except Exception as error:
            self._ventanas.mostrar_mensaje(
                f'No fue posible intercambiar los datos fiscales: {error}',
                tipo='error',
            )
            return

        if not resultado.get('ok'):
            self._ventanas.mostrar_mensaje(
                resultado.get('mensaje', 'No se realizó el intercambio.'),
                tipo='error',
            )
            return

        self._ventanas.mostrar_mensaje(
            resultado['mensaje'],
            tipo='info',
        )
        self._cerrar()

    def _cerrar(self):
        self._master.destroy()
