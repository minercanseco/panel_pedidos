import copy
import datetime
import re
import tkinter as tk
import uuid

import pyperclip
import logging
import gzip, pickle
from pathlib import Path
from datetime import datetime


from herramientas.capturar_documento.herramientas_captura.agregar_epecificaciones import AgregarEspecificaciones
from herramientas.capturar_documento.ventana_captura.herramientas_facturas import HerramientasFacturas
from herramientas.capturar_documento.ventana_captura.herramientas_pedido import HerramientasPedido
from herramientas.capturar_documento.ventana_captura.herramientas_ticket import HerramientasTicket


class ControladorCaptura:
    def __init__(self, interfaz, modelo):

        self._interfaz = interfaz
        self._master = interfaz.master
        self._modelo = modelo

        self._interfaz.ventanas.situar_ventana_arriba(self._master)
        self._cargar_informacion_general()
        self._crear_notebook_herramientas() # dentro se determina el bloqueo de la ventana

        # ------------------------------------------------------
        # Banderas de procesos y variables auxiliares de captura
        # ------------------------------------------------------
        self._agregando_producto = False
        self._procesando_seleccion = False
        self._agregando_partida_tabla = False
        self._servicio_a_domicilio_agregado = False
        self._cargar_shortcuts = True
        self._info_partida_seleccionada = {}

        # ----------------------------------------------------
        # Acciones de inicialización relacionadas con captura
        # ----------------------------------------------------
        self._buscar_ofertas()
        self._interfaz.ventanas.enfocar_componente('tbx_clave')

        if self._modelo.module_id == 1687: # modulo de pedidos
            if self._modelo.documento.document_id > 0:  # capturado previamente
                self._rellenar_desde_base_de_datos()

            self._interfaz.ventanas.enfocar_componente('tbx_buscar_manual')

        if self._modelo.documento.document_id == 0:  # nueva captura
            self._agregar_servicio_a_domicilio()

        if self._cargar_shortcuts: # esto activa la edicion en pedidos capturados previamente candidatos a edicion
            self._configurar_pedido()
            self._cargar_eventos_componentes()

    # -------------------------------------------------------------------------
    # Funciones relacionadas a herramientas y eventos de componentes de captura
    # -------------------------------------------------------------------------
    def _crear_notebook_herramientas(self):

        cargar_shortcuts = False if self._determinar_bloqueo_ventana() else True

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
                    interfaz=self._interfaz,
                    cargar_shortcuts= cargar_shortcuts
                )

            if 'pedido' in frame_name and self._modelo.module_id == 1687:
                HerramientasPedido(
                    master=frame,
                    modelo=self._modelo,
                    interfaz=self._interfaz,
                    controlador=self,
                    cargar_shortcuts=cargar_shortcuts
                )

            if 'facturas' in frame_name and self._modelo.module_id in (21, 1400, 1319, 1316, 967):
                HerramientasFacturas(
                    master=frame,
                    modelo=self._modelo,
                    interfaz=self._interfaz,
                    cargar_shortcuts=cargar_shortcuts
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

    #--------------------------------------------------------------------
    # Funciones relacionadas a información del documento y estado inicial
    # -------------------------------------------------------------------
    def _cargar_informacion_general(self):
        self._cargar_direccion_cliente()
        self._cargar_nombre_cliente()
        self._cargar_informacion_crediticia()

        self._interfaz.ventanas.insertar_input_componente('lbl_captura', self._modelo.user_name)
        self._interfaz.ventanas.insertar_input_componente('lbl_folio', self._modelo.documento.docfolio)

        nombre_modulo = self._modelo.obtener_nombre_y_prefijo_segun_modulo()
        self._interfaz.ventanas.insertar_input_componente('lbl_modulo', nombre_modulo)

        if self._modelo.module_id in (21,1400,1319):
            self._modelo._rellenar_cbxs_fiscales()

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
                componente = self._interfaz.ventanas.componentes_forma.get(nombre, None)
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
                    monto_decimal = self._modelo.utilerias.convertir_valor_a_decimal(monto)
                    monto_moneda = self._modelo.utilerias.convertir_valor_a_decimal(monto_decimal)

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

    def _rellenar_cbxs_fiscales(self):


        # ==============
        # Helpers locales
        # ==============
        def _today_str():
            return datetime.now().strftime("%Y%m%d")

        def _cache_dir():
            base = Path.home() / ".cayal_cache"
            base.mkdir(parents=True, exist_ok=True)
            return base

        def _fiscales_cache_path(kind: str, day: str):
            return _cache_dir() / f"fiscales_{kind}_{day}.pkl.gz"

        def _cache_save_today(kind: str, data):
            day = _today_str()
            path = _fiscales_cache_path(kind, day)
            try:
                with gzip.open(path, "wb") as f:
                    pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
            except Exception:
                pass

        def _cache_load_if_today(kind: str):
            day = _today_str()
            path = _fiscales_cache_path(kind, day)
            try:
                if path.exists():
                    with gzip.open(path, "rb") as f:
                        return pickle.load(f)
            except Exception:
                return None
            return None

        def _cache_cleanup_not_today():
            day = _today_str()
            for f in _cache_dir().glob("fiscales_*.pkl.gz"):
                if not f.name.endswith(f"_{day}.pkl.gz"):
                    try:
                        f.unlink(missing_ok=True)
                    except Exception:
                        pass

        # ==============
        # Lógica principal
        # ==============
        if not hasattr(self, "_fiscales_cache_mem"):
            self._fiscales_cache_mem = {
                'metodopago': None,
                'formapago': None,
                'regimen': None,
                'usocfdi': None,
            }

        parametros = {
            'cbx_metodopago': ('metodopago', 'consulta_metodos_pago', self._modelo.obtener_metodos_de_pago),
            'cbx_formapago': ('formapago', 'consulta_formas_pago', self._modelo.obtener_formas_de_pago),
            'cbx_regimen': ('regimen', 'consulta_regimenes', self._modelo.obtener_regimenes_fiscales),
            'cbx_usocfdi': ('usocfdi', 'consulta_uso_cfdi', self._modelo.obtener_usos_de_cfdi),
        }

        datos_por_tipo = {}
        for componente, (tipo, attr_name, funcion) in parametros.items():
            lista = self._fiscales_cache_mem.get(tipo)
            if lista is None:
                lista = _cache_load_if_today(tipo)
                if lista is not None:
                    self._fiscales_cache_mem[tipo] = lista
                    setattr(self, attr_name, lista)
                    _cache_cleanup_not_today()

            if lista is None:
                lista = funcion()
                self._fiscales_cache_mem[tipo] = lista
                setattr(self, attr_name, lista)
                _cache_save_today(tipo, lista)
                _cache_cleanup_not_today()

            datos_por_tipo[tipo] = lista or []

        for componente, (tipo, attr_name, _) in parametros.items():
            lista = datos_por_tipo.get(tipo, [])
            valores_cbx = [reg.get('Value') for reg in lista]
            self._interfaz.ventanas.rellenar_cbx(componente, valores_cbx, sin_seleccione=True)

        parametros_cliente = {
            'cbx_metodopago': (datos_por_tipo['metodopago'], getattr(self._modelo.cliente, 'metodo_pago', None)),
            'cbx_formapago': (datos_por_tipo['formapago'], getattr(self._modelo.cliente, 'forma_pago', None)),
            'cbx_regimen': (datos_por_tipo['regimen'], getattr(self._modelo.cliente, 'company_type_name', None)),
            'cbx_usocfdi': (datos_por_tipo['usocfdi'], getattr(self._modelo.cliente, 'receptor_uso_cfdi', None)),
        }

        if getattr(self._modelo.documento, 'cfd_type_id', None) == 1 or getattr(self._modelo.cliente, 'cayal_customer_type_id',
                                                                        None) in (0, 1):
            self._interfaz.ventanas.insertar_input_componente('cbx_regimen', '616 - Sin obligaciones fiscales')
            self._interfaz.ventanas.insertar_input_componente('cbx_metodopago', 'PUE - Pago en una sola exhibición')
            self._interfaz.ventanas.insertar_input_componente('cbx_formapago', '01 - Efectivo')
            self._interfaz.ventanas.insertar_input_componente('cbx_usocfdi', 'S01 - Sin efectos fiscales.')
            for componente in parametros_cliente.keys():
                self._interfaz.ventanas.bloquear_componente(componente)
            return

        for componente, (lista, clave) in parametros_cliente.items():
            if not lista:
                continue
            seleccionado = None
            if componente != 'cbx_regimen' and clave is not None:
                _match = [reg.get('Value') for reg in lista if reg.get('Clave') == clave]
                if _match:
                    seleccionado = _match[0]
                    self._interfaz.ventanas.insertar_input_componente(componente, seleccionado)
                    if componente != 'cbx_formapago':
                        self._interfaz.ventanas.bloquear_componente(componente)
            if seleccionado is None and clave is not None:
                _match = [reg.get('Value') for reg in lista if reg.get('Value') == clave]
                if _match:
                    seleccionado = _match[0]
                    self._interfaz.ventanas.insertar_input_componente(componente, seleccionado)
                    self._interfaz.ventanas.bloquear_componente(componente)
            if componente == 'cbx_formapago':
                if getattr(self._modelo.cliente, 'forma_pago', None) == '99':
                    self._interfaz.ventanas.bloquear_componente(componente)

    def _asignar_folio(self, document_id=0, order_document_id=0):
        folio = self._modelo.obtener_folio_documento(document_id, order_document_id)

        self._modelo.documento.folio = folio
        doc_folio = f"{self._modelo.documento.prefix}{folio}"
        self._modelo.documento.doc_folio = doc_folio
        self._interfaz.ventanas.insertar_input_componente('lbl_folio', doc_folio)

    def _determinar_bloqueo_ventana(self):

        if self._modelo.documento.document_id == 0: #garantiza que las nuevas capturas no tengan bloqueo
            return False

        status = 'Bloqueado'
        motivo_bloqueo = 'Sin motivo'
        if self._modelo.module_id == 1687:
            status, motivo_bloqueo, bloquado_por = self._modelo.obtener_status_bloqueo_pedido(self._modelo.documento.document_id,
                                                                                self._modelo.user_id
                                                                                )

        if status == 'Bloqueado' or self._modelo.documento.cancelled_on:
            self._interfaz.ventanas.bloquear_forma('frame_herramientas')

            estilo_cancelado = {
                'foreground': 'white',
                'background': '#ff8000',
            }

            frames = ['frame_totales_manual', 'frame_totales', 'frame_herramientas']
            for nombre_frame in frames:
                frame = self._interfaz.ventanas.componentes_forma[nombre_frame]
                widgets = frame.winfo_children()
                for widget in widgets:
                    widget.config(**estilo_cancelado)

            self._interfaz.ventanas.mostrar_mensaje(f'El documento esta {status} debido a {motivo_bloqueo}')

            return True

        return False
    # -------------------------------------------------------------------------
    # Funciones auxiliares relacionados con la captura de partidas en el pedido
    # -------------------------------------------------------------------------
    def _configurar_pedido(self):
        if self._modelo.documento.document_id < 1:
            valores_pedido = {}
            valores_pedido['OrderTypeID'] = 1
            valores_pedido['CreatedBy'] = self._modelo.parametros.id_usuario
            valores_pedido['CreatedOn'] = datetime.now()
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
        equivalencia_decimal = self._modelo.utilerias.convertir_valor_a_decimal(equivalencia)

        return {
            'valor_chk_monto': self._interfaz.ventanas.obtener_input_componente('chk_monto'),
            'valor_chk_pieza': self._interfaz.ventanas.obtener_input_componente('chk_pieza'),
            'cantidad': self._obtener_cantidad_partida_manual(),
            'equivalencia': equivalencia_decimal
        }

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
            13: 'En el módulo de pedidos no se puede eliminar el servicio a domicilio manualmente.',
            14: 'La captura del producto no está permitida en el módulo de venta actual.',
            15: 'Con la captura de la partida excede el monto autorizado para este modulo.',
            16: 'Con la captura de la partida excede el monto de crédito autorizado.',
            17: 'La captura del documento ha conluido.'
        }

        self._interfaz.ventanas.mostrar_mensaje(mensajes[numero_mensaje], master)

    # --------------------------------------------------
    # Funciones auxiliares relacionados con las ofertas
    # --------------------------------------------------

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
                precio = self._modelo.utilerias.convertir_valor_a_decimal(valores_fila['Precio'])
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
                sale_price_before = self._modelo.utilerias.convertir_valor_a_decimal(
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
        sale_price_before_with_taxes = self._modelo.utilerias.convertir_valor_a_decimal(
            totales_partida.get('total', sale_price_before))
        sale_price_before_with_taxes = f"{sale_price_before_with_taxes:.2f}"
        nombre_producto = f"{producto} (OFE) {sale_price_before_with_taxes}"
        return nombre_producto

    # ----------------------------------------------------------------------------
    # Funciones auxiliares relacionados con la captura de partidas en el documento
    # ----------------------------------------------------------------------------

    def _agregar_partida_por_clave(self):
        clave = self._interfaz.ventanas.obtener_input_componente('tbx_clave')
        if self._agregando_producto:
            return

        try:
            self._agregando_producto = True

            if not self._modelo.utilerias.es_codigo_barras(clave):
                self.mensajes_de_error(7)
                return

            valores_clave = self._modelo.utilerias.validar_codigo_barras(clave)
            codigo_barras = valores_clave.get('clave', None)
            cantidad = valores_clave.get('cantidad', 1)
            cantidad = self._modelo.utilerias.convertir_valor_a_decimal(cantidad)

            consulta_producto = self._modelo.buscar_productos(codigo_barras, 'Clave')

            if not consulta_producto:
                self.mensajes_de_error(8)
                return

            product_id = self._modelo.obtener_product_ids_consulta(consulta_producto)

            if not product_id:
                self.mensajes_de_error(11)
                return

            info_producto = self._modelo.buscar_info_productos_por_ids(product_id, no_en_venta=True)

            if not info_producto:
                existencia = self._modelo.obtener_existencia_producto(product_id)

                if not existencia:
                    self.mensajes_de_error(11)
                    return

                self.mensajes_de_error(9)
                return

            disponible_a_venta = info_producto[0]['AvailableForSale']
            if disponible_a_venta == 0:
                self.mensajes_de_error(10)
                return

            # permite que al capturar por clave se respeten los casos tipo reja de huevo
            equivalencia_especial = self._modelo.utilerias.equivalencias_productos_especiales(product_id)
            if equivalencia_especial:
                cantidad = equivalencia_especial[1]

            partida = self._modelo.utilerias.crear_partida(info_producto[0], cantidad)

            unidad_cayal = 0 if info_producto[0]['ClaveUnidad'] == 'KGM' else 1 # Del control de captura manual
            partida['Comments'] = ''

            self._modelo._agregar_partida_tabla(partida, document_item_id=0, tipo_captura=0, unidad_cayal=unidad_cayal,
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

                self._agregar_partida_tabla(partida, document_item_id=0, tipo_captura=1, unidad_cayal=chk_pieza,
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
            self.mensajes_de_error(6, self._master)
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
            equivalencia_decimal = self._modelo.utilerias.convertir_valor_a_decimal(equivalencia)

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
            sale_price_before_with_taxes = self._modelo.utilerias.convertir_valor_a_decimal(
                producto['SalePriceWithTaxes'])
            sale_price_before_with_taxes = f"{sale_price_before_with_taxes:.2f}"

            _producto = {
                'ProductKey': producto['ProductKey'],
                'ProductName': producto['ProductName'],
                'SalePriceWithTaxes': sale_price_before_with_taxes,
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
                    self.mensajes_de_error(4, self._master)

                if equivalencia == 0:
                    return 'Unidad'

                if equivalencia != 0:
                    return 'Equivalencia'

            if clave_unidad == 'KGM':

                if valor_chk_pieza == 1 and equivalencia == 0:
                    self.mensajes_de_error(3, self._master)
                    self._interfaz.ventanas.cambiar_estado_checkbutton('chk_pieza', 'deseleccionado')
                    return 'Error'

                if valor_chk_monto == 1 and cantidad == 0:
                    self.mensajes_de_error(0, self._master)
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
                    self.mensajes_de_error(2, self._master)
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

            precio_con_impuestos = self._modelo.utilerias.convertir_valor_a_decimal(info_producto.get('SalePriceWithTaxes', 0.0))

            cantidad = valores_controles['cantidad']
            cantidad_piezas = cantidad
            cantidad_decimal = self._modelo.utilerias.convertir_valor_a_decimal(cantidad)

            equivalencia = valores_controles['equivalencia']
            equivalencia_decimal = self._modelo.utilerias.convertir_valor_a_decimal(equivalencia)

            cantidad_real_decimal = calcular_cantidad_real(tipo_calculo, equivalencia_decimal, cantidad_decimal)

            if tipo_calculo == 'Equivalencia':
                if not self._modelo.utilerias.es_numero_entero(cantidad_decimal):
                    cantidad_decimal = self._modelo.utilerias.convertir_valor_a_decimal(cantidad_decimal)
                    self._interfaz.ventanas.insertar_input_componente('tbx_cantidad_manual', cantidad_decimal)
                total = cantidad_real_decimal * precio_con_impuestos

            if tipo_calculo == 'Unidad':
                total = cantidad_real_decimal * precio_con_impuestos

            if tipo_calculo == 'Monto':
                total = cantidad
                cantidad = total / precio_con_impuestos

                cantidad_real_decimal = self._modelo.utilerias.convertir_valor_a_decimal(cantidad)

        _actualizar_lbl_total_manual_moneda(total)
        texto = self._modelo.crear_texto_existencia_producto(info_producto)
        self._interfaz.ventanas.insertar_input_componente('lbl_existencia_manual', texto)

        unidad = info_producto.get('Unit', 'PIEZA')
        product_id = int(info_producto.get('ProductID', 0))

        texto_cantidad = self._modelo.crear_texto_cantidad_producto(cantidad_real_decimal, unidad, product_id)
        self._interfaz.ventanas.insertar_input_componente('lbl_cantidad_manual', texto_cantidad)
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
            return self._modelo.utilerias.convertir_valor_a_decimal(0)

        cantidad_decimal = self._modelo.utilerias.convertir_valor_a_decimal(cantidad)

        return self._modelo.utilerias.convertir_valor_a_decimal(1) if cantidad_decimal <= 0 else cantidad_decimal

    def _selecionar_producto_tabla_manual(self, configurar_forma=None):

        def _obtener_cantidad_manual_partida():
            cantidad = self._interfaz.ventanas.obtener_input_componente('tbx_cantidad_manual')

            if not cantidad or not self._modelo.utilerias.es_cantidad(cantidad):
                return self._modelo.utilerias.convertir_valor_a_decimal(0)

            cantidad_decimal = self._modelo.utilerias.convertir_valor_a_decimal(cantidad)

            return self._modelo.utilerias.convertir_valor_a_decimal(
                1) if cantidad_decimal <= 0 else cantidad_decimal

        if self._procesando_seleccion:
            return

        try:
            self._procesando_seleccion = True
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

    def _filtrar_productos_no_permitidos(self, partida):

        if self._modelo.module_id == 1692: # restriccion por modulo vales
            linea = partida.get('Category1', '')
            if linea not in self._modelo.LINEAS_PRODUCTOS_PERMITIDOS_VALES:
                self.mensajes_de_error(14)
                return

        return partida

    def actualizar_totales_documento(self):

        impuestos_acumulado = 0
        ieps_acumulado = 0
        iva_acumulado = 0
        sub_total_acumulado = 0

        for producto in self._modelo.documento.items:
            ieps_acumulado += producto.get('ieps', 0)
            iva_acumulado += producto.get('iva', 0)
            impuestos_acumulado += producto.get('impuestos',0)
            sub_total_acumulado += producto.get('subtotal', 0)

        totales_documento = self._modelo.impuestos.doc_totales_por_documento(self._modelo.documento.items)
        self._modelo.documento.total = totales_documento['total_doc']


        total_documento_moneda = self._modelo.utilerias.convertir_decimal_a_moneda(self._modelo.documento.total)
        self._interfaz.ventanas.insertar_input_componente('lbl_total', total_documento_moneda)

        self._modelo.documento.total_tax = impuestos_acumulado
        self._modelo.documento.subtotal = sub_total_acumulado
        self._modelo.documento.ieps = ieps_acumulado
        self._modelo.documento.iva = iva_acumulado

        self._interfaz.ventanas.insertar_input_componente('lbl_articulos',
                                                 self._interfaz.ventanas.numero_filas_treeview('tvw_productos'))

        if self._modelo.cliente.cayal_customer_type_id in (1,2) and self._modelo.cliente.credit_block == 0:
            debe = self._modelo.cliente.debt
            debe = self._modelo.utilerias.convertir_valor_a_decimal(debe)

            debe += self._modelo.documento.total
            debe_moneda = self._modelo.utilerias.convertir_decimal_a_moneda(debe)
            self._interfaz.ventanas.insertar_input_componente('lbl_debe', debe_moneda)

            disponible = self._modelo.cliente.remaining_credit
            disponible = self._modelo.utilerias.convertir_valor_a_decimal(disponible)

            disponible = disponible - self._modelo.documento.total
            excedido = abs(disponible) if disponible < 0 else 0

            disponible = 0 if disponible <= 0 else disponible
            self._modelo.documento.credit_document_available = 0 if disponible == 0 else 1

            disponible_moneda = self._modelo.utilerias.convertir_decimal_a_moneda(disponible)
            self._interfaz.ventanas.insertar_input_componente('lbl_restante', disponible_moneda)

            self._modelo.documento.credit_exceeded_amount = excedido

    def _validar_restriccion_por_monto(self, partida, tipo_captura):
        total = self._modelo.documento.total
        total_partida = partida.get('total', 0)
        total_real = total_partida + total

        if self._modelo.module_id in (1400,21,1319):
            if total_real >= 2000 and self._modelo.documento.cfd_type_id == 0 and self._modelo.documento.forma_pago == '01':
                respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                    "Con la captura de la partida excede $2000.00, que es el monto máximo para facturas capturadas en efectivo. "
                    "¿Desea continuar?"
                )
                if not respuesta:
                    return

        # Si ya está completamente cerrado (2), no hacer nada
        if self._modelo.module_id == 1692 and self._modelo.documento.finish_document == 2:
            # IMPORTANTE: devolver True para no bloquear flujos posteriores
            return True

        if self._modelo.module_id == 1692 and self._modelo.documento.finish_document == 0:
            # restricción por vales
            if total_real > self._modelo.cliente.coupons_mount:

                clave_unidad_partida = partida.get('ClaveUnidad', 'KGM')
                if clave_unidad_partida != 'KGM':
                    self._interfaz.ventanas.mostrar_mensaje(
                        "Con la captura de la partida excede el monto autorizado para este módulo. "
                        "La partida no se puede dividir debido a que su unidad es distinta de Kilo."
                    )
                    return

                respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                    "Con la captura de la partida excede el monto autorizado para este módulo. "
                    "¿Desea capturar la diferencia en un folio Minisuper?"
                )
                if not respuesta:
                    return

                # Calcula cuánto se puede quedar en el doc relacionado (finish_document == 0)
                monto_limite = total_real - self._modelo.cliente.coupons_mount
                partida_anterior, partida_nueva = self._modelo.dividir_partida(partida, monto_limite)

                # Etiquetas de captura
                partida_anterior['TipoCaptura'] = tipo_captura
                partida_nueva['TipoCaptura'] = tipo_captura

                # 1) INSERTA PRIMERO LA PARTE "PERMITIDA" EN EL DOCUMENTO RELACIONADO
                #    Evitar revalidación: usa document_item_id != 0 para saltar validar_restriccion_por_monto dentro de agregar_partida_tabla
                self._modelo._agregar_partida_tabla(partida_anterior, document_item_id=-1, tipo_captura=tipo_captura)

                # 2) AHORA sí marca como "finish_document = 1" y crea el folio Minisúper si no existe
                self._modelo.documento.finish_document = 1

                if not getattr(self._modelo.documento, 'adicional_document_id', 0):
                    folio_document_id = self._modelo.crear_cabecera_documento(1400, 'FG')  # fac minisuper
                    self._modelo.documento.adicional_document_id = folio_document_id

                # 3) Inserta la parte restante en el folio Minisúper
                #    Puedes ir directo a items (sin tabla) o usar la tabla con document_item_id != 0 para saltar validación.
                self._modelo._agregar_partida_items_documento(partida_nueva)
                # o, si quieres que aparezca en el treeview de la UI:
                # self.agregar_partida_tabla(partida_nueva, document_item_id=-1, tipo_captura=tipo_captura)

                return  # corta el flujo original (ya insertamos ambas partes)

        # crédito empleado Cayal ruta 7
        if self._modelo.cliente.zone_id == 1040 and self._modelo.module_id in (1400, 21, 1319):
            if total_real > self._modelo.cliente.remaining_credit and self._modelo.documento.credit_document_available == 1:

                respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                    "Con la captura de la partida excede el monto autorizado para este módulo. "
                    "¿Desea continuar?"
                )
                self._modelo.documento.credit_document_available = 0
                if not respuesta:
                    return

        return True

    def _agregar_partida_tabla(self, partida, document_item_id, tipo_captura, unidad_cayal=0, monto_cayal=0):

        if self._modelo.documento.finish_document == 2:
            self.mensajes_de_error(17)
            return

        if document_item_id == 0:
            if not self._filtrar_productos_no_permitidos(partida):
                return

            if not self._validar_restriccion_por_monto(partida, tipo_captura):
                return

        if not self._agregando_partida_tabla:
            try:
                self._agregando_partida_tabla = True

                cantidad = self._modelo.utilerias.convertir_valor_a_decimal(partida['cantidad'])
                comments = partida.get('Comments', '')
                producto = partida.get('ProductName', '')
                partida['TipoCaptura'] = tipo_captura
                partida['DocumentItemID'] = document_item_id
                partida['CayalAmount'] = monto_cayal
                partida['uuid'] = uuid.uuid4()

                if self._modelo.documento.document_id > 0 and document_item_id == 0:
                    partida['ItemProductionStatusModified'] = 1
                    partida['CreatedBy'] = self._modelo.user_id

                    comentario = f'AGREGADO POR {self._modelo.user_name}'
                    self._modelo.agregar_partida_items_documento_extra(partida, 'agregar', comentario, partida['uuid'])

                # en caso que el modulo se use para capturar otro tipo de documentos que no sean pedidos el valor por defecto
                # debe ser 0 y para las subsecuentes modificaciones segun aplique
                # en funcion del diccionario modificaciones_pedido
                item_production_status_modified = partida.get('ItemProductionStatusModified', 0)
                partida['ItemProductionStatusModified'] = item_production_status_modified
                partida['CreatedBy'] = self._modelo.user_id

                cantidad_piezas = 0 if unidad_cayal == 0 else self._modelo.utilerias.convertir_valor_a_decimal(partida['CayalPiece'])

                equivalencia = self._modelo.obtener_equivalencia(partida.get('ProductID', 0))
                equivalencia = 0 if not equivalencia else equivalencia
                equivalencia_decimal = self._modelo.utilerias.convertir_valor_a_decimal(equivalencia)

                if equivalencia_decimal > 0 and unidad_cayal == 1:
                    cantidad_piezas = int((cantidad/equivalencia_decimal))

                funcion = self._modelo.utilerias.convertir_valor_a_decimal

                partida['CayalPiece'] = cantidad_piezas
                cantidad = f"{cantidad:.3f}" if partida['clave_unidad'] == 'KGM' else f"{cantidad:.2f}"

                partida_tabla = (cantidad,
                                 cantidad_piezas,
                                 partida['ProductKey'],
                                 producto,
                                 partida['Unit'],
                                 f"{funcion(partida['precio']):.2f}",
                                 f"{funcion(partida['subtotal']):.2f}",
                                 f"{funcion(partida['impuestos']):.2f}",
                                 f"{funcion(partida['total']):.2f}",
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
                    if self._servicio_a_domicilio_agregado:
                        return

                    self._servicio_a_domicilio_agregado = True

                # agregar tipo de captura
                tabla_captura = self._interfaz.ventanas.componentes_forma['tvw_productos']
                self._interfaz.ventanas.insertar_fila_treeview(tabla_captura, partida_tabla, al_principio=True)

                self._agregar_partida_items_documento(partida)
                self.actualizar_totales_documento()

                # si aplica remueve el servicio a domicilio
                if self._modelo.module_id == 1687 and self._servicio_a_domicilio_agregado == True:
                    if self._modelo.documento.total - self._modelo.documento.delivery_cost >= 200:
                        self.remover_servicio_a_domicilio()

            finally:
                self._agregando_partida_tabla = False

    def remover_servicio_a_domicilio(self):
        self._servicio_a_domicilio_agregado = False
        self._modelo.remover_partida_items_documento(5606)
        self._remover_product_id_tabla(5606)
        self.actualizar_totales_documento()

    def _remover_product_id_tabla(self, product_id):
        filas = self._interfaz.ventanas.obtener_filas_treeview('tvw_productos')

        for fila in filas:
            valores = self._interfaz.ventanas.procesar_fila_treeview('tvw_productos', fila)
            product_id_tabla = int(valores['ProductID'])
            if product_id_tabla == product_id:
                self._interfaz.ventanas.remover_fila_treeview('tvw_productos', fila)

    def _agregar_partida_items_documento(self, partida):

        self._modelo.documento.items.append(partida)

        if self._modelo.module_id != 1687: # si no es el modulo de pedidos inserta la partida
            if self._modelo.documento.document_id == 0:
                document_id = self._modelo.crear_cabecera_documento()
                self._modelo.documento.document_id = document_id

                self._asignar_folio(document_id)

                self._modelo.crear_cabecera_documento_relacionado()

            if self._modelo.documento.finish_document != 1:

                # agregamos partida al documento de venta
                parametros = (
                    self._modelo.documento.document_id,
                    partida['ProductID'],
                    2,  # depot id minisuper
                    partida['cantidad'],
                    partida['precio'],
                    0,  # costo
                    partida['subtotal'],
                    partida['TipoCaptura'],
                    self._modelo.module_id
                )
                self._modelo.insertar_partida_documento(parametros)

        if self._modelo.module_id == 1692: #modulo de vales

            if self._modelo.documento.finish_document == 0: # aplica para el módulo de vales

                # agregamos partida al documento de salida
                costo = self._modelo.utilerias.convertir_valor_a_decimal(partida['CostPrice'])
                cantidad = self._modelo.utilerias.convertir_valor_a_decimal(partida['cantidad'])
                total = costo * cantidad

                parametros = (
                    self._modelo.documento.destination_document_id,
                    partida['ProductID'],
                    2,  # depot id minisuper
                    cantidad,
                    0,
                    costo,  # costo
                    total,
                    partida['TipoCaptura'],
                    203 # salida de inventario
                )
                self._modelo.insertar_partida_documento(parametros)

            if self._modelo.documento.finish_document == 1: # aplica para el restante del módulo vales
                # agregamos partida al documento de venta folio minisuper
                parametros = (
                    self._modelo.documento.adicional_document_id,
                    partida['ProductID'],
                    2,  # depot id minisuper
                    partida['cantidad'],
                    partida['precio'],
                    0,  # costo
                    partida['subtotal'],
                    partida['TipoCaptura'],
                    self._modelo.module_id
                )
                self._modelo.insertar_partida_documento(parametros)

                self._modelo.documento.finish_document = 2 # bandera de cierre final del documento

    def _agregar_servicio_a_domicilio(self):

        def insertar_partida_servicio_a_domicilio():
            delivery_cost_iva = self._modelo.documento.delivery_cost
            self.costo_servicio_a_domicilio = self._modelo.utilerias.convertir_valor_a_decimal(delivery_cost_iva)
            delivery_cost = self._modelo.utilerias.calcular_monto_sin_iva(delivery_cost_iva)

            info_producto = self._modelo.buscar_info_productos_por_ids(5606, no_en_venta=True)

            if info_producto:
                info_producto = info_producto[0]

                info_producto['SalePrice'] = delivery_cost

                partida = self._modelo.utilerias.crear_partida(info_producto, cantidad=1)

                self.partida_servicio_domicilio = partida
                partida['Comments'] = ''
                self._agregar_partida_tabla(partida, document_item_id=0, tipo_captura=2, unidad_cayal=1, monto_cayal=0)

                self.servicio_a_domicilio_agregado = True

        # servicio a domicilio solo aplica para pedidos
        if self._modelo.module_id != 1687:
            return

        # servicio a domicilio no aplica para anexos o cambios 2 y 3 solo para pedidos 1
        if self._modelo.module_id == 1687:
            parametros_pedido = self._modelo.documento.order_parameters
            order_type_id = int(parametros_pedido.get('OrderTypeID', 1))

            # anexos o cambios 2 y 3
            if order_type_id in (2,3):
                return

        # no se debe agregar mas de una partida de servicio a domicilio
        existe_servicio_a_domicilio = [producto for producto in self._modelo.documento.items
                                       if int(producto['ProductID']) == 5606]

        if existe_servicio_a_domicilio:
            return

        # insertamos el servicio a domicilio
        insertar_partida_servicio_a_domicilio()

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

            self._agregar_partida_tabla(partida_procesada, document_item_id=document_item_id, tipo_captura=tipo_captura,
                                        unidad_cayal=chk_pieza, monto_cayal=chk_monto)
