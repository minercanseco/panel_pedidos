import tkinter as tk
from cayal.ventanas import Ventanas

from agregar_partida_produccion import AgregarPartidaProduccion
from editar_partida_produccion import EditarPartidaProduccion


class EditarPedido:
    def __init__(self, master, base_de_datos, utilerias, valores_fila):
        self._master = master
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._ventanas = Ventanas(self._master)

        self._valores_fila = valores_fila

        self._business_entity_id = valores_fila['BusinessEntityID']
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
        valores_fila = self._ventanas.procesar_fila_treeview('tvw_detalle', fila)

        ventana = self._ventanas.crear_popup_ttkbootstrap(titulo='Editar partida')
        instancia = EditarPartidaProduccion(ventana, self._base_de_datos, self._utilerias, valores_fila)
        ventana.wait_window()

        if instancia.actualizar_cantidad:
            print(instancia.valores_partida)

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
        valores_fila = self._ventanas.procesar_fila_treeview('tvw_detalle', fila)
        document_item_id = int(valores_fila.get('DocumentItemID', 0))
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

    def _procesar_partidas(self, partidas_a_procesar, ):
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
                'Esp': partida['Esp'],
                'Comments': partida['Comments'],
                'UUID': partida.get('UUID', ''),
                'DocumentItemID': partida['DocumentItemID']
            }
            nuevas_partidas.append(nueva_partida)

        return nuevas_partidas

    def _guardar_cambios(self):
        pass

    def _calcular_total_pedido(self):
        filas = self._ventanas.obtener_filas_treeview('tvw_detalle')
        total_acumulado = 0

        for fila in filas:
            valores = self._ventanas.procesar_fila_treeview('tvw_detalle', fila)
            total = valores['Total']
            total_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(total)

            total_acumulado += total_decimal
        return total_acumulado

    def _actualizar_totales_documento(self, total):
        total_moneda = self._utilerias.convertir_decimal_a_moneda(total)
        self._ventanas.insertar_input_componente('lbl_total', total_moneda)

        numero_filas = self._ventanas.numero_filas_treeview('tvw_detalle')
        self._ventanas.insertar_input_componente('lbl_partidas', numero_filas)