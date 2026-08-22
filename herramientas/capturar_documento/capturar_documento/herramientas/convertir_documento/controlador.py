class ControladorConvertirDocumento:
    OPCIONES = ('Nota entregada', 'Pedido mayoreo')

    def __init__(self, interfaz, modelo):
        self._interfaz = interfaz
        self._modelo = modelo
        self._ventanas = interfaz.ventanas
        self._master = interfaz._master
        self._documento = None

        self._cargar_eventos()
        self._cargar_documento()

    def _cargar_eventos(self):
        self._ventanas.cargar_eventos({
            'btn_guardar': self._guardar,
            'btn_cancelar': self._cerrar,
        })

    def _cargar_documento(self):
        try:
            self._documento, error = self._modelo.validar_documento()
        except Exception as error_consulta:
            self._documento = None
            self._ventanas.mostrar_mensaje(
                'No fue posible cargar la información del documento:\n{}'
                .format(error_consulta),
                tipo='error',
            )
            self._ventanas.bloquear_componente('btn_guardar')
            return

        if error:
            self._ventanas.mostrar_mensaje(
                error,
                tipo='error',
            )
            self._ventanas.bloquear_componente('btn_guardar')
            return

        self._interfaz.mostrar_documento(
            cliente=self._documento.get('Cliente') or '',
            folio=self._documento.get('DocFolio') or '',
            sucursal=self._documento.get('Sucursal') or 'No aplica',
        )
        self._interfaz.cargar_opciones_conversion(self.OPCIONES)
        self._interfaz.bloquear_informacion()

    def _guardar(self):
        if not self._documento:
            return

        tipo = self._ventanas.obtener_input_componente(
            'cbx_tipo_conversion'
        )
        if tipo not in self.OPCIONES:
            self._ventanas.mostrar_mensaje(
                'Seleccione Nota entregada o Pedido mayoreo.',
                tipo='error',
            )
            return

        folio = self._documento.get('DocFolio') or self._modelo.document_id
        if not self._ventanas.mostrar_mensaje_pregunta(
            'La factura {} será convertida a {}. ¿Desea continuar?'.format(
                folio,
                tipo,
            ),
            master=self._master,
        ):
            return

        try:
            resultado = self._modelo.convertir(tipo)
        except Exception as error:
            self._ventanas.mostrar_mensaje(
                'No fue posible convertir el documento:\n{}'.format(error),
                tipo='error',
            )
            return

        if not resultado.get('ok'):
            self._ventanas.mostrar_mensaje(
                resultado.get('mensaje', 'No se realizó la conversión.'),
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
