import tkinter as tk
import uuid

from herramientas.herramientas_panel.finalizar_surtido import FinalizarSurtido
from cayal.ventanas import Ventanas


class AgregarPartidaProduccion:
    def __init__(self, master, base_de_datos, utilerias, lista_precios):
        self._master = master
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._ventanas = Ventanas(self._master)
        self._customer_type_id = lista_precios
        self._consulta_productos = None

        self._crear_frames()
        self._cargar_componentes()
        self._cargar_eventos()
        self._agregar_validaciones()

        self._ventanas.insertar_input_componente('tbx_cantidad', 1)
        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Agregar partida')
        self._ventanas.enfocar_componente('tbx_buscar')

        self.insertar_en_tabla = False
        self.partida_tabla = None
        self.partida = None

    def _crear_frames(self):
        frames = {

            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_componentes': ('frame_principal', 'Producto:',
                                    {'row': 1, 'column': 0, 'columnspan': 4, 'pady': 2, 'padx': 2,
                                     'sticky': tk.NSEW}),

            'frame_totales': ('frame_componentes', None,
                                      {'row': 0, 'column': 3, 'rowspan':3, 'pady': 2, 'padx': 2,
                                       'sticky': tk.NSEW}),

            'frame_comentario': ('frame_componentes', 'Comentario:',
                              {'row': 3, 'column': 0, 'pady': 2, 'padx': 2, 'columnspan': 4,
                               'sticky': tk.NSEW}),

            'frame_tabla_productos': ('frame_principal', 'Productos:',
                                      {'row': 3, 'column': 0, 'columnspan': 4, 'pady': 2, 'padx': 2,
                                       'sticky': tk.NSEW}),

            'frame_botones': ('frame_principal', None,
                              {'row': 5, 'column': 1, 'padx': 0, 'pady': 5, 'sticky': tk.W}),
        }
        self._ventanas.crear_frames(frames)

    def _cargar_componentes(self):

        componentes = {
            'tbx_buscar': ('frame_componentes', None, 'Buscar:', None),
            'tbx_cantidad': ('frame_componentes', None, 'Cantidad:', None),

            'lbl_precio_texto': ('frame_totales',
                                  {'width': 10, 'text': 'PRECIO:', 'style': 'inverse-danger',
                                   'font': ('Consolas', 15, 'bold')},
                                  {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                  None),

            'lbl_total_texto': ('frame_totales',
                                {'width': 10, 'text': 'TOTAL:', 'style': 'inverse-danger',
                                 'font': ('Consolas', 15, 'bold')},
                                {'row': 1, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                None),

            'lbl_unidad_texto': ('frame_totales',
                                {'width': 10, 'text': 'UNIDAD:', 'style': 'inverse-danger',
                                 'font': ('Consolas', 15, 'bold')},
                                {'row': 2, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                None),
            'lbl_precio': ('frame_totales',
                                 {'width': 10, 'text': '$0.00', 'style': 'inverse-danger', 'anchor':'e',
                                  'font': ('Consolas', 15, 'bold')},
                                 {'row': 0, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                 None),

            'lbl_total': ('frame_totales',
                                {'width': 10, 'text': '$0.00', 'style': 'inverse-danger', 'anchor':'e',
                                 'font': ('Consolas', 15, 'bold')},
                                {'row': 1, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                None),

            'lbl_unidad': ('frame_totales',
                                 {'width': 10, 'text': '', 'style': 'inverse-danger', 'anchor':'e',
                                  'font': ('Consolas', 15, 'bold')},
                                 {'row': 2, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                 None),
            'txt_comentario': ('frame_comentario', None, ' ', None),
            'tvw_productos': ('frame_tabla_productos', self._crear_columnas_detalle(), 5, 'Primary'),
            'btn_guardar':('frame_botones', None, 'Agregar', None),
            'btn_cancelar': ('frame_botones', 'Danger', 'Cancelar', None)
        }
        self._ventanas.crear_componentes(componentes)

    def _agregar_validaciones(self):
        pass
        #self._ventanas.agregar_validacion_tbx('tbx_cantidad', 'cantidad')

    def _crear_columnas_detalle(self):
        return [
            {"text": "Clave", "stretch": False, 'width': 115, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Producto", "stretch": False, 'width': 265, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Unidad", "stretch": False, 'width': 60, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Precio", "stretch": False, 'width': 85, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "ProductID", "stretch": False, 'width': 80, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "ClaveUnidad", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "UnitPrice", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
        ]

    def _cargar_eventos(self):
        eventos = {
            'tbx_buscar': lambda event: self._buscar_producto(),
            'btn_guardar': self._agregar_por_producto_por_clave,
            'btn_cancelar': self._master.destroy,
            'tbx_cantidad': lambda event:self._actualizar_totales(),
            'tvw_productos': (lambda event:self._actualizar_totales(), 'seleccion')
        }
        self._ventanas.cargar_eventos(eventos)

    def _actualizar_totales(self):
        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_productos')

        if not fila:
            return

        if len(fila) > 1:
            return

        if not self._validar_inputs_usuario():
            return

        valores_fila = self._ventanas.procesar_fila_treeview('tvw_productos', fila)

        cantidad = self._ventanas.obtener_input_componente('tbx_cantidad')

        cantidad_decimal =  self._utilerias.redondear_valor_cantidad_a_decimal(cantidad)
        precio_decimal =  self._utilerias.redondear_valor_cantidad_a_decimal(valores_fila['Precio'])

        total = precio_decimal * cantidad_decimal
        total_moneda =  self._utilerias.convertir_decimal_a_moneda(total)
        self._ventanas.insertar_input_componente('lbl_total', total_moneda)

        precio_moneda = self._utilerias.convertir_decimal_a_moneda(precio_decimal)
        self._ventanas.insertar_input_componente('lbl_precio', precio_moneda)

        self._ventanas.insertar_input_componente('lbl_unidad', valores_fila['Unidad'])

    def _buscar_producto(self):
        termino_buscado = self._ventanas.obtener_input_componente('tbx_buscar')
        if not termino_buscado:
            return

        termino_buscado = self._ventanas.obtener_input_componente('tbx_buscar')


        consulta = self._base_de_datos.buscar_product_id_termino(termino_buscado)

        if not consulta:
            self._ventanas.mostrar_mensaje('El término buscado no arrojó resultados')
            self._ventanas.enfocar_componente('tbx_buscar')
            self._ventanas.insertar_input_componente('tbx_cantidad', 1.00)
            return


        ids_productos = self._obtener_product_ids_consulta(consulta)
        consulta_productos = self._buscar_info_productos_por_ids(ids_productos)
        consulta_productos_impuestos = self._agregar_impuestos_productos(consulta_productos)
        self._consulta_productos = consulta_productos_impuestos
        self._rellenar_tabla_productos(consulta_productos_impuestos)

    def _obtener_product_ids_consulta(self, consulta_productos):
        product_ids = [producto['ProductID'] for producto in consulta_productos]

        if len(product_ids) == 1:
            return product_ids[0]

        return product_ids

    def _buscar_info_productos_por_ids(self, productos_ids, no_en_venta=None):

        if no_en_venta:
            return self._base_de_datos.buscar_info_productos(productos_ids,
                                                            self._customer_type_id,
                                                            no_en_venta=True)
        return self._base_de_datos.buscar_info_productos(productos_ids, self._customer_type_id)

    def _agregar_impuestos_productos(self, consulta_productos):
        consulta_procesada = []
        for producto in consulta_productos:
            producto_procesado = self._utilerias.calcular_precio_con_impuesto_producto(producto)
            consulta_procesada.append(producto_procesado)
        return consulta_procesada

    def _rellenar_tabla_productos(self, consulta):
        partidas = []
        for producto in consulta:
            partida = {
                'ProductKey': producto['ProductKey'],
                'ProductName': producto['ProductName'],
                'Unit': producto['Unit'],
                'SalePriceWithTaxes': producto['SalePriceWithTaxes'],
                'ProductID': producto['ProductID'],
                'ClaveUnidad': producto['ClaveUnidad'],
                'SalePrice': producto['SalePrice']
            }
            partidas.append(partida)

        self._ventanas.rellenar_treeview('tvw_productos', self._crear_columnas_detalle(), partidas, valor_barra_desplazamiento=5)

    def _validar_inputs_usuario(self):
        cantidad = self._ventanas.obtener_input_componente('tbx_cantidad')
        if not cantidad:
            self._ventanas.mostrar_mensaje('Debe definir una cantidad.')
            return

        if not self._utilerias.es_cantidad(cantidad):
            self._ventanas.mostrar_mensaje('Debe definir una cantidad válida.')
            return

        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_productos'):
            return

        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_productos')
        valores_fila = self._ventanas.procesar_fila_treeview('tvw_productos', fila)

        unit = valores_fila['Unidad']
        cantidad_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(cantidad)

        if not self._utilerias.validar_unidad(cantidad_decimal, unit):
            self._ventanas.mostrar_mensaje('Los productos con unidad no pueden tener cantidades fraccionarias.')
            return

        return True

    def _agregar_por_producto_por_clave(self):
        if not self._validar_inputs_usuario():
            return

        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_productos')
        valores_filas = self._ventanas.procesar_fila_treeview('tvw_productos', fila)
        product_id = int(valores_filas['ProductID'])
        info_producto = [producto for producto in self._consulta_productos if producto['ProductID'] == product_id]

        producto = info_producto[0]
        uuid_producto = uuid.uuid1()
        producto['UUID'] = uuid_producto


        comentario = self._ventanas.obtener_input_componente('txt_comentario')
        cantidad = self._utilerias.redondear_valor_cantidad_a_decimal(
            self._ventanas.obtener_input_componente('tbx_cantidad'))

        partida_tabla = self._crear_partida_tabla(producto, comentario, cantidad)

        producto['Quantity'] = cantidad
        producto['Comments'] = comentario
        producto['DocumentItemID'] = 0



        ventana = self._ventanas.crear_popup_ttkbootstrap(master=self._master, titulo='Asignar surtido')
        instancia = FinalizarSurtido(ventana, self._base_de_datos, self._utilerias)
        ventana.wait_window()

        if instancia.employee_user_id == 0:
            self._ventanas.mostrar_mensaje('Debe seleccionar un responsable de la preparación del producto.')
            return

        producto['CreatedBy'] = instancia.employee_user_id
        producto['CreatedByName'] = instancia.employee_user_name

        self.partida_tabla = partida_tabla
        self.partida = producto
        self.insertar_en_tabla = True
        self._master.destroy()

    def _crear_partida_tabla(self, info_producto, comentario, cantidad):

        precio = self._utilerias.redondear_valor_cantidad_a_decimal(info_producto['SalePriceWithTaxes'])
        total = cantidad * precio
        total = f"{total:.2f}"
        comentario = comentario.strip()
        parametros = (
                        cantidad,
                        info_producto['ProductKey'] ,
                        info_producto['ProductName'],
                        precio,
                        total,
                        "E" if comentario != '' else comentario, # Especificacion
                        comentario,
                        info_producto['UUID'],
                        0 # document item id
        )

        return parametros