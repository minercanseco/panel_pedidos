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
        self._rellenar_tablas()
        self._ventanas.configurar_ventana_ttkbootstrap()

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

            'frame_total1': ('frame_tabla1', 'Total Capturado',
                             {'row': 1, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                              'sticky': tk.NSEW}),

            'frame_tabla2': ('frame_componentes', 'Producido',
                             {'row': 2, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                              'sticky': tk.NSEW}),

            'frame_total2': ('frame_tabla2', 'Total Producido:',
                             {'row': 1, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                              'sticky': tk.NSEW}),

            'frame_monto': ('frame_componentes', None,
                            {'row': 3, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                             'sticky': tk.NSEW}),

            'frame_tabla3': ('frame_monto', 'Editadas',
                              {'row': 5, 'column': 1, 'padx': 0, 'pady': 5, 'sticky': tk.W}),

        }
        self._ventanas.crear_frames(frames)

    def _crear_componetes(self):
        componentes = {
            'txt_comentario': ('frame_comentario', None, ' ', None),
            'tbx_total_pedido': ('frame_total1',
                                   {'row': 0, 'column': 1, 'pady': 2, 'padx': 2, 'sticky': tk.NE},
                                   ' ', None),
            'tvw_pedido': ('frame_tabla1', self._crear_columnas_tabla(), 6, None),
            'tbx_total_producido': ('frame_total2',
                                  {'row': 0, 'column': 1, 'pady': 2, 'padx': 2, 'sticky': tk.NE},
                                  ' ', None),
            'tvw_producido': ('frame_tabla2', self._crear_columnas_tabla(), 6, 'danger'),

            'tvw_editado': ('frame_tabla3', self._crear_columnas_tabla(), 6, 'danger'),
        }
        self._ventanas.crear_componentes(componentes)

        self._ventanas.ajustar_componente_en_frame('txt_comentario', 'frame_comentario')

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
             'hide': 1}
        ]


    def _rellenar_totales(self, tabla, partidas):
        total_acumulado = 0
        for partida in partidas:
            total_acumulado += self._utilerias.redondear_valor_cantidad_a_decimal(partida['Total'])

        total_acumulado_moneda = self._utilerias.convertir_decimal_a_moneda(total_acumulado)
        tbx = 'tbx_total_pedido' if tabla =='tvw_pedido' else 'tbx_total_producido'
        self._ventanas.insertar_input_componente(tbx, total_acumulado_moneda)

    def _rellenar_tablas(self):
        self._consultar_info_partidas()

        partidas_capturadas = self._procesar_partidas(self._partidas_capturadas)
        self._rellenar_totales('tvw_pedido', partidas_capturadas)
        self._ventanas.rellenar_treeview(_treeview='tvw_pedido',
                                         columnas=self._crear_columnas_tabla(),
                                         consulta= partidas_capturadas,
                                         variar_color_filas=False,
                                         valor_barra_desplazamiento=6
                                         )

        partidas_producidas = self._procesar_partidas(self._partidas_producidas)
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

            valores_partida = self._utilerias.calcular_totales_partida(sale_price, quantity, tax_type_id)
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
                    'DocumentItemID': reg['DocumentItemID']

                }
            )
        return nuevas_partidas
