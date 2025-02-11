import datetime

import ttkbootstrap as ttk
import tkinter as tk
import ttkbootstrap.dialogs

from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.util import Utilerias
from cayal.ventanas import Ventanas
from cayal.cobros import Cobros


class CobroRapido:
    def __init__(self, master, parametros):
        self._master = master
        self._parametros = parametros

        self._inicializar_clases_auxiliares()
        self._inicializar_variables_de_instancia()

        self._crear_frames()
        self._cargar_componentes_forma()
        self._cargar_eventos_componentes_forma()
        self._cargar_info_componentes_forma()
        self._ajustar_apariencia_forma()
        self._agregar_hotkeys()
        self._ventanas.configurar_ventana_ttkbootstrap("Cobro rápido")
        self._ventanas.enfocar_componente('tbx_recibido')

    def _inicializar_variables_de_instancia(self):

        self._document_id = self._parametros.id_principal
        self._usuario_id = self._parametros.id_usuario
        self._inicializar_business_entity_id()
        self._inicializar_saldo_documento()
        self._consulta_formas_pago = []

        self._consulta_terminales = []
        self._inicializar_generales_cliente()
        self._financial_operation_id = 0
        self._monto_recibido = 0
        self._frames = {}

    def _inicializar_generales_cliente(self):

        if self._business_entity_id == 9277:
            self._credito_restante = self._utilerias.redondear_valor_cantidad_a_decimal(0)
            self._official_name = 'PG'
            self._official_number = 'XAXX010101000'
        else:
            self._consulta_info_cliente = self._base_de_datos.buscar_info_cliente(self._business_entity_id)

            credito_restante = self._consulta_info_cliente[0]['RemainingCredit']
            credito_restante = self._utilerias.redondear_valor_cantidad_a_decimal(credito_restante)
            self._credito_restante = credito_restante + self._saldo_documento if credito_restante > 0 else credito_restante

            self._official_name = self._consulta_info_cliente[0]['OfficialName']
            self._official_number = self._consulta_info_cliente[0]['OfficialNumber']


    def _inicializar_saldo_documento(self):
        info_documento = self._base_de_datos.fetchall(
            'SELECT Balance, Total, TotalPaid FROM docDocument WHERE DocumentID = ?',
                                                       (self._document_id,))

        saldo_documento = info_documento[0]['Balance']
        total_documento = info_documento[0]['Total']
        total_pagado = info_documento[0]['TotalPaid']

        self._total_nota = self._utilerias.redondear_valor_cantidad_a_decimal(total_documento)
        self._saldo_documento = self._utilerias.redondear_valor_cantidad_a_decimal(saldo_documento)

        self._pagado_nota = self._utilerias.redondear_valor_cantidad_a_decimal(total_pagado)

    def _inicializar_business_entity_id(self):
        self._business_entity_id = self._base_de_datos.fetchone(
            'SELECT BusinessEntityID FROM docDocument WHERE DocumentID = ?', (self._document_id,))

        if self._business_entity_id == 8179:
            self._business_entity_id = self._base_de_datos.fetchone(
                'SELECT CustomerID FROM docDocumentExt WHERE IDExtra = ?', (self._document_id,))

    def _inicializar_clases_auxiliares(self):
        self._base_de_datos = ComandosBaseDatos(self._parametros.cadena_conexion)
        self._cobros = Cobros(self._parametros.cadena_conexion)
        self._utilerias = Utilerias()

        self._ventanas = Ventanas(self._master)
        self._componentes_forma = self._ventanas.componentes_forma

    def _crear_frames(self):

        self._frames = {
            'frame_principal': ('master', None,
                                {'row':0, 'column':0, 'sticky':tk.NSEW}),

            'frame_info': ('frame_principal', None,
                           {'row': 0, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW}),

            'frame_cambio': ('frame_principal', None,
                             {'row': 1, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW}),

            'frame_restante': ('frame_principal', None,
                             {'row': 2, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW}),

            'frame_cobro': ('frame_principal', None,
                            {'row': 3, 'column': 0, 'columnspan': 2,  'pady': 5, 'sticky': tk.W}),

            'frame_monto': ('frame_principal', None,
                            {'row': 4, 'column': 0, 'columnspan': 2, 'sticky': tk.W}),

            'frame_tarjeta': ('frame_principal', None,
                            {'row': 5, 'column': 0, 'columnspan': 2, 'sticky': tk.W}),

            'frame_dividido': ('frame_principal', 'Dividido',
                              {'row': 6, 'column': 0, 'padx':5, 'columnspan': 2, 'sticky': tk.NSEW}),

            'frame_controles_dividido': ('frame_dividido', None,
                                       {'row': 0, 'column': 0, 'padx': 5, 'columnspan': 2, 'sticky': tk.E}),

            'frame_terminal_dividido': ('frame_dividido', None,
                                       {'row': 1, 'column': 1, 'padx': 5, 'columnspan': 2, 'sticky': tk.E}),

            'frame_recibido_dividido': ('frame_dividido', None,
                                        {'row': 2, 'column': 1, 'padx': 5, 'columnspan': 2, 'sticky': tk.E}),

            'frame_botones_dividido': ('frame_dividido', None,
                                    {'row': 3, 'column': 1, 'padx': 5, 'columnspan': 2, 'sticky': tk.E}),

            'frame_tabla_dividido': ('frame_dividido', None,
                                    {'row': 4, 'column': 1, 'padx': 5, 'columnspan': 2, 'sticky': tk.NSEW}),

            'frame_botones': ('frame_principal', None,
                              {'row': 7, 'column': 1, 'padx':25, 'pady': 5, 'sticky': tk.E})
        }

        self._ventanas.crear_frames(self._frames)

    def _cargar_componentes_forma(self):

        nombres_componentes = {
            'lbl_saldo': ('frame_info', 'inverse-danger'),
            'lbl_monto_saldo': ('frame_info', 'inverse-danger'),
            'lbl_cambio': ('frame_cambio', 'inverse-danger'),
            'lbl_monto_cambio': ('frame_cambio', 'inverse-danger'),
            'lbl_restante': ('frame_restante', 'inverse-warning'),
            'lbl_monto_restante': ('frame_restante', 'inverse-warning'),
            'cbx_tipo': ('frame_cobro', None),
            'tbx_recibido': ('frame_monto', None),
            'lbl_banco': ('frame_tarjeta', None),
            'tbx_barcode': ('frame_tarjeta', None),
            'cbx_terminal': ('frame_tarjeta', None),
            'btn_cobrar': ('frame_botones', 'primary'),
            'btn_cancelar': ('frame_botones', 'danger'),
            'tbx_cobro': ('frame_controles_dividido', None),
            'cbx_tipo_dividido': ('frame_controles_dividido', None),
            'tbx_recibido_dividido': ('frame_recibido_dividido', None),
            'tbx_barcode_dividido': ('frame_terminal_dividido', None),
            'cbx_terminal_dividido': ('frame_terminal_dividido', None),
            'btn_agregar': ('frame_botones_dividido', 'primary'),
            'btn_remover': ('frame_botones_dividido', 'danger'),
            'tvw_cobros': ('frame_tabla_dividido', None)
        }

        for i, (nombre, (frame, configuracion)) in enumerate(nombres_componentes.items()):
            etiqueta = nombre[4::] if 'dividido' not in nombre else nombre[4:nombre.find('_', 4)]
            etiqueta = etiqueta.capitalize()
            tipo = nombre[0:3]
            frame = self._componentes_forma[frame]

            if tipo == 'lbl':

                if 'monto' in nombre:
                    componente = ttk.Label(frame, text='$0.00', font=('consolas', 20, 'bold'), anchor='center',
                                           width=18, style=configuracion)
                elif 'banco' in nombre:
                    componente = ttk.Label(frame, text='BANCO')
                    componente.grid(row=i, column=1,  pady=5, padx=5, sticky=tk.NSEW)
                    self._componentes_forma[nombre] = componente
                    continue
                else:
                    componente = ttk.Label(frame, text=etiqueta, font=('consolas', 18, 'bold'), anchor='center',
                                           width=1, style=configuracion)

                componente.grid(row=i, column=0, sticky=tk.NSEW)

            if tipo == 'tbx':
                componente = ttk.Entry(frame, width=26)

            if tipo == 'cbx':
                componente = ttk.Combobox(frame, state='readonly', width=24)

            if tipo == 'tvw':
                columnas_tabla = [
                    {'text': 'Monto', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                     'hide': 0},
                    {'text': 'F.Pago', "stretch": False, 'width': 105, 'column_anchor': tk.W, 'heading_anchor': tk.W,
                     'hide': 0},
                    {'text': 'Restante', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                     'hide': 0},
                    {'text': 'BancoID', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                     'hide': 1},
                    {'text': 'Afiliacion', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                     'hide': 1},
                    {'text': 'Barcode', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                     'hide': 1}
                    ]
                componente = ttk.Treeview(master=frame,
                                          bootstyle = 'PRIMARY',
                                          columns=columnas_tabla,
                                          show='headings',
                                          height=4)

                self._ventanas.rellenar_treeview(componente, columnas_tabla)
                componente.grid(row=17, column=0, columnspan=2, pady=5, sticky=tk.W)

            if tipo == 'btn':
                componente = ttk.Button(frame, text=etiqueta, style=configuracion)
                componente.grid(row=0, column=i, pady=5, padx=5, sticky=tk.W)

                if 'btn_cobrar' in nombre:
                    hotkey = ttk.Label(frame, text='[F12]', anchor='center')
                    hotkey.grid(row=1, column=i, pady=5, padx=5, sticky=tk.W)

                if 'btn_cancelar' in nombre:
                    hotkey = ttk.Label(frame, text='[ESC]', anchor='center')
                    hotkey.grid(row=1, column=i, pady=5, padx=5, sticky=tk.W)

            if tipo not in ('tvw', 'lbl', 'btn'):
                lbl = ttk.Label(frame,  width=9, text=etiqueta)
                lbl.grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)

                componente.grid(row=i, column=1, padx=5, pady=5, sticky=tk.W)

            self._componentes_forma[nombre] = componente

    def _cargar_eventos_componentes_forma(self):

        eventos = {
            'btn_cancelar': lambda: self._master.destroy(),
            'btn_cobrar': lambda: self._cobrar_documento(),
            'cbx_tipo': lambda event: self._ajustar_apariencia_forma(),
            'tbx_barcode': lambda event: self._buscar_afiliacion(),
            'tbx_recibido': lambda event: self._calcular_cambio(),
            'tbx_barcode_dividido': lambda event: self._buscar_afiliacion(),
            'cbx_terminal': lambda event: self._buscar_afiliacion_seleccion(),
            'cbx_tipo_dividido': lambda event: self._ajustar_apariencia_frame_dividido(),
            'cbx_terminal_dividido': lambda event: self._buscar_afiliacion_seleccion(),
            'btn_agregar': lambda: self._agregar_cobro_tabla(),
            'btn_remover': lambda: self._elimnar_cobro_tabla(),
            'tbx_cobro': lambda event: self._ventanas.enfocar_componente('cbx_tipo_dividido'),
            'tbx_recibido_dividido': lambda event: self._calcular_cambio(),
        }

        for nombre, componente in self._componentes_forma.items():
            if nombre in eventos.keys():
                if 'btn' in nombre:
                    componente.config(command=eventos[nombre])

                if 'cbx' in nombre:
                    componente.bind('<<ComboboxSelected>>', eventos[nombre])

                if 'tbx' in nombre:
                    componente.bind('<Return>', eventos[nombre])

        self._ventanas.agregar_validacion_tbx( 'tbx_cobro', 'cantidad')
        self._ventanas.agregar_validacion_tbx( 'tbx_recibido', 'cantidad')
        self._ventanas.agregar_validacion_tbx( 'tbx_recibido_dividido', 'cantidad')

    def _cargar_info_componentes_forma(self):

        saldo_moneda = self._utilerias.convertir_decimal_a_moneda(self._saldo_documento)
        lbl_monto_saldo = self._componentes_forma['lbl_monto_saldo']
        lbl_monto_saldo.config(text=saldo_moneda)

        restante_moneda = self._utilerias.convertir_decimal_a_moneda(self._credito_restante)
        lbl_monto_restante = self._componentes_forma['lbl_monto_restante']
        lbl_monto_restante.config(text=restante_moneda)

        cbx_tipo = self._componentes_forma['cbx_tipo']
        formas_pago = self._rellenar_cbx_forma_pago(cbx_tipo)

        if self._credito_restante > 0:
            formas_pago.insert(1, '00 - Firma de documento')

        formas_pago.insert(len(formas_pago), '66 - Dividido')
        cbx_tipo['values'] = formas_pago

        cbx_terminal = self._componentes_forma['cbx_terminal']
        self._rellenar_cbx_terminal(cbx_terminal)

    def _agregar_hotkeys(self):
        hotkeys = {
            'F12': lambda: self._cobrar_documento(),
            'E': lambda: self._seleccionar_tipo_cobro('E'),
            'C': lambda: self._seleccionar_tipo_cobro('C'),
            'D': lambda: self._seleccionar_tipo_cobro('D'),
            'M': lambda: self._seleccionar_tipo_cobro('M'),
            'F': lambda: self._seleccionar_tipo_cobro('F')
        }

        self._ventanas.agregar_hotkeys_forma(hotkeys)

    def _rellenar_cbx_forma_pago(self, cbx):

        if not self._consulta_formas_pago:
            self._consulta_formas_pago = self._base_de_datos.buscar_formas_de_pago()

        formas_pago = [reg['Value'] for reg in self._consulta_formas_pago
                       if reg['Clave'] not in ('02', '99')]

        cbx['values'] = formas_pago
        cbx.set(formas_pago[0])

        return formas_pago

    def _rellenar_cbx_terminal(self, cbx):

        if not self._consulta_terminales:
            self._consulta_terminales = self._base_de_datos.buscar_terminales_bancarias()

        terminales = [reg['Barcode'] for reg in self._consulta_terminales]
        terminales.insert(0, 'Seleccione')

        cbx['values'] = terminales
        cbx.set(terminales[0])

    def _ajustar_apariencia_frame_dividido(self):
        seleccion = self._obtener_input_componente('cbx_tipo_dividido')

        if seleccion == '01 - Efectivo':
            self._posicionar_frame('frame_recibido_dividido')
            self._posicionar_frame('frame_cambio')
            self._master.place_window_center()

        if seleccion == 'Seleccione' and not self._cobros_efectivo_tabla():
            self._ocultar_frame('frame_recibido_dividido')
            self._master.place_window_center()

        if seleccion == 'Seleccione' or seleccion not in ('04 - Tarjeta de crédito', '28 - Tarjeta de débito'):
            self._ocultar_frame('frame_terminal_dividido')
            self._master.place_window_center()

            if seleccion != 'Seleccione':
                self._agregar_cobro_tabla()
                self._ventanas.enfocar_componente('tbx_cobro')

        if seleccion in ('04 - Tarjeta de crédito', '28 - Tarjeta de débito'):
            self._posicionar_frame('frame_terminal_dividido')
            self._master.place_window_center()
            self._ventanas.enfocar_componente('tbx_barcode_dividido')

    def _cobros_efectivo_tabla(self):
        tabla = self._componentes_forma['tvw_cobros']
        cobros = tabla.get_children()

        cobro_en_efectivo = False
        if not cobros:
            return False

        for cobro in cobros:
            tipo_cobro = tabla.item(cobro)['values'][1]
            if tipo_cobro == '01 - Efectivo':
                cobro_en_efectivo = True
                break
        return cobro_en_efectivo

    def _ajustar_apariencia_forma(self):
        seleccion = self._obtener_input_componente('cbx_tipo')

        def estado_inicial():
            self._limpiar_componentes()

            if self._credito_restante <= 0:
                self._ocultar_frame('frame_restante')

            self._ocultar_frame('frame_tarjeta')
            self._ocultar_frame('frame_cambio')
            self._ocultar_frame('frame_monto')
            self._ocultar_frame('frame_dividido')

        if seleccion == 'Seleccione' or seleccion[0:2] in ('02', '03', '00'):
            estado_inicial()

        if seleccion == '01 - Efectivo':
            estado_inicial()
            self._posicionar_frame('frame_cambio')
            self._posicionar_frame('frame_monto')
            self._ventanas.enfocar_componente('tbx_recibido')

        if seleccion in ('04 - Tarjeta de crédito', '28 - Tarjeta de débito'):
            estado_inicial()
            self._posicionar_frame('frame_tarjeta')
            self._ventanas.enfocar_componente('tbx_barcode')

        if seleccion == '66 - Dividido':
            estado_inicial()
            self._posicionar_frame('frame_dividido')

            cbx_tipo_dividido = self._componentes_forma['cbx_tipo_dividido']
            self._rellenar_cbx_forma_pago(cbx_tipo_dividido)

            cbx_terminal_dividido = self._componentes_forma['cbx_terminal_dividido']
            self._rellenar_cbx_terminal(cbx_terminal_dividido)

            self._ajustar_apariencia_frame_dividido()

            self._ventanas.enfocar_componente('tbx_cobro')

    def _buscar_afiliacion_seleccion(self):

        seleccion = self._validar_seleccion_cbx_cobro('cbx_tipo')

        if not seleccion:
            return

        tipo = seleccion[0:2].strip()

        nombre_cbx_terminal = 'cbx_terminal' if tipo in ('04', '28') else 'cbx_terminal_dividido'

        cbx_terminal = self._componentes_forma[nombre_cbx_terminal]
        seleccion = cbx_terminal.get()

        if seleccion != 'Seleccione':
            info_terminal = [terminal for terminal in self._consulta_terminales
                             if seleccion == terminal['Barcode']]

            self._settear_valores_terminal(info_terminal)

    def _buscar_afiliacion(self):

        seleccion = self._validar_seleccion_cbx_cobro('cbx_tipo')

        if not seleccion:
            return

        tipo = seleccion[0:2].strip()
        nombre_tbx = 'tbx_barcode' if tipo in ('04', '28') else 'tbx_barcode_dividido'

        tbx_barcode = self._componentes_forma[nombre_tbx]
        barcode = tbx_barcode.get()

        if not barcode:
            ttkbootstrap.dialogs.Messagebox.show_error('Debe capturar un número válido')
            return

        barcode = barcode.strip()

        info_terminal = [terminal for terminal in self._consulta_terminales
                         if barcode == terminal['Barcode']]

        if not info_terminal:
            ttkbootstrap.dialogs.Messagebox.show_error('No se encontró información relacionada'
                                                       'a la afiliación proporcionada.')
            tbx_barcode.delete(0, tk.END)
            return

        self._settear_valores_terminal(info_terminal)

        if nombre_tbx == 'tbx_barcode':
            self._cobrar_documento()
        else:
            self._agregar_cobro_tabla()

            cbx_tipo_dividido = self._componentes_forma['cbx_tipo_dividido']
            valores = cbx_tipo_dividido['values']
            cbx_tipo_dividido.set(valores[0])

            self._ajustar_apariencia_frame_dividido()
            self._ventanas.enfocar_componente('tbx_cobro')

    def _cobrar_documento(self):

        tipo_cobro = self._validar_seleccion_cbx_cobro('cbx_tipo')

        if tipo_cobro:

            date_operation = datetime.datetime.today()

            if tipo_cobro not in ('66 - Dividido', '00 - Firma de documento'):

                if not self._validar_terminal(tipo_cobro):
                    return

                payment_method_id = self._buscar_metodo_pago_id(tipo_cobro)
                barcode = self._obtener_input_componente('tbx_barcode')
                barcode = 0 if barcode == '' else barcode

                afiliacion = self._buscar_afiliacion_barcode_terminal(barcode)
                banco_id = self._obtener_financial_entity_id(afiliacion)

                self._cobros.modality = 0
                self._cobros.total_amount = self._saldo_documento
                self._cobros.barcode = barcode
                self._cobros.document_id = self._document_id
                self._cobros.payment_method_id = payment_method_id
                self._cobros.amount = self._saldo_documento
                self._cobros.financial_entity_id = banco_id
                self._cobros.business_entity_id = self._business_entity_id
                self._cobros.official_number = self._official_number
                self._cobros.official_name = self._official_name
                self._cobros.afiliacion = afiliacion
                self._cobros.created_by = self._usuario_id
                self._cobros.date_operation = date_operation
                self._cobros.total = self._total_nota
                self._cobros.total_paid = self._pagado_nota + self._saldo_documento
                self._cobros.create_payment()

                self._guardar_monto_recibido()
                self._insertar_para_recalcular()
                self._master.destroy()

            if tipo_cobro == '66 - Dividido':
                tabla = self._componentes_forma['tvw_cobros']
                cobros = tabla.get_children()

                if not cobros:
                    ttkbootstrap.dialogs.Messagebox.show_error('Debe por lo menos agregar un cobro al documento.')
                    return

                for cobro in cobros:
                    valores = tabla.item(cobro)['values']

                    monto = self._utilerias.redondear_valor_cantidad_a_decimal(valores[0])
                    forma_cobro = valores[1]
                    payment_method_id = self._buscar_metodo_pago_id(forma_cobro)
                    banco_id = valores[3]
                    afiliacion = valores[4]
                    barcode = valores[5]
                    self._pagado_nota += monto

                    self._cobros.modality = 1
                    self._cobros.total_amount =monto
                    self._cobros.barcode = barcode
                    self._cobros.document_id = self._document_id
                    self._cobros.payment_method_id = payment_method_id
                    self._cobros.amount = monto
                    self._cobros.financial_entity_id = banco_id
                    self._cobros.business_entity_id = self._business_entity_id
                    self._cobros.official_number = self._official_number
                    self._cobros.official_name = self._official_name
                    self._cobros.afiliacion = afiliacion
                    self._cobros.created_by = self._usuario_id
                    self._cobros.date_operation = date_operation
                    self._cobros.total = self._total_nota
                    self._cobros.total_paid = self._pagado_nota
                    self._cobros.create_payment()

                self._guardar_monto_recibido()
                self._insertar_para_recalcular()
                self._master.destroy()

            if tipo_cobro == '00 - Firma de documento':
                cerrar = False

                if self._saldo_documento <= self._credito_restante:
                    cerrar = True

                if self._saldo_documento > self._credito_restante:
                    diferencia = self._saldo_documento - self._credito_restante
                    diferencia_moneda = self._utilerias.convertir_decimal_a_moneda(diferencia)

                    ttkbootstrap.dialogs.Messagebox.show_error('Cobre la nota de manera dividida y '
                                                               'debe cobrar por lo menos un monto de '
                                                               f'{diferencia_moneda}')
                    cerrar = False

                self._master.destroy() if cerrar else cerrar

    def _settear_valores_terminal(self, info_terminal):
        seleccion = self._validar_seleccion_cbx_cobro('cbx_tipo')
        tipo = seleccion[0:2].strip()

        nombre_tbx = 'tbx_barcode' if tipo in ('04', '28') else 'tbx_barcode_dividido'
        nombre_cbx = 'cbx_terminal' if tipo in ('04', '28') else 'cbx_terminal_dividido'

        tbx_barcode = self._componentes_forma[nombre_tbx]

        banco = info_terminal[0]['Banco']

        if nombre_tbx == 'tbx_barcode':

            lbl_banco = self._componentes_forma['lbl_banco']
            lbl_banco.config(text=banco)

        tbx_barcode.delete(0, tk.END)
        tbx_barcode.insert(0, info_terminal[0]['Barcode'])

        cbx_terminal = self._componentes_forma[nombre_cbx]
        valores_cbx_terminal = cbx_terminal['values']
        idx = valores_cbx_terminal.index(info_terminal[0]['Barcode'])
        cbx_terminal.set(valores_cbx_terminal[idx])

    def _posicionar_frame(self, nombre_frame):
        info_frame = self._frames[nombre_frame]
        posicion = info_frame[2]

        frame = self._componentes_forma[nombre_frame]
        frame.grid(**posicion)

    def _ocultar_frame(self, nombre_frame):
        frame = self._componentes_forma[nombre_frame]
        frame.grid_forget()

    def _obtener_input_componente(self, nombre_componente):
        componente = self._componentes_forma[nombre_componente]
        return componente.get()

    def _agregar_cobro_tabla(self):
        monto = self._validar_monto('tbx_cobro')

        if monto:
            forma_cobro = self._validar_seleccion_cbx_cobro('cbx_tipo_dividido')
            if forma_cobro:

                if not self._validar_terminal(forma_cobro):
                    return

                tabla = self._componentes_forma['tvw_cobros']
                aplicado = self._calcular_saldo_tabla(tabla)

                restante = self._saldo_documento - aplicado - monto

                if restante < 0:
                    ttkbootstrap.dialogs.Messagebox.show_error('El monto aplicado no puede ser mayor que el restante.')
                    return

                tbx_barcode_dividido = self._componentes_forma['tbx_barcode_dividido']
                barcode = tbx_barcode_dividido.get()
                afiliacion = self._buscar_afiliacion_barcode_terminal(barcode)
                banco_id = self._obtener_financial_entity_id(afiliacion)
                barcode = 0 if not barcode else barcode

                valores = (monto, forma_cobro, restante, banco_id, afiliacion, barcode)
                tabla.insert('', 'end', values=valores, tags='white')

                tbx_cobro = self._componentes_forma['tbx_cobro']
                tbx_cobro.delete(0, tk.END)
                tbx_cobro.insert(0, restante)

                restante_moneda = self._utilerias.convertir_decimal_a_moneda(restante)
                self._ventanas.insertar_input_componente('lbl_monto_saldo', restante_moneda)



    def _buscar_afiliacion_barcode_terminal(self, barcode):
        barcode = str(barcode)
        barcode = barcode.strip()

        afiliacion = [reg['Afiliacion'] for reg in self._consulta_terminales
                      if str(reg['Barcode']) == barcode]

        return afiliacion[0] if afiliacion else 0

    def _obtener_financial_entity_id(self, afiliacion):
        if not afiliacion or afiliacion == 0:
            return 0
        financial_entity_id = [reg['FinancialEntityID'] for reg in self._consulta_terminales
                         if reg['Afiliacion'] == afiliacion]

        return financial_entity_id[0] if financial_entity_id else 0

    def _validar_terminal(self, forma_cobro):

        if forma_cobro in ('04 - Tarjeta de crédito', '28 - Tarjeta de débito'):

            tipo_cobro = self._obtener_input_componente('cbx_tipo')

            nombre_cbx = 'cbx_terminal' if tipo_cobro != '66 - Dividido' else 'cbx_terminal_dividido'
            seleccion_cbx = self._obtener_input_componente(nombre_cbx)

            if seleccion_cbx == 'Seleccione':
                ttkbootstrap.dialogs.Messagebox.show_error('Debe seleccionar una terminal bancaria.')
                return False

        return True

    def _elimnar_cobro_tabla(self):
        tabla = self._componentes_forma['tvw_cobros']
        filas = tabla.selection()

        if not filas:
            ttkbootstrap.dialogs.Messagebox.show_error('Debe seleccionar por lo menos una fila')
            return

        for fila in filas:
            tabla.delete(fila)

        filas_tabla = tabla.get_children()

        saldo = self._saldo_documento

        for fila in filas_tabla:
            valores_fila = tabla.item(fila)['values']

            aplicado = self._utilerias.redondear_valor_cantidad_a_decimal(valores_fila[0])
            saldo -= aplicado
            restante = saldo
            tabla.set(fila, column=2, value=restante)

            self._ventanas.insertar_input_componente('tbx_cobro', restante)
            restante_moneda = self._utilerias.convertir_decimal_a_moneda(restante)
            self._ventanas.insertar_input_componente('lbl_monto_saldo', restante_moneda)

        if not filas_tabla:
            self._ventanas.insertar_input_componente('tbx_cobro', saldo)
            saldo_moneda = self._utilerias.convertir_decimal_a_moneda(saldo)
            self._ventanas.insertar_input_componente('lbl_monto_saldo', saldo_moneda)

    def _calcular_cambio(self):
        lbl_monto_cambio = self._componentes_forma['lbl_monto_cambio']
        seleccion = self._validar_seleccion_cbx_cobro('cbx_tipo')

        nombre_tbx = 'tbx_recibido_dividido' if seleccion  == '66 - Dividido' else 'tbx_recibido'
        monto = self._validar_monto(nombre_tbx)

        if not monto:
            lbl_monto_cambio.config(text='$0.00')
            return

        saldo = self._saldo_documento if nombre_tbx == 'tbx_recibido' else self._obtener_monto_efectivo_tabla()

        if monto < saldo:
            ttkbootstrap.dialogs.Messagebox.show_error('El monto recibido debe ser mayor que el total de la nota.')
            lbl_monto_cambio.config(text='$0.00')
            return

        cambio = monto - saldo

        cambio_moneda = self._utilerias.convertir_decimal_a_moneda(cambio)
        lbl_monto_cambio.config(text=cambio_moneda)

        self._monto_recibido = monto

    def _obtener_monto_efectivo_tabla(self):
        tabla = self._ventanas.componentes_forma['tvw_cobros']
        filas = tabla.get_children()
        monto_total = self._utilerias.redondear_valor_cantidad_a_decimal(0)

        if len(filas) > 0:

            for fila in filas:
                forma_pago = tabla.item(fila)['values'][1]
                if forma_pago == '01 - Efectivo':
                    monto_aplicado = tabla.item(fila)['values'][0]
                    monto_aplicado = self._utilerias.redondear_valor_cantidad_a_decimal(monto_aplicado)
                    monto_total += monto_aplicado
        return monto_total

    def _validar_monto(self, nombre_tbx):
        tbx = self._componentes_forma[nombre_tbx]
        monto = tbx.get()

        if not monto:
            return False

        if not self._utilerias.es_cantidad(monto):
            ttkbootstrap.dialogs.Messagebox.show_error('Debe capturar un monto válido.')
            return False

        monto = self._utilerias.redondear_valor_cantidad_a_decimal(monto)

        if monto <= 0:
            return False

        return monto

    def _validar_seleccion_cbx_cobro(self, nombre_cbx):

        seleccion = self._obtener_input_componente(nombre_cbx)

        if seleccion == 'Seleccione':
            ttkbootstrap.dialogs.Messagebox.show_error('Debe definir una forma de pago.')
            return False

        return seleccion

    def _limpiar_componentes(self):
        for nombre, componente in self._componentes_forma.items():
            tipo = nombre[0:3]
            if tipo == 'tbx':
                componente.delete(0, tk.END)

            if tipo == 'tvw':
                componente.delete(*componente.get_children())

    def _calcular_saldo_tabla(self, tabla):
        filas = tabla.get_children()
        monto_total = self._utilerias.redondear_valor_cantidad_a_decimal(0)

        if len(filas) > 0:

            for fila in filas:
                monto_aplicado = tabla.item(fila)['values'][0]
                monto_aplicado = self._utilerias.redondear_valor_cantidad_a_decimal(monto_aplicado)
                monto_total += monto_aplicado
        return monto_total

    def _buscar_metodo_pago_id(self, tipo_cobro):
        payment_method_id = [valor['ID'] for valor in self._consulta_formas_pago
                             if valor['Value'] == tipo_cobro]

        return int(payment_method_id[0])

    def _seleccionar_tipo_cobro(self, char):
        opciones = {
            'E': '01 - Efectivo',
            'C': '04 - Tarjeta de crédito',
            'D': '28 - Tarjeta de débito',
            'M': '66 - Dividido',
            'F': '00 - Firma de documento'
        }
        if char in opciones.keys():
            seleccion = opciones.get(char)
            cbx_tipo = self._componentes_forma['cbx_tipo']
            valores = cbx_tipo['values']

            try:
                idx = valores.index(seleccion)
                cbx_tipo.set(valores[idx])
                self._ajustar_apariencia_forma()
            except:
                ttkbootstrap.dialogs.Messagebox.show_error('La opción no está disponible para el documento actual.')

    def _guardar_monto_recibido(self):

        if self._monto_recibido > 0:
            self._base_de_datos.command('UPDATE docDocument SET CambioCayal = ? WHERE DocumentID = ?',
                                        (self._monto_recibido, self._document_id))

    def _insertar_para_recalcular(self):
        self._base_de_datos.exec_stored_procedure('zvwRecalcularDocumentos',
                                                  (self._document_id, self._document_id))
