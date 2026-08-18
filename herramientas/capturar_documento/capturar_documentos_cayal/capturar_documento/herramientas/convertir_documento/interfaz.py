import tkinter as tk

from cayal.ventanas import Ventanas


class InterfazConvertirDocumento:
    def __init__(self, master):
        self._master = master
        self.ventanas = Ventanas(master)

        self._crear_frames()
        self._crear_componentes()
        self._configurar_layout()

        self.ventanas.configurar_ventana_ttkbootstrap(
            titulo='Convertir documento',
            dimensiones=None,
            bloquear=True,
            nombre_icono='CopyToInvoice32.ico',
        )

    def _crear_frames(self):
        self.ventanas.crear_frames({
            'frame_principal': (
                'master',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW,
                 'padx': 10, 'pady': 10},
            ),
            'frame_documento': (
                'frame_principal',
                'Documento seleccionado',
                {'row': 0, 'column': 0, 'sticky': tk.EW,
                 'padx': 5, 'pady': 5},
            ),
            'frame_conversion': (
                'frame_principal',
                'Conversión',
                {'row': 1, 'column': 0, 'sticky': tk.EW,
                 'padx': 5, 'pady': 5},
            ),
            'frame_botones': (
                'frame_principal',
                None,
                {'row': 2, 'column': 0, 'sticky': tk.E,
                 'padx': 5, 'pady': (10, 5)},
            ),
        })

    def _crear_componentes(self):
        self.ventanas.crear_componentes({
            'tbx_cliente': ('frame_documento', 55, 'Cliente:', None),
            'tbx_folio': ('frame_documento', 25, 'Folio:', None),
            'tbx_sucursal': ('frame_documento', 55, 'Sucursal:', None),
            'cbx_tipo_conversion': (
                'frame_conversion', None, 'Convertir a:', None
            ),
            'btn_guardar': ('frame_botones', 'success', 'Guardar', None),
            'btn_cancelar': ('frame_botones', 'danger', 'Cancelar', None),
        })

    def _configurar_layout(self):
        principal = self.ventanas.componentes_forma['frame_principal']
        principal.grid_columnconfigure(0, weight=1)

        for nombre in ('frame_documento', 'frame_conversion'):
            self.ventanas.componentes_forma[nombre].grid_columnconfigure(
                1, weight=1
            )

    def mostrar_documento(self, cliente, folio, sucursal):
        valores = {
            'tbx_cliente': cliente,
            'tbx_folio': folio,
            'tbx_sucursal': sucursal,
        }
        for nombre, valor in valores.items():
            componente = self.ventanas.componentes_forma[nombre]
            componente.configure(state='normal')
            componente.delete(0, tk.END)
            componente.insert(0, '' if valor is None else str(valor))
            componente.configure(state='readonly')

    def cargar_opciones_conversion(self, opciones):
        combo = self.ventanas.componentes_forma['cbx_tipo_conversion']
        valores = ('Seleccione',) + tuple(opciones)
        combo.configure(state='normal')
        combo.configure(values=valores)
        combo.set('Seleccione')
        combo.configure(state='readonly')
        self._master.update_idletasks()

    def bloquear_informacion(self):
        for nombre in ('tbx_cliente', 'tbx_folio', 'tbx_sucursal'):
            self.ventanas.bloquear_componente(nombre)
