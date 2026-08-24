import copy
import gzip, pickle
import uuid
from pathlib import Path
import re
from datetime import datetime

import pyperclip
import logging
import ttkbootstrap as ttk

from herramientas.capturar_documento.herramientas.agregar_epecificaciones import AgregarEspecificaciones
from herramientas.capturar_documento.herramientas.capturar_cliente.notebook_cliente import NoteBookCliente
from herramientas.capturar_documento.herramientas.historial_cliente import HistorialCliente
from herramientas.capturar_documento.herramientas.partida_compra import PartidaCompra
from herramientas.capturar_documento.herramientas.prorrateo_maniobras import ProrrateoManiobras
from herramientas.capturar_documento.herramientas.verificador.interfaz_verificador import InterfazVerificador
from herramientas.capturar_documento.herramientas.verificador.controlador_verificador import ControladorVerificador
from herramientas.capturar_documento.herramientas.editar_partida import EditarPartida
from herramientas.capturar_documento.herramientas.direccion_cliente import DireccionCliente
from herramientas.capturar_documento.herramientas.cobro_rapido.controlador_cobro_rapido import ControladorCobroRapido
from herramientas.capturar_documento.herramientas.cobro_rapido.interfaz_cobro_rapido import InterfazCobroRapido


class ControladorCaptura:
    MODULO_COMPRAS = 152
    MODULO_PEDIDOS = 1687
    MODULO_TICKET = 158
    MODULO_VENTAS = (158,21,1400,1316,1319,967)
    PARTIDAS_EDITABLES = (1687, 152)
    MODULOS_FISCALES = (21, 1400, 1319)
    MODULOS_COBRO = (21, 158, 1319, 1400)
    MODULOS_SIN_OFERTAS_AUTOMATICAS = (158, 21, 1400, 152)
    PRODUCTO_SERVICIO_DOMICILIO = 5606
    MONTO_MINIMO_SIN_ENVIO = 200
    ANCHO_PANTALLA_COMPACTA = 1367
    MODULO_VALES = 1692
    PRODUCTO_MANIOBRAS = 1048

    NOMBRES_MODULO = {
        1687: 'PEDIDOS',
        21: 'MAYOREO',
        1400: 'MINISUPER',
        158: 'VENTAS',
        1316: 'NOTAS',
        1319: 'GLOBAL',
        202: 'ENTRADA',
        203: 'SALIDA',
        1692: 'C.EMPLEADOS',
        152: 'COMPRAS'
    }

    FUNCIONES_INTERFAZ = {
        'verificador_precios': '_verificador_precios',
        'editar_cliente': '_editar_cliente',
        'historial_cliente': '_historial_cliente',
        'cambiar_direccion': '_cambiar_direccion',
        'cambiar_proveedor': '_cambiar_proveedor',
        'editar_partida': '_editar_partida',
        'eliminar_partida': '_eliminar_partida',
        'cobrar_nota': '_cobrar_nota',
        'prorratear': '_prorratear'
    }

    ATAJOS_ACCIONES = {
        'F3': '_verificador_precios',
        'F5': '_cambiar_direccion',
        'F6': '_editar_cliente',
        'F7': '_historial_cliente',
        'F8': '_agregar_partida_manualmente',
        'F9': '_copiar_productos',
        'F10': '_activar_chk_pieza',
        'F11': '_activar_chk_monto',
        'F12': '_cobrar_nota',
        'Ctrl+E': '_agregar_especicificaciones',
    }


    ATAJOS_CAPTURA_MANUAL = {
        'F8': '_agregar_partida_manualmente',
        'F9': '_copiar_productos',
        'F10': '_activar_chk_pieza',
        'F11': '_activar_chk_monto',
        'Ctrl+E': '_agregar_especicificaciones',
    }

    ATAJOS_HERRAMIENTAS = {
        'F3': '_verificador_precios',
        'F5': '_cambiar_direccion',
        'F6': '_editar_cliente',
        'F7': '_historial_cliente',
    }

    ATAJOS_FOCO = {
        'Ctrl+B': 'tbx_buscar_manual',
        'Ctrl+C': 'tbx_cantidad_manual',
        'Ctrl+F': 'cbx_tipo_busqueda_manual',
        'Ctrl+M': 'txt_comentario_manual',
        'Ctrl+T': 'tvw_productos_manual',
        'Ctrl+P': 'txt_portapapeles_manual',
    }

    def __init__(self, interfaz, modelo):

        self._inicializar_clases_auxiliares(interfaz, modelo)
        funciones_interfaz = {
            nombre: getattr(self, metodo)
            for nombre, metodo in self.FUNCIONES_INTERFAZ.items()
        }
        self._interfaz.inyectar_funciones(**funciones_interfaz)
        self._inicializar_variables_de_instancia()

        self._rellenar_controles_interfaz()

        if not self._es_documento_bloqueado():
            self._inicializar_captura_manual()
            self._agregar_atajos()
            self._cargar_eventos_componentes()

        if self.documento.document_id > 0:
            self._rellenar_partidas_desde_base_de_datos()

        self._ventanas.situar_ventana_arriba(self._master)
        self._ventanas.enfocar_componente('tbx_clave')

        if self._module_id == self.MODULO_PEDIDOS: # si es pedido
            self._agregar_servicio_a_domicilio()
            self.parametros_pedido = self._modelo.crear_parametros_pedido()
            self._buscar_ofertas(rellenar_tabla=True)
            self._ventanas.enfocar_componente('tbx_buscar_manual')

        self._interfaz.cambiar_titulo_ventana(self.cliente.official_name)

    def _inicializar_captura_manual(self):

        self._procesando_seleccion = False
        self._info_partida_seleccionada = {}
        self._agregando_producto = False

        self._rellenar_componentes_manual()

    def _es_documento_bloqueado(self):
        import datetime
        from decimal import Decimal, InvalidOperation

        def convertir_decimal(valor):
            try:
                return Decimal(str(valor or 0)).quantize(
                    Decimal('0.01')
                )
            except (InvalidOperation, TypeError, ValueError):
                return Decimal('0.00')

        def convertir_fecha(valor):
            if valor is None:
                return None

            if isinstance(valor, datetime.datetime):
                return valor.date()

            if isinstance(valor, datetime.date):
                return valor

            texto = str(valor).strip()

            try:
                return datetime.datetime.fromisoformat(
                    texto.replace('Z', '').replace('T', ' ')
                ).date()
            except ValueError:
                return None

        def bloquear_documento():
            self._ventanas.bloquear_forma('frame_herramientas')

            estilo_bloqueado = {
                'foreground': 'white',
                'background': '#ff8000',
            }

            frame = self._ventanas.componentes_forma.get(
                'frame_totales'
            )

            if frame is not None:
                for widget in frame.winfo_children():
                    try:
                        widget.config(**estilo_bloqueado)
                    except Exception:
                        continue

            return True

        status_id = 0

        if self._module_id == self.MODULO_PEDIDOS:
            status_id = self._modelo.obtener_estado_pedido(
                self.documento.document_id
            )

        if status_id > 2 or self.documento.cancelled_on:
            return bloquear_documento()

        # Restricciones exclusivas para documentos existentes de compras.
        if (
                self._module_id == self.MODULO_COMPRAS
                and int(self.documento.document_id or 0) > 0
        ):
            balance = convertir_decimal(self.documento.balance)
            total = convertir_decimal(self.documento.total)

            # Si el documento tiene pagos o afectaciones, ningún usuario
            # puede editarlo.
            if balance != total:
                return bloquear_documento()

            fecha_documento = convertir_fecha(
                self.documento.created_on
            )
            fecha_actual = datetime.date.today()
            grupos_autorizados = {1, 15, 21}

            user_group_id = int(
                getattr(self._modelo, 'user_group_id', 0) or 0
            )

            # Los usuarios de los grupos autorizados pueden editar compras
            # de días anteriores; los demás solamente las del día actual.
            if (
                    fecha_documento != fecha_actual
                    and user_group_id not in grupos_autorizados
            ):
                return bloquear_documento()

        return False

    def _actualizar_forma_pago(self):
        if self.documento.cfd_type_id == 1:
            return

        clave = self.documento.forma_pago
        fp_seleccionada = self._ventanas.obtener_input_componente('cbx_formapago')
        consulta_clave_seleccionada =  [reg['Clave'] for reg in self._modelo.consulta_formas_pago
                                        if fp_seleccionada == reg['Value']]
        if consulta_clave_seleccionada:
            clave_seleccionada = str(consulta_clave_seleccionada[0])

            if clave != '99' and clave_seleccionada == '99':
                consulta_valor_documento = [reg['Value'] for reg in self._modelo.consulta_formas_pago
                                        if clave == reg['Clave']]
                if consulta_valor_documento:
                    valor_documento = consulta_valor_documento[0]

                    self._ventanas.mostrar_mensaje('La forma de pago 99 solo es válida con método de pago PPD.')
                    self._ventanas.insertar_input_componente('cbx_formapago', valor_documento)
                    return

            self.documento.forma_pago = clave_seleccionada
            self._ventanas.insertar_input_componente('cbx_formapago', fp_seleccionada)

    def _cargar_eventos_componentes(self):
        eventos = {
            'tbx_clave': lambda event: self._agregar_partida(),

            # eventos captura manual
            'btn_ofertas_manual': lambda: self._buscar_ofertas(rellenar_tabla=True),
            'btn_agregar_manual': lambda: self._agregar_partida_manualmente(),
            'btn_copiar_manual': lambda: self._copiar_productos(),
            'btn_especificaciones_manual': lambda: self._agregar_especicificaciones(),

            'tbx_buscar_manual': lambda event: self._buscar_productos_manualmente(),
            'tbx_cantidad_manual': lambda event: self._selecionar_producto_tabla_manual(),

            'chk_monto': lambda *args: self._selecionar_producto_tabla_manual(),
            'chk_pieza': lambda *args: self._selecionar_producto_tabla_manual(),
            'tvw_productos_manual': (lambda event: self._selecionar_producto_tabla_manual(configurar_forma=True), 'seleccion'),
            'cbx_formapago': lambda event:self._actualizar_forma_pago()
        }
        if self._module_id not in self.MODULOS_FISCALES: # solo aplica actualizacion de forma de pago para facturas
            del eventos['cbx_formapago']

        if self._module_id in self.PARTIDAS_EDITABLES: # solo en el modulo de pedidos se puede editar la partida
            eventos['tvw_productos'] = (lambda event: self._editar_partida(), 'doble_click')

        self._ventanas.cargar_eventos(eventos)

        if self._module_id == self.MODULO_PEDIDOS:  # solo en el modulo de pedidos se puede editar la partida
            evento_adicional = {
                'tvw_productos': (lambda event: self._eliminar_partida(), 'suprimir'),
            }
            self._ventanas.cargar_eventos(evento_adicional)

        ancho, alto = self._ventanas.obtener_resolucion_pantalla()
        if ancho > self.ANCHO_PANTALLA_COMPACTA:
            txt_comentario_pedido = self._ventanas.componentes_forma['txt_comentario_documento']
            txt_comentario_pedido.bind("<FocusOut>",lambda event:self._actualizar_comentario_pedido())

    def _actualizar_comentario_pedido(self):
        comentario = self._ventanas.obtener_input_componente('txt_comentario_documento')
        comentario = comentario.upper().strip() if comentario else ''
        self.documento.comments = comentario

    def _agregar_atajos(self):
        # Los atajos de captura manual aplican a todos los módulos.
        eventos = {
            atajo: getattr(self, metodo)
            for atajo, metodo in self.ATAJOS_CAPTURA_MANUAL.items()
        }

        eventos.update({
            atajo: (
                lambda componente=componente:
                self._ventanas.enfocar_componente(componente)
            )
            for atajo, componente in self.ATAJOS_FOCO.items()
        })

        # El verificador de precios aplica siempre.
        eventos['F3'] = self._verificador_precios

        # Herramientas relacionadas con clientes.
        if self._module_id not in (
                self.MODULO_TICKET,
                self.MODULO_COMPRAS,
        ):
            eventos['F6'] = self._editar_cliente
            eventos['F7'] = self._historial_cliente
            eventos['F5'] = self._cambiar_direccion

        # Edición de partidas.
        if self._module_id in self.PARTIDAS_EDITABLES:
            eventos['F2'] = self._editar_partida

        # F12 depende de la herramienta configurada para cada módulo.
        if self._module_id in self.MODULOS_COBRO:
            eventos['F12'] = self._cobrar_nota

        elif self._module_id == self.MODULO_COMPRAS:
            eventos['F4'] = self._cambiar_proveedor
            eventos['F12'] = self._prorratear

        self._ventanas.agregar_hotkeys_forma(eventos)

    def _inicializar_clases_auxiliares(self, interfaz, modelo):
        self._interfaz = interfaz

        self._modelo = modelo
        self._parametros_contpaqi = self._modelo.parametros_contpaqi

        self._ventanas = self._interfaz.ventanas
        self._utilerias = self._modelo.utilerias
        self._impuestos = self._modelo.impuestos

        self.documento = self._modelo.documento
        self.cliente = self._modelo.cliente

    def _inicializar_variables_de_instancia(self):
        self._master = self._interfaz.master

        self._module_id = self._modelo.module_id
        self._user_id = self._modelo.user_id
        self._user_name = self._modelo.user_name
        self._documento_cobrado = False

        self._costo_servicio_a_domicilio = self._modelo.costo_servicio_a_domicilio

        self._partida_servicio_domicilio = None
        self._realizando_proceso = False

        self._consulta_productos = None
        self.consulta_productos_ofertados = None
        self._termino_buscado = None
        self.direcciones_cliente = self._modelo.obtener_direcciones_cliente()

    def _rellenar_controles_interfaz(self):
        self._cargar_direccion_cliente()
        self._cargar_nombre_cliente()
        self._cargar_informacion_crediticia()

        self._ventanas.insertar_input_componente('lbl_captura', self._user_name)
        self._ventanas.insertar_input_componente('lbl_folio', self.documento.docfolio)

        nombre_modulo = self._cargar_nombre_y_prefijo_modulo()
        self._ventanas.insertar_input_componente('lbl_modulo', nombre_modulo)

        if self._module_id in self.MODULOS_FISCALES:
            self._rellenar_cbxs_fiscales()

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

        self.documento.address_detail_id = datos_direccion.get('address_detail_id',datos_direccion.get('AddressDetailID',0))

        if self._module_id == self.MODULO_PEDIDOS: # modulo de pedidos
            self.documento.order_parameters['AddressDetailID'] = self.documento.address_detail_id

        calle = datos_direccion.get('calle', datos_direccion.get('Street',''))
        numero = datos_direccion.get('numero', datos_direccion.get('ExtNumber',''))
        colonia = datos_direccion.get('colonia', datos_direccion.get('City',''))
        cp = datos_direccion.get('cp', datos_direccion.get('ZipCode',''))
        municipio = datos_direccion.get('municipio', datos_direccion.get('Municipality',''))
        estado = datos_direccion.get('estado', datos_direccion.get('StateProvince',''))
        comentario = datos_direccion.get('comentario', datos_direccion.get('Comments',''))

        texto_direccion = f'{calle} NUM.{numero}, COL.{colonia}, MPIO.{municipio}, EDO.{estado}, C.P.{cp}'
        texto_direccion = texto_direccion.upper()
        self._ventanas.insertar_input_componente('tbx_direccion', texto_direccion)
        self._ventanas.bloquear_componente('tbx_direccion')

        self._ventanas.insertar_input_componente('tbx_comentario', comentario)
        self._ventanas.bloquear_componente('tbx_comentario')

    def _cargar_nombre_cliente(self):
        nombre = self.cliente.official_name if self.documento.document_id < 1 else self.documento.official_name
        nombre_comercial = self.cliente.commercial_name
        sucursal = self.documento.depot_name
        nombre_direccion = self.documento.address_name

        sucursal = f'({nombre_direccion})' if not sucursal else f'({sucursal})'
        nombre_comercial = '' if not nombre_comercial else f'-{nombre_comercial}-'

        nombre_cliente = f'{nombre} {nombre_comercial} {sucursal}'
        self._ventanas.insertar_input_componente('tbx_cliente', nombre_cliente)
        self._ventanas.bloquear_componente('tbx_cliente')

    def _cargar_nombre_y_prefijo_modulo(self):
        return self.NOMBRES_MODULO.get(self._module_id, 'CAYAL')

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

                # el credito del cliente es el credito del documento
                self.documento.credit_document_available = 0 if self.cliente.remaining_credit <= 0 else 1

                for atributo, label in valores.items():
                    monto = getattr(self.cliente, atributo)
                    monto_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(monto)
                    monto_moneda = self._utilerias.convertir_decimal_a_moneda(monto_decimal)

                    self._ventanas.insertar_input_componente(label, monto_moneda)

    def _agregar_partida_por_clave(self, clave):

        if self._agregando_producto:
            return

        try:
            self._agregando_producto = True

            if not self._utilerias.es_codigo_barras(clave):
                self._mensajes_de_error(7)
                return

            valores_clave = self._utilerias.validar_codigo_barras(clave)
            codigo_barras = valores_clave.get('clave', None)
            cantidad = valores_clave.get('cantidad', 1)
            cantidad = self._utilerias.convertir_valor_a_decimal(cantidad)

            consulta_producto = self._modelo.buscar_productos(codigo_barras, 'Clave')

            if not consulta_producto:
                self._mensajes_de_error(8)
                return

            producto_id = self._modelo.obtener_product_ids_consulta(consulta_producto)

            if not producto_id:
                self._mensajes_de_error(11)
                return

            if producto_id == 1048:  # impide que se capture el producto maniobras y servicios y rompa prorrateo
                self._mensajes_de_error(18)
                return

            info_producto = self._modelo.buscar_info_productos_por_ids(producto_id, no_en_venta=True)

            if not info_producto:
                existencia = self._modelo.producto_tiene_existencia(producto_id)

                if not existencia:
                    self._mensajes_de_error(11)
                    return

                self._mensajes_de_error(9)
                return

            disponible_a_venta = info_producto[0]['AvailableForSale']
            if disponible_a_venta == 0:
                self._mensajes_de_error(10)
                return

            # permite que al capturar por clave se respeten los casos tipo reja de huevo
            equivalencia_especial = self._utilerias.equivalencias_productos_especiales(producto_id)
            if equivalencia_especial:
                cantidad = equivalencia_especial[1]

            partida = self._utilerias.crear_partida(info_producto[0], cantidad)

            unidad_cayal = 0 if info_producto[0]['ClaveUnidad'] == 'KGM' else 1 # Del control de captura manual
            partida['Comments'] = ''

            if self._module_id == 152:
                ventana = self._ventanas.crear_popup_ttkbootstrap()
                _ = PartidaCompra(
                    ventana,
                    self._utilerias,
                    partida_producto=partida,
                    costo_producto=self._modelo.obtener_costo_producto(
                        producto_id
                    ),
                )

                ventana.wait_window()
                if not _.partida_actualizada:
                    return

            self._agregar_partida_tabla(partida, document_item_id=0, tipo_captura=0, unidad_cayal=unidad_cayal,
                                        monto_cayal=0)
        finally:
            self._agregando_producto = False
            self._ventanas.limpiar_componentes('tbx_clave')
            self._ventanas.enfocar_componente('tbx_clave')

    def _rellenar_partidas_desde_base_de_datos(self):
        if self.documento.document_id < 1:
            return

        # rellenar comentarios documento
        self._ventanas.insertar_input_componente('txt_comentario_documento', self.documento.comments)

        # rellena la informacion relativa a las partidas
        partidas = self._modelo.buscar_partidas_documento(self._module_id, self.documento.document_id)

        for partida in partidas:
            # Crear una copia profunda para evitar referencias pegadas
            partida_copia = copy.deepcopy(partida)

            piezas = partida_copia.get('CayalPiece', 0)
            chk_pieza = 1 if piezas != 0 else 0

            chk_monto = partida_copia.get('CayalAmount', 0)
            tipo_captura = partida_copia.get('TipoCaptura', 0)
            document_item_id = partida_copia.get('DocumentItemID', 0)

            # Procesar la copia para evitar referencias compartidas
            partida_procesada = self._utilerias.crear_partida(partida_copia)

            self._agregar_partida_tabla(partida_procesada, document_item_id=document_item_id, tipo_captura=tipo_captura,
                                        unidad_cayal=chk_pieza, monto_cayal=chk_monto)


        self._ventanas.configurar_ventana_ttkbootstrap(self.documento.docfolio)

    # ------------------------------------------------------------------------------------------------------------------
    # HERRAMIENTAS DE APLICATIVOS
    # ------------------------------------------------------------------------------------------------------------------

    def _cobrar_nota(self):
        if self.documento.document_id == 0:
            self._ventanas.mostrar_mensaje('Debe por lo menos capturar un producto.')
            return

        if not self._realizando_proceso:
            try:
                self._realizando_proceso = True

                self._modelo.preparar_documento_para_cobro()

                self._parametros_contpaqi.id_principal = self.documento.document_id

                ventana = self._ventanas.crear_popup_ttkbootstrap()
                interfaz = InterfazCobroRapido(ventana)
                controlador = ControladorCobroRapido(
                    interfaz,
                    self._parametros_contpaqi,
                    registrar_documento_para_recalculo=False,
                )
                ventana.wait_window()

                self._documento_cobrado = controlador.documento_cobrado
                self.documento.cobrado_en_captura = self._documento_cobrado
                self.documento.amount_received = controlador.monto_recibido
                self.documento.customer_change = controlador.cambio_cliente

            finally:
                self._realizando_proceso = False

                self._parametros_contpaqi.id_principal = 0

                if self._documento_cobrado:
                    self._interfaz.master.destroy()

    def _prorratear(self):
        if not self._realizando_proceso:
            try:
                self._realizando_proceso = True

                ventana = self._ventanas.crear_popup_ttkbootstrap()
                ProrrateoManiobras(
                    ventana,
                    self.documento,
                    self.PRODUCTO_MANIOBRAS,
                    user_id=self._user_id,
                    guardar_prorrateo=None,
                    revertir_prorrateo=None,
                    registros_prorrateo=None,
                    al_actualizar=None,
                )
                ventana.wait_window()

            finally:
                self._actualizar_totales_documento()
                self._realizando_proceso = False

    def _agregar_partida(self):
        clave = self._ventanas.obtener_input_componente('tbx_clave')
        self._agregar_partida_por_clave(clave)

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
                product_id = partida.get('ProductID', 0)

                if product_id == 1048: # impide que se capture el producto maniobras y servicios y rompa prorrateo
                    self._mensajes_de_error(18)
                    return

                chk_pieza = self._ventanas.obtener_input_componente('chk_pieza')
                chk_monto = self._ventanas.obtener_input_componente('chk_monto')
                comentarios = self._ventanas.obtener_input_componente('txt_comentario_manual')
                partida['Comments'] = comentarios

                if chk_pieza == 1 and partida['CayalPiece'] % 1 != 0:
                    self._ventanas.mostrar_mensaje('La cantidad de piezas deben ser valores no fraccionarios.')
                    return

                if self._module_id == 152:
                    ventana =self._ventanas.crear_popup_ttkbootstrap()
                    _ = PartidaCompra(
                        ventana,
                        self._utilerias,
                        partida_producto=partida,
                        costo_producto=self._modelo.obtener_costo_producto(
                            product_id
                        ),
                    )

                    ventana.wait_window()
                    if not _.partida_actualizada:
                        return

                self._agregar_partida_tabla(partida, document_item_id=0, tipo_captura=1, unidad_cayal=chk_pieza,
                                            monto_cayal=chk_monto)

            finally:
                self._agregando_producto = False
                self._ventanas.insertar_input_componente('tbx_cantidad_manual', 1)
                self._ventanas.limpiar_componentes('txt_comentario_manual')
                self._ventanas.limpiar_componentes('tbx_buscar_manual')
                self._ventanas.enfocar_componente('tbx_buscar_manual')

    def _editar_cliente(self):
        if self._realizando_proceso:
            return
        try:
            self._realizando_proceso = True
            self._parametros_contpaqi.id_principal = self.cliente.business_entity_id
            ventana = self._ventanas.crear_popup_ttkbootstrap(self._master, 'Cliente')

            NoteBookCliente(
                ventana,
                self._modelo.base_de_datos,
                self._parametros_contpaqi,
                self._utilerias,
                self.cliente
            )

            ventana.wait_window()
        finally:
            self._realizando_proceso = False
            self._parametros_contpaqi.id_principal = 0

    def _cambiar_direccion(self):
        if self._realizando_proceso:
            ventana = getattr(self, '_ventana_direccion', None)
            if ventana is not None and ventana.winfo_exists():
                ventana.lift()
                ventana.focus_force()
            return
        try:
            self._realizando_proceso = True
            ventana = self._ventanas.crear_popup_ttkbootstrap(
                self._master, 'Cambiar dirección'
            )
            self._ventana_direccion = ventana
            DireccionCliente(
                ventana,
                self.documento,
                self._modelo.base_de_datos,
                self._ventanas.componentes_forma,
                al_actualizar=self._direccion_actualizada,
            )
            ventana.transient(self._master)
            # En Windows una Toplevel no modal puede quedar detrás de la
            # captura aunque sea transient. Mantenerla topmost conserva la
            # herramienta visible sin bloquear la ventana principal.
            ventana.attributes('-topmost', True)
            ventana.lift()
            # configurar_ventana_ttkbootstrap retira topmost a los 10 ms.
            # Este segundo paso debe ejecutarse después de ese temporizador.
            ventana.after(
                100,
                lambda: self._enfocar_ventana_direccion(ventana)
            )
            ventana.bind(
                '<Destroy>',
                lambda evento: self._cerrar_ventana_direccion(evento),
                add='+',
            )
        except Exception:
            self._realizando_proceso = False
            self._ventana_direccion = None
            raise

    @staticmethod
    def _enfocar_ventana_direccion(ventana):
        if ventana is None or not ventana.winfo_exists():
            return
        # Windows puede conservar el Toplevel en estado iconic aunque Tk lo
        # reporte creado correctamente. Se normaliza antes de elevarlo.
        ventana.deiconify()
        ventana.state('normal')
        ventana.attributes('-topmost', True)
        ventana.lift()
        ventana.focus_force()

    def _cerrar_ventana_direccion(self, evento):
        ventana = getattr(self, '_ventana_direccion', None)
        # Destroy también se genera para los controles hijos. Sólo libera el
        # estado cuando se destruye la ventana completa.
        if ventana is not None and evento.widget is ventana:
            self._realizando_proceso = False
            self._ventana_direccion = None

    def _direccion_actualizada(self, direccion):
        """Sincroniza documento, pedido y encabezado tras la selección."""
        self.documento.address_details = direccion
        self._cargar_direccion_cliente()
        self._cargar_nombre_cliente()

        if self._module_id == self.MODULO_PEDIDOS:
            parametros = getattr(self.documento, 'order_parameters', {})
            parametros['AddressDetailID'] = self.documento.address_detail_id
            parametros['DepotID'] = self.documento.depot_id

            costo_envio = direccion.get(
                'delivery_cost', direccion.get('DeliveryCost')
            )
            if costo_envio not in (None, ''):
                self.documento.delivery_cost = costo_envio

    def _cambiar_proveedor(self):
        """Abre el buscador de proveedores para una compra en captura."""
        if self._module_id != self.MODULO_COMPRAS:
            return

        ventana = getattr(self, '_ventana_proveedor', None)
        if ventana is not None and ventana.winfo_exists():
            ventana.lift()
            ventana.focus_force()
            return

        # Importación diferida: el buscador también utiliza este controlador
        # cuando inicia una captura nueva.
        from capturar_documento.buscar_generales_proveedor import (
            BuscarGeneralesProveedor,
        )

        ventana = self._crear_ventana_cambiar_proveedor()
        self._ventana_proveedor = ventana

        buscador = BuscarGeneralesProveedor(
            ventana,
            self._parametros_contpaqi,
            cliente=self.cliente,
            documento=self.documento,
            al_seleccionar=self._proveedor_actualizado,
        )
        ventana.bind(
            '<Destroy>',
            lambda evento: self._cerrar_ventana_proveedor(evento),
            add='+',
        )
        self._mostrar_ventana_cambiar_proveedor(ventana, buscador)

    def _crear_ventana_cambiar_proveedor(self):
        """Crea la ventana exclusiva sin utilizar los popups genéricos."""
        ventana = ttk.Toplevel(self._master)
        ventana.withdraw()
        ventana.title('Cambiar proveedor')
        ventana.resizable(False, False)
        ventana.transient(self._master)
        ventana.protocol('WM_DELETE_WINDOW', ventana.destroy)
        ventana.bind('<Escape>', lambda evento: ventana.destroy())
        return ventana

    def _mostrar_ventana_cambiar_proveedor(self, ventana, buscador):
        """Muestra, centra y mantiene el buscador delante de la captura."""
        ventana.update_idletasks()

        ancho = ventana.winfo_reqwidth()
        alto = ventana.winfo_reqheight()
        x = self._master.winfo_rootx() + max(
            0,
            (self._master.winfo_width() - ancho) // 2,
        )
        y = self._master.winfo_rooty() + max(
            0,
            (self._master.winfo_height() - alto) // 2,
        )
        ventana.geometry(f'{ancho}x{alto}+{x}+{y}')

        ventana.deiconify()
        ventana.state('normal')
        ventana.attributes('-topmost', True)
        ventana.lift(self._master)
        ventana.grab_set()

        # BuscarGeneralesProveedor desactiva topmost de forma diferida al
        # configurar su interfaz. Este enfoque se ejecuta después y conserva
        # la ventana sobre la captura durante toda la selección.
        ventana.after(
            100,
            lambda: self._enfocar_ventana_cambiar_proveedor(
                ventana,
                buscador,
            ),
        )

    @staticmethod
    def _enfocar_ventana_cambiar_proveedor(ventana, buscador):
        if ventana is None or not ventana.winfo_exists():
            return

        ventana.deiconify()
        ventana.state('normal')
        ventana.attributes('-topmost', True)
        ventana.lift()
        ventana.focus_force()
        buscador.enfocar_busqueda()

    def _cerrar_ventana_proveedor(self, evento):
        ventana = getattr(self, '_ventana_proveedor', None)
        if ventana is not None and evento.widget is ventana:
            try:
                ventana.grab_release()
            except Exception:
                pass
            self._ventana_proveedor = None

    def _proveedor_actualizado(self, cliente, documento):
        """Refresca generales y persiste el dueño de una compra existente."""
        business_entity_id = int(cliente.business_entity_id or 0)
        self.documento.business_entity_id = business_entity_id
        self.documento.official_name = cliente.official_name

        self._modelo.actualizar_proveedor_documento(business_entity_id)
        self._cargar_direccion_cliente()
        self._cargar_nombre_cliente()
        self._interfaz.cambiar_titulo_ventana(cliente.official_name)

    def _eliminar_partida(self):
        filas = self._ventanas.obtener_seleccion_filas_treeview('tvw_productos')
        if not filas:
            return

        if filas:
            if not self._ventanas.mostrar_mensaje_pregunta('¿Desea eliminar las partidas seleccionadas?'):
                return

            partidas_seleccionadas = [
                (
                    fila,
                    self._ventanas.procesar_fila_treeview(
                        'tvw_productos',
                        fila,
                    ),
                )
                for fila in filas
            ]

            # Validar la seleccion completa antes de mutar el pedido evita
            # eliminaciones parciales si tambien se selecciono el servicio.
            if self._module_id == self.MODULO_PEDIDOS and any(
                    int(valores.get('ProductID', 0) or 0)
                    == self.PRODUCTO_SERVICIO_DOMICILIO
                    for _, valores in partidas_seleccionadas):
                self._mensajes_de_error(13)
                return

            for fila, valores_fila in partidas_seleccionadas:

                document_item_id = valores_fila['DocumentItemID']
                identificador = valores_fila['UUID']


                # filtrar de los items del documento
                partida_items = next(
                    (
                        partida
                        for partida in self.documento.items
                        if str(identificador) == str(partida.get('uuid'))
                    ),
                    None,
                )
                if partida_items is None:
                    continue

                # remover del treeview solamente cuando la partida tambien
                # fue localizada en el estado interno del documento.
                self._ventanas.remover_fila_treeview('tvw_productos', fila)

                #----------------------------------------------------------------------------------
                # remover la partida de los items del documento

                if int(document_item_id or 0) == 0:
                    # Si la partida fue agregada en esta captura y todavia no
                    # existe en BD, eliminarla cancela el alta pendiente. No
                    # debe quedar como baja ni generar movimientos ficticios.
                    self.documento.items = [
                        partida
                        for partida in self.documento.items
                        if str(partida.get('uuid')) != str(identificador)
                    ]
                    self._modelo.cancelar_partida_items_documento_extra(
                        identificador
                    )
                else:
                    partida_items['ItemProductionStatusModified'] = 3

                    # Una partida persistida se conserva como baja logica
                    # para historial y para el guardado del pedido.
                    comentario = f'ELIMINADA POR {self._user_name}'
                    self._modelo.agregar_partida_items_documento_extra(
                        partida_items,
                        'eliminar',
                        comentario,
                        identificador,
                    )

                self._actualizar_totales_documento()
                # ----------------------------------------------------------------------------------

                # Solo aplica para el módulo 1687 pedidos
                if self._module_id == self.MODULO_PEDIDOS:
                    # Si el total es menor a 200 y no se ha agregado aún, lo agrega
                    if self.documento.total < self.MONTO_MINIMO_SIN_ENVIO and not self._modelo.servicio_a_domicilio_agregado:

                        self._agregar_servicio_a_domicilio()
                        self._modelo.servicio_a_domicilio_agregado = True

                    # Si ya se agregó pero ahora el total (sin el servicio) es >= 200, lo remueve
                    elif self._modelo.servicio_a_domicilio_agregado and (
                            self.documento.total - self._costo_servicio_a_domicilio) >= self.MONTO_MINIMO_SIN_ENVIO:

                        self._remover_servicio_a_domicilio()
                        self._modelo.servicio_a_domicilio_agregado = False

    def _editar_partida(self):

        if self._module_id not in self.PARTIDAS_EDITABLES:
            return

        filas = self._ventanas.obtener_seleccion_filas_treeview(
            'tvw_productos'
        )

        if not filas:
            self._ventanas.mostrar_mensaje(
                'Debe seleccionar por lo menos un producto'
            )
            return

        if not self._ventanas.validar_seleccion_una_fila_treeview(
                'tvw_productos'
        ):
            self._ventanas.mostrar_mensaje(
                'Debe seleccionar solamente un producto'
            )
            return

        fila = filas[0]
        valores_fila = self._ventanas.procesar_fila_treeview(
            'tvw_productos',
            fila,
        )

        if int(valores_fila['ProductID']) == self.PRODUCTO_SERVICIO_DOMICILIO:
            self._ventanas.mostrar_mensaje(
                'No se puede editar la partida servicio a domicilio.'
            )
            return

        ventana = self._ventanas.crear_popup_ttkbootstrap(
            self._master,
            'Editar partida',
        )

        if self._module_id == self.MODULO_COMPRAS:
            uuid_partida = str(valores_fila.get('UUID', ''))
            document_item_id = str(
                valores_fila.get('DocumentItemID', '0')
            )

            partida_documento = next(
                (
                    partida
                    for partida in self.documento.items
                    if (
                               uuid_partida
                               and str(partida.get('uuid', '')) == uuid_partida
                       ) or (
                               document_item_id not in ('', '0')
                               and str(
                           partida.get('DocumentItemID', '0')
                       ) == document_item_id
                       )
                ),
                None,
            )

            if partida_documento is None:
                ventana.destroy()
                self._ventanas.mostrar_mensaje(
                    'No fue posible localizar la partida seleccionada '
                    'en el documento.'
                )
                return

            instancia = PartidaCompra(
                ventana,
                self._utilerias,
                partida_producto=partida_documento,
                costo_producto=self._modelo.obtener_costo_producto(
                    partida_documento.get('ProductID', 0)
                ),
                subtotal_documento=getattr(
                    self.documento,
                    'subtotal',
                    0,
                ),
                subtotal_con_descuento_documento=getattr(
                    self.documento,
                    'subtotal_with_discount',
                    0,
                ),
                total_descuento_documento=getattr(
                    self.documento,
                    'total_discount',
                    0,
                ),
                total_impuesto_documento=getattr(
                    self.documento,
                    'total_tax',
                    0,
                ),
                total_documento=getattr(
                    self.documento,
                    'total',
                    0,
                ),
                total_costo_documento=getattr(
                    self.documento,
                    'total_cost',
                    0,
                ),
                partida_incluida_en_totales=True,
            )

        else:
            instancia = EditarPartida(
                ventana,
                self._interfaz,
                self._modelo,
                self._utilerias,
                self._modelo.base_de_datos,
                valores_fila,
                actualizar_totales=self._actualizar_totales_documento,
                agregar_servicio_domicilio=(
                    self._agregar_servicio_a_domicilio
                ),
                remover_servicio_domicilio=(
                    self._remover_servicio_a_domicilio
                ),
            )

        ventana.wait_window()

        if (
                self._module_id != self.MODULO_COMPRAS
                or not instancia.partida_actualizada
        ):
            return

        valores_actualizados = dict(valores_fila)

        for nombre_columna in valores_fila:
            if nombre_columna in partida_documento:
                valores_actualizados[nombre_columna] = (
                    partida_documento[nombre_columna]
                )

        cantidad = self._utilerias.redondear_valor_cantidad_a_decimal(
            partida_documento.get(
                'cantidad',
                partida_documento.get('Quantity', 0),
            )
        )

        clave_unidad = partida_documento.get('ClaveUnidad', '')
        cantidad_mostrada = (
            f'{cantidad:.3f}'
            if clave_unidad == 'KGM'
            else f'{cantidad:.2f}'
        )

        valores_actualizados.update({
            'Cantidad': cantidad_mostrada,
            'Piezas': partida_documento.get('CayalPiece', 0),
            'Código': partida_documento.get('ProductKey', ''),
            'Descripción': partida_documento.get('ProductName', ''),
            'Unidad': partida_documento.get('Unit', ''),
            'Precio': partida_documento.get(
                'CostPrice',
                partida_documento.get('precio', 0),
            ),
            'Importe': partida_documento.get('subtotal', 0),
            'Impuesto': partida_documento.get('impuestos', 0),
            'Total': partida_documento.get(
                'total_con_descuento',
                partida_documento.get('total', 0),
            ),
            'Quantity': partida_documento.get(
                'cantidad',
                cantidad,
            ),
            'CostPrice': partida_documento.get('CostPrice', 0),
            'UnitPrice': partida_documento.get('UnitPrice', 0),
            'DiscountPerc': partida_documento.get('DiscountPerc', 0),
            'descuento': partida_documento.get('descuento', 0),
            'subtotal': partida_documento.get('subtotal', 0),
            'subtotal_con_descuento': partida_documento.get(
                'subtotal_con_descuento',
                0,
            ),
            'impuestos': partida_documento.get('impuestos', 0),
            'total': partida_documento.get('total', 0),
            'total_con_descuento': partida_documento.get(
                'total_con_descuento',
                0,
            ),
        })

        self._ventanas.actualizar_fila_treeview_diccionario(
            'tvw_productos',
            fila,
            valores_actualizados,
        )
        self._actualizar_totales_documento()

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
    #------------------------------------------------------------------------------------------------------------------
    #------------------------------------------------------------------------------------------------------------------

    def _buscar_ofertas(self, rellenar_tabla=False):

        if self._module_id in self.MODULOS_SIN_OFERTAS_AUTOMATICAS and not rellenar_tabla:
            return

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
            product_id = int(valores_fila['ProductID'])
            producto = str(valores_fila['Descripción'])

            if product_id in self._modelo.products_ids_ofertados:
                producto_actualizado  = self._actualizar_nombre_producto_ofertado(producto, product_id)
                valores_fila['Descripción'] = producto_actualizado
                precio = self._utilerias.redondear_valor_cantidad_a_decimal(valores_fila['Precio'])
                valores_fila['Precio'] = precio
                self._ventanas.actualizar_fila_treeview_diccionario('tvw_productos_manual', fila, valores_fila)
                self._ventanas.colorear_fila_seleccionada_treeview('tvw_productos_manual', fila, color='warning')

    def _actualizar_nombre_producto_ofertado(self, producto, product_id):

        # Buscar el producto ofertado por ID (copiando solo los campos necesarios)
        for reg in self._modelo.consulta_productos_ofertados:
            if int(reg['ProductID']) == int(product_id):
                sale_price_before = self._utilerias.redondear_valor_cantidad_a_decimal(reg['SalePriceBefore'])  # Copia segura
                tax_type_id = int(reg['TaxTypeID'])  # Copia segura
                clave_unidad = reg['ClaveUnidad']
                clave_sat = reg['ClaveProdServ']
                break
        else:
            return producto  # No encontrado

        # Calcular totales sin modificar referencias originales

        cantidad = 1
        totales_partida = self._utilerias.calcular_totales_partida(
            precio=sale_price_before,
            tipo_impuesto_id=tax_type_id,
            cantidad=cantidad,
            clave_unidad=clave_unidad,
            clave_sat=clave_sat
        )
        producto = re.sub(r"\s*\(OFE\).*", "", producto)
        sale_price_before_with_taxes = self._utilerias.redondear_valor_cantidad_a_decimal(
            totales_partida.get('total', sale_price_before))
        nombre_producto = f"{producto} (OFE) {sale_price_before_with_taxes}"
        return nombre_producto

    def _rellenar_tabla_productos_manual(self, consulta_productos):

        registros_tabla = []
        tabla = self._ventanas.componentes_forma['tvw_productos_manual']

        for producto in consulta_productos:

            _producto = {
                'ProductKey': producto['ProductKey'],
                'ProductName': producto['ProductName'],
                'SalePriceWithTaxes': self._utilerias.redondear_valor_cantidad_a_decimal(
                    producto['SalePriceWithTaxes']),
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
            self._mensajes_de_error(6, self._master)
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

        self._ventanas.insertar_input_componente('txt_portapapeles_manual', self._copiar_portapapeles(), con_saltos_de_linea=True)

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

        if not fila:
            return False

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
            return self._utilerias.convertir_valor_a_decimal(0)

        cantidad_decimal = self._utilerias.convertir_valor_a_decimal(cantidad)

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
            cantidad_decimal = self._utilerias.convertir_valor_a_decimal(cantidad)

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

                cantidad_real_decimal = self._utilerias.convertir_valor_a_decimal(cantidad)

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

        cantidad_decimal = self._utilerias.convertir_valor_a_decimal(cantidad)

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
                self._mensajes_de_error(4, self._master)

            if equivalencia == 0:
                return 'Unidad'

            if equivalencia != 0:
                return 'Equivalencia'

        if clave_unidad == 'KGM':

            if valor_chk_pieza == 1 and equivalencia == 0:
                self._mensajes_de_error(3, self._master)
                self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'deseleccionado')
                return 'Error'

            if valor_chk_monto == 1 and cantidad == 0:
                self._mensajes_de_error(0, self._master)
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
                self._mensajes_de_error(2, self._master)
                return 'Error'

            if valor_chk_monto == 1:
                return 'Monto'
        return 'Error'

    def _rellenar_cbxs_fiscales(self):
        es_remision_o_pg = (
                getattr(self.documento, "cfd_type_id", None) == 1
                or getattr(self.cliente, "cayal_customer_type_id", None) in (0, 1)
                or getattr(self.cliente, "business_entity_id", None) == 9277
                or getattr(self.cliente, "business_entitity_id", None) == 9277
        )

        valores_fiscales_default = {
            "cbx_regimen": "616 - Sin obligaciones fiscales",
            "cbx_metodopago": "PUE - Pago en una sola exhibición",
            "cbx_formapago": "01 - Efectivo",
            "cbx_usocfdi": "S01 - Sin efectos fiscales.",
        }

        if es_remision_o_pg:
            for componente, valor in valores_fiscales_default.items():
                self._interfaz.ventanas.rellenar_cbx(
                    componente,
                    [valor],
                    sin_seleccione=False,
                )
                self._interfaz.ventanas.insertar_input_componente(
                    componente,
                    valor,
                )
                self._interfaz.ventanas.bloquear_componente(componente)

            return

        def _today_str():
            return datetime.now().strftime("%Y%m%d")

        def _cache_dir():
            base = Path.home() / ".cayal_cache"
            base.mkdir(parents=True, exist_ok=True)
            return base

        def _fiscales_cache_path(kind, day):
            return _cache_dir() / f"fiscales_{kind}_{day}.pkl.gz"

        def _cache_save_today(kind, data):
            path = _fiscales_cache_path(kind, _today_str())

            try:
                with gzip.open(path, "wb") as archivo:
                    pickle.dump(
                        data,
                        archivo,
                        protocol=pickle.HIGHEST_PROTOCOL,
                    )
            except Exception:
                pass

        def _cache_load_if_today(kind):
            path = _fiscales_cache_path(kind, _today_str())

            try:
                if path.exists():
                    with gzip.open(path, "rb") as archivo:
                        return pickle.load(archivo)
            except Exception:
                return None

            return None

        def _cache_cleanup_not_today():
            day = _today_str()

            for archivo in _cache_dir().glob("fiscales_*.pkl.gz"):
                if archivo.name.endswith(f"_{day}.pkl.gz"):
                    continue

                try:
                    archivo.unlink(missing_ok=True)
                except Exception:
                    pass

        if not hasattr(self, "_fiscales_cache_mem"):
            self._fiscales_cache_mem = {
                "metodopago": None,
                "formapago": None,
                "regimen": None,
                "usocfdi": None,
            }

        parametros = {
            "cbx_metodopago": (
                "metodopago",
                "consulta_metodos_pago",
                lambda: self._modelo.buscar_info_fiscal(
                    "metodos_de_pago"
                ),
            ),
            "cbx_formapago": (
                "formapago",
                "consulta_formas_pago",
                lambda: self._modelo.buscar_info_fiscal(
                    "formas_de_pago"
                ),
            ),
            "cbx_regimen": (
                "regimen",
                "consulta_regimenes",
                lambda: self._modelo.buscar_info_fiscal(
                    "regimenes_fiscales"
                ),
            ),
            "cbx_usocfdi": (
                "usocfdi",
                "consulta_uso_cfdi",
                lambda: self._modelo.buscar_info_fiscal(
                    "usos_de_cfdi"
                ),
            ),
        }

        datos_por_tipo = {}
        _cache_cleanup_not_today()

        for componente, (tipo, attr_name, proveedor) in parametros.items():
            lista = self._fiscales_cache_mem.get(tipo)

            if lista is None:
                lista = _cache_load_if_today(tipo)

                if lista is not None:
                    self._fiscales_cache_mem[tipo] = lista
                    setattr(self, attr_name, lista)

            if lista is None:
                lista = proveedor() or []
                self._fiscales_cache_mem[tipo] = lista
                setattr(self, attr_name, lista)
                _cache_save_today(tipo, lista)

            datos_por_tipo[tipo] = lista or []

        for componente, (tipo, _, _) in parametros.items():
            lista = datos_por_tipo.get(tipo, [])
            valores_cbx = [
                registro.get("Value")
                for registro in lista
                if registro.get("Value") is not None
            ]

            self._interfaz.ventanas.rellenar_cbx(
                componente,
                valores_cbx,
                sin_seleccione=True,
            )

        parametros_cliente = {
            "cbx_metodopago": (
                datos_por_tipo["metodopago"],
                getattr(self.cliente, "metodo_pago", None),
            ),
            "cbx_formapago": (
                datos_por_tipo["formapago"],
                getattr(self.cliente, "forma_pago", None),
            ),
            "cbx_regimen": (
                datos_por_tipo["regimen"],
                getattr(self.cliente, "company_type_name", None),
            ),
            "cbx_usocfdi": (
                datos_por_tipo["usocfdi"],
                getattr(self.cliente, "receptor_uso_cfdi", None),
            ),
        }

        for componente, (lista, clave) in parametros_cliente.items():
            if not lista:
                continue

            seleccionado = None

            if componente != "cbx_regimen" and clave is not None:
                seleccionado = next(
                    (
                        registro.get("Value")
                        for registro in lista
                        if registro.get("Clave") == clave
                    ),
                    None,
                )

                if seleccionado is not None:
                    self._interfaz.ventanas.insertar_input_componente(
                        componente,
                        seleccionado,
                    )

                    if componente != "cbx_formapago":
                        self._interfaz.ventanas.bloquear_componente(
                            componente
                        )

            if seleccionado is None and clave is not None:
                seleccionado = next(
                    (
                        registro.get("Value")
                        for registro in lista
                        if registro.get("Value") == clave
                    ),
                    None,
                )

                if seleccionado is not None:
                    self._interfaz.ventanas.insertar_input_componente(
                        componente,
                        seleccionado,
                    )
                    self._interfaz.ventanas.bloquear_componente(
                        componente
                    )

            if (
                    componente == "cbx_formapago"
                    and getattr(self.cliente, "forma_pago", None) == "99"
            ):
                self._interfaz.ventanas.bloquear_componente(componente)

    def _mensajes_de_error(self, numero_mensaje, master=None):

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
            17: 'La captura del documento ha conluido.',
            18: 'El producto Maniobras y servicios no es capturable.'
        }

        self._interfaz.ventanas.mostrar_mensaje(mensajes[numero_mensaje], master)

    def _agregar_servicio_a_domicilio(self):

        def insertar_partida_servicio_a_domicilio():
            delivery_cost_iva = self._modelo.obtener_costo_servicio_documicilio(self.documento.address_detail_id)
            self.costo_servicio_a_domicilio = self._utilerias.redondear_valor_cantidad_a_decimal(delivery_cost_iva)
            delivery_cost = self._utilerias.calcular_monto_sin_iva(delivery_cost_iva)

            info_producto = self._modelo.buscar_info_productos_por_ids(5606, no_en_venta=True)

            if info_producto:
                info_producto = info_producto[0]

                info_producto['SalePrice'] = delivery_cost

                partida = self._utilerias.crear_partida(info_producto, cantidad=1)

                self.partida_servicio_domicilio = partida
                partida['Comments'] = ''
                self._agregar_partida_tabla(partida, document_item_id=0, tipo_captura=2, unidad_cayal=1, monto_cayal=0)

                self._modelo.servicio_a_domicilio_agregado = True


        # servicio a domicilio solo aplica para pedidos
        if self._module_id != self.MODULO_PEDIDOS:
            print('no es un pedido')
            return

        # servicio a domicilio no aplica para anexos o cambios 2 y 3 solo para pedidos 1
        if self._module_id == self.MODULO_PEDIDOS:
            parametros_pedido = self.documento.order_parameters
            order_type_id = int(parametros_pedido.get('OrderTypeID', 1))

            # anexos o cambios 2 y 3
            if order_type_id in (2,3):
                print(f'no es un pedido es un {order_type_id}')
                return

        # no se debe agregar mas de una partida de servicio a domicilio
        existe_servicio_a_domicilio = [producto for producto in self.documento.items
                                       if int(producto['ProductID']) == 5606
                                       and int(producto['ItemProductionStatusModified']) != 3]

        if existe_servicio_a_domicilio:
            return

        # insertamos el servicio a domicilio
        insertar_partida_servicio_a_domicilio()

    def _agregar_partida_tabla(self, partida, document_item_id, tipo_captura, unidad_cayal=0, monto_cayal=0):

        product_id = partida.get('ProductID',0) # esta condicion evita romper el flujo de prorrateo en documentos
        if product_id == 1048:
            self._mensajes_de_error(18)
            return

        if self.documento.finish_document == 2:
            self._mensajes_de_error(17)
            return

        if document_item_id == 0:
            if not self._filtrar_productos_no_permitidos(partida):
                return

            if not self._validar_restriccion_por_monto(partida, tipo_captura):
                return

        if not self._modelo.agregando_partida:
            try:
                self._modelo.agregando_partida = True

                cantidad = self._utilerias.convertir_valor_a_decimal(partida['cantidad'])
                comments = partida.get('Comments', '')
                producto = partida.get('ProductName', '')
                partida['TipoCaptura'] = tipo_captura
                partida['DocumentItemID'] = document_item_id
                partida['CayalAmount'] = monto_cayal
                partida['uuid'] = uuid.uuid4()

                if self.documento.document_id > 0 and document_item_id == 0:
                    partida['ItemProductionStatusModified'] = 1
                    partida['CreatedBy'] = self._user_id

                    comentario = f'AGREGADO POR {self._user_name}'
                    self._modelo.agregar_partida_items_documento_extra(partida, 'agregar', comentario, partida['uuid'])

                # en caso que el modulo se use para capturar otro tipo de documentos que no sean pedidos el valor por defecto
                # debe ser 0 y para las subsecuentes modificaciones segun aplique
                # en funcion del diccionario modificaciones_pedido
                item_production_status_modified = partida.get('ItemProductionStatusModified', 0)
                partida['ItemProductionStatusModified'] = item_production_status_modified
                partida['CreatedBy'] = self._user_id

                cantidad_piezas = 0 if unidad_cayal == 0 else self._utilerias.redondear_valor_cantidad_a_decimal(partida['CayalPiece'])

                equivalencia = self._modelo.obtener_equivalencia_producto(partida.get('ProductID', 0))
                equivalencia = 0 if not equivalencia else equivalencia
                equivalencia_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

                if equivalencia_decimal > 0 and unidad_cayal == 1:
                    cantidad_piezas = int((cantidad/equivalencia_decimal))

                partida['CayalPiece'] = cantidad_piezas
                cantidad = f"{cantidad:.3f}" if partida['ClaveUnidad'] == 'KGM' else f"{cantidad:.2f}"
                partida_tabla = (cantidad,
                                 cantidad_piezas,
                                 partida['ProductKey'],
                                 producto,
                                 partida['Unit'],
                                 self._utilerias.convertir_valor_a_decimal(partida['precio']),
                                 self._utilerias.convertir_valor_a_decimal(partida['subtotal']),
                                 self._utilerias.convertir_valor_a_decimal(partida['impuestos']),
                                 self._utilerias.convertir_valor_a_decimal(partida['total']),
                                 product_id,
                                 partida['DocumentItemID'],
                                 partida['TipoCaptura'],  # Tipo de captura 1 para manual y 0 para captura por pistola
                                 cantidad_piezas,  # Viene del control de captura manual
                                 partida['CayalAmount'],  # viene del control de tipo monto
                                 partida['uuid'],
                                 partida['ItemProductionStatusModified'],
                                 comments,
                                 partida['CreatedBy'],
                                 # Datos ocultos utilizados al editar compras.
                                 partida.get('Quantity', partida.get('cantidad', 0)),
                                 partida.get('ProductName', producto),
                                 partida.get('ProductKey', ''),
                                 partida.get('Unit', ''),
                                 partida.get('ClaveUnidad', ''),
                                 partida.get('ClaveProdServ', ''),
                                 partida.get('CostPrice', partida.get('precio', 0)),
                                 partida.get('UnitPrice', partida.get('precio', 0)),
                                 partida.get('DiscountPerc', 0),
                                 partida.get('descuento', 0),
                                 partida.get('subtotal', 0),
                                 partida.get(
                                     'subtotal_con_descuento',
                                     partida.get('subtotal', 0),
                                 ),
                                 partida.get('impuestos', 0),
                                 partida.get('total', 0),
                                 partida.get(
                                     'total_con_descuento',
                                     partida.get('total', 0),
                                 ),
                                 partida.get('TaxTypeID', 0),
                                 partida.get('FechaCosto'),
                                 partida.get('ItemCosto', 0),
                                 )

                if int(partida['ProductID']) == self.PRODUCTO_SERVICIO_DOMICILIO:
                    if self._modelo.servicio_a_domicilio_agregado:
                        return
                    else:
                        self._modelo.servicio_a_domicilio_agregado = True

                # agregar tipo de captura
                tabla_captura = self._interfaz.ventanas.componentes_forma['tvw_productos']
                self._interfaz.ventanas.insertar_fila_treeview(tabla_captura, partida_tabla, al_principio=True)

                self.documento.items.append(partida)

                if self._module_id in self.MODULO_VENTAS:
                    self._modelo.agregar_partida_base_de_datos(partida)

                if self.documento.document_id != 0:
                    self._asignar_folio(self.documento.document_id)

                self._actualizar_totales_documento()

                # si aplica remueve el servicio a domicilio
                if self._module_id == self.MODULO_PEDIDOS and self._modelo.servicio_a_domicilio_agregado == True:
                    if self.documento.total - self._modelo.costo_servicio_a_domicilio >= self.MONTO_MINIMO_SIN_ENVIO:
                        self._remover_servicio_a_domicilio()

            finally:
                self._modelo.agregando_partida = False

    def _validar_restriccion_por_monto(self, partida, tipo_captura):
        # Los módulos sin restricciones especiales deben permitir la partida.
        if self._module_id not in self.MODULO_VENTAS:
            return True

        total = self.documento.total
        total_partida = partida.get('total', 0)
        total_real = total_partida + total

        if self._module_id in (1400, 21, 1319):
            if (
                    total_real >= 2000
                    and self.documento.cfd_type_id == 0
                    and self.documento.forma_pago == '01'
            ):
                respuesta = (
                    self._interfaz.ventanas.mostrar_mensaje_pregunta(
                        'Con la captura de la partida excede $2000.00, '
                        'que es el monto máximo para facturas capturadas '
                        'en efectivo. ¿Desea continuar?'
                    )
                )
                if not respuesta:
                    return False

        if (
                self._module_id == self.MODULO_VALES
                and self.documento.finish_document == 2
        ):
            return True

        if (
                self._module_id == self.MODULO_VALES
                and self.documento.finish_document == 0
                and total_real > self.cliente.coupons_mount
        ):
            clave_unidad = partida.get('ClaveUnidad', 'KGM')

            if clave_unidad != 'KGM':
                self._interfaz.ventanas.mostrar_mensaje(
                    'Con la captura de la partida excede el monto '
                    'autorizado para este módulo. La partida no se puede '
                    'dividir debido a que su unidad es distinta de Kilo.'
                )
                return False

            respuesta = (
                self._interfaz.ventanas.mostrar_mensaje_pregunta(
                    'Con la captura de la partida excede el monto '
                    'autorizado para este módulo. ¿Desea capturar la '
                    'diferencia en un folio Minisuper?'
                )
            )
            if not respuesta:
                return False

            monto_limite = total_real - self.cliente.coupons_mount
            partida_anterior, partida_nueva = (
                self._modelo.dividir_partida(partida, monto_limite)
            )

            partida_anterior['TipoCaptura'] = tipo_captura
            partida_nueva['TipoCaptura'] = tipo_captura

            self._agregar_partida_tabla(
                partida_anterior,
                document_item_id=-1,
                tipo_captura=tipo_captura,
            )

            self.documento.finish_document = 1

            if not getattr(self.documento, 'adicional_document_id', 0):
                document_id = self._modelo.crear_cabecera_documento(
                    1400,
                    'FG',
                )
                self.documento.adicional_document_id = document_id

            self._modelo.agregar_partida_base_de_datos(partida_nueva)

            if self.documento.document_id:
                self._asignar_folio(self.documento.document_id)

            # La partida ya fue procesada dentro de esta función.
            return False

        if (
                self.cliente.zone_id == 1040
                and self._module_id in (967, 1400, 21, 1319)
                and total_real > self.cliente.remaining_credit
                and self.documento.credit_document_available == 1
        ):
            respuesta = self._ventanas.mostrar_mensaje_pregunta(
                'Con la captura de la partida excede el monto autorizado '
                'para este módulo. ¿Desea continuar?'
            )
            self.documento.credit_document_available = 0

            if not respuesta:
                return False

        return True

    def _asignar_folio(self, document_id):
        folio = self._modelo.obtener_folio_documento(document_id)
        self.documento.folio = folio
        doc_folio =  f"{self.documento.prefix}{folio}"
        self.documento.doc_folio = doc_folio
        self._interfaz.ventanas.insertar_input_componente('lbl_folio', doc_folio)

    def _actualizar_totales_documento(self):
        from decimal import Decimal

        def decimal(valor):
            if valor in (None, ''):
                return Decimal('0')
            return Decimal(str(valor))

        partidas_vigentes = [
            producto
            for producto in self.documento.items
            if int(
                producto.get(
                    'ItemProductionStatusModified',
                    0,
                ) or 0
            ) != 3
        ]

        impuestos_acumulado = Decimal('0')
        retenciones_acumulado = Decimal('0')
        ieps_acumulado = Decimal('0')
        iva_acumulado = Decimal('0')
        subtotal_acumulado = Decimal('0')
        descuento_acumulado = Decimal('0')
        subtotal_descuento_acumulado = Decimal('0')
        costo_acumulado = Decimal('0')

        for producto in partidas_vigentes:
            subtotal = decimal(producto.get('subtotal', 0))
            impuestos = decimal(producto.get('impuestos', 0))
            retenciones = decimal(producto.get('retenciones', 0))
            ieps = decimal(producto.get('ieps', 0))
            iva = decimal(producto.get('iva', 0))

            subtotal_acumulado += subtotal

            if self._module_id == self.MODULO_COMPRAS:
                factor_descuento = decimal(
                    producto.get('DiscountPerc', 0)
                )
                factor_neto = Decimal('1') - factor_descuento

                # Conserva la precisión de cada concepto. El CFDI acumula
                # importes con hasta seis decimales y redondea a moneda sólo
                # el total presentado; truncar cada partida provoca diferencias
                # de centavos que deshacen el ajuste del prorrateo.
                descuento = subtotal * factor_descuento
                subtotal_con_descuento = subtotal - descuento

                impuestos_con_descuento = impuestos * factor_neto
                retenciones_con_descuento = retenciones * factor_neto
                ieps_con_descuento = ieps * factor_neto
                iva_con_descuento = iva * factor_neto

                total_con_descuento = (
                        subtotal_con_descuento
                        + impuestos_con_descuento
                        - retenciones_con_descuento
                )

                cantidad = decimal(
                    producto.get(
                        'cantidad',
                        producto.get('Quantity', 0),
                    )
                )
                costo = decimal(
                    producto.get(
                        'CostPrice',
                        producto.get('UnitPrice', 0),
                    )
                )

                descuento_acumulado += descuento
                subtotal_descuento_acumulado += (
                    subtotal_con_descuento
                )
                impuestos_acumulado += impuestos_con_descuento
                retenciones_acumulado += (
                    retenciones_con_descuento
                )
                ieps_acumulado += ieps_con_descuento
                iva_acumulado += iva_con_descuento
                costo_acumulado += cantidad * costo

                producto['descuento'] = descuento
                producto['descuento_raw'] = descuento
                producto['subtotal_raw'] = subtotal
                producto['subtotal_con_descuento'] = (
                    subtotal_con_descuento
                )
                producto['subtotal_con_descuento_raw'] = (
                    subtotal_con_descuento
                )
                producto['impuestos_con_descuento'] = (
                    impuestos_con_descuento
                )
                producto['iva_con_descuento_raw'] = iva_con_descuento
                producto['ieps_con_descuento_raw'] = ieps_con_descuento
                producto['retenciones_con_descuento_raw'] = (
                    retenciones_con_descuento
                )
                producto['retenciones_con_descuento'] = (
                    retenciones_con_descuento
                )
                producto['total_con_descuento'] = (
                    total_con_descuento
                )

            else:
                impuestos_acumulado += impuestos
                retenciones_acumulado += retenciones
                ieps_acumulado += ieps
                iva_acumulado += iva

        if self._module_id == self.MODULO_COMPRAS:
            totales_fiscales = self._impuestos.doc_totales_fiscales(
                partidas_vigentes
            )

            self.documento.subtotal = totales_fiscales[
                'subtotal_doc_raw'
            ]
            self.documento.total_discount = totales_fiscales[
                'descuento_doc_raw'
            ]
            self.documento.subtotal_with_discount = (
                totales_fiscales['subtotal_con_descuento_doc_raw']
            )
            self.documento.total_tax = totales_fiscales[
                'impuestos_doc_raw'
            ]
            self.documento.total_retention = totales_fiscales[
                'ret_doc_raw'
            ]
            self.documento.total_cost = costo_acumulado
            self.documento.ieps = totales_fiscales['ieps_doc_raw']
            self.documento.iva = totales_fiscales['iva_doc_raw']
            self.documento.total = totales_fiscales['total_doc_raw']

            acumuladores_interfaz = {
                'lbl_subtotal': self.documento.subtotal,
                'lbl_descuento': self.documento.total_discount,
                'lbl_subtotal_con_descuento': (
                    self.documento.subtotal_with_discount
                ),
                'lbl_impuestos': self.documento.total_tax,
                'lbl_retenciones': self.documento.total_retention,
                'lbl_total': self.documento.total,
            }

            for componente, importe in acumuladores_interfaz.items():
                self._ventanas.insertar_input_componente(
                    componente,
                    self._utilerias.convertir_decimal_a_moneda(
                        importe
                    ),
                )

        else:
            totales_documento = (
                self._impuestos.doc_totales_por_documento(
                    partidas_vigentes
                )
            )

            self.documento.total = totales_documento['total_doc']
            # TotalTax representa únicamente impuestos trasladados. Las
            # retenciones se conservan por separado en TotalRetention.
            self.documento.total_tax = iva_acumulado + ieps_acumulado
            self.documento.total_retention = retenciones_acumulado
            self.documento.subtotal = subtotal_acumulado
            self.documento.ieps = ieps_acumulado
            self.documento.iva = iva_acumulado

            self._ventanas.insertar_input_componente(
                'lbl_total',
                self._utilerias.convertir_decimal_a_moneda(
                    self.documento.total
                ),
            )

        self._ventanas.insertar_input_componente(
            'lbl_articulos',
            self._ventanas.numero_filas_treeview(
                'tvw_productos'
            ),
        )

        if (
                self._module_id != self.MODULO_COMPRAS
                and self.cliente.cayal_customer_type_id in (1, 2)
                and self.cliente.credit_block == 0
        ):
            debe = (
                self._utilerias.redondear_valor_cantidad_a_decimal(
                    self.cliente.debt
                )
            )
            debe += self.documento.total

            self._ventanas.insertar_input_componente(
                'lbl_debe',
                self._utilerias.convertir_decimal_a_moneda(debe),
            )

            disponible = (
                self._utilerias.redondear_valor_cantidad_a_decimal(
                    self.cliente.remaining_credit
                )
            )
            disponible -= self.documento.total

            excedido = abs(disponible) if disponible < 0 else 0
            disponible = max(disponible, 0)

            self.documento.credit_document_available = (
                1 if disponible > 0 else 0
            )
            self.documento.credit_exceeded_amount = excedido

            self._ventanas.insertar_input_componente(
                'lbl_restante',
                self._utilerias.convertir_decimal_a_moneda(
                    disponible
                ),
            )

        self._interfaz.ajustar_etiquetas_totales()

    def _remover_product_id_tabla(self, product_id):
        filas = self._interfaz.ventanas.obtener_filas_treeview('tvw_productos')

        for fila in filas:
            valores = self._interfaz.ventanas.procesar_fila_treeview('tvw_productos', fila)
            product_id_tabla = int(valores['ProductID'])
            if product_id_tabla == product_id:
                self._interfaz.ventanas.remover_fila_treeview('tvw_productos', fila)

    def _remover_servicio_a_domicilio(self):
        partidas_servicio = [
            partida
            for partida in self.documento.items
            if int(partida.get('ProductID', 0) or 0)
               == self.PRODUCTO_SERVICIO_DOMICILIO
               and int(
                partida.get(
                    'ItemProductionStatusModified',
                    0,
                ) or 0
            ) != 3
        ]

        for partida in partidas_servicio:
            document_item_id = int(
                partida.get('DocumentItemID', 0) or 0
            )

            if document_item_id:
                # Debe conservarse en memoria para que el procedimiento de
                # pedidos reciba el estado 3 y elimine la partida en la BD.
                partida['ItemProductionStatusModified'] = 3

                self._modelo.agregar_partida_items_documento_extra(
                    partida,
                    'eliminar',
                    f'ELIMINADA AUTOMÁTICAMENTE POR {self._user_name}',
                    partida.get('uuid'),
                )
            else:
                # Si todavía no existe en la BD puede retirarse físicamente.
                self.documento.items = [
                    producto
                    for producto in self.documento.items
                    if producto is not partida
                ]
                self._modelo.cancelar_partida_items_documento_extra(
                    partida.get('uuid')
                )

        self._modelo.servicio_a_domicilio_agregado = False
        self.servicio_a_domicilio_agregado = False

        self._remover_product_id_tabla(
            self.PRODUCTO_SERVICIO_DOMICILIO
        )
        self._actualizar_totales_documento()


    def _filtrar_productos_no_permitidos(self, partida):

        if self._module_id == self.MODULO_VALES: # restriccion por modulo validar funcionamiento
            linea = partida.get('Category1', '')
            if linea not in self._modelo.LINEAS_PRODUCTOS_PERMITIDOS_VALES:
                self._mensajes_de_error(14)
                return

        return partida
