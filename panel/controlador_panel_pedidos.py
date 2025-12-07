import os
import platform
import re
import tempfile
import tkinter as tk
from datetime import datetime

from herramientas.herramientas_compartidas.buscar_pedido import BuscarPedido
from herramientas.capturar_documento.buscar_generales_cliente import BuscarGeneralesCliente
from herramientas.herramientas_compartidas.capturado_vs_producido import CapturadoVsProducido
from herramientas.herramientas_panel.editar_caracteristicas_pedido import EditarCaracteristicasPedido
from herramientas.capturar_documento.llamar_instancia_captura import LlamarInstanciaCaptura
from herramientas.herramientas_panel.ticket_pedido_cliente import TicketPedidoCliente
from herramientas.herramientas_panel.selector_tipo_documento import SelectorTipoDocumento
from ttkbootstrap.constants import *
from cayal.tableview_cayal import Tableview
from herramientas.herramientas_panel.editar_pedido import EditarPedido
from cayal.cliente import Cliente
from cayal.documento import Documento
from panel.herramientas_captura import HerramientasCaptura
from panel.herramientas_generales import HerramientasGenerales
from panel.herramientas_timbrado import HerramientasTimbrado


class ControladorPanelPedidos:
    def __init__(self, modelo):
        self._modelo = modelo
        self._interfaz = modelo.interfaz
        self._master = self._interfaz.master

        self._coloreando = False
        self._actualizando_tabla = False

        self._crear_tabla_pedidos()

        self._cargar_eventos()
        self._crear_notebook_herramientas()
        self._interfaz.ventanas.configurar_ventana_ttkbootstrap(titulo='Panel pedidos', bloquear=False)

        self._actualizar_pedidos(self._fecha_seleccionada())

        self._number_orders = -1
        self._number_transfer_payments = -1
        self._count_rest_leq15 = -1
        self._count_rest_16_30 = -1
        self._count_late_gt30 = -1

        self._autorefresco_ms = 3000  # cada 3s (ajústalo)
        self._autorefresco_activo = True
        self._bloquear_autorefresco = False  # se pone True mientras abres popups críticos
        self._iniciar_autorefresco()

    def _iniciar_autorefresco(self):
        # programa el siguiente tick sin bloquear la UI
        self._master.after(self._autorefresco_ms, self._tick_autorefresco)

    def _tick_autorefresco(self):
        # evita reentradas/choques con coloreado o popups
        if self._autorefresco_activo and not self._coloreando and not self._bloquear_autorefresco:
            try:
                self._buscar_nuevos_registros()  # <- tu función actual
            except Exception as e:
                # opcional: loguea, pero no revientes el loop
                print("[AUTOREFRESCO] error:", e)
        # vuelve a programar
        self._iniciar_autorefresco()

    def _pausar_autorefresco(self):
        self._bloquear_autorefresco = True
        print('autorefresco pausado')

    def _reanudar_autorefresco(self):
        self._bloquear_autorefresco = False
        print('autorefresco reanudado')

    def _cargar_eventos(self):
        eventos = {
            'den_fecha': lambda event: self._actualizar_pedidos(self._fecha_seleccionada(), criteria=False),
            'tbv_pedidos': (lambda event: self._rellenar_tabla_detalle(), 'doble_click'),
            'cbx_capturista': lambda event: self._filtrar_por_capturados_por(),
            'cbx_status': lambda event: self._filtrar_por_status(),
            'cbx_horarios': lambda event: self._filtrar_por_horas(),
            'chk_sin_procesar': lambda *args: self._filtrar_no_procesados(),
            'chk_sin_fecha': lambda *args: self._sin_fecha(),
        }
        self._interfaz.ventanas.cargar_eventos(eventos)

        evento_adicional = {
            'tbv_pedidos': (lambda event: self._actualizar_comentario_pedido(), 'seleccion')
        }
        self._interfaz.ventanas.cargar_eventos(evento_adicional)


    def _filtrar_no_procesados(self):
        self._interfaz.ventanas.insertar_input_componente('cbx_capturista', 'Seleccione')
        self._interfaz.ventanas.insertar_input_componente('cbx_status', 'Seleccione')
        self._interfaz.ventanas.insertar_input_componente('cbx_horarios', 'Seleccione')

        valor_chk = self._interfaz.ventanas.obtener_input_componente('chk_sin_procesar')
        if valor_chk == 1:
            self._interfaz.ventanas.cambiar_estado_checkbutton('chk_sin_fecha', 'deseleccionado')
            self._actualizar_pedidos()

        if valor_chk == 0:
            fecha = str(datetime.today().date())
            self._interfaz.ventanas.insertar_input_componente('den_fecha', fecha)


            self._actualizar_pedidos()

    def _buscar_pedidos_cliente_sin_fecha(self, criteria):

        fecha_seleccionada = self._interfaz.ventanas.obtener_input_componente('den_fecha')
        if fecha_seleccionada:
            return

        if not criteria:
            self._interfaz.ventanas.mostrar_mensaje('Debe introducir un valor a buscar.')
            return

        if criteria.strip() == '':
            self._interfaz.ventanas.mostrar_mensaje('Debe abundar en el valor a buscar.')
            return

        consulta = self._modelo.buscar_pedidos_cliente_sin_fecha(criteria)

        # Rellenar tabla con los datos filtrados
        self._interfaz.ventanas.rellenar_table_view(
            'tbv_pedidos',
            self._interfaz.crear_columnas_tabla(),
            consulta
        )

        self._modelo.consulta_pedidos = consulta
        self._colorear_filas_panel_horarios(actualizar_meters=True)

    def _limpiar_componentes(self):
        self._interfaz.ventanas.limpiar_componentes(['tbx_comentarios', 'tvw_detalle'])

    def _buscar_nuevos_registros(self):
            # Usa la fecha seleccionada si existe; si no, hoy
        fecha = self._fecha_seleccionada()
        hoy = datetime.now().date() if not fecha else datetime.strptime(fecha, "%Y-%m-%d").date()
        # 1) Pedidos en logística impresos (4,13 + PrintedOn not null)
        number_orders = int(self.base_de_datos.fetchone(
            """
            SELECT COUNT(1)
            FROM docDocumentOrderCayal P
            INNER JOIN docDocument D ON P.OrderDocumentID = D.DocumentID
            WHERE P.StatusID IN (1,2,3)
              AND D.PrintedOn IS NOT NULL
              AND CAST(P.DeliveryPromise AS date) = CAST(? AS date)
            """,
            (hoy,)
        ) or 0)
        # 2) Transferencias confirmadas = 2
        number_transfer_payments = int(self.base_de_datos.fetchone(
            """
            SELECT COUNT(1)
            FROM docDocumentOrderCayal
            WHERE PaymentConfirmedID = 2
              AND CAST(DeliveryPromise AS date) = CAST(? AS date)
            """,
            (hoy,)
        ) or 0)
        # 3) Buckets de puntualidad (<=15, 16-30, >30)
        rows = self.base_de_datos.fetchall(
            """
              ;WITH Base AS (
                SELECT
                    P.OrderDocumentID,
                    ScheduledDT =
                        CAST(CAST(P.DeliveryPromise AS date) AS datetime)
                        + CAST(TRY_CONVERT(time(0), H.Value) AS datetime)
                FROM dbo.docDocumentOrderCayal AS P
                INNER JOIN dbo.OrderSchedulesCayal AS H
                    ON P.ScheduleID = H.ScheduleID
                WHERE CAST(P.DeliveryPromise AS date) = CAST(? AS date)
                  AND P.StatusID IN (2, 16, 17, 18)  -- panel logística; ajusta si aplica
                  AND TRY_CONVERT(time(0), H.Value) IS NOT NULL
            )
            SELECT
                SUM(CASE WHEN DATEDIFF(MINUTE, GETDATE(), ScheduledDT) <= 15 THEN 1 ELSE 0 END) AS RestLeq15,
                SUM(CASE WHEN DATEDIFF(MINUTE, GETDATE(), ScheduledDT) BETWEEN 16 AND 30 THEN 1 ELSE 0 END) AS Rest16to30,
                SUM(CASE WHEN DATEDIFF(MINUTE, GETDATE(), ScheduledDT) < -30 THEN 1 ELSE 0 END) AS LateGt30
            FROM Base;
            """,
            (hoy,)
        )
        if rows:
            row = rows[0]
            rest_leq15 = int(row.get('RestLeq15') or 0)  # <= 15 minutos restantes (incluye retrasos leves)
            rest_16_30 = int(row.get('Rest16to30') or 0)  # entre 16 y 30 min restantes
            late_gt30 = int(row.get('LateGt30') or 0)  # más de 30 min de retraso
        else:
            rest_leq15 = rest_16_30 = late_gt30 = 0
        # Disparar refresco si cambió cualquiera
        if (
                self._number_orders != number_orders
                or self._number_transfer_payments != number_transfer_payments
                or self._count_rest_leq15 != rest_leq15
                or self._count_rest_16_30 != rest_16_30
                or self._count_late_gt30 != late_gt30
        ):
            self._limpiar_componentes()
            self._actualizar_pedidos(self._fecha_seleccionada())
            # Actualizar contadores internos
            self._number_orders = number_orders
            self._number_transfer_payments = number_transfer_payments
            self._count_rest_leq15 = rest_leq15
            self._count_rest_16_30 = rest_16_30
            self._count_late_gt30 = late_gt30

    def _actualizar_comentario_pedido(self):
        self._limpiar_componentes()
        fila = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)
        if not fila:
            return
        if len(fila) > 1:
            return

        comentario = fila[0]['Comentarios']
        comentario = comentario.strip().upper() if comentario else ''
        comentario = f"{fila[0]['Pedido']}-->{comentario}"
        self._interfaz.ventanas.insertar_input_componente('tbx_comentarios', comentario)
        self._interfaz.ventanas.bloquear_componente('tbx_comentarios')

    def _fecha_seleccionada(self):

        fecha = self._interfaz.ventanas.obtener_input_componente('den_fecha')
        return str(fecha) if fecha else None

    def _crear_tabla_pedidos(self):
        ancho, alto = self._interfaz.ventanas.obtener_resolucion_pantalla()

        frame = self._interfaz.ventanas.componentes_forma['frame_captura']
        colors = self._interfaz.master.style.colors
        componente = Tableview(
            master=frame,
            coldata=self._interfaz.crear_columnas_tabla(),
            rowdata=self._modelo.utilerias.diccionarios_a_tuplas(None),
            paginated=True,
            searchable=True,
            bootstyle=PRIMARY,
            pagesize=19 if ancho  <= 1367 else 24,
            stripecolor=None,  # (colors.light, None),
            height=19 if ancho  <= 1367 else 24,
            autofit=False,
            callbacks=[self._colorear_filas_panel_horarios],
            callbacks_search = [self._buscar_pedidos_cliente_sin_fecha]

        )

        self._interfaz.ventanas.componentes_forma['tbv_pedidos'] = componente
        componente.grid(row=0, column=0, pady=5, padx=5, sticky=tk.NSEW)

        #self._interfaz.ventanas.agregar_callback_table_view_al_actualizar('tbv_pedidos', self._colorear_filas_panel_horarios)



    def _colorear_filas_panel_horarios(self, actualizar_meters=None):
        """
        Colorea las filas de la tabla según la fase de producción (`StatusID`) y los tiempos estimados.
        También tiene en cuenta la fecha y hora de captura. Si `actualizar_meters` es True, solo actualiza
        los contadores sin modificar los colores en la tabla.
        """
        if not self._fecha_seleccionada():
            return

        if self._coloreando:
            return  # Evita ejecuciones simultáneas

        self._coloreando = True
        ahora = datetime.now()

        # Obtener filas a procesar
        filas = self._modelo.consulta_pedidos if actualizar_meters else \
            self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', visibles=True)

        # Reiniciar contadores si estamos actualizando meters
        if actualizar_meters:
            self._modelo.pedidos_retrasados = 0
            self._modelo.pedidos_en_tiempo = 0
            self._modelo.pedidos_a_tiempo = 0

        if not filas:
            self._coloreando = False
            return

        # Definir colores
        colores = {
                1: 'green',  # Pedido a tiempo o programado para otro día
                2: 'orange',  # Pedido próximo a la entrega (tiempo intermedio)
                3: 'red',  # Urgente o con muy poco tiempo para entrega / cancelado
                4: 'blue',  # Entregado o en ruta con poco tiempo para entrega
                5: 'purple',  # Pago pendiente por confirmar
                6: 'lightgreen',  # Transferencia confirmada
                7: 'lightblue'  # En ruta, entregado o en cartera
            }

        for i, fila in enumerate(filas):
            valores_fila = {
                'PriorityID': fila['PriorityID'],
                'Cancelled': fila['Cancelado'],
                'FechaEntrega': fila['FechaEntrega'] if actualizar_meters else fila['F.Entrega'],
                'HoraEntrega': fila['HoraCaptura'] if actualizar_meters else fila['H.Entrega'],
                'StatusID': fila['TypeStatusID'],
                'OrderDeliveryTypeID': fila['OrderDeliveryTypeID'],
                'PaymentConfirmedID': fila['PaymentConfirmedID']

            }
            status_pedido = self.utilerias.determinar_color_fila_respecto_entrega_pedido(valores_fila, ahora)

            color = colores[status_pedido]

            if actualizar_meters:
                if status_pedido in (1, 4):
                    self._modelo.pedidos_en_tiempo += 1
                elif status_pedido == 2:
                    self._modelo.pedidos_a_tiempo += 1
                elif status_pedido == 3:
                    self._modelo.pedidos_retrasados += 1
            else:
                self._interfaz.ventanas.colorear_filas_table_view('tbv_pedidos', [i], color)

        if actualizar_meters:
            self._rellenar_meters()

        self._coloreando = False

    def _obtener_valores_cbx_filtros(self):
        # Obtener valores actuales de los filtros
        vlr_cbx_captura = self._interfaz.ventanas.obtener_input_componente('cbx_capturista')
        vlr_cbx_horarios = self._interfaz.ventanas.obtener_input_componente('cbx_horarios')
        vlr_cbx_status = self._interfaz.ventanas.obtener_input_componente('cbx_status')

        return {'cbx_capturista': vlr_cbx_captura, 'cbx_horarios':vlr_cbx_horarios, 'cbx_status':vlr_cbx_status}

    def _settear_valores_cbx_filtros(self, valores_cbx_filtros):
        vlr_cbx_captura = valores_cbx_filtros['cbx_capturista']
        vlr_cbx_horarios =  valores_cbx_filtros['cbx_horarios']
        vlr_cbx_status =  valores_cbx_filtros['cbx_status']

        # Aplicar filtros solo si el usuario ha seleccionado un valor específico
        if vlr_cbx_captura != 'Seleccione':
            self._interfaz.ventanas.insertar_input_componente('cbx_capturista', vlr_cbx_captura)

        if vlr_cbx_horarios != 'Seleccione':
            self._interfaz.ventanas.insertar_input_componente('cbx_horarios', vlr_cbx_horarios)

        if vlr_cbx_status != 'Seleccione':
            self._interfaz.ventanas.insertar_input_componente('cbx_status', vlr_cbx_status)

    def _actualizar_pedidos(self, fecha=None, criteria=True, refresh=False, despues_de_capturar_pedido=False):
        if self._actualizando_tabla:
            return

        try:
            self._actualizando_tabla = True

            # 1) Limpia filtros visuales si lo pides
            self._interfaz.ventanas.limpiar_filtros_table_view('tbv_pedidos', criteria)

            # 2) Reconsulta si hay refresh, cambiaste fecha o no hay caché
            if refresh or (fecha is not None) or not getattr(self._modelo, 'consulta_pedidos', None):
                consulta = self._modelo.buscar_pedidos(fecha)
                self._modelo.consulta_pedidos = consulta
            else:
                consulta = self._modelo.consulta_pedidos

            if not consulta:
                self._limpiar_tabla()
                return

            # 3) Guarda selección actual del usuario (antes de repoblar combos)
            seleccion_previa = self._obtener_valores_cbx_filtros()

            # 4) Construye opciones de filtros desde la data FRESCA y repuebla combos
            #    - limpia None, strip y de-duplica
            def _norm_set(iterable):
                vistos, res = set(), []
                for v in iterable:
                    if v is None:
                        continue
                    s = str(v).strip()
                    if s and s not in vistos:
                        vistos.add(s)
                        res.append(s)
                return sorted(res)

            capturistas = _norm_set(f['CapturadoPor'] for f in consulta)
            horarios = _norm_set(f['HoraEntrega'] for f in consulta)
            status = _norm_set(f['Status'] for f in consulta)

            # repoblar (usa tu Ventanas.rellenar_cbx(nombre_cbx, valores, sin_seleccione=None))
            self._rellenar_cbx_captura(capturistas)
            self._rellenar_cbx_horarios(horarios)
            self._rellenar_cbx_status(status)

            # 5) Restaura selección previa o aplica "prefiltro post-captura"
            print(self._capturando_nuevo_pedido)
            if self._capturando_nuevo_pedido:
                # capturista = yo
                self._interfaz.ventanas.insertar_input_componente('cbx_capturista', self._user_name)

                # status = alguna variante de "abierto" si existe
                abiertos_posibles = {'abierto', 'abierta', 'open'}
                candidato_abierto = next((s for s in status if s.strip().lower() in abiertos_posibles), None)
                self._interfaz.ventanas.insertar_input_componente('cbx_status', candidato_abierto or 'Seleccione')

                # horario = 'Seleccione'
                self._interfaz.ventanas.insertar_input_componente('cbx_horarios', 'Seleccione')
                print('aqui debieramos filtrar abierto')
                self._capturando_nuevo_pedido = False
            else:
                # restaura selección previa usando tu setter robusto
                print('aqui no filtramos abiertos')
                self._interfaz.ventanas.insertar_input_componente('cbx_capturista',
                                                                  seleccion_previa.get('cbx_capturista', 'Seleccione'))
                self._interfaz.ventanas.insertar_input_componente('cbx_horarios',
                                                                  seleccion_previa.get('cbx_horarios', 'Seleccione'))
                self._interfaz.ventanas.insertar_input_componente('cbx_status',
                                                                  seleccion_previa.get('cbx_status', 'Seleccione'))

            # 6) Aplica filtros según lo que haya en los combos AHORA
            valores = self._obtener_valores_cbx_filtros()
            consulta_filtrada = self._filtrar_consulta_sin_rellenar(
                consulta, valores, despues_de_captura=despues_de_capturar_pedido
            )

            # 7) Pinta la tabla
            self._interfaz.ventanas.rellenar_table_view(
                'tbv_pedidos',
                self._interfaz.crear_columnas_tabla(),
                consulta_filtrada
            )

            self._colorear_filas_panel_horarios(actualizar_meters=True)

        finally:
            self._actualizando_tabla = False

    def _filtrar_consulta_sin_rellenar(self, consulta, valores, despues_de_captura=False):
        """Filtra en una sola pasada; NO toca combos."""
        # Prioridad: "sin procesar"
        if self._interfaz.ventanas.obtener_input_componente('chk_sin_procesar') == 1:
            self._interfaz.ventanas.limpiar_componentes('den_fecha')
            return self._modelo.buscar_pedidos_sin_procesar()

        if despues_de_captura:
            usuario = self._user_name
            return [f for f in consulta
                    if f.get('CapturadoPor') == usuario and f.get('Status') == 'Abierto']

        # Filtros normales desde combos
        vlr_cbx_captura = valores.get('cbx_capturista')
        vlr_cbx_horarios = valores.get('cbx_horarios')
        vlr_cbx_status = valores.get('cbx_status')

        # Predicados solo si el usuario eligió algo distinto a 'Seleccione'
        filtrar_captura = (vlr_cbx_captura and vlr_cbx_captura != 'Seleccione')
        filtrar_horario = (vlr_cbx_horarios and vlr_cbx_horarios != 'Seleccione')
        filtrar_status = (vlr_cbx_status and vlr_cbx_status != 'Seleccione')

        if not (filtrar_captura or filtrar_horario or filtrar_status):
            return consulta

        def ok(f):
            if filtrar_captura and f.get('CapturadoPor') != vlr_cbx_captura:
                return False
            if filtrar_horario and f.get('HoraEntrega') != vlr_cbx_horarios:
                return False
            if filtrar_status and f.get('Status') != vlr_cbx_status:
                return False
            return True

        return [f for f in consulta if ok(f)]

    def _filtrar_consulta(self, consulta, valores_cbx_filtros):
        # Si el checkbox está activado, solo devolver los pedidos sin procesar
        if self._interfaz.ventanas.obtener_input_componente('chk_sin_procesar') == 1:
            self._interfaz.ventanas.limpiar_componentes('den_fecha')
            return self._modelo.buscar_pedidos_sin_procesar()

        vlr_cbx_captura = valores_cbx_filtros['cbx_capturista']
        vlr_cbx_horarios = valores_cbx_filtros['cbx_horarios']
        vlr_cbx_status = valores_cbx_filtros['cbx_status']

        # Extraer valores únicos de los campos para actualizar los filtros
        capturistas = {fila['CapturadoPor'] for fila in consulta}
        horarios = {fila['HoraEntrega'] for fila in consulta}
        status = {fila['Status'] for fila in consulta}

        self._rellenar_cbx_status(status)
        self._rellenar_cbx_horarios(horarios)
        self._rellenar_cbx_captura(capturistas)

        # Aplicar filtros solo si el usuario ha seleccionado un valor específico
        if vlr_cbx_captura and vlr_cbx_captura != 'Seleccione':
            consulta = [fila for fila in consulta if fila['CapturadoPor'] == vlr_cbx_captura]

        if vlr_cbx_horarios and vlr_cbx_horarios != 'Seleccione':
            consulta = [fila for fila in consulta if fila['HoraEntrega'] == vlr_cbx_horarios]

        if vlr_cbx_status and vlr_cbx_status != 'Seleccione':
            consulta = [fila for fila in consulta if fila['Status'] == vlr_cbx_status]

        return consulta

    def _limpiar_tabla(self):
        """Limpia la tabla y restablece los contadores de métricas"""
        tabla = self._interfaz.ventanas.componentes_forma['tbv_pedidos']
        for campo in ['mtr_total', 'mtr_en_tiempo', 'mtr_a_tiempo', 'mtr_retrasado']:
            self._interfaz.ventanas.insertar_input_componente(campo, (1, 0))
        tabla.delete_rows()



    def _capturar_nuevo_pedido(self):
        self._pausar_autorefresco()

        try:
            self._capturando_nuevo_pedido = True
            self._master.iconify()

            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(
                ocultar_master=True,
                master=self._interfaz.master
            )

            self.parametros.id_principal = -1

            # empaquetar ofertas del cliente
            ofertas = {
                'consulta_productos_ofertados': self._modelo.consulta_productos_ofertados,
                'consulta_productos_ofertados_btn': self._modelo.consulta_productos_ofertados_btn,
                'products_ids_ofertados': self._modelo.products_ids_ofertados
            }

            _ = BuscarGeneralesCliente(ventana, self.parametros, ofertas)


        finally:
            self.parametros.id_principal = 0

            # 👉 aquí SIEMPRE entras al cerrar captura (ver ajuste en BuscarGenerales abajo)
            self._actualizar_pedidos(
                fecha=self._fecha_seleccionada(),
                refresh=True,
                despues_de_capturar_pedido=True
            )
            self._reanudar_autorefresco()

    def _editar_pedido(self):

        fila = self._validar_seleccion_una_fila()
        if not fila:
            self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar un pedido.')
            return

        status_id = fila['TypeStatusID']
        order_document_id = fila['OrderDocumentID']

        self._pausar_autorefresco()
        try:
            if status_id < 3:
                # ⚠️ NO crear ventana aquí: LlamarInstanciaCaptura la crea internamente
                cliente = Cliente()
                documento = Documento()
                self.parametros.id_principal = order_document_id

                instancia = LlamarInstanciaCaptura(
                    cliente,
                    documento,
                    self.base_de_datos,
                    self.parametros,
                    self.utilerias,
                    None  # ← evita doble ventana: no pases un Toplevel existente
                )
                # si LlamarInstanciaCaptura expone una ventana y quieres modal, podrías:
                # if hasattr(instancia, "master") and instancia.master:
                #     instancia.master.wait_window()

            elif status_id == 3:
                # Aquí sí creas el Toplevel y lo haces modal
                ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
                instancia = EditarPedido(ventana, self.base_de_datos, self.utilerias, self.parametros, fila)
                ventana.wait_window()

            else:  # status_id > 3
                self._interfaz.ventanas.mostrar_mensaje(
                    'No se pueden editar en este módulo documentos que no estén en status Por Timbrar.'
                )
        finally:
            self._actualizar_totales_pedido(order_document_id)
            self._actualizar_pedidos(self._fecha_seleccionada())
            self._reanudar_autorefresco()




    def _rellenar_cbx_captura(self, valores):
        valores = sorted(list(set(valores)))
        self._interfaz.ventanas.rellenar_cbx('cbx_capturista', valores)

    def _rellenar_cbx_status(self, valores):
        valores = sorted(list(set(valores)))
        self._interfaz.ventanas.rellenar_cbx('cbx_status', valores)

    def _rellenar_cbx_horarios(self, valores):
        valores = sorted(list(set(valores)))
        self._interfaz.ventanas.rellenar_cbx('cbx_horarios', valores)

    def _rellenar_meters(self):

        pedidos_entrega = len(self._modelo.consulta_pedidos)
        if pedidos_entrega == 0:
            self._interfaz.ventanas.insertar_input_componente('mtr_total', (1, pedidos_entrega))
            self._interfaz.ventanas.insertar_input_componente('mtr_en_tiempo', (1, pedidos_entrega))
            self._interfaz.ventanas.insertar_input_componente('mtr_a_tiempo', (1, pedidos_entrega))
            self._interfaz.ventanas.insertar_input_componente('mtr_retrasado', (1, pedidos_entrega))
            return

        self._interfaz.ventanas.insertar_input_componente('mtr_total', (pedidos_entrega, pedidos_entrega))
        self._interfaz.ventanas.insertar_input_componente('mtr_en_tiempo',
                                                          (pedidos_entrega, self._modelo.pedidos_en_tiempo))
        self._interfaz.ventanas.insertar_input_componente('mtr_a_tiempo',
                                                          (pedidos_entrega, self._modelo.pedidos_a_tiempo))
        self._interfaz.ventanas.insertar_input_componente('mtr_retrasado',
                                                          (pedidos_entrega, self._modelo.pedidos_retrasados))

        en_tiempo = f">={self._modelo.valor_en_tiempo}min."
        a_tiempo = f">={self._modelo.valor_a_tiempo}min."
        retrasado = f"<{self._modelo.valor_a_tiempo}min."

        self._interfaz.ventanas.actualizar_etiqueta_meter('mtr_en_tiempo', en_tiempo)
        self._interfaz.ventanas.actualizar_etiqueta_meter('mtr_a_tiempo', a_tiempo)
        self._interfaz.ventanas.actualizar_etiqueta_meter('mtr_retrasado', retrasado)

    def _seleccionar_una_fila(self):
        fila = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)
        if not fila:
            return
        if len(fila) > 1:
            return
        return fila

    def _rellenar_tabla_detalle(self):
        fila = self._seleccionar_una_fila()
        if not fila:
            return

        order_document_id = fila[0]['OrderDocumentID']
        partidas = self._modelo.buscar_partidas_pedido(order_document_id)
        partidas_procesadas = self._procesar_partidas_pedido(partidas)

        self._interfaz.ventanas.limpiar_componentes(['tvw_detalle'])

        for partida in partidas_procesadas:
            self._interfaz.ventanas.insertar_fila_treeview('tvw_detalle', partida)

        self._colorear_partidas_detalle()

    def _colorear_partidas_detalle(self):
        filas = self._interfaz.ventanas.obtener_filas_treeview('tvw_detalle')
        if not filas:
            return

        for fila in filas:
            valores_fila = self._interfaz.ventanas.procesar_fila_treeview('tvw_detalle', fila)

            estado_produccion_modificado = valores_fila['ItemProductionStatusModified']
            if estado_produccion_modificado == 0:
                continue

            # fila borrada
            if estado_produccion_modificado == 3:
                self._interfaz.ventanas.colorear_fila_seleccionada_treeview('tvw_detalle', fila, color='danger')

            # fila agregada
            if estado_produccion_modificado == 1:
                self._interfaz.ventanas.colorear_fila_seleccionada_treeview('tvw_detalle', fila, color='info')

            # fila editada
            if estado_produccion_modificado == 2:
                self._interfaz.ventanas.colorear_fila_seleccionada_treeview('tvw_detalle', fila,
                                                                            color='warning')

    def _procesar_partidas_pedido(self, partidas):
        if not partidas:
            return
        consulta_partidas_con_impuestos = self._modelo.utilerias.agregar_impuestos_productos(partidas)

        partidas_procesadas = []
        for producto in consulta_partidas_con_impuestos:
            precio_con_impuestos = producto['SalePriceWithTaxes']
            cantidad_decimal = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(producto['Quantity'])
            total = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(precio_con_impuestos * cantidad_decimal)
            product_id = producto['ProductID']

            if product_id == 5606:
                continue
            comentario = producto.get('Comments', '')
            comentario = '' if not comentario else comentario
            comentario =  comentario.strip()

            datos_fila = (
                cantidad_decimal,
                producto['ProductKey'],
                producto['ProductName'],
                precio_con_impuestos,
                total,
                producto['Esp'],
                producto['ProductID'],
                producto['DocumentItemID'],
                producto['ItemProductionStatusModified'],
                producto['ClaveUnidad'],
                0,  # status surtido
                producto['UnitPrice'],
                producto['CayalPiece'],
                producto['CayalAmount'],
                comentario,
                producto['ProductTypeIDCayal']
            )
            partidas_procesadas.append(datos_fila)
        return partidas_procesadas

    def _filtrar_por_capturados_por(self):

        self._limpiar_componentes()
        self._actualizar_pedidos(self._fecha_seleccionada())

    def _filtrar_por_status(self):

        self._limpiar_componentes()
        self._actualizar_pedidos(self._fecha_seleccionada())

    def _filtrar_por_horas(self):

        self._limpiar_componentes()
        self._actualizar_pedidos(self._fecha_seleccionada())









    def _actualizar_totales_pedido(self, order_document_id, sin_servicio_domicilio=True):
        consulta_partidas = self._modelo.base_de_datos.buscar_partidas_pedidos_produccion_cayal(
            order_document_id, partidas_producidas=True)

        consulta_partidas_con_impuestos = self._modelo.utilerias.agregar_impuestos_productos(consulta_partidas)
        subtotal = 0
        total_tax = 0
        totales = 0

        for producto in consulta_partidas_con_impuestos:
            precio = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(producto['UnitPrice'])
            precio_con_impuestos = producto['SalePriceWithTaxes']
            cantidad_decimal = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(producto['Quantity'])
            total = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(precio_con_impuestos * cantidad_decimal)
            product_id = producto['ProductID']

            if int(product_id) == 5606 and sin_servicio_domicilio:
                continue

            subtotal += (precio * cantidad_decimal)
            total_tax += (precio_con_impuestos - precio)
            totales += total

        self.base_de_datos.command(
            'UPDATE docDocumentOrderCayal SET SubTotal = ?, Total = ?, TotalTax = ? WHERE OrderDocumentID = ?',
            (subtotal, totales, total_tax, order_document_id)
        )





    def _sin_fecha(self):

        valor_chk_fecha = self._interfaz.ventanas.obtener_input_componente('chk_sin_fecha')

        if valor_chk_fecha == 1:

            self._interfaz.ventanas.cambiar_estado_checkbutton('chk_sin_procesar', 'deseleccionado')

            date_entry = self._interfaz.ventanas.componentes_forma['den_fecha']
            date_entry.entry.delete(first=0, last=tk.END)
        else:
            self._interfaz.ventanas.insertar_input_componente('den_fecha', self._modelo.hoy)

    def _buscar_ofertas(self):
        if not self._modelo.consulta_productos_ofertados:
            self._modelo.buscar_productos_ofertados_cliente()


    def _crear_notebook_herramientas(self):
        info_pestanas = {
            # Texto de la pestaña con emoji de dirección fiscal
            'tab_generales': ('Generales', None),
            'tab_captura': ('Captura', None),
            'tab_timbrado': ('Timbrado', None),
        }

        nombre_notebook = 'nbk_herramientas'
        notebook = self._interfaz.ventanas.crear_notebook(
            nombre_notebook=nombre_notebook,
            info_pestanas=info_pestanas,
            nombre_frame_padre='frame_herramientas',
            config_notebook={
                'row': 0,
                'column': 0,
                'sticky': tk.NSEW,
                'padx': 5,
                'pady': 5,
                'bootstyle': 'primary',
            }
        )

        # Crear frames base para cada pestaña
        frames_tabs = {}
        for clave, valor in info_pestanas.items():
            tab_name = clave  # p.ej. 'tab_direccion_fiscal'
            frame_name = clave.replace('tab_', 'frm_')  # 'frm_direccion_fiscal'
            frames_tabs[frame_name] = (
                tab_name,
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            )

        self._interfaz.ventanas.crear_frames(frames_tabs)

        # cada frame será el master de las subsecuentes ventanas
        for frame_name, (tab_name, configuracion, posicion) in frames_tabs.items():
            frame = self._interfaz.ventanas.componentes_forma[frame_name]
            if 'generales' in frame_name:
                HerramientasGenerales(
                            frame,
                            self._modelo,
                            self._interfaz
                )

            if 'captura' in frame_name:
                HerramientasCaptura(frame)

            if 'timbrado' in frame_name:
                HerramientasTimbrado(frame)





