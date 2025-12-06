import tkinter as tk
from cayal.ventanas import Ventanas
from herramientas.herramientas_compartidas.historial_pedido import HistorialPedido


class BuscarPedido:
    def __init__(self, master, base_de_datos, utilerias, parametros):
        self._master = master
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._parametros = parametros
        self._ventanas = Ventanas(self._master)

        self._crear_frames()
        self._cargar_componentes()
        self._cargar_eventos()

        self._ventanas.configurar_ventana_ttkbootstrap(master=self._master)

        self._rellenar_tabla_pedidos()

    def _crear_frames(self):
        frames = {

            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_buscar': ('frame_principal', 'Buscar:',
                                    {'row': 1, 'column': 0, 'columnspan': 4, 'pady': 2, 'padx': 2,
                                     'sticky': tk.NSEW}),

            'frame_btn_buscar': ('frame_buscar', None,
                                 {'row': 0, 'column': 2, 'pady': 2, 'padx': 2,
                                  'sticky': tk.NSEW}),

            'frame_den_fecha': ('frame_buscar', None,
                                {'row': 0, 'column': 4, 'pady': 2, 'padx': 2,
                                 'sticky': tk.NSEW}),

            'frame_tabla_pedidos': ('frame_principal', 'Pedidos:',
                                      {'row': 3, 'column': 0, 'columnspan': 4, 'pady': 2, 'padx': 2,
                                       'sticky': tk.NSEW}),
            'frame_historial': ('frame_tabla_pedidos', None,
                                  {'row': 1, 'column': 0, 'columnspan': 4, 'pady': 2, 'padx': 2,
                                   'sticky': tk.NSEW}),

            'frame_tabla_detalle': ('frame_principal', 'Detalle:',
                                    {'row': 5, 'column': 0, 'columnspan': 4, 'pady': 2, 'padx': 2,
                                     'sticky': tk.NSEW}),
            'frame_comentarios': ('frame_tabla_detalle', 'Comentarios:',
                                    {'row': 1, 'column': 0, 'columnspan': 4, 'pady': 2, 'padx': 2,
                                     'sticky': tk.NSEW}),

            'frame_botones': ('frame_principal', None,
                              {'row': 7, 'column': 1, 'padx': 0, 'pady': 5, 'sticky': tk.W}),
        }
        self._ventanas.crear_frames(frames)

    def _crear_columnas_pedidos(self):
        return [
            {"text": "Folio", "stretch": False, 'width': 85, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Cliente", "stretch": False, 'width': 135, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Tipo", "stretch": False, 'width': 70, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "H.Entrega", "stretch": False, 'width': 70, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Dirección", "stretch": False, 'width': 110, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Ruta", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Status", "stretch": False, 'width': 80, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "OrderDocumentID", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "Comments", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
        ]

    def _crear_columnas_detalle(self):
        return [
            {"text": "Cantidad", "stretch": False, 'width': 70, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Clave", "stretch": False, 'width': 110, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Producto", "stretch": False, 'width': 210, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Precio", "stretch": False, 'width': 75, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Total", "stretch": False, 'width': 80, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Esp.", "stretch": False, 'width': 35, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Comments", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
        ]

    def _cargar_componentes(self):
        componentes = {
            'tbx_buscar': ('frame_buscar', None, ' ', None),
            'btn_limpiar': ('frame_btn_buscar', 'WARNING', 'Limpiar', None),
            'den_fecha': ('frame_den_fecha', None, 'Fecha:', None),
            'btn_aceptar': ('frame_botones', 'PRIMARY', 'Aceptar', None),
            'btn_cancelar': ('frame_botones', 'DANGER', 'Cancelar', None),

            'tvw_pedidos': ('frame_tabla_pedidos', self._crear_columnas_pedidos(), 5, 'Primary'),
            'btn_historial': ('frame_historial', 'WARNING', 'Historial', None),
            'tvw_detalle': ('frame_tabla_detalle', self._crear_columnas_detalle(), 5, 'Danger'),
            'txt_comentario': ('frame_comentarios', None, 'Comentario:', None),
            'txt_especificacion': ('frame_comentarios', None, 'Especificación:', None),
        }
        self._ventanas.crear_componentes(componentes)

    def _cargar_eventos(self):
        eventos = {
            'btn_cancelar': self._master.destroy,
            'btn_aceptar': self._master.destroy,
            'btn_limpiar': self._limpiar_componentes,
            'tbx_buscar': lambda event: self._filtrar_tabla_pedidos(),
            'btn_historial': self._historial_pedido,
            'tvw_pedidos': (lambda event: self._rellenar_tabla_detalle(), 'doble_click'),
            'tvw_detalle':  (lambda event: self._actualizar_especificacion(), 'seleccion'),
            'den_fecha': lambda event: self._rellenar_tabla_pedidos()
        }
        self._ventanas.cargar_eventos(eventos)

        eventos_adicionales = {
            'tvw_pedidos': (lambda event: self._actualizar_comentario_pedido(), 'seleccion')
        }
        self._ventanas.cargar_eventos(eventos_adicionales)

    def _actualizar_comentario_pedido(self):
        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_pedidos')

        if not fila:
            return

        if len(fila) > 1:
            return

        self._ventanas.limpiar_componentes('txt_comentario')
        valores_fila = self._ventanas.procesar_fila_treeview('tvw_pedidos', fila)
        comentario = valores_fila['Comments']
        self._ventanas.insertar_input_componente('txt_comentario', comentario)
        self._limpiar_tabla_detalle()

    def _limpiar_tabla_detalle(self):
        self._ventanas.limpiar_componentes('tvw_detalle')
        self._ventanas.limpiar_componentes('txt_especificacion')

    def _actualizar_especificacion(self):
        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_detalle')

        if not fila:
            return

        if len(fila) > 1:
            return

        self._ventanas.limpiar_componentes('txt_especificacion')
        valores_fila = self._ventanas.procesar_fila_treeview('tvw_detalle', fila)
        comentario = valores_fila['Comments']
        self._ventanas.insertar_input_componente('txt_especificacion', comentario)

    def _historial_pedido(self):
        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_pedidos'):
            return

        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_pedidos')
        valores_fila = self._ventanas.procesar_fila_treeview('tvw_pedidos', fila)
        order_document_id = valores_fila['OrderDocumentID']

        ventana = self._ventanas.crear_popup_ttkbootstrap(titulo='Historial pedido')
        self._parametros.id_principal = order_document_id
        instancia = HistorialPedido(ventana, self._parametros, self._base_de_datos)
        ventana.wait_window()
        self._parametros.id_principal = 0

    def _rellenar_tabla_pedidos(self):
        fecha = self._ventanas.obtener_input_componente('den_fecha')
        consulta = self._buscar_pedidos(fecha)
        if consulta:
            self._ventanas.rellenar_treeview('tvw_pedidos',
                                             self._crear_columnas_pedidos(),
                                             consulta,
                                             valor_barra_desplazamiento=5)
        if not consulta:
            self._ventanas.limpiar_componentes('tvw_pedidos')

    def _buscar_pedidos(self, fecha):
        return self._base_de_datos.fetchall("""
            SELECT       
                ISNULL(P.FolioPrefix, '') + ISNULL(P.Folio, '') AS FolioPedido,            
                E.OfficialName AS Cliente,        
                TDP.Value AS Tipo,
                H.Value AS HoraEntrega,
                ad.AddressName AS Direccion,                                                            
                SUBSTRING(Z.ZoneName, 1, 3) AS Ruta,
                S.TypeStatusName AS Status,
                P.OrderDocumentID,
                P.CommentsOrder
            FROM    
                dbo.docDocumentOrderCayal AS P
            INNER JOIN dbo.orgBusinessEntity AS E ON P.BusinessEntityID = E.BusinessEntityID
            INNER JOIN dbo.orgAddressDetail AS ADT ON P.AddressDetailID = ADT.AddressDetailID
            INNER JOIN dbo.orgAddress AS ad ON ADT.AddressDetailID = ad.AddressDetailID
            INNER JOIN dbo.OrderTypesCayal AS TDP ON P.OrderTypeID = TDP.ID
            INNER JOIN dbo.OrderStatusTypesCayal AS S ON P.StatusID = S.TypeStatusID
            INNER JOIN dbo.orgZone AS Z ON P.ZoneID = Z.ZoneID
            INNER JOIN  dbo.OrderSchedulesCayal AS H ON P.ScheduleID = H.ScheduleID 
            
            WHERE 
                CAST(P.DeliveryPromise AS date) = CAST(? AS date)
            ORDER BY 
                P.StatusID, H.Value
                
        """,(fecha,))

    def _rellenar_tabla_detalle(self):
        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_pedidos'):
            return

        fila =  self._ventanas.obtener_seleccion_filas_treeview('tvw_pedidos')
        if not fila:
            return

        valores_pedido = self._ventanas.procesar_fila_treeview('tvw_pedidos', fila)
        order_document_id = valores_pedido['OrderDocumentID']

        consulta_partidas = self._base_de_datos.buscar_partidas_pedidos_produccion_cayal(
            order_document_id,
            partidas_eliminadas=False,
            partidas_producidas=True)

        partidas = self._procesar_partidas(consulta_partidas)

        self._ventanas.rellenar_treeview('tvw_detalle',
                                         self._crear_columnas_detalle(),
                                         partidas,
                                         valor_barra_desplazamiento=5)

    def _procesar_partidas(self, partidas_a_procesar):
        partidas = self._utilerias.agregar_impuestos_productos(partidas_a_procesar)

        nuevas_partidas = []
        for partida in partidas:

            if partida['ProductID'] == 5606:
                continue

            cantidad = self._utilerias.redondear_valor_cantidad_a_decimal(partida['Quantity'])
            precio = self._utilerias.redondear_valor_cantidad_a_decimal(partida['SalePriceWithTaxes'])
            total = cantidad*precio
            total = f"{total:.2f}"
            nueva_partida = {
                'Quantity': cantidad,
                'ProductKey': partida['ProductKey'],
                'ProductName': partida['ProductName'],
                'UnitPrice': precio,
                'Total': total,
                'Esp': partida['Esp'],
                'Comments': partida['Comments']
            }
            nuevas_partidas.append(nueva_partida)

        return nuevas_partidas

    def _filtrar_tabla_pedidos(self):
        termino = self._ventanas.obtener_input_componente('tbx_buscar')

        if not termino:
            return

        if termino.strip() == '':
            return

        self._rellenar_tabla_pedidos()
        self._limpiar_tabla_detalle()
        self._ventanas.filtrar_campos_treeview(
            'tvw_pedidos', termino, [
                'Folio',
                'Cliente',
                'Tipo',
                'H.Entrega',
                'Dirección',
                'Ruta',
                'Status'], False
        )

    def _limpiar_componentes(self):
        self._ventanas.limpiar_componentes('tbx_buscar')
        self._rellenar_tabla_pedidos()
        self._limpiar_tabla_detalle()

