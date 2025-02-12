import tkinter as tk
from cayal.ventanas import Ventanas

from agregar_partida_produccion import AgregarPartidaProduccion
from editar_partida_produccion import EditarPartidaProduccion


class EditarPedido:
    def __init__(self, master, base_de_datos, utilerias, parametros, valores_fila):
        self._master = master
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._ventanas = Ventanas(self._master)
        self._parametros = parametros

        self._valores_fila = valores_fila
        self._user_id = self._parametros.id_usuario
        self._user_name = self._base_de_datos.buscar_nombre_de_usuario(self._user_id)

        self._business_entity_id = valores_fila['BusinessEntityID']
        self._order_document_id = valores_fila['OrderDocumentID']

        self._consulta_partidas = []
        self._partidas_a_agregar = []
        self._partidas_a_eliminar = []
        self._partidas_a_editar = []

        self._cargar_frames()
        self._cargar_componentes()
        self._cargar_eventos()
        self._crear_barra_herramientas()
        self._rellenar_tabla_detalle()
        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Editar pedido')

    def _cargar_frames(self):
        frames = {

            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_herramientas': ('frame_principal', 'Herramientas',
                                   {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                    'sticky': tk.W}),

            'frame_totales': ('frame_principal', None,
                              {'row': 0, 'column': 2, 'columnspan': 2, 'pady': 2, 'padx': 2,
                               'sticky': tk.NSEW}),

            'frame_tabla_detalle': ('frame_principal', 'Detalle pedido seleccionado:',
                                    {'row': 1, 'column': 0, 'columnspan': 4, 'pady': 2, 'padx': 2,
                                     'sticky': tk.NSEW}),

            'frame_botones': ('frame_principal', None,
                              {'row': 2, 'column': 1, 'padx': 0, 'pady': 5, 'sticky': tk.W}),
        }
        self._ventanas.crear_frames(frames)

    def _cargar_componentes(self):
        componentes = {
            'lbl_total_texto': ('frame_totales',
                                {'width': 10, 'text': 'TOTAL:', 'style': 'inverse-danger',
                                 'font': ('Consolas', 20, 'bold')},
                                {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                None),

            'lbl_total': ('frame_totales',
                          {'width': 10, 'text': '$ 0.00', 'style': 'inverse-danger', 'anchor': 'e',
                           'font': ('Consolas', 20, 'bold')},
                          {'row': 0, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.E},
                          None),

            'lbl_partidas_texto': ('frame_totales',
                                     {'width': 10, 'text': 'PARTIDAS:', 'style': 'inverse-danger',
                                      'font': ('Consolas', 20, 'bold')},
                                     {'row': 1, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                     None),

            'lbl_partidas': ('frame_totales',
                               {'width': 10, 'text': '0', 'style': 'inverse-danger', 'anchor': 'e',
                                'font': ('Consolas', 20, 'bold')},
                               {'row': 1, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.E},
                               None),

            'tvw_detalle': ('frame_tabla_detalle', self._crear_columnas_detalle(), 10, 'WARNING'),
            'btn_aceptar':('frame_botones',None, 'Aceptar', None),
            'btn_cancelar': ('frame_botones', 'DANGER', 'Cancelar', None),

        }
        self._ventanas.crear_componentes(componentes)

    def _cargar_eventos(self):
        eventos = {
            'btn_aceptar': self._guardar_cambios,
            'btn_cancelar': self._master.destroy
        }

        self._ventanas.cargar_eventos(eventos)

    def _crear_columnas_detalle(self):
        return [
                {"text": "Cantidad", "stretch": False, 'width': 70, 'column_anchor': tk.W,
                 'heading_anchor': tk.W, 'hide': 0},
                {"text": "Clave", "stretch": False, 'width': 125, 'column_anchor': tk.W,
                 'heading_anchor': tk.W, 'hide': 0},
                {"text": "Producto", "stretch": False, 'width': 240, 'column_anchor': tk.W,
                 'heading_anchor': tk.W, 'hide': 0},
                {"text": "Precio", "stretch": False, 'width': 90, 'column_anchor': tk.E,
                 'heading_anchor': tk.W, 'hide': 0},
                {"text": "Total", "stretch": False, 'width': 90, 'column_anchor': tk.E,
                 'heading_anchor': tk.W, 'hide': 0},
                {"text": "Esp.", "stretch": False, 'width': 35, 'column_anchor': tk.W,
                 'heading_anchor': tk.W, 'hide': 0},
                {"text": "Comments", "stretch": False, 'width': 100, 'column_anchor': tk.W,
                 'heading_anchor': tk.W, 'hide': 1},
                {"text": "UUID", "stretch": False, 'width': 100, 'column_anchor': tk.W,
                 'heading_anchor': tk.W, 'hide': 1},
                {"text": "DocumentItemID", "stretch": False, 'width': 100, 'column_anchor': tk.W,
                 'heading_anchor': tk.W, 'hide': 1},
                {"text": "ClaveUnidad", "stretch": False, 'width': 100, 'column_anchor': tk.W,
                 'heading_anchor': tk.W, 'hide': 1},
            ]

    def _crear_barra_herramientas(self):
        self.barra_herramientas = [
            {'nombre_icono': 'Agregar21.ico', 'etiqueta': 'Agregar', 'nombre': 'agregar_partida',
             'hotkey': None, 'comando': self._agregar_partida},

            {'nombre_icono': 'Editar21.ico', 'etiqueta': 'Editar', 'nombre': 'editar_partida',
             'hotkey': None, 'comando': self._editar_partida},

            {'nombre_icono': 'Eliminar21.ico', 'etiqueta': 'Eliminar', 'nombre': 'eliminar_partida',
             'hotkey': None, 'comando': self._eliminar_partida},
        ]

        self.elementos_barra_herramientas = self._ventanas.crear_barra_herramientas(
            self.barra_herramientas,
            'frame_herramientas')
        self.iconos_barra_herramientas = self.elementos_barra_herramientas[0]
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]

    def _agregar_partida(self):
        customer_type_id = self._base_de_datos.fetchone(
            'SELECT CustomerTypeID FROM orgCustomer WHERE BusinessEntityID = ?',
            (self._business_entity_id,)

        )
        ventana = self._ventanas.crear_popup_ttkbootstrap()
        instancia = AgregarPartidaProduccion(ventana, self._base_de_datos, self._utilerias, customer_type_id)
        ventana.wait_window()

        if instancia.insertar_en_tabla:
            self._ventanas.insertar_fila_treeview('tvw_detalle',
                                                  instancia.partida_tabla,
                                                  al_principio=True)
            filas = self._ventanas.obtener_filas_treeview('tvw_detalle')
            self._ventanas.colorear_fila_seleccionada_treeview('tvw_detalle', filas[0], 'info')

            self._partidas_a_agregar.append(instancia.partida)

            total = self._calcular_total_pedido()
            self._actualizar_totales_documento(total)

    def _editar_partida(self):
        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_detalle'):
            return
        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_detalle')
        valores_fila = self._ventanas.obtener_valores_fila_treeview('tvw_detalle', fila)

        ventana = self._ventanas.crear_popup_ttkbootstrap(titulo='Editar partida')
        instancia = EditarPartidaProduccion(ventana, self._base_de_datos, self._utilerias, valores_fila)
        ventana.wait_window()

        if instancia.actualizar_cantidad:
            self._partidas_a_editar.append(instancia.valores_partida)
            self._ventanas.actualizar_fila_treeview('tvw_detalle',
                                                                         fila,
                                                                         instancia.valores_partida)


        total = self._calcular_total_pedido()
        self._actualizar_totales_documento(total)

    def _eliminar_partida(self):

        filas =  self._ventanas.obtener_filas_treeview('tvw_detalle')
        if len(filas) == 1:
            self._ventanas.mostrar_mensaje('El documento por lo menos debe tener una partida.')
            return

        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_detalle'):
            return


        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_detalle')

        print(fila)
        valores_fila = self._ventanas.procesar_fila_treeview('tvw_detalle', fila)
        print(valores_fila)
        document_item_id = int(valores_fila.get('DocumentItemID', 0))
        order_document_id = int(valores_fila.get('OrderDocumentID',0))
        uuid_tabla = str(valores_fila['UUID'])

        # buscar si es un producto adicional
        if self._partidas_a_agregar:
            nuevos_productos_adicionales = [partida for partida in self._partidas_a_agregar
                                            if str(partida['UUID']) != uuid_tabla]

            self._partidas_a_agregar = nuevos_productos_adicionales



        # eliminar de partidas a insertar
        if document_item_id != 0:
            partida_eliminada = [partida for partida in self._consulta_partidas
                                 if document_item_id == int(partida['DocumentItemID'])][0]

            if partida_eliminada:
                self._partidas_a_eliminar.append(partida_eliminada)

            if self._partidas_a_editar:

                nuevas_partidas_a_editar = [partida for partida in self._partidas_a_editar
                                            if int(partida[8]) != document_item_id]

                self._partidas_a_editar = nuevas_partidas_a_editar

        self._ventanas.remover_fila_treeview('tvw_detalle', fila)
        total = self._calcular_total_pedido()
        self._actualizar_totales_documento(total)

    def _rellenar_tabla_detalle(self):

        order_document_id = self._valores_fila['OrderDocumentID']

        consulta_partidas = self._base_de_datos.buscar_partidas_pedidos_produccion_cayal(
            order_document_id,
            partidas_eliminadas=False,
            partidas_producidas=True)

        partidas = self._procesar_partidas(consulta_partidas)

        self._ventanas.rellenar_treeview('tvw_detalle',
                                         self._crear_columnas_detalle(),
                                         partidas,
                                         valor_barra_desplazamiento=5)

        self._consulta_partidas = partidas

        total = self._calcular_total_pedido()
        self._actualizar_totales_documento(total)

    def _procesar_partidas(self, partidas_a_procesar):
        partidas = self._utilerias.agregar_impuestos_productos(partidas_a_procesar)

        nuevas_partidas = []
        for partida in partidas:

            if partida['ProductID'] == 5606:
                continue

            cantidad = self._utilerias.redondear_valor_cantidad_a_decimal(partida['Quantity'])
            precio = self._utilerias.redondear_valor_cantidad_a_decimal(partida['SalePriceWithTaxes'])
            total = cantidad * precio
            total = f"{total:.2f}"
            nueva_partida = {
                'Quantity': cantidad,
                'ProductKey': partida['ProductKey'],
                'ProductName': partida['ProductName'],
                'UnitPrice': precio,
                'Total': total,
                'Comments': partida['Comments'],
                'UUID': partida.get('UUID', ''),
                'DocumentItemID': partida['DocumentItemID'],
                'ClaveUnidad': partida.get('ClaveUnidad','KGM')
            }
            nuevas_partidas.append(nueva_partida)

        return nuevas_partidas

    def _guardar_cambios(self):

        self._eliminar_partidas_tabla_base_datos()
        self._agregar_partidas_adicionales_tabla_base_datos(self._order_document_id)
        self._actualizar_partidas_tabla_base_datos()

        self._master.destroy()

    def _actualizar_partidas_tabla_base_datos(self):
        for partida in self._partidas_a_editar:
            cantidad = partida[0]
            document_item_id = partida[8]
            info_producto = \
            self._base_de_datos.fetchall('SELECT * FROM [dbo].[zvwBuscarPartidaPedidoCayal-DocumentItemID](?)',
                                         (document_item_id,))[0]

            precio = self._utilerias.redondear_valor_cantidad_a_decimal(info_producto['UnitPrice'])
            total = precio * cantidad

            parametros = {
                "ProductName": info_producto['ProductName'],  # este no se pasa como argumento a parametros
                "DocumentID": self._order_document_id,
                "ProductID": info_producto['ProductID'],
                "DepotID": 2,
                "Cantidad": cantidad,
                "Precio": precio,
                "Costo": 0,
                "Total": total,
                "DocumentItemID": document_item_id,  # Se actualizará con el valor de salida
                "TipoCaptura": 1,
                "CayalPiece": 0,
                "CayalAmount": 0,
                "ItemProductionStatusModified": 2,
                "Comments": info_producto['Comments'],
                "CreatedBy": self._user_id

            }

            self._actualizar_partidas_pedidos_cayal(accion='editar', dic_parametros_producto=parametros)

    def _eliminar_partidas_tabla_base_datos(self):
        for partida in self._partidas_a_eliminar:

            document_item_id = partida['DocumentItemID']
            info_producto = self._base_de_datos.fetchall('SELECT * FROM [dbo].[zvwBuscarPartidaPedidoCayal-DocumentItemID](?)',
                                         (document_item_id,))[0]

            parametros = {
                "ProductName": info_producto['ProductName'],  # este no se pasa como argumento a parametros
                "DocumentID": self._order_document_id,
                "ProductID": info_producto['ProductID'],
                "DepotID": 2,
                "Cantidad": info_producto['Quantity'],
                "Precio": info_producto['UnitPrice'],
                "Costo": 0,
                "Total": info_producto['Subtotal'],
                "DocumentItemID": document_item_id,  # Se actualizará con el valor de salida
                "TipoCaptura": 1,
                "CayalPiece": 0,
                "CayalAmount": 0,
                "ItemProductionStatusModified": 3,
                "Comments": info_producto['Comments'],
                "CreatedBy": self._user_id

            }

            self._actualizar_partidas_pedidos_cayal(accion='eliminar', dic_parametros_producto=parametros)

    def _calcular_total_pedido(self):
        filas = self._ventanas.obtener_filas_treeview('tvw_detalle')
        total_acumulado = 0

        for fila in filas:
            valores = self._ventanas.obtener_valores_fila_treeview('tvw_detalle', fila)
            if valores:
                total = valores[4]
                total_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(total)

                total_acumulado += total_decimal
        return total_acumulado

    def _actualizar_totales_documento(self, total):
        total_moneda = self._utilerias.convertir_decimal_a_moneda(total)
        self._ventanas.insertar_input_componente('lbl_total', total_moneda)

        numero_filas = self._ventanas.numero_filas_treeview('tvw_detalle')
        self._ventanas.insertar_input_componente('lbl_partidas', numero_filas)

    def _agregar_partidas_adicionales_tabla_base_datos(self, order_document_id):
        # como seleccionar al pedido al cual agrega las partidas
        for partida in self._partidas_a_agregar:
            producto = partida['ProductName']
            cantidad = self._utilerias.redondear_valor_cantidad_a_decimal(partida['Quantity'])
            precio = self._utilerias.redondear_valor_cantidad_a_decimal(partida['SalePrice'])

            parametros = {
                "ProductName": producto,  # este no se pasa como argumento a parametros
                "DocumentID": order_document_id,
                "ProductID": partida['ProductID'],
                "DepotID": 2,
                "Cantidad": cantidad,
                "Precio": precio,
                "Costo": 0,
                "Total": cantidad * precio,
                "DocumentItemID": 0,  # Se actualizará con el valor de salida
                "TipoCaptura": 1,
                "CayalPiece": 0,
                "CayalAmount": 0,
                "ItemProductionStatusModified": 4,
                "Comments": partida['Comments'],
                "CreatedBy": partida['CreatedBy']

            }

            self._actualizar_partidas_pedidos_cayal(accion='agregar', dic_parametros_producto=parametros)

            # afectar bitacora interna
            self._base_de_datos.command("""
                INSERT INTO OrderProductionAdditionalItems (ProductID, Quantity, CreatedBy, EmployeeUserID, DocumentID)
                VALUES (?, ?, ?, ?, ?) -- Ejemplo de un producto con cantidad y usuarios asociados
            """, (partida['ProductID'], cantidad, self._user_id, partida['CreatedBy'], order_document_id))

    def _actualizar_partidas_pedidos_cayal(self, accion, dic_parametros_producto):

        """parametros_producto es un diccionario con la siguiente estructura

            parametros = {
                        "ProductName": None, # este no se pasa como argumento a parametros
                        "DocumentID": None,
                        "ProductID": None,
                        "DepotID": None,
                        "Cantidad": None,
                        "Precio": None,
                        "Costo": None,
                        "Total": None,
                        "DocumentItemID": None,  # Se actualizará con el valor de salida
                        "TipoCaptura": None,
                        "CayalPiece": None,
                        "CayalAmount": None,
                        "ItemProductionStatusModified": None,
                        "Comments": None,
                        "CreatedBy": None
                    }

        """


        # --------------------------------------------------------------------------------------------------------
        # procesamos el diccionario de parametros
        # --------------------------------------------------------------------------------------------------------
        parametros_producto = [
            dic_parametros_producto['DocumentID'],
            dic_parametros_producto['ProductID'],
            dic_parametros_producto['DepotID'],
            dic_parametros_producto['Cantidad'],
            dic_parametros_producto['Precio'],
            dic_parametros_producto['Costo'],
            dic_parametros_producto['Total'],
            dic_parametros_producto['DocumentItemID'],
            dic_parametros_producto['TipoCaptura'],
            dic_parametros_producto['CayalPiece'],
            dic_parametros_producto['CayalAmount'],
            dic_parametros_producto['ItemProductionStatusModified'],
            dic_parametros_producto['Comments'],
            dic_parametros_producto['CreatedBy'],
        ]
        # --------------------------------------------------------------------------------------------------------
        # afectaciones previas a realizar
        # --------------------------------------------------------------------------------------------------------
        document_item_id = dic_parametros_producto['DocumentItemID']
        product_name = dic_parametros_producto['ProductName']
        cantidad = dic_parametros_producto['Cantidad']
        document_id = dic_parametros_producto['DocumentID']
        user_id = dic_parametros_producto['CreatedBy']
        total = dic_parametros_producto['Total']

        cantidad_anterior = 0

        if accion == 'editar':
            info_producto = self._base_de_datos.fetchall('SELECT * FROM [dbo].[zvwBuscarPartidaPedidoCayal-DocumentItemID](?)',
                                         (document_item_id,))[0]
            cantidad_anterior = info_producto['Quantity']

        # si la partida no existe previamente creala para obtener el item id
        if document_item_id == 0:
            document_item_id = self._base_de_datos.exec_stored_procedure(
                'zvwInsertarProductoPedidoCayal', parametros_producto)

        parametros_producto[7] = document_item_id

        # respaldala para afectaciones posteriores
        self._base_de_datos.exec_stored_procedure(
            'zvwInsertarProductoPedidoCayalExtra', parametros_producto)

        if accion == 'agregar':
            # insertala como finalizada para que esta quede dentro del pedido
            self._base_de_datos.exec_stored_procedure(
                'zvwInsertarProductoFinalizadoPedidoCayal', parametros_producto)

        #--------------------------------------------------------------------------------------------------------
        item_production_status_modified = dic_parametros_producto['ItemProductionStatusModified']
        change_type_id = 0
        comentario  = ''

        if accion == 'agregar':
            # 1 agregado antes de producir 4 agregado despues de producir o durante la produccion
            item_production_status_modified = 1 if item_production_status_modified in (0,1)  else 4
            change_type_id = 15
            comentario = f"Agregado {product_name} - Cant.{cantidad}"

            # actualiza la partidad

        if accion == 'editar':
            item_production_status_modified = 2
            change_type_id = 16
            comentario = dic_parametros_producto['Comments']
            comentario = f"Editado de Cant {cantidad_anterior} -> Cant {cantidad} - {comentario}"

            self._base_de_datos.command(
                """
                DECLARE @Quantity FLOAT = ?
                DECLARE @Total FLOAT = ?
                DECLARE @DocumentItemID INT = ?
                DECLARE @Comments NVARCHAR(MAX) = ?
                
                UPDATE docDocumentItemOrderCayal
                    SET Quantity = @Quantity, Total = @Total, Comments = @Comments
                WHERE DocumentItemID = @DocumentItemID
                
                UPDATE docDocumentItemOrderCayalExtra
                    SET Quantity = @Quantity, Total = @Total, Comments = @Comments
                WHERE DocumentItemID = @DocumentItemID
                
                UPDATE docDocumentItemOrderCayalFinalProduction 
                    SET Quantity = @Quantity, Total = @Total, Comments = @Comments
                WHERE DocumentItemID = @DocumentItemID
                """, (cantidad, total,  document_item_id, comentario,))

        if accion == 'eliminar':
            item_production_status_modified = 3
            change_type_id = 17
            comentario = f"Eliminado {product_name} - Cant.{cantidad}"

            self._base_de_datos.command(
                """
                DECLARE @DeletedBy INT = ?
                DECLARE @DocumentItemID INT = ?
                
                
                UPDATE docDocumentItemOrderCayal
                    SET DeletedOn = GETDATE(), DeletedBy = @DeletedBy
                WHERE DocumentItemID = @DocumentItemID
                
                UPDATE docDocumentItemOrderCayalExtra
                    SET DeletedOn = GETDATE(), DeletedBy = @DeletedBy
                WHERE DocumentItemID = @DocumentItemID
                
                UPDATE docDocumentItemOrderCayalFinalProduction 
                    SET DeletedOn = GETDATE(), DeletedBy = @DeletedBy
                WHERE DocumentItemID = @DocumentItemID
                """, (user_id, document_item_id)
            )

        # afecta la partida en extras y finalizado
        self._base_de_datos.command(
            """
            DECLARE @Comments NVARCHAR(MAX) = ?
            DECLARE @ItemProductionStatusModified INT = ?
            DECLARE @DocumentItemID INT = ?
            
            UPDATE docDocumentItemOrderCayal
                SET Comments = @Comments, ItemProductionStatusModified = @ItemProductionStatusModified
            WHERE DocumentItemID = @DocumentItemID
            
            UPDATE docDocumentItemOrderCayalExtra
                SET Comments = @Comments, ItemProductionStatusModified = @ItemProductionStatusModified
            WHERE DocumentItemID = @DocumentItemID
            
            UPDATE docDocumentItemOrderCayalFinalProduction 
                SET Comments = @Comments, ItemProductionStatusModified = @ItemProductionStatusModified
            WHERE DocumentItemID = @DocumentItemID
            """,(comentario, item_production_status_modified, document_item_id)
        )

        # afecta la bitacora de cambios
        self._base_de_datos.insertar_registro_bitacora_pedidos(order_document_id=document_id,
                                                               change_type_id=change_type_id,
                                                               user_id=user_id,
                                                               comments=comentario)

