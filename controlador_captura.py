import copy
import datetime
import re

import pyperclip
import logging

from agregar_epecificaciones import AgregarEspecificaciones
from agregar_manualmente import AgregarPartidaManualmente
from direccion_cliente import DireccionCliente
from direcciones_adicionales import DireccionesAdicionales
from historial_cliente import HistorialCliente
from panel_direcciones import PanelDirecciones
from formulario_cliente import FormularioCliente
from interfaz_verificador import InterfazVerificador
from controlador_verificador import ControladorVerificador
from editar_partida import EditarPartida


class ControladorCaptura:
    def __init__(self, interfaz, modelo):

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

        logging.basicConfig()

        self._rellenar_controles_interfaz()
        self._cargar_eventos_componentes()
        self._agregar_validaciones()

        if not self._es_documento_bloqueado():
            self._agregar_atajos()

        self._modelo.agregar_servicio_a_domicilio()

        self._rellenar_desde_base_de_datos()

        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Capturar documento')
        self._master.lift()  # Traer al frente
        self._master.focus_force()  # Forzar el foco

        self._ventanas.enfocar_componente('tbx_clave')
        self._configurar_pedido()
        self._inicializar_captura_manual()

    def _inicializar_captura_manual(self):
        if self._interfaz.modulo_id not in [1687]:
            return

        self._procesando_seleccion = False
        self._info_partida_seleccionada = {}
        self._agregando_producto = False

        self._rellenar_componentes_manual()
        self._buscar_ofertas(rellenar_tabla=False)

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
            'btn_especificaciones_manual': lambda: self._agregar_especicificaciones(),
            'tbx_buscar_manual': lambda event: self._buscar_productos_manualmente(),
            'btn_copiar_manual': lambda: self._copiar_productos(),
            'tbx_cantidad_manual': lambda event: self._selecionar_producto_tabla_manual(),
            'chk_monto': lambda *args: self._selecionar_producto_tabla_manual(),
            'chk_pieza': lambda *args: self._selecionar_producto_tabla_manual(),
            'tvw_productos_manual': (lambda event: self._selecionar_producto_tabla_manual(configurar_forma=True), 'seleccion'),
        }

        self._ventanas.cargar_eventos(eventos)

        evento_adicional = {
            'tvw_productos': (lambda event: self._eliminar_partida(), 'suprimir'),
        }
        self._ventanas.cargar_eventos(evento_adicional)

        txt_comentario_pedido = self._ventanas.componentes_forma['txt_comentario_documento']
        txt_comentario_pedido.bind("<FocusOut>",lambda event:self._actualizar_comentario_pedido())

    def _actualizar_comentario_pedido(self):
        comentario = self._ventanas.obtener_input_componente('txt_comentario_documento')
        comentario = comentario.upper().strip() if comentario else ''
        self.documento.comments = comentario

    def _agregar_validaciones(self):
        self._ventanas.agregar_validacion_tbx('tbx_clave', 'codigo_barras')
        self._ventanas.agregar_validacion_tbx('tbx_cantidad_manual', 'cantidad')

    def _agregar_atajos(self):
        eventos = {
            'F1': lambda: self._agregar_partida_manualmente_popup(),
            'F4': lambda: self._editar_partida(),
            'F8': lambda: self._verificador_precios(),
            'F9': lambda: self._editar_direccion(),
            'F10': lambda: self._agregar_direccion(),
            'F12': lambda: self._editar_cliente()
        }
        self._ventanas.agregar_hotkeys_forma(eventos)

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

        unidad_cayal = 0 if info_producto[0]['ClaveUnidad'] == 'KGM' else 1 # Del control de captura manual
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

            self._modelo.agregar_partida_tabla(partida_procesada, document_item_id=document_item_id, tipo_captura=tipo_captura,
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
            return

        cantidad_control = self._obtener_cantidad_partida_manual()

        if cantidad_control <= 0:
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

                #----------------------------------------------------------------------------------
                # remover la partida de los items del documento

                # filtrar de los items del documento
                partida_items = [partida for partida in self.documento.items
                                   if str(identificador) == str(partida['uuid'])][0]

                nuevas_partidas = [partida for partida in self.documento.items
                                   if str(identificador) != str(partida['uuid'])]

                # asignar los nuevos items sin el item que ha sido removido
                self.documento.items = nuevas_partidas
                self._modelo.actualizar_totales_documento(partida_items, decrementar=True)
                # ----------------------------------------------------------------------------------

                # respalda la partida extra para tratamiento despues del cierre del documento
                comentario = f'ELIMINADA POR {self._user_name}'
                self._modelo.agregar_partida_items_documento_extra(partida_items, 'eliminar', comentario, identificador)

                # si aplica agrega servicio a domicilio
                if self.documento.total < 201:
                    self._modelo.agregar_servicio_a_domicilio(partida_eliminada=True)

                # si aplica remueve el servicio a domicilio
                if self._module_id == 1687 and self.servicio_a_domicilio_agregado == True:
                    if self.documento.total - self._costo_servicio_a_domicilio >= 200:
                        self._modelo.remover_servicio_a_domicilio()

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
        instancia = EditarPartida(ventana, self._interfaz, self._modelo, self._utilerias, self.base_de_datos, valores_fila)
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
                {'nombre_icono': 'Product32.ico', 'etiqueta': 'C.Manual', 'nombre': 'captura_manual',
                 'hotkey': '[F1]', 'comando': self._agregar_partida_manualmente_popup},

                {'nombre_icono': 'ProductChange32.ico', 'etiqueta': 'Editar', 'nombre': 'editar_partida',
                 'hotkey': '[F4]', 'comando': self._editar_partida},

                {'nombre_icono': 'Cancelled32.ico', 'etiqueta': 'Eliminar', 'nombre': 'eliminar_partida',
                 'hotkey': '[SUPR]', 'comando': self._eliminar_partida},

                {'nombre_icono': 'Barcode32.ico', 'etiqueta': 'V.Precios', 'nombre': 'verificador_precios',
                 'hotkey': '[F8]', 'comando': self._verificador_precios},

                {'nombre_icono': 'EditAddress32.ico', 'etiqueta': 'E.Dirección', 'nombre': 'editar_direccion',
                 'hotkey': '[F9]', 'comando': self._editar_direccion},

                {'nombre_icono': 'Address32.ico', 'etiqueta': 'A.Dirección', 'nombre': 'agregar_direccion',
                 'hotkey': '[F10]', 'comando': self._agregar_direccion},

                {'nombre_icono': 'DocumentEdit32.ico', 'etiqueta': 'Editar Cliente', 'nombre': 'editar_cliente',
                 'hotkey': '[F12]', 'comando': self._editar_cliente},

                {'nombre_icono': 'CampaignFlow32.ico', 'etiqueta': 'H.Cliente', 'nombre': 'historial_cliente',
                 'hotkey': None, 'comando': self._historial_cliente},

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

            valores_fila = self._ventanas.procesar_fila_treeview('tvw_productos_manual',fila)
            product_id = valores_fila['ProductID']
            producto = str(valores_fila['Descripción'])

            if product_id in self._modelo.products_ids_ofertados:
                producto_actualizado  = self._actualizar_nombre_producto_ofertado(producto, product_id)
                valores_fila['Descripción'] = producto_actualizado
                self._ventanas.actualizar_fila_treeview_diccionario('tvw_productos_manual', fila, valores_fila)
                self._ventanas.colorear_fila_seleccionada_treeview('tvw_productos_manual', fila, color='warning')

    def _actualizar_nombre_producto_ofertado(self, producto, product_id):
        # Buscar el producto ofertado por ID (copiando solo los campos necesarios)
        for reg in self._modelo.consulta_productos_ofertados:
            if int(reg['ProductID']) == int(product_id):
                sale_price_before = self._utilerias.redondear_valor_cantidad_a_decimal(reg['SalePriceBefore'])  # Copia segura
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

                nuevo_comentario = f'{comentario_original}' \
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

        consulta_productos_impuestos = self._modelo.agregar_impuestos_productos(consulta_productos)

        self._modelo.consulta_productos = consulta_productos_impuestos
        self._rellenar_tabla_productos_manual(consulta_productos_impuestos)

    def _limpiar_controles_forma_manual(self):
        componentes = [
            'tbx_equivalencia_manual',
            'lbl_existencia_manual',
            'lbl_monto_manual',
            'chk_pieza_manual',
            'chk_monto_manual',
            'txt_comentario_manual',
            'tvw_productos_manual',
            'tbx_cantidad_manual'
        ]
        self._ventanas.limpiar_componentes(componentes)
        self._ventanas.enfocar_componente('tbx_buscar_manual')

    def _rellenar_componentes_manual(self):

        # 0 por clave o termino /// 1 por linea
        tipo_busqueda = ['Término', 'Línea']
        self._ventanas.rellenar_cbx('cbx_tipo_busqueda_manual', tipo_busqueda, 'Sin seleccione')
        cbx_tipo_busqueda = self._ventanas.componentes_forma['cbx_tipo_busqueda_manual']
        cbx_tipo_busqueda.set('Término')

        self._ventanas.insertar_input_componente('tbx_cantidad_manual', 1)
        self._ventanas.insertar_input_componente('tbx_equivalencia_manual', 0.0)
        self._ventanas.bloquear_componente('tbx_equivalencia_manual')

        self._ventanas.insertar_input_componente('txt_portapapeles_manual', self._copiar_portapapeles())

    def _copiar_productos(self):
        filas = self._ventanas.obtener_seleccion_filas_treeview('tvw_productos_manual')
        datos_tabla = []
        for fila in filas:
            valores_fila = self._ventanas.obtener_valores_fila_treeview('tvw_productos_manual', fila)

            valores = [valores_fila[1], valores_fila[2], valores_fila[5]] #producto, precio linea
            datos_tabla.append(valores)

        tabla = self._crear_tabla_texto(datos_tabla)
        pyperclip.copy(tabla)

    def _crear_tabla_texto(self, datos):
        def obtener_icono(linea):
            iconos = {
                'POLLO': '🍗',
                'RES LOCAL': '🐄',
                'CERDO': '🐖',
                'VERDURAS': '🥑',
                'ABARROTES': '🛒',
                'IMPORTADOS': '🥩'
            }
            return iconos.get(linea.upper(), '🛒')  # Icono por defecto si no coincide

        tabla = []
        for fila in datos:
            producto, precio, linea = fila
            icono = obtener_icono(linea)

            if '(OFE)' in producto:
                limite = producto.find('(OFE)')
                precio_sin_oferta = producto[limite + len('(OFE)'):].strip()
                producto_sin_oferta = producto[:limite].strip()
                texto = f"🏷️ {producto_sin_oferta} (OFERTA)💲 {precio} - (ANTES)💲 {precio_sin_oferta}"
            else:
                texto = f"{icono} {producto} 💲 {precio}"

            tabla.append(texto)

        return "\n".join(tabla)

    def _activar_chk_pieza(self):
        if self._tabla_manual_con_seleccion_valida():
            self._ventanas.cambiar_estado_checkbutton('chk_monto', 'deseleccionado')
            self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'seleccionado')
            self._selecionar_producto_tabla_manual()

    def _activar_chk_monto(self):
        if self._tabla_manual_con_seleccion_valida():
            self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'deseleccionado')
            self._ventanas.cambiar_estado_checkbutton('chk_monto', 'seleccionado')

            precio_unidad = self._info_partida_seleccionada.get('SalePriceWithTaxes', 10)
            self._ventanas.insertar_input_componente('tbx_cantidad_manual', precio_unidad)

            self._selecionar_producto_tabla_manual()

    def _tabla_manual_con_seleccion_valida(self):
        if self._ventanas.numero_filas_treeview('tvw_productos_manual') == 0:
            return False

        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_productos_manual')

        if len(fila) > 1 or len(fila) < 1:
            return False

        return fila

    def _selecionar_producto_tabla_manual(self, configurar_forma=None):

        if self._procesando_seleccion:
            return

        self._procesando_seleccion = True

        try:
            fila = self._tabla_manual_con_seleccion_valida()
            if not fila:
                return

            valores = self._ventanas.obtener_valores_fila_treeview('tvw_productos_manual', fila)

            product_id = int(valores[3])

            info_producto = copy.deepcopy(self._modelo.buscar_informacion_producto(product_id))

            if info_producto:
                self._product_id = product_id

                if configurar_forma:
                    self._configurar_forma_manual_segun_producto(info_producto)

                cantidad = self._obtener_cantidad_manual_partida()
                self._ventanas.insertar_input_componente('tbx_cantidad_manual', cantidad)

                self._product_id = product_id
                self._calcular_valores_partida(info_producto)
                self._info_partida_seleccionada = info_producto

        finally:
            self._procesando_seleccion = False

    def _insertar_equivalencia(self, equivalencia):

        equivalencia = str(equivalencia)
        equivalencia_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

        self._ventanas.desbloquear_componente('tbx_equivalencia_manual')
        self._ventanas.insertar_input_componente('tbx_equivalencia_manual', equivalencia_decimal)
        self._ventanas.bloquear_componente('tbx_equivalencia_manual')

        return equivalencia_decimal

    def _configurar_forma_manual_segun_producto(self, info_producto):

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
            self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'deseleccionado')

    def _obtener_cantidad_manual_partida(self):
        cantidad = self._ventanas.obtener_input_componente('tbx_cantidad_manual')

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

        tipo_calculo = self._determinar_tipo_calculo_partida_manual(info_producto)
        cantidad_piezas = 0
        total = 0
        cantidad_real_decimal = 0

        if tipo_calculo != 'Error':
            valores_controles = self._obtener_valores_controles()

            precio_con_impuestos = self._utilerias.redondear_valor_cantidad_a_decimal(info_producto.get('SalePriceWithTaxes', 0.0))

            cantidad = valores_controles['cantidad']
            cantidad_piezas = cantidad
            cantidad_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(cantidad)

            equivalencia = valores_controles['equivalencia']
            equivalencia_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

            cantidad_real_decimal = calcular_cantidad_real(tipo_calculo, equivalencia_decimal, cantidad_decimal)

            if tipo_calculo == 'Equivalencia':
                if not self._utilerias.es_numero_entero(cantidad_decimal):
                    cantidad_decimal = self._utilerias.redondear_numero_a_entero(cantidad_decimal)
                    self._ventanas.insertar_input_componente('tbx_cantidad_manual', cantidad_decimal)
                total = cantidad_real_decimal * precio_con_impuestos

            if tipo_calculo == 'Unidad':
                total = cantidad_real_decimal * precio_con_impuestos

            if tipo_calculo == 'Monto':
                total = cantidad
                cantidad = total / precio_con_impuestos

                cantidad_real_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(cantidad)

        self._actualizar_lbl_total_manual_moneda(total)
        texto = self._modelo.crear_texto_existencia_producto(info_producto)
        self._ventanas.insertar_input_componente('lbl_existencia_manual', texto)

        unidad = info_producto.get('Unit', 'PIEZA')
        product_id = int(info_producto.get('ProductID', 0))

        texto_cantidad = self._modelo.crear_texto_cantidad_producto(cantidad_real_decimal, unidad, product_id)
        self._ventanas.insertar_input_componente('lbl_cantidad_manual', texto_cantidad)
        self._actualizar_clave_producto_manual()

        return {'cantidad': cantidad_real_decimal, 'cantidad_piezas': cantidad_piezas, 'total': total}

    def _actualizar_clave_producto_manual(self):
        seleccion = self._ventanas.obtener_seleccion_filas_treeview('tvw_productos_manual')
        if not seleccion:
            return

        for fila in seleccion:
            valores_fila = self._ventanas.procesar_fila_treeview('tvw_productos_manual', fila)
            texto = f"CLAVE:{valores_fila['Código']}"
            self._ventanas.insertar_input_componente('lbl_clave_manual', texto)

    def _actualizar_lbl_total_manual_moneda(self, total_decimal):
        total_moneda = self._utilerias.convertir_decimal_a_moneda(total_decimal)
        self._ventanas.insertar_input_componente('lbl_monto_manual', total_moneda)

    def _obtener_valores_controles(self):

        equivalencia = self._ventanas.obtener_input_componente('tbx_equivalencia_manual')
        equivalencia_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

        return {
            'valor_chk_monto': self._ventanas.obtener_input_componente('chk_monto'),
            'valor_chk_pieza': self._ventanas.obtener_input_componente('chk_pieza'),
            'cantidad': self._obtener_cantidad_partida_manual(),
            'equivalencia': equivalencia_decimal
        }

    def _obtener_cantidad_partida_manual(self):
        cantidad = self._ventanas.obtener_input_componente('tbx_cantidad_manual')

        if not cantidad or not self._utilerias.es_cantidad(cantidad):
            return self._utilerias.redondear_valor_cantidad_a_decimal(0)

        cantidad_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(cantidad)

        return self._utilerias.redondear_valor_cantidad_a_decimal(1) if cantidad_decimal <= 0 else cantidad_decimal

    def _determinar_tipo_calculo_partida_manual(self, info_producto):

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
                self._ventanas.insertar_input_componente('tbx_cantidad_manual', 1)

            if valor_chk_pieza == 0:
                self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'seleccionado')

            if valor_chk_monto == 1:
                self._ventanas.cambiar_estado_checkbutton('chk_monto', 'deseleccionado')
                self._modelo.mensajes_de_error(4, self._master)

            if equivalencia == 0:
                return 'Unidad'

            if equivalencia != 0:
                return 'Equivalencia'

        if clave_unidad == 'KGM':

            if valor_chk_pieza == 1 and equivalencia == 0:
                self._modelo.mensajes_de_error(3, self._master)
                self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'deseleccionado')
                return 'Error'

            if valor_chk_monto == 1 and cantidad == 0:
                self._modelo.mensajes_de_error(0, self._master)
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
                self._modelo.mensajes_de_error(2, self._master)
                return 'Error'

            if valor_chk_monto == 1:
                return 'Monto'
        return 'Error'
