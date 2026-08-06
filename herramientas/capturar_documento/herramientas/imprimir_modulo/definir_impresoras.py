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
    def __init__(self, master):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._cargar_componentes()
        self._cargar_eventos()
        self._rellenar_cbx_impresoras()
        self._ventanas.configurar_ventana_ttkbootstrap('Definir impresoras')

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
            'btn_cancelar':self._master.destroy
        }
        self._ventanas.cargar_eventos(eventos)

    def _guardar_impresoras_seleccionadas(self):
        cbx_impresora1 = self._ventanas.obtener_input_componente('cbx_impresora1')
        cbx_impresora2 = self._ventanas.obtener_input_componente('cbx_impresora2')
        base_dir = os.path.dirname(os.path.abspath(__file__))
        ruta_archivo = os.path.join(base_dir,"impresoras.gz")

        self.guardar_impresoras(cbx_impresora1, cbx_impresora2, ruta_archivo)

        self._master.destroy()

    def _rellenar_cbx_impresoras(self):
        impresoras = self._listar_impresoras()
        predeterminada = self._impresora_predeterminada()

        self._ventanas.rellenar_cbx('cbx_impresora1', impresoras or [], True)
        self._ventanas.rellenar_cbx('cbx_impresora2', impresoras or [], True)

        if predeterminada:
            self._ventanas.insertar_input_componente('cbx_impresoras', predeterminada)

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
        with gzip.open(ruta_archivo, "wt", encoding="utf-8") as f:
            json.dump(datos, f)
        print(f"✅ Archivo de impresoras guardado en {os.path.abspath(ruta_archivo)}")

