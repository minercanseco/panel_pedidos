from cayal.util import Utilerias

from saldar_cartera.abrir_cajon import CajonCobro
from saldar_cartera.saldar_documentos import SaldarDocumentos
from datetime import datetime

class ControladorSaldarCartera:
    def __init__(self, interfaz, base_de_datos, parametros, cliente):
        self._interfaz = interfaz
        self._utilerias = Utilerias()
        self._parametros = parametros
        self._cliente = cliente
        self._base_de_datos = base_de_datos

        self._inicializar_variables_de_instancia()
        self._crear_barras_herramientas()
        self._rellenar_componentes()

        self._agregar_atajos()
        self._agregar_eventos()

    ## inicializacion de forma

    def _agregar_atajos(self):
        eventos = {
            'R': lambda: self._aplicar_por_documento('Remisión'),
            'F': lambda: self._aplicar_por_documento('Factura'),
            'Q': lambda: self._deshacer_saldado(),
            'F1': lambda: self._aplicar_por_documento(),
            'F4': lambda: self._aplicar_por_monto('auto'),
            'F8': lambda: self._aplicar_por_monto('selección'),
            'F12': lambda: self._saldar()
        }
        self._interfaz.ventanas.agregar_hotkeys_forma(eventos)

    def _agregar_eventos(self):
        eventos = {
            'cbx_forma_cobro': lambda event: self._interfaz.ajustar_apariencia_terminal(),
            'tbx_recibido': lambda event: self._calcular_cambio(),
            'cbx_terminal': lambda event: self._buscar_afiliacion_seleccion(),
            'tbx_terminal': lambda event: self._buscar_afiliacion(),
            'tvw_tabla_documentos': (lambda event: self._seleccionar_documento(), 'seleccion')
        }
        self._interfaz.ventanas.cargar_eventos(eventos)

    def _crear_barras_herramientas(self):
        self.barra_herramientas1 = [
            {'nombre_icono': 'Payments32.ico', 'etiqueta': 'Total', 'nombre': 'aplicar_total', 'hotkey': '[F1]',
             'comando': lambda: self._aplicar_por_documento()},
            {'nombre_icono': 'Payments32.ico', 'etiqueta': 'Automático', 'nombre': 'aplicar_automatico',
             'hotkey': '[F4]', 'comando': lambda: self._aplicar_por_monto('auto')},
            {'nombre_icono': 'Payments32.ico', 'etiqueta': 'Selección', 'nombre': 'aplicar_seleccion',
             'hotkey': '[F8]', 'comando': lambda: self._aplicar_por_monto('selección')},
            {'nombre_icono': 'Invoice32.ico', 'etiqueta': 'Remisiones', 'nombre': 'aplicar_remisiones',
             'hotkey': '[R]', 'comando': lambda: self._aplicar_por_documento('Remisión')},
            {'nombre_icono': 'Invoice32.ico', 'etiqueta': 'Facturas', 'nombre': 'aplicar_facturas',
             'hotkey': '[F]', 'comando': lambda: self._aplicar_por_documento('Factura')},
        ]

        self.elementos_barra_herramientas1 = self._interfaz.ventanas.crear_barra_herramientas(self.barra_herramientas1,
                                                                                             'frame_botones_aplicar')
        self.iconos_barra_herramientas1 = self.elementos_barra_herramientas1[0]
        self.etiquetas_barra_herramientas1 = self.elementos_barra_herramientas1[2]
        self.hotkeys_barra_herramientas1 = self.elementos_barra_herramientas1[1]

        self.barra_herramientas = [
            {'nombre_icono': 'Validate32.ico', 'etiqueta': 'Saldar', 'nombre': 'saldar', 'hotkey': '[F12]',
             'comando': self._saldar},
            {'nombre_icono': 'Cancelled32.ico', 'etiqueta': 'Deshacer', 'nombre': 'deshacer', 'hotkey': '[Q]',
             'comando': self._deshacer_saldado},
        ]

        self.elementos_barra_herramientas = self._interfaz.ventanas.crear_barra_herramientas(self.barra_herramientas,
                                                                                             'frame_acciones')
        self.iconos_barra_herramientas = self.elementos_barra_herramientas[0]
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]

    def _inicializar_variables_de_instancia(self):
        self._usuario_id = self._parametros.id_usuario
        self._business_entity_id = self._cliente.business_entity_id
        self._official_number = self._cliente.official_number
        self._official_name = self._cliente.official_name

        self._consulta_formas_pago = []
        self._consulta_terminales_bancarias = []
        self._consulta_documentos = None

        self._documentos_seleccionados = []
        self._documentos_seleccionados_previo = []

    def _rellenar_componentes(self):
        moneda = self._utilerias.convertir_decimal_a_moneda

        consulta = self._base_de_datos.buscar_documentos_con_saldo(self._business_entity_id)

        self._interfaz.rellenar_tabla(consulta)

        cliente = self._utilerias.limitar_caracteres(self._cliente.official_name,25)
        self._interfaz.ventanas.insertar_input_componente('lbl_nombre_cliente', cliente)
        self._interfaz.ventanas.insertar_input_componente('lbl_cartera', moneda(self._cliente.debt))

        terminales = self._buscar_terminales_bancarias()
        self._interfaz.ventanas.rellenar_cbx('cbx_terminal', terminales)

        formas_pago = self._buscar_formas_pago()
        self._interfaz.ventanas.rellenar_cbx('cbx_forma_cobro', formas_pago)

        modalidades_de_cobro = ['Un solo cobro', 'Un cobro por documento']
        self._interfaz.ventanas.rellenar_cbx('cbx_modalidad_cobro', modalidades_de_cobro, 'Sin seleccione')

    def _buscar_terminales_bancarias(self):
        if not self._consulta_terminales_bancarias:
            consulta = self._base_de_datos.buscar_terminales_bancarias()
            self._consulta_terminales_bancarias = consulta
        return [reg['Barcode'] for reg in self._consulta_terminales_bancarias]

    def _buscar_formas_pago(self):
        if not self._consulta_formas_pago:
            consulta = self._base_de_datos.buscar_formas_de_pago()
            self._consulta_formas_pago = consulta
        return [reg['Value'] for reg in self._consulta_formas_pago if reg['ID'] != 99]

    ## funcionalidades de eventos

    def _seleccionar_documento(self):
        filas_seleccionadas = self._interfaz.ventanas.obtener_seleccion_filas_treeview('tvw_tabla_documentos')
        if not filas_seleccionadas:
            return

        acumulado = 0
        for fila in filas_seleccionadas:
            valores_fila = self._interfaz.ventanas.procesar_fila_treeview('tvw_tabla_documentos', fila)
            total_moneda = valores_fila['Saldo']
            total = self._utilerias.convertir_moneda_a_decimal(total_moneda)
            acumulado += total
            self._acualizar_acumulado(acumulado)

    def _acualizar_acumulado(self, acumulado):
        self._interfaz.ventanas.insertar_input_componente('tbx_monto', acumulado)

        monto_cartera = self._cliente.debt

        restante = abs(monto_cartera - acumulado)
        restante_moneda = self._utilerias.convertir_decimal_a_moneda(restante)

        self._interfaz.ventanas.insertar_input_componente('lbl_restante', restante_moneda)

        acumulado_moneda = self._utilerias.convertir_decimal_a_moneda(acumulado)
        self._interfaz.ventanas.insertar_input_componente('lbl_monto', acumulado_moneda)

    def _normaliza_formas_pago(self, forma_pago):
        formas_pago = {1: '01', 2: '02', 3: '03', 4: '04', 28: '28'}
        return formas_pago.get(forma_pago, '01')

    def _saldar_fila(self, fila, monto=None):

        def saldar(valores_fila, fila, document_id):
            _moneda = self._utilerias.convertir_decimal_a_moneda

            # actualiza los valores de la tabla
            pagado = valores_fila['Pagado']
            total = valores_fila['Total']
            saldo = valores_fila['Saldo']
            fp = self._normaliza_formas_pago(valores_fila['FP'])

            self._documentos_seleccionados.append(
                {'FP':fp, 'Pagado': pagado, 'Total': total, 'Saldo': saldo, 'DocumentID': document_id})

            valores_fila['Pagado'] = _moneda(pagado)
            valores_fila['Total'] = _moneda(total)
            valores_fila['Saldo'] = _moneda(saldo)
            valores_fila['FP'] = fp

            self._interfaz.ventanas.actualizar_fila_treeview_diccionario('tvw_tabla_documentos', fila, valores_fila)

        _decimal = self._utilerias.convertir_moneda_a_decimal
        valores_fila = self._interfaz.ventanas.procesar_fila_treeview('tvw_tabla_documentos', fila)

        # obtiene los valores dese la tabla
        total = _decimal(valores_fila.get('Total', 0))
        pagado = _decimal(valores_fila.get('Pagado', 0))
        saldo = _decimal(valores_fila.get('Saldo', 0))
        document_id = valores_fila.get('DocumentID')
        fp = self._normaliza_formas_pago(valores_fila['FP'])

        # respalda los valores previo a la afectacion
        self._documentos_seleccionados_previo.append({'FP':fp, 'Pagado': pagado, 'Total': total, 'Saldo': saldo, 'Fila': fila})

        # saldado parcial o total segun corresponda

        # realiza los calculos correspondientes
        if monto:
            if saldo <= monto:
                monto -= saldo
                pagado = saldo
                saldo = 0

                valores_fila['Pagado'] = pagado
                valores_fila['Total'] = total
                valores_fila['Saldo'] = saldo

                saldar(valores_fila, fila, document_id)
                self._interfaz.ventanas.colorear_fila_seleccionada_treeview('tvw_tabla_documentos', fila, 'success')
                return monto

            if saldo > monto:
                pagado = monto
                saldo -= monto
                monto = 0

                valores_fila['Pagado'] = pagado
                valores_fila['Total'] = total
                valores_fila['Saldo'] = saldo

                saldar(valores_fila, fila, document_id)
                self._interfaz.ventanas.colorear_fila_seleccionada_treeview('tvw_tabla_documentos', fila, 'warning')
                return monto

        # saldado sin calculo
        if not monto:
            monto = 0
            monto += saldo
            pagado = saldo
            saldo = 0

            valores_fila['Pagado'] = pagado
            valores_fila['Total'] = total
            valores_fila['Saldo'] = saldo

            saldar(valores_fila, fila, document_id)
            self._interfaz.ventanas.colorear_fila_seleccionada_treeview('tvw_tabla_documentos', fila, 'success')
            return monto

    def _buscar_afiliacion(self):
        afiliacion = self._interfaz.ventanas.obtener_input_componente('tbx_terminal')

        if not afiliacion:
            self._interfaz.ventanas.mostrar_mensaje('Debe escanear un valor a buscar.')
            return

        info_terminal = self._buscar_informacion_terminal('tbx')
        self._actualizar_datos_terminal_forma(info_terminal)

    def _buscar_afiliacion_seleccion(self):
        seleccion = self._interfaz.ventanas.obtener_input_componente('cbx_terminal')

        if seleccion == 'Seleccione':
            self._interfaz.ventanas.limpiar_componente('tbx_terminal')
            return

        info_terminal = self._buscar_informacion_terminal('cbx')
        self._actualizar_datos_terminal_forma(info_terminal)

    def _actualizar_datos_terminal_forma(self, info_terminal):

        barcode = info_terminal['Barcode']
        banco_nombre = info_terminal['Banco']

        self._interfaz.ventanas.insertar_input_componente('lbl_banco', banco_nombre)
        self._interfaz.ventanas.insertar_input_componente('tbx_terminal', barcode)

        cbx_terminal = self._interfaz.ventanas.componentes_forma['cbx_terminal']
        valores = cbx_terminal['values']
        idx = valores.index(barcode)
        cbx_terminal.set(valores[idx])

    def _buscar_informacion_terminal(self, tipo):
        if tipo == 'cbx':
            seleccion = self._interfaz.ventanas.obtener_input_componente('cbx_terminal')
            return [reg for reg in self._consulta_terminales_bancarias
                    if seleccion == reg['Barcode']][0]

        if tipo == 'tbx':
            barcode = self._interfaz.ventanas.obtener_input_componente('tbx_terminal')

            info_terminal = [reg for reg in self._consulta_terminales_bancarias
                             if reg['Barcode'] == barcode]

            if not info_terminal:
                self._interfaz.ventanas.mostrar_mensaje('No se encontró ningún valor favor de validar.')
                return

            if info_terminal:
                return info_terminal[0]

    def _aplicar_por_documento(self, tipo_documento =None):
        self._deshacer_saldado()

        parametros = self._validar_parametros_saldado()

        if not parametros:
            return

        filas = self._interfaz.ventanas.obtener_filas_treeview('tvw_tabla_documentos')
        acumulado = self._utilerias.redondear_valor_cantidad_a_decimal(0)

        for fila in filas:
            valores_fila = self._interfaz.ventanas.procesar_fila_treeview('tvw_tabla_documentos', fila)
            tipo = valores_fila['Tipo']

            if tipo == tipo_documento or not tipo_documento:

                total_moneda = valores_fila['Total']
                total = self._utilerias.convertir_moneda_a_decimal(total_moneda)
                self._saldar_fila(fila)

                acumulado += total

                self._interfaz.ventanas.colorear_fila_seleccionada_treeview('tvw_tabla_documentos', fila, 'success')

        self._acualizar_acumulado(acumulado)
        self._interfaz.ventanas.bloquear_forma()
        self._interfaz.ventanas.desbloquear_componente('tbx_recibido')
        self._interfaz.actualizar_color_etiquetas('bloqueo')

    def _aplicar_por_monto(self, tipo):

        if tipo != 'selección':
            self._deshacer_saldado()

        parametros = self._validar_parametros_saldado()

        if not parametros:
            return

        monto = self._interfaz.ventanas.obtener_input_componente('tbx_monto')
        monto = self._validar_monto(monto)

        if not monto:
            return

        if monto:
            filas_seleccionadas = self._deshacer_saldado('conservar_seleccion')
            self._interfaz.ventanas.insertar_input_componente('tbx_monto', monto)

            if tipo == 'selección':
                filas = filas_seleccionadas

                if not filas:
                    self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar por lo menos un documento')
                    return

            if tipo == 'auto':
                filas = self._interfaz.ventanas.obtener_filas_treeview('tvw_tabla_documentos')


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
            self._interfaz.ventanas.bloquear_forma()
            self._interfaz.ventanas.desbloquear_componente('tbx_recibido')

            self._interfaz.actualizar_color_etiquetas('bloqueo')

    def _validar_monto(self, monto=None):
        monto = self._interfaz.ventanas.componentes_forma['tbx_monto'] if not monto else monto
        if not monto:
            self._interfaz.ventanas.mostrar_mensaje('Monto a saldar no definido.')
            return False

        if not self._utilerias.es_cantidad(monto):
            self._interfaz.ventanas.mostrar_mensaje('Monto a saldar inválido.')
            return False

        if self._utilerias.redondear_valor_cantidad_a_decimal(monto) <= 0:
            self._interfaz.ventanas.mostrar_mensaje('El monto a saldar no puede ser cero o menos que cero.')
            return False

        return self._utilerias.redondear_valor_cantidad_a_decimal(monto)

    def _deshacer_saldado(self, conservar_seleccion = None):
        self._interfaz.ventanas.desbloquear_forma()

        filas = self._interfaz.ventanas.obtener_filas_treeview('tvw_tabla_documentos')
        filas_seleccionadas = self._interfaz.ventanas.obtener_seleccion_filas_treeview('tvw_tabla_documentos')

        if not conservar_seleccion:
            self._interfaz.ventanas.limpiar_seleccion_treeview('tvw_tabla_documentos')

        for fila in filas:
            self._interfaz.ventanas.colorear_fila_seleccionada_treeview('tvw_tabla_documentos', fila, 'white')

        if self._documentos_seleccionados:
            for documento in self._documentos_seleccionados_previo:
                fp = documento['FP']
                pagado = documento['Pagado']
                saldo = documento['Saldo']
                total = documento['Total']
                fila = documento['Fila']

                valores_fila = self._interfaz.ventanas.procesar_fila_treeview('tvw_tabla_documentos', fila)
                valores_fila['Pagado'] = self._utilerias.convertir_decimal_a_moneda(pagado)
                valores_fila['Saldo'] = self._utilerias.convertir_decimal_a_moneda(saldo)
                valores_fila['Total']  = self._utilerias.convertir_decimal_a_moneda(total)
                valores_fila['FP'] = fp

                self._interfaz.ventanas.actualizar_fila_treeview_diccionario('tvw_tabla_documentos', fila, valores_fila)

            self._documentos_seleccionados.clear()
            self._documentos_seleccionados_previo.clear()
            self._acualizar_acumulado(self._utilerias.redondear_valor_cantidad_a_decimal(0))

        self._interfaz.ventanas.refrescar_tamano_forma()
        self._interfaz.ventanas.desbloquear_forma()
        self._interfaz.actualizar_color_etiquetas('desbloqueo')

        return filas_seleccionadas

    def _calcular_cambio(self):
        recibido = self._interfaz.ventanas.obtener_input_componente('tbx_recibido')

        if not self._utilerias.es_cantidad(recibido):
            self._interfaz.ventanas.mostrar_mensaje('Debe introducir un monto válido.')
            return

        recibido = self._utilerias.redondear_valor_cantidad_a_decimal(recibido)

        if recibido <= 0:
            self._interfaz.ventanas.mostrar_mensaje('Debe introducir un monto válido.')
            return

        monto_moneda = self._interfaz.ventanas.obtener_input_componente('lbl_monto')
        monto = self._utilerias.convertir_moneda_a_decimal(monto_moneda)

        if recibido < monto:
            self._interfaz.ventanas.mostrar_mensaje('El monto recibido no debe ser menor al monto a cobrar.')
            return

        restante = recibido - monto

        restante_moneda = self._utilerias.convertir_decimal_a_moneda(restante)
        self._interfaz.ventanas.insertar_input_componente('lbl_restante', restante_moneda)

    def _validar_parametros_saldado(self):
        forma_cobro = self._interfaz.ventanas.obtener_input_componente('cbx_forma_cobro')
        fecha_afectacion = self._interfaz.ventanas.obtener_input_componente('den_fecha_afectacion')
        modalidad = 0 if self._interfaz.ventanas.obtener_input_componente(
            'cbx_modalidad_cobro') == 'Un solo cobro' else 1

        terminal = self._interfaz.ventanas.obtener_input_componente('cbx_terminal')

        #if not self._documentos_seleccionados:
        #    self._interfaz.ventanas.mostrar_mensaje('No hay ningún documento seleccionado.')
        #    return

        if forma_cobro == 'Seleccione':
            self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar una forma de cobro.')
            return

        if forma_cobro[0:2] in ('04', '28') and terminal == 'Seleccione':
            self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar una terminal bancaria o '
                                                    'escanear una.')
            return

        return {'forma_cobro':forma_cobro, 'fecha_afectacion':fecha_afectacion, 'modalidad':modalidad, 'terminal':terminal}

    def _saldar(self):

        parametros = self._validar_parametros_saldado()

        if not parametros:
            return

        if not self._documentos_seleccionados:
            self._interfaz.ventanas.mostrar_mensaje('No hay ningún documento seleccionado.')
            return

        forma_cobro = parametros['forma_cobro']
        fecha_afectacion = parametros['fecha_afectacion']
        modalidad = parametros['modalidad']
        terminal = parametros['terminal']

        forma_cobro_id = [cobro['ID'] for cobro in self._consulta_formas_pago if cobro['Value'] == forma_cobro]
        barcode = 0
        banco_id = 0
        afiliacion = 0
        forma_cobro_id = int(forma_cobro_id[0])

        if forma_cobro_id == 1:
            cajon = CajonCobro("Tickets")
            cajon.abrir_cajon()

        if forma_cobro_id in (28, 4):
            barcode = self._interfaz.ventanas.obtener_input_componente('tbx_terminal')
            afiliacion = [reg['Afiliacion'] for reg in self._consulta_terminales_bancarias
                          if reg['Barcode'] == barcode][0]

            info_terminal = self._buscar_informacion_terminal('cbx')
            banco_id = info_terminal['FinancialEntityID']

            if afiliacion == 'Seleccione':
                self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar una terminal bancaria.')
                return

        fechahoy = datetime.today()
        fechahoy = fechahoy.date()

        if fechahoy < fecha_afectacion:
            self._interfaz.ventanas.mostrar_mensaje('La fecha del cobro no puede ser posterior al día de hoy.')
            return
        else:
            saldar = 0
            if fechahoy > fecha_afectacion:
                validacion = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                    'La fecha del cobro es de un día anterior al día de hoy.\n'
                            '¿Desea proceder?')
                saldar = 0 if validacion != 'No' else 1

            if saldar == 0:
                parametros_de_saldado = {'FormaCobro': forma_cobro_id,
                                         'FechaAfectacion': fecha_afectacion,
                                         'Modalidad': modalidad,
                                         'Documentos': self._documentos_seleccionados,
                                         'Afiliacion': afiliacion,
                                         'BancoID': banco_id,
                                         'Barcode': barcode,
                                         'OfficialName': self._official_name,
                                         'OfficalNumber':self._official_number,
                                         'BusinessEntityID':self._business_entity_id
                                         }

                self._llamar_popup_saldado(parametros_de_saldado)

    def _llamar_popup_saldado(self, parametros_de_saldado):
        nueva_ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(ocultar_master=True)
        instancia = SaldarDocumentos(nueva_ventana, self._parametros, self._base_de_datos, parametros_de_saldado)
        nueva_ventana.wait_window()

        cerrar_ventana = self._interfaz.ventanas.obtener_input_componente('chk_cerrar')

        if cerrar_ventana == 1:
            self._deshacer_saldado()
            self._rellenar_componentes()

        if cerrar_ventana == 0:
            self._interfaz.master.destroy()

