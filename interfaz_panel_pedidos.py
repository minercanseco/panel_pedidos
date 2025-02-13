import tkinter as tk
from cayal.ventanas import Ventanas


class InterfacPanelPedidos:
    def __init__(self, master):
        self.master = master
        self.ventanas = Ventanas(self.master)

        self._cargar_frames()
        self._cargar_componentes_forma()
        self.ventanas.configurar_ventana_ttkbootstrap(titulo='Panel captura', master=self.master)

    def _cargar_frames(self):
        frames = {

            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_herramientas': ('frame_principal', 'Herramientas',
                                   {'row': 0, 'column': 0, 'pady': 2, 'padx': 2,
                                    'sticky': tk.W}),

            'frame_totales': ('frame_principal', None,
                              {'row': 0, 'column': 1, 'pady': 2, 'padx': 2,
                               'sticky': tk.E}),
            'frame_meters': ('frame_totales', None,
                             {'row': 0, 'column': 0, 'pady': 2, 'padx': 2,
                              'sticky': tk.W}),

            'frame_filtros': ('frame_principal', 'Filtros',
                              {'row': 2, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                               'sticky': tk.NSEW}),

            'frame_horarios': ('frame_filtros', None,
                               {'row': 0, 'column': 0, 'pady': 2, 'padx': 2,
                                'sticky': tk.W}),

            'frame_fecha': ('frame_filtros', None,
                            {'row': 0, 'column': 1, 'pady': 2, 'padx': 2,
                             'sticky': tk.W}),

            'frame_capturista': ('frame_filtros', None,
                            {'row': 0, 'column': 2, 'pady': 2, 'padx': 2,
                             'sticky': tk.W}),

            'frame_status': ('frame_filtros', None,
                                {'row': 0, 'column': 3, 'pady': 2, 'padx': 2,
                                 'sticky': tk.W}),

            'frame_captura': ('frame_principal', 'Pedidos',
                              {'row': 3, 'columnspan': 2, 'column': 0, 'pady': 2, 'padx': 2,
                               'sticky': tk.NSEW}),

            'frame_comentarios': ('frame_principal', 'Comentarios',
            {'row': 4, 'columnspan': 2, 'column': 0, 'pady': 2, 'padx': 2,
             'sticky': tk.NSEW}),

        'frame_detalle': ('frame_principal', 'Detalle',
                              {'row': 5, 'columnspan': 2, 'column': 0, 'pady': 2, 'padx': 2,
                               'sticky': tk.NSEW}),

        }

        self.ventanas.crear_frames(frames)

    def _cargar_componentes_forma(self):
        componentes = {
            'cbx_horarios': ('frame_horarios', None, 'Horas:', None),

            'cbx_capturista': ('frame_capturista', None, 'Capturó:', None),

            'cbx_status': ('frame_status', None, 'Status:', None),

            'den_fecha': ('frame_fecha',
                          None,  # {'row': 0, 'column': 0, 'pady': 5, 'padx': 5, 'sticky': tk.W},
                          ' ', None),


            'mtr_total': ('frame_meters', None, 'Total', None),
            'mtr_en_tiempo': ('frame_meters', 'success', 'En tiempo', None),
            'mtr_a_tiempo': ('frame_meters', 'warning', 'A tiempo', None),
            'mtr_retrasado': ('frame_meters', 'danger', 'Retrasos', None),
            'tbx_comentarios': ('frame_comentarios', {'row': 0, 'column': 1, 'pady': 5, 'padx': 2, 'sticky': tk.NSEW},
                                ' ', None),
            'tvw_detalle':('frame_detalle', self.crear_columnas_tabla_detalle(), 5, None)
        }

        self.ventanas.crear_componentes(componentes)
        frame_comentario = self.ventanas.componentes_forma['frame_comentarios']
        frame_comentario.columnconfigure(1, weight=1)  # Asegurar que la columna 1 se extienda
        frame_comentario.rowconfigure(0, weight=1)

    def crear_columnas_tabla_detalle(self):
        return [
            {"text": "Cantidad", "stretch": False, 'width': 68, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Clave", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Producto", "stretch": False, 'width': 445, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Precio", "stretch": False, 'width': 80, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Total", "stretch": False, 'width': 100, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Esp.", "stretch": False, 'width': 35, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "ProductID", "stretch": False, 'width': 80, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "DocumentItemID", "stretch": False, 'width': 80, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "ItemProductionStatusModified", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "ClaveUnidad", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "StatusSurtido", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "UnitPrice", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "Piezas", "stretch": False, 'width': 60, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Monto", "stretch": False, 'width': 60, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Especificaciones", "stretch": False, 'width': 440, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "ProductTypeIDCayal", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
        ]

    def crear_columnas_tabla(self):
        return [
            {"text": "Pedido", "stretch": True, "width": 80},
            {"text": "Relacion", "stretch": True, "width": 80},
            {"text": "Factura", "stretch": True, "width": 80},
            {"text": "Cliente", "stretch": False, "width": 130},
            {"text": "F.Captura", "stretch": True, "width": 70},
            {"text": "H.Captura", "stretch": True, "width": 45},
            {"text": "Captura", "stretch": True, "width": 65},
            {"text": "F.Entrega", "stretch": False, "width": 0},
            {"text": "H.Entrega", "stretch": True, "width": 45},
            {"text": "Direccion", "stretch": True, "width": 80},
            {"text": "HoraID", "stretch": False, "width": 0},
            {"text": "WayToPayID", "stretch": False, "width": 0},
            {"text": "F.Pago", "stretch": True, "width": 70},
            {"text": "Status", "stretch": True, "width": 70},
            {"text": "Ruta", "stretch": True, "width": 40},
            {"text": "OrderTypeID", "stretch": False, "width": 0},
            {"text": "Tipo", "stretch": True, "width": 50},
            {"text": "OrderDeliveryTypeID", "stretch": False, "width": 0},
            {"text": "T.Entrega", "stretch": True, "width": 70},
            {"text": "OrderTypeOriginID", "stretch": False, "width": 0},
            {"text": "Origen", "stretch": True, "width": 70},
            {"text": "ProductionTypeID", "stretch": False, "width": 0},
            {"text": "Áreas", "stretch": True, "width": 50},
            {"text": "PriorityID", "stretch": False, "width": 0},
            {"text": "Prioridad", "stretch": True, "width": 70},
            {"text": "DocumentTypeID", "stretch": False, "width": 0},
            {"text": "T.Docto", "stretch": True, "width": 65},
            {"text": "Adicionales", "stretch": False, "width": 0},
            {"text": "PaymentConfirmedID", "stretch": False, "width": 0},
            {"text": "Pago", "stretch": True, "width": 75},
            {"text": "SubTotal", "stretch": False, "width": 0},
            {"text": "Impuestos", "stretch": False, "width": 0},
            {"text": "Cancelado", "stretch": False, "width": 0},
            {"text": "Total", "stretch": True, "width": 85},
            {"text": "T.Factura", "stretch": True, "width": 85},
            {"text": "Mensajes", "stretch": False, "width": 0},
            {"text": "TypeStatusID", "stretch": False, "width": 0},
            {"text": "StatusScheduleID", "stretch": False, "width": 0},
            {"text": "PrintedStatus", "stretch": False, "width": 0},
            {"text": "Comentarios", "stretch": False, "width": 0},
            {"text": "OrderDocumentID", "stretch": False, "width": 0},
            {"text": "BusinessEntityID", "stretch": False, "width": 0},
            {"text": "DepotID", "stretch": False, "width": 0},
            {"text": "AddressDetailID", "stretch": False, "width": 0},
            {"text": "CaptureBy", "stretch": False, "width": 0}
        ]