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

        # esto garantiza en teoria el poder contrastar la direccion fiscal modificada por el usuario con la de la bd
        if self._modelo.cliente.business_entity_id != 0:
            direccion_fiscal = self._crear_direccion_fiscal()
            informacion_fiscal = self._crear_informacion_fiscal()
            print(informacion_fiscal)
            self._modelo.cliente.add_fiscal_detail_backup(informacion_fiscal)
            self._modelo.cliente.add_address_detail_backup(direccion_fiscal)

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

        self._actualizar_municipio_y_estado()
        municipio = self._interfaz.ventanas.obtener_input_componente('lbl_municipio')
        municipio ='Campeche' if not municipio else municipio.strip()

        estado = self._interfaz.ventanas.obtener_input_componente('lbl_estado')
        estado = 'Campeche' if not estado else estado.strip()

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

        estado, municipio = self._modelo.obtener_estado_y_municipio_colonia(colonia)
        self._interfaz.ventanas.insertar_input_componente('lbl_estado', estado)
        self._interfaz.ventanas.insertar_input_componente('lbl_municipio', municipio)

    def _eventos_cbx_colonia(self):
        self._rellenar_cbx_colonias_por_ruta()
        self._rellenar_costo_envio()
        self._rellenar_cp_por_colonia()
        self._settear_ruta_colonia()

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

        self._registrar_bitacora_cambios_cliente(self._modelo.cliente,
                                                 self._modelo.user_id,
                                                 self._modelo.user_name
                                                 )

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

    def _crear_informacion_fiscal(self):
        return {
            'official_number': self._modelo.cliente.official_number,
            'forma_pago': self._modelo.cliente.forma_pago,
            'metodo_pago': self._modelo.cliente.metodo_pago,
            'receptor_uso_cfdi': self._modelo.cliente.receptor_uso_cfdi,
            'company_type_name': self._modelo.cliente.company_type_name,
            'zone_name':self._modelo.cliente.zone_name
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

    def _generar_bitacora_cambios_direcciones(self, cliente, usuario_id):
        """
        Compara cliente.addresses_details_backup vs cliente.addresses_details
        y genera una lista de dicts con:

          - address_detail_id
          - es_fiscal (bool)
          - address_name
          - campo
          - valor_anterior
          - valor_nuevo
          - motivo
          - motivo_id
          - usuario_id

        Soporta:
          - Dirección fiscal (IsMainAddress == 1 o AddressDetailID == address_fiscal_detail_id)
          - Direcciones adicionales

        NOTA: Altas (AddressDetailID=0 sin versión anterior) y bajas
              las puedes manejar en otra función con motivos 28 y 30.
        """

        cambios = []

        # Si el cliente es nuevo o no hay backup, no hay nada que contrastar
        if not getattr(cliente, "business_entity_id", 0):
            return cambios

        backup = getattr(cliente, "addresses_details_backup", []) or []
        actuales = getattr(cliente, "addresses_details", []) or []

        # Indexar backup y actuales por AddressDetailID (incluimos 0 también, por si quieres usarlos luego)
        backup_por_id = {}
        for d in backup:
            aid = d.get("AddressDetailID", 0) or 0
            backup_por_id[aid] = d

        actuales_por_id = {}
        for d in actuales:
            aid = d.get("AddressDetailID", 0) or 0
            actuales_por_id[aid] = d

        # ID fiscal registrado (si existe)
        fiscal_detail_id_ref = getattr(cliente, 'address_fiscal_detail_id', 0) or 0

        # --- Motivos dirección FISCAL ---
        motivos_fiscal = {
            "Street": (13, "CAMBIO EN CALLE FISCAL"),
            "ExtNumber": (14, "CAMBIO EN NÚMERO EXTERIOR FISCAL"),
            "Comments": (15, "CAMBIOS EN COMENTARIOS DE DIRECCIÓN FISCAL"),
            "ZipCode": (16, "CAMBIO EN CÓDIGO POSTAL FISCAL"),
            "City": (17, "CAMBIO EN COLONIA FISCAL"),
            "Municipality": (18, "CAMBIO EN MUNICIPIO FISCAL"),
            "StateProvince": (19, "CAMBIO EN ESTADO FISCAL"),
            "ZoneName": (20, "CAMBIO EN RUTA DE ENTREGA"),
            "DeliveryCost": (21, "CAMBIO EN COSTO DE ENVÍO"),
            "Telefono": (22, "CAMBIO EN TELÉFONO"),
            "Celular": (23, "CAMBIO EN CELULAR"),
            "Correo": (24, "CAMBIO EN CORREO ELECTRÓNICO"),
        }

        # --- Motivos direcciones ADICIONALES ---
        motivos_adicional = {
            "Street": (32, "CAMBIO EN CALLE DIRECCIÓN ADICIONAL"),
            "ExtNumber": (33, "CAMBIO EN NÚMERO EXTERIOR DIRECCIÓN ADICIONAL"),
            "Comments": (34, "CAMBIO EN COMENTARIOS DE DIRECCIÓN ADICIONAL"),
            "ZipCode": (35, "CAMBIO EN CÓDIGO POSTAL DIRECCIÓN ADICIONAL"),
            "City": (36, "CAMBIO EN COLONIA DIRECCIÓN ADICIONAL"),
            "Municipality": (37, "CAMBIO EN MUNICIPIO DIRECCIÓN ADICIONAL"),
            "StateProvince": (38, "CAMBIO EN ESTADO DIRECCIÓN ADICIONAL"),
            "ZoneName": (39, "CAMBIO EN RUTA DE ENTREGA DIRECCIÓN ADICIONAL"),
            "DeliveryCost": (40, "CAMBIO EN COSTO DE ENVÍO DIRECCIÓN ADICIONAL"),
            "Telefono": (41, "CAMBIO EN TELÉFONO DIRECCIÓN ADICIONAL"),
            "Celular": (42, "CAMBIO EN CELULAR DIRECCIÓN ADICIONAL"),
            "Correo": (43, "CAMBIO EN CORREO ELECTRÓNICO DIRECCIÓN ADICIONAL"),
        }

        # Recorremos TODAS las direcciones que existían en backup
        for address_id, original in backup_por_id.items():
            nueva = actuales_por_id.get(address_id)

            # Si ya no existe en "actuales", aquí NO registramos nada aún
            # (lo manejarás como ELIMINACIÓN de dirección adicional con motivo 30
            #  en otra función, si aplica).
            if not nueva:
                continue

            is_main_original = original.get("IsMainAddress", 0)
            is_main_nueva = nueva.get("IsMainAddress", 0)

            # ¿Es fiscal?
            es_fiscal = (
                    is_main_original == 1
                    or is_main_nueva == 1
                    or (address_id != 0 and address_id == fiscal_detail_id_ref)
            )

            # Seleccionamos el mapa de motivos según si es fiscal o adicional
            mapa_motivos = motivos_fiscal if es_fiscal else motivos_adicional

            address_name = original.get("AddressName", "") or nueva.get("AddressName", "")

            # Comparar campo a campo
            for campo, (motivo_id, motivo_texto) in mapa_motivos.items():
                valor_anterior = original.get(campo)
                valor_nuevo = nueva.get(campo)

                # Normalización
                if valor_anterior is None:
                    valor_anterior = ""
                if valor_nuevo is None:
                    valor_nuevo = ""

                if isinstance(valor_anterior, str):
                    valor_anterior = valor_anterior.strip()
                if isinstance(valor_nuevo, str):
                    valor_nuevo = valor_nuevo.strip()

                # Si no cambió, no registramos
                if valor_anterior == valor_nuevo:
                    continue

                cambios.append({
                    "address_detail_id": address_id,
                    "es_fiscal": bool(es_fiscal),
                    "address_name": address_name,
                    "campo": campo,
                    "valor_anterior": str(valor_anterior),
                    "valor_nuevo": str(valor_nuevo),
                    "motivo": motivo_texto,
                    "motivo_id": motivo_id,
                    "usuario_id": usuario_id,
                })

        return cambios

    def _generar_bitacora_cambios_fiscales(self, cliente, usuario_id):
        """
        Compara los valores actuales del cliente vs los valores originales
        en cliente.consulta (la fila que vino de BD) y genera una lista de
        cambios para bitácora:

          - campo
          - valor_anterior
          - valor_nuevo
          - motivo
          - motivo_id
          - usuario_id

        Motivos:
          11 RFC
          12 Régimen fiscal
          20 Ruta de entrega
          25 Forma de pago CFDI
          26 Método de pago CFDI
          27 Uso CFDI
        """

        cambios = []

        # Si es un cliente nuevo (sin BusinessEntityID), no generamos bitácora fiscal
        beid = getattr(cliente, "business_entity_id", 0) or 0
        if beid == 0:
            return cambios

        # Diccionario original tal como vino de BD
        original = getattr(cliente, "consulta", None) or {}
        if not original:
            # Sin consulta original no tiene sentido comparar
            return cambios

        # Mapeo: (clave_en_consulta, attr_actual_en_cliente, motivo_id, motivo_texto)
        campos_fiscales = [
            ("OfficialNumber", "official_number", 11, "CAMBIO EN RFC"),
            ("CompanyTypeName", "company_type_name", 12, "CAMBIO EN RÉGIMEN FISCAL"),
            ("FormaPago", "forma_pago", 25, "CAMBIO EN FORMA DE PAGO CFDI"),
            ("MetodoPago", "metodo_pago", 26, "CAMBIO EN MÉTODO DE PAGO CFDI"),
            ("ReceptorUsoCFDI", "receptor_uso_cfdi", 27, "CAMBIO EN USO CFDI"),
            ("ZoneName", "zone_name", 20, "CAMBIO EN RUTA DE ENTREGA"),
        ]

        def _normalizar(v):
            if v is None:
                return ""
            if isinstance(v, str):
                return v.strip().upper()
            return str(v).strip().upper()

        for key_consulta, attr_cliente, motivo_id, motivo_texto in campos_fiscales:
            raw_anterior = original.get(key_consulta, "")
            raw_nuevo = getattr(cliente, attr_cliente, "")

            # normalizamos solo para comparar (evitar cambios por espacios/case)
            anterior_norm = _normalizar(raw_anterior)
            nuevo_norm = _normalizar(raw_nuevo)

            # Si no cambió, no registramos nada
            if anterior_norm == nuevo_norm:
                continue

            # Para guardar en bitácora, solo limpiamos espacios
            if isinstance(raw_anterior, str):
                raw_anterior = raw_anterior.strip()
            if isinstance(raw_nuevo, str):
                raw_nuevo = raw_nuevo.strip()

            cambios.append({
                "campo": attr_cliente,
                "valor_anterior": str(raw_anterior),
                "valor_nuevo": str(raw_nuevo),
                "motivo": motivo_texto,
                "motivo_id": motivo_id,
                "usuario_id": usuario_id,
            })

        return cambios

    def _registrar_bitacora_cambios_cliente(self, cliente, usuario_id, nombre_usuario):
        """
        Ejecuta el análisis de cambios (fiscales y direcciones) y registra
        cada cambio en zvwBitacoraCambiosClientesT usando el SP
        InsertarBitacoraCambiosClientes.

        Requiere:
        - generar_bitacora_cambios_fiscales(cliente, usuario_id)
        - generar_bitacora_cambios_direcciones(cliente, usuario_id)

        Cada cambio debe traer al menos:
          {
            "campo":          str,
            "valor_anterior": str,
            "valor_nuevo":    str,
            "motivo":         str,
            "motivo_id":      int,
            "usuario_id":     int,
            # opcional:
            "address_detail_id": int
          }
        """

        business_entity_id = getattr(cliente, "business_entity_id", 0) or 0
        if not business_entity_id:
            # Cliente nuevo sin BEID aún -> nada que registrar
            return

        # 1) Obtener cambios fiscales
        cambios_fiscales = self._generar_bitacora_cambios_fiscales(cliente, usuario_id)

        # 2) Obtener cambios en direcciones (fiscal + adicionales)
        cambios_direcciones = self._generar_bitacora_cambios_direcciones(cliente, usuario_id)

        # 3) Unificamos todos los cambios
        todos_los_cambios = []
        todos_los_cambios.extend(cambios_fiscales)
        todos_los_cambios.extend(cambios_direcciones)

        if not todos_los_cambios:
            return

        # 4) Insertar cada cambio usando el SP InsertarBitacoraCambiosClientes
        for cambio in todos_los_cambios:
            incidencia = cambio["motivo"]  # texto del motivo
            incidencia_id = cambio["motivo_id"]  # ID del motivo en la tabla de incidencias
            valor_anterior = cambio["valor_anterior"]
            valor_nuevo = cambio["valor_nuevo"]
            address_detail_id = cambio.get("address_detail_id", 0)

            # Por si acaso, normalizamos a string corto (el SP recibe VARCHAR(255))
            if valor_anterior is None:
                valor_anterior = ""
            if valor_nuevo is None:
                valor_nuevo = ""

            valor_anterior = str(valor_anterior)[:255]
            valor_nuevo = str(valor_nuevo)[:255]

            # Llamada al procedimiento almacenado
            self._modelo.base_de_datos.command(
                """
                EXEC InsertarBitacoraCambiosClientes
                    @incidencia         = ?,
                    @valor_anterior     = ?,
                    @valor_nuevo        = ?,
                    @nombre_usuario     = ?,
                    @business_entity_id = ?,
                    @incidencia_id      = ?,
                    @address_detail_id  = ?
                """,
                (
                    incidencia,
                    valor_anterior,
                    valor_nuevo,
                    nombre_usuario,
                    business_entity_id,
                    incidencia_id,
                    address_detail_id
                )
            )