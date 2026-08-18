import tkinter as tk
from cayal.ventanas import Ventanas

class DividirPartida:
    def __init__(self, master, utilerias, info_fila):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._utilerias = utilerias

        self._crear_frames()
        self._cargar_componentes()

        self._info_fila = info_fila
        self.fila_remision = {}
        self.fila_factura = {}
        self.dividir =  False

        self._rellenar_componentes()
        self._cargar_eventos()

        self._ventanas.configurar_ventana_ttkbootstrap()
        self._ventanas.enfocar_componente('tbx_cantidad_factura')

    def _cargar_eventos(self):
        eventos = {
            'btn_cancelar':self._master.destroy,
            'btn_dividir':self._dividir_partida,
            'tbx_cantidad_factura': lambda event: self._dividir_partida()
        }
        self._ventanas.cargar_eventos(eventos)

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.W}),

            'frame_componentes': ('frame_principal', 'Dividir documentos:',
                                  {'row': 1, 'column': 0,'padx': 5, 'pady': 5, 'sticky': tk.W}),

            'frame_chk': ('frame_componentes', None,
                              {'row': 6, 'column': 1, 'sticky': tk.W}),

            'frame_botones': ('frame_componentes', None,
                                  {'row': 7, 'column': 1,  'sticky': tk.NSEW}),

        }

        self._ventanas.crear_frames(frames)

    def _cargar_componentes(self):
        componentes = {
            'tbx_producto': ('frame_componentes', None, 'Producto:', None),
            'tbx_clave': ('frame_componentes', None, 'Clave:', None),
            'tbx_unidad': ('frame_componentes', None, 'Unidad:', None),
            'tbx_precio': ('frame_componentes', None, 'Precio:', None),
            'tbx_cantidad': ('frame_componentes', None, 'Cantidad:', None),
            'tbx_cantidad_factura': ('frame_componentes', None, 'Factura:', None),
            'chk_monto': ('frame_chk', None, 'Monto:', None),
            'btn_dividir': ('frame_botones', 'Info', 'Dividir', None),
            'btn_cancelar': ('frame_botones', 'Danger', 'Cancelar', None),

        }
        self._ventanas.crear_componentes(componentes)

    def _rellenar_componentes(self):

        componentes = {
            'tbx_producto': 'Producto',
            'tbx_clave': 'Clave',
            'tbx_unidad': 'ClaveUnidad',
            'tbx_cantidad': 'Cantidad',
            'tbx_precio': 'Precio'
        }
        for componente, clave in componentes.items():
            self._ventanas.insertar_input_componente(componente, self._info_fila.get(clave,''))
            self._ventanas.bloquear_componente(componente)

    def _dividir_partida(self):
        cantidades = self._validar_input_usuario()
        if not cantidades:
            return

        if self.dividir:
            return
        try:
            self.dividir = True
            cantidad_factura  = cantidades['cantidad_factura']
            cantidad_remision = cantidades['cantidad_remision']
            precio = cantidades['precio']

            self._procesar_filas(cantidad_factura, cantidad_remision, precio)
        finally:
            self._master.destroy()

    def _validar_input_usuario(self):
        funcion = self._utilerias.convertir_valor_a_decimal

        cantidad_factura = self._ventanas.obtener_input_componente('tbx_cantidad_factura')
        if not cantidad_factura or not self._utilerias.es_cantidad(cantidad_factura):
            self._ventanas.mostrar_mensaje('Debe ingresar un monto válido.')
            return

        cantidad_factura = funcion(cantidad_factura)
        if cantidad_factura <= 0:
            self._ventanas.mostrar_mensaje('Debe ingresar un monto válido.')
            return

        cantidad_original = funcion(self._ventanas.obtener_input_componente('tbx_cantidad'))
        monto = self._ventanas.obtener_input_componente('chk_monto')

        if cantidad_factura > cantidad_original and monto == 0:
            self._ventanas.mostrar_mensaje('La cantidad facturable no puede ser mayor a la cantidad original')
            return

        cantidad_remision = cantidad_original - cantidad_factura
        precio  = self._ventanas.obtener_input_componente('tbx_precio')
        precio_decimal = funcion(precio)
        return {
            'cantidad_factura': cantidad_factura,
            'cantidad_remision': cantidad_remision,
            'precio':precio_decimal
        }

    def _procesar_filas(self, cantidad_factura, cantidad_remision, precio):

        partida_factura = self._info_fila.copy()
        _partida_factura = self._normalizar_partida(partida_factura)

        por_monto = self._ventanas.obtener_input_componente('chk_monto')
        if por_monto == 1:
            cantidad_factura = cantidad_factura / precio
            cantidad_original = self._utilerias.convertir_valor_a_decimal(self._info_fila['Cantidad'])
            cantidad_remision = cantidad_original - cantidad_factura

        _partida_con_impuestos_factura = self._agregar_impuestos(_partida_factura, cantidad_factura)


        partida_remision = self._info_fila.copy()
        _partida_remision = self._normalizar_partida(partida_remision)
        _partida_con_impuestos_remision = self._agregar_impuestos(partida_remision, cantidad_remision)

        self.fila_factura = self._crear_fila_tabla(_partida_con_impuestos_factura)
        self.fila_remision = self._crear_fila_tabla(_partida_con_impuestos_remision)

    def _normalizar_partida(self, partida):

        partida['UnitPrice'] = partida['Precio']
        del partida['Precio']
        del partida['Cantidad']
        return partida

    def _agregar_impuestos(self, partida, cantidad):
        partida_con_impuesto = self._utilerias.crear_partida(partida, cantidad)
        return partida_con_impuesto

    def _crear_fila_tabla(self, info_fila):
        return {
            'Cantidad': f"{info_fila['cantidad']:.3f}",
            'ProductID': info_fila['ProductID'],
            'Clave': info_fila['Clave'],
            'Producto': info_fila['Producto'],
            'Precio': f"{info_fila['precio']:.2f}",
            'Subtotal': f"{info_fila['subtotal']:.2f}",
            'Total': f"{info_fila['total']:.2f}",
            'TaxTypeID': info_fila['TaxTypeID'],
            'ClaveProdServ': info_fila['clave_sat'],
            'ClaveUnidad': info_fila['clave_unidad'],
            'UUID': info_fila['UUID']
        }