import tkinter as tk
from cayal.ventanas import Ventanas


class AceptarDepositosVendedores:
    def __init__(self, master, base_de_datos, utilerias, parametros):

        self._master =  master
        self._ventanas = Ventanas(self._master)
        self._base_de_datos = base_de_datos
        self._utilerias =  utilerias
        self._parametros = parametros

        self._user_id = self._parametros.id_usuario
        self._user_name = self._base_de_datos.buscar_nombre_de_usuario(self._user_id)
        self._user_group_id = self._base_de_datos.fetchone(
        'SELECT UserGroupID FROM engUser WHERE UserID = ?', (self._user_id,))

        self._crear_frames()
        self._cargar_componentes()

        self._crear_barra_denominaciones()
        self._crear_barra_denominaciones_3()
        self._crear_barra_denominaciones_2()

        self._rellenar_tabla()
        self._cargar_eventos()
        self._actualizar_total_depositos()

        self._ventanas.configurar_ventana_ttkbootstrap('Depósitos por recibir')

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.W}),

            'frame_herramientas': ('frame_principal', 'Herramientas',
                            {'row': 0, 'column': 0, 'columnspan': 2, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_denominaciones': ('frame_principal', 'Denominaciones',
                                     {'row': 1, 'column': 0, 'columnspan': 2,'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),
            'frame_denominaciones1': ('frame_denominaciones', None,
                                      {'row': 0, 'column': 0, 'columnspan': 2, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),
            'frame_denominaciones2': ('frame_denominaciones', None,
                                      {'row': 0, 'column': 4, 'columnspan': 2,'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_tabla': ('frame_principal', 'Depósitos',
                                  {'row': 2, 'column': 0, 'columnspan':2, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),


        }
        self._ventanas.crear_frames(frames)

    def _cargar_componentes(self):
        self._ventanas.crear_table_view(
            nombre='tbv_depositos',
            frame='frame_tabla',
            columnas=self._crear_columnas_tabla(),
            filas=15,
            stripecolor=True
                                        )

    def _crear_barra_denominaciones_3(self):
        self.barra_herramientas3 = [
            {'nombre_icono': 'Cheque.ico', 'etiqueta': '', 'nombre': 'denominacion_20',
             'hotkey': '', 'comando': None},
            {'nombre_icono': 'Billete50.ico', 'etiqueta': '', 'nombre': 'denominacion_50',
             'hotkey': '', 'comando': None},
            {'nombre_icono': 'Billete100.ico', 'etiqueta': '', 'nombre': 'denominacion_100',
             'hotkey': '', 'comando': None},

        ]

        self.elementos_barra_herramientas3 = self._ventanas.crear_barra_herramientas(self.barra_herramientas3,
                                                                                     'frame_denominaciones1')
        self.etiquetas_barra_herramientas3 = self.elementos_barra_herramientas3[2]
        self.hotkeys_barra_herramientas3 = self.elementos_barra_herramientas3[1]

    def _crear_barra_denominaciones_2(self):
        self.barra_herramientas2 = [
            {'nombre_icono': 'Billete200.ico', 'etiqueta': '', 'nombre': 'denominacion_200',
             'hotkey': '', 'comando': None},
            {'nombre_icono': 'Billete500.ico', 'etiqueta': '', 'nombre': 'denominacion_500',
             'hotkey': '', 'comando': None},
            {'nombre_icono': 'Billete1000.ico', 'etiqueta': '', 'nombre': 'denominacion_1000',
             'hotkey': '', 'comando': None},
        ]

        self.elementos_barra_herramientas2 = self._ventanas.crear_barra_herramientas(self.barra_herramientas2,
                                                                                      'frame_denominaciones2')
        self.etiquetas_barra_herramientas2 = self.elementos_barra_herramientas2[2]
        self.hotkeys_barra_herramientas2 = self.elementos_barra_herramientas2[1]

    def _cargar_eventos(self):
        eventos = {
            'tbv_depositos': (lambda event:self._actualizar_denominaciones(),'seleccion')
        }
        self._ventanas.cargar_eventos(eventos)

    def _actualizar_etiqueta_denominacion(self, denominacion, monto, cantidad):
        denominaciones = {
            50: self.etiquetas_barra_herramientas3[1],
            100: self.etiquetas_barra_herramientas3[2],
            200: self.etiquetas_barra_herramientas2[0],
            500: self.etiquetas_barra_herramientas2[1],
            1000: self.etiquetas_barra_herramientas2[2]
        }
        etiqueta = denominaciones[denominacion]
        cantidad = int(cantidad)

        if cantidad > 0:
            monto = f"{monto:.2f}"
            texto = f"{cantidad}={monto}"

            etiqueta.config(text=texto, font=('Consolas', 12, 'bold'))

        if cantidad < 0:
            etiqueta.config(text='')

    def _actualizar_denominaciones(self):
        self._limpiar_deposito()

        filas = self._ventanas.procesar_filas_table_view('tbv_depositos', seleccionadas=True)
        if not filas:
            self._limpiar_deposito()

            return


        denominaciones = {
            50:'B.50',
            100: 'B.100',
            200: 'B.200',
            500:'B.500',
            1000: 'B.1000',
            'Cheques':'Cheques',
            #'Total': 'Total',
            #'Billetes': 'Billetes'
        }


        valores = {
            50:[0,0], 100:[0,0], 200:[0,0], 500:[0,0], 1000:[0,0]
        }

        for fila in filas:
            if fila['Entrega'] == 'TOTALES:':
                self._limpiar_deposito()

                continue

            for denominacion, valor in denominaciones.items():

                if denominacion == 'Cheques':
                    liquidation_id = fila['LiquidationID']
                    self._procesar_cheques(liquidation_id)
                    continue

                cantidad = fila[valor]
                monto = denominacion * cantidad

                valores[denominacion][0] +=  cantidad
                valores[denominacion][1] += monto

        for denominacion, montos in valores.items():
            monto = montos[0]
            cantidad = montos[1]
            self._actualizar_etiqueta_denominacion(denominacion, monto, cantidad)

    def _buscar_cheques(self,liquidation_id):

        #[{'Total': '1500.00', 'Cliente': 'MARIA MINERVA BRITO COLORADO', 'BusinessEntityID': 5162, 'UUID': '9252a7c5-26bd-4269-83cd-1585ad770b31'}]
        #                INSERT INTO zvwChequesDepositosCayal (DepositoID, Emisor, Monto, LiquidationID, Receptor)
        consulta = self._base_de_datos.fetchall(
            """
                SELECT DepositoID, Emisor, Monto, LiquidationID, Receptor
                FROM zvwChequesDepositosCayalNoRecibidos
                WHERE LiquidationID = ?
            """,(liquidation_id,)
        )
        if not consulta:
            return

        self._cheques_capturados = consulta

    def _procesar_cheques(self, liquidation_id):
        self._buscar_cheques(liquidation_id)

        etiqueta_cheques = self.etiquetas_barra_herramientas3[0]

        cantidad_cheques = len(self._cheques_capturados)
        montos_cheques = [self._utilerias.redondear_valor_cantidad_a_decimal(cheque['Monto'])
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

    def _crear_columnas_tabla(self):
        return [
                {"text": "Liquidacion", "stretch": False, "width": 95},
                {"text": "Fecha", "stretch": False, "width": 95},
                {"text": "Entrega", "stretch": False, "width": 95},
                {"text": "Total", "stretch": False, "width": 95},
                {"text": "Cheques", "stretch": False, "width": 75},
                {"text": "B.50", "stretch": False, "width": 75},
                {"text": "B.100", "stretch": False, "width": 75},
                {"text": "B.200", "stretch": False, "width": 75},
                {"text": "B.500", "stretch": False, "width": 75},
                {"text": "B.1000", "stretch": False, "width": 75},
                {"text": "Billetes", "stretch": False, "width": 75},
                {"text": "ID", "stretch": True, "width": 0},
                {"text": "LiquidationID", "stretch": True, "width": 0},

        ]

    def _consulta_depositos_recibidos(self):
        sql = """
            SELECT 
                'LQ-' + CAST(M.LiquidationID AS VARCHAR) AS Folio,
                CAST(M.Fecha AS DATE) AS Fecha,
                U.UserName AS Captura,
                M.Total,
                M.Cheques,
                M.Billetes50,
                M.Billetes100,
                M.Billetes200,
                M.Billetes500,
                M.Billetes1000,
                (ISNULL(M.Billetes50,0) + ISNULL(M.Billetes100,0) + ISNULL(M.Billetes200,0) + ISNULL(M.Billetes500,0) + ISNULL(M.Billetes1000,0)) AS Billetes,
                M.ID,
                M.LiquidationID
            FROM 
                zvwDepositosDiariosCayalNoAceptados M
                INNER JOIN engUser U ON M.EmisorUserID = U.UserID
            WHERE 
                CAST(M.Fecha AS DATE) = CAST(GETDATE() AS DATE)
                AND ISNULL(M.StatusAceptado,0) = 0;

        """

        return self._base_de_datos.fetchall(sql)

    def _rellenar_tabla(self):
        self._ventanas.rellenar_table_view('tbv_depositos',
                                         self._crear_columnas_tabla(),
                                         self._procesar_depositos_recibidos(),
                                         )
        self._actualizar_total_depositos()

    def _procesar_depositos_recibidos(self):
        consulta = self._consulta_depositos_recibidos()

        contadores = {
            50: 0,
            100: 0,
            200: 0,
            500: 0,
            1000: 0,
            'total': 0,
            'billetes': 0,
            'cheques': 0
        }

        for deposito in consulta:
            for denominacion, numero in deposito.items():
                if denominacion in ('Billetes50', 'Billetes100', 'Billetes200', 'Billetes500', 'Billetes1000'):
                    valor = int(denominacion[8::])
                    contadores[valor] += numero

                if denominacion == 'Total':
                    contadores['total'] += numero
                    total_moneda = self._utilerias.convertir_decimal_a_moneda(numero)
                    deposito['Total'] = total_moneda

                if denominacion == 'Billetes':
                    contadores['billetes'] += numero

                if denominacion == 'Cheques':
                    contadores['cheques'] += numero

        fila_total = {'Fecha':'',
                      'Entrega':'',
                      'Recibe': 'TOTALES:',
                      'Total':self._utilerias.convertir_decimal_a_moneda(contadores['total']),
                      'Cheques': contadores['cheques'],
                      'Billetes50': contadores[50],
                      'Billetes100':contadores[100],
                      'Billetes200':contadores[200],
                      'Billetes500':contadores[500],
                      'Billetes1000':contadores[1000],
                      'Billetes': contadores['billetes']
                      }

        consulta.append(fila_total)

        return consulta

    def _actualizar_total_depositos(self):
        filas = self._ventanas.procesar_filas_table_view('tbv_depositos')

        if not filas:
            filas = self._ventanas.procesar_filas_table_view('tbv_depositos')

        if not filas:
            texto = f"Cant. Billetes: 0, Monto: $0.00"
            self._ventanas.actualizar_etiqueta_externa_tabla_view('tbv_depositos', texto)
            return

        total_billetes = 0
        monto_total = 0
        for valores_filas in filas:
            if valores_filas['Entrega'] == 'TOTALES:':
                continue

            total, billetes =  valores_filas['Total'], valores_filas['Billetes']
            total_decimal = self._utilerias.convertir_moneda_a_decimal(total)

            total_billetes += int(billetes)
            monto_total += total_decimal

        monto_total_moneda =  self._utilerias.convertir_decimal_a_moneda(monto_total)

        texto = f"Billetes: {total_billetes}, Monto:{monto_total_moneda}"
        self._ventanas.actualizar_etiqueta_externa_tabla_view('tbv_depositos', texto)

    def _crear_barra_denominaciones(self):
        self.barra_herramientas = [
            {'nombre_icono': 'cobro_multiple.ico', 'etiqueta': 'Aceptar', 'nombre': 'aceptar',
             'hotkey': '', 'comando': self._aceptar_depositos},
            {'nombre_icono': 'rechazar.ico', 'etiqueta': 'Rechazar', 'nombre': 'rechazar',
             'hotkey': '', 'comando': self._rechazar_depositos},
            {'nombre_icono': 'Eliminar21.ico', 'etiqueta': 'Salir', 'nombre': 'salir',
             'hotkey': '', 'comando': self._master.destroy},

        ]

        self.elementos_barra_herramientas = self._ventanas.crear_barra_herramientas(self.barra_herramientas,
                                                                                     'frame_herramientas')
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]

    def _aceptar_depositos(self):
        filas = self._obtener_filas()
        if filas:
            for fila in filas:
                id = fila.get('ID', 0)
                if id != 0:
                    self._copiar_deposito(id, fila['LiquidationID'])
                    self._ventanas.remover_fila_table_view(
                        'tbv_depositos', fila, 'ID'
                    )
                    self._consulta_depositos_recibidos()
                    self._rellenar_tabla()


    def _rechazar_depositos(self):
        filas = self._obtener_filas()
        if filas:
            for fila in filas:
                id = fila.get('ID',0)
                if id != 0:
                    self._rechazar_deposito(id, fila['LiquidationID'])
                    self._ventanas.remover_fila_table_view(
                        'tbv_depositos', fila, 'ID'
                    )
                    self._rellenar_tabla()
                    self._actualizar_total_depositos()

    def _obtener_filas(self):
        filas = self._ventanas.procesar_filas_table_view('tbv_depositos',seleccionadas=True)
        if not filas:
            return
        return filas

    def _copiar_deposito(self, id, liquidation_id):
        deposito_id = self._base_de_datos.command("""
            DECLARE @ID INT = ?
            DECLARE @ReceptorUserID INT = ?
            DECLARE @Receptor NVARCHAR(30) = ?
            
            INSERT INTO zvwDepositosDiariosCayal(
                Total,
                Billetes20,
                Billetes50,
                Billetes100,
                Billetes200,
                Billetes500,
                Billetes1000,
                Status,
                Fecha,
                Receptor,
                Emisor,
                ValidadoPor,
                ValidadoEn,
                TotalValidado,
                EmployeeTypeID,
                Cheques,
                Tipo,
                TotalCheques,
                LiquidationID,
                ReceptorUserID,
                EmisorUserID)
            SELECT
                Total,
                Billetes20,
                Billetes50,
                Billetes100,
                Billetes200,
                Billetes500,
                Billetes1000,
                Status,
                Fecha,
                @Receptor,
                Emisor,
                ValidadoPor,
                ValidadoEn,
                TotalValidado,
                EmployeeTypeID,
                Cheques,
                Tipo,
                TotalCheques,
                LiquidationID,
                @ReceptorUserID,
                EmisorUserID
            FROM zvwDepositosDiariosCayalNoAceptados
            WHERE ID = @ID 
            
            UPDATE zvwDepositosDiariosCayalNoAceptados SET StatusAceptado = 1 WHERE ID = @ID
        """,(id, self._user_id, self._user_name))

        for cheque in self._cheques_capturados:
            cliente, monto = cheque['Cliente'], cheque['Total']
            self._base_de_datos.command("""
                INSERT INTO zvwChequesDepositosCayal (DepositoID, Emisor, Monto, LiquidationID, Receptor)
                                            VALUES(?, ?, ?, ?, ?)
                                            
                UPDATE zvwChequesDepositosCayalNoRecibidos SET StatusAceptado = 1 WHERE LiquidationID = ?

            """,(deposito_id, cliente, monto, liquidation_id, self._user_name, liquidation_id))

    def _rechazar_deposito(self, id, liquidation_id):
        self._base_de_datos.command("""
             UPDATE zvwDepositosDiariosCayalNoAceptados 
             SET StatusAceptado = 2, DeletedOn = GETDATE(), DeletedBy=?
             WHERE ID = ?
             
            UPDATE zvwChequesDepositosCayalNoRecibidos SET StatusAceptado = 2 WHERE LiquidationID = ?

        """,(self._user_id, id, liquidation_id))

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
        #self._actualizar_etiquetas_totales(0, 0)
        self._cheques_capturados = []

        etiquetas_billetes = [
            self.etiquetas_barra_herramientas3[0],
            self.etiquetas_barra_herramientas3[1],
            self.etiquetas_barra_herramientas3[2],
            self.etiquetas_barra_herramientas2[0],
            self.etiquetas_barra_herramientas2[1],
            self.etiquetas_barra_herramientas2[2]
        ]
        for etiqueta in etiquetas_billetes:
            etiqueta.config(text='', font=('Consolas', 12, 'bold'))

        self._ventanas.insertar_input_componente('cbx_entrega', 'Seleccione')
