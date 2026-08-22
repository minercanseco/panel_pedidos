import tkinter as tk
from tkinter import ttk
from cayal.ventanas import Ventanas


class Interfaz:
    def __init__(self, master):
        self._master = master
        self.ventanas = Ventanas(self._master)

        self._contador_quejas = 0
        self._quejas = {}

        self._crear_frames()
        self._crear_notebook()
        self._crear_barra_herramientas()
        self._agregar_queja()

        self.ventanas.configurar_ventana_ttkbootstrap('Agregar queja')


    def _crear_frames(self):
        self._frames = {
            'frame_principal': (
                'master',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW}
            ),

            'frame_toolbar': (
                'frame_principal',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.EW, 'padx': 5, 'pady': (5, 0)}
            ),

            'frame_general': (
                'frame_principal',
                None,
                {'row': 1, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            ),
        }

        self.ventanas.crear_frames(self._frames)

    def _crear_notebook(self):
        self.notebook = ttk.Notebook(
            self.ventanas.componentes_forma.get('frame_general')
        )

        self.notebook.grid(
            row=0,
            column=0,
            sticky=tk.NSEW
        )

    def _crear_barra_herramientas(self):
        self.barra_herramientas = [
            {
                'nombre_icono': 'Agregar21.ico',
                'etiqueta': 'Agregar',
                'nombre': 'agregar_queja',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'Functionality32.ico',
                'etiqueta': 'Guardar',
                'nombre': 'guardar',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'Cancelled32.ico',
                'etiqueta': 'Eliminar',
                'nombre': 'eliminar',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'Editar21.ico',
                'etiqueta': 'Modificaciones',
                'nombre': 'modificaciones',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'History21.ico',
                'etiqueta': 'Historial',
                'nombre': 'historial',
                'hotkey': '',
                'comando': None
            }
        ]

        self.ventanas.crear_barra_herramientas(
            self.barra_herramientas,
            'frame_toolbar'
        )

    def _agregar_queja(self):
        self._contador_quejas += 1

        indice = self._contador_quejas
        nombre_tab = f'Queja {indice}'

        frame_tab = ttk.Frame(self.notebook)

        self.notebook.add(frame_tab, text=nombre_tab)
        self.notebook.select(frame_tab)

        frames = self._crear_frames_queja(frame_tab, indice)
        componentes = self._crear_componentes_queja(indice)

        self.ventanas.crear_componentes(componentes)
        self._ajustar_ancho_componentes(indice)
        self._ajustar_alto_componentes(indice)

        self._quejas[indice] = {
            'frame_tab': frame_tab,
            'frames': frames,
            'componentes': list(componentes.keys()),
            'queja_id': None,
            'document_id': None,
            'eliminado': 0
        }

    def _ajustar_alto_componentes(self, indice):
        componentes = [
            f'txt_comentario_{indice}',
            f'txt_seguimiento_{indice}',
        ]

        for componente in componentes:
            self.ventanas.ajustar_alto_componente(componente, 5)

    def _ajustar_ancho_componentes(self, indice):
        combos = [
            f'cbx_tipo_{indice}',
            f'cbx_producto_{indice}',
            f'cbx_area_{indice}',
            f'cbx_sub_area_{indice}',
            f'cbx_responsable_{indice}',
        ]

        for combo in combos:
            self.ventanas.ajustar_ancho_componente(combo, 50)

    def _crear_frames_queja(self, frame_tab, indice):
        nombres = {
            'contenedor': f'frame_queja_{indice}_contenedor',
            'queja': f'frame_queja_{indice}',
            'seguimiento': f'frame_seguimiento_{indice}',
            'responsable': f'frame_responsable_{indice}',
            'salio': f'frame_salio_{indice}',
        }

        self.ventanas.componentes_forma[nombres['contenedor']] = frame_tab

        frames = {
            nombres['queja']: (
                nombres['contenedor'],
                None,
                {
                    'row': 0,
                    'column': 0,
                    'columnspan': 2,
                    'sticky': tk.NSEW,
                    'padx': 5,
                    'pady': 5
                }
            ),

            nombres['seguimiento']: (
                nombres['contenedor'],
                None,
                {
                    'row': 1,
                    'column': 0,
                    'columnspan': 2,
                    'sticky': tk.NSEW,
                    'padx': 5,
                    'pady': 5
                }
            ),

            nombres['responsable']: (
                nombres['contenedor'],
                None,
                {
                    'row': 2,
                    'column': 0,
                    'sticky': tk.NSEW,
                    'padx': 5,
                    'pady': 5
                }
            ),

            nombres['salio']: (
                nombres['contenedor'],
                None,
                {
                    'row': 3,
                    'column': 0,
                    'sticky': tk.NW,
                    'padx': (100, 5),
                    'pady': 5
                }
            ),
        }

        self.ventanas.crear_frames(frames)

        return nombres

    def _crear_componentes_queja(self, indice):
        return {
            f'cbx_tipo_{indice}': (
                f'frame_queja_{indice}',
                None,
                'Tipo:',
                None
            ),

            f'cbx_producto_{indice}': (
                f'frame_queja_{indice}',
                None,
                'Producto:',
                None
            ),

            f'txt_comentario_{indice}': (
                f'frame_queja_{indice}',
                None,
                'Comentario:',
                None
            ),

            f'cbx_area_{indice}': (
                f'frame_seguimiento_{indice}',
                None,
                'Área:',
                None
            ),

            f'cbx_sub_area_{indice}': (
                f'frame_seguimiento_{indice}',
                None,
                'Sub área:',
                None
            ),

            f'txt_seguimiento_{indice}': (
                f'frame_seguimiento_{indice}',
                None,
                'Seguimiento:',
                None
            ),

            f'cbx_responsable_{indice}': (
                f'frame_responsable_{indice}',
                None,
                'Responsable:',
                None
            ),

            f'tbx_capturo_{indice}': (
                f'frame_responsable_{indice}',
                None,
                'Capturó:',
                None
            ),

            f'chk_salio_{indice}': (
                f'frame_salio_{indice}',
                None,
                'Salió:',
                None
            ),
        }

    def _obtener_indice_queja_actual(self):
        tab_actual = self.notebook.select()

        for indice, datos in self._quejas.items():
            if str(datos['frame_tab']) == tab_actual:
                return indice

        return None

    def _eliminar_queja_actual(self):
        indice = self._obtener_indice_queja_actual()

        if indice is None:
            return

        datos = self._quejas.get(indice)

        if not datos:
            return

        datos['eliminado'] = 1

        self.notebook.forget(datos['frame_tab'])

    def obtener_datos_quejas(self):
        quejas = []

        for indice, datos in self._quejas.items():
            if datos.get('eliminado') == 1:
                continue

            quejas.append({
                'QuejaID': datos.get('queja_id'),
                'DocumentID': datos.get('document_id'),
                'Tipo': self._valor(f'cbx_tipo_{indice}'),
                'Producto': self._valor(f'cbx_producto_{indice}'),
                'Comentario': self._valor(f'txt_comentario_{indice}'),
                'Area': self._valor(f'cbx_area_{indice}'),
                'SubArea': self._valor(f'cbx_sub_area_{indice}'),
                'Seguimiento': self._valor(f'txt_seguimiento_{indice}'),
                'Responsable': self._valor(f'cbx_responsable_{indice}'),
                'Capturo': self._valor(f'tbx_capturo_{indice}'),
                'Salio': self._valor(f'chk_salio_{indice}') or 0,
            })
        return quejas

    def _valor(self, componente):
        widget = self.ventanas.componentes_forma.get(componente)

        if widget is None:
            return None

        try:
            return widget.get('1.0', tk.END).strip()
        except Exception:
            pass

        try:
            return widget.get()
        except Exception:
            return None