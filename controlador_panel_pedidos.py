import os
import platform
import re
import tempfile
import tkinter as tk
from datetime import datetime
from buscar_pedido import BuscarPedido
from cayal.login import Login
from buscar_generales_cliente import BuscarGeneralesCliente
from capturado_vs_producido import CapturadoVsProducido

from cliente.notebook_cliente import NoteBookCliente

from editar_caracteristicas_pedido import EditarCaracteristicasPedido
from cayal.cobros import Cobros

from generador_ticket_produccion import GeneradorTicketProduccion
from historial_pedido import HistorialPedido
from horario_acumulado import HorarioslAcumulados
from llamar_instancia_captura import LlamarInstanciaCaptura
from ticket_pedido_cliente import TicketPedidoCliente
from selector_tipo_documento import SelectorTipoDocumento
from ttkbootstrap.constants import *
from cayal.tableview_cayal import Tableview
from editar_pedido import EditarPedido
from cayal.cliente import Cliente
from cayal.documento import Documento
from buscar_generales_cliente_cartera import BuscarGeneralesCliente
from buscar_clientes import BuscarClientes
from cancelar_pedido import CancelarPedido


class ControladorPanelPedidos:
    def __init__(self, modelo):
        self._modelo = modelo
        self._interfaz = modelo.interfaz
        self._master = self._interfaz.master
        self._base_de_datos = self._modelo.base_de_datos
        self._utilerias = self._modelo.utilerias
        self._parametros = self._modelo.parametros
        self._cobros = Cobros(self._parametros.cadena_conexion)
        self._ticket = GeneradorTicketProduccion(32)
        self._ticket.ruta_archivo = self._obtener_directorio_reportes()

        self._actualizando_tabla = False
        self._number_orders = 0

        self._coloreando = False
        self._user_id = self._parametros.id_usuario
        self._user_name = self._base_de_datos.buscar_nombre_de_usuario(self._user_id)
        self._parametros.nombre_usuario = self._user_name
        self._partidas_pedidos = {}
        self._capturando_nuevo_pedido = False

        self._crear_tabla_pedidos()
        self._actualizar_pedidos(self._fecha_seleccionada())
        self._crear_barra_herramientas()

        self._cargar_eventos()
        self._rellenar_operador()
        self._interfaz.ventanas.configurar_ventana_ttkbootstrap(titulo='Panel pedidos', bloquear=False)
        self._interfaz.ventanas.situar_ventana_arriba(self._interfaz.master)

        self._buscar_ofertas()

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

        evento_adicional2 = {
            'tbv_pedidos': (lambda event: self._pausar_autorefresco(), 'enfocar')
        }
        self._interfaz.ventanas.cargar_eventos(evento_adicional2)

        evento_adicional3 = {
            'tbv_pedidos': (lambda event: self._reanudar_autorefresco(), 'desenfocar')
        }
        self._interfaz.ventanas.cargar_eventos(evento_adicional3)

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
        number_orders = int(self._base_de_datos.fetchone(
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
        number_transfer_payments = int(self._base_de_datos.fetchone(
            """
            SELECT COUNT(1)
            FROM docDocumentOrderCayal
            WHERE PaymentConfirmedID = 2
              AND CAST(DeliveryPromise AS date) = CAST(? AS date)
            """,
            (hoy,)
        ) or 0)
        # 3) Buckets de puntualidad (<=15, 16-30, >30)
        rows = self._base_de_datos.fetchall(
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
            rowdata=self._utilerias.diccionarios_a_tuplas(None),
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

    def _obtener_directorio_reportes(self):

        sistema = platform.system()

        if sistema == "Windows":
            directorio = os.path.join(os.getenv("USERPROFILE"), "Documents")

        elif sistema in ["Darwin", "Linux"]:  # macOS y Linux
            directorio = os.path.join(os.getenv("HOME"), "Documents")

        else:
            directorio = tempfile.gettempdir()  # como último recurso

        if not os.path.exists(directorio):
            os.makedirs(directorio)

        return directorio

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
            status_pedido = self._utilerias.determinar_color_fila_respecto_entrega_pedido(valores_fila, ahora)

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

    def _capturar_nuevo_cliente(self):
        self._pausar_autorefresco()
        try:
            self._parametros.id_principal = 11135
            self._interfaz.master.iconify()

            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
            NoteBookCliente(ventana,
                            self._base_de_datos,
                            self._parametros,
                            self._utilerias
                            )
            ventana.wait_window()

        finally:
            self._parametros.id_principal = 0
            self._reanudar_autorefresco()

    def _capturar_nuevo_pedido(self):
        self._pausar_autorefresco()

        try:
            self._capturando_nuevo_pedido = True
            self._master.iconify()

            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(
                ocultar_master=True,
                master=self._interfaz.master
            )

            self._parametros.id_principal = -1

            # empaquetar ofertas del cliente
            ofertas = {
                'consulta_productos_ofertados': self._modelo.consulta_productos_ofertados,
                'consulta_productos_ofertados_btn': self._modelo.consulta_productos_ofertados_btn,
                'products_ids_ofertados': self._modelo.products_ids_ofertados
            }

            _ = BuscarGeneralesCliente(ventana, self._parametros, ofertas)


        finally:
            self._parametros.id_principal = 0

            # 👉 aquí SIEMPRE entras al cerrar captura (ver ajuste en BuscarGenerales abajo)
            self._actualizar_pedidos(
                fecha=self._fecha_seleccionada(),
                refresh=True,
                despues_de_capturar_pedido=True
            )
            self._reanudar_autorefresco()

    def _editar_caracteristicas(self):
        self._pausar_autorefresco()
        try:
            fila = self._seleccionar_una_fila()
            if not fila:
                return

            status = fila[0]['TypeStatusID']

            if status == 10:
                self._interfaz.ventanas.mostrar_mensaje('NO se pueden editar pedidos cancelados.')
                return

            elif status >= 4:
                self._interfaz.ventanas.mostrar_mensaje('Sólo se pueden afectar las caracteristicas de un pedido hasta el status  Por timbrar.')
                return
            else:
                order_document_id = fila[0]['OrderDocumentID']
                self._parametros.id_principal = order_document_id

                ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
                instancia = EditarCaracteristicasPedido(ventana, self._parametros, self._base_de_datos, self._utilerias)
                ventana.wait_window()

                self._parametros.id_principal = 0
                self._actualizar_pedidos(self._fecha_seleccionada())
        finally:
            self._reanudar_autorefresco()

    def _crear_ticket(self):
        self._pausar_autorefresco()
        try:
            fila = self._seleccionar_una_fila()
            if not fila:
                return

            order_document_id = fila[0]['OrderDocumentID']
            consulta = self._base_de_datos.fetchall("""
                SELECT
                 CASE WHEN DeliveryPromise IS NULL THEN 0 ELSE 1 END StatusEntrega,
                    DeliveryPromise FechaEntrega
                FROM docDocumentOrderCayal 
                WHERE OrderDocumentID = ?
                """,(order_document_id,))
            status_entrega = consulta[0]['StatusEntrega']


            if status_entrega == 0:
                self._interfaz.ventanas.mostrar_mensaje('Debe definir la forma de pago del cliente antes de generar el ticket.')
                return
            else:
                fecha_entrega = self._utilerias.convertir_fecha_str_a_datetime(str(consulta[0]['FechaEntrega'])[0:10])
                if fecha_entrega > self._modelo.hoy:
                    respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                        'EL pedido es para una fecha de entrega posterior, ¿Desea actualizar los precios antes de generar el ticket?')

                    if respuesta:
                        self._base_de_datos.actualizar_precios_pedido(order_document_id)

                self._parametros.id_principal = order_document_id
                instancia = TicketPedidoCliente(self._base_de_datos, self._utilerias, self._parametros)

                self._parametros.id_principal = 0
                self._interfaz.ventanas.mostrar_mensaje(master=self._interfaz.master,
                                                        mensaje='Comprobante generado.', tipo='info')
                self._interfaz.master.iconify()
        finally:
            self._reanudar_autorefresco()

    def _mandar_a_producir(self):

        filas = self._validar_seleccion_multiples_filas()
        if not filas:
            return

        for fila in filas:
            order_document_id = fila['OrderDocumentID']
            consulta = self._base_de_datos.fetchall("""
                SELECT StatusID, 
                    CASE WHEN DeliveryPromise IS NULL THEN 0 ELSE 1 END Entrega,
                    ISNULL(FolioPrefix,'')+ISNULL(Folio,'') DocFolio
                FROM docDocumentOrderCayal 
                WHERE OrderDocumentID = ?
            """,(order_document_id,))

            status = consulta[0]['StatusID']
            entrega = consulta[0]['Entrega']
            folio = consulta[0]['DocFolio']

            if entrega == 0:
                self._interfaz.ventanas.mostrar_mensaje(
                    f'Debe usar la herramienta de editar características para el pedido {folio}.')
                continue

            if status == 1:
                self._base_de_datos.command("""
                     UPDATE docDocumentOrderCayal SET SentToPrepare = GETDATE(),
                                                    SentToPrepareBy = ?,
                                                    StatusID = 2,
                                                    UserID = NULL
                    WHERE OrderDocumentID = ?
                """,(self._user_id, order_document_id,))

                comentario = f'Enviado a producir por {self._user_name}.'
                self._base_de_datos.insertar_registro_bitacora_pedidos(order_document_id=order_document_id,
                                                                       change_type_id=2,
                                                                       user_id=self._user_id,
                                                                       comments=comentario)

        self._actualizar_pedidos(self._fecha_seleccionada())

    def _cobrar_nota(self):
        self._pausar_autorefresco()
        try:
            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
            instancia = BuscarGeneralesCliente(ventana, self._parametros)
            ventana.wait_window()

            fila = self._seleccionar_una_fila()
            if not fila:
                return

        finally:
            self._reanudar_autorefresco()

    def _inciar_facturacion(self):
        self._pausar_autorefresco()
        try:
            self._facturar()
        finally:
            self._actualizar_pedidos(self._fecha_seleccionada())
            self._reanudar_autorefresco()

    def _facturar(self):

        filas = self._validar_seleccion_multiples_filas()

        if not filas:
            return

        filas_filtradas_por_status = self._filtrar_filas_facturables_por_status(filas)

        # filtra por status 3 que es por timbrar
        if not filas_filtradas_por_status:
            self._interfaz.ventanas.mostrar_mensaje('No hay pedidos con un status válido para facturar')
            return

        #--------------------------------------------------------------------------------------------------------------
        # aqui comenzamos el procesamiento de las filas a facturar
        # si es una seleccion unica valida primero si no hay otros pendientes del mimsmo cliente
        if len(filas) == 1:
            hay_pedidos_del_mismo_cliente = self._buscar_pedidos_en_proceso_del_mismo_cliente(filas)

            if not hay_pedidos_del_mismo_cliente:
                self._crear_documento(filas)

            if hay_pedidos_del_mismo_cliente:
                respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta('Hay otro pedido del mismo cliente en proceso o por timbrar.'
                                                                             '¿Desea continuar?')
                if respuesta:
                    self._crear_documento(filas)
            return

        # si hay mas de una fila primero valida que estas filas no tengan solo el mismo cliente
        # si lo tuvieran hay que ofrecer combinarlas en un documento
        tienen_el_mismo_cliente = self._validar_si_los_pedidos_son_del_mismo_cliente(filas)
        if tienen_el_mismo_cliente:
            respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta('Los pedidos son del mismo cliente.'
                                                                         '¿Desea combinarlos?')
            if respuesta:
                self._crear_documento(filas, combinado=True, mismo_cliente=True)
                return

        # del mismo modo que para una fila valida que no existan otras ordenes de un cliente en proceso
        # si lo hay para un cliente ese cliente debe excluirse de la seleccion
        filas_filtradas = self._excluir_pedidos_con_ordenes_en_proceso_del_mismo_cliente(filas)
        if not filas_filtradas:
            return

        self._crear_documento(filas_filtradas)
        self._actualizar_pedidos(self._fecha_seleccionada())
        return

    def _crear_documento(self, filas, combinado=False, mismo_cliente=False):

        tipo_documento = 1 # remision

        # determina el tipo de documento que se generará ya sea remision y/o factura
        if len(filas) > 1 and combinado:
            tipos_documento = list(set([fila['DocumentTypeID'] for fila in filas]))
            if len(tipos_documento) == 1:
                tipo_documento = tipos_documento[0]
            else:
                tipo_documento = -1
                while tipo_documento == -1:
                    ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
                    instancia = SelectorTipoDocumento(ventana)
                    ventana.wait_window()
                    tipo_documento = instancia.tipo_documento


        # cuantificamos el valor de todas las partidas involucradas excluyendo el servicio a domicilio
        # y determinamos si superan el valor 200

        filas_valorizadas = self._cuantificar_valor_partidas_documento(filas, mismo_cliente)
        if not filas_valorizadas:
            self._interfaz.ventanas.mostrar_mensaje('No hay ningún documento que generar.')
            return

        # aqui creamos el o los documentos pertinentes
        # si es un documento por cada orden no hay problema se toma el tipo desde la fila
        document_id = 0
        total_acumulado = 0
        partidas_acumuladas = []

        for fila in filas_valorizadas:
            order_document_id =  fila['OrderDocumentID']
            address_detail_id = fila['AddressDetailID']
            business_entity_id = fila['BusinessEntityID']
            ruta = fila['Ruta']

            info_documento = self._partidas_pedidos.get(order_document_id, None)
            if not info_documento:
                continue

            # info documento es una tupla donde el primer elemento es el total del documento y el segundo las partidas
            # en este punto los documentos valorizados ya estan filtrado despues de n validaciones
            total_documento = info_documento[0]
            partidas = info_documento[1]

            if not combinado:
                tipo_documento = fila['DocumentTypeID']

                document_id = self._crear_cabecera_documento(tipo_documento, fila)
                self._insertar_partidas_documento(order_document_id, document_id, partidas, total_documento, address_detail_id)

                # insertar comentarios desde el pedido
                self._crear_comentario_documento([order_document_id],
                                                 document_id,
                                                 business_entity_id,
                                                 total_documento,
                                                 ruta
                                                 )

                # relacionar documenrtosa con pedidos
                self._actualizar_status_y_relacionar(document_id, order_document_id)

                # agregar documento para recalculo
                self._base_de_datos.exec_stored_procedure('zvwRecalcularPedidos', (document_id, order_document_id))

                # afectar bitacora
                self._afectar_bitacora_de_cambios(document_id, [order_document_id])


            else:
                partidas_acumuladas.extend(partidas)
                total_acumulado += total_documento

        # proceso concluido si no fue combinado el documento
        if not combinado:
            return

        # aplica para documentos combinados
        all_order_document_ids = [fila['OrderDocumentID'] for fila in filas]
        order_document_ids = sorted([fila['OrderDocumentID'] for fila in filas if fila['OrderTypeID'] == 1], reverse=True)
        if not order_document_ids:
            self._interfaz.ventanas.mostrar_mensaje('Debe por lo menos haber un pedido dentro de las ordenes seleccionadas.')
            return

        order_document_id = order_document_ids[0]
        address_detail_id = filas[0]['AddressDetailID']
        business_entity_id = filas[0]['BusinessEntityID']

        # crea cabecera y bloqueala para evitar ediciones
        document_id = self._crear_cabecera_documento(tipo_documento, filas[0])


        self._insertar_partidas_documento(order_document_id, document_id, partidas_acumuladas, total_acumulado, address_detail_id)

        # insertar comentario de los pedidos
        self._crear_comentario_documento(all_order_document_ids,
                                         document_id,
                                         business_entity_id,
                                         total_acumulado,
                                         filas[0]['Ruta']
                                         )

        # relacionar pedidos con factura
        for order in all_order_document_ids:
            self._actualizar_status_y_relacionar(document_id, order)

        # relacionar pedido principal con pedidos
        for order in all_order_document_ids:
            if order != order_document_id:
                self._base_de_datos.command(
                    'UPDATE docDocumentOrderCayal SET RelatedOrderID = ?, StatusID=4 WHERE OrderDocumentID = ?',
                    (order_document_id, order)
                )

        # agregar documento para recalculo
        self._base_de_datos.exec_stored_procedure('zvwRecalcularPedidos', (document_id, order_document_id))

        # afectar la bitacora de cambios
        self._afectar_bitacora_de_cambios(document_id, all_order_document_ids)

    def _afectar_bitacora_de_cambios(self, document_id, order_document_ids):

        folio = self._base_de_datos.fetchone(
            "SELECT ISNULL(FolioPrefix,'')+ISNULL(Folio,'') DocFolio FROM docDocument WHERE DocumentID = ?",
            (document_id,))
        comentario = f"Documento creado por {self._user_name} - {folio}"

        for order_document_id in order_document_ids:
            self._base_de_datos.insertar_registro_bitacora_pedidos(order_document_id,
                                                                   change_type_id=4,
                                                                   comments=comentario,
                                                                   user_id=self._user_id)

            self._base_de_datos.command(
                """
                UPDATE docDocumentOrderCayal 
                SET 
                    SentToInvoice = CASE 
                        WHEN SentToInvoice IS NULL THEN GETDATE() 
                        ELSE SentToInvoice 
                    END,
                    SentToInvoiceBy = CASE 
                        WHEN SentToInvoiceBy > 0 THEN SentToInvoiceBy 
                        ELSE ? 
                    END
                WHERE OrderDocumentID = ?;
                """,
                (self._user_id, order_document_id)
            )

    def _actualizar_status_y_relacionar(self, document_id, order_document_id):
        self._base_de_datos.command(
            """
            DECLARE @DocumentID INT = ?
            DECLARE @OrderDocumentID INT  = ?

            -- Actualizar la tabla docDocumentOrderCayal
            UPDATE docDocumentOrderCayal
            SET StatusID = CASE WHEN StatusID = 3 AND OutputToDeliveryBy = 0 AND AssignedBy = 0 THEN 4 
                                WHEN StatusID = 3 AND OutputToDeliveryBy = 0 AND AssignedBy <> 0 THEN 7 
                                WHEN StatusID = 3 AND OutputToDeliveryBy <> 0 AND AssignedBy <> 0 THEN 13 
                            END,
                DocumentID = @DocumentID
            WHERE OrderDocumentID = @OrderDocumentID;

            -- Insertar en la tabla OrderInvoiceDocumentCayal
            INSERT INTO OrderInvoiceDocumentCayal (OrderDocumentID, DocumentID)
            VALUES (@OrderDocumentID, @DocumentID);
            
            """,
            (document_id, order_document_id)
        )

    def _insertar_partidas_documento(self, order_document_id, document_id, partidas, total_documento, address_detail_id):
        if total_documento < 200:
            order_delivery_type_id = self._base_de_datos.fetchone(
                'SELECT OrderDeliveryTypeID FROM docDocumentOrderCayal WHERE OrderDocumentID = ?',
                                         (order_document_id,))

            # si el cliente viene omite el servicio a domicilio
            if order_delivery_type_id == 1:
                self._insertar_servicio_a_docimicilio(document_id, address_detail_id)

        for partida in partidas:
            parametros = (
                document_id,
                partida['ProductID'],
                2,  # depot_id
                partida['Quantity'],
                partida['UnitPrice'],
                0,  # costo,
                partida['Subtotal'],
                partida['TipoCaptura'],  # tipo captura
                21,  # modulo
                partida['Comments']
            )
            self._base_de_datos.insertar_partida_documento_cayal(parametros)

    def _insertar_servicio_a_docimicilio(self, document_id, address_detail_id):
        precio_servicio = self._base_de_datos.fetchone(
            'SELECT * FROM [dbo].[zvwBuscarCargoEnvio-AddressDetailID](?)',
            (address_detail_id,))

        precio_servicio_sin_impuesto = self._utilerias.calcular_monto_sin_iva(precio_servicio)
        parametros = (
            document_id,
            5606,  # product_id
            2,  # depot_id
            1,
            precio_servicio_sin_impuesto,
            0,  # costo,
            precio_servicio_sin_impuesto,
            0,  # tipo captura
            21  # modulo
        )
        self._base_de_datos.insertar_partida_documento_cayal(parametros)

    def _crear_cabecera_documento(self, document_type_id, fila):
        # este valor hace que se inserte la configuracion del cliente que esta predeterminada
        way_to_pay_id = 0

        # solo si el documento es factura realiza la actualización de tipo de pago
        if document_type_id == 0:
            way_to_pay_id = self._actualizar_forma_de_pago_documento(info_documento=fila)

        document_id = self._base_de_datos.crear_documento(
            document_type_id,
            'FM', # prefijo mayoreo
            fila['BusinessEntityID'],
            21, # modulo facturas mayoreo
            fila['CaptureBy'], # valor de quien captura el pedido
            fila['DepotID'],
            fila['AddressDetailID'],
            self._user_id, # valor de quien crea el documento (envía a timbrar)
            way_to_pay_id
        )

        order_document_id = fila['OrderDocumentID']

        # este valor hace que para los doctos de mayoreo no sean recalculables
        self._base_de_datos.command('UPDATE docDocument SET ExportID = 6, OrderDocumentID = ? WHERE DocumentID = ?',
                                    (order_document_id, document_id))

        return document_id

    def _actualizar_forma_de_pago_documento(self, info_documento):

        # equivalencias de forma de pago de pedidos
        way_to_pay_cfd = {
            2: 1, # efectivo
            3: 28, # tdb
            4: 4, # tbc
            6: 3, # transferencia
            7: 2 # cheque
        }

        way_to_pay_id = int(info_documento['WayToPayID'])

        # si la forma de pago entra entre tdc,tdb, efectivo, transferencia o cheque, actualizala
        """
        1	Por Definir	El pago se definirá en el cobro
        2	Efectivo	Efectivo
        3	Tarjeta Debito	Llevar terminal
        4	Tarjeta Crédito	Llevar terminal
        5	Firma	Es a crédito
        6	Transferencia	Transferencia
        7	Cheque	Cheque
        8	No aplica	No cobrar 
        """
        if way_to_pay_id in (2,3,4,6,7):
            return way_to_pay_cfd[way_to_pay_id]

        return 0

    def _cuantificar_valor_partidas_documento(self, filas, mismo_cliente=False):
        # validar que el monto sea superior a 180 debito a que el cliente podria anexar un producto y con ello
        # evitar generar la factura correspondiente

        total_acumulado = 0
        filas_filtradas = []
        for fila in filas:
            order_document_id = fila['OrderDocumentID']
            total_documento = self._calcular_total_pedido(order_document_id)

            if total_documento < 200 and not mismo_cliente:
                cliente = fila['Cliente']
                pedido = fila['Pedido']

                respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(f'El total de la orden {pedido} del cliente {cliente} '
                                                                 f'es de {total_documento}, ¿Desea omitir este pedido del proceso para consultar con el cliente un posible incremento en su pedido?'
                                                                 )
                if respuesta:
                    continue

                filas_filtradas.append(fila)
                continue

            if mismo_cliente:
                total_acumulado += total_documento
                continue

            if total_documento >  199:
                filas_filtradas.append(fila)
                continue

        if mismo_cliente and total_acumulado < 200:
            cliente = filas[0]['Cliente']

            respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                f'El total acumulado de las ordenes seleccionadas del cliente {cliente}'
                f'es de {total_acumulado}, ¿Desea consultar con el cliente un posible incremento en su pedido?'
                )

            if respuesta:
                return []

            return filas

        if mismo_cliente and total_acumulado > 180:
            return filas

        return filas_filtradas

    def _calcular_total_pedido(self, order_document_id):

        consulta_partidas = self._modelo.base_de_datos.buscar_partidas_pedidos_produccion_cayal(
           order_document_id, partidas_producidas=True)

        consulta_partidas_con_impuestos = self._modelo.utilerias.agregar_impuestos_productos(consulta_partidas)
        subtotal = 0
        total_tax = 0
        totales = 0
        nuevas_partidas = []
        for producto in consulta_partidas_con_impuestos:
            precio = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(producto['UnitPrice'])
            precio_con_impuestos = producto['SalePriceWithTaxes']
            cantidad_decimal = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(producto['Quantity'])
            total = self._modelo.utilerias.redondear_valor_cantidad_a_decimal(precio_con_impuestos * cantidad_decimal)
            product_id = producto['ProductID']

            if product_id == 5606:
                continue

            subtotal += (precio * cantidad_decimal)
            total_tax += (precio_con_impuestos - precio)
            totales += total

            nuevas_partidas.append(producto)

        self._partidas_pedidos[order_document_id] = (totales, nuevas_partidas)

        return totales

    def _validar_si_los_pedidos_son_del_mismo_cliente(self, filas):
        business_entity_ids = []
        for fila in filas:
            business_entity_id = fila['BusinessEntityID']
            business_entity_ids.append(business_entity_id)

        business_entity_ids = list(set(business_entity_ids))
        if len(business_entity_ids) == 1:
            return True
        return False

    def _excluir_pedidos_con_ordenes_en_proceso_del_mismo_cliente(self, filas):


        filas_filtradas = []
        clientes_en_proceso = []
        order_document_ids = [filas[0]['OrderDocumentID']] # agrega el primer pedido a la lista para comparaciones
        for fila in filas:
            hay_pedidos_del_mismo_cliente_en_proceso = self._buscar_pedidos_en_proceso_del_mismo_cliente(fila)
            if not hay_pedidos_del_mismo_cliente_en_proceso:
                filas_filtradas.append(fila)
            else:
                order_document_id = fila['OrderDocumentID']
                if order_document_id not in order_document_ids:
                    clientes_en_proceso.append(fila['Cliente'])
        texto = ''
        if clientes_en_proceso:
            clientes_en_proceso = set(clientes_en_proceso)
            for cliente in clientes_en_proceso:
                texto = f'{texto} {cliente},'
            self._interfaz.ventanas.mostrar_mensaje(f'Los clientes: {texto} tienen más órdenes en proceso o por timbrar.')
        return filas_filtradas

    def _buscar_pedidos_en_proceso_del_mismo_cliente(self, fila):
        business_entity_id = fila[0]['BusinessEntityID'] if isinstance(fila, list) else fila['BusinessEntityID']
        order_document_id = fila[0]['OrderDocumentID'] if isinstance(fila, list) else fila['OrderDocumentID']

        pedidos_del_mismo_cliente = 0

        filas = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos')

        for fila in filas:
            business_entity_id_fila = fila['BusinessEntityID']
            order_document_id_fila = fila['OrderDocumentID']
            status_id = fila['TypeStatusID']

            if order_document_id_fila == order_document_id:
                continue
            if business_entity_id_fila == business_entity_id:
                if status_id in (2, 3, 16, 17, 18):
                    pedidos_del_mismo_cliente += 1
                    continue

        if pedidos_del_mismo_cliente > 0:
            return True

        return False

    def _filtrar_filas_facturables_por_status(self, filas):
        filas_filtradas = []

        # filtrar por status
        for fila in filas:
            status_id = fila['TypeStatusID']
            # pedido por timbrar es status 3
            if status_id < 3:
                continue

            filas_filtradas.append(fila)

        return filas_filtradas

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
                self._parametros.id_principal = order_document_id

                instancia = LlamarInstanciaCaptura(
                    cliente,
                    documento,
                    self._base_de_datos,
                    self._parametros,
                    self._utilerias,
                    None  # ← evita doble ventana: no pases un Toplevel existente
                )
                # si LlamarInstanciaCaptura expone una ventana y quieres modal, podrías:
                # if hasattr(instancia, "master") and instancia.master:
                #     instancia.master.wait_window()

            elif status_id == 3:
                # Aquí sí creas el Toplevel y lo haces modal
                ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
                instancia = EditarPedido(ventana, self._base_de_datos, self._utilerias, self._parametros, fila)
                ventana.wait_window()

            else:  # status_id > 3
                self._interfaz.ventanas.mostrar_mensaje(
                    'No se pueden editar en este módulo documentos que no estén en status Por Timbrar.'
                )
        finally:
            self._actualizar_totales_pedido(order_document_id)
            self._actualizar_pedidos(self._fecha_seleccionada())
            self._reanudar_autorefresco()

    def _buscar_pedido(self):
        self._pausar_autorefresco()
        try:
            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(titulo='Buscar pedido')
            instancia = BuscarPedido(ventana, self._base_de_datos, self._utilerias, self._parametros)
            ventana.wait_window()
        finally:
            self._parametros.id_principal = 0
            self._reanudar_autorefresco()

    def _capturado_vs_producido(self):
        self._pausar_autorefresco()
        try:
            fila = self._validar_seleccion_una_fila()
            if not fila:
                self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar un pedido.')
                return

            status_id = int(fila['TypeStatusID'])
            order_document_id = int(fila['OrderDocumentID'])

            if status_id in (2, 16, 17, 18):
                self._interfaz.ventanas.mostrar_mensaje('El pedido aún no se ha terminado de producir')
                return


            self._parametros.id_principal = order_document_id

            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(titulo='Capturado vs Producido')
            instancia = CapturadoVsProducido(ventana, self._parametros, self._base_de_datos, self._utilerias, fila)
            ventana.wait_window()
        finally:
            self._reanudar_autorefresco()
            self._parametros.id_principal = 0

    def _rellenar_operador(self):
        operador_panel = self._modelo.buscar_nombre_usuario_operador_panel(self._parametros.id_usuario)
        texto = f'PANEL: pedidos OPERADOR: {operador_panel}'
        self._interfaz.ventanas.actualizar_etiqueta_externa_tabla_view('tbv_pedidos', texto)
        self._user_id = self._parametros.id_usuario

    def _validar_seleccion_una_fila(self):
        if not self._interfaz.ventanas.validar_seleccion_una_fila_table_view('tbv_pedidos'):
            return

        return self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)[0]

    def _historial_pedido(self):
        try:
            valores_fila = self._validar_seleccion_una_fila()
            if not valores_fila:
                return

            order_document_id = valores_fila['OrderDocumentID']

            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(titulo='Historial pedido')
            self._parametros.id_principal = order_document_id
            instancia = HistorialPedido(ventana, self._parametros, self._base_de_datos)
            ventana.wait_window()
        finally:
            self._reanudar_autorefresco()
            self._parametros.id_principal = 0

    def _cambiar_usuario(self):

        def si_acceso_exitoso(parametros=None, master=None):
            self._parametros = parametros
            self._rellenar_operador()

        ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
        instancia = Login(ventana, self._parametros, si_acceso_exitoso)
        ventana.wait_window()

    def _buscar_clientes(self):
        self._pausar_autorefresco()
        try:
            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
            instancia = BuscarClientes(ventana, self._base_de_datos, self._parametros, self._utilerias)
            ventana.wait_window()
        finally:
            self._reanudar_autorefresco()

    def _crear_barra_herramientas(self):
        self.barra_herramientas_pedido = [

            {'nombre_icono': 'Partner32.ico', 'etiqueta': 'Clientes', 'nombre': 'buscar_cliente',
             'hotkey': None, 'comando': self._buscar_clientes},

            {'nombre_icono': 'Customer32.ico', 'etiqueta': 'Nuevo', 'nombre': 'nuevo_cliente',
             'hotkey': None, 'comando': self._capturar_nuevo_cliente},

            {'nombre_icono': 'HeaderFooter32.ico', 'etiqueta': 'Nuevo', 'nombre': 'capturar_nuevo',
             'hotkey': None, 'comando': self._capturar_nuevo_pedido},

            {'nombre_icono': 'EditBusinessEntity32.ico', 'etiqueta': 'E.Caracteristicas', 'nombre': 'editar_caracteristicas',
             'hotkey': '', 'comando': self._editar_caracteristicas},

            {'nombre_icono': 'DocumentGenerator32.ico', 'etiqueta': 'Ticket', 'nombre': 'crear_ticket',
             'hotkey': None, 'comando': self._crear_ticket},

            {'nombre_icono': 'Manufacture32.ico', 'etiqueta': 'M.Producir', 'nombre': 'mandar_producir',
             'hotkey': None, 'comando': self._mandar_a_producir},

            {'nombre_icono': 'Payments32.ico', 'etiqueta': 'C.Cartera.', 'nombre': 'cobrar_cartera',
             'hotkey': None, 'comando': self._cobrar_nota},

            {'nombre_icono': 'lista-de-verificacion.ico', 'etiqueta': 'Editar', 'nombre': 'editar',
             'hotkey': None, 'comando': self._editar_pedido},

            {'nombre_icono': 'Invoice32.ico', 'etiqueta': 'Facturar', 'nombre': 'facturar',
             'hotkey': None, 'comando': self._inciar_facturacion},

            {'nombre_icono': 'History21.ico', 'etiqueta': 'Historial', 'nombre': 'historial_pedido',
             'hotkey': None, 'comando': self._historial_pedido},

            {'nombre_icono': 'Cancelled32.ico', 'etiqueta': 'Cancelar', 'nombre': 'cancelar_pedido',
             'hotkey': None, 'comando': self._cancelar_pedido},

            {'nombre_icono': 'Organizer32.ico', 'etiqueta': 'A.Horarios', 'nombre': 'acumular_horarios',
             'hotkey': None, 'comando': self._acumular_horarios},

            {'nombre_icono': 'Printer21.ico', 'etiqueta': 'Imprimir', 'nombre': 'imprimir_pedido',
             'hotkey': None, 'comando': self._imprimir},

            {'nombre_icono': 'PrintSelectedItems.ico', 'etiqueta': 'Producido', 'nombre': 'capturado_vs_producido',
             'hotkey': None, 'comando': self._capturado_vs_producido},

            {'nombre_icono': 'OtrosIngresos32.ico', 'etiqueta': 'C.Transferencia', 'nombre': 'confirmar_transferencia',
             'hotkey': None, 'comando': self._confirmar_transferencia},

            {'nombre_icono': 'SwitchUser32.ico', 'etiqueta': 'C.Usuario', 'nombre': 'cambiar_usuario',
             'hotkey': None, 'comando': self._cambiar_usuario},

        ]

        self.elementos_barra_herramientas = self._interfaz.ventanas.crear_barra_herramientas(self.barra_herramientas_pedido,
                                                                                   'frame_herramientas')
        self.iconos_barra_herramientas = self.elementos_barra_herramientas[0]
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]

    def _confirmar_transferencia(self):
        filas = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos2', seleccionadas=True)
        if not filas:
            self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar un pedido.')
            return

        for fila in filas:
            order_document_id = fila['OrderDocumentID']
            payment_confirmend_id = fila['PaymentConfirmedID']

            if payment_confirmend_id == 1:
                self._interfaz.ventanas.mostrar_mensaje('El pedido seleccionado no es transferencia.')
                return

            if payment_confirmend_id == 3:
                self._interfaz.ventanas.mostrar_mensaje('La transferencia ha sido confirmada con anterioridad.')
                return

            self._modelo.confirmar_transferencia(self._user_id, order_document_id)
            comentario = f"Transferencia confirmada por {self._user_name}"
            self._modelo.afectar_bitacora(order_document_id, self._user_id, comentario)

    def _imprimir(self):
        self._pausar_autorefresco()
        try:
            filas = None
            seleccion_status = self._interfaz.ventanas.obtener_input_componente('cbx_status')
            if seleccion_status == 'En Proceso':
                respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                    '¿Desea imprimir todos los pedidos en el status en proceso, que faltan por imprimir?')
                if respuesta:
                    filas = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos')
                    filas = [
                        fila for fila in filas
                        if fila['TypeStatusID'] in (2, 16, 17, 18) and set(fila['PrintedStatus']) != set(
                            fila['TipoProduccion'])
                    ]
                else:
                    filas =  self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)
            else:
                filas = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)

            if not filas:
                self._interfaz.ventanas.mostrar_mensaje('No hay pedidos que imprimir')
                return

            for fila in filas:
                self._preparar_ticket_impresion(fila)
        finally:
            self._actualizar_pedidos(self._fecha_seleccionada())
            self._reanudar_autorefresco()

    def _preparar_ticket_impresion(self, fila):
        order_document_id = fila['OrderDocumentID']

        areas_imprimibles = set(self._base_de_datos.fetchone("""
                    SELECT PT.Value
                    FROM docDocumentOrderCayal P INNER JOIN
                        OrdersProductionTypesCayal PT ON P.ProductionTypeID = PT.ProductionTypesID
                    WHERE P.OrderDocumentID = ?
                """, (order_document_id,)))

        if len(areas_imprimibles) in (1, 2):
            self._ticket.parcial = True
        else:
            self._ticket.parcial = False

        for area in areas_imprimibles:

            imprimir = self._settear_valores_ticket(fila, order_document_id, area, areas_imprimibles)

            if not imprimir:

                continue

            self._ticket.imprimir(fuente_tamano=10, nombre_impresora="Ticket")
            self._afectar_bitacora_impresion(order_document_id)
            self._actualizar_tablas_impresion(order_document_id)

    def _settear_valores_ticket(self, pedido, order_document_id, areas_imprimibles, todas_las_areas):
        self._ticket.cliente = pedido.get('Cliente', '')
        self._ticket.pedido = pedido.get('Pedido', '')
        self._ticket.relacionado = pedido.get('Relacion', '')
        self._ticket.tipo = pedido.get('Tipo', '')

        fecha_captura = pedido.get('F.Captura', '')
        hora_captura = pedido.get('H.Captura', '')
        captura = f'{fecha_captura}-{hora_captura}'
        self._ticket.venta = captura

        fecha_entrega = pedido.get('F.Entrega', '')
        hora_entrega = pedido.get('H.Entrega', '')
        entrega = f'{fecha_entrega}-{hora_entrega}'
        self._ticket.entrega = entrega
        self._ticket.tipo_entrega = pedido.get('Entrega', '')

        self._ticket.capturista = pedido.get('Captura', '')
        self._ticket.ruta = pedido.get('Ruta')

        consulta = self._base_de_datos.fetchall(
            """
            SELECT Z.ZoneName, DT.City
            FROM docDocumentOrderCayal D INNER JOIN
                orgZone Z ON D.ZoneID = D.ZoneID INNER JOIN
                orgAddressDetail DT ON D.AddressDetailID = DT.AddressDetailID
            WHERE OrderDocumentID = ? AND D.ZoneID = Z.ZoneID
            """,
            (order_document_id,)
        )
        if consulta:
            valores = consulta[0]
            ruta = valores.get('ZoneName', '')
            ruta = self._utilerias.limitar_caracteres(ruta, 22)
            self._ticket.ruta = ruta

            colonia = valores.get('City', '')
            self._ticket.colonia = colonia

        consulta_partidas = self._base_de_datos.buscar_partidas_pedidos_produccion_cayal(
            order_document_id, partidas_eliminadas=False, partidas_producidas=True)

        partidas_filtradas_por_area = self._filtrar_partidas_por_area_impresion(consulta_partidas, areas_imprimibles, todas_las_areas)

        partidas_ticket = self._filtrar_partidas_ticket(partidas_filtradas_por_area)

        if not partidas_ticket:
            return False

        self._ticket.set_productos(partidas_ticket)

        return True

    def _filtrar_partidas_por_area_impresion(self, consulta_partidas, areas_imprimibles, todas_las_areas):

        partidas_sin_servicio_domicilio = [partida for partida in consulta_partidas if partida['ProductID'] != 5606]
        sin_partidas_eliminadas = [partida for partida in partidas_sin_servicio_domicilio
                                   if partida['ItemProductionStatusModified'] != 3]

        tipos_partida = {0: 'M', 1: 'P', 2: 'A'}

        partidas = []
        for partida in sin_partidas_eliminadas:
            product_type_id_cayal = partida.get('ProductTypeIDCayal', 1)
            if tipos_partida[product_type_id_cayal] in areas_imprimibles:
                partidas.append(partida)

        def generar_texto(conjunto):
            # Mapeo de letras a sus respectivos textos
            mapeo = {
                'P': 'Produccion',
                'M': 'Minisuper',
                'A': 'Almacen'
            }

            # Filtrar las letras válidas y generar el texto
            textos = [mapeo[letra] for letra in conjunto if letra in mapeo]
            return ', '.join(textos)

        self._ticket.areas = generar_texto(areas_imprimibles)
        self._ticket.areas_aplicables = generar_texto(todas_las_areas)
        return partidas

    def _filtrar_partidas_ticket(self, consulta_partidas):
        partidas = []

        for partida in consulta_partidas:

            cayal_piece = partida['CayalPiece']
            unidad_producto = partida['Unit']
            product_id = partida['ProductID']

            abreviatura_unidad = self._utilerias.abreviatura_unidad_producto(unidad_producto)

            # es un producto pesado con unidad pieza
            if cayal_piece != 0:

                # el texto experado en la partida si es por piezas es:
                # TOMATE
                # CANTIDAD: (1 Pz) 0.20 Kg

                # HUEVO (REJA)
                # CANTIDAD: (1 Rj) 30 Pz

                # CUERO
                # CANTIDAD: (1 Cj) 25 Kg

                unidad_especial = self._utilerias.equivalencias_productos_especiales(product_id)

                if unidad_especial:
                    unidad_especial = unidad_especial[0]

                if not unidad_especial:
                    unidad_especial = 'Pz' if cayal_piece == 1 else 'Pzs'

                cantidad_original = partida['Quantity']
                if unidad_especial:
                    partida['Quantity'] = f"({cayal_piece} {unidad_especial}) {cantidad_original} {abreviatura_unidad}"
                else:
                    partida['Quantity'] = f"({cayal_piece} {unidad_especial}) {cantidad_original}"

                abreviatura_unidad = ''

            producto = {
                'clave': partida['ProductKey'],
                'cantidad': partida['Quantity'],
                'descripcion': partida['ProductName'],
                'unidad': abreviatura_unidad,
                'observacion': partida['Comments']
            }
            partidas.append(producto)
        return partidas

    def _acumular_horarios(self):
        self._pausar_autorefresco()
        try:
            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(self._interfaz.master, 'Acumulados horarios')
            instancia = HorarioslAcumulados(ventana, self._base_de_datos, self._utilerias)
        finally:
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

    def _validar_seleccion_multiples_filas(self):
        # si imprimir en automatico esta desactivado la seleccion de filas solo aplica a la seleccion
        filas = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)

        if not filas:
            self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar por lo menos un pedido.')
            return

        return filas

    def _filtrar_comentario_documento(self, comentario):

        palabras_a_eliminar = [
            r'\bes un anexo\b',  # Nueva frase a eliminar
            r'\banexo\b', r'\banexos\b',
            r'\bllevar terminal\b',
            #r'\bviene\b',
            #r'\bes viene\b',
            r'\btransferencia\b', r'\btransf\b', r'\bestransferencia\b',
            r'\bcheque\b',
            r'\bfolio\b',
            r'\bllevar a\b',
            r'\bes folio\b',
            r'\bcredito\b',
            r'\bes credito\b',
        ]

        # Expresión regular para eliminar frases no deseadas
        patron_palabras = re.compile(r"(,?\s*)?(" + "|".join(palabras_a_eliminar) + r")(,?\s*)?", re.IGNORECASE)

        # Expresión regular para reemplazar múltiples guiones por un solo guion
        patron_guiones = re.compile(r'-{2,}')  # Busca "--", "---", etc.

        # Eliminar palabras/frases no deseadas
        comentario_filtrado = patron_palabras.sub("", comentario)

        # Reemplazar múltiples guiones por un solo guion
        comentario_filtrado = patron_guiones.sub("-", comentario_filtrado)

        # Limpiar espacios y comas innecesarias después de la sustitución
        comentario_filtrado = re.sub(r'\s*,\s*', ', ', comentario_filtrado)  # Espacios alrededor de comas
        comentario_filtrado = re.sub(r',\s*$', '', comentario_filtrado)  # Coma al final
        comentario_filtrado = comentario_filtrado.strip()  # Eliminar espacios en los extremos

        return comentario_filtrado

    def _crear_comentario_documento(self, order_document_ids, document_id, business_entity_id, total_documento, ruta):
        comentarios_pedidos = []
        comentario_a_insertar = ''
        for order in order_document_ids:
            comentario = self._modelo.obtener_comentario_pedido(order)

            if comentario:
                comentarios_pedidos.append(comentario)

        comentarios = [f"{comentario}," for comentario in comentarios_pedidos]
        comentario_a_insertar = '\n'.join(comentarios)
        comentario_a_insertar = self._filtrar_comentario_documento(comentario_a_insertar)

        comentarios_taras = self._crear_comentario_taras(order_document_ids)
        comentarios_horarios = self._crear_comentario_horarios(order_document_ids)
        comentarios_forma_pago = self._crear_comentario_forma_pago(order_document_ids)
        comentarios_entrega = self._crear_comentario_entrega(order_document_ids)

        comentario_a_insertar = f"{ruta}\n {comentario_a_insertar}\n {comentarios_taras}\n {comentarios_horarios}\n {comentarios_forma_pago}\n {comentarios_entrega}".upper()
        comentario_a_insertar = self._validar_credito_documento_cliente(business_entity_id, comentario_a_insertar, total_documento)

        self._modelo.actualizar_comentario_document_id(comentario_a_insertar, document_id)

    def _crear_comentario_taras(self, order_document_ids):
        comentario = ''

        for order in order_document_ids:
            consulta = self._modelo.obtener_info_taras_pedido(order)

            if not consulta:
                continue

            # Obtener el folio del pedido
            folio = consulta[0]['PedFolio']
            taras = []

            # Generar la lista de taras
            for tara in consulta:
                tara_type = tara['TaraPrefix']
                number_tara = tara['NumberTara']
                taras.append(f"{tara_type}{number_tara}")

            # Crear la cadena para este pedido
            taras_str = ",".join(taras)  # Concatenar las taras separadas por comas
            comentario += f"{folio}->{taras_str}; "

        # Eliminar el último espacio y punto y coma si existe
        comentario = comentario.strip("; ")
        return comentario

    def _crear_comentario_entrega(self, order_document_ids):
        comentario = ''  # Inicia el comentario vacío
        delivery_forms = []
        info_delivery = {}
        for pedido in order_document_ids:
            consulta = self._base_de_datos.buscar_info_documento_pedido_cayal(pedido)
            if consulta:
                info_pedido = consulta[0]
                # Extraer la información necesaria
                order_delivery_type_id = info_pedido['OrderDeliveryTypeID']
                if order_delivery_type_id == 1:
                    continue

                doc_folio = info_pedido['DocFolio']
                delivery_form = 'VIENE' if order_delivery_type_id == 2 else ''

                delivery_forms.append(delivery_form)
                info_delivery[doc_folio] = delivery_form

        if len(delivery_forms) == 1:
            return list(delivery_forms)[0]

        else:
            comentarios = []
            for folio, delivery_form in info_delivery.items():
                comentarios.append(f"{folio} {delivery_form}")

            comentario = ", ".join(comentarios)
            return comentario

    def _crear_comentario_horarios(self, order_document_ids):
        comentario = ''  # Inicia el comentario vacío

        for pedido in order_document_ids:
            consulta = self._base_de_datos.buscar_info_documento_pedido_cayal(pedido)
            if consulta:
                info_pedido = consulta[0]

                # Extraer la información necesaria
                folio = info_pedido['DocFolio']
                he = info_pedido['DeliveryTime']
                hv = info_pedido['CreatedOnTime']

                # Agregar al comentario en el formato deseado
                comentario += f"HE:{he}\n"

        # Opcionalmente, eliminar el salto de línea final
        return comentario.strip()

    def _crear_comentario_forma_pago(self, order_document_ids):
        comentario = ''  # Inicia el comentario vacío

        payment_forms = []
        info_payment = {}
        for pedido in order_document_ids:
            consulta = self._base_de_datos.buscar_info_documento_pedido_cayal(pedido)
            if consulta:
                info_pedido = consulta[0]
                # Extraer la información necesaria
                doc_folio = info_pedido['DocFolio']
                payment_form = info_pedido['WayToPayID']
                total = info_pedido['Total']

                payment_forms.append(payment_form)
                info_payment[doc_folio] = (payment_form, total)

        payment_forms = set(payment_forms)

        if len(payment_forms) == 1:

            way_to_pay_id = list(payment_forms)[0]
            if way_to_pay_id == 5:
                return ''

            return self._base_de_datos.fetchone(
                'SELECT Comments FROM OrdersPaymentTermCayal WHERE PaymentTermID = ?',
                (list(payment_forms)[0])
            )
        else:
            comentarios = []
            for folio, (payment_form, total) in info_payment.items():
                if payment_form == 5:
                    continue

                comentario_pago = self._base_de_datos.fetchone(
                    'SELECT Comments FROM OrdersPaymentTermCayal WHERE PaymentTermID = ?',
                    (payment_form,)
                )
                if comentario_pago:
                    comentarios.append(f"{folio} {comentario_pago}")

            comentario = ", ".join(comentarios)
            return comentario

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

        self._base_de_datos.command(
            'UPDATE docDocumentOrderCayal SET SubTotal = ?, Total = ?, TotalTax = ? WHERE OrderDocumentID = ?',
            (subtotal, totales, total_tax, order_document_id)
        )

    def _eliminar_suspension_crediticia(self, business_entity_id):
        sql = """
            DELETE FROM zvwStatusCreditoCayal WHERE IDEmpresa = ?

            INSERT INTO zvwBitacoraCambiosClientesT (Fecha, Cliente, Incidencia, ValorAnterior, ValorNuevo, Ruta, Usuario)
            VALUES(GETDATE(), 
                    (SELECT DISTINCT OfficialName FROM orgBusinessEntity WHERE BusinessEntityID = ?),
                    'ELIMINACION DE SUSPENSIÓN CREDITICIA',
                    'ELIMINACION DE SUSPENSIÓN CREDITICIA',
                    'ELIMINACION DE SUSPENSIÓN CREDITICIA',
                    (SELECT Z.ZoneName FROM orgCustomer C INNER JOIN orgZone Z on C.ZoneID = Z.ZoneID),
                    'SISTEMA')

            UPDATE orgCustomer SET ComentarioCredito = 'SI EXCEDE LO AUTORIZADO, TIENE QUE PAGAR LA DIFERENCIA' 
            WHERE BusinessEntityID = ?

            UPDATE orgBusinessEntity SET Custom4 = 1 WHERE BusinessEntityID = ?
        """
        self._base_de_datos.command(sql, (business_entity_id, business_entity_id, business_entity_id, business_entity_id))

    def _validar_credito_documento_cliente(self, business_entity_id, comentarios_documento, total_documento):

        info_cliente = self._base_de_datos.fetchall('SELECT * FROM [dbo].[zvwBuscarInfoCliente-BusinessEntityID](?)',
                                        (business_entity_id,))
        credito_autorizado = self._utilerias.redondear_valor_cantidad_a_decimal(info_cliente[0]['AuthorizedCredit'])
        ruta = int(info_cliente[0]['ZoneID'])

        if credito_autorizado > 0 and ruta == 1040:
            bloqueo_crediticio = int(info_cliente[0]['CreditBlock'])

            if bloqueo_crediticio == 1:
                tabla_credito = self._base_de_datos.fetchall("""
                        SELECT IDEmpresa, 
                                IDCLiente,
                                Cliente,
                                FechaBaja,	
                                ISNULL(FechaAlta, CAST('2052-03-26' as date)) FechaAlta,
                                TipoBaja,
                                Usuario,
                                StatusCredito,
                                Motivo,
                                Comentario,
                                ULTIMAEDICION,
                                USUARIOEDICION 
                        FROM zvwStatusCreditoCayal WHERE IDEmpresa = ?
                        """,
                                                 (business_entity_id,))

                if tabla_credito:
                    fecha_alta_bd = tabla_credito[0]['FechaAlta']
                    fecha_alta = fecha_alta_bd.date()
                    fecha_hoy = datetime.today().date()

                    if fecha_hoy >= fecha_alta:
                        self._eliminar_suspension_crediticia(business_entity_id)

                comentario_crediticio = '--NO TIENE CRÉDITO SU COMPRA ES DE CONTADO.-- '
            else:
                credito_restante = self._utilerias.redondear_valor_cantidad_a_decimal(info_cliente[0]['RemainingCredit'])
                debe = credito_autorizado - credito_restante

                if credito_restante > 0:
                    comentario_crediticio = f'--DEBE: {debe}. CRÉDITO DISPONIBLE: {credito_restante}-- '
                else:
                    credito_restante_real = credito_restante + total_documento

                    if credito_restante_real <= 0:
                        comentario_crediticio = '--NO TIENE CRÉDITO SU COMPRA ES DE CONTADO.-- '

                    elif credito_restante_real > 0 and credito_restante_real < total_documento:
                        obligatorio = total_documento - credito_restante_real
                        comentario_crediticio = f'--DEBE PAGAR OBLIGATORIAMENTE: {obligatorio}-- '

                    elif credito_restante_real == total_documento:
                        comentario_crediticio = f'--DEBE: {debe}. CRÉDITO DISPONIBLE: 0-- '

            return f'{comentario_crediticio} {comentarios_documento}'

        return comentarios_documento

    def _cancelar_pedido(self):
        self._pausar_autorefresco()
        try:
            user_group_id = self._base_de_datos.fetchone('SELECT UserGroupID FROM engUser WHERE UserID = ?', (self._user_id,))
            if user_group_id not in (1, 5, 6, 7, 15,20):
                self._interfaz.ventanas.mostrar_mensaje('No está autorizado para cancelar pedidos.')
                return
            valores_fila = self._validar_seleccion_una_fila()
            if not valores_fila:
                self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar solo o por lo menos un pedido.')
                return

            order_document_id = valores_fila['OrderDocumentID']
            self._parametros.id_principal = order_document_id
            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
            instancia = CancelarPedido(ventana, self._parametros, self._base_de_datos)
            ventana.wait_window()
        finally:
            self._reanudar_autorefresco()
            self._parametros.id_principal = 0

        self._actualizar_pedidos(self._fecha_seleccionada())

    def _afectar_bitacora_impresion(self, order_document_id):

        change_type_id = 12
        user_name = self._base_de_datos.buscar_nombre_de_usuario(self._user_id)
        comentario = f"{user_name}-{self._ticket.pedido}-{self._ticket.areas}"

        self._base_de_datos.insertar_registro_bitacora_pedidos(order_document_id,
                                                               change_type_id=change_type_id,
                                                               comments=comentario,
                                                               user_id=self._user_id)

    def _actualizar_tablas_impresion(self, order_document_id):

        areas = self._ticket.areas

        if 'Minisuper' in areas:
            self._base_de_datos.command(
                'UPDATE docDocumentOrderCayal SET StorePrintedOn=GETDATE(), StorePrintedBy=? WHERE OrderDocumentID = ?',
                (self._user_id, order_document_id)
            )

        if 'Almacen' in areas:
            self._base_de_datos.command(
                'UPDATE docDocumentOrderCayal SET WarehousePrintedOn=GETDATE(), WarehousePrintedBy=? WHERE OrderDocumentID = ?',
                (self._user_id, order_document_id)
            )

        if 'Produccion' in areas:
            self._base_de_datos.command(
                'UPDATE docDocumentOrderCayal SET ProductionPrintedOn=GETDATE(), ProductionPrintedBy=? WHERE OrderDocumentID = ?',
                (self._user_id, order_document_id)
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
