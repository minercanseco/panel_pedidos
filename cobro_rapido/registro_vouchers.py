import tkinter as tk
from cayal.ventanas import Ventanas


class RegistroVouchers:
    def __init__(self, master, base_de_datos, utilerias, parametros):
        self._master = master
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._parametros = parametros

        self._user_id = self._parametros.id_usuario

        self._ventanas = Ventanas(self._master)

        self._crear_frames()
        self._cargar_componentes()
        self._cargar_eventos()
        self._rellenar_componentes()
        self._ajustar_etiquetas()

        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Registro de Vouchers')
        self._master.lift()  # Trae la ventana al frente
        self._master.focus_force()  # Le da el foco
    def _crear_frames(self):
        self._frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),
            'frame_info_texto': ('frame_principal', None,
                                 {'row': 0, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW}),
            'frame_info': ('frame_principal', None,
                           {'row': 1, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW}),
            'frame_numero_texto': ('frame_principal', None,
                             {'row': 2, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW}),
            'frame_numero': ('frame_principal', None,
                           {'row': 3, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW}),

            'frame_terminales': ('frame_principal', None,
                           {'row': 4, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW}),

            'frame_detalle': ('frame_principal', None,
                             {'row': 5, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW}),

            'frame_botones': ('frame_principal', None,
                               {'row': 6, 'column': 0, 'columnspan': 2, 'sticky': tk.NSEW}),

        }

        self._ventanas.crear_frames(self._frames)

    def _cargar_componentes(self):
        estilo_total_danger = {
            'foreground': 'white',
            'background': '#E30421',
            'font': ('consolas', 29, 'bold'),
            'text': '$0.00',
            'anchor': 'center'
        }
        estilo_auxiliar_danger = {
            'foreground': 'white',
            'background': '#E30421',
            'font': ('Consolas', 16, 'bold'),
            'text': '$0.00',
            'anchor': 'center'
        }
        posicion = {
            'sticky': tk.NSEW, 'pady': 0, 'padx': 0,
        }
        componentes = {
            'lbl_total_texto': ('frame_info_texto', estilo_auxiliar_danger, posicion, None),
            'lbl_total': ('frame_info', estilo_total_danger, posicion, None),
            'lbl_numero_texto': ('frame_numero_texto', estilo_auxiliar_danger, posicion, None),
            'lbl_numero': ('frame_numero', estilo_total_danger, posicion, None),

            'tvw_terminales':('frame_terminales', self._crear_columnas_tabla(), 5, None),
            'tvw_cobros': ('frame_detalle', self._crear_columnas_tabla_detalle(), 10, 'Danger'),
            'btn_registrar':('frame_botones', None, 'Registrar', None),
            'btn_cancelar': ('frame_botones', 'Danger', 'Cancelar', None),
        }
        self._ventanas.crear_componentes(componentes)

    def _cargar_eventos(self):
        eventos = {
            'btn_registrar':self._registrar_vouchers,
            'btn_cancelar':self._master.destroy,
            'tvw_cobros':(lambda event:self._calcular_acumulados_terminal(),'seleccion')
        }
        self._ventanas.cargar_eventos(eventos)

    def _crear_columnas_tabla_detalle(self):
        return [
                {'text': 'Monto', "stretch": False, 'width': 70, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                 'hide': 0},
                {'text': 'Afiliacion', "stretch": False, 'width': 90, 'column_anchor': tk.W, 'heading_anchor': tk.W,
                 'hide': 0},
                {'text': 'Barcode', "stretch": False, 'width': 90, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                 'hide': 0},
                {'text': 'Forma de pago', "stretch": False, 'width': 185, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                 'hide': 0},
                {'text': 'Banco', "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                'hide': 0},
                {'text': 'FinancialOperationID', "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                'hide': 1},

                ]

    def _crear_columnas_tabla(self):
        return [
                {'text': 'Monto', "stretch": False, 'width': 75, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                 'hide': 0},
                {'text': 'Cobros', "stretch": False, 'width': 70, 'column_anchor': tk.W, 'heading_anchor': tk.W,
                 'hide': 0},
                {'text': 'Afiliación', "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                 'hide': 0},
                {'text': 'Barcode', "stretch": False, 'width': 180, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                 'hide': 0},
                {'text': 'Banco', "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E,
                'hide': 0},
                ]

    def _buscar_cobros_terminales_no_registrados(self):
        return self._base_de_datos.fetchall("""
            SELECT 
                FORMAT(DF.Amount, 'C', 'es-MX') Amount,
                DF.Afiliacion, DF.Barcode, FP.[Value], TM.Banco, DF.FinancialOperationID
            FROM docFinancialOperation DF INNER JOIN
                vwcboAnexo20v33_FormaPago FP ON DF.PaymentMethodID = FP.ID  LEFT OUTER JOIN
                zvwTerminalesBancariasCayalMenu TM ON DF.Barcode = TM.Barcode
            WHERE DF.CreatedBy = ?
             AND DF.Registrado = 0 
             AND CAST(DF.CreatedOn as date) = CAST(GETDATE() as date)
             AND DF.PaymentMethodID IN (28,4)
             AND DF.DeletedOn IS NULL
            ORDER BY DF.FinancialEntityID DESC, DF.Barcode
        """,(self._user_id,))

    def _buscar_terminales_no_registradas(self):
        return self._base_de_datos.fetchall("""
            SELECT SUM(DF.Amount) Monto, COUNT(DF.FinancialOperationID) Cobros, DF.Afiliacion, DF.Barcode, TM.Banco
            FROM docFinancialOperation DF INNER JOIN
                vwcboAnexo20v33_FormaPago FP ON DF.PaymentMethodID = FP.ID LEFT OUTER JOIN
                zvwTerminalesBancariasCayalMenu TM ON DF.Barcode = TM.Barcode
            WHERE DF.CreatedBy = ?
             --AND DF.Registrado = 0 
             AND CAST(DF.CreatedOn as date) = CAST(GETDATE() as date)
             AND DF.PaymentMethodID IN (28,4)
             AND DF.DeletedOn IS NULL
            GROUP BY DF.Afiliacion, DF.Barcode, TM.Banco
            ORDER BY TM.Banco,  DF.Barcode
        """,(self._user_id,))

    def _rellenar_componentes(self):

        consulta_terminales = self._buscar_terminales_no_registradas()
        for reg in consulta_terminales:
            monto = reg['Monto']
            monto_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(monto)
            monto_moneda = self._utilerias.convertir_decimal_a_moneda(monto_decimal)
            reg['Monto'] = monto_moneda


        if consulta_terminales:
            cobros = self._buscar_cobros_terminales_no_registrados()

            self._ventanas.rellenar_treeview('tvw_cobros',
                                             self._crear_columnas_tabla_detalle(),
                                             cobros,
                                             valor_barra_desplazamiento=5)

            self._ventanas.rellenar_treeview('tvw_terminales',
                                             self._crear_columnas_tabla(),
                                             consulta_terminales,
                                             valor_barra_desplazamiento=5)



            self._ventanas.insertar_input_componente('lbl_total_texto', 'Total acumulado')
            self._ventanas.insertar_input_componente('lbl_total', '$0.00')
            self._ventanas.insertar_input_componente('lbl_numero_texto', 'Número vouchers')
            self._ventanas.insertar_input_componente('lbl_numero', '0')

    def _ajustar_etiquetas(self):
        self._ventanas.ajustar_label_en_frame('lbl_total_texto', 'frame_info_texto')
        self._ventanas.ajustar_label_en_frame('lbl_total', 'frame_info')
        self._ventanas.ajustar_label_en_frame('lbl_numero_texto', 'frame_numero_texto')
        self._ventanas.ajustar_label_en_frame('lbl_numero', 'frame_numero')

    def _registrar_vouchers(self):
        filas = self._ventanas.obtener_seleccion_filas_treeview('tvw_cobros')

        if not filas:
            self._master.destroy()
            return

        for fila in filas:
            valores_filas = self._ventanas.procesar_fila_treeview('tvw_cobros', fila)
            financial_operation_id = valores_filas['FinancialOperationID']
            self._base_de_datos.command('UPDATE docFinancialOperation SET Registrado = 1 WHERE FinancialOperationID = ?',
                                        (financial_operation_id,))

        self._master.destroy()

    def _calcular_acumulados_terminal(self):
        filas = self._ventanas.obtener_seleccion_filas_treeview('tvw_cobros')
        if not filas:
            return

        cobros = len(filas)
        self._ventanas.insertar_input_componente('lbl_numero', cobros)

        monto_acumulado = 0
        for fila in filas:
            valores_fila = self._ventanas.procesar_fila_treeview('tvw_cobros', fila)
            monto_moneda = valores_fila['Monto']
            monto_decimal = self._utilerias.convertir_moneda_a_decimal(monto_moneda)
            monto_acumulado += monto_decimal

        acumulado_moneda = self._utilerias.convertir_decimal_a_moneda(monto_acumulado)
        self._ventanas.insertar_input_componente('lbl_total', acumulado_moneda)
