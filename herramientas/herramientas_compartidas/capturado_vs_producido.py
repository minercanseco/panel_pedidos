import tkinter as tk
from cayal.ventanas import Ventanas

class CapturadoVsProducido:
    def __init__(self, master, parametros, base_de_datos, utilerias, valores_fila):
        self._master = master
        self._parametros = parametros
        self._order_document_id = self._parametros.id_principal
        self._valores_fila = valores_fila

        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._ventanas = Ventanas(self._master)

        self._partidas_capturadas = []
        self._partidas_editadas = []
        self._partidas_producidas = []

        self._crear_frames()
        self._crear_componetes()
        self._rellenar_componentes()
        self._cargar_eventos()
        self._ventanas.configurar_ventana_ttkbootstrap()

    def _cargar_eventos(self):
        eventos = {
            'tvw_editado':(lambda event: self._actualizar_comentario_editado(), 'seleccion')
        }

        self._ventanas.cargar_eventos(eventos)

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_componentes': ('frame_principal', None,
                                  {'row': 0, 'column': 0, 'pady': 2, 'padx': 2,
                                   'sticky': tk.NSEW}),

            'frame_comentario': ('frame_componentes', 'Comentario',
                                 {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                  'sticky': tk.NSEW}),

            'frame_tabla1': ('frame_componentes', 'Capturado',
                             {'row': 1, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                              'sticky': tk.NSEW}),

            'frame_tabla_captura': ('frame_tabla1', None,
                             {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                              'sticky': tk.NSEW}),


            'frame_total1': ('frame_tabla1', 'Total Capturado',
                             {'row': 1, 'column': 0,  'pady': 2, 'padx': 2,  'columnspan': 2,
                              'sticky': tk.NSEW}),

            'frame_info1': ('frame_total1', None,
                             {'row': 0, 'column': 2, 'columnspan': 2, 'pady': 2, 'padx': 2,
                              'sticky': tk.NSEW}),

            'frame_tabla2': ('frame_componentes', 'Producido',
                             {'row': 2, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                              'sticky': tk.NSEW}),

            'frame_tabla_producido': ('frame_tabla2', None,
                                    {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                     'sticky': tk.NSEW}),

            'frame_total2': ('frame_tabla2', 'Total Producido:',
                             {'row': 1, 'column': 0, 'pady': 2, 'padx': 2,  'columnspan': 2,
                              'sticky': tk.NSEW}),

            'frame_info2': ('frame_total2', None,
                            {'row': 0, 'column': 2, 'pady': 2, 'padx': 2, 'columnspan': 2,
                             'sticky': tk.NSEW}),

            'frame_monto': ('frame_componentes', None,
                            {'row': 3, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                             'sticky': tk.NSEW}),

            'frame_tabla3': ('frame_monto', 'Editadas',
                              {'row': 5, 'column': 1, 'padx': 0, 'pady': 5, 'sticky': tk.W}),

            'frame_comentario_partida': ('frame_tabla3', 'Comentario',
                                 {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                  'sticky': tk.NSEW}),

            'frame_tabla_editado': ('frame_tabla3', None,
                                      {'row': 1, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                       'sticky': tk.NSEW}),

        }
        self._ventanas.crear_frames(frames)

    def _crear_componetes(self):
        componentes = {
            'txt_comentario': ('frame_comentario', None, ' ', None),
            'tbx_total_pedido': ('frame_total1',
                                   {'row': 0, 'column': 1, 'pady': 2, 'padx': 2, 'sticky': tk.NE},
                                   ' ', None),
            'tbx_info_pedido': ('frame_info1',
                                 {'row': 0, 'column': 1, 'pady': 2, 'padx': 2, 'sticky': tk.NE},
                                 ' ', None),
            'tvw_pedido': ('frame_tabla_captura', self._crear_columnas_tabla(), 6, None),
            'tbx_total_producido': ('frame_total2',
                                  {'row': 0, 'column': 1, 'pady': 2, 'padx': 2, 'sticky': tk.W},
                                  ' ', None),
            'tbx_info_producido': ('frame_info2',
                                {'row': 0, 'column': 1, 'pady': 2, 'padx': 2, 'sticky': tk.W},
                                ' ', None),

            'tvw_producido': ('frame_tabla_producido', self._crear_columnas_tabla(), 6, 'danger'),

            'txt_comentario_partida': ('frame_comentario_partida', None, ' ', None),
            'tvw_editado': ('frame_tabla_editado', self._crear_columnas_tabla(), 6, 'warning'),
        }
        self._ventanas.crear_componentes(componentes)

        self._ventanas.ajustar_componente_en_frame('frame_info1', 'frame_total1')
        self._ventanas.ajustar_componente_en_frame('frame_info2', 'frame_total2')
        self._ventanas.bloquear_componente('tbx_info_pedido')
        self._ventanas.bloquear_componente('tbx_info_producido')

        self._ventanas.ajustar_componente_en_frame('txt_comentario', 'frame_comentario')
        self._ventanas.ajustar_componente_en_frame('txt_comentario_partida', 'frame_comentario_partida')

    def _crear_columnas_tabla(self):
        return [
            {'text': 'N', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E, 'hide': 1},
            {'text': 'Cantidad', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {'text': 'Clave', "stretch": False, 'width': 110, 'column_anchor': tk.W, 'heading_anchor': tk.W, 'hide': 0},
            {'text': 'Producto', "stretch": False, 'width': 260, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'Precio', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E, 'hide': 0},
            {'text': 'Subtotal', "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {'text': 'TaxTypeID', "stretch": False, 'width': 0, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {'text': 'ProductID', "stretch": False, 'width': 0, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {'text': 'ClaveUnidad', "stretch": False, 'width': 0, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {'text': 'Impuestos', "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {'text': 'Total', "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E, 'hide': 0},
            {'text': 'DocumentItemID', "stretch": False, 'width': 0, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {'text': 'ItemProductionStatusModified', "stretch": False, 'width': 0, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {'text': 'Comments', "stretch": False, 'width': 0, 'column_anchor': tk.E,
             'heading_anchor': tk.E,
             'hide': 1},
        ]

    def _rellenar_totales(self, tabla, partidas):
        total_acumulado = 0
        for partida in partidas:
            total_acumulado += self._utilerias.redondear_valor_cantidad_a_decimal(partida['Total'])

        total_acumulado_moneda = self._utilerias.convertir_decimal_a_moneda(total_acumulado)
        tbx = 'tbx_total_pedido' if tabla =='tvw_pedido' else 'tbx_total_producido'
        self._ventanas.insertar_input_componente(tbx, total_acumulado_moneda)
        self._ventanas.bloquear_componente(tbx)

    def _rellenar_componentes(self):
        self._consultar_info_partidas()

        partidas_capturadas = self._procesar_partidas(self._partidas_capturadas)
        partidas_capturadas = self._ordenar_consulta(partidas_capturadas, 'ProductName')
        self._rellenar_totales('tvw_pedido', partidas_capturadas)
        self._ventanas.rellenar_treeview(_treeview='tvw_pedido',
                                         columnas=self._crear_columnas_tabla(),
                                         consulta= partidas_capturadas,
                                         variar_color_filas=False,
                                         valor_barra_desplazamiento=6
                                         )

        partidas_producidas = self._procesar_partidas(self._partidas_producidas)
        partidas_producidas = self._ordenar_consulta(partidas_producidas, 'ProductName')
        self._rellenar_totales('tvw_producido', partidas_producidas)
        self._ventanas.rellenar_treeview(_treeview='tvw_producido',
                                         columnas=self._crear_columnas_tabla(),
                                         consulta=partidas_producidas,
                                         variar_color_filas=False,
                                         valor_barra_desplazamiento=6
                                         )

        self._ventanas.rellenar_treeview(_treeview='tvw_editado',
                                         columnas=self._crear_columnas_tabla(),
                                         consulta=self._procesar_partidas(self._partidas_editadas),
                                         variar_color_filas=False,
                                         valor_barra_desplazamiento=6
                                         )

        self._ventanas.insertar_input_componente('txt_comentario', self._valores_fila['Comentarios'])
        self._ventanas.bloquear_componente('txt_comentario')


        texto_captura = f"Capturado por: {self._valores_fila['Captura']}"
        self._ventanas.insertar_input_componente('tbx_info_pedido', texto_captura)
        self._ventanas.ajustar_componente_en_frame('tbx_info_pedido', 'frame_info1')

        consulta = self._buscar_responsables_produccion_pedido()
        if consulta:
            produccion = consulta[0]['UsuarioProduccion']
            almacen = consulta[0]['UsuarioAlmacen']
            minisuper = consulta[0]['UsuarioMinisuper']

            produccion = '' if produccion == '' else f"Producción:{produccion}"
            almacen = '' if almacen == '' else f"Almacén:{almacen}"
            minisuper = '' if minisuper == '' else f"Minisuper:{minisuper}"

            texto_producido = f"{produccion} {almacen} {minisuper}".strip()
            self._ventanas.insertar_input_componente('tbx_info_producido', texto_producido)
            self._ventanas.ajustar_componente_en_frame('tbx_info_producido', 'frame_info2')

        self._colorear_partidas_editadas()

    def _ordenar_consulta(self, consulta, clave, descendente=False):
        """
        Ordena una lista de diccionarios por el valor de una clave específica.

        :param lista: Lista de diccionarios a ordenar
        :param clave: Clave por la cual se ordenará
        :param descendente: Si es True, ordena de forma descendente
        :return: Lista ordenada
        """
        return sorted(consulta, key=lambda x: x.get(clave, ''), reverse=descendente)

    def _consultar_info_partidas(self):
        self._partidas_capturadas = self._base_de_datos.fetchall("""
                            DECLARE @OrderDocumentID INT = ?
                            SELECT * FROM [dbo].[zvwBuscarPartidasPedidoCayal-DocumentID](@OrderDocumentID)
                            """, (self._order_document_id,))

        self._partidas_editadas = self._base_de_datos.fetchall("""
                            DECLARE @OrderDocumentID INT = ?
                            SELECT * FROM [dbo].[zvwBuscarPartidasPedidoCayalExtra-DocumentID](@OrderDocumentID)
                            """, (self._order_document_id,))

        self._partidas_producidas = self._base_de_datos.fetchall("""
                            DECLARE @OrderDocumentID INT = ?
                            SELECT * FROM [dbo].[zvwBuscarPartidasFinalizadasPedidoCayal-DocumentID](@OrderDocumentID)
                            """, (self._order_document_id,))

    def _colorear_partidas_editadas(self):
        filas = self._ventanas.obtener_filas_treeview('tvw_editado')
        if not filas:
            return
        for fila in filas:
            valores_fila = self._ventanas.procesar_fila_treeview('tvw_editado', fila)
            item_production_status_modified = int(valores_fila['ItemProductionStatusModified'])
            if item_production_status_modified == 1:
                self._ventanas.colorear_fila_seleccionada_treeview('tvw_editado', fila, 'info')

            if item_production_status_modified == 2:
                self._ventanas.colorear_fila_seleccionada_treeview('tvw_editado', fila, 'warning')

            if item_production_status_modified == 3:
                self._ventanas.colorear_fila_seleccionada_treeview('tvw_editado', fila, 'danger')

    def _procesar_partidas(self, partidas):

        def buscar_precio(product_id, customer_type_id):
            consulta = self._base_de_datos.buscar_precios_producto(product_id)
            if not consulta:
                return 0
            return [reg['SalePrice'] for reg in consulta if reg['CustomerTypeID'] == customer_type_id][0]

        business_entity_id = self._valores_fila['BusinessEntityID']
        customer_type_id = self._base_de_datos.fetchone('SELECT CustomerTypeID FROM orgCustomer WHERE BusinessEntityID = ?',
                                                        (business_entity_id,))

        nuevas_partidas = []
        for reg in partidas:

            quantity = self._utilerias.redondear_valor_cantidad_a_decimal(reg['Quantity'])
            product_id = reg['ProductID']
            sale_price = self._utilerias.redondear_valor_cantidad_a_decimal(
                buscar_precio(product_id, customer_type_id))
            tax_type_id = reg['TaxTypeID']

            clave_unidad = reg['ClaveUnidad']
            clave_sat = reg['ClaveProdServ']
            valores_partida = self._utilerias.calcular_totales_partida(sale_price,
                                                                       quantity,
                                                                       tax_type_id,
                                                                       clave_unidad,
                                                                       clave_sat
                                                                       )
            sale_price = self._utilerias.redondear_valor_cantidad_a_decimal(valores_partida['precio'])
            taxes = self._utilerias.redondear_valor_cantidad_a_decimal(valores_partida['impuestos'])
            sub_total = self._utilerias.redondear_valor_cantidad_a_decimal(valores_partida['subtotal'])
            total = self._utilerias.redondear_valor_cantidad_a_decimal(valores_partida['total'])

            nuevas_partidas.append(
                {
                    'N': reg['N'],
                    'Quantity': quantity,
                    'ProductKey': reg['ProductKey'],
                    'ProductName': reg['ProductName'],
                    'SalePrice': sale_price,
                    'Subtotal': sub_total,
                    'TaxTypeID': tax_type_id,
                    'ProductID': product_id,
                    'ClaveUnidad': reg['ClaveUnidad'],
                    'TotalTaxes': taxes,
                    'Total': total,
                    'DocumentItemID': reg['DocumentItemID'],
                    'ItemProductionStatusModified': reg['ItemProductionStatusModified'],
                    'Comments': reg['Comments']
                }
            )
        return nuevas_partidas

    def _buscar_responsables_produccion_pedido(self):
        return self._base_de_datos.fetchall("""
            SELECT ISNULL(UP.UserName ,'') UsuarioProduccion,
               ISNULL( UM.UserName,'') UsuarioMinisuper,
               ISNULL( UA.UserName,'') UsuarioAlmacen
            FROM docDocumentOrderCayal P LEFT OUTER JOIN
                engUser UP ON P.AssignedProductionUser = UP.UserID LEFT OUTER JOIN
                engUser UM ON P.StoreAssignedUser = UM.UserID LEFT OUTER JOIN
                engUser UA ON P.WarehouseAssignedUser = UA.UserID 
            WHERE OrderDocumentID = ?
        """,(self._order_document_id,))

    def _actualizar_comentario_editado(self):
        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_editado'):
            return

        filas = self._ventanas.obtener_filas_treeview('tvw_editado')
        if not filas:
            return

        for fila in filas:
            valores_fila = self._ventanas.procesar_fila_treeview('tvw_editado', fila)
            numero_fila = int(valores_fila['N'])
            texto_adicional = ''

            fila_respaldo = [reg for reg in self._partidas_editadas if reg['N'] == numero_fila]
            if fila_respaldo:
                info_fila = fila_respaldo[0]

                item_production_status_modified = int(valores_fila['ItemProductionStatusModified'])
                texto_adicional = ""
                if item_production_status_modified == 3:
                    user_name = self._base_de_datos.buscar_nombre_de_usuario(info_fila['DeletedBy'])
                    texto_adicional = f"({user_name} {info_fila['DeletedOn']})"
                if item_production_status_modified == 1:
                    user_name = self._base_de_datos.buscar_nombre_de_usuario(info_fila['CreatedBy'])
                    texto_adicional = f"({user_name} {info_fila['CreatedOn']})"

            comentario = valores_fila['Comments']
            comentario = f"{comentario} {texto_adicional}".strip()

            if comentario:
                self._ventanas.insertar_input_componente('txt_comentario_partida', comentario)

