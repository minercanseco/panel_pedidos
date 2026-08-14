import datetime
import math

from .Herramientas.divisor_documentos_por_monto import DivisorDocumentosPorMonto
from .Herramientas.facturar_y_remisionar import FacturarYRemisionar


class ControladorDividirFacturas:
    def __init__(self,  interfaz, modelo):
        self._modelo = modelo
        self._interfaz = interfaz

        self._dividiendo = False
        self._rellenar_componentes()
        self._cargar_eventos()
        self._ajustar_apariencia()

    def _rellenar_componentes(self):
        self._rellenar_cbx_tipo()

        if self._modelo.info_documento:

            componentes = {
                'tbx_cliente': 'OfficialName',
                'tbx_folio': 'DocFolio',
                'tbx_tipo_cfd': 'TipoDocto',
                'tbx_total': 'Total',
                'txt_comentarios':'Comments',
            }
            for nombre_componente, clave in componentes.items():
                valor = self._modelo.info_documento.get(clave,'')
                if valor != '':
                    self._interfaz.ventanas.insertar_input_componente(nombre_componente, valor)
                    self._interfaz.ventanas.bloquear_componente(nombre_componente)

        if self._modelo.info_cliente.get('CayalCustomerTypeID',0) in (0,1) or self._modelo.info_cliente.get('OfficialNumber') == 'XAXX010101000':

            self._interfaz.ventanas.cambiar_estado_checkbutton('chk_remisiones', 'seleccionado')
            self._interfaz.ventanas.bloquear_componente('chk_remisiones')

        self._rellenar_tabla()

    def _rellenar_cbx_tipo(self):
        opciones = self._modelo.obtener_opciones_division()
        self._interfaz.ventanas.rellenar_cbx('cbx_dividir',opciones, sin_seleccione=False)

    def _rellenar_tabla(self):
        total_acumulado, partidas = self._modelo.obtener_partidas_tabla(self._modelo.document_id)
        self._interfaz.ventanas.rellenar_treeview('tvw_factura',
                                                  self._interfaz.columnas(),
                                                  partidas,
                                                  valor_barra_desplazamiento=10)

    def _cargar_eventos(self):
        eventos = {
            'btn_cancelar': self._interfaz.master.destroy,
            'btn_dividir':self._dividir_documento,
            'cbx_dividir': lambda event: self._ajustar_apariencia()
        }
        self._interfaz.ventanas.cargar_eventos(eventos)

    def _ajustar_apariencia(self):
        v = self._interfaz.ventanas

        def mostrar_todo():
            v.posicionar_frame('frame_tbx')
            v.posicionar_frame('frame_chk')
            v.posicionar_frame('frame_factura_tabla')

        def ocultar_monto():
            v.limpiar_componentes('tbx_monto')
            v.cambiar_estado_checkbutton('chk_exacto', 'deseleccionado')
            v.ocultar_frame('frame_tbx')
            v.ocultar_frame('frame_chk')

        def ocultar_tabla():
            v.ocultar_frame('frame_factura_tabla')

        seleccion = v.obtener_input_componente('cbx_dividir')

        # Siempre parte de un estado "visible" y luego oculta lo que toque
        mostrar_todo()

        # Si es "Facturar y Remisionar" => oculta tabla + todo lo de monto
        if seleccion == 'Facturar y Remisionar':
            ocultar_monto()
            ocultar_tabla()
            return

        # Si es cualquier opción distinta a "Por Monto" => oculta solo monto (tabla se queda)
        if seleccion != 'Por Monto':
            ocultar_monto()
            return

        # Si es "Por Monto" => se queda todo visible (no se hace nada extra)

    # ---------------------------------------------------------------------------------------------
    # Funcionalidades del aplicativo
    # ---------------------------------------------------------------------------------------------

    def _dividir_documento(self):

        seleccion = self._interfaz.ventanas.obtener_input_componente('cbx_dividir')
        if seleccion == 'Seleccione':
            self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar una opción válida.')
            return

        if self._dividiendo:
            return

        if seleccion == 'Facturar y Remisionar':
            if self._modelo.info_cliente.get('CayalCustomerTypeID',0) in (0,1):
                self._interfaz.ventanas.mostrar_mensaje('Esta opción solo puede utilizarse con clientes con datos fiscales.')
                return

            partidas_factura, partidas_remision = self._facturar_y_remisionar()
            if not partidas_factura or not partidas_remision:
                return

            documentos = {}
            plan_tipos_documentos = {}

            documentos[1] = partidas_factura
            plan_tipos_documentos[1] = (0, self._modelo.info_documento['BusinessEntityID'])


            documentos[2] = partidas_remision
            plan_tipos_documentos[2] = (1, self._modelo.info_documento['BusinessEntityID'])

            self._modelo.crear_documentos(documentos, plan_tipos_documentos, self._modelo.module_id)
            self._informar_no_olvidar_imprimir()
            self._interfaz.master.destroy()

        elif seleccion == 'Por Monto':
            documentos =  self._dividir_por_monto()
            if not documentos:
                return

            # 1 remsiones 0 facturas
            valor_remisiones = self._interfaz.ventanas.obtener_input_componente('chk_remisiones')
            tipo_cfd = 1 if valor_remisiones == 1 else 0
            tipo_cfd = 1 if self._modelo.info_cliente.get('CayalCustomerTypeID',0) in (0,1) else tipo_cfd

            plan_tipos_documentos = {}
            for i, (documento, partidas) in enumerate(documentos.items(), start=1):
                plan_tipos_documentos[i] = (tipo_cfd, self._modelo.info_documento['BusinessEntityID'])

            self._modelo.crear_documentos(documentos, plan_tipos_documentos, self._modelo.module_id)

            self._informar_no_olvidar_imprimir()
            self._interfaz.master.destroy()

        elif seleccion == 'Especial Pagoda':
            plan_montos = [1500, 1400, 1400,2000] #montos de las facturas del caso especial
            documentos = self._especial_pagoda(plan_montos)
            if not documentos:
                return

            plan_tipos_documentos = {}
            for i, (documento, partidas) in enumerate(documentos.items(), start=1):
                # 3 facturas el resto en remisiones
                plan_tipos_documentos[i] = (0,6986) if i < 4 else (1,7022)

            # hay que actualizar los datos del cliente a pagagoda gastronomica
            self._modelo.obtener_info_cliente(business_entity_id=6986)

            self._modelo.crear_documentos(documentos, plan_tipos_documentos, self._modelo.module_id)
            self._informar_no_olvidar_imprimir()
            self._interfaz.master.destroy()

        elif seleccion == 'Por Impuestos':
            documentos = self._dividir_por_impuestos()
            if not documentos:
                return

            # 1 remsiones 0 facturas
            valor_remisiones = self._interfaz.ventanas.obtener_input_componente('chk_remisiones')
            tipo_cfd = 1 if valor_remisiones == 1 else 0
            tipo_cfd = 1 if self._modelo.info_cliente.get('CayalCustomerTypeID', 0) in (0, 1) else tipo_cfd

            plan_tipos_documentos = {}
            for i, (documento, partidas) in enumerate(documentos.items(), start=1):
                plan_tipos_documentos[i] = (tipo_cfd,self._modelo.info_documento['BusinessEntityID'])

            self._modelo.crear_documentos(documentos, plan_tipos_documentos, self._modelo.module_id)
            self._informar_no_olvidar_imprimir()
            self._interfaz.master.destroy()

        elif seleccion == 'Por Producto':
            documentos =  self._dividir_por_producto()
            if not documentos:
                return

            valor_remisiones = self._interfaz.ventanas.obtener_input_componente('chk_remisiones')
            tipo_cfd = 1 if valor_remisiones == 1 else 0
            tipo_cfd = 1 if self._modelo.info_cliente.get('CayalCustomerTypeID', 0) in (0, 1) else tipo_cfd

            plan_tipos_documentos = {}
            for i, (documento, partidas) in enumerate(documentos.items(), start=1):
                plan_tipos_documentos[i] = (tipo_cfd, self._modelo.info_documento['BusinessEntityID'])


            self._modelo.crear_documentos(documentos, plan_tipos_documentos, self._modelo.module_id)
            self._informar_no_olvidar_imprimir()
            self._interfaz.master.destroy()

    def _facturar_y_remisionar(self):

        self._bloquear_acciones()

        ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(titulo='Facturar y Remisionar')
        instancia = FacturarYRemisionar(ventana, self._modelo.parametros, self._modelo.base_de_datos, self._modelo.utilerias)
        ventana.wait_window()

        if instancia.dividir_documento:
            return instancia.partidas_factura, instancia.partidas_remision

        return False, False

    def _dividir_por_monto(self, monto=0, plan_montos=None):
        funcion = self._modelo.utilerias.convertir_valor_a_decimal

        total_documento = self._interfaz.ventanas.obtener_input_componente('tbx_total')
        total_documento_decimal = funcion(total_documento)
        if not self._validar_monto(total_documento_decimal):
            return

        self._bloquear_acciones()

        if plan_montos is None:
            monto_ui = self._interfaz.ventanas.obtener_input_componente('tbx_monto') if monto == 0 else monto
            plan_montos = monto_ui  # monto único

        chk_exacto = self._interfaz.ventanas.obtener_input_componente('chk_exacto')  # 1 = NO redondear
        al_centavo = (chk_exacto == 1)

        partidas = self._modelo.obtener_partidas_documento(self._modelo.document_id)

        splitter = DivisorDocumentosPorMonto(
            convertir_decimal=self._modelo.utilerias.convertir_valor_a_decimal,
            crear_partida_con_impuestos=self._modelo.utilerias.crear_partida,
            equivalencia_especial_fn=self._modelo.utilerias.equivalencias_productos_especiales,
            redondear_qty_fn=getattr(self._modelo.utilerias, "convertir_valor_a_decimal", None),
        )

        return splitter.dividir(partidas, plan_montos=plan_montos, al_centavo=al_centavo)

    def _especial_pagoda(self, plan_montos):

        total_documento = self._modelo.info_documento.get('Total',0)
        if total_documento < 4500:
            self._interfaz.ventanas.mostrar_mensaje('Esta opción solo es válida para montos superiores a $ 4500.00')
            return

        if self._modelo.info_documento.get('BusinessEntityID',0) not in (6986, 7022):
            self._interfaz.ventanas.mostrar_mensaje('Esta opción solo es válida para el cliente Pagoda o Lobe Lara Richaud.')
            return

        if datetime.date.today().isoweekday() == 3:  # miércoles
            respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta('Esta opción es solo para los miércoles ¿Desea proceder?')
            if not respuesta:
                return

        self._bloquear_acciones()

        partidas = self._modelo.obtener_partidas_documento(self._modelo.document_id)

        al_centavo = 0
        splitter = DivisorDocumentosPorMonto(
            convertir_decimal=self._modelo.utilerias.convertir_valor_a_decimal,
            crear_partida_con_impuestos=self._modelo.utilerias.crear_partida,
            equivalencia_especial_fn=self._modelo.utilerias.equivalencias_productos_especiales,
            redondear_qty_fn=getattr(self._modelo.utilerias, "redondear_valor_cantidad_a_decimal", None),
        )

        return splitter.dividir(partidas, plan_montos=plan_montos, al_centavo=al_centavo)

    def _dividir_por_impuestos(self):
        partidas = self._modelo.obtener_partidas_documento(self._modelo.document_id)
        tax_types_ids = list(set([reg['TaxTypeID'] for reg in partidas]))
        if len(tax_types_ids) == 1:
            self._interfaz.ventanas.mostrar_mensaje('Solo hay un tipo de impuesto en el documento')
            return

        documentos = {}
        for i, tax_type_id in enumerate(tax_types_ids, start=1):
            nuevas_partidas = [reg for reg in partidas if reg['TaxTypeID'] == tax_type_id]
            documentos[i] = nuevas_partidas

        return documentos

    def _dividir_por_producto(self):
        partidas = self._modelo.obtener_partidas_documento(self._modelo.document_id)
        product_ids = list(set([reg['ProductID'] for reg in partidas]))

        if len(product_ids) == 1:
            pregunta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                'Solo hay un tipo de producto en el documento ¿Desea Proceder?')
            if not pregunta:
                return

        documentos = {}
        for i, product_id in enumerate(product_ids, start=1):
            nuevas_partidas = [reg for reg in partidas if reg['ProductID'] == product_id]
            documentos[i] = nuevas_partidas

        return documentos

    #---------------------------------------------------------------------------------------------
    # Helpers relacionados con la division
    # ---------------------------------------------------------------------------------------------
    def _informar_no_olvidar_imprimir(self):
        # solo aplica para facturas mayoreo
        if self._modelo.module_id == 21:
            order_document_id = self._modelo.info_documento.get('OrderDocumentID', 0)
            if order_document_id != 0:
                info_pedido = self._modelo.obtener_info_pedido(order_document_id)
                assigned_by = info_pedido.get('AssignedBy', 0)

                if assigned_by != 0:
                    self._interfaz.ventanas.mostrar_mensaje(
                        'No olvide imprimir las nuevas notas para que sean visibles a logística.', tipo='info')

    def _bloquear_acciones(self):

        componentes = [
            'btn_dividir',
            'btn_cancelar',
            'chk_exacto',
            'chk_remisiones'
        ]
        for componente in componentes:
            self._interfaz.ventanas.bloquear_componente(componente)
        self._dividiendo = True

    def _validar_monto(self, total_documento):
        if total_documento <= 0:
            self._interfaz.ventanas.mostrar_mensaje('El total del documento no puede ser menor o igual a Zero.')
            return

        monto = self._interfaz.ventanas.obtener_input_componente('tbx_monto')

        if not monto:
            self._interfaz.ventanas.mostrar_mensaje('Debe definir un monto.')
            return

        if not self._modelo.utilerias.es_cantidad(monto):
            self._interfaz.ventanas.mostrar_mensaje('Debe definir un monto válido.')
            return

        monto_decimal = self._modelo.utilerias.convertir_valor_a_decimal(monto)
        total_decimal = self._modelo.utilerias.convertir_valor_a_decimal(total_documento)

        if monto_decimal <= 0:
            self._interfaz.ventanas.mostrar_mensaje('El monto no puede ser menor o igual a cero.')
            return

        if monto_decimal >= total_decimal:
            self._interfaz.ventanas.mostrar_mensaje(
                'El monto de division no puede ser igual o mayor al monto del total del documento.'
            )
            return

        # Regla: si el total es > 1000, el monto por documento debe ser >= 500
        if total_decimal > 1000 and monto_decimal < 500:
            self._interfaz.ventanas.mostrar_mensaje(
                'Para totales mayores a $1,000 el monto por documento debe ser mínimo $500.'
            )
            return

        # Límite de "cantidad de documentos" SOLO cuando el total <= 1000
        if total_decimal <= 1000:
            try:
                num_docs = int(math.ceil(float(total_decimal / monto_decimal)))
            except Exception:
                self._interfaz.ventanas.mostrar_mensaje('No se pudo calcular la cantidad de documentos.')
                return

            if num_docs > 10:
                self._interfaz.ventanas.mostrar_mensaje('Error en cantidad de documentos.')
                return

        return True
