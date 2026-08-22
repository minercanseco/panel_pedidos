import platform
import subprocess
import gzip
import os
import json

try:
    import win32print  # Solo en Windows
except Exception:
    win32print = None

from cayal.ventanas import Ventanas


class DefinirImpresoras:
    def __init__(
            self, master, ruta_archivo=None, al_guardar=None,
            impresora_primaria='', impresora_secundaria='',
            obligatoria=False, bloquear=True,
    ):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._ruta_archivo = ruta_archivo or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'impresoras.gz',
        )
        self._al_guardar = al_guardar
        self._impresora_primaria = str(impresora_primaria or '')
        self._impresora_secundaria = str(impresora_secundaria or '')
        self._obligatoria = bool(obligatoria)
        self._bloquear = bool(bloquear)
        self._cargar_componentes()
        self._cargar_eventos()
        self._rellenar_cbx_impresoras()
        self._ventanas.configurar_ventana_ttkbootstrap('Definir impresoras')
        self._master.protocol('WM_DELETE_WINDOW', self._cancelar)
        self._master.bind('<Escape>', lambda event: self._cancelar())
        if self._obligatoria and self._bloquear:
            self._master.after_idle(self._mostrar_como_modal)

    def _mostrar_como_modal(self):
        """Muestra el diálogo antes de bloquear la ventana principal."""
        try:
            padre = self._master.master
            self._master.deiconify()
            self._master.update_idletasks()

            ancho = max(self._master.winfo_reqwidth(), 360)
            alto = max(self._master.winfo_reqheight(), 160)
            x = padre.winfo_rootx() + max(
                0, (padre.winfo_width() - ancho) // 2
            )
            y = padre.winfo_rooty() + max(
                0, (padre.winfo_height() - alto) // 2
            )
            self._master.geometry('+{}+{}'.format(x, y))
            self._master.transient(padre)
            self._master.attributes('-topmost', True)
            self._master.lift()
            self._master.focus_force()
            self._master.grab_set()
            self._master.after(
                500,
                lambda: self._master.attributes('-topmost', False),
            )
        except Exception:
            # Si el gestor de ventanas no admite alguna operación visual,
            # conserva al menos el diálogo visible y al frente.
            try:
                self._master.deiconify()
                self._master.lift()
                self._master.focus_force()
            except Exception:
                pass

    def _cargar_componentes(self):
        componentes = [
            ('cbx_impresora1', 'Principal:'),
            ('cbx_impresora2', 'Secundaria:'),
            ('btn_guardar', 'Guardar')
        ]
        self._ventanas.crear_formulario_simple(componentes)

    def _cargar_eventos(self):
        eventos = {
            'btn_guardar': self._guardar_impresoras_seleccionadas,
            'btn_cancelar': self._cancelar,
        }
        self._ventanas.cargar_eventos(eventos)

    def _cancelar(self):
        if self._obligatoria:
            self._ventanas.mostrar_mensaje(
                'Debe configurar las impresoras principal y secundaria '
                'antes de continuar.',
                self._master,
            )
            return
        self._master.destroy()

    def _guardar_impresoras_seleccionadas(self):
        cbx_impresora1 = self._ventanas.obtener_input_componente('cbx_impresora1')
        cbx_impresora2 = self._ventanas.obtener_input_componente('cbx_impresora2')
        if not cbx_impresora1 or not cbx_impresora2:
            self._ventanas.mostrar_mensaje(
                'Seleccione la impresora principal y la secundaria.',
                self._master,
            )
            return

        self.guardar_impresoras(
            cbx_impresora1, cbx_impresora2, self._ruta_archivo
        )
        if callable(self._al_guardar):
            self._al_guardar(
                cbx_impresora1,
                cbx_impresora2,
                self._ruta_archivo,
            )

        self._master.destroy()

    def _rellenar_cbx_impresoras(self):
        impresoras = self._listar_impresoras()
        predeterminada = self._impresora_predeterminada()

        self._ventanas.rellenar_cbx('cbx_impresora1', impresoras or [], True)
        self._ventanas.rellenar_cbx('cbx_impresora2', impresoras or [], True)

        primaria = self._impresora_primaria or predeterminada
        secundaria = self._impresora_secundaria or primaria
        if primaria:
            self._ventanas.insertar_input_componente(
                'cbx_impresora1', primaria
            )
        if secundaria:
            self._ventanas.insertar_input_componente(
                'cbx_impresora2', secundaria
            )

    def _listar_impresoras(self):
        so = platform.system()
        try:
            if so == 'Windows' and win32print is not None:
                # PRINTER_ENUM_LOCAL (2) | PRINTER_ENUM_CONNECTIONS (4)
                flags = 2 | 4
                return sorted({p[2] for p in win32print.EnumPrinters(flags)})
            else:
                # macOS / Linux con CUPS
                salida = subprocess.check_output(['lpstat', '-a'], stderr=subprocess.DEVNULL)
                nombres = []
                for linea in salida.decode(errors='ignore').splitlines():
                    linea = linea.strip()
                    if not linea:
                        continue
                    nombre = linea.split()[0]
                    nombres.append(nombre)
                return sorted(set(nombres))
        except Exception:
            return []

    def _impresora_predeterminada(self):
        so = platform.system()
        try:
            if so == 'Windows' and win32print is not None:
                return win32print.GetDefaultPrinter()
            else:
                salida = subprocess.check_output(['lpstat', '-d'], stderr=subprocess.DEVNULL).decode(errors='ignore')
                partes = salida.strip().split(':', 1)
                if len(partes) == 2:
                    return partes[1].strip()
                return None
        except Exception:
            impresoras = self._listar_impresoras()
            return impresoras[0] if impresoras else None

    def guardar_impresoras(self, impresora_primaria: str, impresora_secundaria: str, ruta_archivo: str = "impresoras.gz"):
        """
        Guarda los nombres de dos impresoras (primaria y secundaria) en un archivo comprimido gzip.
        Si el archivo no existe, se crea.
        """

        datos = {
            "primaria": impresora_primaria,
            "secundaria": impresora_secundaria
        }
        os.makedirs(os.path.dirname(os.path.abspath(ruta_archivo)), exist_ok=True)
        with gzip.open(ruta_archivo, "wt", encoding="utf-8") as f:
            json.dump(datos, f)
        print(f"✅ Archivo de impresoras guardado en {os.path.abspath(ruta_archivo)}")
