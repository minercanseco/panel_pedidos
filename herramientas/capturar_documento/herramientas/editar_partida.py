import copy
import tkinter as tk
from decimal import Decimal, InvalidOperation, ROUND_DOWN

from cayal.ventanas import Ventanas


class EditarPartida:
    def __init__(
            self,
            master,
            interfaz,
            modelo,
            utilerias,
            base_de_datos,
            valores_fila_tabla,
            actualizar_totales=None,
            agregar_servicio_domicilio=None,
            remover_servicio_domicilio=None,
    ):
        self._master = master
        self._interfaz = interfaz

        self._ventanas_interfaz = self._interfaz.ventanas
        self._modelo = modelo
        self._parametros_contpaqi = self._modelo.parametros_contpaqi
        self._documento = self._modelo.documento
        self._utilerias = utilerias
        self._base_de_datos = base_de_datos
        self._valores_fila = valores_fila_tabla
        self._ventanas = Ventanas(self._master)
        self._actualizar_totales = actualizar_totales
        self._agregar_servicio_domicilio = agregar_servicio_domicilio
        self._remover_servicio_domicilio = remover_servicio_domicilio

        self._user_id = self._parametros_contpaqi.id_usuario
        self._user_name = self._modelo.obtener_nombre_usuario(self._user_id)
        self._module_id = self._parametros_contpaqi.id_modulo
        self._partida_items_documento = None
        self._info_producto = None
        self._procesando_producto = False
        self._actualizacion_pendiente = None
        self.partida_actualizada = False

        self._cargar_frames()
        self._cargar_componentes()
        self._cargar_eventos()
        self._rellenar_componentes_forma()
        self._ventanas.configurar_ventana_ttkbootstrap('Editar partida')

        self._ventanas.enfocar_componente('tbx_cantidad')

    def _rellenar_componentes_forma(self):
        product_id = int(self._valores_fila['ProductID'])
        quantity = self._valores_fila['Cantidad']
        valor_uuid = self._valores_fila['UUID']
        total = self._valores_fila['Total']

        partida_documento = self._obtener_info_partida_documento(valor_uuid)

        self._ventanas.insertar_input_componente(
            'lbl_producto',
            partida_documento.get(
                'ProductName',
                self._valores_fila.get('Descripción', ''),
            ),
        )
        self._ventanas.insertar_input_componente(
            'lbl_clave',
            partida_documento.get(
                'ProductKey',
                self._valores_fila.get('Código', ''),
            ),
        )

        if partida_documento:
            piezas = partida_documento.get('CayalPiece',0)
            if piezas == 0:
                self._ventanas.insertar_input_componente(
                    'tbx_cantidad',
                    self._truncar_para_presentacion(quantity),
                )
                self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'deseleccionado')


            if  piezas % 1 == 0 and piezas != 0:
                self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'seleccionado')
                self._ventanas.insertar_input_componente(
                    'tbx_cantidad',
                    self._truncar_para_presentacion(piezas),
                )


        consulta_producto = self._modelo.buscar_info_productos_por_ids(
            product_id
        )
        if not consulta_producto:
            raise ValueError('No fue posible recuperar la información del producto.')

        info_producto = copy.deepcopy(consulta_producto[0])
        self._info_producto = self._utilerias.calcular_precio_con_impuesto_producto(info_producto)

        # Editar cantidad no debe sustituir el precio que ya tiene la partida.
        precio_partida = partida_documento.get('precio')
        if precio_partida not in (None, ''):
            self._info_producto['SalePriceWithTaxes'] = (
                self._utilerias.redondear_valor_cantidad_a_decimal(
                    precio_partida
                )
            )

        equivalencia = info_producto.get('Equivalencia', 0)
        equivalencia_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

        self._ventanas.insertar_input_componente(
            'tbx_equivalencia',
            self._truncar_para_presentacion(equivalencia_decimal),
        )
        self._ventanas.bloquear_componente('tbx_equivalencia')

        self._actualizar_lbl_total_moneda(total)

        texto = self._modelo.crear_texto_existencia_producto(info_producto)
        self._ventanas.insertar_input_componente('lbl_existencia', texto)

        comentario = partida_documento.get('Comments','')
        self._ventanas.insertar_input_componente('txt_comentario', comentario)

    @staticmethod
    def _truncar_para_presentacion(valor):
        """Trunca a dos decimales sin modificar el valor almacenado."""
        try:
            numero = Decimal(str(valor or 0)).quantize(
                Decimal('0.01'),
                rounding=ROUND_DOWN,
            )
        except (InvalidOperation, TypeError, ValueError):
            numero = Decimal('0.00')
        return f'{numero:.2f}'

    def _obtener_info_partida_documento(self, uuid_partida):
        self._partida_items_documento = next(
            (
                partida for partida in self._documento.items
                if str(partida.get('uuid', '')) == str(uuid_partida)
            ),
            None,
        )

        if self._partida_items_documento is None:
            raise ValueError(
                'No fue posible localizar la partida seleccionada.'
            )

        return self._partida_items_documento

    def _cargar_frames(self):
        frames = {

            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_partida': ('frame_principal', 'Partida:',
                              {'row': 1, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                               'sticky': tk.NSEW}),

            'frame_producto': ('frame_partida', 'Producto',
                               {'row': 0, 'column': 0, 'columnspan': 5,
                                'pady': 4, 'padx': 4, 'sticky': tk.NSEW}),

            'frame_cantidades': ('frame_partida', None,
                                 {'row': 1, 'column': 0, 'rowspan': 2,
                                  'columnspan': 3, 'pady': 4, 'padx': 4,
                                  'sticky': tk.EW}),

            'frame_controles': ('frame_partida', None,
                                {'row': 3, 'column': 0, 'rowspan': 2, 'columnspan': 2, 'pady': 4, 'padx': 4,
                                 'sticky': tk.W}),

            'frame_txt_comentario': ('frame_partida', 'Especificación:[Ctrl+M]',
                                     {'row': 6, 'column': 0, 'columnspan': 5, 'pady': 4, 'padx': 4,
                                      'sticky': tk.NSEW}),

            'frame_totales': ('frame_partida', None,
                              {'row': 1, 'column': 3, 'rowspan': 4, 'columnspan': 2, 'pady': 4, 'padx': 4,
                               'sticky': tk.NE}),

            'frame_botones': ('frame_partida', None,
                              {'row': 10, 'column': 0, 'columnspan': 5,
                               'padx': 4, 'pady': 8, 'sticky': tk.E}),
        }

        self._ventanas.crear_frames(frames)

    def _cargar_componentes(self):
        componentes = {
            'lbl_producto_texto': ('frame_producto',
                                   {'text': 'Descripción:', 'anchor': 'w'},
                                   {'row': 0, 'column': 0, 'padx': 4, 'sticky': tk.W}, None),
            'lbl_producto': ('frame_producto',
                             {'text': '', 'anchor': 'w', 'font': ('TkDefaultFont', 11, 'bold')},
                             {'row': 0, 'column': 1, 'padx': 4, 'sticky': tk.W}, None),
            'lbl_clave_texto': ('frame_producto',
                                {'text': 'Código:', 'anchor': 'w'},
                                {'row': 1, 'column': 0, 'padx': 4, 'sticky': tk.W}, None),
            'lbl_clave': ('frame_producto',
                          {'text': '', 'anchor': 'w'},
                          {'row': 1, 'column': 1, 'padx': 4, 'sticky': tk.W}, None),
            'tbx_cantidad': ('frame_cantidades',
                             {'row': 0, 'column': 1, 'pady': 5,
                              'padx': (5, 18), 'sticky': tk.W},
                             'Cantidad:', None),
            'tbx_equivalencia': ('frame_cantidades',
                                 {'row': 0, 'column': 3, 'pady': 5,
                                  'padx': 5, 'sticky': tk.W},
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
        self._ventanas.ajustar_componente_en_frame('tbx_cantidad', 'frame_cantidades')
        self._ventanas.ajustar_componente_en_frame('tbx_equivalencia', 'frame_cantidades')
        self._ventanas.ajustar_componente_en_frame('txt_comentario', 'frame_txt_comentario')
        self._ventanas.ajustar_ancho_componente('tbx_cantidad', 8)
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

        tbx_cantidad = self._ventanas.componentes_forma.get(
            'tbx_cantidad'
        )
        if tbx_cantidad is not None:
            tbx_cantidad.bind(
                '<KeyRelease>',
                self._programar_actualizacion_dinamica,
                add='+',
            )

    def _programar_actualizacion_dinamica(self, event=None):
        """Actualiza la vista previa después de una pausa breve al escribir."""
        if self._actualizacion_pendiente is not None:
            try:
                self._master.after_cancel(self._actualizacion_pendiente)
            except (tk.TclError, ValueError):
                pass

        self._actualizacion_pendiente = self._master.after(
            180,
            self._actualizar_vista_previa,
        )

    def _actualizar_vista_previa(self):
        self._actualizacion_pendiente = None
        cantidad = self._ventanas.obtener_input_componente(
            'tbx_cantidad'
        )

        # Mientras el usuario está escribiendo puede existir temporalmente un
        # valor vacío, un punto o un signo. No se muestra un error en ese lapso.
        if cantidad in (None, '', '.', '-', '-.'):
            self._actualizar_lbl_total_moneda(0)
            self._ventanas.insertar_input_componente(
                'lbl_cantidad',
                '0.00',
            )
            return

        if not self._utilerias.es_cantidad(cantidad):
            return

        self._procesar_producto(
            formatear_entrada=False,
            mostrar_errores=False,
        )

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
                self._mostrar_mensaje(
                    'El cálculo por monto no aplica para esta unidad.'
                )

            if equivalencia == 0:
                return 'Unidad'

            if equivalencia != 0:
                return 'Equivalencia'

        if clave_unidad == 'KGM':

            if valor_chk_pieza == 1 and equivalencia == 0:
                self._mostrar_mensaje(
                    'El producto no tiene una equivalencia configurada.'
                )
                self._ventanas.cambiar_estado_checkbutton('chk_pieza', 'deseleccionado')
                return 'Error'

            if valor_chk_monto == 1 and cantidad == 0:
                self._mostrar_mensaje(
                    'Debe proporcionar un monto mayor que cero.'
                )
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
                self._mostrar_mensaje(
                    'El monto debe ser mayor que uno.'
                )
                return 'Error'

            if valor_chk_monto == 1:
                return 'Monto'
        return 'Error'

    def _mostrar_mensaje(self, mensaje):
        self._ventanas.mostrar_mensaje(
            mensaje=mensaje,
            master=self._master,
        )

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
                    self._ventanas.insertar_input_componente(
                        'tbx_cantidad',
                        self._truncar_para_presentacion(cantidad_decimal),
                    )

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
        self._ventanas.insertar_input_componente(
            'lbl_cantidad',
            self._truncar_para_presentacion(cantidad_real_decimal),
        )

        return {'cantidad': cantidad_real_decimal, 'total': total}

    def _actualizar_lbl_total_moneda(self, total_decimal):
        total_truncado = Decimal(
            self._truncar_para_presentacion(total_decimal)
        )
        total_moneda = self._utilerias.convertir_decimal_a_moneda(
            total_truncado
        )
        self._ventanas.insertar_input_componente('lbl_monto', total_moneda)

    def _insertar_equivalencia(self, equivalencia):

        equivalencia = str(equivalencia)
        equivalencia_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(equivalencia)

        self._ventanas.desbloquear_componente('tbx_equivalencia')
        self._ventanas.insertar_input_componente(
            'tbx_equivalencia',
            self._truncar_para_presentacion(equivalencia_decimal),
        )
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
        if not valores_partida:
            return

        partida = self._partida_items_documento
        uuid_partida = str(partida.get('uuid', ''))
        document_item_id = int(partida.get('DocumentItemID', 0) or 0)

        cantidad_original = (
            self._utilerias.redondear_valor_cantidad_a_decimal(
                partida.get('cantidad', partida.get('Quantity', 0))
            )
        )
        cantidad_nueva = (
            self._utilerias.redondear_valor_cantidad_a_decimal(
                valores_partida['cantidad']
            )
        )

        comentario_anterior = str(partida.get('Comments', '') or '').strip()
        comentario_nuevo = str(
            self._ventanas.obtener_input_componente('txt_comentario') or ''
        ).strip()

        precio = partida.get(
            'precio',
            partida.get('UnitPrice', self._info_producto.get('SalePrice', 0)),
        )
        valores_actualizados = self._utilerias.calcular_totales_partida(
            precio,
            cantidad_nueva,
            partida.get('TaxTypeID', self._info_producto.get('TaxTypeID', 10)),
            partida.get('ClaveUnidad', self._info_producto.get('ClaveUnidad', 'H87')),
            partida.get('ClaveProdServ', self._info_producto.get('ClaveProdServ')),
        )

        valor_pieza = int(
            self._ventanas.obtener_input_componente('chk_pieza') or 0
        )
        equivalencia = self._utilerias.redondear_valor_cantidad_a_decimal(
            self._info_producto.get('Equivalencia', 0)
        )
        piezas = (
            cantidad_nueva / equivalencia
            if valor_pieza and equivalencia > 0
            else (cantidad_nueva if valor_pieza else 0)
        )

        partida.update(valores_actualizados)
        partida['Quantity'] = cantidad_nueva
        partida['cantidad'] = cantidad_nueva
        partida['CayalPiece'] = piezas
        partida['CayalAmount'] = int(
            self._ventanas.obtener_input_componente('chk_monto') or 0
        )
        partida['Comments'] = comentario_nuevo
        partida['CreatedBy'] = self._user_id

        # Una partida nueva debe conservar el estado 1 para que posteriormente
        # sea insertada. Solamente una partida existente cambia al estado 2.
        if document_item_id > 0:
            partida['ItemProductionStatusModified'] = 2
        else:
            partida['ItemProductionStatusModified'] = int(
                partida.get('ItemProductionStatusModified', 1) or 1
            )

        self._actualizar_fila_tabla(partida)

        cambios = []
        if cantidad_original != cantidad_nueva:
            cambios.append(
                f'Cantidad {cantidad_original} -> {cantidad_nueva}'
            )
        if comentario_anterior != comentario_nuevo:
            cambios.append(
                f'Especificación "{comentario_anterior}" -> '
                f'"{comentario_nuevo}"'
            )
        if not cambios:
            cambios.append('Partida confirmada sin cambios de cantidad')

        comentario_auditoria = (
            f'EDITADO POR {self._user_name}: ' + '; '.join(cambios)
        )
        self._respaldar_edicion_con_historial(
            partida,
            comentario_auditoria,
            uuid_partida,
            'editar',
        )

        if callable(self._actualizar_totales):
            self._actualizar_totales()

        self._actualizar_servicio_domicilio()
        self.partida_actualizada = True
        self._master.destroy()

    def _actualizar_fila_tabla(self, partida):
        uuid_partida = str(partida.get('uuid', ''))
        filas = self._ventanas_interfaz.obtener_filas_treeview(
            'tvw_productos'
        )

        for fila in filas:
            valores = self._ventanas_interfaz.procesar_fila_treeview(
                'tvw_productos',
                fila,
            )
            if str(valores.get('UUID', '')) != uuid_partida:
                continue

            valores['Cantidad'] = partida.get('cantidad', 0)
            valores['Piezas'] = partida.get('CayalPiece', 0)
            valores['Precio'] = partida.get('precio', 0)
            valores['Importe'] = partida.get('subtotal', 0)
            if 'Impuesto' in valores:
                valores['Impuesto'] = partida.get('impuestos', 0)
            if 'Impuestos' in valores:
                valores['Impuestos'] = partida.get('impuestos', 0)
            valores['Total'] = partida.get('total', 0)
            valores['Comments'] = partida.get('Comments', '')
            valores['ItemProductionStatusModified'] = partida.get(
                'ItemProductionStatusModified', 0
            )

            self._ventanas_interfaz.actualizar_fila_treeview_diccionario(
                'tvw_productos',
                fila,
                valores,
            )
            break

    def _respaldar_edicion_con_historial(
            self,
            partida,
            comentario,
            uuid_partida,
            accion,
    ):
        # El modelo conserva una entrada por cada acción. Los comentarios ya
        # no se concatenan en un único registro porque eso ocultaba ediciones
        # sucesivas y evitaba respaldarlas individualmente.
        self._modelo.agregar_partida_items_documento_extra(
            partida,
            accion,
            comentario,
            uuid_partida,
        )

    def _actualizar_servicio_domicilio(self):
        if self._module_id != 1687:
            return

        total_documento = self._documento.total
        if self._modelo.servicio_a_domicilio_agregado:
            total_sin_servicio = (
                total_documento
                - self._modelo.costo_servicio_a_domicilio
            )
            if (
                    total_sin_servicio >= 200
                    and callable(self._remover_servicio_domicilio)
            ):
                self._remover_servicio_domicilio()
        elif (
                total_documento < 200
                and callable(self._agregar_servicio_domicilio)
        ):
            self._agregar_servicio_domicilio()

    def _procesar_producto(
            self,
            event=None,
            formatear_entrada=True,
            mostrar_errores=True,
    ):

        if self._procesando_producto:
            return

        info_producto = self._info_producto

        try:
            if info_producto:
                self._procesando_producto = True

                cantidad = self._obtener_cantidad_partida()

                chk_pieza = self._ventanas.obtener_input_componente('chk_pieza')
                if chk_pieza == 1 and cantidad % 1 != 0:
                    if mostrar_errores:
                        self._ventanas.mostrar_mensaje(
                            mensaje=(
                                'La cantidad de piezas debe ser un valor '
                                'no fraccionario.'
                            ),
                            master=self._master,
                        )
                    return False

                if formatear_entrada:
                    self._ventanas.insertar_input_componente(
                        'tbx_cantidad',
                        self._truncar_para_presentacion(cantidad),
                    )

                return self._calcular_valores_partida(info_producto)
        finally:
            self._procesando_producto = False
