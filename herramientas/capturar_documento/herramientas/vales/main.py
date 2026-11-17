"""Acceso desde Generales: selección de factura y captura valorizada por barcode."""
import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal

from cayal.ventanas import Ventanas

from .modelo import ModeloVales, moneda


class Vales:
    def __init__(self, master, parametros):
        self.master = master
        self.modelo = ModeloVales(parametros)
        self.factura = None
        self.partidas = []
        self.guardando = False
        self._validando_vale = False
        master.title('Vales de facturas anticipadas')
        master.geometry('1080x680')
        
        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(4, weight=2)
        encabezado = ttk.Frame(master, padding=8)
        encabezado.grid(row=0, column=0, sticky='ew')
        encabezado.grid_columnconfigure(1, weight=1)
        ttk.Label(encabezado, text='Factura anticipada:').grid(row=0, column=0, sticky='w')
        self.facturas = ttk.Combobox(encabezado, state='readonly', width=75)
        self.facturas.grid(row=0, column=1, padx=8, sticky='ew')
        self.facturas.bind('<<ComboboxSelected>>', self.seleccionar)
        ttk.Button(encabezado, text='Actualizar', command=self.actualizar).grid(row=0, column=2)
        formulario = ttk.LabelFrame(master, text='Información de la factura', padding=12)
        formulario.grid(row=1, column=0, padx=8, pady=(0, 4), sticky='ew')
        formulario.grid_columnconfigure(1, weight=1)
        formulario.grid_columnconfigure(3, weight=1)
        self.campos_factura = {}
        for indice, nombre in enumerate((
                'Factura', 'Cliente', 'Pedido', 'Lista de precios',
                'Total factura', 'Importe surtido', 'Vales autorizados',
                'Vales aplicados', 'Vales pendientes', 'Saldo disponible')):
            fila, columna = divmod(indice, 2)
            columna *= 2
            ttk.Label(formulario, text=nombre + ':').grid(
                row=fila, column=columna, padx=(0, 8), pady=4, sticky='w',
            )
            variable = tk.StringVar(master=master, value='')
            self.campos_factura[nombre] = variable
            ttk.Entry(formulario, textvariable=variable, state='readonly').grid(
                row=fila, column=columna + 1, padx=(0, 16), pady=4, sticky='ew',
            )
        self.info = ttk.Label(master, text='Seleccione una factura con saldo y vales pendientes.', padding=8)
        self.info.grid(row=2, column=0, sticky='ew')
        captura = ttk.Frame(master, padding=8)
        captura.grid(row=3, column=0, sticky='ew')
        ttk.Label(captura, text='Número de vale:').pack(side='left')
        self.clave = ttk.Entry(captura, width=15)
        self.clave.pack(side='left', padx=8)
        self.clave.bind('<Return>', self.confirmar_numero_vale)
        self.clave.bind('<FocusOut>', self.validar_numero_vale)
        ttk.Label(captura, text='Código de barras:').pack(side='left')
        self.codigo = ttk.Entry(captura, width=32, state='disabled')
        self.codigo.pack(side='left', padx=8)
        self.codigo.bind('<Return>', self.capturar)
        self.agregar = ttk.Button(captura, text='Agregar', command=self.capturar, state='disabled')
        self.agregar.pack(side='left')
        self.detalle = self._tabla(4, (
            ('Clave', 120), ('Producto', 330), ('Cantidad', 95),
            ('Precio sin impuestos', 155), ('Importe con impuestos', 155),
        ))
        pie = ttk.Frame(master, padding=8)
        pie.grid(row=5, column=0, sticky='ew')
        ttk.Button(pie, text='Quitar seleccionado', command=self.quitar).pack(side='left')
        self.total = ttk.Label(pie, text='Total: $0.00', padding=8)
        self.total.pack(side='left')
        self.guardar_btn = ttk.Button(pie, text='Generar salida y aplicar vale', command=self.guardar, state='disabled')
        self.guardar_btn.pack(side='right')
        ttk.Button(pie, text='Cerrar', command=self.cerrar).pack(side='right', padx=8)
        master.protocol('WM_DELETE_WINDOW', self.cerrar)
        self.actualizar()
        master.after_idle(lambda: Ventanas(master).centrar_ventana_ttkbootstrap())

    def _tabla(self, fila, columnas):
        contenedor = ttk.Frame(self.master, padding=(8, 0))
        contenedor.grid(row=fila, column=0, sticky='nsew')
        contenedor.grid_columnconfigure(0, weight=1)
        contenedor.grid_rowconfigure(0, weight=1)
        tabla = ttk.Treeview(contenedor, columns=[c[0] for c in columnas], show='headings', selectmode='browse')
        for nombre, ancho in columnas:
            tabla.heading(nombre, text=nombre)
            tabla.column(nombre, width=ancho)
        barra = ttk.Scrollbar(contenedor, command=tabla.yview)
        tabla.configure(yscrollcommand=barra.set)
        tabla.grid(row=0, column=0, sticky='nsew')
        barra.grid(row=0, column=1, sticky='ns')
        return tabla

    def error(self, error):
        messagebox.showerror('Vales', str(error), parent=self.master)

    def actualizar(self):
        if self.partidas and not messagebox.askyesno('Vales', '¿Descartar la captura y actualizar las facturas?', parent=self.master):
            return
        self.factura = None
        self.partidas = []
        self._estado(False)
        self.facturas.set('')
        self.clave.delete(0, tk.END)
        self.codigo.delete(0, tk.END)
        self._mostrar_informacion()
        self.info.configure(text='Seleccione una factura con saldo y vales pendientes.')
        self.refrescar_partidas()
        try:
            self.consulta = self.modelo.facturas()
            self.mostrar_facturas()
        except Exception as error:
            self.consulta = []
            self.facturas.configure(values=())
            self.error(error)

    def mostrar_facturas(self):
        self.facturas.configure(values=tuple(
            f"{f['FolioFactura']} — {f['Empresa']} — Pedido {f.get('Pedido') or 'Sin pedido'} (ID {f['DocumentID']})"
            for f in self.consulta
        ))

    def _mostrar_informacion(self, factura=None, cliente=None):
        for variable in self.campos_factura.values():
            variable.set('')
        if factura is None:
            return
        cliente = cliente or {}
        datos = {
            'Factura': factura['FolioFactura'],
            'Cliente': factura['Empresa'],
            'Pedido': factura.get('Pedido') or '',
            'Lista de precios': cliente.get('CustomerTypeName') or cliente.get('CustomerTypeID', ''),
            'Total factura': f"${moneda(factura['TotalFactura']):,.2f}",
            'Importe surtido': f"${moneda(factura['Surtido']):,.2f}",
            'Vales autorizados': factura['NumeroVales'],
            'Vales aplicados': factura['Aplicados'],
            'Vales pendientes': factura['Pendientes'],
            'Saldo disponible': f"${moneda(factura['Saldo']):,.2f}",
        }
        for nombre, valor in datos.items():
            self.campos_factura[nombre].set('' if valor is None else str(valor))

    def _estado(self, habilitado):
        estado = 'normal' if habilitado else 'disabled'
        for widget in (self.codigo, self.agregar, self.guardar_btn):
            widget.configure(state=estado)

    def seleccionar(self, _evento=None):
        indice = self.facturas.current()
        if self.guardando or indice < 0 or indice >= len(self.consulta):
            return
        nueva = self.consulta[indice]
        if self.factura and nueva['DocumentID'] == self.factura['DocumentID']:
            return
        if self.partidas and not messagebox.askyesno('Vales', '¿Descartar los productos y cambiar de factura?', parent=self.master):
            if self.factura:
                anterior = next(i for i, f in enumerate(self.consulta)
                                if f['DocumentID'] == self.factura['DocumentID'])
                self.facturas.current(anterior)
            return
        self.factura = None
        self.partidas = []
        self.clave.delete(0, tk.END)
        self._estado(False)
        self.refrescar_partidas()
        self._mostrar_informacion(nueva)
        try:
            self.modelo.validar_disponibilidad(nueva)
            cliente = self.modelo.cliente(nueva)
            self.factura = nueva
            self.refrescar_partidas()
            self._mostrar_informacion(nueva, cliente)
            self.info.configure(text='Factura seleccionada. Capture el número de vale y los productos.')
            self._estado(True)
            self.clave.focus_set()
        except Exception as error:
            self.info.configure(text='Factura no disponible para surtir.')
            self.error(error)

    def validar_numero_vale(self, _evento=None):
        """Muestra el aviso en la pantalla sin bloquear ni modificar el foco."""
        if self._validando_vale or self.guardando or not self.factura:
            return
        clave = self.clave.get().strip()
        if not clave:
            self.info.configure(text='Capture el número de vale y los productos.')
            return
        self._validando_vale = True
        try:
            self.modelo.validar_numero_vale(self.factura, clave)
        except Exception as error:
            self.info.configure(text=f'Aviso: {error}')
        else:
            self.info.configure(text=f'Vale {clave}: sin registro previo en esta factura.')
        finally:
            self._validando_vale = False

    def confirmar_numero_vale(self, _evento=None):
        self.validar_numero_vale()
        if self.factura and not self.guardando:
            self.codigo.focus_set()
        return 'break'

    def capturar(self, _evento=None):
        if not self.factura or self.guardando:
            return
        try:
            partida = self.modelo.capturar_codigo(self.codigo.get().strip(), self.factura)
            self.partidas.append(partida)
            self.refrescar_partidas()
        except Exception as error:
            self.error(error)
        finally:
            self.codigo.delete(0, tk.END)
            self.codigo.focus_set()

    def quitar(self):
        seleccion = self.detalle.selection()
        if seleccion and not self.guardando:
            self.partidas.pop(int(seleccion[0]))
            self.refrescar_partidas()

    def refrescar_partidas(self):
        self.detalle.delete(*self.detalle.get_children())
        for i, p in enumerate(self.partidas):
            self.detalle.insert('', 'end', iid=str(i), values=(
                p.get('ProductKey', ''), p['ProductName'], p['cantidad'],
                f"${moneda(p['precio']):,.2f}", f"${moneda(p['total']):,.2f}",
            ))
        total = moneda(sum((p['total'] for p in self.partidas), Decimal(0)))
        saldo = moneda(self.factura['Saldo']) - total if self.factura else Decimal(0)
        self.total.configure(text=f'Total: ${total:,.2f} | Saldo después del surtido: ${saldo:,.2f}')

    def guardar(self):
        if self.guardando or not self.factura:
            return
        self.guardando = True
        self._estado(False)
        try:
            folio = self.modelo.guardar(self.factura, self.clave.get(), self.partidas)
        except Exception as error:
            self.error(error)
            self._estado(True)
        else:
            messagebox.showinfo('Vales', f'Salida {folio} generada y vale registrado.', parent=self.master)
            self.partidas = []
            self.master.destroy()
        finally:
            self.guardando = False

    def cerrar(self):
        if self.guardando:
            return
        if not self.partidas or messagebox.askyesno('Vales', '¿Cerrar y descartar los productos capturados?', parent=self.master):
            self.master.destroy()
