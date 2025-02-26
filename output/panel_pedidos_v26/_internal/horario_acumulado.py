import tkinter as tk
from cayal.ventanas import Ventanas
from datetime import datetime


class HorarioslAcumulados:
    def __init__(self, master, base_de_datos, utilerias):
        self._master = master
        self._base_de_datos = base_de_datos
        self._ventanas = Ventanas(self._master)
        self._utilerias = utilerias

        self._consulta_status = []
        self._consulta_horarios = []
        self._consulta_pedidos = []

        self._crear_frames()
        self._crear_componentes_forma()
        self._cargar_eventos()
        self._rellenar_tabla_horarios()

        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Pedidos acumulados por horarios')

    def _crear_frames(self):
        frames = {

            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_total_horarios': ('frame_principal', None,
                                     {'row': 0, 'column': 0, 'pady': 2, 'padx': 2,
                                      'sticky': tk.NSEW}),

            'frame_total_pedidos': ('frame_principal', None,
                                     {'row': 0, 'column': 1, 'pady': 2, 'padx': 2,
                                      'sticky': tk.NSEW}),

            'frame_total_partidas': ('frame_principal', None,
                                     {'row': 0, 'column': 2, 'pady': 2, 'padx': 2,
                                      'sticky': tk.NSEW}),

            'frame_tabla_horarios': ('frame_principal', 'Horarios',
                                     {'row': 1, 'column': 0, 'pady': 2, 'padx': 2,
                                      'sticky': tk.NSEW}),


            'frame_tabla_detalle_pedidos': ('frame_principal', 'Pedidos',
                                            {'row': 1, 'column': 1, 'pady': 2, 'padx': 2,
                                             'sticky': tk.NSEW}),

            'frame_tabla_detalle_partidas': ('frame_principal', 'Partidas',
                                             {'row': 1, 'column': 2, 'pady': 2, 'padx': 2,
                                              'sticky': tk.NSEW}),

            'frame_componentes': ('frame_tabla_horarios', None,
                                  {'row': 3, 'column': 0, 'pady': 2, 'padx': 2,
                                   'sticky': tk.NSEW}),

            'frame_den_fecha': ('frame_componentes', None,
                                {'row': 0, 'column': 1, 'pady': 2, 'padx': 2,
                                 'sticky': tk.W}),

            'frame_txt_comentario': ('frame_tabla_detalle_pedidos', None,
                                     {'row': 3, 'column': 0, 'pady': 2, 'padx': 2,
                                      'sticky': tk.NSEW}),

            'frame_txt_especificacion': ('frame_tabla_detalle_partidas', None,
                                         {'row': 3, 'column': 0, 'pady': 2, 'padx': 2,
                                          'sticky': tk.NSEW}),

            'frame_botones': ('frame_principal', None,
                              {'row': 4, 'column': 1, 'padx': 0, 'pady': 5, 'sticky': tk.W}),
        }
        self._ventanas.crear_frames(frames)

    def _crear_componentes_forma(self):
        componentes = {

                'txt_comentario': ('frame_txt_comentario', None, ' ', None),
                'txt_especificacion': ('frame_txt_especificacion', None, ' ', None),
                'den_fecha': ('frame_componentes', None, ' ', None),
                'btn_aceptar': ('frame_botones', 'PRIMARY', 'Aceptar', None),
                'btn_cancelar': ('frame_botones', 'DANGER', 'Cancelar', None),
                'tvw_horarios': ('frame_tabla_horarios', self._crear_columnas_tabla_horarios(), 15, None),
                'tvw_pedidos': ('frame_tabla_detalle_pedidos', self._crear_columnas_tabla_pedidos(), 15, 'DANGER'),
                'tvw_detalle_partidas': ('frame_tabla_detalle_partidas', self._crear_columnas_tabla_detalle(), 15, 'WARNING'),
                'lbl_total_horarios': ('frame_total_horarios',
                                    {'text': 'TOTAL HORARIOS:', 'style': 'inverse-primary', 'anchor': 'center',
                                     'font': ('Consolas', 20, 'bold')},
                                    {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                    None),

            'lbl_total_pedidos': ('frame_total_pedidos',
                                {'text': 'TOTAL PEDIDOS:', 'style': 'inverse-danger', 'anchor': 'center',
                                 'font': ('Consolas', 20, 'bold')},
                                {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                None),

            'lbl_total_partidas': ('frame_total_partidas',
                                {'text': 'TOTAL PARTIDAS:', 'style': 'inverse-warning', 'anchor': 'center',
                                 'font': ('Consolas', 20, 'bold')},
                                {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                None),
        }
        self._ventanas.crear_componentes(componentes)

        frames = ['frame_total_horarios', 'frame_total_pedidos', 'frame_total_partidas']
        for nombre_frame in frames:
            frame = self._ventanas.componentes_forma[nombre_frame]
            frame.grid_columnconfigure(0, weight=1)  # La única columna en el frame se expande
            frame.grid_rowconfigure(0, weight=1)

    def _rellenar_tabla_pedidos(self):
        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_horarios'):
            return

        self._ventanas.limpiar_componentes(['tvw_pedidos',
                                            'tvw_detalle_partidas',
                                            'txt_especificacion',
                                            'txt_comentario',
                                            'lbl_total_pedidos',
                                            'lbl_total_partidas',
                                            ])

        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_horarios')
        valores_fila = self._ventanas.procesar_fila_treeview('tvw_horarios', fila)
        consulta_pedidos = self._base_de_datos.fetchall(self._crear_sql_consulta_horarios(),
                                                        (self._ventanas.obtener_input_componente('den_fecha'),
                                                        valores_fila['ScheduleID']))

        consulta_filtrada = []
        cancelados = 0
        for pedido in consulta_pedidos:
            status = pedido['Status']
            if status == 'Cancelado':
                cancelados += 1
            consulta_filtrada.append(
                {
                    'FolioPedido': pedido['FolioPedido'],
                    'Tipo': pedido['Tipo'],
                    'Cliente': pedido['Cliente'],
                    'Total': pedido['Total'],
                    'HoraEntrega': pedido['HoraEntrega'],
                    'Status': status,
                    'OrderDocumentID': pedido['OrderDocumentID'],
                    'Comentarios': pedido['Comentarios']
                }
            )

        self._ventanas.rellenar_treeview('tvw_pedidos',
                                         self._crear_columnas_tabla_pedidos(),
                                         consulta_filtrada,
                                         valor_barra_desplazamiento=15,
                                         variar_color_filas=True
                                         )
        self._ventanas.insertar_input_componente('lbl_total_pedidos', f'TOTAL: {len(consulta_filtrada) -cancelados}')

    def _crear_sql_consulta_horarios(self):
        return """
            SELECT       
                    ISNULL(P.FolioPrefix, '') + ISNULL(P.Folio, '') AS FolioPedido,            
                    ISNULL(P2.FolioPrefix, '') + ISNULL(P2.Folio, '') AS Relacionado,          
                    TDP.Value AS Tipo,                                                         
                    FORMAT(P.CreatedOn, 'dd-MM-yy') AS FechaCaptura,             
                    dbo.FORMAT(P.CreatedOn, N'HH:mm') AS HoraCaptura, 
                    FORMAT(P.DeliveryPromise, 'dd-MM-yy')  AS FechaEntrega,                        
                    H.Value AS HoraEntrega,                                                    
                    E.OfficialName AS Cliente,                                                 
                    SUBSTRING(Z.ZoneName, 1, 3) AS Ruta,                                       
                    FORMAT(P.Total, 'C', 'es-MX') Total,                                               
                    UC.UserName AS CapturadoPor,                                               
                    TDR.Value AS Prioridad,                                                    
                    TDE.DeliveryTypesName AS TipoEntrega,
                    CASE
                        WHEN P.StorePrintedOn IS NOT NULL AND P.ProductionPrintedOn IS NULL AND P.WarehousePrintedOn IS NULL THEN 'M'
                        WHEN P.StorePrintedOn IS NULL AND P.ProductionPrintedOn IS NOT NULL AND P.WarehousePrintedOn IS NULL THEN 'P'
                        WHEN P.StorePrintedOn IS NULL AND P.ProductionPrintedOn IS NULL AND P.WarehousePrintedOn IS NOT NULL THEN 'A'
                        ELSE
                            COALESCE(
                                CASE WHEN P.StorePrintedOn IS NOT NULL THEN 'M' ELSE NULL END, ''
                            ) +
                            COALESCE(
                                CASE WHEN P.ProductionPrintedOn IS NOT NULL THEN 'P' ELSE NULL END, ''
                            ) +
                            COALESCE(
                                CASE WHEN P.WarehousePrintedOn IS NOT NULL THEN 'A' ELSE NULL END, ''
                            )
                    END AS  PrintedStatus,                                       
                    TS.Value AS TipoProduccion,         
                    CASE
                        WHEN P.StoreAssignedDate IS NOT NULL AND P.AssignedUserProductionDate IS NULL AND P.WarehouseAssignedDate IS NULL THEN 'M'
                        WHEN P.StoreAssignedDate IS NULL AND P.AssignedUserProductionDate IS NOT NULL AND P.WarehouseAssignedDate IS NULL THEN 'P'
                        WHEN P.StoreAssignedDate IS NULL AND P.AssignedUserProductionDate IS NULL AND P.WarehouseAssignedDate IS NOT NULL THEN 'A'
                        ELSE
                            COALESCE(
                                CASE WHEN P.StoreAssignedDate IS NOT NULL THEN 'M' ELSE NULL END, ''
                            ) +
                            COALESCE(
                                CASE WHEN P.AssignedUserProductionDate IS NOT NULL THEN 'P' ELSE NULL END, ''
                            ) +
                            COALESCE(
                                CASE WHEN P.WarehouseAssignedDate IS NOT NULL THEN 'A' ELSE NULL END, ''
                            )
                    END AS AssignedArea,

                    CASE
                        WHEN P.FinishedPreparingStore IS NOT NULL AND P.FinishedPreparingProduction IS NULL AND P.FinishedPreparingWarehouse IS NULL THEN 'M'
                        WHEN P.FinishedPreparingStore IS NULL AND P.FinishedPreparingProduction IS NOT NULL AND P.FinishedPreparingWarehouse IS NULL THEN 'P'
                        WHEN P.FinishedPreparingStore IS NULL AND P.FinishedPreparingProduction IS NULL AND P.FinishedPreparingWarehouse IS NOT NULL THEN 'A'
                        ELSE
                            COALESCE(
                                CASE WHEN P.FinishedPreparingStore IS NOT NULL THEN 'M' ELSE NULL END, ''
                            ) +
                            COALESCE(
                                CASE WHEN P.FinishedPreparingProduction IS NOT NULL THEN 'P' ELSE NULL END, ''
                            ) +
                            COALESCE(
                                CASE WHEN P.FinishedPreparingWarehouse IS NOT NULL THEN 'A' ELSE NULL END, ''
                            )
                    END AS  FinalizationTypeOrderFulfillment, 
                    
                    
                    
                    P.OrderDocumentID,                                                         
                    P.CommentsOrder AS Comentarios,                                            
                    H.ScheduleID,                                                              
                    P.PriorityID,                                                              
                    TS.ProductionTypesID,                                                      
                    CASE WHEN P.CancelledOn IS NOT NULL THEN 1 ELSE 0 END Cancelled, 
                    C.CustomerTypeID,
                    S.TypeStatusName Status
                    
                FROM    
                    dbo.docDocumentOrderCayal AS P INNER JOIN
                    dbo.orgBusinessEntity AS E ON P.BusinessEntityID = E.BusinessEntityID INNER JOIN
                    dbo.engUser AS UC ON P.CreatedBy = UC.UserID INNER JOIN
                    dbo.OrderSchedulesCayal AS H ON P.ScheduleID = H.ScheduleID INNER JOIN
                    dbo.OrderTypesCayal AS TDP ON P.OrderTypeID = TDP.ID INNER JOIN
                    dbo.OrdersDeliveryTypesCayal AS TDE ON P.OrderDeliveryTypeID = TDE.DeliveryTypesID INNER JOIN
                    dbo.OrderTypesOriginsCayal AS TDO ON P.OrderTypeOriginID = TDO.ID INNER JOIN
                    dbo.OrdersProductionTypesCayal AS TS ON P.ProductionTypeID = TS.ProductionTypesID INNER JOIN
                    dbo.OrderTypesPriorityCayal AS TDR ON P.PriorityID = TDR.ID INNER JOIN
                    dbo.OrderPaymentConfirmedOptions AS TCPO ON P.PaymentConfirmedID = TCPO.ID INNER JOIN
                    dbo.OrdersPaymentTermCayal AS TFP ON P.WayToPayID = TFP.PaymentTermID INNER JOIN
                    dbo.OrderStatusTypesCayal AS S ON P.StatusID = S.TypeStatusID INNER JOIN
                    dbo.orgZone AS Z ON P.ZoneID = Z.ZoneID LEFT OUTER JOIN
                    dbo.docDocumentOrderCayal AS P2 ON P.OrderDocumentID = P2.RelatedOrderID INNER JOIN
                    dbo.orgCustomer C ON P.BusinessEntityID = C.BusinessEntityID
                WHERE CAST(P.DeliveryPromise as date) = CAST( ? as date)
                 AND H.ScheduleID = ? 
                 ORDER BY S.TypeStatusName
        """

    def _rellenar_tabla_partidas(self):

        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_pedidos'):
            return

        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_pedidos')
        valores_fila = self._ventanas.procesar_fila_treeview('tvw_pedidos', fila)

        self._ventanas.limpiar_componentes(['tvw_detalle_partidas', 'txt_especificacion'])

        order_document_id = valores_fila['OrderDocumentID']
        consulta_partidas = self._base_de_datos.buscar_partidas_pedidos_produccion_cayal(
            order_document_id, partidas_eliminadas=True, partidas_producidas=True)


        consulta_partidas_con_impuestos = self._utilerias.agregar_impuestos_productos(consulta_partidas)
        for producto in consulta_partidas_con_impuestos:
            precio_con_impuestos = producto['SalePriceWithTaxes']
            cantidad_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(producto['Quantity'])
            total = self._utilerias.redondear_valor_cantidad_a_decimal(precio_con_impuestos * cantidad_decimal)
            product_id = producto['ProductID']

            if product_id == 5606:
                continue

            datos_fila = (
                cantidad_decimal,
                producto['ProductKey'],
                producto['ProductName'],
                precio_con_impuestos,
                total,
                producto['Esp'],
                producto['ProductID'],
                producto['DocumentItemID'],
                producto['ItemProductionStatusModified'],
                producto['ClaveUnidad'],
                0, # status surtido
                producto['UnitPrice'],
                producto['CayalPiece'],
                producto['CayalAmount'],
                producto['Comments'],
                producto['ProductTypeIDCayal']
            )
            self._ventanas.insertar_fila_treeview('tvw_detalle_partidas', datos_fila)

        self._ventanas.insertar_input_componente('lbl_total_partidas', f'TOTAL: {len(consulta_partidas_con_impuestos)}')

    def _rellenar_comentarios_partidas(self):
        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_detalle_partidas'):
            return

        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_detalle_partidas')
        valores_fila = self._ventanas.procesar_fila_treeview('tvw_detalle_partidas', fila)
        self._ventanas.insertar_input_componente('txt_especificacion', valores_fila['Comments'])

    def _cargar_eventos(self):
        eventos = {
            'btn_aceptar': self._master.destroy,
            'btn_cancelar': self._master.destroy,
            'den_fecha': lambda event:self._rellenar_tabla_horarios(),
            'tvw_horarios': (lambda event:self._rellenar_tabla_pedidos(), 'doble_click'),
            'tvw_pedidos': (lambda event:self._rellenar_tabla_partidas(), 'doble_click'),
            'tvw_detalle_partidas': (lambda event: self._rellenar_comentarios_partidas(), 'seleccion')
        }

        self._ventanas.cargar_eventos(eventos)
        evento_adicional = {
            'tvw_pedidos': (lambda event: self._actualizar_comentario_pedido(), 'seleccion'),

        }

        self._ventanas.cargar_eventos(evento_adicional)

    def _crear_columnas_tabla_horarios(self):
        return [
            {"text": "Cantidad", "stretch": False, 'width': 60, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Fecha", "stretch": False, 'width': 95, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Hora", "stretch": False, 'width': 85, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "ScheduleID", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            ]

    def _crear_columnas_tabla_pedidos(self):
        return [
            {"text": "Folio", "stretch": False, 'width': 75, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Tipo", "stretch": False, 'width': 75, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Cliente", "stretch": False, 'width': 110, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Total", "stretch": False, 'width': 80, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "H.Entrega", "stretch": False, 'width': 70, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Status", "stretch": False, 'width': 70, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "OrderDocumentID", "stretch": False, 'width': 110, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "CommentsOrder", "stretch": False, 'width': 110, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
        ]

    def _crear_columnas_tabla_detalle(self):
        return [
            {"text": "Cantidad", "stretch": False, 'width': 68, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Clave", "stretch": False, 'width': 80, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Producto", "stretch": False, 'width': 165, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Precio", "stretch": False, 'width': 65, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Total", "stretch": False, 'width': 70, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Esp.", "stretch": False, 'width': 35, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "ProductID", "stretch": False, 'width': 80, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "DocumentItemID", "stretch": False, 'width': 80, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "ItemProductionStatusModified", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "ClaveUnidad", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "StatusSurtido", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "UnitPrice", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "CayalPiece", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "CayalAmount", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "Comments", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "ProductTypeIDCayal", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
        ]

    def _rellenar_tabla_horarios(self):
        self._limpiar_componentes()
        consulta = self._base_de_datos.fetchall("""
            SELECT H.ScheduleID, H.Value, H.Quantity, H.Status,
                                ISNULL(ORI.OrdersNumber, 0) AS OrdersNumber
                            FROM OrderSchedulesCayal H
                            LEFT OUTER JOIN (
                                SELECT COUNT(P.OrderDocumentID) AS OrdersNumber,
                                    E.ScheduleID,
                                    E.Value
                                FROM docDocumentOrderCayal P
                                INNER JOIN OrderSchedulesCayal E ON P.ScheduleID = E.ScheduleID
                                INNER JOIN OrderTypesCayal T ON P.OrderTypeID = T.ID
                                INNER JOIN OrderStatusTypesCayal S ON P.StatusID = S.TypeStatusID
                                WHERE P.CancelledOn IS NULL 
                                AND CAST( ?  AS date) = CAST(P.DeliveryPromise AS date)
                                AND P.OrderTypeID = 1
                                --AND P.StatusID in (2, 10, 16, 17, 18)
                                GROUP BY E.ScheduleID, E.Value
                            ) AS ORI ON H.ScheduleID = ORI.ScheduleID
                            
        """,self._ventanas.obtener_input_componente('den_fecha'),)

        consulta_agrupada = self._agrupar_por_fecha_y_horarios(consulta)
        consulta_filtrada = self._procesar_filas(consulta_agrupada)


        self._ventanas.rellenar_treeview('tvw_horarios',
                                         self._crear_columnas_tabla_horarios(),
                                         consulta_filtrada,
                                         valor_barra_desplazamiento=10,
                                         variar_color_filas=True)

        self._consulta_horarios = consulta_filtrada
        valores_horario = [reg['numero']for reg in consulta_filtrada]
        total_pedidos = sum(valores_horario)
        self._ventanas.insertar_input_componente('lbl_total_horarios', f"TOTAL: {total_pedidos}")

    def _procesar_filas(self, consulta_agrupada):
        return [
            {
                'numero': reg['OrdersNumber'],
                'fecha': datetime.now().date(),
                'horario': reg['Value'],
                'schedule': reg['ScheduleID']
            }
                for reg in consulta_agrupada]

    def _agrupar_por_fecha_y_horarios(self, consulta):
        return [reg for reg in consulta if reg['OrdersNumber'] != 0]

    def _limpiar_componentes(self):
        componentes = ['tvw_horarios', 'tvw_pedidos', 'tvw_detalle_partidas', 'txt_comentario', 'txt_especificacion',
                       'lbl_total_pedidos',
                       'lbl_total_partidas',
                       ]
        self._ventanas.limpiar_componentes(componentes)

    def _actualizar_comentario_pedido(self):
        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_pedidos'):
            return

        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_pedidos')
        valores_fila = self._ventanas.procesar_fila_treeview('tvw_pedidos', fila)
        self._ventanas.insertar_input_componente('txt_comentario', valores_fila['CommentsOrder'])
        self._ventanas.limpiar_componentes(['tvw_detalle_partidas', 'txt_especificacion'])
