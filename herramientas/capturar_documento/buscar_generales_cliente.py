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


class BuscarGeneralesCliente:

    def __init__(self, master, parametros):

        # --- Referencias principales ---
        self._master = master
        self._parametros_contpaqi = parametros

        # --- Estado interno y variables resultado ---
        self._declarar_variables_globales()
        self._crear_instancias_de_clases()

        # --- Construcción UI ---
        self._crear_frames()
        self._cargar_componentes()
        self._cargar_eventos()
        self._cargar_hotkeys()
        self._ajustar_y_boquear_componentes()

        # --- Apariencia inicial ---
        self._actualizar_apariencia_forma(solo_apariencia_inicial=True)
        #self._ventanas.configurar_ventana_ttkbootstrap('Seleccionar cliente')
        self._ventanas.enfocar_componente('tbx_buscar')

        # --- Manejo seguro del cierre con “X” ---
        # Si el usuario cierra sin seleccionar, devolver valores neutros.
        #self._master.protocol("WM_DELETE_WINDOW", self._cerrar_sin_seleccion)

    #-----------------------------------------
    # Construcción de la forma
    #-----------------------------------------
    def _declarar_variables_globales(self):
        """
        Todas estas variables deben ser por instancia
        y reiniciarse en cada ejecución del popup.
        """

        # Búsqueda / selección
        self._termino_buscado = None
        self._consulta_clientes = None
        self._info_cliente_seleccionado = None
        self._consulta_sucursales = None

        # Control interno
        self._instancia_llamada = False          # evita doble ejecución de aceptar
        self._procesando_documento = False
        self._tipo_documento = 0

        # Parámetros operativos
        self._module_id = self._parametros_contpaqi.id_modulo
        self._user_id = self._parametros_contpaqi.id_usuario
        self._document_id = self._parametros_contpaqi.id_principal

        # Ofertas (estado por instancia)
        self._customer_types_ids_ofertas = set()
        self.consulta_productos = []
        self.consulta_productos_ofertados = []
        self.consulta_productos_ofertados_btn = []
        self.products_ids_ofertados = []

        # Resultado final que el panel leerá
        self.ofertas = {}              # ← se llenará al aceptar selección
        self._ofertas_por_lista = {}   # ← se llena en _buscar_ofertas()
        self.seleccion_aceptada = False

    def _crear_instancias_de_clases(self):
        """
        Instancias frescas para cada ejecución.
        Las anteriores NO se deben reutilizar.
        """
        self._base_de_datos = ComandosBaseDatos()
        self._utilerias = Utilerias()

        # Objetos resultado frescos para el panel
        self.cliente = Cliente()
        self.documento = Documento()

        # Manejo de UI independiente por popup
        self._ventanas = Ventanas(self._master)

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_buscar': ('frame_principal', 'Buscar cliente, folio o código de barras:',
                                      {'row': 0, 'columnspan': 4, 'column': 0, 'padx': 1, 'pady': 1, 'sticky': tk.NSEW}),

            'frame_botones': ('frame_buscar', None,
                              {'row': 2, 'column': 1,  'pady': 5, 'sticky': tk.NSEW}),

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

    def _cargar_componentes(self):

        componentes = {
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

    def _ajustar_y_boquear_componentes(self):
        self._ventanas.ajustar_ancho_componente('cbx_resultados', 50)
        self._ventanas.bloquear_componente('btn_seleccionar')

    def _cargar_eventos(self):
        eventos = {
            'btn_cancelar': self._cerrar_sin_seleccion,
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

    def _cerrar_sin_seleccion(self):
        """
        Cierre seguro cuando el usuario presiona la 'X'.
        El panel puede detectar esto porque cliente queda en None.
        """
        self.cliente = None
        self.documento = None
        self.ofertas = {}

        try:
            self._master.destroy()
        except Exception:
            pass
    #------------------------------------------
    # Flujo de trabajo
    #------------------------------------------
    def _buscar_termino(self, event=None):
        def _validar_termino():
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

        termino_buscado = _validar_termino()
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
            cfd_type_id = info_documento['CFDTypeID']
            self._settear_info_cliente_y_direcciones(business_entity_id, abrir=True, cfd_type_id=cfd_type_id)
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
                self._settear_info_cliente_y_direcciones(business_entity_id, actualizar=True)

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
        cfd_type_id = info_documento['CFDTypeID']

        self._settear_info_cliente_y_direcciones(business_entity_id, abrir=True, cfd_type_id=cfd_type_id)
    # ------------------------------------------
    # Helpers de busqueda ya sea por codigo de barras o nombre
    # ------------------------------------------
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
                    D.Balance, D.Total, D.TotalPaid, StatusPaidID, D.chkCustom1 CFDTypeID
                FROM docDocument D
                INNER JOIN orgBusinessEntity E ON D.BusinessEntityID = E.BusinessEntityID
                WHERE D.DocumentID = ?
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
                    D.Balance, D.Total, D.TotalPaid, StatusPaidID, D.chkCustom1 CFDTypeID
                FROM docDocument D
                INNER JOIN orgBusinessEntity E ON D.BusinessEntityID = E.BusinessEntityID
                WHERE D.FolioPrefix = ?
                AND D.Folio = ?
                AND D.ModuleID IN (21,1400,1319)
            """,(prefijo, folio))

        if consulta:
            info_documento = consulta[0]

        if not consulta:
            if folio_documento != '':
                self._ventanas.mostrar_mensaje(f'La búsqueda del término {folio_documento} no devolvió resultados.')
            return

        return info_documento

    def _settear_info_cliente_y_direcciones(self,
                                            business_entity_id,
                                            abrir: bool = False,
                                            actualizar: bool = False,
                                            cfd_type_id: int = 2
                                            ):
        """
        Busca la información del cliente por BusinessEntityID,
        la carga en self.cliente y prepara documentos/ofertas.

        Parámetros
        ----------
        business_entity_id : int
            Identificador del cliente a buscar.
        abrir : bool
            Si True, al finalizar la carga ejecuta _aceptar_seleccion().
        actualizar : bool
            Si True, refresca la apariencia de la forma (_actualizar_apariencia_forma()).
        """

        # 1) Reset mínimo de contexto para evitar arrastrar datos de búsquedas previas
        self._info_cliente_seleccionado = None
        self._consulta_sucursales = None
        # ofertas de esta instancia se recalcularán
        self.ofertas = {}
        self._ofertas_por_lista = {}

        # 2) Buscar info del cliente
        self._buscar_info_cliente_seleccionado(business_entity_id)

        # Si no hubo resultado, no seguimos
        if not self._info_cliente_seleccionado:
            self._ventanas.mostrar_mensaje("No se encontró información del cliente.")
            return

        # 3) Pasar la consulta al objeto Cliente y setear sus atributos
        self.cliente.consulta = self._info_cliente_seleccionado
        self.cliente.settear_valores_consulta()

        # 4) cargar la informacion de las direcciones del cliente
        self.cliente.addresses_details = []
        direcciones_cliente = self._buscar_info_direcciones_cliente_seleccionado(business_entity_id)
        for direccion in direcciones_cliente:
            self.cliente.add_address_detail(direccion)

        self._rellenar_cbx_direccion()

        # 5) Preparar documentos / direcciones / sucursales según ese cliente
        self._rellenar_cbx_documento()

        # 5) Buscar ofertas (debe llenar self._ofertas_por_lista para este cliente)
        self._buscar_ofertas()

        # 6) Lógica opcional: abrir captura y/o refrescar UI
        if actualizar and not abrir:
            self._actualizar_apariencia_forma()

        # 7) Caso opcional para apertura por ejemplo folio o codigo de barras
        if abrir:
            seleccion = 'Seleccione'
            if cfd_type_id != 2:
                seleccion =  'Factura' if cfd_type_id == 0 else 'Remisión'
            self._aceptar_seleccion(seleccion)

    # ------------------------------------------------------------------------------
    # Helper que garantiza homologar clientes antiguos a nuevo proceso de direcciones adicionales
    # ------------------------------------------------------------------------------
    def _homologar_direccion_fiscal(self, business_entity_id):
        if business_entity_id <= 0:
            return
        # esta funcion es deuda tecnica de la homologacion entre la direccion fiscal
        # y orgbusinessentitymaininfo que es la tabla donde nace los parametros
        # de la direccion fiscal del cliente, esto es necesario para coherencia en
        # la información y la impresion de los formatos del cliente

        self._base_de_datos.command("""
           DECLARE @business_entity_id INT = ?;

        DECLARE @CH TABLE
        (
            BusinessEntityID       INT PRIMARY KEY,
            BusinessEntityEMail    NVARCHAR(255) NULL,
            BusinessEntityPhone    NVARCHAR(50)  NULL,
            Celular                NVARCHAR(50)  NULL
        );
        
        INSERT INTO @CH (BusinessEntityID, BusinessEntityEMail, BusinessEntityPhone, Celular)
        SELECT
            oc.BusinessEntityID,
        
            COALESCE(
                MAX(CASE WHEN oc.ChannelTypeID = 1 AND oc.IsMainChannel = 1
                         THEN NULLIF(LTRIM(RTRIM(oc.ChannelValue)), '') END),
                MAX(CASE WHEN oc.ChannelTypeID = 1
                         THEN NULLIF(LTRIM(RTRIM(oc.ChannelValue)), '') END)
            ) AS BusinessEntityEMail,
        
            COALESCE(
                MAX(CASE WHEN oc.ChannelTypeID = 2 AND oc.IsMainChannel = 1
                         THEN NULLIF(LTRIM(RTRIM(oc.ChannelValue)), '') END),
                MAX(CASE WHEN oc.ChannelTypeID = 2
                         THEN NULLIF(LTRIM(RTRIM(oc.ChannelValue)), '') END)
            ) AS BusinessEntityPhone,
        
            COALESCE(
                MAX(CASE WHEN oc.ChannelTypeID = 3 AND oc.IsMainChannel = 1
                         THEN NULLIF(LTRIM(RTRIM(oc.ChannelValue)), '') END),
                MAX(CASE WHEN oc.ChannelTypeID = 3
                         THEN NULLIF(LTRIM(RTRIM(oc.ChannelValue)), '') END)
            ) AS Celular
        FROM orgCommunicationChannel oc
        WHERE oc.BusinessEntityID = @business_entity_id
          AND oc.DeletedOn IS NULL
        GROUP BY oc.BusinessEntityID;
        
        -- 1) Refrescar orgBusinessEntityMainInfo
        UPDATE EM
        SET
            EM.BusinessEntityEMail = COALESCE(CH.BusinessEntityEMail, EM.BusinessEntityEMail),
            EM.BusinessEntityPhone = COALESCE(CH.BusinessEntityPhone, EM.BusinessEntityPhone),
            EM.Celular             = COALESCE(CH.Celular, EM.Celular)
        FROM orgBusinessEntityMainInfo EM
        LEFT JOIN @CH CH
            ON CH.BusinessEntityID = EM.BusinessEntityID
        WHERE EM.BusinessEntityID = @business_entity_id
          AND (
                ISNULL(EM.BusinessEntityEMail,'')  <> ISNULL(CH.BusinessEntityEMail,'')
             OR ISNULL(EM.BusinessEntityPhone,'') <> ISNULL(CH.BusinessEntityPhone,'')
             OR ISNULL(EM.Celular,'')             <> ISNULL(CH.Celular,'')
          );
        
        -- 2) Refrescar dirección fiscal + teléfono
        UPDATE ADT
        SET
            ADT.StateProvince      = EM.AddressFiscalStateProvince,
            ADT.City               = EM.AddressFiscalCity,
            ADT.Municipality       = EM.AddressFiscalMunicipality,
            ADT.Street             = EM.AddressFiscalStreet,
            ADT.Comments           = EM.AddressFiscalComments,
            ADT.CountryCode        = EM.AddressFiscalCountryCode,
            ADT.CityCode           = EM.AddressFiscalCityCode,
            ADT.MunicipalityCode   = EM.AddressFiscalMunicipalityCode,
            ADT.Telefono           = COALESCE(CH.BusinessEntityPhone, CH.Celular, ADT.Telefono)
        FROM orgBusinessEntityMainInfo EM
        INNER JOIN orgAddressDetail ADT
            ON EM.AddressFiscalDetailID = ADT.AddressDetailID
        LEFT JOIN @CH CH
            ON CH.BusinessEntityID = EM.BusinessEntityID
        WHERE EM.BusinessEntityID = @business_entity_id
          AND ADT.AddressDetailID = EM.AddressFiscalDetailID
          AND (
                ISNULL(ADT.StateProvince, '')    <> ISNULL(EM.AddressFiscalStateProvince, '') OR
                ISNULL(ADT.City, '')             <> ISNULL(EM.AddressFiscalCity, '') OR
                ISNULL(ADT.Municipality, '')     <> ISNULL(EM.AddressFiscalMunicipality, '') OR
                ISNULL(ADT.Street, '')           <> ISNULL(EM.AddressFiscalStreet, '') OR
                ISNULL(ADT.Comments, '')         <> ISNULL(EM.AddressFiscalComments, '') OR
                ISNULL(ADT.CountryCode, '')      <> ISNULL(EM.AddressFiscalCountryCode, '') OR
                ISNULL(ADT.CityCode, '')         <> ISNULL(EM.AddressFiscalCityCode, '') OR
                ISNULL(ADT.MunicipalityCode, '') <> ISNULL(EM.AddressFiscalMunicipalityCode, '') OR
                ISNULL(ADT.Telefono, '')         <> ISNULL(COALESCE(CH.BusinessEntityPhone, CH.Celular, ''), '')
          );
        """, (business_entity_id,))
    #------------------------------------------------------------------------------
    # Helpers de búsqueda de información relacionada al cliente y ss direcciones
    #------------------------------------------------------------------------------
    def _buscar_info_cliente_seleccionado(self, business_entity_id):
        if business_entity_id != 0:
            self._info_cliente_seleccionado = self._base_de_datos.fetchall("""
              SELECT * FROM [dbo].[zvwBuscarInfoCliente-BusinessEntityID](?)
            """, (business_entity_id,))

        self._homologar_direccion_fiscal(business_entity_id)

    def _buscar_info_direcciones_cliente_seleccionado(self, business_entity_id):
        return self._base_de_datos.buscar_direcciones_cliente(business_entity_id)
    # ------------------------------------------------------------------------
    # Funciones destinadas a construir las ofertas relacionadas con el cliente
    # ------------------------------------------------------------------------
    def _buscar_ofertas(self):
        """
        Se asegura de tener ofertas cargadas para el tipo de cliente actual.
        Utiliza memoria y cache en disco (HOY) desde _buscar_productos_ofertados_cliente.
        """
        customer_type_id = getattr(self.cliente, "customer_type_id", None)
        if customer_type_id is None:
            self.ofertas = {}
            return
        ofertas = self._buscar_productos_ofertados_cliente()
        # opcionalmente, puedes guardar directamente en self.ofertas aquí:
        # self.ofertas = ofertas or {}
        return ofertas

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
        customer_type_id = self.cliente.customer_type_id
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
    # ------------------------------------------------------------------------------
    # Funciones relacionadas a eventos de carga y seleccion de cliente
    # ------------------------------------------------------------------------------
    def _actualizar_apariencia_forma(self, solo_apariencia_inicial = False):

        def apariencia_inicial():
            self._ventanas.ocultar_frame('frame_data')

        if solo_apariencia_inicial:
            apariencia_inicial()
            self._master.place_window_center()
            return

        if self.cliente.cayal_customer_type_id in (1, 2):
            self._ventanas.posicionar_frame('frame_data')
            self._ventanas.posicionar_frame('frame_informacion')
            self._ventanas.posicionar_frame('frame_direccion')
            self._cargar_info_credito()
        else:
            self._ventanas.posicionar_frame('frame_data')
            self._ventanas.ocultar_frame('frame_informacion')
            posicion = {'row': 1, 'column': 0, 'columnspan': 2, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}
            self._ventanas.posicionar_frame('frame_direccion', posicion)

        self._master.place_window_center()

    def _cargar_info_credito(self):

        def _credito_autorizado():
            text = f'${self.cliente.authorized_credit}'

            if self.cliente.credit_block == 1:
                text = '$0.00'
            return text

        def _credito_restante():
            text = f'${self.cliente.remaining_credit}'

            if self.cliente.credit_block == 1:
                text = '$0.00'
            return text

        def _documentos_en_cartera():
            texto = ''
            if self.cliente.documents_with_balance > 0:
                texto = f'Debe ${self.cliente.debt} en {self.cliente.documents_with_balance} documentos.'
            else:
                texto = f'${self.cliente.debt}'
            return texto

        def _credito_en_super():
            text = 'NO TIENE CRÉDITO EN MINISUPER'

            if self.cliente.store_credit == 1:
                if self.cliente.credit_block == 1:
                    text = 'NO TIENE CRÉDITO EN MINISUPER'

                else:
                    text = 'CRÉDITO EN MINISUPER PERMITIDO'

            return text

        def _vales_empleados():
            if self.cliente.coupons_block == 1:
                return f"NO TIENE DERECHO"

            if self.cliente.coupons != 0:
                return f"COMPRA DEL MES REALIZADA"

            return f"DISPONIBLE {self.cliente.remaining_coupons}"

        informacion = {
            'lbl_nombre': self.cliente.official_name,
            'lbl_rfc': self.cliente.official_number,
            'lbl_ruta': self.cliente.zone_name,
            'lbl_autorizado': _credito_autorizado(),
            'lbl_debe': _documentos_en_cartera(),
            'lbl_restante': _credito_restante(),
            'lbl_condicion': self.cliente.payment_term_name,
            'lbl_pcompra': self._ultimo_documento_en_cartera(self.cliente.business_entity_id),
            'lbl_comentario': self.cliente.credit_comments,
            'lbl_minisuper': _credito_en_super(),
            'lbl_vales': _vales_empleados(),
            'lbl_lista': self.cliente.customer_type_name,
        }
        for nombre_componente, valores in self._componentes_credito.items():
            if '_txt' in nombre_componente:
                continue

            valor = informacion.get(nombre_componente, '')
            self._ventanas.insertar_input_componente(nombre_componente, valor)

    def _seleccionar_cliente(self):
        # Asegura selección consolidada por si llegamos aquí desde F1
        self._forzar_confirmar_cbx('cbx_resultados')

        seleccion = self._ventanas.obtener_input_componente('cbx_resultados') or ''
        if seleccion == 'Seleccione' and getattr(self, '_ultimo_cliente_texto', None):
            seleccion = self._ultimo_cliente_texto

        if not seleccion or seleccion == 'Seleccione':
            self._ventanas.mostrar_mensaje(master=self._master, mensaje='Debe buscar y seleccionar un cliente.')
            return

        proceder = True

        beid = getattr(self, '_ultimo_cliente_id', None)
        if not beid:
            beid = self._buscar_busines_entity_id(seleccion)

        if self.cliente.depots > 0:
            seleccion_direccion = (self._ventanas.obtener_input_componente('cbx_direccion') or '').upper()
            if seleccion_direccion == 'DIRECCIÓN FISCAL' or not seleccion_direccion:
                respuesta = ttk.dialogs.Messagebox.yesno(
                    parent=self._master, message='El cliente tiene sucursales ¿Desea proceder sin seleccionar una?')
                if respuesta == 'No':
                    proceder = False

        if proceder:
            self._aceptar_seleccion()

    def _seleccionar_cliente_por_documento(self, tipo):
        if self._ventanas.obtener_input_componente('cbx_resultados') == 'Seleccione':
            return

        if tipo == 'factura':
            if self.cliente.cayal_customer_type_id in (0, 1):
                return

            self._ventanas.insertar_input_componente('cbx_documento', 'Factura')
            # Ejecutamos las funciones directamente, no con lambda suelta
            self._forzar_confirmar_cbx('cbx_resultados')
            self._seleccionar_cliente()

        elif tipo == 'remision':
            self._ventanas.insertar_input_componente('cbx_documento', 'Remisión')
            self._forzar_confirmar_cbx('cbx_resultados')
            self._seleccionar_cliente()

    def _cambio_de_seleccion_cliente(self, event=None):
        seleccion = self._ventanas.obtener_input_componente('cbx_resultados')

        if seleccion == 'Seleccione':
            self.cliente.reinicializar_atributos()
            self.documento.reinicializar_atributos()
            self._ventanas.mostrar_mensaje(mensaje='Debe seleccionar un cliente de la lista', master=self._master)
            self._ventanas.bloquear_componente('btn_seleccionar')
            return

        self._ultimo_cliente_texto = seleccion
        self._ultimo_cliente_id = self._buscar_busines_entity_id(seleccion)

        self._ventanas.desbloquear_componente('btn_seleccionar')
        self._settear_info_cliente_y_direcciones(self._ultimo_cliente_id, actualizar=True)
        self._actualizar_apariencia_forma()
        self._seleccionar_direccion()
    # ------------------------------------------------------------------------------
    # Helpers relacionados a la seleccion del cliente
    # ------------------------------------------------------------------------------
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

    def _rellenar_cbx_documento(self):
        if self.cliente.cayal_customer_type_id == 2:
            tipos_documento = ['Remisión', 'Factura']
            self._ventanas.rellenar_cbx('cbx_documento', tipos_documento)
        else:
            self._ventanas.mostrar_componente('cbx_documento')
            tipos_documento = ['Remisión']
            self._ventanas.rellenar_cbx('cbx_documento', tipos_documento, sin_seleccione=True)
            self._ventanas.bloquear_componente('cbx_documento')

    def _actualizar_apariencia_si_tiene_sucursales(self):

        if self.cliente.depots == 0:
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
                    """, (self.cliente.business_entity_id,))

            nombres_sucursales = [sucursal['DepotName'] for sucursal in self._consulta_sucursales]

            if self._consulta_sucursales:
                self._ventanas.rellenar_cbx('cbx_sucursales', nombres_sucursales)

    def _seleccionar_direccion(self, event=None):

        def _limpiar_direccion():
            componentes = ['lbl_calle', 'lbl_numero', 'lbl_cp', 'lbl_telefono', 'lbl_celular',
                           'lbl_estado', 'lbl_municipio', 'lbl_colonia', 'lbl_ncomercial'
                           ]
            self._ventanas.limpiar_componentes(componentes)

        def _cargar_info_direccion(info_direccion):
            informacion = {
                'lbl_ncomercial': self.cliente.commercial_name,
                'lbl_ruta': self.cliente.zone_name,
                'lbl_telefono': info_direccion.get('Telefono', ''),
                'lbl_celular': info_direccion.get('Celular', ''),
                'lbl_calle': info_direccion.get('Street', ''),
                'lbl_numero': info_direccion.get('ExtNumber', ''),
                'lbl_cp': info_direccion.get('ZipCode', ''),
                'lbl_colonia': info_direccion.get('City', ''),
                'lbl_estado': info_direccion.get('StateProvince', ''),
                'lbl_municipio': info_direccion.get('Municipality', ''),
                'txt_comentario': info_direccion.get('Comments', '')
            }

            for nombre_componente, valores in self._componentes_direccion.items():
                if '_txt' in nombre_componente:
                    continue

                valor_direccion = informacion.get(nombre_componente, '')
                self._ventanas.insertar_input_componente(nombre_componente, valor_direccion)

        direccion = {}

        self._ventanas.posicionar_frame('frame_cbxs')
        self._ventanas.mostrar_componente('cbx_direccion')
        direccion_seleccionada = self._ventanas.obtener_input_componente('cbx_direccion')

        # direccion fiscal es la direccion AddressTypeID = 1
        if self.cliente.addresses == 1:
            consulta = [reg for reg in self.cliente.addresses_details if reg['AddressTypeID'] == 1]
        else:
            consulta = [reg for reg in self.cliente.addresses_details if reg['AddressName'] == direccion_seleccionada]

        if consulta and direccion_seleccionada != 'Seleccione':
            direccion = consulta[0]

            # Sólo usamos el ID aquí, para que la asignación "fuerte"
            # se haga una sola vez en _asignar_parametros_a_documento
            self.documento.address_detail_id = direccion.get('AddressDetailID', 0)

            _limpiar_direccion()
            _cargar_info_direccion(direccion)
            self._ventanas.posicionar_frame('frame_direccion')

    def _limpiar_formulario(self):
        componentes = ['lbl_ncomercial','lbl_nombre',  'lbl_rfc', 'lbl_ruta', 'lbl_autorizado', 'lbl_debe', 'lbl_restante',
                       'lbl_condicion','lbl_pcompra', 'lbl_comentario', 'lbl_minisuper', 'lbl_lista',
                       'lbl_telefono', 'lbl_celular', 'lbl_calle', 'lbl_numero','lbl_cp',
                       'lbl_estado','lbl_municipio'
                       ]
        self._ventanas.limpiar_componentes(componentes)

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

    def _rellenar_cbx_direccion(self):
        direcciones = getattr(self.cliente, "addresses_details", []) or []

        nombres_fiscal = []
        nombres_otros = []

        for d in direcciones:
            nombre = (d.get('AddressName') or '').strip()
            if not nombre:
                continue

            # Fiscal: AddressTypeID == 1
            if d.get('AddressTypeID') == 1:
                if nombre not in nombres_fiscal:
                    nombres_fiscal.append(nombre)
            else:
                if nombre not in nombres_otros:
                    nombres_otros.append(nombre)

        # Fiscal primero, luego el resto
        nombres = nombres_fiscal + nombres_otros

        if not nombres:
            self._ventanas.rellenar_cbx('cbx_direccion', None, 'sin seleccione')
            # Si no hay direcciones, aseguramos que el documento no arrastre algo anterior
            self.documento.address_detail_id = 0
            self.documento.address_details = {}
            return

        # Rellenamos el combo normalmente
        self._ventanas.rellenar_cbx('cbx_direccion', nombres, 'sin seleccione')

        # Dejamos seleccionada por defecto la primera (en tu lógica: la fiscal)
        direccion_por_defecto = nombres[0]
        self._ventanas.insertar_input_componente('cbx_direccion', direccion_por_defecto)

        # 🔴 Aquí es la clave: aplicamos de inmediato la dirección por defecto
        # para que se asigne self.documento.address_detail_id y se carguen los labels.
        self._seleccionar_direccion()
    # ------------------------------------------------------------------------------
    # funcion adcional de copia de informacion de la direccion
    # ------------------------------------------------------------------------------
    def _copiar_informacion_direccion(self):
        business_entity_id = self._info_cliente_seleccionado[0]['BusinessEntityID']
        address_detail_id = self.documento.address_detail_id

        informacion = self._base_de_datos.buscar_informacion_direccion_whatsapp(address_detail_id, business_entity_id)
        pyperclip.copy(informacion)
        self._master.iconify()
    # ------------------------------------------------------------------------------
    # funcion principal de seleccion del cliente y sus caracteristicas
    # ------------------------------------------------------------------------------
    def _aceptar_seleccion(self, seleccion_documento=None):
        """
        Confirma la selección del cliente y prepara los datos
        que leerá el panel (cliente, documento, ofertas).

        - Evita doble disparo usando _instancia_llamada.
        - Verifica que haya documento seleccionado y que el cliente cumpla restricciones.
        - Empaqueta las ofertas para el tipo de cliente actual.
        - Cierra la ventana de selección.
        """
        # 1) Evitar ejecuciones repetidas o sin documento válido
        if self._instancia_llamada:
            return

        if not self._documento_seleccionado(seleccion_documento):
            return

        # 2) Restricciones adicionales (crédito, bloqueo, etc.)
        if not self._validar_restriccion_vales_cliente():
            return

        try:
            self._instancia_llamada = True
            self.seleccion_aceptada = True

            self._asignar_parametros_a_documento()

            # 3) Empaquetar ofertas para el tipo de cliente actual
            ct_id = getattr(self.cliente, "customer_type_id", None)

            if ct_id is not None:
                # .get para evitar KeyError y caer en {} si no hay ofertas para ese tipo
                self.ofertas = self._ofertas_por_lista.get(ct_id, {})
            else:
                # si por alguna razón no hay tipo de cliente, devolvemos ofertas vacías
                self.ofertas = {}

        finally:
            # 4) Cerrar la ventana de selección de forma segura
            try:
                self._master.destroy()
            except Exception:
                pass
    # ------------------------------------------------------------------------------
    # helpers de la funcion principal de la seleccion del cliente
    # ------------------------------------------------------------------------------
    def _documento_seleccionado(self, seleccion=None):

        prefijos = {
            967: 'PM', 1692:'CE', 21:'FM', 1400: 'FG', 1316:'NVR', 1319:'FGR', 158:'NV'
        }


        def es_remision():
            self.documento.cfd_type_id = 1
            self.documento.doc_type = 'REMISIÓN'
            self.documento.forma_pago = '01'
            self.documento.metodo_pago = 'PUE'
            self.documento.receptor_uso_cfdi = 'S01'

        def es_factura():
            self.documento.cfd_type_id = 0
            self.documento.doc_type = 'FACTURA'
            self.documento.forma_pago = self.cliente.forma_pago
            self.documento.metodo_pago = self.cliente.metodo_pago
            self.documento.receptor_uso_cfdi = self.cliente.receptor_uso_cfdi

        self.documento.prefix = prefijos.get(self._module_id, 'CAYAL')

        if self._module_id in (967,1692,1316):
            es_remision()
            return True

        if self.cliente.cayal_customer_type_id in (0, 1):
            es_remision()
            return True

        else:
            seleccion = self._ventanas.obtener_input_componente('cbx_documento') if not seleccion else seleccion

            if seleccion == 'Seleccione':
                self._ventanas.mostrar_mensaje('Debe seleccionar un tipo de documento.')
                return False

            es_factura() if seleccion == 'Factura' else es_remision()
            return True

    def _asignar_parametros_a_documento(self):

        # Si por alguna razón aún no hay address_detail_id,
        # elegimos una dirección por defecto (fiscal si existe, si no la primera).
        if not getattr(self.documento, "address_detail_id", 0):
            direcciones = getattr(self.cliente, "addresses_details", []) or []

            if direcciones:
                direccion_defecto = None

                # Preferimos la fiscal (AddressTypeID == 1)
                for d in direcciones:
                    if d.get('AddressTypeID') == 1:
                        direccion_defecto = d
                        break

                if direccion_defecto is None:
                    direccion_defecto = direcciones[0]

                self.documento.address_detail_id = direccion_defecto.get('AddressDetailID', 0)
            else:
                # No hay direcciones registradas para el cliente; dejamos todo vacío y salimos
                self.documento.address_details = {}
                self.documento.depot_id = 0
                self.documento.depot_name = ''
                return

        # En este punto, address_detail_id debe ser > 0
        consulta = [
            reg for reg in self.cliente.addresses_details
            if reg['AddressDetailID'] == self.documento.address_detail_id
        ]

        if not consulta:
            # No encontramos una dirección que matchee ese ID; evitamos reventar
            self.documento.address_details = {}
            self.documento.depot_id = 0
            self.documento.depot_name = ''
            return

        direccion = consulta[0]

        depot_id = direccion.get('DepotID', 0)
        depot_name = ''
        if depot_id != 0:
            depot_name_row = self._base_de_datos.fetchone(
                'SELECT DepotName FROM orgDepot WHERE DepotID = ?',
                (depot_id,)
            )
            # fetchone te puede devolver dict o valor simple según lo tengas implementado
            depot_name = depot_name_row['DepotName'] if isinstance(depot_name_row, dict) else depot_name_row

        self.documento.address_details = direccion
        self.documento.depot_id = depot_id
        self.documento.depot_name = depot_name
        self.documento.address_detail_id = direccion.get('AddressDetailID', 0)
        self.documento.address_name = direccion.get('AddressName', '')
        self.documento.business_entity_id = self.cliente.business_entity_id
        self.documento.customer_type_id = self.cliente.customer_type_id
        self.documento.delivery_cost = self._utilerias.redondear_valor_cantidad_a_decimal(direccion.get('DeliveryCost', 20))

    def _validar_restriccion_vales_cliente(self):
        if self._module_id == 1692:
            if self.cliente.coupons != 0 or self.cliente.coupons_block == 1:
                texto =f"COMPRA DEL MES REALIZADA".lower().capitalize()

                self._ventanas.mostrar_mensaje(texto)
                return

            if self.cliente.coupons_block == 1:
                texto = f"NO TIENE DERECHO"
                self._ventanas.mostrar_mensaje(texto)
                return

        return True
