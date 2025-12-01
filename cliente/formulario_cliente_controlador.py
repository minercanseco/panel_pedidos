import webbrowser


class FormularioClienteControlador:
    def __init__(self, interfaz, modelo):
        self._interfaz = interfaz
        self._modelo = modelo

        self._rellenar_componentes()
        self._bloqueos_iniciales()
        self._cargar_eventos()

    def _cargar_eventos(self):
        eventos = {
            #'tbx_cp':  lambda event: self._cargar_info_por_cp(),
            #'cbx_colonia':  lambda event: self._cargar_info_por_colonia(),
            'btn_cancelar': self._interfaz.master.destroy,
            #'btn_guardar': self._validar_inputs_formulario,
            #'btn_copiar': self._copiar_info_formulario,
            #'btn_cif': self._actualizar_por_cif,
            'btn_domicilios': self._agregar_direccion,
            'btn_cif_visual': self._visualizar_cif
        }

        self._interfaz.ventanas.cargar_eventos(eventos)

    def _bloqueos_iniciales(self):
        es_cif = self._modelo.utilerias.es_cif(self._modelo.cliente.cif)
        es_rfc = self._modelo.utilerias.es_rfc(self._modelo.cliente.official_number)

        if es_rfc and es_cif:
            self._interfaz.ventanas.bloquear_componente('tbx_cif')
            self._interfaz.ventanas.bloquear_componente('tbx_rfc')

        self._interfaz.ventanas.bloquear_componente('tbx_envio')

        if self._modelo.cliente.zone_id == 1040:
            self._interfaz.ventanas.bloquear_componente('cbx_ruta')

        self._interfaz.ventanas.bloquear_componente('tbx_cliente')

    def _visualizar_cif(self):
        cif = self._interfaz.ventanas.obtener_input_componente('tbx_cif')
        rfc = self._interfaz.ventanas.obtener_input_componente('tbx_rfc')

        if not self._modelo.utilerias.es_rfc(rfc):
            self._interfaz.ventanas.mostrar_mensaje('El RFC es inválido')
            return

        if not self._modelo.utilerias.es_cif(cif):
            self._interfaz.ventanas.mostrar_mensaje('El CIF es inválido')
            return

        url = f'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={cif}_{rfc}'
        webbrowser.open(url)

    def _rellenar_componentes(self):
        MAPEO_COMPONENTES_CLIENTE = {
            'tbx_cliente': 'official_name',
            'tbx_domicilios': 'addresses',
            'tbx_rfc': 'official_number',
            'tbx_cif': 'cif',

            'tbx_ncomercial': 'commercial_name',
            'tbx_telefono': 'phone',
            'tbx_celular': 'cellphone',
            'tbx_numero': 'address_fiscal_ext_number',
            'tbx_calle': 'address_fiscal_street',
            'txt_comentario': 'address_fiscal_comments',
            'tbx_cp': 'address_fiscal_zip_code',
            'txt_correo': 'email',
            'tbx_envio': 'delivery_cost',

            'lbl_estado': 'address_fiscal_state_province',
            'lbl_municipio': 'address_fiscal_municipality',
        }

        for componente, atributo in MAPEO_COMPONENTES_CLIENTE.items():
            valor = getattr(self._modelo.cliente, atributo, None)
            self._interfaz.ventanas.insertar_input_componente(componente, valor)

        # rellenar cbx fiscales
        #------------------------------------------------------------------------
        consultas = {
            'cbx_regimen': (self._modelo.obtener_regimenes_fiscales, self._modelo.cliente.company_type_name),
            'cbx_formapago': (self._modelo.obtener_formas_pago, self._modelo.cliente.forma_pago),
            'cbx_metodopago': (self._modelo.obtener_metodos_pago, self._modelo.cliente.metodo_pago),
            'cbx_usocfdi': (self._modelo.obtener_uso_cfdi, self._modelo.cliente.receptor_uso_cfdi),
        }

        for componente, (funcion_consulta, atributo) in consultas.items():
            consulta = funcion_consulta()
            valores = [reg['Value'] for reg in consulta]
            self._interfaz.ventanas.rellenar_cbx(componente, valores)

            if self._modelo.cliente.business_entity_id != 0:
                if componente == 'cbx_regimen':
                    valor_seleccion = [reg['Value'] for reg in consulta if reg['Value'] == atributo]
                else:
                    valor_seleccion = [reg['Value'] for reg in consulta if reg['Clave'] == atributo]

                if valor_seleccion:
                    self._interfaz.ventanas.insertar_input_componente(componente, valor_seleccion[0])

        # ------------------------------------------------------------------------
        # rellenar cbx colonias
        info_colonias = self._modelo.obtener_colonias(self._modelo.cliente.address_fiscal_detail_id)
        colonias = [reg['City'] for reg in info_colonias]
        colonias = sorted(colonias)
        self._interfaz.ventanas.rellenar_cbx('cbx_colonia', colonias)
        if self._modelo.cliente.business_entity_id != 0:
            self._interfaz.ventanas.insertar_input_componente('cbx_colonia',
                                                              self._modelo.cliente.address_fiscal_city
                                                              )
        # ------------------------------------------------------------------------
        # rellenar cbx rutas
        info_rutas = self._modelo.obtener_todas_las_rutas()
        rutas = [reg['ZoneName'] for reg in info_rutas]
        rutas = sorted(rutas)
        self._interfaz.ventanas.rellenar_cbx('cbx_ruta', rutas)
        if self._modelo.business_entity_id != 0:
            self._interfaz.ventanas.insertar_input_componente('cbx_ruta',
                                                              self._modelo.cliente.zone_name
                                                              )
        # ------------------------------------------------------------------------

    def _agregar_direccion(self):
        self._interfaz.ventanas.agregar_pestana_notebook('formulario_cliente')