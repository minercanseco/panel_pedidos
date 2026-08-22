import tkinter as tk

from cayal.ventanas import Ventanas


class InterfazRelacionarFactura:
    """
    Interfaz para seleccionar y relacionar una factura con otro CFDI.

    La interfaz únicamente define la estructura visual. El controlador debe:

        - insertar cliente, folio y documento relacionado;
        - rellenar el catálogo de tipos de relación;
        - cargar las facturas disponibles;
        - enlazar los eventos de Guardar y Seleccionar.
    """

    def __init__(self, master):
        self.master = master
        self.ventanas = Ventanas(master)

        self._crear_frames()
        self._crear_componentes()
        self._ajustar_layout()

        self.ventanas.configurar_ventana_ttkbootstrap(
            titulo='Relacionar factura',
            bloquear=True,
            nombre_icono='factura.ico',
        )

    def _crear_frames(self):
        frames = {
            'frame_principal': (
                'master',
                None,
                {
                    'row': 0,
                    'column': 0,
                    'sticky': tk.NSEW,
                    'padx': 6,
                    'pady': 6,
                },
            ),
            'frame_encabezado': (
                'frame_principal',
                None,
                {
                    'row': 0,
                    'column': 0,
                    'sticky': tk.EW,
                },
            ),
            'frame_datos_documento': (
                'frame_principal',
                None,
                {
                    'row': 1,
                    'column': 0,
                    'sticky': tk.EW,
                    'padx': 8,
                    'pady': (12, 5),
                },
            ),
            'frame_tipo_relacion': (
                'frame_principal',
                None,
                {
                    'row': 2,
                    'column': 0,
                    'sticky': tk.EW,
                    'padx': 8,
                    'pady': (5, 10),
                },
            ),
            'frame_tabla': (
                'frame_principal',
                None,
                {
                    'row': 3,
                    'column': 0,
                    'sticky': tk.NSEW,
                    'padx': 3,
                    'pady': 3,
                },
            ),
            'frame_botones': (
                'frame_principal',
                None,
                {
                    'row': 4,
                    'column': 0,
                    'sticky': tk.EW,
                    'padx': 5,
                    'pady': (10, 3),
                },
            ),
        }

        self.ventanas.crear_frames(frames)
    @staticmethod
    def columnas():
        return [
            {
                'text': 'DocumentID',
                'stretch': False,
                'width': 80,
                'column_anchor': tk.E,
                'heading_anchor': tk.E,
                'hide': 1,
            },
            {
                'text': 'N',
                'stretch': False,
                'width': 45,
                'column_anchor': tk.CENTER,
                'heading_anchor': tk.CENTER,
                'hide': 0,
            },
            {
                'text': 'Fecha',
                'stretch': False,
                'width': 100,
                'column_anchor': tk.CENTER,
                'heading_anchor': tk.CENTER,
                'hide': 0,
            },
            {
                'text': 'Tipo',
                'stretch': False,
                'width': 100,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 0,
            },
            {
                'text': 'Folio',
                'stretch': False,
                'width': 100,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 0,
            },
            {
                'text': 'FP',
                'stretch': False,
                'width': 55,
                'column_anchor': tk.CENTER,
                'heading_anchor': tk.CENTER,
                'hide': 0,
            },
            {
                'text': 'Sucursal',
                'stretch': True,
                'width': 100,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 0,
            },
            {
                'text': 'UUID',
                'stretch': False,
                'width': 280,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 0,
            },
        ]

    def _crear_componentes(self):

        componentes = {

            'tbx_cliente': (
                'frame_datos_documento',
                {
                    'row': 0,
                    'column': 1,
                    'sticky': tk.EW,
                    'padx': (5, 8),
                    'pady': 4,
                },
                'Cliente:',
                None,
            ),
            'tbx_folio': (
                'frame_datos_documento',
                {
                    'row': 1,
                    'column': 1,
                    'sticky': tk.EW,
                    'padx': (5, 8),
                    'pady': 4,
                },
                'Folio:',
                None,
            ),
            'tbx_status': (
                'frame_datos_documento',
                {
                    'row': 2,
                    'column': 1,
                    'sticky': tk.EW,
                    'padx': (5, 8),
                    'pady': 4,
                },
                'Status:',
                None,
            ),

            'cbx_tipo_relacion': (
                'frame_tipo_relacion',
                {
                    'row': 0,
                    'column': 1,
                    'sticky': tk.EW,
                    'padx': (5, 8),
                    'pady': 4,
                },
                'T. relación:',
                None,
            ),
            'tvw_facturas': (
                'frame_tabla',
                self.columnas(),
                16,
                'primary',
            ),
            'btn_guardar': (
                'frame_botones',
                'primary',
                'Guardar',
                None,
            ),
            'btn_seleccionar': (
                'frame_botones',
                'success',
                'Seleccionar',
                None,
            ),
            'btn_cancelar': (
                'frame_botones',
                'danger',
                'Cancelar',
                None,
            ),
        }

        self.ventanas.crear_componentes(componentes)

    def _ajustar_layout(self):
        frame_principal = self.ventanas.componentes_forma[
            'frame_principal'
        ]
        frame_encabezado = self.ventanas.componentes_forma[
            'frame_encabezado'
        ]
        frame_datos = self.ventanas.componentes_forma[
            'frame_datos_documento'
        ]
        frame_tipo_relacion = self.ventanas.componentes_forma[
            'frame_tipo_relacion'
        ]
        frame_botones = self.ventanas.componentes_forma[
            'frame_botones'
        ]

        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        frame_principal.grid_rowconfigure(3, weight=1)
        frame_principal.grid_columnconfigure(0, weight=1)

        frame_encabezado.grid_columnconfigure(0, weight=1)

        frame_datos.grid_columnconfigure(0, minsize=105)
        frame_datos.grid_columnconfigure(1, weight=1)

        frame_tipo_relacion.grid_columnconfigure(0, minsize=105)
        frame_tipo_relacion.grid_columnconfigure(1, weight=1)

        frame_botones.grid_columnconfigure(0, weight=1)
        frame_botones.grid_columnconfigure(1, weight=1)
        frame_botones.grid_columnconfigure(2, weight=1)

        self.ventanas.ajustar_componente_en_frame(
            'tvw_facturas',
            'frame_tabla',
            expandir=True,
        )

        self.ventanas.ajustar_ancho_componente(
            'tbx_cliente',
            60,
        )
        self.ventanas.ajustar_ancho_componente(
            'tbx_folio',
            25,
        )

        self.ventanas.ajustar_ancho_componente(
            'cbx_tipo_relacion',
            55,
        )

        self.ventanas.bloquear_componente('tbx_cliente')
        self.ventanas.bloquear_componente('tbx_folio')
        self.ventanas.bloquear_componente('tbx_relacionado')