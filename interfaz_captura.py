import os
import random
import time

import tkinter as tk
import ttkbootstrap as ttk
from PIL import Image, ImageTk

from cayal.ventanas import Ventanas


class InterfazCaptura:
    def __init__(self, master, modulo_id):
        self.master = master
        self._modulo_id = modulo_id
        self.ventanas = Ventanas(self.master)
        self._PATH_IMAGENES_PUBLICITARIAS = self._obtener_ruta_imagenes_publitarias()

        self._cargar_frames()
        self._cargar_componentes_forma()
        self._ajustar_componentes_forma()
        self._cargar_imagen_publicitaria()
        self._cargar_componentes_frame_totales()
        self._agregar_validaciones()
        self._cargar_captura_manual()

    def _cargar_frames(self):
        nombre_frame_anuncio = 'Anuncios' if self._modulo_id not in [1687] else 'Captura manual'
        frames = {

            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_herramientas': ('frame_principal', 'Herramientas',
                                   {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                    'sticky': tk.NSEW}),

            'frame_cliente': ('frame_principal', 'Cliente',
                              {'row': 1, 'column': 0, 'columnspan': 2, 'rowspan': 3, 'pady': 5, 'padx': 5, 'sticky': tk.NSEW}),

            'frame_totales': ('frame_principal', None,
                              {'row': 0, 'column': 2, 'rowspan': 2, 'columnspan': 5, 'pady': 5, 'padx': 5,
                               'sticky': tk.NE}),

            'frame_captura': ('frame_principal', 'Captura',
                              {'row': 4, 'columnspan': 2, 'column': 0, 'pady': 5, 'padx': 5,
                               'sticky': tk.NSEW}),

            'frame_clave': ('frame_captura', None,
                              {'row': 0, 'columnspan': 2, 'column': 0, 'pady': 0, 'padx': 5,
                               'sticky': tk.NSEW}),
            'frame_tabla': ('frame_captura', None,
                            {'row': 1, 'columnspan': 2, 'column': 0, 'pady': 2, 'padx': 5,
                             'sticky': tk.NSEW}),

            'frame_comentario': ('frame_principal', None,
                             {'row': 5, 'column': 0, 'columnspan': 2, 'pady': 5, 'padx': 5, 'sticky': tk.NSEW}
                             ),

            'frame_anuncio': ('frame_principal', nombre_frame_anuncio,
                              {'row': 2, 'rowspan': 4, 'column': 2, 'columnspan': 4, 'pady': 5, 'padx': 5,
                               'sticky': tk.NSEW}),
        }

        if self._modulo_id not in [1687]:
            frames.update({
                'frame_fiscal': ('frame_principal', 'Parametros Fiscales:',
                                 {'row': 6, 'column': 0, 'columnspan': 5, 'pady': 5, 'padx': 5, 'sticky': tk.NSEW}
                                 )  # Cierra correctamente la tupla
            })  # Cierra correctamente el diccionario

        self.ventanas.crear_frames(frames)

    def _cargar_componentes_forma(self):
        ancho, alto = self.ventanas.obtener_resolucion_pantalla()
        filas_tabla_producto = 15 if ancho <= 1367 else 20

        componentes = {
            'tbx_cliente': ('frame_cliente', None, 'Cliente:', None),
            'tbx_direccion': ('frame_cliente', None, 'Dirección:', None),
            'tbx_comentario': ('frame_cliente', None, 'Comentario:', None),
            'tbx_clave': ('frame_clave', None, None, None),
            'tvw_productos': ('frame_tabla', self.crear_columnas_tabla(), filas_tabla_producto, None),
            'txt_comentario_documento': ('frame_comentario', None,'Comentarios:', None),

        }

        if self._modulo_id not in [1687]:
            componentes.update({
                'lbl_anuncio': ('frame_anuncio',
                                {'text': '', 'style': 'inverse-danger'},
                                {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                None),

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

        self.ventanas.crear_componentes(componentes)

    def _cargar_componentes_frame_totales(self):
        ancho, alto = self.ventanas.obtener_resolucion_pantalla()

        tamano_fuente_titulo_1 = 16 if ancho > 1366 else 11
        tamano_fuente_titulo_2 = 29 if ancho > 1366 else 24

        estilo_auxiliar = {
            'foreground': 'white',
            'background': '#E30421',
            'font': ('Consolas', tamano_fuente_titulo_1, 'bold'),
        }

        estilo_total = {
            'foreground': 'white',
            'background': '#E30421',
            'font': ('consolas', tamano_fuente_titulo_2, 'bold'),
        }

        etiqueta_totales = {
            'lbl_articulos': (estilo_auxiliar, {'row': 0, 'column': 1, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW},
                              'ARTS.:'),
            'lbl_folio': (estilo_auxiliar, {'row': 1, 'column': 1, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW},
                          'FOLIO:'),
            'lbl_modulo': (estilo_auxiliar, {'row': 2, 'column': 1, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW},
                           'MÓDULO:'),

            'lbl_captura': (estilo_auxiliar, {'row': 3, 'column': 1, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW},
                            'CAPTURA:'),

            'lbl_total': (estilo_total, {'row': 0, 'column': 5, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW},
                          'TOTAL'),

            'lbl_credito': (estilo_total, {'row': 1, 'column': 5, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW},
                            'CRÉDITO'),

            'lbl_debe': (estilo_total, {'row': 2, 'column': 5, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW},
                         'DEBE'),

            'lbl_restante': (estilo_total, {'row': 3, 'column': 5, 'padx': 0, 'pady': 0, 'sticky': tk.NSEW},
                             'DISP.'),

        }

        frame_totales = self.ventanas.componentes_forma['frame_totales']

        tamano_fuente_titulo_2 = 16 if ancho > 1366 else 13
        tamano_fuente_titulo_3 = 20 if ancho > 1366 else 17


        for nombre, (estilo, posicion, etiqueta) in etiqueta_totales.items():
            componente = ttk.Label(frame_totales)
            componente.config(**estilo)
            componente.grid(**posicion)

            texto = etiqueta  # nombre[4::].capitalize() if nombre not in en_mayusculas else nombre[4::].upper()

            lbl = ttk.Label(frame_totales, text=texto)
            posicion['column'] = posicion['column'] - 1
            lbl.config(**estilo)
            lbl.grid(**posicion)



            if nombre in ('lbl_credito', 'lbl_debe', 'lbl_restante'):
                lbl.config(font=('roboto', tamano_fuente_titulo_2, 'bold'))
                lbl_texto = f'{nombre}_texto'

                self.ventanas.componentes_forma[lbl_texto] = lbl

            if nombre in ('lbl_credito', 'lbl_debe', 'lbl_restante', 'lbl_total'):
                componente.config(text='$ 0.00', font=('roboto', tamano_fuente_titulo_3, 'bold'), anchor='e')

            if nombre == 'lbl_articulos':
                componente.config(text='0')

            self.ventanas.componentes_forma[nombre] = componente

    def _agregar_validaciones(self):
        self.ventanas.agregar_validacion_tbx('tbx_clave', 'codigo_barras')

    def _obtener_ruta_imagenes_publitarias(self):
        ruta_windows = r'\\ccayal\Users\Administrador\Pictures\ClienteVentas'
        if not os.path.exists(ruta_windows):
            RUTA_BASE =  os.path.dirname(os.path.abspath(__file__))
            return os.path.join(RUTA_BASE, 'publicidad')
        return ruta_windows

    def _cargar_imagen_publicitaria(self):

        if self._modulo_id  in [1687]:
            return

        if not os.path.exists(self._PATH_IMAGENES_PUBLICITARIAS):
            print("Ruta inválida")
            return

        archivos = [
            f for f in os.listdir(self._PATH_IMAGENES_PUBLICITARIAS)
            if f.lower().endswith('.png')
        ]
        if not archivos:
            print("No hay imágenes")
            return

        ruta = os.path.join(self._PATH_IMAGENES_PUBLICITARIAS, random.choice(archivos))
        imagen = Image.open(ruta)

        self.label_imagen =  self.ventanas.componentes_forma['lbl_anuncio']
        self.label_imagen.update_idletasks()  # Forzar cálculo de tamaño
        largo = self.label_imagen.winfo_width()
        alto = self.label_imagen.winfo_height()

        if largo <= 1 or alto <= 1:
            print(f"Tamaño inválido ({largo}x{alto}), reintentando...")
            return

        # Redimensionar y mostrar
        imagen = imagen.resize((largo+100, alto), Image.Resampling.LANCZOS)
        self.imagen_publicitaria = ImageTk.PhotoImage(imagen)
        self.label_imagen.configure(image=self.imagen_publicitaria)

    def _ajustar_componentes_forma(self):
        self.ventanas.ajustar_componente_en_frame('tbx_cliente', 'frame_cliente')
        self.ventanas.ajustar_componente_en_frame('tbx_direccion', 'frame_cliente')
        self.ventanas.ajustar_componente_en_frame('tbx_comentario', 'frame_cliente')
        self.ventanas.ajustar_componente_en_frame('txt_comentario_documento', 'frame_comentario')
        self.ventanas.ajustar_label_en_frame('lbl_anuncio', 'frame_anuncio')

    def _cargar_captura_manual(self):
        if self._modulo_id  in [1687]:
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

            'frame_anuncio': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_buscar_manual' : ('frame_anuncio', 'Búsqueda',
                       {'row': 0, 'column': 0, 'columnspan': 4, 'pady': 2, 'padx': 2, 'sticky': tk.NSEW}),

            'frame_tbx_buscar_manual' : ('frame_buscar_manual', None,
                                       {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2, 'sticky': tk.NS}),

            'frame_cbx_buscar_manual' : ('frame_buscar_manual', None,
                                       {'row': 0, 'column': 3, 'columnspan': 2, 'pady': 2, 'padx': 2, 'sticky': tk.NS}),

            'frame_partida_manual' : ('frame_anuncio', 'Partida:',
                                    {'row': 2, 'column': 0, 'columnspan': 4, 'pady': 2, 'padx': 2, 'sticky': tk.NSEW}),



            'frame_detalles_partida_manual' : ('frame_partida_manual', 'Detalles:',
                                       {'row': 0, 'column': 0,  'columnspan': 4, 'pady': 2, 'padx': 2, 'sticky': tk.NSEW}),



            'frame_cantida_y_equivalencia': ('frame_detalles_partida_manual', 'Cantidad:',
                                        {'row': 0, 'column': 0,  'columnspan': 2, 'pady': 2, 'padx': 2,
                                         'sticky': tk.W}),

            'frame_totales_manual': ('frame_detalles_partida_manual', 'Total pieza:',
                                     {'row': 0, 'column': 2, 'columnspan': 2, 'rowspan': 2, 'pady': 2, 'padx': 2,
                                      'sticky': tk.NSEW}),


            'frame_controles_manual' : ('frame_detalles_partida_manual', None,
                                      {'row': 1, 'column': 0,  'columnspan': 2, 'pady': 2, 'padx': 2, 'sticky': tk.NSEW}),

            'frame_txt_comentario_manual' : ('frame_partida_manual', 'Especificación:',
                                           {'row': 6, 'column': 0, 'columnspan': 4, 'pady': 2, 'padx': 2, 'sticky': tk.NSEW}),

            'frame_txt_portapapeles_manual' : ('frame_partida_manual', 'Portapapeles:',
                                             {'row': 7, 'column': 0, 'columnspan': 4, 'pady': 2, 'padx': 2, 'sticky': tk.NSEW}),

            'frame_botones_manual' : ('frame_partida_manual', None,
                                    {'row': 11, 'column': 1, 'padx': 0, 'pady': 5, 'sticky': tk.W}),

            'frame_tabla_manual': ('frame_anuncio', 'Productos ',
                                   {'row': 3, 'column': 0, 'columnspan': 4, 'pady': 2, 'padx': 2, 'sticky': tk.NSEW})
        }
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
                'btn_copiar_manual': '[F12]',
            }

            return _atajos_botones[nombre_boton]

        componentes = {
            'cbx_tipo_busqueda': ('frame_cbx_buscar_manual', None, 'Tipo:', None),
            'tbx_buscar_manual': ('frame_tbx_buscar_manual', None, 'Buscar:', None),

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
                                      {'text': 'CLAVE 000000', 'style': 'inverse-danger', 'anchor': 'center',
                                       'font': ('Consolas', tamano_fuente, 'bold')},
                                      {'row': 3, 'columnspan': 2, 'column': 0, 'padx': 0, 'sticky': tk.NSEW},
                                      None),

            'chk_pieza_manual': ('frame_controles_manual',
                          {'row': 0, 'column': 3, 'pady': 5, 'padx': 5, 'sticky': tk.W},
                          'Pieza', None),

            'chk_monto_manual': ('frame_controles_manual',
                          {'row': 0, 'column': 5, 'pady': 5, 'padx': 5, 'sticky': tk.W},
                          'Monto', None),

            'tvw_productos_manual': ('frame_tabla_manual', self._crear_columnas_tabla_manual(), 5, None),
            'btn_agregar_manual': ('frame_botones_manual', 'success', 'Agregar',
                                   atajos_botones(ancho, 'btn_agregar_manual')),
            'btn_especificaciones_manual': ('frame_botones_manual', 'primary', 'Especificación',
                                            atajos_botones(ancho, 'btn_especificaciones_manual')),
            'btn_ofertas_manual': ('frame_botones_manual', 'info', 'Ofertas',
                                   atajos_botones(ancho, 'btn_ofertas_manual')),
            'btn_copiar_manual': ('frame_botones_manual', 'warning', 'Copiar',
                                  atajos_botones(ancho, 'btn_copiar_manual')),

        }

        self.ventanas.crear_componentes(componentes)
        self.ventanas.ajustar_ancho_componente('cbx_tipo_busqueda',15)
        self.ventanas.ajustar_ancho_componente('tbx_buscar_manual', 15)
        self.ventanas.ajustar_ancho_componente('tbx_equivalencia_manual', 6)

        self.ventanas.ajustar_componente_en_frame('txt_comentario_manual', 'frame_txt_comentario_manual')
        self.ventanas.ajustar_componente_en_frame('txt_portapapeles_manual', 'frame_txt_portapapeles_manual')
        self.ventanas.ajustar_alto_componente('txt_comentario_manual', alto_comentarios)
        self.ventanas.ajustar_alto_componente('txt_portapapeles_manual', alto_comentarios)

    def _crear_columnas_tabla_manual(self):

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
        ]
