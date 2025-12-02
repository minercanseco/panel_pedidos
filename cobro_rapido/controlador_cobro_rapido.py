import datetime

from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.util import Utilerias
from cayal.cobros import Cobros

from cobro_rapido.abrir_cajon import CajonCobro

class ControladorCobroRapido:
    def __init__(self, interfaz, parametros):
        self._interfaz = interfaz
        self._parametros = parametros
        self._base_de_datos = ComandosBaseDatos(self._parametros.cadena_conexion)
        self._cobros = Cobros(self._parametros.cadena_conexion)
        self._utilerias = Utilerias()

        self._inicializar_variables_de_instancia()
        self._crear_barra_herramientas()
        self._cargar_eventos()

        self._rellenar_cbx_terminal()
        self._rellenar_cbx_forma_pago()

        self._inicializar_totales_documento()
        self._ajustar_apariencia()
        self._agregar_hotkeys()

    def _crear_barra_herramientas(self):
        self.barra_herramientas_pedido = [
            {'nombre_icono': 'Finance32.ico', 'etiqueta': 'Cobrar', 'nombre': 'asignar_pedidos',
             'hotkey': '[F12]', 'comando': self._cobrar_documento},
            {'nombre_icono': 'Cancelled32.ico', 'etiqueta': 'Cancelar', 'nombre': 'editar_empleado',
             'hotkey': '[Esc]', 'comando': self._cancelar},
            {'nombre_icono': 'Agregar21.ico', 'etiqueta': 'Agregar', 'nombre': 'asignar_cartera',
             'hotkey': '[A]', 'comando': self._agregar_cobro_parcial},

        ]

        self.elementos_barra_herramientas = self._interfaz.ventanas.crear_barra_herramientas(
            self.barra_herramientas_pedido,
            'frame_herramientas')
        self.iconos_barra_herramientas = self.elementos_barra_herramientas[0]
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]

    def _cargar_eventos(self):
        eventos = {
            'cbx_tipo': lambda event: self._ajustar_apariencia(),
            'tbx_barcode': lambda event: self._buscar_afiliacion_tbx(),
            'tbx_recibido': lambda event: self._calcular_cambio(),
            'cbx_terminal': lambda event: self._buscar_afiliacion_cbx(),
            #'tvw_cobros':  (lambda event: self._buscar_afiliacion_tvw(), 'seleccion')
        }
        self._interfaz.ventanas.cargar_eventos(eventos)

        evento_adicional = {
            'tvw_cobros': (lambda event: self._eliminar_cobro_tabla(), 'suprimir')
        }
        self._interfaz.ventanas.cargar_eventos(evento_adicional)

    def _agregar_hotkeys(self):
        hotkeys = {
            'F12': lambda: self._cobrar_documento(),
            'E': lambda: self._seleccionar_tipo_cobro('E'),
            'C': lambda: self._seleccionar_tipo_cobro('C'),
            'D': lambda: self._seleccionar_tipo_cobro('D'),
            'T': lambda: self._seleccionar_tipo_cobro('T'),
            'H': lambda: self._seleccionar_tipo_cobro('H')
        }

        self._interfaz.ventanas.agregar_hotkeys_forma(hotkeys)

    def _seleccionar_tipo_cobro(self, char):
        opciones = {
            'E': '01 - Efectivo',
            'C': '04 - Tarjeta de crédito',
            'D': '28 - Tarjeta de débito',
            'T': '03 - Transferencia electrónica de fondos',
            'H': '02 - Cheque nominativo'
        }
        if char in opciones.keys():
            seleccion = opciones.get(char)

            try:
                self._interfaz.ventanas.insertar_input_componente('cbx_tipo', seleccion)
                self._ajustar_apariencia()
            except:
                pass

    def _buscar_afiliacion_tvw(self):

        if not self._interfaz.ventanas.validar_seleccion_una_fila_treeview('tvw_cobros'):
            return

        filas = self._interfaz.ventanas.obtener_seleccion_filas_treeview('tvw_cobros')

        for fila in filas:
            valores_fila = self._interfaz.ventanas.procesar_fila_treeview('tvw_cobros', fila)
            payment_method_id = int(valores_fila['PaymentMethodID'])

            if payment_method_id not in(4,28):
                self._ajustar_apariencia(solo_inicial=True)
                continue

            self._ajustar_apariencia()
            self._interfaz.ventanas.posicionar_frame('frame_tarjeta')
            self._interfaz.ventanas.enfocar_componente('tbx_barcode')

            barcode = valores_fila['Barcode']
            self._settear_valores_terminal(barcode)

    def _buscar_afiliacion_cbx(self, barcode=None):

        if not barcode:
            barcode =  self._interfaz.ventanas.obtener_input_componente('cbx_terminal')

            if barcode == 'Seleccione':
                self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar una terminal de la lista.')
                return

        barcode = barcode.strip()

        return self._settear_valores_terminal(barcode)

    def _buscar_afiliacion_tbx(self):
        barcode = str(self._interfaz.ventanas.obtener_input_componente('tbx_barcode'))

        if not barcode:
            self._interfaz.ventanas.mostrar_mensaje('Debe introducir un código de barras de una terminal bancaria.')
            return
        if not self._utilerias.es_cantidad(barcode):
            self._interfaz.ventanas.mostrar_mensaje('Debe introducir un código de barras de una terminal bancaria.')
            return

        return self._buscar_afiliacion_cbx(barcode)

    def _ajustar_apariencia(self, solo_inicial=False):

        def configurar_apariencia_inicial():

            self._interfaz.ventanas.limpiar_componentes('tbx_monto')
            self._interfaz.ventanas.limpiar_componentes('tbx_recibido')
            self._interfaz.ventanas.limpiar_componentes('tbx_barcode')

            frames = ['frame_restante', 'frame_tabla_dividido', 'frame_tarjeta' ]
            for frame in frames:
                if self._numero_cobros_aplicados > 0 and frame =='frame_tabla_dividido':
                    continue

                self._interfaz.ventanas.ocultar_frame(frame)

            if self._cayal_customer_type_id != 0 and self._credito_restante > 0:
                self._interfaz.ventanas.posicionar_frame('frame_restante')

            self._interfaz.ventanas.insertar_input_componente('tbx_monto_cobro', self._saldo)
            self._interfaz.ventanas.enfocar_componente('tbx_recibido')

            self._actualizar_etiqueta_saldo()

        # configura como se debe inicialmente configurar la app es decir en efectivo de ahi ajusta
        configurar_apariencia_inicial()
        if solo_inicial:
            return

        forma_cobro = self._interfaz.ventanas.obtener_input_componente('cbx_tipo')
        payment_method_id = self._buscar_metodo_pago_id(forma_cobro)

        # 1 efectivo, 2 cheque, 3 transferencia, 4 tdcredito, 28 tddebito
        if payment_method_id in (4, 28):
            self._interfaz.ventanas.posicionar_frame('frame_tarjeta')
            self._interfaz.ventanas.enfocar_componente('tbx_barcode')

    def _actualizar_etiqueta_saldo(self):
        saldo_moneda = self._utilerias.convertir_decimal_a_moneda(self._saldo)
        self._interfaz.ventanas.insertar_input_componente('lbl_saldo', saldo_moneda)
        self._interfaz.ventanas.insertar_input_componente('tbx_monto_cobro', self._saldo)

    def _cancelar(self):
        self._interfaz.master.destroy()

    def _agregar_cobro_parcial(self):

        valores_fila = self._crear_valores_cobro()
        if not valores_fila:
            return

        monto_cobro_decimal = valores_fila[0]

        if monto_cobro_decimal == self._saldo and self._numero_cobros_aplicados == 0:
            return

        self._interfaz.ventanas.posicionar_frame('frame_tabla_dividido')

        # valores aplicables para la tabla de cobros parciales

        print(valores_fila)
        self._interfaz.ventanas.insertar_fila_treeview('tvw_cobros', valores_fila, al_principio=True)

        # marca el numero de cobros aplicados
        self._numero_cobros_aplicados += 1
        self._saldo = valores_fila[2]
        self._actualizar_etiqueta_saldo()

    def _crear_valores_cobro(self):
        forma_pago = self._interfaz.ventanas.obtener_input_componente('cbx_tipo')
        tipo = forma_pago[0:2].strip()

        if tipo in ('04', '28') and not self._buscar_afiliacion_tbx():
            return

        monto_cobro_decimal = self._validar_monto_cobro()

        if not monto_cobro_decimal:
            return


        # valores aplicables para la tabla de cobros parciales

        forma_pago = self._interfaz.ventanas.obtener_input_componente('cbx_tipo')
        payment_method_id = self._buscar_metodo_pago_id(forma_pago)

        saldo_restante_decimal = self._calcular_saldo_restante(monto_cobro_decimal)

        financial_entity_id = 0
        afiliacion = '0'
        barcode = '0'

        if payment_method_id in (4, 28):
            info_terminal = self._buscar_afiliacion_tbx()
            if not info_terminal:
                return

            # Banco, Afiliacion, Barcode, FinancialEntityID
            financial_entity_id = info_terminal['FinancialEntityID']
            afiliacion = str(info_terminal['Afiliacion'])
            barcode = str(info_terminal['Barcode'])

        return (monto_cobro_decimal,
                        forma_pago,
                        saldo_restante_decimal,
                        financial_entity_id,
                        afiliacion,
                        barcode,
                        payment_method_id)

    def _calcular_saldo_restante(self, monto_cobro_decimal):
        return self._saldo - monto_cobro_decimal

    def _rellenar_cbx_forma_pago(self):

        if not self._consulta_formas_pago:
            self._consulta_formas_pago = self._base_de_datos.buscar_formas_de_pago()

        formas_pago = [reg['Value'] for reg in self._consulta_formas_pago
                       if reg['Clave'] not in ('99')]

        self._interfaz.ventanas.rellenar_cbx('cbx_tipo', formas_pago, sin_seleccione=True)

    def _rellenar_cbx_terminal(self):

        if not self._consulta_terminales:
            self._consulta_terminales = self._base_de_datos.buscar_terminales_bancarias()

        terminales = [reg['Barcode'] for reg in self._consulta_terminales]

        self._interfaz.ventanas.rellenar_cbx('cbx_terminal', terminales)

    def _inicializar_variables_de_instancia(self):
        self._module_id = self._parametros.id_modulo
        self._document_id = self._parametros.id_principal
        self._user_id = self._parametros.id_usuario
        self._cayal_customer_type_id = 0
        self.valores_cobro = {}

        self._consulta_formas_pago = []
        self._consulta_terminales = []
        self._cobros_aplicados = []

        self._numero_cobros_aplicados = 0
        self._monto_recibido = self._utilerias.redondear_valor_cantidad_a_decimal(0)
        self._cambio_cliente = self._utilerias.redondear_valor_cantidad_a_decimal(0)

        self._saldo =  self._utilerias.redondear_valor_cantidad_a_decimal(0)
        self._total = self._utilerias.redondear_valor_cantidad_a_decimal(0)
        self._pagado = self._utilerias.redondear_valor_cantidad_a_decimal(0)

        self._inicializar_generales_cliente()

    def _inicializar_totales_documento(self):
        info_documento = self._base_de_datos.fetchall(
            """
            SELECT ISNULL(Balance,0) Balance,
                     ISNULL(Total,0) Total,
                     ISNULL(TotalPaid,0) TotalPaid 
            FROM docDocument WHERE DocumentID = ?
            """,
            (self._document_id,))

        saldo_documento = info_documento[0]['Balance'] if info_documento else 0
        total_documento = info_documento[0]['Total']  if info_documento else 0
        total_pagado = info_documento[0]['TotalPaid']  if info_documento else 0

        self._total = self._utilerias.redondear_valor_cantidad_a_decimal(total_documento)
        self._saldo = self._utilerias.redondear_valor_cantidad_a_decimal(saldo_documento)
        self._pagado = self._utilerias.redondear_valor_cantidad_a_decimal(total_pagado)

    def _validar_monto_cobro(self):

        monto_cobro = self._interfaz.ventanas.obtener_input_componente('tbx_monto_cobro')
        if not monto_cobro:
            self._interfaz.ventanas.mostrar_mensaje('Debe introducir un monto del cobro.')
            return

        if not self._utilerias.es_cantidad(monto_cobro):
            self._interfaz.ventanas.mostrar_mensaje('Debe introducir un valor válido para el monto del cobro.')
            return

        monto_cobro_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(monto_cobro)

        if monto_cobro_decimal > self._saldo:
            self._interfaz.ventanas.mostrar_mensaje('El monto del cobro no puede ser superior al saldo.')
            return

        if monto_cobro_decimal <= 0:
            self._interfaz.ventanas.mostrar_mensaje('El monto del cobro no puede menor o igual a cero.')
            return

        return monto_cobro_decimal

    def _calcular_cambio(self):

        def validar_monto_recibido(monto_cobro):
            monto_recibido = self._interfaz.ventanas.obtener_input_componente('tbx_recibido')
            if not monto_recibido:
                self._interfaz.ventanas.mostrar_mensaje('Debe introducir un monto recibido.')
                return

            if not self._utilerias.es_cantidad(monto_recibido):
                self._interfaz.ventanas.mostrar_mensaje('Debe introducir un valor válido para el monto recibido.')
                return

            monto_recibido_decimal = self._utilerias.redondear_valor_cantidad_a_decimal(monto_recibido)

            if monto_recibido_decimal <= 0:
                self._interfaz.ventanas.mostrar_mensaje('El monto recibido no puede menor o igual a cero.')
                return

            if monto_recibido_decimal < monto_cobro:
                self._interfaz.ventanas.mostrar_mensaje('El monto recibido no puede menor que el cobro.')
                return

            return monto_recibido_decimal

        monto_cobro_decimal = 0

        if self._numero_cobros_aplicados == 0:
            monto_cobro_decimal = self._validar_monto_cobro()
            if not monto_cobro_decimal:
                return

        if self._numero_cobros_aplicados > 0:
            filas = self._interfaz.ventanas.obtener_filas_treeview('tvw_cobros')
            if not filas:
                return
            for fila in filas:
                valores_fila = self._interfaz.ventanas.procesar_fila_treeview('tvw_cobros', fila)
                payment_method_id = valores_fila['PaymentMethodID']

                if int(payment_method_id) == 1:
                    monto = self._utilerias.redondear_valor_cantidad_a_decimal(valores_fila['Monto'])
                    monto_cobro_decimal += monto

        monto_recibido_decimal = validar_monto_recibido(monto_cobro_decimal)

        if not monto_recibido_decimal:
            return

        cambio_decimal = monto_recibido_decimal - monto_cobro_decimal
        self._cambio_cliente = cambio_decimal
        self._monto_recibido = monto_recibido_decimal
        cambio_moneda = self._utilerias.convertir_decimal_a_moneda(cambio_decimal)
        self._interfaz.ventanas.insertar_input_componente('lbl_cambio', cambio_moneda)

    def _buscar_metodo_pago_id(self, tipo_cobro):
        payment_method_id = [valor['ID'] for valor in self._consulta_formas_pago
                             if valor['Value'] == tipo_cobro]

        return int(payment_method_id[0])

    def _settear_valores_terminal(self, barcode):

        info_terminal = [terminal for terminal in self._consulta_terminales
                         if int(barcode) == int(terminal['Barcode'])]
        if not info_terminal:
            self._interfaz.ventanas.mostrar_mensaje('No se encontró información relacionada'
                                                    'a la afiliación proporcionada.')

            self._interfaz.ventanas.limpiar_componentes('tbx_barcode')
            return

        banco = info_terminal[0]['Banco']
        self._interfaz.ventanas.insertar_input_componente('lbl_banco', banco)

        barcode = info_terminal[0]['Barcode']
        self._interfaz.ventanas.insertar_input_componente('cbx_terminal', barcode)
        self._interfaz.ventanas.insertar_input_componente('tbx_barcode', barcode)

        return info_terminal[0]

    def _eliminar_cobro_tabla(self):
        filas = self._interfaz.ventanas.obtener_seleccion_filas_treeview('tvw_cobros')
        self._numero_cobros_aplicados = len(filas)
        if not filas:
            return

        for fila in filas:
            valores_fila = self._interfaz.ventanas.procesar_fila_treeview('tvw_cobros',fila)
            monto = self._utilerias.redondear_valor_cantidad_a_decimal(valores_fila['Monto'])
            self._saldo += monto
            self._interfaz.ventanas.remover_fila_treeview('tvw_cobros', fila)
            self._numero_cobros_aplicados -= 1

        self._actualizar_etiqueta_saldo()

    def _guardar_monto_recibido(self):

        if self._monto_recibido > 0 and self._module_id != 1367:
            self._base_de_datos.command('UPDATE docDocument SET CambioCayal = ? WHERE DocumentID = ?',
                                        (self._monto_recibido, self._document_id))

    def _insertar_para_recalcular(self):
        if self._module_id != 1367:
            self._base_de_datos.exec_stored_procedure('zvwRecalcularDocumentos',
                                                  (self._document_id, self._document_id))

    def _inicializar_generales_cliente(self):
        self._business_entity_id = self._base_de_datos.fetchone(
            'SELECT BusinessEntityID FROM docDocument WHERE DocumentID = ?', (self._document_id,))

        if self._business_entity_id == 8179:
            self._business_entity_id = self._base_de_datos.fetchone(
                'SELECT CustomerID FROM docDocumentExt WHERE IDExtra = ?', (self._document_id,))

        if self._business_entity_id == 9277:
            self._credito_restante = self._utilerias.redondear_valor_cantidad_a_decimal(0)
            self._official_name = 'PG'
            self._official_number = 'XAXX010101000'
        else:


            self._consulta_info_cliente = self._base_de_datos.buscar_info_cliente(self._business_entity_id)

            self._cayal_customer_type_id = self._consulta_info_cliente[0]['CayalCustomerTypeID']
            self._official_name = self._consulta_info_cliente[0]['OfficialName']
            self._official_number = self._consulta_info_cliente[0]['OfficialNumber']

            if self._cayal_customer_type_id != 0:

                credito_restante = self._consulta_info_cliente[0]['RemainingCredit']
                credito_restante = self._utilerias.redondear_valor_cantidad_a_decimal(credito_restante)
                self._credito_restante = credito_restante + self._saldo if credito_restante > 0 else credito_restante


                restante_moneda = self._utilerias.convertir_decimal_a_moneda(self._credito_restante)
                self._interfaz.ventanas.insertar_input_componente('lbl_restante', restante_moneda)

    def _cobrar_documento(self):

        abrir_cajon_dinero = False

        date_operation = datetime.datetime.today()

        if self._numero_cobros_aplicados == 0:
            valores_cobro = self._crear_valores_cobro()

            #abre el cajon si el cobro es efectivo
            if valores_cobro[6] == 1:
                abrir_cajon_dinero = True

            valores_cobro = {
                "barcode": valores_cobro[5],
                "payment_method_id": valores_cobro[6],
                "financial_entity_id": valores_cobro[3],
                "afiliacion": valores_cobro[4],
                "modality": 0,
                "total_paid": self._pagado + self._saldo,
                "monto": self._saldo
            }
            self._asignar_cobros(valores_cobro, date_operation)

        if self._numero_cobros_aplicados > 0:

            cobros = self._interfaz.ventanas.obtener_filas_treeview('tvw_cobros')
            for cobro in cobros:
                valores = self._interfaz.ventanas.procesar_fila_treeview('tvw_cobros', cobro)
                print(valores)
                monto = self._utilerias.redondear_valor_cantidad_a_decimal(valores['Monto'])
                forma_cobro = valores['Forma de Pago']
                payment_method_id = self._buscar_metodo_pago_id(forma_cobro)
                financial_entity_id = valores['FinancialEntityID']
                afiliacion = str(valores['Afiliacion'])
                barcode = str(valores['Barcode'])
                self._pagado += monto

                # abre el cajon de dinero si el cobro es efectivo
                if payment_method_id == 1:
                    abrir_cajon_dinero = True

                valores_cobro = {
                    "barcode": barcode,
                    "payment_method_id": payment_method_id,
                    "financial_entity_id": financial_entity_id,
                    "afiliacion": afiliacion,
                    "modality": 1,
                    "total_paid": self._pagado,
                    "monto": monto
                }
                self._asignar_cobros(valores_cobro, date_operation)

        self._guardar_monto_recibido()
        self._insertar_para_recalcular()
        self._interfaz.master.destroy()

        if abrir_cajon_dinero:
            cajon = CajonCobro("Tickets")
            cajon.abrir_cajon()

    def _asignar_cobros(self, valores_cobro, date_operation):
        if self._module_id != 1367:
            self._cobros.modality = valores_cobro['modality']
            self._cobros.total_amount = self._saldo
            self._cobros.barcode = valores_cobro['barcode']
            self._cobros.document_id = self._document_id
            self._cobros.payment_method_id = valores_cobro['payment_method_id']
            self._cobros.amount = valores_cobro['monto']
            self._cobros.financial_entity_id = valores_cobro['financial_entity_id']
            self._cobros.business_entity_id = self._business_entity_id
            self._cobros.official_number = self._official_number
            self._cobros.official_name = self._official_name
            self._cobros.afiliacion = valores_cobro['afiliacion']
            self._cobros.created_by = self._user_id
            self._cobros.date_operation = date_operation
            self._cobros.total = self._total
            self._cobros.total_paid = valores_cobro['total_paid']
            self._cobros.create_payment()
        else:
            valores_cobro['total_amount'] = self._saldo
            valores_cobro['document_id'] = self._document_id
            valores_cobro['business_entity_id'] = self._business_entity_id
            valores_cobro['official_number'] = self._official_number
            valores_cobro['official_number'] = self._official_name
            valores_cobro['created_by'] = self._user_id
            valores_cobro['date_operation'] = date_operation
            valores_cobro['total'] = self._total

            self.valores_cobro = valores_cobro
