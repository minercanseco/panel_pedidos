import tkinter as tk
from datetime import datetime

from ttkbootstrap.constants import *
from cayal.tableview_cayal import Tableview
from panel.herramientas_captura import HerramientasCaptura
from panel.herramientas_generales import HerramientasGenerales
from panel.herramientas_timbrado import HerramientasTimbrado


class ControladorPanelPedidos:
    def __init__(self, modelo):
        """
        Controlador del panel de pedidos.

        Responsabilidades principales:
        - Guardar referencias a modelo / interfaz / master.
        - Inicializar flags de estado y contadores internos.
        - Construir la UI (tabla, eventos, notebook de herramientas).
        - Cargar la primera consulta de pedidos.
        - Arrancar el autorefresco periódico.
        """
        # --------------------------
        # Referencias básicas
        # --------------------------
        self._modelo = modelo
        self._interfaz = modelo.interfaz
        self._master = self._interfaz.master



        # eventos reales del usuario
        self._master.bind("<Button>", self._on_user_interaction)  # clics
        self._master.bind("<Key>", self._on_user_interaction)  # teclas

        # --------------------------
        # Flags de estado interno
        # --------------------------
        # Usado para detectar uso del aplicativo
        self._foco_humano = False  # flag
        self._nivel_pausa_autorefresco = 0

        # Evita que se solapen coloreos de filas
        self._coloreando = False
        # Evita reentradas mientras se repuebla la tabla
        self._actualizando_tabla = False
        # Se usa al regresar de la captura de un nuevo pedido
        self._capturando_nuevo_pedido = False

        # --------------------------
        # Contadores para autorefresco
        # (detectan cambios en la info para disparar refrescos)
        # --------------------------
        self._number_orders = -1
        self._number_transfer_payments = -1
        self._count_rest_leq15 = -1
        self._count_rest_16_30 = -1
        self._count_late_gt30 = -1

        # --------------------------
        # Configuración de autorefresco
        # --------------------------
        self._autorefresco_ms = 3000          # cada 3s
        self._autorefresco_activo = True
        # Se pone True mientras abres popups críticos (captura, etc.)
        self._bloquear_autorefresco = False

        # --------------------------
        # Construcción de la UI
        # --------------------------
        self._crear_tabla_pedidos()
        self._cargar_eventos()
        self._crear_notebook_herramientas()

        self._interfaz.ventanas.configurar_ventana_ttkbootstrap(
            titulo='Panel pedidos',
            bloquear=False
        )

        # --------------------------
        # Carga inicial de datos
        # --------------------------
        # Usa la fecha seleccionada en el dateentry si existe
        self._actualizar_pedidos(self._fecha_seleccionada())

        # --------------------------
        # Arranque del loop de autorefresco
        # --------------------------
        self._iniciar_autorefresco()

    # ------------------------------
    # Funciones relacionadas a la actualizacion automatica de la tabla
    # ------------------------------
    def _iniciar_autorefresco(self):
        # programa el siguiente tick sin bloquear la UI
        self._master.after(self._autorefresco_ms, self._tick_autorefresco)

    def _tick_autorefresco(self):
        if (
                self._autorefresco_activo
                and not self._coloreando
                and not self._bloquear_autorefresco
        ):
            try:
                self._buscar_nuevos_registros(self._fecha_seleccionada())
            except Exception as e:
                print("[AUTOREFRESCO] error:", e)

        self._iniciar_autorefresco()

    def _pausar_autorefresco(self):
        if not self._autorefresco_activo:
            return
        self._nivel_pausa_autorefresco += 1
        self._bloquear_autorefresco = True
        print(f"⏸️  Autorefresco pausado (nivel={self._nivel_pausa_autorefresco})")

    def _reanudar_autorefresco(self):
        if not self._autorefresco_activo:
            return
        if self._nivel_pausa_autorefresco > 0:
            self._nivel_pausa_autorefresco -= 1

        if self._nivel_pausa_autorefresco == 0:
            self._bloquear_autorefresco = False
            print("▶️  Autorefresco reanudado")
        else:
            print(f"▶️  Autorefresco sigue pausado (nivel={self._nivel_pausa_autorefresco})")

    def _on_user_interaction(self, event=None):
        self._foco_humano = True
        self._pausar_autorefresco()
        print("👤 Usuario interactuando → pausa")

    def _hay_subventanas_abiertas(self):
        """
        Devuelve True si existe al menos una Toplevel visible/activa
        asociada al mismo root que el panel.
        Funciona con las ventanas creadas por crear_popup_ttkbootstrap.
        """
        try:
            root = self._master.winfo_toplevel()
        except tk.TclError:
            return False

        try:
            hijos = root.winfo_children()
        except tk.TclError:
            return False

        for w in hijos:
            # Toplevel distintos a la raíz
            if isinstance(w, tk.Toplevel) and w is not root:
                try:
                    if w.winfo_exists() and w.state() not in ("withdrawn", "iconic"):
                        return True
                except tk.TclError:
                    # Si se destruyó entre medias, lo ignoramos
                    continue

        return False

    # ------------------------------
    # Helpers de fecha / filtros
    # ------------------------------
    def _fecha_seleccionada(self):
        fecha = self._interfaz.ventanas.obtener_input_componente('den_fecha')
        return str(fecha) if fecha else None

    def _obtener_valores_cbx_filtros(self):
        """Lee los valores actuales de los filtros de captura, horario, status y transferencias."""
        return {
            'cbx_capturista': self._interfaz.ventanas.obtener_input_componente('cbx_capturista'),
            'cbx_horarios': self._interfaz.ventanas.obtener_input_componente('cbx_horarios'),
            'cbx_status': self._interfaz.ventanas.obtener_input_componente('cbx_status'),
            'chk_transferencias': self._interfaz.ventanas.obtener_input_componente('chk_transferencias'),
        }

    def _settear_valores_cbx_filtros(self, valores_cbx_filtros):
        """Restaura valores en los combos, respetando 'Seleccione'."""
        vlr_cbx_captura = valores_cbx_filtros.get('cbx_capturista', 'Seleccione')
        vlr_cbx_horarios = valores_cbx_filtros.get('cbx_horarios', 'Seleccione')
        vlr_cbx_status = valores_cbx_filtros.get('cbx_status', 'Seleccione')
        vlr_chk_transferencias = valores_cbx_filtros.get('chk_transferencias', 0)

        if vlr_cbx_captura != 'Seleccione':
            self._interfaz.ventanas.insertar_input_componente('cbx_capturista', vlr_cbx_captura)
        else:
            self._interfaz.ventanas.insertar_input_componente('cbx_capturista', 'Seleccione')

        if vlr_cbx_horarios != 'Seleccione':
            self._interfaz.ventanas.insertar_input_componente('cbx_horarios', vlr_cbx_horarios)
        else:
            self._interfaz.ventanas.insertar_input_componente('cbx_horarios', 'Seleccione')

        if vlr_cbx_status != 'Seleccione':
            self._interfaz.ventanas.insertar_input_componente('cbx_status', vlr_cbx_status)
        else:
            self._interfaz.ventanas.insertar_input_componente('cbx_status', 'Seleccione')

        self._interfaz.ventanas.insertar_input_componente('chk_transferencias', 1 if vlr_chk_transferencias == 1 else 0)

    # ------------------------------
    # Carga de datos base
    # ------------------------------
    def _obtener_consulta_pedidos(self, fecha, refresh):
        """
        Devuelve la consulta de pedidos.
        - Usa caché si existe y no se pidió refresh ni cambio de fecha.
        - Actualiza self._modelo.consulta_pedidos cuando reconsulta.
        """
        if refresh or (fecha is not None) or not getattr(self._modelo, 'consulta_pedidos', None):
            consulta = self._modelo.buscar_pedidos(fecha)
            self._modelo.consulta_pedidos = consulta
        else:
            consulta = self._modelo.consulta_pedidos

        return consulta or []

    # ------------------------------
    # Construcción de opciones de filtros
    # ------------------------------
    @staticmethod
    def _normalizar_opciones(iterable):
        """
        Limpia None, aplica strip, de-duplica y regresa lista ordenada.
        """
        vistos, res = set(), []
        for v in iterable:
            if v is None:
                continue
            s = str(v).strip()
            if s and s not in vistos:
                vistos.add(s)
                res.append(s)
        return sorted(res)

    def _extraer_opciones_filtros(self, consulta):
        """
        A partir de la consulta, construye las listas de opciones para los combos.
        """
        capturistas = self._normalizar_opciones(f['CapturadoPor'] for f in consulta)
        horarios    = self._normalizar_opciones(f['HoraEntrega']  for f in consulta)
        status      = self._normalizar_opciones(f['Status']       for f in consulta)
        return {
            'capturistas': capturistas,
            'horarios':    horarios,
            'status':      status,
        }

    def _rellenar_filtros(self, opciones):
        """
        Rellena los combos de captura, horarios y status a partir de las opciones calculadas.
        """
        self._rellenar_cbx_captura(opciones['capturistas'])
        self._rellenar_cbx_horarios(opciones['horarios'])
        self._rellenar_cbx_status(opciones['status'])

    # ------------------------------
    # Lógica de selección en filtros
    # ------------------------------
    def _configurar_estado_filtros_post_captura(self, filtros_previos, lista_status, despues_de_capturar_pedido):
        """
        Decide qué debe quedar seleccionado en los combos después de actualizar datos:
        - Si se acaba de capturar un pedido: filtra por usuario actual y status "abierto".
        - Si no: restaura lo que el usuario tenía seleccionado.
        """
        if despues_de_capturar_pedido:
            # Caso especial: acabas de capturar un nuevo pedido
            self._interfaz.ventanas.insertar_input_componente('cbx_capturista', self._modelo.user_name)

            abiertos_posibles = {'abierto', 'abierta', 'open'}
            candidato_abierto = next(
                (s for s in lista_status if s.strip().lower() in abiertos_posibles),
                None
            )
            self._interfaz.ventanas.insertar_input_componente('cbx_status', candidato_abierto or 'Seleccione')
            self._interfaz.ventanas.insertar_input_componente('cbx_horarios', 'Seleccione')
        else:
            # Comportamiento normal: restaurar filtros previos
            self._settear_valores_cbx_filtros(filtros_previos)

    # ------------------------------
    # Aplicación de filtros a la consulta
    # ------------------------------
    def _aplicar_filtros_consulta(self, consulta, valores_filtros, despues_de_captura=False):
        """
        Aplica la lógica de filtrado:
        - Prioriza checkbox 'sin procesar'.
        - Si despues_de_captura=True → filtra por usuario actual y status 'Abierto'.
        - Si no hay ningún filtro activo → regresa la consulta tal cual.
        """

        def es_transferencia(f):
            way_to_pay_id = f.get('WayToPayID')
            forma_pago = str(
                f.get('FormaPago') or f.get('PaymentMethodName') or f.get('WayToPay') or '').strip().lower()

            # en varios flujos tuyos WayToPayID 6 = transferencia
            if way_to_pay_id == 6:
                return True

            if 'transferencia' in forma_pago:
                return True

            # deja esto solo como respaldo si tu consulta usa este campo para transferencias
            #if payment_confirmed_id in (1, 2):
            #    return True

            return False

        # 1) Prioridad: "sin procesar"
        if self._interfaz.ventanas.obtener_input_componente('chk_sin_procesar') == 1:
            self._interfaz.ventanas.limpiar_componentes('den_fecha')
            return self._modelo.buscar_pedidos_sin_procesar()

        # 2) Después de capturar un pedido: solo mis pedidos abiertos
        if despues_de_captura:
            usuario = self._modelo.user_name
            consulta = [
                f for f in consulta
                if f.get('CapturadoPor') == usuario and f.get('Status') == 'Abierto'
            ]

        vlr_cbx_captura = valores_filtros.get('cbx_capturista')
        vlr_cbx_horarios = valores_filtros.get('cbx_horarios')
        vlr_cbx_status = valores_filtros.get('cbx_status')
        vlr_chk_transferencias = valores_filtros.get('chk_transferencias', 0)

        filtrar_captura = (vlr_cbx_captura and vlr_cbx_captura != 'Seleccione')
        filtrar_horario = (vlr_cbx_horarios and vlr_cbx_horarios != 'Seleccione')
        filtrar_status = (vlr_cbx_status and vlr_cbx_status != 'Seleccione')
        filtrar_transferencias = (vlr_chk_transferencias == 1)

        if not (filtrar_captura or filtrar_horario or filtrar_status or filtrar_transferencias):
            return consulta

        def ok(f):
            if filtrar_captura and f.get('CapturadoPor') != vlr_cbx_captura:
                return False
            if filtrar_horario and f.get('HoraEntrega') != vlr_cbx_horarios:
                return False
            if filtrar_status and f.get('Status') != vlr_cbx_status:
                return False
            if filtrar_transferencias and not es_transferencia(f):
                return False
            return True

        return [f for f in consulta if ok(f)]

    # Mantengo este wrapper por compatibilidad con tu nombre original
    def _filtrar_consulta_sin_rellenar(self, consulta, valores, despues_de_captura=False):
        return self._aplicar_filtros_consulta(consulta, valores, despues_de_captura)

    # ------------------------------
    # Pintar tabla + meters
    # ------------------------------
    def _pintar_tabla_pedidos(self, consulta_filtrada):
        """
        Pinta la tabla de pedidos y actualiza colores/meters.
        """
        if not consulta_filtrada:
            self._limpiar_tabla()
            return

        self._interfaz.ventanas.rellenar_table_view(
            'tbv_pedidos',
            self._interfaz.crear_columnas_tabla(),
            consulta_filtrada
        )

        # Actualiza colores + meters
        self._colorear_filas_panel_horarios(actualizar_meters=True)

    # ------------------------------
    # Método orquestador principal
    # ------------------------------
    def _actualizar_pedidos(self, fecha=None, criteria=True,
                            refresh=False, despues_de_capturar_pedido=False):
        """
        Punto único de entrada para:
        - Limpiar filtros visuales (opcional)
        - Cargar/recargar datos
        - Construir opciones de filtros
        - Decidir qué queda seleccionado en los combos
        - Aplicar filtros sobre la consulta
        - Pintar tabla y meters
        """
        if self._actualizando_tabla:
            return

        try:
            fecha = self._interfaz.ventanas.obtener_input_componente('den_fecha') if not fecha else fecha
            self._actualizando_tabla = True

            # 1) Limpia filtros visuales de la tabla (no de los combos)
            self._interfaz.ventanas.limpiar_filtros_table_view('tbv_pedidos', criteria)

            # 2) Carga consulta base (usa caché si aplica)
            consulta = self._obtener_consulta_pedidos(fecha, refresh)
            if not consulta:
                self._limpiar_tabla()
                return

            # 3) Guarda selección previa del usuario en combos
            filtros_previos = self._obtener_valores_cbx_filtros()

            # 4) Construye opciones de filtros y repuebla combos
            opciones = self._extraer_opciones_filtros(consulta)
            self._rellenar_filtros(opciones)

            # 5) Decide qué queda seleccionado en los combos
            self._configurar_estado_filtros_post_captura(
                filtros_previos,
                opciones['status'],
                despues_de_capturar_pedido
            )

            # 6) Lee de nuevo los filtros (ya con la selección definitiva)
            filtros_actuales = self._obtener_valores_cbx_filtros()

            # 7) Aplica filtros sobre la consulta
            consulta_filtrada = self._aplicar_filtros_consulta(
                consulta,
                filtros_actuales,
                despues_de_captura=despues_de_capturar_pedido
            )

            # 8) Pinta tabla + meters
            self._pintar_tabla_pedidos(consulta_filtrada)

        finally:
            self._actualizando_tabla = False

    # ------------------------------
    # Filtros disparados por eventos
    # ------------------------------
    def _filtrar_por_capturados_por(self):
        self._limpiar_componentes()
        self._actualizar_pedidos(self._fecha_seleccionada())

    def _filtrar_por_status(self):
        self._limpiar_componentes()
        self._actualizar_pedidos(self._fecha_seleccionada())

    def _filtrar_por_horas(self):
        self._limpiar_componentes()
        self._actualizar_pedidos(self._fecha_seleccionada())

    def _filtrar_post_captura(self):
        self._actualizar_pedidos(self._fecha_seleccionada())
        self._interfaz.ventanas.insertar_input_componente('cbx_capturista', self._modelo.user_name)
        self._interfaz.ventanas.insertar_input_componente('cbx_status', 'Abierto')
        self._interfaz.ventanas.insertar_input_componente('chk_transferencias', 0)
        self._filtrar_por_status()

    def _limpiar_componentes(self):
        self._interfaz.ventanas.limpiar_componentes(['tbx_comentarios', 'tvw_detalle'])

    def _limpiar_tabla(self):
        """Limpia la tabla y restablece los contadores de métricas"""
        tabla = self._interfaz.ventanas.componentes_forma['tbv_pedidos']
        for campo in ['mtr_total', 'mtr_en_tiempo', 'mtr_a_tiempo', 'mtr_retrasado']:
            self._interfaz.ventanas.insertar_input_componente(campo, (1, 0))
        tabla.delete_rows()

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
            status_pedido = self._modelo.utilerias.determinar_color_fila_respecto_entrega_pedido(valores_fila, ahora)

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

    def _rellenar_cbx_captura(self, valores):
        valores = sorted(list(set(valores)))
        self._interfaz.ventanas.rellenar_cbx('cbx_capturista', valores)

    def _rellenar_cbx_status(self, valores):
        valores = sorted(list(set(valores)))
        self._interfaz.ventanas.rellenar_cbx('cbx_status', valores)

    def _rellenar_cbx_horarios(self, valores):
        valores = sorted(list(set(valores)))
        self._interfaz.ventanas.rellenar_cbx('cbx_horarios', valores)

    def _filtrar_transferencias(self):
        self._limpiar_componentes()

        valor_chk = self._interfaz.ventanas.obtener_input_componente('chk_transferencias')

        if valor_chk == 1:
            # opcionalmente desactiva "sin procesar" porque son filtros de naturaleza distinta
            self._interfaz.ventanas.cambiar_estado_checkbutton('chk_sin_procesar', 'deseleccionado')

        self._actualizar_pedidos(self._fecha_seleccionada())

    def _cargar_eventos(self):
        eventos = {
            'den_fecha': lambda event: self._actualizar_pedidos(self._fecha_seleccionada(), criteria=False),
            'tbv_pedidos': (lambda event: self._rellenar_tabla_detalle(), 'doble_click'),
            'cbx_capturista': lambda event: self._filtrar_por_capturados_por(),
            'cbx_status': lambda event: self._filtrar_por_status(),
            'cbx_horarios': lambda event: self._filtrar_por_horas(),
            'chk_sin_procesar': lambda *args: self._filtrar_no_procesados(),
            'chk_sin_fecha': lambda *args: self._sin_fecha(),
            'chk_transferencias': lambda *args: self._filtrar_transferencias(),
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
        self._interfaz.ventanas.insertar_input_componente('chk_transferencias', 0)

        valor_chk = self._interfaz.ventanas.obtener_input_componente('chk_sin_procesar')
        if valor_chk == 1:
            self._interfaz.ventanas.cambiar_estado_checkbutton('chk_sin_fecha', 'deseleccionado')
            self._actualizar_pedidos()

        if valor_chk == 0:
            fecha = str(datetime.today().date())
            self._interfaz.ventanas.insertar_input_componente('den_fecha', fecha)
            self._actualizar_pedidos()

    def _crear_tabla_pedidos(self):
        ancho, alto = self._interfaz.ventanas.obtener_resolucion_pantalla()

        frame = self._interfaz.ventanas.componentes_forma['frame_captura']
        colors = self._interfaz.master.style.colors
        numero_filas = 15 if ancho <= 1367 else 20
        componente = Tableview(
            master=frame,
            coldata=self._interfaz.crear_columnas_tabla(),
            rowdata=self._modelo.utilerias.diccionarios_a_tuplas(None),
            paginated=True,
            searchable=True,
            bootstyle=PRIMARY,
            pagesize=numero_filas,
            stripecolor=None,  # (colors.light, None),
            height=numero_filas,
            autofit=False,
            callbacks=[self._colorear_filas_panel_horarios],
            callbacks_search=[self._buscar_pedidos_cliente_sin_fecha]

        )

        self._interfaz.ventanas.componentes_forma['tbv_pedidos'] = componente
        componente.grid(row=0, column=0, pady=5, padx=5, sticky=tk.NSEW)

        operador_panel = self._modelo.user_name
        version_paquete = self._modelo.parametros.version_paquete

        texto = f'Max:{numero_filas} Paquete: {version_paquete} OPERADOR: {operador_panel}'
        self._interfaz.ventanas.actualizar_etiqueta_externa_tabla_view('tbv_pedidos', texto)

    def _buscar_nuevos_registros(self, fecha):

        # Usa la fecha seleccionada si existe; si no, hoy
        hoy = datetime.now().date() if not fecha else datetime.strptime(fecha, "%Y-%m-%d").date()
        # 1) Pedidos en logística impresos (4,13 + PrintedOn not null)
        number_orders = self._modelo.obtener_numero_pedidos_fecha(hoy) or 0

        # 2) Transferencias confirmadas = 2
        number_transfer_payments = self._modelo.obtener_numero_pedidos_transferencia_fecha(hoy) or 0

        # 3) Buckets de puntualidad (<=15, 16-30, >30)
        rows = self._modelo.obtener_pedidos_por_puntualidad_fecha(hoy)

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

    def _sin_fecha(self):

        valor_chk_fecha = self._interfaz.ventanas.obtener_input_componente('chk_sin_fecha')

        if valor_chk_fecha == 1:

            self._interfaz.ventanas.cambiar_estado_checkbutton('chk_sin_procesar', 'deseleccionado')

            date_entry = self._interfaz.ventanas.componentes_forma['den_fecha']
            date_entry.entry.delete(first=0, last=tk.END)
        else:
            self._interfaz.ventanas.insertar_input_componente('den_fecha', self._modelo.hoy)

    def _obtener_valores_fila_pedido_seleccionado(self, valor = None):
        if not self._interfaz.ventanas.validar_seleccion_una_fila_table_view('tbv_pedidos'):
            return

        valores_fila = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)[0]
        if not valor:
            return

        return valores_fila[valor]

    # funciones relacionadas con herramientas del panel
    #------------------------------------------------------------------------------------------------------------------
    def _crear_notebook_herramientas(self):
        info_pestanas = {
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
            tab_name = clave
            frame_name = clave.replace('tab_', 'frm_')
            frames_tabs[frame_name] = (
                tab_name,
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            )

        self._interfaz.ventanas.crear_frames(frames_tabs)

        # Callbacks para herramientas del notebook
        callbacks_autorefresco = {
            "pausar": self._pausar_autorefresco,
            "reanudar": self._reanudar_autorefresco,
            "postcaptura":self._filtrar_post_captura,
            "rellenar_tabla":self._actualizar_pedidos
        }

        # cada frame será el master de las subsecuentes ventanas
        for frame_name, (tab_name, configuracion, posicion) in frames_tabs.items():
            frame = self._interfaz.ventanas.componentes_forma[frame_name]

            if 'generales' in frame_name:
                HerramientasGenerales(
                    master=frame,
                    modelo=self._modelo,
                    interfaz=self._interfaz,
                    callbacks_autorefresco=callbacks_autorefresco,
                )

            if 'captura' in frame_name:
                HerramientasCaptura(
                    master=frame,
                    modelo=self._modelo,
                    interfaz=self._interfaz,
                    callbacks_autorefresco=callbacks_autorefresco,
                )

            if 'timbrado' in frame_name:
                HerramientasTimbrado(
                    master=frame,
                    modelo=self._modelo,
                    interfaz=self._interfaz,
                    callbacks_autorefresco=callbacks_autorefresco,
                )

    # ------------------------------------------------------------------------------------------------------------------
    # Funciones auxiliares
    # ------------------------------------------------------------------------------------------------------------------
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

    def _rellenar_tabla_detalle(self):

        def procesar_partidas_pedido(partidas):
            if not partidas:
                return []

            consulta = self._modelo.utilerias.agregar_impuestos_productos(partidas) or []
            redondear = self._modelo.utilerias.redondear_valor_cantidad_a_decimal
            es_flotante = self._modelo.utilerias.es_flotante

            partidas_procesadas = []

            for producto in consulta:
                if not isinstance(producto, dict):
                    continue

                product_id = producto.get('ProductID')
                if product_id == 5606:
                    continue

                comentario = (producto.get('Comments') or '').strip()
                piezas = producto.get('CayalPiece', 0)
                piezas = 0 if es_flotante(piezas) else piezas

                registro = {
                    'cantidad_producida': redondear(producto.get('cantidad', 0)),
                    'product_key': producto.get('ProductKey', ''),
                    'product_name': producto.get('ProductName', ''),
                    'tipo_captura': self._modelo.utilerias.resolver_icono(
                        'inventario' if producto.get('TipoCaptura', 1) == 0 else 'manual'),
                    'precio': redondear(producto.get('precio', 0)),
                    'total': redondear(producto.get('total', 0)),
                    'esp': producto.get('Esp', ''),
                    'product_id': product_id,
                    'document_item_id': producto.get('DocumentItemID'),
                    'item_production_status_modified': producto.get('ItemProductionStatusModified', 0),
                    'clave_unidad': producto.get('ClaveUnidad', ''),
                    'status_surtido': 0,
                    'unit_price': producto.get('UnitPrice', 0),
                    'cayal_piece': piezas,
                    'cayal_amount': producto.get('CayalAmount', 0),
                    'comentario': comentario,
                    'product_type_id_cayal': producto.get('ProductTypeIDCayal'),
                }

                partidas_procesadas.append(registro)

            return partidas_procesadas

        def colorear_partidas_detalle():
            filas = self._interfaz.ventanas.obtener_filas_treeview('tvw_detalle')
            if not filas:
                return

            for fila in filas:
                valores_fila = self._interfaz.ventanas.procesar_fila_treeview('tvw_detalle', fila)
                if not valores_fila:
                    continue

                estado = valores_fila.get('ItemProductionStatusModified', 0)

                if estado == 3:
                    self._interfaz.ventanas.colorear_fila_seleccionada_treeview(
                        'tvw_detalle', fila, color='danger'
                    )
                elif estado == 1:
                    self._interfaz.ventanas.colorear_fila_seleccionada_treeview(
                        'tvw_detalle', fila, color='info'
                    )
                elif estado == 2:
                    self._interfaz.ventanas.colorear_fila_seleccionada_treeview(
                        'tvw_detalle', fila, color='warning'
                    )

        order_document_id = self._obtener_valores_fila_pedido_seleccionado('OrderDocumentID')
        if not order_document_id:
            self._interfaz.ventanas.limpiar_componentes(['tvw_detalle'])
            return

        partidas_producidas = self._modelo.buscar_partidas_pedido_producidas(order_document_id) or []
        partidas_capturadas = self._modelo.buscar_partidas_pedido_capturadas(order_document_id) or []

        self._interfaz.ventanas.limpiar_componentes(['tvw_detalle'])

        if not partidas_producidas or not partidas_capturadas:
            return

        partidas_procesadas_producidas = procesar_partidas_pedido(partidas_producidas)
        partidas_procesadas_capturadas = procesar_partidas_pedido(partidas_capturadas)

        if not partidas_procesadas_producidas:
            return

        cantidades_capturadas_por_document_item_id = {}
        for reg in partidas_procesadas_capturadas:
            document_item_id = reg.get('document_item_id')
            if document_item_id is None:
                continue
            cantidades_capturadas_por_document_item_id[document_item_id] = reg.get('cantidad_producida', 0)

        for partida in partidas_procesadas_producidas:
            document_item_id = partida.get('document_item_id')
            cantidad_capturada = cantidades_capturadas_por_document_item_id.get(document_item_id, 0)

            datos_fila = [
                cantidad_capturada,
                partida.get('cantidad_producida', 0),
                partida.get('tipo_captura', 0),
                partida.get('product_key', ''),
                partida.get('product_name', ''),
                partida.get('precio', 0),
                partida.get('total', 0),
                partida.get('esp', ''),
                partida.get('product_id'),
                partida.get('document_item_id'),
                partida.get('item_production_status_modified', 0),
                partida.get('clave_unidad', ''),
                partida.get('status_surtido', 0),
                partida.get('unit_price', 0),
                partida.get('cayal_piece', 0),
                partida.get('cayal_amount', 0),
                partida.get('comentario', ''),
                partida.get('product_type_id_cayal'),
            ]

            self._interfaz.ventanas.insertar_fila_treeview('tvw_detalle', datos_fila)

        colorear_partidas_detalle()
    #------------------------------------------------------------------------------------------------------------------

