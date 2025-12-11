import copy
import datetime
import re
import tkinter as tk
import pyperclip
import logging

from herramientas.capturar_documento.herramientas_captura.agregar_epecificaciones import AgregarEspecificaciones
from herramientas.capturar_documento.ventana_captura.herramientas_facturas import HerramientasFacturas
from herramientas.capturar_documento.ventana_captura.herramientas_pedido import HerramientasPedido
from herramientas.capturar_documento.ventana_captura.herramientas_ticket import HerramientasTicket


class ControladorCaptura:
    def __init__(self, interfaz, modelo):

        self._interfaz = interfaz
        self._master = interfaz.master
        self._modelo = modelo

        self._crear_notebook_herramientas()
        self._cargar_informacion_general()
        self._cargar_eventos_componentes()
        # ---------------------------------------------------------------------
        # Banderas de procesos
        # ---------------------------------------------------------------------
        self._agregando_producto = False
        self._procesando_seleccion = False

        # ---------------------------------------------------------------------
        # Acciones de inicializacion relacionadas con captura
        # ---------------------------------------------------------------------
        if self._modelo.module_id == 1687: # modulo de pedidos
            self._modelo.agregar_servicio_a_domicilio()
            self._configurar_pedido()

        if self._modelo.module_id == 1687 and self._modelo.documento.document_id > 0: # modulo de pedidos
            self._rellenar_desde_base_de_datos()

        self._buscar_ofertas()
        self._interfaz.ventanas.situar_ventana_arriba(self._master)
        self._interfaz.ventanas.enfocar_componente('tbx_clave')

        if self._modelo.module_id == 1687: # si es pedido
            self._interfaz.ventanas.enfocar_componente('tbx_buscar_manual')

    # ---------------------------------------------------------------------
    # Funciones relacionadas a herramientas y eventos de componentes de captura
    # ---------------------------------------------------------------------
    def _crear_notebook_herramientas(self):
        info_pestanas = {
            'tab_ticket': ('Herramientas', [158]),
            'tab_pedido': ('Herramientas', [1687]),
            'tab_facturas': ('Herramientas', [21, 1400, 1319, 1316, 967]),
        }

        info_pestanas_modulo = {
            clave: (etiqueta, modulos)
            for clave, (etiqueta, modulos) in info_pestanas.items()
            if self._modelo.module_id in modulos
        }

        # Si el módulo no tiene pestaña asociada, no hacemos nada
        if not info_pestanas_modulo:
            return

        nombre_notebook = 'nbk_herramientas_captura'
        notebook = self._interfaz.ventanas.crear_notebook(
            nombre_notebook=nombre_notebook,
            info_pestanas=info_pestanas_modulo,
            nombre_frame_padre='frame_herramientas',
            config_notebook={
                'row': 0,
                'column': 0,
                'sticky': tk.NSEW,
                'padx': 0,
                'pady': 0,
                'bootstyle': 'primary',
            }
        )

        # Crear frames base para cada pestaña (en la práctica será solo una)
        frames_tabs = {}
        for clave, (etiqueta, modulos) in info_pestanas_modulo.items():
            tab_name = clave
            frame_name = clave.replace('tab_', 'frm_')
            frames_tabs[frame_name] = (
                tab_name,
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW, 'padx': 0, 'pady': 0}
            )

        self._interfaz.ventanas.crear_frames(frames_tabs)

        # cada frame será el master de las subsecuentes ventanas
        for frame_name, (tab_name, configuracion, posicion) in frames_tabs.items():
            frame = self._interfaz.ventanas.componentes_forma[frame_name]

            if 'ticket' in frame_name and self._modelo.module_id == 158:
                HerramientasTicket(
                    master=frame,
                    modelo=self._modelo,
                    interfaz=self._interfaz
                )

            if 'pedido' in frame_name and self._modelo.module_id == 1687:
                HerramientasPedido(
                    master=frame,
                    modelo=self._modelo,
                    interfaz=self._interfaz
                )

            if 'facturas' in frame_name and self._modelo.module_id in (21, 1400, 1319, 1316, 967):
                HerramientasFacturas(
                    master=frame,
                    modelo=self._modelo,
                    interfaz=self._interfaz
                )

    def _cargar_eventos_componentes(self):
        eventos = {
            'tbx_clave': lambda event: self._agregar_partida_por_clave(),
            # eventos captura manual
            'btn_ofertas_manual': lambda: self._buscar_ofertas(rellenar_tabla=True),
            'btn_agregar_manual': lambda: self._agregar_partida_manualmente(),
            'btn_copiar_manual': lambda: self._copiar_productos(),
            'btn_especificaciones_manual': lambda: self._agregar_especicificaciones(),
            'tbx_buscar_manual': lambda event: self._buscar_productos_manualmente(),
            'tbx_cantidad_manual': lambda event: self._selecionar_producto_tabla_manual(),
            'chk_monto': lambda *args: self._selecionar_producto_tabla_manual(),
            'chk_pieza': lambda *args: self._selecionar_producto_tabla_manual(),
            'tvw_productos_manual': (lambda event: self._selecionar_producto_tabla_manual(configurar_forma=True), 'seleccion')
        }

        self._interfaz.ventanas.cargar_eventos(eventos)

    #---------------------------------------------------------------------
    # Funciones relacionadas a información del documento y estado inicial
    # ---------------------------------------------------------------------
    def _cargar_informacion_general(self):
        self._cargar_direccion_cliente()
        self._cargar_nombre_cliente()
        self._cargar_informacion_crediticia()

        self._interfaz.ventanas.insertar_input_componente('lbl_captura', self._modelo.user_name)
        self._interfaz.ventanas.insertar_input_componente('lbl_folio', self._modelo.documento.docfolio)

        nombre_modulo = self._modelo.obtener_nombre_y_prefijo_segun_modulo()
        self._interfaz.ventanas.insertar_input_componente('lbl_modulo', nombre_modulo)

        if self._modelo.module_id in (21,1400,1319):
            self._modelo.rellenar_cbxs_fiscales()

        self._cargar_info_inicial_componentes_captura_manual()

    def _cargar_nombre_cliente(self):
        nombre = self._modelo.cliente.official_name
        nombre_comercial = self._modelo.cliente.commercial_name
        sucursal = self._modelo.documento.depot_name
        nombre_direccion = self._modelo.documento.address_name

        sucursal = f'({nombre_direccion})' if not sucursal else f'({sucursal})'
        nombre_comercial = '' if not nombre_comercial else f'-{nombre_comercial}-'

        nombre_cliente = f'{nombre} {nombre_comercial} {sucursal}'
        self._interfaz.ventanas.insertar_input_componente('tbx_cliente', nombre_cliente)
        self._interfaz.ventanas.bloquear_componente('tbx_cliente')

    def _cargar_direccion_cliente(self):
        datos_direccion = self._modelo.documento.address_details

        self._modelo.documento.address_detail_id = datos_direccion['AddressDetailID']
        if self._modelo.module_id == 1687: # modulo de pedidos
            self._modelo.documento.order_parameters['AddressDetailID'] = datos_direccion['AddressDetailID']

        calle = datos_direccion.get('Street', '')
        numero = datos_direccion.get('ExtNumber', '')
        colonia = datos_direccion.get('City', '')
        cp = datos_direccion.get('ZipCode', '')
        municipio = datos_direccion.get('Municipality', '')
        estado = datos_direccion.get('StateProvince', '')
        comentario = datos_direccion.get('Comments', '')

        texto_direccion = f'{calle} NUM.{numero}, COL.{colonia}, MPIO.{municipio}, EDO.{estado}, C.P.{cp}'
        texto_direccion = texto_direccion.upper()

        self._interfaz.ventanas.insertar_input_componente('tbx_direccion', texto_direccion)
        self._interfaz.ventanas.bloquear_componente('tbx_direccion')

        self._interfaz.ventanas.insertar_input_componente('tbx_comentario', comentario)
        self._interfaz.ventanas.bloquear_componente('tbx_comentario')

    def _cargar_informacion_crediticia(self):

        if self._modelo.cliente.credit_block == 1:
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
                componente = self._modelo.ventanas.componentes_forma.get(nombre, None)
                if componente:
                    componente.config(**estilo)

        if self._modelo.cliente.credit_block == 0:
            if self._modelo.cliente.authorized_credit > 0 and self._modelo.cliente.remaining_credit > 0:
                valores = {'authorized_credit': 'lbl_credito',
                           'remaining_credit': 'lbl_restante',
                           'debt': 'lbl_debe'
                           }

                # el credito del cliente es el credito del documento
                self._modelo.documento.credit_document_available = 0 if self._modelo.cliente.remaining_credit <= 0 else 1

                for atributo, label in valores.items():
                    monto = getattr(self._modelo.cliente, atributo)
                    monto_decimal = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(monto)
                    monto_moneda = self._modelo.utilerias.convertir_decimal_a_moneda(monto_decimal)

                    self._interfaz.ventanas.insertar_input_componente(label, monto_moneda)

    def _cargar_info_inicial_componentes_captura_manual(self):

        # 0 por clave o termino /// 1 por linea
        tipo_busqueda = ['Término', 'Línea']
        self._interfaz.ventanas.rellenar_cbx('cbx_tipo_busqueda_manual', tipo_busqueda, 'Sin seleccione')
        cbx_tipo_busqueda = self._interfaz.ventanas.componentes_forma['cbx_tipo_busqueda_manual']
        cbx_tipo_busqueda.set('Término')

        self._interfaz.ventanas.insertar_input_componente('tbx_cantidad_manual', 1)
        self._interfaz.ventanas.insertar_input_componente('tbx_equivalencia_manual', 0.0)
        self._interfaz.ventanas.bloquear_componente('tbx_equivalencia_manual')

        if self._modelo.module_id != 158:
            self._interfaz.ventanas.insertar_input_componente('txt_portapapeles_manual',
                                                              self._copiar_portapapeles(),
                                                              con_saltos_de_linea=True)

    # ---------------------------------------------------------------------
    # Funciones auxiliares relacionados con la captura de partidas en el pedido
    # ---------------------------------------------------------------------
    def _configurar_pedido(self):
        if self._modelo.documento.document_id < 1:
            valores_pedido = {}
            valores_pedido['OrderTypeID'] = 1
            valores_pedido['CreatedBy'] = self._modelo.parametros.id_usuario
            valores_pedido['CreatedOn'] = datetime.datetime.now()
            comentario_pedido = self._modelo.documento.comments
            valores_pedido['CommentsOrder'] = comentario_pedido.upper().strip() if comentario_pedido else ''
            valores_pedido['BusinessEntityID'] = self._modelo.cliente.business_entity_id
            related_order_id = 0
            valores_pedido['RelatedOrderID'] = related_order_id
            valores_pedido['ZoneID'] = self._modelo.cliente.zone_id
            valores_pedido['SubTotal'] = 0
            valores_pedido['TotalTax'] = 0
            valores_pedido['Total'] = 0
            valores_pedido['HostName'] = self._modelo.utilerias.obtener_hostname()
            valores_pedido['AddressDetailID'] = self._modelo.documento.address_detail_id
            valores_pedido['DocumentTypeID'] = self._modelo.documento.cfd_type_id
            valores_pedido['OrderDeliveryCost'] = self._modelo.documento.delivery_cost
            valores_pedido['DepotID'] = self._modelo.documento.depot_id
            valores_pedido['OrderDocumentID'] = self._modelo.documento.order_document_id

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
            self._modelo.documento.order_parameters = valores_pedido

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

    def _copiar_productos(self):

        def obtener_icono(linea):
            iconos = {
                'POLLO': '🍗',
                'RES LOCAL': '🐄',
                'CERDO': '🐖',
                'VERDURAS': '🥑',
                'ABARROTES': '🛒',
                'IMPORTADOS': '🥩'
            }
            return iconos.get(linea.upper(), '🛒')

        def crear_tabla_texto(datos):
            # Icono por defecto si no coincide

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

        filas = self._interfaz.ventanas.obtener_seleccion_filas_treeview('tvw_productos_manual')
        datos_tabla = []
        for fila in filas:
            valores_fila = self._interfaz.ventanas.obtener_valores_fila_treeview('tvw_productos_manual', fila)

            valores = [valores_fila[1], valores_fila[2], valores_fila[5]]  # producto, precio linea
            datos_tabla.append(valores)

        tabla = crear_tabla_texto(datos_tabla)
        pyperclip.copy(tabla)

    def _agregar_especicificaciones(self):
        ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(titulo='Agregar especificacion')
        instancia = AgregarEspecificaciones(ventana, self._modelo.base_de_datos)
        ventana.wait_window()
        especificaciones = instancia.especificaciones_texto
        if especificaciones:
            comentario_original = self._interfaz.ventanas.obtener_input_componente('txt_comentario_manual')
            nuevo_comentario = ''

            if comentario_original != '':

                nuevo_comentario = f'{comentario_original}' \
                                   f'{especificaciones}'

            if comentario_original == '':
                nuevo_comentario = f'{especificaciones}'
                nuevo_comentario = nuevo_comentario.strip()

            self._interfaz.ventanas.insertar_input_componente('txt_comentario_manual', nuevo_comentario)

    def _activar_chk_pieza(self):
        if self._tabla_manual_con_seleccion_valida():

            self._interfaz.ventanas.cambiar_estado_checkbutton('chk_monto', 'deseleccionado')
            self._interfaz.ventanas.cambiar_estado_checkbutton('chk_pieza', 'seleccionado')

            self._selecionar_producto_tabla_manual()

    def _activar_chk_monto(self):
        if self._tabla_manual_con_seleccion_valida():
            self._interfaz.ventanas.cambiar_estado_checkbutton('chk_pieza', 'deseleccionado')
            self._interfaz.ventanas.cambiar_estado_checkbutton('chk_monto', 'seleccionado')

            precio_unidad = self._info_partida_seleccionada.get('SalePriceWithTaxes', 10)
            self._interfaz.ventanas.insertar_input_componente('tbx_cantidad_manual', precio_unidad)

            self._selecionar_producto_tabla_manual()

    def _obtener_valores_controles(self):

        equivalencia = self._interfaz.ventanas.obtener_input_componente('tbx_equivalencia_manual')
        equivalencia_decimal = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

        return {
            'valor_chk_monto': self._interfaz.ventanas.obtener_input_componente('chk_monto'),
            'valor_chk_pieza': self._interfaz.ventanas.obtener_input_componente('chk_pieza'),
            'cantidad': self._obtener_cantidad_partida_manual(),
            'equivalencia': equivalencia_decimal
        }

    # ---------------------------------------------------------------------
    # Funciones auxiliares relacionados con las ofertas
    # ---------------------------------------------------------------------

    def _buscar_ofertas(self, rellenar_tabla=True):

        if not self._modelo.consulta_productos_ofertados:
            self._modelo.buscar_productos_ofertados_cliente()

        if rellenar_tabla:
            self._modelo.consulta_productos = self._modelo.consulta_productos_ofertados_btn
            self._rellenar_tabla_productos_manual(self._modelo.consulta_productos)
            self._colorear_productos_ofertados()

    def _colorear_productos_ofertados(self):
        filas = self._interfaz.ventanas.obtener_filas_treeview('tvw_productos_manual')
        if not filas:
            return

        for fila in filas:
            if not fila:
                continue

            valores_fila = self._interfaz.ventanas.procesar_fila_treeview('tvw_productos_manual', fila)
            product_id = valores_fila['ProductID']
            producto = str(valores_fila['Descripción'])

            if product_id in self._modelo.products_ids_ofertados:
                producto_actualizado = self._actualizar_nombre_producto_ofertado(producto, product_id)
                valores_fila['Descripción'] = producto_actualizado
                precio = self._interfaz.utilerias.redondear_valor_cantidad_a_decimal(valores_fila['Precio'])
                valores_fila['Precio'] = precio
                self._interfaz.ventanas.actualizar_fila_treeview_diccionario('tvw_productos_manual', fila, valores_fila)
                self._interfaz.ventanas.colorear_fila_seleccionada_treeview('tvw_productos_manual', fila,
                                                                            color='warning')

    def _actualizar_nombre_producto_ofertado(self, producto, product_id):
        def _remover_texto_oferta(producto):
            return re.sub(r"\s*\(OFE\).*", "", producto)

        # Buscar el producto ofertado por ID (copiando solo los campos necesarios)
        for reg in self._modelo.consulta_productos_ofertados:
            if int(reg['ProductID']) == int(product_id):
                sale_price_before = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(
                    reg['SalePriceBefore'])  # Copia segura
                tax_type_id = int(reg['TaxTypeID'])  # Copia segura
                clave_unidad = reg['ClaveUnidad']
                clave_sat = reg['ClaveProdServ']
                break
        else:
            return producto  # No encontrado

        # Calcular totales sin modificar referencias originales

        cantidad = 1
        totales_partida = self._modelo.utilerias.calcular_totales_partida(
            precio=sale_price_before,
            tipo_impuesto_id=tax_type_id,
            cantidad=cantidad,
            clave_unidad=clave_unidad,
            clave_sat=clave_sat
        )
        producto = _remover_texto_oferta(producto)
        sale_price_before_with_taxes = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(
            totales_partida.get('total', sale_price_before))
        nombre_producto = f"{producto} (OFE) {sale_price_before_with_taxes}"
        return nombre_producto

    # ---------------------------------------------------------------------
    # Funciones auxiliares relacionados con la captura de partidas en el documento
    # ---------------------------------------------------------------------

    def _agregar_partida_por_clave(self):
        clave = self._interfaz.ventanas.obtener_input_componente('tbx_clave')
        if self._agregando_producto:
            return

        try:
            self._agregando_producto = True

            if not self._modelo.utilerias.es_codigo_barras(clave):
                self._modelo.mensajes_de_error(7)
                return

            valores_clave = self._modelo.utilerias.validar_codigo_barras(clave)
            codigo_barras = valores_clave.get('clave', None)
            cantidad = valores_clave.get('cantidad', 1)
            cantidad = self._modelo.utilerias.convertir_valor_a_decimal(cantidad)

            consulta_producto = self._modelo.buscar_productos(codigo_barras, 'Clave')

            if not consulta_producto:
                self._modelo.mensajes_de_error(8)
                return

            product_id = self._modelo.obtener_product_ids_consulta(consulta_producto)

            if not product_id:
                self._modelo.mensajes_de_error(11)
                return

            info_producto = self._modelo.buscar_info_productos_por_ids(product_id, no_en_venta=True)

            if not info_producto:
                existencia = self._modelo.obtener_existencia_producto(product_id)

                if not existencia:
                    self._modelo.mensajes_de_error(11)
                    return

                self._modelo.mensajes_de_error(9)
                return

            disponible_a_venta = info_producto[0]['AvailableForSale']
            if disponible_a_venta == 0:
                self._modelo.mensajes_de_error(10)
                return

            # permite que al capturar por clave se respeten los casos tipo reja de huevo
            equivalencia_especial = self._modelo.utilerias.equivalencias_productos_especiales(product_id)
            if equivalencia_especial:
                cantidad = equivalencia_especial[1]

            partida = self._modelo.utilerias.crear_partida(info_producto[0], cantidad)

            unidad_cayal = 0 if info_producto[0]['ClaveUnidad'] == 'KGM' else 1 # Del control de captura manual
            partida['Comments'] = ''

            self._modelo.agregar_partida_tabla(partida, document_item_id=0, tipo_captura=0, unidad_cayal=unidad_cayal,
                                               monto_cayal=0)
        finally:
            self._agregando_producto = False
            self._interfaz.ventanas.limpiar_componentes('tbx_clave')
            self._interfaz.ventanas.enfocar_componente('tbx_clave')

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

                partida = self._modelo.utilerias.crear_partida(info_partida_seleccionada, cantidad)

                chk_pieza = self._interfaz.ventanas.obtener_input_componente('chk_pieza')
                chk_monto = self._interfaz.ventanas.obtener_input_componente('chk_monto')
                comentarios = self._interfaz.ventanas.obtener_input_componente('txt_comentario_manual')

                partida['Comments'] = comentarios

                if chk_pieza == 1 and partida['CayalPiece'] % 1 != 0:
                    self._interfaz.ventanas.mostrar_mensaje('La cantidad de piezas deben ser valores no fraccionarios.')
                    return

                self._modelo.agregar_partida_tabla(partida, document_item_id=0, tipo_captura=1, unidad_cayal=chk_pieza,
                                                   monto_cayal=chk_monto)
            finally:
                self._agregando_producto = False
                self._interfaz.ventanas.insertar_input_componente('tbx_cantidad_manual', 1)
                self._interfaz.ventanas.limpiar_componentes('txt_comentario_manual')
                self._interfaz.ventanas.limpiar_componentes('tbx_buscar_manual')
                self._interfaz.ventanas.enfocar_componente('tbx_buscar_manual')

    def _buscar_productos_manualmente(self, event=None):

        tipo_busqueda = self._interfaz.ventanas.obtener_input_componente('cbx_tipo_busqueda_manual')
        termino_buscado = self._interfaz.ventanas.obtener_input_componente('tbx_buscar_manual')

        consulta = self._modelo.buscar_productos(termino_buscado, tipo_busqueda)

        if not consulta:
            self._modelo.mensajes_de_error(6, self._master)
            self._limpiar_controles_captura_manual()
            self._interfaz.ventanas.enfocar_componente('tbx_buscar_manual')
            self._interfaz.ventanas.insertar_input_componente('tbx_cantidad_manual', 1.00)
            return

        ids_productos = self._modelo.obtener_product_ids_consulta(consulta)
        consulta_productos = self._modelo.buscar_info_productos_por_ids(ids_productos)

        consulta_productos_impuestos = self._modelo.agregar_impuestos_productos(consulta_productos)

        self._modelo.consulta_productos = consulta_productos_impuestos
        self._rellenar_tabla_productos_manual(consulta_productos_impuestos)

    def _configurar_forma_manual_segun_producto(self, info_producto):

        def _insertar_equivalencia(equivalencia):

            equivalencia = str(equivalencia)
            equivalencia_decimal = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

            self._interfaz.ventanas.desbloquear_componente('tbx_equivalencia_manual')
            self._interfaz.ventanas.insertar_input_componente('tbx_equivalencia_manual', equivalencia_decimal)
            self._interfaz.ventanas.bloquear_componente('tbx_equivalencia_manual')

            return equivalencia_decimal

        clave_unidad = info_producto.get('ClaveUnidad', 'H87')

        equivalencia = info_producto.get('Equivalencia', 0.0)
        equivalencia_decimal = _insertar_equivalencia(equivalencia)

        if equivalencia_decimal == 0:

            if clave_unidad == 'KGM':
                self._interfaz.ventanas.cambiar_estado_checkbutton('chk_pieza', 'deseleccionado')

            if clave_unidad != 'KGM':
                self._interfaz.ventanas.cambiar_estado_checkbutton('chk_monto', 'deseleccionado')
                self._interfaz.ventanas.cambiar_estado_checkbutton('chk_pieza', 'seleccionado')
        else:
            self._interfaz.ventanas.cambiar_estado_checkbutton('chk_monto', 'deseleccionado')
            self._interfaz.ventanas.cambiar_estado_checkbutton('chk_pieza', 'deseleccionado')

    def _rellenar_tabla_productos_manual(self, consulta_productos):

        registros_tabla = []
        tabla = self._interfaz.ventanas.componentes_forma['tvw_productos_manual']

        for producto in consulta_productos:

            _producto = {
                'ProductKey': producto['ProductKey'],
                'ProductName': producto['ProductName'],
                'SalePriceWithTaxes': self._modelo.utilerias.redondear_valor_cantidad_a_decimal(
                    producto['SalePriceWithTaxes']),
                'ProductID': producto['ProductID'],
                'ClaveUnidad': producto['ClaveUnidad'],
                'Category1': producto['Category1']
            }

            registros_tabla.append(_producto)

        self._interfaz.ventanas.rellenar_treeview(tabla, self._interfaz.crear_columnas_tabla_manual(), registros_tabla)
        self._colorear_productos_ofertados()

        if self._interfaz.ventanas.numero_filas_treeview('tvw_productos_manual') == 1:
            self._interfaz.ventanas.seleccionar_fila_treeview('tvw_productos_manual', 1)

    def _calcular_valores_partida(self, info_producto):

        def calcular_cantidad_real(tipo_calculo, equivalencia, cantidad):

            if tipo_calculo == 'Equivalencia':
                return cantidad * equivalencia

            if tipo_calculo in ('Unidad', 'Monto'):
                return cantidad

        def _actualizar_clave_producto_manual():
            seleccion = self._interfaz.ventanas.obtener_seleccion_filas_treeview('tvw_productos_manual')
            if not seleccion:
                return

            for fila in seleccion:
                valores_fila = self._interfaz.ventanas.procesar_fila_treeview('tvw_productos_manual', fila)
                texto = f"CLAVE:{valores_fila['Código']}"
                self._interfaz.ventanas.insertar_input_componente('lbl_clave_manual', texto)

        def _actualizar_lbl_total_manual_moneda(total_decimal):
            total_moneda = self._modelo.utilerias.convertir_decimal_a_moneda(total_decimal)
            self._interfaz.ventanas.insertar_input_componente('lbl_monto_manual', total_moneda)

        def _determinar_tipo_calculo_partida_manual(info_producto):

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

                if not self._modelo.utilerias.es_numero_entero(cantidad):
                    self._interfaz.ventanas.insertar_input_componente('tbx_cantidad_manual', 1)

                if valor_chk_pieza == 0:
                    self._interfaz.ventanas.cambiar_estado_checkbutton('chk_pieza', 'seleccionado')

                if valor_chk_monto == 1:
                    self._interfaz.ventanas.cambiar_estado_checkbutton('chk_monto', 'deseleccionado')
                    self._modelo.mensajes_de_error(4, self._master)

                if equivalencia == 0:
                    return 'Unidad'

                if equivalencia != 0:
                    return 'Equivalencia'

            if clave_unidad == 'KGM':

                if valor_chk_pieza == 1 and equivalencia == 0:
                    self._modelo.mensajes_de_error(3, self._master)
                    self._interfaz.ventanas.cambiar_estado_checkbutton('chk_pieza', 'deseleccionado')
                    return 'Error'

                if valor_chk_monto == 1 and cantidad == 0:
                    self._modelo.mensajes_de_error(0, self._master)
                    self._interfaz.ventanas.cambiar_estado_checkbutton('chk_monto', 'deseleccionado')
                    return 'Error'

                if equivalencia != 0:
                    if valor_chk_monto == 1 and valor_chk_pieza == 1:
                        self._interfaz.ventanas.cambiar_estado_checkbutton('chk_monto', 'deseleccionado')
                        self._interfaz.ventanas.cambiar_estado_checkbutton('chk_pieza', 'deseleccionado')
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

        tipo_calculo = _determinar_tipo_calculo_partida_manual(info_producto)
        cantidad_piezas = 0
        total = 0
        cantidad_real_decimal = 0

        if tipo_calculo != 'Error':
            valores_controles = self._obtener_valores_controles()

            precio_con_impuestos = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(info_producto.get('SalePriceWithTaxes', 0.0))

            cantidad = valores_controles['cantidad']
            cantidad_piezas = cantidad
            cantidad_decimal = self._modelo.utilerias.convertir_valor_a_decimal(cantidad)

            equivalencia = valores_controles['equivalencia']
            equivalencia_decimal = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

            cantidad_real_decimal = calcular_cantidad_real(tipo_calculo, equivalencia_decimal, cantidad_decimal)

            if tipo_calculo == 'Equivalencia':
                if not self._modelo.utilerias.es_numero_entero(cantidad_decimal):
                    cantidad_decimal = self._modelo.utilerias.redondear_numero_a_entero(cantidad_decimal)
                    self._modelo.ventanas.insertar_input_componente('tbx_cantidad_manual', cantidad_decimal)
                total = cantidad_real_decimal * precio_con_impuestos

            if tipo_calculo == 'Unidad':
                total = cantidad_real_decimal * precio_con_impuestos

            if tipo_calculo == 'Monto':
                total = cantidad
                cantidad = total / precio_con_impuestos

                cantidad_real_decimal = self._modelo.utilerias.convertir_valor_a_decimal(cantidad)

        _actualizar_lbl_total_manual_moneda(total)
        texto = self._modelo.crear_texto_existencia_producto(info_producto)
        self._modelo.ventanas.insertar_input_componente('lbl_existencia_manual', texto)

        unidad = info_producto.get('Unit', 'PIEZA')
        product_id = int(info_producto.get('ProductID', 0))

        texto_cantidad = self._modelo.crear_texto_cantidad_producto(cantidad_real_decimal, unidad, product_id)
        self._modelo.ventanas.insertar_input_componente('lbl_cantidad_manual', texto_cantidad)
        _actualizar_clave_producto_manual()

        return {'cantidad': cantidad_real_decimal, 'cantidad_piezas': cantidad_piezas, 'total': total}

    def _limpiar_controles_captura_manual(self):
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
        self._interfaz.ventanas.limpiar_componentes(componentes)
        self._interfaz.ventanas.enfocar_componente('tbx_buscar_manual')

    def _obtener_cantidad_partida_manual(self):
        cantidad = self._interfaz.ventanas.obtener_input_componente('tbx_cantidad_manual')

        if not cantidad or not self._modelo.utilerias.es_cantidad(cantidad):
            return self._modelo.utilerias.redondear_valor_cantidad_a_decimal(0)

        cantidad_decimal = self._modelo.utilerias.convertir_valor_a_decimal(cantidad)

        return self._modelo.utilerias.redondear_valor_cantidad_a_decimal(1) if cantidad_decimal <= 0 else cantidad_decimal

    def _selecionar_producto_tabla_manual(self, configurar_forma=None):

        def _obtener_cantidad_manual_partida():
            cantidad = self._interfaz.ventanas.obtener_input_componente('tbx_cantidad_manual')

            if not cantidad or not self._interfaz.utilerias.es_cantidad(cantidad):
                return self._interfaz.utilerias.convertir_valor_a_decimal(0)

            cantidad_decimal = self._interfaz.utilerias.convertir_valor_a_decimal(cantidad)

            return self._interfaz.utilerias.redondear_valor_cantidad_a_decimal(
                1) if cantidad_decimal <= 0 else cantidad_decimal

        if self._procesando_seleccion:
            return

        self._procesando_seleccion = True

        try:
            fila = self._tabla_manual_con_seleccion_valida()
            if not fila:
                return

            valores = self._interfaz.ventanas.obtener_valores_fila_treeview('tvw_productos_manual', fila)

            product_id = int(valores[3])

            info_producto = copy.deepcopy(self._modelo.buscar_informacion_producto(product_id))

            if info_producto:
                self._product_id = product_id

                if configurar_forma:
                    self._configurar_forma_manual_segun_producto(info_producto)

                cantidad = _obtener_cantidad_manual_partida()
                self._interfaz.ventanas.insertar_input_componente('tbx_cantidad_manual', cantidad)

                self._product_id = product_id
                self._calcular_valores_partida(info_producto)
                self._info_partida_seleccionada = info_producto

        finally:
            self._procesando_seleccion = False

    def _tabla_manual_con_seleccion_valida(self):
        if self._interfaz.ventanas.numero_filas_treeview('tvw_productos_manual') == 0:
            return False

        fila = self._interfaz.ventanas.obtener_seleccion_filas_treeview('tvw_productos_manual')

        if not fila:
            return False

        if len(fila) > 1 or len(fila) < 1:
            return False

        return fila

    # ---------------------------------------------------------------------
    # Funciones auxiliares relacionados con la carga de partidas de un documento previamente capturado
    # ---------------------------------------------------------------------
    def _rellenar_desde_base_de_datos(self):
        if self._modelo.documento.document_id < 1:
            return

        # rellenar comentarios documento
        self._interfaz.ventanas.insertar_input_componente('txt_comentario_documento', self._modelo.documento.comments)

        # rellena la informacion relativa a las partidas
        partidas = self._modelo.obtener_partidas_pedido(self._modelo.documento.document_id)

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
            partida_procesada = self._modelo.utilerias.crear_partida(partida_copia)

            self._modelo.agregar_partida_tabla(partida_procesada, document_item_id=document_item_id, tipo_captura=tipo_captura,
                                               unidad_cayal=chk_pieza, monto_cayal=chk_monto)