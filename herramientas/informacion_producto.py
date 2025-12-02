import tkinter as tk
import ttkbootstrap as ttk
import pyperclip
from cayal.ventanas import Ventanas
from PIL import Image, ImageTk


class InformacionProducto:

    def __init__(self, master, informacion):

        self._informacion = informacion

        self._ruta_imagen = self._informacion['PathImagen']
        image = Image.open(self._ruta_imagen)
        self._imagen = ImageTk.PhotoImage(image)

        self._master = master

        self._ventanas = Ventanas(self._master)
        self._componentes_forma = self._ventanas.componentes_forma

        self._cargar_componentes_forma()
        self._cargar_eventos_forma()
        self._cargar_info_componentes_forma()

        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Información')

    def _cargar_componentes_forma(self):

        frame_principal = ttk.LabelFrame(self._master, text='Información:')
        frame_principal.grid(row=0, column=0, pady=5, padx=5, sticky=tk.NSEW)

        frame_generales = ttk.Frame(frame_principal)
        frame_generales.grid(row=0, column=0, columnspan=2, pady=5, padx=5, sticky=tk.NSEW)

        frame_botones = ttk.Frame(frame_principal)
        frame_botones.grid(row=1, column=1, pady=5, padx=5, sticky=tk.NSEW)

        nombres_componentes = {
            'cvs_imagen': (frame_generales, 'Label', None),
            'tbx_producto': (frame_generales, 'Entry', None),
            'txt_caracteristicas': (frame_generales, 'Text', None),
            'txt_presentacion': (frame_generales, 'Text', None),
            'txt_preparacion': (frame_generales, 'Text', None),
            'txt_observaciones': (frame_generales, 'Text', None),
            'btn_copiar': (frame_botones, 'Button', 'primary'),
            'btn_imagen': (frame_botones, 'Button', 'warning'),
            'btn_cancelar': (frame_botones, 'Button', 'danger')
        }

        for i, (nombre, (frame, tipo, estado)) in enumerate(nombres_componentes.items()):
            etiqueta = nombre[4::].capitalize()

            if 'txt' in nombre:
                componente = ttk.Text(frame, width=50, height=4)

            if 'tbx' in nombre:
                componente = ttk.Entry(frame, width=50)

            if 'cvs' in nombre:
                componente = tk.Canvas(frame)
                componente.grid(row=0, column=1, padx=5, sticky=tk.W)

            if 'btn' in nombre:
                componente = ttk.Button(frame, text=etiqueta, style=estado)
                componente.grid(row=0, column=i, padx=5, pady=5, sticky=tk.W)

            if tipo not in ('Label', 'Button'):
                lbl = ttk.Label(frame, text=etiqueta)
                lbl.grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)

                componente.grid(row=i, column=1, padx=5, pady=5, sticky=tk.W)

            self._componentes_forma[nombre] = componente

    def _cargar_eventos_forma(self):

        btn_cancelar = self._componentes_forma['btn_cancelar']
        btn_cancelar.config(command=lambda: self._master.destroy())

        btn_copiar = self._componentes_forma['btn_copiar']
        btn_copiar.config(command=lambda: self._copiar_informacion())

        btn_imagen = self._componentes_forma['btn_imagen']
        btn_imagen.config(state='disabled', command=lambda: self._copiar_imagen_portapapeles())


    def _cargar_info_componentes_forma(self):

        def rellenar_text(nombre_text, valor):

            componete = self._componentes_forma[nombre_text]

            if 'txt' in nombre_text:
                componete.insert("1.0", valor)
            else:
                componete.insert(0, valor)

        rellenar_text('tbx_producto', self._informacion['ProductName'])
        rellenar_text('txt_caracteristicas', self._informacion['Caracteristicas'])
        rellenar_text('txt_presentacion', self._informacion['Presentacion'])
        rellenar_text('txt_preparacion', self._informacion['Preparacion'])
        rellenar_text('txt_observaciones', self._informacion['Observaciones'])

        canvas = self._componentes_forma['cvs_imagen']
        canvas.create_image(0, 0, anchor="nw", image=self._imagen)

    def _copiar_informacion(self):
        valores_etiquetas = {}

        for nombre, componente in self._componentes_forma.items():

            valor = ''
            if 'txt' in nombre:
                valor = componente.get("1.0", tk.END)

            if 'tbx' in nombre:
                valor = componente.get()

            valor = valor.strip()
            valores_etiquetas[nombre[4::]] = valor

        texto = f"Producto: {valores_etiquetas['producto']}\n\n" \
                f"Características: {valores_etiquetas['caracteristicas']}\n\n" \
                f"Presentación: {valores_etiquetas['presentacion']}\n\n" \
                f"Preparación: {valores_etiquetas['preparacion']}\n\n" \
                f"Observaciones: {valores_etiquetas['observaciones']}"

        pyperclip.copy(texto)

        self._master.destroy()

    def _copiar_imagen_portapapeles(self):

        # Abrir la imagen desde el disco
        imagen = Image.open(self._ruta_imagen)

        # Convertir la imagen a formato RGBA
        imagen_rgba = imagen.convert("RGBA")

        # Guardar la imagen temporalmente en formato PNG
        ruta_temporal = "temp.png"
        imagen_rgba.save(ruta_temporal, format="PNG")

        # Copiar la imagen al portapapeles
        clipboard.copy(imagen_rgba)

        # Eliminar la imagen temporal

        self._master.destroy()