import copy
import re
import tkinter as tk
import pyperclip

from cayal.ventanas import Ventanas
from cayal.util import Utilerias

from agregar_epecificaciones import AgregarEspecificaciones


class AgregarPartidaManualmente:
    def __init__(self, master, modelo, documento, componentes_captura, portapapeles):
        self._master = master
        self._modelo = modelo
        self._componentes_captura = componentes_captura
        self.documento = documento
        self._items = self.documento.items

        self._ventanas = Ventanas(self._master)
        self._utilerias = Utilerias()

        self._inicializar_variables_de_instancia()
        self._portapapeles = portapapeles

        self._cargar_frames()
        self._cargar_componentes()
        self._rellenar_componentes()
        self._agregar_eventos()
        self._agregar_hotkeys()
        self._agregar_validaciones()
        self._agregando_producto = False

        self._ventanas.configurar_ventana_ttkbootstrap()
        self._ventanas.enfocar_componente('tbx_buscar')

    def _inicializar_variables_de_instancia(self):
        self._procesando_seleccion = False
        self._info_partida_seleccionada = {}

    def _cargar_frames(self):

        frames = {

            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_buscar': ('frame_principal', 'Buscar',
                             {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                              'sticky': tk.NSEW}),

            'frame_tbx_buscar': ('frame_buscar', None,
                                 {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                  'sticky': tk.NSEW}),

            'frame_cbx_buscar': ('frame_buscar', None,
                                 {'row': 0, 'column': 3, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                  'sticky': tk.NSEW}),

            'frame_partida': ('frame_principal', 'Partida:',
                              {'row': 2, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                               'sticky': tk.NSEW}),

            'frame_cantidades': ('frame_partida', None,
                                 {'row': 0, 'column': 0, 'rowspan': 2, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                  'sticky': tk.W}),

            'frame_controles': ('frame_partida', None,
                                {'row': 3, 'column': 1, 'rowspan': 2, 'columnspan': 2, 'pady': 2, 'padx': 50,
                                 'sticky': tk.W}),

            'frame_totales': ('frame_partida', None,
                              {'row': 1, 'column': 3, 'rowspan': 4, 'columnspan': 2, 'pady': 2, 'padx': 2,
                               'sticky': tk.NE}),

            'frame_txt_comentario': ('frame_partida', 'Especificación:[Ctrl+M]',
                                     {'row': 6, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                      'sticky': tk.NSEW}),

            'frame_txt_portapapeles': ('frame_partida', 'Portapapeles:[Ctrl+P]',
                                       {'row': 6, 'column': 3, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                        'sticky': tk.NSEW}),

            'frame_tabla': ('frame_principal', 'Productos [Ctrl+T]',
                            {'row': 3, 'column': 0, 'columnspan': 4, 'pady': 2, 'padx': 2,
                             'sticky': tk.NSEW}),

            'frame_botones': ('frame_partida', None,
                              {'row': 10, 'column': 1, 'padx': 0, 'pady': 5, 'sticky': tk.W}),

        }

        self._ventanas.crear_frames(frames)

    def _cargar_componentes(self):

        componentes = {
            'cbx_tipo_busqueda': ('frame_cbx_buscar', None, 'Tipo:', '[Ctrl+F]'),
            'tbx_buscar': ('frame_tbx_buscar', None, 'Buscar:', '[Ctrl+B]'),

            'tbx_cantidad': ('frame_cantidades', 10, 'Cantidad:', '[Ctrl+C]'),
            'tbx_equivalencia': ('frame_cantidades',
                                 {'row': 2, 'column': 3, 'pady': 5, 'padx': 5, 'sticky': tk.W},
                                 'Equivalencia:', None),

            'txt_comentario': ('frame_txt_comentario', None, ' ', None),
            'txt_portapapeles': ('frame_txt_portapapeles', None, ' ', None),

            'lbl_monto_texto': ('frame_totales',
                                {'width': 10, 'text': 'TOTAL:', 'style': 'inverse-danger', 'anchor': 'e',
                                 'font': ('Consolas', 16, 'bold')},
                                {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                None),

            'lbl_monto': ('frame_totales',
                          {'width': 10, 'text': '$0.00', 'style': 'inverse-danger', 'anchor': 'e',
                           'font': ('Consolas', 16, 'bold')},
                          {'row': 0, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                          None),

            'lbl_cantidad_texto': ('frame_totales',
                                   {'width': 10, 'text': 'CANTIDAD:', 'style': 'inverse-danger', 'anchor': 'e',
                                    'font': ('Consolas', 16, 'bold')},
                                   {'row': 1, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                   None),

            'lbl_cantidad': ('frame_totales',
                             {'width': 10, 'text': '0.00', 'style': 'inverse-danger', 'anchor': 'e',
                              'font': ('Consolas', 16, 'bold')},
                             {'row': 1, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                             None),

            'lbl_existencia_texto': ('frame_totales',
                                     {'width': 10, 'text': 'EXISTENCIA:', 'style': 'inverse-danger', 'anchor': 'e',
                                      'font': ('Consolas', 15, 'bold')},
                                     {'row': 2, 'column': 0, 'padx': 0, 'sticky': tk.NSEW},
                                     None),

            'lbl_existencia': ('frame_totales',
                               {'width': 10, 'text': '0.00', 'style': 'inverse-danger', 'anchor': 'e',
                                'font': ('Consolas', 16, 'bold')},
                               {'row': 2, 'column': 1, 'padx': 0, 'sticky': tk.NSEW},
                               None),

            'chk_pieza': ('frame_controles',
                          {'row': 0, 'column': 3, 'pady': 5, 'padx': 5, 'sticky': tk.W},
                          'Pieza', '[F1]'),

            'chk_monto': ('frame_controles',
                          {'row': 0, 'column': 5, 'pady': 5, 'padx': 5, 'sticky': tk.W},
                          'Monto', '[F4]'),

            'tvw_productos': ('frame_tabla', self._crear_columnas_tabla(), 10, None),
            'btn_agregar': ('frame_botones', 'success', 'Agregar', '[F8]'),
            'btn_especificaciones': ('frame_botones', 'primary', 'Especificación', '[Ctrl+E]'),
            'btn_ofertas': ('frame_botones', 'info', 'Ofertas', '[F9]'),
            'btn_copiar': ('frame_botones', 'warning', 'Copiar', '[F12]'),

        }

        self._ventanas.crear_componentes(componentes)
        self._ventanas.ajustar_ancho_componente('tbx_equivalencia', 6)

        self._ventanas.ajustar_componente_en_frame('txt_comentario', 'frame_txt_comentario')
        self._ventanas.ajustar_componente_en_frame('txt_portapapeles', 'frame_txt_portapapeles')
        self._ventanas.ajustar_alto_componente('txt_comentario', 6)
        self._ventanas.ajustar_alto_componente('txt_portapapeles', 6)

    def _rellenar_componentes(self):

        # 0 por clave o termino /// 1 por linea
        tipo_busqueda = ['Término', 'Línea']
        self._ventanas.rellenar_cbx('cbx_tipo_busqueda', tipo_busqueda, 'Sin seleccione')
        cbx_tipo_busqueda = self._ventanas.componentes_forma['cbx_tipo_busqueda']
        cbx_tipo_busqueda.set('Término')

        self._ventanas.insertar_input_componente('tbx_cantidad', 1)
        self._ventanas.insertar_input_componente('tbx_equivalencia', 0.0)
        self._ventanas.bloquear_componente('tbx_equivalencia')

        self._ventanas.insertar_input_componente('txt_portapapeles', self._portapapeles)

    def _crear_columnas_tabla(self):
        return [
            {"text": "Código", "stretch": False, 'width': 130, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Descripción", "stretch": False, 'width': 460, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Precio", "stretch": False, 'width': 70, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "ProductID", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "ClaveUnidad", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "Category1", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
        ]

    def _rellenar_frame_info(self):

        estilo_auxiliar = {
            'foreground': 'white',
            'background': '#E30421',
            'font': ('Consolas', 14, 'bold'),
            # 'anchor': 'center'
        }

        estilo_total = {
            'foreground': 'white',
            'background': '#E30421',
            'font': ('consolas', 27, 'bold'),
            # 'anchor': 'center'
        }

        componentes = {
            'lbl_producto': ('frame_info', estilo_auxiliar, None, None)

        }

        self._ventanas.crear_componentes(componentes)

    def _agregar_eventos(self):
        eventos = {
            'btn_ofertas': lambda: self._buscar_ofertas(),
            'btn_especificaciones': lambda: self._agregar_especicificaciones(),
            'btn_agregar': lambda: self._agregar_partida(),
            'btn_copiar': lambda: self._copiar_productos(),

            'tbx_buscar': lambda event: self._buscar_productos_manualmente(),
            'tbx_cantidad': lambda event: self._selecionar_producto_tabla(),

            'chk_monto': lambda *args: self._selecionar_producto_tabla(),
            'chk_pieza': lambda *args: self._selecionar_producto_tabla(),
            'tvw_productos': (lambda event: self._selecionar_producto_tabla(configurar_forma=True), 'seleccion'),
        }
        self._ventanas.cargar_eventos(eventos)

    def _agregar_hotkeys(self):
        hotkeys = {
            'Ctrl+B': lambda: self._ventanas.enfocar_componente('tbx_buscar'),
            'Ctrl+C': lambda: self._ventanas.enfocar_componente('tbx_cantidad'),
            'Ctrl+F': lambda: self._ventanas.enfocar_componente('cbx_tipo_busqueda'),
            'Ctrl+M': lambda: self._ventanas.enfocar_componente('txt_comentario'),
            'Ctrl+T': lambda: self._ventanas.enfocar_componente('tvw_productos'),
            'Ctrl+P': lambda: self._ventanas.enfocar_componente('txt_portapapeles'),
            'Ctrl+E': lambda: self._agregar_especicificaciones(),

            'F1': lambda: self._activar_chk_pieza(),
            'F4': lambda: self._activar_chk_monto(),

            'F8': lambda: self._agregar_partida(),
            'F9': lambda: self._copiar_productos(),
            'F12': lambda: self._buscar_ofertas(),

        }

        self._ventanas.agregar_hotkeys_forma(hotkeys)

    def _activar_chk_pieza(self):
        if self._tabla_con_seleccion_valida():
            self._ventanas.cambiar_estado_checkbutton('chk_monto', 'deseleccionado')
            self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'seleccionado')
            self._selecionar_producto_tabla()

    def _activar_chk_monto(self):
        if self._tabla_con_seleccion_valida():
            self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'deseleccionado')
            self._ventanas.cambiar_estado_checkbutton('chk_monto', 'seleccionado')

            precio_unidad = self._info_partida_seleccionada.get('SalePriceWithTaxes', 10)
            self._ventanas.insertar_input_componente('tbx_cantidad', precio_unidad)

            self._selecionar_producto_tabla()

    def _agregar_validaciones(self):
        self._ventanas.agregar_validacion_tbx('tbx_cantidad', 'cantidad')

    def _buscar_productos_manualmente(self, event=None):

        tipo_busqueda = self._ventanas.obtener_input_componente('cbx_tipo_busqueda')
        termino_buscado = self._ventanas.obtener_input_componente('tbx_buscar')

        consulta = self._modelo.buscar_productos(termino_buscado, tipo_busqueda)

        if not consulta:
            self._modelo.mensajes_de_error(6, self._master)
            self._limpiar_controles_forma()
            self._ventanas.enfocar_componente('tbx_buscar')
            self._ventanas.insertar_input_componente('tbx_cantidad', 1.00)
            return

        ids_productos = self._modelo.obtener_product_ids_consulta(consulta)
        consulta_productos = self._modelo.buscar_info_productos_por_ids(ids_productos)

        consulta_productos_impuestos = self._modelo.agregar_impuestos_productos(consulta_productos)

        self._modelo.consulta_productos = consulta_productos_impuestos
        self._rellenar_tabla_productos(consulta_productos_impuestos)

    def _limpiar_controles_forma(self):
        componentes = [
            'tbx_equivalencia',
            'lbl_existencia',
            'lbl_monto',
            'chk_pieza',
            'chk_monto',
            'txt_comentario',
            'tvw_productos',
            'tbx_cantidad'
        ]
        self._ventanas.limpiar_componentes(componentes)
        self._ventanas.enfocar_componente('tbx_buscar')

    def _rellenar_tabla_productos(self, consulta_productos):
        registros_tabla = []
        tabla = self._ventanas.componentes_forma['tvw_productos']

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

        self._ventanas.rellenar_treeview(tabla, self._crear_columnas_tabla(), registros_tabla)
        self._colorear_productos_ofertados()
        if self._ventanas.numero_filas_treeview('tvw_productos') == 1:
            self._ventanas.seleccionar_fila_treeview('tvw_productos', 1)

    def _selecionar_producto_tabla(self, configurar_forma=None):

        if self._procesando_seleccion:
            return

        self._procesando_seleccion = True

        try:
            fila = self._tabla_con_seleccion_valida()
            if not fila:
                return

            valores = self._ventanas.obtener_valores_fila_treeview('tvw_productos', fila)

            product_id = int(valores[3])

            info_producto = copy.deepcopy(self._modelo.buscar_informacion_producto(product_id))

            if info_producto:
                self._product_id = product_id

                if configurar_forma:
                    self._configurar_forma_segun_producto(info_producto)

                cantidad = self._obtener_cantidad_partida()
                self._ventanas.insertar_input_componente('tbx_cantidad', cantidad)

                self._product_id = product_id
                self._calcular_valores_partida(info_producto)
                self._info_partida_seleccionada = info_producto

        finally:
            self._procesando_seleccion = False

    def _insertar_equivalencia(self, equivalencia):

        equivalencia = str(equivalencia)
        equivalencia_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

        self._ventanas.desbloquear_componente('tbx_equivalencia')
        self._ventanas.insertar_input_componente('tbx_equivalencia', equivalencia_decimal)
        self._ventanas.bloquear_componente('tbx_equivalencia')

        return equivalencia_decimal

    def _configurar_forma_segun_producto(self, info_producto):

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

    def _obtener_variables_partida(self):

        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_productos')
        valores = self._ventanas.obtener_valores_fila_treeview('tvw_productos', fila)

        precio = valores[2]
        precio_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(precio)

        equivalencia = self._ventanas.obtener_input_componente('tbx_equivalencia')
        equivalencia_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

        product_id = int(valores[3])
        clave_unidad = valores[4]

        return {
            'precio_decimal': precio_decimal,
            'equivalencia_decimal': equivalencia_decimal,
            'product_id': product_id,
            'clave_unidad': clave_unidad
        }

    def _calcular_valores_partida(self, info_producto):

        def calcular_cantidad_real(tipo_calculo, equivalencia, cantidad):

            if tipo_calculo == 'Equivalencia':
                return cantidad * equivalencia

            if tipo_calculo in ('Unidad', 'Monto'):
                return cantidad

        tipo_calculo = self._determinar_tipo_calculo_partida(info_producto)
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
                    self._ventanas.insertar_input_componente('tbx_cantidad', cantidad_decimal)
                total = cantidad_real_decimal * precio_con_impuestos

            if tipo_calculo == 'Unidad':
                total = cantidad_real_decimal * precio_con_impuestos

            if tipo_calculo == 'Monto':
                total = cantidad
                cantidad = total / precio_con_impuestos

                cantidad_real_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(cantidad)

        self._actualizar_lbl_total_moneda(total)
        texto = self._modelo.crear_texto_existencia_producto(info_producto)
        self._ventanas.insertar_input_componente('lbl_existencia', texto)

        unidad = info_producto.get('Unit', 'PIEZA')
        product_id = int(info_producto.get('ProductID', 0))

        texto_cantidad = self._modelo.crear_texto_cantidad_producto(cantidad_real_decimal, unidad, product_id)
        self._ventanas.insertar_input_componente('lbl_cantidad', texto_cantidad)
        return {'cantidad': cantidad_real_decimal, 'cantidad_piezas': cantidad_piezas, 'total': total}

    def _obtener_valores_controles(self):

        equivalencia = self._ventanas.obtener_input_componente('tbx_equivalencia')
        equivalencia_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

        return {
            'valor_chk_monto': self._ventanas.obtener_input_componente('chk_monto'),
            'valor_chk_pieza': self._ventanas.obtener_input_componente('chk_pieza'),
            'cantidad': self._obtener_cantidad_partida(),
            'equivalencia': equivalencia_decimal
        }

    def _determinar_tipo_calculo_partida(self, info_producto):

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
                self._ventanas.insertar_input_componente('tbx_cantidad', 1)

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

    def _tabla_con_seleccion_valida(self):
        if self._ventanas.numero_filas_treeview('tvw_productos') == 0:
            return False

        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_productos')

        if len(fila) > 1 or len(fila) < 1:
            return False

        return fila

    def _obtener_cantidad_partida(self):
        cantidad = self._ventanas.obtener_input_componente('tbx_cantidad')

        if not cantidad or not self._utilerias.es_cantidad(cantidad):
            return self._utilerias.redondear_valor_cantidad_a_decimal(0)

        cantidad_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(cantidad)

        return self._utilerias.redondear_valor_cantidad_a_decimal(1) if cantidad_decimal <= 0 else cantidad_decimal

    def _actualizar_lbl_total_moneda(self, total_decimal):
        total_moneda = self._utilerias.convertir_decimal_a_moneda(total_decimal)
        self._ventanas.insertar_input_componente('lbl_monto', total_moneda)

    def _buscar_ofertas(self, rellenar_tabla=True):
        if not self._modelo.consulta_productos_ofertados:
            self._modelo.buscar_productos_ofertados_cliente()

        if rellenar_tabla:
            self._modelo.consulta_productos = self._modelo.consulta_productos_ofertados_btn
            self._rellenar_tabla_productos(self._modelo.consulta_productos)
            self._colorear_productos_ofertados()

    def _colorear_productos_ofertados(self):
        filas = self._ventanas.obtener_filas_treeview('tvw_productos')
        if not filas:
            return

        for fila in filas:
            if not fila:
                continue

            valores_fila = self._ventanas.procesar_fila_treeview('tvw_productos',fila)
            product_id = valores_fila['ProductID']
            producto = str(valores_fila['Descripción'])

            if product_id in self._modelo.products_ids_ofertados:
                producto_actualizado = self._actualizar_nombre_producto_ofertado(producto, product_id)
                valores_fila['Descripción'] = producto_actualizado
                self._ventanas.actualizar_fila_treeview_diccionario('tvw_productos', fila, valores_fila)
                self._ventanas.colorear_fila_seleccionada_treeview('tvw_productos', fila, color='warning')

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

    def _agregar_partida(self):
        if not self._tabla_con_seleccion_valida():
            return

        cantidad_control = self._obtener_cantidad_partida()

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
                comentarios = self._ventanas.obtener_input_componente('txt_comentario')

                partida['Comments'] = comentarios


                if chk_pieza == 1 and partida['CayalPiece'] % 1 != 0:
                    self._ventanas.mostrar_mensaje('La cantidad de piezas deben ser valores no fraccionarios.')
                    return

                self._modelo.agregar_partida_tabla(partida, document_item_id=0, tipo_captura=1, unidad_cayal=chk_pieza,
                                                   monto_cayal=chk_monto)

                self._ventanas.insertar_input_componente('tbx_cantidad', 1)
                self._ventanas.limpiar_componentes('txt_comentario')
                self._ventanas.limpiar_componentes('tbx_buscar')
                self._ventanas.enfocar_componente('tbx_buscar')


            finally:
                self._agregando_producto = False

    def _copiar_productos(self):
        filas = self._ventanas.obtener_seleccion_filas_treeview('tvw_productos')
        datos_tabla = []
        for fila in filas:
            valores_fila = self._ventanas.obtener_valores_fila_treeview('tvw_productos', fila)
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

    def _agregar_especicificaciones(self):
        ventana = self._ventanas.crear_popup_ttkbootstrap(titulo='Agregar especificacion')
        instancia = AgregarEspecificaciones(ventana, self._modelo.base_de_datos)
        ventana.wait_window()
        especificaciones = instancia.especificaciones_texto
        if especificaciones:
            comentario_original = self._ventanas.obtener_input_componente('txt_comentario')
            nuevo_comentario = ''

            if comentario_original != '':

                nuevo_comentario = f'{comentario_original}' \
                                   f'{especificaciones}'

            if comentario_original == '':
                nuevo_comentario = f'{especificaciones}'

            self._ventanas.insertar_input_componente('txt_comentario', nuevo_comentario)
