import datetime
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
            'btn_cancelar': self._cerrar_notebook,
            'btn_guardar': self._guardar_o_actualizar_cliente,
            'btn_copiar': self._copiar_info_direccion,
            'btn_cif': self._actualizar_por_cif,
            'btn_nueva_direccion':self._agregar_direccion,
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
            valores = []
            # este if solo es valido cuando el cliente es nuevo y la captura es por CIF
            if componente == 'cbx_regimen' and self._modelo.cliente.company_type_names:
                valores = self._modelo.cliente.company_type_names
            else:
                valores = [reg['Value'] for reg in consulta]

            if len(valores) == 1:
                self._interfaz.ventanas.rellenar_cbx(componente, valores, sin_seleccione=True)
            else:
                self._interfaz.ventanas.rellenar_cbx(componente, valores, sin_seleccione=False)

            #if self._modelo.cliente.business_entity_id != 0:
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
                'nbk_formulario_cliente',
                nombre_base,
                f'{texto_pestana} 🏠'
            )

            info_direccion = {
                'AddressDetailID': 0,
                'AddressName': texto_pestana,
                'OfficialName': self._modelo.cliente.official_name,
                'ComercialName': self._modelo.cliente.commercial_name,
                'OfficialNumber': self._modelo.cliente.official_number,
                'CIF': self._modelo.cliente.cif,

            }

            info_notebook = {
                'notebook': self._interfaz.info_notebook['notebook'],
                'tab_notebook': frame_widget,
                'nombre_notebook': self._interfaz.info_notebook['nombre_notebook'],
                'nombre_tab': tab
            }
            _ = DireccionAdicional(frame_widget, self._modelo, info_direccion, info_notebook)

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

    def _rellenar_cp_por_colonia(self):
        colonia = self._interfaz.ventanas.obtener_input_componente('cbx_colonia')
        if colonia == 'Seleccione':
            return

        municipio = self._interfaz.ventanas.obtener_input_componente('lbl_municipio')
        estado = self._interfaz.ventanas.obtener_input_componente('lbl_estado')

        cp = self._modelo.obtener_cp_por_colonia(colonia, estado, municipio)

        self._interfaz.ventanas.insertar_input_componente('tbx_cp', cp)

    def _settear_ruta_colonia(self):
        colonia = self._interfaz.ventanas.obtener_input_componente('cbx_colonia')
        if colonia == 'Seleccione':
            return

        ruta = self._interfaz.ventanas.obtener_input_componente('cbx_ruta')

        # si el cliente fue previamente guardado entonces
        if self._modelo.buscar_tipo_ruta_id(ruta) == 2:
            return

        consulta = self._modelo.consulta_colonias
        consulta_ruta = [reg['ZoneName'] for reg in consulta if reg['City'] == colonia]
        if consulta_ruta:
            ruta = consulta_ruta[0]
            self._interfaz.ventanas.insertar_input_componente('cbx_ruta', ruta)

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
        self._rellenar_cp_por_colonia()
        self._settear_ruta_colonia()
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
            'lbl_estado':'',
            'lbl_municipio':'',
            'cbx_regimen': '',
            'cbx_formapago': '',
            'cbx_metodopago': '',
            'cbx_usocfdi': '',

            'txt_correo': '',
        }

        for nombre in componentes:
            componentes[nombre] = self._interfaz.ventanas.obtener_input_componente(nombre)

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
        forma_pago = valores['cbx_formapago'] or ''
        metodo_pago = valores['cbx_metodopago'] or ''
        uso_cfdi = valores['cbx_usocfdi'] or ''
        regimen = valores['cbx_regimen'] or ''
        rfc = (valores['tbx_rfc'] or '').strip().upper()
        cif = valores['tbx_cif'] or ''
        email = (valores['txt_correo'] or '').strip()

        # === CASO REMISIÓN ===
        if 'S01' in uso_cfdi or rfc == 'XAXX010101000' or '616' in regimen:
            if not ('S01' in uso_cfdi and rfc == 'XAXX010101000' and '616' in regimen):
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

        # === CASO 99 + PPD ===
        if '99' in forma_pago or 'PPD' in metodo_pago:
            if not ('99' in forma_pago and 'PPD' in metodo_pago):
                mensaje = (
                    "La forma de pago: 99 - Por definir\n"
                    "debe configurarse solamente con:\n"
                    "El método de pago: PPD - Pago en parcialidades o diferido.\n"
                    "Favor de validar y corregir."
                )
                self._interfaz.ventanas.mostrar_mensaje(mensaje)
                return

        # === CASO CIF ===
        if rfc == 'XAXX010101000' and cif:
            self._interfaz.ventanas.mostrar_mensaje(
                'La captura del CIF sólo es válida para un cliente que factura.'
            )
            return

        # === VALIDACIÓN DE CORREO(S) ===
        # Para clientes que facturan (RFC distinto de genérico) el correo es obligatorio
        if not email and rfc != 'XAXX010101000':
            self._interfaz.ventanas.mostrar_mensaje(
                'La captura de un email válido es obligatoria para un cliente que factura.'
            )
            return

        if email and rfc != 'XAXX010101000':
            if not self._modelo.utilerias.validar_cadena_correos(email):
                self._interfaz.ventanas.mostrar_mensaje(
                    'La cadena de correos es inválida, favor de corregir. '
                    'Inserte cada correo separado por una coma.'
                )
                return

        return True

    def _validar_estructura_inputs(self):
        valores = self._obtener_inputs_usuario()
        rfc = valores['tbx_rfc'] or ''
        celular = valores['tbx_celular'] or ''
        telefono = valores['tbx_telefono'] or ''
        comentarios = valores['txt_comentario'] or ''

        campos_obligatorios = [
            'tbx_cliente',
            'tbx_calle',
            'tbx_numero',
            'txt_comentario',
            'tbx_cp',
            'tbx_envio',
            'cbx_ruta',
            # --- FISCAL ---
            'tbx_rfc',
            'cbx_colonia',
            'cbx_regimen',
            'cbx_formapago',
            'cbx_metodopago',
            'cbx_usocfdi',
        ]

        # === CAMPOS OBLIGATORIOS ===
        for componente, valor in valores.items():
            if componente in campos_obligatorios:
                tipo = componente[0:3]  # tbx / cbx / txt
                nombre = componente[4:].capitalize()  # cliente, calle, numero, ...

                if tipo == 'tbx' and not valor:
                    self._interfaz.ventanas.mostrar_mensaje(
                        f'Debe agregar un valor al campo: {nombre}'
                    )
                    return

                if tipo == 'cbx' and valor == 'Seleccione:':
                    self._interfaz.ventanas.mostrar_mensaje(
                        f'Debe agregar un valor al campo: {nombre}'
                    )
                    return

        # === RFC ===
        if not self._modelo.utilerias.es_rfc(rfc):
            self._interfaz.ventanas.mostrar_mensaje('El RFC es inválido.')
            return

        # === TELÉFONOS ===
        # 1) Debe haber al menos uno capturado
        if not celular and not telefono:
            self._interfaz.ventanas.mostrar_mensaje(
                'Debe capturar por lo menos un número telefónico.'
            )
            return

        # 2) Debe haber al menos uno válido en formato
        es_cel_valido = bool(celular) and self._modelo.utilerias.es_numero_de_telefono(celular)
        es_tel_valido = bool(telefono) and self._modelo.utilerias.es_numero_de_telefono(telefono)

        if not (es_cel_valido or es_tel_valido):
            self._interfaz.ventanas.mostrar_mensaje(
                'Debe capturar por lo menos un número telefónico válido.'
            )
            return

        # === COMENTARIOS ===
        if not comentarios:
            self._interfaz.ventanas.mostrar_mensaje(
                'Debe abundar en los comentarios de la dirección del cliente.'
            )
            return

        return True

    def _validar_reglas_de_ruta(self):

        def _validar_ruta(ruta_id, tipo_ruta_id):
            # Cliente nuevo y ruta R7 (1040)
            if ruta_id == 1040 and self._modelo.cliente.business_entity_id <= 0:
                self._interfaz.ventanas.mostrar_mensaje(
                    'No se puede hacer uso de la ruta R7 para clientes nuevos por este aplicativo.'
                )
                return

            # Mayoreo (tipo_ruta_id = 2) no permitida para cajeros (user_group_id = 11) en clientes nuevos
            if (tipo_ruta_id == 2
                    and self._modelo.user_group_id == 11
                    and self._modelo.cliente.business_entity_id <= 0):
                self._interfaz.ventanas.mostrar_mensaje(
                    'Las rutas de mayoreo no pueden ser establecidas por cajeros.'
                )
                return

            return True

        valores = self._obtener_inputs_usuario()
        ruta_seleccionada = valores['cbx_ruta']

        tipo_ruta_id_sel = self._modelo.buscar_tipo_ruta_id(ruta_seleccionada)
        ruta_id_sel = self._modelo.buscar_ruta_id(ruta_seleccionada)

        if not _validar_ruta(ruta_id_sel, tipo_ruta_id_sel):
            return

        # Si ya tenía ruta guardada, asumimos que se pretende cambiar
        if self._modelo.cliente.zone_id != 0:
            ruta_guardada = self._modelo.cliente.zone_name
            tipo_ruta_id_guardada = self._modelo.buscar_tipo_ruta_id(ruta_guardada)
            ruta_id_guardada = self._modelo.cliente.zone_id

            if not _validar_ruta(ruta_id_guardada, tipo_ruta_id_guardada):
                return

        return True

    def _settear_valores_formulario_a_cliente(self):
        valores = self._obtener_inputs_usuario()
        cliente = self._modelo.cliente

        # -----------------------------------------
        # 1) Atributos de dirección fiscal del cliente
        # -----------------------------------------
        atributos_equivalentes = {
            'tbx_cliente': 'official_name',
            'tbx_ncomercial': 'commercial_name',
            'tbx_telefono': 'phone',
            'tbx_celular': 'cellphone',
            'tbx_calle': 'address_fiscal_street',
            'tbx_numero': 'address_fiscal_ext_number',
            'txt_comentario': 'address_fiscal_comments',
            'tbx_cp': 'address_fiscal_zip_code',
            'tbx_envio': 'delivery_cost',
            'cbx_ruta': 'zone_name',
            'tbx_rfc': 'official_number',
            'tbx_cif': 'cif',
            'cbx_colonia': 'address_fiscal_city',
            'cbx_regimen': 'company_type_name',
            'txt_correo': 'email',
            'lbl_estado': 'address_fiscal_state_province',
            'lbl_municipio': 'address_fiscal_municipality',
        }

        # Campos que queremos en MAYÚSCULAS
        upper_cases = [
            'tbx_cliente',
            'tbx_ncomercial',
            'tbx_calle',
            'tbx_numero',
            'txt_comentario',
            'tbx_rfc',  # RFC
            'cbx_colonia',  # colonia / ciudad
            'lbl_estado',  # estado
            'lbl_municipio',  # municipio
        ]

        for componente, atributo_cliente in atributos_equivalentes.items():
            if componente not in valores:
                continue

            valor = valores[componente]

            # Normalización básica
            if isinstance(valor, str):
                valor = valor.strip()
                if componente in upper_cases and valor:
                    valor = valor.upper()

            # Tratamientos especiales por tipo de dato
            if atributo_cliente == 'delivery_cost':
                # Si viene vacío, asumimos 20
                try:
                    valor = float(valor) if valor not in (None, '') else 20
                except ValueError:
                    valor = 20

            if atributo_cliente == 'address_fiscal_zip_code':
                # CP como string limpio
                valor = valor or ''

            # Asignar al cliente
            setattr(cliente, atributo_cliente, valor)

        # -----------------------------------------
        # 2) Atributos fiscales (formas/ métodos / uso CFDI)
        # -----------------------------------------
        atributos_fiscales = {
            'cbx_formapago': (self._modelo.consulta_formas_pago, 'forma_pago'),
            'cbx_metodopago': (self._modelo.consulta_metodos_pago, 'metodo_pago'),
            'cbx_usocfdi': (self._modelo.consulta_uso_cfdi, 'receptor_uso_cfdi'),
        }

        for componente, (consulta, atributo_cliente) in atributos_fiscales.items():
            seleccionado = valores.get(componente, '')
            if isinstance(seleccionado, str):
                seleccionado = seleccionado.strip()

            if not seleccionado or seleccionado == 'Seleccione:':
                continue

            registro = next(
                (reg for reg in consulta if reg['Value'] == seleccionado),
                None
            )
            if not registro:
                continue

            clave = registro['Clave']
            setattr(cliente, atributo_cliente, clave)

        # -----------------------------------------
        # 3) Códigos SAT según colonia
        # -----------------------------------------
        info_colonia = self._modelo.obtener_info_colonia(
            valores.get('cbx_colonia', ''),
            valores.get('lbl_estado', ''),
            valores.get('lbl_municipio', '')
        )

        cliente.country_code = info_colonia.get('CountryCode', '')
        cliente.state_code = info_colonia.get('StateCode', '')
        cliente.city_code = info_colonia.get('CityCode', '')
        cliente.municipality_code = info_colonia.get('MunicipalityCode', '')

        # Agregar/actualizar dirección fiscal en addresses_details
        cliente.add_address_detail(self._crear_direccion_fiscal())

        # -----------------------------------------
        # 4) ZoneID según ruta
        # -----------------------------------------
        nombre_ruta = valores.get('cbx_ruta', '')

        zone_id = next(
            (reg['ZoneID'] for reg in self._modelo.consulta_rutas
             if reg['ZoneName'] == nombre_ruta),
            1030  # default si no se encuentra
        )

        cliente.zone_id = zone_id

    def _guardar_o_actualizar_cliente(self):
        # garantizar que exista colonia acorde a la ruta
        self._rellenar_cp_por_colonia()
        self._settear_ruta_colonia()

        # esto valida las reglas de negocio para la dirección fiscal
        if not self._validar_reglas_de_negocio():
            return

        # aqui iniciamos el proceso de validación si existen de las direcciones adicionales
        self._cargar_direcciones_adicionales_en_cliente()
        for direccion in self._modelo.cliente.addresses_details:
            if not self._validar_direccion_adicional(direccion):
                return

        # aqui guardamos al cliente o lo actualizamos, guardamos las direcciones adicionales o las actualizamos
        self._settear_valores_formulario_a_cliente()

        # borramos las direcciones que ya no sean validas
        for address_detail_id in self._modelo.cliente.deleted_addresses:
            if address_detail_id == 0:
                continue
            self._modelo.base_de_datos.borrar_direccion(address_detail_id, self._modelo.user_id)

        self._modelo.base_de_datos.crear_cliente(self._modelo.cliente, self._modelo.user_id)

        self._cerrar_notebook()

    def _crear_direccion_fiscal(self):
        return {
            'AddressDetailID': self._modelo.cliente.address_fiscal_detail_id,
            'AddressName': 'Dirección Fiscal',
            'City': self._modelo.cliente.address_fiscal_city,
            'CreatedOn': datetime.datetime.now().date(),
            'UserName': self._modelo.user_name,
            'Street': self._modelo.cliente.address_fiscal_street,
            'ExtNumber': self._modelo.cliente.address_fiscal_ext_number,
            'Comments': self._modelo.cliente.address_fiscal_comments,
            'ZipCode': self._modelo.cliente.address_fiscal_zip_code,
            'StateProvince': self._modelo.cliente.address_fiscal_state_province,
            'Municipality': self._modelo.cliente.address_fiscal_municipality,
            'StateProvinceCode': self._modelo.cliente.state_code,
            'MunicipalityCode': self._modelo.cliente.municipality_code,
            'CityCode': self._modelo.cliente.city_code,
            'Telefono': self._modelo.cliente.phone,
            'Correo': self._modelo.cliente.email,
            'Celular': self._modelo.cliente.cellphone,
            'DepotID': 0,
            'DeliveryCost': self._modelo.utilerias.redondear_valor_cantidad_a_decimal(
                self._modelo.cliente.delivery_cost),
            'OfficialName': self._modelo.cliente.official_name,
            'ComercialName': self._modelo.cliente.commercial_name,
            'OfficialNumber': self._modelo.cliente.official_number,
            'CIF':self._modelo.cliente.cif,
            'ZoneName': self._modelo.cliente.zone_name,
            'IsMainAddress':1
        }

    def _cargar_direcciones_adicionales_en_cliente(self):
        client = self._modelo.cliente

        # Limpiar detalles actuales para recargar desde la UI
        client.addresses_details = []

        for instancia in client.additional_address_instances:
            # Si la pestaña ya no existe (se eliminó), se omite.
            # La propia DireccionAdicional ya habrá gestionado deleted_addresses.
            if not instancia.existe_frame():
                continue

            # Si la pestaña existe → leer inputs y agregar a addresses_details
            instancia.cargar_direccion_en_cliente()

    def _validar_direccion_adicional(self, info_direccion_adicional):
        """
        info_direccion_adicional ~
        {
            'AddressName': 'Monte verde',
            'Street': 'Monteverde 4 ',
            'ExtNumber': 'Mza 2 LT 2',
            'Comments': 'Casa de dos pisos a dos casas de la esquina con garaje\n',
            'ZipCode': '24038',
            'City': 'Monte Verde',
            'Municipality': 'Campeche',
            'StateProvince': 'Campeche',
            'Telefono': '9811140593',
            'Celular': '',
            'Correo': '\n',
        }
        """
        componentes_validables = {
            'AddressName': 'el nombre de la dirección',
            'Street': 'la calle de la dirección',
            'ExtNumber': 'el número de la dirección',
            'Comments': 'los comentarios de la dirección',
            'ZipCode': 'el código postal de la dirección',
            'City': 'la colonia de la dirección',
            'Municipality': 'el municipio de la dirección',
            'StateProvince': 'el estado de la dirección',
        }

        nombre_direccion = info_direccion_adicional.get('AddressName', '').strip() or '(sin nombre)'

        # -------------------------------------------------
        # 1) Validar nulidad / longitud mínima de campos base
        # -------------------------------------------------
        for clave, etiqueta in componentes_validables.items():
            valor = info_direccion_adicional.get(clave, '')

            # Normalizar a string
            if valor is None:
                valor_str = ''
            else:
                valor_str = str(valor).strip()

            if not valor_str:
                mensaje = f"Debe capturar {etiqueta} para la dirección: {nombre_direccion}."
                self._interfaz.ventanas.mostrar_mensaje(mensaje)
                return

            if len(valor_str) < 2:
                mensaje = f"Debe abundar en {etiqueta} para la dirección: {nombre_direccion}."
                self._interfaz.ventanas.mostrar_mensaje(mensaje)
                return

        # -------------------------------------------------
        # 2) Validar que exista al menos un teléfono o celular
        # -------------------------------------------------
        telefono = (info_direccion_adicional.get('Telefono') or '').strip()
        celular = (info_direccion_adicional.get('Celular') or '').strip()

        if not telefono and not celular:
            mensaje = (
                f"Debe capturar por lo menos un teléfono o celular "
                f"para la dirección: {nombre_direccion}."
            )
            self._interfaz.ventanas.mostrar_mensaje(mensaje)
            return

        # Si se capturó teléfono, validar formato (si tienes utilería)
        if telefono and not self._modelo.utilerias.es_numero_de_telefono(telefono):
            mensaje = (
                f"El teléfono capturado para la dirección {nombre_direccion} es inválido. "
                f"Favor de verificar."
            )
            self._interfaz.ventanas.mostrar_mensaje(mensaje)
            return

        # Si se capturó celular, validar formato
        if celular and not self._modelo.utilerias.es_numero_de_telefono(celular):
            mensaje = (
                f"El celular capturado para la dirección {nombre_direccion} es inválido. "
                f"Favor de verificar."
            )
            self._interfaz.ventanas.mostrar_mensaje(mensaje)
            return

        # -------------------------------------------------
        # 3) Validar estructura del correo electrónico (si existe)
        # -------------------------------------------------
        correo = (info_direccion_adicional.get('Correo') or '').strip()

        # En direcciones adicionales lo dejamos opcional: solo validamos si viene algo
        if correo:
            # Si usas cadena de correos separada por comas, mantén validar_cadena_correos:
            if not self._modelo.utilerias.validar_cadena_correos(correo):
                mensaje = (
                    f"El correo capturado para la dirección {nombre_direccion} es inválido.\n"
                    f"Si son varios, sepárelos con una coma."
                )
                self._interfaz.ventanas.mostrar_mensaje(mensaje)
                return

        return True

    def _cerrar_notebook(self):
        ventana = self._interfaz.master.winfo_toplevel()
        ventana.destroy()