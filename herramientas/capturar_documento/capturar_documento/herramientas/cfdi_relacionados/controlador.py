
class ControladorRelacionarFactura:
    def __init__(self, interfaz, modelo):
        self._interfaz = interfaz
        self._modelo = modelo
        self._info_documento = self._modelo.obtener_info_documento(self._modelo.document_id)[0]

        self._documentos_seleccionados = {}
        self._info_tipos_relaciones_fiscales = []
        self._rellenar_componentes()
        self._cargar_eventos()


    def _rellenar_componentes(self):

        self._interfaz.ventanas.insertar_input_componente(
            'tbx_cliente',
            self._info_documento.get('OfficialName','')
        )
        self._interfaz.ventanas.insertar_input_componente(
            'tbx_folio',
            self._info_documento.get('DocFolio','')
        )

        self._interfaz.ventanas.insertar_input_componente(
            'tbx_status',
            self._obtener_status()
        )

        self._interfaz.ventanas.bloquear_componente('tbx_cliente')
        self._interfaz.ventanas.bloquear_componente('tbx_folio')
        self._interfaz.ventanas.bloquear_componente('tbx_status')

        consulta_tipos = self._modelo.obtener_tipos_relacion_fiscal()
        if not consulta_tipos:
            return

        self._info_tipos_relaciones_fiscales = consulta_tipos
        tipos = [reg['Value'] for reg in self._info_tipos_relaciones_fiscales]
        self._interfaz.ventanas.rellenar_cbx('cbx_tipo_relacion', tipos, sin_seleccione=True)
        consulta = []

        if not self._es_relacionable():
            return

        # si espera relacion
        if self._info_documento.get('CFDStatusID',0) == 0:
            consulta = self._modelo.obtener_documentos_relacionables(self._modelo.document_id)

        # si esta cancelado y relacionado
        elif self._info_documento.get('CancelledOn',None):
            consulta = self._modelo.obtener_documentos_relacionados_cancelados(self._modelo.document_id)
            self._bloquear_acciones()

        # si no esta cancelado y esta relacionado
        else:
            consulta = self._modelo.obtener_documentos_relacionados(self._modelo.document_id)
            self._bloquear_acciones()

        if not consulta:
            return

        self._interfaz.ventanas.rellenar_treeview('tvw_facturas', self._interfaz.columnas(), consulta, 10)

    def _cargar_eventos(self):
        eventos = {
            'btn_cancelar':self._interfaz.master.destroy,
            'btn_seleccionar':self._seleccionar_documentos,
            'btn_guardar':self._guardar_relacion
        }
        self._interfaz.ventanas.cargar_eventos(eventos)

    def _bloquear_acciones(self):
        self._interfaz.ventanas.bloquear_componente('btn_guardar')
        self._interfaz.ventanas.bloquear_componente('btn_seleccionar')

    def _es_relacionable(self):
        if self._info_documento.get('TipoCFD', True) and self._info_documento.get('CFDStatusID', 0) == 0:
            self._interfaz.ventanas.mostrar_mensaje('No está permitido relacionar remisiones a otros doctos.')
            self._bloquear_acciones()
            return

        return True

    def _obtener_status(self):
        status_cfdi = self._info_documento.get('CFDStatusID', 0)
        status = ''
        if status_cfdi == 3:
            status = 'Timbrado'
            if self._info_documento.get('CancelledOn', None):
                status = 'Cancelado'
        if status_cfdi == 0:
            status = 'No enviado'
        return status

    def _decolorar_documentos(self):
        filas = self._interfaz.ventanas.obtener_filas_treeview('tvw_facturas')
        for fila in filas:
            self._interfaz.ventanas.colorear_fila_seleccionada_treeview('tvw_facturas', fila)

    def _seleccionar_documentos(self):
        filas = self._interfaz.ventanas.obtener_seleccion_filas_treeview('tvw_facturas')
        if not filas:
            return

        self._decolorar_documentos()
        self._documentos_seleccionados = {}
        for fila in filas:
            valores_fila = self._interfaz.ventanas.procesar_fila_treeview(
                'tvw_facturas',
                fila
            )
            document_id = valores_fila.get('DocumentID', 0)

            if document_id not in self._documentos_seleccionados:
                self._documentos_seleccionados[document_id] = valores_fila
                self._interfaz.ventanas.colorear_fila_seleccionada_treeview('tvw_facturas', fila, 'warning')

    def _guardar_relacion(self):
        if not self._documentos_seleccionados:
            self._interfaz.ventanas.mostrar_mensaje(
                'Debe seleccionar al menos un documento para relacionar.'
            )
            return

        cfd_folios_fiscales = self._procesar_cadenas()

        mensaje = (
            f'Se relacionarán {len(cfd_folios_fiscales)} documento(s).\n\n'
            'Folios fiscales:\n'
            f'{"\n".join(cfd_folios_fiscales)}\n\n'
            '¿Está seguro(a) de que desea continuar?'
        )

        if not self._interfaz.ventanas.mostrar_mensaje_pregunta(mensaje):
            return

        # Guardar la relación aquí
        cadenas_relacionadas = ', '.join(self._procesar_cadenas())
        documentos = [document_id for document_id, valores_fila in self._documentos_seleccionados.items()]
        clave_relacion = self._obtener_clave_relacion()
        self._modelo.guardar_relacion(cadenas_relacionadas, documentos,clave_relacion)

        self._interfaz.ventanas.mostrar_mensaje(
            'La relación de documentos se guardó correctamente.',tipo='info'
        )
        self._interfaz.master.destroy()

    def _procesar_cadenas(self):
        folios_fiscales = []

        for valores_fila in self._documentos_seleccionados.values():
            folio_fiscal = valores_fila.get('UUID', '').strip()

            if folio_fiscal:
                folios_fiscales.append(folio_fiscal)

        return folios_fiscales

    def _obtener_clave_relacion(self):
        seleccion = self._interfaz.ventanas.obtener_input_componente('cbx_tipo_relacion')
        resultado = [reg['Clave'] for reg in self._info_tipos_relaciones_fiscales if reg['Value'] ==  seleccion]
        if resultado:
            return resultado[0]

        return

