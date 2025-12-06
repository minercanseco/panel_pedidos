# Project Context Dump

Ruta: `/Users/minercansecomanuel/PycharmProjects/panel_pedidos`
Fecha: 2025-09-03 13:33:41

## Árbol de directorios (filtrado)

  - agregar_epecificaciones.py (3 KB)
  - agregar_manualmente.py (30 KB)
  - agregar_partida_produccion.py (13 KB)
  - buscar_clientes.py (5 KB)
  - buscar_generales_cliente.py (34 KB)
  - buscar_generales_cliente_cartera.py (15 KB)
  - buscar_info_cif.py (12 KB)
  - buscar_pedido.py (12 KB)
  - cancelar_pedido.py (6 KB)
  - capturado_vs_producido.py (17 KB)
  - configurar_pedido.py (18 KB)
  - controlador_captura.py (48 KB)
  - controlador_panel_pedidos.py (90 KB)
  - controlador_saldar_cartera.py (19 KB)
  - controlador_verificador.py (19 KB)
  - direccion_cliente.py (2 KB)
  - direcciones_adicionales.py (23 KB)
  - editar_caracteristicas_pedido.py (35 KB)
  - editar_partida.py (20 KB)
  - editar_partida_produccion.py (2 KB)
  - editar_pedido.py (25 KB)
  - finalizar_surtido.py (2 KB)
  - formulario_cliente.py (42 KB)
  - generador_ticket_cliente.py (24 KB)
  - generador_ticket_produccion.py (7 KB)
  - historial_cliente.py (11 KB)
  - historial_pedido.py (4 KB)
  - horario_acumulado.py (25 KB)
  - informacion_producto.py (5 KB)
  - interfaz_captura.py (23 KB)
  - interfaz_panel_pedidos.py (9 KB)
  - interfaz_saldar_cartera.py (12 KB)
  - interfaz_verificador.py (8 KB)
  - llamar_instancia_captura.py (19 KB)
  - main.py (1 KB)
  - modelo_captura.py (16 KB)
  - modelo_panel_pedidos.py (1 KB)
  - panel_direcciones.py (15 KB)
  - panel_principal_cliente.py (19 KB)
  - saldar_documentos.py (4 KB)
  - selector_tipo_documento.py (1 KB)
  - ticket_pedido_cliente.py (5 KB)
  - verificador_precios.py (29 KB)
    - **C:\PaquetesCarnesCayal\/**
- **publicidad/**


## main.py

```py

import ttkbootstrap as ttk
from cayal.parametros_contpaqi import ParametrosContpaqi
from panel.interfaz_panel_pedidos import InterfazPanelPedidos
from panel.modelo_panel_pedidos import ModeloPanelPedidos
from panel.controlador_panel_pedidos import ControladorPanelPedidos
from cayal.actualizador_de_paquetes import ActualizadorDePaquetes
from cayal.login import Login
from cayal.generar_contexto_ia import GenerarContextoIA


def si_acceso_exitoso(parametros=None, master=None):
    llamar_instancia_principal(master, parametros)


def llamar_instancia_principal(ventana, parametros):
    vista = InterfazPanelPedidos(ventana)
    modelo = ModeloPanelPedidos(vista, parametros)
    controlador = ControladorPanelPedidos(modelo)
    ventana.mainloop()


if __name__ == '__main__':
    ventana_login = ttk.Window()
    parametros_login = ParametrosContpaqi()

    actualizador = ActualizadorDePaquetes('panel_pedidos_v103')
    nueva_version = actualizador.verificar_version_actualizada()
    solo_contexto = True

    if solo_contexto:
        gen = GenerarContextoIA(root=".", out="contexto.md")
        ruta = gen.build()
        print("Contexto generado en:", ruta)

    if nueva_version:
        actualizador.actualizar_con_interfaz(ventana_login)

    if not nueva_version:
        parametros_login.id_modulo = 1687

        instancia_login = Login(ventana_login, parametros_login, si_acceso_exitoso)
        ventana_login.mainloop()
```


## buscar_generales_cliente.py

```py
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
                                      {'row': 0, 'columnspan': 4, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.NSEW}),

            'frame_botones': ('frame_buscar', None,
                              {'row': 2, 'column': 1,  'pady': 5, 'sticky': tk.NSEW}),

            'frame_data': ('frame_principal', 'Información:',
                           {'row': 3, 'column': 0, 'columnspan': 8, 'padx': 1, 'pady': 1, 'sticky': tk.NSEW}),

            'frame_cbxs': ('frame_data', None,
                              {'row': 0, 'column': 0,  'columnspan': 4, 'pady': 1, 'sticky': tk.W}),

            'frame_cbx_direccion': ('frame_cbxs', 'Dirección:',
                               {'row': 0, 'column': 1,  'padx': 1, 'pady': 1, 'sticky': tk.NSEW}),

            'frame_cbx_documento': ('frame_cbxs', 'Documento:',
                               {'row': 0, 'column': 2, 'padx': 1, 'pady': 1, 'sticky': tk.NSEW}),

            'frame_informacion': ('frame_data', 'Generales:',
                                  {'row': 1, 'column': 0, 'columnspan': 2, 'padx': 1, 'pady': 1, 'sticky': tk.NSEW}),

            'frame_direccion': ('frame_data', 'Detalles dirección:',
                                {'row': 1, 'column': 2, 'columnspan': 2, 'padx': 1, 'pady': 1, 'sticky': tk.NS}),

            'frame_copiar_direccion': ('frame_direccion', None,
                                       {'row': 11, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}),

        }

        self._ventanas.crear_frames(frames)

    def _cargar_componentes_forma(self):

        componentes = {
            'tbx_buscar': ('frame_buscar', None, 'Buscar:', None),
            'cbx_resultados': ('frame_buscar', None, '  ', None),

            'cbx_direccion': ('frame_cbx_direccion',
                              {'row': 0, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W},
                              '  ', '[Ctrl+D]'),
            'cbx_documento': ('frame_cbx_documento',
                              {'row': 0, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W},
                              '  ', '[Ctrl+R] ó [Ctrl+F]'),
            'btn_seleccionar': ('frame_botones', 'primary', 'Seleccionar', '[F1]'),
            'btn_cancelar': ('frame_botones', 'danger', 'Cancelar', '[Esc]'),

        }
        self._ventanas.crear_componentes(componentes)

        self._componentes_direccion = {

            'lbl_txt_ncomercial': ('frame_direccion',
                                   {'font': ('Arial', 9, 'bold'), 'text': 'N.Comercial:'},
                                   {'row': 0, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),
            'lbl_txt_ruta': ('frame_direccion',
                             {'font': ('Arial', 9, 'bold'), 'text': 'Ruta:'},
                             {'row': 1, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),
            'lbl_txt_telefono': ('frame_direccion',
                                 {'font': ('Arial', 9, 'bold'), 'text': 'Teléfono:'},
                                 {'row': 2, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W},  None),
            'lbl_txt_celular': ('frame_direccion',
                                {'font': ('Arial', 9, 'bold'), 'text': 'Celular:'},
                                {'row': 3, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),
            'lbl_txt_calle': ('frame_direccion',
                              {'font': ('Arial', 9, 'bold'), 'text': 'Calle:'},
                              {'row': 4, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),
            'lbl_txt_numero': ('frame_direccion',
                               {'font': ('Arial', 9, 'bold'), 'text': 'Número:'},
                               {'row': 5, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W},  None),
            'txt_comentario': ('frame_direccion',
                               {'row': 6, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W}, ' ', None),
            'lbl_txt_cp': ('frame_direccion',
                           {'font': ('Arial', 9, 'bold'), 'text': 'C.P.'},
                           {'row': 7, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),
            'lbl_txt_colonia': ('frame_direccion',
                                {'font': ('Arial', 9, 'bold'), 'text': 'Colonia:'},
                                {'row': 8, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W},  None),
            'lbl_txt_estado': ('frame_direccion',
                               {'font': ('Arial', 9, 'bold'), 'text': 'Estado:'},
                               {'row': 9, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),
            'lbl_txt_municipio': ('frame_direccion',
                                  {'font': ('Arial', 9, 'bold'), 'text': 'Municipio:'},
                                  {'row': 10, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W},  None),

            'lbl_ncomercial': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                               {'row': 0, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_ruta': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                         {'row': 1, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_telefono': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                             {'row': 2, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_celular': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                            {'row': 3, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_calle': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                          {'row': 4, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_numero': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                           {'row': 5, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_cp': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                       {'row': 7, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_colonia': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                            {'row': 8, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_estado': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                           {'row': 9, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_municipio': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                              {'row': 10, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'btn_copiar': ('frame_copiar_direccion', 'warning', 'Copiar', '[F4]'),
        }
        self._ventanas.crear_componentes(self._componentes_direccion)

        self._componentes_credito = {
            'lbl_txt_nombre': ('frame_informacion', None, 'Nombre:', None),
            'lbl_txt_rfc': ('frame_informacion', None, 'RFC:', None),
            'lbl_txt_autorizado': ('frame_informacion', None, 'Autorizado:', None),
            'lbl_txt_debe': ('frame_informacion', None, 'Debe:', None),
            'lbl_txt_restante': ('frame_informacion', None, 'Restante:', None),
            'lbl_txt_condicion': ('frame_informacion', None, 'Condición:', None),
            'lbl_txt_pcompra': ('frame_informacion', None, 'P.Compra:', None),
            'lbl_txt_comentario': ('frame_informacion', None, 'Comentario:', None),
            'lbl_txt_minisuper': ('frame_informacion', None, 'Minisuper:', None),
            'lbl_txt_lista': ('frame_informacion', None, 'Lista:', None),

            'lbl_nombre': ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                           {'row': 0, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_rfc': ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                        {'row': 1, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),


            'lbl_autorizado': ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                               {'row': 2, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_debe': ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                         {'row': 3, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_restante': ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                             {'row': 4, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_condicion': (
            'frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
            {'row': 5, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_pcompra': ('frame_informacion', {'font': ('Arial', 9, 'bold'),
                                                  'text': ''},
                            {'row': 6, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_comentario': ('frame_informacion', {'font': ('Arial', 9, 'bold'),
                                                     'text': ''},
                               {'row': 7, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_minisuper': ('frame_informacion', {'font': ('Arial', 9, 'bold'),
                                                    'text': ''},
                              {'row': 8, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_lista': ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                          {'row': 9, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),
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
            'F4': self._copiar_informacion_direccion,
            'Ctrl+D': lambda  :self._ventanas.enfocar_componente('cbx_direccion'),
            'Ctrl+R': lambda : self._enfocar_tipo_documento('Ctrl+R'),
            'Ctrl+F': lambda: self._enfocar_tipo_documento('Ctrl+F')
        }

        self._ventanas.agregar_hotkeys_forma(hotkeys)

    def _enfocar_tipo_documento(self, atajo):
        if atajo == 'Ctrl+R':
            self._ventanas.insertar_input_componente('cbx_documento','Remisión')

        if atajo == 'Ctrl+F':
            self._ventanas.insertar_input_componente('cbx_documento','Factura')

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
                self._ventanas.enfocar_componente('btn_seleccionar')

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
        if self._instancia_llamada or not self._documento_seleccionado():
            return
        self._instancia_llamada = True

        # prepara datos
        self._cliente.consulta = self._info_cliente_seleccionado
        self._cliente.settear_valores_consulta()
        self._asignar_parametros_a_documento()
        if self._parametros_contpaqi.id_principal == -1:
            self._parametros_contpaqi.nombre_usuario = self._base_de_datos.buscar_nombre_de_usuario(
                self._parametros_contpaqi.id_usuario
            )

        # oculta búsqueda
        try:
            self._master.withdraw()
        except Exception:
            pass

        # popup intermedio
        raiz = getattr(self._ventanas, "_master", None) or self._master
        popup = self._ventanas.crear_popup_ttkbootstrap(
            master=raiz, titulo="Capturar pedido", ocultar_master=False, ejecutar_al_cierre=None, preguntar=None
        )
        try:
            popup.transient(self._master)
            popup.lift();
            popup.focus_force()
        except Exception:
            pass

        # instancia captura
        instancia = LlamarInstanciaCaptura(
            self._cliente, self._documento, self._base_de_datos, self._parametros_contpaqi, self._utilerias, popup
        )

        # detecta toplevel de captura (si existe); si no, usa el popup como captura
        captura = None
        for cand in (getattr(instancia, "master", None),
                     getattr(instancia, "ventana", None),
                     getattr(instancia, "toplevel", None)):
            try:
                if cand and int(cand.winfo_exists()):
                    captura = cand;
                    break
            except Exception:
                pass
        if captura is None:
            captura = popup

        # cierre en cascada simple
        def cerrar_todo(_=None):
            # cierra popup y búsqueda; (si captura es distinta, ya estará cerrada por su propio evento)
            try:
                if int(popup.winfo_exists()): popup.destroy()
            except Exception:
                pass
            try:
                if int(self._master.winfo_exists()): self._master.destroy()
            except Exception:
                pass

        # si cierran el popup → cerrar todo
        try:
            popup.protocol("WM_DELETE_WINDOW", cerrar_todo)
        except Exception:
            pass
        try:
            popup.bind("<Destroy>", lambda e: cerrar_todo())
        except Exception:
            pass

        # si cierran la captura → cerrar todo
        try:
            captura.protocol("WM_DELETE_WINDOW", lambda: (captura.destroy(), cerrar_todo()))
        except Exception:
            pass
        try:
            captura.bind("<Destroy>", lambda e: cerrar_todo())
        except Exception:
            pass

        # foco a la ventana operativa
        try:
            captura.lift(); captura.focus_force()
        except Exception:
            pass

    def _asignar_parametros_a_documento(self):

        # las propiedades  self._doc_type | self._cfd_type_id son aginadas por la funcion self._documento_seleccionado

        datos_direccion_seleccionada = self._procesar_direccion_seleccionada()

        self._documento.depot_id = datos_direccion_seleccionada.get('depot_id', 0)
        self._documento.depot_name = datos_direccion_seleccionada.get('depot_name', '')
        self._documento.address_detail_id = datos_direccion_seleccionada.get('address_detail_id', 0)
        self._documento.address_name = datos_direccion_seleccionada.get('address_name', '')
        self._documento.business_entity_id = self._cliente.business_entity_id
        self._documento.customer_type_id = self._cliente.cayal_customer_type_id
```


## controlador_panel_pedidos.py

```py
import os
import platform
import re
import tempfile
import tkinter as tk
from datetime import datetime
from herramientas.herramientas_compartidas.buscar_pedido import BuscarPedido
from cayal.login import Login
from buscar_generales_cliente import BuscarGeneralesCliente
from herramientas.herramientas_compartidas.capturado_vs_producido import CapturadoVsProducido
from herramientas.herramientas_panel.editar_caracteristicas_pedido import EditarCaracteristicasPedido
from cayal.cobros import Cobros

from herramientas.herramientas_compartidas.generador_ticket_produccion import GeneradorTicketProduccion
from herramientas.herramientas_compartidas.historial_pedido import HistorialPedido
from herramientas.herramientas_compartidas.horario_acumulado import HorarioslAcumulados
from llamar_instancia_captura import LlamarInstanciaCaptura
from herramientas.herramientas_panel.ticket_pedido_cliente import TicketPedidoCliente
from herramientas.cliente.cliente_nuevo import PanelPrincipal
from herramientas.herramientas_panel.selector_tipo_documento import SelectorTipoDocumento
from ttkbootstrap.constants import *
from cayal.tableview_cayal import Tableview
from herramientas.herramientas_panel.editar_pedido import EditarPedido
from cayal.cliente import Cliente
from cayal.documento import Documento
from herramientas.saldar_cartera.buscar_generales_cliente_cartera import BuscarGeneralesClienteCartera
from herramientas.cliente.buscar_clientes import BuscarClientes
from herramientas.herramientas_compartidas.cancelar_pedido import CancelarPedido


class ControladorPanelPedidos:
    def __init__(self, modelo):
        self._modelo = modelo
        self._interfaz = modelo.interfaz
        self._master = self._interfaz.master
        self._base_de_datos = self._modelo.base_de_datos
        self._utilerias = self._modelo.utilerias
        self._parametros = self._modelo.parametros
        self._cobros = Cobros(self._parametros.cadena_conexion)
        self._ticket = GeneradorTicketProduccion(32)
        self._ticket.ruta_archivo = self._obtener_directorio_reportes()

        self._actualizando_tabla = False
        self._number_orders = 0

        self._coloreando = False
        self._user_id = self._parametros.id_usuario
        self._user_name = self._base_de_datos.buscar_nombre_de_usuario(self._user_id)
        self._parametros.nombre_usuario = self._user_name
        self._partidas_pedidos = {}

        self._capturando_nuevo_pedido = False

        self._crear_tabla_pedidos()
        self._actualizar_pedidos(self._fecha_seleccionada())
        self._crear_barra_herramientas()

        self._cargar_eventos()
        self._rellenar_operador()
        self._interfaz.ventanas.configurar_ventana_ttkbootstrap(titulo='Panel pedidos', bloquear=False)
        self._interfaz.ventanas.situar_ventana_arriba(self._interfaz.master)

        self._number_orders = -1
        self._number_transfer_payments = -1
        self._count_rest_leq15 = -1
        self._count_rest_16_30 = -1
        self._count_late_gt30 = -1

        self._autorefresco_ms = 3000  # cada 3s (ajústalo)
        self._autorefresco_activo = True
        self._bloquear_autorefresco = False  # se pone True mientras abres popups críticos
        self._iniciar_autorefresco()

    def _iniciar_autorefresco(self):
        # programa el siguiente tick sin bloquear la UI
        self._master.after(self._autorefresco_ms, self._tick_autorefresco)

    def _tick_autorefresco(self):
        # evita reentradas/choques con coloreado o popups
        if self._autorefresco_activo and not self._coloreando and not self._bloquear_autorefresco:
            try:
                self._buscar_nuevos_registros()  # <- tu función actual
            except Exception as e:
                # opcional: loguea, pero no revientes el loop
                print("[AUTOREFRESCO] error:", e)
        # vuelve a programar
        self._iniciar_autorefresco()

    def _pausar_autorefresco(self):
        self._bloquear_autorefresco = True
        print('autorefresco pausado')

    def _reanudar_autorefresco(self):
        self._bloquear_autorefresco = False
        print('autorefresco reanudado')

    def _cargar_eventos(self):
        eventos = {

            'den_fecha': lambda event: self._actualizar_pedidos(self._fecha_seleccionada(), criteria=False),
            'tbv_pedidos': (lambda event: self._rellenar_tabla_detalle(), 'doble_click'),
            'cbx_capturista': lambda event: self._filtrar_por_capturados_por(),
            'cbx_status': lambda event: self._filtrar_por_status(),
            'cbx_horarios': lambda event: self._filtrar_por_horas(),
            'chk_sin_procesar': lambda *args: self._filtrar_no_procesados(),
            'chk_sin_fecha': lambda *args: self._sin_fecha(),

        }
        self._interfaz.ventanas.cargar_eventos(eventos)

        evento_adicional = {
            'tbv_pedidos': (lambda event: self._actualizar_comentario_pedido(), 'seleccion')
        }
        self._interfaz.ventanas.cargar_eventos(evento_adicional)

        evento_adicional2 = {
            'tbv_pedidos': (lambda event: self._pausar_autorefresco(), 'enfocar')
        }
        self._interfaz.ventanas.cargar_eventos(evento_adicional2)

        evento_adicional3 = {
            'tbv_pedidos': (lambda event: self._reanudar_autorefresco(), 'desenfocar')
        }
        self._interfaz.ventanas.cargar_eventos(evento_adicional3)

    def _filtrar_no_procesados(self):
        self._interfaz.ventanas.insertar_input_componente('cbx_capturista', 'Seleccione')
        self._interfaz.ventanas.insertar_input_componente('cbx_status', 'Seleccione')
        self._interfaz.ventanas.insertar_input_componente('cbx_horarios', 'Seleccione')

        valor_chk = self._interfaz.ventanas.obtener_input_componente('chk_sin_procesar')
        if valor_chk == 1:
            self._interfaz.ventanas.cambiar_estado_checkbutton('chk_sin_fecha', 'deseleccionado')
            self._actualizar_pedidos()

        if valor_chk == 0:
            fecha = str(datetime.today().date())
            self._interfaz.ventanas.insertar_input_componente('den_fecha', fecha)

            self._actualizar_pedidos()

    def _buscar_pedidos_cliente_sin_fecha(self, criteria):

        fecha_seleccionada = self._interfaz.ventanas.obtener_input_componente('den_fecha')
        if fecha_seleccionada:
            return

        if not criteria:
            self._interfaz.ventanas.mostrar_mensaje('Debe introducir un valor a buscar.')
            return

        if criteria.strip() == '':
            self._interfaz.ventanas.mostrar_mensaje('Debe abundar en el valor a buscar.')
            return

        consulta = self._modelo.buscar_pedidos_cliente_sin_fecha(criteria)

        # Rellenar tabla con los datos filtrados
        self._interfaz.ventanas.rellenar_table_view(
            'tbv_pedidos',
            self._interfaz.crear_columnas_tabla(),
            consulta
        )

        self._modelo.consulta_pedidos = consulta
        self._colorear_filas_panel_horarios(actualizar_meters=True)

    def _limpiar_componentes(self):
        self._interfaz.ventanas.limpiar_componentes(['tbx_comentarios', 'tvw_detalle'])

    def _buscar_nuevos_registros(self):
        # Usa la fecha seleccionada si existe; si no, hoy
        fecha = self._fecha_seleccionada()
        hoy = datetime.now().date() if not fecha else datetime.strptime(fecha, "%Y-%m-%d").date()
        # 1) Pedidos en logística impresos (4,13 + PrintedOn not null)
        number_orders = int(self._base_de_datos.fetchone(
            """
            SELECT COUNT(1)
            FROM docDocumentOrderCayal P
            INNER JOIN docDocument D ON P.OrderDocumentID = D.DocumentID
            WHERE P.StatusID IN (1,2,3)
              AND D.PrintedOn IS NOT NULL
              AND CAST(P.DeliveryPromise AS date) = CAST(? AS date)
            """,
            (hoy,)
        ) or 0)
        # 2) Transferencias confirmadas = 2
        number_transfer_payments = int(self._base_de_datos.fetchone(
            """
            SELECT COUNT(1)
            FROM docDocumentOrderCayal
            WHERE PaymentConfirmedID = 2
              AND CAST(DeliveryPromise AS date) = CAST(? AS date)
            """,
            (hoy,)
        ) or 0)
        # 3) Buckets de puntualidad (<=15, 16-30, >30)
        rows = self._base_de_datos.fetchall(
            """
              ;WITH Base AS (
                SELECT
                    P.OrderDocumentID,
                    ScheduledDT =
                        CAST(CAST(P.DeliveryPromise AS date) AS datetime)
                        + CAST(TRY_CONVERT(time(0), H.Value) AS datetime)
                FROM dbo.docDocumentOrderCayal AS P
                INNER JOIN dbo.OrderSchedulesCayal AS H
                    ON P.ScheduleID = H.ScheduleID
                WHERE CAST(P.DeliveryPromise AS date) = CAST(? AS date)
                  AND P.StatusID IN (2, 16, 17, 18)  -- panel logística; ajusta si aplica
                  AND TRY_CONVERT(time(0), H.Value) IS NOT NULL
            )
            SELECT
                SUM(CASE WHEN DATEDIFF(MINUTE, GETDATE(), ScheduledDT) <= 15 THEN 1 ELSE 0 END) AS RestLeq15,
                SUM(CASE WHEN DATEDIFF(MINUTE, GETDATE(), ScheduledDT) BETWEEN 16 AND 30 THEN 1 ELSE 0 END) AS Rest16to30,
                SUM(CASE WHEN DATEDIFF(MINUTE, GETDATE(), ScheduledDT) < -30 THEN 1 ELSE 0 END) AS LateGt30
            FROM Base;
            """,
            (hoy,)
        )
        if rows:
            row = rows[0]
            rest_leq15 = int(row.get('RestLeq15') or 0)  # <= 15 minutos restantes (incluye retrasos leves)
            rest_16_30 = int(row.get('Rest16to30') or 0)  # entre 16 y 30 min restantes
            late_gt30 = int(row.get('LateGt30') or 0)  # más de 30 min de retraso
        else:
            rest_leq15 = rest_16_30 = late_gt30 = 0
        # Disparar refresco si cambió cualquiera
        if (
                self._number_orders != number_orders
                or self._number_transfer_payments != number_transfer_payments
                or self._count_rest_leq15 != rest_leq15
                or self._count_rest_16_30 != rest_16_30
                or self._count_late_gt30 != late_gt30
        ):
            self._limpiar_componentes()
            self._actualizar_pedidos(self._fecha_seleccionada())
            # Actualizar contadores internos
            self._number_orders = number_orders
            self._number_transfer_payments = number_transfer_payments
            self._count_rest_leq15 = rest_leq15
            self._count_rest_16_30 = rest_16_30
            self._count_late_gt30 = late_gt30

    def _actualizar_comentario_pedido(self):
        self._limpiar_componentes()
        fila = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)
        if not fila:
            return
        if len(fila) > 1:
            return

        comentario = fila[0]['Comentarios']
        comentario = comentario.strip().upper() if comentario else ''
        comentario = f"{fila[0]['Pedido']}-->{comentario}"
        self._interfaz.ventanas.insertar_input_componente('tbx_comentarios', comentario)
        self._interfaz.ventanas.bloquear_componente('tbx_comentarios')

    def _fecha_seleccionada(self):

        fecha = self._interfaz.ventanas.obtener_input_componente('den_fecha')
        return str(fecha) if fecha else None

    def _crear_tabla_pedidos(self):
        ancho, alto = self._interfaz.ventanas.obtener_resolucion_pantalla()

        frame = self._interfaz.ventanas.componentes_forma['frame_captura']
        colors = self._interfaz.master.style.colors
        componente = Tableview(
            master=frame,
            coldata=self._interfaz.crear_columnas_tabla(),
            rowdata=self._utilerias.diccionarios_a_tuplas(None),
            paginated=True,
            searchable=True,
            bootstyle=PRIMARY,
            pagesize=19 if ancho <= 1367 else 24,
            stripecolor=None,  # (colors.light, None),
            height=19 if ancho <= 1367 else 24,
            autofit=False,
            callbacks=[self._colorear_filas_panel_horarios],
            callbacks_search=[self._buscar_pedidos_cliente_sin_fecha]

        )

        self._interfaz.ventanas.componentes_forma['tbv_pedidos'] = componente
        componente.grid(row=0, column=0, pady=5, padx=5, sticky=tk.NSEW)

        # self._interfaz.ventanas.agregar_callback_table_view_al_actualizar('tbv_pedidos', self._colorear_filas_panel_horarios)

    def _obtener_directorio_reportes(self):

        sistema = platform.system()

        if sistema == "Windows":
            directorio = os.path.join(os.getenv("USERPROFILE"), "Documents")

        elif sistema in ["Darwin", "Linux"]:  # macOS y Linux
            directorio = os.path.join(os.getenv("HOME"), "Documents")

        else:
            directorio = tempfile.gettempdir()  # como último recurso

        if not os.path.exists(directorio):
            os.makedirs(directorio)

        return directorio

    def _colorear_filas_panel_horarios(self, actualizar_meters=None):
        """
        Colorea las filas de la tabla según la fase de producción (`StatusID`) y los tiempos estimados.
        También tiene en cuenta la fecha y hora de captura. Si `actualizar_meters` es True, solo actualiza
        los contadores sin modificar los colores en la tabla.
        """
        if not self._fecha_seleccionada():
            return

        if self._coloreando:
            return  # Evita ejecuciones simultáneas

        self._coloreando = True
        ahora = datetime.now()

        # Obtener filas a procesar
        filas = self._modelo.consulta_pedidos if actualizar_meters else
        self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', visibles=True)

    # Reiniciar contadores si estamos actualizando meters
    if actualizar_meters:
        self._modelo.pedidos_retrasados = 0
        self._modelo.pedidos_en_tiempo = 0
        self._modelo.pedidos_a_tiempo = 0

    if not filas:
        self._coloreando = False
        return

    # Definir colores
    colores = {
        1: 'green',  # Pedido a tiempo o programado para otro día
        2: 'orange',  # Pedido próximo a la entrega (tiempo intermedio)
        3: 'red',  # Urgente o con muy poco tiempo para entrega / cancelado
        4: 'blue',  # Entregado o en ruta con poco tiempo para entrega
        5: 'purple',  # Pago pendiente por confirmar
        6: 'lightgreen',  # Transferencia confirmada
        7: 'lightblue'  # En ruta, entregado o en cartera
    }

    for i, fila in enumerate(filas):
        valores_fila = {
            'PriorityID': fila['PriorityID'],
            'Cancelled': fila['Cancelado'],
            'FechaEntrega': fila['FechaEntrega'] if actualizar_meters else fila['F.Entrega'],
            'HoraEntrega': fila['HoraCaptura'] if actualizar_meters else fila['H.Entrega'],
            'StatusID': fila['TypeStatusID'],
            'OrderDeliveryTypeID': fila['OrderDeliveryTypeID'],
            'PaymentConfirmedID': fila['PaymentConfirmedID']

        }
        status_pedido = self.utilerias.determinar_color_fila_respecto_entrega_pedido(valores_fila, ahora)

        color = colores[status_pedido]

        if actualizar_meters:
            if status_pedido in (1, 4):
                self._modelo.pedidos_en_tiempo += 1
            elif status_pedido == 2:
                self._modelo.pedidos_a_tiempo += 1
            elif status_pedido == 3:
                self._modelo.pedidos_retrasados += 1
        else:
            self._interfaz.ventanas.colorear_filas_table_view('tbv_pedidos', [i], color)

    if actualizar_meters:
        self._rellenar_meters()

    self._coloreando = False


def _obtener_valores_cbx_filtros(self):
    # Obtener valores actuales de los filtros
    vlr_cbx_captura = self._interfaz.ventanas.obtener_input_componente('cbx_capturista')
    vlr_cbx_horarios = self._interfaz.ventanas.obtener_input_componente('cbx_horarios')
    vlr_cbx_status = self._interfaz.ventanas.obtener_input_componente('cbx_status')

    return {'cbx_capturista': vlr_cbx_captura, 'cbx_horarios': vlr_cbx_horarios, 'cbx_status': vlr_cbx_status}


def _settear_valores_cbx_filtros(self, valores_cbx_filtros):
    vlr_cbx_captura = valores_cbx_filtros['cbx_capturista']
    vlr_cbx_horarios = valores_cbx_filtros['cbx_horarios']
    vlr_cbx_status = valores_cbx_filtros['cbx_status']

    # Aplicar filtros solo si el usuario ha seleccionado un valor específico
    if vlr_cbx_captura != 'Seleccione':
        self._interfaz.ventanas.insertar_input_componente('cbx_capturista', vlr_cbx_captura)

    if vlr_cbx_horarios != 'Seleccione':
        self._interfaz.ventanas.insertar_input_componente('cbx_horarios', vlr_cbx_horarios)

    if vlr_cbx_status != 'Seleccione':
        self._interfaz.ventanas.insertar_input_componente('cbx_status', vlr_cbx_status)


def _actualizar_pedidos(self, fecha=None, criteria=True, refresh=False, despues_de_capturar_pedido=False):
    if self._actualizando_tabla:
        return

    try:
        self._actualizando_tabla = True

        # 1) Limpia filtros visuales si lo pides
        self._interfaz.ventanas.limpiar_filtros_table_view('tbv_pedidos', criteria)

        # 2) Reconsulta si hay refresh, cambiaste fecha o no hay caché
        if refresh or (fecha is not None) or not getattr(self._modelo, 'consulta_pedidos', None):
            consulta = self._modelo.buscar_pedidos(fecha)
            self._modelo.consulta_pedidos = consulta
        else:
            consulta = self._modelo.consulta_pedidos

        if not consulta:
            self._limpiar_tabla()
            return

        # 3) Guarda selección actual del usuario (antes de repoblar combos)
        seleccion_previa = self._obtener_valores_cbx_filtros()

        # 4) Construye opciones de filtros desde la data FRESCA y repuebla combos
        #    - limpia None, strip y de-duplica
        def _norm_set(iterable):
            vistos, res = set(), []
            for v in iterable:
                if v is None:
                    continue
                s = str(v).strip()
                if s and s not in vistos:
                    vistos.add(s)
                    res.append(s)
            return sorted(res)

        capturistas = _norm_set(f['CapturadoPor'] for f in consulta)
        horarios = _norm_set(f['HoraEntrega'] for f in consulta)
        status = _norm_set(f['Status'] for f in consulta)

        # repoblar (usa tu Ventanas.rellenar_cbx(nombre_cbx, valores, sin_seleccione=None))
        self._rellenar_cbx_captura(capturistas)
        self._rellenar_cbx_horarios(horarios)
        self._rellenar_cbx_status(status)

        # 5) Restaura selección previa o aplica "prefiltro post-captura"
        print(self._capturando_nuevo_pedido)
        if self._capturando_nuevo_pedido:
            # capturista = yo
            self._interfaz.ventanas.insertar_input_componente('cbx_capturista', self._user_name)

            # status = alguna variante de "abierto" si existe
            abiertos_posibles = {'abierto', 'abierta', 'open'}
            candidato_abierto = next((s for s in status if s.strip().lower() in abiertos_posibles), None)
            self._interfaz.ventanas.insertar_input_componente('cbx_status', candidato_abierto or 'Seleccione')

            # horario = 'Seleccione'
            self._interfaz.ventanas.insertar_input_componente('cbx_horarios', 'Seleccione')
            print('aqui debieramos filtrar abierto')
            self._capturando_nuevo_pedido = False
        else:
            # restaura selección previa usando tu setter robusto
            print('aqui no filtramos abiertos')
            self._interfaz.ventanas.insertar_input_componente('cbx_capturista',
                                                              seleccion_previa.get('cbx_capturista', 'Seleccione'))
            self._interfaz.ventanas.insertar_input_componente('cbx_horarios',
                                                              seleccion_previa.get('cbx_horarios', 'Seleccione'))
            self._interfaz.ventanas.insertar_input_componente('cbx_status',
                                                              seleccion_previa.get('cbx_status', 'Seleccione'))

        # 6) Aplica filtros según lo que haya en los combos AHORA
        valores = self._obtener_valores_cbx_filtros()
        consulta_filtrada = self._filtrar_consulta_sin_rellenar(
            consulta, valores, despues_de_captura=despues_de_capturar_pedido
        )

        # 7) Pinta la tabla
        self._interfaz.ventanas.rellenar_table_view(
            'tbv_pedidos',
            self._interfaz.crear_columnas_tabla(),
            consulta_filtrada
        )

        self._colorear_filas_panel_horarios(actualizar_meters=True)

    finally:
        self._actualizando_tabla = False


def _filtrar_consulta_sin_rellenar(self, consulta, valores, despues_de_captura=False):
    """Filtra en una sola pasada; NO toca combos."""
    # Prioridad: "sin procesar"
    if self._interfaz.ventanas.obtener_input_componente('chk_sin_procesar') == 1:
        self._interfaz.ventanas.limpiar_componentes('den_fecha')
        return self._modelo.buscar_pedidos_sin_procesar()

    if despues_de_captura:
        usuario = self._user_name
        return [f for f in consulta
                if f.get('CapturadoPor') == usuario and f.get('Status') == 'Abierto']

    # Filtros normales desde combos
    vlr_cbx_captura = valores.get('cbx_capturista')
    vlr_cbx_horarios = valores.get('cbx_horarios')
    vlr_cbx_status = valores.get('cbx_status')

    # Predicados solo si el usuario eligió algo distinto a 'Seleccione'
    filtrar_captura = (vlr_cbx_captura and vlr_cbx_captura != 'Seleccione')
    filtrar_horario = (vlr_cbx_horarios and vlr_cbx_horarios != 'Seleccione')
    filtrar_status = (vlr_cbx_status and vlr_cbx_status != 'Seleccione')

    if not (filtrar_captura or filtrar_horario or filtrar_status):
        return consulta

    def ok(f):
        if filtrar_captura and f.get('CapturadoPor') != vlr_cbx_captura:
            return False
        if filtrar_horario and f.get('HoraEntrega') != vlr_cbx_horarios:
            return False
        if filtrar_status and f.get('Status') != vlr_cbx_status:
            return False
        return True

    return [f for f in consulta if ok(f)]


def _filtrar_consulta(self, consulta, valores_cbx_filtros):
    # Si el checkbox está activado, solo devolver los pedidos sin procesar
    if self._interfaz.ventanas.obtener_input_componente('chk_sin_procesar') == 1:
        self._interfaz.ventanas.limpiar_componentes('den_fecha')
        return self._modelo.buscar_pedidos_sin_procesar()

    vlr_cbx_captura = valores_cbx_filtros['cbx_capturista']
    vlr_cbx_horarios = valores_cbx_filtros['cbx_horarios']
    vlr_cbx_status = valores_cbx_filtros['cbx_status']

    # Extraer valores únicos de los campos para actualizar los filtros
    capturistas = {fila['CapturadoPor'] for fila in consulta}
    horarios = {fila['HoraEntrega'] for fila in consulta}
    status = {fila['Status'] for fila in consulta}

    self._rellenar_cbx_status(status)
    self._rellenar_cbx_horarios(horarios)
    self._rellenar_cbx_captura(capturistas)

    # Aplicar filtros solo si el usuario ha seleccionado un valor específico
    if vlr_cbx_captura and vlr_cbx_captura != 'Seleccione':
        consulta = [fila for fila in consulta if fila['CapturadoPor'] == vlr_cbx_captura]

    if vlr_cbx_horarios and vlr_cbx_horarios != 'Seleccione':
        consulta = [fila for fila in consulta if fila['HoraEntrega'] == vlr_cbx_horarios]

    if vlr_cbx_status and vlr_cbx_status != 'Seleccione':
        consulta = [fila for fila in consulta if fila['Status'] == vlr_cbx_status]

    return consulta


def _limpiar_tabla(self):
    """Limpia la tabla y restablece los contadores de métricas"""
    tabla = self._interfaz.ventanas.componentes_forma['tbv_pedidos']
    for campo in ['mtr_total', 'mtr_en_tiempo', 'mtr_a_tiempo', 'mtr_retrasado']:
        self._interfaz.ventanas.insertar_input_componente(campo, (1, 0))
    tabla.delete_rows()


def _capturar_nuevo_cliente(self):
    self._pausar_autorefresco()
    try:
        self.parametros.id_principal = -1
        self._interfaz.master.iconify()
        ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
        instancia = PanelPrincipal(ventana, self.parametros, self.base_de_datos, self.utilerias)
        ventana.wait_window()
    finally:
        self.parametros.id_principal = 0
        self._reanudar_autorefresco()


def _capturar_nuevo_pedido(self):
    self._pausar_autorefresco()

    try:
        self._capturando_nuevo_pedido = True
        self._master.iconify()

        ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(
            ocultar_master=True,
            master=self._interfaz.master
        )

        self.parametros.id_principal = -1
        _ = BuscarGeneralesCliente(ventana, self.parametros)


    finally:
        self.parametros.id_principal = 0

        # 👉 aquí SIEMPRE entras al cerrar captura (ver ajuste en BuscarGenerales abajo)
        self._actualizar_pedidos(
            fecha=self._fecha_seleccionada(),
            refresh=True,
            despues_de_capturar_pedido=True
        )
        self._reanudar_autorefresco()


def _editar_caracteristicas(self):
    self._pausar_autorefresco()
    try:
        fila = self._seleccionar_una_fila()
        if not fila:
            return

        status = fila[0]['TypeStatusID']

        if status == 10:
            self._interfaz.ventanas.mostrar_mensaje('NO se pueden editar pedidos cancelados.')
            return

        elif status >= 4:
            self._interfaz.ventanas.mostrar_mensaje(
                'Sólo se pueden afectar las caracteristicas de un pedido hasta el status  Por timbrar.')
            return
        else:
            order_document_id = fila[0]['OrderDocumentID']
            self.parametros.id_principal = order_document_id

            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
            instancia = EditarCaracteristicasPedido(ventana, self.parametros, self.base_de_datos, self.utilerias)
            ventana.wait_window()

            self.parametros.id_principal = 0
            self._actualizar_pedidos(self._fecha_seleccionada())
    finally:
        self._reanudar_autorefresco()


def _crear_ticket(self):
    self._pausar_autorefresco()
    try:
        fila = self._seleccionar_una_fila()
        if not fila:
            return

        order_document_id = fila[0]['OrderDocumentID']
        consulta = self.base_de_datos.fetchall("""
                SELECT
                 CASE WHEN DeliveryPromise IS NULL THEN 0 ELSE 1 END StatusEntrega,
                    DeliveryPromise FechaEntrega
                FROM docDocumentOrderCayal 
                WHERE OrderDocumentID = ?
                """, (order_document_id,))
        status_entrega = consulta[0]['StatusEntrega']

        if status_entrega == 0:
            self._interfaz.ventanas.mostrar_mensaje(
                'Debe definir la forma de pago del cliente antes de generar el ticket.')
            return
        else:
            fecha_entrega = self.utilerias.convertir_fecha_str_a_datetime(str(consulta[0]['FechaEntrega'])[0:10])
            if fecha_entrega > self._modelo.hoy:
                respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                    'EL pedido es para una fecha de entrega posterior, ¿Desea actualizar los precios antes de generar el ticket?')

                if respuesta:
                    self.base_de_datos.actualizar_precios_pedido(order_document_id)

            self.parametros.id_principal = order_document_id
            instancia = TicketPedidoCliente(self.base_de_datos, self.utilerias, self.parametros)

            self.parametros.id_principal = 0
            self._interfaz.ventanas.mostrar_mensaje(master=self._interfaz.master,
                                                    mensaje='Comprobante generado.', tipo='info')
            self._interfaz.master.iconify()
    finally:
        self._reanudar_autorefresco()


def _mandar_a_producir(self):
    filas = self._validar_seleccion_multiples_filas()
    if not filas:
        return

    for fila in filas:
        order_document_id = fila['OrderDocumentID']
        consulta = self.base_de_datos.fetchall("""
                SELECT StatusID, 
                    CASE WHEN DeliveryPromise IS NULL THEN 0 ELSE 1 END Entrega,
                    ISNULL(FolioPrefix,'')+ISNULL(Folio,'') DocFolio
                FROM docDocumentOrderCayal 
                WHERE OrderDocumentID = ?
            """, (order_document_id,))

        status = consulta[0]['StatusID']
        entrega = consulta[0]['Entrega']
        folio = consulta[0]['DocFolio']

        if entrega == 0:
            self._interfaz.ventanas.mostrar_mensaje(
                f'Debe usar la herramienta de editar características para el pedido {folio}.')
            continue

        if status == 1:
            self.base_de_datos.command("""
                     UPDATE docDocumentOrderCayal SET SentToPrepare = GETDATE(),
                                                    SentToPrepareBy = ?,
                                                    StatusID = 2,
                                                    UserID = NULL
                    WHERE OrderDocumentID = ?
                """, (self._user_id, order_document_id,))

            comentario = f'Enviado a producir por {self._user_name}.'
            self.base_de_datos.insertar_registro_bitacora_pedidos(order_document_id=order_document_id,
                                                                  change_type_id=2,
                                                                  user_id=self._user_id,
                                                                  comments=comentario)

    self._actualizar_pedidos(self._fecha_seleccionada())


def _cobrar_nota(self):
    self._pausar_autorefresco()
    try:
        ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
        instancia = BuscarGeneralesClienteCartera(ventana, self.parametros)
        ventana.wait_window()

        fila = self._seleccionar_una_fila()
        if not fila:
            return

    finally:
        self._reanudar_autorefresco()


def _inciar_facturacion(self):
    self._pausar_autorefresco()
    try:
        self._facturar()
    finally:
        self._actualizar_pedidos(self._fecha_seleccionada())
        self._reanudar_autorefresco()


def _facturar(self):
    filas = self._validar_seleccion_multiples_filas()

    if not filas:
        return

    filas_filtradas_por_status = self._filtrar_filas_facturables_por_status(filas)

    # filtra por status 3 que es por timbrar
    if not filas_filtradas_por_status:
        self._interfaz.ventanas.mostrar_mensaje('No hay pedidos con un status válido para facturar')
        return

    # --------------------------------------------------------------------------------------------------------------
    # aqui comenzamos el procesamiento de las filas a facturar
    # si es una seleccion unica valida primero si no hay otros pendientes del mimsmo cliente
    if len(filas) == 1:
        hay_pedidos_del_mismo_cliente = self._buscar_pedidos_en_proceso_del_mismo_cliente(filas)

        if not hay_pedidos_del_mismo_cliente:
            self._crear_documento(filas)

        if hay_pedidos_del_mismo_cliente:
            respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                'Hay otro pedido del mismo cliente en proceso o por timbrar.'
                '¿Desea continuar?')
            if respuesta:
                self._crear_documento(filas)
        return

    # si hay mas de una fila primero valida que estas filas no tengan solo el mismo cliente
    # si lo tuvieran hay que ofrecer combinarlas en un documento
    tienen_el_mismo_cliente = self._validar_si_los_pedidos_son_del_mismo_cliente(filas)
    if tienen_el_mismo_cliente:
        respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta('Los pedidos son del mismo cliente.'
                                                                     '¿Desea combinarlos?')
        if respuesta:
            self._crear_documento(filas, combinado=True, mismo_cliente=True)
            return

    # del mismo modo que para una fila valida que no existan otras ordenes de un cliente en proceso
    # si lo hay para un cliente ese cliente debe excluirse de la seleccion
    filas_filtradas = self._excluir_pedidos_con_ordenes_en_proceso_del_mismo_cliente(filas)
    if not filas_filtradas:
        return

    self._crear_documento(filas_filtradas)
    self._actualizar_pedidos(self._fecha_seleccionada())
    return


def _crear_documento(self, filas, combinado=False, mismo_cliente=False):
    tipo_documento = 1  # remision

    # determina el tipo de documento que se generará ya sea remision y/o factura
    if len(filas) > 1 and combinado:
        tipos_documento = list(set([fila['DocumentTypeID'] for fila in filas]))
        if len(tipos_documento) == 1:
            tipo_documento = tipos_documento[0]
        else:
            tipo_documento = -1
            while tipo_documento == -1:
                ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
```


## controlador_captura.py

```py
import copy
import datetime
import re

import pyperclip
import logging

from herramientas.herramientas_panel.editar_pedido import AgregarEspecificaciones
from herramientas.herramientas_panel.editar_pedido import AgregarPartidaManualmente
from direccion_cliente import DireccionCliente
from cliente.direcciones_adicionales import DireccionesAdicionales
from historial_cliente import HistorialCliente
from cliente.panel_direcciones import PanelDirecciones
from cliente.formulario_cliente import FormularioCliente
from herramientas.verificador_precios.interfaz_verificador import InterfazVerificador
from herramientas.verificador_precios.controlador_verificador import ControladorVerificador
from editar_partida import EditarPartida


class ControladorCaptura:
    def __init__(self, interfaz, modelo, ofertas=None):

        self._interfaz = interfaz
        self._master = interfaz.master
        self._modelo = modelo
        self._parametros_contpaqi = self._modelo.parametros_contpaqi
        self._ventanas = self._interfaz.ventanas

        self.base_de_datos = self._modelo.base_de_datos
        self._utilerias = self._modelo.utilerias

        self.documento = self._modelo.documento
        self.cliente = self._modelo.cliente

        self._crear_barra_herramientas()

        self.direcciones_cliente = self.base_de_datos.rellenar_cbx_direcciones(self.cliente.business_entity_id)

        self._inicializar_variables_de_instancia()

        self.servicio_a_domicilio_agregado = self._modelo.servicio_a_domicilio_agregado
        self._costo_servicio_a_domicilio = self._modelo.costo_servicio_a_domicilio
        self._partida_servicio_domicilio = None

        self._consulta_productos = None
        self.consulta_productos_ofertados = None

        self._termino_buscado = None

        self._rellenar_controles_interfaz()
        self._cargar_eventos_componentes()
        self._agregar_validaciones()

        if not self._es_documento_bloqueado():
            self._agregar_atajos()

        self._modelo.agregar_servicio_a_domicilio()

        self._rellenar_desde_base_de_datos()

        self._configurar_pedido()
        self._ventanas.enfocar_componente('tbx_clave')
        self._inicializar_captura_manual()

        self._interfaz.ventanas.configurar_ventana_ttkbootstrap(titulo='Nuevo pedido', bloquear=False)
        self._ventanas.situar_ventana_arriba(self._master)
        self._ventanas.enfocar_componente('tbx_buscar_manual')

    def _inicializar_captura_manual(self):
        if self._interfaz.modulo_id not in [1687]:
            return

        if self._es_documento_bloqueado():
            return

        self._procesando_seleccion = False
        self._info_partida_seleccionada = {}
        self._agregando_producto = False

        self._rellenar_componentes_manual()

    def _es_documento_bloqueado(self):
        status_id = 0

        if self._module_id == 1687:
            status_id = self.base_de_datos.fetchone(
                'SELECT ISNULL(StatusID,0) Status FROM docDocumentOrderCayal WHERE OrderDocumentID = ?',
                (self.documento.document_id,)
            )
            status_id = 0 if not status_id else status_id

        if status_id > 2 or self.documento.cancelled_on:
            self._ventanas.bloquear_forma('frame_herramientas')

            estilo_cancelado = {
                'foreground': 'white',
                'background': '#ff8000',
            }

            frame = self._ventanas.componentes_forma['frame_totales']
            widgets = frame.winfo_children()

            for widget in widgets:
                widget.config(**estilo_cancelado)

            return True

        return False

    def _cargar_eventos_componentes(self):
        eventos = {
            'tbx_clave': lambda event: self._agregar_partida(),
            'tvw_productos': (lambda event: self._editar_partida(), 'doble_click'),
            # eventos captura manual
            'btn_ofertas_manual': lambda: self._buscar_ofertas(rellenar_tabla=True),
            'btn_agregar_manual': lambda: self._agregar_partida_manualmente(),
            'btn_copiar_manual': lambda: self._copiar_productos(),
            'btn_especificaciones_manual': lambda: self._agregar_especicificaciones(),

            'tbx_buscar_manual': lambda event: self._buscar_productos_manualmente(),
            'tbx_cantidad_manual': lambda event: self._selecionar_producto_tabla_manual(),

            'chk_monto': lambda *args: self._selecionar_producto_tabla_manual(),
            'chk_pieza': lambda *args: self._selecionar_producto_tabla_manual(),
            'tvw_productos_manual': (
                lambda event: self._selecionar_producto_tabla_manual(configurar_forma=True), 'seleccion'),
        }

        self._ventanas.cargar_eventos(eventos)

        evento_adicional = {
            'tvw_productos': (lambda event: self._eliminar_partida(), 'suprimir'),
        }
        self._ventanas.cargar_eventos(evento_adicional)

        txt_comentario_pedido = self._ventanas.componentes_forma['txt_comentario_documento']
        txt_comentario_pedido.bind("<FocusOut>", lambda event: self._actualizar_comentario_pedido())

    def _actualizar_comentario_pedido(self):
        comentario = self._ventanas.obtener_input_componente('txt_comentario_documento')
        comentario = comentario.upper().strip() if comentario else ''
        self.documento.comments = comentario

    def _agregar_validaciones(self):
        self._ventanas.agregar_validacion_tbx('tbx_clave', 'codigo_barras')
        self._ventanas.agregar_validacion_tbx('tbx_cantidad_manual', 'cantidad')

    def _agregar_atajos(self):
        eventos = {
            'F2': lambda: self._editar_partida(),
            'F3': lambda: self._verificador_precios(),
            'F4': lambda: self._editar_direccion(),
            'F5': lambda: self._agregar_direccion(),
            'F6': lambda: self._editar_cliente(),
            'F7': lambda: self._historial_cliente,

            'F8': lambda: self._agregar_partida_manualmente(),
            'F9': lambda: self._copiar_productos(),
            'F10': lambda: self._activar_chk_pieza(),
            'F11': lambda: self._activar_chk_monto(),
            'F12': lambda: self._buscar_ofertas(),

            'Ctrl+B': lambda: self._ventanas.enfocar_componente('tbx_buscar_manual'),
            'Ctrl+C': lambda: self._ventanas.enfocar_componente('tbx_cantidad_manual'),
            'Ctrl+F': lambda: self._ventanas.enfocar_componente('cbx_tipo_busqueda_manual'),
            'Ctrl+M': lambda: self._ventanas.enfocar_componente('txt_comentario_manual'),
            'Ctrl+T': lambda: self._ventanas.enfocar_componente('tvw_productos_manual'),
            'Ctrl+P': lambda: self._ventanas.enfocar_componente('txt_portapapeles_manual'),
            'Ctrl+E': lambda: self._agregar_especicificaciones(),

        }
        self._ventanas.agregar_hotkeys_forma(eventos)
        if self._parametros_contpaqi.id_modulo != 1687:
            evento_adicional = {
                'F1': lambda: self._agregar_partida_manualmente_popup(),
            }
            self._ventanas.agregar_hotkeys_forma(evento_adicional)

    def _inicializar_variables_de_instancia(self):
        self._iconos_barra_herramientas = []
        self._module_id = self._parametros_contpaqi.id_modulo
        self._user_id = self._parametros_contpaqi.id_usuario

        if self.documento.document_id > 0:
            self._user_name = self.base_de_datos.buscar_nombre_de_usuario(self.documento.created_by)

        if self.documento.document_id < 1:
            self._user_name = self._parametros_contpaqi.nombre_usuario

        self._consulta_uso_cfdi = []
        self._consulta_formas_pago = []
        self._consulta_metodos_pago = []
        self._consulta_regimenes = []

    def _rellenar_controles_interfaz(self):
        self._cargar_direccion_cliente()
        self._cargar_nombre_cliente()
        self._cargar_informacion_crediticia()

        self._ventanas.insertar_input_componente('lbl_captura', self._user_name)
        self._ventanas.insertar_input_componente('lbl_folio', self.documento.docfolio)

        nombre_modulo = self._cargar_nombre_modulo()
        self._ventanas.insertar_input_componente('lbl_modulo', nombre_modulo)

    def _copiar_portapapeles(self):
        try:
            # Intentamos obtener el texto del portapapeles
            texto = pyperclip.paste()
            logging.info("Texto obtenido del portapapeles: %s", texto)
            return texto
        except Exception as e:
            # Si ocurre algún error, lo registramos
            logging.error("Error al obtener el texto del portapapeles: %s", e)
            return None

    def _cargar_direccion_cliente(self):
        datos_direccion = self.documento.address_details
        self.documento.address_detail_id = datos_direccion['address_detail_id']
        self.documento.order_parameters['AddressDetailID'] = datos_direccion['address_detail_id']

        calle = datos_direccion.get('calle', '')
        numero = datos_direccion.get('numero', '')
        colonia = datos_direccion.get('colonia', '')
        cp = datos_direccion.get('cp', '')
        municipio = datos_direccion.get('municipio', '')
        estado = datos_direccion.get('estado', '')
        comentario = datos_direccion.get('comentario', '')

        texto_direccion = f'{calle} NUM.{numero}, COL.{colonia}, MPIO.{municipio}, EDO.{estado}, C.P.{cp}'
        texto_direccion = texto_direccion.upper()
        self._ventanas.insertar_input_componente('tbx_direccion', texto_direccion)
        self._ventanas.bloquear_componente('tbx_direccion')

        self._ventanas.insertar_input_componente('tbx_comentario', comentario)
        self._ventanas.bloquear_componente('tbx_comentario')

    def _cargar_nombre_cliente(self):
        nombre = self.cliente.official_name
        nombre_comercial = self.cliente.commercial_name
        sucursal = self.documento.depot_name
        nombre_direccion = self.documento.address_name

        sucursal = f'({nombre_direccion})' if not sucursal else f'({sucursal})'
        nombre_comercial = '' if not nombre_comercial else f'-{nombre_comercial}-'

        nombre_cliente = f'{nombre} {nombre_comercial} {sucursal}'
        self._ventanas.insertar_input_componente('tbx_cliente', nombre_cliente)
        self._ventanas.bloquear_componente('tbx_cliente')

    def _cargar_nombre_modulo(self):

        nombre_modulo = {1687: 'PEDIDOS',
                         21: 'MAYOREO',
                         1400: 'MINISUPER',
                         158: 'VENTAS',
                         1316: 'NOTAS',
                         1319: 'GLOBAL',
                         202: 'ENTRADA',
                         203: 'SALIDA'
                         }

        return nombre_modulo.get(self._module_id, 'CAYAL')

    def _cargar_informacion_crediticia(self):

        if self.cliente.credit_block == 1:
            estilo = {
                'foreground': '#E30421',
                'background': '#E30421',
                'font': ('Consolas', 14, 'bold'),
                # 'anchor': 'center'
            }

            nombres = ['lbl_credito_texto', 'lbl_restante_texto', 'lbl_debe_texto',
                       'lbl_credito', 'lbl_restante', 'lbl_debe'
                       ]
            for nombre in nombres:
                componente = self._ventanas.componentes_forma.get(nombre, None)
                if componente:
                    componente.config(**estilo)

        if self.cliente.credit_block == 0:
            if self.cliente.authorized_credit > 0 and self.cliente.remaining_credit > 0:
                valores = {'authorized_credit': 'lbl_credito',
                           'remaining_credit': 'lbl_restante',
                           'debt': 'lbl_debe'
                           }

                for atributo, label in valores.items():
                    monto = getattr(self.cliente, atributo)
                    monto_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(monto)
                    monto_moneda = self._utilerias.convertir_decimal_a_moneda(monto_decimal)

                    self._ventanas.insertar_input_componente(label, monto_moneda)

    def _agregar_partida_por_clave_producto(self, clave):
        if not self._utilerias.es_codigo_barras(clave):
            self._modelo.mensajes_de_error(7)
            return

        valores_clave = self._utilerias.validar_codigo_barras(clave)
        codigo_barras = valores_clave.get('clave', None)
        cantidad = valores_clave.get('cantidad', 1)

        consulta_producto = self._modelo.buscar_productos(codigo_barras, 'Término')

        if not consulta_producto:
            self._modelo.mensajes_de_error(8)
            return

        producto_id = self._modelo.obtener_product_ids_consulta(consulta_producto)

        info_producto = self._modelo.buscar_info_productos_por_ids(producto_id, no_en_venta=True)

        if not info_producto:
            existencia = self.base_de_datos.buscar_existencia_productos(producto_id)

            if not existencia:
                self._modelo.mensajes_de_error(11)
                return

            self._modelo.mensajes_de_error(9)
            return

        disponible_a_venta = info_producto[0]['AvailableForSale']
        if disponible_a_venta == 0:
            self._modelo.mensajes_de_error(10)
            return

        partida = self._utilerias.crear_partida(info_producto[0], cantidad)

        unidad_cayal = 0 if info_producto[0]['ClaveUnidad'] == 'KGM' else 1  # Del control de captura manual
        partida['Comments'] = ''

        self._modelo.agregar_partida_tabla(partida, document_item_id=0, tipo_captura=0, unidad_cayal=unidad_cayal,
                                           monto_cayal=0)

        self._ventanas.limpiar_componentes('tbx_clave')

    def _configurar_pedido(self):
        if self.documento.document_id < 1:
            valores_pedido = {}
            valores_pedido['OrderTypeID'] = 1
            valores_pedido['CreatedBy'] = self._parametros_contpaqi.id_usuario
            valores_pedido['CreatedOn'] = datetime.datetime.now()
            comentario_pedido = self.documento.comments
            valores_pedido['CommentsOrder'] = comentario_pedido.upper().strip() if comentario_pedido else ''
            valores_pedido['BusinessEntityID'] = self.cliente.business_entity_id
            related_order_id = 0
            valores_pedido['RelatedOrderID'] = related_order_id
            valores_pedido['ZoneID'] = self.cliente.zone_id
            valores_pedido['SubTotal'] = 0
            valores_pedido['TotalTax'] = 0
            valores_pedido['Total'] = 0
            valores_pedido['HostName'] = self._utilerias.obtener_hostname()
            valores_pedido['AddressDetailID'] = self.documento.address_detail_id
            valores_pedido['DocumentTypeID'] = self.documento.cfd_type_id
            valores_pedido['OrderDeliveryCost'] = self.documento.delivery_cost
            valores_pedido['DepotID'] = self.documento.depot_id

            way_to_pay_id = valores_pedido.get('WayToPayID', 1)
            payment_confirmed_id = 1
            delivery_type_id = valores_pedido.get('OrderDeliveryTypeID', 1)

            # si la forma de pago es transferencia el id es transferencia no confirmada
            if way_to_pay_id == 6:
                payment_confirmed_id = 2

            # si el tipo de entrga es viene y la fomra de pago NO es transferencia entonces la forma de pago es en tienda
            if delivery_type_id == 2 and way_to_pay_id != 6:
                payment_confirmed_id = 4

            valores_pedido['PaymentConfirmedID'] = payment_confirmed_id

            self.parametros_pedido = valores_pedido
            self.documento.order_parameters = valores_pedido

    def _rellenar_desde_base_de_datos(self):
        if self.documento.document_id < 1:
            return

        # rellenar comentarios documento
        self._ventanas.insertar_input_componente('txt_comentario_documento', self.documento.comments)

        # rellena la informacion relativa a las partidas
        partidas = self.base_de_datos.buscar_partidas_pedidos_produccion_cayal(self.documento.document_id,
                                                                               partidas_producidas=True)

        for partida in partidas:
            # Crear una copia profunda para evitar referencias pegadas
            partida_copia = copy.deepcopy(partida)

            piezas = partida_copia.get('CayalPiece', 0)
            chk_pieza = 1 if piezas != 0 else 0

            chk_monto = partida_copia.get('CayalAmount', 0)
            tipo_captura = partida_copia.get('TipoCaptura', 0)
            document_item_id = partida_copia.get('DocumentItemID', 0)

            # Modificar la copia en lugar del objeto original
            partida_copia['ItemProductionStatusModified'] = 0

            # Procesar la copia para evitar referencias compartidas
            partida_procesada = self._utilerias.crear_partida(partida_copia)

            self._modelo.agregar_partida_tabla(partida_procesada, document_item_id=document_item_id,
                                               tipo_captura=tipo_captura,
                                               unidad_cayal=chk_pieza, monto_cayal=chk_monto)

    def _agregar_partida(self):
        clave = self._ventanas.obtener_input_componente('tbx_clave')
        self._agregar_partida_por_clave_producto(clave)

    def _agregar_partida_manualmente_popup(self):
        ventana = self._ventanas.crear_popup_ttkbootstrap(master=self._master, titulo='Captura Manual')
        portapapeles = self._copiar_portapapeles()
        instancia = AgregarPartidaManualmente(ventana,
                                              self._modelo,
                                              self.documento,
                                              self._ventanas.componentes_forma,
                                              portapapeles,
                                              )
        ventana.wait_window()
        self.documento = instancia.documento

    def _agregar_partida_manualmente(self):
        if not self._tabla_manual_con_seleccion_valida():
            print('no hay un producto seleccionable')
            return

        cantidad_control = self._obtener_cantidad_partida_manual()

        if cantidad_control <= 0:
            print('cantidad es cero')
            return

        if not self._agregando_producto:

            try:
                self._agregando_producto = True
                info_partida_seleccionada = copy.deepcopy(self._info_partida_seleccionada)
                valores_partida = self._calcular_valores_partida(info_partida_seleccionada)

                cantidad = valores_partida['cantidad']

                partida = self._utilerias.crear_partida(info_partida_seleccionada, cantidad)

                chk_pieza = self._ventanas.obtener_input_componente('chk_pieza')
                chk_monto = self._ventanas.obtener_input_componente('chk_monto')
                comentarios = self._ventanas.obtener_input_componente('txt_comentario_manual')

                partida['Comments'] = comentarios

                if chk_pieza == 1 and partida['CayalPiece'] % 1 != 0:
                    self._ventanas.mostrar_mensaje('La cantidad de piezas deben ser valores no fraccionarios.')
                    return

                self._modelo.agregar_partida_tabla(partida, document_item_id=0, tipo_captura=1, unidad_cayal=chk_pieza,
                                                   monto_cayal=chk_monto)

                self._ventanas.insertar_input_componente('tbx_cantidad_manual', 1)
                self._ventanas.limpiar_componentes('txt_comentario_manual')
                self._ventanas.limpiar_componentes('tbx_buscar_manual')
                self._ventanas.enfocar_componente('tbx_buscar_manual')

            finally:
                self._agregando_producto = False

    def _editar_direccion(self):

        if self.cliente.addresses == 1:
            self._llamar_instancia_direccion_adicionanl()
            return
        ventana = self._ventanas.crear_popup_ttkbootstrap(self._master, 'Editar Dirección')
        instancia = DireccionCliente(ventana,
                                     self.documento,
                                     self.base_de_datos,
                                     self._ventanas.componentes_forma)
        ventana.wait_window()
        self._cargar_direccion_cliente()
        self._cargar_nombre_cliente()

    def _agregar_direccion(self):
        if self.cliente.addresses == 1:
            self._llamar_instancia_direccion_adicionanl()
            return
        ventana = self._ventanas.crear_popup_ttkbootstrap(self._master, 'Direcciones cliente')
        instancia = PanelDirecciones(ventana,
                                     self._parametros_contpaqi,
                                     self.cliente)
        ventana.wait_window()

        # comprobar si la direccion actual no esta borrada en cuyo defecto actualizar a la direccion
        # fiscal del cliente y hacer lo mismo con la sucursal si aplica
        esta_borrada = self._direccion_esta_borrada(self.documento.address_detail_id)

        if esta_borrada:
            self.documento.address_detail_id = instancia.address_fiscal_detail_id
            direccion = self.base_de_datos.buscar_detalle_direccion_formateada(self.documento.address_detail_id)
            self.documento.address_details = direccion
            self.documento.depot_name = ''
            self.documento.depot_id = 0
            self.documento.address_name = 'Dirección Fiscal'

            self._cargar_direccion_cliente()
            self._cargar_nombre_cliente()

        self.cliente.addresses = instancia.numero_direcciones

    def _direccion_esta_borrada(self, address_detail_id):
        direccion = self.base_de_datos.fetchone("""
                SELECT * FROM orgAddress WHERE AddressDetailID = ? AND DeletedOn IS NULL
                """, (address_detail_id,))

        if not direccion:
            return True

        return False

    def _llamar_instancia_direccion_adicionanl(self):
        ventana = self._ventanas.crear_popup_ttkbootstrap(self._master, 'Dirección')
        instancia = DireccionesAdicionales(
            ventana,
            self._parametros_contpaqi,
            self.direcciones_cliente,
            'agregar'
        )
        ventana.wait_window()
        direcciones_adicionales = instancia.direcciones_adicionales
        numero_direcciones = self.base_de_datos.actualizar_direcciones_panel_direcciones(
            direcciones_adicionales,
            self.cliente.business_entity_id,
            self._parametros_contpaqi.id_usuario
        )
        self.cliente.addresses = int(numero_direcciones)

    def _editar_cliente(self):

        self._parametros_contpaqi.id_principal = self.cliente.business_entity_id

        ventana = self._ventanas.crear_popup_ttkbootstrap(self._master, 'Cliente')
        tipo_captura = 'Remisión' if self.cliente.official_number == 'XAXX010101000' else 'Factura'
        parametros_cliente = {'TipoCaptura': tipo_captura}
        instancia = FormularioCliente(ventana,
                                      self._parametros_contpaqi,
                                      parametros_cliente,
                                      self.cliente)
        ventana.wait_window()

    def _eliminar_partida(self):
        filas = self._ventanas.obtener_seleccion_filas_treeview('tvw_productos')
        if not filas:
            return

        if filas:
            if not self._ventanas.mostrar_mensaje_pregunta('¿Desea eliminar las partidas seleccionadas?'):
                return

            production_status_modified = 0
            for fila in filas:
                valores_fila = self._ventanas.procesar_fila_treeview('tvw_productos', fila)
                product_id = valores_fila['ProductID']

                # la eliminacion del servicio a domicilio es de forma automatizada
                if product_id == 5606 and self._module_id == 1687:
                    self._modelo.mensajes_de_error(13)
                    return

                document_item_id = valores_fila['DocumentItemID']
                identificador = valores_fila['UUID']

                # si aplica remover de la bd
                if document_item_id != 0:
                    self.base_de_datos.exec_stored_procedure(
                        'zvwBorrarPartidasDocumentoCayal', (self.documento.document_id,
                                                            self._parametros_contpaqi.id_modulo,
                                                            document_item_id,
                                                            self._parametros_contpaqi.id_usuario)
                    )

                # remover del treeview
                self._ventanas.remover_fila_treeview('tvw_productos', fila)

                # ----------------------------------------------------------------------------------
                # remover la partida de los items del documento

                # filtrar de los items del documento
                partida_items = [partida for partida in self.documento.items
                                 if str(identificador) == str(partida['uuid'])][0]

                nuevas_partidas = [partida for partida in self.documento.items
                                   if str(identificador) != str(partida['uuid'])]

                # asignar los nuevos items sin el item que ha sido removido
                self.documento.items = nuevas_partidas
                self._modelo.actualizar_totales_documento()
                # ----------------------------------------------------------------------------------

                # respalda la partida extra para tratamiento despues del cierre del documento
                comentario = f'ELIMINADA POR {self._user_name}'
                self._modelo.agregar_partida_items_documento_extra(partida_items, 'eliminar', comentario, identificador)

                # Solo aplica para el módulo 1687 pedidos
                if self._module_id == 1687:
                    # Si el total es menor a 200 y no se ha agregado aún, lo agrega
                    if self.documento.total < 200 and not self.servicio_a_domicilio_agregado:
                        self._modelo.agregar_servicio_a_domicilio()
                        self.servicio_a_domicilio_agregado = True

                    # Si ya se agregó pero ahora el total (sin el servicio) es >= 200, lo remueve
                    elif self.servicio_a_domicilio_agregado and (
                            self.documento.total - self._costo_servicio_a_domicilio) >= 200:
                        self._modelo.remover_servicio_a_domicilio()
                        self.servicio_a_domicilio_agregado = False

    def _editar_partida(self):
        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_productos')

        if not fila:
            self._ventanas.mostrar_mensaje('Debe seleccionar por lo menos un producto')
            return

        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_productos'):
            self._ventanas.mostrar_mensaje('Debe seleccionar por lo menos un producto')
            return

        valores_fila = self._ventanas.procesar_fila_treeview('tvw_productos', fila)
        if valores_fila['ProductID'] == 5606:
            self._ventanas.mostrar_mensaje('No se puede editar la partida servicio a domicilio.')
            return

        ventana = self._ventanas.crear_popup_ttkbootstrap(self._master, 'Editar partida')
        instancia = EditarPartida(ventana, self._interfaz, self._modelo, self._utilerias, self.base_de_datos,
                                  valores_fila)
        ventana.wait_window()

    def _verificador_precios(self):
        ventana = self._ventanas.crear_popup_ttkbootstrap(self._master)
        vista = InterfazVerificador(ventana)
        controlador = ControladorVerificador(vista, self._parametros_contpaqi)

    def _historial_cliente(self):
        ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
        instancia = HistorialCliente(ventana,
                                     self._modelo.base_de_datos,
                                     self._utilerias,
                                     self.cliente.business_entity_id
                                     )
        ventana.wait_window()

    def _crear_barra_herramientas(self):

        # herramientas de pedidos
        if self._parametros_contpaqi.id_modulo == 1687:
            self.barra_herramientas_pedido = [
                # {'nombre_icono': 'Product32.ico', 'etiqueta': 'C.Manual', 'nombre': 'captura_manual',
                # 'hotkey': '[F1]', 'comando': self._agregar_partida_manualmente_popup},

                {'nombre_icono': 'ProductChange32.ico', 'etiqueta': 'Editar', 'nombre': 'editar_partida',
                 'hotkey': '[F2]', 'comando': self._editar_partida},

                {'nombre_icono': 'Cancelled32.ico', 'etiqueta': 'Eliminar', 'nombre': 'eliminar_partida',
                 'hotkey': '[SUPR]', 'comando': self._eliminar_partida},

                {'nombre_icono': 'Barcode32.ico', 'etiqueta': 'V.Precios', 'nombre': 'verificador_precios',
                 'hotkey': '[F3]', 'comando': self._verificador_precios},

                {'nombre_icono': 'EditAddress32.ico', 'etiqueta': 'E.Dirección', 'nombre': 'editar_direccion',
                 'hotkey': '[F4]', 'comando': self._editar_direccion},

                {'nombre_icono': 'Address32.ico', 'etiqueta': 'A.Dirección', 'nombre': 'agregar_direccion',
                 'hotkey': '[F5]', 'comando': self._agregar_direccion},

                {'nombre_icono': 'DocumentEdit32.ico', 'etiqueta': 'Editar Cliente', 'nombre': 'editar_cliente',
                 'hotkey': '[F6]', 'comando': self._editar_cliente},

                {'nombre_icono': 'CampaignFlow32.ico', 'etiqueta': 'H.Cliente', 'nombre': 'historial_cliente',
                 'hotkey': '[F7]', 'comando': self._historial_cliente},

            ]

        self.elementos_barra_herramientas = self._ventanas.crear_barra_herramientas(self.barra_herramientas_pedido,
                                                                                    'frame_herramientas')
        self.iconos_barra_herramientas = self.elementos_barra_herramientas[0]
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]

    def _buscar_ofertas(self, rellenar_tabla=True):

        if not self._modelo.consulta_productos_ofertados:
            self._modelo.buscar_productos_ofertados_cliente()

        if rellenar_tabla:
            self._modelo.consulta_productos = self._modelo.consulta_productos_ofertados_btn
            self._rellenar_tabla_productos_manual(self._modelo.consulta_productos)
            self._colorear_productos_ofertados()

    def _colorear_productos_ofertados(self):
        filas = self._ventanas.obtener_filas_treeview('tvw_productos_manual')
        if not filas:
            return

        for fila in filas:
            if not fila:
                continue

            valores_fila = self._ventanas.procesar_fila_treeview('tvw_productos_manual', fila)
            product_id = valores_fila['ProductID']
            producto = str(valores_fila['Descripción'])

            if product_id in self._modelo.products_ids_ofertados:
                producto_actualizado = self._actualizar_nombre_producto_ofertado(producto, product_id)
                valores_fila['Descripción'] = producto_actualizado
                self._ventanas.actualizar_fila_treeview_diccionario('tvw_productos_manual', fila, valores_fila)
                self._ventanas.colorear_fila_seleccionada_treeview('tvw_productos_manual', fila, color='warning')

    def _actualizar_nombre_producto_ofertado(self, producto, product_id):
        # Buscar el producto ofertado por ID (copiando solo los campos necesarios)
        for reg in self._modelo.consulta_productos_ofertados:
            if int(reg['ProductID']) == int(product_id):
                sale_price_before = self._utilerias.redondear_valor_cantidad_a_decimal(
                    reg['SalePriceBefore'])  # Copia segura
                tax_type_id = int(reg['TaxTypeID'])  # Copia segura
                break
        else:
            return producto  # No encontrado

        # Calcular totales sin modificar referencias originales
        cantidad = 1
        totales_partida = self._utilerias.calcular_totales_partida(
            precio=sale_price_before,
            tipo_impuesto_id=tax_type_id,
            cantidad=cantidad
        )
        producto = self._remover_texto_oferta(producto)
        sale_price_before_with_taxes = totales_partida.get('total', sale_price_before)
        nombre_producto = f"{producto} (OFE) {sale_price_before_with_taxes}"
        return nombre_producto

    def _remover_texto_oferta(self, producto):
        return re.sub(r"\s*\(OFE\).*", "", producto)

    def _rellenar_tabla_productos_manual(self, consulta_productos):
        registros_tabla = []
        tabla = self._ventanas.componentes_forma['tvw_productos_manual']

        for producto in consulta_productos:
            _producto = {
                'ProductKey': producto['ProductKey'],
                'ProductName': producto['ProductName'],
                'SalePriceWithTaxes': producto['SalePriceWithTaxes'],
                'ProductID': producto['ProductID'],
                'ClaveUnidad': producto['ClaveUnidad'],
                'Category1': producto['Category1']
            }

            registros_tabla.append(_producto)

        self._ventanas.rellenar_treeview(tabla, self._interfaz.crear_columnas_tabla_manual(), registros_tabla)
        self._colorear_productos_ofertados()

        if self._ventanas.numero_filas_treeview('tvw_productos_manual') == 1:
            self._ventanas.seleccionar_fila_treeview('tvw_productos_manual', 1)

    def _agregar_especicificaciones(self):
        ventana = self._ventanas.crear_popup_ttkbootstrap(titulo='Agregar especificacion')
        instancia = AgregarEspecificaciones(ventana, self._modelo.base_de_datos)
        ventana.wait_window()
        especificaciones = instancia.especificaciones_texto
        if especificaciones:
            comentario_original = self._ventanas.obtener_input_componente('txt_comentario_manual')
            nuevo_comentario = ''

            if comentario_original != '':
                nuevo_comentario = f'{comentario_original}'
                f'{especificaciones}'

        if comentario_original == '':
            nuevo_comentario = f'{especificaciones}'
            nuevo_comentario = nuevo_comentario.strip()

        self._ventanas.insertar_input_componente('txt_comentario_manual', nuevo_comentario)


def _buscar_productos_manualmente(self, event=None):
    tipo_busqueda = self._ventanas.obtener_input_componente('cbx_tipo_busqueda_manual')
    termino_buscado = self._ventanas.obtener_input_componente('tbx_buscar_manual')

    consulta = self._modelo.buscar_productos(termino_buscado, tipo_busqueda)

    if not consulta:
        self._modelo.mensajes_de_error(6, self._master)
        self._limpiar_controles_forma_manual()
        self._ventanas.enfocar_componente('tbx_buscar_manual')
        self._ventanas.insertar_input_componente('tbx_cantidad_manual', 1.00)
        return

    ids_productos = self._modelo.obtener_product_ids_consulta(consulta)
    consulta_productos = self._modelo.buscar_info_productos_por_ids(ids_productos)
```


## llamar_instancia_captura.py

```py
import copy

from cayal.ventanas import Ventanas

from controlador_captura import ControladorCaptura
from interfaz_captura import InterfazCaptura
from modelo_captura import ModeloCaptura


class LlamarInstanciaCaptura:
    def __init__(self, cliente, documento, base_de_datos, parametros, utilerias, master):
        self._master = master
        self._cliente = cliente
        self.documento = documento
        self._base_de_datos = base_de_datos
        self._parametros_contpaqi = parametros

        self._utilerias = utilerias
        self._ventanas = Ventanas(self._master)

        self._procesando_documento = False
        self._editando_documento = False
        self._info_documento = {}

        self._locked_doc_id = 0
        self._locked_is_pedido = False
        self._locked_active = False

        self._settear_valores_principales()
        self._determinar_si_se_inicia_captura_o_edicion()

    def _llamar_instancia_captura(self):

        if self._parametros_contpaqi.id_principal not in (0, -1):
            self._rellenar_instancias_importadas()

        # --- callback que SIEMPRE guarda (si procede) y DESMARCA el bloqueo ---
        def _on_close():
            try:
                self._procesar_documento()
            finally:
                # usa helper si existe; si no, fallback directo
                if hasattr(self, "_unmark_in_use"):
                    self._unmark_in_use()
                else:
                    try:
                        doc_id = int(getattr(self.documento, "document_id", 0) or 0)
                        if doc_id > 0:
                            pedido_flag = (self._module_id == 1687)
                            self._base_de_datos.desmarcar_documento_en_uso(doc_id, pedido=pedido_flag)
                    except Exception:
                        pass



        # --- crea el popup como antes, pero usando _on_close ---
        if not self.documento.cancelled_on:
            pregunta = '¿Desea guardar el documento?'
            ventana = self._ventanas.crear_popup_ttkbootstrap(
                master=self._master,
                titulo='Capturar pedido',
                ocultar_master=True,
                ejecutar_al_cierre=_on_close,
                preguntar=pregunta
            )
        else:
            ventana = self._ventanas.crear_popup_ttkbootstrap(
                self._master,
                titulo='Capturar pedido',
                ocultar_master=True,
                ejecutar_al_cierre=_on_close
            )



        # ----- Resto de tu flujo intacto -----
        interfaz = InterfazCaptura(ventana, self._parametros_contpaqi.id_modulo)

        modelo = ModeloCaptura(self._base_de_datos,
                               interfaz.ventanas,
                               self._utilerias,
                               self._cliente,
                               self._parametros_contpaqi,
                               self.documento)

        controlador = ControladorCaptura(interfaz, modelo)

        # asigna el valor del documento por posibles cambios que haya habido en el proceso de captura
        self.documento = controlador.documento

    def _solo_existe_servicio_domicilio_en_documento(self):

        existe = [producto for producto in self.documento.items if producto['ProductID'] == 5606]

        if existe and len(self.documento.items) == 1:
            return True

        return False

    def _procesar_documento(self):
        if self._procesando_documento:
            return  # ya se está procesando / se procesó

        self._procesando_documento = True
        try:
            # 1) Documento nuevo: crear cabecera si aplica
            if int(self.documento.document_id or 0) == 0:
                if self._parametros_contpaqi.id_modulo == 1687:
                    # Si solo hay servicio a domicilio o no hay partidas, no hay nada que guardar
                    if self._solo_existe_servicio_domicilio_en_documento():
                        return
                    if not self.documento.items:
                        return

                    # Crear cabecera
                    self.documento.document_id = int(self._crear_cabecera_pedido_cayal() or 0)

                    # Si se generó ID, opcionalmente marca en uso ahora para evitar colisiones
                    if self.documento.document_id > 0:
                        if hasattr(self, "_mark_in_use") and callable(self._mark_in_use):
                            self._mark_in_use(self.documento.document_id, pedido=True)
                        else:
                            # Fallback directo si no tienes helper
                            self._base_de_datos.marcar_documento_en_uso(self.documento.document_id,
                                                                        self._user_id, pedido=True)
                else:
                    # Otros módulos (no 1687): deja el camino preparado por si agregas creación aquí
                    pass

            # Si después de la fase anterior seguimos sin ID, no se puede persistir nada
            if int(self.documento.document_id or 0) == 0:
                return

            # 2) Insert/merge de partidas
            self._insertar_partidas_documento(self.documento.document_id)
            self._insertar_partidas_extra_documento(self.documento.document_id)

            # 3) Totales
            self._actualizar_totales_documento(self.documento.document_id)

            # 4) Actualizaciones finales en cabecera (ProductionType y campos editables)
            production_type_id = int(self._determinar_tipo_de_orden_produccion() or 1)
            comments = self.documento.comments or ''
            address_detail_id = int(self.documento.address_detail_id or 0)
            total = float(self.documento.total or 0)

            self._base_de_datos.command("""
                DECLARE @ProductionTypeID INT = ?
                DECLARE @CommentsOrder NVARCHAR(MAX) = ?
                DECLARE @AddressDetailID INT = ?
                DECLARE @Total FLOAT = ?
                DECLARE @OrderDocumentID INT = ?

                DECLARE @StatusID INT = (SELECT StatusID
                                         FROM docDocumentOrderCayal 
                                         WHERE OrderDocumentID = @OrderDocumentID)

                IF @StatusID IN (1,2,3,4,11,12,16,17,18,13)
                BEGIN
                    UPDATE docDocumentOrderCayal 
                    SET CommentsOrder = @CommentsOrder,
                        AddressDetailID = @AddressDetailID
                    WHERE OrderDocumentID = @OrderDocumentID
                END

                UPDATE docDocumentOrderCayal 
                SET ProductionTypeID = @ProductionTypeID
                WHERE OrderDocumentID = @OrderDocumentID
            """, (production_type_id, comments, address_detail_id, total, self.documento.document_id))

        except Exception as e:
            # Log simple; evita romper el cierre de la ventana.
            try:
                print(f"[procesar_documento] Error: {e}")
            except Exception:
                pass
            # Puedes relanzar si quieres que se vea arriba:
            # raise
        finally:
            # NO desmarques aquí. El desmarcado debe suceder en el callback de cierre del popup
            # (p.ej., _on_close) para garantizar que se libere incluso si hubo excepciones.
            pass

    def _determinar_tipo_de_orden_produccion(self):

        partidas = self.documento.items
        tipos_productos = [partida['ProductTypeIDCayal'] for partida in partidas
                           if partida['ProductID'] != 5606]

        tipos_productos = list(set(tipos_productos))

        if tipos_productos:
            if len(tipos_productos) == 1:
                tipo_producto = tipos_productos[0]

                # tipos de producto segun orgproduct
                orden_type_id = {
                    0: 2,  # 0 tipo minisuper
                    1: 1,  # 1 tipo produccion
                    2: 3  # 2 tipo almacen
                }
                return orden_type_id[tipo_producto]

            if len(tipos_productos) == 2:
                suma = sum(tipos_productos)

                orden_type_id = {
                    1: 4,  # produccion y minisuper
                    3: 5,  # produccion y almacen
                    2: 6  # minisuper y almacen
                }
                return orden_type_id[suma]

            if len(tipos_productos) == 3:
                return 7

        return 1

    def _crear_cabecera_pedido_cayal(self):

        # aplica insercion especial a tabla de sistema de pedidos cayal

        document_id = 0

        parametros_pedido = self.documento.order_parameters
        production_type_id = self._determinar_tipo_de_orden_produccion()
        if parametros_pedido:
            parametros = (
                parametros_pedido.get('RelatedOrderID',0),
                parametros_pedido.get('BusinessEntityID'),
                parametros_pedido.get('CreatedBy'),
                self.documento.comments,
                parametros_pedido.get('ZoneID'),
                parametros_pedido.get('AddressDetailID'),
                parametros_pedido.get('DocumentTypeID'),
                parametros_pedido.get('OrderTypeID'),
                parametros_pedido.get('OrderDeliveryTypeID'),
                parametros_pedido.get('SubTotal'),
                parametros_pedido.get('TotalTax'),
                parametros_pedido.get('Total'),
                production_type_id,
                parametros_pedido.get('HostName'),
                parametros_pedido.get('ScheduleID', 1),
                parametros_pedido.get('OrderDeliveryCost'),
                parametros_pedido.get('DepotID', 0)

            )

            document_id = self._base_de_datos.crear_pedido_cayal2(parametros)
            if document_id:
                self._base_de_datos.insertar_registro_bitacora_pedidos(
                    document_id, 1, parametros_pedido['CreatedBy'], parametros_pedido['CommentsOrder']
                )

            # en caso que la orden sea un anexo o un pedido hay que actualizar dicho documento
            if parametros_pedido['OrderTypeID'] in (2, 3):
                self._base_de_datos.command(
                    """
                    DECLARE @OrderID INT = ?
                    UPDATE docDocumentOrderCayal
                    SET NumberAdditionalOrders = (SELECT Count(OrderDocumentID)
                                                 FROM docDocumentOrderCayal
                                                 WHERE RelatedOrderID = @OrderID AND CancelledOn IS NULL),
                        StatusID = 2 
                    WHERE OrderDocumentID = @OrderID
                    """,
                    (parametros_pedido['RelatedOrderID'])
                )

        return document_id

    def _insertar_partidas_documento(self, document_id):

        if self._parametros_contpaqi.id_modulo == 1687:

            for partida in self.documento.items:
                # Crear una copia profunda para evitar referencias compartidas
                partida_copia = copy.deepcopy(partida)

                unidad = partida_copia.get('Unit', 'KILO')
                product_id = partida_copia.get('ProductID', 0)

                if unidad != 'KILO' and not self._utilerias.equivalencias_productos_especiales(product_id):
                    partida_copia['CayalPiece'] = 0

                parametros = (
                    document_id,
                    partida_copia['ProductID'],
                    2,  # DepotID
                    partida_copia['cantidad'],
                    partida_copia['precio'],
                    partida_copia['CostPrice'],
                    partida_copia['subtotal'],
                    partida_copia['DocumentItemID'],
                    partida_copia['TipoCaptura'],  # CaptureTypeID 0 lector, 1 manual, 2 automático
                    partida_copia['CayalPiece'],  # Viene del control de captura manual
                    partida_copia['CayalAmount'],  # Viene del control de tipo monto
                    partida_copia['ItemProductionStatusModified'],  # Viene del status de edición de la partida
                    partida_copia['Comments'],
                    partida_copia['CreatedBy']
                )

                document_item_id = self._base_de_datos.insertar_partida_pedido_cayal(parametros)

                # Actualizar el objeto original solo con el nuevo ID generado
                partida['DocumentItemID'] = document_item_id

        if self._parametros_contpaqi.id_modulo != 1687:
            print('agrgar proceso de insercion convencional')

    def _insertar_partidas_extra_documento(self, document_id):

        def _buscar_document_item_id(uuid_partida):
            for partida in self.documento.items:
                if partida.get('uuid') == uuid_partida:
                    return int(partida.get('DocumentItemID', 0))
            return 0  # o puedes lanzar una excepción controlada si prefieres


        if not self.documento.items_extra:
            return

        if self._parametros_contpaqi.id_modulo == 1687:

            for partida in self.documento.items_extra:

                accion_id = partida['ItemProductionStatusModified']
                change_type_id = 0
                comentario = ''
                uuid_partida = partida['uuid']

                # partida agregada
                if accion_id == 1:
                    document_item_id = _buscar_document_item_id(uuid_partida)
                    partida['DocumentItemID'] = document_item_id

                    change_type_id = 15
                    comentario = f"Agregado {partida['ProductName']} - Cant.{partida['cantidad']}"

                # partida editada
                if accion_id == 2:
                    change_type_id = 16
                    comentario = partida['Comments']

                # partida eliminada
                if accion_id == 3:
                    change_type_id = 17
                    comentario = f"Eliminado {partida['ProductName']} - Cant.{partida['cantidad']}"

                self._base_de_datos.insertar_registro_bitacora_pedidos(order_document_id=document_id,
                                                                       change_type_id=change_type_id,
                                                                       user_id=self._user_id,
                                                                       comments=comentario)

    def _actualizar_totales_documento(self, document_id):
        total = self.documento.total
        subtotal = self.documento.subtotal
        total_tax = self.documento.total_tax

        if self._parametros_contpaqi.id_modulo == 1687:
            self._base_de_datos.actualizar_totales_pedido_cayal(document_id,
                                                                subtotal,
                                                                total_tax,
                                                                total)

    def _rellenar_instancias_importadas(self):

        # 1) Cliente
        busines_entity_id = self._buscar_business_entity_id(self.documento.document_id)
        info_cliente = self._buscar_info_cliente(busines_entity_id) or []
        self._cliente.consulta = info_cliente
        self._cliente.settear_valores_consulta()

        # 2) Datos del pedido/documento
        info_pedido = self._info_documento or {}

        self.documento.depot_id = info_pedido.get('DepotID', 0)
        self.documento.depot_name = info_pedido.get('DepotName', '')
        self.documento.created_by = info_pedido.get('CreatedBy', 0)
        self.documento.address_detail_id = info_pedido.get('AddressDetailID', 0)
        self.documento.cancelled_on = info_pedido.get('CancelledOn', None)
        self.documento.docfolio = info_pedido.get('DocFolio', '')
        self.documento.comments = info_pedido.get('CommentsOrder', '')
        self.documento.address_name = info_pedido.get('AddressName', '')
        self.documento.business_entity_id = self._cliente.business_entity_id
        self.documento.customer_type_id = self._cliente.cayal_customer_type_id

        # 3) Dirección formateada (solo si hay ID válido)
        if int(self.documento.address_detail_id or 0) > 0:
            direccion = self._base_de_datos.buscar_detalle_direccion_formateada(self.documento.address_detail_id)
        else:
            direccion = {}
        self.documento.address_details = direccion

        # 4) Marcar en uso (solo si hay document_id > 0). Evita doble marcado en la misma instancia.
        doc_id = int(self.documento.document_id or 0)
        if doc_id > 0:
            pedido_flag = (self._module_id == 1687)

            # Si ya está marcado por esta misma instancia, no lo marques de nuevo
            already_locked_same_doc = getattr(self, "_locked_active", False) and \
                                      getattr(self, "_locked_doc_id", 0) == doc_id

            if not already_locked_same_doc:
                # Usa helper si existe; si no, usa la BD directamente
                if hasattr(self, "_mark_in_use") and callable(self._mark_in_use):
                    self._mark_in_use(doc_id, pedido=pedido_flag)
                else:
                    self._base_de_datos.marcar_documento_en_uso(doc_id, self._user_id, pedido=pedido_flag)

        # 5) Bandera de estado
        self._editando_documento = True

    def _buscar_business_entity_id(self, document_id):
        return self._base_de_datos.buscar_business_entity_id_documento(
            document_id,
            self._parametros_contpaqi.id_modulo
        )

    def _buscar_info_cliente(self, business_entity_id):
        return self._base_de_datos.buscar_info_cliente(business_entity_id)

    def _determinar_si_se_inicia_captura_o_edicion(self):

        if self._module_id == 1687:

            if self.documento.document_id > 0:
                order_type_id = self._info_documento['OrderTypeID']

                if order_type_id != 1 and self._user_group_id == 11:
                    self._ventanas.mostrar_mensaje('No se pueden editar los anexos o cambios por cajeros.')
                    return

        self._llamar_instancia_captura()

    def _buscar_informacion_documento_existente(self):
        # rellena la informacion relativa al documento
        consulta_info_pedido = self._base_de_datos.buscar_info_documento_pedido_cayal(
            self.documento.document_id
        )
        info_pedido = consulta_info_pedido[0]
        self._info_documento = info_pedido

    def _settear_valores_principales(self):

        self._module_id = self._parametros_contpaqi.id_modulo
        self._user_id = self._parametros_contpaqi.id_usuario
        self._user_group_id = self._base_de_datos.fetchone(
            'SELECT UserGroupID FROM engUser WHERE UserID = ?',
            (self._user_id,))
        self._parametros_contpaqi.nombre_usuario = self._base_de_datos.buscar_nombre_de_usuario(self._user_id)

        if self._parametros_contpaqi.id_principal > 0:
            self.documento.document_id = self._parametros_contpaqi.id_principal
            self._buscar_informacion_documento_existente()

    def _mark_in_use(self, document_id, pedido: bool):
        self._locked_doc_id = int(document_id or 0)
        self._locked_is_pedido = bool(pedido)
        self._locked_active = self._locked_doc_id > 0
        if self._locked_active:
            self._base_de_datos.marcar_documento_en_uso(self._locked_doc_id, self._user_id,
                                                        pedido=self._locked_is_pedido)

    def _unmark_in_use(self):
        # idempotente, por si se llama más de una vez
        if getattr(self, "_locked_active", False) and getattr(self, "_locked_doc_id", 0):
            try:
                self._base_de_datos.desmarcar_documento_en_uso(self._locked_doc_id, pedido=self._locked_is_pedido)
            finally:
                self._locked_active = False
                self._locked_doc_id = 0
                self._locked_is_pedido = False

```


## modelo_panel_pedidos.py

```py
from datetime import datetime

from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.util import Utilerias


class ModeloPanelPedidos:
    def __init__(self, interfaz, parametros):
        self.parametros = parametros
        self.interfaz = interfaz
        self.base_de_datos = ComandosBaseDatos(self.parametros.cadena_conexion)
        self.utilerias = Utilerias()
        self.consulta_pedidos = []

        valores_puntualidad = self.obtener_valores_de_puntualidad()

        self.valor_a_tiempo = valores_puntualidad['ATiempo']
        self.valor_en_tiempo = valores_puntualidad['EnTiempo']

        self.hoy = datetime.now().date()
        self.hora_actual = self.utilerias.hora_actual()
        self.usuario_operador_panel = ''

        self.pedidos_en_tiempo = 0
        self.pedidos_a_tiempo = 0
        self.pedidos_retrasados = 0

    def buscar_pedidos(self, fecha_entrega):
        return self.base_de_datos.buscar_pedidos_panel_captura_cayal(fecha_entrega)

    def buscar_pedidos_sin_procesar(self):
        return self.base_de_datos.pedidos_sin_procesar('pedidos')

    def buscar_pedidos_cliente_sin_fecha(self, criteria):
        return self.base_de_datos.buscar_pedidos_cliente_sin_fecha_panel_pedidos(criteria)

    def obtener_valores_de_puntualidad(self):
        consulta = self.base_de_datos.obtener_valores_de_puntualidad_pedidos_cayal('timbrado')
        if not consulta:
            return
        return consulta[0]

    def buscar_nombre_usuario_operador_panel(self, user_id):
        return self.base_de_datos.buscar_nombre_de_usuario(user_id)

    def buscar_partidas_pedido(self, order_document_id):
        consulta = self.base_de_datos.buscar_partidas_pedidos_produccion_cayal(order_document_id= order_document_id,
                                                                                partidas_producidas=True,
                                                                                partidas_eliminadas=True)
        if not consulta:
            return
        return consulta
```


## interfaz_captura.py

```py
import os
import random

import tkinter as tk
import ttkbootstrap as ttk
from PIL import Image, ImageTk
import threading

from cayal.ventanas import Ventanas


class InterfazCaptura:
    def __init__(self, master, modulo_id):
        self.master = master
        self.modulo_id = modulo_id
        self.ventanas = Ventanas(self.master)
        self._PATH_IMAGENES_PUBLICITARIAS = self._obtener_ruta_imagenes_publitarias()

        self._cargar_frames()
        self._cargar_componentes_forma()
        self._ajustar_componentes_forma()
        self._cargar_imagen_publicitaria_async()
        self._cargar_componentes_frame_totales()
        self._agregar_validaciones()
        self._cargar_captura_manual()


    def _cargar_frames(self):
        nombre_frame_anuncio = 'Anuncios' if self.modulo_id not in [1687] else 'Captura manual'
        frames = {

            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_izquierdo': ('frame_principal', None,
                              {'row': 0, 'column': 0,  'pady': 0, 'padx': 0, 'sticky': tk.NSEW}),

            'frame_herramientas': ('frame_izquierdo', None,
                                   {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 0, 'padx': 0,
                                    'sticky': tk.NSEW}),

            'frame_cliente': ('frame_izquierdo', 'Datos cliente:',
                              {'row': 1, 'column': 0, 'columnspan': 2, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW}),

            'frame_captura': ('frame_izquierdo', 'Captura',
                              {'row': 2, 'columnspan': 2, 'column': 0, 'pady': 0, 'padx': 0,
                               'sticky': tk.NSEW}),

            'frame_clave': ('frame_captura', None,
                            {'row': 0, 'columnspan': 2, 'column': 0, 'pady': 0, 'padx': 0,
                             'sticky': tk.NSEW}),
            'frame_tabla': ('frame_captura', None,
                            {'row': 1, 'columnspan': 2, 'column': 0, 'pady': 0, 'padx': 0,
                             'sticky': tk.NSEW}),

            'frame_comentario': ('frame_izquierdo', 'Comentarios:',
                                 {'row': 4, 'column': 0, 'columnspan': 2, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW}
                                 ),


            'frame_derecho': ('frame_principal', None,
                              {'row': 0, 'column': 2,  'rowspan':5, 'pady': 0, 'padx': 0,
                               'sticky': tk.NSEW}),

            'frame_totales': ('frame_derecho', None,
                              {'row': 0, 'column': 2,  'columnspan': 5, 'pady': 0, 'padx': 0,
                               'sticky': tk.NE}),

            'frame_anuncio': ('frame_derecho', nombre_frame_anuncio,
                              {'row': 2,  'column': 2, 'columnspan': 4, 'pady': 0, 'padx': 0,
                               'sticky': tk.NSEW}),




        }



        if self.modulo_id not in [1687]:
            frames.update({
                'frame_fiscal': ('frame_principal', 'Parametros Fiscales:',
                                 {'row': 6, 'column': 0, 'columnspan': 5, 'pady': 5, 'padx': 5, 'sticky': tk.NSEW}
                                 )  # Cierra correctamente la tupla
            })  # Cierra correctamente el diccionario

        self.ventanas.crear_frames(frames)

    def _cargar_componentes_forma(self):
        ancho, alto = self.ventanas.obtener_resolucion_pantalla()
        filas_tabla_producto = 20 if ancho <= 1367 else 30

        componentes = {
            'tbx_cliente': ('frame_cliente', {'row': 0, 'column': 1, 'pady': 2, 'padx': 0, 'sticky': tk.NSEW},
                            ' ', None),
            'tbx_direccion': ('frame_cliente', {'row': 1, 'column': 1, 'pady': 2, 'padx': 0, 'sticky': tk.NSEW},
                              ' ', None),
            'tbx_comentario': ('frame_cliente', {'row': 2, 'column': 1, 'pady': 2, 'padx': 0, 'sticky': tk.NSEW},
                               ' ', None),
            'tbx_clave': ('frame_clave', None, None, None),
            'tvw_productos': ('frame_tabla', self.crear_columnas_tabla(), filas_tabla_producto, None),
            'txt_comentario_documento': ('frame_comentario', None,' ', None),
        }

        if self.modulo_id not in [1687]:
            componentes.update({
                'lbl_anuncio': ('frame_anuncio',
                                {'text': '', 'style': 'inverse-danger'},
                                {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                None),

                'lbl_usocfdi': ('frame_fiscal',
                                {'text': 'Uso CFDI:'},
                                {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                None),

                'cbx_usocfdi': ('frame_fiscal', {'row': 0, 'column': 1, 'pady': 5, 'padx': 5}, None, None),

                'lbl_metodopago': ('frame_fiscal',
                                {'text': 'Método Pago:'},
                                {'row': 0, 'column': 2, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                None),

                'cbx_metodopago': ('frame_fiscal', {'row': 0, 'column': 3, 'pady': 5, 'padx': 5}, None, None),

                'lbl_formapago': ('frame_fiscal',
                                   {'text': 'Forma Pago:'},
                                   {'row': 0, 'column': 4, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                   None),

                'cbx_formapago': ('frame_fiscal', {'row': 0, 'column': 5, 'pady': 5, 'padx': 5},  None,None),

                'lbl_regimen': ('frame_fiscal',
                                   {'text': 'Régimen Fiscal:'},
                                   {'row': 0, 'column': 6, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                   None),

                'cbx_regimen': ('frame_fiscal', {'row': 0, 'column': 7, 'pady': 5, 'padx': 5},  None, None),
            })

        self.ventanas.crear_componentes(componentes)

    def _cargar_componentes_frame_totales(self):
        ancho, alto = self.ventanas.obtener_resolucion_pantalla()

        tamano_fuente_titulo_1 = 16 if ancho > 1366 else 11
        tamano_fuente_titulo_2 = 29 if ancho > 1366 else 24

        estilo_auxiliar = {
            'foreground': 'white',
            'background': '#E30421',
            'font': ('Consolas', tamano_fuente_titulo_1, 'bold'),
        }

        estilo_total = {
            'foreground': 'white',
            'background': '#E30421',
            'font': ('consolas', tamano_fuente_titulo_2, 'bold'),
        }

        etiqueta_totales = {
            'lbl_articulos': (estilo_auxiliar, {'row': 0, 'column': 1, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW},
                              'ARTS.:'),
            'lbl_folio': (estilo_auxiliar, {'row': 1, 'column': 1, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW},
                          'FOLIO:'),
            'lbl_modulo': (estilo_auxiliar, {'row': 2, 'column': 1, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW},
                           'MÓDULO:'),

            'lbl_captura': (estilo_auxiliar, {'row': 3, 'column': 1, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW},
                            'CAPTURA:'),

            'lbl_total': (estilo_total, {'row': 0, 'column': 5, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW},
                          'TOTAL'),

            'lbl_credito': (estilo_total, {'row': 1, 'column': 5, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW},
                            'CRÉDITO'),

            'lbl_debe': (estilo_total, {'row': 2, 'column': 5, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW},
                         'DEBE'),

            'lbl_restante': (estilo_total, {'row': 3, 'column': 5, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW},
                             'DISP.'),

        }

        frame_totales = self.ventanas.componentes_forma['frame_totales']

        tamano_fuente_titulo_2 = 14 if ancho > 1366 else 13
        tamano_fuente_titulo_3 = 18 if ancho > 1366 else 17


        for nombre, (estilo, posicion, etiqueta) in etiqueta_totales.items():
            componente = ttk.Label(frame_totales)
            componente.config(**estilo)
            componente.grid(**posicion)

            texto = etiqueta  # nombre[4::].capitalize() if nombre not in en_mayusculas else nombre[4::].upper()

            lbl = ttk.Label(frame_totales, text=texto)
            posicion['column'] = posicion['column'] - 1
            lbl.config(**estilo)
            lbl.grid(**posicion)



            if nombre in ('lbl_credito', 'lbl_debe', 'lbl_restante'):
                lbl.config(font=('roboto', tamano_fuente_titulo_2, 'bold'))
                lbl_texto = f'{nombre}_texto'

                self.ventanas.componentes_forma[lbl_texto] = lbl

            if nombre in ('lbl_credito', 'lbl_debe', 'lbl_restante', 'lbl_total'):
                componente.config(text='$ 0.00', font=('roboto', tamano_fuente_titulo_3, 'bold'), anchor='e')

            if nombre == 'lbl_articulos':
                componente.config(text='0')

            self.ventanas.componentes_forma[nombre] = componente

    def _agregar_validaciones(self):
        self.ventanas.agregar_validacion_tbx('tbx_clave', 'codigo_barras')

    def _obtener_ruta_imagenes_publitarias(self):
        if self.modulo_id in [1687]:
            return

        ruta_windows = r'\\ccayal\Users\Administrador\Pictures\ClienteVentas'
        if os.path.exists(ruta_windows):
            return ruta_windows
        RUTA_BASE = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(RUTA_BASE, 'publicidad')

    def _lista_imagenes_publicitarias(self):
        if self.modulo_id in [1687]:
            return
        # cachea en la instancia
        if not hasattr(self, '_cache_imgs'):
            path = self._PATH_IMAGENES_PUBLICITARIAS
            self._cache_imgs = []
            if os.path.exists(path):
                # scandir es más rápido que os.listdir
                with os.scandir(path) as it:
                    self._cache_imgs = [e.path for e in it if e.is_file() and e.name.lower().endswith('.png')]
        return self._cache_imgs


    def _cargar_imagen_publicitaria_async(self):
        if self.modulo_id in [1687]:
            return
        archivos = self._lista_imagenes_publicitarias()
        if not archivos:
            return
        ruta = random.choice(archivos)
        lbl = self.ventanas.componentes_forma['lbl_anuncio']

        def worker():
            try:
                img = Image.open(ruta).convert('RGB')
                lbl.update_idletasks()
                w, h = lbl.winfo_width(), lbl.winfo_height()
                if w <= 1 or h <= 1:
                    return
                img.thumbnail((w, h), Image.Resampling.LANCZOS)
            except Exception:
                return

            # volver al hilo principal para PhotoImage y configurar
            def apply():
                self.imagen_publicitaria = ImageTk.PhotoImage(img)
                lbl.configure(image=self.imagen_publicitaria)

            self.master.after(0, apply)

        threading.Thread(target=worker, daemon=True).start()

    def _ajustar_componentes_forma(self):
        self.ventanas.ajustar_componente_en_frame('tbx_cliente', 'frame_cliente')

        self.ventanas.ajustar_componente_en_frame('txt_comentario_documento', 'frame_comentario')
        self.ventanas.ajustar_label_en_frame('lbl_anuncio', 'frame_anuncio')

    def _cargar_captura_manual(self):
        if self.modulo_id  in [1687]:
            self._cargar_frames_manual()
            self._cargar_componentes_manual()

    def crear_columnas_tabla(self):
        ancho, alto = self.ventanas.obtener_resolucion_pantalla()
        ancho_descripcion = 180 if ancho <= 1367 else 230

        return [
            {"text": "Cantidad", "stretch": False, 'width': 70, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Piezas", "stretch": False, 'width': 70, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Código", "stretch": False, 'width': 110, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Descripción", "stretch": False, 'width': ancho_descripcion, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Unidad", "stretch": False, 'width': 70, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Precio", "stretch": False, 'width': 70, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Importe", "stretch": False, 'width': 80, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Impuesto", "stretch": False, 'width': 80, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Total", "stretch": False, 'width': 90, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "ProductID", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "DocumentItemID", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "TipoCaptura", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "UnidadCayal", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "MontoCayal", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "UUID", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "ItemProductionStatusModified", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "Comments", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "CreatedBy", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1}
        ]

    def _cargar_frames_manual(self):

        frames = {

            'frame_buscar_manual' : ('frame_anuncio', 'Búsqueda',
                       {'row': 0, 'column': 0, 'columnspan': 4, 'pady': 1, 'padx': 2, 'sticky': tk.NSEW}),

            'frame_tbx_buscar_manual' : ('frame_buscar_manual', None,
                                       {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 1, 'padx': 2, 'sticky': tk.NS}),

            'frame_cbx_buscar_manual' : ('frame_buscar_manual', None,
                                       {'row': 0, 'column': 3, 'columnspan': 2, 'pady': 1, 'padx': 2, 'sticky': tk.NS}),

            'frame_partida_manual' : ('frame_anuncio', 'Partida:',
                                    {'row': 2, 'column': 0, 'columnspan': 4, 'pady': 1, 'padx': 2, 'sticky': tk.NSEW}),



            'frame_detalles_partida_manual' : ('frame_partida_manual', 'Detalles:',
                                       {'row': 0, 'column': 0,  'columnspan': 4, 'pady': 1, 'padx': 2, 'sticky': tk.NSEW}),



            'frame_cantida_y_equivalencia': ('frame_detalles_partida_manual', 'Cantidad [Ctrl+C]',
                                        {'row': 0, 'column': 0,  'columnspan': 2, 'pady': 1, 'padx': 2,
                                         'sticky': tk.W}),

            'frame_totales_manual': ('frame_detalles_partida_manual', 'Total pieza:',
                                     {'row': 0, 'column': 2, 'columnspan': 2, 'rowspan': 2, 'pady': 1, 'padx': 2,
                                      'sticky': tk.NSEW}),


            'frame_controles_manual' : ('frame_detalles_partida_manual', None,
                                      {'row': 1, 'column': 0,  'columnspan': 2, 'pady': 1, 'padx': 2, 'sticky': tk.NSEW}),

            'frame_txt_comentario_manual' : ('frame_partida_manual', 'Especificación [Ctrl+M]',
                                           {'row': 6, 'column': 0, 'columnspan': 4, 'pady': 1, 'padx': 2, 'sticky': tk.NSEW}),

            'frame_txt_portapapeles_manual' : ('frame_partida_manual', 'Portapapeles [Ctrl+P]',
                                             {'row': 7, 'column': 0, 'columnspan': 4, 'pady': 1, 'padx': 2, 'sticky': tk.NSEW}),

            'frame_botones_manual' : ('frame_partida_manual', None,
                                    {'row': 11, 'column': 1, 'padx': 0, 'pady': 3, 'sticky': tk.W}),

            'frame_tabla_manual': ('frame_anuncio', 'Productos [Ctrl+T]',
                                   {'row': 3, 'column': 0, 'columnspan': 4, 'pady': 1, 'padx': 2, 'sticky': tk.NSEW})
        }
        self.ventanas.crear_frames(frames)

    def _cargar_componentes_manual(self):

        ancho, alto = self.ventanas.obtener_resolucion_pantalla()
        tamano_fuente = 8 if ancho <= 1367 else 12
        alto_comentarios = 2 if ancho <= 1367 else 4

        def atajos_botones(ancho, nombre_boton):

            if ancho <= 1367:
               return None

            _atajos_botones = {
                'btn_agregar_manual': '[F8]',
                'btn_especificaciones_manual': '[Ctrl+E]',
                'btn_ofertas_manual': '[F9]',
                'btn_copiar_manual': '[F12]',
                'tbx_buscar_manual': '[Ctrl+B]',
                'cbx_tipo_busqueda_manual': 'Ctrl+F'
            }

            return _atajos_botones[nombre_boton]

        componentes = {
            'cbx_tipo_busqueda_manual': ('frame_cbx_buscar_manual', None, 'Tipo:', atajos_botones( ancho,'cbx_tipo_busqueda_manual')),
            'tbx_buscar_manual': ('frame_tbx_buscar_manual', None, 'Buscar:', atajos_botones( ancho,'tbx_buscar_manual')),

            'tbx_cantidad_manual': ('frame_cantida_y_equivalencia', 6, 'Cant:', None),
            'tbx_equivalencia_manual': ('frame_cantida_y_equivalencia',
                                 {'row': 2, 'column': 3, 'pady': 5, 'padx': 5, 'sticky': tk.W},
                                 'Equi:', None),

            'txt_comentario_manual': ('frame_txt_comentario_manual', None, ' ', None),
            'txt_portapapeles_manual': ('frame_txt_portapapeles_manual', None, ' ', None),

            'lbl_monto_texto_manual': ('frame_totales_manual',
                                { 'text': 'TOTAL:', 'style': 'inverse-danger', 'anchor': 'e',
                                 'font': ('Consolas', tamano_fuente, 'bold')},
                                {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                None),

            'lbl_monto_manual': ('frame_totales_manual',
                          {'width':10, 'text': '$0.00', 'style': 'inverse-danger', 'anchor': 'e',
                           'font': ('Consolas', tamano_fuente, 'bold')},
                          {'row': 0, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                          None),

            'lbl_cantidad_texto_manual': ('frame_totales_manual',
                                   { 'text': 'CANTIDAD:', 'style': 'inverse-danger', 'anchor': 'e',
                                    'font': ('Consolas', tamano_fuente, 'bold')},
                                   {'row': 1, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                   None),

            'lbl_cantidad_manual': ('frame_totales_manual',
                             { 'text': '0.00', 'style': 'inverse-danger', 'anchor': 'e',
                              'font': ('Consolas', tamano_fuente, 'bold')},
                             {'row': 1, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                             None),

            'lbl_existencia_texto_manual': ('frame_totales_manual',
                                     { 'text': 'EXISTENCIA:', 'style': 'inverse-danger', 'anchor': 'e',
                                      'font': ('Consolas', tamano_fuente, 'bold')},
                                     {'row': 2, 'column': 0, 'padx': 0, 'sticky': tk.NSEW},
                                     None),

            'lbl_existencia_manual': ('frame_totales_manual',
                               { 'text': '0.00', 'style': 'inverse-danger', 'anchor': 'e',
                                'font': ('Consolas', tamano_fuente, 'bold')},
                               {'row': 2, 'column': 1, 'padx': 0, 'sticky': tk.NSEW},
                               None),

            'lbl_clave_manual': ('frame_totales_manual',
                                      {'text': 'CLAVE:', 'style': 'inverse-danger', 'anchor': 'center',
                                       'font': ('Consolas', tamano_fuente, 'bold')},
                                      {'row': 3, 'columnspan': 2, 'column': 0, 'padx': 0, 'sticky': tk.NSEW},
                                      None),

            'chk_pieza': ('frame_controles_manual',
                          {'row': 0, 'column': 1, 'pady': 2, 'padx': 2, 'sticky': tk.W},
                          'Pieza [F10]', None),

            'chk_monto': ('frame_controles_manual',
                          {'row': 0, 'column': 3, 'pady': 2, 'padx': 2, 'sticky': tk.W},
                          'Monto [F11]', None),


            'tvw_productos_manual': ('frame_tabla_manual', self.crear_columnas_tabla_manual(), 5, None),
            'btn_agregar_manual': ('frame_botones_manual', 'success', 'Agregar',
                                   atajos_botones(ancho, 'btn_agregar_manual')),
            'btn_especificaciones_manual': ('frame_botones_manual', 'primary', 'Especificación',
                                            atajos_botones(ancho, 'btn_especificaciones_manual')),
            'btn_ofertas_manual': ('frame_botones_manual', 'info', 'Ofertas',
                                   atajos_botones(ancho, 'btn_ofertas_manual')),
            'btn_copiar_manual': ('frame_botones_manual', 'warning', 'Copiar',
                                  atajos_botones(ancho, 'btn_copiar_manual')),

        }

        self.ventanas.crear_componentes(componentes)
        self.ventanas.ajustar_ancho_componente('cbx_tipo_busqueda',15)
        self.ventanas.ajustar_ancho_componente('tbx_buscar_manual', 15)
        self.ventanas.ajustar_ancho_componente('tbx_equivalencia_manual', 6)

        self.ventanas.ajustar_componente_en_frame('txt_comentario_manual', 'frame_txt_comentario_manual')
        self.ventanas.ajustar_componente_en_frame('txt_portapapeles_manual', 'frame_txt_portapapeles_manual')
        self.ventanas.ajustar_alto_componente('txt_comentario_manual', alto_comentarios)
        self.ventanas.ajustar_alto_componente('txt_portapapeles_manual', alto_comentarios)

    def crear_columnas_tabla_manual(self):

        ancho, alto = self.ventanas.obtener_resolucion_pantalla()
        ancho_descripcion = 300 if ancho <= 1367 else 390

        return [
            {"text": "Código", "stretch": False, 'width': 130, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "Descripción", "stretch": False, 'width': ancho_descripcion, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Precio", "stretch": False, 'width': 70, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "ProductID", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "ClaveUnidad", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "Category1", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
        ]
```


## panel_principal_cliente.py

```py
import ttkbootstrap as ttk
import tkinter as tk
import ttkbootstrap.dialogs

from herramientas.cliente.buscar_info_cif import BuscarInfoCif
from cliente.formulario_cliente import FormularioCliente
from cayal.cliente import Cliente
from cayal.ventanas import Ventanas


class PanelPrincipal:
    def __init__(self, master, parametros, base_de_datos, utilerias):

        self._parametros = parametros
        self._utilerias = utilerias
        self._cliente = Cliente()
        self._base_de_datos = base_de_datos

        self._master = master
        self._ventanas = Ventanas(self._master)
        self._ventanas.configurar_ventana_ttkbootstrap('Nuevo:')

        self.componentes_forma = {}
        self._cargar_componentes_forma()
        self._cargar_info_componentes_forma()
        self._cargar_eventos_componentes_forma()

    def _cargar_componentes_forma(self):
        frame_principal = ttk.LabelFrame(self._master, text='Seleccion')
        frame_principal.grid(row=0, column=0, columnspan=2, pady=5, padx=5, sticky=tk.NSEW)

        frame_manual = ttk.LabelFrame(self._master, text='Manual')
        frame_cedula = ttk.LabelFrame(self._master, text='Cedula')
        frame_factura = ttk.Frame(frame_manual)

        frame_botones = ttk.Frame(self._master)
        frame_botones.grid(row=3, column=1, pady=5, padx=5, sticky=tk.E)

        self.componentes_forma['frame_cedula'] = frame_cedula
        self.componentes_forma['frame_manual'] = frame_manual
        self.componentes_forma['frame_factura'] = frame_factura

        nombres_componentes = {
            'cbx_tipo': ('Combobox', frame_principal, 'readonly'),
            'tbx_cliente': ('Entry', frame_manual, None),
            'cbx_documento': ('Combobox', frame_manual, 'readonly'),
            'tbx_cif': ('Entry', frame_cedula, None),
            'tbx_rfc': ('Entry', frame_cedula, None),
            'tbx_rfc2': ('Entry', frame_factura, None),
            'btn_aceptar': ('Button', frame_botones, None),
            'btn_cancelar': ('Button', frame_botones, 'danger')

        }

        for i, (nombre, (tipo, frame, estado)) in enumerate(nombres_componentes.items()):
            lbl_texto = nombre[4:].capitalize() if 'rfc2' not in nombre else 'Rfc'

            if tipo == 'Combobox':
                componente = ttk.Combobox(frame, state=estado)
            elif tipo == 'Entry':
                if nombre == 'cliente':
                    componente = ttk.Entry(frame, width=77)
                elif 'rfc2' in nombre:
                    componente = ttk.Entry(frame, width=20)
                else:
                    componente = ttk.Entry(frame)
            elif tipo == 'Button':
                componente = ttk.Button(frame, text=lbl_texto, style=estado if estado else None)
                componente.grid(row=0, column=i, padx=5, pady=5, sticky=tk.W)

            if tipo != 'Button':
                if 'rfc2' in nombre:
                    lbl = ttk.Label(frame, text=lbl_texto, width=11)
                else:
                    lbl = ttk.Label(frame, text=lbl_texto)

                lbl.grid(row=i, column=0, pady=5, padx=5, sticky=tk.W)
                componente.grid(row=i, column=1, padx=5, pady=5, sticky=tk.W)

            self.componentes_forma[nombre] = componente

    def _cargar_info_componentes_forma(self):
        cbx_tipo = self.componentes_forma['cbx_tipo']
        tipos_captura = ['Seleccione', 'Manual', 'Cédula fiscal']
        cbx_tipo['values'] = tipos_captura
        cbx_tipo.set(tipos_captura[0])

        cbx_documento = self.componentes_forma['cbx_documento']
        tipos_clientes = ['Seleccione', 'Remisión', 'Factura']
        cbx_documento['values'] = tipos_clientes
        cbx_documento.set(tipos_clientes[0])

    def _cargar_eventos_componentes_forma(self):

        tbx_cif = self.componentes_forma['tbx_cif']
        tbx_cif.config(validate='focus',
                       validatecommand=(self._master.register(
                           lambda text: self._ventanas.validar_entry(tbx_cif, 'cif')), '%P'))

        tbx_rfc = self.componentes_forma['tbx_rfc']
        tbx_rfc.config(validate='focus',
                       validatecommand=(self._master.register(
                           lambda text: self._ventanas.validar_entry(tbx_rfc, 'rfc')), '%P'))

        tbx_rfc2 = self.componentes_forma['tbx_rfc2']
        tbx_rfc2.config(validate='focus',
                        validatecommand=(self._master.register(
                            lambda text: self._ventanas.validar_entry(tbx_rfc2, 'rfc')), '%P'))

        btn_cancelar = self.componentes_forma['btn_cancelar']
        btn_cancelar.config(command=lambda: self._master.destroy())

        cbx_tipo = self.componentes_forma['cbx_tipo']
        cbx_tipo.bind('<<ComboboxSelected>>', lambda event: self._cambiar_apariencia_forma())

        cbx_documento = self.componentes_forma['cbx_documento']
        cbx_documento.bind('<<ComboboxSelected>>', lambda event: self._cambiar_apariencia_forma())

        btn_aceptar = self.componentes_forma['btn_aceptar']
        btn_aceptar.config(command=lambda: self._validaciones_inputs())

    def _cambiar_apariencia_forma(self):

        cbx_documento = self.componentes_forma['cbx_documento']
        seleccion_documento = cbx_documento.get()

        cbx_tipo = self.componentes_forma['cbx_tipo']
        seleccion = cbx_tipo.get()

        frame_cedula = self.componentes_forma['frame_cedula']
        frame_manual = self.componentes_forma['frame_manual']
        frame_factura = self.componentes_forma['frame_factura']

        if seleccion != 'Manual' or seleccion_documento == 'Seleccione':
            self._limpiar_controles()

        if seleccion == 'Manual' and seleccion_documento in ('Remisión', 'Seleccione'):
            frame_cedula.grid_forget()
            frame_factura.grid_forget()
            frame_manual.grid(row=1, column=0, columnspan=2, pady=5, padx=5, sticky=tk.NSEW)

        if seleccion == 'Manual' and seleccion_documento == 'Factura':
            frame_cedula.grid_forget()
            frame_manual.grid(row=1, column=0, columnspan=2, pady=5, padx=5, sticky=tk.NSEW)
            frame_factura.grid(row=3, column=0, columnspan=2, pady=5, sticky=tk.W)

        if seleccion == 'Cédula fiscal':
            frame_manual.grid_forget()
            frame_factura.grid_forget()
            frame_cedula.grid(row=2, column=0, columnspan=2, pady=5, padx=5, sticky=tk.NSEW)

        if seleccion == 'Seleccione':
            frame_manual.grid_forget()
            frame_cedula.grid_forget()
            frame_factura.grid_forget()

    def _limpiar_controles(self):
        for nombre, componente in self.componentes_forma.items():
            if 'tbx' in nombre:
                componente.delete(0, tk.END)

    def _validaciones_inputs(self):
        pass
        cbx_tipo = self.componentes_forma['cbx_tipo']
        seleccion = cbx_tipo.get()

        cbx_documento = self.componentes_forma['cbx_documento']
        seleccion_documento = cbx_documento.get()

        if seleccion == 'Seleccione':
            ttkbootstrap.dialogs.Messagebox.show_error(parent=self._master,
                                                       message='Debe seleccionar una opción válida.')
            return

        if seleccion_documento == 'Seleccione' and seleccion == 'Manual':
            ttkbootstrap.dialogs.Messagebox.show_error(parent=self._master,
                                                       message='Debe seleccionar un documento preferente.')
            return

        if seleccion == 'Manual':
            tbx_cliente = self.componentes_forma['tbx_cliente']
            cliente = tbx_cliente.get()

            if not self._validar_cliente(cliente):
                return
            else:
                business_entity_id = self._base_de_datos.cliente_existente(cliente)

                if business_entity_id > 0:
                    validacion = ttkbootstrap.dialogs.Messagebox.yesno(parent=self._master, message=
                    '¿El cliente ya existe en la base de datos desea continuar?')

                    if validacion == 'No':
                        return

                if business_entity_id == 0:
                    business_entity_id = self._base_de_datos.cliente_borrado(cliente)

                    if business_entity_id > 0:
                        validacion = ttkbootstrap.dialogs.Messagebox.yesno(parent=self._master, message=
                        '¿El cliente ya existe en la base de datos pero esta borrado desea continuar?')

                        if validacion == 'No':
                            return
                        else:
                            self._restaurar_cliente_borrado(business_entity_id)
                            self._master.destroy()

                if seleccion_documento == 'Factura':

                    tbx_rfc2 = self.componentes_forma['tbx_rfc2']
                    rfc2 = tbx_rfc2.get()

                    if not self._validar_seleccion_factura(rfc2):
                        return

                self._llamar_forma_segun_tipo_captura(seleccion_documento)

        if seleccion == 'Cédula fiscal':
            tbx_rfc = self.componentes_forma['tbx_rfc']
            rfc = tbx_rfc.get()

            if not self._validar_seleccion_factura(rfc):
                return

            tbx_cif = self.componentes_forma['tbx_cif']
            cif = tbx_cif.get()

            if not self._validar_cif(cif):
                return

            self._llamar_forma_segun_tipo_captura(seleccion)

    def _validar_seleccion_factura(self, rfc):

        if self._validar_rfc(rfc):
            business_entity_id = self._base_de_datos.rfc_existente(rfc)

            if business_entity_id > 0:
                validacion = ttkbootstrap.dialogs.Messagebox.yesno(parent=self._master, message=
                '¿El rfc ya existe en la base de datos desea continuar?')

                if validacion == 'No':
                    return False

            if business_entity_id == 0:
                business_entity_id = self._base_de_datos.rfc_borrado(rfc)

                if business_entity_id > 0:
                    validacion = ttkbootstrap.dialogs.Messagebox.yesno(parent=self._master, message=
                    '¿El rfc ya existe en la base de datos pero está borrado desea continuar?')

                    if validacion == 'No':
                        return False

            return True

    def _validar_cliente(self, cliente):
        if not cliente:
            ttkbootstrap.dialogs.Messagebox.show_error(parent=self._master,
                                                       message='Debe agregar un nombre para el cliente.')
            return False

        if len(cliente) < 5:
            ttkbootstrap.dialogs.Messagebox.show_error(parent=self._master, message='Debe agregar un nombre más largo.')
            return False

        return True

    def _validar_cif(self, cif):

        if not cif:
            ttkbootstrap.dialogs.Messagebox.show_error(parent=self._master,
                                                       message='Debe introducir información en los campos requeridos.')
            return False

        if not self._utilerias.es_cif(cif):
            ttkbootstrap.dialogs.Messagebox.show_error(parent=self._master,
                                                       message='El cif es es inválido favor de validar.')
            return False

        return True

    def _validar_rfc(self, rfc):

        if not rfc:
            ttkbootstrap.dialogs.Messagebox.show_error(parent=self._master,
                                                       message='Debe introducir información en los campos requeridos.')
            return False

        if not self._utilerias.es_rfc(rfc):
            ttkbootstrap.dialogs.Messagebox.show_error(parent=self._master,
                                                       message='El rfc es inválido favor de validar.')
            return False

        return True

    def _llamar_forma_segun_tipo_captura(self, tipo_captura):

        # tipos de seleccion 'Cédula fiscal' 'Factura' 'Remisión'

        if tipo_captura == 'Remisión':
            self._settear_valores_cliente_remision()

        if tipo_captura in ('Factura', 'Cédula fiscal'):
            self._settear_valores_cliente_factura()

        if tipo_captura in ('Factura', 'Remisión'):
            self._master.withdraw()

            informacion_captura = {'TipoCaptura': tipo_captura}
            ventana = self._ventanas.crear_popup_ttkbootstrap('Formulario cliente')
            instancia = FormularioCliente(ventana, self._parametros, informacion_captura, self._cliente)
            ventana.wait_window()
            self._master.destroy()

        if tipo_captura == 'Cédula fiscal':
            self._master.withdraw()

            ventana = ttk.Toplevel()
            buscar_info_cif = BuscarInfoCif(ventana,
                                            self._parametros,
                                            self._cliente.official_number,
                                            self._cliente.cif,
                                            self._cliente)
            ventana.wait_window()

            informacion_captura = buscar_info_cif.informacion_captura

            if informacion_captura:
                self._master.withdraw()

                instancia_cliente = buscar_info_cif.cliente
                ventana = self._ventanas.crear_popup_ttkbootstrap()
                instancia = FormularioCliente(ventana,
                                              self._parametros,
                                              informacion_captura,
                                              instancia_cliente)
                ventana.wait_window()
                self._master.destroy()

    def _restaurar_cliente_borrado(self, business_entity_id):
        self._base_de_datos.command("""
               --Declara variables a usar
                DECLARE @IDEMPR bigint = ?
                DECLARE @DFiscalID bigint
                DECLARE @Control int
                
                --REACTIVA EL CLIENTE SELECCIONADO
                
                SET @Control=(SELECT CASE WHEN DeletedOn IS NULL THEN 0 ELSE 1 END FROM orgBusinessEntity WHERE BusinessEntityID=@IDEMPR)
                
                IF @Control=1
                BEGIN
                
                    UPDATE orgBusinessEntity SET DeletedOn=NULL, DeletedBy=NULL 
                    WHERE BusinessEntityID=@IDEMPR
                
                    UPDATE orgCustomer SET CustomerTypeID=2,DeletedOn=NULL, DeletedBy=NULL, ZoneID=1033 
                    WHERE BusinessEntityID=@IDEMPR
                
                
                    --HOMOLOGACION DE DATOS DE DIRECCIÓN DE CLIENTE 
                
                    --Busca si existe o no la dirección fiscal en la tabla orgaddress
                    SET @DFiscalID=(SELECT AddressFiscalDetailID FROM orgBusinessEntityMainInfo WHERE BusinessEntityID=@IDEMPR)
                    SET @DFiscalID=(SELECT AddressDetailID FROM orgAddress WHERE AddressDetailID=@DFiscalID)
                
                    -- Si la dirección fiscal no existe, INSERT, de lo contrario, actualiza
                    MERGE INTO orgAddressDetail AS target
                    USING (VALUES (@DFiscalID)) AS source (AddressDetailID)
                    ON target.AddressDetailID = source.AddressDetailID
                    WHEN NOT MATCHED BY TARGET THEN
                        INSERT (AddressDetailID, CountryID, StateProvince, City, ZipCode, Municipality, Street, ExtNumber, Comments, CreatedOn, CreatedBy, DeletedBy, UserID, CountryCode, StateProvinceCode, CityCode, MunicipalityCode, IsFiscalAddress)
                        SELECT 
                            ee.AddressFiscalDetailID, 
                            412, 
                            ee.AddressFiscalStateProvince, 
                            ee.AddressFiscalCity, 
                            ee.AddressFiscalZipCode, 
                            ee.AddressFiscalMunicipality, 
                            ee.AddressFiscalStreet, 
                            ee.AddressFiscalExtNumber, 
                            ee.AddressFiscalComments, 
                            ee.CreatedOn, 
                            ee.CreatedBy, 
                            ee.DeletedBy, 
                            0, 
                            ee.AddressFiscalCountryCode, 
                            ee.AddressFiscalStateProvinceCode, 
                            ee.AddressFiscalCityCode, 
                            ee.AddressFiscalMunicipalityCode, 
                            0
                        FROM orgBusinessEntityMainInfo AS ee
                        INNER JOIN orgBusinessEntity AS e ON ee.BusinessEntityID = e.BusinessEntityID
                        WHERE ee.AddressFiscalDetailID = @DFiscalID
                    WHEN MATCHED AND (target.AddressDetailID = @DFiscalID) THEN -- Aquí se agrega la condición de coincidencia
                        UPDATE 
                        SET 
                            target.CountryID = 412, 
                            target.StateProvince = ee.AddressFiscalStateProvince,
                            target.City = ee.AddressFiscalCity,
                            target.ZipCode = ee.AddressFiscalZipCode,
                            target.Municipality = ee.AddressFiscalMunicipality,
                            target.Street = ee.AddressFiscalStreet,
                            target.ExtNumber = ee.AddressFiscalExtNumber,
                            target.Comments = ee.AddressFiscalComments,
                            target.CreatedOn = ee.CreatedOn,
                            target.CreatedBy = ee.CreatedBy,
                            target.DeletedBy = ee.DeletedBy,
                            target.UserID = 0,
                            target.CountryCode = ee.AddressFiscalCountryCode,
                            target.StateProvinceCode = ee.AddressFiscalStateProvinceCode,
                            target.CityCode = ee.AddressFiscalCityCode,
                            target.MunicipalityCode = ee.AddressFiscalMunicipalityCode,
                            target.IsFiscalAddress = 0;
                END

            """, (business_entity_id))

    def _settear_valores_cliente_remision(self):

        tbx_cliente = self.componentes_forma['tbx_cliente']
        cliente = tbx_cliente.get()

        self._cliente.official_name = cliente.upper()
        self._cliente.company_type_name = '616 - Sin obligaciones fiscales'
        self._cliente.official_number = 'XAXX010101000'
        self._cliente.forma_pago = '01'
        self._cliente.metodo_pago = 'PUE'
        self._cliente.receptor_uso_cfdi = 'S01'
        self._cliente.reference = 'REMISIÓN'
        self._cliente.customer_type_id = 2

    def _settear_valores_cliente_factura(self):

        tbx_cliente = self.componentes_forma['tbx_cliente']
        cliente = tbx_cliente.get()

        tbx_rfc = self.componentes_forma['tbx_rfc']
        rfc = tbx_rfc.get()
        rfc = rfc.upper() if rfc else rfc

        tbx_rfc2 = self.componentes_forma['tbx_rfc2']
        rfc2 = tbx_rfc2.get()
        rfc2 = rfc2.upper() if rfc2 else rfc2

        tbx_cif = self.componentes_forma['tbx_cif']
        cif = tbx_cif.get()

        self._cliente.official_name = cliente.upper() if cliente else ''
        self._cliente.forma_pago = '99'
        self._cliente.metodo_pago = 'PPD'
        self._cliente.reference = 'FACTURA'
        self._cliente.customer_type_id = 2
        self._cliente.official_number = rfc if rfc else rfc2
        self._cliente.cif = cif



```


## interfaz_panel_pedidos.py

```py
import tkinter as tk
from cayal.ventanas import Ventanas


class InterfazPanelPedidos:
    def __init__(self, master):
        self.master = master
        self.ventanas = Ventanas(self.master)
        self._cargar_frames()
        self._cargar_componentes_forma()

    def _cargar_frames(self):

        frames = {

            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_herramientas': ('frame_principal', None,
                                   {'row': 0, 'column': 0, 'pady': 0, 'padx': 0,
                                    'sticky': tk.W}),

            'frame_totales': ('frame_principal', None,
                              {'row': 0, 'column': 1, 'pady': 0, 'padx': 0,
                               'sticky': tk.E}),

            'frame_meters': ('frame_totales', None,
                             {'row': 0, 'column': 0, 'pady': 0, 'padx': 0,
                              'sticky': tk.W}),

            'frame_filtros': ('frame_principal', None,
                              {'row': 2, 'column': 0, 'columnspan': 2, 'pady': 0, 'padx': 0,
                               'sticky': tk.NSEW}),

            'frame_horarios': ('frame_filtros', None,
                               {'row': 0, 'column': 0, 'pady': 0, 'padx': 0,
                                'sticky': tk.NSEW}),

            'frame_fecha': ('frame_filtros', None,
                            {'row': 0, 'column': 1, 'pady': 0, 'padx': 0,
                             'sticky': tk.NSEW}),

            'frame_den_fecha': ('frame_fecha', None,
                            {'row': 0, 'column': 0, 'pady': 0, 'padx': 0,
                             'sticky': tk.NSEW}),

            'frame_chks': ('frame_fecha', None,
                            {'row': 0, 'column': 1, 'pady': 0, 'padx': 0,
                             'sticky': tk.NSEW}),

            'frame_capturista': ('frame_filtros', None,
                            {'row': 0, 'column': 3, 'pady': 0, 'padx': 0,
                             'sticky': tk.NSEW}),

            'frame_status': ('frame_filtros', None,
                                {'row': 0, 'column': 5, 'pady': 0, 'padx': 0,
                                 'sticky': tk.NSEW}),

            'frame_captura': ('frame_principal', None,
                              {'row': 3, 'columnspan': 2, 'column': 0, 'pady': 0, 'padx':0,
                               'sticky': tk.NSEW}),

            'frame_comentarios': ('frame_principal', None,
            {'row': 4, 'columnspan': 2, 'column': 0, 'pady': 0, 'padx': 0,
             'sticky': tk.NSEW}),

        'frame_detalle': ('frame_principal', None,
                              {'row': 5, 'columnspan': 2, 'column': 0, 'pady': 0, 'padx': 0,
                               'sticky': tk.NSEW}),

        }

        self.ventanas.crear_frames(frames)

    def _cargar_componentes_forma(self):
        ancho, alto = self.ventanas.obtener_resolucion_pantalla()
        tamano_meters =  75 if ancho <= 1367 else None
        componentes = {
            'cbx_horarios': ('frame_horarios', None, 'Horas:', None),

            'cbx_capturista': ('frame_capturista', None, 'Captura:', None),

            'cbx_status': ('frame_status', None, 'Status:', None),

            'den_fecha': ('frame_den_fecha',
                          'normal',   None
                          , None),

            'chk_sin_fecha': ('frame_chks',
                                 {'row': 5, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                 'Sin fecha', None),
            'chk_sin_procesar': ('frame_chks',
                               {'row': 5, 'column': 3, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                               'Sin procesar', None),

            'mtr_total': ('frame_meters', None, 'Total', tamano_meters),
            'mtr_en_tiempo': ('frame_meters', 'success', 'En tiempo', tamano_meters),
            'mtr_a_tiempo': ('frame_meters', 'warning', 'A tiempo', tamano_meters),
            'mtr_retrasado': ('frame_meters', 'danger', 'Retrasos', tamano_meters),
            'tbx_comentarios': ('frame_comentarios', {'row': 0, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                ' ', None),
            'tvw_detalle':('frame_detalle', self.crear_columnas_tabla_detalle(), 5, None)
        }

        self.ventanas.crear_componentes(componentes)
        frame_comentario = self.ventanas.componentes_forma['frame_comentarios']
        frame_comentario.columnconfigure(1, weight=1)  # Asegurar que la columna 1 se extienda
        frame_comentario.rowconfigure(0, weight=1)

        if ancho <= 1367:
            self.ventanas.ocultar_frame('frame_meters')

    def crear_columnas_tabla_detalle(self):
        columnas = [
            {"text": "Cantidad", "stretch": False, 'width': 68, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Clave", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Producto", "stretch": False, 'width': 445, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Precio", "stretch": False, 'width': 80, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Total", "stretch": False, 'width': 100, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Esp.", "stretch": False, 'width': 35, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "ProductID", "stretch": False, 'width': 80, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "DocumentItemID", "stretch": False, 'width': 80, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "ItemProductionStatusModified", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "ClaveUnidad", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "StatusSurtido", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "UnitPrice", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "Piezas", "stretch": False, 'width': 60, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Monto", "stretch": False, 'width': 60, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Especificaciones", "stretch": False, 'width': 440, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "ProductTypeIDCayal", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
        ]

        return self.ventanas.ajustar_columnas_a_resolucion(columnas)

    def crear_columnas_tabla(self):
        columnas = [
            {"text": "Pedido", "stretch": True, "width": 80},
            {"text": "Relacion", "stretch": True, "width": 80},
            {"text": "Factura", "stretch": True, "width": 80},
            {"text": "Cliente", "stretch": False, "width": 130},
            {"text": "F.Captura", "stretch": True, "width": 70},
            {"text": "H.Captura", "stretch": True, "width": 45},
            {"text": "Captura", "stretch": True, "width": 65},
            {"text": "F.Entrega", "stretch": False, "width": 70},
            {"text": "H.Entrega", "stretch": True, "width": 45},
            {"text": "Direccion", "stretch": True, "width": 80},
            {"text": "HoraID", "stretch": False, "width": 0},
            {"text": "WayToPayID", "stretch": False, "width": 0},
            {"text": "F.Pago", "stretch": True, "width": 70},
            {"text": "Status", "stretch": True, "width": 70},
            {"text": "Ruta", "stretch": True, "width": 40},
            {"text": "OrderTypeID", "stretch": False, "width": 0},
            {"text": "Tipo", "stretch": True, "width": 50},
            {"text": "OrderDeliveryTypeID", "stretch": False, "width": 0},
            {"text": "T.Entrega", "stretch": True, "width": 70},
            {"text": "OrderTypeOriginID", "stretch": False, "width": 0},
            {"text": "Origen", "stretch": True, "width": 70},
            {"text": "ProductionTypeID", "stretch": False, "width": 0},
            {"text": "Áreas", "stretch": True, "width": 50},
            {"text": "PriorityID", "stretch": False, "width": 0},
            {"text": "Impreso", "stretch": True, "width": 50},
            {"text": "Prioridad", "stretch": True, "width": 70},
            {"text": "DocumentTypeID", "stretch": False, "width": 0},
            {"text": "T.Docto", "stretch": True, "width": 65},
            {"text": "Adicionales", "stretch": False, "width": 0},
            {"text": "PaymentConfirmedID", "stretch": False, "width": 0},
            {"text": "Pago", "stretch": False, "width": 0},
            {"text": "SubTotal", "stretch": False, "width": 0},
            {"text": "Impuestos", "stretch": False, "width": 0},
            {"text": "Cancelado", "stretch": False, "width": 0},
            {"text": "Total", "stretch": True, "width": 85},
            {"text": "T.Factura", "stretch": True, "width": 85},
            {"text": "Mensajes", "stretch": False, "width": 0},
            {"text": "TypeStatusID", "stretch": False, "width": 0},
            {"text": "StatusScheduleID", "stretch": False, "width": 0},
            {"text": "Comentarios", "stretch": False, "width": 0},
            {"text": "OrderDocumentID", "stretch": False, "width": 0},
            {"text": "BusinessEntityID", "stretch": False, "width": 0},
            {"text": "DepotID", "stretch": False, "width": 0},
            {"text": "AddressDetailID", "stretch": False, "width": 0},
            {"text": "CaptureBy", "stretch": False, "width": 0}
        ]
        return self.ventanas.ajustar_columnas_a_resolucion(columnas)

```


## editar_caracteristicas_pedido.py

```py
import tkinter as tk
from datetime import datetime, timedelta, date

from cayal.ventanas import Ventanas


class EditarCaracteristicasPedido:
    def __init__(self, master, parametros, base_de_datos, utilerias):
        self._master = master
        self._parametros = parametros
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._ventanas = Ventanas(self._master)

        self._hoy = datetime.now().date()
        self._order_document_id = self._parametros.id_principal
        self._user_id = self._parametros.id_usuario
        self._business_entity_id = self._base_de_datos.fetchone(
            'SELECT BusinessEntityID FROM docDocumentOrderCayal WHERE OrderDocumentID = ?',
            (self._order_document_id,))

        self.info_pedido = self._base_de_datos.buscar_info_documento_pedido_cayal(self._order_document_id)[0]
        comments = self.info_pedido['CommentsOrder']
        comments = comments.upper().strip() if comments else comments

        self.info_pedido['CommentsOrder'] = comments

        self.parametros_pedido = {}

        self._cargar_componentes_forma()
        self._inicializar_variables_de_instancia()

        fecha_entrega = self.info_pedido['DeliveryPromise']
        self._filtrar_horario_disponibles(fecha_entrega)


        self._rellenar_componentes()
        self._cargar_eventos()

        self._settear_valores_pedido_desde_base_de_datos()

        if self.info_pedido['RelatedOrderID'] != 0:
            self._bloquear_componentes_segun_tipo_pedido(self._ventanas.obtener_input_componente('cbx_tipo'))
            self._ventanas.bloquear_componente('btn_guardar')


        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Editar caracteristicas', master=self._master)

    def _crear_columnas_tabla(self):
        return [
            {"text": "Folio", "stretch": False, 'width': 80, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Tipo", "stretch": False, 'width': 90, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Entrega", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Hora", "stretch": False, 'width': 60, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Status", "stretch": False, 'width': 120, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "OrderDocumentID", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "MinutosTranscurridos", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
        ]

    def _cargar_componentes_forma(self):
        componentes = [
            ('cbx_tipo', 'Tipo:'),
            ('cbx_documento', 'Documento:'),
            ('cbx_direccion', 'Dirección:'),
            ('cbx_sucursal', 'Sucursal:'),
            ('cbx_prioridad', 'Prioridad:'),
            ('den_fecha', 'Entrega:'),
            ('cbx_horario', 'Horario:'),
            ('cbx_origen', 'Origen:'),
            ('cbx_entrega', 'Entrega:'),
            ('cbx_forma_pago', 'F.Pago:'),
            ('txt_comentario', 'Com.:'),
            ('tvw_pedidos', self._crear_columnas_tabla()),
            ('btn_guardar', 'Guardar')
        ]

        self._ventanas.crear_formulario_simple(componentes, 'Detalles Pedido:', 'Pedidos:')
        self._ventanas.ajustar_ancho_componente('txt_comentario', 63)

    def _cargar_eventos(self):
        eventos = {
            'btn_guardar': self._guardar_parametros_pedido,
            'btn_cancelar': self._master.destroy,
            'tvw_pedidos': (lambda event: self._relacionar_a_pedido(), 'doble_click'),
            'den_fecha': lambda event: self._filtrar_horario_disponibles(
                self._ventanas.obtener_input_componente('den_fecha')),
            'cbx_tipo': lambda event: self._filtrar_horario_disponibles(
                self._ventanas.obtener_input_componente('den_fecha')),

        }
        self._ventanas.cargar_eventos(eventos)

    def _actualizar_horario_de_viene(self):

        fecha_entrega = self.info_pedido['DeliveryPromise']
        if fecha_entrega != self._hoy:
            return

        hora_actual_mas_hora = self._hora_actual_mas_hora()
        consulta = self._base_de_datos.buscar_numero_pedidos_por_horario(fecha_entrega)

        horas = [hora for hora in consulta if
         datetime.strptime(hora['Value'], "%H:%M").time() > hora_actual_mas_hora]

        hora_mas_cercana = horas[0]
        self.info_pedido['ScheduleID'] = hora_mas_cercana['ScheduleID']

    def _rellenar_componentes(self):
        componentes = {
            'cbx_tipo': (self._consulta_tipos_pedidos, 'Value'),
            'cbx_direccion': (self._consulta_direcciones, 'AddressName'),
            'cbx_documento': (self._consulta_tipo_documentos, 'Value'),

            'cbx_origen': (self._consulta_origen_pedidos, 'Value'),
            'cbx_horario': (self._consulta_horarios, 'Value'),
            'cbx_entrega': (self._consulta_tipos_entrega, 'DeliveryTypesName'),
            'cbx_forma_pago': (self._consulta_formas_pago, 'PaymentTermName'),
            'cbx_prioridad': (self._consulta_prioridad_pedidos, 'Value'),
            'cbx_sucursal': (self._consulta_sucursales, 'DepotName'),


        }
        try:
            for nombre, (consulta, campo_consulta) in componentes.items():
                valores = [reg[campo_consulta] for reg in consulta]
                if nombre == 'cbx_prioridad':
                    self._ventanas.rellenar_cbx(nombre, valores, 'sin_seleccione')
                    continue

                self._ventanas.rellenar_cbx(nombre, valores)

            self._ventanas.rellenar_treeview('tvw_pedidos',
                                             self._crear_columnas_tabla(),
                                             self._consulta_pedidos_relacionables)
            if not self._consulta_sucursales:
                self._ventanas.rellenar_cbx('cbx_sucursal', ['No aplica'], sin_seleccione=True)
                self._ventanas.bloquear_componente('cbx_sucursal')

            self._ventanas.insertar_input_componente('txt_comentario', self.info_pedido['CommentsOrder'])

        except:
            print(nombre)

    def _hora_actual_mas_hora(self):
        ahora = datetime.now()
        nueva_hora = ahora + timedelta(hours=1, minutes=00)

        return nueva_hora.time()

    def _hora_actual_mas_hora_y_media(self):
        ahora = datetime.now()
        nueva_hora = ahora + timedelta(hours=1, minutes=30)

        return nueva_hora.time()

    def _hora_actual(self):
        ahora = datetime.now()
        hora_actual_str = f'{ahora.hour:02}:{ahora.minute:02}'
        return datetime.strptime(hora_actual_str, "%H:%M").time()

    def _filtrar_hora_actual(self, consulta):

        tipo_pedido = self._ventanas.obtener_input_componente('cbx_tipo')
        hora_actual = self._hora_actual_mas_hora_y_media() if tipo_pedido != 'Cambio' else self._hora_actual()
        return [hora for hora in consulta if
                     datetime.strptime(hora['Value'], "%H:%M").time() > hora_actual]

    def _inicializar_variables_de_instancia(self):
        self._consulta_tipos_pedidos = self._base_de_datos.buscar_tipos_pedidos_cayal()
        self._consulta_formas_pago = self._base_de_datos.buscar_formas_pago_pedido_cayal()
        self._consulta_tipos_entrega = self._base_de_datos.buscar_tipos_entrega_pedido_cayal()
        self._consulta_prioridad_pedidos = self._base_de_datos.buscar_tipos_prioridad_pedidos_cayal()
        self._consulta_origen_pedidos = self._base_de_datos.buscar_tipo_origen_pedidos_cayal()

        consulta_pedidos_relacionables = self._base_de_datos.buscar_pedidos_relacionables(self._business_entity_id)
        self._consulta_pedidos_relacionables = [ reg for reg in consulta_pedidos_relacionables
                                                 if reg['OrderDocumentID'] != self._order_document_id]

        self._consulta_horarios = None
        self._consulta_direcciones = self._base_de_datos.buscar_direcciones(self._business_entity_id)
        self._consulta_sucursales = self._base_de_datos.buscar_sucursales(self._business_entity_id)
        self._consulta_tipo_documentos = [{'ID':0, 'Value':'FACTURA'},{'ID':1, 'Value':'REMISIÓN'}]

    def _validar_fecha_pedido(self):

        fecha_pedido = self._ventanas.obtener_input_componente('den_fecha')
        if fecha_pedido < self._hoy:
            return False

        return fecha_pedido

    def _normalizar_a_date(self, f):
        if f is None:
            return None
        if isinstance(f, date) and not isinstance(f, datetime):
            return f
        if isinstance(f, datetime):
            return f.date()
        if isinstance(f, str):
            # Ajusta a tu utilería si ya tienes una
            try:
                # intenta formatos comunes
                try:
                    return datetime.strptime(f, "%Y-%m-%d").date()
                except ValueError:
                    return datetime.strptime(f, "%Y-%m-%d %H:%M:%S").date()
            except ValueError:
                # como último recurso
                return self._utilerias.convertir_fecha_str_a_datetime(f)
        return None

    def _filtrar_horario_disponibles(self, fecha):
        # 1) Trae SIEMPRE la lista completa
        consulta_completa = self._base_de_datos.buscar_horarios_pedido_cayal()

        # 2) Normaliza la fecha recibida o usa la del control si no viene
        fecha_entrega = self._normalizar_a_date(fecha) or self._validar_fecha_pedido() or self._hoy

        # 3) Si NO es hoy -> todos los horarios (sin filtrar por disponibilidad del día ni hora actual)
        if fecha_entrega != self._hoy:
            self._consulta_horarios = list(consulta_completa)  # copia nueva
        else:
            # 4) Si ES hoy -> aplica disponibilidad y quita horas pasadas (según tu lógica)
            consulta = self._base_de_datos.buscar_numero_pedidos_por_horario(fecha_entrega)
            disponibles = [h for h in consulta if int(h['OrdersNumber']) < int(h['Quantity'])]
            self._consulta_horarios = self._filtrar_hora_actual(disponibles)

        # 5) Arma los valores a mostrar
        valores = [reg['Value'] for reg in self._consulta_horarios]

        # 6) Si el pedido ya tenía horario y es HOY, anteponer el horario original para permitir conservarlo
        if self.info_pedido.get('DeliveryPromise') and fecha_entrega == self._hoy:
            schedule_order_id = self.info_pedido['ScheduleID']
            try:
                horario_pedido = next(r for r in consulta_completa if int(r['ScheduleID']) == int(schedule_order_id))
                if horario_pedido['Value'] not in valores:
                    valores.insert(0, horario_pedido['Value'])
                    self._consulta_horarios.insert(0, horario_pedido)
            except StopIteration:
                pass

        # 7) Rellenar el combo SIEMPRE desde la lista recién construida
        self._ventanas.rellenar_cbx('cbx_horario', valores)

    def _settear_valores_pedido_desde_base_de_datos(self):


        if not self.info_pedido['DeliveryPromise']:

            priority_id = self.info_pedido['PriorityID']

            priority = [tipo['Value'] for tipo in self._consulta_prioridad_pedidos
                          if priority_id == tipo['ID']][0]

            address_detail_id = self.info_pedido['AddressDetailID']
            address_name = [tipo['AddressName'] for tipo in self._consulta_direcciones
                          if address_detail_id == tipo['AddressDetailID']][0]

            if self._consulta_sucursales:
                depot_id = self.info_pedido['DepotID']

                if depot_id != 0:
                    depot_name = [tipo['DepotName'] for tipo in self._consulta_sucursales
                              if depot_id == tipo['DepotID']][0]
                    self._ventanas.insertar_input_componente('cbx_sucursal', depot_name)




            self._ventanas.insertar_input_componente('cbx_documento', self.info_pedido['DocumentType'])
            self._ventanas.insertar_input_componente('cbx_direccion', address_name)
            self._ventanas.insertar_input_componente('cbx_prioridad', priority)

            return

        payment_term_name = self.info_pedido['PaymentTermName']
        comments = self.info_pedido['CommentsOrder']
        comments = comments.upper() if comments else ''

        order_type_id = self.info_pedido['OrderTypeID']
        order_type = [tipo['Value'] for tipo in self._consulta_tipos_pedidos
                      if order_type_id == tipo['ID']][0]

        order_type_origin_id = self.info_pedido['OrderTypeOriginID']
        order_type_origin = [tipo['Value'] for tipo in self._consulta_origen_pedidos
                             if order_type_origin_id == tipo['ID']][0]

        order_delivery_type_id = self.info_pedido['OrderDeliveryTypeID']

        order_delivery_type = [tipo['DeliveryTypesName'] for tipo in self._consulta_tipos_entrega
                               if order_delivery_type_id == tipo['DeliveryTypesID']][0]

        priority_id = self.info_pedido['PriorityID']

        priority = [tipo['Value'] for tipo in self._consulta_prioridad_pedidos
                    if priority_id == tipo['ID']][0]

        address_detail_id = self.info_pedido['AddressDetailID']
        address_name = [tipo['AddressName'] for tipo in self._consulta_direcciones
                        if address_detail_id == tipo['AddressDetailID']][0]


        delivery_promise = self.info_pedido['DeliveryPromise']

        self._ventanas.insertar_input_componente('cbx_documento', self.info_pedido['DocumentType'])
        self._ventanas.insertar_input_componente('cbx_direccion', address_name)
        self._ventanas.insertar_input_componente('cbx_prioridad', priority)
        self._ventanas.insertar_input_componente('den_fecha', delivery_promise)
        self._ventanas.insertar_input_componente('cbx_entrega', order_delivery_type)
        self._ventanas.insertar_input_componente('cbx_origen', order_type_origin)
        self._ventanas.insertar_input_componente('cbx_tipo', order_type)
        self._ventanas.insertar_input_componente('txt_comentario', comments)
        self._ventanas.insertar_input_componente('cbx_forma_pago', payment_term_name)



        schedule_order_id = self.info_pedido['ScheduleID']
        if self._consulta_horarios:
            schedule_order = [tipo['Value'] for tipo in self._consulta_horarios
                              if int(schedule_order_id) == int(tipo['ScheduleID'])][0]
            if schedule_order:
                self._ventanas.insertar_input_componente('cbx_horario', schedule_order)

        if self._consulta_sucursales:
            depot_id = self.info_pedido['DepotID']

            if depot_id != 0:
                depot_name = [tipo['DepotName'] for tipo in self._consulta_sucursales
                              if depot_id == tipo['DepotID']][0]
                self._ventanas.insertar_input_componente('cbx_sucursal', depot_name)

    def _relacionar_a_pedido(self):

        tipo_pedido = self._ventanas.obtener_input_componente('cbx_tipo')

        if tipo_pedido in ('Seleccione', 'Pedido'):
            self._ventanas.mostrar_mensaje('Esta opción es solo válida para anexos y cambios.')
            return

        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_pedidos')
        if len(fila) > 1 or len(fila) < 1:
            self._ventanas.mostrar_mensaje('Debe seleccionar solo un registro.')
            return

        valores_fila = self._ventanas.obtener_valores_fila_treeview('tvw_pedidos', fila)

        if tipo_pedido == 'Anexo':
            fecha_entrega_str = valores_fila[2]
            fecha_entrega = self._utilerias.convertir_fecha_str_a_datetime(fecha_entrega_str)
            fecha_pedido = self._ventanas.obtener_input_componente('den_fecha')
            minutos_transcurridos = int(valores_fila[6])

            if not self._validar_fecha_pedido():
                self._ventanas.mostrar_mensaje('La fecha no puede ser menor al día de hoy.')
                return

            if fecha_entrega < self._hoy:
                self._ventanas.mostrar_mensaje('Solo puede relacionar anexos a pedidos del mismo día.')
                return

            if tipo_pedido == 'Anexo' and minutos_transcurridos > 30:
                self._ventanas.mostrar_mensaje('Solo puede capturar anexos dentro de los 30 primeros minutos'
                                               'después de la captura del pedido.')
                return

            if fecha_pedido < self._hoy:
                self._ventanas.mostrar_mensaje('Los anexos solo se pueden asignar a pedidos del día.')
                return

        folio_pedido = valores_fila[0]
        respuesta = self._ventanas.mostrar_mensaje_pregunta(
            f'Desea relacionar el {tipo_pedido} con el pedido {folio_pedido}')

        if not respuesta:
            return

        order_document_id = int(valores_fila[5])

        self._asignar_valores_pedido_a_anexo_o_cambio(order_document_id, tipo_pedido)

    def _buscar_parametros_pedido_asignable(self, order_document_id):
        consulta = self._base_de_datos.buscar_parametros_pedido(order_document_id)

        if not consulta:
            return False

        consulta = consulta[0]
        self.parametros_pedido = consulta

        return consulta

    def _asignar_valores_pedido_a_anexo_o_cambio(self, order_document_id, tipo_pedido):

        consulta_order_document_id = self._buscar_parametros_pedido_asignable(order_document_id)

        if not consulta_order_document_id:
            return

        componentes_actualizables_anexo = ['cbx_tipo', 'cbx_origen', 'cbx_horario', 'cbx_entrega',
                                           'cbx_prioridad', 'cbx_forma_pago']

        componentes_actualizables_cambio_hoy = ['cbx_tipo', 'cbx_origen', 'cbx_horario', 'cbx_entrega',
                                                'cbx_forma_pago']

        componentes_actualizables_cambio_otros_dias = ['cbx_tipo', 'cbx_prioridad', 'cbx_forma_pago']

        # asginar valores de la consulta de la bd a los componentes de la forma
        componentes = {
            'cbx_tipo': (self._consulta_tipos_pedidos, 'ID', 'Value', 'OrderTypeID'),
            'cbx_origen': (self._consulta_origen_pedidos, 'ID', 'Value', 'OrderTypeOriginID'),
            'cbx_horario': (self._consulta_horarios, 'ScheduleID', 'Value', 'ScheduleID'),
            'cbx_entrega': (self._consulta_tipos_entrega,
                            'DeliveryTypesID',
                            'DeliveryTypesName',
                            'OrderDeliveryTypeID'),
            'cbx_prioridad': (self._consulta_prioridad_pedidos, 'ID', 'Value', 'PriorityID'),
            'cbx_forma_pago': (self._consulta_formas_pago, 'PaymentTermID', 'PaymentTermName', 'WayToPayID')
        }

        for nombre, (consulta, campo_consulta, seleccion_consulta, campo_tabla) in componentes.items():
            valor_bd = self.parametros_pedido[campo_tabla]

            #  setear el tipo de pedido segun el caso
            if tipo_pedido == 'Anexo':
                if nombre == 'cbx_tipo':
                    valor_bd = 2

            if tipo_pedido == 'Cambio':
                if nombre == 'cbx_tipo':
                    valor_bd = 3

            valor_componente = [reg[seleccion_consulta] for reg in consulta if reg[campo_consulta] == valor_bd]

            if valor_componente:

                if tipo_pedido == 'Anexo':
                    if nombre in componentes_actualizables_anexo:
                        self._ventanas.insertar_input_componente(nombre, valor_componente[0])

                if tipo_pedido == 'Cambio':
                    fecha_pedido_original = consulta_order_document_id['CreatedOn']

                    if fecha_pedido_original != self._hoy:
                        if nombre in componentes_actualizables_cambio_otros_dias:
                            self._ventanas.insertar_input_componente(nombre, valor_componente[0])

                    if fecha_pedido_original == self._hoy:
                        if nombre in componentes_actualizables_cambio_hoy:
                            self._ventanas.insertar_input_componente(nombre, valor_componente[0])

        self._bloquear_componentes_segun_tipo_pedido(tipo_pedido)
        self._actualizar_parametros_nuevos_anexo_o_cambio(order_document_id, tipo_pedido)

    def _actualizar_parametros_nuevos_anexo_o_cambio(self, order_document_id, tipo_pedido):
        self.parametros_pedido['OrderTypeID'] = 2 if tipo_pedido == 'Anexo' else 3
        self.parametros_pedido['RelatedOrderID'] = order_document_id
        self.parametros_pedido['CreatedOn'] = datetime.now()
        self.parametros_pedido['CreatedBy'] = self._parametros.id_usuario
        self.parametros_pedido['HostName'] = self._utilerias.obtener_hostname()

    def _bloquear_componentes_segun_tipo_pedido(self, tipo_pedido):
        # bloquear los componentes
        componentes_a_bloquear_anexo = ['den_fecha', 'cbx_tipo', 'cbx_horario', 'cbx_origen', 'cbx_entrega',
                                        'cbx_forma_pago', 'cbx_prioridad']

        componentes_a_bloquear_cambio = ['den_fecha', 'cbx_tipo',
                                         'cbx_prioridad']

        componentes_a_bloquear = componentes_a_bloquear_anexo if tipo_pedido == 'Anexo' else componentes_a_bloquear_cambio

        for nombre in componentes_a_bloquear:
            self._ventanas.bloquear_componente(nombre)

    def _validar_inputs_formulario(self):
        for nombre, componente in self._ventanas.componentes_forma.items():

            tipo = nombre[:3]  # 'den' o 'cbx'

            if tipo == 'den':
                fecha_entrega = self._ventanas.obtener_input_componente('den_fecha')
                # valida que exista y no sea menor a hoy
                if not fecha_entrega or fecha_entrega < self._hoy:
                    self._ventanas.mostrar_mensaje('La fecha de entrega no puede ser menor a la fecha actual.')
                    return False

            if tipo == 'cbx':
                seleccion = self._ventanas.obtener_input_componente(nombre)

                if nombre == 'cbx_documento' and seleccion == 'Seleccione':
                    self._ventanas.mostrar_mensaje('Debe seleccionar un tipo de documento válido.')
                    return False

                if nombre == 'cbx_sucursal' and seleccion == 'Seleccione':
                    self._ventanas.mostrar_mensaje('Debe seleccionar una sucursal válida.')
                    return False

                if nombre == 'cbx_direccion' and seleccion == 'Seleccione':
                    self._ventanas.mostrar_mensaje('Debe seleccionar una dirección válida.')
                    return False

                if nombre == 'cbx_tipo' and seleccion not in ('Seleccione', 'Pedido'):
                    comentario = (self._ventanas.obtener_input_componente('txt_comentario') or '').strip()
                    if len(comentario) < 5:
                        self._ventanas.mostrar_mensaje(
                            'Para anexos y cambios el comentario es obligatorio (mínimo 5 caracteres).'
                        )
                        return False

                if seleccion == 'Seleccione':
                    etiqueta = nombre[4:].replace('_', ' ').capitalize()
                    self._ventanas.mostrar_mensaje(f'Debe seleccionar una opción válida para {etiqueta}.')
                    return False

        if not self._validar_fecha_pedido():
            return False

        return True

    def _procesar_seleccion_usuario(self):

        tipo_pedido = self._ventanas.obtener_input_componente('tbx_tipo')
        if tipo_pedido in ('Anexo', 'Cambio'):
            return

        componentes = {
            'cbx_direccion': (self._consulta_direcciones, 'AddressDetailID', 'AddressName', 'AddressDetailID'),
            'cbx_tipo': (self._consulta_tipos_pedidos, 'ID', 'Value', 'OrderTypeID'),
            'cbx_documento': (self._consulta_tipo_documentos, 'ID', 'Value', 'DocumentTypeID'),

            'cbx_origen': (self._consulta_origen_pedidos, 'ID', 'Value', 'OrderTypeOriginID'),
            'cbx_horario': (self._consulta_horarios, 'ScheduleID', 'Value', 'ScheduleID'),
            'cbx_entrega': (
            self._consulta_tipos_entrega, 'DeliveryTypesID', 'DeliveryTypesName', 'OrderDeliveryTypeID'),
            'cbx_prioridad': (self._consulta_prioridad_pedidos, 'ID', 'Value', 'PriorityID'),
            'cbx_forma_pago': (self._consulta_formas_pago, 'PaymentTermID', 'PaymentTermName', 'WayToPayID')
        }
        valores_pedido = {}
        for nombre, (consulta, campo_consulta, seleccion_consulta, campo_tabla) in componentes.items():
            seleccion = self._ventanas.obtener_input_componente(nombre)

            valor = [reg[campo_consulta] for reg in consulta if seleccion == reg[seleccion_consulta]][0]
            valores_pedido[campo_tabla] = valor

        valores_pedido['DeliveryPromise'] = self._ventanas.obtener_input_componente('den_fecha')
        comentario_pedido = self._ventanas.obtener_input_componente('txt_comentario')
        valores_pedido['CommentsOrder'] = comentario_pedido.upper().strip() if comentario_pedido else ''
        valores_pedido['BusinessEntityID'] = self._business_entity_id

        related_order_id = self.parametros_pedido.get('RelatedOrderID', 0)
        valores_pedido['RelatedOrderID'] = related_order_id
        valores_pedido['ZoneID'] = self.info_pedido['ZoneID']
        valores_pedido['OrderDeliveryCost'] = self._base_de_datos.buscar_costo_servicio_domicilio(valores_pedido['AddressDetailID'])

        way_to_pay_id = valores_pedido.get('WayToPayID', 1)
        payment_confirmed_id = 1
        delivery_type_id = valores_pedido.get('OrderDeliveryTypeID', 1)

        # si la forma de pago es transferencia el id es transferencia no confirmada
        if way_to_pay_id == 6:
            payment_confirmed_id = 2

        # si el tipo de entrga es viene y la fomra de pago NO es transferencia entonces la forma de pago es en tienda
        if delivery_type_id == 2 and way_to_pay_id != 6:
            payment_confirmed_id = 4

        valores_pedido['PaymentConfirmedID'] = payment_confirmed_id

        #caso especial sucursales
        if not self._consulta_sucursales:
            valores_pedido['DepotID'] = self.info_pedido['DepotID']
        else:
            depot_name = self._ventanas.obtener_input_componente('cbx_sucursal')
            depot_id = [tipo['DepotID'] for tipo in self._consulta_sucursales
                          if depot_name == tipo['DepotName']][0]
            valores_pedido['DepotID'] = depot_id

        self.parametros_pedido = valores_pedido

    def _guardar_parametros_pedido(self):
        if self._validar_inputs_formulario():
            self._procesar_seleccion_usuario()

            order_related_id = self.parametros_pedido['RelatedOrderID']
            tipo_pedido = self._ventanas.obtener_input_componente('cbx_tipo')

            if tipo_pedido in ('Anexo', 'Cambio') and order_related_id == 0:
                self._ventanas.mostrar_mensaje('Debe relacionar el anexo o el cambio con un pedido.')
                self.parametros_pedido = {}
            else:

                # aqui actualiza el horario de un pedido de viene a hora de entrega a 1 hora despues de procesado
                order_delivery_type_id = self.parametros_pedido['OrderDeliveryTypeID']
                if order_delivery_type_id == 2:
                    self._actualizar_horario_de_viene()

                self._actualizar_docdocument_order_cayal(self._order_document_id, self.parametros_pedido)

                # para el caso de anexo o cambio hay que marcarlos como urgentes en el horario mas cercano a realizar
                # en caso que la orden sea un anexo o un pedido hay que actualizar dicho documento
                if tipo_pedido in ('Anexo', 'Cambio'):
                    consulta_completa = self._base_de_datos.buscar_horarios_pedido_cayal()

                    horario_disponible = [hora for hora in consulta_completa if
                                          datetime.strptime(hora['Value'], "%H:%M").time() > self._hora_actual()]
                    schedule_id = 1

                    order_type_id = 2 if tipo_pedido == 'Anexo' else 3

                    if horario_disponible:
                        schedule_id = horario_disponible[0]['ScheduleID']
                        schedule_id_order_related = [hora['ScheduleID'] for hora in consulta_completa
                                                     if self._ventanas.obtener_input_componente('cbx_horario') == hora['Value']
                                                    ][0]
                        schedule_id = schedule_id_order_related if schedule_id <= schedule_id_order_related else schedule_id

                    self._base_de_datos.command(
                        """
                        DECLARE @OrderID INT = ?
                        UPDATE docDocumentOrderCayal
                        SET NumberAdditionalOrders = (SELECT Count(OrderDocumentID)
                                                     FROM docDocumentOrderCayal
                                                     WHERE RelatedOrderID = @OrderID AND CancelledOn IS NULL),
                            StatusID = 2,
                            ScheduleID = ?, 
                            PriorityID = 2,
                            OrderTypeID = ?
                        WHERE OrderDocumentID = @OrderID
                        """,
                        (self._order_document_id, schedule_id, order_type_id)
                    )

                self._master.destroy()

    def _actualizar_docdocument_order_cayal(self, order_document_id, valores_actualizacion):
        """
        Actualiza la tabla 'docdocumentordercayal' con los valores proporcionados en el diccionario.

        :param order_document_id: ID del documento de pedido a actualizar.
        :param valores_actualizacion: Diccionario con los campos y valores a actualizar.
        """
        # Crear la parte dinámica del SET en el query
        campos_set = ", ".join([f"{campo} = ?" for campo in valores_actualizacion.keys()])

        # Crear el query SQL dinámico
        query = f"""
            UPDATE docDocumentOrderCayal
            SET {campos_set}
            WHERE OrderDocumentID = ?
        """

        # Preparar los valores en el orden correcto
        valores = list(valores_actualizacion.values()) + [order_document_id]

        # Ejecutar el comando
        self._base_de_datos.command(query, tuple(valores))

        # Actualiza la bitacora de cambios
        self._actualizar_bitacora(valores_actualizacion)

    def _actualizar_bitacora(self, valores_actualizacion):
        claves_bitacora = self._encontrar_claves_diferentes(self.info_pedido, valores_actualizacion)

        valores_bitacora = {

            'AddressDetailID':  (26, 'Dirección actualizada:', self._consulta_direcciones, 'AddressName', 'AddressDetailID'),
            'OrderTypeID': (44,'Tipo de orden cambiada:', self._consulta_tipos_pedidos, 'Value', 'ID'),
            'OrderTypeOriginID': (28,'Origen de orden actualizada:', self._consulta_origen_pedidos, 'Value', 'ID'),
            'ScheduleID': (21,'Horario actualizado:', self._consulta_horarios, 'Value', 'ScheduleID'),
            'OrderDeliveryTypeID': (25,'Forma de entrega actualizada:', self._consulta_tipos_entrega, 'DeliveryTypesName', 'DeliveryTypesID'),
            'PriorityID': (29,'Prioridad actualizada:', self._consulta_prioridad_pedidos, 'Value','ID'),
            'WayToPayID': (24,'Forma de pago actualizada:', self._consulta_formas_pago, 'PaymentTermName', 'PaymentTermID'),
            'DeliveryPromise': (22,'Promesa de entrega actualizada:', None, None),
            'CommentsOrder': (30,'Comentario modificado:', None, None),
            'RelatedOrderID': (45,'Relación agregada:', None, None),
            'DocumentTypeID': (46,'Tipo documento actualizado:', self._consulta_tipo_documentos, 'Value', 'ID'),
            'OrderDeliveryCost': (47,'Costo de envío actualizado'),
            'DepotID': (27, 'Sucursal actualizada:', self._consulta_sucursales, 'DepotName', 'DepotID')
        }
        user_name = self._base_de_datos.buscar_nombre_de_usuario(self._user_id)

        for clave in claves_bitacora:
            try:
                change_type_id = valores_bitacora[clave][0]
                comentario = valores_bitacora[clave][1]

                valor_nuevo = ''
                valor_anterior = ''
                consulta = valores_bitacora[clave][2]
                valor_buscado = ''
                valor_buscado_id = 0

                if clave not in ('DeliveryPromise', 'CommentsOrder', 'RelatedOrderID'):
                    valor_buscado = valores_bitacora[clave][3]
                    valor_buscado_id = valores_bitacora[clave][4]

                if clave not in ('ScheduleID','DepotID','DeliveryPromise', 'CommentsOrder', 'RelatedOrderID'):
                    valor_nuevo = [reg[valor_buscado] for reg in consulta if  reg[valor_buscado_id] == valores_actualizacion[clave]][0]
                    valor_anterior = [reg[valor_buscado] for reg in consulta if reg[valor_buscado_id] == self.info_pedido[clave]][0]

                if clave == 'ScheduleID':
                    valor_nuevo = [reg[valor_buscado] for reg in consulta if reg[valor_buscado_id] == valores_actualizacion[clave]][0]

                if clave == 'DepotID' and self._consulta_sucursales:
                    valor_nuevo = [reg[valor_buscado] for reg in consulta if reg[valor_buscado_id] == valores_actualizacion[clave]][0]
                    if self.info_pedido[clave] != 0:
                        valor_anterior = [reg[valor_buscado] for reg in consulta if reg[valor_buscado_id] == self.info_pedido[clave]][0]

                if clave in ('CommentsOrder', 'DeliveryPromise'):
                    valor_nuevo = valores_actualizacion[clave]
                    valor_anterior = self.info_pedido[clave]

                if clave ==  'RelatedOrderID':
                    nueva_consulta =  self._base_de_datos.buscar_info_documento_pedido_cayal(valores_actualizacion[clave])
                    if consulta:
                        info_pedido = nueva_consulta[0]
                        valor_nuevo = info_pedido['DocFolio']

                comentario = f"{comentario} {user_name} - {valor_anterior} --> {valor_nuevo}"
                self._base_de_datos.insertar_registro_bitacora_pedidos(self._order_document_id,
                                                                       change_type_id=change_type_id,
                                                                       comments=comentario,
                                                                       user_id=self._user_id)
            except:
                print(clave)

    def _encontrar_claves_diferentes(self, dict1, dict2):
        """
        Compara dos diccionarios y devuelve una lista de claves con valores diferentes.
        :param dict1: Primer diccionario.
        :param dict2: Segundo diccionario.
        :return: Lista de claves con valores diferentes.
        """
        # Verificar las claves compartidas entre ambos diccionarios
        claves_comunes = set(dict1.keys()).intersection(set(dict2.keys()))
        # Encontrar las claves con valores diferentes
        claves_diferentes = [
            clave for clave in claves_comunes if dict1[clave] != dict2[clave]
        ]
        return claves_diferentes
```


## capturado_vs_producido.py

```py
import tkinter as tk
from cayal.ventanas import Ventanas

class CapturadoVsProducido:
    def __init__(self, master, parametros, base_de_datos, utilerias, valores_fila):
        self._master = master
        self._parametros = parametros
        self._order_document_id = self._parametros.id_principal
        self._valores_fila = valores_fila

        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._ventanas = Ventanas(self._master)

        self._partidas_capturadas = []
        self._partidas_editadas = []
        self._partidas_producidas = []

        self._crear_frames()
        self._crear_componetes()
        self._rellenar_componentes()
        self._cargar_eventos()
        self._ventanas.configurar_ventana_ttkbootstrap()

    def _cargar_eventos(self):
        eventos = {
            'tvw_editado':(lambda event: self._actualizar_comentario_editado(), 'seleccion')
        }

        self._ventanas.cargar_eventos(eventos)

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_componentes': ('frame_principal', None,
                                  {'row': 0, 'column': 0, 'pady': 2, 'padx': 2,
                                   'sticky': tk.NSEW}),

            'frame_comentario': ('frame_componentes', 'Comentario',
                                 {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                  'sticky': tk.NSEW}),

            'frame_tabla1': ('frame_componentes', 'Capturado',
                             {'row': 1, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                              'sticky': tk.NSEW}),

            'frame_tabla_captura': ('frame_tabla1', None,
                             {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                              'sticky': tk.NSEW}),


            'frame_total1': ('frame_tabla1', 'Total Capturado',
                             {'row': 1, 'column': 0,  'pady': 2, 'padx': 2,  'columnspan': 2,
                              'sticky': tk.NSEW}),

            'frame_info1': ('frame_total1', None,
                             {'row': 0, 'column': 2, 'columnspan': 2, 'pady': 2, 'padx': 2,
                              'sticky': tk.NSEW}),

            'frame_tabla2': ('frame_componentes', 'Producido',
                             {'row': 2, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                              'sticky': tk.NSEW}),

            'frame_tabla_producido': ('frame_tabla2', None,
                                    {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                     'sticky': tk.NSEW}),

            'frame_total2': ('frame_tabla2', 'Total Producido:',
                             {'row': 1, 'column': 0, 'pady': 2, 'padx': 2,  'columnspan': 2,
                              'sticky': tk.NSEW}),

            'frame_info2': ('frame_total2', None,
                            {'row': 0, 'column': 2, 'pady': 2, 'padx': 2, 'columnspan': 2,
                             'sticky': tk.NSEW}),

            'frame_monto': ('frame_componentes', None,
                            {'row': 3, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                             'sticky': tk.NSEW}),

            'frame_tabla3': ('frame_monto', 'Editadas',
                              {'row': 5, 'column': 1, 'padx': 0, 'pady': 5, 'sticky': tk.W}),

            'frame_comentario_partida': ('frame_tabla3', 'Comentario',
                                 {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                  'sticky': tk.NSEW}),

            'frame_tabla_editado': ('frame_tabla3', None,
                                      {'row': 1, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                       'sticky': tk.NSEW}),

        }
        self._ventanas.crear_frames(frames)

    def _crear_componetes(self):
        componentes = {
            'txt_comentario': ('frame_comentario', None, ' ', None),
            'tbx_total_pedido': ('frame_total1',
                                   {'row': 0, 'column': 1, 'pady': 2, 'padx': 2, 'sticky': tk.NE},
                                   ' ', None),
            'tbx_info_pedido': ('frame_info1',
                                 {'row': 0, 'column': 1, 'pady': 2, 'padx': 2, 'sticky': tk.NE},
                                 ' ', None),
            'tvw_pedido': ('frame_tabla_captura', self._crear_columnas_tabla(), 6, None),
            'tbx_total_producido': ('frame_total2',
                                  {'row': 0, 'column': 1, 'pady': 2, 'padx': 2, 'sticky': tk.W},
                                  ' ', None),
            'tbx_info_producido': ('frame_info2',
                                {'row': 0, 'column': 1, 'pady': 2, 'padx': 2, 'sticky': tk.W},
                                ' ', None),

            'tvw_producido': ('frame_tabla_producido', self._crear_columnas_tabla(), 6, 'danger'),

            'txt_comentario_partida': ('frame_comentario_partida', None, ' ', None),
            'tvw_editado': ('frame_tabla_editado', self._crear_columnas_tabla(), 6, 'warning'),
        }
        self._ventanas.crear_componentes(componentes)

        self._ventanas.ajustar_componente_en_frame('frame_info1', 'frame_total1')
        self._ventanas.ajustar_componente_en_frame('frame_info2', 'frame_total2')
        self._ventanas.bloquear_componente('tbx_info_pedido')
        self._ventanas.bloquear_componente('tbx_info_producido')

        self._ventanas.ajustar_componente_en_frame('txt_comentario', 'frame_comentario')
        self._ventanas.ajustar_componente_en_frame('txt_comentario_partida', 'frame_comentario_partida')

    def _crear_columnas_tabla(self):
        return [
            {'text': 'N', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E, 'hide': 1},
            {'text': 'Cantidad', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {'text': 'Clave', "stretch": False, 'width': 110, 'column_anchor': tk.W, 'heading_anchor': tk.W, 'hide': 0},
            {'text': 'Producto', "stretch": False, 'width': 260, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'Precio', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E, 'hide': 0},
            {'text': 'Subtotal', "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {'text': 'TaxTypeID', "stretch": False, 'width': 0, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {'text': 'ProductID', "stretch": False, 'width': 0, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {'text': 'ClaveUnidad', "stretch": False, 'width': 0, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {'text': 'Impuestos', "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {'text': 'Total', "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E, 'hide': 0},
            {'text': 'DocumentItemID', "stretch": False, 'width': 0, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {'text': 'ItemProductionStatusModified', "stretch": False, 'width': 0, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {'text': 'Comments', "stretch": False, 'width': 0, 'column_anchor': tk.E,
             'heading_anchor': tk.E,
             'hide': 1},
        ]

    def _rellenar_totales(self, tabla, partidas):
        total_acumulado = 0
        for partida in partidas:
            total_acumulado += self._utilerias.redondear_valor_cantidad_a_decimal(partida['Total'])

        total_acumulado_moneda = self._utilerias.convertir_decimal_a_moneda(total_acumulado)
        tbx = 'tbx_total_pedido' if tabla =='tvw_pedido' else 'tbx_total_producido'
        self._ventanas.insertar_input_componente(tbx, total_acumulado_moneda)
        self._ventanas.bloquear_componente(tbx)

    def _rellenar_componentes(self):
        self._consultar_info_partidas()

        partidas_capturadas = self._procesar_partidas(self._partidas_capturadas)
        partidas_capturadas = self._ordenar_consulta(partidas_capturadas, 'ProductName')
        self._rellenar_totales('tvw_pedido', partidas_capturadas)
        self._ventanas.rellenar_treeview(_treeview='tvw_pedido',
                                         columnas=self._crear_columnas_tabla(),
                                         consulta= partidas_capturadas,
                                         variar_color_filas=False,
                                         valor_barra_desplazamiento=6
                                         )

        partidas_producidas = self._procesar_partidas(self._partidas_producidas)
        partidas_producidas = self._ordenar_consulta(partidas_producidas, 'ProductName')
        self._rellenar_totales('tvw_producido', partidas_producidas)
        self._ventanas.rellenar_treeview(_treeview='tvw_producido',
                                         columnas=self._crear_columnas_tabla(),
                                         consulta=partidas_producidas,
                                         variar_color_filas=False,
                                         valor_barra_desplazamiento=6
                                         )

        self._ventanas.rellenar_treeview(_treeview='tvw_editado',
                                         columnas=self._crear_columnas_tabla(),
                                         consulta=self._procesar_partidas(self._partidas_editadas),
                                         variar_color_filas=False,
                                         valor_barra_desplazamiento=6
                                         )

        self._ventanas.insertar_input_componente('txt_comentario', self._valores_fila['Comentarios'])
        self._ventanas.bloquear_componente('txt_comentario')


        texto_captura = f"Capturado por: {self._valores_fila['Captura']}"
        self._ventanas.insertar_input_componente('tbx_info_pedido', texto_captura)
        self._ventanas.ajustar_componente_en_frame('tbx_info_pedido', 'frame_info1')

        consulta = self._buscar_responsables_produccion_pedido()
        if consulta:
            produccion = consulta[0]['UsuarioProduccion']
            almacen = consulta[0]['UsuarioAlmacen']
            minisuper = consulta[0]['UsuarioMinisuper']

            produccion = '' if produccion == '' else f"Producción:{produccion}"
            almacen = '' if almacen == '' else f"Almacén:{almacen}"
            minisuper = '' if minisuper == '' else f"Minisuper:{minisuper}"

            texto_producido = f"{produccion} {almacen} {minisuper}".strip()
            self._ventanas.insertar_input_componente('tbx_info_producido', texto_producido)
            self._ventanas.ajustar_componente_en_frame('tbx_info_producido', 'frame_info2')

        self._colorear_partidas_editadas()

    def _ordenar_consulta(self, consulta, clave, descendente=False):
        """
        Ordena una lista de diccionarios por el valor de una clave específica.

        :param lista: Lista de diccionarios a ordenar
        :param clave: Clave por la cual se ordenará
        :param descendente: Si es True, ordena de forma descendente
        :return: Lista ordenada
        """
        return sorted(consulta, key=lambda x: x.get(clave, ''), reverse=descendente)

    def _consultar_info_partidas(self):
        self._partidas_capturadas = self._base_de_datos.fetchall("""
                            DECLARE @OrderDocumentID INT = ?
                            SELECT * FROM [dbo].[zvwBuscarPartidasPedidoCayal-DocumentID](@OrderDocumentID)
                            """, (self._order_document_id,))

        self._partidas_editadas = self._base_de_datos.fetchall("""
                            DECLARE @OrderDocumentID INT = ?
                            SELECT * FROM [dbo].[zvwBuscarPartidasPedidoCayalExtra-DocumentID](@OrderDocumentID)
                            """, (self._order_document_id,))

        self._partidas_producidas = self._base_de_datos.fetchall("""
                            DECLARE @OrderDocumentID INT = ?
                            SELECT * FROM [dbo].[zvwBuscarPartidasFinalizadasPedidoCayal-DocumentID](@OrderDocumentID)
                            """, (self._order_document_id,))

    def _colorear_partidas_editadas(self):
        filas = self._ventanas.obtener_filas_treeview('tvw_editado')
        if not filas:
            return
        for fila in filas:
            valores_fila = self._ventanas.procesar_fila_treeview('tvw_editado', fila)
            item_production_status_modified = int(valores_fila['ItemProductionStatusModified'])
            if item_production_status_modified == 1:
                self._ventanas.colorear_fila_seleccionada_treeview('tvw_editado', fila, 'info')

            if item_production_status_modified == 2:
                self._ventanas.colorear_fila_seleccionada_treeview('tvw_editado', fila, 'warning')

            if item_production_status_modified == 3:
                self._ventanas.colorear_fila_seleccionada_treeview('tvw_editado', fila, 'danger')

    def _procesar_partidas(self, partidas):

        def buscar_precio(product_id, customer_type_id):
            consulta = self._base_de_datos.buscar_precios_producto(product_id)
            if not consulta:
                return 0
            return [reg['SalePrice'] for reg in consulta if reg['CustomerTypeID'] == customer_type_id][0]

        business_entity_id = self._valores_fila['BusinessEntityID']
        customer_type_id = self._base_de_datos.fetchone('SELECT CustomerTypeID FROM orgCustomer WHERE BusinessEntityID = ?',
                                                        (business_entity_id,))

        nuevas_partidas = []
        for reg in partidas:

            quantity = self._utilerias.redondear_valor_cantidad_a_decimal(reg['Quantity'])
            product_id = reg['ProductID']
            sale_price = self._utilerias.redondear_valor_cantidad_a_decimal(
                buscar_precio(product_id, customer_type_id))
            tax_type_id = reg['TaxTypeID']

            valores_partida = self._utilerias.calcular_totales_partida(sale_price, quantity, tax_type_id)
            sale_price = self._utilerias.redondear_valor_cantidad_a_decimal(valores_partida['precio'])
            taxes = self._utilerias.redondear_valor_cantidad_a_decimal(valores_partida['impuestos'])
            sub_total = self._utilerias.redondear_valor_cantidad_a_decimal(valores_partida['subtotal'])
            total = self._utilerias.redondear_valor_cantidad_a_decimal(valores_partida['total'])

            nuevas_partidas.append(
                {
                    'N': reg['N'],
                    'Quantity': quantity,
                    'ProductKey': reg['ProductKey'],
                    'ProductName': reg['ProductName'],
                    'SalePrice': sale_price,
                    'Subtotal': sub_total,
                    'TaxTypeID': tax_type_id,
                    'ProductID': product_id,
                    'ClaveUnidad': reg['ClaveUnidad'],
                    'TotalTaxes': taxes,
                    'Total': total,
                    'DocumentItemID': reg['DocumentItemID'],
                    'ItemProductionStatusModified': reg['ItemProductionStatusModified'],
                    'Comments': reg['Comments']
                }
            )
        return nuevas_partidas

    def _buscar_responsables_produccion_pedido(self):
        return self._base_de_datos.fetchall("""
            SELECT ISNULL(UP.UserName ,'') UsuarioProduccion,
               ISNULL( UM.UserName,'') UsuarioMinisuper,
               ISNULL( UA.UserName,'') UsuarioAlmacen
            FROM docDocumentOrderCayal P LEFT OUTER JOIN
                engUser UP ON P.AssignedProductionUser = UP.UserID LEFT OUTER JOIN
                engUser UM ON P.StoreAssignedUser = UM.UserID LEFT OUTER JOIN
                engUser UA ON P.WarehouseAssignedUser = UA.UserID 
            WHERE OrderDocumentID = ?
        """,(self._order_document_id,))

    def _actualizar_comentario_editado(self):
        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_editado'):
            return

        filas = self._ventanas.obtener_filas_treeview('tvw_editado')
        if not filas:
            return

        for fila in filas:
            valores_fila = self._ventanas.procesar_fila_treeview('tvw_editado', fila)
            numero_fila = int(valores_fila['N'])
            texto_adicional = ''

            fila_respaldo = [reg for reg in self._partidas_editadas if reg['N'] == numero_fila]
            if fila_respaldo:
                info_fila = fila_respaldo[0]

                item_production_status_modified = int(valores_fila['ItemProductionStatusModified'])
                texto_adicional = ""
                if item_production_status_modified == 3:
                    user_name = self._base_de_datos.buscar_nombre_de_usuario(info_fila['DeletedBy'])
                    texto_adicional = f"({user_name} {info_fila['DeletedOn']})"
                if item_production_status_modified == 1:
                    user_name = self._base_de_datos.buscar_nombre_de_usuario(info_fila['CreatedBy'])
                    texto_adicional = f"({user_name} {info_fila['CreatedOn']})"

            comentario = valores_fila['Comments']
            comentario = f"{comentario} {texto_adicional}".strip()

            if comentario:
                self._ventanas.insertar_input_componente('txt_comentario_partida', comentario)

```


## modelo_captura.py

```py
import copy
import uuid
from datetime import datetime


class ModeloCaptura:
    def __init__(self, base_de_datos, ventanas, utilerias, cliente, parametros_contpaqi, documento):
        self.base_de_datos = base_de_datos
        self._ventanas = ventanas
        self.utilerias = utilerias
        self.cliente = cliente

        self.parametros_contpaqi = parametros_contpaqi
        self._module_id = self.parametros_contpaqi.id_modulo
        self._usuario_id = self.parametros_contpaqi.id_usuario
        self._user_name = self.parametros_contpaqi.nombre_usuario

        self.documento = documento

        self.consulta_productos = []
        self.consulta_productos_ofertados = []
        self.consulta_productos_ofertados_btn = []
        self.products_ids_ofertados = []

        self._customer_type_id = self.cliente.customer_type_id
        self.costo_servicio_a_domicilio = self.utilerias.redondear_valor_cantidad_a_decimal(20)
        self.servicio_a_domicilio_agregado = False
        self._agregando_partida = False
        self.partida_servicio_domicilio = {}

        self.MODIFICACIONES_PEDIDO = {
            'Agregado': 1,  # partida añadida al pedido
            'Editado': 2,  # partida eliminada del pedido
            'Eliminado': 3  # parida eliminada del pedido
        }

    def buscar_productos(self, termino_buscado, tipo_busqueda):

        if termino_buscado != '' and termino_buscado:

            if tipo_busqueda == 'Término':
                return self.base_de_datos.buscar_product_id_termino(termino_buscado)

            if tipo_busqueda == 'Línea':
                return self.base_de_datos.buscar_product_id_linea(termino_buscado)

            return False

    def mensajes_de_error(self, numero_mensaje, master=None):

        mensajes = {
            0: 'El valor de la cantidad no puede ser menor o igual a zero',
            1: 'El valor de la pieza no puede ser numero fracionario.',
            2: 'El monto no puede ser menor o igual a 1',
            3: 'El producto no tiene una equivalencia válida',
            4: 'No se puede calcular el monto de un producto cuya unidad sea pieza.',
            5: 'Solo puede elegir o monto o pieza en productos que tengan equivalencia.',
            6: 'El término de búsqueda no arrojó ningún resultado.',
            7: 'La el código de barras es inválido.',
            8: 'La consulta por código no devolvió ningún resultado.',
            9: 'La consulta a la base de datos del código proporcionado no devolvió resultados.',
            10: 'El producto no está disponible a la venta favor de validar.',
            11: 'El producto no tiene existencia favor de validar.',
            12: 'El cliente solo tiene una direccion agreguela desde editar cliente.',
            13: 'En el módulo de pedidos no se puede eliminar el servicio a domicilio manualmente.'
        }

        self._ventanas.mostrar_mensaje(mensajes[numero_mensaje], master)

    def obtener_product_ids_consulta(self, consulta_productos):
        product_ids = [producto['ProductID'] for producto in consulta_productos]

        if len(product_ids) == 1:
            return product_ids[0]

        return product_ids

    def buscar_info_productos_por_ids(self, productos_ids, no_en_venta=None):

        if no_en_venta:
            return self.base_de_datos.buscar_info_productos(productos_ids,
                                                            self._customer_type_id,
                                                            no_en_venta=True)
        return self.base_de_datos.buscar_info_productos(productos_ids, self._customer_type_id)

    def agregar_impuestos_productos(self, consulta_productos):
        consulta_procesada = []
        for producto in consulta_productos:
            producto_procesado = self.utilerias.calcular_precio_con_impuesto_producto(producto)
            consulta_procesada.append(producto_procesado)
        return consulta_procesada

    def buscar_informacion_producto(self, product_id):
        info_producto = [producto for producto in self.consulta_productos
                         if product_id == producto['ProductID']]

        return info_producto[0] if info_producto else {}

    def buscar_productos_ofertados_cliente(self):

        consulta_productos_ofertados = self.base_de_datos.buscar_productos_en_oferta(self._customer_type_id)
        productos_ids = [reg['ProductID'] for reg in consulta_productos_ofertados]
        consulta_productos = self.buscar_info_productos_por_ids(productos_ids)
        consulta_procesada = self.agregar_impuestos_productos(consulta_productos)
        self.consulta_productos_ofertados = consulta_productos_ofertados
        self.consulta_productos = consulta_procesada
        self.consulta_productos_ofertados_btn = consulta_procesada
        self.products_ids_ofertados = productos_ids

        return consulta_procesada

    def agregar_partida_tabla(self, partida, document_item_id, tipo_captura, unidad_cayal=0, monto_cayal=0):

        if not self._agregando_partida:
            try:
                self._agregando_partida = True

                cantidad = self.utilerias.redondear_valor_cantidad_a_decimal(partida['cantidad'])
                comments = partida.get('Comments', '')
                producto = partida.get('ProductName', '')
                partida['TipoCaptura'] = tipo_captura
                partida['DocumentItemID'] = document_item_id
                partida['CayalAmount'] = monto_cayal
                partida['uuid'] = uuid.uuid4()

                if self.documento.document_id > 0 and document_item_id == 0:
                    partida['ItemProductionStatusModified'] = 1
                    partida['CreatedBy'] = self._usuario_id

                    comentario = f'AGREGADO POR {self._user_name}'
                    self.agregar_partida_items_documento_extra(partida, 'agregar', comentario, partida['uuid'])

                # en caso que el modulo se use para capturar otro tipo de documentos que no sean pedidos el valor por defecto
                # debe ser 0 y para las subsecuentes modificaciones segun aplique
                # en funcion del diccionario modificaciones_pedido
                item_production_status_modified = partida.get('ItemProductionStatusModified', 0)
                partida['ItemProductionStatusModified'] = item_production_status_modified
                partida['CreatedBy'] = self._usuario_id

                cantidad_piezas = 0 if unidad_cayal == 0 else self.utilerias.redondear_valor_cantidad_a_decimal(partida['CayalPiece'])

                equivalencia = self.base_de_datos.fetchone(
                    'SELECT ISNULL(Equivalencia,0) Equivalencia FROM orgProduct WHERE ProductID = ?'
                    , partida.get('ProductID', 0))
                equivalencia = 0 if not equivalencia else equivalencia
                equivalencia_decimal = self.utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

                if equivalencia_decimal > 0 and unidad_cayal == 1:
                    cantidad_piezas = int((cantidad/equivalencia_decimal))

                partida['CayalPiece'] = cantidad_piezas

                partida_tabla = (cantidad,
                                 cantidad_piezas,
                                 partida['ProductKey'],
                                 producto,
                                 partida['Unit'],
                                 self.utilerias.redondear_valor_cantidad_a_decimal(partida['precio']),
                                 self.utilerias.redondear_valor_cantidad_a_decimal(partida['subtotal']),
                                 self.utilerias.redondear_valor_cantidad_a_decimal(partida['impuestos']),
                                 self.utilerias.redondear_valor_cantidad_a_decimal(partida['total']),
                                 partida['ProductID'],
                                 partida['DocumentItemID'],
                                 partida['TipoCaptura'],  # Tipo de captura 1 para manual y 0 para captura por pistola
                                 cantidad_piezas,  # Viene del control de captura manual
                                 partida['CayalAmount'],  # viene del control de tipo monto
                                 partida['uuid'],
                                 partida['ItemProductionStatusModified'],
                                 comments,
                                 partida['CreatedBy']
                                 )

                if int(partida['ProductID']) == 5606:
                    if self.servicio_a_domicilio_agregado:
                        return
                    else:
                        self.servicio_a_domicilio_agregado = True

                # agregar tipo de captura
                tabla_captura = self._ventanas.componentes_forma['tvw_productos']
                self._ventanas.insertar_fila_treeview(tabla_captura, partida_tabla, al_principio=True)
                self.agregar_partida_items_documento(partida)
                self.actualizar_totales_documento()

                # si aplica remueve el servicio a domicilio
                if self._module_id == 1687 and self.servicio_a_domicilio_agregado == True:
                    if self.documento.total - self.costo_servicio_a_domicilio >= 200:
                        self.remover_servicio_a_domicilio()

            finally:
                self._agregando_partida = False


    def agregar_partida_items_documento(self, partida):
        self.documento.items.append(partida)

    def actualizar_totales_documento(self):

        impuestos_acumulado = 0
        sub_total_acumulado = 0
        total_acumulado = 0

        for producto in self.documento.items:
            impuestos_acumulado += producto.get('impuestos',0)
            sub_total_acumulado += producto.get('subtotal', 0)
            total_acumulado += producto.get('total', 0)

        self.documento.total = total_acumulado
        total_documento_moneda = self.utilerias.convertir_decimal_a_moneda(total_acumulado)
        self._ventanas.insertar_input_componente('lbl_total', total_documento_moneda)

        self.documento.total_tax = impuestos_acumulado
        self.documento.subtotal = sub_total_acumulado

        self._ventanas.insertar_input_componente('lbl_articulos',
                                                 self._ventanas.numero_filas_treeview('tvw_productos'))

        if self.cliente.cayal_customer_type_id in (1,2) and self.cliente.credit_block == 0:
            debe = self.cliente.debt
            debe = self.utilerias.redondear_valor_cantidad_a_decimal(debe)

            debe += total_acumulado
            debe_moneda = self.utilerias.convertir_decimal_a_moneda(debe)
            self._ventanas.insertar_input_componente('lbl_debe', debe_moneda)

            disponible = self.cliente.remaining_credit
            disponible = self.utilerias.redondear_valor_cantidad_a_decimal(disponible)

            disponible = disponible - total_acumulado
            disponible_moneda = self.utilerias.convertir_decimal_a_moneda(disponible)
            self._ventanas.insertar_input_componente('lbl_restante', disponible_moneda)

    def remover_servicio_a_domicilio(self):
        self.servicio_a_domicilio_agregado = False
        self.remover_partida_items_documento(5606)
        self.remover_product_id_tabla(5606)
        self.actualizar_totales_documento()

    def agregar_servicio_a_domicilio(self):

        def insertar_partida_servicio_a_domicilio():
            delivery_cost_iva = self.base_de_datos.buscar_costo_servicio_domicilio(self.documento.address_detail_id)
            self.costo_servicio_a_domicilio = self.utilerias.redondear_valor_cantidad_a_decimal(delivery_cost_iva)
            delivery_cost = self.utilerias.calcular_monto_sin_iva(delivery_cost_iva)

            info_producto = self.buscar_info_productos_por_ids(5606, no_en_venta=True)

            if info_producto:
                info_producto = info_producto[0]

                info_producto['SalePrice'] = delivery_cost

                partida = self.utilerias.crear_partida(info_producto, cantidad=1)

                self.partida_servicio_domicilio = partida
                partida['Comments'] = ''
                self.agregar_partida_tabla(partida, document_item_id=0, tipo_captura=2, unidad_cayal=1, monto_cayal=0)

                self.servicio_a_domicilio_agregado = True

        # servicio a domicilio solo aplica para pedidos
        if self._module_id != 1687:
            return

        # servicio a domicilio no aplica para anexos o cambios 2 y 3 solo para pedidos 1
        if self._module_id == 1687:
            parametros_pedido = self.documento.order_parameters
            order_type_id = int(parametros_pedido.get('OrderTypeID', 1))

            # anexos o cambios 2 y 3
            if order_type_id in (2,3):
                return

        # no se debe agregar mas de una partida de servicio a domicilio
        existe_servicio_a_domicilio = [producto for producto in self.documento.items
                                       if int(producto['ProductID']) == 5606]

        if existe_servicio_a_domicilio:
            return

        # insertamos el servicio a domicilio
        insertar_partida_servicio_a_domicilio()

    def remover_product_id_tabla(self, product_id):
        filas = self._ventanas.obtener_filas_treeview('tvw_productos')

        for fila in filas:
            valores = self._ventanas.procesar_fila_treeview('tvw_productos', fila)
            product_id_tabla = int(valores['ProductID'])
            if product_id_tabla == product_id:
                self._ventanas.remover_fila_treeview('tvw_productos', fila)

    def remover_partida_items_documento(self, product_id):
        partidas = self.documento.items

        partidas_filtradas = [partida for partida in partidas if partida['ProductID'] != product_id]

        self.documento.items = partidas_filtradas

    def crear_texto_existencia_producto(self, info_producto):
        product_id = info_producto.get('ProductID',0)
        unidad = info_producto.get('Unit', 'PIEZA')
        consulta = self.base_de_datos.buscar_existencia_productos(product_id)
        existencia = 0.0
        if consulta:
           existencia = consulta[0].get('Existencia', 0.0)

        existencia = 0 if existencia < 0 else existencia

        unidad_producto = self.utilerias.abreviatura_unidad_producto(unidad)

        producto_especial = self.utilerias.equivalencias_productos_especiales(product_id)
        if producto_especial:
            unidad_producto = producto_especial[0]
            existencia = existencia / producto_especial[1]

        existencia_decimal = self.utilerias.redondear_valor_cantidad_a_decimal(existencia)

        return f'{existencia_decimal} {unidad_producto}'

    def crear_texto_cantidad_producto(self, cantidad, unidad, product_id):
        unidad_producto = self.utilerias.abreviatura_unidad_producto(unidad)

        producto_especial = self.utilerias.equivalencias_productos_especiales(product_id)
        if producto_especial:
            unidad_producto = producto_especial[0]

        return f'{cantidad:.2f} {unidad_producto}'

    def agregar_partida_items_documento_extra(self, partida, accion, comentario, uuid_tabla):
        # esta funcion procesa las partidas extra (agregadas, eliminadas, editadas) despues de la creación del docto
        # para inserción en tabla de respaldo, para procesamiento en panel de producción
        # considerando que las partidas editadas pueden ser editadas multiples veces
        # considerando que las partidas agregadas pueden ser agregadas, editadas y eliminadas
        # considerando que las partidas eliminadas pueden ser solo eliminadas

        partida_copia = copy.deepcopy(partida)
        partida_copia['uuid'] = uuid_tabla

        # agrega el comentario a la partida despues de agregarle la hora de procesamiento
        ahora = datetime.now().strftime('%Y-%m-%d a las %H:%M')
        comentario = f'{comentario} ({ahora})'
        partida_copia['Comments'] = comentario

        partidas_extra = self.documento.items_extra
        nuevas_partidas = [
                partida_extra for partida_extra in partidas_extra
                if str(partida_extra['uuid']) != str(uuid_tabla)
            ]

        # procesa la partida y agregala

        if accion == 'eliminar':
            partida_copia['ItemProductionStatusModified'] = 3

        if accion == 'editar':
            partida_copia['ItemProductionStatusModified'] = 2

        if accion == 'agregar':
            partida_copia['ItemProductionStatusModified'] = 1

        nuevas_partidas.append(partida_copia)

        self.documento.items_extra = nuevas_partidas



```


## editar_partida.py

```py
import copy
import tkinter as tk

from cayal.ventanas import Ventanas


class EditarPartida:
    def __init__(self, master, interfaz, modelo, utilerias, base_de_datos, valores_fila_tabla):
        self._master = master
        self._interfaz = interfaz

        self._ventanas_interfaz = self._interfaz.ventanas
        self._modelo = modelo
        self._parametros_contpaqi = self._modelo.parametros_contpaqi
        self._documento = self._modelo.documento
        self._utilerias = utilerias
        self._base_de_datos = base_de_datos
        self._valores_fila = valores_fila_tabla
        self._ventanas = Ventanas(self._master)

        self._user_id = self._parametros_contpaqi.id_usuario
        self._user_name = self._base_de_datos.buscar_nombre_de_usuario(self._user_id)
        self._module_id = self._parametros_contpaqi.id_modulo
        self._partida_items_documento = None
        self._info_producto = None
        self._procesando_producto = False

        self._cargar_frames()
        self._cargar_componentes()
        self._cargar_eventos()
        self._rellenar_componentes_forma()
        self._ventanas.configurar_ventana_ttkbootstrap('Editar partida')

        self._ventanas.enfocar_componente('btn_cancelar')

    def _rellenar_componentes_forma(self):
        product_id = int(self._valores_fila['ProductID'])
        quantity = self._valores_fila['Cantidad']
        valor_uuid = self._valores_fila['UUID']
        total = self._valores_fila['Total']

        partida_documento = self._obtener_info_partida_documento(valor_uuid)

        if partida_documento:
            piezas = partida_documento.get('CayalPiece',0)
            if piezas == 0:
                self._ventanas.insertar_input_componente('tbx_cantidad', quantity)
                self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'deseleccionado')


            if  piezas % 1 == 0 and piezas != 0:
                self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'seleccionado')
                self._ventanas.insertar_input_componente('tbx_cantidad', piezas)


        info_producto = self._modelo.buscar_info_productos_por_ids(product_id)[0]
        self._info_producto = self._utilerias.calcular_precio_con_impuesto_producto(info_producto)

        equivalencia = info_producto.get('Equivalencia', 0)
        equivalencia_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

        self._ventanas.insertar_input_componente('tbx_equivalencia', equivalencia_decimal)
        self._ventanas.bloquear_componente('tbx_equivalencia')

        self._ventanas.insertar_input_componente('lbl_monto', total)

        texto = self._modelo.crear_texto_existencia_producto(info_producto)
        self._ventanas.insertar_input_componente('lbl_existencia', texto)

        comentario = partida_documento.get('Comments','')
        self._ventanas.insertar_input_componente('txt_comentario', comentario)

    def _obtener_info_partida_documento(self, uuid_partida):

        partidas_documento = self._documento.items
        self._partida_items_documento = [partida for partida in partidas_documento
                                         if str(partida['uuid']) == str(uuid_partida)][0]

        return self._partida_items_documento

    def _cargar_frames(self):
        frames = {

            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_partida': ('frame_principal', 'Partida:',
                              {'row': 1, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                               'sticky': tk.NSEW}),

            'frame_cantidades': ('frame_partida', None,
                                 {'row': 0, 'column': 0, 'rowspan': 2, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                  'sticky': tk.W}),

            'frame_controles': ('frame_partida', None,
                                {'row': 2, 'column': 1, 'rowspan': 2, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                 'sticky': tk.W}),

            'frame_txt_comentario': ('frame_partida', 'Especificación:[Ctrl+M]',
                                     {'row': 6, 'column': 0, 'columnspan': 5, 'pady': 2, 'padx': 2,
                                      'sticky': tk.NSEW}),

            'frame_totales': ('frame_partida', None,
                              {'row': 1, 'column': 3, 'rowspan': 4, 'columnspan': 2, 'pady': 2, 'padx': 2,
                               'sticky': tk.NE}),

            'frame_botones': ('frame_partida', None,
                              {'row': 10, 'column': 1, 'padx': 0, 'pady': 5, 'sticky': tk.W}),
        }

        self._ventanas.crear_frames(frames)

    def _cargar_componentes(self):
        componentes = {
            'tbx_cantidad': ('frame_cantidades', 10, 'Cantidad:', None),
            'tbx_equivalencia': ('frame_cantidades',
                                 {'row': 0, 'column': 3, 'pady': 5, 'padx': 5, 'sticky': tk.W},
                                 'Equivalencia:', None),

            'lbl_monto_texto': ('frame_totales',
                                {'width': 10, 'text': 'TOTAL:', 'style': 'inverse-danger', 'anchor': 'e',
                                 'font': ('Consolas', 16, 'bold')},
                                {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                None),

            'lbl_monto': ('frame_totales',
                          {'width': 10, 'text': '$0.00', 'style': 'inverse-danger', 'anchor': 'e',
                           'font': ('Consolas', 16, 'bold')},
                          {'row': 0, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                          None),

            'lbl_cantidad_texto': ('frame_totales',
                                   {'width': 10, 'text': 'CANTIDAD:', 'style': 'inverse-danger', 'anchor': 'e',
                                    'font': ('Consolas', 16, 'bold')},
                                   {'row': 1, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                   None),

            'lbl_cantidad': ('frame_totales',
                             {'width': 10, 'text': '0.00', 'style': 'inverse-danger', 'anchor': 'e',
                              'font': ('Consolas', 16, 'bold')},
                             {'row': 1, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                             None),

            'lbl_existencia_texto': ('frame_totales',
                                     {'width': 10, 'text': 'EXISTENCIA:', 'style': 'inverse-danger', 'anchor': 'e',
                                      'font': ('Consolas', 15, 'bold')},
                                     {'row': 2, 'column': 0, 'padx': 0, 'sticky': tk.NSEW},
                                     None),

            'lbl_existencia': ('frame_totales',
                               {'width': 10, 'text': '0.00', 'style': 'inverse-danger', 'anchor': 'e',
                                'font': ('Consolas', 16, 'bold')},
                               {'row': 2, 'column': 1, 'padx': 0, 'sticky': tk.NSEW},
                               None),

            'chk_pieza': ('frame_controles',
                          {'row': 0, 'column': 3, 'pady': 5, 'padx': 5, 'sticky': tk.W},
                          'Pieza', '[F1]'),

            'chk_monto': ('frame_controles',
                          {'row': 0, 'column': 5, 'pady': 5, 'padx': 5, 'sticky': tk.W},
                          'Monto', '[F4]'),

            'txt_comentario': ('frame_txt_comentario', None, ' ', None),
            'btn_actualizar': ('frame_botones', 'success', 'Actualizar', '[F8]'),
            'btn_cancelar': ('frame_botones', 'danger', 'Cancelar', '[Esc]'),

        }

        self._ventanas.crear_componentes(componentes)
        self._ventanas.ajustar_componente_en_frame('tbx_equivalencia', 'frame_cantidades')
        self._ventanas.ajustar_componente_en_frame('txt_comentario', 'frame_txt_comentario')
        self._ventanas.ajustar_ancho_componente('tbx_equivalencia', 6)
        self._ventanas.ajustar_ancho_componente('txt_comentario', 60)

    def _cargar_eventos(self):
        eventos = {
            'btn_cancelar': self._master.destroy,
            'btn_actualizar': self._actualizar_partida,
            'tbx_cantidad': self._procesar_producto,
            'chk_monto': lambda *args: self._procesar_producto(),
            'chk_pieza': lambda *args: self._procesar_producto(),
        }
        self._ventanas.cargar_eventos(eventos)

    def _determinar_tipo_calculo_partida(self, info_producto):

        # devuelve el tipo de calculo que realizara la funcion calcular_valores_partida
        # dado que la configuracion de los productos se toma en automatico o segun lo elejido por el usuario
        # calculo por unidad, calculo por equivalencia, calculo por monto
        valores_controles = self._obtener_valores_controles()

        clave_unidad = info_producto.get('ClaveUnidad', 'H87')
        valor_chk_monto = valores_controles['valor_chk_monto']
        valor_chk_pieza = valores_controles['valor_chk_pieza']
        cantidad = valores_controles['cantidad']
        equivalencia = valores_controles['equivalencia']

        if clave_unidad != 'KGM':  # todos las unidades que no sean kilo, es decir paquetes, piezas, litros, etc

            if not self._utilerias.es_numero_entero(cantidad):
                self._ventanas.insertar_input_componente('tbx_cantidad', 1)

            if valor_chk_pieza == 0:
                self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'seleccionado')

            if valor_chk_monto == 1:
                self._ventanas.cambiar_estado_checkbutton('chk_monto', 'deseleccionado')
                self._modelo.mensajes_de_error(4)

            if equivalencia == 0:
                return 'Unidad'

            if equivalencia != 0:
                return 'Equivalencia'

        if clave_unidad == 'KGM':

            if valor_chk_pieza == 1 and equivalencia == 0:
                self._modelo.mensajes_de_error(3)
                self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'deseleccionado')
                return 'Error'

            if valor_chk_monto == 1 and cantidad == 0:
                self._modelo.mensajes_de_error(0)
                self._ventanas.cambiar_estado_checkbutton('chk_monto', 'deseleccionado')
                return 'Error'

            if equivalencia != 0:
                if valor_chk_monto == 1 and valor_chk_pieza == 1:
                    self._ventanas.cambiar_estado_checkbutton('chk_monto', 'deseleccionado')
                    self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'deseleccionado')
                    return 'Unidad'

            if valor_chk_monto == 0 and valor_chk_pieza == 0:
                return 'Unidad'

            if valor_chk_pieza == 1:
                return 'Equivalencia'

            if valor_chk_monto == 1 and cantidad <= 1:
                self._modelo.mensajes_de_error(2)
                return 'Error'

            if valor_chk_monto == 1:
                return 'Monto'
        return 'Error'

    def _obtener_valores_controles(self):

        equivalencia = self._ventanas.obtener_input_componente('tbx_equivalencia')
        equivalencia_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

        return {
            'valor_chk_monto': self._ventanas.obtener_input_componente('chk_monto'),
            'valor_chk_pieza': self._ventanas.obtener_input_componente('chk_pieza'),
            'cantidad': self._obtener_cantidad_partida(),
            'equivalencia': equivalencia_decimal
        }

    def _obtener_cantidad_partida(self):
        cantidad = self._ventanas.obtener_input_componente('tbx_cantidad')

        if not cantidad or not self._utilerias.es_cantidad(cantidad):
            return self._utilerias.redondear_valor_cantidad_a_decimal(0)

        cantidad_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(cantidad)

        return self._utilerias.redondear_valor_cantidad_a_decimal(1) if cantidad_decimal <= 0 else cantidad_decimal

    def _calcular_valores_partida(self, info_producto):

        def calcular_cantidad_real(tipo_calculo, equivalencia, cantidad):
            if tipo_calculo == 'Equivalencia':
                return cantidad * equivalencia

            if tipo_calculo in ('Unidad', 'Monto'):
                return cantidad

        tipo_calculo = self._determinar_tipo_calculo_partida(info_producto)

        total = 0
        cantidad_real_decimal = 0

        if tipo_calculo != 'Error':
            valores_controles = self._obtener_valores_controles()

            precio_con_impuestos = info_producto.get('SalePriceWithTaxes', 0.0)

            cantidad = valores_controles['cantidad']
            cantidad_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(cantidad)

            equivalencia = valores_controles['equivalencia']
            equivalencia_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

            cantidad_real_decimal = calcular_cantidad_real(tipo_calculo, equivalencia_decimal, cantidad_decimal)

            if tipo_calculo == 'Equivalencia':
                if not self._utilerias.es_numero_entero(cantidad_decimal):
                    cantidad_decimal = self._utilerias.redondear_numero_a_entero(cantidad_decimal)
                    self._ventanas.insertar_input_componente('tbx_cantidad', cantidad_decimal)

                total = cantidad_real_decimal * precio_con_impuestos

            if tipo_calculo == 'Unidad':
                total = cantidad_real_decimal * precio_con_impuestos

            if tipo_calculo == 'Monto':
                total = cantidad
                cantidad = total / precio_con_impuestos
                cantidad_real_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(cantidad)

        self._actualizar_lbl_total_moneda(total)
        texto = self._modelo.crear_texto_existencia_producto(info_producto)

        self._ventanas.insertar_input_componente('lbl_existencia', texto)
        self._ventanas.insertar_input_componente('lbl_cantidad', cantidad_real_decimal)

        return {'cantidad': cantidad_real_decimal, 'total': total}

    def _actualizar_lbl_total_moneda(self, total_decimal):
        total_moneda = self._utilerias.convertir_decimal_a_moneda(total_decimal)
        self._ventanas.insertar_input_componente('lbl_monto', total_moneda)

    def _insertar_equivalencia(self, equivalencia):

        equivalencia = str(equivalencia)
        equivalencia_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

        self._ventanas.desbloquear_componente('tbx_equivalencia')
        self._ventanas.insertar_input_componente('tbx_equivalencia', equivalencia_decimal)
        self._ventanas.bloquear_componente('tbx_equivalencia')

        return equivalencia_decimal

    def _configurar_forma_segun_producto(self, info_producto):

        clave_unidad = info_producto.get('ClaveUnidad', 'H87')

        equivalencia = info_producto.get('Equivalencia', 0.0)
        equivalencia_decimal = self._insertar_equivalencia(equivalencia)

        if equivalencia_decimal == 0:

            if clave_unidad == 'KGM':
                self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'deseleccionado')

            if clave_unidad != 'KGM':
                self._ventanas.cambiar_estado_checkbutton('chk_monto', 'deseleccionado')
                self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'seleccionado')
        else:
            self._ventanas.cambiar_estado_checkbutton('chk_monto', 'deseleccionado')
            self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'seleccionado')

    def _actualizar_partida(self):
        valores_partida = self._procesar_producto()

        if valores_partida:
            document_item_id = int(self._valores_fila['DocumentItemID'])
            cantidad_original = self._utilerias.redondear_valor_cantidad_a_decimal(self._valores_fila['Cantidad'])
            cantidad_nueva = valores_partida['cantidad']

            comentario = f'EDITADO POR {self._user_name}: Cant {cantidad_original} --> Cant {cantidad_nueva}'

            uuid_partida = str(self._partida_items_documento['uuid'])

            # Crear partida original antes de cualquier modificación y hacer una copia profunda
            partida_original = self._utilerias.crear_partida(self._info_producto, cantidad_original)

            for partida in self._documento.items:
                uuid_partida_items = str(partida['uuid'])
                if uuid_partida == uuid_partida_items:
                    # Crear partida actualizada solo si encontramos la partida correspondiente
                    partida_actualizada = self._utilerias.crear_partida(self._info_producto, cantidad_nueva)

                    valor_pieza = self._ventanas.obtener_input_componente('chk_pieza')
                    piezas = partida_actualizada['CayalPiece'] if valor_pieza == 1 else 0

                    # Actualizar valores de la partida en el documento
                    partida['ItemProductionStatusModified'] = 2 if document_item_id > 0 else 0
                    partida['cantidad'] = cantidad_nueva
                    partida['subtotal'] = partida_actualizada['subtotal']
                    partida['total'] = partida_actualizada['total']
                    partida['CayalPiece'] = piezas #self._ventanas.obtener_input_componente('chk_pieza')
                    partida['monto_cayal'] = self._ventanas.obtener_input_componente('chk_monto')
                    partida['Comments'] = self._ventanas.obtener_input_componente('txt_comentario')
                    partida['CreatedBy'] = self._user_id
                    partida['DocumentItemID'] = document_item_id

                    # Actualizar la tabla UI con los nuevos valores
                    filas = self._ventanas_interfaz.obtener_filas_treeview('tvw_productos')
                    for fila in filas:
                        valores_fila = self._ventanas_interfaz.procesar_fila_treeview('tvw_productos', fila)
                        uuid_tabla = str(valores_fila['UUID'])
                        if uuid_tabla == uuid_partida:

                            valores_fila['Cantidad'] = cantidad_nueva
                            valores_fila['Importe'] = "{:.2f}".format(partida_actualizada['subtotal'])
                            valores_fila['Impuestos'] = "{:.2f}".format(partida_actualizada['impuestos'])
                            valores_fila['Total'] = "{:.2f}".format(partida_actualizada['total'])
                            valores_fila['Piezas'] = piezas
                            self._ventanas_interfaz.actualizar_fila_treeview_diccionario('tvw_productos', fila,
                                                                                         valores_fila)

            # Redondear valores de cantidad
            cantidad_original = self._utilerias.redondear_valor_cantidad_a_decimal(cantidad_original)
            cantidad_nueva = self._utilerias.redondear_valor_cantidad_a_decimal(cantidad_nueva)

            if cantidad_original == cantidad_nueva:
                comentario  = self._ventanas.obtener_input_componente('txt_comentario')
                comentario = f'EDITADO POR {self._user_name}: {comentario}'
            else:
                # actualiza los totales de la nota para posteriores modificaciones
                self._modelo.actualizar_totales_documento()

            # respalda la partida extra para tratamiento despues del cierre del documento
            self._modelo.agregar_partida_items_documento_extra(partida_original, 'editar', comentario, uuid_partida)

        # Solo aplica para el módulo de pedidos
        if self._module_id == 1687:
            total_documento = self._documento.total

            if self._modelo.servicio_a_domicilio_agregado:
                total_sin_servicio = total_documento - self._modelo.costo_servicio_a_domicilio

                if total_sin_servicio >= 200:
                    self._modelo.remover_servicio_a_domicilio()
            else:
                if total_documento < 200:
                    self._modelo.agregar_servicio_a_domicilio()

        self._master.destroy()

    def _procesar_producto(self, event=None):

        if self._procesando_producto:
            return

        info_producto = self._info_producto

        try:
            if info_producto:
                self._procesando_producto = True

                cantidad = self._obtener_cantidad_partida()

                chk_pieza = self._ventanas.obtener_input_componente('chk_pieza')
                if chk_pieza == 1 and cantidad % 1 != 0:
                    self._ventanas.mostrar_mensaje(mensaje='La cantidad de piezas deben ser valores no fraccionarios.',
                                                   master=self._master)
                    return False

                self._ventanas.insertar_input_componente('tbx_cantidad', cantidad)

                return self._calcular_valores_partida(info_producto)
        finally:
            self._procesando_producto = False

```
