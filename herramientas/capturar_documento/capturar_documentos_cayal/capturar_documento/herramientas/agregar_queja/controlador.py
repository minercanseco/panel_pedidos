import tkinter as tk

class ControladorAgregarQueja:
    GRUPOS_ADMIN = (5,3,15,7,6,1)

    def __init__(self, interfaz, modelo):
        self._interfaz = interfaz
        self._modelo = modelo
        self._ventanas = self._interfaz.ventanas
        self._master = self._interfaz._master

        self._empleados = []
        self._areas = []
        self._sub_areas_por_indice = {}
        self._tipos = []
        self._productos = []
        self._info_quejas = []

        self._user_id = self._modelo.user_id
        self._user_group_id = self._modelo.user_group_id()
        self._document_id = self._modelo.document_id
        self._module_id = self._modelo.module_id

        self._cargar_catalogos()
        self._inyectar_funciones_barra_herramientas()
        self._rellenar_info_desde_bd()

    def _inyectar_funciones_barra_herramientas(self):
        funciones = {
            'agregar_queja': self._agregar_queja,
            'guardar': self._guardar_quejas,
            'eliminar': self._eliminar_queja_actual,
            'modificaciones': self._llamar_instancia_modificaciones,
            'historial': self._llamar_instancia_historial,
        }

        for item in self._interfaz.barra_herramientas:
            nombre = item.get('nombre')

            if nombre in funciones:
                item['comando'] = funciones[nombre]

        self._interfaz.elementos_barra_herramientas = (
            self._interfaz.ventanas.crear_barra_herramientas(
                self._interfaz.barra_herramientas,
                'frame_toolbar'
            )
        )

        self._interfaz.hotkeys_barra_herramientas = (
            self._interfaz.elementos_barra_herramientas[1]
        )

        self._interfaz.etiquetas_barra_herramientas = (
            self._interfaz.elementos_barra_herramientas[2]
        )

    def _cargar_catalogos(self):
        self._empleados = self._modelo.obtener_empleados()
        self._areas = self._modelo.obtener_areas()
        self._tipos = self._modelo.obtener_tipos_queja()
        self._productos = self._modelo.obtener_productos_documento()

        self._empleados_texto = sorted([
            reg['OfficialName'] for reg in self._empleados
        ])

        self._areas_texto = sorted([
            reg['Value'] for reg in self._areas
        ])

        self._tipos_texto = sorted([
            reg['ItemValue'] for reg in self._tipos
        ])

        self._productos_texto = sorted([
            reg['Producto'] for reg in self._productos
        ])

        self._productos_texto.insert(0, 'DOCUMENTO COMPLETO')

    def _agregar_queja(self):
        self._interfaz._agregar_queja()

        indice = self._interfaz._contador_quejas

        self._rellenar_cbxs_queja(indice)
        self._rellenar_cbx_producto(indice)
        self._cargar_eventos_queja(indice)

    def _rellenar_cbxs_queja(self, indice):
        componentes = {
            f'cbx_tipo_{indice}': self._tipos_texto,
            f'cbx_responsable_{indice}': self._empleados_texto,
            f'cbx_area_{indice}': self._areas_texto,
        }

        for componente, valores in componentes.items():
            if componente in self._ventanas.componentes_forma:
                self._ventanas.rellenar_cbx(componente, valores)

    def _rellenar_cbx_sub_area(self, indice):
        cbx_area = f'cbx_area_{indice}'
        cbx_sub_area = f'cbx_sub_area_{indice}'

        seleccion = self._ventanas.obtener_input_componente(cbx_area)

        if seleccion == 'Seleccione':
            return

        area = [
            reg for reg in self._areas
            if reg['Value'] == seleccion
        ]

        if not area:
            return

        area_id = area[0]['ID']

        self._sub_areas_por_indice[indice] = self._modelo.obtener_sub_areas(area_id)

        sub_areas = sorted([
            reg['Value'] for reg in self._sub_areas_por_indice[indice]
        ])

        self._ventanas.rellenar_cbx(cbx_sub_area, sub_areas)

    def _rellenar_info_desde_bd(self):
        self._rellenar_cbxs_queja(1)
        self._rellenar_cbx_producto(1)
        self._cargar_eventos_queja(1)

        self._info_quejas = self._modelo.obtener_quejas_documento()

        if not self._info_quejas:
            self._ventanas.bloquear_componente('eliminar')
            self._bloquear_capturo(1)
            return

        for posicion, info_queja in enumerate(self._info_quejas, start=1):
            if posicion > 1:
                self._agregar_queja()

            self._rellenar_info_queja(posicion, info_queja)

    def _rellenar_info_queja(self, indice, info_queja):
        self._interfaz._quejas[indice]['queja_id'] = info_queja['ID']
        self._interfaz._quejas[indice]['document_id'] = info_queja['DocumentID']

        editable = 1 if self._puede_editar_queja(info_queja) else 0
        self._interfaz._quejas[indice]['editable'] = editable

        valores = {
            f'cbx_tipo_{indice}': 'TipoDeError',
            f'cbx_producto_{indice}': 'Producto',
            f'txt_comentario_{indice}': 'Comentario',
            f'cbx_responsable_{indice}': 'Responsable',
            f'cbx_area_{indice}': 'Area',
            f'cbx_sub_area_{indice}': 'SubArea',
            f'txt_seguimiento_{indice}': 'Seguimiento',
            f'tbx_capturo_{indice}': 'UserName',
        }

        for componente, clave in valores.items():
            if componente not in self._ventanas.componentes_forma:
                continue

            # Solo administradores pueden ver quién capturó la queja
            if clave == 'UserName' and self._user_group_id not in self.GRUPOS_ADMIN:
                self._ventanas.ocultar_componente(componente)
                continue

            valor = info_queja.get(clave, '')

            if valor is None:
                valor = ''

            if componente == f'cbx_area_{indice}':
                self._ventanas.insertar_input_componente(componente, valor)
                self._rellenar_cbx_sub_area(indice)
                continue

            self._ventanas.insertar_input_componente(componente, valor)

        chk_salio = f'chk_salio_{indice}'

        if chk_salio in self._ventanas.componentes_forma:
            if info_queja.get('Salio') == 1:
                self._ventanas.cambiar_estado_checkbutton(chk_salio, 'seleccionado')
            else:
                self._ventanas.cambiar_estado_checkbutton(chk_salio, 'deseleccionado')

        self._bloquear_capturo(indice)

        if editable == 0:
            self._bloquear_formulario_queja(indice)

    def _obtener_valor_check_salio(self, indice):
        componente = f'chk_salio_{indice}'

        if componente not in self._ventanas.componentes_forma:
            return 0

        valor = self._ventanas.obtener_input_componente(componente)

        if valor in (1, True, '1', 'true', 'True', 'SI', 'Sí', 'si', 'sí'):
            return 1

        return 0

    def _bloquear_capturo(self, indice):
        componente = f'tbx_capturo_{indice}'

        if componente in self._ventanas.componentes_forma:
            self._ventanas.bloquear_componente(componente)

    def _guardar_quejas(self):
        if not self._validar_quejas():
            return

        quejas = self._obtener_datos_quejas()

        self._modelo.guardar_quejas(quejas)

        self._master.destroy()

    def _obtener_datos_quejas(self):
        quejas = []

        for indice, datos in self._interfaz._quejas.items():
            if datos.get('eliminado') == 1:
                continue

            if datos.get('editable', 1) == 0:
                continue

            producto = self._valor(f'cbx_producto_{indice}')

            if not producto or producto == 'Seleccione':
                producto = 'DOCUMENTO COMPLETO'

            if producto == 'DOCUMENTO COMPLETO':
                producto_bd = 'DOCUMENTO COMPLETO'
                product_id = 0
            else:
                producto_bd = producto
                product_id = self._obtener_product_id(producto)

            quejas.append({
                'QuejaID': datos.get('queja_id'),
                'DocumentID': self._document_id,
                'Tipo': self._valor(f'cbx_tipo_{indice}'),
                'Producto': producto_bd,
                'ProductID': product_id,
                'Comentario': self._valor(f'txt_comentario_{indice}'),
                'Responsable': self._valor(f'cbx_responsable_{indice}'),
                'Salio': self._obtener_valor_check_salio(indice),
                'Area': self._valor(f'cbx_area_{indice}'),
                'SubArea': self._valor(f'cbx_sub_area_{indice}'),
                'Seguimiento': self._valor(f'txt_seguimiento_{indice}'),
            })

        return quejas

    def _validar_quejas(self):
        for indice, datos in self._interfaz._quejas.items():
            if datos.get('eliminado') == 1:
                continue

            if datos.get('editable', 1) == 0:
                continue

            if not self._validar_queja(indice):
                return False

        return True

    def _validar_queja(self, indice):
        valores = {
            f'cbx_tipo_{indice}': 'tipo',
            f'cbx_producto_{indice}': 'producto',
            f'txt_comentario_{indice}': 'comentario',
            f'cbx_responsable_{indice}': 'responsable',
            f'cbx_area_{indice}': 'área',
            f'cbx_sub_area_{indice}': 'sub área',
            f'txt_seguimiento_{indice}': 'seguimiento',
        }

        for componente, nombre in valores.items():
            if componente not in self._ventanas.componentes_forma:
                continue

            valor = self._valor(componente)

            tipo = componente[0:3]

            if tipo == 'cbx':
                if valor in ('Seleccione', '', None):
                    self._ventanas.mostrar_mensaje(
                        f'Debe seleccionar una opción para el campo {nombre}.'
                    )
                    return False

            if tipo == 'txt':
                if not valor:
                    self._ventanas.mostrar_mensaje(
                        f'Debe capturar algo en el campo {nombre}.'
                    )
                    return False

                if len(valor.strip()) < 5:
                    self._ventanas.mostrar_mensaje(
                        f'Debe abundar en el texto del campo {nombre}.'
                    )
                    return False

        return True

    def _eliminar_queja_actual(self):
        indice = self._interfaz._obtener_indice_queja_actual()

        if indice is None:
            return

        datos = self._interfaz._quejas.get(indice)

        if not datos:
            return

        if datos.get('editable', 1) == 0:
            self._ventanas.mostrar_mensaje(
                'No tiene permiso para eliminar esta queja.'
            )
            return

        queja_id = datos.get('queja_id')

        if queja_id:
            eliminado = self._modelo.eliminar_queja(queja_id)

            if not eliminado:
                self._ventanas.mostrar_mensaje(
                    'No está autorizado para realizar esta acción.'
                )
                return

        if not self._interfaz.ventanas.mostrar_mensaje_pregunta('¿Esta seguro de realizar esta acción?'):
            return

        self._interfaz._eliminar_queja_actual()

    def _valor(self, componente):
        if componente not in self._ventanas.componentes_forma:
            return None

        return self._interfaz._valor(componente)

    def _cargar_eventos_queja(self, indice):
        cbx_area = f'cbx_area_{indice}'
        cbx_tipo = f'cbx_tipo_{indice}'

        if cbx_area in self._ventanas.componentes_forma:
            self._ventanas.componentes_forma[cbx_area].bind(
                '<<ComboboxSelected>>',
                lambda event, idx=indice: self._rellenar_cbx_sub_area(idx),
                add='+'
            )

        if cbx_tipo in self._ventanas.componentes_forma:
            self._ventanas.componentes_forma[cbx_tipo].bind(
                '<<ComboboxSelected>>',
                lambda event, idx=indice: self._cargar_plantilla_comentario(idx),
                add='+'
            )

    def _cargar_plantilla_comentario(self, indice):
        cbx_tipo = f'cbx_tipo_{indice}'
        txt_comentario = f'txt_comentario_{indice}'

        tipo = self._valor(cbx_tipo)

        if not tipo or tipo == 'Seleccione':
            return

        plantilla = self._obtener_plantilla_comentario(tipo)

        if not plantilla:
            return

        comentario_actual = self._valor(txt_comentario)

        # Si está vacío, carga plantilla.
        if not comentario_actual:
            self._ventanas.insertar_input_componente(
                txt_comentario,
                plantilla
            )
            return

        # Si el comentario actual es una plantilla previa, permite reemplazarla.
        plantillas_existentes = [
            valor.strip()
            for valor in self._obtener_diccionario_plantillas().values()
        ]

        if comentario_actual.strip() in plantillas_existentes:
            widget = self._ventanas.componentes_forma.get(txt_comentario)

            if widget is not None:
                try:
                    widget.delete('1.0', tk.END)
                except Exception:
                    try:
                        widget.delete(0, tk.END)
                    except Exception:
                        pass

            self._ventanas.insertar_input_componente(
                txt_comentario,
                plantilla
            )

    def _obtener_plantilla_comentario(self, tipo):
        return self._obtener_diccionario_plantillas().get(tipo)

    def _obtener_diccionario_plantillas(self):
        return {
            'PASARON MAL EL PEDIDO':
                'EL PEDIDO FUE CAPTURADO DE FORMA INCORRECTA. INDICAR LAS DIFERENCIAS.',

            'NO PASARON EL PEDIDO':
                'EL PEDIDO NO FUE REGISTRADO EN EL SISTEMA. DESCRIBIR LA AFECTACIÓN.',

            'OTRO NOMBRE DE CLIENTE':
                'NO SE CONFIRMÓ EL NOMBRE COMPLETO DEL CLIENTE. INDICAR EL NOMBRE CORRECTO.',

            'PASARON TARDE/CONTESTARON TARDE':
                'LA ATENCIÓN AL CLIENTE FUE REALIZADA FUERA DEL TIEMPO ESPERADO. ESPECIFICAR EL RETRASO.',

            'COBRADO MAL':
                'SE REALIZÓ UN COBRO INCORRECTO. INDICAR EL IMPORTE O CONCEPTO AFECTADO.',

            'TRASPAPELARON DOCUMENTO':
                'EL DOCUMENTO FUE EXTRAVIADO TEMPORALMENTE. DESCRIBIR LO OCURRIDO.',

            'FALTA AMABILIDAD/ MAL SERVICIO':
                'SE RECIBIÓ UN TRATO INADECUADO DURANTE LA ATENCIÓN. DESCRIBIR BREVEMENTE.',

            'NO PASARON A DESCONGELAR':
                'NO SE AVISÓ QUE EL PRODUCTO DEBÍA PASAR A DESCONGELACIÓN.',

            'NO APUNTARON DIRECCION P/LLEVAR':
                'NO SE CONFIRMÓ CORRECTAMENTE LA DIRECCIÓN DE ENTREGA.',

            'NO AVISARON RECADO':
                'EL RECADO DEL CLIENTE NO FUE COMUNICADO AL ÁREA CORRESPONDIENTE.',

            'FALLA SISTEMA':
                'NO SE PUDO COMPLETAR EL PROCESO POR FALLA DEL SISTEMA. DESCRIBIR EL ERROR.',

            'MAL PREPARADO':
                'EL CLIENTE PIDIÓ ____ Y SE LE PREPARÓ ____.',

            'NO ENCONTRABAN EL PEDIDO':
                'EL PEDIDO NO PUDO LOCALIZARSE OPORTUNAMENTE. DESCRIBIR LA SITUACIÓN.',

            'PUSIERON MAL LOS PESOS':
                'SE REGISTRÓ UN PESO INCORRECTO. INDICAR EL PESO CORRECTO.',

            'ENTREGADO MAL/OTRO CLIENTE':
                'EL PEDIDO FUE ENTREGADO INCORRECTAMENTE O A OTRO CLIENTE. DESCRIBIR LA AFECTACIÓN.',

            'FOLIO TRASPAPELADO':
                'EL FOLIO FUE EXTRAVIADO TEMPORALMENTE. DESCRIBIR LO OCURRIDO.',

            'NO SACARON A DESCONGELAR':
                'EL PRODUCTO NO FUE RETIRADO OPORTUNAMENTE PARA DESCONGELACIÓN.',

            'NO HAY EXISTENCIAS':
                'NO HUBO EXISTENCIA SUFICIENTE PARA SURTIR EL PRODUCTO SOLICITADO.',

            'ENTREGARON/TERMINARON TARDE':
                'LA PREPARACIÓN O ENTREGA SE REALIZÓ FUERA DEL HORARIO COMPROMETIDO.',

            'ERROR DE ETIQUETA':
                'SE ETIQUETÓ ____ EN VEZ DE ____.',

            'MAL INFORMADOS':
                'SE DIO INFORMACIÓN INCORRECTA AL CLIENTE. INDICAR EL DATO CORRECTO.',

            'MALA CALIDAD':
                'EL PRODUCTO PRESENTÓ PROBLEMAS DE CALIDAD. DESCRIBIR LA CONDICIÓN.',

            'PREPARADO TARDE':
                'LA PREPARACIÓN DEL PEDIDO CONCLUYÓ DESPUÉS DEL TIEMPO ESPERADO.',

            'PRECIOS EQUIVOCADOS':
                'SE APLICÓ UN PRECIO INCORRECTO. INDICAR EL PRECIO CORRECTO.',

            'CON GUSANOS/CUCARACHAS':
                'SE DETECTÓ PRESENCIA DE PLAGA EN EL PRODUCTO. DESCRIBIR LA EVIDENCIA.',

            'MAL OLOR- HECHADO A PERDER':
                'EL PRODUCTO PRESENTÓ MAL OLOR O SIGNOS DE DESCOMPOSICIÓN. INDICAR EL TIPO DE OLOR.',

            'MAL SERVICIO':
                'SE DETECTÓ UNA DEFICIENCIA EN LA ATENCIÓN AL CLIENTE. DESCRIBIR LO OCURRIDO.',

            'CADUCADO':
                'EL PRODUCTO ENTREGADO SE ENCONTRABA CADUCADO. ESPECIFICAR EL LOTE SI APLICA.',

            'ENTREGADO TARDE':
                'EL PEDIDO FUE ENTREGADO DESPUÉS DEL HORARIO COMPROMETIDO.',

            'ENTREGADO INCOMPLETO':
                'EL PEDIDO FUE ENTREGADO CON PRODUCTOS FALTANTES. ESPECIFICAR CUÁLES.',

            'PEDIDO OTRO CLIENTE':
                'SE PREPARÓ O ENTREGÓ EL PEDIDO CORRESPONDIENTE A OTRO CLIENTE.',

            'NO DEJARON PEDIDO':
                'EL PEDIDO NO FUE ENTREGADO AL CLIENTE. DESCRIBIR EL MOTIVO.',

            'NO LEVANTARON PEDIDO':
                'LA SOLICITUD DEL CLIENTE NO FUE REGISTRADA COMO PEDIDO.',

            'PASARON TARDE EL PEDIDO':
                'EL PEDIDO FUE REGISTRADO CON RETRASO. INDICAR EL IMPACTO.',

            'OTRA DIRECCION':
                'EL PEDIDO FUE ENVIADO A UNA DIRECCIÓN INCORRECTA. INDICAR LA CORRECTA.',

            'NO LLEVARON LA TERMINAL':
                'NO SE LLEVÓ LA TERMINAL DE COBRO AL MOMENTO DE LA ENTREGA.',

            'NO AVISARON CLIENTE':
                'NO SE NOTIFICÓ OPORTUNAMENTE AL CLIENTE. INDICAR QUÉ COMUNICACIÓN FALTÓ.',

            'MAL EMBOLSADO':
                'EL PRODUCTO FUE EMPACADO DE FORMA INCORRECTA. DESCRIBIR EL PROBLEMA.',

            'NO LLEVARON EL PEDIDO':
                'EL PEDIDO NO FUE TRANSPORTADO AL CLIENTE. DESCRIBIR LA CAUSA.',

            'TERMINADOS MAS TARDE DE LA HR COMPROMISO':
                'EL PEDIDO SE CONCLUYÓ DESPUÉS DE LA HORA COMPROMISO.',

            'FOLIO EXTRAVIADO':
                'EL FOLIO FUE EXTRAVIADO. DESCRIBIR LAS ACCIONES REALIZADAS.',

            'CON MOSCAS':
                'SE DETECTÓ PRESENCIA DE MOSCAS EN EL PRODUCTO.',

            'CON CABELLOS':
                'SE DETECTÓ UN CABELLO EN EL PRODUCTO.',

            'ENTREGADO MAL':
                'EL PEDIDO FUE ENTREGADO INCORRECTAMENTE. ESPECIFICAR LA DIFERENCIA.',

            'ERROR EN FORMA DE PAGO':
                'SE REGISTRÓ UNA FORMA DE PAGO INCORRECTA. INDICAR LA CORRECTA.',

            'NO SALDO':
                'EL DOCUMENTO NO FUE SALDADO CORRECTAMENTE. DESCRIBIR LA DIFERENCIA.',

            'VALIDARON MAL':
                'LA VALIDACIÓN REALIZADA FUE INCORRECTA. ESPECIFICAR EL ERROR.',

            'NO TIMBRO FACTURA':
                'NO TERMINÓ SU PROCESO DE TIMBRADO. DESCRIBIR EL MOTIVO.',

            'EXTRAVIO VOUCHER':
                'EL COMPROBANTE DE PAGO FUE EXTRAVIADO. DESCRIBIR LA SITUACIÓN.'
        }

    def _rellenar_cbx_producto(self, indice):
        cbx_producto = f'cbx_producto_{indice}'

        if not hasattr(self, '_productos_por_nombre'):
            self._productos_por_nombre = {
                'DOCUMENTO COMPLETO': 0
            }

        productos = ['DOCUMENTO COMPLETO']

        for reg in sorted(self._productos, key=lambda x: x['Producto']):
            nombre = reg['Producto']

            if nombre not in self._productos_por_nombre:
                self._productos_por_nombre[nombre] = reg['ProductID']

            if nombre not in productos:
                productos.append(nombre)

        self._ventanas.rellenar_cbx(
            cbx_producto,
            productos
        )

    def _obtener_product_id(self, producto):
        if not producto or producto in ('Seleccione', 'DOCUMENTO COMPLETO'):
            return 0

        return self._productos_por_nombre.get(producto, 0)

    def _llamar_instancia_modificaciones(self):
        if self._user_group_id not in self.GRUPOS_ADMIN:
            self._ventanas.mostrar_mensaje(
                'No está autorizado para consultar las modificaciones.'
            )
            return

        from .interfaz_modificaciones import InterfazModificacionesQuejas
        from .controlador_modificaciones import ControladorModificacionesQuejas

        master = self._ventanas.crear_popup_ttkbootstrap()

        interfaz = InterfazModificacionesQuejas(master)
        ControladorModificacionesQuejas(interfaz, self._modelo)

    def _llamar_instancia_historial(self):
        if self._user_group_id not in self.GRUPOS_ADMIN:
            self._ventanas.mostrar_mensaje(
                'No está autorizado para consultar el historial.'
            )
            return

        from .interfaz_historial import InterfazHistorialQuejas
        from .controlador_historial import ControladorHistorialQuejas

        master = self._ventanas.crear_popup_ttkbootstrap()

        interfaz = InterfazHistorialQuejas(master)
        ControladorHistorialQuejas(interfaz, self._modelo)

    def _puede_editar_queja(self, info_queja):
        if self._user_group_id in self.GRUPOS_ADMIN:
            return True

        usuario_queja = info_queja.get('Usuario')
        editable_mismo_dia = info_queja.get('Editable', 0)

        return self._user_id == usuario_queja and editable_mismo_dia == 1

    def _bloquear_formulario_queja(self, indice):
        componentes = [
            f'cbx_tipo_{indice}',
            f'cbx_producto_{indice}',
            f'txt_comentario_{indice}',
            f'cbx_responsable_{indice}',
            f'cbx_area_{indice}',
            f'cbx_sub_area_{indice}',
            f'txt_seguimiento_{indice}',
            f'tbx_capturo_{indice}',
            f'chk_salio_{indice}',
        ]

        for componente in componentes:
            if componente in self._ventanas.componentes_forma:
                self._ventanas.bloquear_componente(componente)
