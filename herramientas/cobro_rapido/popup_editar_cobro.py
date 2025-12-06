import tkinter as tk
from cayal.ventanas import  Ventanas


class ActualizarCobro:
    def __init__(self, master, parametros, base_de_datos, valores_fila):

        self.valores_fila = valores_fila
        self.actualizar_fila = False

        self._master = master
        self._ventanas = Ventanas(self._master)
        self._parametros = parametros
        self._base_de_datos = base_de_datos

        self._consulta_formas_pago = []
        self._consulta_terminales = []

        self._crear_frames()
        self._crear_componentes()
        self._cargar_eventos()
        self._rellenar_componentes()
        self._ventanas.configurar_ventana_ttkbootstrap("Actualizar cobro")
        self._master.lift()
        self._master.focus_force()

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),
            'frame_componentes': ('frame_principal', None,
                                   {'row': 0, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW}),
            'frame_terminal': ('frame_principal', None,
                                   {'row': 1, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW}),
            'frame_botones': ('frame_principal', None,
                                   {'row': 2, 'column': 1,  'sticky': tk.NSEW})
        }
        self._ventanas.crear_frames(info_frames=frames)

    def _crear_componentes(self):
        componentes = {
           'cbx_cobro': ('frame_componentes', None, 'F.Cobro', None),
           'cbx_terminal': ('frame_terminal', None, 'Terminal', None),
           'btn_actualizar': ('frame_botones', None, 'Actualizar', None),
            'btn_cancelar': ('frame_botones', 'Danger', 'Cancelar', None),
        }

        self._ventanas.crear_componentes(componentes)

    def _cargar_eventos(self):
        eventos = {
            'btn_actualizar': lambda: self._actualizar_tabla(),
            'btn_cancelar': lambda: self._master.destroy(),
            'cbx_cobro': lambda event: self._cambio_seleccion()
        }

        self._ventanas.cargar_eventos(eventos)

    def _rellenar_componentes(self):
        self._consulta_formas_pago = self._base_de_datos.buscar_formas_de_pago()
        formas_pago = [reg['Value'] for reg in self._consulta_formas_pago]
        self._ventanas.rellenar_cbx('cbx_cobro', formas_pago, sin_seleccione=True)

        self._consulta_terminales = self._base_de_datos.buscar_terminales_bancarias()
        barcodes = [reg['Barcode'] for reg in self._consulta_terminales]
        self._ventanas.rellenar_cbx('cbx_terminal', barcodes)

        self._cambio_seleccion()

    def _cambio_seleccion(self):
        seleccion = self._ventanas.obtener_input_componente('cbx_cobro')
        if seleccion[0:2] in ('28', '04'):
            self._ventanas.posicionar_frame('frame_terminal')
        else:
            self._ventanas.ocultar_frame('frame_terminal')

    def _buscar_metodo_pago_id(self, tipo_cobro):
        payment_method_id = [valor['ID'] for valor in self._consulta_formas_pago
                             if valor['Value'] == tipo_cobro]

        return int(payment_method_id[0])

    def _actualizar_tabla(self):

        forma_pago = self._ventanas.obtener_input_componente('cbx_cobro')
        barcode = self._ventanas.obtener_input_componente('cbx_terminal')

        if barcode == 'Seleccione' and forma_pago[0:2] in ('28', '04'):
            self._ventanas.mostrar_mensaje(master=self._master, mensaje='Debe seleccionar una terminal bancaria')
            return

        barcode = 0 if barcode == 'Seleccione' else barcode
        financial_entity_id = 0
        afiliacion = 0
        payment_method_id = self._buscar_metodo_pago_id(forma_pago)
        banco = 'NO APLICA'

        if barcode != 0:
            info = [reg for reg in self._consulta_terminales if reg['Barcode'] == barcode][0]

            financial_entity_id = info['FinancialEntityID']
            afiliacion = info['Afiliacion']
            banco = info['Banco']

        self.actualizar_fila = True
        self.valores_fila['Forma de Pago'] = forma_pago
        self.valores_fila['Barcode'] = barcode
        self.valores_fila['Afiliacion'] = afiliacion
        self.valores_fila['Banco'] =  banco
        self.valores_fila['FinancialEntityID'] = financial_entity_id
        self.valores_fila['PaymentMethodID'] = payment_method_id

        self._master.destroy()



