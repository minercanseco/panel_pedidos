import webbrowser

import pyperclip

from cliente.direccion_adicional import DireccionAdicional
from cliente.nombre_direccion import NombreDireccion


class FormularioClienteControlador:
    def __init__(self, interfaz, modelo):
        self._interfaz = interfaz
        self._modelo = modelo

        self._rellenar_componentes()
        self._bloqueos_iniciales()
        self._cargar_eventos()

    def _cargar_eventos(self):
        eventos = {
            'tbx_cp':  lambda event: self._rellenar_cbx_colonias_por_cp(),
            'cbx_colonia':  lambda event: self._eventos_cbx_colonia(),
            'btn_cancelar': self._interfaz.master.destroy,
            'btn_guardar': self._guardar_o_actualizar_cliente,
            'btn_copiar': self._copiar_info_direccion,
            'btn_cif': self._actualizar_por_cif,
            'btn_nueva_direccion':self._agregar_direccion,
            'btn_domicilios': self._agregar_direccion,
            'btn_cif_visual': self._visualizar_cif,

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

    def _actualizar_por_cif(self):
        cif = self._interfaz.ventanas.obtener_input_componente('tbx_cif')

        if not self._modelo.utilerias.es_cif(cif):
            return

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

        popup = self._interfaz.ventanas.crear_popup_ttkbootstrap()
        instancia = NombreDireccion(popup)
        popup.wait_window()

        if instancia.nombre_direccion:
            texto_pestana = instancia.nombre_direccion
            tab = texto_pestana.replace(' ', '_').lower()
            tab = f"tab_direccion_{tab}"

            nombre_base = tab.replace('tab_', '')

            frame_widget = self._interfaz.ventanas.agregar_pestana_notebook(
                'nb_formulario_cliente',
                nombre_base,
                texto_pestana
            )

            info_direccion = {
                'AddressDetailID': 0,
                'AddressName': texto_pestana,
                'OfficialName': self._modelo.cliente.official_name,
                'ComercialName': self._modelo.cliente.commercial_name,
                'OfficialNumber': self._modelo.cliente.official_number,
                'CIF': self._modelo.cliente.cif,
            }

            _ = DireccionAdicional(frame_widget, self._modelo, info_direccion)

    def _buscar_informacion_direccion_whatsapp(self):

        mensaje = (
            f"📍 ¿Podría confirmar si los datos de su dirección son correctos?  \n\n"
            f"👤 *Cliente:* {self._modelo.cliente.official_name}\n"
            f"📍 *Dirección del cliente* ({'Dirección Fiscal'})\n"
            f"🏠 *Calle:* {self._modelo.cliente.address_fiscal_street}\n"
            f"🔢 *Número:* {self._modelo.cliente.address_fiscal_ext_number}\n"
            f"📮 *C.P.:* {self._modelo.cliente.address_fiscal_zip_code}\n"
            f"🏘️ *Colonia:* {self._modelo.cliente.address_fiscal_city}\n"
            f"🏙️ *Municipio:* {self._modelo.cliente.address_fiscal_municipality}\n"
            f"🌎 *Estado:* {self._modelo.cliente.address_fiscal_state_province}\n\n"
            f"📞 *Teléfono:* {self._modelo.cliente.phone}\n"
            f"📱 *Celular:* {self._modelo.cliente.cellphone}\n\n"
            f"📝 *Comentarios:* {self._modelo.cliente.address_fiscal_comments}\n"
            f"🚚💸 *Envío a domicilio:* ${self._modelo.cliente.delivery_cost} (En compras menores a 200)\n"
        )
        if self._modelo.cliente.cayal_customer_type_id == 2:
            fiscales = (
                f"\n📧 *Correo:* {self._modelo.cliente.email}\n"
                f"🆔 *RFC:* {self._modelo.cliente.official_number}\n"
                f"📄 *Uso CFDI:* {self._modelo.cliente.receptor_uso_cfdi}\n"
            )
            mensaje += fiscales
        return mensaje.replace('None', '')

    def _copiar_info_direccion(self):
        mensaje = self._buscar_informacion_direccion_whatsapp()
        pyperclip.copy(mensaje)

    # funciones relacionadas al relleno del cbx colonias en base a las reglas de negocio

    def _rellenar_cbx_colonias_por_cp(self):
        cp = self._interfaz.ventanas.obtener_input_componente('tbx_cp')
        if not self._modelo.utilerias.es_codigo_postal(cp):
            return

        consulta = self._modelo.obtener_colonias(zip_code=cp)
        colonias = [reg['City'] for reg in consulta]
        colonias = sorted(colonias)
        self._interfaz.ventanas.rellenar_cbx('cbx_colonia', colonias)

    def _rellenar_cbx_colonias_por_ruta(self):
        if self._interfaz.ventanas.obtener_input_componente('cbx_colonia') != 'Seleccione':
            return

        consulta = self._modelo.obtener_colonias()
        colonias = [reg['City'] for reg in consulta]
        colonias = sorted(colonias)
        self._interfaz.ventanas.rellenar_cbx('cbx_colonia', colonias)

    def _rellenar_costo_envio(self):
        colonia = self._interfaz.ventanas.obtener_input_componente('cbx_colonia')
        if colonia == 'Seleccione':
            return

        monto_envio = self._modelo.obtener_envio_por_colonia(colonia)
        self._interfaz.ventanas.insertar_input_componente('tbx_envio', monto_envio)
        self._interfaz.ventanas.bloquear_componente('tbx_envio')

    def _actualizar_municipio_y_estado(self):
        colonia = self._interfaz.ventanas.obtener_input_componente('cbx_colonia')
        if colonia == 'Seleccione':
            return

        municipio, estado = self._modelo.obtener_estado_y_municipio_colonia(colonia)
        self._interfaz.ventanas.insertar_input_componente('lbl_estado', estado)
        self._interfaz.ventanas.insertar_input_componente('lbl_municipio', municipio)

    def _eventos_cbx_colonia(self):
        self._rellenar_cbx_colonias_por_ruta()
        self._rellenar_costo_envio()
        self._actualizar_municipio_y_estado()

    # recupera los inputs del formulario
    def _obtener_inputs_usuario(self):
        componentes = {
            # --- GENERALES ---
            'tbx_cliente': '',
            'tbx_ncomercial': '',
            'tbx_telefono': '',
            'tbx_celular': '',
            'tbx_calle': '',
            'tbx_numero': '',
            'txt_comentario': '',
            'tbx_cp': '',
            'tbx_envio': '',
            'cbx_ruta': '',

            # --- FISCAL ---
            'tbx_rfc': '',
            'tbx_cif': '',
            'btn_cif': '',

            'cbx_colonia': '',
            'cbx_regimen': '',
            'cbx_formapago': '',
            'cbx_metodopago': '',
            'cbx_usocfdi': '',

            'txt_correo': '',
        }

        for componente, valor in componentes.items():
            valor = self._interfaz.ventanas.obtener_input_componente(componente)
            componentes[componente] = valor

        return componentes

    def _validar_reglas_de_negocio(self):
        if not self._validar_estructura_inputs():
            return

        if not self._validar_reglas_fiscales():
            return

        if not self._validar_reglas_de_ruta():
            return

        return True

    def _validar_reglas_fiscales(self):
        valores = self._obtener_inputs_usuario()

        # valida la configuracion fiscal
        forma_pago = valores['cbx_formapago']
        metodo_pago = valores['cbx_metodopago']
        uso_cfdi = valores['cbx_usocfdi']
        regimen = valores['cbx_regimen']
        rfc = valores['tbx_rfc']
        cif = valores['tbx_cif']
        email = valores['txt_correo']

        # caso remision
        if 'S01' in uso_cfdi or rfc == 'XAXX010101000' or '616' in regimen:
            if not('S01' in uso_cfdi and rfc == 'XAXX010101000' and '616' in regimen):
                mensaje = (
                    "La configuración válida para un cliente que remisiona es la siguiente:\n"
                    "Forma de pago: 01, 04, 28\n"
                    "Método de pago: PUE - Pago en una sola exhibición.\n"
                    "Uso de CFDI: S01 - Sin efectos fiscales.\n"
                    "Régimen: 616 - Sin obligaciones fiscales.\n"
                    "Favor de validar y corregir."
                )
                self._interfaz.ventanas.mostrar_mensaje(mensaje)
                return

        # caso 99 ppd
        if '99' in forma_pago or 'PPD' in metodo_pago:

            if not ('99' in forma_pago and 'PPD' in metodo_pago):
                mensaje = (
                    "La forma de pago: 99 - Por definir\n"
                    "Debe configurarse solamente con \n"
                    "El método de pago: PPD - Pago en parcialidades o diferido.\n"
                    "Favor de validar y corregir."
                )
                self._interfaz.ventanas.mostrar_mensaje(mensaje)
                return

        # caso cif
        if rfc == 'XAXX010101000' and cif:
            self._interfaz.ventanas.mostrar_mensaje('La captura del CIF sólo es válida para un cliente que factura.')
            return

        # valida correos
        if (not email or email == '') and rfc != 'XAXX010101000':
            self._interfaz.ventanas.mostrar_mensaje('La captura de un email válido es obligatoria para un cliente'
                                                    'que factura.')
            return

        if email and rfc != 'XAXX010101000':
            if not self._modelo.utilerias.validar_cadena_correos(email):
                self._interfaz.ventanas.mostrar_mensaje('La cadena de correos es inválida, favor de corregir'
                                                        'inserte cada correo separado por una coma.')
                return

        return True

    def _validar_estructura_inputs(self):
        # valida telefonos
        valores = self._obtener_inputs_usuario()
        rfc = valores['tbx_rfc']
        celular = valores['tbx_celular']
        telefono = valores['tbx_telefono']
        comentarios = valores['txt_comentario']

        campos_obligatorios= [
            'tbx_cliente',
            'tbx_calle',
            'tbx_numero',
            'txt_comentario',
            'tbx_cp',
            'tbx_envio',
            'cbx_ruta',
            # --- FISCA,
            'tbx_rfc',
            'cbx_colonia',
            'cbx_regimen',
            'cbx_formapago',
            'cbx_metodopago',
            'cbx_usocfdi',
        ]

        for componente, valor in valores.items():
            if componente in campos_obligatorios:
                tipo = componente[0:3]
                nombre = componente[4::].capitalize()

                if tipo == 'tbx' and not valor:
                    self._interfaz.ventanas.mostrar_mensaje(f'Debe agregar un valor al campo: {nombre}')
                    return
                if tipo == 'cbx' and valor == 'Seleccione:':
                    self._interfaz.ventanas.mostrar_mensaje(f'Debe agregar un valor al campo: {nombre}')
                    return

        if not self._modelo.utilerias.es_rfc(rfc):
            self._interfaz.ventanas.mostrar_mensaje('El rfc es inválido.')
            return

        if not celular and not telefono:
            self._interfaz.ventanas.mostrar_mensaje('Debe capturar por lo menos un número telefónico.')
            return

        if not self._modelo.utilerias.es_numero_de_telefono(celular) and self._modelo.utilerias.es_numero_de_telefono(telefono):
            self._interfaz.ventanas.mostrar_mensaje('Debe capturar por lo menos un número telefónico.')
            return

        if not comentarios:
            self._interfaz.ventanas.mostrar_mensaje('Debe abundar en los comentarios de la dirección del cliente.')
            return


        return True

    def _validar_reglas_de_ruta(self):

        def _buscar_tipo_ruta_id(nombre_ruta):
            consulta_ruta_id = [ruta['TipoRutaID'] for ruta in self._modelo.consulta_rutas
                                if nombre_ruta == ruta['ZoneName']]
            if not consulta_ruta_id:
                return 1

            if consulta_ruta_id:
                return consulta_ruta_id[0]

        def _buscar_ruta_id(nombre_ruta):
            consulta_ruta_id = [ruta['ZoneID'] for ruta in self._modelo.consulta_rutas
                                if nombre_ruta == ruta['ZoneName']]
            if not consulta_ruta_id:
                return 0

            if consulta_ruta_id:
                return consulta_ruta_id[0]

        def _validar_ruta(ruta_id, tipo_ruta_id):
            # para cliente nuevo asumiendo que recien se capturan
            if ruta_id == 1040 and self._modelo.cliente.business_entity_id <= 0:
                self._interfaz.ventanas.mostrar_mensaje(
                    'No se puede hacer uso de la ruta R7 para clientes nuevos por este aplicativo.')
                return

            if tipo_ruta_id == 2 and self._modelo.user_group_id == 11 and self._modelo.cliente.business_entity_id <= 0:
                self._interfaz.ventanas.mostrar_mensaje('Las rutas de mayoreo no pueden ser establecidos por cajeros.')
                return

            return True


        valores = self._obtener_inputs_usuario()
        ruta_seleccionada = valores['cbx_ruta']

        # 2 mayoreo 1 domicilio
        tipo_ruta_id_seleccionada = _buscar_tipo_ruta_id(ruta_seleccionada)
        ruta_id_seleccionada = _buscar_ruta_id(ruta_seleccionada)

        if not _validar_ruta(ruta_id_seleccionada,tipo_ruta_id_seleccionada):
            return

        # asume que se pretende cambiar la ruta de un cliente:
        if self._modelo.cliente.zone_id != 0:
            ruta_guardada = self._modelo.cliente.zone_name
            tipo_ruta_id_guardada = _buscar_tipo_ruta_id(ruta_guardada)
            ruta_id_guardada = self._modelo.cliente.zone_id

            if not _validar_ruta(ruta_id_guardada, tipo_ruta_id_guardada):
                return

        return True

    def _guardar_o_actualizar_cliente(self):
        if not self._validar_reglas_de_negocio():
            return

        print('aqui actualizamos o guardamos')