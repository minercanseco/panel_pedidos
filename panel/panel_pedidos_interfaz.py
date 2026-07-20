import tkinter as tk

from cayal.ventanas import Ventanas


class InterfazPanelPedidos:
    """
    Interfaz adaptable para el panel de pedidos.

    Distribución vertical:
        0. Herramientas y medidores.
        1. Separación mínima.
        2. Filtros.
        3. Captura o tabla principal.
        4. Comentarios.
        5. Detalle del pedido.

    Las zonas de captura y detalle absorben el espacio disponible.
    """

    PORCENTAJE_ANCHO_PANTALLA = 0.96
    PORCENTAJE_ALTO_PANTALLA = 0.92

    ANCHO_MINIMO = 960
    ALTO_MINIMO = 600

    def __init__(self, master):
        self.master = master
        self.ventanas = Ventanas(self.master)

        self._configurar_ventana_adaptable()
        self._cargar_frames()
        self._cargar_componentes_forma()
        self._configurar_expansion_frames()

        # Recalcula la geometría una vez que todos los componentes existen.
        self.master.after_idle(self._finalizar_configuracion_ventana)

    # ------------------------------------------------------------------
    # CONFIGURACIÓN GENERAL
    # ------------------------------------------------------------------

    def _configurar_ventana_adaptable(self):
        """
        Ajusta la ventana al tamaño de la pantalla sin exceder su área útil.

        No utiliza un tamaño fijo para permitir que la interfaz funcione
        correctamente en resoluciones pequeñas, medianas y grandes.
        """
        ancho_pantalla, alto_pantalla = (
            self.ventanas.obtener_resolucion_pantalla()
        )

        ancho_ventana = int(
            ancho_pantalla * self.PORCENTAJE_ANCHO_PANTALLA
        )
        alto_ventana = int(
            alto_pantalla * self.PORCENTAJE_ALTO_PANTALLA
        )

        ancho_ventana = min(ancho_ventana, ancho_pantalla)
        alto_ventana = min(alto_ventana, alto_pantalla)

        posicion_x = max((ancho_pantalla - ancho_ventana) // 2, 0)
        posicion_y = max((alto_pantalla - alto_ventana) // 2, 0)

        self.master.geometry(
            f'{ancho_ventana}x{alto_ventana}'
            f'+{posicion_x}+{posicion_y}'
        )

        ancho_minimo = min(
            self.ANCHO_MINIMO,
            max(ancho_pantalla - 40, 640),
        )
        alto_minimo = min(
            self.ALTO_MINIMO,
            max(alto_pantalla - 80, 480),
        )

        self.master.minsize(ancho_minimo, alto_minimo)
        self.master.resizable(True, True)

        # Permite que frame_principal llene completamente la ventana.
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

    def _finalizar_configuracion_ventana(self):
        """
        Refresca la geometría después de construir completamente la interfaz.

        Se vuelve a habilitar el redimensionamiento porque algunas funciones
        generales de Ventanas pueden establecer resizable(False, False).
        """
        self.master.update_idletasks()
        self.master.resizable(True, True)

    def _obtener_tamano_meters(self):
        """
        Define un tamaño proporcional para los medidores.

        Los Meter no se redimensionan automáticamente como un Frame, por lo
        que se establece un tamaño inicial adecuado para cada resolución.
        """
        ancho, alto = self.ventanas.obtener_resolucion_pantalla()

        if ancho <= 1366 or alto <= 768:
            return 72

        if ancho <= 1600 or alto <= 900:
            return 88

        if ancho <= 1920 or alto <= 1080:
            return 102

        return 112

    # ------------------------------------------------------------------
    # FRAMES
    # ------------------------------------------------------------------

    def _cargar_frames(self):
        frames = {
            'frame_principal': (
                'master',
                None,
                {
                    'row': 0,
                    'column': 0,
                    'sticky': tk.NSEW,
                },
            ),

            'frame_herramientas': (
                'frame_principal',
                None,
                {
                    'row': 0,
                    'column': 0,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.NW,
                },
            ),

            'frame_totales': (
                'frame_principal',
                None,
                {
                    'row': 0,
                    'column': 1,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.NE,
                },
            ),

            'frame_meters': (
                'frame_totales',
                None,
                {
                    'row': 0,
                    'column': 0,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.NE,
                },
            ),

            'frame_filtros': (
                'frame_principal',
                None,
                {
                    'row': 2,
                    'column': 0,
                    'columnspan': 2,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.EW,
                },
            ),

            'frame_horarios': (
                'frame_filtros',
                None,
                {
                    'row': 0,
                    'column': 0,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.EW,
                },
            ),

            'frame_fecha': (
                'frame_filtros',
                None,
                {
                    'row': 0,
                    'column': 1,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.EW,
                },
            ),

            'frame_den_fecha': (
                'frame_fecha',
                None,
                {
                    'row': 0,
                    'column': 0,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.EW,
                },
            ),

            'frame_chks': (
                'frame_fecha',
                None,
                {
                    'row': 0,
                    'column': 1,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.EW,
                },
            ),

            'frame_capturista': (
                'frame_filtros',
                None,
                {
                    'row': 0,
                    'column': 3,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.EW,
                },
            ),

            'frame_status': (
                'frame_filtros',
                None,
                {
                    'row': 0,
                    'column': 5,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.EW,
                },
            ),

            'frame_captura': (
                'frame_principal',
                None,
                {
                    'row': 3,
                    'column': 0,
                    'columnspan': 2,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.NSEW,
                },
            ),

            'frame_comentarios': (
                'frame_principal',
                None,
                {
                    'row': 4,
                    'column': 0,
                    'columnspan': 2,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.EW,
                },
            ),

            'frame_detalle': (
                'frame_principal',
                None,
                {
                    'row': 5,
                    'column': 0,
                    'columnspan': 2,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.NSEW,
                },
            ),
        }

        self.ventanas.crear_frames(frames)

    def _configurar_expansion_frames(self):
        """
        Define qué zonas deben crecer y cuáles deben conservar su tamaño.

        La captura recibe una proporción mayor porque normalmente contiene
        la tabla principal. El detalle recibe el resto del espacio.
        """
        componentes = self.ventanas.componentes_forma

        frame_principal = componentes['frame_principal']
        frame_filtros = componentes['frame_filtros']
        frame_fecha = componentes['frame_fecha']
        frame_meters = componentes['frame_meters']
        frame_captura = componentes['frame_captura']
        frame_comentarios = componentes['frame_comentarios']
        frame_detalle = componentes['frame_detalle']

        # --------------------------------------------------------------
        # Ventana principal
        # --------------------------------------------------------------

        # Herramientas a la izquierda y medidores a la derecha.
        frame_principal.grid_columnconfigure(0, weight=1)
        frame_principal.grid_columnconfigure(1, weight=0)

        # Filas compactas.
        frame_principal.grid_rowconfigure(0, weight=0)
        frame_principal.grid_rowconfigure(1, weight=0)
        frame_principal.grid_rowconfigure(2, weight=0)
        frame_principal.grid_rowconfigure(4, weight=0)

        # Zonas que absorben el espacio vertical.
        frame_principal.grid_rowconfigure(3, weight=3)
        frame_principal.grid_rowconfigure(5, weight=2)

        # --------------------------------------------------------------
        # Filtros
        # --------------------------------------------------------------

        frame_filtros.grid_rowconfigure(0, weight=1)

        for columna in (0, 1, 3, 5):
            frame_filtros.grid_columnconfigure(
                columna,
                weight=1,
                uniform='filtros',
            )

        # --------------------------------------------------------------
        # Fecha y checks
        # --------------------------------------------------------------

        frame_fecha.grid_rowconfigure(0, weight=1)
        frame_fecha.grid_columnconfigure(0, weight=1)
        frame_fecha.grid_columnconfigure(1, weight=0)

        # --------------------------------------------------------------
        # Medidores
        # --------------------------------------------------------------

        frame_meters.grid_rowconfigure(0, weight=1)

        for columna in range(4):
            frame_meters.grid_columnconfigure(columna, weight=0)

        # --------------------------------------------------------------
        # Captura
        # --------------------------------------------------------------

        frame_captura.grid_rowconfigure(0, weight=1)
        frame_captura.grid_columnconfigure(0, weight=1)

        # --------------------------------------------------------------
        # Comentarios
        # --------------------------------------------------------------

        frame_comentarios.grid_rowconfigure(0, weight=1)
        frame_comentarios.grid_columnconfigure(0, weight=0)
        frame_comentarios.grid_columnconfigure(1, weight=1)

        # --------------------------------------------------------------
        # Detalle
        # --------------------------------------------------------------

        frame_detalle.grid_rowconfigure(0, weight=1)
        frame_detalle.grid_columnconfigure(0, weight=1)

        self.ventanas.ajustar_componente_en_frame(
            'tvw_detalle',
            'frame_detalle',
            expandir=True,
        )

    # ------------------------------------------------------------------
    # COMPONENTES
    # ------------------------------------------------------------------

    def _cargar_componentes_forma(self):
        tamano_meters = self._obtener_tamano_meters()

        componentes = {
            'cbx_horarios': (
                'frame_horarios',
                None,
                'Horas:',
                None,
            ),

            'cbx_capturista': (
                'frame_capturista',
                None,
                'Captura:',
                None,
            ),

            'cbx_status': (
                'frame_status',
                None,
                'Status:',
                None,
            ),

            'den_fecha': (
                'frame_den_fecha',
                'normal',
                None,
                None,
            ),

            'chk_sin_fecha': (
                'frame_chks',
                {
                    'row': 5,
                    'column': 1,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.W,
                },
                'Sin fecha',
                None,
            ),

            'chk_transferencias': (
                'frame_chks',
                {
                    'row': 5,
                    'column': 3,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.W,
                },
                'Transferencias',
                None,
            ),

            'mtr_total': (
                'frame_meters',
                None,
                'Total',
                tamano_meters,
            ),

            'mtr_en_tiempo': (
                'frame_meters',
                'success',
                'En tiempo',
                tamano_meters,
            ),

            'mtr_a_tiempo': (
                'frame_meters',
                'warning',
                'A tiempo',
                tamano_meters,
            ),

            'mtr_retrasado': (
                'frame_meters',
                'danger',
                'Retrasos',
                tamano_meters,
            ),

            'tbx_comentarios': (
                'frame_comentarios',
                {
                    'row': 0,
                    'column': 1,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.EW,
                },
                ' ',
                None,
            ),

            'tvw_detalle': (
                'frame_detalle',
                self.crear_columnas_tabla_detalle(),
                5,
                None,
            ),
        }

        self.ventanas.crear_componentes(componentes)

    # ------------------------------------------------------------------
    # COLUMNAS DE TABLAS
    # ------------------------------------------------------------------

    def crear_columnas_tabla_detalle(self):
        columnas = [
            {
                'text': 'Pedido',
                'stretch': False,
                'width': 68,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 0,
            },
            {
                'text': 'Producido',
                'stretch': False,
                'width': 68,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 0,
            },
            {
                'text': 'Tipo',
                'stretch': False,
                'width': 50,
                'column_anchor': tk.E,
                'heading_anchor': tk.W,
                'hide': 0,
            },
            {
                'text': 'Clave',
                'stretch': False,
                'width': 100,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 0,
            },
            {
                'text': 'Producto',
                'stretch': True,
                'width': 445,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 0,
            },
            {
                'text': 'Precio',
                'stretch': False,
                'width': 80,
                'column_anchor': tk.E,
                'heading_anchor': tk.W,
                'hide': 0,
            },
            {
                'text': 'Total',
                'stretch': False,
                'width': 100,
                'column_anchor': tk.E,
                'heading_anchor': tk.W,
                'hide': 0,
            },
            {
                'text': 'Esp.',
                'stretch': False,
                'width': 35,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 1,
            },
            {
                'text': 'ProductID',
                'stretch': False,
                'width': 80,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 1,
            },
            {
                'text': 'DocumentItemID',
                'stretch': False,
                'width': 80,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 1,
            },
            {
                'text': 'ItemProductionStatusModified',
                'stretch': False,
                'width': 0,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 1,
            },
            {
                'text': 'ClaveUnidad',
                'stretch': False,
                'width': 100,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 0,
            },
            {
                'text': 'StatusSurtido',
                'stretch': False,
                'width': 100,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 1,
            },
            {
                'text': 'UnitPrice',
                'stretch': False,
                'width': 100,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 1,
            },
            {
                'text': 'Piezas',
                'stretch': False,
                'width': 60,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 0,
            },
            {
                'text': 'Monto',
                'stretch': False,
                'width': 60,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 0,
            },
            {
                'text': 'Especificaciones',
                'stretch': True,
                'width': 440,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 0,
            },
            {
                'text': 'ProductTypeIDCayal',
                'stretch': False,
                'width': 100,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 1,
            },
        ]

        return self.ventanas.ajustar_columnas_a_resolucion(
            columnas,
            margen=60,
            factor_maximo=1.15,
            escalar_solo_si_excede=True,
        )

    def crear_columnas_tabla(self):
        columnas = [
            {'text': 'Pedido', 'stretch': True, 'width': 80},
            {'text': 'Relacion', 'stretch': True, 'width': 80},
            {'text': 'Factura', 'stretch': True, 'width': 80},
            {'text': 'Cliente', 'stretch': True, 'width': 130},
            {'text': 'F.Captura', 'stretch': True, 'width': 70},
            {'text': 'H.Captura', 'stretch': True, 'width': 45},
            {'text': 'Captura', 'stretch': True, 'width': 65},
            {'text': 'F.Entrega', 'stretch': True, 'width': 70},
            {'text': 'H.Entrega', 'stretch': True, 'width': 45},
            {'text': 'Direccion', 'stretch': True, 'width': 80},
            {'text': 'HoraID', 'stretch': False, 'width': 0},
            {'text': 'WayToPayID', 'stretch': False, 'width': 0},
            {'text': 'F.Pago', 'stretch': True, 'width': 70},
            {'text': 'Status', 'stretch': True, 'width': 70},
            {'text': 'Ruta', 'stretch': True, 'width': 40},
            {'text': 'OrderTypeID', 'stretch': False, 'width': 0},
            {'text': 'Tipo', 'stretch': True, 'width': 50},
            {
                'text': 'OrderDeliveryTypeID',
                'stretch': False,
                'width': 0,
            },
            {'text': 'T.Entrega', 'stretch': True, 'width': 70},
            {
                'text': 'OrderTypeOriginID',
                'stretch': False,
                'width': 0,
            },
            {'text': 'Origen', 'stretch': True, 'width': 70},
            {'text': 'ProductionTypeID', 'stretch': False, 'width': 0},
            {'text': 'Áreas', 'stretch': True, 'width': 50},
            {'text': 'PriorityID', 'stretch': False, 'width': 0},
            {'text': 'Impreso', 'stretch': True, 'width': 50},
            {'text': 'Prioridad', 'stretch': True, 'width': 70},
            {'text': 'DocumentTypeID', 'stretch': False, 'width': 0},
            {'text': 'T.Docto', 'stretch': True, 'width': 65},
            {'text': 'Adicionales', 'stretch': False, 'width': 0},
            {
                'text': 'PaymentConfirmedID',
                'stretch': False,
                'width': 0,
            },
            {'text': 'Pago', 'stretch': False, 'width': 0},
            {'text': 'SubTotal', 'stretch': False, 'width': 0},
            {'text': 'Impuestos', 'stretch': False, 'width': 0},
            {'text': 'Cancelado', 'stretch': False, 'width': 0},
            {'text': 'Total', 'stretch': True, 'width': 85},
            {'text': 'T.Factura', 'stretch': True, 'width': 85},
            {'text': 'Mensajes', 'stretch': False, 'width': 0},
            {'text': 'TypeStatusID', 'stretch': False, 'width': 0},
            {'text': 'StatusScheduleID', 'stretch': False, 'width': 0},
            {'text': 'Comentarios', 'stretch': False, 'width': 0},
            {'text': 'OrderDocumentID', 'stretch': False, 'width': 0},
            {'text': 'BusinessEntityID', 'stretch': False, 'width': 0},
            {'text': 'DepotID', 'stretch': False, 'width': 0},
            {'text': 'AddressDetailID', 'stretch': False, 'width': 0},
            {'text': 'CaptureBy', 'stretch': False, 'width': 0},
        ]

        return self.ventanas.ajustar_columnas_a_resolucion(
            columnas,
            margen=60,
            factor_maximo=1.15,
            escalar_solo_si_excede=True,
        )