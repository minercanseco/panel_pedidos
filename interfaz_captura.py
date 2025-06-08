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

    def _cargar_frames(self):

        frames = {

            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_herramientas': ('frame_principal', 'Herramientas',
                                   {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                    'sticky': tk.NSEW}),

            'frame_cliente': ('frame_principal', 'Cliente',
                              {'row': 1, 'column': 0, 'columnspan': 2, 'rowspan': 3, 'pady': 5, 'padx': 5, 'sticky': tk.NSEW}),

            'frame_totales': ('frame_principal', None,
                              {'row': 0, 'column': 2, 'rowspan': 2, 'columnspan': 4, 'pady': 5, 'padx': 5,
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

            'frame_anuncio': ('frame_principal', 'Anuncios',
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

        componentes = {
            'tbx_cliente': ('frame_cliente', None, 'Cliente:', None),
            'tbx_direccion': ('frame_cliente', None, 'Dirección:', None),
            'tbx_comentario': ('frame_cliente', None, 'Comentario:', None),
            'tbx_clave': ('frame_clave', None, None, None),
            'tvw_productos': ('frame_tabla', self.crear_columnas_tabla(), 15, None),
            'txt_comentario_documento': ('frame_comentario', None,'Comentarios:', None),
            'lbl_anuncio': ('frame_anuncio',
                               {'text': '', 'style': 'inverse-danger'},
                               {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                               None),
        }

        if self._modulo_id not in [1687]:
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

        self.ventanas.crear_componentes(componentes)

    def _cargar_componentes_frame_totales(self):
        ancho, alto = self.ventanas.obtener_resolucion_pantalla()

        tamano_fuente_titulo_1 = 16 if ancho > 1366 else 13
        tamano_fuente_titulo_2 = 29 if ancho > 1366 else 26

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

    def crear_columnas_tabla(self):

        return [
            {"text": "Cantidad", "stretch": False, 'width': 70, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Piezas", "stretch": False, 'width': 70, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Código", "stretch": False, 'width': 110, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "Descripción", "stretch": False, 'width': 260, 'column_anchor': tk.W,
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