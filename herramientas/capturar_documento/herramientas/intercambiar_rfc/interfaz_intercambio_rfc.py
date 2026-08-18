import tkinter as tk

from cayal.ventanas import Ventanas


class InterfazIntercambioRfc:
    """Formulario para confirmar los datos fiscales de un cliente."""

    CAMPOS_INFORMATIVOS = (
        'tbx_cliente',
        'tbx_tipo',
        'tbx_rfc',
        'tbx_rfc_respaldado',
        'tbx_regimen',
        'tbx_regimen_respaldado',
        'cbx_forma_pago',
        'cbx_metodo_pago',
        'cbx_uso_cfdi'
    )

    def __init__(self, master):
        self._master = master
        self.ventanas = Ventanas(master)

        self._crear_frames()
        self._crear_componentes()
        self._ajustar_layout()
        self.bloquear_campos_informativos()

        self.ventanas.configurar_ventana_ttkbootstrap(
            titulo='Información fiscal del cliente',
            dimensiones=None,
            bloquear=True,
            nombre_icono='Customer32.ico',
        )

    def _crear_frames(self):
        self.ventanas.crear_frames({
            'frame_principal': (
                'master',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW,
                 'padx': 10, 'pady': 10},
            ),
            'frame_cliente': (
                'frame_principal',
                'Cliente seleccionado',
                {'row': 0, 'column': 0, 'sticky': tk.EW,
                 'padx': 5, 'pady': 5},
            ),
            'frame_datos_fiscales': (
                'frame_principal',
                'Datos fiscales',
                {'row': 1, 'column': 0, 'sticky': tk.EW,
                 'padx': 5, 'pady': 5},
            ),
            'frame_facturacion': (
                'frame_principal',
                'Datos de facturación',
                {'row': 2, 'column': 0, 'sticky': tk.EW,
                 'padx': 5, 'pady': 5},
            ),
            'frame_botones': (
                'frame_principal',
                None,
                {'row': 3, 'column': 0, 'sticky': tk.E,
                 'padx': 5, 'pady': (10, 5)},
            ),
        })

    def _crear_componentes(self):
        self.ventanas.crear_componentes({
            'tbx_cliente': ('frame_cliente', 50, 'Cliente:', None),
            'tbx_tipo': ('frame_cliente', 30, 'Tipo:', None),
            'tbx_rfc': ('frame_datos_fiscales', 30, 'RFC:', None),
            'tbx_rfc_respaldado': (
                'frame_datos_fiscales', 30, 'RFC respaldado:', None
            ),
            'tbx_regimen': (
                'frame_datos_fiscales', 50, 'Régimen fiscal:', None
            ),
            'tbx_regimen_respaldado': (
                'frame_datos_fiscales', 50, 'Régimen respaldado:', None
            ),
            'cbx_forma_pago': (
                'frame_facturacion', None, 'Forma de pago:', None
            ),
            'cbx_metodo_pago': (
                'frame_facturacion', None, 'Método de pago:', None
            ),
            'cbx_uso_cfdi': (
                'frame_facturacion', None, 'Uso de CFDI:', None
            ),
            'btn_aceptar': ('frame_botones', 'primary', 'Aceptar', None),
            'btn_cancelar': ('frame_botones', 'danger', 'Cancelar', None),
        })

    def _ajustar_layout(self):
        frame_principal = self.ventanas.componentes_forma['frame_principal']
        frame_principal.grid_columnconfigure(0, weight=1)

        for nombre_frame in (
            'frame_cliente',
            'frame_datos_fiscales',
            'frame_facturacion',
        ):
            frame = self.ventanas.componentes_forma[nombre_frame]
            frame.grid_columnconfigure(1, weight=1)

    def bloquear_campos_informativos(self):
        for nombre_componente in self.CAMPOS_INFORMATIVOS:
            self.ventanas.bloquear_componente(nombre_componente)
