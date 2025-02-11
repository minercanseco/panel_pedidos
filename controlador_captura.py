import copy
import datetime

import pyperclip
import logging

from configurar_pedido import ConfigurarPedido
from agregar_manualmente import AgregarPartidaManualmente
from direccion_cliente import DireccionCliente
from direcciones_adicionales import DireccionesAdicionales
from historial_cliente import HistorialCliente
from panel_direcciones import PanelDirecciones
from formulario_cliente import FormularioCliente
from verificador_precios import VerificadorPrecios
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

    def _agregar_atajos(self):
        eventos = {
            'F1': lambda: self._agregar_partida_manualmente(),
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

    def _agregar_partida_manualmente(self):
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
            VerificadorPrecios(ventana, self._parametros_contpaqi)

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
                 'hotkey': '[F1]', 'comando': self._agregar_partida_manualmente},

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

