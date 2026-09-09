import tkinter as tk
from datetime import date

from cayal.ventanas import Ventanas


class NoSurtidos:
    def __init__(self, master, modelo):
        self._master = master
        self._modelo = modelo
        self._ventanas = Ventanas(master)
        self._columnas = self._crear_columnas()

        self._crear_frames()
        self._crear_componentes()
        self._crear_tableview()
        self._cargar_eventos()
        self._establecer_fechas_iniciales()
        self._ventanas.configurar_ventana_ttkbootstrap(
            titulo='Productos no surtidos',
            nombre_icono='StockOut32.ico',
        )
        self._consultar()

    @staticmethod
    def _crear_columnas():
        return [
            {'text': 'Fecha', 'stretch': False, 'width': 90},
            {'text': 'Cliente', 'stretch': False, 'width': 210},
            {'text': 'Dirección', 'stretch': False, 'width': 170},
            {'text': 'Folio', 'stretch': False, 'width': 85},
            {'text': 'Cantidad', 'stretch': False, 'width': 75},
            {'text': 'Producto', 'stretch': False, 'width': 220},
            {'text': 'Veces no surtido', 'stretch': False, 'width': 110},
            {'text': 'Borrado por', 'stretch': False, 'width': 110},
            {'text': 'Motivo', 'stretch': False, 'width': 140},
            {'text': 'Línea', 'stretch': False, 'width': 130},
        ]

    def _crear_frames(self):
        self._ventanas.crear_frames({
            'frame_principal': (
                'master', None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW},
            ),
            'frame_filtros': (
                'frame_principal', 'Periodo de consulta',
                {'row': 0, 'column': 0, 'sticky': tk.EW, 'padx': 8, 'pady': (8, 4)},
            ),
            'frame_tabla': (
                'frame_principal', 'Productos no surtidos',
                {'row': 1, 'column': 0, 'sticky': tk.NSEW, 'padx': 8, 'pady': 4},
            ),
            'frame_estado': (
                'frame_principal', None,
                {'row': 2, 'column': 0, 'sticky': tk.EW, 'padx': 8},
            ),
            'frame_botones': (
                'frame_principal', None,
                {'row': 3, 'column': 0, 'sticky': tk.E, 'padx': 8, 'pady': (4, 8)},
            ),
        })

    def _crear_componentes(self):
        self._ventanas.crear_componentes({
            'den_fecha_inicial': (
                'frame_filtros',
                {'row': 0, 'column': 1, 'sticky': tk.W, 'padx': 5, 'pady': 5},
                'Desde:', None,
            ),
            'den_fecha_final': (
                'frame_filtros',
                {'row': 0, 'column': 3, 'sticky': tk.W, 'padx': 5, 'pady': 5},
                'Hasta:', None,
            ),
            'btn_consultar': (
                'frame_filtros', 'primary', 'Consultar', None,
            ),
            'lbl_estado': (
                'frame_estado', {'text': '0 productos no surtidos', 'anchor': tk.W},
                {'row': 0, 'column': 0, 'sticky': tk.EW}, None,
            ),
            'btn_cerrar': (
                'frame_botones', 'danger', 'Cerrar', None,
            ),
        })

    def _crear_tableview(self):
        self._ventanas.crear_table_view(
            nombre='tbv_no_surtidos',
            frame='frame_tabla',
            columnas=self._columnas,
            filas=20,
            stripecolor=True,
        )
        self._ventanas.habilitar_ordenamiento_table_view('tbv_no_surtidos')

    def _cargar_eventos(self):
        self._ventanas.cargar_eventos({
            'den_fecha_inicial': self._consultar,
            'den_fecha_final': self._consultar,
            'btn_consultar': self._consultar,
            'btn_cerrar': self._master.destroy,
        })

    def _establecer_fechas_iniciales(self):
        hoy = date.today().strftime('%Y-%m-%d')
        self._ventanas.insertar_input_componente('den_fecha_inicial', hoy)
        self._ventanas.insertar_input_componente('den_fecha_final', hoy)

    def _obtener_periodo(self):
        fecha_inicial = self._ventanas.obtener_input_componente(
            'den_fecha_inicial'
        )
        fecha_final = self._ventanas.obtener_input_componente(
            'den_fecha_final'
        ) or fecha_inicial
        if fecha_inicial > fecha_final:
            raise ValueError(
                'La fecha inicial no puede ser posterior a la fecha final.'
            )
        return fecha_inicial, fecha_final

    def _consultar(self, event=None):
        try:
            fecha_inicial, fecha_final = self._obtener_periodo()
            resultados = self._modelo.buscar_productos_no_surtidos(
                fecha_inicial,
                fecha_final,
            )
            self._ventanas.rellenar_table_view(
                'tbv_no_surtidos',
                self._columnas,
                resultados,
            )
            cantidad = len(resultados)
            texto = 'registro' if cantidad == 1 else 'registros'
            self._ventanas.insertar_input_componente(
                'lbl_estado',
                f'{cantidad} {texto} de productos no surtidos',
            )
        except Exception as error:
            self._ventanas.mostrar_mensaje(
                f'No fue posible consultar los productos no surtidos:\n{error}'
            )

