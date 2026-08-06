import tkinter as tk
from cayal.ventanas import Ventanas


class InterfazSelectorModulo:
    def __init__(self, master):
        self._master = master
        self.ventanas = Ventanas(self._master)


        self._crear_frames()
        self._cargar_componentes()
        self._crear_barra_herramientas()
        self.ventanas.configurar_ventana_ttkbootstrap('Ventas')

    def _crear_frames(self):
        frames = {
            'frame_principal': (
                'master',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW}
            ),

            'frame_herramientas': (
                'frame_principal',
                'Herramientas',
                {'row': 0, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}
            ),

            'frame_notebook': (
                'frame_principal',
                'Ventas',
                {'row': 1, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}
            ),
        }

        self.ventanas.crear_frames(frames)

        frame_principal = self.ventanas.componentes_forma['frame_principal']
        frame_principal.rowconfigure(1, weight=1)
        frame_principal.columnconfigure(0, weight=1)

        frame_notebook = self.ventanas.componentes_forma['frame_notebook']
        frame_notebook.rowconfigure(0, weight=1)
        frame_notebook.columnconfigure(0, weight=1)

    def _cargar_componentes(self):
        info_pestanas = {
            'tab_tickets': ('Tickets 🧾', None),
            'tab_facturas': ('Facturas 📄', None),
            'tab_depositos': ('Depositos 📄', None),
        }

        self.nombre_notebook = 'nbk_ventas'

        self.notebook = self.ventanas.crear_notebook(
            nombre_notebook=self.nombre_notebook,
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

        frames_tabs = {
            'frm_tickets': (
                'tab_tickets',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            ),

            'frm_facturas': (
                'tab_facturas',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            ),

            'frm_depositos': (
                'tab_depositos',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            ),
        }

        self.ventanas.crear_frames(frames_tabs)

        frame_tickets = self.ventanas.componentes_forma['frm_tickets']
        frame_facturas = self.ventanas.componentes_forma['frm_facturas']
        frame_depositos = self.ventanas.componentes_forma['frm_depositos']

        frame_tickets.rowconfigure(0, weight=1)
        frame_tickets.columnconfigure(0, weight=1)

        frame_facturas.rowconfigure(0, weight=1)
        frame_facturas.columnconfigure(0, weight=1)

        frame_depositos.rowconfigure(0, weight=1)
        frame_depositos.columnconfigure(0, weight=1)

        self.ventanas.crear_table_view(
            nombre='tbv_tickets',
            frame='frm_tickets',
            columnas=[],
            filas=35,
            stripecolor=True
        )

        self.ventanas.crear_table_view(
            nombre='tbv_facturas',
            frame='frm_facturas',
            columnas=[],
            filas=35,
            stripecolor=True
        )

        self.ventanas.crear_table_view(
            nombre='tbv_depositos',
            frame='frm_depositos',
            columnas=[],
            filas=35,
            stripecolor=True
        )

    def _crear_barra_herramientas(self):

        self.barra_herramientas = [
            {
                'nombre_icono': 'HeaderFooter32.ico',
                'etiqueta': 'Ticket',
                'nombre': 'nuevo_ticket',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'Invoice32.ico',
                'etiqueta': 'Factura',
                'nombre': 'nueva_factura',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'Ingreso.ico',
                'etiqueta': 'Depósito',
                'nombre': 'nuevo_deposito',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'Payments32.ico',
                'etiqueta': 'Cartera',
                'nombre': 'cobrar_cartera',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'Refresh32.ico',
                'etiqueta': 'Actualizar',
                'nombre': 'actualizar',
                'hotkey': '',
                'comando': None
            },

            {
                'nombre_icono': 'Print32.ico',
                'etiqueta': 'Imprimir',
                'nombre': 'imprimir',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'FormOfPayment32.ico',
                'etiqueta': 'Cobro Rápido',
                'nombre': 'cobro_rapido',
                'hotkey': '',
                'comando': None
            },

            {
                'nombre_icono': 'Barcode32.ico',
                'etiqueta': 'Verificador',
                'nombre': 'verificador',
                'hotkey': '',
                'comando': None
            }
        ]


    def obtener_tab_activa(self) -> dict:
        notebook = self.notebook

        tab_id = notebook.select()
        tab_texto = notebook.tab(tab_id, 'text')

        mapa_tabs = {
            'tab_tickets': {
                'frame': 'frm_tickets',
                'tabla': 'tbv_tickets',
                'texto': 'Tickets 🧾'
            },
            'tab_facturas': {
                'frame': 'frm_facturas',
                'tabla': 'tbv_facturas',
                'texto': 'Facturas 📄'
            },
            'tab_depositos': {
                'frame': 'frm_depositos',
                'tabla': 'tbv_depositos',
                'texto': 'Depositos 📄'
            },
        }

        for nombre_tab, datos in mapa_tabs.items():
            frame_tab = self.ventanas.componentes_forma.get(nombre_tab)

            if str(frame_tab) == tab_id:
                return {
                    'tab': nombre_tab,
                    'frame': datos['frame'],
                    'tabla': datos['tabla'],
                    'texto': datos['texto']
                }

        return {
            'tab': None,
            'frame': None,
            'tabla': None,
            'texto': tab_texto
        }

    def obtener_tabla_activa(self):
        tab_activa = self.obtener_tab_activa()
        nombre_tabla = tab_activa['tabla']

        if not nombre_tabla:
            return None

        return nombre_tabla

    def obtener_frame_activo(self):
        tab_activa = self.obtener_tab_activa()
        nombre_frame = tab_activa['frame']

        if not nombre_frame:
            return None

        return nombre_frame