import tkinter as tk

import ttkbootstrap as ttk

from cayal.ventanas import Ventanas


class InterfazCaptura:
    """Construye la interfaz de captura a partir de configuración centralizada."""

    MENSAJE_GUARDAR_DOCUMENTO = '¿Desea guardar el documento antes de cerrar?'

    MODULOS_FISCALES = (21, 1400, 1319)
    MODULO_SIN_SALDOS = 158
    MODULO_COMPRAS = 152
    MODULO_PEDIDOS = 1687
    MODULOS_VENTAS = (158, 21, 1400, 1316, 1319, 967)
    MODULOS_COBRO = (21, 1400, 1319, 158)
    ANCHO_COMPACTO = 1366
    ANCHO_TABLA_COMPACTA = 1367

    COLOR_TOTALES = '#E30421'
    FUENTE_TOTALES = 'Consolas'

    ATAJOS_MANUALES = {
        'btn_agregar_manual': '[F8]',
        'btn_especificaciones_manual': '[Ctrl+E]',
        'btn_ofertas_manual': '[F9]',
        'btn_copiar_manual': '',
        'tbx_buscar_manual': '[Ctrl+B]',
        'cbx_tipo_busqueda_manual': 'Ctrl+F',
    }

    HERRAMIENTAS_CONFIG = (
        {
            'funcion': 'verificador_precios',
            'nombre_icono': 'Barcode32.ico',
            'etiqueta': 'V.Precios',
            'nombre': 'verificador_precios',
            'hotkey': '[F3]',
            'aplica': 'siempre',
        },

        {
            'funcion': 'editar_cliente',
            'nombre_icono': 'DocumentEdit32.ico',
            'etiqueta': 'Editar Cliente',
            'nombre': 'editar_cliente',
            'hotkey': '[F6]',
            'aplica': 'con_cliente',
        },
        {
            'funcion': 'cambiar_direccion',
            'nombre_icono': 'Address32.ico',
            'etiqueta': 'Dirección',
            'nombre': 'cambiar_direccion',
            'hotkey': '[F5]',
            'aplica': 'con_cliente',
        },
        {
            'funcion': 'historial_cliente',
            'nombre_icono': 'CampaignFlow32.ico',
            'etiqueta': 'H.Cliente',
            'nombre': 'historial_cliente',
            'hotkey': '[F7]',
            'aplica': 'con_cliente',
        },
        {
            'funcion': 'editar_partida',
            'nombre_icono': 'ProductChange32.ico',
            'etiqueta': 'Editar',
            'nombre': 'editar_partida',
            'hotkey': '[F2]',
            'aplica': 'partidas_editables',
        },
        {
            'funcion': 'eliminar_partida',
            'nombre_icono': 'Cancelled32.ico',
            'etiqueta': 'Eliminar',
            'nombre': 'eliminar_partida',
            'hotkey': '[SUPR]',
            'aplica': 'partidas_editables',
        },
        {
            'funcion': 'cobrar_nota',
            'nombre_icono': 'Finance32.ico',
            'etiqueta': 'Cobrar',
            'nombre': 'cobrar_nota',
            'hotkey': '[F12]',
            'aplica': 'cobro',
        },

        {
            'funcion': 'cambiar_proveedor',
            'nombre_icono': 'Supplier.ico',
            'etiqueta': 'Proveedor',
            'nombre': 'cambiar_proveedor',
            'hotkey': '[F4]',
            'aplica': 'compras',
        },
        {
            'funcion': 'prorratear',
            'nombre_icono': 'Finance32.ico',
            'etiqueta': 'Prorrateo',
            'nombre': 'prorratear',
            'hotkey': '[F12]',
            'aplica': 'compras',
        },
    )

    COLUMNAS_PRODUCTOS = (
        ('Cantidad', 70, tk.W, 0),
        ('Piezas', 70, tk.W, 0),
        ('Código', 110, tk.W, 0),
        ('Descripción', None, tk.W, 0),
        ('Unidad', 70, tk.W, 0),
        ('Precio', 70, tk.E, 0),
        ('Importe', 80, tk.E, 0),
        ('Impuesto', 80, tk.E, 0),
        ('Total', 90, tk.E, 0),
        ('ProductID', 0, tk.W, 1),
        ('DocumentItemID', 0, tk.W, 1),
        ('TipoCaptura', 0, tk.W, 1),
        ('UnidadCayal', 0, tk.W, 1),
        ('MontoCayal', 0, tk.W, 1),
        ('UUID', 0, tk.W, 1),
        ('ItemProductionStatusModified', 0, tk.W, 1),
        ('Comments', 0, tk.W, 1),
        ('CreatedBy', 0, tk.W, 1),
        # Datos técnicos para reconstruir y editar una partida de compra.
        ('Quantity', 0, tk.W, 1), #
        ('ProductName', 0, tk.W, 1), #
        ('ProductKey', 0, tk.W, 1), #
        ('Unit', 0, tk.W, 1), #
        ('ClaveUnidad', 0, tk.W, 1),
        ('ClaveProdServ', 0, tk.W, 1),
        ('CostPrice', 0, tk.W, 1),
        ('UnitPrice', 0, tk.W, 1),
        ('DiscountPerc', 0, tk.W, 1),
        ('descuento', 0, tk.W, 1),
        ('subtotal', 0, tk.W, 1),
        ('subtotal_con_descuento', 0, tk.W, 1),
        ('impuestos', 0, tk.W, 1),
        ('total', 0, tk.W, 1),
        ('total_con_descuento', 0, tk.W, 1),
        ('TaxTypeID', 0, tk.W, 1),
        ('FechaCosto', 0, tk.W, 1),
        ('ItemCosto', 0, tk.W, 1),
    )

    # Sólo controla la presentación de la tabla para compras. Los nombres y
    # posiciones originales de COLUMNAS_PRODUCTOS se conservan porque el
    # controlador los utiliza para reconstruir el diccionario de la partida.
    COLUMNAS_VISIBLES_COMPRAS = {
        'Cantidad': (65, 'Cantidad'),
        'Código': (105, 'Código'),
        'Descripción': (230, 'Descripción'),
        'Unidad': (65, 'Unidad'),
        'Precio': (75, 'Costo U.'),
        'Importe': (85, 'Subtotal'),
        'descuento': (80, 'Descuento'),
        'subtotal_con_descuento': (95, 'Sub-desc.'),
        'Impuesto': (80, 'Impuestos'),
        'Total': (90, 'Total'),
    }

    COLUMNAS_PRODUCTOS_MANUAL = (
        ('Código', 130, tk.W, 1),
        ('Descripción', None, tk.W, 0),
        ('Precio', 70, tk.E, 0),
        ('ProductID', 0, tk.W, 1),
        ('ClaveUnidad', 0, tk.W, 1),
        ('Category1', 0, tk.W, 1),
    )

    def __init__(self, master, modulo_id, solicitar_guardado=False):
        self.master = master
        self.module_id = modulo_id
        self.solicitar_guardado = solicitar_guardado

        self.ventanas = Ventanas(self.master)
        self.ancho_pantalla, self.alto_pantalla = self.ventanas.obtener_resolucion_pantalla()
        self.funciones = {}
        self.barra_herramientas_pedido = []
        self.elementos_barra_herramientas = None
        self.iconos_barra_herramientas = []
        self.etiquetas_barra_herramientas = []
        self.hotkeys_barra_herramientas = []
        # None indica que el usuario todavía no ha respondido la confirmación.
        self.guardar_documento = None
        self.cierre_solicitado = False
        self._procesando_confirmacion_cierre = False

        self._cargar_frames()
        self._cargar_componentes_forma()
        self._ajustar_componentes_forma()
        self._cargar_componentes_frame_totales()
        self._agregar_validaciones()
        self._cargar_captura_manual()

        if self.solicitar_guardado:
            self._configurar_confirmacion_guardado()

    def cambiar_titulo_ventana(self, titulo):
        """Cambia únicamente el título de la ventana actual."""
        self.master.title(str(titulo))

    def _configurar_confirmacion_guardado(self):
        """Intercepta los cierres solicitados por el usuario."""
        self.master.protocol('WM_DELETE_WINDOW', self.solicitar_cierre)
        self.master.bind('<Escape>', self.solicitar_cierre)

    def preguntar_guardar_documento(self):
        """Pregunta si debe guardarse y conserva la respuesta en una bandera."""
        respuesta = self.ventanas.mostrar_mensaje_pregunta(
            self.MENSAJE_GUARDAR_DOCUMENTO,
            master=self.master,
        )
        self.guardar_documento = bool(respuesta)
        return self.guardar_documento

    def solicitar_cierre(self, event=None):
        """Procesa una sola confirmación y cierra después de registrar la decisión."""
        if self._procesando_confirmacion_cierre:
            return

        self._procesando_confirmacion_cierre = True
        try:
            self.cierre_solicitado = True
            self.preguntar_guardar_documento()
            self.master.destroy()
        finally:
            self._procesando_confirmacion_cierre = False

    def inyectar_funciones(self, **funciones):
        """Recibe las acciones del controlador y crea la barra de herramientas.

        Las claves deben coincidir con ``funcion`` en HERRAMIENTAS_CONFIG.
        Sólo se exigen las funciones que aplican al módulo actual.
        """
        configuraciones = self._obtener_configuracion_herramientas()
        funciones_requeridas = {configuracion['funcion'] for configuracion in configuraciones}
        funciones_faltantes = sorted(funciones_requeridas.difference(funciones))

        if funciones_faltantes:
            nombres = ', '.join(funciones_faltantes)
            raise ValueError(f'Faltan funciones para la barra de herramientas: {nombres}')

        funciones_invalidas = sorted(
            nombre for nombre, funcion in funciones.items()
            if nombre in funciones_requeridas and not callable(funcion)
        )
        if funciones_invalidas:
            nombres = ', '.join(funciones_invalidas)
            raise TypeError(f'Las siguientes funciones no son ejecutables: {nombres}')

        self.funciones = funciones.copy()
        self._crear_barra_herramientas()

    def _aplica_herramienta(self, tipo):
        reglas = {
            'siempre': True,
            # Compras trabaja con proveedor y usa su propia barra específica.
            'con_cliente': self.module_id not in (
                self.MODULO_SIN_SALDOS,
                self.MODULO_COMPRAS,
            ),
            'pedidos': self.module_id == self.MODULO_PEDIDOS,
            'partidas_editables': self.module_id in (
                self.MODULO_PEDIDOS,
                self.MODULO_COMPRAS,
            ),
            'cobro': self.module_id in self.MODULOS_COBRO,
            'compras': self.module_id == self.MODULO_COMPRAS,
        }
        return reglas[tipo]

    def _obtener_configuracion_herramientas(self):
        return [
            configuracion
            for configuracion in self.HERRAMIENTAS_CONFIG
            if self._aplica_herramienta(configuracion['aplica'])
        ]

    def _crear_barra_herramientas(self):
        herramientas = []
        for configuracion in self._obtener_configuracion_herramientas():
            herramienta = {
                clave: valor
                for clave, valor in configuracion.items()
                if clave not in ('funcion', 'aplica')
            }
            herramienta['comando'] = self.funciones[configuracion['funcion']]
            herramientas.append(herramienta)

        self.barra_herramientas_pedido = herramientas
        self.elementos_barra_herramientas = self.ventanas.crear_barra_herramientas(
            self.barra_herramientas_pedido,
            'frame_herramientas',
        )
        self.iconos_barra_herramientas = self.elementos_barra_herramientas[0]
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]

    @property
    def _es_modulo_fiscal(self):
        return self.module_id in self.MODULOS_FISCALES

    @property
    def _es_pantalla_compacta(self):
        return self.ancho_pantalla <= self.ANCHO_COMPACTO

    @staticmethod
    def _grid(row, column=0, **opciones):
        posicion = {'row': row, 'column': column, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW}
        posicion.update(opciones)
        return posicion

    @staticmethod
    def _crear_columna(texto, ancho, anchor, ocultar):
        return {
            'text': texto,
            'stretch': False,
            'width': ancho,
            'column_anchor': anchor,
            'heading_anchor': tk.W,
            'hide': ocultar,
        }

    def _cargar_frames(self):
        frames = {
            'frame_principal': ('master', None, self._grid(0)),
            'frame_izquierdo': ('frame_principal', None, self._grid(0)),
            'frame_herramientas': ('frame_izquierdo', None, self._grid(0, columnspan=2)),
            'frame_cliente': ('frame_izquierdo', 'Datos cliente:', self._grid(1, columnspan=2)),
            'frame_captura': ('frame_izquierdo', 'Captura', self._grid(2, columnspan=2)),
            'frame_clave': ('frame_captura', None, self._grid(0, columnspan=2)),
            'frame_tabla': ('frame_captura', None, self._grid(1, columnspan=2)),
            'frame_comentario': ('frame_izquierdo', 'Comentarios:', self._grid(4, columnspan=2)),
            'frame_derecho': ('frame_principal', None, self._grid(0, 2, rowspan=5)),
            'frame_totales': ('frame_derecho', None, self._grid(0, 2, columnspan=5, sticky=tk.EW)),
            'frame_anuncio': ('frame_derecho', 'Captura manual', self._grid(2, 2, columnspan=4)),
        }

        if self._es_modulo_fiscal:
            frames['frame_fiscal'] = (
                'frame_principal',
                'Parametros Fiscales:',
                self._grid(6, columnspan=5, pady=5, padx=5),
            )

        if self._es_pantalla_compacta:
            frames.pop('frame_comentario')

        self.ventanas.crear_frames(frames)

    def _cargar_componentes_forma(self):
        filas_tabla_producto = 20 if self.ancho_pantalla <= self.ANCHO_TABLA_COMPACTA else 25
        if self._es_modulo_fiscal:
            filas_tabla_producto = 20

        componentes = {
            'tbx_cliente': ('frame_cliente', self._grid(0, 1, pady=2), ' ', None),
            'tbx_direccion': ('frame_cliente', self._grid(1, 1, pady=2), ' ', None),
            'tbx_comentario': ('frame_cliente', self._grid(2, 1, pady=2), ' ', None),
            'tbx_clave': ('frame_clave', None, None, None),
            'tvw_productos': ('frame_tabla', self.crear_columnas_tabla(), filas_tabla_producto, None),
            'txt_comentario_documento': ('frame_comentario', None, ' ', None),
        }

        if self._es_modulo_fiscal:
            campos_fiscales = (
                ('usocfdi', 'Uso CFDI:'),
                ('metodopago', 'Método Pago:'),
                ('formapago', 'Forma Pago:'),
                ('regimen', 'Régimen Fiscal:'),
            )
            for indice, (nombre, texto) in enumerate(campos_fiscales):
                columna = indice * 2
                componentes[f'lbl_{nombre}'] = (
                    'frame_fiscal',
                    {'text': texto},
                    self._grid(0, columna, sticky=tk.W),
                    None,
                )
                componentes[f'cbx_{nombre}'] = (
                    'frame_fiscal',
                    self._grid(0, columna + 1, pady=5, padx=5, sticky=tk.NSEW),
                    None,
                    None,
                )

        if self._es_pantalla_compacta:
            componentes.pop('txt_comentario_documento')

        self.ventanas.crear_componentes(componentes)
        self._configurar_encabezados_tabla_productos()

    def _cargar_componentes_frame_totales(self):
        frame_totales = self.ventanas.componentes_forma['frame_totales']
        frame_derecho = self.ventanas.componentes_forma['frame_derecho']
        color = self.COLOR_TOTALES

        # El encabezado ocupa el ancho disponible del panel derecho. De esta
        # forma su propio contenido no determina (y reduce) la escala.
        frame_derecho.grid_columnconfigure(2, weight=1)
        frame_totales.grid_configure(sticky=tk.EW)

        # Dos contenedores evitan que los datos generales y los importes
        # compartan columnas y se encimen cuando la ventana pierde ancho.
        frame_info = tk.Frame(frame_totales, background=color)
        frame_importes = tk.Frame(frame_totales, background=color)
        frame_info.grid(row=0, column=0, sticky=tk.NSEW)
        frame_importes.grid(row=0, column=1, sticky=tk.NSEW)
        if self.module_id in self.MODULOS_VENTAS:
            frame_totales.grid_columnconfigure(0, weight=2)
            frame_totales.grid_columnconfigure(1, weight=3)
        else:
            frame_totales.grid_columnconfigure(0, weight=1)
            frame_totales.grid_columnconfigure(1, weight=1)

        self.ventanas.componentes_forma['frame_info_totales'] = frame_info
        self.ventanas.componentes_forma[
            'frame_importes_totales'
        ] = frame_importes
        self._widgets_totales_responsive = []

        def crear_par(
                frame,
                fila,
                nombre,
                texto,
                valor_inicial='',
                rol='info',
        ):
            etiqueta = tk.Label(
                frame,
                text=texto,
                foreground='white',
                background=color,
                anchor='e',
                borderwidth=0,
                padx=2,
                pady=0,
            )
            valor = tk.Label(
                frame,
                text=valor_inicial,
                foreground='white',
                background=color,
                anchor='e',
                borderwidth=0,
                padx=2,
                pady=0,
            )
            etiqueta.grid(row=fila, column=0, sticky=tk.E)
            valor.grid(row=fila, column=1, sticky=tk.EW)
            frame.grid_columnconfigure(1, weight=1)

            self.ventanas.componentes_forma[nombre] = valor
            self.ventanas.componentes_forma[f'{nombre}_texto'] = etiqueta
            self._widgets_totales_responsive.extend((
                (etiqueta, f'{rol}_etiqueta'),
                (valor, f'{rol}_valor'),
            ))
            return valor, etiqueta

        datos_documento = (
            ('lbl_articulos', 'ARTS.:', '0'),
            ('lbl_folio', 'FOLIO:', ''),
            ('lbl_modulo', 'MÓDULO:', ''),
            ('lbl_captura', 'CAPTURA:', ''),
        )
        for fila, (nombre, texto, valor) in enumerate(datos_documento):
            crear_par(frame_info, fila, nombre, texto, valor, 'info')

        if self.module_id == self.MODULO_COMPRAS:
            importes = (
                ('lbl_subtotal', 'SUBTOTAL', '$ 0.00'),
                ('lbl_descuento', 'DESCUENTO', '$ 0.00'),
                (
                    'lbl_subtotal_con_descuento',
                    'SUB-DESC.',
                    '$ 0.00',
                ),
                ('lbl_impuestos', 'IMPUESTOS', '$ 0.00'),
                ('lbl_retenciones', 'RETENCIONES', '$ 0.00'),
                ('lbl_total', 'TOTAL', '$ 0.00'),
            )
        else:
            importes = (
                ('lbl_total', 'TOTAL', '$ 0.00'),
                ('lbl_credito', 'CRÉDITO', '$ 0.00'),
                ('lbl_debe', 'DEBE', '$ 0.00'),
                ('lbl_restante', 'DISP.', '$ 0.00'),
            )

        for fila, (nombre, texto, valor) in enumerate(importes):
            ocultar = (
                self.module_id == self.MODULO_SIN_SALDOS
                and nombre in ('lbl_credito', 'lbl_debe', 'lbl_restante')
            )
            componente, etiqueta = crear_par(
                frame_importes,
                fila,
                nombre,
                texto,
                '' if ocultar else valor,
                'total' if nombre == 'lbl_total' else 'importe',
            )
            if ocultar:
                etiqueta.config(text='')

        # Se ajusta después de que Tk conoce el ancho real y también cuando la
        # ventana cambia de tamaño o se visualiza mediante escritorio remoto.
        frame_derecho.bind(
            '<Configure>',
            self._escalar_etiquetas_totales,
            add='+',
        )
        self.master.after_idle(self._escalar_etiquetas_totales)

    def _escalar_etiquetas_totales(self, event=None):
        frame_derecho = self.ventanas.componentes_forma.get('frame_derecho')
        if frame_derecho is None:
            return

        ancho = frame_derecho.winfo_width()
        if event is not None and event.widget is frame_derecho:
            ancho = event.width
        if ancho <= 1:
            ancho = int(self.ancho_pantalla * 0.32)

        # Compras necesita alojar seis acumulados; los módulos de captura
        # tienen menor densidad y pueden dar más jerarquía al total. Ambos
        # perfiles conservan sus proporciones al cambiar la resolución.
        if self.module_id == self.MODULO_COMPRAS:
            escala = max(0.78, min(1.15, ancho / 500))
            tamanos_base = {
                'info_etiqueta': 12,
                'info_valor': 12,
                'importe_etiqueta': 12,
                'importe_valor': 16,
                'total_etiqueta': 16,
                'total_valor': 26,
            }
        else:
            escala = max(0.84, min(1.15, ancho / 500))
            tamanos_base = {
                'info_etiqueta': 14,
                'info_valor': 14,
                'importe_etiqueta': 13,
                'importe_valor': 17,
                'total_etiqueta': 24,
                'total_valor': 36,
            }
        tamanos = {
            rol: max(9, round(tamano * escala))
            for rol, tamano in tamanos_base.items()
        }

        # En ventas, al aparecer el separador de miles el texto deja de caber
        # con la fuente grande. Pedidos y compras conservan su escala actual.
        if self.module_id in self.MODULOS_VENTAS:
            nombres_importes = (
                'lbl_total',
                'lbl_credito',
                'lbl_debe',
                'lbl_restante',
            )
            longitud_mayor = max(
                len(str(
                    self.ventanas.componentes_forma[nombre].cget('text')
                ))
                for nombre in nombres_importes
                if nombre in self.ventanas.componentes_forma
            )

            # Desde cuatro cifras el formato monetario incluye separador de
            # miles (por ejemplo, "$4,047.00", 9 caracteres) y ya requiere
            # la fuente compacta. El umbral anterior de 10 sólo corregía los
            # importes de $10,000.00 en adelante.
            if longitud_mayor >= 9:
                tamanos['total_etiqueta'] = min(
                    tamanos['total_etiqueta'],
                    max(14, round(18 * escala)),
                )
                tamanos['total_valor'] = min(
                    tamanos['total_valor'],
                    max(18, round(24 * escala)),
                )
                tamanos['importe_valor'] = min(
                    tamanos['importe_valor'],
                    max(12, round(15 * escala)),
                )

        for widget, rol in self._widgets_totales_responsive:
            widget.configure(
                font=(self.FUENTE_TOTALES, tamanos[rol], 'bold')
            )

    def ajustar_etiquetas_totales(self):
        """Recalcula las fuentes después de modificar los importes."""
        self.master.after_idle(self._escalar_etiquetas_totales)

    def _agregar_validaciones(self):
        pass
        # self.ventanas.agregar_validacion_tbx('tbx_clave', 'codigo_barras')

    def _ajustar_componentes_forma(self):
        self.ventanas.ajustar_componente_en_frame('tbx_cliente', 'frame_cliente')
        self.ventanas.ajustar_componente_en_frame('txt_comentario_documento', 'frame_comentario')
        self.ventanas.ajustar_label_en_frame('lbl_anuncio', 'frame_anuncio')

    def _cargar_captura_manual(self):
        self._cargar_frames_manual()
        self._cargar_componentes_manual()

    def crear_columnas_tabla(self):
        ancho_descripcion = 180 if self.ancho_pantalla <= self.ANCHO_TABLA_COMPACTA else 230

        if self.module_id == self.MODULO_COMPRAS:
            columnas = []
            for texto, ancho, anchor, _ocultar in self.COLUMNAS_PRODUCTOS:
                configuracion = self.COLUMNAS_VISIBLES_COMPRAS.get(texto)
                if configuracion:
                    ancho_compra = configuracion[0]
                    if texto == 'Descripción':
                        ancho_compra = ancho_descripcion
                    columnas.append(
                        self._crear_columna(texto, ancho_compra, anchor, 0)
                    )
                else:
                    columnas.append(
                        self._crear_columna(texto, 0, anchor, 1)
                    )
            return columnas

        return [
            self._crear_columna(texto, ancho_descripcion if ancho is None else ancho, anchor, ocultar)
            for texto, ancho, anchor, ocultar in self.COLUMNAS_PRODUCTOS
        ]

    def _configurar_encabezados_tabla_productos(self):
        """Aplica títulos amigables sin cambiar las claves de las columnas."""
        if self.module_id != self.MODULO_COMPRAS:
            return

        tabla = self.ventanas.componentes_forma.get('tvw_productos')
        if tabla is None:
            return

        for indice, (texto, _ancho, _anchor, _ocultar) in enumerate(
                self.COLUMNAS_PRODUCTOS
        ):
            configuracion = self.COLUMNAS_VISIBLES_COMPRAS.get(texto)
            if configuracion:
                tabla.heading(indice, text=configuracion[1], anchor=tk.W)

    def _cargar_frames_manual(self):
        frames = {
            'frame_buscar_manual': ('frame_anuncio', 'Búsqueda', self._grid(0, columnspan=4, pady=1, padx=2)),
            'frame_tbx_buscar_manual': ('frame_buscar_manual', None, self._grid(0, columnspan=2, pady=1, padx=2, sticky=tk.NS)),
            'frame_cbx_buscar_manual': ('frame_buscar_manual', None, self._grid(0, 3, columnspan=2, pady=1, padx=2, sticky=tk.NS)),
            'frame_partida_manual': ('frame_anuncio', 'Partida:', self._grid(2, columnspan=4, pady=1, padx=2)),
            'frame_detalles_partida_manual': ('frame_partida_manual', 'Detalles:', self._grid(0, columnspan=4, pady=1, padx=2)),
            'frame_cantida_y_equivalencia': ('frame_detalles_partida_manual', 'Cantidad [Ctrl+C]', self._grid(0, columnspan=2, pady=1, padx=2, sticky=tk.W)),
            'frame_totales_manual': ('frame_detalles_partida_manual', 'Total pieza:', self._grid(0, 2, columnspan=2, rowspan=2, pady=1, padx=2)),
            'frame_controles_manual': ('frame_detalles_partida_manual', None, self._grid(1, columnspan=2, pady=1, padx=2)),
            'frame_txt_comentario_manual': ('frame_partida_manual', 'Especificación [Ctrl+M]', self._grid(6, columnspan=4, pady=1, padx=2)),
            'frame_txt_portapapeles_manual': ('frame_partida_manual', 'Portapapeles [Ctrl+P]', self._grid(7, columnspan=4, pady=1, padx=2)),
            'frame_botones_manual': ('frame_partida_manual', None, self._grid(11, 1, pady=3, sticky=tk.W)),
            'frame_tabla_manual': ('frame_anuncio', 'Productos [Ctrl+T]', self._grid(3, columnspan=4, pady=1, padx=2)),
        }
        if self._es_modulo_fiscal:
            frames.pop('frame_txt_portapapeles_manual')
        self.ventanas.crear_frames(frames)

    def _cargar_componentes_manual(self):
        tamano_fuente = 8 if self.ancho_pantalla <= self.ANCHO_TABLA_COMPACTA else 12
        alto_comentarios = 2 if self.ancho_pantalla <= self.ANCHO_TABLA_COMPACTA else 4

        def atajos_botones(ancho, nombre_boton):
            if ancho <= self.ANCHO_TABLA_COMPACTA:
                return None
            return self.ATAJOS_MANUALES[nombre_boton]

        fuente = (self.FUENTE_TOTALES, tamano_fuente, 'bold')

        def datos_label(texto, row, column, **opciones):
            estilo = {'text': texto, 'style': 'inverse-danger', 'anchor': 'e', 'font': fuente}
            estilo.update(opciones.pop('estilo', {}))
            return 'frame_totales_manual', estilo, self._grid(row, column, **opciones), None

        componentes = {
            'cbx_tipo_busqueda_manual': ('frame_cbx_buscar_manual', None, 'Tipo:', atajos_botones(self.ancho_pantalla, 'cbx_tipo_busqueda_manual')),
            'tbx_buscar_manual': ('frame_tbx_buscar_manual', None, 'Buscar:', atajos_botones(self.ancho_pantalla, 'tbx_buscar_manual')),
            'tbx_cantidad_manual': ('frame_cantida_y_equivalencia', 6, 'Cant:', None),
            'tbx_equivalencia_manual': ('frame_cantida_y_equivalencia', self._grid(2, 3, pady=5, padx=5, sticky=tk.W), 'Equi:', None),
            'txt_comentario_manual': ('frame_txt_comentario_manual', None, ' ', None),
            'txt_portapapeles_manual': ('frame_txt_portapapeles_manual', None, ' ', None),
            'lbl_monto_texto_manual': datos_label('TOTAL:', 0, 0),
            'lbl_monto_manual': datos_label('$0.00', 0, 1, estilo={'width': 10}),
            'lbl_cantidad_texto_manual': datos_label('CANTIDAD:', 1, 0),
            'lbl_cantidad_manual': datos_label('0.00', 1, 1),
            'lbl_existencia_texto_manual': datos_label('EXISTENCIA:', 2, 0),
            'lbl_existencia_manual': datos_label('0.00', 2, 1),
            'lbl_clave_manual': datos_label('CLAVE:', 3, 0, columnspan=2, estilo={'anchor': 'center'}),
            'chk_pieza': ('frame_controles_manual', self._grid(0, 1, pady=2, padx=2, sticky=tk.W), 'Pieza [F10]', None),
            'chk_monto': ('frame_controles_manual', self._grid(0, 3, pady=2, padx=2, sticky=tk.W), 'Monto [F11]', None),
            'tvw_productos_manual': ('frame_tabla_manual', self.crear_columnas_tabla_manual(), 5, None),
            'btn_agregar_manual': ('frame_botones_manual', 'success', 'Agregar', atajos_botones(self.ancho_pantalla, 'btn_agregar_manual')),
            'btn_especificaciones_manual': ('frame_botones_manual', 'primary', 'Especificación', atajos_botones(self.ancho_pantalla, 'btn_especificaciones_manual')),
            'btn_ofertas_manual': ('frame_botones_manual', 'info', 'Ofertas', atajos_botones(self.ancho_pantalla, 'btn_ofertas_manual')),
            'btn_copiar_manual': ('frame_botones_manual', 'warning', 'Copiar', atajos_botones(self.ancho_pantalla, 'btn_copiar_manual')),
        }
        if self._es_modulo_fiscal:
            componentes.pop('txt_portapapeles_manual')

        self.ventanas.crear_componentes(componentes)
        self.ventanas.ajustar_ancho_componente('cbx_tipo_busqueda', 15)
        self.ventanas.ajustar_ancho_componente('tbx_buscar_manual', 15)
        self.ventanas.ajustar_ancho_componente('tbx_equivalencia_manual', 6)
        self.ventanas.ajustar_componente_en_frame('txt_comentario_manual', 'frame_txt_comentario_manual')
        self.ventanas.ajustar_componente_en_frame('txt_portapapeles_manual', 'frame_txt_portapapeles_manual')
        self.ventanas.ajustar_alto_componente('txt_comentario_manual', alto_comentarios)
        self.ventanas.ajustar_alto_componente('txt_portapapeles_manual', alto_comentarios)

    def crear_columnas_tabla_manual(self):
        ancho_descripcion = 300 if self.ancho_pantalla <= self.ANCHO_TABLA_COMPACTA else 390
        return [
            self._crear_columna(texto, ancho_descripcion if ancho is None else ancho, anchor, ocultar)
            for texto, ancho, anchor, ocultar in self.COLUMNAS_PRODUCTOS_MANUAL
        ]
