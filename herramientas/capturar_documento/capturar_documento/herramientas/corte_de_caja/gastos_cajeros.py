import tkinter as tk
from cayal.ventanas import Ventanas

class GastosCajeros:
    def __init__(self, master, parametros, base_de_datos, utilerias):
        self.gastos_capturados = []

        self._termino_buscado = None
        self._consulta_empleado = []

        self._master = master
        self._ventanas = Ventanas(self._master)
        self._parametros = parametros
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias

        self._crear_frames()
        self._crear_componentes()
        self._cargar_eventos()
        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Gastos cajeros')

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.W}),

            'frame_busqueda': ('frame_principal', 'Buscar',
                               {'row': 0, 'column': 0, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_componentes': ('frame_principal', 'Anticipos',
                                  {'row': 1, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_monto': ('frame_componentes', None,
                            {'row': 1, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_btn_monto': ('frame_monto', None,
                                {'row': 1, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_tabla': ('frame_componentes', None,
                            {'row': 3, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_botones': ('frame_principal', None,
                              {'row': 2, 'column': 0, 'pady': 5, 'sticky': tk.NSEW}),
        }
        self._ventanas.crear_frames(frames)

    def _crear_componentes(self):
        componentes = {
            'tbx_monto': ('frame_monto', None, 'Monto:', None),
            'btn_agregar': ('frame_btn_monto', 'Warning', 'Agregar', None),
            'btn_remover': ('frame_btn_monto', 'Danger', 'Remover', None),
            'tbx_buscar': ('frame_busqueda', None, 'Buscar:', None),
            'cbx_buscar': ('frame_busqueda', None, ' ', None),
            'tvw_gastos': ('frame_tabla', self._columnas_tabla(), None, None),
            'btn_guardar': ('frame_botones', 'Primary', 'Guardar', None),
            'btn_cancelar': ('frame_botones', 'Danger', 'Cancelar', None)
        }
        self._ventanas.crear_componentes(componentes)
        self._ventanas.agregar_validacion_tbx('tbx_monto', 'cantidad')

    def _columnas_tabla(self):
        return [
            {'text': 'Monto', "stretch": False, 'width': 60, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {'text': 'Receptor', "stretch": False, 'width': 200, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'BusinessEntityID', "stretch": False, 'width': 0, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 1},
        ]

    def _cargar_eventos(self):
        eventos = {
            'tbx_buscar': lambda event: self._buscar_cliente(),
            'btn_cancelar': self._master.destroy,
            'btn_guardar': self._procesar_gastos,
            'btn_agregar': self._agregar_gasto,
            'btn_remover': self._remover_gasto
        }
        self._ventanas.cargar_eventos(eventos)

    def _buscar_cliente(self, event=None):
        termino_buscado_tbx = self._ventanas.obtener_input_componente('tbx_buscar')

        if not termino_buscado_tbx:
            self._ventanas.mostrar_mensaje(master=self._master, mensaje='Debe introducir un termino a buscar')
            return

        if len(termino_buscado_tbx) < 5:
            self._ventanas.mostrar_mensaje(master=self._master, mensaje='Insuficientes letras en el termino a buscar')
            return

        if termino_buscado_tbx == self._termino_buscado:
            return

        self._termino_buscado = termino_buscado_tbx

        self._consulta_empleado = self._base_de_datos.fetchall("""
                        DECLARE @Valor NVARCHAR(255) = ?
                        SELECT E.BusinessEntityID,E.OfficialName
                        FROM zvwEmpleadosCayalMenu E
                        WHERE E.OfficialName LIKE '%'+@Valor+'%'
                """, (termino_buscado_tbx,))

        if not self._consulta_empleado:
            self._ventanas.mostrar_mensaje(master=self._master,
                                           mensaje='El término de búsqueda no arrojó resultados.')
            self._ventanas.limpiar_componentes('tbx_buscar')
            return

        nombres_de_clientes = [cliente['OfficialName'] for cliente in self._consulta_empleado]
        self._ventanas.rellenar_cbx('cbx_buscar', nombres_de_clientes, sin_seleccione=True)

    def _remover_gasto(self):
        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_gastos'):
            return

        filas = self._ventanas.obtener_seleccion_filas_treeview('tvw_gastos')
        if not filas:
            return

        for fila in filas:
            self._ventanas.remover_fila_treeview('tvw_gastos', fila)

    def _procesar_gastos(self):

        filas = self._ventanas.obtener_filas_treeview('tvw_gastos')
        if not filas:
            return

        for fila in filas:
            valores_fila = self._ventanas.procesar_fila_treeview('tvw_gastos', fila)
            monto_anticipo = self._utilerias.redondear_valor_cantidad_a_decimal(valores_fila['Monto'])
            receptor = valores_fila['Receptor']
            self.gastos_capturados.append(
                {
                    'receptor_gasto': receptor, 'monto_gasto': monto_anticipo
                }
            )

        self._master.destroy()

    def _agregar_gasto(self):
        receptor = self._ventanas.obtener_input_componente('cbx_buscar')
        if not receptor:
            self._ventanas.mostrar_mensaje('Debe buscar primero un receptor del gasto.')
            return

        monto = self._ventanas.obtener_input_componente('tbx_monto')
        if not monto:
            self._ventanas.mostrar_mensaje('Debe capturar un monto válido.')
            return

        if not self._utilerias.es_cantidad(monto):
            self._ventanas.mostrar_mensaje('Debe capturar un monto válido.')
            return

        monto_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(monto)
        if monto_decimal <= 0:
            self._ventanas.mostrar_mensaje('Debe introducir un valor válido.')
            return

        consulta = [reg['BusinessEntityID'] for reg in self._consulta_empleado
                    if reg['OfficialName'] == receptor]

        if consulta:
            business_entity_id = consulta[0]

            datos_fila = (monto_decimal, receptor, business_entity_id)
            self._ventanas.insertar_fila_treeview('tvw_gastos', datos_fila, al_principio=True)

            self._ventanas.limpiar_componentes(['tbx_buscar', 'tbx_monto'])