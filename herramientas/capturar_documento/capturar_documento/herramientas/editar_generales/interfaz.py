import tkinter as tk

from cayal.ventanas import Ventanas


class InterfazEditarDocumento:

    def __init__(self, master):
        self._master = master
        self.ventanas = Ventanas(master)

        self._crear_frames()
        self._crear_componentes()

        self.ventanas.configurar_ventana_ttkbootstrap('Editar documento')

    def _crear_frames(self):
        frames = {
            'frame_principal': (
                'master',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW}
            ),

            'frame_generales': (
                'frame_principal',
                'Generales',
                {'row': 0, 'column': 0, 'padx': 8, 'pady': 8, 'sticky': tk.NSEW}
            ),

            'frame_botones': (
                'frame_principal',
                None,
                {'row': 1, 'column': 0, 'padx': 8, 'pady': 5, 'sticky': tk.E}
            ),
        }

        self.ventanas.crear_frames(frames)

    def _crear_componentes(self):
        componentes = {
            'tbx_cliente': ('frame_generales', None, 'Cliente:', None),
            'tbx_folio': ('frame_generales', None, 'Folio:', None),

            'cbx_formapago': ('frame_generales', None, 'FormaPago:', None),
            'cbx_metodopago': ('frame_generales', None, 'MetodoPago:', None),
            'cbx_usocfdi': ('frame_generales', None, 'UsoCFDI:', None),

            'txt_comentario': ('frame_generales', None, 'Comentario:', None),

            'btn_guardar': ('frame_botones', 'primary', 'Guardar', None),
            'btn_convertir_factura': ('frame_botones', 'secondary', 'C. Factura', None),
            'btn_convertir_remision': ('frame_botones', 'success', 'C. Remisión', None),
        }

        self.ventanas.crear_componentes(componentes)

        self.ventanas.ajustar_ancho_componente('tbx_cliente', 45)
        self.ventanas.ajustar_ancho_componente('tbx_folio', 20)

        self.ventanas.ajustar_ancho_componente('cbx_formapago', 45)
        self.ventanas.ajustar_ancho_componente('cbx_metodopago', 45)
        self.ventanas.ajustar_ancho_componente('cbx_usocfdi', 45)

        self.ventanas.ajustar_ancho_componente('txt_comentario', 45)
        self.ventanas.ajustar_alto_componente('txt_comentario', 5)

        self.ventanas.bloquear_componente('tbx_cliente')
        self.ventanas.bloquear_componente('tbx_folio')