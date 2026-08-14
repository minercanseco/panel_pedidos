import tkinter as tk
from cayal.ventanas import Ventanas
from .comentario_corte import ComentarioCorte
from .tabla_detalles import TablaDetalles


class CorteDeCaja:
    def __init__(self, master,
                 parametros,
                 base_de_datos,
                 utilerias,
                 parametros_corte = {},
                 documentos_cobrados = [],
                 ):

        self._master = master
        self._parametros = parametros
        self._utilerias = utilerias
        self._base_de_datos = base_de_datos
        self._ventanas = Ventanas(self._master)

        self._inicializar_parametros_corte(parametros_corte)
        self._inicializar_variables_de_instancia()
        self._documentos_cobrados = documentos_cobrados
        self._procesar_valores_corte()


        self._crear_frames()
        self._crear_componentes()
        self._rellenar_componentes()
        self._cargar_eventos()

        if self._id_corte == 0:
            self._crear_corte_caja_en_base_datos()
            self._respaldar_items_cobrados()

        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Corte de caja')

    def _inicializar_variables_de_instancia(self):
        self._id_corte = self._parametros.id_principal
        self._user_id = self._parametros.id_usuario
        self._fecha = self._parametros.fecha
        self._user_name = self._base_de_datos.fetchone('SELECT UserName FROM engUser WHERE UserID = ?',
                                                       (self._user_id,))
        self._user_group_id = self._base_de_datos.fetchone('SELECT UserGroupID FROM engUser WHERE UserID = ?',
                                                       (self._user_id,))

        self._vendors = []

        self._documentos_cancelados = []
        self._documentos_tarjetas = []
        self._documentos_tarjeta_debito = []
        self._documentos_tarjeta_credito = []
        self._documentos_transferencias = []
        self._documentos_cheques = []
        self._documentos_efectivo = []
        self._documentos_notas_venta = []
        self._documentos_facturas = []
        self._depositos_emitidos = []

    def _inicializar_parametros_corte(self, parametros_corte):
        self._parametros_corte = {
            'monto_sobrante': 0,
            'monto_faltante': 0,
            'monto_tarjetas': 0,
            'monto_tarjetas_debito': 0,
            'monto_tarjetas_credito': 0,
            'monto_transferencias': 0,
            'monto_cheques': 0,
            'monto_efectivo': 0,
            'monto_efectivo_cajero': 0,
            'monto_depositos': 0,
            'monto_total_cobrado': 0,
            'monto_efectivo_menos_rubros': 0,
            'numero_facturas': 0,
            'numero_notas': 0,
            'monto_monedas': 0,
            'monto_billetes': 0,
            'monto_gastos': 0,
            'monto_anticipos': 0,
            'billetes_capturados': {},
            'monedas_capturadas': {},
            'anticipos_capturados': [],
            'gastos_capturados': [],
        }

        if parametros_corte:
            self._parametros_corte.update(parametros_corte)

    def _calcular_efectivo_sistema(self):
        rubros = ['monto_depositos', 'monto_gastos',
                  'monto_anticipos', 'monto_cheques',
                  'monto_tarjetas','monto_transferencias']

        monto_total_cobrado = self._parametros_corte['monto_total_cobrado']
        for rubro in rubros:
            valor_rubro = self._parametros_corte[rubro]
            monto_total_cobrado -= valor_rubro

        self._parametros_corte['monto_efectivo_menos_rubros'] = monto_total_cobrado

    def _calcular_efectivo_cajero(self):
        rubros_incrementos =['monto_monedas', 'monto_billetes']

        monto_total_cobrado = 0
        for rubro in rubros_incrementos:
            valor_rubro = self._parametros_corte[rubro]
            monto_total_cobrado += valor_rubro
        self._parametros_corte['monto_efectivo_cajero'] = monto_total_cobrado

    def _calcular_faltante_o_sobrante(self):
        monto_sistema = self._parametros_corte['monto_efectivo_menos_rubros']
        monto_cajero = self._parametros_corte['monto_efectivo_cajero']

        diferencia = monto_cajero - monto_sistema
        if diferencia <= 0:
            self._parametros_corte['monto_faltante'] = diferencia
        else:
            self._parametros_corte['monto_sobrante'] = diferencia

    def _procesar_valores_corte(self):

        if self._id_corte != 0:
            self._obtener_info_corte_desde_base_de_datos()

        def procesar_montos(fila):
            campos = ['TotalCobro', 'CobroNota', 'TotalPaid', 'Total', 'Balance']
            for campo in campos:
                fila[campo] = self._utilerias.redondear_valor_cantidad_a_decimal(fila[campo])
            return fila

        for reg in self._documentos_cobrados:
            # Formatear hora
            reg['Hora'] = str(reg['Hora'])[:5]

            # Redondear montos
            reg = procesar_montos(reg)
            monto = reg['CobroNota']
            self._parametros_corte['monto_total_cobrado'] += monto

            # Clasificar por método de pago
            metodo = reg['PaymentMethodID']
            if metodo == 1:
                self._documentos_efectivo.append(reg)
                self._parametros_corte['monto_efectivo'] += monto
            elif metodo in (4, 28):
                self._documentos_tarjetas.append(reg)
                self._parametros_corte['monto_tarjetas'] += monto
                if metodo == 4:
                    self._documentos_tarjeta_credito.append(reg)
                    self._parametros_corte['monto_tarjetas_credito'] += monto
                elif metodo == 28:
                    self._documentos_tarjeta_debito.append(reg)
                    self._parametros_corte['monto_tarjetas_debito'] += monto
            elif metodo == 3:
                self._documentos_transferencias.append(reg)
                self._parametros_corte['monto_transferencias'] += monto
            elif metodo == 2:
                self._documentos_cheques.append(reg)
                self._parametros_corte['monto_cheques'] += monto

            # Capturar vendedores distintos al usuario actual
            if reg['CreatedBy'] != self._user_id:
                self._vendors.append(reg['CreatedBy'])

            # Clasificar por tipo de documento
            if reg['ModuleID'] == 158:
                self._parametros_corte['numero_notas'] += 1
            else:
                self._parametros_corte['numero_facturas'] += 1

        # Eliminar duplicados en la lista de vendedores
        self._vendors = list(set(self._vendors))

        self._consultar_depositos_emitidos()
        self._calcular_efectivo_sistema()
        self._calcular_efectivo_cajero()
        self._calcular_faltante_o_sobrante()
        self._documentos_cancelados = self._buscar_ventas_canceladas()

    def _obtener_info_corte_desde_base_de_datos(self):
        self._documentos_cobrados = self._base_de_datos.fetchall("""
                        SELECT 
                            DocumentID, Fecha, Periodo, CAST(Hora as time) Hora, Folio, OfficialName, ModuleID, StatusPaidID,
                            Globalized, DestinationDocumentID, Cancelado, PaymentMethodID, TotalCobro, CobroNota, 
                            Total, TotalPaid, Balance,  FinancialOperationID, CobradoPor, CreatedBy
                        FROM zvwCortesCajaItemDetalle WHERE CorteID = ?
                    """, (self._id_corte,))

        consulta_info_corte = self._base_de_datos.fetchall("""
                        SELECT 
                            CAST(Fecha as date)Fecha, Ventas, Facturas, Notas, TotalVentas, Depositos, TotalDepositos,
                            EfectivoSistema, EfectivoCajero, Transferencias, TotalTransferencias,
                            Tarjetas, TotalTarjetas, TDebito, TotalDebito, TCredito, TotalCredito,
                            Cheques, TotalCheques, Anticipos, TotalAnticipos, Gastos, TotalGastos,
                            Sobrante, Faltante, Validado, ValidadoEn, ValidadoPor, Comentario,
                            Cajero, UsuarioID, ComentarioCobranza
                        FROM 
                            zvwCortesDeCaja 
                        WHERE 
                            ID = ?
                    """, (self._id_corte,))
        info_corte = consulta_info_corte[0]

        self._user_id = info_corte['UsuarioID']
        self._parametros.id_usuario = info_corte['UsuarioID']
        self._user_name = info_corte['Cajero']

        fecha = info_corte['Fecha']
        self._parametros.fecha = fecha
        self._fecha = fecha

        anticipos = self._base_de_datos.fetchall("""
                        SELECT EmisorAnticipo emisor_anticipo, MontoAnticipo monto_anticipo FROM zvwAnticiposCorteDeCaja WHERE CorteID = ?
                    """, (self._id_corte,))

        gastos = self._base_de_datos.fetchall("""
                            SELECT ReceptorGasto receptor_gasto, MontoGasto monto_gasto  FROM zvwGastosCorteDeCaja WHERE CorteID = ?
                        """, (self._id_corte,))

        conversion = self._utilerias.redondear_valor_cantidad_a_decimal
        parametros_corte = {'monto_monedas': 0,
                            'monto_billetes': conversion(info_corte['EfectivoCajero']),
                            'monto_gastos': conversion(info_corte['TotalGastos']),
                            'monto_anticipos': conversion(info_corte['TotalAnticipos']),
                            'billetes_capturados': {},
                            'monedas_capturadas': {},
                            'anticipos_capturadas': anticipos,
                            'gastos_capturados': gastos,
                            'comentario': info_corte['Comentario'],
                            'comentario_cobranza': info_corte['ComentarioCobranza']
                            }

        self._parametros_corte.update(parametros_corte)

    def _consultar_depositos_emitidos(self):

        user_ids = set(int(x) for x in (self._vendors or []))
        user_ids.add(int(self._user_id))
        user_ids_csv = ",".join(str(x) for x in sorted(user_ids))


        depositos = self._base_de_datos.fetchall("""
            DECLARE @Fecha NVARCHAR(30) = ?;
            DECLARE @CorteID INT = ?;
            DECLARE @UserIDs NVARCHAR(MAX) = ?;

            ;WITH UsuariosPermitidos AS (
                SELECT DISTINCT TRY_CONVERT(INT, value) AS UserID
                FROM STRING_SPLIT(@UserIDs, ',')
                WHERE TRY_CONVERT(INT, value) IS NOT NULL
            )
            
            SELECT DP.Total, DP.ID, DP.Emisor, DP.EmisorUserID
            FROM zvwDepositosDiariosCayal DP
                INNER JOIN engUser U ON DP.EmisorUserID = U.UserID
                INNER JOIN UsuariosPermitidos UP ON UP.UserID = DP.EmisorUserID
            WHERE
                CAST(@Fecha AS date) = CAST(DP.Fecha AS date)
                AND U.DeletedOn IS NULL
                AND DP.CorteID = @CorteID
                
                
        """, (self._fecha, self._id_corte, user_ids_csv))

        for reg in depositos:
            deposito = self._utilerias.redondear_valor_cantidad_a_decimal(reg['Total'])

            self._parametros_corte['monto_depositos'] += deposito
            self._depositos_emitidos.append(reg)


    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', 'Resumen cobranza:',
                                {'row': 0, 'column': 0, 'padx': 2, 'pady': 2,  'sticky': tk.NSEW}),
            'frame_generales': ('frame_principal', 'Generales:',
                                   {'row': 0, 'column': 1, 'padx': 2, 'pady': 2, 'sticky': tk.NSEW}),

            'frame_btn_comentario': ('frame_generales', None,
                                {'row': 0, 'column': 3, 'padx': 2, 'pady': 2, 'sticky': tk.W}),

            'frame_btn_cancelados': ('frame_generales', None,
                                     {'row': 1, 'column': 3, 'padx': 2, 'pady': 2, 'sticky': tk.W}),

            'frame_totales': ('frame_principal', 'Totales:',
                                   {'row': 1, 'column': 1, 'padx': 2, 'pady': 2, 'sticky': tk.NSEW}),

            'frame_btn_depositos': ('frame_totales', None,
                                     {'row': 1, 'column': 3, 'padx': 2, 'pady': 2, 'sticky': tk.E}),

            'frame_btn_anticipos': ('frame_totales', None,
                                     {'row': 2, 'column': 3, 'padx': 2, 'pady': 2, 'sticky': tk.E}),

            'frame_btn_gastos': ('frame_totales', None,
                                    {'row': 3, 'column': 3, 'padx': 2, 'pady': 2, 'sticky': tk.E}),

            'frame_efectivo': ('frame_principal', 'Efectivo:',
                                {'row': 2, 'column': 1, 'padx': 2, 'pady': 2, 'sticky': tk.NSEW}),
            'frame_btn_efectivo': ('frame_efectivo', None,
                                    {'row': 0, 'column': 3, 'padx': 2, 'pady': 2, 'sticky': tk.E}),

            'frame_tarjetas': ('frame_principal', 'Tarjetas:',
                                {'row': 3, 'column': 1, 'padx': 2, 'pady': 2, 'sticky': tk.NSEW}),

            'frame_btn_tarjetas_debito': ('frame_tarjetas', None,
                                   {'row': 1, 'column': 3, 'padx': 2, 'pady': 2, 'sticky': tk.E}),

            'frame_btn_tarjetas_credito': ('frame_tarjetas', None,
                                   {'row': 2, 'column': 3, 'padx': 2, 'pady': 2, 'sticky': tk.E}),


            'frame_transferencias_cheques': ('frame_principal', 'Transferencias y Cheques:',
                                {'row': 4, 'column': 1, 'padx': 2, 'pady': 2, 'sticky': tk.NSEW}),

            'frame_btn_transferencias': ('frame_transferencias_cheques', None,
                                           {'row': 0, 'column': 3, 'padx': 2, 'pady': 2, 'sticky': tk.E}),
            'frame_btn_cheques': ('frame_transferencias_cheques', None,
                                         {'row': 1, 'column': 3, 'padx': 2, 'pady': 2, 'sticky': tk.E}),

        }
        self._ventanas.crear_frames(frames)

    def _crear_componentes(self):
        configuracion_label = {'width': 14, 'text': '0', 'font': ('Consolas', 8, 'normal')}
        configuracion_label_numero = {'width': 4, 'text': '0', 'font': ('Consolas', 8, 'normal')}

        componentes_generales = {
            'lbl_fecha_texto': ('frame_generales',
                                configuracion_label,
                                {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                None),
            'lbl_cajero_texto': ('frame_generales',
                          configuracion_label,
                          {'row': 1, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                          None),

            'lbl_fecha': ('frame_generales',
                          configuracion_label,
                          {'row': 0, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                          None),
            'lbl_cajero': ('frame_generales',
                           configuracion_label,
                           {'row': 1, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                           None),

            'btn_comentario': ('frame_btn_comentario','Warning', 'Comentario', None),
            'btn_cancelados': ('frame_btn_cancelados','Danger', 'Cancelados', None),

        }
        self._ventanas.crear_componentes(componentes_generales)

        componentes_totales = {
            'lbl_total_texto': ('frame_totales',
                                configuracion_label,
                                {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                None),
            'lbl_depositos_texto': ('frame_totales',
                                 configuracion_label,
                                 {'row': 1, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                 None),

            'lbl_anticipos_texto': ('frame_totales',
                                    configuracion_label,
                                    {'row': 2, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                    None),

            'lbl_gastos_texto': ('frame_totales',
                                    configuracion_label,
                                    {'row': 3, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                    None),

            'lbl_total_numero': ('frame_totales',
                                configuracion_label_numero,
                                {'row': 0, 'column': 2, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                None),
            'lbl_depositos_numero': ('frame_totales',
                                    configuracion_label_numero,
                                    {'row': 1, 'column': 2, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                    None),

            'lbl_anticipos_numero': ('frame_totales',
                                    configuracion_label_numero,
                                    {'row': 2, 'column': 2, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                    None),

            'lbl_gastos_numero': ('frame_totales',
                                 configuracion_label_numero,
                                 {'row': 3, 'column': 2, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                 None),

            'lbl_total': ('frame_totales',
                          configuracion_label,
                          {'row': 0, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                          None),
            'lbl_depositos': ('frame_totales',
                           configuracion_label,
                           {'row': 1, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                           None),

            'lbl_anticipos': ('frame_totales',
                                    configuracion_label,
                                    {'row': 2, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                    None),

            'lbl_gastos': ('frame_totales',
                                 configuracion_label,
                                 {'row': 3, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                 None),

            'btn_depositos': ('frame_btn_depositos', 'Primary', 'Detalles', None),
            'btn_anticipos': ('frame_btn_anticipos', 'Primary', 'Detalles', None),
            'btn_gastos': ('frame_btn_gastos', 'Primary', 'Detalles', None),

        }
        self._ventanas.crear_componentes(componentes_totales)

        componentes_efectivo = {
            'lbl_total_sistema_texto': ('frame_efectivo',
                                configuracion_label,
                                {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                None),
            'lbl_total_cajero_texto': ('frame_efectivo',
                                    configuracion_label,
                                    {'row': 1, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                    None),

            'lbl_diferencia_texto': ('frame_efectivo',
                                    configuracion_label,
                                    {'row': 2, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                    None),


            'lbl_total_sistema_numero': ('frame_efectivo',
                                 configuracion_label_numero,
                                 {'row': 0, 'column': 2, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                 None),

            'lbl_total_sistema': ('frame_efectivo',
                          configuracion_label,
                          {'row': 0, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                          None),
            'lbl_total_cajero': ('frame_efectivo',
                              configuracion_label,
                              {'row': 1, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                              None),

            'lbl_diferencia': ('frame_efectivo',
                              configuracion_label,
                              {'row': 2, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                              None),

            'btn_efectivo': ('frame_btn_efectivo', 'Primary', 'Detalles', None),


        }
        self._ventanas.crear_componentes(componentes_efectivo)

        componentes_tarjetas = {
            'lbl_total_tarjetas_texto': ('frame_tarjetas',
                                        configuracion_label,
                                        {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                        None),
            'lbl_total_tarjetas_debito_texto': ('frame_tarjetas',
                                     configuracion_label,
                                       {'row': 1, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                       None),

            'lbl_total_tarjetas_credito_texto': ('frame_tarjetas',
                                    configuracion_label,
                                     {'row': 2, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                     None),

            'lbl_total_tarjetas_numero': ('frame_tarjetas',
                                         configuracion_label_numero,
                                         {'row': 0, 'column': 2, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                         None),
            'lbl_total_tarjetas_debito_numero': ('frame_tarjetas',
                                        configuracion_label_numero,
                                        {'row': 1, 'column': 2, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                        None),

            'lbl_total_tarjetas_credito_numero': ('frame_tarjetas',
                                      configuracion_label_numero,
                                      {'row': 2, 'column': 2, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                      None),

            'lbl_total_tarjetas': ('frame_tarjetas',
                                  configuracion_label,
                                  {'row': 0, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                  None),
            'lbl_total_tarjetas_debito': ('frame_tarjetas',
                                 configuracion_label,
                                 {'row': 1, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                 None),

            'lbl_total_tarjetas_credito': ('frame_tarjetas',
                               configuracion_label,
                               {'row': 2, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                               None),

            'btn_debito': ('frame_btn_tarjetas_debito', 'Primary', 'Detalles', None),
            'btn_credito': ('frame_btn_tarjetas_credito', 'Primary', 'Detalles', None),

        }
        self._ventanas.crear_componentes(componentes_tarjetas)

        componentes_transferencias_y_cheques = {
            'lbl_total_transferencias_texto': ('frame_transferencias_cheques',
                                        configuracion_label,
                                         {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                         None),
            'lbl_total_cheques_texto': ('frame_transferencias_cheques',
                                          configuracion_label,
                                          {'row': 1, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                          None),


            'lbl_total_transferencias_numero': ('frame_transferencias_cheques',
                                          configuracion_label_numero,
                                          {'row': 0, 'column': 2, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                          None),
            'lbl_total_cheques_numero': ('frame_transferencias_cheques',
                                           configuracion_label_numero,
                                           {'row': 1, 'column': 2, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                           None),


            'lbl_total_transferencias': ('frame_transferencias_cheques',
                                   configuracion_label,
                                   {'row': 0, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                   None),
            'lbl_total_cheques': ('frame_transferencias_cheques',
                                          configuracion_label,
                                          {'row': 1, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.W},
                                          None),


            'btn_trasferencias': ('frame_btn_transferencias', 'Primary', 'Detalles', None),
            'btn_cheques': ('frame_btn_cheques', 'Primary', 'Detalles', None),

        }
        self._ventanas.crear_componentes(componentes_transferencias_y_cheques)

    def _cargar_eventos(self):
        eventos = {
            'btn_comentario': self._comentario_corte,
            'btn_cancelados':lambda: self._cargar_tabla_detalles('cancelados'),
            'btn_depositos':lambda: self._cargar_tabla_detalles('depositos'),
            'btn_anticipos':lambda: self._cargar_tabla_detalles('anticipos'),
            'btn_gastos':lambda: self._cargar_tabla_detalles('gastos'),
            'btn_efectivo':lambda: self._cargar_tabla_detalles('efectivo'),
            'btn_debito':lambda: self._cargar_tabla_detalles('debito'),
            'btn_credito': lambda: self._cargar_tabla_detalles('credito'),
            'btn_trasferencias':lambda: self._cargar_tabla_detalles('tranferencias'),
            'btn_cheques': lambda: self._cargar_tabla_detalles('cheques'),

        }
        self._ventanas.cargar_eventos(eventos)

    def _rellenar_componentes(self):
        #rellenar titulos
        diferencia_texto = 'Faltante:' if self._parametros_corte['monto_sobrante'] == 0 else 'Sobrante:'

        titulos = {
            'lbl_fecha': self._fecha,
            'lbl_cajero': self._user_name,
            'lbl_fecha_texto':'Fecha:',
            'lbl_cajero_texto': 'Cajero(a):',
            'lbl_total_texto': 'Total cobrado:',
            'lbl_depositos_texto': 'Depósitos:',
            'lbl_anticipos_texto': 'Anticipos:',
            'lbl_gastos_texto': 'Gastos:',
            'lbl_total_sistema_texto': 'Total sistema:',
            'lbl_total_cajero_texto': 'Total cajero(a):',
            'lbl_diferencia_texto': diferencia_texto,
            'lbl_total_tarjetas_texto': 'Total tarjetas:',
            'lbl_total_tarjetas_debito_texto': 'Débito:',
            'lbl_total_tarjetas_credito_texto': 'Crédito:',
            'lbl_total_transferencias_texto': 'Transferencias:',
            'lbl_total_cheques_texto': 'Cheques:',
        }
        for componente, input in titulos.items():
            self._ventanas.insertar_input_componente(componente, input)

        # rellenar montos
        conversion_moneda = self._utilerias.convertir_decimal_a_moneda
        diferencia = self._parametros_corte['monto_faltante'] if self._parametros_corte['monto_sobrante'] == 0 else self._parametros_corte['monto_sobrante']
        montos = {
            'lbl_total': self._parametros_corte.get('monto_total_cobrado','$0.00'),
            'lbl_depositos': self._parametros_corte.get('monto_depositos','$0.00'),
            'lbl_anticipos':self._parametros_corte.get('monto_anticipos','$0.00'),
            'lbl_gastos': self._parametros_corte.get('monto_gastos','$0.00'),
            'lbl_total_sistema': self._parametros_corte.get('monto_efectivo_menos_rubros','$0.00'),
            'lbl_total_cajero': self._parametros_corte.get('monto_efectivo_cajero','$0.00'),
            'lbl_diferencia': diferencia,
            'lbl_total_tarjetas': self._parametros_corte.get('monto_tarjetas','$0.00'),
            'lbl_total_tarjetas_debito': self._parametros_corte.get('monto_tarjetas_debito','$0.00'),
            'lbl_total_tarjetas_credito': self._parametros_corte.get('monto_tarjetas_credito','$0.00'),
            'lbl_total_transferencias': self._parametros_corte.get('monto_transferencias','$0.00'),
            'lbl_total_cheques': self._parametros_corte.get('monto_cheques','$0.00'),
        }
        for componente, input in montos.items():
            if input != '$0.00':
                input = conversion_moneda(input)
            self._ventanas.insertar_input_componente(componente, input)

        # rellenar numeros
        numeros = {
            'lbl_total_numero': self._documentos_cobrados,
            'lbl_depositos_numero': len(self._depositos_emitidos),
            'lbl_anticipos_numero': len(self._parametros_corte['anticipos_capturados']),
            'lbl_gastos_numero': len(self._parametros_corte['gastos_capturados']),
            'lbl_total_sistema_numero': self._documentos_efectivo,
            'lbl_total_tarjetas_numero': self._documentos_tarjetas,
            'lbl_total_tarjetas_debito_numero': self._documentos_tarjeta_debito,
            'lbl_total_tarjetas_credito_numero': self._documentos_tarjeta_credito,
            'lbl_total_transferencias_numero': self._documentos_transferencias,
            'lbl_total_cheques_numero': self._documentos_cheques,

        }
        agrudables_por_financial_opeation_id = [
            'lbl_total_numero', 'lbl_total_sistema_numero', 'lbl_total_tarjetas_numero',
            'lbl_total_tarjetas_debito_numero', 'lbl_total_tarjetas_credito_numero', 'lbl_total_transferencias_numero',
            'lbl_total_cheques_numero'
        ]
        for componente, input in numeros.items():
            if componente in agrudables_por_financial_opeation_id:
                input = len(set([reg['FinancialOperationID'] for reg in input]))

            self._ventanas.insertar_input_componente(componente, input)

    def _comentario_corte(self):

        consulta = self._base_de_datos.fetchall(
            'SELECT Comentario, ComentarioCobranza from zvwCortesDeCaja WHERE ID = ?',
            (self._id_corte,)
        )
        if consulta:
            comentario_cajero = consulta[0]['Comentario']
            comentario_cobranza = consulta[0]['ComentarioCobranza']

            comentarios = {
                'comentario': comentario_cajero,
                'comentario_cobranza': comentario_cobranza
            }
            ventana = self._ventanas.crear_popup_ttkbootstrap()
            instancia = ComentarioCorte(ventana, self._utilerias, comentarios, self._user_group_id)
            ventana.wait_window()

            if instancia.actualizar_comentario:
                self._base_de_datos.command(
                    'UPDATE zvwCortesDeCaja SET Comentario=?, ComentarioCobranza=? WHERE ID = ?',
                    (instancia.comentarios['comentario'], instancia.comentarios['comentario_cobranza'], self._id_corte)
                )
                self._parametros_corte['comentario'] = instancia.comentarios['comentario']
                self._parametros_corte['comentario_cobranza'] = instancia.comentarios['comentario_cobranza']

    def _respaldar_items_cobrados(self):
        # respaldar documentos de liquidacion
        self._base_de_datos.command("""
            DECLARE @UserID INT = ?
            DECLARE @Fecha NVARCHAR (20) = ?
            DECLARE @CorteID INT = ?
        
            INSERT INTO zvwCortesCajaItemDetalle
                (DocumentID, Fecha, Periodo, Folio, OfficialName, ModuleID, StatusPaidID, Globalized, 
                DestinationDocumentID, Cancelado, PaymentMethodID, Amount, CobradoPor, CorteID, FinancialOperationID,
                Hora, TotalCobro, CobroNota, Total, TotalPaid, Balance, CreatedBy)
            
            SELECT DISTINCT DocumentID, Fecha, Periodo, Folio, OfficialName, ModuleID, StatusPaidID, Globalized, 
                DestinationDocumentID, Cancelado, PaymentMethodID, Amount, CobradoPor, @CorteID, FinancialOperationID,
                Hora, TotalCobro, CobroNota, Total, TotalPaid, Balance, CreatedBy
			FROM(
                SELECT D.DocumentID, CAST(D.DateDocument as date) Fecha,
					DatePart(Year, D.DateDocument) Periodo,
				CAST(D.DateDocument as time) Hora,
                     ISNULL(D.FolioPrefix,'')+ISNULL(D.Folio,'') Folio,
                      E.OfficialName, D.ModuleID, D.StatusPaidID, D.Globalized, D.DestinationDocumentID,
                      CASE WHEN D.CancelledOn IS NULL THEN 0 ELSE 1 END Cancelado, DF.PaymentMethodID, DP.Amount, 
                      DP.FinancialOperationID,
                      CASE WHEN DF.VendorUserID = 0 THEN U.UserName ELSE UV.UserName END CobradoPor,
                      DF.Amount TotalCobro, DP.Amount CobroNota, D.Total, D.TotalPaid, D.Balance,
                      CASE WHEN DF.VendorUserID = 0 THEN DF.CreatedBy ELSE VendorUserID END CreatedBy
                FROM docFinancialOperation DF INNER JOIN
                    docDocumentPayment DP ON DF.FinancialOperationID = DP.FinancialOperationID INNER JOIN
                    docDocument D ON DP.DocumentID = D.DocumentID INNER JOIN
                    orgBusinessEntity E ON DF.BusinessEntityID = E.BusinessEntityID INNER JOIN
                    engUser U ON U.UserID = DF.CreatedBy LEFT OUTER JOIN
                    engUser UV ON DF.VendorUserID = UV.UserID
                WHERE DF.CreatedBy = @UserID 
                    AND CAST(DF.DateOperation AS date) = CAST(@Fecha AS date)
                    AND D.CancelledOn IS NULL
                    AND DP.DeletedON IS NULL
            
        ) TABLA
        ORDER BY TABLA.Folio DESC
        
        
        UPDATE D SET DailySettlementID = @CorteID
        FROM docFinancialOperation DF INNER JOIN
            docDocumentPayment DP ON DF.FinancialOperationID = DP.FinancialOperationID INNER JOIN
            docDocument D ON DP.DocumentID = D.DocumentID INNER JOIN
            orgBusinessEntity E ON DF.BusinessEntityID = E.BusinessEntityID INNER JOIN
            engUser U ON U.UserID = DF.CreatedBy LEFT OUTER JOIN
            engUser UV ON DF.VendorUserID = UV.UserID
        WHERE DF.CreatedBy = @UserID 
            AND CAST(DF.DateOperation AS date) = CAST(@Fecha AS date)
            AND D.CancelledOn IS NULL
            AND DP.DeletedON IS NULL
        """, (self._user_id, self._fecha, self._id_corte))

        # respaldar depositos de liquidacion
        for deposito in self._depositos_emitidos:
            parametros = (self._id_corte, deposito['ID'], deposito['Total'], deposito['Emisor'], deposito['EmisorUserID'])
            self._base_de_datos.command("""
                INSERT INTO zvwDepositosCortesDeCaja (
                    CorteID, DepositoID, MontoDeposito, UsuarioDesposito, CreatedBy)
                VALUES(?,?,?,?,?)
            """, parametros)

            self._base_de_datos.command('UPDATE zvwDepositosDiariosCayal SET CorteID = ? WHERE ID = ?',
                                        (self._id_corte, deposito['ID']))

        # respaldar efectivo corte
        monedas_capturadas = self._parametros_corte['monedas_capturadas']
        billetes_capturados = self._parametros_corte['billetes_capturados']
        monto_billetes = self._parametros_corte['monto_billetes']
        monto_monedas = self._parametros_corte['monto_monedas']

        parametros_efectivo = (self._id_corte,
                               monto_billetes + monto_monedas,
                               monedas_capturadas[50]['cantidad'],
                               monedas_capturadas[20]['cantidad'],
                               monedas_capturadas[1]['cantidad'],
                               monedas_capturadas[2]['cantidad'],
                               monedas_capturadas[5]['cantidad'],
                               monedas_capturadas[10]['cantidad'],
                               billetes_capturados[20]['cantidad'],
                               billetes_capturados[50]['cantidad'],
                               billetes_capturados[100]['cantidad'],
                               billetes_capturados[200]['cantidad'],
                               billetes_capturados[500]['cantidad'],
                               billetes_capturados[1000]['cantidad']
                               )
        self._base_de_datos.command("""
            INSERT INTO zvwRelacionEfectivoCortesCaja (
                        CorteID,TotalEfectivo,Monedas50,Monedas20,Monedas1,
                        Monedas2,Monedas5,Monedas10,Billetes20, Billetes50,
                        Billetes100,Billetes200,Billetes500,Billetes1000)
            VALUES (?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?)
            """, (parametros_efectivo))

    def _crear_corte_caja_en_base_datos(self):

        # afectacion tabla principal
        parametros_corte = (
            len(self._documentos_cobrados),
            self._parametros_corte['numero_facturas'],
            self._parametros_corte['numero_notas'],
            self._parametros_corte['monto_total_cobrado'],
            len(self._depositos_emitidos),
            self._parametros_corte['monto_depositos'],
            self._parametros_corte['monto_efectivo_menos_rubros'],
            self._parametros_corte['monto_efectivo_cajero'],
            len(self._documentos_transferencias),
            self._parametros_corte['monto_transferencias'],
            len(self._documentos_tarjetas),
            self._parametros_corte['monto_tarjetas'],
            len(self._documentos_tarjeta_debito),
            self._parametros_corte['monto_tarjetas_debito'],
            len(self._documentos_tarjeta_credito),
            self._parametros_corte['monto_tarjetas_credito'],
            len(self._documentos_cheques),
            self._parametros_corte['monto_cheques'],
            len(self._parametros_corte['anticipos_capturados']),
            self._parametros_corte['monto_anticipos'],
            len(self._parametros_corte['gastos_capturados']),
            self._parametros_corte['monto_gastos'],
            abs(self._parametros_corte['monto_sobrante']),
            abs(self._parametros_corte['monto_faltante']),
            self._user_name,
            self._user_id
        )

        self._id_corte = self._base_de_datos.command("""
            INSERT INTO zvwCortesDeCaja(
                Fecha, Ventas, Facturas, Notas, TotalVentas,
                Depositos, TotalDepositos, EfectivoSistema, EfectivoCajero, 
                Transferencias, TotalTransferencias, 
                Tarjetas, TotalTarjetas, TDebito, 
                TotalDebito, TCredito, TotalCredito, Cheques, TotalCheques, Anticipos, TotalAnticipos,
                Gastos, TotalGastos, Sobrante, Faltante, Cajero, UsuarioID)
            VALUES (GETDATE(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, parametros_corte)

        #  afectacion en tablas de detalle
        for gasto in self._parametros_corte['gastos_capturados']:

            monto_gasto = gasto['monto_gasto']
            receptor_gasto = gasto['receptor_gasto']

            self._base_de_datos.command("""
                INSERT INTO zvwGastosCorteDeCaja(CorteID, ReceptorGasto, MontoGasto)
                VALUES (?, ?, ?)
            """, (self._id_corte, receptor_gasto, monto_gasto))

        for anticipo in self._parametros_corte['anticipos_capturados']:
            monto_anticipo = anticipo['monto_anticipo']
            emisor_anticipo = anticipo['emisor_anticipo']

            self._base_de_datos.command("""
                            INSERT INTO zvwAnticiposCorteDeCaja(CorteID, EmisorAnticipo, MontoAnticipo)
                            VALUES (?, ?, ?)
                        """, (self._id_corte, emisor_anticipo, monto_anticipo))

    def _consultar_ventas_canceladas(self):
        consulta = self._base_de_datos.fetchall("""
            DECLARE @UserID INT = ?
            DECLARE @Fecha NVARCHAR(20) = ?
            DECLARE @CorteID INT = ?
            
            SELECT
                CAST( D.CancelledOn as date) Cancelado,
                ISNULL(D.FolioPrefix,'')+ISNULL(D.Folio,'') Folio, ISNULL( cc.Sustituye,'') Sustituye,
                U.UserName Captura,
                UC.UserName Cancela, D.Total, D.Balance, CC.Motivo, Cc.Comentario
            FROM docDocument D INNER JOIN
                zvwComentariosVentasCanceladas CC ON D.DocumentID = CC.DocumentID INNER JOIN
                engUser UC ON D.CancelledBy = UC.UserID INNER JOIN
                engUser U ON D.CreatedBy = U.UserID
            WHERE D.CreatedBy = @UserID 
            AND CAST(D.CreatedOn as date) = CAST(@Fecha as date)
            AND D.CancelledOn IS NOT NULL
            AND D.ModuleID IN (1400,1319,158,21)
            AND D.DailySettlementID = @CorteID
        """, (self._user_id, self._fecha, self._id_corte))

        self._documentos_cancelados = consulta
        return consulta

    def _cargar_tabla_detalles(self, tipo):

        acciones_por_tipo = {
            'cancelados': self._documentos_cancelados,
            'depositos': self._depositos_emitidos,
            'anticipos': self._parametros_corte['anticipos_capturados'],
            'gastos': self._parametros_corte['gastos_capturados'],
            'efectivo': self._documentos_efectivo,
            'debito': self._documentos_tarjeta_debito,
            'credito': self._documentos_tarjeta_credito,
            'tranferencias': self._documentos_transferencias,
            'cheques': self._documentos_cheques
        }

        consulta = acciones_por_tipo[tipo]

        if not consulta:
            self._ventanas.mostrar_mensaje('No se encontró información relacionada al rubro seleccionado.')
            return

        ventana = self._ventanas.crear_popup_ttkbootstrap()

        if tipo in ('efectivo', 'debito', 'credito', 'tranferencias', 'cheques'):
            instancia = TablaDetalles(ventana, self._utilerias, consulta)
        else:

            instancia = TablaDetalles(ventana, self._utilerias, consulta, tipo)
        ventana.wait_window()

    def _buscar_ventas_canceladas(self):
        return self._base_de_datos.fetchall("""
                DECLARE @UserID INT = ?
                DECLARE @Fecha NVARCHAR(20) = ?
                DECLARE @CorteID INT = ?

                SELECT
                    CAST( D.CancelledOn as date) Cancelado,
                    ISNULL(D.FolioPrefix,'')+ISNULL(D.Folio,'') Folio, ISNULL( cc.Sustituye,'') Sustituye,
                    U.UserName Captura,
                    UC.UserName Cancela, D.Total, D.Balance, CC.Motivo, Cc.Comentario
                FROM docDocument D INNER JOIN
                    zvwComentariosVentasCanceladas CC ON D.DocumentID = CC.DocumentID INNER JOIN
                    engUser UC ON D.CancelledBy = UC.UserID INNER JOIN
                    engUser U ON D.CreatedBy = U.UserID
                WHERE D.CreatedBy = @UserID 
                AND CAST(D.CreatedOn as date) = CAST(@Fecha as date)
                AND D.CancelledOn IS NOT NULL
                AND D.ModuleID IN (1400,1319,158,21)
                AND D.DailySettlementID = @CorteID
            
            """, (self._user_id, self._fecha, self._id_corte))
