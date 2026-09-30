import tkinter as tk

import ttkbootstrap as ttk

from cayal.ventanas import Ventanas


class SeguimientoClientes:
    COLUMNAS = [
        {'text': 'ID cliente', 'stretch': False, 'width': 75},
        {'text': 'Última compra', 'stretch': False, 'width': 105},
        {'text': 'Días', 'stretch': False, 'width': 55},
        {'text': 'Cliente', 'stretch': False, 'width': 230},
        {'text': 'Ruta', 'stretch': False, 'width': 90},
        {'text': 'Folio', 'stretch': False, 'width': 85},
        {'text': 'Total', 'stretch': False, 'width': 90},
        {'text': 'Correo', 'stretch': False, 'width': 190},
        {'text': 'Tel. casa', 'stretch': False, 'width': 105},
        {'text': 'Celular', 'stretch': False, 'width': 105},
        {'text': 'Último seguimiento', 'stretch': False, 'width': 135},
        {'text': 'Atendió', 'stretch': False, 'width': 110},
        {'text': 'Recuperado', 'stretch': False, 'width': 85},
        {'text': 'Comentario', 'stretch': False, 'width': 260},
    ]

    def __init__(self, master, modelo):
        self._master = master
        self._modelo = modelo
        self._ventanas = Ventanas(master)
        self._clientes = []
        self._busqueda = tk.StringVar(value='')
        self._estado = tk.StringVar(value='Todos')

        self._crear_interfaz()
        self._ventanas.configurar_ventana_ttkbootstrap(
            titulo='Seguimiento a clientes',
            nombre_icono='Partner32.ico',
            bloquear=False,
        )
        self._master.geometry('1380x650')
        self._master.minsize(980, 520)
        self._consultar()

    def _crear_interfaz(self):
        principal = ttk.Frame(self._master, padding=8)
        principal.grid(row=0, column=0, sticky=tk.NSEW)
        self._master.grid_rowconfigure(0, weight=1)
        self._master.grid_columnconfigure(0, weight=1)
        principal.grid_rowconfigure(1, weight=1)
        principal.grid_columnconfigure(0, weight=1)

        filtros = ttk.LabelFrame(principal, text='Buscar clientes', padding=8)
        filtros.grid(row=0, column=0, sticky=tk.EW, pady=(0, 6))
        filtros.grid_columnconfigure(1, weight=1)
        ttk.Label(filtros, text='Buscar:').grid(row=0, column=0, padx=(0, 6))
        entrada = ttk.Entry(filtros, textvariable=self._busqueda)
        entrada.grid(row=0, column=1, sticky=tk.EW, padx=(0, 10))
        ttk.Label(filtros, text='Seguimiento:').grid(row=0, column=2, padx=(0, 6))
        estado = ttk.Combobox(
            filtros,
            textvariable=self._estado,
            values=('Todos', 'Pendientes', 'Con seguimiento', 'Recuperados'),
            state='readonly',
            width=17,
        )
        estado.grid(row=0, column=3, padx=(0, 8))
        ttk.Button(
            filtros, text='Actualizar', bootstyle='primary', command=self._consultar,
        ).grid(row=0, column=4)

        tabla = ttk.LabelFrame(principal, text='Clientes sin compra por más de 90 días')
        tabla.grid(row=1, column=0, sticky=tk.NSEW)
        tabla.grid_rowconfigure(0, weight=1)
        tabla.grid_columnconfigure(0, weight=1)
        self._ventanas.componentes_forma['frame_seguimiento_tabla'] = tabla
        self._ventanas.crear_table_view(
            nombre='tbv_seguimiento_clientes',
            frame='frame_seguimiento_tabla',
            columnas=self.COLUMNAS,
            filas=22,
            stripecolor=True,
        )
        self._ventanas.habilitar_ordenamiento_table_view(
            'tbv_seguimiento_clientes'
        )

        pie = ttk.Frame(principal)
        pie.grid(row=2, column=0, sticky=tk.EW, pady=(6, 0))
        pie.grid_columnconfigure(0, weight=1)
        self._lbl_estado = ttk.Label(pie, text='0 clientes')
        self._lbl_estado.grid(row=0, column=0, sticky=tk.W)
        ttk.Button(
            pie,
            text='Registrar seguimiento',
            bootstyle='success',
            command=self._abrir_seguimiento,
        ).grid(row=0, column=1, padx=4)
        ttk.Button(
            pie, text='Cerrar', bootstyle='danger', command=self._master.destroy,
        ).grid(row=0, column=2, padx=(4, 0))

        self._busqueda.trace_add('write', lambda *_args: self._aplicar_filtros())
        estado.bind('<<ComboboxSelected>>', self._aplicar_filtros)
        entrada.bind('<Escape>', lambda _event: self._busqueda.set(''))
        self._master.bind('<F5>', self._consultar)
        self._master.bind('<Escape>', lambda _event: self._master.destroy())
        tabla_view = self._ventanas.componentes_forma['tbv_seguimiento_clientes']
        tabla_view.bind('<Double-1>', self._abrir_seguimiento)
        entrada.focus_set()

    def _consultar(self, _event=None):
        try:
            self._clientes = self._modelo.buscar_clientes_sin_compra(90)
            self._aplicar_filtros()
        except Exception as error:
            self._ventanas.mostrar_mensaje(
                'No fue posible consultar el seguimiento a clientes. '
                'Verifique que el script de base de datos esté instalado.\n\n'
                f'{error}'
            )

    @staticmethod
    def _texto_busqueda(cliente):
        campos = (
            'BusinessEntityID', 'Cliente', 'TipoRuta', 'DocFolio',
            'Correo', 'TelCasa', 'TelCel', 'UsuarioSeguimiento',
            'ComentarioSeguimiento',
        )
        return ' '.join(str(cliente.get(campo) or '') for campo in campos).casefold()

    def _aplicar_filtros(self, _event=None):
        termino = self._busqueda.get().strip().casefold()
        estado = self._estado.get()
        clientes = []
        for cliente in self._clientes:
            recuperado = cliente.get('Recuperado') or 'Pendiente'
            if termino and termino not in self._texto_busqueda(cliente):
                continue
            if estado == 'Pendientes' and recuperado != 'Pendiente':
                continue
            if estado == 'Con seguimiento' and recuperado == 'Pendiente':
                continue
            if estado == 'Recuperados' and recuperado != 'Sí':
                continue
            clientes.append(cliente)

        self._ventanas.rellenar_table_view(
            'tbv_seguimiento_clientes', self.COLUMNAS, clientes,
        )
        self._lbl_estado.configure(text=f'{len(clientes)} clientes mostrados')

    def _abrir_seguimiento(self, _event=None):
        seleccion = self._ventanas.procesar_filas_table_view(
            'tbv_seguimiento_clientes', seleccionadas=True,
        )
        if not seleccion:
            self._ventanas.mostrar_mensaje('Debe seleccionar un cliente.')
            return
        ventana = self._ventanas.crear_popup_ttkbootstrap(
            titulo='Registrar seguimiento'
        )
        FormularioSeguimiento(
            ventana,
            self._modelo,
            seleccion[0],
            al_guardar=self._consultar,
        )
        ventana.wait_window()


class FormularioSeguimiento:
    def __init__(self, master, modelo, cliente, al_guardar):
        self._master = master
        self._modelo = modelo
        self._cliente = cliente
        self._al_guardar = al_guardar
        self._recuperado = tk.BooleanVar(value=False)
        self._crear_interfaz()

    def _crear_interfaz(self):
        principal = ttk.Frame(self._master, padding=12)
        principal.grid(row=0, column=0, sticky=tk.NSEW)
        principal.grid_columnconfigure(1, weight=1)
        ttk.Label(principal, text='Cliente:').grid(row=0, column=0, sticky=tk.NW)
        ttk.Label(
            principal,
            text=self._cliente.get('Cliente') or '',
            font=('TkDefaultFont', 10, 'bold'),
            wraplength=460,
        ).grid(row=0, column=1, sticky=tk.W, pady=(0, 8))
        ttk.Label(principal, text='Motivo / comentarios:').grid(
            row=1, column=0, columnspan=2, sticky=tk.W,
        )
        self._comentario = tk.Text(principal, width=65, height=7, wrap=tk.WORD)
        self._comentario.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=(4, 8))
        ttk.Checkbutton(
            principal,
            text='Se logró recuperar la compra',
            variable=self._recuperado,
            bootstyle='success-round-toggle',
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W)
        botones = ttk.Frame(principal)
        botones.grid(row=4, column=0, columnspan=2, sticky=tk.E, pady=(12, 0))
        ttk.Button(
            botones, text='Guardar', bootstyle='success', command=self._guardar,
        ).grid(row=0, column=0, padx=4)
        ttk.Button(
            botones, text='Cancelar', bootstyle='danger', command=self._master.destroy,
        ).grid(row=0, column=1, padx=4)
        self._master.bind('<Escape>', lambda _event: self._master.destroy())
        self._master.resizable(False, False)
        self._comentario.focus_set()

    def _guardar(self):
        comentario = self._comentario.get('1.0', tk.END).strip()
        if len(comentario) < 10:
            Ventanas(self._master).mostrar_mensaje(
                'Explique el motivo de no compra con al menos 10 caracteres.'
            )
            return
        try:
            self._modelo.guardar_seguimiento_cliente(
                int(self._cliente['ID cliente']),
                comentario,
                self._recuperado.get(),
            )
            self._master.destroy()
            self._al_guardar()
        except Exception as error:
            Ventanas(self._master).mostrar_mensaje(
                f'No fue posible guardar el seguimiento:\n{error}'
            )
