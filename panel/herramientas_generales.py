import tkinter as tk
from cayal.ventanas import Ventanas

class HerramientasGenerales:
    def __init__(self, master):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._crear_frames()
        self._crear_barra_herramientas()

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'pady': 5, 'padx': 5, 'sticky': tk.NSEW}),

            'frame_componentes': ('frame_principal', None,
                                  {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                   'sticky': tk.NSEW})
        }
        self._ventanas.crear_frames(frames)

    def _crear_barra_herramientas(self):
        self.barra_herramientas_pedido = [

            {'nombre_icono': 'Partner32.ico', 'etiqueta': 'Clientes', 'nombre': 'buscar_cliente',
             'hotkey': None, 'comando': self._hola},

            {'nombre_icono': 'Customer32.ico', 'etiqueta': 'Nuevo', 'nombre': 'nuevo_cliente',
             'hotkey': None, 'comando': self._hola},

            {'nombre_icono': ' AssignSalesRep32.ico', 'etiqueta': 'E.Nombre', 'nombre': 'editar_nombre',
             'hotkey': None, 'comando': self._hola},

            {'nombre_icono': 'History21.ico', 'etiqueta': 'Historial', 'nombre': 'historial_pedido',
             'hotkey': None, 'comando': self._hola},

            {'nombre_icono': 'Cancelled32.ico', 'etiqueta': 'Cancelar', 'nombre': 'cancelar_pedido',
             'hotkey': None, 'comando': self._hola},

            {'nombre_icono': 'Organizer32.ico', 'etiqueta': 'A.Horarios', 'nombre': 'acumular_horarios',
             'hotkey': None, 'comando': self._hola},

            {'nombre_icono': 'Printer21.ico', 'etiqueta': 'Imprimir', 'nombre': 'imprimir_pedido',
             'hotkey': None, 'comando': self._hola},

            {'nombre_icono': 'Payments32.ico', 'etiqueta': 'C.Cartera.', 'nombre': 'cobrar_cartera',
             'hotkey': None, 'comando': self._hola},

            {'nombre_icono': 'OtrosIngresos32.ico', 'etiqueta': 'C.Transferencia', 'nombre': 'confirmar_transferencia',
             'hotkey': None, 'comando': self._hola},

            {'nombre_icono': 'SwitchUser32.ico', 'etiqueta': 'C.Usuario', 'nombre': 'cambiar_usuario',
             'hotkey': None, 'comando': self._hola},

        ]

        self.elementos_barra_herramientas = self._ventanas.crear_barra_herramientas(self.barra_herramientas_pedido,
                                                                                   'frame_componentes')
        self.iconos_barra_herramientas = self.elementos_barra_herramientas[0]
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]

    def _hola(self):
        print('hola')
