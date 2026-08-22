import tkinter as tk

from cayal.cliente import Cliente
from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.documento import Documento
from cayal.util import Utilerias
from cayal.ventanas import Ventanas

from capturar_documento.controlador_captura import ControladorCaptura
from capturar_documento.interfaz_captura import InterfazCaptura
from capturar_documento.modelo_captura import ModeloCaptura


class BuscarGeneralesProveedor:
    """Busca un proveedor, permite seleccionarlo y abre la captura.

    La clase conserva las consultas de generales utilizadas por la búsqueda de
    clientes. La dirección fiscal se asigna internamente al documento, pero no
    se presenta ni se permite seleccionar direcciones desde esta ventana.
    """

    MINIMO_CARACTERES = 5
    MODULOS_FISCALES = 0
    PREFIJOS_DOCUMENTO = {
        152:'FC'
    }

    def __init__(
            self,
            master,
            parametros,
            cliente=None,
            documento=None,
            al_seleccionar=None,
    ):
        self._master = master
        self._parametros_contpaqi = parametros
        self._cliente_existente = cliente
        self._documento_existente = documento
        self._al_seleccionar = al_seleccionar

        self._declarar_variables_globales()
        self._crear_instancias_de_clases()
        self._crear_frames()
        self._cargar_componentes_forma()
        self._cargar_eventos_componentes_forma()
        self._cargar_hotkeys()
        self._ajustar_componentes()

        self._ventanas.configurar_ventana_ttkbootstrap('Seleccionar proveedor')
        self._ventanas.enfocar_componente('tbx_buscar_proveedor')

    def enfocar_busqueda(self):
        """Devuelve el foco al campo principal del selector."""
        self._ventanas.enfocar_componente('tbx_buscar_proveedor')

    def _declarar_variables_globales(self):
        self._termino_buscado = None
        self._consulta_proveedores = []
        self._info_proveedor_seleccionado = []
        self._instancia_llamada = False

        self._module_id = self._parametros_contpaqi.id_modulo
        self._user_id = self._parametros_contpaqi.id_usuario
        self._document_id = self._parametros_contpaqi.id_principal
        self._modelo_captura = None

    def _crear_instancias_de_clases(self):
        self._base_de_datos = ComandosBaseDatos()
        # ModeloCaptura trabaja con la entidad Cliente. Se conserva esta clase
        # para no romper su contrato al utilizar generales de un proveedor.
        self._cliente = self._cliente_existente or Cliente()
        self._documento = self._documento_existente or Documento()
        self._utilerias = Utilerias()
        self._ventanas = Ventanas(self._master)

    def _crear_frames(self):
        frames = {
            'frame_principal_proveedor': (
                'master',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW},
            ),
            'frame_buscar_proveedor': (
                'frame_principal_proveedor',
                'Buscar proveedor:',
                {
                    'row': 0,
                    'column': 0,
                    'columnspan': 4,
                    'padx': 5,
                    'pady': 5,
                    'sticky': tk.NSEW,
                },
            ),
            'frame_resultados_proveedor': (
                'frame_principal_proveedor',
                'Resultados:',
                {
                    'row': 1,
                    'column': 0,
                    'columnspan': 4,
                    'padx': 5,
                    'pady': 5,
                    'sticky': tk.NSEW,
                },
            ),
            'frame_botones_proveedor': (
                'frame_principal_proveedor',
                None,
                {
                    'row': 2,
                    'column': 0,
                    'columnspan': 4,
                    'padx': 5,
                    'pady': 5,
                    'sticky': tk.E,
                },
            ),
        }
        self._ventanas.crear_frames(frames)

    def _cargar_componentes_forma(self):
        componentes = {
            'tbx_buscar_proveedor': (
                'frame_buscar_proveedor',
                None,
                'Buscar:',
                '[Enter]',
            ),
            'tvw_proveedores': (
                'frame_resultados_proveedor',
                self.crear_columnas_tabla_proveedores(),
                12,
                None,
            ),
            'btn_seleccionar_proveedor': (
                'frame_botones_proveedor',
                'primary',
                'Seleccionar',
                '[F1]',
            ),
            'btn_cancelar_proveedor': (
                'frame_botones_proveedor',
                'danger',
                'Cancelar',
                '[Esc]',
            ),
        }
        self._ventanas.crear_componentes(componentes)

    def crear_columnas_tabla_proveedores(self):
        return [
            {
                'text': 'BusinessEntityID',
                'stretch': False,
                'width': 0,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 1,
            },
            {
                'text': 'Proveedor',
                'stretch': True,
                'width': 520,
                'column_anchor': tk.W,
                'heading_anchor': tk.W,
                'hide': 0,
            },
        ]

    def _cargar_eventos_componentes_forma(self):
        eventos = {
            'tbx_buscar_proveedor': self._buscar_termino,
            'btn_seleccionar_proveedor': self._seleccionar_proveedor,
            'btn_cancelar_proveedor': self._master.destroy,
            'tvw_proveedores': (
                lambda event: self._seleccionar_proveedor(),
                'doble_click',
            ),
        }
        self._ventanas.cargar_eventos(eventos)

    def _cargar_hotkeys(self):
        hotkeys = {
            'F1': self._seleccionar_proveedor,
            'Esc': self._master.destroy,
        }
        self._ventanas.agregar_hotkeys_forma(hotkeys)

    def _ajustar_componentes(self):
        self._ventanas.ajustar_ancho_componente('tbx_buscar_proveedor', 50)
        self._ventanas.ajustar_componente_en_frame(
            'tvw_proveedores',
            'frame_resultados_proveedor',
        )
        self._ventanas.bloquear_componente('btn_seleccionar_proveedor')

    def _validar_termino(self):
        termino = self._ventanas.obtener_input_componente('tbx_buscar_proveedor')
        termino = termino.strip() if termino else ''

        if not termino:
            self._ventanas.mostrar_mensaje('Debe introducir un término a buscar.')
            return None

        if len(termino) < self.MINIMO_CARACTERES:
            self._ventanas.mostrar_mensaje(
                'Insuficientes letras en el término a buscar.'
            )
            return None

        return termino.upper()

    def _buscar_termino(self, event=None):
        termino = self._validar_termino()
        if not termino:
            self._limpiar_resultados()
            return

        self._termino_buscado = termino
        self._consulta_proveedores = self._buscar_proveedores_por_nombre_similar(termino)
        self._rellenar_tabla_proveedores()

    def _buscar_proveedores_por_nombre_similar(self, termino_buscado):
        """Conserva la consulta por palabras utilizada en la clase original."""
        palabras = termino_buscado.split()
        condiciones = ' AND '.join(
            "E.OfficialName LIKE '%' + ? + '%'" for _ in palabras
        )
        query = f'''
            SELECT E.BusinessEntityID, E.OfficialName
            FROM orgSupplier C
            INNER JOIN orgBusinessEntity E
                ON C.BusinessEntityID = E.BusinessEntityID
            WHERE {condiciones}
              AND C.DeletedOn IS NULL
              AND E.DeletedOn IS NULL
              AND E.BusinessEntityID NOT IN (1, 8179, 9277)
        '''

        if self._module_id == 1692:
            query = f'{query} AND C.ZoneID = 1040'

        return self._base_de_datos.fetchall(query, palabras)

    def _rellenar_tabla_proveedores(self):
        registros = [
            {
                'BusinessEntityID': proveedor['BusinessEntityID'],
                'Proveedor': proveedor['OfficialName'],
            }
            for proveedor in (self._consulta_proveedores or [])
        ]
        tabla = self._ventanas.componentes_forma['tvw_proveedores']
        self._ventanas.rellenar_treeview(
            tabla,
            self.crear_columnas_tabla_proveedores(),
            registros,
        )

        if not registros:
            self._ventanas.bloquear_componente('btn_seleccionar_proveedor')
            self._ventanas.mostrar_mensaje('No se encontraron resultados.')
            self._ventanas.enfocar_componente('tbx_buscar_proveedor')
            return

        self._ventanas.desbloquear_componente('btn_seleccionar_proveedor')
        if len(registros) == 1:
            self._ventanas.seleccionar_fila_treeview('tvw_proveedores', 1)
        self._ventanas.enfocar_componente('tvw_proveedores')

    def _limpiar_resultados(self):
        self._consulta_proveedores = []
        self._ventanas.limpiar_componentes('tvw_proveedores')
        self._ventanas.bloquear_componente('btn_seleccionar_proveedor')

    def _obtener_proveedor_seleccionado(self):
        filas = self._ventanas.obtener_seleccion_filas_treeview('tvw_proveedores')
        if not filas:
            self._ventanas.mostrar_mensaje('Debe seleccionar un proveedor de la tabla.')
            return None

        if not self._ventanas.validar_seleccion_una_fila_treeview('tvw_proveedores'):
            self._ventanas.mostrar_mensaje('Debe seleccionar solamente un proveedor.')
            return None

        return self._ventanas.procesar_fila_treeview('tvw_proveedores', filas)

    def _buscar_info_proveedor_seleccionado(self, business_entity_id):
        self._info_proveedor_seleccionado = self._base_de_datos.fetchall(
            'SELECT * FROM [dbo].[zvwBuscarInfoCliente-BusinessEntityID](?)',
            (business_entity_id,),
        )
        return self._info_proveedor_seleccionado

    def _seleccionar_proveedor(self):
        proveedor = self._obtener_proveedor_seleccionado()
        if not proveedor:
            return

        business_entity_id = proveedor['BusinessEntityID']
        consulta = self._buscar_info_proveedor_seleccionado(business_entity_id)

        if not consulta:
            consulta = self._buscar_info_proveedor_seleccionado(8179) # busca la info de publico en general
            if consulta:
                consulta[0]['BusinessEntityID'] = proveedor['BusinessEntityID']
                consulta[0]['OfficialName'] = proveedor['Proveedor']

        if not consulta:
            self._ventanas.mostrar_mensaje(
                'No se encontró la información general del proveedor.'
            )
            return

        self._cliente.consulta = consulta
        self._cliente.settear_valores_consulta()
        self._asignar_parametros_a_documento()

        if self._al_seleccionar is not None:
            self._al_seleccionar(self._cliente, self._documento)
            self._master.destroy()
            return

        self._llamar_instancia()

    def _asignar_parametros_a_documento(self):
        """Asigna la dirección fiscal sin mostrarla ni pedir selección."""
        direccion = {
            'address_detail_id': self._cliente.address_fiscal_detail_id,
            'address_name': 'Dirección Fiscal',
            'depot_id': 0,
            'depot_name': '',
            'telefono': self._cliente.phone,
            'celular': self._cliente.cellphone,
            'calle': self._cliente.address_fiscal_street,
            'numero': self._cliente.address_fiscal_ext_number,
            'comentario': self._cliente.address_fiscal_comments,
            'cp': self._cliente.address_fiscal_zip_code,
            'colonia': self._cliente.address_fiscal_city,
            'estado': self._cliente.address_fiscal_state_province,
            'municipio': self._cliente.address_fiscal_municipality,
        }
        self._documento.address_details = direccion
        self._documento.address_detail_id = direccion['address_detail_id']
        self._documento.address_name = direccion['address_name']
        self._documento.depot_id = 0
        self._documento.depot_name = ''
        self._documento.business_entity_id = self._cliente.business_entity_id
        self._documento.customer_type_id = self._cliente.cayal_customer_type_id

    def _documento_seleccionado(self):
        self._documento.prefix = self.PREFIJOS_DOCUMENTO.get(self._module_id, 'CAYAL')

        if self._cliente.cayal_customer_type_id == 2:
            self._documento.cfd_type_id = 0
            self._documento.doc_type = 'FACTURA'
            self._documento.forma_pago = self._cliente.forma_pago
            self._documento.metodo_pago = self._cliente.metodo_pago
            self._documento.receptor_uso_cfdi = self._cliente.receptor_uso_cfdi
        else:
            self._documento.cfd_type_id = 1
            self._documento.doc_type = 'REMISIÓN'
            self._documento.forma_pago = '01'
            self._documento.metodo_pago = 'PUE'
            self._documento.receptor_uso_cfdi = 'S01'
        return True

    def _llamar_instancia(self):
        if self._instancia_llamada or not self._documento_seleccionado():
            return

        try:
            self._instancia_llamada = True
            if self._document_id == -1:
                self._parametros_contpaqi.nombre_usuario = (
                    self._base_de_datos.buscar_nombre_de_usuario(self._user_id)
                )

            interfaz = InterfazCaptura(self._master, self._module_id, solicitar_guardado=True)
            modelo = ModeloCaptura(
                self._base_de_datos,
                self._utilerias,
                self._cliente,
                self._documento,
                self._parametros_contpaqi,
                ofertas=None,
            )
            self._modelo_captura = modelo
            controlador = ControladorCaptura(interfaz, modelo)


            self._master.wait_window()

            if not interfaz.guardar_documento or not self._documento.items:
                print('no se guarda nada')
                return

            document_id = self.crear_cabecera_documento(152, 'FC')

            self._documento.document_id = document_id
            partidas = modelo.documento.items

            if partidas:
                for partida in partidas:
                    estado_modificacion = int(
                        partida.get('ItemProductionStatusModified', 0) or 0
                    )
                    # Maniobras se conserva en memoria como origen reversible,
                    # pero después del prorrateo queda marcada como eliminada.
                    # No debe insertarse además del importe ya distribuido.
                    if estado_modificacion == 3:
                        continue

                    parametros = (
                        document_id,
                        partida['ProductID'],
                        2,  # depot id minisuper
                        partida['cantidad'],
                        partida['precio'],
                        partida.get('CostPrice', partida['precio']),
                        partida['subtotal'],
                        partida['TipoCaptura'],
                        self._module_id,
                        partida['Comments'],
                        partida.get('DiscountPerc', 0),
                        partida.get('ApplyGlobalDiscount', 0),
                        partida.get('ProductSupplierKey'),
                        partida.get('SupplierBusinessEntityID', 0),
                        partida.get('ExpenseTypeID', 0),
                        partida.get('DateItem'),
                    )
                    self._base_de_datos.insertar_partida_documento_cayal(parametros)


            registros = self._documento.prorrateo_maniobras
            if registros:

                self._base_de_datos.guardar_prorrateo_maniobras(document_id, self._user_id, registros)

            self._modelo_captura.actualizar_totales_documento(document_id)

        finally:
            self._finalizar_captura()

    def crear_cabecera_documento(self, module_id = 0, prefix=None):

        module_id = self._module_id if module_id == 0 else module_id
        prefix = self._documento.prefix if not prefix else prefix

        document_id = self._base_de_datos.crear_documento(
                            self._documento.cfd_type_id,
                             prefix,
                            self._cliente.business_entity_id,
                            module_id,
                            self._user_id,
                            self._documento.depot_id,
                            self._documento.address_detail_id
        )
        return document_id

    def _finalizar_captura(self):
        if self._documento.document_id:
            documentos = {
                self._documento.document_id,
                self._documento.destination_document_id,
                self._documento.adicional_document_id,
            }
            for document_id in documentos:
                if document_id:
                    self._base_de_datos.registrar_documento_a_recalcular(
                        document_id,
                        document_id,
                        self._parametros_contpaqi.uuid,
                    )


            self._base_de_datos.command(
                'UPDATE docDocument SET Comments = ? WHERE DocumentID = ?',
                (self._documento.comments, self._documento.document_id),
            )

            self._base_de_datos.command("""
                    UPDATE P SET CostPrice = UC.UltimoCosto 
                    FROM docDocument D INNER JOIN
                        docDocumentItem DT ON D.DocumentID = DT.DocumentID INNER JOIN
                        orgProduct P ON DT.ProductID = P.ProductID INNER JOIN 
                        zvwUltimoCostoProductosCayal2Final UC ON DT.ProductID = UC.ProductID
                    WHERE 
                    D.DocumentID = ?
                    AND DT.DeletedOn IS NULL
                """, (self._documento.document_id,))

        #self._master.destroy()
