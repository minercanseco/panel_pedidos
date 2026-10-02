import tkinter as tk

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
        {'text': 'Motivo', 'stretch': False, 'width': 180},
        {'text': 'Recuperado', 'stretch': False, 'width': 85},
        {'text': 'Comentario', 'stretch': False, 'width': 260},
    ]

    def __init__(self, master, modelo):
        self._master = master
        self._modelo = modelo
        self._ventanas = Ventanas(master)
        self._clientes = []
        self._crear_frames()
        self._crear_componentes()
        self._configurar_layout()
        self._cargar_eventos()
        self._ventanas.configurar_ventana_ttkbootstrap(
            titulo='Seguimiento a clientes',
            nombre_icono='Partner32.ico',
            bloquear=False,
        )
        self._master.geometry('1380x650')
        self._master.minsize(980, 520)
        self._consultar()

    def _crear_frames(self):
        self._ventanas.crear_frames({
            'frame_principal': (
                'master', None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW, 'padx': 8, 'pady': 8},
            ),
            'frame_filtros': (
                'frame_principal', 'Buscar clientes',
                {'row': 0, 'column': 0, 'sticky': tk.EW, 'pady': (0, 6)},
            ),
            'frame_estado_filtro': (
                'frame_filtros', None,
                {'row': 0, 'column': 2, 'sticky': tk.W, 'padx': (0, 8)},
            ),
            'frame_tabla': (
                'frame_principal', 'Clientes sin compra por más de 90 días',
                {'row': 1, 'column': 0, 'sticky': tk.NSEW},
            ),
            'frame_pie': (
                'frame_principal', None,
                {'row': 2, 'column': 0, 'sticky': tk.EW, 'pady': (6, 0)},
            ),
        })

    def _crear_componentes(self):
        self._ventanas.crear_componentes({
            'tbx_buscar': (
                'frame_filtros',
                {'row': 0, 'column': 1, 'sticky': tk.EW, 'padx': (0, 10)},
                'Buscar:', None,
            ),
        })
        self._ventanas.crear_componentes({
            'cbx_estado': ('frame_estado_filtro', None, 'Seguimiento:', None),
        })
        self._ventanas.crear_componentes({
            'btn_actualizar': ('frame_filtros', 'primary', 'Actualizar', None),
        })
        self._ventanas.componentes_forma['btn_actualizar'].grid_configure(
            row=0, column=3,
        )
        self._ventanas.rellenar_cbx(
            'cbx_estado',
            ('Todos', 'Pendientes', 'Con seguimiento', 'Recuperados'),
            sin_seleccione=True,
        )
        self._ventanas.crear_table_view(
            nombre='tbv_seguimiento_clientes',
            frame='frame_tabla',
            columnas=self.COLUMNAS,
            filas=22,
            stripecolor=True,
        )
        self._ventanas.habilitar_ordenamiento_table_view(
            'tbv_seguimiento_clientes'
        )
        self._ventanas.crear_componentes({
            'lbl_estado': ('frame_pie', None, '0 clientes', None),
            'btn_registrar': ('frame_pie', 'success', 'Registrar seguimiento', None),
            'btn_cerrar': ('frame_pie', 'danger', 'Cerrar', None),
        })

    def _configurar_layout(self):
        principal = self._ventanas.componentes_forma['frame_principal']
        filtros = self._ventanas.componentes_forma['frame_filtros']
        tabla = self._ventanas.componentes_forma['frame_tabla']
        pie = self._ventanas.componentes_forma['frame_pie']
        self._master.grid_rowconfigure(0, weight=1)
        self._master.grid_columnconfigure(0, weight=1)
        principal.grid_rowconfigure(1, weight=1)
        principal.grid_columnconfigure(0, weight=1)
        filtros.grid_columnconfigure(1, weight=1)
        tabla.grid_rowconfigure(0, weight=1)
        tabla.grid_columnconfigure(0, weight=1)
        pie.grid_columnconfigure(0, weight=1)
        self._ventanas.componentes_forma['lbl_estado'].grid_configure(
            row=0, column=0, sticky=tk.W,
        )
        self._ventanas.componentes_forma['btn_registrar'].grid_configure(
            row=0, column=1, padx=4,
        )
        self._ventanas.componentes_forma['btn_cerrar'].grid_configure(
            row=0, column=2, padx=(4, 0),
        )

    def _cargar_eventos(self):
        self._ventanas.cargar_eventos({
            'btn_actualizar': self._consultar,
            'cbx_estado': self._aplicar_filtros,
            'btn_registrar': self._abrir_seguimiento,
            'btn_cerrar': self._master.destroy,
            'tbv_seguimiento_clientes': (self._abrir_seguimiento, 'doble_click'),
        })
        buscar = self._ventanas.componentes_forma['tbx_buscar']
        buscar.bind('<KeyRelease>', self._aplicar_filtros)
        buscar.bind('<Escape>', self._limpiar_busqueda)
        self._master.bind('<F5>', self._consultar)
        self._master.bind('<Escape>', lambda _event: self._master.destroy())
        buscar.focus_set()

    def _limpiar_busqueda(self, _event=None):
        self._ventanas.limpiar_componentes('tbx_buscar')
        self._aplicar_filtros()

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
            'MotivoSeguimiento', 'ComentarioSeguimiento',
        )
        return ' '.join(str(cliente.get(campo) or '') for campo in campos).casefold()

    def _aplicar_filtros(self, _event=None):
        termino = self._ventanas.obtener_input_componente('tbx_buscar').strip().casefold()
        estado = self._ventanas.obtener_input_componente('cbx_estado')
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
        self._ventanas.insertar_input_componente(
            'lbl_estado', f'{len(clientes)} clientes mostrados',
        )

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
            ventana, self._modelo, seleccion[0], al_guardar=self._consultar,
        )
        ventana.wait_window()


class FormularioSeguimiento:
    def __init__(self, master, modelo, cliente, al_guardar):
        self._master = master
        self._modelo = modelo
        self._cliente = cliente
        self._al_guardar = al_guardar
        self._ventanas = Ventanas(master)
        self._motivos_por_nombre = {}
        self._crear_frames()
        self._crear_componentes()
        self._configurar_layout()
        self._cargar_eventos()
        self._cargar_motivos()

    def _crear_frames(self):
        self._ventanas.crear_frames({
            'frame_principal': (
                'master', None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW, 'padx': 12, 'pady': 12},
            ),
            'frame_botones': (
                'frame_principal', None,
                {'row': 5, 'column': 0, 'columnspan': 2, 'sticky': tk.E, 'pady': (12, 0)},
            ),
        })

    def _crear_componentes(self):
        self._ventanas.crear_componentes({
            'lbl_cliente_titulo': (
                'frame_principal', {'text': 'Cliente:'},
                {'row': 0, 'column': 0, 'sticky': tk.NW}, None,
            ),
            'lbl_cliente': (
                'frame_principal',
                {
                    'text': self._cliente.get('Cliente') or '',
                    'font': ('TkDefaultFont', 10, 'bold'),
                    'wraplength': 460,
                },
                {'row': 0, 'column': 1, 'sticky': tk.W, 'pady': (0, 8)}, None,
            ),
            'cbx_motivo': (
                'frame_principal', None, 'Motivo:', None,
            ),
            'txt_comentario': (
                'frame_principal', None, 'Comentarios:', None,
            ),
        })
        self._ventanas.ajustar_ancho_componente('txt_comentario', 65)
        self._ventanas.ajustar_alto_componente('txt_comentario', 7)
        self._ventanas.crear_componentes({
            'chk_recuperado': (
                'frame_principal', None, 'Se logró recuperar la compra', None,
            ),
        })
        self._ventanas.componentes_forma['chk_recuperado'].grid_configure(
            row=4, column=0, columnspan=2, sticky=tk.W,
        )
        self._ventanas.crear_componentes({
            'btn_guardar': ('frame_botones', 'success', 'Guardar', None),
            'btn_cancelar': ('frame_botones', 'danger', 'Cancelar', None),
        })

    def _configurar_layout(self):
        principal = self._ventanas.componentes_forma['frame_principal']
        principal.grid_columnconfigure(1, weight=1)
        self._master.grid_rowconfigure(0, weight=1)
        self._master.grid_columnconfigure(0, weight=1)
        self._master.resizable(False, False)

    def _cargar_eventos(self):
        self._ventanas.cargar_eventos({
            'btn_guardar': self._guardar,
            'btn_cancelar': self._master.destroy,
        })
        self._master.bind('<Escape>', lambda _event: self._master.destroy())

    def _cargar_motivos(self):
        try:
            motivos = self._modelo.obtener_motivos_seguimiento()
            self._motivos_por_nombre = {
                str(motivo['ItemValue']): int(motivo['ItemData'])
                for motivo in motivos
            }
            self._ventanas.rellenar_cbx(
                'cbx_motivo', self._motivos_por_nombre.keys(),
            )
            self._ventanas.enfocar_componente('cbx_motivo')
        except Exception as error:
            self._ventanas.mostrar_mensaje(
                f'No fue posible consultar los motivos de seguimiento:\n{error}'
            )
            self._master.destroy()

    def _guardar(self):
        motivo = self._ventanas.obtener_input_componente('cbx_motivo')
        motivo_id = self._motivos_por_nombre.get(motivo)
        if motivo_id is None:
            self._ventanas.mostrar_mensaje('Debe seleccionar un motivo de seguimiento.')
            return
        comentario = self._ventanas.obtener_input_componente(
            'txt_comentario'
        ).strip()
        if len(comentario) < 10:
            self._ventanas.mostrar_mensaje(
                'Explique el seguimiento con al menos 10 caracteres.'
            )
            return
        try:
            self._modelo.guardar_seguimiento_cliente(
                int(self._cliente['ID cliente']),
                motivo_id,
                comentario,
                bool(self._ventanas.obtener_input_componente('chk_recuperado')),
            )
            self._master.destroy()
            self._al_guardar()
        except Exception as error:
            self._ventanas.mostrar_mensaje(
                f'No fue posible guardar el seguimiento:\n{error}'
            )
