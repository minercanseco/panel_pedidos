import tkinter as tk

import pyperclip
from cayal.ventanas import Ventanas

class DireccionAdicional:
    def __init__(self, master,modelo, info_direccion, info_notebook):
        self.master = master

        self._ventanas = Ventanas(self.master)
        self.info_direccion =  info_direccion
        self.info_notebook = info_notebook


        self._modelo = modelo
        self._modelo.cliente.register_additional_address_instance(self)

        self._nombre_direccion = self.info_direccion.get('AddressName', '')
        self._address_detail_id = self.info_direccion['AddressDetailID']

        self._crear_frames()
        self._cargar_componentes()
        self._ajustar_ancho_componentes()
        self._agregar_componentes_notebook_a_ventanas(info_notebook)
        self._rellenar_componentes()
        self._bloquear_componentes()
        self._cargar_eventos()

    def _agregar_componentes_notebook_a_ventanas(self, info_notebook):

        nombre_note_book = info_notebook['nombre_notebook']
        nombre_tab = info_notebook['nombre_tab']

        tab_notebook = info_notebook['tab_notebook']
        notebook = info_notebook['notebook']
        self._ventanas.componentes_forma[nombre_note_book] = notebook
        self._ventanas.componentes_forma[nombre_tab] = tab_notebook

    def _registrar_en_ventanas(self, info_notebook):
        """
        Registra esta instancia de DireccionAdicional en Ventanas,
        usando el nombre_tab como clave.
        """
        nombre_tab = info_notebook['nombre_tab']  # ej. 'tab_direccion_sucursal_1'

        # Creamos el contenedor si no existe aún
        if not hasattr(self._ventanas, "_direcciones_adicionales"):
            self._ventanas._direcciones_adicionales = {}

        self._ventanas._direcciones_adicionales[nombre_tab] = self

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.W}),

            'frame_generales': ('frame_principal', f'Dirección {self._nombre_direccion}:',
                                  {'row': 0, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.W}),

            'frame_lbl_estado': ('frame_generales', None,
                                    {'row': 11, 'column': 1, 'sticky': tk.NSEW}),

            'frame_btn_domicilios': ('frame_generales', None,
                                 {'row': 12, 'column': 1, 'sticky': tk.NSEW}),

            'frame_domicilios': ('frame_generales', None,
                              {'row': 13, 'column': 0, 'columnspan': 2,  'padx': 5, 'pady': 5,  'sticky': tk.NSEW}),

            'frame_fiscal': ('frame_principal', 'Datos Fiscales:',
                              {'row': 0, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_fiscal1': ('frame_fiscal', None,
                             {'row': 40, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_botones': ('frame_principal', None,
                              {'row': 2, 'column': 0, 'sticky': tk.E}),

        }

        self._ventanas.crear_frames(frames)

    def _cargar_componentes(self):

        estilo_label = {
            'foreground': 'black',
            'background': 'white',
            'font': ('Consolas', 12, 'bold'),
            'text': '',
            'anchor': 'w'
        }

        posicion_label = {
            'sticky': tk.W, 'pady': 0, 'padx': 0,
        }

        componentes = {
            'tbx_nombre': ('frame_generales', None, 'Dirección:', None),
            'tbx_ncomercial': ('frame_generales', None, 'N.Comercial:', None),
            'tbx_telefono': ('frame_generales', None, 'Teléfono:', None),
            'tbx_celular': ('frame_generales', None, 'Celular:', None),
            'tbx_calle': ('frame_generales', None, 'Calle:', None),
            'tbx_numero': ('frame_generales', None, 'Número:', None),
            'txt_comentario': ('frame_generales', None, 'Comentarios:', None),
            'tbx_cp': ('frame_generales', None, 'CP:', None),
            'lbl_estado': ('frame_lbl_estado', estilo_label, posicion_label, None),
            'lbl_municipio': ('frame_lbl_estado', estilo_label, posicion_label, None),
            'cbx_colonia': ('frame_generales', None, 'Colonia:', None),

            'tbx_envio': ('frame_domicilios', None, 'Envío:          ', None),
            'cbx_ruta': ('frame_domicilios', None, 'Ruta:          ', None),

            'tbx_rfc': ('frame_fiscal', None, 'RFC:     ', None),
            'tbx_cif': ('frame_fiscal', None, 'CIF:     ', None),
            'cbx_regimen': ('frame_fiscal', None, 'Régimen:', None),
            'cbx_formapago': ('frame_fiscal', None, 'FormaPago:', None),
            'cbx_metodopago': ('frame_fiscal', None, 'MétodoPago:', None),
            'cbx_usocfdi': ('frame_fiscal', None, 'UsoCFDI:', None),
            'txt_correo': ('frame_fiscal', None, 'Email:', None),

            'btn_eliminar': ('frame_botones', 'danger', 'Eliminar', None),
            'btn_copiar': ('frame_botones', 'warning', 'Copiar', None),
        }

        self._ventanas.crear_componentes(componentes)

    def _ajustar_ancho_componentes(self):
        componentes = {
            # --- GENERALES ---
            'tbx_cliente':25,
            'tbx_ncomercial':25,
            'tbx_telefono': 0,
            'tbx_celular': 0,
            'tbx_calle': 25,
            'tbx_numero': 5,
            'txt_comentario': 35,
            'tbx_cp': 10,

            'tbx_envio': 5,
            'tbx_domicilios':5,
            'cbx_ruta': 30,

            # --- FISCAL ---
            'tbx_rfc': 0,
            'tbx_cif': 0,
            'btn_cif': 0,

            'cbx_colonia':30,
            'cbx_regimen': 30,
            'cbx_formapago': 30,
            'cbx_metodopago': 30,
            'cbx_usocfdi': 30,

            'txt_correo': 25,
        }

        for componente, valor in componentes.items():
            if valor == 0:
                continue

            self._ventanas.ajustar_ancho_componente(componente, valor)

    def _rellenar_componentes(self):
        componentes = {
            'tbx_nombre': 'AddressName',
            'tbx_ncomercial': 'ComercialName',
            'tbx_telefono': 'Telefono',
            'tbx_celular': 'Celular',
            'tbx_calle': 'Street',
            'tbx_numero': 'ExtNumber',
            'txt_comentario': 'Comments',
            'tbx_cp': 'ZipCode',

            'lbl_estado': 'StateProvince',
            'lbl_municipio': 'Municipality',
            'cbx_colonia': '',

            'tbx_envio': 'DeliveryCost',
            'cbx_ruta': '',

            'tbx_rfc': 'OfficialNumber',
            'tbx_cif': 'CIF',
            'cbx_regimen': '',
            'cbx_formapago': '',
            'cbx_metodopago': '',
            'cbx_usocfdi': '',
            'txt_correo': 'Correo',

        }
        for componente, clave in componentes.items():
            valor = self.info_direccion.get(clave, '')
            self._ventanas.insertar_input_componente(componente, valor)

        self._rellenar_componentes_fiscales()

    def _rellenar_componentes_fiscales(self):
        # ------------------------------------------------------------------------
        consultas = {
            'cbx_regimen': (self._modelo.obtener_regimenes_fiscales, self._modelo.cliente.company_type_name),
            'cbx_formapago': (self._modelo.obtener_formas_pago, self._modelo.cliente.forma_pago),
            'cbx_metodopago': (self._modelo.obtener_metodos_pago, self._modelo.cliente.metodo_pago),
            'cbx_usocfdi': (self._modelo.obtener_uso_cfdi, self._modelo.cliente.receptor_uso_cfdi),
        }

        for componente, (funcion_consulta, atributo) in consultas.items():
            consulta = funcion_consulta()
            valores = [reg['Value'] for reg in consulta]
            self._ventanas.rellenar_cbx(componente, valores)

            if componente == 'cbx_regimen':
                valor_seleccion = [reg['Value'] for reg in consulta if reg['Value'] == atributo]
            else:
                valor_seleccion = [reg['Value'] for reg in consulta if reg['Clave'] == atributo]

            if valor_seleccion:
                    self._ventanas.insertar_input_componente(componente, valor_seleccion[0])

        # ------------------------------------------------------------------------
        # rellenar cbx colonias
        info_colonias = self._modelo.obtener_colonias(self._address_detail_id)
        colonias = [reg['City'] for reg in info_colonias]
        colonias = sorted(colonias)
        self._ventanas.rellenar_cbx('cbx_colonia', colonias)
        if self._modelo.cliente.business_entity_id != 0:
            self._ventanas.insertar_input_componente('cbx_colonia',
                                                              self.info_direccion.get('City', '')
                                                              )
        # ------------------------------------------------------------------------
        # rellenar cbx rutas
        info_rutas = self._modelo.obtener_todas_las_rutas()
        rutas = [reg['ZoneName'] for reg in info_rutas]
        rutas = sorted(rutas)
        self._ventanas.rellenar_cbx('cbx_ruta', rutas)
        if self._modelo.business_entity_id != 0:
            self._ventanas.insertar_input_componente('cbx_ruta',
                                                              self._modelo.cliente.zone_name
                                                              )
        # ------------------------------------------------------------------------

    def _bloquear_componentes(self):
        componentes = [
            'tbx_ncomercial',
            'tbx_envio',
            'cbx_ruta',
            'tbx_rfc',
            'tbx_cif',
            'cbx_regimen',
            'cbx_formapago',
            'cbx_metodopago',
            'cbx_usocfdi'
        ]
        for componente in componentes:
            self._ventanas.bloquear_componente(componente)

    def _cargar_eventos(self):
        eventos = {
            'btn_copiar': self._copiar_info_direccion,
            'btn_eliminar': self._eliminar_direccion,
            'tbx_cp': lambda event: self._rellenar_cbx_colonias_por_cp(),
            'cbx_colonia':  lambda event: self._eventos_cbx_colonia(),

        }
        self._ventanas.cargar_eventos(eventos)

    def _eliminar_direccion(self):
        notebook = self.info_notebook['notebook']  # widget ttk.Notebook
        frame_contenido = self.info_notebook['tab_notebook']  # frm_xxx (donde está la UI)

        self._ventanas.eliminar_pestana_por_frame(notebook, frame_contenido)
        self._modelo.cliente.deleted_addresses.append(self._address_detail_id)

    def _buscar_informacion_direccion_whatsapp(self):
        funcion = self._ventanas.obtener_input_componente
        mensaje = (
            f"📍 ¿Podría confirmar si los datos de su dirección son correctos?  \n\n"
            f"👤 *Cliente:* {self._modelo.cliente.official_name}\n"
            f"📍 *Dirección del cliente* ({funcion('tbx_nombre')})\n"
            f"🏠 *Calle:* {funcion('tbx_calle')}\n"
            f"🔢 *Número:* {funcion('tbx_numero')}\n"
            f"📮 *C.P.:* {funcion('tbx_cp')}\n"
            f"🏘️ *Colonia:* {funcion('cbx_colonia')}\n"
            f"🏙️ *Municipio:* {funcion('lbl_municipio')}\n"
            f"🌎 *Estado:* {funcion('lbl_estado')}\n\n"
            f"📞 *Teléfono:* {funcion('tbx_telefono')}\n"
            f"📱 *Celular:* {funcion('tbx_celular')}\n\n"
            f"📝 *Comentarios:* {funcion('txt_comentario')}\n"
            f"🚚💸 *Envío a domicilio:* ${funcion('tbx_envio')} (En compras menores a 200)\n"
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

    def _rellenar_cbx_colonias_por_cp(self):
        cp = self._ventanas.obtener_input_componente('tbx_cp')
        if not self._modelo.utilerias.es_codigo_postal(cp):
            return

        consulta = self._modelo.obtener_colonias(zip_code=cp)
        colonias = [reg['City'] for reg in consulta]
        colonias = sorted(colonias)
        self._ventanas.rellenar_cbx('cbx_colonia', colonias)

    def _rellenar_cbx_colonias_por_ruta(self):
        if self._ventanas.obtener_input_componente('cbx_colonia') != 'Seleccione':
            return

        consulta = self._modelo.obtener_colonias()
        colonias = [reg['City'] for reg in consulta]
        colonias = sorted(colonias)
        self._ventanas.rellenar_cbx('cbx_colonia', colonias)

    def _actualizar_municipio_y_estado(self):
        colonia = self._ventanas.obtener_input_componente('cbx_colonia')
        if colonia == 'Seleccione':
            return

        estado, municipio = self._modelo.obtener_estado_y_municipio_colonia(colonia)
        self._ventanas.insertar_input_componente('lbl_estado', estado)
        self._ventanas.insertar_input_componente('lbl_municipio', municipio)

    def _rellenar_costo_envio(self):
        colonia = self._ventanas.obtener_input_componente('cbx_colonia')
        if colonia == 'Seleccione':
            return

        monto_envio = self._modelo.obtener_envio_por_colonia(colonia)
        self._ventanas.insertar_input_componente('tbx_envio', monto_envio)
        self._ventanas.bloquear_componente('tbx_envio')

    def _rellenar_cp_por_colonia(self):
        colonia = self._ventanas.obtener_input_componente('cbx_colonia')
        if colonia == 'Seleccione':
            return

        self._actualizar_municipio_y_estado()
        municipio = self._ventanas.obtener_input_componente('lbl_municipio')
        municipio = 'Campeche' if not municipio else municipio.strip()

        estado = self._ventanas.obtener_input_componente('lbl_estado')
        estado = 'Campeche' if not estado else estado.strip()

        cp = self._modelo.obtener_cp_por_colonia(colonia, estado, municipio)
        self._ventanas.insertar_input_componente('tbx_cp', cp)

    def _eventos_cbx_colonia(self):
        self._rellenar_cbx_colonias_por_ruta()
        self._rellenar_costo_envio()
        self._rellenar_cp_por_colonia()

    def _obtener_parametros_direccion_adicional(self):
        self._rellenar_cp_por_colonia()

        componentes = {
            'tbx_nombre': 'AddressName',
            'tbx_telefono': 'Telefono',
            'tbx_celular': 'Celular',
            'tbx_calle': 'Street',
            'tbx_numero': 'ExtNumber',
            'txt_comentario': 'Comments',
            'tbx_cp': 'ZipCode',
            'lbl_estado': 'StateProvince',
            'lbl_municipio': 'Municipality',
            'cbx_colonia': 'City',
            'cbx_ruta': 'ZoneName',
            'txt_correo': 'Correo',
        }

        for componente, clave in componentes.items():
            if clave:
                valor = self._ventanas.obtener_input_componente(componente)
                self.info_direccion[clave] = valor

        info_colonia = self._modelo.obtener_info_colonia(
            self._ventanas.obtener_input_componente('cbx_colonia'),
            self._ventanas.obtener_input_componente('lbl_estado'),
            self._ventanas.obtener_input_componente('lbl_municipio')
        )
        self.info_direccion['StateProvinceCode'] = info_colonia.get('StateProvinceCode','')
        self.info_direccion['MunicipalityCode'] = info_colonia.get('MunicipalityCode', '')
        self.info_direccion['CityCode'] = info_colonia.get('CityCode', '')

        return self.info_direccion

    def cargar_direccion_en_cliente(self):
        info_procesada = self._obtener_parametros_direccion_adicional()
        self._modelo.cliente.add_address_detail(info_procesada)

    def existe_frame(self):
        """
        Retorna True si el frame asociado a esta dirección sigue existiendo.
        Si la pestaña fue eliminada y el frame destruido, será False.
        """
        try:
            # Usa el master que recibiste en __init__ (o tab_notebook, lo que te funcione mejor)
            frame = self.master  # o: frame = self.info_notebook['tab_notebook']

            return bool(frame and frame.winfo_exists())
        except Exception:
            return False
