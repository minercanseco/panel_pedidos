import webbrowser


class FormularioClienteControlador:
    def __init__(self, interfaz, modelo):
        self._interfaz = interfaz
        self._modelo = modelo

        self._settar_info_cliente()
        self._rellenar_componentes()

    def _cargar_eventos(self):
        eventos = {
            #'tbx_cp':  lambda event: self._cargar_info_por_cp(),
            #'cbx_colonia':  lambda event: self._cargar_info_por_colonia(),
            'btn_cancelar': self._interfaz.master.destroy,
            #'btn_guardar': self._validar_inputs_formulario,
            #'btn_copiar': self._copiar_info_formulario,
            #'btn_cif': self._actualizar_por_cif,
            #'btn_domicilios': self._validar_cliente_con_adicionales
            'btn_cif_visual': self._visualizar_cif
        }

        self._interfaz.ventanas.cargar_eventos(eventos)

    def _visualizar_cif(self):
        cif = 'tbx_cif'
        rfc = 'tbx_rfc'

        if not self._modelo.utilerias.es_rfc(rfc):
            self._interfaz.ventanas.mostrar_mensaje('El RFC es inválido')
            return

        if not self._modelo.utilerias.es_cif(cif):
            self._interfaz.ventanas.mostrar_mensaje('El CIF es inválido')
            return

        url = f'https://siat.sat.gob.mx/app/qr/faces/pages/mobile/validadorqr.jsf?D1=10&D2=1&D3={cif}_{rfc}'
        webbrowser.open(url)

    def _settar_info_cliente(self):
        if self._modelo.business_entity_id == 0:
            # se asume como nueva captura
            return

        info_cliente = self._modelo.obtener_info_cliente(self._modelo.business_entity_id)
        self._modelo.cliente.consulta = info_cliente
        self._modelo.cliente.settear_valores_consulta()

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

            if componente == 'cbx_regimen':
                valor_seleccion = [reg['Value'] for reg in consulta if reg['Value'] == atributo]
            else:
                valor_seleccion = [reg['Value'] for reg in consulta if reg['Clave'] == atributo]

            if valor_seleccion:
                self._interfaz.ventanas.insertar_input_componente(componente, valor_seleccion[0])

        # ------------------------------------------------------------------------
        # rellenar cbx colonias
        print(self._modelo.cliente.address_fiscal_detail_id)
        # ------------------------------------------------------------------------
        # rellenar cbx rutas
        print(self._modelo.cliente.zone_id)
        # ------------------------------------------------------------------------