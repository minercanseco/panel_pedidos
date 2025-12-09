import tkinter as tk
from cayal.ventanas import Ventanas

from herramientas.capturar_documento.buscar_generales_cliente import BuscarGeneralesCliente
from herramientas.capturar_documento.llamar_instancia_captura import LlamarInstanciaCaptura
from herramientas.herramientas_panel.editar_caracteristicas_pedido import EditarCaracteristicasPedido
from herramientas.herramientas_panel.editar_pedido import EditarPedido
from herramientas.herramientas_panel.ticket_pedido_cliente import TicketPedidoCliente


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

    def _capturar_nuevo_pedido(self):

        self._pausar_autorefresco()

        try:
            # 1) Popup para seleccionar cliente
            ventana = self._ventanas.crear_nuevo_popup_ttkbootstrap('Seleccionar cliente')
            self._parametros.id_principal = 0

            instancia = BuscarGeneralesCliente(ventana, self._parametros)

            # Esperar a que CIERRA la ventana de búsqueda
            ventana.wait_window()

            # Si el usuario cerró sin seleccionar cliente, salimos
            if not getattr(instancia, "cliente", None):
                return

            # 2) Popup para captura
            nueva_ventana = self._ventanas.crear_nuevo_popup_ttkbootstrap('Nueva captura')

            # ⚠️ NO usamos nueva_ventana.wait_window() aquí
            # porque LlamarInstanciaCaptura ya la destruye en su finally.

            _ = LlamarInstanciaCaptura(
                nueva_ventana,  # master
                self._parametros,
                instancia.cliente,
                instancia.documento,
                instancia.ofertas
            )

            ventana.mainloop()
            # En este punto, LlamarInstanciaCaptura ya terminó y
            # nueva_ventana ya fue destruida desde adentro.

        finally:
            self._parametros.id_principal = 0
            self._reanudar_autorefresco()

    def _editar_pedido(self):

        fila = self._obtener_valores_fila_pedido_seleccionado()
        if not fila:
            self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar un pedido.')
            return

        status_id = fila['TypeStatusID']
        order_document_id = fila['OrderDocumentID']

        try:
            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
            if status_id < 3:
                self._parametros.id_principal = order_document_id

                _ = LlamarInstanciaCaptura(
                    ventana,
                    self._parametros,
                )

            elif status_id == 3:
                _ = EditarPedido(ventana, self._base_de_datos, self._utilerias, self._parametros, fila)

            else:  # status_id > 3
                self._interfaz.ventanas.mostrar_mensaje(
                    'No se pueden editar en este módulo documentos que no estén en status Por Timbrar.'
                )

            ventana.wait_window()

        finally:
            self._modelo.actualizar_totales_pedido(order_document_id)

    def _editar_caracteristicas_pedido(self):
        try:
            fila = self._obtener_valores_fila_pedido_seleccionado()
            if not fila:
                return

            status = fila['TypeStatusID']

            if status == 10:
                self._interfaz.ventanas.mostrar_mensaje('NO se pueden editar pedidos cancelados.')
                return

            elif status >= 4:
                self._interfaz.ventanas.mostrar_mensaje('Sólo se pueden afectar las caracteristicas de un pedido hasta el status  Por timbrar.')
                return
            else:
                order_document_id = fila['OrderDocumentID']

                self._parametros.id_principal = order_document_id
                ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
                instancia = EditarCaracteristicasPedido(ventana,
                                                        self._parametros,
                                                        self._base_de_datos,
                                                        self._utilerias)
                ventana.wait_window()
        finally:
            self._parametros.id_principal = 0

    def _crear_ticket_pedido_cliente(self):
        order_document_id = self._obtener_valores_fila_pedido_seleccionado(valor='OrderDocumentID')
        if not order_document_id:
            return

        valores = self._modelo.obtener_status_entrega_pedido(order_document_id)

        if not valores:
            return

        status_entrega = valores['status_entrega']
        fecha_entrega = valores['fecha_entrega']

        if status_entrega == 0:
            self._interfaz.ventanas.mostrar_mensaje('Debe definir la forma de pago del cliente antes de generar el ticket.')
            return

        try:
            fecha_entrega = self._utilerias.convertir_fecha_str_a_datetime(str(fecha_entrega))
            if fecha_entrega > self._modelo.hoy:
                respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                    'EL pedido es para una fecha de entrega posterior, ¿Desea actualizar los precios antes de generar el ticket?')
                if respuesta:
                    self._base_de_datos.actualizar_precios_pedido(order_document_id)

            self._parametros.id_principal = order_document_id
            instancia = TicketPedidoCliente(self._base_de_datos, self._utilerias, self._parametros)
            self._interfaz.ventanas.mostrar_mensaje(master=self._interfaz.master,
                                                    mensaje='Comprobante generado.',
                                                    tipo='info')
            self._interfaz.master.iconify()
        finally:
            self._parametros.id_principal = 0

    def _mandar_a_producir(self):

        filas = self._obtener_valores_filas_pedidos_seleccionados()
        if not filas:
            return

        for fila in filas:
            order_document_id = fila['OrderDocumentID']
            valores = self._modelo.obtener_status_entrega_pedido(order_document_id)

            status = int(valores['status_id'])
            entrega = int(valores['fecha_entrega'])
            folio = valores['doc_folio']

            if entrega == 0:
                self._interfaz.ventanas.mostrar_mensaje(
                    f'Debe usar la herramienta de editar características para el pedido {folio}.')
                continue

            if status == 1:
                self._modelo.mandar_pedido_a_producir(order_document_id)

