import tkinter as tk
import ttkbootstrap as ttk
import ttkbootstrap.dialogs
from cayal.util import Utilerias
from cayal.comandos_base_datos import ComandosBaseDatos
from ttkbootstrap import dialogs
from saldar_documentos import SaldarDocumentos
from datetime import datetime

class ControladorSaldarCartera:
    def __init__(self, parametros):
        self._utilerias = Utilerias()
        self._parametros = parametros
        self._cadena_conexion = self._parametros.cadena_conexion
        self._base_de_datos = ComandosBaseDatos(self._cadena_conexion)

        self._usuario_id = self._parametros.id_usuario
        self._business_entity_id = self._parametros.id_principal

        self._consulta_formas_pago = []
        self._consulta_terminales_bancarias = []

        self._consulta_documentos = None

        self._documentos_seleccionados = []
        self._documentos_seleccionados_previo = []

        self.ventanas = None
        self.master = None

    def buscar_monto_cartera(self):
        return self._base_de_datos.fetchone("""
                    SELECT FORMAT(SUM(Balance), 'C', 'es-MX') Cartera
                    FROM docDocument D
                    WHERE D.CancelledOn IS NULL AND D.StatusPaidID<>1 
                        AND D.BusinessEntityID= ? AND D.ModuleID IN (21,1400,1319) AND D.Balance<>0 
                """, (self._business_entity_id,))

    def rellenar_tabla(self, tabla, columnas):
        consulta = self._buscar_documentos_con_saldo()
        self.ventanas.rellenar_treeview(tabla, columnas, consulta, 4)

    def _buscar_documentos_con_saldo(self):
        if not self._consulta_documentos:
            self._consulta_documentos = self._base_de_datos.fetchall("""
                SELECT ROW_NUMBER() OVER(ORDER BY D.DocumentID ASC) AS N,
                   CAST(D.CreatedOn AS date) AS Fecha,
                   CASE WHEN D.chkCustom1 = 1 THEN 'Remisión' ELSE 'Factura' END AS TipoDocto,
                   ISNULL(D.FolioPrefix,'')+ISNULL(D.Folio,'') AS Folio,
                   CFD.FormaPago as FP,
                   FORMAT(D.Total, 'C', 'es-MX') AS Total,
                   FORMAT(D.TotalPaid, 'C', 'es-MX') AS Pagado,
                   FORMAT(D.Balance, 'C', 'es-MX') AS Saldo,
                   CASE WHEN A.DepotName IS NULL THEN '' ELSE A.DepotName END AS Sucursal,
                   D.DocumentID
                FROM docDocument D
                    INNER JOIN docDocumentExtra X ON D.DocumentID=X.DocumentID
                    LEFT OUTER JOIN orgDepot A ON X.BusinessEntityDepotID=A.DepotID
                    INNER JOIN docDocumentCFD CFD ON D.DocumentID=CFD.DocumentID
                    INNER JOIN vwcboAnexo20v33_FormaPago FP ON CFD.FormaPago=FP.Clave
                    WHERE D.CancelledOn IS NULL
                      AND D.StatusPaidID<>1
                      AND D.BusinessEntityID=?
                      AND D.ModuleID IN (21,1400,1319)
                      AND D.Balance<>0
                    ORDER BY CAST(D.CreatedOn AS date)
                    """, (self._business_entity_id,))

        return self._consulta_documentos

    def buscar_official_name(self):
        return self._base_de_datos.fetchone(
            'SELECT OfficialName FROM orgBusinessEntity WHERE BusinessEntityID = ?',
            (self._business_entity_id,))

    def _bloquear_forma(self):
        tabla = self.ventanas.componentes_forma['tvw_tabla_documentos']
        tabla.configure(bootstyle='primary', selectmode="none")

        tbx_monto = self.ventanas.componentes_forma['tbx_monto']
        tbx_monto.config(state='disabled')

        frame = self.ventanas.componentes_forma['frame_botones_aplicar']
        widgets = frame.winfo_children()

        for widget in widgets:
            try:
                widget.config(state='disabled')
            except:
                pass

    def _desbloquear_forma(self):
        tbx_monto = self.ventanas.componentes_forma['tbx_monto']
        tbx_monto.config(state='enabled')

        tabla = self.ventanas.componentes_forma['tvw_tabla_documentos']
        tabla.configure(selectmode="extended")

        frame = self.ventanas.componentes_forma['frame_botones_aplicar']
        widgets = frame.winfo_children()
        for widget in widgets:
            try:
                widget.config(state='normal')
            except:
                pass

    def buscar_terminales_bancarias(self):
        if not self._consulta_terminales_bancarias:
            consulta = self._base_de_datos.buscar_terminales_bancarias()
            self._consulta_terminales_bancarias = consulta
            return [reg['Barcode'] for reg in self._consulta_terminales_bancarias]

    def buscar_formas_pago(self):
        if not self._consulta_formas_pago:
            consulta = self._base_de_datos.buscar_formas_de_pago()
            self._consulta_formas_pago = consulta
            return [reg['Value'] for reg in self._consulta_formas_pago]

    def _buscar_afiliacion(self):
        afiliacion = self.ventanas.obtener_input_componente('tbx_terminal')

        if not afiliacion:
            ttkbootstrap.dialogs.Messagebox.show_error('Debe escanear un valor a buscar.')
            return

        info_terminal = self._buscar_informacion_terminal('tbx')
        self._actualizar_datos_terminal_forma(info_terminal)

    def _buscar_afiliacion_seleccion(self):
        tbx_terminal = self.ventanas.componentes_forma['tbx_terminal']
        seleccion = self.ventanas.obtener_input_componente('cbx_terminal')

        if seleccion == 'Seleccione':
            tbx_terminal.delete(0, tk.END)
            return

        info_terminal = self._buscar_informacion_terminal('cbx')
        self._actualizar_datos_terminal_forma(info_terminal)

    def _actualizar_datos_terminal_forma(self, info_terminal):
        afiliacion = info_terminal['Afiliacion']
        barcode = info_terminal['Barcode']
        banco_nombre = info_terminal['Banco']

        self.ventanas.insertar_input_componente('lbl_banco', banco_nombre)
        self.ventanas.insertar_input_componente('tbx_terminal', barcode)

        cbx_terminal = self.ventanas.componentes_forma['cbx_terminal']
        valores = cbx_terminal['values']
        idx = valores.index(barcode)
        cbx_terminal.set(valores[idx])

    def _buscar_informacion_terminal(self, tipo):
        if tipo == 'cbx':
            seleccion = self.ventanas.obtener_input_componente('cbx_terminal')
            return [reg for reg in self._consulta_terminales_bancarias
                    if seleccion == reg['Barcode']][0]

        if tipo == 'tbx':
            barcode = self.ventanas.obtener_input_componente('tbx_terminal')

            info_terminal = [reg for reg in self._consulta_terminales_bancarias
                             if reg['Barcode'] == barcode]

            if not info_terminal:
                ttkbootstrap.dialogs.Messagebox.show_error('No se encontró ningún valor favor de validar.')
                return

            if info_terminal:
                return info_terminal[0]

    def seleccionar_documento(self):
        tvw_tabla_documentos = self.ventanas.componentes_forma['tvw_tabla_documentos']
        filas_seleccionadas = tvw_tabla_documentos.selection()

        if filas_seleccionadas:
            acumulado = self._utilerias.redondear_valor_cantidad_a_decimal(0)
            for fila in filas_seleccionadas:
                total_moneda = tvw_tabla_documentos.item(fila)['values'][7]
                total = self._utilerias.convertir_moneda_a_decimal(total_moneda)
                acumulado += total

            self._acualizar_acumulado(acumulado)

    def _acualizar_acumulado(self, acumulado):
        tbx_monto = self.ventanas.componentes_forma['tbx_monto']
        tbx_monto.delete(0, tk.END)
        tbx_monto.insert(0, acumulado)

        monto_cartera_moneda = self.ventanas.obtener_input_componente('lbl_cartera')
        monto_cartera = self._utilerias.convertir_moneda_a_decimal(monto_cartera_moneda)

        restante = abs(monto_cartera - acumulado)
        restante_moneda = self._utilerias.convertir_decimal_a_moneda(restante)

        self.ventanas.insertar_input_componente('lbl_restante', restante_moneda)

        acumulado_moneda = self._utilerias.convertir_decimal_a_moneda(acumulado)
        self.ventanas.insertar_input_componente('lbl_monto', acumulado_moneda)

    def aplicar_por_documento(self, tipo_documento =None):
        self.deshacer_saldado()

        tabla = self.ventanas.componentes_forma['tvw_tabla_documentos']
        filas = tabla.get_children()

        acumulado = self._utilerias.redondear_valor_cantidad_a_decimal(0)

        for fila in filas:
            tipo = tabla.item(fila)['values'][2]

            if tipo == tipo_documento or not tipo_documento:

                total_moneda = tabla.item(fila)['values'][7]
                total = self._utilerias.convertir_moneda_a_decimal(total_moneda)

                self._saldar_fila(fila)

                acumulado += total

                self.ventanas.colorear_fila_seleccionada_treeview('tvw_tabla_documentos', fila, 'success')

        self._acualizar_acumulado(acumulado)
        self._bloquear_forma()

    def aplicar_por_monto(self, tipo):

        monto = self.ventanas.obtener_input_componente('tbx_monto')
        monto = self._validar_monto(monto)

        if not monto:
            return

        if monto:
            filas_seleccionadas = self.deshacer_saldado('conservar_seleccion')
            self.ventanas.insertar_input_componente('tbx_monto', monto)
            tabla = self.ventanas.componentes_forma['tvw_tabla_documentos']

            if tipo == 'selección':
                filas = filas_seleccionadas

                if not filas:
                    ttkbootstrap.dialogs.Messagebox.show_error('Debe seleccionar por lo menos un documento')
                    return

            if tipo == 'auto':
                filas = tabla.get_children()

            acumulado = self._utilerias.redondear_valor_cantidad_a_decimal(0)

            for fila in filas:

                if monto <= self._utilerias.redondear_valor_cantidad_a_decimal(0):
                    break

                if monto > self._utilerias.redondear_valor_cantidad_a_decimal(0):
                    restante = self._saldar_fila(fila, monto)
                    saldado = monto - restante
                    monto = monto - saldado
                    acumulado += saldado

            self._acualizar_acumulado(acumulado)
            self._bloquear_forma()

    def _validar_monto(self, monto=None):
        monto = self.ventanas.componentes_forma['tbx_monto'] if not monto else monto
        if not monto:
            dialogs.Messagebox.show_error(parent=self.master,
                                          message='Monto a saldar no definido.')
            return False

        if not self._utilerias.es_cantidad(monto):
            dialogs.Messagebox.show_error(parent=self.master,
                                              message='Monto a saldar inválido.')
            return False

        if self._utilerias.redondear_valor_cantidad_a_decimal(monto) <= 0:
            dialogs.Messagebox.show_error(parent=self.master,
                                              message='El monto a saldar no puede ser cero o menos que cero.')
            return False

        return self._utilerias.redondear_valor_cantidad_a_decimal(monto)

    def deshacer_saldado(self, conservar_seleccion = None):
        self._desbloquear_forma()

        tabla = self.ventanas.componentes_forma['tvw_tabla_documentos']
        filas = tabla.get_children()
        filas_seleccionadas = tabla.selection()

        if not conservar_seleccion:
            for fila in filas:
                tabla.selection_remove(fila)

        for fila in filas:
            self.ventanas.colorear_fila_seleccionada_treeview('tvw_tabla_documentos', fila, 'white')

        if self._documentos_seleccionados:
            for documento in self._documentos_seleccionados_previo:
                cobrado = documento['Cobrado']
                saldo = documento['Saldo']
                fila = documento['Fila']

                valores_fila = tabla.item(fila)['values']
                valores_fila[6] = self._utilerias.convertir_decimal_a_moneda(cobrado)
                valores_fila[7] = self._utilerias.convertir_decimal_a_moneda(saldo)

                tabla.item(fila, values=valores_fila)

            self._documentos_seleccionados.clear()
            self._documentos_seleccionados_previo.clear()
            self._acualizar_acumulado(self._utilerias.redondear_valor_cantidad_a_decimal(0))

        return filas_seleccionadas

    def _saldar_fila(self, fila, monto = None):

        def saldar(tabla, cobrado, total, saldo, document_id):
            self._documentos_seleccionados.append(
                {'Cobrado': cobrado, 'Total': total, 'Saldo': saldo, 'DocumentID': document_id})

            # actualiza los valores de la tabla
            valores_fila = tabla.item(fila)['values']
            valores_fila[6] = self._utilerias.convertir_decimal_a_moneda(cobrado)
            valores_fila[7] = self._utilerias.convertir_decimal_a_moneda(saldo)
            tabla.item(fila, values=valores_fila)

        tabla = self.ventanas.componentes_forma['tvw_tabla_documentos']

        # obtiene los valores dese la tabla
        total = self._utilerias.convertir_moneda_a_decimal(tabla.item(fila)['values'][5])
        cobrado = self._utilerias.convertir_moneda_a_decimal(tabla.item(fila)['values'][6])
        saldo = self._utilerias.convertir_moneda_a_decimal(tabla.item(fila)['values'][7])
        document_id = tabla.item(fila)['values'][9]

        # respalda los valores previo a la afectacion
        self._documentos_seleccionados_previo.append({'Cobrado': cobrado, 'Saldo': saldo, 'Fila': fila})

        #saldado parcial o total segun corresponda

        # realiza los calculos correspondientes
        if monto:
            if saldo <= monto:
                monto -= saldo
                cobrado = saldo
                saldo = 0

                saldar(tabla, cobrado, total, saldo, document_id)
                self.ventanas.colorear_fila_seleccionada_treeview('tvw_tabla_documentos', fila, 'success')
                return monto

            if saldo > monto:
                cobrado = monto
                saldo -= monto
                monto = 0

                saldar(tabla, cobrado, total, saldo, document_id)
                self.ventanas.colorear_fila_seleccionada_treeview('tvw_tabla_documentos', fila, 'warning')
                return monto

        # saldado sin calculo
        if not monto:
            monto = 0
            monto += saldo
            cobrado = saldo
            saldo = 0

            saldar(tabla, cobrado, total, saldo, document_id)
            self.ventanas.colorear_fila_seleccionada_treeview('tvw_tabla_documentos', fila, 'success')
            return monto

    def calcular_cambio(self):
        recibido = self.ventanas.obtener_input_componente('tbx_recibido')

        if not self._utilerias.es_cantidad(recibido):
            ttkbootstrap.dialogs.Messagebox.show_error('Debe introducir un monto válido.')
            return

        recibido = self._utilerias.redondear_valor_cantidad_a_decimal(recibido)

        if recibido <= 0:
            ttkbootstrap.dialogs.Messagebox.show_error('Debe introducir un monto válido.')
            return

        monto_moneda = self.ventanas.obtener_input_componente('lbl_monto')
        monto = self._utilerias.convertir_moneda_a_decimal(monto_moneda)

        if recibido < monto:
            ttkbootstrap.dialogs.Messagebox.show_error('El monto recibido no debe ser menor al monto a cobrar.')
            return

        restante = recibido - monto

        restante_moneda = self._utilerias.convertir_decimal_a_moneda(restante)
        self.ventanas.insertar_input_componente('lbl_restante', restante_moneda)

    def saldar(self):
        forma_cobro = self.ventanas.obtener_input_componente('cbx_forma_cobro')
        fecha_afectacion = self.ventanas.obtener_input_componente('den_fecha_afectacion')
        modalidad = 0 if self.ventanas.obtener_input_componente('cbx_modalidad_cobro') == 'Un solo cobro' else 1
        terminal = self.ventanas.obtener_input_componente('cbx_terminal')

        if not self._documentos_seleccionados:
            dialogs.Messagebox.show_error(message='No hay ningún documento seleccionado.', parent=self.master)
            return

        if forma_cobro == 'Seleccione':
            dialogs.Messagebox.show_error(message='Debe seleccionar una forma de cobro.', parent=self.master)
            return

        if forma_cobro[0:2] in ('04', '28') and terminal == 'Seleccione':
            dialogs.Messagebox.show_error(message='Debe seleccionar una terminal bancaria o '
                                                  'escanear una.', parent=self.master)
            return

        forma_cobro_id = [cobro['ID'] for cobro in self._consulta_formas_pago if cobro['Value'] == forma_cobro]
        barcode = 0
        banco_id = 0
        afiliacion = 0
        forma_cobro_id = int(forma_cobro_id[0])

        if forma_cobro_id in (28, 4):
            barcode = self.ventanas.obtener_input_componente('tbx_terminal')
            afiliacion = [reg['Afiliacion'] for reg in self._consulta_terminales_bancarias
                          if reg['Barcode'] == barcode][0]

            info_terminal = self._buscar_informacion_terminal('cbx')
            banco_id = info_terminal['FinancialEntityID']

            if afiliacion == 'Seleccione':
                ttkbootstrap.dialogs.Messagebox.show_error('Debe seleccionar una terminal bancaria.')
                return

        fechahoy = datetime.today()
        fechahoy = fechahoy.date()
        #fecha_afectacion = datetime.strptime(fecha_afectacion, '%Y-%m-%d')
        #fecha_afectacion = fecha_afectacion.date()

        if fechahoy < fecha_afectacion:
            dialogs.Messagebox.show_error(message='La fecha del cobro no puede ser posterior al día de hoy.',
                                          parent=self.master)
            return
        else:
            saldar = 0
            if fechahoy > fecha_afectacion:
                validacion = dialogs.Messagebox.yesno(
                    message='La fecha del cobro es de un día anterior al día de hoy.\n'
                            '¿Desea proceder?', parent=self.master)
                saldar = 0 if validacion != 'No' else 1

            if saldar == 0:
                parametros_de_saldado = {'FormaCobro': forma_cobro_id, 'FechaAfectacion': fecha_afectacion,
                                         'Modalidad': modalidad, 'Documentos': self._documentos_seleccionados,
                                         'Afiliacion': afiliacion, 'BancoID': banco_id, 'Barcode': barcode}

                self._llamar_popup_saldado(parametros_de_saldado)

    def _llamar_popup_saldado(self, parametros_de_saldado):
        nueva_ventana = ttk.Toplevel()
        instancia = SaldarDocumentos(nueva_ventana, parametros_de_saldado, self._cadena_conexion,
                                     self._business_entity_id, self._usuario_id)
        nueva_ventana.wait_window()
        self.master.destroy()