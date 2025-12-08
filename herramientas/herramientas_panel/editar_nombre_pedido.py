
import os.path
import tkinter as tk
import unicodedata
import os
import gzip
import pickle
from pathlib import Path

from datetime import datetime

import pyperclip
import ttkbootstrap as ttk
import ttkbootstrap.dialogs
import re

from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.cliente import Cliente
from cayal.ventanas import Ventanas
from cayal.documento import Documento
from cayal.util import Utilerias


class EditarNombrePedido:

    def __init__(self, master, parametros, valores_fila):

        self._master = master
        self._parametros_contpaqi = parametros
        self._valores_fila = valores_fila


        self._declarar_variables_globales()
        self._crear_instancias_de_clases()

        self._crear_frames()
        self._cargar_componentes_forma()
        self._rellenar_info_inicial()
        self._cargar_eventos_componentes_forma()
        self._cargar_hotkeys()
        self._ajustar_componentes()

        self._actualizar_apariencia_forma(solo_apariencia_inicial=True)
        self._ventanas.configurar_ventana_ttkbootstrap('Seleccionar cliente')
        self._ventanas.enfocar_componente('tbx_buscar')

    def _declarar_variables_globales(self):
        self._termino_buscado = None
        self._consulta_clientes = None
        self._info_cliente_seleccionado = None
        self._consulta_direcciones = None
        self._instancia_llamada = False
        self._consulta_sucursales = None
        self._procesando_documento = False
        self._tipo_documento = 0

        self._module_id = self._parametros_contpaqi.id_modulo
        self._user_id = self._parametros_contpaqi.id_usuario
        self._document_id = self._parametros_contpaqi.id_principal

        self._customer_types_ids_ofertas = set()
        self.consulta_productos = []
        self.consulta_productos_ofertados = []
        self.consulta_productos_ofertados_btn = []
        self.products_ids_ofertados = []
        self._ofertas = {}
        self._ofertas_por_lista = {}

    def _crear_instancias_de_clases(self):
        self._base_de_datos = ComandosBaseDatos()
        self._cliente = Cliente()
        self._ventanas = Ventanas(self._master)
        self._documento = Documento()
        self._utilerias = Utilerias()

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_actual': ('frame_principal', 'Buscar cliente o folio de nota:',
                             {'row': 0, 'columnspan': 4, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.NSEW}),

            'frame_buscar': ('frame_principal', 'Buscar cliente o folio de nota:',
                                      {'row': 1, 'columnspan': 4, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.NSEW}),

            'frame_botones': ('frame_buscar', None,
                              {'row': 5, 'column': 1,  'pady': 5, 'sticky': tk.NSEW}),

            'frame_data': ('frame_principal', 'Información:',
                           {'row': 3, 'column': 0, 'columnspan': 8, 'padx': 1, 'pady': 1, 'sticky': tk.NSEW}),

            'frame_cbxs': ('frame_data', None,
                              {'row': 0, 'column': 0,  'columnspan': 4, 'pady': 1, 'sticky': tk.W}),

            'frame_cbx_direccion': ('frame_cbxs', 'Dirección:',
                               {'row': 0, 'column': 1,  'padx': 1, 'pady': 1, 'sticky': tk.NSEW}),

            'frame_cbx_documento': ('frame_cbxs', 'Documento:',
                                    {'row': 0, 'column': 2, 'padx': 1, 'pady': 1, 'sticky': tk.NSEW}),

            'frame_informacion': ('frame_data', 'Generales:',
                                  {'row': 3, 'column': 0, 'columnspan': 2, 'padx': 1, 'pady': 1, 'sticky': tk.NSEW}),

            'frame_direccion': ('frame_data', 'Detalles dirección:',
                                {'row': 3, 'column': 2, 'columnspan': 2, 'padx': 1, 'pady': 1, 'sticky': tk.NS}),

            'frame_copiar_direccion': ('frame_direccion', None,
                                       {'row': 11, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}),

        }

        self._ventanas.crear_frames(frames)

    def _cargar_componentes_forma(self):

        componentes = {
            'tbx_nombre_actual': ('frame_actual', None, 'Nombre actual:', None),
            'tbx_direccion_actual': ('frame_actual', None, 'Dirección actual:', None),
            'tbx_tipo_documento_actual': ('frame_actual', None, 'Tipo docto actual:', None),

            'tbx_buscar': ('frame_buscar', None, 'Buscar:', None),
            'cbx_resultados': ('frame_buscar', None, '  ', None),
            'cbx_documento': ('frame_cbx_documento',
                              {'row': 0, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W},
                              '  ', '[Ctrl+R] ó [Ctrl+F]'),
            'btn_seleccionar': ('frame_botones', 'primary', 'Seleccionar', '[F1]'),
            'btn_cancelar': ('frame_botones', 'danger', 'Cancelar', '[Esc]'),
            'cbx_direccion': ('frame_cbx_direccion', None, '  ', None),
        }
        self._ventanas.crear_componentes(componentes)

        self._componentes_direccion = {

            'lbl_txt_ncomercial': ('frame_direccion',
                                   {'font': ('Arial', 9, 'bold'), 'text': 'N.Comercial:'},
                                   {'row': 0, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),
            'lbl_txt_ruta': ('frame_direccion',
                             {'font': ('Arial', 9, 'bold'), 'text': 'Ruta:'},
                             {'row': 1, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),
            'lbl_txt_telefono': ('frame_direccion',
                                 {'font': ('Arial', 9, 'bold'), 'text': 'Teléfono:'},
                                 {'row': 2, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W},  None),
            'lbl_txt_celular': ('frame_direccion',
                                {'font': ('Arial', 9, 'bold'), 'text': 'Celular:'},
                                {'row': 3, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),
            'lbl_txt_calle': ('frame_direccion',
                              {'font': ('Arial', 9, 'bold'), 'text': 'Calle:'},
                              {'row': 4, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),
            'lbl_txt_numero': ('frame_direccion',
                               {'font': ('Arial', 9, 'bold'), 'text': 'Número:'},
                               {'row': 5, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W},  None),
            'txt_comentario': ('frame_direccion',
                               {'row': 6, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W}, ' ', None),
            'lbl_txt_cp': ('frame_direccion',
                           {'font': ('Arial', 9, 'bold'), 'text': 'C.P.'},
                           {'row': 7, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),
            'lbl_txt_colonia': ('frame_direccion',
                                {'font': ('Arial', 9, 'bold'), 'text': 'Colonia:'},
                                {'row': 8, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W},  None),
            'lbl_txt_estado': ('frame_direccion',
                               {'font': ('Arial', 9, 'bold'), 'text': 'Estado:'},
                               {'row': 9, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),
            'lbl_txt_municipio': ('frame_direccion',
                                  {'font': ('Arial', 9, 'bold'), 'text': 'Municipio:'},
                                  {'row': 10, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.W},  None),

            'lbl_ncomercial': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                               {'row': 0, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_ruta': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                         {'row': 1, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_telefono': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                             {'row': 2, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_celular': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                            {'row': 3, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_calle': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                          {'row': 4, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_numero': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                           {'row': 5, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_cp': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                       {'row': 7, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_colonia': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                            {'row': 8, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_estado': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                           {'row': 9, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_municipio': ('frame_direccion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                              {'row': 10, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'btn_copiar': ('frame_copiar_direccion', 'warning', 'Copiar', '[F4]'),
        }
        self._ventanas.crear_componentes(self._componentes_direccion)

        self._componentes_credito = {
            'lbl_txt_nombre': ('frame_informacion', None, 'Nombre:', None),
            'lbl_txt_rfc': ('frame_informacion', None, 'RFC:', None),
            'lbl_txt_autorizado': ('frame_informacion', None, 'Autorizado:', None),
            'lbl_txt_debe': ('frame_informacion', None, 'Debe:', None),
            'lbl_txt_restante': ('frame_informacion', None, 'Restante:', None),
            'lbl_txt_condicion': ('frame_informacion', None, 'Condición:', None),
            'lbl_txt_pcompra': ('frame_informacion', None, 'P.Compra:', None),
            'lbl_txt_comentario': ('frame_informacion', None, 'Comentario:', None),
            'lbl_txt_minisuper': ('frame_informacion', None, 'Minisuper:', None),
            'lbl_txt_vales': ('frame_informacion', None, 'C.Empleados:', None),
            'lbl_txt_lista': ('frame_informacion', None, 'Lista:', None),

            'lbl_nombre': ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                           {'row': 0, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_rfc': ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                        {'row': 1, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),


            'lbl_autorizado': ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                               {'row': 2, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_debe': ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                         {'row': 3, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_restante': ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                             {'row': 4, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_condicion': (
            'frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
            {'row': 5, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_pcompra': ('frame_informacion', {'font': ('Arial', 9, 'bold'),
                                                  'text': ''},
                            {'row': 6, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_comentario': ('frame_informacion', {'font': ('Arial', 9, 'bold'),
                                                     'text': ''},
                               {'row': 7, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_minisuper': ('frame_informacion', {'font': ('Arial', 9, 'bold'),
                                                    'text': ''},
                              {'row': 8, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_vales': ('frame_informacion', {'font': ('Arial', 9, 'bold'),
                                                    'text': ''},
                              {'row': 9, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),

            'lbl_lista': ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                          {'row': 10, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None),
        }


        if self._module_id != 1692:
            self._componentes_credito['lbl_lista'] = ('frame_informacion', {'font': ('Arial', 9, 'bold'), 'text': ''},
                          {'row': 9, 'column': 1, 'padx': 1, 'pady': 1, 'sticky': tk.W}, None)

            del self._componentes_credito['lbl_vales']
            del self._componentes_credito['lbl_txt_vales']


        self._ventanas.crear_componentes(self._componentes_credito)

    def _rellenar_info_inicial(self):
        self._ventanas.insertar_input_componente('tbx_nombre_actual',
                                                 self._valores_fila.get('Cliente',''))
        self._ventanas.insertar_input_componente('tbx_direccion_actual',
                                                 self._valores_fila.get('Direccion', ''))
        self._ventanas.insertar_input_componente('tbx_tipo_documento_actual',
                                                 self._valores_fila.get('T.Docto',''))

    def _ajustar_componentes(self):
        self._ventanas.ajustar_ancho_componente('cbx_resultados', 50)
        self._ventanas.ajustar_ancho_componente('tbx_nombre_actual',50)
        self._ventanas.bloquear_componente('btn_seleccionar')

    def _cargar_eventos_componentes_forma(self):
        eventos = {
            'btn_cancelar': self._master.destroy,
            'btn_seleccionar': self._seleccionar_cliente,
            'tbx_buscar': self._buscar_termino,
            'cbx_resultados': self._cambio_de_seleccion_cliente,
            'cbx_direccion': self._seleccionar_direccion,
            'btn_copiar':self._copiar_informacion_direccion
        }

        self._ventanas.cargar_eventos(eventos)

    def _cargar_hotkeys(self):
        hotkeys = {
            'F1': lambda: (self._forzar_confirmar_cbx('cbx_resultados'), self._seleccionar_cliente()),
            'F4': self._copiar_informacion_direccion,
            'Ctrl+F': lambda: self._seleccionar_cliente_por_documento('factura'),
            'Ctrl+R': lambda: self._seleccionar_cliente_por_documento('remision'),
        }
        self._ventanas.agregar_hotkeys_forma(hotkeys)

    def _seleccionar_cliente_por_documento(self, tipo):
        if self._ventanas.obtener_input_componente('cbx_resultados') == 'Seleccione':
            return

        if tipo == 'factura':
            if self._cliente.cayal_customer_type_id in (0, 1):
                return

            self._ventanas.insertar_input_componente('cbx_documento', 'Factura')
            # Ejecutamos las funciones directamente, no con lambda suelta
            self._forzar_confirmar_cbx('cbx_resultados')
            self._seleccionar_cliente()

        elif tipo == 'remision':
            self._ventanas.insertar_input_componente('cbx_documento', 'Remisión')
            self._forzar_confirmar_cbx('cbx_resultados')
            self._seleccionar_cliente()

    def _copiar_informacion_direccion(self):
        business_entity_id = self._info_cliente_seleccionado[0]['BusinessEntityID']
        address_detail_id = self._documento.address_detail_id

        informacion = self._base_de_datos.buscar_informacion_direccion_whatsapp(address_detail_id, business_entity_id)
        pyperclip.copy(informacion)
        self._master.iconify()

    def _validar_termino(self):
        termino_buscado = self._ventanas.obtener_input_componente('tbx_buscar')

        if not termino_buscado:
            self._ventanas.mostrar_mensaje('Debe introducir un termino a buscar')
            self._ventanas.bloquear_componente('btn_seleccionar')
            return

        if len(termino_buscado) < 5 and not termino_buscado.startswith(('FG', 'FM', 'FGR')):
            self._ventanas.mostrar_mensaje('Insuficientes letras en el termino a buscar')
            self._ventanas.bloquear_componente('btn_seleccionar')
            return

        return termino_buscado

    def _buscar_info_y_setear_cliente(self, business_entity_id, abrir=False, actualizar=False):
        """Busca info del cliente, setea en self._cliente y ejecuta la acción final."""
        self._buscar_info_cliente_seleccionado(business_entity_id)
        self._cliente.consulta = self._info_cliente_seleccionado
        self._cliente.settear_valores_consulta()
        self._rellenar_cbx_documento()
        self._buscar_ofertas()

        if abrir:
            self._llamar_instancia()
        if actualizar:
            self._actualizar_apariencia_forma()

    def _buscar_termino(self, event=None):
        termino_buscado = self._validar_termino()
        if not termino_buscado:
            return

        termino_buscado = termino_buscado.upper().strip()

        if termino_buscado != getattr(self, "_termino_buscado", None):
            self._termino_buscado = termino_buscado

        # 1) Búsqueda por folio (prefijos)
        if termino_buscado.startswith(('FG', 'FM', 'FGR')):
            info_documento = self._buscar_info_document_id(folio_documento=termino_buscado)
            if not info_documento:
                return
            business_entity_id = info_documento['BusinessEntityID']
            self._buscar_info_y_setear_cliente(business_entity_id, abrir=True)
            return

        es_numero = self._utilerias.es_cantidad(termino_buscado)

        # 2) Búsqueda por nombre (no numérico)
        if not es_numero:
            self._consulta_clientes = self._buscar_clientes_por_nombre_similar(self._termino_buscado)
            nombres_clientes = [reg['OfficialName'] for reg in (self._consulta_clientes or [])]

            if not nombres_clientes:
                self._ventanas.bloquear_componente('btn_seleccionar')
                self._ventanas.rellenar_cbx('cbx_resultados', None, 'sin seleccione')
                self._ventanas.mostrar_mensaje('No se encontraron resultados.')
                return

            if len(nombres_clientes) > 1:
                self._ventanas.rellenar_cbx('cbx_resultados', nombres_clientes)
            else:
                self._ventanas.rellenar_cbx('cbx_resultados', nombres_clientes, 'sin seleccione')
                cliente = nombres_clientes[0]
                business_entity_id = self._buscar_busines_entity_id(cliente)
                self._buscar_info_y_setear_cliente(business_entity_id, actualizar=True)

            self._ventanas.desbloquear_componente('btn_seleccionar')
            self._ventanas.enfocar_componente('cbx_resultados')
            self._ventanas.enfocar_componente('btn_seleccionar')
            return

        # 3) Búsqueda por código de barras (numérico)
        if len(self._termino_buscado) < 12:
            self._ventanas.mostrar_mensaje(f'El código {self._termino_buscado} es incorrecto.')
            self._ventanas.enfocar_componente('tbx_buscar')
            return

        codigo = self._termino_buscado[0:11]
        document_id = int(codigo.lstrip('0') or '0')
        info_documento = self._buscar_info_document_id(document_id=document_id)
        if not info_documento:
            self._ventanas.mostrar_mensaje(f'La búsqueda del término {codigo} no devolvió resultados.')
            return

        business_entity_id = info_documento['BusinessEntityID']
        self._buscar_info_y_setear_cliente(business_entity_id, abrir=True)

    def _buscar_clientes_por_nombre_similar(self, termino_buscado):
        # Dividir el término en palabras clave
        palabras = termino_buscado.split()

        # Construir dinámicamente la condición WHERE para incluir todas las palabras
        condiciones = " AND ".join([f"E.OfficialName LIKE '%' + ? + '%'" for _ in palabras])

        # Crear el query dinámico
        query = f"""
            SELECT E.BusinessEntityID, E.OfficialName
            FROM orgCustomer C
            INNER JOIN orgBusinessEntity E ON C.BusinessEntityID = E.BusinessEntityID
            WHERE {condiciones}
            AND C.DeletedOn IS NULL
            AND E.DeletedOn IS NULL
            AND E.BusinessEntityID NOT IN (1, 8179, 9277)
        """

        if self._module_id == 1692: #los vales de empleados estan limitados a ruta 7
            query = f"{query} AND C.ZoneID = 1040"

        return self._base_de_datos.fetchall(query, palabras)

    def _buscar_info_document_id(self, document_id=0, folio_documento=''):
        consulta = []
        info_documento ={}

        if document_id != 0:
            consulta = self._base_de_datos.fetchall("""
                SELECT D.BusinessEntityID, E.OfficialName,
                    ISNULL(D.FolioPrefix,'')+ISNULL(D.Folio,'') DocFolio,
                    CASE WHEN D.CancelledOn IS NULL THEN 0 ELSE 1 END Cancelled,
                    D.Balance, D.Total, D.TotalPaid, StatusPaidID
                FROM docDocument D
                INNER JOIN orgBusinessEntity E ON D.BusinessEntityID = E.BusinessEntityID
                WHERE D.DocumentID = ? AND ISNULL(D.Custom3,0) =1040
                AND D.ModuleID IN (21,1400,1319)
            """, (document_id,))

        if folio_documento != '':
            # aqui obtenemos el folio que son los numeros despues de las letras del prefijo
            folio = re.sub(r"\D", "", folio_documento)  # Reemplaza todo lo que no es dígito
            prefijo = re.match(r"[A-Za-z]+", folio_documento).group()   # Solo letras al inicio

            consulta =  self._base_de_datos.fetchall("""
                SELECT D.BusinessEntityID, E.OfficialName,
                    ISNULL(D.FolioPrefix,'')+ISNULL(D.Folio,'') DocFolio,
                    CASE WHEN D.CancelledOn IS NULL THEN 0 ELSE 1 END Cancelled,
                    D.Balance, D.Total, D.TotalPaid, StatusPaidID
                FROM docDocument D
                INNER JOIN orgBusinessEntity E ON D.BusinessEntityID = E.BusinessEntityID
                WHERE D.FolioPrefix = ?
                AND D.Folio = ?
                AND D.ModuleID IN (21,1400,1319)
            """,(prefijo, folio))

        if consulta:
            info_documento = consulta[0]

            cancelado = info_documento['Cancelled']
            status_paid_id = info_documento['StatusPaidID']
            official_name= info_documento['OfficialName']
            doc_folio = info_documento['DocFolio']

            if cancelado == 1:
                self._ventanas.mostrar_mensaje(f'El documento {doc_folio} del cliente {official_name} está cancelado.')
                return

            if status_paid_id == 1:
                self._ventanas.mostrar_mensaje(f'El documento {doc_folio} del cliente {official_name} está saldado completamente.')
                return

        if not consulta:
            if folio_documento != '':
                self._ventanas.mostrar_mensaje(f'La búsqueda del término {folio_documento} no devolvió resultados.')
            return

        return info_documento

    def _cambio_de_seleccion_cliente(self, event=None):
        seleccion = self._ventanas.obtener_input_componente('cbx_resultados')

        if seleccion == 'Seleccione':
            self._cliente.reinicializar_atributos()
            self._ventanas.mostrar_mensaje(mensaje='Debe seleccionar un cliente de la lista', master=self._master)
            self._ventanas.bloquear_componente('btn_seleccionar')
            return

        # <<< NUEVO: cachear selección confirmada >>>
        self._ultimo_cliente_texto = seleccion
        self._ultimo_cliente_id = self._buscar_busines_entity_id(seleccion)

        self._ventanas.desbloquear_componente('btn_seleccionar')
        self._buscar_info_y_setear_cliente(self._ultimo_cliente_id, actualizar=True)
        self._actualizar_apariencia_forma()

    def _forzar_confirmar_cbx(self, nombre_cbx):
        """Si el combobox tiene un item resaltado pero no confirmado, confírmalo.
           Si no hay nada confirmado, usa el último cliente cacheado o el primer valor."""
        cbx = self._ventanas.componentes_forma.get(nombre_cbx)
        if not cbx:
            return
        try:
            cur = cbx.current()  # -1 si no hay confirmación
            val = cbx.get()
            vals = list(cbx['values']) if 'values' in cbx.keys() else []
            if (cur == -1 or val == 'Seleccione') and vals:
                # Si tenemos último confirmado, úsalo
                if getattr(self, '_ultimo_cliente_texto', None) in vals:
                    cbx.set(self._ultimo_cliente_texto)
                else:
                    cbx.current(0)  # al menos fija el primero
                cbx.event_generate('<<ComboboxSelected>>')  # dispara tu flujo normal
        except Exception:
            pass

    def _buscar_busines_entity_id(self, cliente):
        business_entity_id = [valor['BusinessEntityID'] for valor in self._consulta_clientes if valor['OfficialName'] == cliente]
        business_entity_id = business_entity_id[0]

        return business_entity_id if business_entity_id else 0

    def _buscar_info_cliente_seleccionado(self, business_entity_id):
        if business_entity_id != 0:
            self._info_cliente_seleccionado = self._base_de_datos.fetchall("""
              SELECT * FROM [dbo].[zvwBuscarInfoCliente-BusinessEntityID](?)
            """, (business_entity_id,))

    def _seleccionar_cliente(self):
        # Asegura selección consolidada por si llegamos aquí desde F1
        self._forzar_confirmar_cbx('cbx_resultados')

        seleccion = self._ventanas.obtener_input_componente('cbx_resultados') or ''
        if seleccion == 'Seleccione' and getattr(self, '_ultimo_cliente_texto', None):
            # usa el último confirmado si el cbx sigue en placeholder
            seleccion = self._ultimo_cliente_texto

        if not seleccion or seleccion == 'Seleccione':
            self._ventanas.mostrar_mensaje(master=self._master, mensaje='Debe buscar y seleccionar un cliente.')
            return

        proceder = True

        # Prepara datos (usa el id cacheado si existe; evita re-resolver por texto)
        beid = getattr(self, '_ultimo_cliente_id', None)
        if not beid:
            beid = self._buscar_busines_entity_id(seleccion)

        self._buscar_info_y_setear_cliente(beid, actualizar=False)  # ya venimos con selección hecha
        self._cliente.consulta = self._info_cliente_seleccionado
        self._cliente.settear_valores_consulta()
        self._asignar_parametros_a_documento()

        if self._cliente.depots > 0:
            seleccion_direccion = (self._ventanas.obtener_input_componente('cbx_direccion') or '').upper()
            if seleccion_direccion == 'DIRECCIÓN FISCAL' or not seleccion_direccion:
                respuesta = ttk.dialogs.Messagebox.yesno(
                    parent=self._master, message='El cliente tiene sucursales ¿Desea proceder sin seleccionar una?')
                if respuesta == 'No':
                    proceder = False

        if proceder:
            self._llamar_instancia()

    def _rellenar_cbx_documento(self):
        if self._cliente.cayal_customer_type_id == 2:
            tipos_documento = ['Remisión', 'Factura']
            self._ventanas.rellenar_cbx('cbx_documento', tipos_documento)
        else:
            self._ventanas.mostrar_componente('cbx_documento')
            tipos_documento = ['Remisión']
            self._ventanas.rellenar_cbx('cbx_documento', tipos_documento, sin_seleccione=True)
            self._ventanas.bloquear_componente('cbx_documento')

    def _documento_seleccionado(self):

        prefijos = {
            967: 'PM', 1692:'CE', 21:'FM', 1400: 'FG', 1316:'NVR', 1319:'FGR', 158:'NV'
        }


        def es_remision():
            self._documento.cfd_type_id = 1
            self._documento.doc_type = 'REMISIÓN'
            self._documento.forma_pago = '01'
            self._documento.metodo_pago = 'PUE'
            self._documento.receptor_uso_cfdi = 'S01'

        def es_factura():
            self._documento.cfd_type_id = 0
            self._documento.doc_type = 'FACTURA'
            self._documento.forma_pago = self._cliente.forma_pago
            self._documento.metodo_pago = self._cliente.metodo_pago
            self._documento.receptor_uso_cfdi = self._cliente.receptor_uso_cfdi

        self._documento.prefix = prefijos.get(self._module_id, 'CAYAL')

        if self._module_id in (967,1692,1316):
            es_remision()
            return True

        if self._cliente.cayal_customer_type_id in (0, 1):
            es_remision()
            return True

        else:
            seleccion = self._ventanas.obtener_input_componente('cbx_documento')

            if seleccion == 'Seleccione':
                self._ventanas.mostrar_mensaje('Debe seleccionar un tipo de documento.')
                return False

            es_factura() if seleccion == 'Factura' else es_remision()
            return True

    def _procesar_direccion_seleccionada(self):

        def normalizar(texto):
            """Elimina acentos y convierte a minúsculas."""
            texto = unicodedata.normalize('NFD', texto)
            texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
            return texto.lower()

        # Obtener nombre de dirección del componente
        address_name = self._ventanas.obtener_input_componente('cbx_direccion')

        # Normaliza el texto para comparación
        address_name_normalizado = normalizar(address_name)

        # Verifica si contiene "direccion fiscal"
        if 'direccion fiscal' in address_name_normalizado:

            address_fiscal_detail_id = self._info_cliente_seleccionado[0].get('AddressFiscalDetailID', 0)
            address_selected = [reg for reg in self._consulta_direcciones
                            if reg['AddressDetailID'] == address_fiscal_detail_id]

            if address_selected:
                self._seleccionar_direccion_fiscal(address_selected)

                # esto pr
                self._base_de_datos.homologar_direccion_fiscal(address_fiscal_detail_id)
                return address_selected[0]

        return self._base_de_datos.procesar_direccion_seleccionada_cbx(address_name, self._consulta_direcciones)

    def _actualizar_apariencia_si_tiene_sucursales(self):

        if self._cliente.depots == 0:
            self._ventanas.ocultar_componente('cbx_sucursales')
            self._consulta_sucursales = None
        else:
            frame_buscar = self._ventanas.componentes_forma['frame_buscar']
            cbx_sucursales = ttk.Combobox(frame_buscar, state='readonly')
            cbx_sucursales.grid(row=2,  column=1, padx=185, pady=5, sticky=tk.W)
            self._ventanas.componentes_forma['cbx_sucursales'] = cbx_sucursales

            self._consulta_sucursales = self._base_de_datos.fetchall("""
                    SELECT A.DepotID,A.DepotName 
            		FROM orgBusinessEntity E INNER JOIN
            			orgDepot A ON E.BusinessEntityID=A.BusinessEntityID 
            		WHERE E.BusinessEntityID = ? AND A.DeletedOn IS NULL
                    """, (self._cliente.business_entity_id,))

            nombres_sucursales = [sucursal['DepotName'] for sucursal in self._consulta_sucursales]

            if self._consulta_sucursales:
                self._ventanas.rellenar_cbx('cbx_sucursales', nombres_sucursales)

    def _actualizar_apariencia_forma(self, solo_apariencia_inicial = False):

        def apariencia_inicial():
            self._ventanas.ocultar_frame('frame_data')


        if solo_apariencia_inicial:
            apariencia_inicial()
            self._master.place_window_center()
            #self.master.after_idle(lambda: self.ventanas.centrar_ventana_ttkbootstrap(self.master))
            return

        cbx_direccion = self._ventanas.componentes_forma['cbx_direccion']

        if self._cliente.cayal_customer_type_id in (1, 2):
            self._ventanas.posicionar_frame('frame_data')
            self._ventanas.posicionar_frame('frame_informacion')
            self._ventanas.posicionar_frame('frame_direccion')
            self._cargar_info_credito()
        else:
            self._ventanas.posicionar_frame('frame_data')
            self._ventanas.ocultar_frame('frame_informacion')
            posicion = {'row': 1, 'column': 0, 'columnspan': 2, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}
            self._ventanas.posicionar_frame('frame_direccion', posicion)

        self._consulta_direcciones = self._base_de_datos.rellenar_cbx_direcciones(
            self._cliente.business_entity_id,
            cbx_direccion
        )
        self._seleccionar_direccion()

        self._master.place_window_center()

    def _seleccionar_direccion(self, event=None):
        direccion = {}

        self._ventanas.posicionar_frame('frame_cbxs')
        self._ventanas.mostrar_componente('cbx_direccion')

        if self._cliente.addresses == 1:
            direccion = self._seleccionar_direccion_fiscal(direccion)
        else:
            datos_direccion = self._procesar_direccion_seleccionada()
            address_detail_id = datos_direccion.get('address_detail_id', 0)
            direccion = self._base_de_datos.buscar_detalle_direccion_formateada(address_detail_id)
            direccion['celular'] = self._info_cliente_seleccionado[0]['CellPhone']

        self._documento.address_details = direccion
        self._documento.address_detail_id = direccion.get('address_detail_id', 0)
        self._cargar_info_direccion(direccion)

    def _seleccionar_direccion_fiscal(self, direccion):

        if isinstance(direccion, list):
            direccion = direccion[0]

        direccion['address_detail_id'] = self._cliente.address_fiscal_detail_id
        direccion['address_name'] = 'Dirección Fiscal'
        direccion['depot_id'] = 0
        direccion['telefono'] = self._cliente.phone
        direccion['celular'] = self._cliente.cellphone
        direccion['calle'] = self._cliente.address_fiscal_street
        direccion['numero'] = self._cliente.address_fiscal_ext_number
        direccion['comentario'] = self._cliente.address_fiscal_comments
        direccion['cp'] = self._cliente.address_fiscal_zip_code
        direccion['colonia'] = self._cliente.address_fiscal_city
        direccion['estado'] = self._cliente.address_fiscal_state_province
        direccion['municipio'] = self._cliente.address_fiscal_municipality

        return direccion

    def _cargar_info_direccion(self, info_direccion):
        self._limpiar_direccion()
        self._ventanas.posicionar_frame('frame_direccion')

        informacion = {
            'lbl_ncomercial': self._cliente.commercial_name,
            'lbl_ruta': self._cliente.zone_name,
            'lbl_telefono': info_direccion.get('telefono', ''),
            'lbl_celular': info_direccion.get('celular', ''),
            'lbl_calle': info_direccion.get('calle', ''),
            'lbl_numero': info_direccion.get('numero', ''),
            'lbl_cp': info_direccion.get('cp', ''),
            'lbl_colonia': info_direccion.get('colonia', ''),
            'lbl_estado': info_direccion.get('estado', ''),
            'lbl_municipio': info_direccion.get('municipio', ''),
            'txt_comentario': info_direccion.get('comentario','')
        }

        for nombre_componente, valores in self._componentes_direccion.items():
            if '_txt' in nombre_componente:
                continue

            valor_direccion = informacion.get(nombre_componente, '')
            self._ventanas.insertar_input_componente(nombre_componente, valor_direccion)

    def _cargar_info_credito(self):
        self._limpiar_formulario()
        informacion = {
            'lbl_nombre': self._cliente.official_name,
            'lbl_rfc': self._cliente.official_number,
            'lbl_ruta': self._cliente.zone_name,
            'lbl_autorizado': self._credito_autorizado(),
            'lbl_debe': self._documentos_en_cartera(),
            'lbl_restante': self._credito_restante(),
            'lbl_condicion': self._cliente.payment_term_name,
            'lbl_pcompra': self._ultimo_documento_en_cartera(self._cliente.business_entity_id),
            'lbl_comentario': self._cliente.credit_comments,
            'lbl_minisuper': self._credito_en_super(),
            'lbl_vales': self._vales_empleados(),
            'lbl_lista': self._cliente.customer_type_name,
        }
        for nombre_componente, valores in self._componentes_credito.items():
            if '_txt' in nombre_componente:
                continue

            valor_direccion = informacion.get(nombre_componente, '')
            self._ventanas.insertar_input_componente(nombre_componente, valor_direccion)

    def _limpiar_formulario(self):
        componentes = ['lbl_ncomercial','lbl_nombre',  'lbl_rfc', 'lbl_ruta', 'lbl_autorizado', 'lbl_debe', 'lbl_restante',
                       'lbl_condicion','lbl_pcompra', 'lbl_comentario', 'lbl_minisuper', 'lbl_lista',
                       'lbl_telefono', 'lbl_celular', 'lbl_calle', 'lbl_numero','lbl_cp',
                       'lbl_estado','lbl_municipio'
                       ]
        self._ventanas.limpiar_componentes(componentes)

    def _limpiar_direccion(self):
        componentes = [ 'lbl_calle', 'lbl_numero', 'lbl_cp', 'lbl_telefono', 'lbl_celular',
                       'lbl_estado', 'lbl_municipio', 'lbl_colonia', 'lbl_ncomercial'
                       ]
        self._ventanas.limpiar_componentes(componentes)

    def _credito_en_super(self):
        text = 'NO TIENE CRÉDITO EN MINISUPER'

        if self._cliente.store_credit == 1:
            if self._cliente.credit_block == 1:
                text = 'NO TIENE CRÉDITO EN MINISUPER'

            else:
                text = 'CRÉDITO EN MINISUPER PERMITIDO'

        return text

    def _vales_empleados(self):
        if self._cliente.coupons_block == 1:
            return f"NO TIENE DERECHO"

        if self._cliente.coupons != 0:
            return f"COMPRA DEL MES REALIZADA"

        return f"DISPONIBLE {self._cliente.remaining_coupons}"

    def _credito_autorizado(self):
        text = f'${self._cliente.authorized_credit}'

        if self._cliente.credit_block == 1:
            text = '$0.00'
        return text

    def _credito_restante(self):
        text = f'${self._cliente.remaining_credit}'

        if self._cliente.credit_block == 1:
            text = '$0.00'
        return text

    def _documentos_en_cartera(self):
        texto = ''
        if self._cliente.documents_with_balance > 0:
            texto = f'Debe ${self._cliente.debt} en {self._cliente.documents_with_balance} documentos.'
        else:
            texto = f'${self._cliente.debt}'
        return texto

    def _ultimo_documento_en_cartera(self, business_entity_id):
        info_ultimo_folio = self._base_de_datos.fetchall("""
            WITH CTE AS (
            SELECT 
                D.DocumentID,
                CAST(D.CreatedOn AS date) AS Fecha,
                CASE WHEN D.chkCustom1 = 1 THEN 'Remisión' ELSE 'Factura' END AS TipoDocto,
                ISNULL(D.FolioPrefix, '') + ISNULL(D.Folio, '') AS Folio,
                CFD.FormaPago AS FP,
                FORMAT(D.Total, 'C', 'es-MX') AS Total,
                FORMAT(D.TotalPaid, 'C', 'es-MX') AS Pagado,
                FORMAT(D.Balance, 'C', 'es-MX') AS Saldo,
                CASE WHEN A.DepotName IS NULL THEN '' ELSE A.DepotName END AS Sucursal
            FROM 
                docDocument D
                INNER JOIN docDocumentExtra X ON D.DocumentID = X.DocumentID
                LEFT OUTER JOIN orgDepot A ON X.BusinessEntityDepotID = A.DepotID
                INNER JOIN docDocumentCFD CFD ON D.DocumentID = CFD.DocumentID
                INNER JOIN vwcboAnexo20v33_FormaPago FP ON CFD.FormaPago = FP.Clave
            WHERE 
                D.CancelledOn IS NULL
                AND D.StatusPaidID <> 1
                AND D.BusinessEntityID = ?
                AND D.ModuleID IN (21, 1400, 1319)
                AND D.Balance <> 0
        )
        SELECT 
            MIN(D.DocumentID) AS DocumentID,
            D.Fecha,
            D.TipoDocto,
            D.Folio,
            D.FP,
            D.Total,
            D.Pagado,
            D.Saldo,
            D.Sucursal,
            DATEDIFF(DAY, D.Fecha, GETDATE()) AS Dias  -- Calcula la diferencia en días
        FROM 
            CTE D
        WHERE 
            D.DocumentID = (SELECT MIN(DocumentID) FROM CTE)
        GROUP BY 
            D.Fecha, D.TipoDocto, D.Folio, D.FP, D.Total, D.Pagado, D.Saldo, D.Sucursal

        """, (business_entity_id,))

        texto = ''

        if info_ultimo_folio:
            info_ultimo_folio = info_ultimo_folio[0]
            folio = info_ultimo_folio['Folio']
            saldo = info_ultimo_folio['Saldo']
            dias = info_ultimo_folio['Dias']

            texto = f'{folio}, saldo: {saldo}, hace {dias} días.'


        return texto

    def _validar_restriccion_por_cliente(self):
        if self._module_id == 1692:
            if self._cliente.coupons != 0 or self._cliente.coupons_block == 1:
                texto = self._vales_empleados().lower().capitalize()

                self._ventanas.mostrar_mensaje(texto)
                return

            if self._cliente.coupons_block == 1:
                texto = self._vales_empleados()
                self._ventanas.mostrar_mensaje(texto)
                return

        return True

    def _llamar_instancia(self):
        if self._instancia_llamada or not self._documento_seleccionado():
            return

        if not self._validar_restriccion_por_cliente():
            return

        try:
            self._instancia_llamada = True

            # aqui actualizamos y agregamos a la bitacora
            print(self._cliente.business_entity_id)
            print(self._documento.address_detail_id)
            print(self._documento.doc_type)

        finally:
            self._master.destroy()

    def _actualizar_excedente_crediticio(self):
        self._base_de_datos.command(
            'UPDATE docDocument SET CreditExceededAmount = ? WHERE DocumentID = ?',
            (self._documento.credit_exceeded_amount, self._documento.document_id)
        )

    def _actualizar_forma_pago_documento(self):
        self._base_de_datos.command(
            'UPDATE docDocumentCFD SET FormaPago = ? WHERE DocumentID = ?',
            (
                self._documento.forma_pago,
                self._documento.document_id)
        )

    def _actualizar_comentario_documento(self):
        self._base_de_datos.command(
            'UPDATE docDocument SET Comments = ? WHERE DocumentID = ?',
            (self._documento.comments, self._documento.document_id)
        )

    def _asignar_parametros_a_documento(self):

        # las propiedades  self._doc_type | self._cfd_type_id son aginadas por la funcion self._documento_seleccionado

        datos_direccion_seleccionada = self._procesar_direccion_seleccionada()

        self._documento.depot_id = datos_direccion_seleccionada.get('depot_id', 0)
        self._documento.depot_name = datos_direccion_seleccionada.get('depot_name', '')
        self._documento.address_detail_id = datos_direccion_seleccionada.get('address_detail_id', 0)
        self._documento.address_name = datos_direccion_seleccionada.get('address_name', '')
        self._documento.business_entity_id = self._cliente.business_entity_id
        self._documento.customer_type_id = self._cliente.cayal_customer_type_id

    def _buscar_ofertas(self):

        if self._cliente.customer_type_id in self._customer_types_ids_ofertas:
            return

        self._buscar_productos_ofertados_cliente()

    def _buscar_productos_ofertados_cliente(self):
        try:
            from zoneinfo import ZoneInfo  # Py>=3.9
            tz = ZoneInfo("America/Merida")
        except Exception:
            tz = None  # fallback sin zona (no debería pasar en Py>=3.9)

        def _today_str():
            now = datetime.now(tz) if tz else datetime.now()
            return now.strftime("%Y%m%d")

        def _cache_dir() -> Path:
            base = getattr(self, "_offers_cache_dir", None)
            if base is None:
                base = Path(".offers_cache")
                setattr(self, "_offers_cache_dir", base)
            base.mkdir(parents=True, exist_ok=True)
            return base

        def _cache_path(ctid: int, day: str) -> Path:
            # nombre con fecha para validar día y facilitar limpieza
            safe = f"ofertas_{ctid}_{day}.pkl.gz"
            return _cache_dir() / safe

        def _cache_load_if_today(ctid: int):
            day = _today_str()
            p = _cache_path(ctid, day)
            if not p.exists():
                return None
            try:
                with gzip.open(p, "rb") as fh:
                    return pickle.load(fh)
            except Exception:
                try:
                    p.unlink(missing_ok=True)
                except Exception:
                    pass
                return None

        def _cache_save_today(ctid: int, data: dict):
            day = _today_str()
            p = _cache_path(ctid, day)
            tmp = p.with_suffix(".tmp")
            with gzip.open(tmp, "wb") as fh:
                pickle.dump(data, fh, protocol=pickle.HIGHEST_PROTOCOL)
            os.replace(tmp, p)

        def _cache_cleanup_not_today():
            day = _today_str()
            base = _cache_dir()
            # Borra cualquier archivo que no termine en _YYYYMMDD.pkl.gz (día actual)
            for f in base.glob("ofertas_*.pkl.gz"):
                if not f.name.endswith(f"_{day}.pkl.gz"):
                    try:
                        f.unlink(missing_ok=True)
                    except Exception:
                        pass

        customer_type_id = self._cliente.customer_type_id

        # 1) Memoria
        ofertas_mem = self._ofertas_por_lista.get(customer_type_id)
        if ofertas_mem is not None:
            self._customer_types_ids_ofertas.add(customer_type_id)
            return ofertas_mem

        # 2) Cache local (solo si es de HOY)
        ofertas_disk = _cache_load_if_today(customer_type_id)
        if ofertas_disk is not None:
            self._ofertas_por_lista[customer_type_id] = ofertas_disk
            self._customer_types_ids_ofertas.add(customer_type_id)
            _cache_cleanup_not_today()
            return ofertas_disk

        # 3) Consulta BD + proceso
        consulta_productos_ofertados = self._base_de_datos.buscar_productos_en_oferta(
            lista_precios=customer_type_id
        )
        productos_ids = list({reg['ProductID'] for reg in consulta_productos_ofertados})

        consulta_productos = self._buscar_info_productos_por_ids(productos_ids)
        consulta_procesada = self._agregar_impuestos_productos(consulta_productos)

        ofertas = {
            'consulta_productos': consulta_procesada,
            'consulta_productos_ofertados': consulta_productos_ofertados,
            'consulta_productos_ofertados_btn': consulta_procesada,  # ajusta si necesitas otro set
            'products_ids_ofertados': productos_ids
        }

        # Guarda en memoria y en disco (para HOY)
        self._ofertas_por_lista[customer_type_id] = ofertas
        self._customer_types_ids_ofertas.add(customer_type_id)
        _cache_save_today(customer_type_id, ofertas)

        # 4) Limpieza de archivos no correspondientes a HOY
        _cache_cleanup_not_today()

        return ofertas

    def _buscar_info_productos_por_ids(self, productos_ids, no_en_venta=None):

        if no_en_venta:
            return self._base_de_datos.buscar_info_productos(productos_ids,
                                                            no_en_venta=True)
        return self._base_de_datos.buscar_info_productos(productos_ids)

    def _agregar_impuestos_productos(self, consulta_productos):
        consulta_procesada = []
        for producto in consulta_productos:
            producto_procesado = self._utilerias.calcular_precio_con_impuesto_producto(producto)
            consulta_procesada.append(producto_procesado)
        return consulta_procesada