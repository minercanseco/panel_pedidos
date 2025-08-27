import tkinter as tk
import unicodedata
import pyperclip
import ttkbootstrap as ttk
import ttkbootstrap.dialogs

from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.cliente import Cliente
from cayal.ventanas import Ventanas
from cayal.documento import Documento
from cayal.util import Utilerias

from llamar_instancia_captura import LlamarInstanciaCaptura


class BuscarGeneralesCliente:

    def __init__(self, master, parametros):

        self._parametros_contpaqi = parametros

        self._master = master
        self._declarar_variables_globales()
        self._crear_instancias_de_clases()

        self._crear_frames()
        self._cargar_componentes_forma()
        self._cargar_eventos_componentes_forma()
        self._cargar_hotkeys()
        self._ajustar_componentes()
        self._actualizar_apariencia_forma(solo_apariencia_inicial=True)
        self._ventanas.configurar_ventana_ttkbootstrap('Seleccionar cliente')
        self._ventanas.enfocar_componente('tbx_buscar')

    def _declarar_variables_globales(self):
        self._cadena_conexion = self._parametros_contpaqi.cadena_conexion
        self._termino_buscado = None
        self._consulta_clientes = None
        self._info_cliente_seleccionado = None
        self._consulta_direcciones = None
        self._instancia_llamada = False
        self._consulta_sucursales = None
        self._procesando_documento = False
        self._tipo_documento = 0

    def _crear_instancias_de_clases(self):
        self._base_de_datos = ComandosBaseDatos(self._cadena_conexion)
        self._cliente = Cliente()
        self._ventanas = Ventanas(self._master)
        self._documento = Documento()
        self._utilerias = Utilerias()

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_buscar': ('frame_principal', 'Buscar cliente:',
                                      {'row': 0, 'columnspan': 4, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_botones': ('frame_buscar', None,
                              {'row': 2, 'column': 1,  'pady': 5, 'sticky': tk.NSEW}),

            'frame_data': ('frame_principal', 'Información:',
                           {'row': 3, 'column': 0, 'columnspan': 8, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_cbxs': ('frame_data', None,
                              {'row': 0, 'column': 0,  'columnspan': 4, 'pady': 5, 'sticky': tk.W}),

            'frame_cbx_direccion': ('frame_cbxs', 'Dirección:',
                               {'row': 0, 'column': 1,  'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_cbx_documento': ('frame_cbxs', 'Documento:',
                               {'row': 0, 'column': 2, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_informacion': ('frame_data', 'Generales:',
                                  {'row': 1, 'column': 0, 'columnspan': 2, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_direccion': ('frame_data', 'Detalles dirección:',
                                {'row': 1, 'column': 2, 'columnspan': 2, 'padx': 5, 'pady': 5, 'sticky': tk.NS}),

            'frame_copiar_direccion': ('frame_direccion', None,
                                       {'row': 11, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}),

        }

        self._ventanas.crear_frames(frames)

    def _cargar_componentes_forma(self):

        componentes = {
            'tbx_buscar': ('frame_buscar', None, 'Buscar:', None),
            'cbx_resultados': ('frame_buscar', None, '  ', None),

            'cbx_direccion': ('frame_cbx_direccion',
                              {'row': 0, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W},
                              '[Ctrl+T]', None),
            'cbx_documento': ('frame_cbx_documento',
                              {'row': 0, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W},
                              'Ctrl+D', None ),
            'btn_seleccionar': ('frame_botones', 'primary', 'Seleccionar', '[F1]'),
            'btn_cancelar': ('frame_botones', 'danger', 'Cancelar', '[Esc]'),

        }
        self._ventanas.crear_componentes(componentes)

        self._componentes_direccion = {

            'lbl_txt_ncomercial': ('frame_direccion',  None, 'N.Comercial:', None),
            'lbl_txt_ruta': ('frame_direccion', None, 'Ruta:', None),
            'lbl_txt_telefono': ('frame_direccion', None, 'Teléfono:', None),
            'lbl_txt_celular': ('frame_direccion', None, 'Celular:', None),
            'lbl_txt_calle': ('frame_direccion', None, 'Calle:', None),
            'lbl_txt_numero': ('frame_direccion', None, 'Número:', None),
            'txt_comentario': ('frame_direccion', None, 'Comentario:', None),
            'lbl_txt_cp': ('frame_direccion', None, 'C.P.', None),
            'lbl_txt_colonia': ('frame_direccion', None, 'Colonia:', None),
            'lbl_txt_estado': ('frame_direccion', None, 'Estado:', None),
            'lbl_txt_municipio': ('frame_direccion', None, 'Municipio:', None),

            'lbl_ncomercial': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                               {'row': 0, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            'lbl_ruta': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                         {'row': 1, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            'lbl_telefono': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                             {'row': 2, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            'lbl_celular': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                            {'row': 3, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            'lbl_calle': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                          {'row': 4, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            'lbl_numero': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                           {'row': 5, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            'lbl_cp': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                       {'row': 7, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            'lbl_colonia': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                            {'row': 8, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            'lbl_estado': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                           {'row': 9, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            'lbl_municipio': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                              {'row': 10, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            'btn_copiar': ('frame_copiar_direccion', 'warning', 'Copiar', '[F4]'),
        }
        self._ventanas.crear_componentes(self._componentes_direccion)

        self._componentes_credito = {
            'lbl_txt_nombre': ('frame_informacion', None, 'Nombre:', None),
            'lbl_txt_rfc': ('frame_informacion', None, 'RFC:', None),
            #'lbl_txt_ruta': ('frame_informacion', None, 'Ruta:', None),
            'lbl_txt_autorizado': ('frame_informacion', None, 'Autorizado:', None),
            'lbl_txt_debe': ('frame_informacion', None, 'Debe:', None),
            'lbl_txt_restante': ('frame_informacion', None, 'Restante:', None),
            'lbl_txt_condicion': ('frame_informacion', None, 'Condición:', None),
            'lbl_txt_pcompra': ('frame_informacion', None, 'P.Compra:', None),
            'lbl_txt_comentario': ('frame_informacion', None, 'Comentario:', None),
            'lbl_txt_minisuper': ('frame_informacion', None, 'Minisuper:', None),
            'lbl_txt_lista': ('frame_informacion', None, 'Lista:', None),

            'lbl_nombre': ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                           {'row': 0, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            'lbl_rfc': ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                        {'row': 1, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            #'lbl_ruta': ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
            #             {'row': 2, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            'lbl_autorizado': ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                               {'row': 2, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            'lbl_debe': ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                         {'row': 3, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            'lbl_restante': ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                             {'row': 4, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            'lbl_condicion': (
            'frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
            {'row': 5, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            'lbl_pcompra': ('frame_informacion', {'font': ('Arial', 9, 'bold'),
                                                  'text': ''},
                            {'row': 6, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            'lbl_comentario': ('frame_informacion', {'font': ('Arial', 9, 'bold'),
                                                     'text': ''},
                               {'row': 7, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            'lbl_minisuper': ('frame_informacion', {'font': ('Arial', 9, 'bold'),
                                                    'text': ''},
                              {'row': 8, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),

            'lbl_lista': ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                          {'row': 9, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}, None),
        }
        self._ventanas.crear_componentes(self._componentes_credito)

    def _ajustar_componentes(self):
        self._ventanas.ajustar_ancho_componente('cbx_resultados', 50)
        self._ventanas.bloquear_componente('btn_seleccionar')

    def _cargar_eventos_componentes_forma(self):
        eventos = {
            'btn_cancelar': self._master.destroy,
            'btn_seleccionar': self._seleccionar_cliente,
            'tbx_buscar': self._buscar_cliente,
            'cbx_resultados': self._cambio_de_seleccion_cliente,
            'cbx_direccion': self._seleccionar_direccion,
            'btn_copiar':self._copiar_informacion_direccion
        }

        self._ventanas.cargar_eventos(eventos)

    def _cargar_hotkeys(self):
        hotkeys = {
            'F1': self._seleccionar_cliente,
            'F4': self._copiar_informacion_direccion
        }

        self._ventanas.agregar_hotkeys_forma(hotkeys)

    def _copiar_informacion_direccion(self):
        business_entity_id = self._info_cliente_seleccionado[0]['BusinessEntityID']
        address_detail_id = self._documento.address_detail_id

        informacion = self._base_de_datos.buscar_informacion_direccion_whatsapp(address_detail_id, business_entity_id)
        pyperclip.copy(informacion)
        self._master.iconify()

    def _buscar_cliente(self, event=None):

        tbx_buscar = self._ventanas.componentes_forma['tbx_buscar']
        termino_buscado = tbx_buscar.get()
        btn_seleccionar = self._ventanas.componentes_forma['btn_seleccionar']

        if not termino_buscado:
            ttkbootstrap.dialogs.Messagebox.show_error(parent=self._master,message='Debe introducir un termino a buscar')
            btn_seleccionar.config(state='disabled')

        elif len(termino_buscado) < 5:
            ttkbootstrap.dialogs.Messagebox.show_error(parent = self._master,message='Insuficientes letras en el termino a buscar')
            btn_seleccionar.config(state='disabled')

        elif termino_buscado != self._termino_buscado:
            self._termino_buscado = termino_buscado

            self._consulta_clientes = self._base_de_datos.buscar_clientes_por_nombre_similar(self._termino_buscado)

            nombres_clientes = [reg['OfficialName'] for reg in self._consulta_clientes]

            if not nombres_clientes:
                btn_seleccionar.config(state='disabled')
                self._ventanas.rellenar_cbx('cbx_resultados', None, 'sin seleccione')
                ttkbootstrap.dialogs.Messagebox.show_error(parent=self._master, message='No se encontraron resultados.')
            else:
                if len(nombres_clientes) > 1:
                    self._ventanas.rellenar_cbx('cbx_resultados', nombres_clientes)
                else:
                    self._ventanas.rellenar_cbx('cbx_resultados', nombres_clientes, 'sin seleccione')
                    cliente = nombres_clientes[0]
                    business_entity_id = self._buscar_busines_entity_id(cliente)
                    self._buscar_info_cliente_seleccionado(business_entity_id)

                    self._cliente.consulta = self._info_cliente_seleccionado
                    self._cliente.settear_valores_consulta()
                    self._actualizar_apariencia_forma()

                btn_seleccionar.config(state='enabled')
                self._ventanas.enfocar_componente('cbx_resultados')

    def _cambio_de_seleccion_cliente(self, event=None):
        seleccion = self._ventanas.obtener_input_componente('cbx_resultados')

        if seleccion == 'Seleccione':
            self._cliente.reinicializar_atributos()
            self._ventanas.mostrar_mensaje(mensaje= 'Debe seleccionar un cliente de la lista', master=self._master)
            self._ventanas.bloquear_componente('btn_seleccionar')
            return

        self._ventanas.desbloquear_componente('btn_seleccionar')
        business_entity_id = self._buscar_busines_entity_id(seleccion)
        self._buscar_info_cliente_seleccionado(business_entity_id)
        self._cliente.consulta = self._info_cliente_seleccionado
        self._cliente.settear_valores_consulta()

        self._actualizar_apariencia_forma()

    def _buscar_busines_entity_id(self, cliente):
        business_entity_id = [valor['BusinessEntityID'] for valor in self._consulta_clientes if valor['OfficialName'] == cliente]
        business_entity_id = business_entity_id[0]

        return business_entity_id if business_entity_id else 0

    def _buscar_info_cliente_seleccionado(self, business_entity_id):
        if business_entity_id != 0:
            self._info_cliente_seleccionado = self._base_de_datos.fetchall("""
              SELECT * FROM [dbo].[zvwBuscarInfoCliente-BusinessEntityID](?)
            """, (business_entity_id,))

    def _seleccionar_cliente(self):
        seleccion = self._ventanas.obtener_input_componente('cbx_resultados')

        if not seleccion:
            self._ventanas.mostrar_mensaje(master =self._master, mensaje='Debe buscar y seleccionar un cliente.')
        elif seleccion == 'Seleccione':
            self._ventanas.mostrar_mensaje(master=self._master, mensaje='Debe seleccionar un cliente de la lista.')
        else:
            proceder = True

            if self._cliente.depots > 0:
                seleccion_direccion = self._ventanas.obtener_input_componente('cbx_direccion')
                seleccion_direccion = seleccion_direccion.upper()

                if seleccion_direccion == 'DIRECCIÓN FISCAL' or not seleccion_direccion:
                    respuesta = ttk.dialogs.Messagebox.yesno(parent =self._master, message='El cliente tiene sucursales '
                                                            '¿Desea proceder sin seleccionar una?')
                    if respuesta == 'No':
                        proceder = False

            if proceder:
                self._llamar_instancia()

    def _documento_seleccionado(self):

        def es_remision():
            self._documento.cfd_type_id = 1
            self._documento.doc_type = 'REMISIÓN'

        def es_factura():
            self._documento.cfd_type_id = 0
            self._documento.doc_type = 'FACTURA'

        if self._cliente.cayal_customer_type_id in (0, 1):
            es_remision()
            return True
        else:
            seleccion = self._ventanas.obtener_input_componente('cbx_documento')

            if seleccion == 'Seleccione':
                ttkbootstrap.dialogs.Messagebox.show_error(parent=self._master, message='Debe seleccionar un tipo de documento.')
                return False

            es_factura() if seleccion == 'Factura' else es_remision()
            return True

    def _procesar_direccion_seleccionada(self):

        def normalizar(texto):
            """Elimina acentos y convierte a minúsculas."""
            texto = unicodedata.normalize('NFD', texto)
            texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
            return texto.lower()

        # Obtener nombre de dirección del componente
        address_name = self._ventanas.obtener_input_componente('cbx_direccion')

        # Normaliza el texto para comparación
        address_name_normalizado = normalizar(address_name)

        # Verifica si contiene "direccion fiscal"
        if 'direccion fiscal' in address_name_normalizado:

            address_fiscal_detail_id = self._info_cliente_seleccionado[0].get('AddressFiscalDetailID', 0)
            address_selected = [reg for reg in self._consulta_direcciones
                            if reg['AddressDetailID'] == address_fiscal_detail_id]

            if address_selected:
                self._seleccionar_direccion_fiscal(address_selected)

                # esto pr
                self._base_de_datos.homologar_direccion_fiscal(address_fiscal_detail_id)
                return address_selected[0]

        return self._base_de_datos.procesar_direccion_seleccionada_cbx(address_name, self._consulta_direcciones)

    def _actualizar_apariencia_si_tiene_sucursales(self):

        if self._cliente.depots == 0:
            self._ventanas.ocultar_componente('cbx_sucursales')
            self._consulta_sucursales = None
        else:
            frame_buscar = self._ventanas.componentes_forma['frame_buscar']
            cbx_sucursales = ttk.Combobox(frame_buscar, state='readonly')
            cbx_sucursales.grid(row=2,  column=1, padx=185, pady=5, sticky=tk.W)
            self._ventanas.componentes_forma['cbx_sucursales'] = cbx_sucursales

            self._consulta_sucursales = self._base_de_datos.fetchall("""
                    SELECT A.DepotID,A.DepotName 
            		FROM orgBusinessEntity E INNER JOIN
            			orgDepot A ON E.BusinessEntityID=A.BusinessEntityID 
            		WHERE E.BusinessEntityID = ? AND A.DeletedOn IS NULL
                    """, (self._cliente.business_entity_id,))

            nombres_sucursales = [sucursal['DepotName'] for sucursal in self._consulta_sucursales]

            if self._consulta_sucursales:
                self._ventanas.rellenar_cbx('cbx_sucursales', nombres_sucursales)

    def _actualizar_apariencia_forma(self, solo_apariencia_inicial = False):

        def apariencia_inicial():
            self._ventanas.ocultar_frame('frame_data')


        if solo_apariencia_inicial:
            apariencia_inicial()
            self._master.place_window_center()
            #self._master.after_idle(lambda: self._ventanas.centrar_ventana_ttkbootstrap(self._master))
            return

        cbx_direccion = self._ventanas.componentes_forma['cbx_direccion']

        if self._cliente.cayal_customer_type_id in (1, 2):
            self._ventanas.posicionar_frame('frame_data')
            self._ventanas.posicionar_frame('frame_informacion')
            self._ventanas.posicionar_frame('frame_direccion')
            self._cargar_info_credito()
        else:
            self._ventanas.posicionar_frame('frame_data')
            self._ventanas.ocultar_frame('frame_informacion')
            posicion = {'row': 1, 'column': 0, 'columnspan': 2, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}
            self._ventanas.posicionar_frame('frame_direccion', posicion)

        self._consulta_direcciones = self._base_de_datos.rellenar_cbx_direcciones(
            self._cliente.business_entity_id,
            cbx_direccion
        )
        self._rellenar_cbx_documento()
        self._seleccionar_direccion()

        self._master.place_window_center()

        #self._master.after_idle(lambda: self._ventanas.centrar_ventana_ttkbootstrap(self._master))

    def _rellenar_cbx_documento(self):
        if self._cliente.cayal_customer_type_id == 2:
            tipos_documento = ['Remisión', 'Factura']
            self._ventanas.rellenar_cbx('cbx_documento', tipos_documento)
        else:
            self._ventanas.mostrar_componente('cbx_documento')
            tipos_documento = ['Remisión']
            self._ventanas.rellenar_cbx('cbx_documento', tipos_documento, sin_seleccione=True)

    def _seleccionar_direccion(self, event=None):
        direccion = {}

        self._ventanas.posicionar_frame('frame_cbxs')
        self._ventanas.mostrar_componente('cbx_direccion')

        if self._cliente.addresses == 1:
            direccion = self._seleccionar_direccion_fiscal(direccion)
        else:
            datos_direccion = self._procesar_direccion_seleccionada()
            address_detail_id = datos_direccion.get('address_detail_id', 0)
            direccion = self._base_de_datos.buscar_detalle_direccion_formateada(address_detail_id)
            direccion['celular'] = self._info_cliente_seleccionado[0]['CellPhone']

        self._documento.address_details = direccion
        self._documento.address_detail_id = direccion.get('address_detail_id', 0)
        self._cargar_info_direccion(direccion)

    def _seleccionar_direccion_fiscal(self, direccion):

        if isinstance(direccion, list):
            direccion = direccion[0]

        direccion['address_detail_id'] = self._cliente.address_fiscal_detail_id
        direccion['address_name'] = 'Dirección Fiscal'
        direccion['depot_id'] = 0
        direccion['telefono'] = self._cliente.phone
        direccion['celular'] = self._cliente.cellphone
        direccion['calle'] = self._cliente.address_fiscal_street
        direccion['numero'] = self._cliente.address_fiscal_ext_number
        direccion['comentario'] = self._cliente.address_fiscal_comments
        direccion['cp'] = self._cliente.address_fiscal_zip_code
        direccion['colonia'] = self._cliente.address_fiscal_city
        direccion['estado'] = self._cliente.address_fiscal_state_province
        direccion['municipio'] = self._cliente.address_fiscal_municipality

        return direccion

    def _cargar_info_direccion(self, info_direccion):
        self._limpiar_direccion()
        self._ventanas.posicionar_frame('frame_direccion')

        informacion = {
            'lbl_ncomercial': self._cliente.commercial_name,
            'lbl_ruta': self._cliente.zone_name,
            'lbl_telefono': info_direccion.get('telefono', ''),
            'lbl_celular': info_direccion.get('celular', ''),
            'lbl_calle': info_direccion.get('calle', ''),
            'lbl_numero': info_direccion.get('numero', ''),
            'lbl_cp': info_direccion.get('cp', ''),
            'lbl_colonia': info_direccion.get('colonia', ''),
            'lbl_estado': info_direccion.get('estado', ''),
            'lbl_municipio': info_direccion.get('municipio', ''),
            'txt_comentario': info_direccion.get('comentario','')
        }

        for nombre_componente, valores in self._componentes_direccion.items():
            if '_txt' in nombre_componente:
                continue

            valor_direccion = informacion.get(nombre_componente, '')
            self._ventanas.insertar_input_componente(nombre_componente, valor_direccion)

    def _cargar_info_credito(self):
        self._limpiar_formulario()
        informacion = {
            'lbl_nombre': self._cliente.official_name,
            'lbl_rfc': self._cliente.official_number,
            'lbl_ruta': self._cliente.zone_name,
            'lbl_autorizado': self._credito_autorizado(),
            'lbl_debe': self._documentos_en_cartera(),
            'lbl_restante': self._credito_restante(),
            'lbl_condicion': self._cliente.payment_term_name,
            'lbl_pcompra': self._ultimo_documento_en_cartera(self._cliente.business_entity_id),
            'lbl_comentario': self._cliente.credit_comments,
            'lbl_minisuper': self._credito_en_super(),
            'lbl_lista': self._cliente.customer_type_name,
        }
        for nombre_componente, valores in self._componentes_credito.items():
            if '_txt' in nombre_componente:
                continue

            valor_direccion = informacion.get(nombre_componente, '')
            self._ventanas.insertar_input_componente(nombre_componente, valor_direccion)

    def _limpiar_formulario(self):
        componentes = ['lbl_ncomercial','lbl_nombre',  'lbl_rfc', 'lbl_ruta', 'lbl_autorizado', 'lbl_debe', 'lbl_restante',
                       'lbl_condicion','lbl_pcompra', 'lbl_comentario', 'lbl_minisuper', 'lbl_lista',
                       'lbl_telefono', 'lbl_celular', 'lbl_calle', 'lbl_numero','lbl_cp',
                       'lbl_estado','lbl_municipio'
                       ]
        self._ventanas.limpiar_componentes(componentes)

    def _limpiar_direccion(self):
        componentes = [ 'lbl_calle', 'lbl_numero', 'lbl_cp', 'lbl_telefono', 'lbl_celular',
                       'lbl_estado', 'lbl_municipio', 'lbl_colonia', 'lbl_ncomercial'
                       ]
        self._ventanas.limpiar_componentes(componentes)

    def _credito_en_super(self):
        text = 'NO TIENE CRÉDITO EN MINISUPER'

        if self._cliente.store_credit == 1:
            if self._cliente.credit_block == 1:
                text = 'NO TIENE CRÉDITO EN MINISUPER'

            else:
                text = 'CRÉDITO EN MINISUPER PERMITIDO'

        return text

    def _credito_autorizado(self):
        text = f'${self._cliente.authorized_credit}'

        if self._cliente.credit_block == 1:
            text = '$0.00'
        return text

    def _credito_restante(self):
        text = f'${self._cliente.remaining_credit}'

        if self._cliente.credit_block == 1:
            text = '$0.00'
        return text

    def _documentos_en_cartera(self):
        texto = ''
        if self._cliente.documents_with_balance > 0:
            texto = f'Debe ${self._cliente.debt} en {self._cliente.documents_with_balance} documentos.'
        else:
            texto = f'${self._cliente.debt}'
        return texto

    def _ultimo_documento_en_cartera(self, business_entity_id):
        info_ultimo_folio = self._base_de_datos.fetchall("""
            WITH CTE AS (
            SELECT 
                D.DocumentID,
                CAST(D.CreatedOn AS date) AS Fecha,
                CASE WHEN D.chkCustom1 = 1 THEN 'Remisión' ELSE 'Factura' END AS TipoDocto,
                ISNULL(D.FolioPrefix, '') + ISNULL(D.Folio, '') AS Folio,
                CFD.FormaPago AS FP,
                FORMAT(D.Total, 'C', 'es-MX') AS Total,
                FORMAT(D.TotalPaid, 'C', 'es-MX') AS Pagado,
                FORMAT(D.Balance, 'C', 'es-MX') AS Saldo,
                CASE WHEN A.DepotName IS NULL THEN '' ELSE A.DepotName END AS Sucursal
            FROM 
                docDocument D
                INNER JOIN docDocumentExtra X ON D.DocumentID = X.DocumentID
                LEFT OUTER JOIN orgDepot A ON X.BusinessEntityDepotID = A.DepotID
                INNER JOIN docDocumentCFD CFD ON D.DocumentID = CFD.DocumentID
                INNER JOIN vwcboAnexo20v33_FormaPago FP ON CFD.FormaPago = FP.Clave
            WHERE 
                D.CancelledOn IS NULL
                AND D.StatusPaidID <> 1
                AND D.BusinessEntityID = ?
                AND D.ModuleID IN (21, 1400, 1319)
                AND D.Balance <> 0
        )
        SELECT 
            MIN(D.DocumentID) AS DocumentID,
            D.Fecha,
            D.TipoDocto,
            D.Folio,
            D.FP,
            D.Total,
            D.Pagado,
            D.Saldo,
            D.Sucursal,
            DATEDIFF(DAY, D.Fecha, GETDATE()) AS Dias  -- Calcula la diferencia en días
        FROM 
            CTE D
        WHERE 
            D.DocumentID = (SELECT MIN(DocumentID) FROM CTE)
        GROUP BY 
            D.Fecha, D.TipoDocto, D.Folio, D.FP, D.Total, D.Pagado, D.Saldo, D.Sucursal

        """, (business_entity_id,))

        texto = ''

        if info_ultimo_folio:
            info_ultimo_folio = info_ultimo_folio[0]
            folio = info_ultimo_folio['Folio']
            saldo = info_ultimo_folio['Saldo']
            dias = info_ultimo_folio['Dias']

            texto = f'{folio}, saldo: {saldo}, hace {dias} días.'


        return texto

    def _llamar_instancia(self):

        if not self._instancia_llamada and self._documento_seleccionado():

            self._instancia_llamada = True

            # asignamos parámetros del cliente
            self._cliente.consulta = self._info_cliente_seleccionado
            self._cliente.settear_valores_consulta()

            # asignamos parámetros al documento
            self._asignar_parametros_a_documento()

            if self._parametros_contpaqi.id_principal == -1:
                self._parametros_contpaqi.nombre_usuario = self._base_de_datos.buscar_nombre_de_usuario(
                    self._parametros_contpaqi.id_usuario
                )

            # 1) Oculta la ventana origen ANTES de crear el popup (evita parpadeos y ventanas “huérfanas”)
            try:
                self._master.withdraw()
            except Exception:
                pass

            # 2) Crea el popup como hijo del master (NO crees una nueva raíz)
            raiz = getattr(self._ventanas, "_master", None) or self._master
            ventana = self._ventanas.crear_popup_ttkbootstrap(
                master=raiz,
                titulo="Capturar pedido",
                ocultar_master=False,  # ⬅️ la raíz ya está withdraw
                ejecutar_al_cierre=None,
                preguntar=None
            )

            # 3) Configura el popup correctamente
            try:
                ventana.transient(self._master)  # se comporta como diálogo
                #ventana.grab_set()  # foco modal
                ventana.focus_force()
                ventana.lift()
            except Exception:
                pass

            # 4) Qué pasa al cerrar el popup:
            #    Opción A: cerrar todo (popup + ventana de búsqueda)
            def _cerrar_todo():
                try:
                    ventana.destroy()
                finally:
                    # si quieres matar la búsqueda al cerrar captura:
                    try:
                        self._master.destroy()
                    except Exception:
                        pass

            #    Opción B (alternativa): restaurar la búsqueda en lugar de destruirla:
            # def _cerrar_todo():
            #     try:
            #         ventana.destroy()
            #     finally:
            #         try:
            #             self._master.deiconify()
            #             self._ventanas.centrar_ventana_ttkbootstrap(self._master)
            #         except Exception:
            #             pass

            try:
                ventana.protocol("WM_DELETE_WINDOW", _cerrar_todo)
            except Exception:
                pass

            # 5) Instancia la UI de captura usando el popup como master
            instancia = LlamarInstanciaCaptura(
                self._cliente,
                self._documento,
                self._base_de_datos,
                self._parametros_contpaqi,
                self._utilerias,
                ventana
            )

            # 6) Si tu flujo necesita esperar a que cierre la captura para seguir:
            # ventana.wait_window()
            # _cerrar_todo()

    def _asignar_parametros_a_documento(self):

        # las propiedades  self._doc_type | self._cfd_type_id son aginadas por la funcion self._documento_seleccionado

        datos_direccion_seleccionada = self._procesar_direccion_seleccionada()

        self._documento.depot_id = datos_direccion_seleccionada.get('depot_id', 0)
        self._documento.depot_name = datos_direccion_seleccionada.get('depot_name', '')
        self._documento.address_detail_id = datos_direccion_seleccionada.get('address_detail_id', 0)
        self._documento.address_name = datos_direccion_seleccionada.get('address_name', '')
        self._documento.business_entity_id = self._cliente.business_entity_id
        self._documento.customer_type_id = self._cliente.cayal_customer_type_id
