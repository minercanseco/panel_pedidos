import tkinter as tk
from datetime import datetime

from cayal.ventanas import Ventanas

from capturar_documento.herramientas.depositos.agregar_cheque import AgregarCheque
from capturar_documento.herramientas.depositos.contador_divisa import ContadorBilletes
from capturar_documento.herramientas.depositos.depositos_recibidos import DepositosRecibitos


class AgregarDeposito:
    def __init__(self, master, base_de_datos, utilerias, parametros):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._parametros = parametros

        self._base_de_datos = base_de_datos
        self._utilerias = utilerias

        self._user_id = self._parametros.id_usuario
        self._user_group_id = self._base_de_datos.fetchone(
            'SELECT UserGroupID FROM engUser WHERE UserID = ?', (self._user_id,)
        )

        self._procesando_denominacion = False

        self._deposito_capturado = {
                                    50: {'cantidad': 0, 'monto': 0},
                                    100: {'cantidad': 0, 'monto': 0},
                                    200: {'cantidad': 0, 'monto': 0},
                                    500: {'cantidad': 0, 'monto': 0},
                                    1000: {'cantidad': 0, 'monto': 0}
                                    }
        self._GRUPOS_USUARIO = {
            11: 'cajero',
            6: 'cobranza',
            4: 'minisuper',
            5: 'ventas',
            20: 'ventas',
            22: 'ventas',
            18: 'ventas',
            25: 'vendedor',
            32: 'ventas'
        }
        self._SQL_CBXS = """
                        SELECT OfficialName, BusinessEntityID, UserName, UserID, EmployeeTypeID
                        FROM zvwEmpleadosCayalMenu
                        WHERE EmployeeTypeID IN(11, 6, 1, 4, 5, 18, 20, 21, 22, 25,32, 31)
                        ORDER BY OfficialName
                        """

        self._monto_total_deposito = 0
        self._monto_total_cheques = 0
        self._cheques_capturados = []

        self._consulta_empleados_recibe = []
        self._consulta_empleados_entrega = []

        self._crear_frames()
        self._crear_componentes()
        self._crear_barra_denominaciones_1()
        self._crear_barra_denominaciones_2()
        self._cargar_eventos()

        self._rellenar_cbxs()
        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Depósitos')
        self._settear_valores_cierre_y_cbxs()


    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.W}),

            'frame_info': ('frame_principal', 'Información',
                               {'row': 1, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_deposito': ('frame_principal', 'Depósito',
                                  {'row': 0, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),
            'frame_monto': ('frame_deposito', None,
                              {'row': 0, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.W}),

            'frame_botones': ('frame_info', None,
                                     {'row': 3, 'column': 1, 'pady': 5, 'sticky': tk.NSEW}),
            'frame_chk': ('frame_info', None,
                              {'row': 4, 'column': 1, 'pady': 5, 'sticky': tk.W}),
            'frame_denominaciones': ('frame_principal', 'Denominaciones',
                                     {'row': 3, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),
            'frame_denominaciones1': ('frame_denominaciones', None,
                                     {'row': 0, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),
            'frame_denominaciones2': ('frame_denominaciones', None,
                                      {'row': 1, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),
        }
        self._ventanas.crear_frames(frames)

    def _crear_componentes(self):
        componentes = {

            'cbx_recibe':('frame_info', None, 'Recibe:', None),
            'cbx_entrega': ('frame_info', None, 'Entrega:', None),

            'lbl_total_texto': ('frame_monto',
                                  {'width': 10, 'text': 'Monto:',
                                   'font': ('Consolas', 12, 'bold')},
                                  {'row': 0, 'column': 0, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                  None),

            'lbl_total': ('frame_monto',
                                {'width': 10, 'text': '$0.00',
                                 'font': ('Consolas', 18, 'bold')},
                                {'row': 0, 'column': 1, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                None),

            'lbl_billetes_texto': ('frame_monto',
                                {'width': 10, 'text': 'Billetes:',
                                 'font': ('Consolas', 12, 'bold')},
                                {'row': 0, 'column': 2, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                                None),

            'lbl_billetes': ('frame_monto',
                          {'width': 10, 'text': '0',
                           'font': ('Consolas', 18, 'bold')},
                          {'row': 0, 'column': 3, 'pady': 0, 'padx': 0, 'sticky': tk.NSEW},
                          None),

            'btn_guardar': ('frame_botones', 'Primary', 'Guardar', None),
            'btn_cancelar': ('frame_botones', 'Danger', 'Cancelar', None),
            'btn_depositos': ('frame_botones', 'Warning', 'Capturados', None),

            'chk_cerrar_aplicacion': ('frame_chk',
                          {'row': 0, 'column': 0, 'pady': 5, 'padx': 5, 'sticky': tk.W},
                          'No cerrar', None),
        }
        self._ventanas.crear_componentes(componentes)
        self._ventanas.ajustar_ancho_componente('cbx_recibe',35)
        self._ventanas.ajustar_ancho_componente('cbx_entrega', 35)

    def _cargar_eventos(self):
        eventos = {
            'btn_guardar': self._guardar_deposito,
            'btn_cancelar': self._master.destroy,
            'btn_depositos': self._llamar_depositos_recibitos
        }
        self._ventanas.cargar_eventos(eventos)

    def _crear_barra_denominaciones_1(self):
        self.barra_herramientas = [
            {'nombre_icono': 'Cheque.ico', 'etiqueta': '', 'nombre': 'denominacion_20',
             'hotkey': '', 'comando': self._denominacion_cheque},
            {'nombre_icono': 'Billete50.ico', 'etiqueta': '', 'nombre': 'denominacion_50',
             'hotkey': '', 'comando': self._denominacion_50},
            {'nombre_icono': 'Billete100.ico', 'etiqueta': '', 'nombre': 'denominacion_100',
             'hotkey': '', 'comando': self._denominacion_100},

        ]

        self.elementos_barra_herramientas = self._ventanas.crear_barra_herramientas(self.barra_herramientas,
                                                                                     'frame_denominaciones1')
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]

    def _crear_barra_denominaciones_2(self):
        self.barra_herramientas2 = [
            {'nombre_icono': 'Billete200.ico', 'etiqueta': '', 'nombre': 'denominacion_200',
             'hotkey': '', 'comando': self._denominacion_200},
            {'nombre_icono': 'Billete500.ico', 'etiqueta': '', 'nombre': 'denominacion_500',
             'hotkey': '', 'comando': self._denominacion_500},
            {'nombre_icono': 'Billete1000.ico', 'etiqueta': '', 'nombre': 'denominacion_1000',
             'hotkey': '', 'comando': self._denominacion_1000},
        ]

        self.elementos_barra_herramientas2 = self._ventanas.crear_barra_herramientas(self.barra_herramientas2,
                                                                                      'frame_denominaciones2')
        self.etiquetas_barra_herramientas2 = self.elementos_barra_herramientas2[2]
        self.hotkeys_barra_herramientas2 = self.elementos_barra_herramientas2[1]

    def _llamar_contador_billetes(self, denominacion):

        if not self._procesando_denominacion:
            try:
                self._procesando_denominacion = True
                ventana = self._ventanas.crear_popup_ttkbootstrap(self._master, 'Valorizar')
                instancia = ContadorBilletes(ventana, self._utilerias, denominacion)
                ventana.wait_window()

                self._actualizar_etiqueta_denominacion(denominacion, instancia.monto, instancia.cantidad)
                self._actualizar_deposito_acumulado(denominacion, instancia.monto, instancia.cantidad)
            finally:
                self._procesando_denominacion = False

    def _actualizar_etiqueta_denominacion(self, denominacion, monto, cantidad):
        denominaciones = {
            50: self.etiquetas_barra_herramientas[1],
            100: self.etiquetas_barra_herramientas[2],
            200: self.etiquetas_barra_herramientas2[0],
            500: self.etiquetas_barra_herramientas2[1],
            1000: self.etiquetas_barra_herramientas2[2]
        }
        etiqueta = denominaciones[denominacion]
        cantidad = int(cantidad)

        if cantidad > 0:
            monto =  f"{monto:.2f}"
            texto = f"{cantidad}={monto}"

            etiqueta.config(text=texto, font=('Consolas', 12, 'bold'))

        if cantidad < 0:
            etiqueta.config(text='')

    def _actualizar_deposito_acumulado(self, denominacion, monto, cantidad):
        self._deposito_capturado[denominacion]['monto'] = monto
        self._deposito_capturado[denominacion]['cantidad'] = cantidad

        total_billetes = sum(billete['cantidad'] for billete in self._deposito_capturado.values())
        total_monto = sum(billete['monto'] for billete in self._deposito_capturado.values())

        self._monto_total_deposito = total_monto
        self._actualizar_etiquetas_totales(total_billetes, total_monto)

    def _actualizar_etiquetas_totales(self, total_billetes, total_monto):

        total_monto_moneda = self._utilerias.convertir_decimal_a_moneda(total_monto)
        self._ventanas.insertar_input_componente('lbl_total', total_monto_moneda)

        self._ventanas.insertar_input_componente('lbl_billetes', int(total_billetes))

    def _denominacion_50(self):
        self._llamar_contador_billetes(50)

    def _denominacion_100(self):
        self._llamar_contador_billetes(100)

    def _denominacion_200(self):
        self._llamar_contador_billetes(200)

    def _denominacion_500(self):
        self._llamar_contador_billetes(500)

    def _denominacion_1000(self):
        self._llamar_contador_billetes(1000)

    def _denominacion_cheque(self):
        ventana = self._ventanas.crear_popup_ttkbootstrap(titulo='Agregar cheque')
        instancia = AgregarCheque(ventana, self._parametros, self._base_de_datos, self._utilerias, self._cheques_capturados)
        ventana.wait_window()

        self._cheques_capturados = instancia.cheques_capturados

        self._procesar_cheques()

    def _procesar_cheques(self):
        etiqueta_cheques = self.etiquetas_barra_herramientas[0]

        cantidad_cheques = len(self._cheques_capturados)
        montos_cheques = [self._utilerias.redondear_valor_cantidad_a_decimal(cheque['Total'])
                           for cheque in self._cheques_capturados]
        total_cheques = 0
        if montos_cheques:
            total_cheques = sum(montos_cheques)
            self._monto_total_cheques = total_cheques

        if cantidad_cheques > 0:
            total_cheques = f"{total_cheques:.2f}"
            texto = f"{cantidad_cheques}={total_cheques}"

            etiqueta_cheques.config(text=texto, font=('Consolas', 12, 'bold'))

        if cantidad_cheques < 0:
            etiqueta_cheques.config(text='')
            self._monto_total_cheques = 0

    def _limpiar_deposito(self):
        self._deposito_capturado = {
            50: {'cantidad': 0, 'monto': 0},
            100: {'cantidad': 0, 'monto': 0},
            200: {'cantidad': 0, 'monto': 0},
            500: {'cantidad': 0, 'monto': 0},
            1000: {'cantidad': 0, 'monto': 0}
        }
        self._monto_total_deposito = 0
        self._ventanas.insertar_input_componente('lbl_total', 0)
        self._ventanas.insertar_input_componente('lbl_billetes', 0)
        self._actualizar_etiquetas_totales(0, 0)
        self._cheques_capturados = []

        etiquetas_billetes = [
            self.etiquetas_barra_herramientas[0],
            self.etiquetas_barra_herramientas[1],
            self.etiquetas_barra_herramientas[2],
            self.etiquetas_barra_herramientas2[0],
            self.etiquetas_barra_herramientas2[1],
            self.etiquetas_barra_herramientas2[2]
        ]
        for etiqueta in etiquetas_billetes:
            etiqueta.config(text='', font=('Consolas', 12, 'bold'))

        self._ventanas.insertar_input_componente('cbx_entrega', 'Seleccione')

    def _guardar_deposito(self):
        if not self._validar_inputs_deposito():
            return

        # obten la cantidad de los billetes que componen el deposito
        b_cantidad = {50: 0, 100: 0, 200: 0, 500: 0, 1000: 0}

        for denominacion, valores in self._deposito_capturado.items():
            cantidad_billetes = valores['cantidad']
            if denominacion in b_cantidad:
                b_cantidad[denominacion] = cantidad_billetes

        # busca el nombre de usuario tanto del emisor como del receptor
        nombre_recibe = self._ventanas.obtener_input_componente('cbx_recibe')
        user_name_recibe = [empleado['UserName'] for empleado in self._consulta_empleados_recibe
                            if empleado['OfficialName'] == nombre_recibe][0]

        nombre_entrega = self._ventanas.obtener_input_componente('cbx_entrega')
        user_name_entrega = [empleado['UserName'] for empleado in self._consulta_empleados_entrega
                            if empleado['OfficialName'] == nombre_entrega][0]

        # buscar si el usuario es alguien de ventas si existe una liquidacion asociada
        liquidation_id = 0
        receptor_user_id = [empleado['UserID'] for empleado in self._consulta_empleados_recibe
                           if empleado['UserName'] == user_name_recibe][0]

        emisor_user_id = [empleado['UserID'] for empleado in self._consulta_empleados_entrega
                           if empleado['UserName'] == user_name_entrega][0]

        emisor_user_group_id = self._base_de_datos.fetchone(
            'SELECT UserGroupID FROM engUser WHERE UserID = ?',
            (emisor_user_id,)
        )

        if emisor_user_group_id in (20, 22, 23, 25, 31):
            liquidation_id = self._base_de_datos.buscar_liquidacion_vendedor(emisor_user_id)
            liquidation_id = 0 if not liquidation_id else liquidation_id
            #self._base_de_datos.actualizar_totales_liquidacion(liquidacion_id=liquidation_id)

        # crea los parametros requeridos de insercion
        parametros = (user_name_recibe,
                      user_name_entrega,
                      self._monto_total_deposito,
                      b_cantidad[50],
                      b_cantidad[100],
                      b_cantidad[200],
                      b_cantidad[500],
                      b_cantidad[1000],
                      0,
                      self._user_group_id,
                      len(self._cheques_capturados),
                      self._monto_total_cheques,
                      liquidation_id,
                      receptor_user_id,
                      emisor_user_id
                      )




        # inserta el registro en la base de datos
        deposito_id = self._base_de_datos.command("""
            INSERT INTO zvwDepositosDiariosCayal (
                Receptor, 
                Emisor, 
                Total,
                Billetes20, 
                Billetes50, 
                Billetes100, 
                Billetes200, 
                Billetes500, 
                Billetes1000,
                Status, 
                Fecha, 
                EmployeeTypeID, 
                Cheques, 
                TotalCheques,
                LiquidationID,
                ReceptorUserID,
                EmisorUserID
            )
            VALUES (
                ?, 
                ?, 
                ?, 
                0, 
                ?, 
                ?, 
                ?, 
                ?, 
                ?, 
                ?, 
                GETDATE(), 
                ?, 
                ?, 
                ?,
                ?,
                ?,
                ?
            )
        """, parametros)

        # inserta el registro de cada cheque en la base de datos

        for cheque in self._cheques_capturados:
            cliente, monto = cheque['Cliente'], cheque['Total']
            self._base_de_datos.command("""
                INSERT INTO zvwChequesDepositosCayal (DepositoID, Emisor, Monto, LiquidationID, Receptor)
                                            VALUES(?, ?, ?, ?, ?)
            """,(deposito_id, cliente, monto, liquidation_id, user_name_entrega))

        self._limpiar_deposito()

        if self._cerrar_aplicacion_al_guardar():
            self._master.destroy()

    def _cerrar_aplicacion_al_guardar(self):
        chk_cerrar_aplicacion = self._ventanas.obtener_input_componente('chk_cerrar_aplicacion')
        return False if int(chk_cerrar_aplicacion) == 1 else True

    def _validar_inputs_deposito(self):
        if (self._monto_total_deposito + self._monto_total_cheques) <= 0:
            self._ventanas.mostrar_mensaje('El valor del depósito no puede ser zero.')
            return

        recibe_deposito = self._ventanas.obtener_input_componente('cbx_recibe')
        entrega_deposito = self._ventanas.obtener_input_componente('cbx_entrega')

        if recibe_deposito == 'Seleccione':
            self._ventanas.mostrar_mensaje('Debe seleccionar quien recibe el deposito')
            return

        if entrega_deposito == 'Seleccione':
            self._ventanas.mostrar_mensaje('Debe seleccionar quien entrega el deposito')
            return

        return True

    def _rellenar_cbxs(self):

        consulta = self._base_de_datos.fetchall(self._SQL_CBXS, ())

        consulta_recibe =  self._filtrar_consulta_recibe(consulta)
        empleados_recibe = [empleado['OfficialName'] for empleado in consulta_recibe]
        self._ventanas.rellenar_cbx('cbx_recibe', empleados_recibe)
        self._consulta_empleados_recibe = consulta_recibe

        consulta_entrega = self._filtrar_consulta_entrega(consulta)
        empleados_entrega =  [empleado['OfficialName'] for empleado in consulta_entrega]
        self._ventanas.rellenar_cbx('cbx_entrega', empleados_entrega)
        self._consulta_empleados_entrega = consulta_entrega

    def _filtrar_consulta_recibe(self, consulta):
        tipo_de_usuario = self._GRUPOS_USUARIO.get(self._user_group_id, 'admin')

        filtro = (11, 5, 6, 1, 4, 23, 22, 31)

        if tipo_de_usuario == 'vendedor':
            filtro =  (20, 22, 23, 25, 31)

        if self._parametros.id_modulo == 1664 and tipo_de_usuario == 'cajero':
            filtro = (11, 6, 1, 4, 15)



        return [reg for reg in consulta if reg['EmployeeTypeID'] in filtro]

    def _filtrar_consulta_entrega(self, consulta):

        tipo_de_usuario = self._GRUPOS_USUARIO.get(self._user_group_id,'admin')

        filtros = {
            'cajero': (11, 0, ),
            'ventas': (20, 22, 23, 25, 31),
            'vendedor': (20, 22, 23, 25, 31)
        }

        filtro = filtros.get(tipo_de_usuario, (6, 11,20, 22, 23, 25, 31))

        if self._es_domingo() and tipo_de_usuario == 'cajero':
            filtro = (11,0)
        #1664 modulo de depositos en contpaq
        if self._parametros.id_modulo != 1664 and tipo_de_usuario == 'cajero':
            filtro = (23, 20, 22, 25)

        return [reg for reg in consulta if reg['EmployeeTypeID'] in filtro]

    def _settear_valores_cierre_y_cbxs(self):
        tipo_de_usuario = self._GRUPOS_USUARIO.get(self._user_group_id, 'admin')

        if self._es_domingo() and tipo_de_usuario == 'cajero':
            # preguntar
            respuesta = self._ventanas.mostrar_mensaje_pregunta(
                '¿Desea recepcionar depósitos? Esta opción es solo para Domingos.'
            )

            if respuesta:
                self._ventanas.insertar_input_componente('cbx_recibe', self._nombre_empleado_receptor())
                self._ventanas.bloquear_componente('cbx_recibe')

                return

        if tipo_de_usuario == 'cajero' and self._parametros.id_modulo != 1664: # no es el modulo de contpaq depositos

            self._ventanas.insertar_input_componente('cbx_entrega', 'Seleccione')
            self._ventanas.insertar_input_componente('cbx_recibe', self._nombre_empleado_receptor())
            self._ventanas.bloquear_componente('cbx_recibe')
            return

        if tipo_de_usuario == 'cajero' and self._parametros.id_modulo == 1664: # es el modulo de contpaq depositos
            print('b')
            self._ventanas.insertar_input_componente('cbx_entrega', self._nombre_empleado_receptor())
            self._ventanas.insertar_input_componente('cbx_recibe', 'Seleccione')
            self._ventanas.bloquear_componente('cbx_entrega')
            return

        if tipo_de_usuario == 'vendedor':
            self._ventanas.insertar_input_componente('cbx_recibe', self._nombre_empleado_receptor())
            self._ventanas.insertar_input_componente('cbx_entrega', 'Selececcione')
            self._ventanas.bloquear_componente('cbx_recibe')

        if tipo_de_usuario not in ('vendedor', 'cajero'):
            self._ventanas.insertar_input_componente('cbx_recibe', self._nombre_empleado_receptor())
            self._ventanas.bloquear_componente('cbx_recibe')
            return



    def _es_domingo(self):
        fecha = datetime.today()
        dia = fecha.weekday()

        if dia == 6:
            return True

        return False

    def _nombre_empleado_receptor(self):
        nombre_empleado = [empleado['OfficialName'] for empleado in self._consulta_empleados_recibe
                if empleado['UserID'] == self._user_id ]
        if not nombre_empleado:
            return 'Seleccione'
        return nombre_empleado[0]

    def _llamar_depositos_recibitos(self):
        ventana = self._ventanas.crear_popup_ttkbootstrap(titulo='Depósitos recibidos', master=self._master)
        instancia = DepositosRecibitos(ventana, self._base_de_datos, self._utilerias, self._parametros)
        ventana.wait_window()