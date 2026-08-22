import tkinter as tk
from cayal.util import Utilerias
from cayal.comandos_base_datos import ComandosBaseDatos
from .billetes_cajeros import BilletesCajeros
from .morralla_cajeros import MorrallaCajeros
from .anticipos_cajeros import AnticiposCajeros
from .gastos_cajeros import GastosCajeros
from .corte_de_caja import CorteDeCaja
from cayal.ventanas import Ventanas

class PanelPrincipal:
    def __init__(self, master, parametros):
        self._master = master
        self._parametros = parametros

        self._inicializar_clases_auxiliares()
        self._inicializar_variables_de_instancia()

        self._crear_frames()
        self._crear_barra_herramientas()
        self._crear_componentes()
        self._cargar_eventos()
        self._consultar_documentos_cobrados()

        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Corte de caja')
        self._validaciones_previas()

    def _inicializar_clases_auxiliares(self):
        self._utilerias = Utilerias()

        self._base_de_datos = ComandosBaseDatos()
        self._ventanas = Ventanas(self._master)

    def _inicializar_variables_de_instancia(self):
        self._user_id = self._parametros.id_usuario
        self._fecha = self._parametros.fecha
        self._ventas_efectivo = 0
        self._documentos_cobrados = []

        self._monto_total_monedas = 0
        self._monto_total_billetes = 0
        self._monto_total_gastos = 0
        self._monto_total_anticipos = 0
        self._monto_total_cheques = 0

        self._billetes_capturados = {20: {'cantidad': 0, 'monto': 0},
                                     50: {'cantidad': 0, 'monto': 0},
                                     100: {'cantidad': 0, 'monto': 0},
                                     200: {'cantidad': 0, 'monto': 0},
                                     500: {'cantidad': 0, 'monto': 0},
                                     1000: {'cantidad': 0, 'monto': 0}
                                     }

        self._monedas_capturadas = {20: {'cantidad': 0, 'monto': 0},
                                    50: {'cantidad': 0, 'monto': 0},
                                    1: {'cantidad': 0, 'monto': 0},
                                    2: {'cantidad': 0, 'monto': 0},
                                    5: {'cantidad': 0, 'monto': 0},
                                    10: {'cantidad': 0, 'monto': 0}
                                    }

        self._cheques_capturados = []
        self._anticipos_capturados = []
        self._gastos_capturados = []

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),
            'frame_herramientas': ('frame_principal', None,
                                   {'row': 0, 'column': 1, 'padx': 25, 'pady': 5, 'sticky': tk.E}),
            'frame_botones': ('frame_principal', None,
                                   {'row': 1, 'column': 1, 'padx': 25, 'pady': 5, 'sticky': tk.E}),
        }
        self._ventanas.crear_frames(frames)

    def _cargar_eventos(self):
        eventos = {
            'btn_cerrar_corte': self._llamar_corte_caja,
            'btn_cancelar': self._master.destroy
        }
        self._ventanas.cargar_eventos(eventos)

    def _crear_componentes(self):
        componentes = {
            'btn_cerrar_corte': ('frame_botones', 'Warning', 'Corte caja', None),
            'btn_cancelar': ('frame_botones', 'Danger', 'Cancelar', None),
        }

        self._ventanas.crear_componentes(componentes)
        self._ventanas.bloquear_componente('btn_cerrar_corte')

    def _crear_barra_herramientas(self):
        self.barra_herramientas = [
            {'nombre_icono': 'Monedas.ico', 'etiqueta': 'Monedas', 'nombre': 'morralla',
             'hotkey': '$ 0.00', 'comando': self._llamar_morralla_cajeros},
            {'nombre_icono': 'Billetes.ico', 'etiqueta': 'Billetes', 'nombre': 'billetes',
             'hotkey': '$ 0.00', 'comando': self._llamar_billetes_cajeros},
            {'nombre_icono': 'Anticipos.ico', 'etiqueta': 'Anticipos', 'nombre': 'anticipos',
             'hotkey': '$ 0.00', 'comando': self._llamar_anticipos_cajeros},
            {'nombre_icono': 'Gastos.ico', 'etiqueta': 'Gastos', 'nombre': 'gastos',
             'hotkey': '$ 0.00', 'comando': self._llamar_gastos_cajeros},
        ]
        self.elementos_barra_herramientas = self._ventanas.crear_barra_herramientas(self.barra_herramientas,
                                                                                    'frame_herramientas')
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]

        for etiqueta in self.hotkeys_barra_herramientas:
            etiqueta.config(font=('Consolas', 10, 'bold'), anchor='e', )

    def _validaciones_previas(self):

        if not self._documentos_cobrados:
            self._mostrar_mensaje('No tiene ninguna venta capturada.')
            self._master.destroy()
            return

        if not self._validar_ventas_globalizadas_del_turno():
            self._master.destroy()
            return

        if not self._validar_facturas_timbradas():
            self._master.destroy()
            return

        if not self._validar_ventas_con_saldo():
            self._master.destroy()
            return

        self._validar_totales_corte()

    def _mostrar_mensaje(self, mensaje):
        self._ventanas.mostrar_mensaje(mensaje=mensaje, master=self._master)

    def _llamar_billetes_cajeros(self):
        ventana = self._ventanas.crear_popup_ttkbootstrap()
        instancia = BilletesCajeros(ventana, self._parametros, self._base_de_datos, self._utilerias)
        ventana.wait_window()

        if instancia.monto_total_cheques != 0 or instancia.monto_total_billetes != 0:
            self._monto_total_billetes = instancia.monto_total_billetes
            self._billetes_capturados = instancia.billetes_capturados
            self._cheques_capturados = instancia.cheques_capturados

            self._validar_totales_corte()

    def _llamar_morralla_cajeros(self):
        ventana = self._ventanas.crear_popup_ttkbootstrap()
        instancia = MorrallaCajeros(ventana, self._parametros, self._base_de_datos, self._utilerias)
        ventana.wait_window()

        if instancia.monto_total_monedas != 0:
            self._monto_total_monedas = instancia.monto_total_monedas
            self._monedas_capturadas = instancia.monedas_capturadas
            self._validar_totales_corte()

    def _llamar_anticipos_cajeros(self):
        self._anticipos_capturados = []
        ventana = self._ventanas.crear_popup_ttkbootstrap()
        instancia = AnticiposCajeros(ventana,
                                     self._parametros,
                                     self._base_de_datos,
                                     self._utilerias
                                     )
        ventana.wait_window()

        if len(instancia.anticipos_capturados) > 0:
            self._anticipos_capturados = instancia.anticipos_capturados
            self._validar_totales_corte()

    def _llamar_gastos_cajeros(self):
        ventana = self._ventanas.crear_popup_ttkbootstrap()
        instancia = GastosCajeros(ventana, self._parametros, self._base_de_datos, self._utilerias)
        ventana.wait_window()

        if len(instancia.gastos_capturados) > 0:
            self._gastos_capturados = instancia.gastos_capturados

            self._validar_totales_corte()

    def _procesar_gastos(self):
        if len(self._gastos_capturados) > 0:
            etiqueta_gastos = self.hotkeys_barra_herramientas[3]

            monto_acumulado = 0
            for gasto in self._gastos_capturados:
                monto_acumulado += gasto['monto_gasto']

            self._monto_total_gastos = monto_acumulado
            monto_acumulado_moneda = self._utilerias.convertir_decimal_a_moneda(monto_acumulado)
            etiqueta_gastos.config(text=monto_acumulado_moneda)

    def _procesar_anticipos(self):
        if len(self._anticipos_capturados) > 0:
            etiqueta_anticipos = self.hotkeys_barra_herramientas[2]

            monto_acumulado = 0
            for anticipo in self._anticipos_capturados:
                monto_acumulado += anticipo['monto_anticipo']

            self._monto_total_anticipos = monto_acumulado
            monto_acumulado_moneda = self._utilerias.convertir_decimal_a_moneda(monto_acumulado)
            etiqueta_anticipos.config(text=monto_acumulado_moneda)

    def _procesar_monedas(self):
        etiqueta_monedas = self.hotkeys_barra_herramientas[0]
        monto_total_monedas_moneda = self._utilerias.convertir_decimal_a_moneda(self._monto_total_monedas)
        etiqueta_monedas.config(text=monto_total_monedas_moneda)

    def _procesar_cheques(self):
        if not self._cheques_capturados:
            return

    def _procesar_billetes(self):
        etiqueta_billetes = self.hotkeys_barra_herramientas[1]
        monto_total_billetes_moneda = self._utilerias.convertir_decimal_a_moneda(self._monto_total_billetes)
        etiqueta_billetes.config(text=monto_total_billetes_moneda)

    def _validar_totales_corte(self):

        self._procesar_anticipos()
        self._procesar_gastos()
        self._procesar_billetes()
        self._procesar_monedas()
        self._procesar_cheques()

        if self._monto_total_monedas != 0 or self._monto_total_billetes != 0 or self._ventas_efectivo == 0\
                or self._monto_total_anticipos != 0 or self._monto_total_gastos > 0:

            self._ventanas.desbloquear_componente('btn_cerrar_corte')
            self._ventanas.refrescar_tamano_forma()

    def _llamar_corte_caja(self):

        parametros_corte = {'monto_monedas': self._monto_total_monedas,
                            'monto_billetes': self._monto_total_billetes,
                            'monto_gastos' : self._monto_total_gastos,
                            'monto_anticipos' : self._monto_total_anticipos,
                            'billetes_capturados' : self._billetes_capturados,
                            'monedas_capturadas' : self._monedas_capturadas,
                            'anticipos_capturados': self._anticipos_capturados,
                            'gastos_capturados' : self._gastos_capturados
                            }

        ventana = self._ventanas.crear_popup_ttkbootstrap()
        instancia = CorteDeCaja(ventana,
                                self._parametros,
                                self._base_de_datos,
                                self._utilerias,
                                parametros_corte,
                                self._documentos_cobrados)
        self._master.withdraw()
        ventana.wait_window()
        self._master.destroy()

    def _consultar_documentos_cobrados(self):
        consulta = self._base_de_datos.fetchall("""
        DECLARE @UserID INT = ?
        DECLARE @Fecha NVARCHAR (20) = ?
	   
	        SELECT DISTINCT
                DocumentID, Fecha, Periodo, Hora, Folio, OfficialName, ModuleID, StatusPaidID,
                Globalized, DestinationDocumentID, Cancelado, PaymentMethodID, TotalCobro, CobroNota, 
                Total, TotalPaid, Balance, FinancialOperationID, CobradoPor, CreatedBy
	  
			FROM(
                SELECT D.DocumentID, CAST(D.DateDocument as date) Fecha,
					DatePart(Year, D.DateDocument) Periodo,
				CAST(D.DateDocument as time) Hora,
                     ISNULL(D.FolioPrefix,'')+ISNULL(D.Folio,'') Folio,
                      E.OfficialName, D.ModuleID, D.StatusPaidID, D.Globalized, D.DestinationDocumentID,
                      CASE WHEN D.CancelledOn IS NULL THEN 0 ELSE 1 END Cancelado, DF.PaymentMethodID, 
                      DF.Amount TotalCobro, DP.Amount CobroNota, DP.FinancialOperationID,
                      CASE WHEN DF.VendorUserID = 0 THEN U.UserName ELSE UV.UserName END CobradoPor,
                      D.Total, D.TotalPaid, D.Balance,
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
       ORDER BY   TABLA.FinancialOperationID ASC, TABLA.ModuleID
        """, (self._user_id, self._fecha))

        for reg in consulta:

            if reg['PaymentMethodID'] == 1:
                self._ventas_efectivo += 1

        self._documentos_cobrados = consulta

    def _validar_ventas_globalizadas_del_turno(self):
        consulta_facturas_globales = self._base_de_datos.fetchall("""
                            SELECT DISTINCT D.DestinationDocumentID,
                                ISNULL(DF.FolioPrefix, '')
                                    + ISNULL(DF.Folio, '') Folio,
                                ISNULL(CFD.CFDStatusID, 0) CFDStatusID
                            FROM docDocument D LEFT JOIN
								docDocument DF
                                    ON D.DestinationDocumentID = DF.DocumentID LEFT JOIN
                                docDocumentCFD CFD
                                    ON DF.DocumentID = CFD.DocumentID
                            WHERE D.ModuleID = 158
                                AND CAST(D.CreatedON as date) = CAST(GETDATE() as date)
                                AND D.CancelledOn IS NULL
                                AND D.CreatedBy = ?
								AND (ISNULL(D.DestinationDocumentID, 0) = 0
                                    OR DF.CancelledOn IS NULL)
                            """, (self._user_id,))

        if any(
                int(factura['DestinationDocumentID'] or 0) == 0
                for factura in consulta_facturas_globales
        ):
            self._mostrar_mensaje('Tiene tickets pendientes de globalizar.')
            return False

        pendientes_timbrado = [
            factura
            for factura in consulta_facturas_globales
            if int(factura['DestinationDocumentID'] or 0) > 0
            and int(factura['CFDStatusID'] or 0) != 3
        ]
        if pendientes_timbrado:
            folios = ', '.join(
                str(factura['Folio'] or factura['DestinationDocumentID'])
                for factura in pendientes_timbrado
            )
            return bool(self._ventanas.mostrar_mensaje_pregunta(
                'Las siguientes facturas globales están pendientes de '
                'timbrado: {}.\n\n¿Desea proceder con el corte de caja '
                'a pesar de ello?'.format(folios),
                master=self._master,
            ))

        return True

    def _validar_ventas_con_saldo(self):
        consulta = self._base_de_datos.fetchall("""
            DECLARE @UserID INT = ?
            DECLARE @Fecha NVARCHAR (20) = ?
            
            SELECT DocumentID, No DocFolio
            FROM vwLBSDocCustomerSaleList
            WHERE CreatedBy = @UserID 
            AND StatusPaidID <> 1 
            AND CanceladoIcon = 0
            AND CAST(Fecha as date) = CAST(@Fecha as date)
            
        """, (self._user_id, self._fecha))

        if not consulta:
            return True

        if len(consulta) == 1:
            folio = consulta[0]['DocFolio']
            self._mostrar_mensaje(f'El documento {folio} no ha sido saldado.')
            return False

        if len(consulta) > 1:
            documentos_no_timbrados = [documento['DocFolio'] for documento in consulta]
            self._mostrar_mensaje(f'Los documentos {documentos_no_timbrados} no han sido saldados.')
            return False

    def _validar_facturas_timbradas(self):

        if not self._utilerias.horario_cierre_cayal():
            return True

        consulta = self._base_de_datos.fetchall("""
            DECLARE @UserID INT = ?
            
            SELECT D.DocumentID, ISNULL(D.FolioPrefix,'')+ISNULL(D.Folio,'') DocFolio, D.ModuleID
            FROM docDocument D INNER JOIN
                docDocumentCFD CFD ON D.DocumentID = CFD.DocumentID
            WHERE D.ModuleID IN (21, 1400,1319) 
            AND CAST(D.CreatedON as date) = CAST(GETDATE() as date)
            AND D.CancelledOn IS NULL
            AND CFD.CFDStatusID <> 3
            AND D.CreatedBy = @UserID
        """, (self._user_id,))

        if not consulta:
            return True

        if len(consulta) == 1:
            folio = consulta[0]['DocFolio']
            self._mostrar_mensaje(f'El documento {folio} no ha sido timbrado.')
            return False

        if len(consulta) > 1:
            documentos_no_timbrados = [documento['DocFolio'] for documento in consulta]
            self._mostrar_mensaje(f'Los documentos {documentos_no_timbrados} no han sido timbrados.')
            return False



