import tkinter as tk
import uuid
import pyperclip
from datetime import datetime

from cayal.util import Utilerias
from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.ventanas import Ventanas


class DireccionesAdicionales:

    def __init__(self,
                 master,
                 parametros,
                 direcciones_cliente,
                 accion,
                 tabla_direcciones = None,
                 seleccion=None,
                 business_entity_id=None):

        self._parametros = parametros

        self._utilerias = Utilerias()
        self._base_de_datos = ComandosBaseDatos(self._parametros.cadena_conexion)

        self._master = master
        self._ventanas = Ventanas(self._master)

        self._consulta_colonias = []
        self.direcciones_adicionales = direcciones_cliente
        self._tabla_direcciones = tabla_direcciones
        self._accion = accion
        self._seleccion = seleccion
        self._valores_fila_seleccionada = {}
        self._business_entity_id = self._parametros.id_principal
        self._crear_frames()
        self._cargar_componentes_forma()
        self._cargar_eventos_forma()
        self._cargar_info_componentes_forma()

        self._nombre_usuario = self._base_de_datos.buscar_nombre_de_usuario(self._parametros.id_usuario)
        self.numero_direcciones = 0


        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Direcciones adicionales')

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_generales': ('frame_principal', 'Dirección:',
                                  {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                   'sticky': tk.NSEW}),

            'frame_botones': ('frame_generales', None,
                              {'row': 10, 'column': 1, 'padx': 0, 'pady': 5, 'sticky': tk.W}),
        }

        self._ventanas.crear_frames(frames)

    def _cargar_componentes_forma(self):

        nombres_componentes = {
            'tbx_titulo': ('frame_generales', None, 'Titulo:', None),
            'tbx_telefono': ('frame_generales', None, 'Teléfono:', None),
            'tbx_calle': ('frame_generales', None, 'Calle:', None),
            'tbx_numero': ('frame_generales', None, 'Numero:', None),
            'txt_comentario': ('frame_generales', None, 'Comen.:', None),
            'tbx_cp': ('frame_generales', None, 'C.P.:', None),
            'lbl_estado': ('frame_generales', {'text':''},
                           {'row':6, 'column':1, 'pady':5, 'padx':5, 'sticky':tk.W}, None),
            'lbl_municipio': ('frame_generales', {'text':''},
                           {'row':7, 'column':1, 'pady':5, 'padx':5, 'sticky':tk.W}, None),
            'cbx_colonia': ('frame_generales', None, 'Colonia:', None),
            'btn_guardar': ('frame_botones', None, 'Guardar', None),
            'btn_cancelar': ('frame_botones', 'danger', 'Cancelar', None),
            'btn_copiar': ('frame_botones', 'warning', 'Copiar', None)
        }

        self._ventanas.crear_componentes(nombres_componentes)

        if not self._accion == 'editar':
            self._ventanas.bloquear_componente('btn_copiar')

    def _cargar_eventos_forma(self):

        tbx_telefono = self._ventanas.componentes_forma['tbx_telefono']
        self._ventanas.agregar_validacion_tbx(tbx_telefono, 'telefono')

        tbx_cp = self._ventanas.componentes_forma['tbx_cp']
        self._ventanas.agregar_validacion_tbx(tbx_cp, 'codigo_postal')

        btn_guardar = self._ventanas.componentes_forma['btn_guardar']
        btn_guardar.config(command=lambda: self._guardar_parametros_direccion())

        btn_cancelar = self._ventanas.componentes_forma['btn_cancelar']
        btn_cancelar.config(command=lambda: self._master.destroy())

        btn_copiar = self._ventanas.componentes_forma['btn_copiar']
        btn_copiar.config(command=lambda: self.copiar_direccion())

        tbx_cp = self._ventanas.componentes_forma['tbx_cp']
        tbx_cp.bind('<Return>', lambda event: self._cargar_info_por_cp())

        cbx_colonia = self._ventanas.componentes_forma['cbx_colonia']
        cbx_colonia.bind('<<ComboboxSelected>>', lambda event: self._cargar_info_por_colonia())

    def copiar_direccion(self):

        business_entity_id = self._business_entity_id
        address_detail_id = self._valores_fila_seleccionada.get('address_detail_id', 0)

        informacion = self._base_de_datos.buscar_informacion_direccion_whatsapp(address_detail_id, business_entity_id)
        pyperclip.copy(informacion)
        self._ventanas.mostrar_mensaje(mensaje="Dirección copiada al portapapeles.", master=self._master, tipo='info')
        self._master.destroy()

    def _validar_inputs_formulario(self):

        for nombre, componente, in self._ventanas.componentes_forma.items():

            tipo = nombre[0:3]

            if tipo in ('tbx', 'txt', 'cbx'):
                valor = componente.get("1.0", tk.END) if tipo == 'txt' else componente.get()

                if not valor or valor == 'Seleccione':
                    self._ventanas.mostrar_mensaje(f'Debe establecer un valor para {nombre[4::]}')
                    return False

                if nombre[4::] == 'titulo':
                    if len(valor) > 40:
                        self._ventanas.mostrar_mensaje(f'Debe elegir un nombre corto para {nombre[4::]}')
                        return False

                if nombre[4::] == 'telefono':
                    if not self._utilerias.es_numero_de_telefono(valor):
                        self._ventanas.mostrar_mensaje(f'Debe elegir un número válido para el {nombre[4::]}')
                        return False
        return True

    def _obtener_valores_de_controles(self):
        cbx_colonia = self._ventanas.componentes_forma['cbx_colonia']
        colonia = cbx_colonia.get()

        info_colonia = [reg for reg in self._consulta_colonias if reg['City'] == colonia][0]

        valores = {}
        for nombre, componente in self._ventanas.componentes_forma.items():
            tipo = nombre[0:3]
            if tipo in ('txt', 'tbx'):
                valor = componente.get("1.0", tk.END) if tipo == 'txt' else componente.get()
                valor = valor.strip()
                valor = valor.upper() if nombre[4::] != 'titulo' else self._utilerias.capitalizar_cada_palabra(valor)
                valores[nombre[4::]] = valor

        accion = 'editar' if self._parametros_direccion_editar else 'agregar'
        identificador = uuid.uuid4() if accion == 'agregar' else self._parametros_direccion_editar['uuid']
        address_detail_id = 0 if accion == 'agregar' else self._parametros_direccion_editar['address_detail_id']
        depot_id = 0 if accion == 'agregar' else self._parametros_direccion_editar['depot_id']

        fecha = str(datetime.today())
        fecha = fecha[0:10]

        return {
            'state_province': info_colonia['State'],
            'city': info_colonia['City'],
            'zip_code': info_colonia['ZipCode'],
            'municipality': info_colonia['Municipality'],
            'street': valores['calle'],
            'ext_number': valores['numero'],
            'comments': valores['comentario'],
            'state_code': info_colonia['StateCode'],
            'city_code': info_colonia['CityCode'],
            'municipality_code': info_colonia['MunicipalityCode'],
            'tipo_direccion': 2,
            'address_name': valores['titulo'],
            'direccion_principal': 0,
            'accion': accion,
            'address_detail_id': address_detail_id,
            'uuid': identificador,
            'telefono': valores['telefono'],
            'depot_id': depot_id,
            'created_on': fecha,
            'user_name': self._nombre_usuario,
            'delivery_cost': info_colonia['DeliveryCost']
        }

    def _cargar_info_por_cp(self):
        cp = self._ventanas.obtener_input_componente('tbx_cp')

        if not self._utilerias.es_codigo_postal(cp):
            return

        self._rellenar_colonias_por_cp(cp)

    def _rellenar_colonias_por_cp(self, cp):

        cbx_colonia = self._ventanas.componentes_forma['cbx_colonia']

        self._consulta_colonias = self._base_de_datos.fetchall("""
            SELECT CountryAddressID, State, Municipality, MunicipalityCode, StateCode, AutonomiaCode, 
                            CountryID, CountryCode, Pais, CityCode, Autonomia, City,
                          EFA.ZoneID, ZipCode, ISNULL(CargoEnvio,20) DeliveryCost
            FROM engRefCountryAddress EFA INNER JOIN
					orgZone Z ON EFA.ZoneID = z.ZoneID
            WHERE Efa.ZoneID IS NOT NULL AND ZipCode = ?
            ORDER BY City
        """, (cp))

        if not self._consulta_colonias:
            self._consulta_colonias = self._base_de_datos.fetchall("""
                        SELECT CountryAddressID, State, Municipality, MunicipalityCode, StateCode, AutonomiaCode, 
                            CountryID, CountryCode, Pais, CityCode, Autonomia, City,
                          EFA.ZoneID, ZipCode, ISNULL(CargoEnvio,20) DeliveryCost
                        FROM engRefCountryAddress EFA INNER JOIN
                                    orgZone Z ON EFA.ZoneID = z.ZoneID
                        WHERE ZipCode = ?
                        ORDER BY City
                    """, (cp))

        if self._consulta_colonias:
            colonias = [colonia['City'] for colonia in self._consulta_colonias]
            colonias.insert(0, 'Seleccione')

            cbx_colonia['values'] = colonias
            cbx_colonia.set(colonias[0])

            self._ventanas.insertar_input_componente('lbl_estado', self._consulta_colonias[0].get('State', None))
            self._ventanas.insertar_input_componente('lbl_municipio',
                                                     self._consulta_colonias[0].get('Municipality', None))

    def _cargar_info_por_colonia(self, colonia=None):
        cbx_colonia = self._ventanas.componentes_forma['cbx_colonia']
        colonia = cbx_colonia.get() if not colonia else colonia

        if colonia == 'Seleccione':
            self._rellenar_colonias_por_ruta()
        else:
            idx_colonia = [i for i, reg in enumerate(self._consulta_colonias) if reg['City'] == colonia]
            if idx_colonia:
                idx_colonia = idx_colonia[0]

                tbx_cp = self._ventanas.componentes_forma['tbx_cp']
                cp = self._consulta_colonias[idx_colonia]['ZipCode']

                tbx_cp.delete(0, tk.END)
                tbx_cp.insert(0, cp)

                valores_cbx = cbx_colonia['values']

                cbx_colonia.set(valores_cbx[idx_colonia + 1])

                lbl_estado = self._ventanas.componentes_forma['lbl_estado']
                lbl_municipio = self._ventanas.componentes_forma['lbl_municipio']

                lbl_estado.config(text=self._consulta_colonias[idx_colonia]['State'])
                lbl_municipio.config(text=self._consulta_colonias[idx_colonia]['Municipality'])

    def _rellenar_colonias_por_ruta(self):
        cbx_colonia = self._ventanas.componentes_forma['cbx_colonia']

        self._consulta_colonias = self._base_de_datos.fetchall("""
                    SELECT CountryAddressID, State, Municipality, MunicipalityCode, StateCode, AutonomiaCode, 
                            CountryID, CountryCode, Pais, CityCode, Autonomia, City,
                          EFA.ZoneID, ZipCode, CargoEnvio DeliveryCost
                    FROM engRefCountryAddress EFA INNER JOIN
					orgZone Z ON EFA.ZoneID = z.ZoneID
                    WHERE Efa.ZoneID IS NOT NULL
                    ORDER BY City
                """, ())
        colonias = [colonia['City'] for colonia in self._consulta_colonias]
        colonias.insert(0, 'Seleccione')

        cbx_colonia['values'] = colonias
        cbx_colonia.set(colonias[0])

    def _guardar_parametros_direccion(self):
        if not self._validar_inputs_formulario():
            return

        direccion = self._formatear_direccion()
        direccion['fecha_direccion'] = datetime.today()

        if direccion['tipo_direccion'] in ('sucursal_sin_direccion', 'direccion_nueva'):
            direccion['Accion'] = 'agregar'
            direccion['address_detail_id'] = 0
            self.direcciones_adicionales.append(direccion)
        else:

            identificador = str(direccion['uuid'])
            for reg in self.direcciones_adicionales:
                identificador_lista_direcciones = str(reg['UUID'])
                if identificador_lista_direcciones == identificador:
                    direccion_base_datos = self._formatear_direccion_base_datos(direccion)
                    direccion['Accion'] = 'editar'

                    reg.update(direccion_base_datos)
                    direccion_base_datos_formateada = self._formatear_direccion(direccion_base_datos)
                    reg.update(direccion_base_datos_formateada)
                    reg['Accion'] = 'editar'

        self.afectar_tabla_direcciones(direccion)

        self._master.destroy()

    def afectar_tabla_direcciones(self, direccion):

        if not self._tabla_direcciones:
            self._base_de_datos.actualizar_direcciones_cliente(direccion,
                                                               self._business_entity_id,
                                                               self._parametros.id_usuario)
            self.numero_direcciones = 1
            return

        if self._accion == 'agregar' and direccion['tipo_direccion'] != 'sucursal_sin_direccion':

            self._tabla_direcciones.insert(
                "", 0, values=(
                    direccion['address_detail_id'],
                    direccion['address_name'],
                    direccion['city'],
                    direccion['fecha_direccion'],
                    direccion['usuario'],
                    direccion['delivery_cost'],
                    direccion['uuid'],
                    direccion['tipo_direccion'],
                    direccion['depot_id']
                )
            )
            return

        self._ventanas.actualizar_fila_treeview(
            self._tabla_direcciones,
            self._valores_fila_seleccionada['fila'],
            (
                direccion['address_detail_id'],
                direccion['address_name'],
                direccion['city'],
                direccion['fecha_direccion'],
                direccion['usuario'],
                direccion['delivery_cost'],
                direccion['uuid'],
                direccion['tipo_direccion'],
                direccion['depot_id']
            )
        )
        return

    def _cargar_info_componentes_forma(self):
        if self._accion == 'agregar':
            self._rellenar_colonias_por_ruta()
            return

        if self._accion == 'editar':
            self._obtener_valores_fila_tabla()
            info_direccion = self._buscar_detalle_direccion()
            self._rellenar_formulario(info_direccion)

            if self._valores_fila_seleccionada['tipo_direccion'] == 'sucursal_sin_direccion':
                address_name = self._valores_fila_seleccionada['address_name']
                address_name = address_name.lower()
                address_name = address_name.capitalize()

                self._ventanas.insertar_input_componente('tbx_titulo', address_name)
                self._ventanas.bloquear_componente('tbx_titulo')

    def _buscar_detalle_direccion(self):

        identificador = self._valores_fila_seleccionada.get('uuid')
        for direccion in self.direcciones_adicionales:

            identificador_direccion = direccion['UUID']

            if str(identificador) == str(identificador_direccion):
                return self._formatear_direccion(direccion)

        direccion = self._base_de_datos.buscar_detalle_direccion_formateada(
            self._valores_fila_seleccionada['address_detail_id'])

        direccion['tipo_direccion'] = self._valores_fila_seleccionada.get('tipo_direccion', 'direccion_nueva')
        return direccion

    def _obtener_valores_fila_tabla(self):

        filas = self._tabla_direcciones.get_children()
        for fila in filas:
            valores_fila = self._tabla_direcciones.item(fila)['values']
            identificador = valores_fila[6]
            if identificador == self._seleccion:
                self._valores_fila_seleccionada = {
                    'tipo_direccion': valores_fila[7],
                    'address_detail_id': valores_fila[0],
                    'address_name': valores_fila[1],
                    'uuid': identificador,
                    'depot_id': valores_fila[8],
                    'fila': fila,
                    'fecha_direccion': valores_fila[2]
                }

    def _rellenar_formulario(self, info_direccion):
        tipo_direccion = info_direccion['tipo_direccion']

        if tipo_direccion == 'sucursal_sin_direccion':
            componentes = {
                'tbx_titulo': 'address_name',
                'tbx_telefono': 'telefono',
                'tbx_calle': 'calle',
                'tbx_numero': 'numero',
                'txt_comentario': 'comentario',
                'tbx_cp': 'cp',
                'lbl_estado': 'estado',
                'lbl_municipio': 'municipio'
            }
        else:
            componentes = {
                'tbx_titulo': 'address_name',
                'tbx_telefono': 'telefono',
                'tbx_calle': 'street',
                'tbx_numero': 'ext_number',
                'txt_comentario': 'comments',
                'tbx_cp': 'zip_code',
                'lbl_estado': 'state_province',
                'lbl_municipio': 'municipality'
            }
        for nombre_componente, clave_direccion in componentes.items():
            if info_direccion.get(clave_direccion,None):
                self._ventanas.insertar_input_componente(nombre_componente, info_direccion[clave_direccion])

        self._cargar_info_por_cp()
        colonia = info_direccion.get('city', None) if tipo_direccion != 'sucursal_sin_direccion' else info_direccion.get('colonia', None)
        if colonia:
            self._ventanas.insertar_input_componente('cbx_colonia', colonia)

    def _formatear_direccion(self, info_direccion = None):

        parametros = {}

        if not info_direccion:
            colonia_seleccionada = self._ventanas.obtener_input_componente('cbx_colonia')
            info_colonia = [colonia for colonia in self._consulta_colonias
                            if colonia['City'] == colonia_seleccionada]

            if not info_colonia:
                return

            info_colonia = info_colonia[0]
            costo_envio = info_colonia.get('DeliveryCost', 20)

            parametros['state_province'] = info_colonia['State']
            parametros['city'] = info_colonia['City']
            parametros['zip_code'] = info_colonia['ZipCode']
            parametros['municipality'] = info_colonia['Municipality']
            parametros['street'] = self._ventanas.obtener_input_componente('tbx_calle')
            parametros['ext_number'] = self._ventanas.obtener_input_componente('tbx_numero')
            parametros['comments'] = self._ventanas.obtener_input_componente('txt_comentario')
            parametros['usuario_id'] = self._parametros.id_usuario
            parametros['state_code'] = info_colonia['StateCode']
            parametros['city_code'] = info_colonia['CityCode']
            parametros['municipality_code'] = info_colonia['MunicipalityCode']
            parametros['telefono'] = self._ventanas.obtener_input_componente('tbx_telefono')
            parametros['delivery_cost'] = self._utilerias.convertir_numero_a_moneda(costo_envio)
            parametros['depot_id'] = self._valores_fila_seleccionada.get('depot_id',0)
            parametros['address_detail_id'] = self._valores_fila_seleccionada.get('address_detail_id', 0)
            parametros['uuid'] = self._valores_fila_seleccionada.get('uuid', uuid.uuid4())
            parametros['accion'] = self._seleccion
            parametros['address_name'] = self._ventanas.obtener_input_componente('tbx_titulo')
            parametros['fecha_direccion'] = self._valores_fila_seleccionada.get('fecha_direccion', datetime.today())
            parametros['usuario'] = self._nombre_usuario
            parametros['tipo_direccion'] = self._valores_fila_seleccionada.get('tipo_direccion','direccion_nueva')
            parametros['fila'] = self._valores_fila_seleccionada.get('fila', None)

        if info_direccion:
            parametros['state_province'] = info_direccion['StateProvince']
            parametros['city'] = info_direccion['City']
            parametros['zip_code'] = info_direccion['ZipCode']
            parametros['municipality'] = info_direccion['Municipality']
            parametros['street'] = info_direccion['Street']
            parametros['ext_number'] = info_direccion['ExtNumber']
            parametros['comments'] = info_direccion['Comments']
            parametros['usuario_id'] = self._parametros.id_usuario
            parametros['state_code'] = info_direccion['StateProvinceCode']
            parametros['city_code'] = info_direccion['CityCode']
            parametros['municipality_code'] = info_direccion['MunicipalityCode']
            parametros['telefono'] = info_direccion['Telefono']
            parametros['delivery_cost'] = info_direccion['DeliveryCost']
            parametros['depot_id'] = info_direccion['DepotID']
            parametros['address_detail_id'] = info_direccion['AddressDetailID']
            parametros['uuid'] = info_direccion['UUID']
            parametros['accion'] = self._seleccion
            parametros['address_name'] = info_direccion['AddressName']
            parametros['fecha_direccion'] = info_direccion['CreatedOn']
            parametros['usuario'] = info_direccion['UserName']
            parametros['tipo_direccion'] = info_direccion.get('TipoDireccion', 'direccion_nueva')
            parametros['fila'] = self._valores_fila_seleccionada.get('fila', None)

        return parametros

    def _formatear_direccion_base_datos(self, parametros):
        info_direccion = {}

        info_direccion['StateProvince'] = parametros['state_province']
        info_direccion['City'] = parametros['city']
        info_direccion['ZipCode'] = parametros['zip_code']
        info_direccion['Municipality'] = parametros['municipality']
        info_direccion['Street'] = parametros['street']
        info_direccion['ExtNumber'] = parametros['ext_number']
        info_direccion['Comments'] = parametros['comments']
        info_direccion['StateProvinceCode'] = parametros['state_code']
        info_direccion['CityCode'] = parametros['city_code']
        info_direccion['MunicipalityCode'] = parametros['municipality_code']
        info_direccion['Telefono'] = parametros['telefono']
        info_direccion['DeliveryCost'] = parametros['delivery_cost']
        info_direccion['DepotID'] = parametros['depot_id']
        info_direccion['AddressDetailID'] = parametros['address_detail_id']
        info_direccion['UUID'] = parametros['uuid']
        info_direccion['AddressName'] = parametros['address_name']
        info_direccion['CreatedOn'] = parametros['fecha_direccion']
        info_direccion['UserName'] = parametros['usuario']

        return info_direccion
