import tkinter as tk
from cayal.ventanas import Ventanas


class FinalizarSurtido:
    def __init__(self, master, base_de_datos, utilerias):
        self._master = master
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._ventanas = Ventanas(self._master)

        self._hostname = self._utilerias.obtener_hostname()
        self.employee_user_id = 0
        self.employee_user_name = ''

        self._cargar_componentes()
        self._rellenar_tabla_empleados()
        self._cargar_eventos()

    def _cargar_eventos(self):
        eventos = {
            'btn_guardar': self._finalizar_surtido,
            'btn_cancelar': self._master.destroy

        }
        self._ventanas.cargar_eventos(eventos)

    def _finalizar_surtido(self):
        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_empleados'):
            return

        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_empleados')
        valores_fila = self._ventanas.procesar_fila_treeview('tvw_empleados', fila)

        employee_user_id = valores_fila['UserID']
        employee_user_name = valores_fila['Colaborador']
        self.employee_user_id = employee_user_id
        self.employee_user_name = employee_user_name
        self._master.destroy()

    def _cargar_componentes(self):
        componentes = [
            ('tvw_empleados', self._crear_columnas_tabla()),
            ('btn_guardar', 'Guardar')
        ]
        self._ventanas.crear_formulario_simple(componentes, titulo_frame_tabla='Colaboradores')

    def _crear_columnas_tabla(self):
        return [
            {"text": "Colaborador", "stretch": False, 'width': 265, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 0},
            {"text": "BusinessEntityID", "stretch": False, 'width': 80, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "EmployeeTypeID", "stretch": False, 'width': 80, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
            {"text": "UserID", "stretch": False, 'width': 0, 'column_anchor': tk.W,
             'heading_anchor': tk.W, 'hide': 1},
        ]

    def _rellenar_tabla_empleados(self):

        self._consulta_empleados = self._base_de_datos.fetchall(
            """
            SELECT 
            OfficialName, BusinessEntityID,	EmployeeTypeID,	UserID 
            FROM zvwEmpleadosCayalMenu
            ORDER BY OfficialName
            """,
            ()
        )
        self._ventanas.rellenar_treeview('tvw_empleados',
                                         self._crear_columnas_tabla(),
                                         self._consulta_empleados,
                                         valor_barra_desplazamiento=5
                                         )
