import tkinter as tk
import uuid
from cayal.ventanas import Ventanas


class AgregarCheque:
    def __init__(self, master, parametros, base_de_datos, utilerias, cheques_capturados):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._parametros = parametros
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias

        self.cheques_capturados = cheques_capturados

        self._termino_buscado = None
        self._consulta_clientes = []

        self._cargar_componentes()
        self._cargar_eventos()
        self._rellenar_tabla_cheques()
        self._ventanas.configurar_ventana_ttkbootstrap()

    def _cargar_componentes(self):
        componentes = [
            ('tbx_buscar', 'Buscar:'),
            ('cbx_clientes', 'Clientes:'),
            ('btn_guardar', 'Guardar'),
            ('tvw_cheques',self._crear_columnas())
        ]

        self._ventanas.crear_formulario_simple(componentes, titulo_frame_tabla='Cheques:')

        frame_adicional = {
            'frame_botones_tabla': ('frame_componentes', 'Agregar cheque:',
                          {'row': 3, 'column': 0, 'columnspan':2, 'pady': 5, 'padx': 5, 'sticky': tk.NSEW}
                          ),

            'frame_cbx_monto': ('frame_botones_tabla', None,
                                    {'row': 0, 'column': 0, 'columnspan':2, 'pady': 5, 'padx': 5, 'sticky': tk.W}
                                    ),
            'frame_btns_tabla': ('frame_botones_tabla', None,
                                {'row': 1, 'column': 1, 'pady': 5,  'padx': 5, 'sticky': tk.W}
                                ),
        }
        self._ventanas.crear_frames(frame_adicional)

        componentes_adicionales = {
            'tbx_monto': ('frame_cbx_monto', None, 'Monto:', None),
            'btn_agregar': ('frame_btns_tabla', 'Warning', 'Agregar', None),
            'btn_eliminar': ('frame_btns_tabla', 'Danger', 'Eliminar', None),
        }

        self._ventanas.crear_componentes(componentes_adicionales)
        self._ventanas.agregar_validacion_tbx('tbx_monto', 'cantidad')

    def _cargar_eventos(self):
        eventos = {
            'tbx_buscar': lambda event:self._buscar_cliente(),
            'btn_cancelar': self._master.destroy,
            'btn_guardar': self._actualizar_cheques,
            'btn_agregar': self._agregar_cheque_tabla,
            'btn_eliminar': self._eliminar_cheque
        }
        self._ventanas.cargar_eventos(eventos)

    def _eliminar_cheque(self):
        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_cheques'):
            return

        filas = self._ventanas.obtener_filas_treeview('tvw_cheques')
        for fila in filas:
            valores_fila = self._ventanas.procesar_fila_treeview('tvw_cheques', fila)
            uuid_tabla = valores_fila['UUID']

            self._ventanas.remover_fila_treeview('tvw_cheques', fila)

            cheques = [cheque for cheque in self.cheques_capturados if str(uuid_tabla) != str(cheque['UUID'])]

            self.cheques_capturados = cheques



    def _crear_columnas(self):
        columnas = [
            {'nombre': 'Total', 'ancho': 75, 'orientacion': 'izquierda', 'oculta': False},
            {'nombre': 'Cliente', 'ancho': 230, 'orientacion': 'izquierda', 'oculta': False},
            {'nombre': 'BusinessEntityID', 'ancho': 75, 'orientacion': 'izquierda', 'oculta': True},
            {'nombre': 'UUID', 'ancho': 75, 'orientacion': 'izquierda', 'oculta': True},

        ]
        return  self._ventanas.crear_columnas_tabla(columnas)

    def _actualizar_cheques(self):
        filas = self._ventanas.obtener_filas_treeview('tvw_cheques')

        if not filas:
            self.cheques_capturados = []
        else:
            for fila in filas:
                valores_filas = self._ventanas.procesar_fila_treeview('tvw_cheques', fila)
                if not self._existe_en_lista_cheques(valores_filas['UUID']):
                    self.cheques_capturados.append(valores_filas)

        self._master.destroy()

    def _buscar_cliente(self, event=None):

        termino_buscado = self._ventanas.obtener_input_componente('tbx_buscar')
        if not termino_buscado:
            self._ventanas.mostrar_mensaje('Debe introducir un termino a buscar')
            return

        if len(termino_buscado) < 5:
            self._ventanas.mostrar_mensaje('Insuficientes letras en el termino a buscar')
            return

        if termino_buscado == self._termino_buscado:
            return

        consulta = self._base_de_datos.buscar_clientes_por_nombre(termino_buscado)

        clientes = [cliente['OfficialName'] for cliente in consulta]

        self._ventanas.rellenar_cbx('cbx_clientes', clientes)
        self._consulta_clientes = consulta

    def _agregar_cheque_tabla(self):
        if not self._validar_inputs_cheque():
            return

        cliente = self._ventanas.obtener_input_componente('cbx_clientes')

        monto = self._ventanas.obtener_input_componente('tbx_monto')
        monto_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(monto)

        business_entity_id = [cliente['BusinessEntityID'] for cliente in self._consulta_clientes][0]

        self._ventanas.insertar_fila_treeview('tvw_cheques',
                                              (monto_decimal, cliente, business_entity_id, uuid.uuid4()),
                                              al_principio=True)

    def _existe_en_lista_cheques(self, uuid_tabla):
        uuid_lista = [uuid_id for uuid_id in self.cheques_capturados if str(uuid_tabla) == str(uuid_id['UUID'])]

        return  True if uuid_lista else False

    def _validar_inputs_cheque(self):
        cliente = self._ventanas.obtener_input_componente('cbx_clientes')

        if not cliente:
            self._ventanas.mostrar_mensaje('Debe buscar un cliente.')
            return

        if cliente == 'Seleccione':
            self._ventanas.mostrar_mensaje('Debe seleccionar un cliente.')
            return

        monto = self._ventanas.obtener_input_componente('tbx_monto')

        if not monto:
            self._ventanas.mostrar_mensaje('Debe capturar un monto.')
            return

        if not self._utilerias.es_cantidad(monto):
            self._ventanas.mostrar_mensaje('Monto inválido')
            return

        monto_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(monto)

        if monto_decimal <= 0:
            self._ventanas.mostrar_mensaje('Debe capturar un monto válido')
            return

        return True

    def _rellenar_tabla_cheques(self):
        if self.cheques_capturados:
            self._ventanas.rellenar_treeview('tvw_cheques',
                                             self._crear_columnas(),
                                             self.cheques_capturados,
                                             valor_barra_desplazamiento=5)