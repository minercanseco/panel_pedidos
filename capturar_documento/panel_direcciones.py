import tkinter as tk
import uuid
import ttkbootstrap as ttk
from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.util import Utilerias
from cayal.ventanas import Ventanas

from direcciones_adicionales import DireccionesAdicionales


class PanelDirecciones:
    def __init__(self, master, parametros, cliente):

        self._master = master
        self._parametros = parametros
        self._ventanas = Ventanas(self._master)

        self._cliente = cliente
        self._business_entity_id = self._cliente.business_entity_id
        self.address_fiscal_detail_id = self._cliente.address_fiscal_detail_id

        self.direcciones_adicionales = []
        self._registros_tabla_direccion = []

        self._consulta_direcciones_adicionales = [] # consulta desde bd
        self._consulta_sucursales_cliente = [] # ayuda a dar tratamiento a clientes con sucursales
        self.consulta_detalles_direccion_fiscal = []

        self._utilerias = Utilerias()
        self._base_de_datos = ComandosBaseDatos(self._parametros.cadena_conexion)
        self._buscar_informacion_base_datos()
        self._nombre_usuario = self._base_de_datos.buscar_nombre_de_usuario(self._parametros.id_usuario)

        self._cargar_componentes_forma()
        self._cargar_info_componentes_forma()
        self._cargar_eventos_componentes_forma()
        self._ventanas.configurar_ventana_ttkbootstrap('Direcciones')
        self.numero_direcciones = 0

    def _buscar_informacion_base_datos(self):
        self._consulta_direcciones_adicionales = self._base_de_datos.buscar_direcciones_adicionales(self._business_entity_id)
        self._consulta_sucursales_cliente = self._base_de_datos.buscar_sucursales(self._business_entity_id)
        consulta_direccion_fiscal = self._base_de_datos.buscar_detalle_de_direccion(self.address_fiscal_detail_id)
        self.consulta_detalles_direccion_fiscal = consulta_direccion_fiscal[0]

        self.fecha_creacion_cliente = self._base_de_datos.fetchone("""
                       SELECT CAST(CreatedON as date) FROM orgBusinessEntity WHERE BusinessEntityID = ? 
                       """, (self._business_entity_id,))

        self.usuario_creador_cliente = self._base_de_datos.fetchone("""
                       SELECT  U.UserName
                       FROM orgBusinessEntity E INNER JOIN
                           engUser U ON E.CreatedBy = U.UserID
                       WHERE E.BusinessEntityID = ?
                       """, (self._business_entity_id,))

        self._costo_envio_direccion_fiscal = self._base_de_datos.fetchone("""
                       SELECT CargoEnvio FROM [dbo].[zvwBuscarCargoEnvio-AddressDetailID](?)
                   """, (self.address_fiscal_detail_id,))

    def _cargar_componentes_forma(self):

        frame_principal = ttk.LabelFrame(self._master, text='Direcciones')
        frame_principal.grid(row=0, padx=5, pady=5, sticky=tk.NSEW)

        frame_botones = ttk.Frame(frame_principal)
        frame_botones.grid(row=1, column=1,  pady=5, padx=5, sticky=tk.W)

        columnas_tabla = [
            {'text': 'AddressDetailID', "stretch": False, 'width': 85, 'column_anchor': tk.W,
             'heading_anchor': tk.W,
             'hide': 1},
            {'text': 'Titulo', "stretch": False, 'width': 100, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'Colonia', "stretch": False, 'width': 100, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'Creado', "stretch": False, 'width': 70, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'CreadoPor', "stretch": False, 'width': 70, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'Envio', "stretch": False, 'width': 70, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'UUID', "stretch": False, 'width': 85, 'column_anchor': tk.W,
             'heading_anchor': tk.W,
             'hide': 1},
            {'text': 'Tipo', "stretch": False, 'width': 85, 'column_anchor': tk.W,
             'heading_anchor': tk.W,
             'hide': 1},
            {'text': 'DepotID', "stretch": False, 'width': 85, 'column_anchor': tk.W,
             'heading_anchor': tk.W,
             'hide': 1},
        ]

        self._ventanas.componentes_forma['columnas_tabla'] = columnas_tabla

        componentes_forma = {'tvw_direcciones': ('Treeview', frame_principal, None),
                             'btn_guardar': ('Button', frame_botones, 'primary'),
                             'btn_agregar': ('Button', frame_botones, 'info'),
                             'btn_editar': ('Button', frame_botones, 'warning'),
                             'btn_borrar': ('Button', frame_botones, 'danger'),
                             }

        for i, (nombre, (tipo, frame, estado)) in enumerate(componentes_forma.items()):

            if 'tvw' in nombre:
                componente = ttk.Treeview(bootstyle='PRIMARY', master=frame,
                                         columns=columnas_tabla, show='headings', height=5)

                componente.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

            if 'btn' in nombre:
                componente = ttk.Button(frame, text=nombre[4::].capitalize(), style=estado)
                componente.grid(row=0, column=i, pady=5, padx=5, sticky=tk.W)

            self._ventanas.componentes_forma[nombre] = componente

    def _cargar_eventos_componentes_forma(self):
        eventos = {
            'btn_borrar': self._borrar_direccion_adicional,
            'btn_editar': self._editar_direccion_adicional,
            'tvw_direcciones':(lambda event: self._editar_direccion_adicional(), 'doble_click'),
            'btn_agregar': self._agregar_direccion_adicional,
            'btn_guardar': self._actualizar_direcciones_en_base_de_datos
        }

        self._ventanas.cargar_eventos(eventos)

    def _procesar_consulta_direcciones(self):
        if not self._consulta_direcciones_adicionales:
            return

        for direccion in self._consulta_direcciones_adicionales:
            direccion_adicional = {}

            # el identificador relaciona el registro de la tabla con el registo de la lista de direcciones
            identificador = uuid.uuid4()

            direccion_adicional['address_name'] = direccion.get('AddressName', 'Dirección')
            direccion_adicional['city'] = direccion.get('City', 'Colonia')
            direccion_adicional['fecha_direccion'] = direccion.get('CreatedOn', '2019-09-14')
            direccion_adicional['usuario'] = direccion.get('UserName', 'Admin')
            direccion_adicional['costo_envio'] = direccion.get('DeliveryCost', 20)
            direccion_adicional['uuid'] = identificador
            direccion_adicional['tipo_direccion'] = 'direccion_adicional'
            direccion_adicional['address_detail_id'] = direccion.get('AddressDetailID',
                                                                     self.address_fiscal_detail_id)
            direccion_adicional['depot_id'] = direccion.get('DepotID', 0)

            #agrega un marcador a la direccion para que al procesarla el programa sepa que accion tomar
            direccion['Accion'] = 'ninguna'
            direccion['UUID'] = identificador
            direccion['TipoDireccion'] = 'direccion_adicional'

            self._registros_tabla_direccion.append(direccion_adicional)
            self.direcciones_adicionales.append(direccion)

    def _procesar_consulta_sucursales(self):

        if not self._consulta_sucursales_cliente:
            return

        # remover las sucursales que ya tienen asociada una direccion de las que no

        for sucursal in self._consulta_sucursales_cliente:
            address_detail_id_sucursal = sucursal['AddressDetailID']

            direccion_sucursal = {}

            # este identificador relaciona el registro de la tabla con el registro de la lista de direcciones
            identificador = uuid.uuid4()

            # En caso de que la sucursal no tenga establecida una direccion
            if address_detail_id_sucursal == self.address_fiscal_detail_id:

                direccion_sucursal['address_name'] = sucursal.get('DepotName', 'Dirección Fiscal')
                direccion_sucursal['city'] = self._cliente.address_fiscal_city
                direccion_sucursal['fecha_direccion'] = self.fecha_creacion_cliente
                direccion_sucursal['usuario'] = self.usuario_creador_cliente
                direccion_sucursal['costo_envio'] = self._costo_envio_direccion_fiscal
                direccion_sucursal['uuid'] = identificador
                direccion_sucursal['tipo_direccion'] = 'sucursal_sin_direccion'
                direccion_sucursal['address_detail_id'] = self.address_fiscal_detail_id
                direccion_sucursal['depot_id'] = sucursal.get('DepotID', 0)
                direccion_sucursal['accion'] = 'ninguna'

                # No se agrega a direcciones adionales porque hay que hacer una distincion entre la direccion
                # Duplicada fiscal y la direccion de la tabla para visualizacion del usuario
                self._registros_tabla_direccion.append(direccion_sucursal)

            if address_detail_id_sucursal != self.address_fiscal_detail_id:

                existe_en_direciones = [direccion for direccion in self.direcciones_adicionales
                                        if direccion['AddressDetailID'] == address_detail_id_sucursal]

                if not existe_en_direciones:
                    consulta_direccion_sucursal = self._base_de_datos.buscar_detalle_de_direccion(
                        address_detail_id_sucursal)
                    if not consulta_direccion_sucursal:
                        return

                    info_direccion_sucursal = consulta_direccion_sucursal[0]

                    direccion_sucursal['address_name'] = info_direccion_sucursal.get('AddressName', 'Dirección')
                    direccion_sucursal['city'] = info_direccion_sucursal.get('City', 'Colonia')
                    direccion_sucursal['fecha_direccion'] = info_direccion_sucursal.get('CreatedOn', '2019-03-14')
                    direccion_sucursal['usuario'] = info_direccion_sucursal.get('UserName', 'Admin')
                    direccion_sucursal['costo_envio'] = info_direccion_sucursal.get('DeliveryCost', 20)
                    direccion_sucursal['uuid'] = identificador
                    direccion_sucursal['tipo_direccion'] = 'sucursal_con_direccion'
                    direccion_sucursal['address_detail_id'] = info_direccion_sucursal.get('address_detail_id',
                                                                                          self.address_fiscal_detail_id)
                    direccion_sucursal['depot_id'] = info_direccion_sucursal.get('DepotID', 0)

                    # agrega un marcador a la direccion para que al procesarla el programa sepa que accion tomar
                    info_direccion_sucursal['Accion'] = 'ninguna'
                    info_direccion_sucursal['UUID'] = identificador
                    info_direccion_sucursal['TipoDireccion'] = 'sucursal_con_direccion'

                    # en este caso se agrega a ambas listas porque la sucursal esta ligada a una direccion adicional
                    self._registros_tabla_direccion.append(direccion_sucursal)
                    self.direcciones_adicionales.append(info_direccion_sucursal)

    def _cargar_info_componentes_forma(self):
        columnas_tabla = self._ventanas.componentes_forma['columnas_tabla']
        tabla_direcciones = self._ventanas.componentes_forma['tvw_direcciones']

        self._procesar_consulta_direcciones()
        self._procesar_consulta_sucursales()

        # en caso de que no se tenga que procesar nada
        if not self._registros_tabla_direccion:
            self._ventanas.rellenar_treeview(tabla_direcciones, columnas_tabla, valor_barra_desplazamiento=4)
            return

        if self._registros_tabla_direccion:

            self._ventanas.rellenar_treeview(tabla_direcciones, columnas_tabla, valor_barra_desplazamiento=4)

            for direccion in self._registros_tabla_direccion:
                costo_envio = self._utilerias.convertir_numero_a_moneda(direccion['costo_envio'])
                tabla_direcciones.insert("", 0, values=(direccion['address_detail_id'],
                                                        direccion['address_name'],
                                                        direccion['city'],
                                                        direccion['fecha_direccion'],
                                                        direccion['usuario'],
                                                        costo_envio,
                                                        direccion['uuid'],
                                                        direccion['tipo_direccion'],
                                                        direccion['depot_id']))

    def _llamar_instancia_direcciones_adicionales(self, accion, seleccion = None):

        tabla_direcciones = self._ventanas.componentes_forma['tvw_direcciones']
        ventana = self._ventanas.crear_popup_ttkbootstrap()

        instancia = DireccionesAdicionales(ventana,
                                           self._parametros,
                                           self.direcciones_adicionales,
                                           accion,
                                           tabla_direcciones,
                                           seleccion)
        ventana.wait_window()
        self.direcciones_adicionales = instancia.direcciones_adicionales

    def _agregar_direccion_adicional(self):
        self._llamar_instancia_direcciones_adicionales('agregar')

    def _borrar_direccion_adicional(self):
        seleccion = self._ventanas.obtener_seleccion_filas_treeview('tvw_direcciones')

        if not seleccion:
            self._ventanas.mostrar_mensaje('Debe seleccionar por lo menos un registro.')
            return

        valores_fila = self._ventanas.obtener_valores_fila_treeview('tvw_direcciones', seleccion)
        identificador_tabla = str(valores_fila[6])

        for direccion in self.direcciones_adicionales:
            identificador_direccion = str(direccion['UUID'])

            if identificador_direccion == identificador_tabla:
                direccion['Accion'] = 'borrar'
                break

        self._ventanas.remover_fila_treeview('tvw_direcciones', seleccion)

    def _editar_direccion_adicional(self):

        seleccion = self._ventanas.obtener_seleccion_filas_treeview('tvw_direcciones')

        if not seleccion:
            self._ventanas.mostrar_mensaje('Debe seleccionar por lo menos un registro.')
            return

        if len(seleccion) > 1:
            self._ventanas.mostrar_mensaje('Debe seleccionar solo un registro a la vez.')
            return

        valores_fila = self._ventanas.obtener_valores_fila_treeview('tvw_direcciones', seleccion)
        identificador = valores_fila[6]

        self._llamar_instancia_direcciones_adicionales('editar', identificador)

    def _actualizar_direcciones_en_base_de_datos(self):
        if not (self.direcciones_adicionales and self._cliente.business_entity_id != 0):
            self._ventanas.mostrar_mensaje('No existen registros o el cliente aún no ha sido creado.')
            return

        # Desde que se procesar y/o se agregan se agrega la clave Accion a la direccion
        # Para que segun corresponda se puedan realizar las acciones_pertinentes
        numero_direcciones = self._base_de_datos.actualizar_direcciones_panel_direcciones(
                                self.direcciones_adicionales,
                                self._cliente.business_entity_id,
                                self._parametros.id_usuario,)

        self.numero_direcciones = numero_direcciones

        self._master.destroy()
