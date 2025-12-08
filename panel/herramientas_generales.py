import tkinter as tk

from cayal.login import Login
from cayal.ventanas import Ventanas
from cayal.cliente import Cliente

from herramientas.cliente.buscar_clientes import BuscarClientes
from herramientas.cliente.cliente_nuevo import ClienteNuevo
from herramientas.cliente.notebook_cliente import NoteBookCliente
from herramientas.herramientas_compartidas.cancelar_pedido import CancelarPedido
from herramientas.herramientas_compartidas.generador_ticket_produccion import GeneradorTicketProduccion
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
        self._ticket = GeneradorTicketProduccion(32)
        self._ticket.ruta_archivo = self._modelo.obtener_directorio_reportes()

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
             'hotkey': None, 'comando': self._imprimir_ticket_produccion},

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
            return valores_fila

        return valores_fila[valor]

    def _imprimir_ticket_produccion(self):

        def filtrar_partidas_por_area_impresion(consulta_partidas, areas_imprimibles, todas_las_areas):

            partidas_sin_servicio_domicilio = [partida for partida in consulta_partidas if partida['ProductID'] != 5606]
            sin_partidas_eliminadas = [partida for partida in partidas_sin_servicio_domicilio
                                       if partida['ItemProductionStatusModified'] != 3]

            tipos_partida = {0: 'M', 1: 'P', 2: 'A'}

            partidas = []
            for partida in sin_partidas_eliminadas:
                product_type_id_cayal = partida.get('ProductTypeIDCayal', 1)
                if tipos_partida[product_type_id_cayal] in areas_imprimibles:
                    partidas.append(partida)

            def generar_texto(conjunto):
                # Mapeo de letras a sus respectivos textos
                mapeo = {
                    'P': 'Produccion',
                    'M': 'Minisuper',
                    'A': 'Almacen'
                }

                # Filtrar las letras válidas y generar el texto
                textos = [mapeo[letra] for letra in conjunto if letra in mapeo]
                return ', '.join(textos)

            return generar_texto(areas_imprimibles), generar_texto(todas_las_areas), partidas

        def filtrar_partidas_ticket(consulta_partidas):
            partidas = []

            for partida in consulta_partidas:

                cayal_piece = partida['CayalPiece']
                unidad_producto = partida['Unit']
                product_id = partida['ProductID']

                abreviatura_unidad = self._utilerias.abreviatura_unidad_producto(unidad_producto)

                # es un producto pesado con unidad pieza
                if cayal_piece != 0:

                    # el texto experado en la partida si es por piezas es:
                    # TOMATE
                    # CANTIDAD: (1 Pz) 0.20 Kg

                    # HUEVO (REJA)
                    # CANTIDAD: (1 Rj) 30 Pz

                    # CUERO
                    # CANTIDAD: (1 Cj) 25 Kg

                    unidad_especial = self._utilerias.equivalencias_productos_especiales(product_id)

                    if unidad_especial:
                        unidad_especial = unidad_especial[0]

                    if not unidad_especial:
                        unidad_especial = 'Pz' if cayal_piece == 1 else 'Pzs'

                    cantidad_original = partida['Quantity']
                    if unidad_especial:
                        partida[
                            'Quantity'] = f"({cayal_piece} {unidad_especial}) {cantidad_original} {abreviatura_unidad}"
                    else:
                        partida['Quantity'] = f"({cayal_piece} {unidad_especial}) {cantidad_original}"

                    abreviatura_unidad = ''

                producto = {
                    'clave': partida['ProductKey'],
                    'cantidad': partida['Quantity'],
                    'descripcion': partida['ProductName'],
                    'unidad': abreviatura_unidad,
                    'observacion': partida['Comments']
                }
                partidas.append(producto)
            return partidas

        def settear_valores_ticket(pedido, order_document_id, areas_imprimibles, todas_las_areas):
            self._ticket.cliente = pedido.get('Cliente', '')
            self._ticket.pedido = pedido.get('Pedido', '')
            self._ticket.relacionado = pedido.get('Relacion', '')
            self._ticket.tipo = pedido.get('Tipo', '')

            fecha_captura = pedido.get('F.Captura', '')
            hora_captura = pedido.get('H.Captura', '')
            captura = f'{fecha_captura}-{hora_captura}'
            self._ticket.venta = captura

            fecha_entrega = pedido.get('F.Entrega', '')
            hora_entrega = pedido.get('H.Entrega', '')
            entrega = f'{fecha_entrega}-{hora_entrega}'
            self._ticket.entrega = entrega
            self._ticket.tipo_entrega = pedido.get('Entrega', '')

            self._ticket.capturista = pedido.get('Captura', '')
            self._ticket.ruta = pedido.get('Ruta')

            ruta, colonia = self._modelo.obtener_ruta_y_colonia(order_document_id)
            self._ticket.ruta = ruta
            self._ticket.colonia = colonia

            consulta_partidas = self._modelo.obtener_partidas_pedido(order_document_id)
            areas_imprimibles, todas_las_areas, partidas = filtrar_partidas_por_area_impresion(
                consulta_partidas, areas_imprimibles, todas_las_areas
            )
            self._ticket.areas = areas_imprimibles
            self._ticket.areas_aplicables =todas_las_areas

            partidas_ticket = filtrar_partidas_ticket(partidas)

            if not partidas_ticket:
                return False

            self._ticket.set_productos(partidas_ticket)

            return True

        def preparar_e_imprimir_ticket(fila):
            order_document_id = fila['OrderDocumentID']
            areas_imprimibles = self._modelo.obtener_areas_imprimibles(order_document_id)

            if len(areas_imprimibles) in (1, 2):
                self._ticket.parcial = True
            else:
                self._ticket.parcial = False

            for area in areas_imprimibles:

                imprimir = settear_valores_ticket(fila, order_document_id, area, areas_imprimibles)

                if not imprimir:
                    continue

                self._ticket.imprimir(fuente_tamano=10, nombre_impresora="Ticket")
                self._modelo.afectar_bitacora_impresion(self._ticket, order_document_id)
                self._modelo.actualizar_tablas_impresion(self._ticket, order_document_id)

        filas = None
        seleccion_status = self._interfaz.ventanas.obtener_input_componente('cbx_status')
        if seleccion_status == 'En Proceso':
            respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                '¿Desea imprimir todos los pedidos en el status en proceso, que faltan por imprimir?')
            if respuesta:
                filas = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos')
                filas = [
                    fila for fila in filas
                    if fila['TypeStatusID'] in (2, 16, 17, 18) and set(fila['PrintedStatus']) != set(
                        fila['TipoProduccion'])
                ]
            else:
                filas = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)
        else:
            filas = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)

        if not filas:
            self._interfaz.ventanas.mostrar_mensaje('No hay pedidos que imprimir')
            return

        for fila in filas:
            preparar_e_imprimir_ticket(fila)

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
        valores_fila = self._obtener_valores_fila_pedido_seleccionado()

        if not valores_fila:
            return

        order_document_id = valores_fila['OrderDocumentID']
        status_id = valores_fila['TypeStatusID']
        fecha_entrega = valores_fila['F.Entrega']
        relacion = valores_fila['Relacion']

        if status_id not in (1,3):
            self._ventanas.mostrar_mensaje('Esta función no aplica para pedidos en status Abierto y Por Timbrar.')
            return
        if not fecha_entrega or fecha_entrega in ('None', ''):
            self._ventanas.mostrar_mensaje('Debe definir las caracteristicas del pedido antes de usar esta función')
            return
        if relacion:
            self._ventanas.mostrar_mensaje('Esta función no se puede usar en órdenes de producción relacionada a otras.')
            return
        try:
            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(titulo='Editar nombre pedido.')
            self._parametros.id_principal = order_document_id
            instancia = EditarNombrePedido(ventana,
                                           self._parametros,
                                           self._modelo,
                                           valores_fila)
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
        status_id = fila['TypeStatusID']

        if status_id in (1,10, 14,15): #abierto, cancelado, cobrado, en cartera
            self._ventanas.mostrar_mensaje('El no tiene un status válido para confirmar la transferencia.')
            return

        if payment_confirmend_id == 1:
            self._ventanas.mostrar_mensaje('El pedido seleccionado no es transferencia.')
            return

        if payment_confirmend_id == 3:
            self._ventanas.mostrar_mensaje('La transferencia ha sido confirmada con anterioridad.')
            return

        self._modelo.confirmar_transferencia(self._modelo.user_id, order_document_id)
        comentario = f"Transferencia confirmada por {self._modelo.user_name}"
        self._modelo.afectar_bitacora(order_document_id, self._modelo.user_id, comentario, change_type_id=19)

    def _cambiar_usuario(self):

        def rellenar_operador():
            operador_panel = self._modelo.user_name
            version_paquete = self._parametros.version_paquete

            texto = f'Paquete: {version_paquete} OPERADOR: {operador_panel}'
            self._interfaz.ventanas.actualizar_etiqueta_externa_tabla_view('tbv_pedidos', texto)
            self._modelo.user_id = self._parametros.id_usuario

        def si_acceso_exitoso(parametros=None, master=None):
            self._parametros = parametros
            rellenar_operador()

        ventana = self._ventanas.crear_popup_ttkbootstrap()
        instancia = Login(ventana, self._parametros, si_acceso_exitoso)
        ventana.wait_window()


