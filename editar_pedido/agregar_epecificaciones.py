import tkinter as tk
from cayal.ventanas import Ventanas


class AgregarEspecificaciones:
    def __init__(self, master, base_de_datos):
        self._master = master
        self._base_de_datos = base_de_datos
        self._ventanas = Ventanas(self._master)

        self.especificaciones_texto = ''
        self._especificaciones_seleccionadas = []
        self._consulta_especificaciones = []
        self._componentes = {}

        self._buscar_especificaciones()
        self._procesar_especificaciones()

        self._cargar_frames()
        self._cargar_componentes()
        self._cargar_eventos()
        self._ventanas.configurar_ventana_ttkbootstrap('Especificaciones')

    def _buscar_especificaciones(self):
        self._consulta_especificaciones = self._base_de_datos.fetchall(
            'SELECT Value FROM ProductOrdersSpecificationsCayal',
            ())

    def _procesar_especificaciones(self):
        especificaciones = [especificacion['Value'] for especificacion in self._consulta_especificaciones]
        especificaciones.sort()
        diccionario_especificaciones = {}

        for especificacion in especificaciones:
            nombre_especificacion = especificacion.lower()
            nombre_especificacion = nombre_especificacion.replace(' ', '_')
            nombre_componente = f'tck_{nombre_especificacion}'
            diccionario_especificaciones[nombre_componente] = especificacion

        columna = 0
        fila = 0

        for nombre_componente, etiqueta in diccionario_especificaciones.items():
            self._componentes[nombre_componente] = (
                'frame_principal',
                {'row': fila, 'column': columna, 'pady': 5, 'padx': 5, 'sticky': tk.W},
                etiqueta, None
            )
            fila += 1
            if fila == 10:
                fila = 0
                columna += 1

    def _cargar_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),
        }

        self._ventanas.crear_frames(frames)

    def _cargar_componentes(self):
        self._ventanas.crear_componentes(self._componentes)

    def _cargar_eventos(self):
        eventos = {}

        for nombre_componente in self._componentes.keys():
            eventos[nombre_componente] = lambda *args, nombre=nombre_componente: self._seleccionar_especificacion(
                nombre)

        self._ventanas.cargar_eventos(eventos)

    def _seleccionar_especificacion(self, nombre_componente, event=None):

        componente = self._ventanas.componentes_forma.get(nombre_componente, None)
        if componente:
            especificacion = componente.cget("text")
            if especificacion in self._especificaciones_seleccionadas:
                nuevas_especificaciones = [reg for reg in self._especificaciones_seleccionadas
                                           if reg != especificacion]
                self._especificaciones_seleccionadas = nuevas_especificaciones
            else:
                self._especificaciones_seleccionadas.append(especificacion)

            self._crear_texto_especificacion()

    def _crear_texto_especificacion(self):
        texto = ''
        numero = len(self._especificaciones_seleccionadas)
        for especificacion in self._especificaciones_seleccionadas:
            texto = f'{especificacion}' if numero == 1 else f'{texto} {especificacion},'
        texto = texto.strip()
        self.especificaciones_texto = texto
