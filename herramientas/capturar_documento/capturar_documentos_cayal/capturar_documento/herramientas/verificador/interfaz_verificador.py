import tkinter as tk

from cayal.ventanas import Ventanas


class InterfazVerificador:
    TITULO = 'Verificador de precios'

    ESTADO_INICIAL = 'inicial'
    ESTADO_PRODUCTO = 'producto'
    ESTADO_OFERTA = 'oferta'

    def __init__(self, master):
        self.master = master
        self.ventanas = Ventanas(self.master)

        self._crear_frames()

        self._crear_componentes()
        self._crear_barra_herramientas()
        self._ajustar_componentes()
        self._rellenar_componentes()
        self._agregar_validaciones()
        self.configurar_posicion_frames(self.ESTADO_INICIAL)

        self.ventanas.configurar_ventana_ttkbootstrap(
            titulo=self.TITULO,
            nombre_icono='barcode.ico'
        )
        self.ventanas.enfocar_componente('tbx_buscar')

    @staticmethod
    def _grid(
            row,
            column=0,
            columnspan=1,
            pady=2,
            padx=2,
            sticky=tk.NSEW
    ):
        return {
            'row': row,
            'column': column,
            'columnspan': columnspan,
            'pady': pady,
            'padx': padx,
            'sticky': sticky
        }

    # ------------------------------------------------------------------
    # Frames
    # ------------------------------------------------------------------

    def _crear_frames(self):
        """
        Organiza la parte superior en secciones funcionales sin cambiar
        la distribución original de las etiquetas de producto y oferta.
        """
        frames = {
            'frame_principal': (
                'master',
                None,
                self._grid(
                    row=0,
                    column=0,
                    pady=5,
                    padx=5,
                    sticky=tk.NSEW
                )
            ),

            # ----------------------------------------------------------
            # Consulta del producto
            # ----------------------------------------------------------
            'frame_consulta': (
                'frame_principal',
                'Consulta del producto',
                self._grid(
                    row=0,
                    column=0,
                    columnspan=2,
                    pady=(0, 5),
                    padx=0,
                    sticky=tk.EW
                )
            ),

            'frame_busqueda': (
                'frame_consulta',
                None,
                self._grid(
                    row=0,
                    column=0,
                    columnspan=2,
                    pady=3,
                    padx=5,
                    sticky=tk.EW
                )
            ),

            'frame_chk_busqueda': (
                'frame_busqueda',
                None,
                self._grid(
                    row=0,
                    column=2,
                    pady=2,
                    padx=(8, 2),
                    sticky=tk.W
                )
            ),

            'frame_seleccion': (
                'frame_consulta',
                None,
                self._grid(
                    row=1,
                    column=0,
                    columnspan=2,
                    pady=3,
                    padx=5,
                    sticky=tk.EW
                )
            ),

            # ----------------------------------------------------------
            # Cálculo
            # ----------------------------------------------------------
            'frame_calculo': (
                'frame_principal',
                'Cálculo',
                self._grid(
                    row=1,
                    column=0,
                    columnspan=2,
                    pady=(0, 5),
                    padx=0,
                    sticky=tk.EW
                )
            ),

            'frame_cantidad': (
                'frame_calculo',
                None,
                self._grid(
                    row=0,
                    column=0,
                    columnspan=2,
                    pady=3,
                    padx=5,
                    sticky=tk.EW
                )
            ),

            'frame_chk_monto': (
                'frame_calculo',
                None,
                self._grid(
                    row=0,
                    column=2,
                    pady=2,
                    padx=(8, 2),
                    sticky=tk.W
                )
            ),

            # ----------------------------------------------------------
            # Acciones
            # ----------------------------------------------------------
            'frame_acciones': (
                'frame_principal',
                'Acciones',
                self._grid(
                    row=2,
                    column=0,
                    columnspan=2,
                    pady=(0, 5),
                    padx=0,
                    sticky=tk.EW
                )
            ),

            'frame_botones': (
                'frame_acciones',
                None,
                self._grid(
                    row=0,
                    column=0,
                    pady=3,
                    padx=5,
                    sticky=tk.EW
                )
            ),

            # ----------------------------------------------------------
            # Etiquetas originales de resultado
            # ----------------------------------------------------------
            'frame_etiqueta_producto': (
                'frame_principal',
                None,
                self._grid(
                    row=3,
                    column=0,
                    columnspan=2,
                    pady=0,
                    padx=0,
                    sticky=tk.EW
                )
            ),

            'frame_detalles_oferta': (
                'frame_principal',
                None,
                self._grid(
                    row=4,
                    column=0,
                    columnspan=2,
                    pady=0,
                    padx=0,
                    sticky=tk.EW
                )
            ),

            'frame_detalles': (
                'frame_principal',
                None,
                self._grid(
                    row=5,
                    column=0,
                    columnspan=2,
                    pady=0,
                    padx=0,
                    sticky=tk.EW
                )
            ),

            # ----------------------------------------------------------
            # Mapa anatómico del producto
            # ----------------------------------------------------------
            'frame_mapa': (
                'frame_principal',
                None,
                self._grid(
                    row=6,
                    column=0,
                    columnspan=2,
                    pady=(5, 0),
                    padx=0,
                    sticky=tk.NSEW
                )
            )
        }

        self.ventanas.crear_frames(frames)

        frame_principal = self.ventanas.componentes_forma.get(
            'frame_principal'
        )

        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        if frame_principal:
            frame_principal.grid_columnconfigure(0, weight=1)
            frame_principal.grid_columnconfigure(1, weight=1)
            frame_principal.grid_rowconfigure(6, weight=0, minsize=0)

        frame_mapa = self.ventanas.componentes_forma.get(
            'frame_mapa'
        )

        if frame_mapa:
            frame_mapa.grid_rowconfigure(0, weight=1)
            frame_mapa.grid_columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # Componentes
    # ------------------------------------------------------------------

    def _crear_componentes(self):
        # Estos estilos se mantienen iguales al aplicativo original.
        estilo_lbl_blanca = {
            'foreground': 'white',
            'background': 'white',
            'font': ('consolas', 12, 'bold'),
            'anchor': 'center'
        }

        estilo_lbl_roja = {
            'width': 44,
            'foreground': 'white',
            'background': '#E30421',
            'font': ('consolas', 12, 'bold'),
            'anchor': 'center'
        }

        estilo_lbl_azul = {
            'width': 22,
            'foreground': 'white',
            'background': '#2A569A',
            'font': ('consolas', 25, 'bold'),
            'anchor': 'center'
        }

        estilo_lbl_naranja = {
            'width': 22,
            'foreground': 'white',
            'background': '#FE7F00',
            'font': ('consolas', 25, 'bold'),
            'anchor': 'center'
        }

        componentes = {
            # Consulta
            'tbx_buscar': (
                'frame_busqueda',
                None,
                'Buscar:',
                None
            ),

            'chk_linea': (
                'frame_chk_busqueda',
                None,
                'Línea',
                None
            ),

            'cbx_resultado': (
                'frame_seleccion',
                None,
                'Resultado:',
                None
            ),

            'cbx_lista': (
                'frame_seleccion',
                None,
                'Lista:',
                None
            ),

            # Cálculo
            'tbx_cantidad': (
                'frame_cantidad',
                None,
                'Cantidad:',
                None
            ),

            'chk_monto': (
                'frame_chk_monto',
                None,
                'Monto',
                None
            ),

            # ----------------------------------------------------------
            # Etiquetas originales: se conserva su estructura visual.
            # ----------------------------------------------------------
            'lbl_mapa_producto': (
                'frame_mapa',
                estilo_lbl_blanca,
                {
                    'row': 0,
                    'column': 0,
                    'columnspan': 2,
                    'pady': 5,
                    'padx': 5,
                    'sticky': tk.NSEW
                },
                None
            ),

            'lbl_producto': (
                'frame_etiqueta_producto',
                estilo_lbl_roja,
                {
                    'row': 0,
                    'column': 0,
                    'columnspan': 2,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.NSEW
                },
                None
            ),

            'lbl_precio': (
                'frame_detalles',
                estilo_lbl_azul,
                {
                    'row': 0,
                    'column': 0,
                    'columnspan': 2,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.NSEW
                },
                None
            ),

            'lbl_clave': (
                'frame_detalles',
                estilo_lbl_azul,
                {
                    'row': 1,
                    'column': 0,
                    'columnspan': 2,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.NSEW
                },
                None
            ),

            'lbl_existencia': (
                'frame_detalles',
                estilo_lbl_azul,
                {
                    'row': 2,
                    'column': 0,
                    'columnspan': 2,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.NSEW
                },
                None
            ),

            'lbl_existencia_texto': (
                'frame_detalles',
                estilo_lbl_azul,
                {
                    'row': 3,
                    'column': 0,
                    'columnspan': 2,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.NSEW
                },
                None
            ),

            'lbl_oferta_texto': (
                'frame_detalles_oferta',
                estilo_lbl_naranja,
                {
                    'row': 0,
                    'column': 0,
                    'columnspan': 2,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.NSEW
                },
                None
            ),

            'lbl_tipo_oferta': (
                'frame_detalles_oferta',
                estilo_lbl_naranja,
                {
                    'row': 1,
                    'column': 0,
                    'columnspan': 2,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.NSEW
                },
                None
            ),

            'lbl_validez_oferta': (
                'frame_detalles_oferta',
                estilo_lbl_naranja,
                {
                    'row': 2,
                    'column': 0,
                    'columnspan': 2,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.NSEW
                },
                None
            ),

            'lbl_precio_oferta': (
                'frame_detalles_oferta',
                estilo_lbl_naranja,
                {
                    'row': 3,
                    'column': 0,
                    'columnspan': 2,
                    'pady': 0,
                    'padx': 0,
                    'sticky': tk.NSEW
                },
                None
            )
        }

        self.ventanas.crear_componentes(componentes)

        lbl_mapa = self.ventanas.componentes_forma.get(
            'lbl_mapa_producto'
        )

        if lbl_mapa:
            lbl_mapa.configure(
                anchor='center'
            )

    # ------------------------------------------------------------------
    # Ajustes
    # ------------------------------------------------------------------

    def _ajustar_componentes(self):
        self.ventanas.ajustar_ancho_componente(
            'tbx_buscar',
            35
        )

        self.ventanas.ajustar_ancho_componente(
            'tbx_cantidad',
            12
        )

        self.ventanas.ajustar_ancho_componente(
            'cbx_resultado',
            60
        )

        self.ventanas.ajustar_ancho_componente(
            'cbx_lista',
            15
        )

        # Ajustes originales de las etiquetas.
        self.ventanas.ajustar_label_en_frame(
            'lbl_producto',
            'frame_etiqueta_producto'
        )

        self.ventanas.ajustar_label_en_frame(
            'lbl_precio',
            'frame_detalles'
        )

        self.ventanas.ajustar_label_en_frame(
            'lbl_oferta_texto',
            'frame_detalles_oferta'
        )

        etiquetas = (
            'lbl_tipo_oferta',
            'lbl_validez_oferta'
        )

        for etiqueta in etiquetas:
            componente = self.ventanas.componentes_forma[etiqueta]
            componente.config(
                font=('consolas', 12, 'bold')
            )

    # ------------------------------------------------------------------
    # Valores iniciales
    # ------------------------------------------------------------------

    def _rellenar_componentes(self):
        self.ventanas.insertar_input_componente(
            'lbl_existencia_texto',
            'EXISTENCIA'
        )

        self.ventanas.insertar_input_componente(
            'lbl_oferta_texto',
            'OFERTA'
        )

    def mostrar_mapa(self):
        frame_principal = self.ventanas.componentes_forma[
            'frame_principal'
        ]

        frame_principal.grid_rowconfigure(
            6,
            weight=1,
            minsize=260
        )

        self.ventanas.posicionar_frame('frame_mapa')
        self.ventanas.refrescar_tamano_forma()

    def ocultar_mapa(self):
        frame_principal = self.ventanas.componentes_forma[
            'frame_principal'
        ]

        self.ventanas.ocultar_frame('frame_mapa')

        frame_principal.grid_rowconfigure(
            6,
            weight=0,
            minsize=0
        )

        self.ventanas.refrescar_tamano_forma()

    # ------------------------------------------------------------------
    # Posicionamiento dinámico
    # ------------------------------------------------------------------

    def configurar_posicion_frames(
            self,
            estado=ESTADO_INICIAL
    ):
        estados_validos = {
            self.ESTADO_INICIAL,
            self.ESTADO_PRODUCTO,
            self.ESTADO_OFERTA
        }

        if estado not in estados_validos:
            raise ValueError(
                'Estado de interfaz no válido: {0}'.format(
                    estado
                )
            )

        self._ocultar_frames_resultado()

        if estado == self.ESTADO_PRODUCTO:
            self.ventanas.posicionar_frame(
                'frame_etiqueta_producto'
            )
            self.ventanas.posicionar_frame(
                'frame_detalles'
            )

        elif estado == self.ESTADO_OFERTA:
            self.ventanas.posicionar_frame(
                'frame_etiqueta_producto'
            )
            self.ventanas.posicionar_frame(
                'frame_detalles'
            )
            self.ventanas.posicionar_frame(
                'frame_detalles_oferta'
            )

        self.ventanas.configurar_ventana_ttkbootstrap(
            titulo=self.TITULO
        )
        self.ventanas.refrescar_tamano_forma()

    def _ocultar_frames_resultado(self):
        frames = (
            'frame_etiqueta_producto',
            'frame_detalles',
            'frame_detalles_oferta',

        )

        for nombre_frame in frames:
            self.ventanas.ocultar_frame(nombre_frame)

    # ------------------------------------------------------------------
    # Validaciones
    # ------------------------------------------------------------------

    def _agregar_validaciones(self):
        self.ventanas.agregar_validacion_tbx(
            'tbx_cantidad',
            'cantidad'
        )

    def _crear_barra_herramientas(self):
        """Crea la barra superior alineada a la derecha."""

        self.barra_herramientas = [
            {
                'nombre_icono': 'ProductGenerator32.ico',
                'etiqueta': 'Copiar',
                'nombre': 'copiar',
                'hotkey': '',
                'comando': None,
            },
            {
                'nombre_icono': 'CopyToOpportunity32.ico',
                'etiqueta': 'Copiar Todo',
                'nombre': 'copiar_todo',
                'hotkey': '',
                'comando': None,
            },
            {
                'nombre_icono': 'ConciliateProducts32.ico',
                'etiqueta': 'Ofertas',
                'nombre': 'ofertas',
                'hotkey': '',
                'comando': None,
            },
            {
                'nombre_icono': 'ProductInspection32.ico',
                'etiqueta': 'Información',
                'nombre': 'informacion',
                'hotkey': '',
                'comando': None,
            }


        ]

        self.elementos_barra_herramientas = (
            self.ventanas.crear_barra_herramientas(
                self.barra_herramientas,
                'frame_botones',
                vertical=False,
            )
        )
