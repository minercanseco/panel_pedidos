import tkinter as tk
import uuid

from cayal.ventanas import Ventanas
from .dividir_partida import DividirPartida


class FacturarYRemisionar:
    def __init__(self, master, parametros, base_de_datos, utilerias):
        self._master = master
        self._parametros = parametros
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._ventanas = Ventanas(self._master)

        self.document_id = self._parametros.id_principal
        self.user_id = self._parametros.id_usuario
        self.module_id = self._parametros.id_modulo
        self.dividir_documento = False

        self._partidas_factura_backup = []
        self.partidas_factura = []
        self.partidas_remision = []

        self._crear_frames()
        self._cargar_componentes()
        self._rellenar_componentes()
        self._cargar_eventos()
        self._ventanas.configurar_ventana_ttkbootstrap()

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_componentes': ('frame_principal', 'Facturar y Remisionar:',
                                  {'row': 0, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            # -------------------------
            # FACTURA (contenedor)
            # -------------------------
            'frame_factura': ('frame_componentes', 'Factura:',
                              {'row': 0, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_factura_total': ('frame_factura', None,
                                    {'row': 0, 'column': 0, 'padx': 0, 'pady': 0, 'sticky': tk.EW}),

            'frame_factura_tabla': ('frame_factura', None,
                                    {'row': 1, 'column': 0, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW}),

            # -------------------------
            # REMISIÓN (contenedor)
            # -------------------------
            'frame_remision': ('frame_componentes', 'Remisión:',
                               {'row': 0, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_remision_total': ('frame_remision', None,
                                     {'row': 0, 'column': 0, 'padx': 0, 'pady': 0, 'sticky': tk.EW}),

            'frame_remision_tabla': ('frame_remision', None,
                                     {'row': 1, 'column': 0, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW}),

            # -------------------------
            # BOTONES
            # -------------------------
            'frame_botones': ('frame_componentes', None,
                              {'row': 1, 'column': 0, 'columnspan': 2, 'sticky': tk.EW}),
        }

        self._ventanas.crear_frames(frames)

    def _cargar_componentes(self):
        componentes_iniciales = {
            'tvw_factura': ('frame_factura_tabla', self._columnas(), 10, 'Danger'),
            'tvw_remision': ('frame_remision_tabla', self._columnas(), 10, None),
            'btn_dividir': ('frame_botones', None, 'Dividir', None),
            'btn_cancelar': ('frame_botones', 'Danger', 'Cancelar', None),
        }
        self._ventanas.crear_componentes(componentes_iniciales)

        estilo_bg = {'background': '#E30421'}

        estilo_total = {
            'foreground': 'white',
            **estilo_bg,
            'font': ('Consolas', 14, 'bold'),
            'text': '$0.00',
            'anchor': 'center',
        }

        pos = lambda r, c, cs=1: {
            'row': r, 'column': c, 'columnspan': cs,
            'sticky': tk.NSEW, 'padx': 0, 'pady': 0
        }

        componentes_totales = {
            # Totales Factura
            'lbl_total_factura': (
                'frame_factura_total',
                {**estilo_total, 'text': '🧾  $0.00'},
                pos(0, 0, cs=4),
                None
            ),

            # Totales Remisión (va en su frame_total2)
            'lbl_total_remision': (
                'frame_remision_total',
                {**estilo_total, 'text': '📄  $0.00'},
                pos(0, 0, cs=4),
                None
            ),
        }
        self._ventanas.crear_componentes(componentes_totales)

    def _columnas(self):
        return [
            {"text": "Cantidad", "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.W,
             'hide': 0},
            {"text": "ProductID", "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.W,
             'hide': 1},
            {"text": "Clave", "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.W,
             'hide': 0},
            {"text": "Producto", "stretch": False, 'width': 163, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {"text": "Precio", "stretch": False, 'width': 55, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {"text": "Subtotal", "stretch": False, 'width': 90, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {"text": "Total", "stretch": False, 'width': 90, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {"text": "TaxTypeID", "stretch": False, 'width': 55, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {"text": "ClaveProdServ", "stretch": False, 'width': 55, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {"text": "ClaveUnidad", "stretch": False, 'width': 55, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {"text": "UUID", "stretch": False, 'width': 55, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1}
        ]

    def _rellenar_componentes(self):
        total_acumulado, partidas = self._buscar_partidas(self.document_id)
        self._partidas_factura = partidas
        self._partidas_factura_backup = partidas.copy()

        self._ventanas.rellenar_treeview('tvw_factura', self._columnas(), partidas, valor_barra_desplazamiento=5)
        self._actualizar_total('tvw_factura')

    def _cargar_eventos(self):
        eventos = {
            'btn_cancelar':self._master.destroy,
            'tvw_factura': (lambda event:self._dividir_partida('tvw_factura'), 'doble_click'),
            'tvw_remision': (lambda event: self._dividir_partida('tvw_remision'), 'doble_click'),
            'btn_dividir':self._dividir_documento
        }
        self._ventanas.cargar_eventos(eventos)

        eventos_tablas = {
            'tvw_factura': (lambda event: self._eliminar_fila('tvw_factura'), 'suprimir'),
            'tvw_remision': (lambda event: self._eliminar_fila('tvw_remision'), 'suprimir'),
        }
        self._ventanas.cargar_eventos(eventos_tablas)

    def _dividir_partida(self, tabla):

        if not self._ventanas.validar_seleccion_una_fila_treeview(tabla):
            return

        filas = self._ventanas.obtener_seleccion_filas_treeview(tabla)

        for fila in filas:
            valores = self._ventanas.procesar_fila_treeview(tabla, fila)

            valores_originales = [reg for reg in self._partidas_factura_backup if reg['UUID'] == valores['UUID']][0]
            valores['Cantidad'] = valores_originales['Quantity']
            valores['Subtotal'] = valores_originales['Subtotal']
            valores['Total'] = valores_originales['Total']


            ventana = self._ventanas.crear_popup_ttkbootstrap('Dividir partida')
            instancia = DividirPartida(ventana, self._utilerias, valores)
            ventana.wait_window()

            if instancia.dividir:
                self._reemplazar_fila_tabla('tvw_factura', instancia.fila_factura)
                self._actualizar_total('tvw_factura')

                self._reemplazar_fila_tabla('tvw_remision', instancia.fila_remision)
                self._actualizar_total('tvw_remision')

    def _reemplazar_fila_tabla(self, tabla, valores_fila):
        uuid_fila = valores_fila['UUID']

        filas = self._ventanas.obtener_filas_treeview(tabla)
        fila_a_reemplazar = None
        for fila in filas:
            valores = self._ventanas.procesar_fila_treeview(tabla, fila)
            if valores['UUID'] == uuid_fila:
                fila_a_reemplazar = fila

        if fila_a_reemplazar:
            self._ventanas.actualizar_fila_treeview_diccionario(tabla, fila_a_reemplazar, valores_fila)
        else:
            parametros = (
                valores_fila['Cantidad'],
                valores_fila['ProductID'],
                valores_fila['Clave'],
                valores_fila['Producto'],
                valores_fila['Precio'],
                valores_fila['Subtotal'],
                valores_fila['Total'],
                valores_fila['TaxTypeID'],
                valores_fila['ClaveProdServ'],
                valores_fila['ClaveUnidad'],
                valores_fila['UUID'],
            )
            self._ventanas.insertar_fila_treeview(tabla, parametros, al_principio=True)

    def _actualizar_total(self, tabla):
        filas = self._ventanas.obtener_filas_treeview(tabla)
        if not filas:
            return

        total_acumulado = 0
        for fila in filas:
            valores = self._ventanas.procesar_fila_treeview(tabla, fila)
            total = self._utilerias.convertir_valor_a_decimal(valores['Total'])
            total_acumulado += total

        total_acumulado = f"{total_acumulado:.2f}"
        texto = f"'📄  ${total_acumulado}"

        if tabla == 'tvw_factura':
            self._ventanas.insertar_input_componente('lbl_total_factura', texto)
        else:
            self._ventanas.insertar_input_componente('lbl_total_remision', texto)

    def _buscar_partidas(self, document_id):
        partidas = self._base_de_datos.buscar_partidas_documento(documento=document_id)

        partidas_con_impuestos = []
        for partida in partidas:
            partidas_con_impuestos.append(self._utilerias.crear_partida(partida))

        total_acumulado = 0
        nuevas_partidas = []
        for partida in partidas_con_impuestos:
            nuevas_partidas.append(
                {
                    'Quantity':f"{partida['cantidad']:.2f}",
                    'ProductID': partida['ProductID'],
                    'ProductKey':partida['ProductKey'],
                    'ProductName':partida['ProductName'],
                    'UnitPrice':f"{partida['precio']:.2f}",
                    'Subtotal': f"{partida['subtotal']:.2f}",
                    'Total':f"{partida['total']:.2f}",
                    'TaxTypeID':partida['TaxTypeID'],
                    'ClaveProdServ':partida['ClaveProdServ'],
                    'ClaveUnidad':partida['ClaveUnidad'],
                    'UUID': str(uuid.uuid4())
                }
            )
        return total_acumulado, nuevas_partidas

    def _eliminar_fila(self, tabla):
        if not self._ventanas.validar_seleccion_una_fila_treeview(tabla):
            return

        filas = self._ventanas.obtener_seleccion_filas_treeview(tabla)
        if len(filas)!=1:
            return

        tabla_espejo =  'tvw_factura' if tabla == 'tvw_remision' else 'tvw_remision'
        for fila in filas:
            valores = self._ventanas.procesar_fila_treeview(tabla, fila)
            valores_originales = [reg for reg in self._partidas_factura_backup if reg['UUID'] == valores['UUID']][0]
            valores_originales = self._crear_fila_tabla(valores_originales)
            self._reemplazar_fila_tabla(tabla_espejo, valores_originales)
            self._ventanas.remover_fila_treeview(tabla, fila)

        self._actualizar_total(tabla)
        self._actualizar_total(tabla_espejo)

    def _crear_fila_tabla(self, info_fila):

        return {
            'Cantidad': f"{info_fila['Quantity']}",
            'ProductID': f"{info_fila['ProductID']}",
            'Clave': info_fila['ProductKey'],
            'Producto': info_fila['ProductName'],
            'Precio': f"{info_fila['UnitPrice']}",
            'Subtotal': f"{info_fila['Subtotal']}",
            'Total': f"{info_fila['Total']}",
            'TaxTypeID': info_fila['TaxTypeID'],
            'ClaveProdServ': info_fila['ClaveProdServ'],
            'ClaveUnidad': info_fila['ClaveUnidad'],
            'UUID': info_fila['UUID']
        }

    def _dividir_documento(self):
        if self.dividir_documento:
            return

        try:
            self.dividir_documento = True
            self._crear_partidas_tabla('tvw_factura')
            self._crear_partidas_tabla('tvw_remision')
        finally:
            self._master.destroy()

    def _crear_partidas_tabla(self, tabla):
        filas = self._ventanas.obtener_filas_treeview(tabla)
        if not filas:
            return

        for fila in filas:
            valores = self._ventanas.procesar_fila_treeview(tabla, fila)
            valores['Quantity'] = valores['Cantidad']
            valores['UnitPrice'] = valores['Precio']
            valores.pop('Cantidad')
            valores.pop('Precio')

            if tabla == 'tvw_factura':
                self.partidas_factura.append(valores)
            else:
                self.partidas_remision.append(valores)
