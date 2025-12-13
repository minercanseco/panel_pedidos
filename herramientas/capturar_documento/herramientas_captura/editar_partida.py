import copy
import tkinter as tk

from cayal.ventanas import Ventanas


class EditarPartida:
    def __init__(self, master, interfaz, modelo, controlador, utilerias, base_de_datos, valores_fila_tabla):
        self._master = master
        self._interfaz = interfaz

        self._ventanas_interfaz = self._interfaz.ventanas
        self._modelo = modelo
        self._controlador = controlador
        self._parametros_contpaqi = self._modelo.parametros
        self._documento = self._modelo.documento
        self._utilerias = utilerias
        self._base_de_datos = base_de_datos
        self._valores_fila = valores_fila_tabla
        self._ventanas = Ventanas(self._master)

        self._user_id = self._parametros_contpaqi.id_usuario
        self._user_name = self._base_de_datos.buscar_nombre_de_usuario(self._user_id)
        self._module_id = self._parametros_contpaqi.id_modulo
        self._partida_items_documento = None
        self._info_producto = None
        self._procesando_producto = False

        self._cargar_frames()
        self._cargar_componentes()
        self._cargar_eventos()
        self._rellenar_componentes_forma()
        self._ventanas.configurar_ventana_ttkbootstrap('Editar partida')

        self._ventanas.enfocar_componente('btn_cancelar')

    def _rellenar_componentes_forma(self):
        product_id = int(self._valores_fila['ProductID'])
        quantity = self._valores_fila['Cantidad']
        valor_uuid = self._valores_fila['UUID']
        total = self._valores_fila['Total']

        partida_documento = self._obtener_info_partida_documento(valor_uuid)

        if partida_documento:
            piezas = partida_documento.get('CayalPiece',0)
            if piezas == 0:
                self._ventanas.insertar_input_componente('tbx_cantidad', quantity)
                self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'deseleccionado')


            if  piezas % 1 == 0 and piezas != 0:
                self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'seleccionado')
                self._ventanas.insertar_input_componente('tbx_cantidad', piezas)


        info_producto = self._modelo.buscar_info_productos_por_ids(product_id)[0]
        self._info_producto = self._utilerias.calcular_precio_con_impuesto_producto(info_producto)

        equivalencia = info_producto.get('Equivalencia', 0)
        equivalencia_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

        self._ventanas.insertar_input_componente('tbx_equivalencia', equivalencia_decimal)
        self._ventanas.bloquear_componente('tbx_equivalencia')

        self._ventanas.insertar_input_componente('lbl_monto', total)

        texto = self._modelo.crear_texto_existencia_producto(info_producto)
        self._ventanas.insertar_input_componente('lbl_existencia', texto)

        comentario = partida_documento.get('Comments','')
        self._ventanas.insertar_input_componente('txt_comentario', comentario)

    def _obtener_info_partida_documento(self, uuid_partida):

        partidas_documento = self._documento.items
        self._partida_items_documento = [partida for partida in partidas_documento
                                         if str(partida['uuid']) == str(uuid_partida)][0]

        return self._partida_items_documento

    def _cargar_frames(self):
        frames = {

            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_partida': ('frame_principal', 'Partida:',
                              {'row': 1, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                               'sticky': tk.NSEW}),

            'frame_cantidades': ('frame_partida', None,
                                 {'row': 0, 'column': 0, 'rowspan': 2, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                  'sticky': tk.W}),

            'frame_controles': ('frame_partida', None,
                                {'row': 2, 'column': 1, 'rowspan': 2, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                 'sticky': tk.W}),

            'frame_txt_comentario': ('frame_partida', 'Especificación:[Ctrl+M]',
                                     {'row': 6, 'column': 0, 'columnspan': 5, 'pady': 2, 'padx': 2,
                                      'sticky': tk.NSEW}),

            'frame_totales': ('frame_partida', None,
                              {'row': 1, 'column': 3, 'rowspan': 4, 'columnspan': 2, 'pady': 2, 'padx': 2,
                               'sticky': tk.NE}),

            'frame_botones': ('frame_partida', None,
                              {'row': 10, 'column': 1, 'padx': 0, 'pady': 5, 'sticky': tk.W}),
        }

        self._ventanas.crear_frames(frames)

    def _cargar_componentes(self):
        componentes = {
            'tbx_cantidad': ('frame_cantidades', 10, 'Cantidad:', None),
            'tbx_equivalencia': ('frame_cantidades',
                                 {'row': 0, 'column': 3, 'pady': 5, 'padx': 5, 'sticky': tk.W},
                                 'Equivalencia:', None),

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

            'txt_comentario': ('frame_txt_comentario', None, ' ', None),
            'btn_actualizar': ('frame_botones', 'success', 'Actualizar', '[F8]'),
            'btn_cancelar': ('frame_botones', 'danger', 'Cancelar', '[Esc]'),

        }

        self._ventanas.crear_componentes(componentes)
        self._ventanas.ajustar_componente_en_frame('tbx_equivalencia', 'frame_cantidades')
        self._ventanas.ajustar_componente_en_frame('txt_comentario', 'frame_txt_comentario')
        self._ventanas.ajustar_ancho_componente('tbx_equivalencia', 6)
        self._ventanas.ajustar_ancho_componente('txt_comentario', 60)

    def _cargar_eventos(self):
        eventos = {
            'btn_cancelar': self._master.destroy,
            'btn_actualizar': self._actualizar_partida,
            'tbx_cantidad': self._procesar_producto,
            'chk_monto': lambda *args: self._procesar_producto(),
            'chk_pieza': lambda *args: self._procesar_producto(),
        }
        self._ventanas.cargar_eventos(eventos)

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
                self._modelo.mensajes_de_error(4)

            if equivalencia == 0:
                return 'Unidad'

            if equivalencia != 0:
                return 'Equivalencia'

        if clave_unidad == 'KGM':

            if valor_chk_pieza == 1 and equivalencia == 0:
                self._modelo.mensajes_de_error(3)
                self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'deseleccionado')
                return 'Error'

            if valor_chk_monto == 1 and cantidad == 0:
                self._modelo.mensajes_de_error(0)
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
                self._modelo.mensajes_de_error(2)
                return 'Error'

            if valor_chk_monto == 1:
                return 'Monto'
        return 'Error'

    def _obtener_valores_controles(self):

        equivalencia = self._ventanas.obtener_input_componente('tbx_equivalencia')
        equivalencia_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

        return {
            'valor_chk_monto': self._ventanas.obtener_input_componente('chk_monto'),
            'valor_chk_pieza': self._ventanas.obtener_input_componente('chk_pieza'),
            'cantidad': self._obtener_cantidad_partida(),
            'equivalencia': equivalencia_decimal
        }

    def _obtener_cantidad_partida(self):
        cantidad = self._ventanas.obtener_input_componente('tbx_cantidad')

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

        tipo_calculo = self._determinar_tipo_calculo_partida(info_producto)

        total = 0
        cantidad_real_decimal = 0

        if tipo_calculo != 'Error':
            valores_controles = self._obtener_valores_controles()

            precio_con_impuestos = info_producto.get('SalePriceWithTaxes', 0.0)

            cantidad = valores_controles['cantidad']
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
        self._ventanas.insertar_input_componente('lbl_cantidad', cantidad_real_decimal)

        return {'cantidad': cantidad_real_decimal, 'total': total}

    def _actualizar_lbl_total_moneda(self, total_decimal):
        total_moneda = self._utilerias.convertir_decimal_a_moneda(total_decimal)
        self._ventanas.insertar_input_componente('lbl_monto', total_moneda)

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
            self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'seleccionado')

    def _actualizar_partida(self):
        valores_partida = self._procesar_producto()

        if valores_partida:
            document_item_id = int(self._valores_fila['DocumentItemID'])
            cantidad_original = self._utilerias.redondear_valor_cantidad_a_decimal(self._valores_fila['Cantidad'])
            cantidad_nueva = valores_partida['cantidad']

            comentario = f'EDITADO POR {self._user_name}: Cant {cantidad_original} --> Cant {cantidad_nueva}'

            uuid_partida = str(self._partida_items_documento['uuid'])

            # Crear partida original antes de cualquier modificación y hacer una copia profunda
            partida_original = self._utilerias.crear_partida(self._info_producto, cantidad_original)

            for partida in self._documento.items:
                uuid_partida_items = str(partida['uuid'])
                if uuid_partida == uuid_partida_items:
                    # Crear partida actualizada solo si encontramos la partida correspondiente
                    partida_actualizada = self._utilerias.crear_partida(self._info_producto, cantidad_nueva)

                    valor_pieza = self._ventanas.obtener_input_componente('chk_pieza')
                    piezas = partida_actualizada['CayalPiece'] if valor_pieza == 1 else 0

                    # Actualizar valores de la partida en el documento
                    partida['ItemProductionStatusModified'] = 2 if document_item_id > 0 else 0
                    partida['cantidad'] = cantidad_nueva
                    partida['subtotal'] = partida_actualizada['subtotal']
                    partida['total'] = partida_actualizada['total']
                    partida['CayalPiece'] = piezas #self._ventanas.obtener_input_componente('chk_pieza')
                    partida['monto_cayal'] = self._ventanas.obtener_input_componente('chk_monto')
                    partida['Comments'] = self._ventanas.obtener_input_componente('txt_comentario')
                    partida['CreatedBy'] = self._user_id
                    partida['DocumentItemID'] = document_item_id

                    # Actualizar la tabla UI con los nuevos valores
                    filas = self._ventanas_interfaz.obtener_filas_treeview('tvw_productos')
                    for fila in filas:
                        valores_fila = self._ventanas_interfaz.procesar_fila_treeview('tvw_productos', fila)
                        uuid_tabla = str(valores_fila['UUID'])
                        if uuid_tabla == uuid_partida:

                            valores_fila['Cantidad'] = cantidad_nueva
                            valores_fila['Importe'] = "{:.2f}".format(partida_actualizada['subtotal'])
                            valores_fila['Impuestos'] = "{:.2f}".format(partida_actualizada['impuestos'])
                            valores_fila['Total'] = "{:.2f}".format(partida_actualizada['total'])
                            valores_fila['Piezas'] = piezas
                            self._ventanas_interfaz.actualizar_fila_treeview_diccionario('tvw_productos', fila,
                                                                                         valores_fila)

            # Redondear valores de cantidad
            cantidad_original = self._utilerias.convertir_valor_a_decimal(cantidad_original)
            cantidad_nueva = self._utilerias.convertir_valor_a_decimal(cantidad_nueva)

            if cantidad_original == cantidad_nueva:
                comentario  = self._ventanas.obtener_input_componente('txt_comentario')
                comentario = f'EDITADO POR {self._user_name}: {comentario}'
            else:
                # actualiza los totales de la nota para posteriores modificaciones
                self._controlador.actualizar_totales_documento()

            # respalda la partida extra para tratamiento despues del cierre del documento
            self._modelo.agregar_partida_items_documento_extra(partida_original, 'editar', comentario, uuid_partida)

        # Solo aplica para el módulo de pedidos
        if self._module_id == 1687:
            total_documento = self._documento.total

            if self._controlador.servicio_a_domicilio_agregado:
                total_sin_servicio = total_documento - self._modelo.documento.delivery_cost

                if total_sin_servicio >= 200:
                    self._controlador.remover_servicio_a_domicilio()
            else:
                if total_documento < 200:
                    self._controlador.agregar_servicio_a_domicilio()

        self._master.destroy()

    def _procesar_producto(self, event=None):

        if self._procesando_producto:
            return

        info_producto = self._info_producto

        try:
            if info_producto:
                self._procesando_producto = True

                cantidad = self._obtener_cantidad_partida()

                chk_pieza = self._ventanas.obtener_input_componente('chk_pieza')
                if chk_pieza == 1 and cantidad % 1 != 0:
                    self._ventanas.mostrar_mensaje(mensaje='La cantidad de piezas deben ser valores no fraccionarios.',
                                                   master=self._master)
                    return False

                self._ventanas.insertar_input_componente('tbx_cantidad', cantidad)

                return self._calcular_valores_partida(info_producto)
        finally:
            self._procesando_producto = False

