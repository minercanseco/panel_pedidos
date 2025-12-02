import tkinter as tk
from cayal.ventanas import Ventanas

from editar_cobro import EditarCobros
from registro_vouchers import RegistroVouchers

class PanelPrincipal:
    def __init__(self, master, base_de_datos, utilerias, parametros):
        self._master = master
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._parametros = parametros
        self._ventanas = Ventanas(self._master)

        self._crear_frames()
        self._crear_barra_herramientas()
        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Herramientas')

    def _crear_frames(self):
        frames = {
        'frame_principal': ('master', None,
                            {'row': 0, 'column': 0, 'sticky': tk.NSEW}),
        'frame_herramientas': ('frame_principal', 'Opciones',
                               {'row': 0, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW})
        }
        self._ventanas.crear_frames(info_frames=frames)

    def _crear_barra_herramientas(self):
        self.barra_herramientas = [
            {'nombre_icono': 'terminal_bancaria.ico', 'etiqueta': 'Vouchers', 'nombre': 'registrar_vouchers',
             'hotkey': '[V]', 'comando': self._registrar_vouchers},
            {'nombre_icono': 'Editar21.ico', 'etiqueta': 'Editar', 'nombre': 'editar_cobro',
             'hotkey': '[E]', 'comando': self._editar_cobro},
            {'nombre_icono': 'Eliminar21.ico', 'etiqueta': 'Cancelar', 'nombre': 'cancelar',
             'hotkey': '[Esc]', 'comando': self._cancelar}

        ]

        self.elementos_barra_herramientas = self._ventanas.crear_barra_herramientas(
            self.barra_herramientas,
            'frame_herramientas')
        self.iconos_barra_herramientas = self.elementos_barra_herramientas[0]
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]

    def _registrar_vouchers(self):
        ventana = self._ventanas.crear_popup_ttkbootstrap(ocultar_master=True)
        instancia = RegistroVouchers(ventana, self._base_de_datos, self._utilerias, self._parametros)
        ventana.wait_window()

        self._master.destroy()

    def _editar_cobro(self):
        ventana = self._ventanas.crear_popup_ttkbootstrap(ocultar_master=True)
        instancia = EditarCobros(ventana, self._base_de_datos, self._utilerias, self._parametros)
        ventana.wait_window()

        self._master.destroy()

    def _cancelar(self):
        self._master.destroy()