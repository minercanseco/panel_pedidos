import tkinter as tk
from cayal.ventanas import Ventanas

class EditarPedido:
    def __init__(self, master, base_de_datos, utilerias, valores_fila):
        self._master = master
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._ventanas = Ventanas(self._master)

        self._valores_fila = valores_fila

        self._cargar_frames()
        self._cargar_componentes()

    def _cargar_frames(self):
        pass

    def _cargar_componentes(self):
        componentes = {
            'tvw_detalle': ('frame_tabla_detalle', self._crear_columnas_detalle(), 5, 'WARNING'),
        }
        self._ventanas.crear_componentes(componentes)

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