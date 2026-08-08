import tkinter as tk
from decimal import (
    Decimal,
    InvalidOperation,
    ROUND_CEILING,
    ROUND_HALF_UP,
)

from cayal.ventanas import Ventanas


class PartidaCompra:
    """Interfaz para revisar y actualizar el precio de compra de una partida."""

    TITULO = 'Partida de compra'
    ICONO = 'ProductChange32.ico'

    FUENTE_CAMPO = ('Arial', 10)
    FUENTE_RESUMEN = ('Consolas', 13, 'bold')
    FUENTE_TOTAL = ('Consolas', 20, 'bold')
    ESTILO_RESUMEN = 'inverse-danger'

    COMPONENTES_EDITABLES = (
        'tbx_cantidad_compra',
        'tbx_nuevo_costo_compra',
        'tbx_descuento_compra',
        'tbx_descuento_monto_compra',
        'tbx_importe_compra',
    )

    COMPONENTES_CALCULADOS = (
        'tbx_nombre_producto_compra',
        'tbx_clave_producto_compra',
        'tbx_costo_actual_compra',
    )

    ETIQUETAS_TOTALES = {
        'lbl_subtotal_compra': 'SUBTOTAL',
        'lbl_descuento_total_compra': 'DESCUENTO',
        'lbl_subtotal_descuento_compra': 'SUB-DESC',
        'lbl_impuesto_compra': 'IMPUESTO',
        'lbl_total_compra': 'TOTAL',
    }

    FUNCIONES_REQUERIDAS = (
        'actualizar_partida',
        'cancelar',
    )

    def __init__(
            self,
            master,
            utilerias,
            partida_producto=None,
            *,
            subtotal_documento=0,
            subtotal_con_descuento_documento=0,
            total_descuento_documento=0,
            total_impuesto_documento=0,
            total_documento=0,
            total_costo_documento=0,
            partida_incluida_en_totales=False,
    ):
        self._master = master
        self.configuracion = self._crear_configuracion()
        self.partida_producto = partida_producto if partida_producto is not None else {}
        self._partida_original = dict(self.partida_producto)
        self.ventanas = Ventanas(master)
        self._utilerias = utilerias
        self.funciones = {}
        self.partida_actualizada = False
        self.modo_descuento = 'porcentaje'
        self.modo_calculo = 'costo'
        self._recalculando = False
        self.partida_incluida_en_totales = partida_incluida_en_totales
        self.totales_documento = {
            'subtotal': self._decimal(subtotal_documento),
            'subtotal_con_descuento': self._decimal(subtotal_con_descuento_documento),
            'descuento': self._decimal(total_descuento_documento),
            'impuesto': self._decimal(total_impuesto_documento),
            'total': self._decimal(total_documento),
            'costo': self._decimal(total_costo_documento),
        }
        self._totales_partida_original = self._obtener_totales_partida(
            self._partida_original
        )

        self._crear_frames()
        self._crear_componentes()
        self._ajustar_componentes()
        self._configurar_estado_inicial()
        self.cargar_partida_producto(self.partida_producto)
        self._configurar_ventana()
        self.cargar_eventos()

    def _crear_configuracion(self):
        valores = {
            'titulo': self.TITULO,
            'icono': self.ICONO,
            'bloquear': True,
            'mostrar_descuento': True,
            'permitir_actualizar': True,
            'permitir_agregar': True,
            'costo_inicial': '0.00',
            'cantidad_inicial': '1.00',
            'descuento_inicial': '0.00',
            'descuento_monto_inicial': '0.00',
            'cantidad_minima': Decimal('0.000001'),
            'cantidad_maxima': Decimal('999999.999999'),
            'costo_minimo': Decimal('0.000001'),
            'costo_maximo': Decimal('999999999.99'),
            'total_minimo': Decimal('0.01'),
            'total_maximo': Decimal('999999999999.99'),
            'descuento_minimo': Decimal('0'),
            'descuento_maximo': Decimal('100'),
        }

        return valores

    @staticmethod
    def _grid(row, column=0, **opciones):
        posicion = {
            'row': row,
            'column': column,
            'padx': 5,
            'pady': 4,
            'sticky': tk.EW,
        }
        posicion.update(opciones)
        return posicion

    def _crear_frames(self):
        frames = {
            'frame_principal_compra': (
                'master',
                None,
                self._grid(0, sticky=tk.NSEW),
            ),
            'frame_datos_partida_compra': (
                'frame_principal_compra',
                'Actualizar partida de compra',
                self._grid(0, 0, padx=8, pady=8, sticky=tk.NSEW),
            ),
            'frame_producto_compra': (
                'frame_datos_partida_compra',
                'Producto seleccionado',
                self._grid(0, 0, columnspan=2, sticky=tk.NSEW),
            ),
            'frame_valores_compra': (
                'frame_datos_partida_compra',
                'Datos de la compra',
                self._grid(1, 0, columnspan=2, pady=(8, 0), sticky=tk.NSEW),
            ),
            'frame_botones_compra': (
                'frame_datos_partida_compra',
                None,
                self._grid(2, 0, columnspan=2, pady=10, sticky=tk.E),
            ),
            'frame_resumen_compra': (
                'frame_principal_compra',
                None,
                self._grid(0, 1, padx=(0, 8), pady=8, sticky=tk.NSEW),
            ),
        }
        self.ventanas.crear_frames(frames)

    def _crear_componentes(self):
        componentes = {
            'tbx_nombre_producto_compra': (
                'frame_producto_compra',
                self._grid(0, 1),
                'Producto:',
                None,
            ),
            'tbx_clave_producto_compra': (
                'frame_producto_compra',
                self._grid(1, 1),
                'Clave:',
                None,
            ),
            'tbx_cantidad_compra': (
                'frame_valores_compra',
                self._grid(0, 1),
                'Cantidad:',
                None,
            ),
            'tbx_costo_actual_compra': (
                'frame_valores_compra',
                self._grid(1, 1),
                'Costo anterior:',
                None,
            ),
            'tbx_nuevo_costo_compra': (
                'frame_valores_compra',
                self._grid(2, 1),
                'Nuevo costo:',
                None,
            ),
            'tbx_descuento_compra': (
                'frame_valores_compra',
                self._grid(3, 1),
                'Descuento (%):',
                None,
            ),
            'tbx_descuento_monto_compra': (
                'frame_valores_compra',
                self._grid(4, 1),
                'Descuento ($):',
                None,
            ),
            'tbx_importe_compra': (
                'frame_valores_compra',
                self._grid(5, 1),
                'Total neto editable:',
                None,
            ),
        }
        botones = {
            'btn_actualizar': (
                'frame_botones_compra',
                'success',
                'Aplicar cambios',
                '[F1]',
            ),
            'btn_cancelar': (
                'frame_botones_compra',
                'danger',
                'Cancelar',
                '[Esc]',
            ),
        }
        self.ventanas.crear_componentes(componentes)
        self.ventanas.crear_componentes(botones)
        self.ventanas.crear_componentes(self._crear_componentes_resumen())

    def _crear_componentes_resumen(self):
        componentes = {
            'lbl_titulo_resumen_compra': (
                'frame_resumen_compra',
                {
                    'text': 'RESUMEN DE LA PARTIDA',
                    'style': self.ESTILO_RESUMEN,
                    'font': self.FUENTE_RESUMEN,
                    'anchor': tk.CENTER,
                },
                self._grid(0, 0, columnspan=2, pady=(0, 12), sticky=tk.NSEW),
                None,
            ),
        }

        for fila, (nombre, texto) in enumerate(self.ETIQUETAS_TOTALES.items(), start=1):
            es_total = nombre == 'lbl_total_compra'
            fuente = self.FUENTE_TOTAL if es_total else self.FUENTE_RESUMEN
            pady = (16, 6) if es_total else 6
            componentes[f'{nombre}_texto'] = (
                'frame_resumen_compra',
                {
                    'text': texto,
                    'style': self.ESTILO_RESUMEN,
                    'font': fuente,
                    'anchor': tk.W,
                },
                self._grid(fila, 0, pady=pady, sticky=tk.NSEW),
                None,
            )
            componentes[nombre] = (
                'frame_resumen_compra',
                {
                    'text': '$ 0.00',
                    'style': self.ESTILO_RESUMEN,
                    'font': fuente,
                    'anchor': tk.E,
                    'width': 12,
                },
                self._grid(fila, 1, pady=pady, sticky=tk.NSEW),
                None,
            )
        return componentes

    def _ajustar_componentes(self):
        for componente in self.COMPONENTES_EDITABLES + self.COMPONENTES_CALCULADOS:
            self.ventanas.ajustar_ancho_componente(componente, 24)
        self.ventanas.ajustar_ancho_componente('tbx_nombre_producto_compra', 40)

    def _configurar_estado_inicial(self):
        valores = {
            'tbx_cantidad_compra': self.configuracion['cantidad_inicial'],
            'tbx_importe_compra': '0.00',
            'tbx_costo_actual_compra': self.configuracion['costo_inicial'],
            'tbx_nuevo_costo_compra': self.configuracion['costo_inicial'],
            'tbx_descuento_compra': self.configuracion['descuento_inicial'],
            'tbx_descuento_monto_compra': (
                self.configuracion['descuento_monto_inicial']
            ),
        }
        for componente, valor in valores.items():
            self.ventanas.insertar_input_componente(componente, valor)

        for componente in self.COMPONENTES_CALCULADOS:
            self.ventanas.bloquear_componente(componente)

        if not self.configuracion['mostrar_descuento']:
            self.ventanas.ocultar_componente('tbx_descuento_compra')
            self.ventanas.ocultar_componente('tbx_descuento_monto_compra')
            frame_valores = self.ventanas.componentes_forma['frame_valores_compra']
            for etiqueta in frame_valores.grid_slaves(row=3, column=0):
                etiqueta.grid_remove()
            for etiqueta in frame_valores.grid_slaves(row=4, column=0):
                etiqueta.grid_remove()
            self.ventanas.ocultar_componente('lbl_descuento_total_compra')
            self.ventanas.ocultar_componente('lbl_descuento_total_compra_texto')
            self.ventanas.ocultar_componente('lbl_subtotal_descuento_compra')
            self.ventanas.ocultar_componente('lbl_subtotal_descuento_compra_texto')

        if not self.configuracion['permitir_actualizar']:
            self.ventanas.ocultar_componente('btn_actualizar')

    def _configurar_ventana(self):
        self.ventanas.configurar_ventana_ttkbootstrap(
            titulo=self.configuracion['titulo'],
            bloquear=self.configuracion['bloquear'],
            nombre_icono=self.configuracion['icono'],
        )
        self.ventanas.enfocar_componente('tbx_nuevo_costo_compra')

    def inyectar_funciones(self, **funciones):
        """Enlaza las acciones proporcionadas por el controlador.

        Requeridas: ``actualizar_partida`` y ``cancelar``.
        Opcional: ``recalcular_partida``.
        """
        faltantes = [
            nombre
            for nombre in self.FUNCIONES_REQUERIDAS
            if nombre not in funciones or not callable(funciones[nombre])
        ]
        if faltantes:
            raise ValueError(
                'Faltan funciones requeridas para PartidaCompra: '
                + ', '.join(faltantes)
            )

        self.funciones = funciones.copy()
        eventos = {
            'btn_actualizar': funciones['actualizar_partida'],
            'btn_cancelar': funciones['cancelar'],
        }

        recalcular = funciones.get('recalcular_partida')
        if callable(recalcular):
            eventos.update({
                'tbx_cantidad_compra': recalcular,
                'tbx_nuevo_costo_compra': recalcular,
                'tbx_descuento_compra': recalcular,
                'tbx_descuento_monto_compra': recalcular,
                'tbx_importe_compra': recalcular,
            })

        self.ventanas.cargar_eventos(eventos)
        self.ventanas.agregar_hotkeys_forma({
            'F1': funciones['actualizar_partida'],
        })

    @staticmethod
    def _convertir_decimal(valor, predeterminado='0'):
        if valor in (None, ''):
            valor = predeterminado
        try:
            return Decimal(str(valor))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal(str(predeterminado))

    @classmethod
    def _decimal(cls, valor, predeterminado='0'):
        return cls._convertir_decimal(valor, predeterminado)

    def _leer_decimal_input(self, componente, etiqueta, minimo, maximo):
        valor = self.ventanas.obtener_input_componente(componente)
        texto = str(valor).strip().replace(',', '') if valor is not None else ''
        if not texto:
            raise ValueError(f'Debe capturar {etiqueta}.')
        try:
            numero = Decimal(texto)
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(f'{etiqueta.capitalize()} debe ser un número válido.')
        if not numero.is_finite():
            raise ValueError(f'{etiqueta.capitalize()} debe ser un número finito.')
        if numero < minimo or numero > maximo:
            raise ValueError(
                f'{etiqueta.capitalize()} debe estar entre {minimo} y {maximo}.'
            )
        return numero

    def _obtener_inputs_validados(self):
        cantidad = self._leer_decimal_input(
                'tbx_cantidad_compra',
                'la cantidad',
                self.configuracion['cantidad_minima'],
                self.configuracion['cantidad_maxima'],
            )
        costo = self._leer_decimal_input(
                'tbx_nuevo_costo_compra',
                'el nuevo costo',
                self.configuracion['costo_minimo'],
                self.configuracion['costo_maximo'],
            )
        subtotal = cantidad * costo

        if self.modo_descuento == 'monto':
            descuento_monto = self._leer_decimal_input(
                'tbx_descuento_monto_compra',
                'el monto del descuento',
                Decimal('0'),
                subtotal,
            )
            factor_descuento = self._factor_desde_monto(
                descuento_monto,
                subtotal,
            )
            descuento_porcentaje = factor_descuento * Decimal('100')
        else:
            descuento_porcentaje = self._leer_decimal_input(
                'tbx_descuento_compra',
                'el descuento',
                self.configuracion['descuento_minimo'],
                self.configuracion['descuento_maximo'],
            )
            factor_descuento = descuento_porcentaje / Decimal('100')
            descuento_monto = subtotal * factor_descuento

        return {
            'cantidad': cantidad,
            'costo': costo,
            'subtotal': subtotal,
            'descuento_porcentaje': descuento_porcentaje,
            'descuento_monto': descuento_monto,
            'factor_descuento': factor_descuento,
        }

    @staticmethod
    def _factor_desde_monto(monto, subtotal):
        """Convierte un monto monetario en el factor decimal usado por la BD."""
        if subtotal <= 0 or monto <= 0:
            return Decimal('0')
        if monto >= subtotal:
            return Decimal('1')

        # La BD admite 18 decimales. ROUND_CEILING evita que una fracción
        # periódica produzca un centavo menos al redondear posteriormente.
        return (monto / subtotal).quantize(
            Decimal('0.000000000000000001'),
            rounding=ROUND_CEILING,
        )

    @staticmethod
    def _formatear_decimal(valor, decimales=2):
        formato = Decimal('1').scaleb(-decimales)
        return str(valor.quantize(formato, rounding=ROUND_HALF_UP))

    @classmethod
    def _formatear_moneda(cls, valor):
        return f'$ {cls._formatear_decimal(valor, 6)}'

    def _obtener_factor_descuento(self, partida):
        if partida.get('DiscountPerc') not in (None, ''):
            factor = self._decimal(partida.get('DiscountPerc'))
            return max(Decimal('0'), min(factor, Decimal('1')))

        porcentaje = self._decimal(partida.get('descuento_porcentaje', 0))
        return max(Decimal('0'), min(porcentaje / Decimal('100'), Decimal('1')))

    def _obtener_costo_partida(self, partida):
        """Obtiene el costo unitario mostrado en la tabla de compras.

        La columna ``Costo U.`` se construye con el precio de la partida. Por
        eso ``UnitPrice``/``precio`` deben prevalecer sobre ``CostPrice``, que
        puede contener el costo anterior del producto.
        """
        for campo in ('UnitPrice', 'precio', 'CostPrice'):
            costo = self._decimal(partida.get(campo, 0))
            if costo > 0:
                return costo
        return Decimal('0')

    def _obtener_totales_partida(self, partida):
        cantidad = self._decimal(
            partida.get('cantidad', partida.get('Quantity', 0))
        )
        costo = self._obtener_costo_partida(partida)
        subtotal = cantidad * costo
        factor_descuento = self._obtener_factor_descuento(partida)
        descuento = subtotal * factor_descuento
        subtotal_con_descuento = subtotal - descuento

        impuesto_bruto = self._decimal(
            partida.get('impuestos', partida.get('TotalTax', 0))
        )
        impuesto = impuesto_bruto * (Decimal('1') - factor_descuento)
        total = subtotal_con_descuento + impuesto
        return {
            'subtotal': subtotal,
            'subtotal_con_descuento': subtotal_con_descuento,
            'descuento': descuento,
            'impuesto': impuesto,
            'total': total,
            'costo': subtotal,
        }

    def _actualizar_totales_documento(self, nuevos_totales):
        for nombre, nuevo_valor in nuevos_totales.items():
            valor = self.totales_documento.get(nombre, Decimal('0'))
            if self.partida_incluida_en_totales:
                valor -= self._totales_partida_original.get(nombre, Decimal('0'))
            self.totales_documento[nombre] = valor + nuevo_valor

    def _mostrar_totales_partida(self, totales):
        self.actualizar_resumen({
            'subtotal': self._formatear_moneda(totales['subtotal']),
            'descuento': self._formatear_moneda(totales['descuento']),
            'subtotal_descuento': self._formatear_moneda(
                totales['subtotal_con_descuento']
            ),
            'impuesto': self._formatear_moneda(totales['impuesto']),
            'total': self._formatear_moneda(totales['total']),
            'importe': self._formatear_decimal(totales['total'], 6),
        })

    def cargar_partida_producto(self, partida_producto):
        """Carga los datos generales y calcula el importe inicial de compra."""
        self.partida_producto = partida_producto or {}

        cantidad = self._convertir_decimal(
            self.partida_producto.get(
                'cantidad',
                self.partida_producto.get('CayalPiece', 1),
            ),
            predeterminado='1',
        )
        costo = self._obtener_costo_partida(self.partida_producto)
        factor_descuento = self._obtener_factor_descuento(self.partida_producto)
        descuento_porcentaje = factor_descuento * Decimal('100')
        totales = self._obtener_totales_partida(self.partida_producto)

        valores_componentes = {
            'tbx_nombre_producto_compra': self.partida_producto.get('ProductName', ''),
            'tbx_clave_producto_compra': self.partida_producto.get('ProductKey', ''),
            'tbx_cantidad_compra': self._formatear_decimal(cantidad, 6),
            'tbx_costo_actual_compra': self._formatear_decimal(costo, 6),
            'tbx_nuevo_costo_compra': self._formatear_decimal(costo, 6),
            'tbx_descuento_compra': self._formatear_decimal(descuento_porcentaje),
            'tbx_descuento_monto_compra': self._formatear_decimal(
                totales['descuento'],
                6,
            ),
        }
        for componente, valor in valores_componentes.items():
            self.ventanas.insertar_input_componente(componente, valor)

        self._mostrar_totales_partida(totales)

        self.product_id = self.partida_producto.get('ProductID', 0)
        self.product_name = self.partida_producto.get('ProductName', '')
        self.product_key = self.partida_producto.get('ProductKey', '')
        self.tax_type_id = self.partida_producto.get('TaxTypeID', 0)
        self.fecha_costo = self.partida_producto.get('FechaCosto')

        # insertar_input_componente habilita temporalmente los Entry; se
        # restablece aquí el estado de los campos informativos/calculados.
        for componente in self.COMPONENTES_CALCULADOS:
            self.ventanas.bloquear_componente(componente)

        self.ventanas.bloquear_componente('tbx_descuento_compra')


    def actualizar_resumen(self, valores):
        """Actualiza los indicadores con valores ya calculados por el controlador."""
        componentes = {
            'subtotal': 'lbl_subtotal_compra',
            'descuento': 'lbl_descuento_total_compra',
            'subtotal_descuento': 'lbl_subtotal_descuento_compra',
            'impuesto': 'lbl_impuesto_compra',
            'total': 'lbl_total_compra',
            'importe': 'tbx_importe_compra',
        }
        for clave, componente in componentes.items():
            if clave in valores:
                self.ventanas.insertar_input_componente(
                    componente,
                    valores[clave],
                )

    def cargar_productos(self, productos, seleccion=None):
        """Compatibilidad: carga una partida desde una lista o diccionario."""
        if isinstance(productos, dict):
            self.cargar_partida_producto(productos)
            return

        productos = list(productos or [])
        if not productos:
            return

        partida = seleccion if isinstance(seleccion, dict) else productos[0]
        self.cargar_partida_producto(partida)

    def cargar_eventos(self):
        eventos = {
            'btn_cancelar': self.cancelar,
            'btn_actualizar': self.actualizar_partida,
            'tbx_cantidad_compra': self.recalcular_vista,
            'tbx_nuevo_costo_compra': self.recalcular_vista,
            'tbx_descuento_compra': self._recalcular_desde_porcentaje,
            'tbx_descuento_monto_compra': self._recalcular_desde_monto,
            'tbx_importe_compra': self._recalcular_desde_total,
        }
        self.ventanas.cargar_eventos(eventos)
        self.ventanas.agregar_hotkeys_forma({'F1': self.actualizar_partida})

        for nombre in self.COMPONENTES_EDITABLES:
            componente = self.ventanas.componentes_forma[nombre]
            componente.bind('<FocusOut>', self.recalcular_vista, add='+')

        self.ventanas.componentes_forma['tbx_descuento_compra'].bind(
            '<FocusIn>',
            lambda _event: self._establecer_modo_descuento('porcentaje'),
            add='+',
        )
        self.ventanas.componentes_forma['tbx_descuento_compra'].bind(
            '<FocusIn>',
            lambda _event: self._establecer_modo_calculo('costo'),
            add='+',
        )
        self.ventanas.componentes_forma['tbx_descuento_monto_compra'].bind(
            '<FocusIn>',
            lambda _event: self._establecer_modo_descuento('monto'),
            add='+',
        )
        self.ventanas.componentes_forma['tbx_descuento_monto_compra'].bind(
            '<FocusIn>',
            lambda _event: self._establecer_modo_calculo('costo'),
            add='+',
        )
        self.ventanas.componentes_forma['tbx_importe_compra'].bind(
            '<FocusIn>',
            lambda _event: self._establecer_modo_calculo('total'),
            add='+',
        )
        for nombre in ('tbx_cantidad_compra', 'tbx_nuevo_costo_compra'):
            self.ventanas.componentes_forma[nombre].bind(
                '<FocusIn>',
                lambda _event: self._establecer_modo_calculo('costo'),
                add='+',
            )

    def _establecer_modo_descuento(self, modo):
        self.modo_descuento = modo

    def _establecer_modo_calculo(self, modo):
        self.modo_calculo = modo

    def _recalcular_desde_porcentaje(self, event=None):
        self._establecer_modo_descuento('porcentaje')
        self.ventanas.bloquear_componente('tbx_descuento_compra')

        return self.recalcular_vista(event)

    def _recalcular_desde_monto(self, event=None):
        self._establecer_modo_descuento('monto')
        return self.recalcular_vista(event)

    def _recalcular_desde_total(self, event=None):
        self._establecer_modo_calculo('total')
        return self.recalcular_vista(event)

    def _totales_con_costo(self, cantidad, costo):
        partida_temporal = dict(self.partida_producto)
        partida_temporal.update({
            'cantidad': cantidad,
            'Quantity': cantidad,
            'CostPrice': costo,
            'UnitPrice': costo,
        })

        subtotal = cantidad * costo
        if self.modo_descuento == 'monto':
            monto = self._leer_decimal_input(
                'tbx_descuento_monto_compra',
                'el monto del descuento',
                Decimal('0'),
                self.configuracion['total_maximo'],
            )
            monto = min(monto, subtotal)
            factor = self._factor_desde_monto(monto, subtotal)
        else:
            porcentaje = self._leer_decimal_input(
                'tbx_descuento_compra',
                'el descuento',
                self.configuracion['descuento_minimo'],
                self.configuracion['descuento_maximo'],
            )
            factor = porcentaje / Decimal('100')

        partida_temporal['DiscountPerc'] = factor
        self._utilerias.crear_partida(
            partida_temporal,
            cantidad=cantidad,
            tipo='compra',
        )
        return self._obtener_totales_partida(partida_temporal)

    def _calcular_costo_desde_total(self, cantidad, total_objetivo):
        """Obtiene el costo que produce el total solicitado por el usuario."""
        inferior = self.configuracion['costo_minimo']
        superior = max(
            total_objetivo / cantidad * Decimal('2'),
            Decimal('1'),
        )
        superior = min(superior, self.configuracion['costo_maximo'])

        while (
                self._totales_con_costo(cantidad, superior)['total']
                < total_objetivo
                and superior < self.configuracion['costo_maximo']
        ):
            superior = min(
                superior * Decimal('2'),
                self.configuracion['costo_maximo'],
            )

        if self._totales_con_costo(cantidad, superior)['total'] < total_objetivo:
            raise ValueError('El total solicitado excede el costo máximo permitido.')

        # La función de total es monótona respecto del costo. La búsqueda
        # también funciona cuando impuestos o descuentos introducen redondeos.
        for _ in range(60):
            medio = (inferior + superior) / Decimal('2')
            if self._totales_con_costo(cantidad, medio)['total'] < total_objetivo:
                inferior = medio
            else:
                superior = medio

        return superior.quantize(Decimal('0.000001'), rounding=ROUND_CEILING)

    def recalcular_vista(self, event=None):
        if self._recalculando:
            return False

        self._recalculando = True
        try:
            if self.modo_calculo == 'total':
                cantidad = self._leer_decimal_input(
                    'tbx_cantidad_compra',
                    'la cantidad',
                    self.configuracion['cantidad_minima'],
                    self.configuracion['cantidad_maxima'],
                )
                total_objetivo = self._leer_decimal_input(
                    'tbx_importe_compra',
                    'el total neto',
                    self.configuracion['total_minimo'],
                    self.configuracion['total_maximo'],
                )
                costo = self._calcular_costo_desde_total(
                    cantidad,
                    total_objetivo,
                )
                self.ventanas.insertar_input_componente(
                    'tbx_nuevo_costo_compra',
                    self._formatear_decimal(costo, 6),
                )

            entradas = self._obtener_inputs_validados()
        except ValueError:
            return False
        finally:
            self._recalculando = False

        partida_temporal = dict(self.partida_producto)
        partida_temporal.update({
            'cantidad': entradas['cantidad'],
            'Quantity': entradas['cantidad'],
            'CostPrice': entradas['costo'],
            'UnitPrice': entradas['costo'],
            'DiscountPerc': entradas['factor_descuento'],
        })
        self._utilerias.crear_partida(
            partida_temporal,
            cantidad=entradas['cantidad'],
            tipo='compra',
        )
        totales = self._obtener_totales_partida(partida_temporal)
        self.ventanas.insertar_input_componente(
            'tbx_descuento_compra',
            self._formatear_decimal(entradas['descuento_porcentaje'], 6),
        )
        self.ventanas.insertar_input_componente(
            'tbx_descuento_monto_compra',
            self._formatear_decimal(totales['descuento'], 6),
        )
        self._mostrar_totales_partida(totales)
        self.ventanas.bloquear_componente('tbx_descuento_compra')
        return True

    def cancelar(self):
        self.partida_actualizada = False
        self._master.destroy()

    def actualizar_partida(self):
        """Valida y modifica en el lugar la partida entregada por el controlador."""
        if not self.partida_producto.get('ProductID'):
            self.ventanas.mostrar_mensaje('La partida no contiene un producto válido.')
            return False

        # F1 no cambia el foco; garantiza que un total recién capturado haya
        # recalculado el costo antes de guardar la partida.
        if self.modo_calculo == 'total' and not self.recalcular_vista():
            self.ventanas.mostrar_mensaje('El total neto capturado no es válido.')
            return False

        try:
            entradas = self._obtener_inputs_validados()
        except ValueError as error:
            self.ventanas.mostrar_mensaje(str(error))
            return False

        factor_descuento = entradas['factor_descuento']
        self.partida_producto.update({
            'Quantity': entradas['cantidad'],
            'cantidad': entradas['cantidad'],
            'CostPrice': entradas['costo'],
            'UnitPrice': entradas['costo'],
            # La BD usa factor decimal: 2.25 % se guarda como 0.0225.
            'DiscountPerc': factor_descuento,
            'descuento_porcentaje': entradas['descuento_porcentaje'],
        })
        self._utilerias.crear_partida(
            self.partida_producto,
            cantidad=entradas['cantidad'],
            tipo='compra',
        )

        totales = self._obtener_totales_partida(self.partida_producto)
        self.partida_producto.update({
            'descuento': totales['descuento'],
            'subtotal_con_descuento': totales['subtotal_con_descuento'],
            'total_con_descuento': totales['total'],
        })
        self._actualizar_totales_documento(totales)
        self._mostrar_totales_partida(totales)

        # Sólo las partidas que ya existen en la base de datos se marcan
        # como editadas. Las nuevas conservan el flujo regular de inserción.
        document_item_id = self._decimal(
            self.partida_producto.get('DocumentItemID', 0)
        )
        if document_item_id != 0:
            self.partida_producto['ItemProductionStatusModified'] = 2

        self.partida_actualizada = True
        self._master.destroy()
        return True
