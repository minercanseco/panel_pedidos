import copy
import tkinter as tk
import uuid
from decimal import Decimal, InvalidOperation, ROUND_DOWN

import ttkbootstrap as ttk


class ProrrateoManiobras:
    """Crea/edita Maniobras y prorratea su costo entre productos con IVA."""

    ESTADO_ELIMINADO = 3
    ESTADO_EDITADO = 2

    COLUMNAS = (
        ('codigo', 'Código', 105, tk.W),
        ('producto', 'Producto', 250, tk.W),
        ('cantidad', 'Cantidad', 75, tk.E),
        ('costo_anterior', 'Costo anterior', 105, tk.E),
        ('prorrateo', 'Prorrateo', 95, tk.E),
        ('costo_nuevo', 'Costo nuevo', 105, tk.E),
        ('iva', 'IVA documento', 100, tk.E),
        ('total', 'Total documento', 110, tk.E),
    )

    CAMPOS_SNAPSHOT = (
        'Quantity', 'cantidad', 'ProductID', 'ProductName', 'Description',
        'ProductKey', 'Unit', 'ClaveUnidad', 'ClaveProdServ', 'TaxTypeID',
        'TaxPerc', 'UnitPrice', 'CostPrice', 'precio', 'subtotal',
        'descuento', 'subtotal_con_descuento', 'iva', 'impuestos', 'total',
        'total_con_descuento', 'IEPSAmount', 'IVABase', 'IVAImport',
        'DocumentItemID', 'TipoCaptura', 'Comments',
        'ItemProductionStatusModified', 'ProrrateoManiobras',
        'ProrrateoManiobrasOperationID', 'uuid',
    )

    def __init__(
            self,
            master,
            documento,
            product_id_maniobras,
            user_id=0,
            guardar_prorrateo=None,
            revertir_prorrateo=None,
            registros_prorrateo=None,
            al_actualizar=None,
            producto_maniobras=None,
            tasa_iva_maniobras=Decimal('0.16'),
    ):
        self.master = master
        self.documento = documento
        self.product_id_maniobras = int(product_id_maniobras)
        self.user_id = int(user_id or 0)
        self.guardar_prorrateo = guardar_prorrateo
        self.revertir_prorrateo = revertir_prorrateo
        if registros_prorrateo is None:
            registros_prorrateo = getattr(
                self.documento,
                'prorrateo_maniobras',
                [],
            )
        self._registros_documento = [
            copy.deepcopy(dict(registro))
            for registro in (registros_prorrateo or [])
        ]
        self.registros_prorrateo = self._obtener_operacion_activa(
            self._registros_documento
        )
        self.al_actualizar = al_actualizar
        self.producto_maniobras = dict(producto_maniobras or {})
        self.tasa_iva_maniobras = self._normalizar_tasa(tasa_iva_maniobras)

        self.operation_id = (
            str(self.registros_prorrateo[0].get('OperationID'))
            if self.registros_prorrateo
            else str(uuid.uuid4())
        )
        self.aplicado = False
        self.revertido = False
        self.registros_persistencia = []
        self._plan = []
        self._snapshots = []
        self._maniobras_existia = False

        self.var_costo = tk.StringVar(value='0.00')
        self._crear_interfaz()
        self._cargar_estado_inicial()

    @staticmethod
    def _obtener_operacion_activa(registros):
        activos = [
            registro for registro in registros
            if registro.get('RevertedOn') in (None, '')
            and str(registro.get('DatabaseAction', '')).upper()
            not in ('DELETE', 'REVERT')
        ]
        if not activos:
            return []

        operaciones = {}
        for registro in activos:
            operation_id = str(registro.get('OperationID', ''))
            operaciones.setdefault(operation_id, []).append(registro)

        # La consulta debe venir ordenada; si no, se toma la operación con la
        # fecha de aplicación más reciente.
        operation_id = max(
            operaciones,
            key=lambda clave: max(
                str(registro.get('AppliedOn') or '')
                for registro in operaciones[clave]
            ),
        )
        return copy.deepcopy(operaciones[operation_id])

    @staticmethod
    def _decimal(valor):
        if valor in (None, ''):
            return Decimal('0')
        try:
            return Decimal(str(valor))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal('0')

    @classmethod
    def _normalizar_tasa(cls, valor):
        tasa = cls._decimal(valor)
        return tasa / Decimal('100') if tasa > 1 else tasa

    @classmethod
    def _moneda(cls, valor):
        numero = cls._decimal(valor).quantize(
            Decimal('0.01'), rounding=ROUND_DOWN
        )
        return f'$ {numero:,.2f}'

    @classmethod
    def _truncar_moneda(cls, valor):
        return cls._decimal(valor).quantize(
            Decimal('0.01'), rounding=ROUND_DOWN
        )

    @staticmethod
    def _esta_eliminada(partida):
        return int(partida.get('ItemProductionStatusModified', 0) or 0) == 3

    def _crear_interfaz(self):
        self.master.title('Prorrateo de maniobras')
        self.master.resizable(False, False)

        principal = ttk.Frame(self.master, padding=10)
        principal.grid(row=0, column=0, sticky=tk.NSEW)

        resumen = ttk.LabelFrame(
            principal, text='Partida Maniobras', padding=8
        )
        resumen.grid(row=0, column=0, sticky=tk.EW)

        ttk.Label(resumen, text='Costo:').grid(row=0, column=0, padx=5)
        self.tbx_costo = ttk.Entry(
            resumen,
            textvariable=self.var_costo,
            width=14,
            justify=tk.RIGHT,
        )
        self.tbx_costo.grid(row=0, column=1, padx=5)
        self.tbx_costo.bind('<KeyRelease>', self._actualizar_vista_previa)
        self.tbx_costo.bind('<FocusOut>', self._actualizar_vista_previa)

        self.lbl_impuestos = self._crear_indicador(
            resumen, 2, 'IMPUESTOS'
        )
        self.lbl_total = self._crear_indicador(resumen, 3, 'TOTAL')

        detalle = ttk.LabelFrame(
            principal,
            text='Productos con IVA que recibirán el costo',
            padding=6,
        )
        detalle.grid(row=1, column=0, pady=(10, 0), sticky=tk.NSEW)

        columnas = [columna[0] for columna in self.COLUMNAS]
        self.tabla = ttk.Treeview(
            detalle, columns=columnas, show='headings', height=12
        )
        for identificador, texto, ancho, alineacion in self.COLUMNAS:
            self.tabla.heading(identificador, text=texto)
            self.tabla.column(
                identificador,
                width=ancho,
                anchor=alineacion,
                stretch=False,
            )
        self.tabla.grid(row=0, column=0, sticky=tk.NSEW)

        barra = ttk.Scrollbar(
            detalle, orient=tk.VERTICAL, command=self.tabla.yview
        )
        barra.grid(row=0, column=1, sticky=tk.NS)
        self.tabla.configure(yscrollcommand=barra.set)

        botones = ttk.Frame(principal)
        botones.grid(row=2, column=0, pady=(10, 0), sticky=tk.E)

        self.btn_aplicar = ttk.Button(
            botones,
            text='Aplicar',
            bootstyle='success',
            command=self.aplicar,
        )
        self.btn_aplicar.grid(row=0, column=0, padx=4)

        self.btn_eliminar = ttk.Button(
            botones,
            text='Eliminar maniobras',
            bootstyle='danger',
            command=self.eliminar_maniobras,
        )
        self.btn_eliminar.grid(row=0, column=1, padx=4)

        self.btn_revertir = ttk.Button(
            botones,
            text='Revertir',
            bootstyle='warning',
            command=self.revertir,
            state='normal' if self.registros_prorrateo else 'disabled',
        )
        self.btn_revertir.grid(row=0, column=2, padx=4)

        ttk.Button(
            botones,
            text='Cerrar',
            bootstyle='secondary',
            command=self.master.destroy,
        ).grid(row=0, column=3, padx=4)

        self.master.bind('<Escape>', lambda _event: self.master.destroy())

    @staticmethod
    def _crear_indicador(frame, columna, texto):
        contenedor = ttk.Frame(frame, padding=4)
        contenedor.grid(row=0, column=columna, padx=8)
        ttk.Label(
            contenedor,
            text=texto,
            font=('Consolas', 10, 'bold'),
        ).grid(row=0, column=0)
        valor = ttk.Label(
            contenedor,
            text='$ 0.00',
            font=('Consolas', 16, 'bold'),
            bootstyle='danger',
        )
        valor.grid(row=1, column=0)
        return valor

    def _buscar_partida_maniobras(self, incluir_eliminada=False):
        return next((
            partida for partida in self.documento.items
            if int(partida.get('ProductID', 0) or 0)
            == self.product_id_maniobras
            and (incluir_eliminada or not self._esta_eliminada(partida))
        ), None)

    def _tasa_iva_partida(self, partida):
        subtotal = self._decimal(
            partida.get(
                'subtotal_con_descuento',
                partida.get('subtotal', 0),
            )
        )
        iva = self._decimal(partida.get('iva', 0))
        if subtotal > 0 and iva > 0:
            return iva / subtotal
        return self._normalizar_tasa(partida.get('TaxPerc', 0))

    def _partidas_aplicables(self):
        return [
            partida for partida in self.documento.items
            if not self._esta_eliminada(partida)
            and int(partida.get('ProductID', 0) or 0)
            != self.product_id_maniobras
            and self._decimal(
                partida.get('cantidad', partida.get('Quantity', 0))
            ) > 0
            and self._decimal(partida.get('subtotal', 0)) > 0
            and self._tasa_iva_partida(partida) > 0
            and abs(
                self._tasa_iva_partida(partida) - self.tasa_iva_maniobras
            ) <= Decimal('0.000001')
        ]

    def _costo_efectivo(self, partida):
        # En compras (módulo 152) el importe de la partida se afecta mediante
        # UnitPrice; CostPrice no forma parte del prorrateo.
        return self._decimal(
            partida.get('UnitPrice', partida.get('precio', 0))
        )

    def _leer_costo(self):
        texto = str(self.var_costo.get() or '').replace(',', '').strip()
        try:
            costo = Decimal(texto)
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError('El costo de Maniobras debe ser numérico.')
        if not costo.is_finite() or costo < 0:
            raise ValueError('El costo de Maniobras no puede ser negativo.')
        return costo

    def _obtener_subtotal_bruto_desde_neto(
            self,
            subtotal_neto,
            factor_descuento,
    ):
        """Obtiene un bruto cuyo descuento truncado produzca el neto exacto."""
        if factor_descuento <= 0:
            return subtotal_neto, Decimal('0')

        factor_neto = Decimal('1') - factor_descuento
        if factor_neto <= 0:
            raise ValueError(
                'Un descuento del 100 % impide realizar el prorrateo.'
            )

        subtotal_bruto = subtotal_neto / factor_neto
        for _ in range(10):
            descuento = self._truncar_moneda(
                subtotal_bruto * factor_descuento
            )
            nuevo_subtotal_bruto = subtotal_neto + descuento
            if nuevo_subtotal_bruto == subtotal_bruto:
                break
            subtotal_bruto = nuevo_subtotal_bruto

        descuento = self._truncar_moneda(
            subtotal_bruto * factor_descuento
        )
        subtotal_bruto = subtotal_neto + descuento
        return subtotal_bruto, descuento

    def _calcular_plan(self, costo_maniobras):
        partidas = self._partidas_aplicables()
        if not partidas:
            raise ValueError(
                'No se puede crear Maniobras porque el documento no tiene '
                'productos vigentes con IVA.'
            )

        base = sum(
            (self._decimal(p.get('subtotal', 0)) for p in partidas),
            Decimal('0'),
        )
        if base <= 0:
            raise ValueError('La base del prorrateo es cero.')

        impuesto_maniobras = self._truncar_moneda(
            costo_maniobras * self.tasa_iva_maniobras
        )
        plan = []
        acumulado = Decimal('0')
        impuesto_acumulado = Decimal('0')
        for indice, partida in enumerate(partidas):
            if indice == len(partidas) - 1:
                monto = costo_maniobras - acumulado
                monto_impuesto = impuesto_maniobras - impuesto_acumulado
            else:
                proporcion = self._decimal(partida.get('subtotal', 0)) / base
                monto = self._truncar_moneda(costo_maniobras * proporcion)
                monto_impuesto = self._truncar_moneda(
                    impuesto_maniobras * proporcion
                )
            acumulado += monto
            impuesto_acumulado += monto_impuesto

            cantidad = self._decimal(
                partida.get('cantidad', partida.get('Quantity', 0))
            )
            factor_descuento = self._decimal(
                partida.get('DiscountPerc', 0)
            )
            subtotal_neto_anterior = self._decimal(
                partida.get(
                    'subtotal_con_descuento',
                    self._decimal(partida.get('subtotal', 0))
                    - self._decimal(partida.get('descuento', 0)),
                )
            )
            subtotal_neto_nuevo = subtotal_neto_anterior + monto
            subtotal_bruto_nuevo, descuento_nuevo = (
                self._obtener_subtotal_bruto_desde_neto(
                    subtotal_neto_nuevo,
                    factor_descuento,
                )
            )
            monto_bruto = (
                subtotal_bruto_nuevo
                - self._decimal(partida.get('subtotal', 0))
            )
            costo_anterior = self._costo_efectivo(partida)
            costo_nuevo = subtotal_bruto_nuevo / cantidad
            plan.append({
                'partida': partida,
                'monto': monto,
                'monto_bruto': monto_bruto,
                'monto_impuesto': monto_impuesto,
                'subtotal_bruto_nuevo': subtotal_bruto_nuevo,
                'subtotal_neto_nuevo': subtotal_neto_nuevo,
                'descuento_nuevo': descuento_nuevo,
                'costo_anterior': costo_anterior,
                'costo_nuevo': costo_nuevo,
            })
        return plan

    def _cargar_estado_inicial(self):
        registro_maniobras = next((
            registro for registro in self.registros_prorrateo
            if bool(registro.get('IsManeuverItem'))
        ), None)
        if registro_maniobras:
            costo = registro_maniobras.get(
                'ProratedAmount',
                registro_maniobras.get('SubTotalBefore', 0),
            )
            self.var_costo.set(str(self._decimal(costo)))
            self._actualizar_vista_previa()
            return

        maniobras = self._buscar_partida_maniobras()
        if maniobras:
            self.var_costo.set(str(self._decimal(maniobras.get('subtotal', 0))))
        self._actualizar_vista_previa()

    def _restaurar_base_operacion_activa(self):
        """Restaura los valores Before sin registrar aún una reversión."""
        for registro in self.registros_prorrateo:
            partida = self._localizar_partida(registro)
            if partida is None:
                continue
            partida.update({
                'UnitPrice': self._decimal(registro.get('UnitPriceBefore', 0)),
                'precio': self._decimal(registro.get('UnitPriceBefore', 0)),
                'CostPrice': self._decimal(registro.get('CostPriceBefore', 0)),
                'subtotal': self._decimal(registro.get('SubTotalBefore', 0)),
                'descuento': self._decimal(
                    registro.get('DiscountAmountBefore', 0)
                ),
                'subtotal_con_descuento': self._decimal(
                    registro.get('SubTotalWithDiscountBefore', 0)
                ),
                'iva': self._decimal(registro.get('IVAAmountBefore', 0)),
                'impuestos': self._decimal(registro.get('TaxBefore', 0)),
                'total': self._decimal(registro.get('TotalBefore', 0)),
                'total_con_descuento': self._decimal(
                    registro.get('TotalWithDiscountBefore', 0)
                ),
            })

    @staticmethod
    def _clave_registro(registro):
        registro_id = registro.get('DocumentProrrateoManiobrasID')
        if registro_id:
            return 'ID', int(registro_id)
        if registro.get('IsManeuverItem'):
            return 'MANIOBRA', str(registro.get('OperationID', ''))
        document_item_id = int(registro.get('DocumentItemID', 0) or 0)
        if document_item_id:
            return 'ITEM', document_item_id
        return 'UUID', str(registro.get('ItemUUID') or '')

    @staticmethod
    def _es_mismo_registro(anterior, nuevo):
        anterior_id = anterior.get('DocumentProrrateoManiobrasID')
        nuevo_id = nuevo.get('DocumentProrrateoManiobrasID')
        if anterior_id and nuevo_id:
            return int(anterior_id) == int(nuevo_id)
        if anterior.get('IsManeuverItem') and nuevo.get('IsManeuverItem'):
            return True
        anterior_item = int(anterior.get('DocumentItemID', 0) or 0)
        nuevo_item = int(nuevo.get('DocumentItemID', 0) or 0)
        if anterior_item and nuevo_item:
            return anterior_item == nuevo_item
        anterior_uuid = str(anterior.get('ItemUUID') or '')
        nuevo_uuid = str(nuevo.get('ItemUUID') or '')
        return bool(anterior_uuid and anterior_uuid == nuevo_uuid)

    def _guardar_registros_en_documento(self, nuevos_registros):
        """Reemplaza la operación activa y conserva el resto del historial."""
        actualizados = []
        for nuevo in nuevos_registros:
            nuevo = copy.deepcopy(dict(nuevo))
            anterior = next((
                registro for registro in self.registros_prorrateo
                if self._es_mismo_registro(registro, nuevo)
            ), None)

            # Si Maniobras fue recreada puede cambiar su UUID; se identifica
            # también por su rol dentro de la misma operación.
            if anterior is None and nuevo.get('IsManeuverItem'):
                anterior = next((
                    registro for registro in self.registros_prorrateo
                    if registro.get('IsManeuverItem')
                ), None)

            if anterior:
                for campo in (
                    'DocumentProrrateoManiobrasID',
                    'AppliedOn',
                    'CreatedOn',
                ):
                    if anterior.get(campo) not in (None, ''):
                        nuevo[campo] = anterior[campo]
                nuevo['DatabaseAction'] = 'UPDATE'
            else:
                nuevo['DatabaseAction'] = 'INSERT'
            actualizados.append(nuevo)

        otras_operaciones = [
            copy.deepcopy(registro)
            for registro in self._registros_documento
            if str(registro.get('OperationID', '')) != self.operation_id
        ]
        coleccion = otras_operaciones + actualizados
        self.documento.prorrateo_maniobras = coleccion
        self._registros_documento = copy.deepcopy(coleccion)
        self.registros_prorrateo = copy.deepcopy(actualizados)

    def _actualizar_vista_previa(self, event=None):
        try:
            costo = self._leer_costo()
            self._plan = self._calcular_plan(costo)
            self.btn_aplicar.configure(state='normal' if costo > 0 else 'disabled')
        except ValueError:
            self._plan = []
            self.btn_aplicar.configure(state='disabled')

        impuesto = self._truncar_moneda(costo * self.tasa_iva_maniobras) \
            if 'costo' in locals() else Decimal('0')
        self.lbl_impuestos.configure(text=self._moneda(impuesto))
        self.lbl_total.configure(text=self._moneda(
            (costo if 'costo' in locals() else Decimal('0')) + impuesto
        ))
        self._pintar_plan()

    def _pintar_plan(self):
        self.tabla.delete(*self.tabla.get_children())
        for registro in self._plan:
            partida = registro['partida']
            self.tabla.insert('', tk.END, values=(
                partida.get('ProductKey', ''),
                partida.get('ProductName', partida.get('Description', '')),
                partida.get('cantidad', partida.get('Quantity', 0)),
                self._moneda(registro['costo_anterior']),
                self._moneda(registro['monto']),
                self._moneda(registro['costo_nuevo']),
                self._moneda(partida.get('iva', 0)),
                self._moneda(partida.get('total', 0)),
            ))

    def _crear_partida_maniobras(self, costo):
        impuesto = self._truncar_moneda(costo * self.tasa_iva_maniobras)
        total = costo + impuesto
        datos = {
            'ProductID': self.product_id_maniobras,
            'ProductName': 'MANIOBRAS',
            'Description': 'MANIOBRAS',
            'ProductKey': '',
            'Unit': 'SERVICIO',
            'ClaveUnidad': 'E48',
            'ClaveProdServ': '',
            'TaxTypeID': 0,
            'TaxPerc': self.tasa_iva_maniobras,
            'Quantity': Decimal('1'),
            'cantidad': Decimal('1'),
            'UnitPrice': costo,
            'CostPrice': Decimal('0'),
            'precio': costo,
            'DiscountPerc': Decimal('0'),
            'descuento': Decimal('0'),
            'subtotal': costo,
            'subtotal_con_descuento': costo,
            'iva': impuesto,
            'impuestos': impuesto,
            'total': total,
            'total_con_descuento': total,
            'DocumentItemID': 0,
            'TipoCaptura': 1,
            'Comments': '',
            'ItemProductionStatusModified': 0,
            'uuid': uuid.uuid4(),
        }
        datos.update(self.producto_maniobras)
        return datos

    def _actualizar_partida_maniobras(self, partida, costo):
        impuesto = self._truncar_moneda(costo * self.tasa_iva_maniobras)
        total = costo + impuesto
        partida.update({
            'Quantity': Decimal('1'),
            'cantidad': Decimal('1'),
            'UnitPrice': costo,
            'precio': costo,
            'DiscountPerc': Decimal('0'),
            'descuento': Decimal('0'),
            'subtotal': costo,
            'subtotal_con_descuento': costo,
            'iva': impuesto,
            'impuestos': impuesto,
            'total': total,
            'total_con_descuento': total,
            'ProrrateoManiobras': True,
            'ProrrateoManiobrasOperationID': self.operation_id,
        })
        self._marcar_editada(partida)

    def _actualizar_partida_destino(self, registro):
        partida = registro['partida']
        cantidad = self._decimal(
            partida.get('cantidad', partida.get('Quantity', 0))
        )
        subtotal_nuevo = registro['subtotal_bruto_nuevo']
        descuento_nuevo = registro['descuento_nuevo']
        subtotal_descuento_nuevo = registro['subtotal_neto_nuevo']
        iva_nuevo = (
            self._decimal(partida.get('iva', 0))
            + registro['monto_impuesto']
        )
        impuestos_nuevos = (
            self._decimal(partida.get('impuestos', 0))
            + registro['monto_impuesto']
        )
        retenciones = self._decimal(partida.get('retenciones', 0))
        total_nuevo = (
            subtotal_descuento_nuevo
            + impuestos_nuevos
            - retenciones
        )

        partida.update({
            'UnitPrice': registro['costo_nuevo'],
            'precio': registro['costo_nuevo'],
            'subtotal': subtotal_nuevo,
            'descuento': descuento_nuevo,
            'subtotal_con_descuento': subtotal_descuento_nuevo,
            'iva': iva_nuevo,
            'impuestos': impuestos_nuevos,
            'total': total_nuevo,
            'total_con_descuento': total_nuevo,
            'ProrrateoManiobras': True,
            'ProrrateoManiobrasOperationID': self.operation_id,
        })
        self._marcar_editada(partida)

    @classmethod
    def _marcar_editada(cls, partida):
        if int(partida.get('DocumentItemID', 0) or 0) != 0:
            partida['ItemProductionStatusModified'] = cls.ESTADO_EDITADO

    def _snapshot(self, partida):
        return {
            campo: copy.deepcopy(partida.get(campo))
            for campo in self.CAMPOS_SNAPSHOT
        }

    def aplicar(self):
        estado_actual = [
            (partida, self._snapshot(partida))
            for partida in self.documento.items
        ]
        if self.registros_prorrateo:
            self._restaurar_base_operacion_activa()

        try:
            costo = self._leer_costo()
            if costo <= 0:
                raise ValueError('El costo debe ser mayor que cero.')
            plan = self._calcular_plan(costo)
        except ValueError as error:
            for partida, snapshot in estado_actual:
                self._restaurar_snapshot(partida, snapshot)
            self._mostrar_error(str(error))
            return False

        maniobras = self._buscar_partida_maniobras(incluir_eliminada=True)
        self._maniobras_existia = maniobras is not None
        afectados = [registro['partida'] for registro in plan]
        anteriores = {id(p): self._snapshot(p) for p in afectados}

        if maniobras is None:
            maniobras = self._crear_partida_maniobras(costo)
            self.documento.items.append(maniobras)
        else:
            anteriores[id(maniobras)] = self._snapshot(maniobras)
            maniobras['ItemProductionStatusModified'] = 0

        try:
            self._actualizar_partida_maniobras(maniobras, costo)
            for registro in plan:
                self._actualizar_partida_destino(registro)

            # Maniobras funciona como partida origen. Una vez distribuido su
            # importe se excluye del documento activo para no duplicar costo,
            # IVA ni total; su estado previo queda en la bitácora reversible.
            maniobras['ItemProductionStatusModified'] = self.ESTADO_ELIMINADO

            self.registros_persistencia = self._crear_registros(
                maniobras, plan, anteriores
            )
            self._guardar_registros_en_documento(
                self.registros_persistencia
            )
            if callable(self.guardar_prorrateo):
                self.guardar_prorrateo(
                    self.documento.prorrateo_maniobras
                )

            self._snapshots = [
                (partida, anteriores[id(partida)]) for partida in afectados
            ]
            if self._maniobras_existia:
                self._snapshots.append((maniobras, anteriores[id(maniobras)]))

            self.aplicado = True
            self.btn_aplicar.configure(state='disabled')
            self.btn_revertir.configure(state='normal')
            self._recalcular_documento()
            return True
        except Exception as error:
            for partida in afectados:
                self._restaurar_snapshot(partida, anteriores[id(partida)])
            if self._maniobras_existia:
                self._restaurar_snapshot(maniobras, anteriores[id(maniobras)])
            elif maniobras in self.documento.items:
                self.documento.items.remove(maniobras)
            for partida, snapshot in estado_actual:
                self._restaurar_snapshot(partida, snapshot)
            self._mostrar_error(str(error))
            return False

    def eliminar_maniobras(self):
        if self.aplicado or self.registros_prorrateo:
            self.revertir()

        partida = self._buscar_partida_maniobras(incluir_eliminada=True)
        if partida is None:
            return False

        if int(partida.get('DocumentItemID', 0) or 0) == 0:
            self.documento.items.remove(partida)
        else:
            partida['ItemProductionStatusModified'] = self.ESTADO_ELIMINADO

        self.var_costo.set('0.00')
        self._recalcular_documento()
        self._actualizar_vista_previa()
        return True

    def revertir(self):
        if self._snapshots:
            for partida, snapshot in self._snapshots:
                self._restaurar_snapshot(partida, snapshot)
                self._marcar_editada(partida)

            maniobras = self._buscar_partida_maniobras(incluir_eliminada=True)
            if not self._maniobras_existia and maniobras in self.documento.items:
                self.documento.items.remove(maniobras)
        elif self.registros_prorrateo:
            self._revertir_desde_registros()
        else:
            return False

        if callable(self.revertir_prorrateo):
            self.revertir_prorrateo(self.operation_id, self.user_id)

        registros_reversion = copy.deepcopy(
            self.registros_persistencia or self.registros_prorrateo
        )
        for registro in registros_reversion:
            registro['DatabaseAction'] = 'REVERT'
            registro['RevertedBy'] = self.user_id
        otras_operaciones = [
            copy.deepcopy(registro)
            for registro in self._registros_documento
            if str(registro.get('OperationID', '')) != self.operation_id
        ]
        coleccion = otras_operaciones + registros_reversion
        self.documento.prorrateo_maniobras = coleccion
        self._registros_documento = copy.deepcopy(coleccion)
        self.registros_prorrateo = copy.deepcopy(registros_reversion)

        self.aplicado = False
        self.revertido = True
        self.btn_revertir.configure(state='disabled')
        self.btn_aplicar.configure(state='normal')
        self._recalcular_documento()
        self._cargar_estado_inicial()
        return True

    def _revertir_desde_registros(self):
        for registro in self.registros_prorrateo:
            partida = self._localizar_partida(registro)
            if partida is None:
                continue
            if registro.get('IsManeuverItem') and not registro.get(
                    'ItemExistedBefore', True
            ):
                if int(partida.get('DocumentItemID', 0) or 0) == 0:
                    self.documento.items.remove(partida)
                else:
                    partida['ItemProductionStatusModified'] = 3
                continue

            partida.update({
                'UnitPrice': self._decimal(registro.get('UnitPriceBefore', 0)),
                'precio': self._decimal(registro.get('UnitPriceBefore', 0)),
                'CostPrice': self._decimal(registro.get('CostPriceBefore', 0)),
                'subtotal': self._decimal(registro.get('SubTotalBefore', 0)),
                'descuento': self._decimal(
                    registro.get('DiscountAmountBefore', 0)
                ),
                'subtotal_con_descuento': self._decimal(
                    registro.get('SubTotalWithDiscountBefore', 0)
                ),
                'iva': self._decimal(registro.get('IVAAmountBefore', 0)),
                'impuestos': self._decimal(registro.get('TaxBefore', 0)),
                'total': self._decimal(registro.get('TotalBefore', 0)),
                'total_con_descuento': self._decimal(
                    registro.get('TotalWithDiscountBefore', 0)
                ),
            })
            self._marcar_editada(partida)
            self.operation_id = str(registro.get('OperationID', self.operation_id))

    def _crear_registros(self, maniobras, plan, anteriores):
        maniobra_id = int(maniobras.get('DocumentItemID', 0) or 0) or None
        maniobra_uuid = str(maniobras.get('uuid')) if maniobras.get('uuid') else None
        registros = []

        anterior_maniobras = anteriores.get(id(maniobras), {})
        registros.append(self._registro(
            maniobras,
            anterior_maniobras,
            self._decimal(maniobras.get('subtotal', 0)),
            True,
            self._maniobras_existia,
            maniobra_id,
            maniobra_uuid,
        ))
        for elemento in plan:
            partida = elemento['partida']
            registros.append(self._registro(
                partida,
                anteriores[id(partida)],
                elemento['monto'],
                False,
                True,
                maniobra_id,
                maniobra_uuid,
            ))
        return registros

    def _registro(
            self, partida, anterior, monto, es_maniobra,
            existia, maniobra_id, maniobra_uuid,
    ):
        def antes(campo, predeterminado=0):
            return self._decimal(anterior.get(campo, predeterminado))

        def despues(campo, predeterminado=0):
            return self._decimal(partida.get(campo, predeterminado))

        return {
            'DatabaseAction': 'INSERT',
            'OperationID': self.operation_id,
            'DocumentID': int(getattr(self.documento, 'document_id', 0) or 0),
            'DocumentItemID': int(partida.get('DocumentItemID', 0) or 0) or None,
            'ItemUUID': str(partida.get('uuid')) if partida.get('uuid') else None,
            'ManeuverDocumentItemID': maniobra_id,
            'ManeuverItemUUID': maniobra_uuid,
            'ProductID': int(partida.get('ProductID', 0) or 0),
            'IsManeuverItem': bool(es_maniobra),
            'ItemExistedBefore': bool(existia),
            'Quantity': despues('cantidad', partida.get('Quantity', 0)),
            'TaxTypeID': int(partida.get('TaxTypeID', 0) or 0),
            'TaxPerc': despues('TaxPerc'),
            'DiscountPerc': despues('DiscountPerc'),
            'ProratedAmount': self._decimal(monto),
            'UnitPriceBefore': antes('UnitPrice', anterior.get('precio', 0)),
            'CostPriceBefore': antes('CostPrice'),
            'SubTotalBefore': antes('subtotal'),
            'DiscountAmountBefore': antes('descuento'),
            'SubTotalWithDiscountBefore': antes('subtotal_con_descuento'),
            'TaxBefore': antes('impuestos'),
            'IVAAmountBefore': antes('iva'),
            'TotalBefore': antes('total'),
            'TotalWithDiscountBefore': antes('total_con_descuento'),
            'IEPSAmountBefore': antes('IEPSAmount'),
            'IVABaseBefore': antes('IVABase'),
            'IVAImportBefore': antes('IVAImport'),
            'UnitPriceAfter': despues('UnitPrice', partida.get('precio', 0)),
            'CostPriceAfter': despues('CostPrice'),
            'SubTotalAfter': despues('subtotal'),
            'DiscountAmountAfter': despues('descuento'),
            'SubTotalWithDiscountAfter': despues('subtotal_con_descuento'),
            'TaxAfter': despues('impuestos'),
            'IVAAmountAfter': despues('iva'),
            'TotalAfter': despues('total'),
            'TotalWithDiscountAfter': despues('total_con_descuento'),
            'IEPSAmountAfter': despues('IEPSAmount'),
            'IVABaseAfter': despues('IVABase'),
            'IVAImportAfter': despues('IVAImport'),
            'AppliedBy': self.user_id,
        }

    def _localizar_partida(self, registro):
        item_id = int(registro.get('DocumentItemID', 0) or 0)
        item_uuid = str(registro.get('ItemUUID') or '')
        return next((
            partida for partida in self.documento.items
            if (item_id and int(partida.get('DocumentItemID', 0) or 0) == item_id)
            or (item_uuid and str(partida.get('uuid', '')) == item_uuid)
        ), None)

    @staticmethod
    def _restaurar_snapshot(partida, snapshot):
        for campo, valor in snapshot.items():
            if valor is None:
                partida.pop(campo, None)
            else:
                partida[campo] = copy.deepcopy(valor)

    def _recalcular_documento(self):
        items = [p for p in self.documento.items if not self._esta_eliminada(p)]
        self.documento.subtotal = sum(
            (self._decimal(p.get('subtotal', 0)) for p in items), Decimal('0')
        )
        self.documento.total_discount = sum(
            (self._decimal(p.get('descuento', 0)) for p in items), Decimal('0')
        )
        self.documento.subtotal_with_discount = sum(
            (
                self._decimal(p.get(
                    'subtotal_con_descuento', p.get('subtotal', 0)
                )) for p in items
            ),
            Decimal('0'),
        )
        self.documento.total_tax = sum(
            (self._decimal(p.get('impuestos', 0)) for p in items), Decimal('0')
        )
        self.documento.total = sum(
            (self._decimal(p.get('total', 0)) for p in items), Decimal('0')
        )
        if callable(self.al_actualizar):
            self.al_actualizar()

    def _mostrar_error(self, mensaje):
        try:
            ttk.dialogs.Messagebox.show_error(
                message=mensaje,
                title='Prorrateo de maniobras',
                parent=self.master,
            )
        except Exception:
            print(mensaje)
