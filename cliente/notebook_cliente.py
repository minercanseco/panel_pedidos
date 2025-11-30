import tkinter as tk
from cayal.ventanas import Ventanas
from cliente.formulario_cliente_interfaz import FormularioClienteInterfaz
from cliente.formulario_cliente_modelo import FormularioClienteModelo
from cliente.formulario_cliente_controlador import FormularioClienteControlador


class NoteBookCliente:
    def __init__(self, master, base_de_datos, parametros, utilerias):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._base_de_datos = base_de_datos
        self._parametros = parametros
        self._utilerias = utilerias

        # Cargar todo al crear el objeto
        self._crear_frames()
        self._cargar_componentes()
        self._ventanas.configurar_ventana_ttkbootstrap()

    def _crear_frames(self):
        frames = {
            'frame_principal': (
                'master',
                'Direcciones:',
                {'row': 0, 'column': 0, 'sticky': tk.NSEW}
            ),

            'frame_notebook': (
                'frame_principal',
                None,
                {'row': 1, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}
            ),
        }
        self._ventanas.crear_frames(frames)

        frame_principal = self._ventanas.componentes_forma['frame_principal']
        frame_principal.rowconfigure(1, weight=1)
        frame_principal.columnconfigure(0, weight=1)

    def _cargar_componentes(self):
        # 1) Definir pestañas del notebook
        info_pestanas = {
            # Texto de la pestaña con emoji de dirección fiscal
            'tab_direccion_fiscal': ('Dirección fiscal 🧾📍', None),
        }

        # 2) Crear notebook dentro de frame_notebook
        self._ventanas.crear_notebook(
            nombre_notebook='nb_formulario_cliente',
            info_pestanas=info_pestanas,
            nombre_frame_padre='frame_notebook',
            config_notebook={
                'row': 0,
                'column': 0,
                'sticky': tk.NSEW,
                'padx': 5,
                'pady': 5,
                'bootstyle': 'primary',
            }
        )

        # 3) Crear frames internos por cada pestaña
        frames_tabs = {
            'frm_direccion_fiscal': (
                'tab_direccion_fiscal',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            )
        }

        self._ventanas.crear_frames(frames_tabs)

        # ============================================================
        # 4) MONTAR CADA MÓDULO EN SU CORRESPONDIENTE PESTAÑA
        # ============================================================

        # ========== DIRECCIÓN FISCAL ==========
        frame_direccion_fiscal = self._ventanas.componentes_forma['frm_direccion_fiscal']
        self._interfaz = FormularioClienteInterfaz(frame_direccion_fiscal)
        self._modelo = FormularioClienteModelo(self._base_de_datos, self._parametros, self._utilerias)
        self._controlador = FormularioClienteControlador(
            self._interfaz,
            self._modelo
        )