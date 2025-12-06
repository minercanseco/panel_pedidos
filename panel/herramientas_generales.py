import tkinter as tk

from cayal.login import Login
from cayal.ventanas import Ventanas
from cayal.cliente import Cliente

from herramientas.cliente.buscar_clientes import BuscarClientes
from herramientas.cliente.cliente_nuevo import ClienteNuevo
from herramientas.cliente.notebook_cliente import NoteBookCliente
from herramientas.herramientas_compartidas.cancelar_pedido import CancelarPedido
from herramientas.herramientas_compartidas.historial_pedido import HistorialPedido
from herramientas.herramientas_compartidas.horario_acumulado import HorarioslAcumulados
from herramientas.herramientas_panel.editar_nombre_pedido import EditarNombrePedido
from herramientas.cobrar_cartera.buscar_generales_cliente_cartera import BuscarGeneralesCliente


class HerramientasGenerales:
    def __init__(self, master, modelo, interfaz):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._modelo = modelo
        self._interfaz = interfaz

        self._base_de_datos = self._modelo.base_de_datos
        self._parametros = self._modelo.parametros
        self._utilerias = self._modelo.utilerias

        self._crear_frames()
        self._crear_barra_herramientas()

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'pady': 5, 'padx': 5, 'sticky': tk.NSEW}),

            'frame_componentes': ('frame_principal', None,
                                  {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                   'sticky': tk.NSEW})
        }
        self._ventanas.crear_frames(frames)

    def _crear_barra_herramientas(self):
        self.barra_herramientas_pedido = [

            {'nombre_icono': 'Partner32.ico', 'etiqueta': 'Clientes', 'nombre': 'buscar_cliente',
             'hotkey': None, 'comando': self._buscar_clientes},

            {'nombre_icono': 'Customer32.ico', 'etiqueta': 'Nuevo', 'nombre': 'nuevo_cliente',
             'hotkey': None, 'comando': self._capturar_nuevo_cliente},

            {'nombre_icono': 'DocumentEdit32.ico', 'etiqueta': 'E.Cliente', 'nombre': 'editar_cliente',
             'hotkey': None, 'comando': self._editar_info_cliente},

            {'nombre_icono': 'AssignSalesRep32.ico', 'etiqueta': 'E.Nombre', 'nombre': 'editar_nombre',
             'hotkey': None, 'comando': self._editar_nombre_pedido},

            {'nombre_icono': 'History21.ico', 'etiqueta': 'Historial', 'nombre': 'historial_pedido',
             'hotkey': None, 'comando': self._historial_pedido},

            {'nombre_icono': 'Cancelled32.ico', 'etiqueta': 'Cancelar', 'nombre': 'cancelar_pedido',
             'hotkey': None, 'comando': self._cancelar_pedido},

            {'nombre_icono': 'Organizer32.ico', 'etiqueta': 'A.Horarios', 'nombre': 'acumular_horarios',
             'hotkey': None, 'comando': self._acumular_horarios},

            {'nombre_icono': 'Printer21.ico', 'etiqueta': 'Imprimir', 'nombre': 'imprimir_pedido',
             'hotkey': None, 'comando': self._hola},

            {'nombre_icono': 'Payments32.ico', 'etiqueta': 'C.Cartera.', 'nombre': 'cobrar_cartera',
             'hotkey': None, 'comando': self._cobrar_cartera},

            {'nombre_icono': 'OtrosIngresos32.ico', 'etiqueta': 'C.Transferencia', 'nombre': 'confirmar_transferencia',
             'hotkey': None, 'comando': self._confirmar_transferencia},

            {'nombre_icono': 'SwitchUser32.ico', 'etiqueta': 'C.Usuario', 'nombre': 'cambiar_usuario',
             'hotkey': None, 'comando': self._cambiar_usuario},

        ]

        self.elementos_barra_herramientas = self._ventanas.crear_barra_herramientas(self.barra_herramientas_pedido,
                                                                                   'frame_componentes')
        self.iconos_barra_herramientas = self.elementos_barra_herramientas[0]
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]

    def _obtener_valores_fila_pedido_seleccionado(self, valor = None):
        if not self._interfaz.ventanas.validar_seleccion_una_fila_table_view('tbv_pedidos'):
            return

        valores_fila = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)[0]
        if not valor:
            return

        return valores_fila[valor]

    def _hola(self):
        print('hola')

    def _capturar_nuevo_cliente(self):
        ventana = self._ventanas.crear_popup_ttkbootstrap()
        self._parametros.id_principal = 0
        ClienteNuevo(ventana,
                            self._parametros,
                            self._base_de_datos,
                            self._utilerias,
                            )
        ventana.wait_window()

    def _editar_info_cliente(self):

        business_entity_id = self._obtener_valores_fila_pedido_seleccionado(valor='BusinessEntityID')
        if not business_entity_id:
            return

        self._parametros.id_principal = business_entity_id
        try:
            ventana = self._ventanas.crear_popup_ttkbootstrap()
            cliente = Cliente()
            NoteBookCliente(
                            ventana,
                            self._base_de_datos,
                            self._parametros,
                            self._utilerias,
                            cliente
                            )
            ventana.wait_window()
        finally:
            self._parametros.id_principal = 0

    def _editar_nombre_pedido(self):
        order_document_id = self._obtener_valores_fila_pedido_seleccionado(valor='OrderDocumentID')
        if not order_document_id:
            return
        try:
            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(titulo='Editar nombre pedido.')
            self._parametros.id_principal = order_document_id
            instancia = EditarNombrePedido(ventana, self._parametros, self._base_de_datos)
            ventana.wait_window()
        finally:
            self._parametros.id_principal = 0

    def _historial_pedido(self):
        order_document_id = self._obtener_valores_fila_pedido_seleccionado(valor='OrderDocumentID')
        if not order_document_id:
            return
        try:
            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(titulo='Historial pedido')
            self._parametros.id_principal = order_document_id
            instancia = HistorialPedido(ventana, self._parametros, self._base_de_datos)
            ventana.wait_window()
        finally:
            self._parametros.id_principal = 0

    def _cancelar_pedido(self):

        if self._modelo.user_group_id not in (1, 5, 6, 7, 15, 20):
            self._interfaz.ventanas.mostrar_mensaje('No está autorizado para cancelar pedidos.')
            return

        order_document_id = self._obtener_valores_fila_pedido_seleccionado(valor='OrderDocumentID')
        if not order_document_id:
            return
        try:
            self._parametros.id_principal = order_document_id
            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
            instancia = CancelarPedido(ventana, self._parametros, self._base_de_datos)
            ventana.wait_window()
        finally:
            self._parametros.id_principal = 0

    def _buscar_clientes(self):
        ventana = self._ventanas.crear_popup_ttkbootstrap()
        instancia = BuscarClientes(ventana, self._base_de_datos, self._parametros, self._utilerias)
        ventana.wait_window()

    def _acumular_horarios(self):
        ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(self._interfaz.master, 'Acumulados horarios')
        instancia = HorarioslAcumulados(ventana, self._base_de_datos, self._utilerias)
        ventana.wait_window()

    def _cobrar_cartera(self):
        ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(self._interfaz.master, 'Acumulados horarios')
        instancia = BuscarGeneralesCliente(ventana, self._parametros)
        ventana.wait_window()

    def _confirmar_transferencia(self):

        fila = self._obtener_valores_fila_pedido_seleccionado()
        if not fila:
            return

        order_document_id = fila['OrderDocumentID']
        payment_confirmend_id = fila['PaymentConfirmedID']

        if payment_confirmend_id == 1:
            self._ventanas.mostrar_mensaje('El pedido seleccionado no es transferencia.')
            return

        if payment_confirmend_id == 3:
            self._ventanas.mostrar_mensaje('La transferencia ha sido confirmada con anterioridad.')
            return

        self._modelo.confirmar_transferencia(self._modelo.user_id, order_document_id)
        comentario = f"Transferencia confirmada por {self._modelo.user_name}"
        self._modelo.afectar_bitacora(order_document_id, self._modelo.user_id, comentario)

    def _cambiar_usuario(self):

        def rellenar_operador():
            operador_panel = self._modelo.user_name
            texto = f'PANEL: pedidos OPERADOR: {operador_panel}'
            self._interfaz.ventanas.actualizar_etiqueta_externa_tabla_view('tbv_pedidos', texto)
            self._modelo.user_id = self._parametros.id_usuario

        def si_acceso_exitoso(parametros=None, master=None):
            self._parametros = parametros
            rellenar_operador()

        ventana = self._ventanas.crear_popup_ttkbootstrap()
        instancia = Login(ventana, self._parametros, si_acceso_exitoso)
        ventana.wait_window()


