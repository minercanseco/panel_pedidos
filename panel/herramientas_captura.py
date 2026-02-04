import tkinter as tk

from cayal.documento import Documento
from cayal.ventanas import Ventanas

from herramientas.capturar_documento.buscar_generales_cliente import BuscarGeneralesCliente
from herramientas.capturar_documento.llamar_instancia_captura import LlamarInstanciaCaptura
from herramientas.herramientas_panel.editar_caracteristicas_pedido import EditarCaracteristicasPedido
from herramientas.herramientas_panel.editar_pedido import EditarPedido
from herramientas.herramientas_panel.ticket_pedido_cliente import TicketPedidoCliente


class HerramientasCaptura:
    def __init__(self, master, modelo, interfaz, callbacks_autorefresco):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._modelo = modelo
        self._interfaz = interfaz
        self._callbacks_autorefresco = callbacks_autorefresco or {}

        self._base_de_datos = self._modelo.base_de_datos
        self._parametros = self._modelo.parametros
        self._utilerias = self._modelo.utilerias

        self._interfaz.ventanas._master.grab_release()

        self._crear_frames()
        self._crear_barra_herramientas()

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'pady': 5, 'padx': 5, 'sticky': tk.NSEW}),

            'frame_componentes': ('frame_principal', None,
                                  {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                   'sticky': tk.NSEW})
        }
        self._ventanas.crear_frames(frames)

    def _crear_barra_herramientas(self):
        self.barra_herramientas_pedido = [


            {'nombre_icono': 'HeaderFooter32.ico', 'etiqueta': 'Nuevo', 'nombre': 'capturar_nuevo',
             'hotkey': None, 'comando': self._capturar_nuevo_pedido},

            {'nombre_icono': 'EditBusinessEntity32.ico', 'etiqueta': 'E.Caracteristicas', 'nombre': 'editar_caracteristicas',
             'hotkey': '', 'comando': self._editar_caracteristicas_pedido},

            {'nombre_icono': 'DocumentGenerator32.ico', 'etiqueta': 'Ticket', 'nombre': 'crear_ticket',
             'hotkey': None, 'comando': self._crear_ticket_pedido_cliente},

            {'nombre_icono': 'Manufacture32.ico', 'etiqueta': 'M.Producir', 'nombre': 'mandar_producir',
             'hotkey': None, 'comando': self._mandar_a_producir},

            {'nombre_icono': 'lista-de-verificacion.ico', 'etiqueta': 'Editar', 'nombre': 'editar',
             'hotkey': None, 'comando': self._editar_pedido},

        ]

        self.elementos_barra_herramientas = self._ventanas.crear_barra_herramientas(self.barra_herramientas_pedido,
                                                                                   'frame_componentes')
        self.iconos_barra_herramientas = self.elementos_barra_herramientas[0]
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]

    def _pausar_autorefresco(self):
        fn = self._callbacks_autorefresco.get("pausar")
        if fn:
            fn()

    def _reanudar_autorefresco(self):
        fn = self._callbacks_autorefresco.get("reanudar")
        if fn:
            fn()

    def _filtro_post_captura(self):
        fn = self._callbacks_autorefresco.get("postcaptura")
        if fn:
            fn()

    def _rellenar_tabla(self):
        fn = self._callbacks_autorefresco.get("rellenar_tabla")
        if fn:
            fn()

    def _obtener_valores_fila_pedido_seleccionado(self, valor = None):
        if not self._interfaz.ventanas.validar_seleccion_una_fila_table_view('tbv_pedidos'):
            return

        valores_fila = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)[0]
        if not valor:
            return valores_fila

        return valores_fila[valor]

    def _obtener_valores_filas_pedidos_seleccionados(self):
        # si imprimir en automatico esta desactivado la seleccion de filas solo aplica a la seleccion
        filas = self._interfaz.ventanas.procesar_filas_table_view('tbv_pedidos', seleccionadas=True)

        if not filas:
            self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar por lo menos un pedido.')
            return

        return filas

    def _capturar_nuevo_pedido(self):
        """
        Objetivo:
        - Abrir ventana de búsqueda de cliente (puede ser modal normal).
        - Al seleccionar cliente, abrir captura en un Toplevel NO MODAL.
        - Permitir múltiples capturas simultáneas y alternar foco (Windows/Mac).
        """
        import time

        self._pausar_autorefresco()
        self._parametros.id_principal = 0

        estado = {
            "inst_buscar": None,
            "v_buscar": None,
            "watch_id": None,
        }

        # -------------------------
        # helpers base
        # -------------------------
        def _cerrar_ventana(w):
            try:
                if w is not None and w.winfo_exists():
                    w.destroy()
            except Exception:
                pass

        def _cancel_watch():
            try:
                if estado["watch_id"] is not None:
                    self._interfaz.master.after_cancel(estado["watch_id"])
            except Exception:
                pass
            estado["watch_id"] = None

        def _reanudar_seguro():
            try:
                self._reanudar_autorefresco()
            except Exception:
                pass

        def _post_cierre_captura(nuevo_pedido_flag: bool):
            try:
                self._parametros.id_principal = 0
            except Exception:
                pass

            try:
                self._rellenar_tabla()
                if nuevo_pedido_flag:
                    self._filtro_post_captura()
            finally:
                _reanudar_seguro()

        # -------------------------
        # GRAB CONTROL (Windows)
        # -------------------------
        def _release_any_grab():
            """Rompe cualquier grab en el root (si existe)."""
            try:
                root = self._interfaz.master
                g = root.grab_current()
                if g is not None:
                    g.grab_release()
            except Exception:
                pass

        def _make_window_non_modal(win):
            """
            Fuerza comportamiento NO modal en Windows.
            - Rompe grab al abrir
            - Evita que la ventana pueda aplicar grab (monkeypatch local)
            - Watchdog que rompe grab periódicamente mientras exista
            - Facilita foco alternable con lift/focus
            """
            # 1) romper grab inicial
            _release_any_grab()

            # 2) asegurar topmost off
            try:
                win.attributes("-topmost", False)
            except Exception:
                pass

            # 3) monkeypatch: bloquear grab_set/grab_set_global SOLO en esta ventana
            #    (para que si Captura intenta modalizarse, no lo logre)
            try:
                if not hasattr(win, "_orig_grab_set"):
                    win._orig_grab_set = win.grab_set
                    win._orig_grab_set_global = win.grab_set_global

                    def _blocked_grab_set(*args, **kwargs):
                        # print("[BLOCK] grab_set", win)
                        return None

                    def _blocked_grab_set_global(*args, **kwargs):
                        # print("[BLOCK] grab_set_global", win)
                        return None

                    win.grab_set = _blocked_grab_set
                    win.grab_set_global = _blocked_grab_set_global
            except Exception:
                pass

            # 4) cuando se enfoque o se haga click, rompe cualquier grab activo
            try:
                win.bind("<FocusIn>", lambda e: _release_any_grab(), add="+")
                win.bind("<Button-1>", lambda e: _release_any_grab(), add="+")
            except Exception:
                pass

            # 5) watchdog: mientras la ventana exista, cada 150ms rompe grab
            watchdog = {"id": None}

            def _tick():
                try:
                    if win is None or not win.winfo_exists():
                        watchdog["id"] = None
                        return
                    _release_any_grab()
                    watchdog["id"] = self._interfaz.master.after(150, _tick)
                except Exception:
                    watchdog["id"] = None

            try:
                watchdog["id"] = self._interfaz.master.after(50, _tick)
            except Exception:
                _tick()

            # 6) on destroy: cancelar watchdog
            def _stop_watchdog(_e=None):
                try:
                    if watchdog["id"] is not None:
                        self._interfaz.master.after_cancel(watchdog["id"])
                except Exception:
                    pass
                watchdog["id"] = None

            try:
                win.bind("<Destroy>", _stop_watchdog, add="+")
            except Exception:
                pass

            # 7) bring to front (Windows sometimes needs idle)
            def _lift_focus():
                try:
                    win.lift()
                except Exception:
                    pass
                try:
                    win.focus_force()
                except Exception:
                    pass

            try:
                self._interfaz.master.after_idle(_lift_focus)
            except Exception:
                _lift_focus()

        # -------------------------
        # abrir captura (no modal real)
        # -------------------------
        def _abrir_captura_con(inst_buscar):
            # Importante: re-pausar aquí
            self._pausar_autorefresco()

            vcap = self._ventanas.crear_popup_ttkbootstrap_async(
                titulo="Nueva captura",
                nombre_icono="icono_logo.ico",
                ocultar_master=False
            )

            # ✅ convertirla a NO modal (a prueba de Windows)
            _make_window_non_modal(vcap)

            cap = LlamarInstanciaCaptura(
                vcap,
                self._parametros,
                inst_buscar.cliente,
                inst_buscar.documento,
                inst_buscar.ofertas
            )

            def _on_close():
                nuevo = False
                try:
                    nuevo = bool(getattr(cap, "nuevo_pedido", False))
                except Exception:
                    pass

                _release_any_grab()
                _cerrar_ventana(vcap)
                _post_cierre_captura(nuevo)

            try:
                vcap.protocol("WM_DELETE_WINDOW", _on_close)
                vcap.bind("<Escape>", lambda e: _on_close(), add="+")
            except Exception:
                pass

        # -------------------------
        # fallback Destroy buscar (Windows delay)
        # -------------------------
        def _on_buscar_destroyed():
            def _check():
                try:
                    inst = estado["inst_buscar"]
                    if inst is not None and getattr(inst, "seleccion_aceptada", False):
                        _abrir_captura_con(inst)
                    else:
                        _reanudar_seguro()
                except Exception:
                    _reanudar_seguro()

            try:
                self._interfaz.master.after(80, _check)  # Windows-friendly
            except Exception:
                _check()

        # -------------------------
        # watcher (respaldo)
        # -------------------------
        def _watch_busqueda():
            try:
                inst = estado["inst_buscar"]
                vbus = estado["v_buscar"]

                if inst is not None and getattr(inst, "seleccion_aceptada", False):
                    _cancel_watch()
                    _cerrar_ventana(vbus)
                    estado["v_buscar"] = None

                    # Windows: deja que el destroy termine y luego abre captura
                    try:
                        self._interfaz.master.after(60, lambda: _abrir_captura_con(inst))
                    except Exception:
                        _abrir_captura_con(inst)
                    return

                if vbus is None or not vbus.winfo_exists():
                    _cancel_watch()
                    return

            except Exception:
                _cancel_watch()
                _reanudar_seguro()
                return

            try:
                estado["watch_id"] = self._interfaz.master.after(120, _watch_busqueda)
            except Exception:
                _cancel_watch()
                _reanudar_seguro()

        # ============================================================
        # Abrir búsqueda cliente (se deja como la tienes para poder escribir)
        # ============================================================
        vbus = self._ventanas.crear_popup_ttkbootstrap_async(
            titulo="Seleccionar cliente",
            nombre_icono="icono_logo.ico",
            ocultar_master=False
        )
        estado["v_buscar"] = vbus

        inst = BuscarGeneralesCliente(vbus, self._parametros)
        estado["inst_buscar"] = inst

        def _cerrar_busqueda():
            _cancel_watch()
            _cerrar_ventana(vbus)
            _reanudar_seguro()

        try:
            vbus.bind("<Escape>", lambda e: _cerrar_busqueda(), add="+")
            vbus.protocol("WM_DELETE_WINDOW", _cerrar_busqueda)
        except Exception:
            pass

        # Destroy fallback
        try:
            vbus.bind("<Destroy>", lambda e: _on_buscar_destroyed() if e.widget is vbus else None, add="+")
        except Exception:
            pass

        _watch_busqueda()

    def _editar_pedido(self):

        fila = self._obtener_valores_fila_pedido_seleccionado()
        if not fila:
            self._interfaz.ventanas.mostrar_mensaje('Debe seleccionar un pedido.')
            return

        status_id = fila['TypeStatusID']
        order_document_id = fila['OrderDocumentID']
        business_entity_id = fila['BusinessEntityID']

        #  cancelado, modificando, surtido parcialmente minisuper, produccion, almacen, entregado, cobrado o cartera
        if status_id in (10, 12, 16, 17, 18, 13, 14, 15):
            self._interfaz.ventanas.mostrar_mensaje('El pedido no tiene un estatus válido para ser editado.')
            return

        try:
            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap(titulo='Pedido', nombre_icono='icono_logo.ico')
            if status_id < 3:
                self._parametros.id_principal = order_document_id
                documento = Documento()
                documento.document_id = order_document_id
                documento.business_entity_id = business_entity_id

                _ = LlamarInstanciaCaptura(
                    ventana,
                    self._parametros,
                    documento=documento
                )

            elif status_id >= 3:
                _ = EditarPedido(ventana, self._base_de_datos, self._utilerias, self._parametros, fila)

            else:
                self._interfaz.ventanas.mostrar_mensaje(
                    'No hay acción válida para un pedido en este estado.'
                )

            ventana.wait_window()

        finally:
            self._modelo.actualizar_totales_pedido(order_document_id)
            self._rellenar_tabla()
            if status_id == 1:
                self._filtro_post_captura()

    def _editar_caracteristicas_pedido(self):
        status_id = None
        se_abrio_popup = False
        try:
            fila = self._obtener_valores_fila_pedido_seleccionado()
            if not fila:
                return

            status_id = fila['TypeStatusID']

            if status_id == 10:
                self._interfaz.ventanas.mostrar_mensaje('NO se pueden editar pedidos cancelados.')
                return
            elif status_id >= 4:
                self._interfaz.ventanas.mostrar_mensaje(
                    'Sólo se pueden afectar las caracteristicas de un pedido hasta el status Por timbrar.'
                )
                return

            order_document_id = fila['OrderDocumentID']
            self._parametros.id_principal = order_document_id

            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()
            se_abrio_popup = True
            instancia = EditarCaracteristicasPedido(ventana, self._parametros, self._base_de_datos, self._utilerias)
            ventana.wait_window()

        finally:
            self._parametros.id_principal = 0
            if se_abrio_popup and status_id == 1:
                self._filtro_post_captura()

    def _crear_ticket_pedido_cliente(self):
        status_id = None  # <- para que exista siempre en finally

        order_document_id = self._obtener_valores_fila_pedido_seleccionado(valor='OrderDocumentID')
        if not order_document_id:
            return

        valores = self._modelo.obtener_status_entrega_pedido(order_document_id)
        if not valores:
            return

        status_id = valores.get('status_id')
        status_entrega = valores.get('status_entrega')
        fecha_entrega = valores.get('fecha_entrega')

        if status_entrega == 0:
            self._interfaz.ventanas.mostrar_mensaje(
                'Debe definir la forma de pago del cliente antes de generar el ticket.'
            )
            return

        try:
            fecha_entrega = str(fecha_entrega)[0:10]
            fecha_entrega = self._utilerias.convertir_fecha_str_a_datetime(str(fecha_entrega))

            if fecha_entrega > self._modelo.hoy:
                respuesta = self._interfaz.ventanas.mostrar_mensaje_pregunta(
                    'EL pedido es para una fecha de entrega posterior, ¿Desea actualizar los precios antes de generar el ticket?'
                )
                if respuesta:
                    self._base_de_datos.actualizar_precios_pedido(order_document_id)

            self._parametros.id_principal = order_document_id
            instancia = TicketPedidoCliente(self._base_de_datos, self._utilerias, self._parametros)

            self._interfaz.ventanas.mostrar_mensaje(
                master=self._interfaz.master,
                mensaje='Comprobante generado.',
                tipo='info'
            )
            self._interfaz.master.iconify()

        finally:
            self._parametros.id_principal = 0
            self._rellenar_tabla()

            if status_id == 1:
                self._filtro_post_captura()

    def _mandar_a_producir(self):

        filas = self._obtener_valores_filas_pedidos_seleccionados()
        if not filas:
            return
        try:
            for fila in filas:
                order_document_id = fila['OrderDocumentID']

                valores = self._modelo.obtener_status_entrega_pedido(order_document_id)
                status = valores['status_id']
                entrega = valores['fecha_entrega']
                folio = valores['doc_folio']

                if not entrega or entrega == 'None':
                    self._interfaz.ventanas.mostrar_mensaje(
                        f'Debe usar la herramienta de editar características para el pedido {folio}.')
                    continue

                if status == 1:
                    self._modelo.mandar_pedido_a_producir(order_document_id)

                if status > 1:
                    continue
        finally:
            self._rellenar_tabla()

    def _asegurar_admin_capturas(self):
        """Inicializa estructuras para manejar múltiples capturas."""
        if not hasattr(self, "_capturas_abiertas"):
            self._capturas_abiertas = []  # lista de Toplevel
        if not hasattr(self, "_guardian_grab_id"):
            self._guardian_grab_id = None

    def _registrar_captura(self, win):
        self._asegurar_admin_capturas()
        try:
            if win not in self._capturas_abiertas:
                self._capturas_abiertas.append(win)
        except Exception:
            pass
        self._iniciar_guardian_grab()

    def _desregistrar_captura(self, win):
        self._asegurar_admin_capturas()
        try:
            self._capturas_abiertas = [w for w in self._capturas_abiertas if
                                       w is not None and w.winfo_exists() and w != win]
        except Exception:
            self._capturas_abiertas = []
        if not self._capturas_abiertas:
            self._detener_guardian_grab()

    def _iniciar_guardian_grab(self):
        """
        Guardian: mientras haya capturas abiertas, evita que un grab (modal) bloquee el enfoque.
        Revienta cualquier grab activo (grab_set/grab_set_global) que se haya quedado.
        """
        self._asegurar_admin_capturas()

        if self._guardian_grab_id is not None:
            return

        def _tick():
            # si ya no hay capturas, parar
            try:
                vivos = []
                for w in list(self._capturas_abiertas):
                    if w is not None and w.winfo_exists():
                        vivos.append(w)
                self._capturas_abiertas = vivos
            except Exception:
                self._capturas_abiertas = []

            if not self._capturas_abiertas:
                self._detener_guardian_grab()
                return

            # 1) Revienta cualquier grab activo (esto es lo que impide enfocar otras ventanas)
            try:
                g = self._interfaz.master.grab_current()
                if g is not None:
                    try:
                        g.grab_release()
                    except Exception:
                        pass
            except Exception:
                pass

            # 2) Asegura que ninguna captura quede "topmost" (si algún código lo pone)
            for w in list(self._capturas_abiertas):
                try:
                    w.attributes("-topmost", False)
                except Exception:
                    pass

            # reprogramar
            try:
                self._guardian_grab_id = self._interfaz.master.after(120, _tick)
            except Exception:
                self._guardian_grab_id = None

        # arrancar
        try:
            self._guardian_grab_id = self._interfaz.master.after(0, _tick)
        except Exception:
            self._guardian_grab_id = None

    def _detener_guardian_grab(self):
        self._asegurar_admin_capturas()
        try:
            if self._guardian_grab_id is not None:
                self._interfaz.master.after_cancel(self._guardian_grab_id)
        except Exception:
            pass
        self._guardian_grab_id = None