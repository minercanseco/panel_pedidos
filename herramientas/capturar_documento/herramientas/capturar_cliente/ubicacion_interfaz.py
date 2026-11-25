import threading
import queue
import webbrowser
from cayal.ventanas import Ventanas
from .ubicacion import extraer_ubicacion, enlace_mapa, enlace_desde_texto


class CapturaUbicacion:
    def __init__(self, ventanas, ubicacion, al_aceptar):
        self._aceptar = al_aceptar
        self._ubicacion_original = dict(ubicacion)
        self._enlace_original = (enlace_mapa(ubicacion)
                                 if ubicacion.get('Latitude') is not None
                                 and ubicacion.get('Longitude') is not None else '')
        self._pendiente = False
        self.master = ventanas.crear_popup_ttkbootstrap(titulo='Ubicación de la dirección')
        self.ventanas = Ventanas(self.master)
        self.ventanas.crear_frames({
            'frame_principal': ('master', 'Ubicación:',
                                {'row': 0, 'column': 0, 'padx': 10, 'pady': 10}),
            'frame_botones': ('master', None, {'row': 1, 'column': 0, 'padx': 10, 'pady': 10})})
        self.ventanas.crear_componentes({
            'txt_enlace': ('frame_principal', None, 'Enlace de Maps / WhatsApp:', None),
            'btn_mapa': ('frame_botones', 'info', 'Ver en Maps', None),
            'btn_aceptar': ('frame_botones', 'success', 'Aceptar', None),
            'btn_cancelar': ('frame_botones', 'danger', 'Cancelar', None)})
        self.ventanas.ajustar_ancho_componente('txt_enlace', 55)
        self.ventanas.ajustar_alto_componente('txt_enlace', 3)
        self.ventanas.insertar_input_componente('txt_enlace', self._enlace_original)
        self.ventanas.cargar_eventos({
            'btn_mapa': self._ver_mapa,
            'btn_aceptar': self._guardar,
            'btn_cancelar': self.master.destroy})
        self.ventanas.enfocar_componente('txt_enlace')

    def _ver_mapa(self):
        texto = self.ventanas.obtener_input_componente('txt_enlace').strip()
        try:
            webbrowser.open(enlace_desde_texto(texto))
        except ValueError as exc:
            self.ventanas.mostrar_mensaje(str(exc))

    def _guardar(self):
        if self._pendiente:
            return
        texto = self.ventanas.obtener_input_componente('txt_enlace').strip()
        if not texto:
            self.ventanas.mostrar_mensaje('Pegue un enlace de ubicación de Maps o WhatsApp.')
            return
        self._pendiente = True
        for nombre in ('btn_aceptar', 'btn_mapa'):
            self.ventanas.componentes_forma[nombre].configure(state='disabled')
        self.ventanas.bloquear_componente('txt_enlace')
        resultados = queue.Queue()

        def interpretar():
            try:
                # Al aceptar el enlace precargado conservar también su precisión interna.
                ubicacion = (dict(self._ubicacion_original) if texto == self._enlace_original
                             else extraer_ubicacion(texto))
                resultados.put((ubicacion, None))
            except Exception as exc:
                resultados.put((None, str(exc)))

        def revisar():
            if not self.master.winfo_exists():
                return
            try:
                ubicacion, error = resultados.get_nowait()
            except queue.Empty:
                self.master.after(100, revisar)
                return
            self._pendiente = False
            for nombre in ('btn_aceptar', 'btn_mapa'):
                self.ventanas.componentes_forma[nombre].configure(state='normal')
            self.ventanas.desbloquear_componente('txt_enlace')
            if error:
                self.ventanas.mostrar_mensaje(error)
                return
            try:
                self._aceptar(ubicacion)
            except ValueError as exc:
                self.ventanas.mostrar_mensaje(str(exc))
                return
            self.master.destroy()

        threading.Thread(target=interpretar, daemon=True).start()
        self.master.after(100, revisar)
