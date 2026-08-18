class ControladorEditarDocumento:

    FORMAS_PAGO_VALIDAS_REMISION = ('01', '04', '28')

    CLAVE_FORMA_PAGO_REMISION = '01'
    CLAVE_METODO_PAGO_REMISION = 'PUE'
    CLAVE_USO_CFDI_REMISION = 'S01'

    def __init__(self, interfaz, modelo):
        self._interfaz = interfaz
        self._modelo = modelo
        self._ventanas = self._interfaz.ventanas
        self._master = self._interfaz._master

        self._documento = None
        self._formas_pago = []
        self._metodos_pago = []
        self._usos_cfdi = []
        self._documento_editable = True

        self._cargar_eventos()
        self._cargar_catalogos()
        self._cargar_documento()

    def _cargar_eventos(self):
        eventos = {
            'btn_guardar': self._guardar,
            'btn_convertir_factura': self._convertir_en_factura,
            'btn_convertir_remision': self.convertir_en_remision
        }

        self._ventanas.cargar_eventos(eventos)

    def _cargar_catalogos(self):
        self._formas_pago = self._modelo.obtener_formas_pago()
        self._metodos_pago = self._modelo.obtener_metodos_pago()
        self._usos_cfdi = self._modelo.obtener_usos_cfdi()

        self._ventanas.rellenar_cbx(
            'cbx_formapago',
            self._extraer_valores_combo(self._formas_pago)
        )

        self._ventanas.rellenar_cbx(
            'cbx_metodopago',
            self._extraer_valores_combo(self._metodos_pago)
        )

        self._ventanas.rellenar_cbx(
            'cbx_usocfdi',
            self._extraer_valores_combo(self._usos_cfdi)
        )

    def _cargar_documento(self):
        self._documento = self._modelo.obtener_documento()

        if not self._documento:
            self._ventanas.mostrar_mensaje(
                'No se encontró la información del documento.',
                tipo='error'
            )
            self._cerrar()
            return

        self._ventanas.insertar_input_componente(
            'tbx_cliente',
            self._documento.get('Cliente', '')
        )

        self._ventanas.insertar_input_componente(
            'tbx_folio',
            self._documento.get('Folio', '')
        )

        self._ventanas.insertar_input_componente(
            'txt_comentario',
            self._documento.get('Comentario', ''),
            con_saltos_de_linea=True
        )

        self._cargar_datos_fiscales_documento()
        self._aplicar_estado_documento()

    def _cargar_datos_fiscales_documento(self):
        self._seleccionar_combo_por_clave(
            'cbx_formapago',
            self._formas_pago,
            self._documento.get('FormaPago', '')
        )

        self._seleccionar_combo_por_clave(
            'cbx_metodopago',
            self._metodos_pago,
            self._documento.get('MetodoPago', '')
        )

        self._seleccionar_combo_por_clave(
            'cbx_usocfdi',
            self._usos_cfdi,
            self._documento.get('UsoCFDI', '')
        )

    def _cargar_datos_fiscales_remision(self):
        self._seleccionar_combo_por_clave(
            'cbx_formapago',
            self._formas_pago,
            self.CLAVE_FORMA_PAGO_REMISION
        )

        self._seleccionar_combo_por_clave(
            'cbx_metodopago',
            self._metodos_pago,
            self.CLAVE_METODO_PAGO_REMISION
        )

        self._seleccionar_combo_por_clave(
            'cbx_usocfdi',
            self._usos_cfdi,
            self.CLAVE_USO_CFDI_REMISION
        )

    def _cargar_datos_fiscales_factura_cliente(self):
        if not self._modelo.cliente_tiene_datos_facturacion():
            self._ventanas.mostrar_mensaje(
                (
                    'El cliente no cuenta con datos de facturación guardados. '
                    'Actualícelos e inténtelo de nuevo.'
                ),
                tipo='error'
            )
            return False

        info_cliente = self._modelo.obtener_info_cliente()

        self._seleccionar_combo_por_clave(
            'cbx_formapago',
            self._formas_pago,
            info_cliente.get('FormaPago', '')
        )

        self._seleccionar_combo_por_clave(
            'cbx_metodopago',
            self._metodos_pago,
            info_cliente.get('MetodoPago', '')
        )

        self._seleccionar_combo_por_clave(
            'cbx_usocfdi',
            self._usos_cfdi,
            info_cliente.get('ReceptorUsoCFDI', '')
        )

        return True

    def _aplicar_estado_documento(self):
        self._documento_editable = self._puede_editar_documento()

        if self._documento_editable:
            self._ventanas.bloquear_componente('tbx_cliente')
            self._ventanas.bloquear_componente('tbx_folio')
            return

        self._bloquear_formulario()

        self._ventanas.mostrar_mensaje(
            (
                'Este documento no puede editarse porque ya está timbrado '
                'o se encuentra cancelado.'
            ),
            tipo='error'
        )

    def _puede_editar_documento(self):
        cfd_status_id = int(self._documento.get('CFDStatusID', 0) or 0)
        cancelled = int(self._documento.get('Cancelled', 0) or 0)

        return cfd_status_id != 3 and cancelled == 0

    def _bloquear_formulario(self):
        componentes = [
            'tbx_cliente',
            'tbx_folio',
            'cbx_formapago',
            'cbx_metodopago',
            'cbx_usocfdi',
            'txt_comentario',
            'btn_guardar',
            'btn_convertir_factura',
            'btn_convertir_remision'
        ]

        for componente in componentes:
            if componente in self._ventanas.componentes_forma:
                self._ventanas.bloquear_componente(componente)

    def _guardar(self):
        if not self._documento_editable:
            self._ventanas.mostrar_mensaje(
                'El documento no está disponible para edición.',
                tipo='error'
            )
            return

        metodo_pago = self._obtener_clave_combo(
            'cbx_metodopago',
            self._metodos_pago
        )

        forma_pago = self._obtener_clave_combo(
            'cbx_formapago',
            self._formas_pago
        )

        uso_cfdi = self._obtener_clave_combo(
            'cbx_usocfdi',
            self._usos_cfdi
        )

        comentario = self._ventanas.obtener_input_componente(
            'txt_comentario'
        )

        if not self._validar_datos_guardado(
            metodo_pago=metodo_pago,
            forma_pago=forma_pago,
            uso_cfdi=uso_cfdi
        ):
            return

        if self._datos_corresponden_a_remision(
            metodo_pago=metodo_pago,
            forma_pago=forma_pago,
            uso_cfdi=uso_cfdi
        ):
            resultado = self._modelo.guardar_como_remision(
                comentario=comentario,
                forma_pago=forma_pago
            )

            if isinstance(resultado, dict) and not resultado.get('ok', True):
                self._ventanas.mostrar_mensaje(
                    resultado.get(
                        'mensaje',
                        'No fue posible guardar el documento como remisión.'
                    ),
                    tipo='error'
                )
                return

            self._documento['EsRemision'] = 1
            mensaje = resultado.get(
                'mensaje',
                'Documento actualizado como remisión correctamente.'
            ) if isinstance(resultado, dict) else 'Documento actualizado como remisión correctamente.'

        else:
            resultado = self._modelo.guardar_como_factura(
                comentario=comentario,
                metodo_pago=metodo_pago,
                forma_pago=forma_pago,
                uso_cfdi=uso_cfdi
            )

            if not resultado.get('ok'):
                self._ventanas.mostrar_mensaje(
                    resultado.get(
                        'mensaje',
                        'No fue posible guardar el documento como factura.'
                    ),
                    tipo='error'
                )
                return

            self._documento['EsRemision'] = 0
            mensaje = resultado.get(
                'mensaje',
                'Documento actualizado como factura correctamente.'
            )

        self._documento['MetodoPago'] = metodo_pago
        self._documento['FormaPago'] = forma_pago
        self._documento['UsoCFDI'] = uso_cfdi
        self._documento['Comentario'] = comentario

        self._ventanas.mostrar_mensaje(
            mensaje,
            tipo='info'
        )

        self._cerrar()

    def _validar_datos_guardado(self, metodo_pago, forma_pago, uso_cfdi):
        if not metodo_pago:
            self._ventanas.mostrar_mensaje(
                'Debe seleccionar un método de pago.',
                tipo='error'
            )
            return False

        if not forma_pago:
            self._ventanas.mostrar_mensaje(
                'Debe seleccionar una forma de pago.',
                tipo='error'
            )
            return False

        if not uso_cfdi:
            self._ventanas.mostrar_mensaje(
                'Debe seleccionar un uso CFDI.',
                tipo='error'
            )
            return False

        if self._datos_corresponden_a_remision(
            metodo_pago=metodo_pago,
            forma_pago=forma_pago,
            uso_cfdi=uso_cfdi
        ):
            return True

        return self._validar_datos_factura(
            metodo_pago=metodo_pago,
            forma_pago=forma_pago
        )

    def _datos_corresponden_a_remision(self, metodo_pago, forma_pago, uso_cfdi):
        return (
            metodo_pago == self.CLAVE_METODO_PAGO_REMISION
            and uso_cfdi == self.CLAVE_USO_CFDI_REMISION
            and forma_pago in self.FORMAS_PAGO_VALIDAS_REMISION
        )

    def _validar_datos_factura(self, metodo_pago, forma_pago):
        if not self._modelo.cliente_tiene_datos_facturacion():
            self._ventanas.mostrar_mensaje(
                (
                    'El cliente no cuenta con datos de facturación guardados. '
                    'Solo puede guardar datos fiscales válidos para remisión.'
                ),
                tipo='error'
            )
            return False

        if metodo_pago == 'PPD' and forma_pago != '99':
            self._ventanas.mostrar_mensaje(
                'Cuando el método de pago es PPD, la forma de pago debe ser 99.',
                tipo='error'
            )
            return False

        return True

    def _convertir_en_factura(self):
        if not self._documento_editable:
            self._ventanas.mostrar_mensaje(
                'El documento no está disponible para edición.',
                tipo='error'
            )
            return

        if not self._cargar_datos_fiscales_factura_cliente():
            return

        self._documento['EsRemision'] = 0

        self._ventanas.mostrar_mensaje(
            'Valores fiscales del cliente cargados. Presione Guardar para aplicar los cambios.',
            tipo='info'
        )

    def convertir_en_remision(self):
        if not self._documento_editable:
            self._ventanas.mostrar_mensaje(
                'El documento no está disponible para edición.',
                tipo='error'
            )
            return

        self._cargar_datos_fiscales_remision()
        self._documento['EsRemision'] = 1
        self._documento['FormaPago'] = self.CLAVE_FORMA_PAGO_REMISION
        self._documento['MetodoPago'] = self.CLAVE_METODO_PAGO_REMISION
        self._documento['UsoCFDI'] = self.CLAVE_USO_CFDI_REMISION

        self._ventanas.mostrar_mensaje(
            'Valores fiscales de remisión cargados. Presione Guardar para aplicar los cambios.',
            tipo='info'
        )

    def _documento_es_remision(self):
        if not self._documento:
            return False

        return int(self._documento.get('EsRemision', 0) or 0) == 1

    def _extraer_valores_combo(self, consulta):
        valores = []

        for reg in consulta:
            valor = str(reg.get('Value', '')).strip()

            if valor:
                valores.append(valor)

        return valores

    def _obtener_clave_combo(self, nombre_combo, catalogo):
        valor_combo = self._ventanas.obtener_input_componente(nombre_combo)

        if not valor_combo or valor_combo == 'Seleccione':
            return None

        valor_combo = str(valor_combo).strip()

        for reg in catalogo:
            clave = str(reg.get('Clave', '')).strip()
            valor = str(reg.get('Value', '')).strip()

            if valor == valor_combo:
                return clave

            if clave == valor_combo:
                return clave

        return valor_combo.split(' - ')[0].strip()

    def _seleccionar_combo_por_clave(self, nombre_combo, catalogo, clave):
        clave = str(clave or '').strip()

        if not clave:
            return

        for reg in catalogo:
            clave_reg = str(reg.get('Clave', '')).strip()
            valor_reg = str(reg.get('Value', '')).strip()

            if clave_reg == clave:
                self._ventanas.insertar_input_componente(
                    nombre_combo,
                    valor_reg
                )
                return

    def _cerrar(self):
        try:
            self._master.destroy()
        except Exception:
            try:
                self._master.close()
            except Exception:
                pass