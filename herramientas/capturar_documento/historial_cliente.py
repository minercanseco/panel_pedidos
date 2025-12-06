import tkinter as tk
from cayal.ventanas import Ventanas


class HistorialCliente:
    def __init__(self, master, base_de_datos, utilerias, bussiness_entity_id):

        self._master = master
        self._ventanas = Ventanas(self._master)
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias

        self._business_entity_id = bussiness_entity_id
        self._cargar_frames()
        self._cargar_componentes()
        self._rellenar_componentes()
        self._cargar_eventos()
        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Historial del cliente')

    def _cargar_frames(self):
        frames = {

            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_tabla': ('frame_principal', 'Documentos:',
                                    {'row': 1, 'column': 0, 'columnspan': 4, 'pady': 2, 'padx': 2,
                                     'sticky': tk.NSEW}),

            'frame_tabla_detalle': ('frame_principal', 'Detalle documento seleccionado:',
                                    {'row': 2, 'column': 0, 'columnspan': 4, 'pady': 2, 'padx': 2,
                                     'sticky': tk.NSEW}),

            'frame_comentarios': ('frame_principal', 'Comentarios:',
                                    {'row': 3, 'column': 0, 'columnspan': 4, 'pady': 2, 'padx': 2,
                                     'sticky': tk.NSEW}),

            'frame_comentarios_especificaciones': ('frame_principal', 'Especificaciones: ',
                                    {'row': 6, 'column': 0, 'columnspan': 4, 'pady': 2, 'padx': 2,
                                     'sticky': tk.NSEW}),

            'frame_botones': ('frame_principal', None,
                              {'row': 9, 'column': 1, 'padx': 0, 'pady': 5, 'sticky': tk.W}),
        }
        self._ventanas.crear_frames(frames)

    def _cargar_componentes(self):
        componentes = {
            'tvw_documentos': ('frame_tabla', self._crear_columnas_tabla(), 10, None),
            'tvw_detalle': ('frame_tabla_detalle', self._crear_columnas_tabla_detalle(), 10, 'Danger'),
            'txt_comentario_documento':('frame_comentarios', None, ' ', None ),
            'txt_especificacion':('frame_comentarios_especificaciones', None, ' ', None ),
            'btn_aceptar': ('frame_botones', None, 'Aceptar', None),
            'btn_cancelar': ('frame_botones', 'Danger', 'Cancelar', None),
        }
        self._ventanas.crear_componentes(componentes)
        self._ventanas.ajustar_componente_en_frame('txt_comentario_documento', 'frame_comentarios')
        self._ventanas.ajustar_componente_en_frame('txt_especificacion', 'frame_comentarios_especificaciones')

        self._ventanas.ajustar_ancho_componente('txt_comentario_documento',65)
        self._ventanas.ajustar_ancho_componente('txt_especificacion', 65)

    def _rellenar_componentes(self):
        consulta = self._buscar_historial_cliente(self._business_entity_id)
        self._ventanas.rellenar_treeview('tvw_documentos',
                                         self._crear_columnas_tabla(),
                                         consulta,
                                         variar_color_filas=True,
                                         valor_barra_desplazamiento=5
                                         )

    def _cargar_eventos(self):
        eventos = {
            'btn_cancelar': self._master.destroy,
            'btn_aceptar': self._master.destroy,
            'tvw_documentos':(lambda event:self._rellenar_tabla_detalle(), 'doble_click')
        }
        self._ventanas.cargar_eventos(eventos)

        evento_adicional = {
            'tvw_documentos': (lambda event: self._actualizar_comentario_documento(), 'seleccion'),
            'tvw_detalle': (lambda event: self._actualizar_comentario_especificacion(), 'seleccion')
        }
        self._ventanas.cargar_eventos(evento_adicional)

    def _actualizar_comentario_documento(self):
        self._limpiar_componentes()
        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_documentos'):
            return
        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_documentos')
        valores_fila = self._ventanas.procesar_fila_treeview('tvw_documentos', fila)
        comentario = valores_fila['Comments']

        comentario = comentario if comentario else ''

        self._ventanas.insertar_input_componente('txt_comentario_documento', comentario)

    def _actualizar_comentario_especificacion(self):
        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_detalle'):
            return

        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_detalle')
        valores_fila = self._ventanas.procesar_fila_treeview('tvw_detalle', fila)
        comentario = valores_fila['Comments']

        comentario = comentario if comentario else ''
        self._ventanas.insertar_input_componente('txt_especificacion', comentario)

    def _limpiar_componentes(self):
        componentes = ['tvw_detalle', 'txt_especificacion', 'txt_comentario_documento']
        self._ventanas.limpiar_componentes(componentes)

    def _buscar_historial_cliente(self, business_entity_id):
        return self._base_de_datos.fetchall(
            """
            SELECT  
                FORMAT(D.CreatedOn, 'dd-MM-yy') AS Fecha, 
                ISNULL(D.FolioPrefix,'') + ISNULL(D.Folio,'') DocFolio,
                CASE WHEN D.chkCustom1 = 1 THEN 'Remisión' ELSE 'Factura' END Tipo, 
                FORMAT(D.Total, 'C', 'es-MX') Total,                                               
                
                CFD.FormaPago, cfd.MetodoPago, CFD.ReceptorUsoCFDI UsoCFDI,
                CASE WHEN X.AddressDetailID = 0 THEN  ADE.AddressName ELSE   ad.AddressName END Dirección, 
                CASE WHEN X.AddressDetailID = 0 THEN  ADTE.City ELSE   ADT.City END Colonia, D.DocumentID, 
                D.Comments
            FROM docDocument D INNER JOIN
                docDocumentCFD CFD ON D.DocumentID = CFD.DocumentID INNER JOIN
                orgBusinessEntity E ON D.BusinessEntityID = E.BusinessEntityID INNER JOIN
                orgBusinessEntityMainInfo EM ON E.BusinessEntityID = EM.BusinessEntityID LEFT OUTER JOIN
                orgAddressDetail ADTE ON EM.AddressFiscalDetailID = ADTE.AddressDetailID LEFT OUTER JOIN
                orgAddress ADE ON ADTE.AddressDetailID = ADE.AddressDetailID LEFT OUTER JOIN
                docDocumentExtra X ON D.DocumentID = X.DocumentID LEFT OUTER JOIN
                orgAddressDetail ADT ON X.AddressDetailID = ADT.AddressDetailID LEFT OUTER JOIN
                orgAddress AD ON ADT.AddressDetailID = AD.AddressDetailID
            
            WHERE D.CancelledOn IS NULL AND D.ModuleID IN (21,1400,1316,1319) AND D.BusinessEntityID=?
            ORDER By D.DocumentID DESC
            """,(business_entity_id,)
        )

    def _crear_columnas_tabla(self):
        return [
            {"text": "Fecha", "stretch": False, 'width': 80, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Folio", "stretch": False, 'width': 80, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Tipo", "stretch": False, 'width': 90, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Total", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "FP", "stretch": False, 'width': 40, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "MP", "stretch": False, 'width': 40, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "CFDI", "stretch": False, 'width': 40, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Dirección", "stretch": False, 'width': 120, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Colonia", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "DocumentID", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "Comments", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
        ]

    def _crear_columnas_tabla_detalle(self):
        return [
            {"text": "Cantidad", "stretch": False, 'width': 68, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Clave", "stretch": False, 'width': 100, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Unidad", "stretch": False, 'width': 90, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Producto", "stretch": False, 'width': 250, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Precio", "stretch": False, 'width': 80, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Total", "stretch": False, 'width': 100, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Esp.", "stretch": False, 'width': 100, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Comments", "stretch": False, 'width': 100, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 1}
        ]

    def _rellenar_tabla_detalle(self):

        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_documentos'):
            return

        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_documentos')

        valores_fila = self._ventanas.procesar_fila_treeview('tvw_documentos', fila)
        document_id = valores_fila['DocumentID']

        consulta = self._base_de_datos.buscar_partidas_documento(document_id)
        partidas_prodcesadas = self._procesar_partidas(consulta)
        self._ventanas.rellenar_treeview('tvw_detalle',
                                         self._crear_columnas_tabla_detalle(),
                                         partidas_prodcesadas,
                                         variar_color_filas=True,
                                         valor_barra_desplazamiento=10)

    def _procesar_partidas(self, partidas):
        partidas = self._utilerias._agregar_impuestos_productos(partidas)
        partidas_procesadas = []

        for partida in partidas:

            cantidad = self._utilerias.redondear_valor_cantidad_a_decimal(partida['Quantity'])
            precio = self._utilerias.redondear_valor_cantidad_a_decimal(partida['SalePriceWithTaxes'])
            total = cantidad * precio
            total = f"{total:.2f}"
            comentario = self._base_de_datos.fetchone(
                "SELECT ISNULL(Comments, '') Comentario FROM docDocumentItem WHERE DocumentItemID = ?",(partida['DocumentItemID'])
            )
            nueva_partida = {
                'Quantity': cantidad,
                'ProductKey': partida['ProductKey'],
                'Unit': partida['Unit'],
                'ProductName': partida['Description'],
                'UnitPrice': precio,
                'Total': total,
                'Esp.': 'E' if comentario != '' else '',
                'Comments': comentario if comentario != '' else '',

            }
            partidas_procesadas.append(nueva_partida)

        return partidas_procesadas