from cayal.ventanas import Ventanas
from capturar_documento.herramientas.enviar_correos.modelo_enviar_correo import (
    ModeloEnviarCorreo,
)


class ControladorEnviarCorreo:

    def __init__(self, master, parametros, funcionamiento_prueba=None):
        self._master = master
        self._modelo = ModeloEnviarCorreo(parametros, funcionamiento_prueba)
        self._ventanas = Ventanas(self._master)

        self._documentos_pendientes_envio = []
        self._complementos_pendientes_envio = []

        self._correos_documentos_pendientes_envio = {}
        self._correos_complementos_pendientes_envio = {}

        self._adjuntos_documentos_pendientes_envio = {}
        self._adjuntos_complementos_pendientes_envio = {}

        self._incidencias_documentos = {}
        self._incidencias_complementos = {}
        self._incidencias = []

        self._cliente_actual = ''
        self._estado_actual = ''
        self._debug_estados = True

        if not self._modelo.setear_parametros_correo(correo_id=7):
            self._master.destroy()
            return

        self._inicializar_aplicacion()

    def _inicializar_aplicacion(self):

        print(
            self._modelo.items_seleccionados,
            self._modelo.module_id
        )

        numero_pendientes = self._determinar_numero_pendientes_envio()
        print(numero_pendientes)
        if numero_pendientes == 0:
            self._master.destroy()
            return

        self._ventanas.crear_progressbar(
            nombre='pgb_barra',
            bootstyle='info',
            valor_maximo=numero_pendientes
        )

        self._ventanas.componentes_forma['lbl_barra'].config(
            text=f"Procesados 0 de {numero_pendientes} (0%)"
        )

        self._ventanas.configurar_ventana_ttkbootstrap('Enviar correos')

        self._ventanas.procesar_con_barra(
            nombre_barra='pgb_barra',
            total_elementos=numero_pendientes,
            funcion_procesamiento=self._enviar_correos_al_cliente,
            fin_callback=self._cerrar_ventana
        )

    def _determinar_numero_pendientes_envio(self):
        module_id = int(getattr(self._modelo, 'module_id', 0) or 0)

        self._documentos_pendientes_envio = []
        self._complementos_pendientes_envio = []

        if module_id in (21, 1400, 1319):
            self._documentos_pendientes_envio = self._modelo.buscar_pendientes_envio_documentos()
        else:
            self._complementos_pendientes_envio = self._modelo.buscar_pendientes_envio_complementos()
            self._documentos_pendientes_envio = self._modelo.buscar_pendientes_envio_documentos()

        print('DOCUMENTOS PENDIENTES:', self._documentos_pendientes_envio)
        print('COMPLEMENTOS PENDIENTES:', self._complementos_pendientes_envio)

        return (
                len(self._documentos_pendientes_envio)
                + len(self._complementos_pendientes_envio)
        )

    def _enviar_correos_al_cliente(self, indice, continuar):
        print('INDICE RECIBIDO:', indice)

        pendiente = self._resolver_pendiente_por_indice(indice)

        print('PENDIENTE RESUELTO:', pendiente)

        if not pendiente:
            self._registrar_incidencia_general(
                f"No se pudo resolver el pendiente del índice {indice}"
            )
            self._actualizar_progreso(indice)
            self._master.after(50, continuar)
            return

        resultado = self._procesar_pendiente(pendiente)

        print('RESULTADO PROCESAMIENTO:', resultado)
        print('INCIDENCIAS DOCUMENTOS:', self._incidencias_documentos)
        print('INCIDENCIAS GENERALES:', self._incidencias)

        self._actualizar_progreso(indice)
        self._master.after(50, continuar)

    def _resolver_pendiente_por_indice(self, indice):
        total = (
                len(self._documentos_pendientes_envio)
                + len(self._complementos_pendientes_envio)
        )

        if indice >= total and indice - 1 >= 0:
            indice = indice - 1

        total_docs = len(self._documentos_pendientes_envio)

        if indice < total_docs:
            return {
                'elemento': self._documentos_pendientes_envio[indice],
                'es_complemento': False
            }

        indice_complemento = indice - total_docs

        if indice_complemento < len(self._complementos_pendientes_envio):
            return {
                'elemento': self._complementos_pendientes_envio[indice_complemento],
                'es_complemento': True
            }

        return None

    def _cerrar_ventana(self):
        incidencias = []
        incidencias.extend(self._incidencias)
        incidencias.extend(
            '{}: {}'.format(referencia, mensaje)
            for referencia, mensaje in self._incidencias_documentos.items()
        )
        incidencias.extend(
            '{}: {}'.format(referencia, mensaje)
            for referencia, mensaje in self._incidencias_complementos.items()
        )
        if incidencias:
            self._ventanas.mostrar_mensaje(
                'El envío terminó con incidencias:\n\n{}'.format(
                    '\n'.join(incidencias)
                ),
                tipo='error',
            )
        self._master.destroy()

    def _enviar_incidencias(self):
        if not self._incidencias:
            return

        incidencias_texto = "\n".join(self._incidencias)

        self._modelo.correo.archivo_adjunto = []
        self._modelo.correo.asunto = 'Envío de incidencias de correos'
        self._modelo.correo.destinatario = 'sistemas@carnescayal.com'
        self._modelo.correo.cuerpo = incidencias_texto

        self._modelo.enviar_correo()

    # =========================================================
    # PROCESAMIENTO
    # =========================================================

    def _procesar_pendiente(self, pendiente):
        elemento = pendiente.get('elemento')
        es_complemento = pendiente.get('es_complemento', False)

        valores = self._validar_documento_a_enviar(
            elemento,
            es_complemento
        )

        if not valores:
            razon = self._obtener_razon_incidencia(
                elemento,
                es_complemento
            )

            tipo = 'complemento' if es_complemento else 'documento'

            self._registrar_incidencia_general(
                f'{tipo} {elemento}, razón: {razon}'
            )

            return False

        envio_correcto = self._enviar_correo(valores)

        if envio_correcto:
            return True

        referencia = (
                valores.get('financial_operation_id')
                or valores.get('document_id')
                or elemento
        )

        tipo = 'complemento' if es_complemento else 'documento'

        self._registrar_incidencia_general(
            f'Error enviando {tipo} {referencia}'
        )

        return False

    # =========================================================
    # VALIDACIÓN
    # =========================================================

    def _validar_documento_a_enviar(self, documento_o_complemento, es_complemento=False):
        contexto = self._resolver_contexto_documento(
            documento_o_complemento,
            es_complemento
        )

        if not contexto:
            return False

        valores = contexto['valores_documento']
        financial_operation_id = contexto['financial_operation_id']

        if not self._validar_estado_documento(valores, financial_operation_id):
            return False

        if not self._validar_correos_electronicos_documento(valores, financial_operation_id):
            referencia = (
                financial_operation_id
                if financial_operation_id != 0
                else valores.get('document_id', 0)
            )

            self._registrar_incidencia_detallada(
                referencia,
                'Correos inválidos',
                es_complemento
            )

            return False

        if not self._validar_adjuntos(valores, financial_operation_id):
            return False

        valores['financial_operation_id'] = financial_operation_id

        return valores

    def _resolver_contexto_documento(self, documento_o_complemento, es_complemento):
        financial_operation_id = 0
        documento = documento_o_complemento

        if es_complemento:
            financial_operation_id = documento_o_complemento

            validacion_complemento = self._modelo.validar_complemento(
                financial_operation_id
            )

            if not validacion_complemento:
                self._registrar_incidencia_detallada(
                    financial_operation_id,
                    'Sin datos',
                    True
                )
                return False

            if validacion_complemento.get('cancelled') == 1:
                self._registrar_incidencia_detallada(
                    financial_operation_id,
                    'Cancelado',
                    True
                )
                return False

            if validacion_complemento.get('deleted') == 1:
                self._registrar_incidencia_detallada(
                    financial_operation_id,
                    'Borrado',
                    True
                )
                return False

            if validacion_complemento.get('status_cfdi') != 3:
                self._registrar_incidencia_detallada(
                    financial_operation_id,
                    'No timbrado',
                    True
                )
                return False

            documento = self._modelo.obtener_documento_por_complemento(
                financial_operation_id
            )

        valores_documento = self._modelo.validar_documento(documento)

        if not valores_documento:
            self._registrar_incidencia_detallada(
                documento,
                'Sin datos',
                es_complemento
            )
            return False

        return {
            'financial_operation_id': financial_operation_id,
            'documento': documento,
            'valores_documento': valores_documento
        }

    def _validar_estado_documento(self, valores_documento, financial_operation_id):
        documento = valores_documento.get('document_id', 0)
        es_complemento = financial_operation_id != 0
        referencia = financial_operation_id if es_complemento else documento

        if valores_documento.get('cancelled') == 1:
            self._registrar_incidencia_detallada(
                referencia,
                'Cancelado',
                es_complemento
            )
            return False

        if valores_documento.get('deleted') == 1:
            self._registrar_incidencia_detallada(
                referencia,
                'Borrado',
                es_complemento
            )
            return False

        if valores_documento.get('status_cfdi') != 3:
            self._registrar_incidencia_detallada(
                referencia,
                'No timbrado',
                es_complemento
            )
            return False

        return True

    def _validar_correos_electronicos_documento(self, valores_documento, financial_operation_id):
        document_id = valores_documento.get('document_id', 0)
        depot_id = valores_documento.get('business_entity_depot_id', 0)
        business_entity_id = valores_documento.get('business_entity_id', 0)

        row = self._modelo.obtener_correos_cliente(
            business_entity_id,
            depot_id
        )

        if not row:
            return False

        if isinstance(row, dict):
            emails_str = row.get('Correos') or row.get('BusinessEntityEmail') or ''
        else:
            emails_str = row or ''

        emails_str = str(emails_str).strip()

        if not emails_str:
            return False

        emails_limpios = self._modelo.utilerias.normalizar_cadena_correos(
            emails_str
        )

        if not emails_limpios:
            return False

        if financial_operation_id == 0:
            self._correos_documentos_pendientes_envio[document_id] = emails_limpios
        else:
            self._correos_complementos_pendientes_envio[financial_operation_id] = emails_limpios

        return True

    def _validar_adjuntos(self, valores_documento, financial_operation_id):
        documento = valores_documento['document_id']
        es_complemento = financial_operation_id != 0
        referencia = financial_operation_id if es_complemento else documento

        self._set_estado(f'Validando adjuntos de {referencia}...')

        rfc_timbrado = self._modelo.obtener_rfc_timbrado(documento)
        rfc_timbrado = (rfc_timbrado or '').strip()

        if not rfc_timbrado:
            self._registrar_incidencia_detallada(
                referencia,
                'Sin RFC timbrado',
                es_complemento
            )
            return False

        if es_complemento:
            self._set_estado(f'Buscando XML/PDF de complemento {financial_operation_id}...')

            nombre_archivo_xml = self._modelo.crear_nombre_archivo_complemento(
                'xml',
                financial_operation_id,
                rfc_timbrado
            )

            nombre_archivo_pdf = self._modelo.crear_nombre_archivo_complemento(
                'pdf',
                financial_operation_id,
                rfc_timbrado
            )

        else:
            doc_folio = valores_documento['doc_folio']

            nombre_archivo_xml = self._modelo.crear_nombre_archivo_factura(
                'xml',
                rfc_timbrado,
                doc_folio
            )

            nombre_archivo_pdf = self._modelo.crear_nombre_archivo_factura(
                'pdf',
                rfc_timbrado,
                doc_folio
            )

            self._set_estado(f'Generando PDF documento {documento} / {doc_folio}...')

            pdf_generado = self._modelo.crear_pdf_documento(
                nombre_archivo_pdf,
                documento,
                valores_documento
            )

            if pdf_generado is False:
                detalle_error = self._modelo.ultimo_error_pdf
                mensaje = 'No fue posible generar PDF'
                if detalle_error:
                    mensaje = '{}: {}'.format(mensaje, detalle_error)
                self._registrar_incidencia_detallada(
                    referencia,
                    mensaje,
                    es_complemento
                )
                return False

        self._set_estado(f'Comprobando archivos de {referencia}...')

        path_archivo_xml = self._modelo.comprobar_path_archivo(nombre_archivo_xml)
        path_archivo_pdf = self._modelo.comprobar_path_archivo(nombre_archivo_pdf)

        if not path_archivo_xml:
            self._registrar_incidencia_detallada(
                referencia,
                f'Sin XML: {nombre_archivo_xml}',
                es_complemento
            )
            return False

        if not path_archivo_pdf:
            self._registrar_incidencia_detallada(
                referencia,
                f'Sin PDF: {nombre_archivo_pdf}',
                es_complemento
            )
            return False

        if es_complemento:
            self._adjuntos_complementos_pendientes_envio[financial_operation_id] = (
                path_archivo_pdf,
                path_archivo_xml
            )
        else:
            self._adjuntos_documentos_pendientes_envio[documento] = (
                path_archivo_pdf,
                path_archivo_xml
            )

        self._set_estado(f'Adjuntos listos para {referencia}.')

        return True

    # =========================================================
    # ENVÍO
    # =========================================================

    def _enviar_correo(self, valores_documento):
        try:
            self._set_estado('Armando datos del correo...')

            datos_correo = self._armar_datos_correo(valores_documento)

            if not datos_correo:
                return False

            self._cliente_actual = datos_correo['official_name']

            self._modelo.correo.archivo_adjunto = datos_correo['archivos_adjuntos']
            self._modelo.correo.asunto = datos_correo['asunto']
            self._modelo.correo.destinatario = datos_correo['correos']
            self._modelo.correo.cuerpo = datos_correo['cuerpo']

            self._set_estado(
                f"Enviando correo a {datos_correo['official_name']}..."
            )

            resultado = self._modelo.enviar_correo()
            envio_correo = resultado[0]

            if not envio_correo:
                referencia = datos_correo['referencia']
                mensaje = resultado[1]

                self._registrar_incidencia_detallada(
                    referencia,
                    mensaje,
                    datos_correo['es_complemento']
                )

                return False

            self._set_estado('Actualizando bitácora de envío...')

            self._modelo.actualizar_bitacora_correos_enviados(
                documento=datos_correo['referencia'],
                tipo_de_envio=datos_correo['tipo_de_envio'],
                correos=datos_correo['correos'],
                doc_folio=datos_correo['doc_folio'],
                official_name=datos_correo['official_name']
            )

            return True

        except Exception as ex:
            referencia = (
                    valores_documento.get('financial_operation_id')
                    or valores_documento.get('document_id', 0)
            )

            es_complemento = valores_documento.get('financial_operation_id', 0) != 0

            self._registrar_incidencia_detallada(
                referencia,
                f'Excepción enviando correo: {ex}',
                es_complemento
            )

            return False

    def _actualizar_progreso(self, indice):
        total = (
                len(self._documentos_pendientes_envio)
                + len(self._complementos_pendientes_envio)
        )

        if total <= 0:
            return

        barra = self._ventanas.componentes_forma['pgb_barra']
        lbl = self._ventanas.componentes_forma['lbl_barra']

        procesados = indice + 1
        pct = int((procesados / total) * 100)

        barra['value'] = procesados
        barra.configure(mask=f'Completado... {pct}%')

        lbl.config(
            text=(
                f'Procesados {procesados} de {total} '
                f'({pct}%) — Cliente: {self._cliente_actual}'
            )
        )


    def _armar_datos_correo(self, valores_documento):
        business_entity_id = valores_documento.get('business_entity_id', 0)
        zone_id = valores_documento.get('zone_id', 0)
        financial_operation_id = valores_documento.get('financial_operation_id', 0)
        business_entity_depot_id = valores_documento.get('business_entity_depot_id', 0)
        doc_folio = valores_documento.get('doc_folio', '')
        document_id = valores_documento.get('document_id', 0)

        depot_name = self._modelo.obtener_nombre_depot(
            business_entity_depot_id
        )

        official_name = self._modelo.obtener_nombre_cliente(
            business_entity_id
        )

        es_complemento = financial_operation_id != 0

        if not es_complemento:
            archivos_adjuntos = list(
                self._adjuntos_documentos_pendientes_envio[document_id]
            )

            correos = self._correos_documentos_pendientes_envio[document_id]

            asunto = f'Facturas Carnes Cayal {doc_folio} {official_name} {depot_name}'

            cuerpo = (
                'Estimado cliente:\n\n'
                'Por este medio le hacemos llegar la factura de su compra.\n\n'
                'Saludos cordiales.'
            )

            if int(zone_id) == 1040:
                try:
                    estado_cuenta = self._modelo.status_credito(business_entity_id)
                except Exception:
                    estado_cuenta = ''

                if estado_cuenta:
                    cuerpo += '\n\n' + estado_cuenta

            return {
                'es_complemento': False,
                'referencia': document_id,
                'tipo_de_envio': 'Factura',
                'archivos_adjuntos': archivos_adjuntos,
                'correos': correos,
                'asunto': asunto,
                'cuerpo': cuerpo,
                'official_name': official_name,
                'doc_folio': doc_folio
            }

        archivos_adjuntos = list(
            self._adjuntos_complementos_pendientes_envio[financial_operation_id]
        )

        correos = self._correos_complementos_pendientes_envio[financial_operation_id]

        asunto = (
            f'Carnes Cayal Cobro ID{financial_operation_id} '
            f'{doc_folio} {official_name} {depot_name}'
        )

        return {
            'es_complemento': True,
            'referencia': financial_operation_id,
            'tipo_de_envio': 'Complemento',
            'archivos_adjuntos': archivos_adjuntos,
            'correos': correos,
            'asunto': asunto,
            'cuerpo': '',
            'official_name': official_name,
            'doc_folio': doc_folio
        }

    # =========================================================
    # INCIDENCIAS
    # =========================================================

    def _registrar_incidencia_detallada(self, referencia, mensaje, es_complemento=False):
        if es_complemento:
            self._incidencias_complementos[referencia] = mensaje
            return

        self._incidencias_documentos[referencia] = mensaje

    def _registrar_incidencia_general(self, mensaje):
        self._incidencias.append(mensaje)

    def _obtener_razon_incidencia(self, referencia, es_complemento=False):
        if es_complemento:
            return self._incidencias_complementos.get(
                referencia,
                'desconocida'
            )

        return self._incidencias_documentos.get(
            referencia,
            'desconocida'
        )

    def _set_estado(self, mensaje):
        self._estado_actual = mensaje

        if getattr(self, '_debug_estados', False):
            print(mensaje)

        lbl = self._ventanas.componentes_forma.get('lbl_barra')

        if lbl:
            lbl.config(text=mensaje)
            self._master.update_idletasks()
