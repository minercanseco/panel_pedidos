import tkinter as tk

from cayal.cliente import Cliente
from cayal.ventanas import Ventanas

from herramientas.capturar_documento.herramientas_captura.editar_direccion_documento import EditarDireccionDocumento
from herramientas.capturar_documento.herramientas_captura.editar_partida import EditarPartida
from herramientas.capturar_documento.herramientas_captura.historial_cliente import HistorialCliente
from herramientas.cliente.notebook_cliente import NoteBookCliente
from herramientas.verificador_precios.controlador_verificador import ControladorVerificador
from herramientas.verificador_precios.interfaz_verificador import InterfazVerificador


class HerramientasPedido:
    def __init__(self, master, modelo, interfaz, controlador, cargar_shortcuts=True):
        self._master = master
        self._modelo = modelo
        self._interfaz = interfaz
        self._controlador = controlador
        self._cargar_shortcuts = cargar_shortcuts

        self._base_de_datos = self._modelo.base_de_datos
        self._parametros = self._modelo.parametros
        self._utilerias = self._modelo.utilerias
        self._ventanas = Ventanas(self._master)


        self._crear_frames()
        self._crear_barra_herramientas()


        if self._cargar_shortcuts:
            self._cargar_eventos()
            self._agregar_atajos()

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'pady': 5, 'padx': 5, 'sticky': tk.NSEW}),

            'frame_herramientas': ('frame_principal', None,
                                  {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                   'sticky': tk.NSEW})
        }
        self._ventanas.crear_frames(frames)

    def _crear_barra_herramientas(self):
        herramientas = [
            {
                'nombre_icono': 'Barcode32.ico',
                'etiqueta': 'V.Precios',
                'nombre': 'verificador_precios',
                'hotkey': '[F3]',
                'comando': self._verificador_precios,
            },
            {
                'nombre_icono': 'EditAddress32.ico',
                'etiqueta': 'E.Dirección',
                'nombre': 'editar_direccion',
                'hotkey': '[F4]',
                'comando': self._editar_direccion_documento,
            },
            {
                'nombre_icono': 'DocumentEdit32.ico',
                'etiqueta': 'Editar Cliente',
                'nombre': 'editar_cliente',
                'hotkey': '[F6]',
                'comando': self._editar_cliente,
            },
            {
                'nombre_icono': 'CampaignFlow32.ico',
                'etiqueta': 'H.Cliente',
                'nombre': 'historial_cliente',
                'hotkey': '[F7]',
                'comando': self._historial_cliente,
            },
            {
                'nombre_icono': 'ProductChange32.ico',
                'etiqueta': 'Editar',
                'nombre': 'editar_partida',
                'hotkey': '[F2]',
                'comando': self._editar_partida,
            },
            {
                'nombre_icono': 'Cancelled32.ico',
                'etiqueta': 'Eliminar',
                'nombre': 'eliminar_partida',
                'hotkey': '[SUPR]',
                'comando': self._eliminar_partida,
            },
        ]

        self.barra_herramientas_pedido = herramientas
        self.elementos_barra_herramientas = self._ventanas.crear_barra_herramientas(
            self.barra_herramientas_pedido,
            'frame_herramientas'
        )
        self.iconos_barra_herramientas = self.elementos_barra_herramientas[0]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]

    def _cargar_eventos(self):
        evento_1 = {
            'tvw_productos': (lambda event: self._editar_partida(), 'doble_click')
        }

        evento_2 = {
            'tvw_productos':  (lambda event: self._eliminar_partida(), 'suprimir')
        }

        self._interfaz.ventanas.cargar_eventos(evento_1)
        self._interfaz.ventanas.cargar_eventos(evento_2)

        ancho, alto = self._interfaz.ventanas.obtener_resolucion_pantalla()

        if ancho > 1367:
            txt_comentario_pedido = self._interfaz.ventanas.componentes_forma['txt_comentario_documento']
            txt_comentario_pedido.bind("<FocusOut>", lambda event: self._actualizar_comentario_pedido())

    def _actualizar_comentario_pedido(self):
        comentario = self._ventanas.obtener_input_componente('txt_comentario_documento')
        comentario = comentario.upper().strip() if comentario else ''
        self._modelo.documento.comments = comentario

    def _agregar_atajos(self):
        eventos = {
            'F2': lambda: self._editar_partida(),
            'F3': lambda: self._verificador_precios(),
            'F4': lambda: self._editar_direccion_documento(),
            'F6': lambda: self._editar_cliente(),
            'F7': lambda: self._historial_cliente(),
            'Delete': lambda: self._eliminar_partida(),
        }

        self._interfaz.ventanas.agregar_hotkeys_forma(eventos)

    def _validar_bloqueo(self):
        if not self._cargar_shortcuts:
            self._ventanas.mostrar_mensaje('El documento está bloqueado a la edición.')
            return

        return True
    #-----------------------------------------------------------
    # Funciones relacionadas con la sección
    # -----------------------------------------------------------
    def _editar_cliente(self):

        if not self._validar_bloqueo():
            return

        business_entity_id = self._modelo.cliente.business_entity_id
        if not business_entity_id or business_entity_id == 0:
            return

        self._parametros.id_principal = business_entity_id
        try:
            ventana = self._ventanas.crear_popup_ttkbootstrap()

            NoteBookCliente(
                ventana,
                self._base_de_datos,
                self._parametros,
                self._utilerias,
                Cliente()
            )
            ventana.wait_window()
        finally:
            self._modelo.actualizar_info_cliente()
            self._modelo.settear_info_direcciones_cliente(business_entity_id)
            self._parametros.id_principal = 0

    def _eliminar_partida(self):
        if not self._validar_bloqueo():
            return

        filas = self._interfaz.ventanas.obtener_seleccion_filas_treeview('tvw_productos')
        if not filas:
            return

        if filas:
            if not self._ventanas.mostrar_mensaje_pregunta('¿Desea eliminar las partidas seleccionadas?'):
                return

            production_status_modified = 0
            for fila in filas:
                valores_fila = self._interfaz.ventanas.procesar_fila_treeview('tvw_productos', fila)
                product_id = valores_fila['ProductID']

                # la eliminacion del servicio a domicilio es de forma automatizada
                if product_id == 5606 and self._modelo.module_id == 1687:
                    self._controlador.mensajes_de_error(13)
                    return

                document_item_id = valores_fila['DocumentItemID']
                identificador = valores_fila['UUID']

                # si aplica remover de la bd
                if document_item_id != 0:
                    self._modelo.eliminar_partida_documento(document_item_id)

                # remover del treeview
                self._interfaz.ventanas.remover_fila_treeview('tvw_productos', fila)

                # ----------------------------------------------------------------------------------
                # remover la partida de los items del documento

                # filtrar de los items del documento
                partida_items = [partida for partida in self._modelo.documento.items
                                 if str(identificador) == str(partida['uuid'])][0]

                nuevas_partidas = [partida for partida in self._modelo.documento.items
                                   if str(identificador) != str(partida['uuid'])]

                # asignar los nuevos items sin el item que ha sido removido
                self._modelo.documento.items = nuevas_partidas
                self._controlador.actualizar_totales_documento()
                # ----------------------------------------------------------------------------------

                # respalda la partida extra para tratamiento despues del cierre del documento
                comentario = f'ELIMINADA POR {self._modelo.user_name}'
                self._modelo.agregar_partida_items_documento_extra(partida_items, 'eliminar', comentario, identificador)

                # Solo aplica para el módulo 1687 pedidos
                if self._modelo.module_id == 1687:
                    # Si el total es menor a 200 y no se ha agregado aún, lo agrega
                    if self._modelo.documento.total < 200 and not self._controlador._servicio_a_domicilio_agregado:
                        self._controlador.agregar_servicio_a_domicilio()
                        self._controlador._servicio_a_domicilio_agregado = True

                    # Si ya se agregó pero ahora el total (sin el servicio) es >= 200, lo remueve
                    elif self._controlador._servicio_a_domicilio_agregado and (
                            self._modelo.documento.total - self._modelo.documento.delivery_cost) >= 200:
                        self._controlador.remover_servicio_a_domicilio()
                        self._controlador._servicio_a_domicilio_agregado = False

    def _editar_partida(self):
        if not self._validar_bloqueo():
            return

        fila = self._interfaz.ventanas.obtener_seleccion_filas_treeview('tvw_productos')

        if not fila:
            self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar por lo menos un producto')
            return

        if not self._interfaz.ventanas.validar_seleccion_una_fila_treeview('tvw_productos'):
            self._ventanas.mostrar_mensaje('Debe seleccionar por lo menos un producto')
            return

        valores_fila = self._interfaz.ventanas.procesar_fila_treeview('tvw_productos', fila)
        if valores_fila['ProductID'] == 5606:
            self._ventanas.mostrar_mensaje('No se puede editar la partida servicio a domicilio.')
            return

        ventana = self._ventanas.crear_popup_ttkbootstrap('Editar partida')
        instancia = EditarPartida(ventana, self._interfaz, self._modelo, self._utilerias, self._base_de_datos,
                                  valores_fila)
        ventana.wait_window()


    def _verificador_precios(self):
        if not self._validar_bloqueo():
            return

        ventana = self._ventanas.crear_popup_ttkbootstrap()
        vista = InterfazVerificador(ventana)
        controlador = ControladorVerificador(vista, self._parametros)

    def _historial_cliente(self):
        if not self._validar_bloqueo():
            return

        ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
        instancia = HistorialCliente(ventana,
                                     self._modelo.base_de_datos,
                                     self._utilerias,
                                     self._modelo.cliente.business_entity_id
                                     )
        ventana.wait_window()

    def _editar_direccion_documento(self):
        if not self._validar_bloqueo():
            return

        ventana = self._ventanas.crear_popup_ttkbootstrap(self._master)
        _ = EditarDireccionDocumento(ventana, self._modelo, self._interfaz)
        ventana.wait_window()

