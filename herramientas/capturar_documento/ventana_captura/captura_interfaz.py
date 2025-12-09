import tkinter as tk
import ttkbootstrap as ttk
from cayal.ventanas import Ventanas


class InterfazCaptura:
    def __init__(self, master, modulo_id):
        self.master = master
        self.module_id = modulo_id
        self.ventanas = Ventanas(self.master)

        self._cargar_frames()
        self._cargar_componentes_forma()
        self._ajustar_componentes_forma()
        self._cargar_componentes_frame_totales()
        self._agregar_validaciones()
        self._cargar_captura_manual()

    def _cargar_frames(self):
        nombre_frame_anuncio = 'Captura manual'
        frames = {

            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_izquierdo': ('frame_principal', None,
                              {'row': 0, 'column': 0,  'pady': 0, 'padx': 0, 'sticky': tk.NSEW}),

            'frame_herramientas': ('frame_izquierdo', None,
                                   {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 0, 'padx': 0,
                                    'sticky': tk.NSEW}),

            'frame_cliente': ('frame_izquierdo', 'Datos cliente:',
                              {'row': 1, 'column': 0, 'columnspan': 2, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW}),

            'frame_captura': ('frame_izquierdo', 'Captura',
                              {'row': 2, 'columnspan': 2, 'column': 0, 'pady': 0, 'padx': 0,
                               'sticky': tk.NSEW}),

            'frame_clave': ('frame_captura', None,
                            {'row': 0, 'columnspan': 2, 'column': 0, 'pady': 0, 'padx': 0,
                             'sticky': tk.NSEW}),
            'frame_tabla': ('frame_captura', None,
                            {'row': 1, 'columnspan': 2, 'column': 0, 'pady': 0, 'padx': 0,
                             'sticky': tk.NSEW}),

            'frame_comentario': ('frame_izquierdo', 'Comentarios:',
                                 {'row': 4, 'column': 0, 'columnspan': 2, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW}
                                 ),


            'frame_derecho': ('frame_principal', None,
                              {'row': 0, 'column': 2,  'rowspan':5, 'pady': 0, 'padx': 0,
                               'sticky': tk.NSEW}),

            'frame_totales': ('frame_derecho', None,
                              {'row': 0, 'column': 2,  'columnspan': 5, 'pady': 0, 'padx': 0,
                               'sticky': tk.NE}),

            'frame_anuncio': ('frame_derecho', nombre_frame_anuncio,
                              {'row': 2,  'column': 2, 'columnspan': 4, 'pady': 0, 'padx': 0,
                               'sticky': tk.NSEW}),
        }

        if self.module_id in (21, 1400, 1319): # facturas mayoreo, minisuper, globables entregadas
            frames.update({
                'frame_fiscal': ('frame_principal', 'Parametros Fiscales:',
                                 {'row': 6, 'column': 0, 'columnspan': 5, 'pady': 5, 'padx': 5, 'sticky': tk.NSEW}
                                 )
            })

        ancho, alto = self.ventanas.obtener_resolucion_pantalla()
        if ancho <= 1366:
            del frames['frame_comentario']

        self.ventanas.crear_frames(frames)

    def _cargar_componentes_forma(self):
        ancho, alto = self.ventanas.obtener_resolucion_pantalla()
        filas_tabla_producto = 20 if ancho <= 1367 else 30

        if self.module_id in(21, 1400, 1319):
            filas_tabla_producto = 20

        componentes = {
            'tbx_cliente': ('frame_cliente', {'row': 0, 'column': 1, 'pady': 2, 'padx': 0, 'sticky': tk.NSEW},
                            ' ', None),
            'tbx_direccion': ('frame_cliente', {'row': 1, 'column': 1, 'pady': 2, 'padx': 0, 'sticky': tk.NSEW},
                              ' ', None),
            'tbx_comentario': ('frame_cliente', {'row': 2, 'column': 1, 'pady': 2, 'padx': 0, 'sticky': tk.NSEW},
                               ' ', None),
            'tbx_clave': ('frame_clave', None, None, None),
            'tvw_productos': ('frame_tabla', self.crear_columnas_tabla(), filas_tabla_producto, None),
            'txt_comentario_documento': ('frame_comentario', None,' ', None),
        }

        if self.module_id in (21, 1400, 1319): # facturas mayoreo, minisuper, globables entregadas
            componentes.update({

                'lbl_usocfdi': ('frame_fiscal',
                                {'text': 'Uso CFDI:'},
                                {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                None),

                'cbx_usocfdi': ('frame_fiscal', {'row': 0, 'column': 1, 'pady': 5, 'padx': 5}, None, None),

                'lbl_metodopago': ('frame_fiscal',
                                {'text': 'Método Pago:'},
                                {'row': 0, 'column': 2, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                None),

                'cbx_metodopago': ('frame_fiscal', {'row': 0, 'column': 3, 'pady': 5, 'padx': 5}, None, None),

                'lbl_formapago': ('frame_fiscal',
                                   {'text': 'Forma Pago:'},
                                   {'row': 0, 'column': 4, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                   None),

                'cbx_formapago': ('frame_fiscal', {'row': 0, 'column': 5, 'pady': 5, 'padx': 5},  None,None),

                'lbl_regimen': ('frame_fiscal',
                                   {'text': 'Régimen Fiscal:'},
                                   {'row': 0, 'column': 6, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                   None),

                'cbx_regimen': ('frame_fiscal', {'row': 0, 'column': 7, 'pady': 5, 'padx': 5},  None, None),
            })

        if ancho <= 1366:
            del componentes['txt_comentario_documento']

        self.ventanas.crear_componentes(componentes)

    def _cargar_componentes_frame_totales(self):
        ancho, _ = self.ventanas.obtener_resolucion_pantalla()

        tam1 = 16 if ancho > 1366 else 11
        tam2_lbl = 14 if ancho > 1366 else 13
        tam2_val = 18 if ancho > 1366 else 17

        estilo_auxiliar = {
            'foreground': 'white',
            'background': '#E30421',
            'font': ('Consolas', tam1, 'bold'),
        }

        estilo_total = {
            'foreground': 'white',
            'background': '#E30421',
            'font': ('consolas', 29 if ancho > 1366 else 24, 'bold'),
        }

        etiqueta_totales = {
            'lbl_articulos': (
            estilo_auxiliar, {'row': 0, 'column': 1, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW}, 'ARTS.:'),
            'lbl_folio': (estilo_auxiliar, {'row': 1, 'column': 1, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW}, 'FOLIO:'),
            'lbl_modulo': (
            estilo_auxiliar, {'row': 2, 'column': 1, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW}, 'MÓDULO:'),
            'lbl_captura': (
            estilo_auxiliar, {'row': 3, 'column': 1, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW}, 'CAPTURA:'),
            'lbl_total': (estilo_total, {'row': 0, 'column': 5, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW}, 'TOTAL'),
            'lbl_credito': (estilo_total, {'row': 1, 'column': 5, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW}, 'CRÉDITO'),
            'lbl_debe': (estilo_total, {'row': 2, 'column': 5, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW}, 'DEBE'),
            'lbl_restante': (estilo_total, {'row': 3, 'column': 5, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW}, 'DISP.'),
        }

        frame_totales = self.ventanas.componentes_forma['frame_totales']

        # Crear estilo sin padding, compatible con ttkbootstrap
        try:
            style = ttk.Style()  # ttkbootstrap / ttk moderno
        except TypeError:
            style = ttk.Style(master=frame_totales)  # fallback para ttk clásico

        style.configure('NoPad.TLabel', padding=0, borderwidth=0)

        for nombre, (estilo, posicion, etiqueta) in etiqueta_totales.items():
            pos_val = posicion.copy()
            pos_txt = posicion.copy();
            pos_txt['column'] = pos_txt['column'] - 1

            # Label de valor (derecha)
            componente = ttk.Label(frame_totales, style='NoPad.TLabel')
            componente.config(**estilo)
            componente.grid(**pos_val)
            componente.grid_configure(padx=0, pady=0, ipadx=0, ipady=0)

            # Label de texto (izquierda)
            lbl = ttk.Label(frame_totales, text=etiqueta, style='NoPad.TLabel')
            lbl.config(**estilo)
            lbl.grid(**pos_txt)
            lbl.grid_configure(padx=0, pady=0, ipadx=0, ipady=0)

            if nombre in ('lbl_credito', 'lbl_debe', 'lbl_restante'):
                lbl.config(font=('roboto', tam2_lbl, 'bold'))
                lbl_texto = f'{nombre}_texto'
                self.ventanas.componentes_forma[lbl_texto] = lbl
                if self.module_id == 158:
                    lbl.config(text="")  # etiqueta vacía

            if nombre in ('lbl_credito', 'lbl_debe', 'lbl_restante', 'lbl_total'):
                if self.module_id == 158 and nombre in ('lbl_credito', 'lbl_debe', 'lbl_restante'):
                    componente.config(text='', font=('roboto', tam2_val, 'bold'), anchor='e')
                else:
                    if nombre == 'lbl_total':
                        componente.config(text='$ 0.00', font=('roboto', 29, 'bold'), anchor='e')
                    else:
                        componente.config(text='$ 0.00', font=('roboto', tam2_val, 'bold'), anchor='e')

            if nombre == 'lbl_articulos':
                componente.config(text='0')

            # Asegurar sin borde ni highlight
            for w in (componente, lbl):
                try:
                    w.configure(borderwidth=0, highlightthickness=0)
                except tk.TclError:
                    pass

            self.ventanas.componentes_forma[nombre] = componente

    def _agregar_validaciones(self):
        pass
        #self.ventanas.agregar_validacion_tbx('tbx_clave', 'codigo_barras')

    def _ajustar_componentes_forma(self):
        self.ventanas.ajustar_componente_en_frame('tbx_cliente', 'frame_cliente')

        self.ventanas.ajustar_componente_en_frame('txt_comentario_documento', 'frame_comentario')
        self.ventanas.ajustar_label_en_frame('lbl_anuncio', 'frame_anuncio')

    def _cargar_captura_manual(self):
        self._cargar_frames_manual()
        self._cargar_componentes_manual()

    def crear_columnas_tabla(self):
        ancho, alto = self.ventanas.obtener_resolucion_pantalla()
        ancho_descripcion = 180 if ancho <= 1367 else 230

        return [
            {"text": "Cantidad", "stretch": False, 'width': 70, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Piezas", "stretch": False, 'width': 70, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Código", "stretch": False, 'width': 110, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Descripción", "stretch": False, 'width': ancho_descripcion, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Unidad", "stretch": False, 'width': 70, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Precio", "stretch": False, 'width': 70, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Importe", "stretch": False, 'width': 80, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Impuesto", "stretch": False, 'width': 80, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Total", "stretch": False, 'width': 90, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "ProductID", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "DocumentItemID", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "TipoCaptura", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "UnidadCayal", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "MontoCayal", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "UUID", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "ItemProductionStatusModified", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "Comments", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "CreatedBy", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1}
        ]

    def _cargar_frames_manual(self):

        frames = {

            'frame_buscar_manual' : ('frame_anuncio', 'Búsqueda',
                       {'row': 0, 'column': 0, 'columnspan': 4, 'pady': 1, 'padx': 2, 'sticky': tk.NSEW}),

            'frame_tbx_buscar_manual' : ('frame_buscar_manual', None,
                                       {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 1, 'padx': 2, 'sticky': tk.NS}),

            'frame_cbx_buscar_manual' : ('frame_buscar_manual', None,
                                       {'row': 0, 'column': 3, 'columnspan': 2, 'pady': 1, 'padx': 2, 'sticky': tk.NS}),

            'frame_partida_manual' : ('frame_anuncio', 'Partida:',
                                    {'row': 2, 'column': 0, 'columnspan': 4, 'pady': 1, 'padx': 2, 'sticky': tk.NSEW}),



            'frame_detalles_partida_manual' : ('frame_partida_manual', 'Detalles:',
                                       {'row': 0, 'column': 0,  'columnspan': 4, 'pady': 1, 'padx': 2, 'sticky': tk.NSEW}),



            'frame_cantida_y_equivalencia': ('frame_detalles_partida_manual', 'Cantidad [Ctrl+C]',
                                        {'row': 0, 'column': 0,  'columnspan': 2, 'pady': 1, 'padx': 2,
                                         'sticky': tk.W}),

            'frame_totales_manual': ('frame_detalles_partida_manual', 'Total pieza:',
                                     {'row': 0, 'column': 2, 'columnspan': 2, 'rowspan': 2, 'pady': 1, 'padx': 2,
                                      'sticky': tk.NSEW}),


            'frame_controles_manual' : ('frame_detalles_partida_manual', None,
                                      {'row': 1, 'column': 0,  'columnspan': 2, 'pady': 1, 'padx': 2, 'sticky': tk.NSEW}),

            'frame_txt_comentario_manual' : ('frame_partida_manual', 'Especificación [Ctrl+M]',
                                           {'row': 6, 'column': 0, 'columnspan': 4, 'pady': 1, 'padx': 2, 'sticky': tk.NSEW}),

            'frame_txt_portapapeles_manual' : ('frame_partida_manual', 'Portapapeles [Ctrl+P]',
                                             {'row': 7, 'column': 0, 'columnspan': 4, 'pady': 1, 'padx': 2, 'sticky': tk.NSEW}),

            'frame_botones_manual' : ('frame_partida_manual', None,
                                    {'row': 11, 'column': 1, 'padx': 0, 'pady': 3, 'sticky': tk.W}),

            'frame_tabla_manual': ('frame_anuncio', 'Productos [Ctrl+T]',
                                   {'row': 3, 'column': 0, 'columnspan': 4, 'pady': 1, 'padx': 2, 'sticky': tk.NSEW})
        }

        if self.module_id in (21, 1400, 1319):

            del frames['frame_txt_portapapeles_manual']

        self.ventanas.crear_frames(frames)

    def _cargar_componentes_manual(self):

        ancho, alto = self.ventanas.obtener_resolucion_pantalla()
        tamano_fuente = 8 if ancho <= 1367 else 12
        alto_comentarios = 2 if ancho <= 1367 else 4

        def atajos_botones(ancho, nombre_boton):

            if ancho <= 1367:
               return None

            _atajos_botones = {
                'btn_agregar_manual': '[F8]',
                'btn_especificaciones_manual': '[Ctrl+E]',
                'btn_ofertas_manual': '[F9]',
                'btn_copiar_manual': '',
                'tbx_buscar_manual': '[Ctrl+B]',
                'cbx_tipo_busqueda_manual': 'Ctrl+F'
            }

            return _atajos_botones[nombre_boton]

        componentes = {
            'cbx_tipo_busqueda_manual': ('frame_cbx_buscar_manual', None, 'Tipo:', atajos_botones( ancho,'cbx_tipo_busqueda_manual')),
            'tbx_buscar_manual': ('frame_tbx_buscar_manual', None, 'Buscar:', atajos_botones( ancho,'tbx_buscar_manual')),

            'tbx_cantidad_manual': ('frame_cantida_y_equivalencia', 6, 'Cant:', None),
            'tbx_equivalencia_manual': ('frame_cantida_y_equivalencia',
                                 {'row': 2, 'column': 3, 'pady': 5, 'padx': 5, 'sticky': tk.W},
                                 'Equi:', None),

            'txt_comentario_manual': ('frame_txt_comentario_manual', None, ' ', None),
            'txt_portapapeles_manual': ('frame_txt_portapapeles_manual', None, ' ', None),

            'lbl_monto_texto_manual': ('frame_totales_manual',
                                { 'text': 'TOTAL:', 'style': 'inverse-danger', 'anchor': 'e',
                                 'font': ('Consolas', tamano_fuente, 'bold')},
                                {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                None),

            'lbl_monto_manual': ('frame_totales_manual',
                          {'width':10, 'text': '$0.00', 'style': 'inverse-danger', 'anchor': 'e',
                           'font': ('Consolas', tamano_fuente, 'bold')},
                          {'row': 0, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                          None),

            'lbl_cantidad_texto_manual': ('frame_totales_manual',
                                   { 'text': 'CANTIDAD:', 'style': 'inverse-danger', 'anchor': 'e',
                                    'font': ('Consolas', tamano_fuente, 'bold')},
                                   {'row': 1, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                   None),

            'lbl_cantidad_manual': ('frame_totales_manual',
                             { 'text': '0.00', 'style': 'inverse-danger', 'anchor': 'e',
                              'font': ('Consolas', tamano_fuente, 'bold')},
                             {'row': 1, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                             None),

            'lbl_existencia_texto_manual': ('frame_totales_manual',
                                     { 'text': 'EXISTENCIA:', 'style': 'inverse-danger', 'anchor': 'e',
                                      'font': ('Consolas', tamano_fuente, 'bold')},
                                     {'row': 2, 'column': 0, 'padx': 0, 'sticky': tk.NSEW},
                                     None),

            'lbl_existencia_manual': ('frame_totales_manual',
                               { 'text': '0.00', 'style': 'inverse-danger', 'anchor': 'e',
                                'font': ('Consolas', tamano_fuente, 'bold')},
                               {'row': 2, 'column': 1, 'padx': 0, 'sticky': tk.NSEW},
                               None),

            'lbl_clave_manual': ('frame_totales_manual',
                                      {'text': 'CLAVE:', 'style': 'inverse-danger', 'anchor': 'center',
                                       'font': ('Consolas', tamano_fuente, 'bold')},
                                      {'row': 3, 'columnspan': 2, 'column': 0, 'padx': 0, 'sticky': tk.NSEW},
                                      None),

            'chk_pieza': ('frame_controles_manual',
                          {'row': 0, 'column': 1, 'pady': 2, 'padx': 2, 'sticky': tk.W},
                          'Pieza [F10]', None),

            'chk_monto': ('frame_controles_manual',
                          {'row': 0, 'column': 3, 'pady': 2, 'padx': 2, 'sticky': tk.W},
                          'Monto [F11]', None),


            'tvw_productos_manual': ('frame_tabla_manual', self.crear_columnas_tabla_manual(), 5, None),
            'btn_agregar_manual': ('frame_botones_manual', 'success', 'Agregar',
                                   atajos_botones(ancho, 'btn_agregar_manual')),
            'btn_especificaciones_manual': ('frame_botones_manual', 'primary', 'Especificación',
                                            atajos_botones(ancho, 'btn_especificaciones_manual')),
            'btn_ofertas_manual': ('frame_botones_manual', 'info', 'Ofertas',
                                   atajos_botones(ancho, 'btn_ofertas_manual')),
            'btn_copiar_manual': ('frame_botones_manual', 'warning', 'Copiar',
                                  atajos_botones(ancho, 'btn_copiar_manual')),

        }
        if self.module_id in(21, 1400, 1319):
            del componentes['txt_portapapeles_manual']

        self.ventanas.crear_componentes(componentes)
        self.ventanas.ajustar_ancho_componente('cbx_tipo_busqueda',15)
        self.ventanas.ajustar_ancho_componente('tbx_buscar_manual', 15)
        self.ventanas.ajustar_ancho_componente('tbx_equivalencia_manual', 6)

        self.ventanas.ajustar_componente_en_frame('txt_comentario_manual', 'frame_txt_comentario_manual')
        self.ventanas.ajustar_componente_en_frame('txt_portapapeles_manual', 'frame_txt_portapapeles_manual')
        self.ventanas.ajustar_alto_componente('txt_comentario_manual', alto_comentarios)
        self.ventanas.ajustar_alto_componente('txt_portapapeles_manual', alto_comentarios)

    def crear_columnas_tabla_manual(self):

        ancho, alto = self.ventanas.obtener_resolucion_pantalla()
        ancho_descripcion = 300 if ancho <= 1367 else 390

        return [
            {"text": "Código", "stretch": False, 'width': 130, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "Descripción", "stretch": False, 'width': ancho_descripcion, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Precio", "stretch": False, 'width': 70, 'column_anchor': tk.E,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "ProductID", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "ClaveUnidad", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "Category1", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
        ]
