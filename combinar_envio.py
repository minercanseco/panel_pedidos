import tkinter as tk
from cayal.ventanas import Ventanas

class CombinarEnvio:
    def __init__(self, master, base_de_datos, parametros):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._base_de_datos = base_de_datos
        self._parametros = parametros

        self._cargar_componentes()
        self._cargar_eventos()

        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Combinar direcciones')

    def _cargar_componentes(self):
        componente = [
            ('tvw_direccion', self._crear_columnas_tabla()),
            ('btn_combinar', 'Combinar')
        ]
        self._ventanas.crear_formulario_simple(componente)

    def _cargar_eventos(self):
        eventos = {
            'btn_cancelar': self._master.destroy,
            'btn_combinar':self._combinar_direcciones
        }
        self._ventanas.cargar_eventos(eventos)

    def _combinar_direcciones(self):
        print('combiunes')

    def _crear_columnas_tabla(self):
        return [
            {"text": "Sucursal", "stretch": False, 'width': 80, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Direccion", "stretch": False, 'width': 80, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Colonia", "stretch": False, 'width': 90, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Envío", "stretch": False, 'width': 90, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "AddressDetailID", "stretch": False, 'width': 90, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
        ]