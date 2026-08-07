import copy
import tkinter as tk

from cayal.documento import Documento
from cayal.ventanas import Ventanas

from herramientas.capturar_documento.buscar_generales_cliente import BuscarGeneralesCliente
from herramientas.capturar_documento.llamar_instancia_captura_pedido import LlamarInstanciaCapturaPedido
from herramientas.herramientas_panel.editar_caracteristicas_pedido import EditarCaracteristicasPedido
from herramientas.herramientas_panel.editar_pedido import EditarPedido
from herramientas.herramientas_panel.ticket_pedido_cliente import TicketPedidoCliente
from herramientas.verificador_precios.controlador_verificador import ControladorVerificador
from herramientas.verificador_precios.interfaz_verificador import InterfazVerificador


class HerramientasCaptura:
    def __init__(self, master, modelo, interfaz, callbacks_autorefresco):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._modelo = modelo
        self._interfaz = interfaz
        self._callbacks_autorefresco = callbacks_autorefresco or {}

        self._base_de_datos = self._modelo.base_de_datos
        self._parametros = self._modelo.parametros
        self._utilerias = self._modelo.utilerias
        self._capturas_activas = 0

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


            {'nombre_icono': 'HeaderFooter32.ico', 'etiqueta': 'Nuevo', 'nombre': 'capturar_nuevo',
             'hotkey': None, 'comando': self._capturar_nuevo_pedido},

            {'nombre_icono': 'EditBusinessEntity32.ico', 'etiqueta': 'E.Caracteristicas', 'nombre': 'editar_caracteristicas',
             'hotkey': '', 'comando': self._editar_caracteristicas_pedido},

            {'nombre_icono': 'DocumentGenerator32.ico', 'etiqueta': 'Ticket', 'nombre': 'crear_ticket',
             'hotkey': None, 'comando': self._crear_ticket_pedido_cliente},

            {'nombre_icono': 'Manufacture32.ico', 'etiqueta': 'M.Producir', 'nombre': 'mandar_producir',
             'hotkey': None, 'comando': self._mandar_a_producir},

            {'nombre_icono': 'lista-de-verificacion.ico', 'etiqueta': 'Editar', 'nombre': 'editar',
             'hotkey': None, 'comando': self._editar_pedido},

            {'nombre_icono': 'Barcode.ico', 'etiqueta': 'Verificador', 'nombre': 'verificador',
             'hotkey': None, 'comando': self._verificador_precios},

        ]

        self.elementos_barra_herramientas = self._ventanas.crear_barra_herramientas(self.barra_herramientas_pedido,
                                                                                   'frame_componentes')
        self.iconos_barra_herramientas = self.elementos_barra_herramientas[0]
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]

    def _pausar_autorefresco(self):
        fn = self._callbacks_autorefresco.get("pausar")
        if fn:
            fn()

    def _reanudar_autorefresco(self):
        fn = self._callbacks_autorefresco.get("reanudar")
        if fn:
            fn()

    def _iniciar_captura(self):
        """Pausa una sola vez aunque existan varias capturas abiertas."""
        if self._capturas_activas == 0:
            self._pausar_autorefresco()
        self._capturas_activas += 1

    def _finalizar_captura(self):
        """Reanuda el refresco cuando cierre la última captura."""
        self._capturas_activas = max(0, self._capturas_activas - 1)
        if self._capturas_activas == 0:
            self._reanudar_autorefresco()

    def _filtro_post_captura(self):
        fn = self._callbacks_autorefresco.get("postcaptura")
        if fn:
            fn()

    def _rellenar_tabla(self):
        fn = self._callbacks_autorefresco.get("rellenar_tabla")
        if fn:
            fn()

    def _crear_parametros_captura(self, document_id=0):
        """Aísla los parámetros mutables de cada ventana de captura."""
        parametros = copy.copy(self._parametros)
        parametros.id_principal = document_id
        return parametros

    @staticmethod
    def _hacer_ventana_no_modal(ventana):
        """Permite interactuar con el panel y abrir otras capturas."""
        try:
            if ventana.grab_current() == ventana:
                ventana.grab_release()
        except tk.TclError:
            pass

    def _obtener_valores_fila_pedido_seleccionado(self, valor = None):
        if not self._interfaz.ventanas.validar_seleccion_una_fila_table_view('tbv_pedidos'):
            return

        valores_fila = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)[0]
        if not valor:
            return valores_fila

        return valores_fila[valor]

    def _obtener_valores_filas_pedidos_seleccionados(self):
        # si imprimir en automatico esta desactivado la seleccion de filas solo aplica a la seleccion
        filas = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)

        if not filas:
            self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar por lo menos un pedido.')
            return

        return filas

    def _verificador_precios(self):
        ventana = self._ventanas.crear_popup_ttkbootstrap(self._master)
        vista = InterfazVerificador(ventana)
        controlador = ControladorVerificador(vista, self._parametros)

    def _capturar_nuevo_pedido(self):
        self._iniciar_captura()
        try:
            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(
                titulo='Pedido',
                nombre_icono='icono_logo.ico',
            )
            BuscarGeneralesCliente(
                ventana,
                self._crear_parametros_captura(),
            )

            # BuscarGeneralesCliente configura la ventana con grab_set().
            # Se libera después de construirlo para mantener abierto el panel.
            self._hacer_ventana_no_modal(ventana)
            ventana.wait_window()

            self._rellenar_tabla()
            self._filtro_post_captura()
        finally:
            self._finalizar_captura()

    def _editar_pedido(self):

        fila = self._obtener_valores_fila_pedido_seleccionado()
        if not fila:
            self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar un pedido.')
            return

        status_id = fila['TypeStatusID']
        order_document_id = fila['OrderDocumentID']
        business_entity_id = fila['BusinessEntityID']

        #  cancelado, modificando, surtido parcialmente minisuper, produccion, almacen, entregado, cobrado o cartera
        if status_id in (10, 12, 16, 17, 18, 13, 14, 15):
            self._interfaz.ventanas.mostrar_mensaje('El pedido no tiene un estatus válido para ser editado.')
            return

        captura_pedido = status_id < 3
        if captura_pedido:
            self._iniciar_captura()

        try:
            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(titulo='Pedido', nombre_icono='icono_logo.ico')
            self._hacer_ventana_no_modal(ventana)
            if status_id < 3:
                documento = Documento()
                documento.document_id = order_document_id
                documento.business_entity_id = business_entity_id

                LlamarInstanciaCapturaPedido(
                    ventana,
                    self._crear_parametros_captura(order_document_id),
                    documento=documento,
                )

            elif status_id >= 3:
                EditarPedido(ventana, self._base_de_datos, self._utilerias, self._parametros, fila)
                ventana.wait_window()

            else:
                self._interfaz.ventanas.mostrar_mensaje(
                    'No hay acción válida para un pedido en este estado.'
                )

        finally:
            self._modelo.actualizar_totales_pedido(order_document_id)
            self._rellenar_tabla()
            if status_id == 1:
                self._filtro_post_captura()
            if captura_pedido:
                self._finalizar_captura()

    def _editar_caracteristicas_pedido(self):
        status_id = None
        se_abrio_popup = False
        try:
            fila = self._obtener_valores_fila_pedido_seleccionado()
            if not fila:
                return

            status_id = fila['TypeStatusID']

            if status_id == 10:
                self._interfaz.ventanas.mostrar_mensaje('NO se pueden editar pedidos cancelados.')
                return
            elif status_id >= 4:
                self._interfaz.ventanas.mostrar_mensaje(
                    'Sólo se pueden afectar las caracteristicas de un pedido hasta el status Por timbrar.'
                )
                return

            order_document_id = fila['OrderDocumentID']
            self._parametros.id_principal = order_document_id

            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
            se_abrio_popup = True
            instancia = EditarCaracteristicasPedido(ventana, self._parametros, self._base_de_datos, self._utilerias)
            ventana.wait_window()

        finally:
            self._parametros.id_principal = 0
            if se_abrio_popup and status_id == 1:
                self._filtro_post_captura()

    def _crear_ticket_pedido_cliente(self):
        status_id = None  # <- para que exista siempre en finally

        order_document_id = self._obtener_valores_fila_pedido_seleccionado(valor='OrderDocumentID')
        if not order_document_id:
            return

        valores = self._modelo.obtener_status_entrega_pedido(order_document_id)
        if not valores:
            return

        status_id = valores.get('status_id')
        status_entrega = valores.get('status_entrega')
        fecha_entrega = valores.get('fecha_entrega')

        if status_entrega == 0:
            self._interfaz.ventanas.mostrar_mensaje(
                'Debe definir la forma de pago del cliente antes de generar el ticket.'
            )
            return

        try:
            fecha_entrega = str(fecha_entrega)[0:10]
            fecha_entrega = self._utilerias.convertir_fecha_str_a_datetime(str(fecha_entrega))

            if fecha_entrega > self._modelo.hoy:
                respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                    'EL pedido es para una fecha de entrega posterior, ¿Desea actualizar los precios antes de generar el ticket?'
                )
                if respuesta:
                    self._base_de_datos.actualizar_precios_pedido(order_document_id)

            self._parametros.id_principal = order_document_id
            instancia = TicketPedidoCliente(self._base_de_datos, self._utilerias, self._parametros)

            self._interfaz.ventanas.mostrar_mensaje(
                master=self._interfaz.master,
                mensaje='Comprobante generado.',
                tipo='info'
            )
            self._interfaz.master.iconify()

        finally:
            self._parametros.id_principal = 0
            self._rellenar_tabla()

            if status_id == 1:
                self._filtro_post_captura()

    def _mandar_a_producir(self):

        filas = self._obtener_valores_filas_pedidos_seleccionados()
        if not filas:
            return
        try:
            for fila in filas:
                order_document_id = fila['OrderDocumentID']

                valores = self._modelo.obtener_status_entrega_pedido(order_document_id)
                status = valores['status_id']
                entrega = valores['fecha_entrega']
                folio = valores['doc_folio']

                if not entrega or entrega == 'None':
                    self._interfaz.ventanas.mostrar_mensaje(
                        f'Debe usar la herramienta de editar características para el pedido {folio}.')
                    continue

                if status == 1:
                    self._modelo.mandar_pedido_a_producir(order_document_id)

                if status > 1:
                    continue
        finally:
            self._rellenar_tabla()
