import os
import random

import tkinter as tk
import ttkbootstrap as ttk
from PIL import Image, ImageTk

from cayal.ventanas import Ventanas


class InterfazCaptura:
    def __init__(self, master, modulo_id):
        self.master = master
        self._modulo_id = modulo_id
        self.ventanas = Ventanas(self.master)
        self._PATH_IMAGENES_PUBLICITARIAS = r'\\ccayal\Users\Administrador\Pictures\ClienteVentas'

        self._cargar_frames()
        self._cargar_componentes_forma()
        self._cargar_imagen_publicitaria()
        self._cargar_componentes_frame_totales()

        self._ajustar_tamaño_componentes_forma()
        self._agregar_validaciones()



    def _cargar_frames(self):

        frames = {

            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_herramientas': ('frame_principal', 'Herramientas',
                                   {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                    'sticky': tk.NSEW}),

            'frame_cliente': ('frame_principal', 'Cliente',
                              {'row': 1, 'column': 0, 'columnspan': 2, 'pady': 5, 'padx': 5, 'sticky': tk.NSEW}),

            'frame_totales': ('frame_principal', None,
                              {'row': 0, 'column': 2, 'rowspan': 2, 'columnspan': 3, 'pady': 5, 'padx': 5,
                               'sticky': tk.NE}),

            'frame_captura': ('frame_principal', 'Captura',
                              {'row': 2, 'columnspan': 3, 'column': 0, 'pady': 5, 'padx': 5,
                               'sticky': tk.NS}),
            'frame_comentario': ('frame_principal', None,
                             {'row': 3, 'column': 0, 'columnspan': 3, 'pady': 5, 'padx': 5, 'sticky': tk.NSEW}
                             ),

            'frame_anuncio': ('frame_principal', 'Anuncios',
                              {'row': 2, 'rowspan': 2, 'column': 3, 'columnspan': 2, 'pady': 5, 'padx': 5,
                               'sticky': tk.NSEW}),
        }

        if self._modulo_id not in [1687]:
            frames.update({
                'frame_fiscal': ('frame_principal', None,
                                 {'row': 4, 'column': 0, 'columnspan': 3, 'pady': 5, 'padx': 5, 'sticky': tk.NSEW}
                                 )  # Cierra correctamente la tupla
            })  # Cierra correctamente el diccionario

        self.ventanas.crear_frames(frames)

    def _cargar_componentes_forma(self):
        componentes = {
            'tbx_cliente': ('frame_cliente',
                            {'row': 0, 'column': 0, 'columnspan': 5, 'sticky': tk.W, 'pady': 5, 'padx': 5},
                            None, 'Cliente:'),

            'tbx_direccion': ('frame_cliente',
                              {'row': 1, 'column': 0, 'columnspan': 5, 'sticky': tk.W, 'pady': 5, 'padx': 5},
                              None, 'Dirección:'),

            'tbx_comentario': ('frame_cliente',
                               {'row': 2, 'column': 0, 'columnspan': 5, 'sticky': tk.W, 'pady': 5, 'padx': 5},
                               None, 'Comentario:'),

            'tbx_clave': ('frame_captura', None, None, None),

            'tvw_productos': ('frame_captura', None, None, None),

            'txt_comentario_documento': ('frame_comentario',
                               {'row': 0, 'column': 0, 'columnspan': 5, 'sticky': tk.W, 'pady': 5, 'padx': 5},
                               None, 'Comentarios:'),

            'cvs_anuncio': ('frame_anuncio', None, None, None),
        }

        if self._modulo_id not in [1687]:
            componentes.update({
                'cbx_usocfdi': ('frame_fiscal', {'row': 0, 'column': 0, 'pady': 5, 'padx': 5}, None, None),

                'cbx_metodopago': ('frame_fiscal', {'row': 0, 'column': 2, 'pady': 5, 'padx': 5}, None, None),

                'cbx_formapago': ('frame_fiscal', {'row': 0, 'column': 4, 'pady': 5, 'padx': 5}, None, None),

                'cbx_regimen': ('frame_fiscal', {'row': 0, 'column': 6, 'pady': 5, 'padx': 5}, None, None),
            })

        for i, (nombre, (nombre_frame, info_grid, estilo, etiqueta)) in enumerate(componentes.items()):
            etiqueta = nombre[4::].capitalize() if not etiqueta else etiqueta
            tipo = nombre[0:3]
            frame = self.ventanas.componentes_forma[nombre_frame]

            if tipo == 'tbx':
                componente = ttk.Entry(frame)

            if tipo == 'txt':
                componente = ttk.Text(frame, width=47, height=2)

            if tipo == 'tvw':
                style = ttk.Style()
                style.configure("Treeview.Heading", font=("Roboto", 10)) #13
                style.configure("Treeview", font=("Consolas", 9)) #12

                componente = ttk.Treeview(master=frame,
                                          bootstyle='primary',
                                          columns=self.crear_columnas_tabla(),
                                          show='headings',
                                          height=20)

                self.ventanas.rellenar_treeview(componente, self.crear_columnas_tabla())

                componente.grid(row=i, column=0, columnspan=26, padx=5, pady=5, sticky=tk.W)

            if tipo == 'cbx':
                componente = ttk.Combobox(frame, state='readonly')

            if tipo == 'cvs':
                componente = tk.Canvas(frame, width=290, height=450)
                componente.grid(row=0, column=1, padx=5, sticky=tk.W)

            if tipo not in ('btn', 'tvw', 'cvs'):

                if not (info_grid and tipo in ('tbx', 'txt','cbx')):
                    lbl = ttk.Label(frame, text=etiqueta)
                    lbl.grid(row=i, column=0, pady=5, padx=5, sticky=tk.W)

                    componente.grid(row=i, column=1, padx=5, pady=5, sticky=tk.W)

                if info_grid and tipo in ('tbx', 'txt', 'cbx'):
                    lbl = ttk.Label(frame, text=etiqueta, width=12)
                    lbl.grid(row=info_grid["row"], column=info_grid["column"], pady=5, padx=5, sticky=tk.W)

                    info_grid["column"] = info_grid["column"] + 1
                    componente.grid(**info_grid)

            self.ventanas.componentes_forma[nombre] = componente

    def _cargar_componentes_frame_totales(self):

        estilo_auxiliar = {
            'foreground': 'white',
            'background': '#E30421',
            'font': ('Consolas', 16, 'bold'),
        }

        estilo_total = {
            'foreground': 'white',
            'background': '#E30421',
            'font': ('consolas', 29, 'bold'),
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
                lbl.config(font=('roboto', 16, 'bold'))
                lbl_texto = f'{nombre}_texto'

                self.ventanas.componentes_forma[lbl_texto] = lbl

            if nombre in ('lbl_credito', 'lbl_debe', 'lbl_restante', 'lbl_total'):
                componente.config(text='$ 0.00', font=('roboto', 20, 'bold'), anchor='e')

            if nombre == 'lbl_articulos':
                componente.config(text='0')

            self.ventanas.componentes_forma[nombre] = componente

    def _agregar_validaciones(self):
        self.ventanas.agregar_validacion_tbx('tbx_clave', 'codigo_barras')

    def _cargar_imagen_publicitaria(self):
        # Obtener la lista de archivos y seleccionar uno al azar
        if not os.path.exists(self._PATH_IMAGENES_PUBLICITARIAS):
            return

        # Filtrar solo archivos con extensión .png
        archivos = [
            archivo for archivo in os.listdir(self._PATH_IMAGENES_PUBLICITARIAS)
            if archivo.lower().endswith('.png')
        ]

        # Verificar si hay archivos válidos
        if not archivos:
            print("No hay imágenes PNG disponibles.")
            return

        # Seleccionar un archivo aleatorio
        archivo = random.choice(archivos)

        # Obtener la ruta completa de la imagen seleccionada
        ruta_imagen = os.path.join(self._PATH_IMAGENES_PUBLICITARIAS, archivo)

        # Cargar la imagen
        image = Image.open(ruta_imagen)

        # Obtener las dimensiones del Canvas
        self.cvs_anuncio = self.ventanas.componentes_forma['cvs_anuncio']
        self.cvs_anuncio.update_idletasks()  # Asegurarse de que el Canvas tiene el tamaño correcto
        canvas_width = self.cvs_anuncio.winfo_width()
        canvas_height = self.cvs_anuncio.winfo_height()

        # Redimensionar la imagen para que coincida con el tamaño del Canvas
        image = image.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)

        # Convertir la imagen redimensionada en un objeto PhotoImage
        self._imagen_publicitaria = ImageTk.PhotoImage(image)  # Mantener referencia en la clase

        # Mostrar la imagen en el Canvas
        self.cvs_anuncio.create_image(0, 0, anchor=tk.NW, image=self._imagen_publicitaria)

        # Actualizar el Canvas en el diccionario de componentes
        self.ventanas.componentes_forma['cvs_anuncio'] = self.cvs_anuncio

    def _ajustar_tamaño_componentes_forma(self):
        self.ventanas.ajustar_ancho_componente('tbx_cliente', 101)
        self.ventanas.ajustar_ancho_componente('tbx_direccion', 101)
        self.ventanas.ajustar_ancho_componente('tbx_comentario', 101)
        self.ventanas.ajustar_ancho_componente('txt_comentario_documento', 135)

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