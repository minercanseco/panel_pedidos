import tkinter as tk
from cayal.ventanas import Ventanas

class HerramientasCaptura:
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


            {'nombre_icono': 'HeaderFooter32.ico', 'etiqueta': 'Nuevo', 'nombre': 'capturar_nuevo',
             'hotkey': None, 'comando': self._hola},

            {'nombre_icono': 'EditBusinessEntity32.ico', 'etiqueta': 'E.Caracteristicas', 'nombre': 'editar_caracteristicas',
             'hotkey': '', 'comando': self._hola},

            {'nombre_icono': 'DocumentGenerator32.ico', 'etiqueta': 'Ticket', 'nombre': 'crear_ticket',
             'hotkey': None, 'comando': self._hola},

            {'nombre_icono': 'Manufacture32.ico', 'etiqueta': 'M.Producir', 'nombre': 'mandar_producir',
             'hotkey': None, 'comando': self._hola},

            {'nombre_icono': 'lista-de-verificacion.ico', 'etiqueta': 'Editar', 'nombre': 'editar',
             'hotkey': None, 'comando': self._hola},

        ]

        self.elementos_barra_herramientas = self._ventanas.crear_barra_herramientas(self.barra_herramientas_pedido,
                                                                                   'frame_componentes')
        self.iconos_barra_herramientas = self.elementos_barra_herramientas[0]
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]

    def _hola(self):
        print('hola')
