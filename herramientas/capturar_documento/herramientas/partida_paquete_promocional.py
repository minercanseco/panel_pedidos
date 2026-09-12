import tkinter as tk
from decimal import Decimal, InvalidOperation
from tkinter import messagebox, simpledialog
from tkinter import ttk


class PartidaPaquetePromocional:
    """Captura todos los ingredientes de un paquete antes de venderlo."""

    def __init__(
            self, master, nombre_paquete, componentes, utilerias,
            resolver_producto_codigo):
        self.master = master
        self.componentes = [dict(componente) for componente in componentes]
        self.utilerias = utilerias
        self.resolver_producto_codigo = resolver_producto_codigo
        self.confirmado = False

        master.title(f'Capturar paquete - {nombre_paquete}')
        master.protocol('WM_DELETE_WINDOW', self.cancelar)

        frame_codigo = ttk.Frame(master)
        frame_codigo.grid(
            row=0, column=0, columnspan=2, padx=8, pady=(8, 2),
            sticky=tk.EW,
        )
        ttk.Label(frame_codigo, text='Código de barras:').grid(
            row=0, column=0, padx=(0, 6), sticky=tk.W,
        )
        self.codigo = ttk.Entry(frame_codigo)
        self.codigo.grid(row=0, column=1, sticky=tk.EW)
        frame_codigo.grid_columnconfigure(1, weight=1)

        columnas = ('Cantidad', 'Clave', 'Ingrediente', 'Unidad', 'Capturado')
        self.tabla = ttk.Treeview(
            master, columns=columnas, show='headings', height=14,
            selectmode='browse',
        )
        for columna in columnas:
            self.tabla.heading(columna, text=columna)
        self.tabla.column('Cantidad', width=90, anchor=tk.E)
        self.tabla.column('Clave', width=125)
        self.tabla.column('Ingrediente', width=310)
        self.tabla.column('Unidad', width=80)
        self.tabla.column('Capturado', width=95, anchor=tk.E)
        estilo = ttk.Style(master)
        estilo.map(
            'ComponentesPaquete.Treeview',
            background=[('selected', '#6B625A')],
            foreground=[('selected', '#FFFFFF')],
        )
        self.tabla.configure(style='ComponentesPaquete.Treeview')
        self.tabla.grid(
            row=1, column=0, columnspan=2, padx=8, pady=8,
            sticky='nsew',
        )
        self.tabla.tag_configure('capturado', background='#E8DED1')
        self.tabla.tag_configure('pendiente', background='#F2F0EC')

        ttk.Button(
            master, text='Capturar / editar', command=self.editar,
        ).grid(row=2, column=0, padx=8, pady=8, sticky=tk.W)
        ttk.Button(
            master, text='Aceptar paquete', command=self.aceptar,
        ).grid(row=2, column=1, padx=8, pady=8, sticky=tk.E)

        self.codigo.bind('<Return>', self.capturar_codigo)
        self.tabla.bind('<Double-1>', lambda _evento: self.editar())
        self.tabla.bind('<Return>', lambda _evento: self.editar())
        master.bind('<Escape>', lambda _evento: self.cancelar())
        master.grid_rowconfigure(1, weight=1)
        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=1)

        self._rellenar()
        self._seleccionar_primero()
        self.codigo.focus_set()

    @staticmethod
    def _decimal(valor):
        try:
            return Decimal(str(valor))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal('0')

    @staticmethod
    def cantidad_valida(cantidad, requerida, clave_unidad):
        if cantidad <= 0:
            return False
        if str(clave_unidad or '').strip().upper() == 'KGM':
            return True
        return cantidad == requerida

    @classmethod
    def componente_completo(cls, componente):
        cantidad = componente.get('SuppliedQuantity')
        if cantidad is None:
            return False
        return cls.cantidad_valida(
            cls._decimal(cantidad),
            cls._decimal(componente.get('RequiredQuantity')),
            componente.get('ClaveUnidad'),
        )

    def _rellenar(self):
        self.tabla.delete(*self.tabla.get_children())
        for indice, componente in enumerate(self.componentes):
            capturado = componente.get('SuppliedQuantity')
            self.tabla.insert(
                '', 'end', iid=str(indice),
                values=(
                    componente.get('RequiredQuantity', 0),
                    componente.get('ProductKey', ''),
                    componente.get('Description', ''),
                    componente.get('Unit', ''),
                    capturado if capturado is not None else 'Pendiente',
                ),
                tags=(
                    'capturado' if self.componente_completo(componente)
                    else 'pendiente',
                ),
            )

    def _seleccionar_primero(self):
        filas = self.tabla.get_children()
        if filas:
            self.tabla.selection_set(filas[0])
            self.tabla.focus(filas[0])
            self.tabla.focus_set()

    def _seleccionar_siguiente(self, indice):
        filas = list(self.tabla.get_children())
        orden = filas[indice + 1:] + filas[:indice + 1]
        siguiente = next(
            (fila for fila in orden
             if not self.componente_completo(self.componentes[int(fila)])),
            None,
        )
        if siguiente is None:
            self.aceptar()
            return
        self.tabla.selection_set(siguiente)
        self.tabla.focus(siguiente)
        self.tabla.see(siguiente)
        self.tabla.focus_set()

    def editar(self):
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        indice = int(seleccion[0])
        componente = self.componentes[indice]
        requerida = self._decimal(componente.get('RequiredQuantity'))
        actual = componente.get('SuppliedQuantity')
        if actual is None:
            actual = requerida
        captura = simpledialog.askstring(
            'Cantidad surtida',
            f"{componente.get('Description', '')}\n"
            f"Cantidad requerida: {requerida}\n"
            'Capture la cantidad surtida:',
            initialvalue=str(actual), parent=self.master,
        )
        if captura is None:
            self.tabla.focus_set()
            return
        cantidad = self._decimal(captura)
        unidad = componente.get('ClaveUnidad', '')
        if not self.cantidad_valida(cantidad, requerida, unidad):
            mensaje = (
                'La cantidad debe ser mayor que cero.'
                if str(unidad).strip().upper() == 'KGM'
                else 'Los ingredientes que no se venden por kilo deben '
                     'capturarse en su cantidad completa.'
            )
            messagebox.showwarning('Cantidad inválida', mensaje, parent=self.master)
            self.tabla.focus_set()
            return
        componente['SuppliedQuantity'] = cantidad
        self._rellenar()
        self._seleccionar_siguiente(indice)

    def capturar_codigo(self, _evento=None):
        codigo = self.codigo.get().strip()
        self.codigo.delete(0, tk.END)
        if not self.utilerias.es_codigo_barras(codigo):
            messagebox.showwarning(
                'Código inválido', 'Ha introducido un código de barras inválido.',
                parent=self.master,
            )
            self.codigo.focus_set()
            return

        valores = self.utilerias.validar_codigo_barras(codigo)
        cantidad = self._decimal(valores.get('cantidad'))
        product_id = self.resolver_producto_codigo(valores.get('clave'))
        coincidencias = [
            (indice, componente)
            for indice, componente in enumerate(self.componentes)
            if int(componente.get('ComponentProductID', 0) or 0)
               == int(product_id or 0)
        ]
        if not coincidencias:
            messagebox.showwarning(
                'Ingrediente no encontrado',
                'El producto leído no pertenece a este paquete.',
                parent=self.master,
            )
            self.codigo.focus_set()
            return
        if cantidad <= 0:
            messagebox.showwarning(
                'Cantidad inválida',
                'La cantidad contenida en el código debe ser mayor que cero.',
                parent=self.master,
            )
            self.codigo.focus_set()
            return

        indice, componente = coincidencias[0]
        actual = self._decimal(componente.get('SuppliedQuantity'))
        nueva = actual + cantidad
        requerida = self._decimal(componente.get('RequiredQuantity'))
        unidad = str(componente.get('ClaveUnidad') or '').strip().upper()
        if unidad != 'KGM' and nueva > requerida:
            messagebox.showwarning(
                'Cantidad excedida',
                f'La cantidad capturada no puede exceder {requerida}.',
                parent=self.master,
            )
            self.codigo.focus_set()
            return

        componente['SuppliedQuantity'] = nueva
        self._rellenar()
        if all(self.componente_completo(c) for c in self.componentes):
            self.aceptar()
            return
        self._seleccionar_siguiente(indice)
        self.codigo.focus_set()

    def aceptar(self):
        pendientes = [
            componente for componente in self.componentes
            if not self.componente_completo(componente)
        ]
        if pendientes:
            messagebox.showwarning(
                'Paquete incompleto',
                'Debe capturar todos los ingredientes antes de aceptar el paquete.',
                parent=self.master,
            )
            self._seleccionar_primero()
            return
        self.confirmado = True
        self.master.destroy()

    def cancelar(self):
        self.confirmado = False
        self.master.destroy()
