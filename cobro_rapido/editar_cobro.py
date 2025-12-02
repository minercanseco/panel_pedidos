import datetime
import tkinter as tk
from cayal.ventanas import Ventanas
from popup_editar_cobro import ActualizarCobro

class EditarCobros:

    def __init__(self, master, base_de_datos, utilerias, parametros):
        self._master = master
        self._parametros = parametros
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias

        self._user_id = self._parametros.id_usuario
        self._document_id = self._parametros.id_principal
        self._consulta_cobros = self._buscar_cobros_relacionados()

        self._ventanas = Ventanas(self._master)
        self._crear_componentes()
        self._cargar_eventos()
        self._rellenar_tabla_cobros()
        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Editar cobros')

        self._master.lift()
        self._master.focus_force()

    def _buscar_cobros_relacionados(self):
        sql = """
                SELECT DF.Amount, FP.[Value], DF.Afiliacion,  DF.Barcode, ISNULL(TM.Banco, 'NO APLICA' ) Banco, 
                    U.UserName,
                    DF.FinancialOperationID, ISNULL(TM.FinancialEntityID,0)  FinancialEntityID, DF.PaymentMethodID

                FROM docDocumentPayment DP INNER JOIN
                     docFinancialOperation DF ON DP.FinancialOperationID = DF.FinancialOperationID INNER JOIN
                     vwcboAnexo20v33_FormaPago FP ON DF.PaymentMethodID = FP.ID LEFT OUTER JOIN
                zvwTerminalesBancariasCayalMenu TM ON DF.Barcode = TM.Barcode INNER JOIN
                engUser U ON DF.CreatedBy = U.UserID
                WHERE DF.DeletedOn IS NULL AND DP.DocumentID = ? AND CAST(DF.CreatedOn as date) = CAST(GETDATE() as date)
            """

        info_documento = self._base_de_datos.buscar_info_documento(self._document_id)
        if not info_documento:
            return

        if info_documento[0]['CancelledBy'] != 0:
            print('rechazado por cancelado')
            return
        if info_documento[0]['Globalized'] != 0:
            print('rechazado por globalizado')
            return

        return self._base_de_datos.fetchall(sql, (self._document_id,))

    def _crear_componentes(self):
        componentes = [
            ('tvw_cobros', self._crear_columnas()),
            ('btn_guardar', 'Guardar')
        ]
        self._ventanas.crear_formulario_simple(componentes)

    def _crear_columnas(self):
        return  [
            {'text': 'Monto', "stretch": False, 'width': 60, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {'text': 'Forma de Pago', "stretch": False, 'width': 160, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'Afiliacion', "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {'text': 'Barcode', "stretch": False, 'width': 80, 'column_anchor': tk.E,
             'heading_anchor': tk.E,
             'hide': 0},
            {'text': 'Banco', "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {'text': 'Usuario', "stretch": False, 'width': 90, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {'text': 'FinancialOperationID', "stretch": False, 'width': 60, 'column_anchor': tk.E,
             'heading_anchor': tk.E,
             'hide': 1},
            {'text': 'FinancialEntityID', "stretch": False, 'width': 60, 'column_anchor': tk.E,
             'heading_anchor': tk.E,
             'hide': 1},
            {'text': 'PaymentMethodID', "stretch": False, 'width': 60, 'column_anchor': tk.E,
             'heading_anchor': tk.E,
             'hide': 1}

        ]

    def _rellenar_tabla_cobros(self):
        self._ventanas.rellenar_treeview('tvw_cobros',
                                         self._crear_columnas(),
                                         self._consulta_cobros,
                                         valor_barra_desplazamiento=5,
                                         variar_color_filas=True)

    def _cargar_eventos(self):
        eventos = {
            'btn_cancelar':self._master.destroy,
            'btn_guardar':self._guardar_cambios,
            'tvw_cobros': (lambda event:self._llamar_poppup(), 'doble_click')
        }
        self._ventanas.cargar_eventos(eventos)

    def _llamar_poppup(self):

        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_cobros'):
            return

        fila = self._ventanas.obtener_seleccion_filas_treeview('tvw_cobros')

        if not fila:
            return

        valores_fila = self._ventanas.procesar_fila_treeview('tvw_cobros', fila)
        ventana = self._ventanas.crear_popup_ttkbootstrap(titulo='Editar')
        instancia = ActualizarCobro(ventana, self._parametros, self._base_de_datos, valores_fila)
        ventana.wait_window()

        if instancia.actualizar_fila:
            self._ventanas.actualizar_fila_treeview_diccionario('tvw_cobros', fila, instancia.valores_fila)

    def _guardar_cambios(self):
        filas = self._ventanas.obtener_filas_treeview('tvw_cobros')

        if not filas:
            self._master.destroy()

        for fila in filas:
            valores_fila = self._ventanas.procesar_fila_treeview('tvw_cobros', fila)

            financial_operation_id = valores_fila['FinancialOperationID']
            afiliacion = valores_fila['Afiliacion']
            financial_entity_id = valores_fila['FinancialEntityID']
            barcode = valores_fila['Barcode']
            payment_method_id = int(valores_fila['PaymentMethodID'])

            self._base_de_datos.command(
                """
                DECLARE @FormaPagoID INT = ?
                DECLARE @FinancialOperationID INT = ?
                DECLARE @BancoID INT = ?
                DECLARE @Afiliacion BIGINT = ?
                DECLARE @Barcode NVARCHAR(13) = ?
                 
                UPDATE docFinancialOperation SET PaymentMethodID = @FormaPagoID,
                                                BancoID = @BancoID,
                                                Afiliacion = @Afiliacion,
                                                Barcode = @Barcode
                WHERE FinancialOperationID = @FinancialOperationID
                
                """, (payment_method_id, financial_operation_id, financial_entity_id, afiliacion, barcode))

            self._base_de_datos.command(
                    """
                    DECLARE @FormaPagoID INT = ?
                    DECLARE @FinancialOperationID INT = ?
                    
                    UPDATE docDocument SET CobroTarjeta = (CASE WHEN @FormaPagoID = 4 THEN 4 
                                                                WHEN @FormaPagoID = 28 THEN 28
                                                                ELSE 0 END) 
                    WHERE DocumentID IN (
                        SELECT DocumentID FROM docDocumentPayment WHERE FinancialOperationID = @FinancialOperationID)
                    """, (payment_method_id, financial_operation_id))

        self._master.destroy()