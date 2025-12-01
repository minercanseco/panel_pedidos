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
            'cbx_colonia':  lambda event: self._rellenar_cbx_colonias_por_ruta(),
            'btn_cancelar': self._interfaz.master.destroy,
            #'btn_guardar': self._validar_inputs_formulario,
            'btn_copiar': self._buscar_informacion_direccion_whatsapp,
            #'btn_cif': self._actualizar_por_cif,
            'btn_nueva_direccion':self._agregar_direccion,
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
            f"🌎 *Estado:* {self._modelo.address_fiscal_state_province}\n\n"
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


