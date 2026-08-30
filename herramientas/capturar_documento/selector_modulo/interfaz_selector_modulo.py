import tkinter as tk
from datetime import datetime

import ttkbootstrap as ttk
from cayal.ventanas import Ventanas


class InterfazSelectorModulo:
    MOSTRAR_FACTURAS_GLOBALES = False

    def __init__(self, master):
        self._master = master
        self.ventanas = Ventanas(self._master)


        self._crear_frames()
        self._crear_pestanas_herramientas()
        self._crear_encabezado()
        self._cargar_componentes()
        self._crear_barra_herramientas()
        self.ventanas.configurar_ventana_ttkbootstrap(
            'Captura de ventas'
        )
        # La configuración general deja los popups sin redimensionamiento.
        # Este panel necesita ocupar toda el área disponible para sus tablas.
        self._master.resizable(True, True)
        self._master.minsize(1000, 600)
        self._master.after_idle(self._maximizar)
        # En Windows el primer zoom puede ejecutarse antes de que la ventana
        # esté completamente mapeada; el segundo asegura el estado final.
        self._master.after(250, self._maximizar)

    def _crear_frames(self):
        self._master.rowconfigure(0, weight=1)
        self._master.columnconfigure(0, weight=1)
        frames = {
            'frame_principal': (
                'master',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW}
            ),

            'frame_herramientas': (
                'frame_principal',
                'Herramientas',
                {'row': 1, 'column': 0, 'padx': 8, 'pady': 4, 'sticky': tk.EW}
            ),

            'frame_notebook': (
                'frame_principal',
                'Ventas',
                {'row': 2, 'column': 0, 'padx': 8, 'pady': 4, 'sticky': tk.NSEW}
            ),
        }

        self.ventanas.crear_frames(frames)

        frame_principal = self.ventanas.componentes_forma['frame_principal']
        frame_principal.rowconfigure(2, weight=1)
        frame_principal.columnconfigure(0, weight=1)

        frame_notebook = self.ventanas.componentes_forma['frame_notebook']
        frame_notebook.rowconfigure(0, weight=1)
        frame_notebook.columnconfigure(0, weight=1)

    def _crear_pestanas_herramientas(self):
        frame_herramientas = self.ventanas.componentes_forma[
            'frame_herramientas'
        ]
        frame_herramientas.columnconfigure(0, weight=1)

        self.notebook_herramientas = self.ventanas.crear_notebook(
            nombre_notebook='nbk_herramientas',
            info_pestanas={
                'tab_herramientas_generales': ('Generales', None),
                'tab_herramientas_timbrado': ('Timbrado', None),
                'tab_herramientas_administracion': ('Administración', None),
            },
            nombre_frame_padre='frame_herramientas',
            config_notebook={
                'row': 0,
                'column': 0,
                'sticky': tk.EW,
                'padx': 5,
                'pady': 3,
                'bootstyle': 'primary',
            },
        )

        self.frames_barra_herramientas = {
            'generales': 'tab_herramientas_generales',
            'timbrado': 'tab_herramientas_timbrado',
            'administracion': 'tab_herramientas_administracion',
        }

    def _crear_encabezado(self):
        principal = self.ventanas.componentes_forma['frame_principal']
        encabezado = ttk.Frame(principal, padding=(14, 9), bootstyle='danger')
        encabezado.grid(row=0, column=0, sticky=tk.EW)
        encabezado.columnconfigure(1, weight=1)

        self.var_titulo = tk.StringVar(
            value='CAPTURA DE VENTAS MINISUPER'
        )
        ttk.Label(
            encabezado,
            textvariable=self.var_titulo,
            font=('Consolas', 18, 'bold'),
            bootstyle='inverse-danger',
        ).grid(row=0, column=0, sticky=tk.W)
        self.var_estado = tk.StringVar(value='Preparando documentos...')
        ttk.Label(
            encabezado,
            textvariable=self.var_estado,
            font=('Consolas', 10, 'bold'),
            bootstyle='inverse-danger',
        ).grid(row=0, column=1, padx=20, sticky=tk.E)

    def _maximizar(self):
        if not self._master.winfo_exists():
            return
        self._master.resizable(True, True)
        self._master.update_idletasks()
        try:
            self._master.wm_state('zoomed')
        except tk.TclError:
            try:
                self._master.attributes('-zoomed', True)
            except tk.TclError:
                ancho = int(self._master.winfo_screenwidth() * 0.96)
                alto = int(self._master.winfo_screenheight() * 0.90)
                self._master.geometry(f'{ancho}x{alto}+0+0')

    def mostrar_estado(self, mensaje):
        hora = datetime.now().strftime('%H:%M:%S')
        self.var_estado.set(f'{mensaje} · {hora}')

    def actualizar_titulo_usuario(self, user_name):
        usuario = str(user_name or '').strip()
        titulo = 'CAPTURA DE VENTAS MINISUPER'
        if usuario:
            titulo = f'{titulo}, USUARIO: {usuario}'
        self.var_titulo.set(titulo)

    def _calcular_filas_tabla(self):
        """Reserva espacio para búsqueda y navegación con cualquier DPI."""
        alto_pantalla = self._master.winfo_screenheight()
        try:
            escala = float(self._master.tk.call('tk', 'scaling'))
        except (tk.TclError, TypeError, ValueError):
            escala = 96 / 72

        factor_dpi = max(1.0, escala / (96 / 72))
        alto_reservado = int(300 * factor_dpi)
        alto_fila = max(22, int(16 * escala))
        filas = int((alto_pantalla - alto_reservado) / alto_fila)
        return max(8, min(26, filas))

    def actualizar_contador_tabla(self, tabla, cantidad):
        configuracion = {
            'tbv_tickets': ('tab_tickets', 'Tickets 🧾'),
            'tbv_facturas': ('tab_facturas', 'Facturas 📄'),
            'tbv_facturas_globales': (
                'tab_facturas_globales', 'Facturas globales 🌐'
            ),
            'tbv_depositos': ('tab_depositos', 'Depósitos 💰'),
            'tbv_cortes': ('tab_cortes', 'Cortes de caja 🧮'),
        }
        datos = configuracion.get(tabla)
        if not datos:
            return
        nombre_tab, texto = datos
        tab = self.ventanas.componentes_forma.get(nombre_tab)
        if tab is not None:
            self.notebook.tab(tab, text=f'{texto} ({cantidad})')

    def _cargar_componentes(self):
        filas_tabla = self._calcular_filas_tabla()
        info_pestanas = {
            'tab_tickets': ('Tickets 🧾', None),
            'tab_facturas': ('Facturas 📄', None),
            'tab_facturas_globales': ('Facturas globales 🌐', None),
            'tab_depositos': ('Depósitos 💰', None),
            'tab_cortes': ('Cortes de caja 🧮', None),
        }

        self.nombre_notebook = 'nbk_ventas'

        self.notebook = self.ventanas.crear_notebook(
            nombre_notebook=self.nombre_notebook,
            info_pestanas=info_pestanas,
            nombre_frame_padre='frame_notebook',
            config_notebook={
                'row': 0,
                'column': 0,
                'sticky': tk.NSEW,
                'padx': 5,
                'pady': 5,
                'bootstyle': 'primary',
            }
        )

        frames_tabs = {
            'frm_tickets': (
                'tab_tickets',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            ),

            'frm_facturas': (
                'tab_facturas',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            ),

            'frm_facturas_globales': (
                'tab_facturas_globales',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            ),

            'frm_depositos': (
                'tab_depositos',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            ),

            'frm_cortes': (
                'tab_cortes',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            ),
        }

        self.ventanas.crear_frames(frames_tabs)

        frame_tickets = self.ventanas.componentes_forma['frm_tickets']
        frame_facturas = self.ventanas.componentes_forma['frm_facturas']
        frame_facturas_globales = self.ventanas.componentes_forma[
            'frm_facturas_globales'
        ]
        frame_depositos = self.ventanas.componentes_forma['frm_depositos']
        frame_cortes = self.ventanas.componentes_forma['frm_cortes']

        frame_tickets.rowconfigure(0, weight=1)
        frame_tickets.columnconfigure(0, weight=1)

        frame_facturas.rowconfigure(0, weight=1)
        frame_facturas.columnconfigure(0, weight=1)

        frame_facturas_globales.rowconfigure(0, weight=1)
        frame_facturas_globales.columnconfigure(0, weight=1)

        frame_depositos.rowconfigure(0, weight=1)
        frame_depositos.columnconfigure(0, weight=1)

        frame_cortes.rowconfigure(0, weight=1)
        frame_cortes.columnconfigure(0, weight=1)

        self.ventanas.crear_table_view(
            nombre='tbv_tickets',
            frame='frm_tickets',
            columnas=[],
            filas=filas_tabla,
            stripecolor=True
        )

        self.ventanas.crear_table_view(
            nombre='tbv_facturas',
            frame='frm_facturas',
            columnas=[],
            filas=filas_tabla,
            stripecolor=True
        )

        self.ventanas.crear_table_view(
            nombre='tbv_facturas_globales',
            frame='frm_facturas_globales',
            columnas=[],
            filas=filas_tabla,
            stripecolor=True
        )

        self.ventanas.crear_table_view(
            nombre='tbv_depositos',
            frame='frm_depositos',
            columnas=[],
            filas=filas_tabla,
            stripecolor=True
        )

        self.ventanas.crear_table_view(
            nombre='tbv_cortes',
            frame='frm_cortes',
            columnas=[],
            filas=filas_tabla,
            stripecolor=True
        )

        if not self.MOSTRAR_FACTURAS_GLOBALES:
            tab_facturas_globales = self.ventanas.componentes_forma.get(
                'tab_facturas_globales'
            )
            if tab_facturas_globales is not None:
                self.notebook.hide(tab_facturas_globales)

    def _crear_barra_herramientas(self):

        self.barra_herramientas = [
            {
                'nombre_icono': 'HeaderFooter32.ico',
                'etiqueta': 'Ticket',
                'nombre': 'nuevo_ticket',
                'hotkey': '[F2]',
                'comando': None
            },
            {
                'nombre_icono': 'Invoice32.ico',
                'etiqueta': 'Factura',
                'nombre': 'nueva_factura',
                'hotkey': '[F3]',
                'comando': None
            },

            {
                'nombre_icono': 'CFD.ico',
                'etiqueta': 'Timbrar',
                'nombre': 'timbrar',
                'seccion': 'timbrado',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'DocRelacionados.ico',
                'etiqueta': 'CFDI relacionados',
                'nombre': 'cfdi_relacionados',
                'seccion': 'timbrado',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'AddendaFieldRefRefresh.ico',
                'etiqueta': 'Intercambiar RFC',
                'nombre': 'intercambiar_rfc',
                'seccion': 'timbrado',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'Mail.ico',
                'etiqueta': 'Enviar correos',
                'nombre': 'enviar_correos',
                'seccion': 'timbrado',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'CopyToInvoice32.ico',
                'etiqueta': 'Convertir docto',
                'nombre': 'convertir_documento',
                'hotkey': '',
                'comando': None
            },

            {
                'nombre_icono': 'Payments32.ico',
                'etiqueta': 'Cartera',
                'nombre': 'cobrar_cartera',
                'hotkey': '[F6]',
                'comando': None
            },
            {
                'nombre_icono': 'Refresh32.ico',
                'etiqueta': 'Actualizar',
                'nombre': 'actualizar',
                'hotkey': '[F5]',
                'comando': None
            },

            {
                'nombre_icono': 'Print32.ico',
                'etiqueta': 'Imprimir',
                'nombre': 'imprimir',
                'hotkey': '[Ctrl+P]',
                'comando': None
            },
            {
                'nombre_icono': 'FormOfPayment32.ico',
                'etiqueta': 'Cobro Rápido',
                'nombre': 'cobro_rapido',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'Barcode32.ico',
                'etiqueta': 'Verificador',
                'nombre': 'verificador',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'DocumentEdit.ico',
                'etiqueta': 'E.Cliente',
                'nombre': 'editar_cliente',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'Deudor.ico',
                'etiqueta': 'Cliente',
                'nombre': 'capturar_cliente',
                'hotkey': '',
                'comando': None
            },


            {
                'nombre_icono': 'DeliveryConciliation.ico',
                'etiqueta': 'Editar generales',
                'nombre': 'editar_generales',
                'seccion': 'timbrado',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'Cut.ico',
                'etiqueta': 'Dividir',
                'nombre': 'dividir_documento',
                'hotkey': '',
                'comando': None
            },

            {
                'nombre_icono': 'CashRegister.ico',
                'etiqueta': 'Abrir cajón',
                'nombre': 'abrir_cajon',
                'hotkey': '[F7]',
                'comando': None
            },

            {
                'nombre_icono': 'Ingreso.ico',
                'etiqueta': 'Depósito',
                'nombre': 'nuevo_deposito',
                'hotkey': '[F4]',
                'comando': None
            },


            {
                'nombre_icono': 'warning.ico',
                'etiqueta': 'Queja',
                'nombre': 'agregar_queja',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'GlobalizeBuysToInvoice.ico',
                'etiqueta': 'Globalizar',
                'nombre': 'globalizar',
                'seccion': 'timbrado',
                'hotkey': '',
                'comando': None
            },

            {
                'nombre_icono': 'cortes_caja.ico',
                'etiqueta': 'Corte de caja',
                'nombre': 'nuevo_corte_caja',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'ActivitySector.ico',
                'etiqueta': 'Lista de precios',
                'nombre': 'listas_precios',
                'seccion': 'administracion',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'ActivitySector.ico',
                'etiqueta': 'Archivo Mayoreo',
                'nombre': 'archivo_mayoreo',
                'seccion': 'administracion',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'ActivitySector.ico',
                'etiqueta': 'Archivo Minisúper',
                'nombre': 'archivo_minisuper',
                'seccion': 'administracion',
                'hotkey': '',
                'comando': None
            },
            {
                'nombre_icono': 'ActivitySector.ico',
                'etiqueta': 'Archivo complementos',
                'nombre': 'archivo_complementos',
                'seccion': 'administracion',
                'hotkey': '',
                'comando': None
            },

        ]


    def obtener_tab_activa(self) -> dict:
        notebook = self.notebook

        tab_id = notebook.select()
        tab_texto = notebook.tab(tab_id, 'text')

        mapa_tabs = {
            'tab_tickets': {
                'frame': 'frm_tickets',
                'tabla': 'tbv_tickets',
                'texto': 'Tickets 🧾'
            },
            'tab_facturas': {
                'frame': 'frm_facturas',
                'tabla': 'tbv_facturas',
                'texto': 'Facturas 📄'
            },
            'tab_facturas_globales': {
                'frame': 'frm_facturas_globales',
                'tabla': 'tbv_facturas_globales',
                'texto': 'Facturas globales 🌐'
            },
            'tab_depositos': {
                'frame': 'frm_depositos',
                'tabla': 'tbv_depositos',
                'texto': 'Depósitos 💰'
            },
            'tab_cortes': {
                'frame': 'frm_cortes',
                'tabla': 'tbv_cortes',
                'texto': 'Cortes de caja 🧮'
            },
        }

        for nombre_tab, datos in mapa_tabs.items():
            frame_tab = self.ventanas.componentes_forma.get(nombre_tab)

            if str(frame_tab) == tab_id:
                return {
                    'tab': nombre_tab,
                    'frame': datos['frame'],
                    'tabla': datos['tabla'],
                    'texto': datos['texto']
                }

        return {
            'tab': None,
            'frame': None,
            'tabla': None,
            'texto': tab_texto
        }

    def obtener_tabla_activa(self):
        tab_activa = self.obtener_tab_activa()
        nombre_tabla = tab_activa['tabla']

        if not nombre_tabla:
            return None

        return nombre_tabla

    def obtener_frame_activo(self):
        tab_activa = self.obtener_tab_activa()
        nombre_frame = tab_activa['frame']

        if not nombre_frame:
            return None

        return nombre_frame
