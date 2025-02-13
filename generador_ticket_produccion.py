import os
import textwrap
import subprocess

class GeneradorTicketProduccion:
    def __init__(self, ancho_max=32):
        self._cliente = ''
        self._pedido = None
        self._venta = None
        self._entrega = None
        self._capturista = None
        self._ruta = None
        self._ruta_archivo = None
        self._colonia = ''
        self._ancho_max = ancho_max  # Ancho configurable
        self.productos = []
        self._relacionado = ''
        self._tipo = ''
        self._areas = ''
        self._parcial = False
        self._areas_aplicables = ''
        self._tipo_entrega = ''
        self._ticket_simple = False

    @property
    def ticket_simple(self):
        return self._ticket_simple

    @ticket_simple.setter
    def ticket_simple(self, value):
        self._ticket_simple = value

    @property
    def tipo_entrega(self):
        return self._tipo_entrega

    @tipo_entrega.setter
    def tipo_entrega(self, value):
        self._tipo_entrega = value

    @property
    def areas(self):
        return self._areas

    @areas.setter
    def areas(self, value):
        self._areas = value

    @property
    def parcial(self):
        return self._parcial

    @parcial.setter
    def parcial(self, value):
        self._parcial = value

    @property
    def cliente(self):
        return self._cliente

    @cliente.setter
    def cliente(self, value):
        self._cliente = value

    @property
    def pedido(self):
        return self._pedido

    @pedido.setter
    def pedido(self, value):
        self._pedido = value

    @property
    def relacionado(self):
        return self._relacionado

    @relacionado.setter
    def relacionado(self, value):
        self._relacionado = value

    @property
    def venta(self):
        return self._venta

    @venta.setter
    def venta(self, value):
        self._venta = value

    @property
    def areas_aplicables(self):
        """
        Devuelve las áreas aplicables.
        """
        return self._areas_aplicables

    @areas_aplicables.setter
    def areas_aplicables(self, value):
        """
        Permite establecer las áreas aplicables. Asegura que el valor
        asignado sea un conjunto válido.
        """
        self._areas_aplicables = value

    @property
    def entrega(self):
        return self._entrega

    @entrega.setter
    def entrega(self, value):
        self._entrega = value

    @property
    def capturista(self):
        return self._capturista

    @capturista.setter
    def capturista(self, value):
        self._capturista = value

    @property
    def ruta(self):
        return self._ruta

    @ruta.setter
    def ruta(self, value):
        self._ruta = value

    @property
    def ruta_archivo(self):
        return self._ruta_archivo

    @ruta_archivo.setter
    def ruta_archivo(self, value):
        self._ruta_archivo = value

    @property
    def colonia(self):
        return self._colonia

    @colonia.setter
    def colonia(self, value):
        self._colonia = value

    @property
    def tipo(self):
        return self._tipo

    @tipo.setter
    def tipo(self, value):
        self._tipo = value

    @property
    def ancho_max(self):
        return self._ancho_max

    @ancho_max.setter
    def ancho_max(self, value):
        if value < 20 or value > 80:
            raise ValueError("El ancho debe estar entre 20 y 80 caracteres.")
        self._ancho_max = value

    # Función para configurar productos
    def set_productos(self, productos):
        """ Recibe una lista de diccionarios con clave, cantidad, descripción, unidad y observación """
        self.productos = productos

    # Generador del ticket
    def generar_ticket(self):
        separator = "-" * (self.ancho_max -4)
        encabezado = f"""
{self.cliente}
FOLIO:  {self.pedido}
TIPO: {self.tipo}
RELACION: {self.relacionado}
VENTA:   {self.venta}
ENTREGA: {self.entrega}
CAPTURISTA: {self.capturista}
RUTA: {self.ruta}
COLONIA: {self.colonia}
AREAS: {self.areas_aplicables}
T.ENTREGA: {self.tipo_entrega}
T.IMPRESION: {'PARCIAL' if self.parcial else 'TOTAL'}
{separator}
"""
        cuerpo = ""
        for producto in self.productos:
            clave = f"Clave: {producto['clave']}"
            desc = textwrap.fill(producto['descripcion'], self.ancho_max)
            cantidad = f"Cantidad: {producto['cantidad']} {producto['unidad']}"

            cuerpo += f"{clave}\n{desc}\n{cantidad}\n"
            observacion = producto.get("observacion","")
            observacion = observacion.strip()
            if observacion != "":
                obs = textwrap.fill(f"Obs: {producto['observacion']}", self.ancho_max)
                cuerpo += f"{obs}\n"

            cuerpo += separator + "\n"

        pie = "\n" * 25
        return encabezado + cuerpo + separator + pie + separator

    def generar_ticket_simple(self):
        separator = "-" * (self.ancho_max -4)
        # Encabezado solo con las áreas
        encabezado = (
            f"AREAS: {self.areas_aplicables}\n"
            f"{separator}\n"
        )

        # Cuerpo con productos
        cuerpo = ""
        for producto in self.productos:
            clave = f"Clave: {producto['clave']}"
            desc = textwrap.fill(producto['descripcion'], self.ancho_max)
            cantidad = f"Cantidad: {producto['cantidad']}"

            cuerpo += f"{clave}\n{desc}\n{cantidad}\n"
            cuerpo += separator + "\n"

        pie = "\n" * 20

        return encabezado + cuerpo + separator + pie + separator

    def _nombre_archivo(self):
        tipo_surtido = 'PARCIAL' if self.parcial else 'TOTAL'
        cliente = self.cliente.strip().replace('\n', '').replace(' ', '')
        return f"{cliente}_{self.pedido}_{tipo_surtido}_{self.areas}.txt"

    def imprimir(self, fuente_tamano=None, nombre_impresora=None):
        # Verifica y ajusta la ruta del archivo
        nombre_archivo = self._nombre_archivo()
        directorio = self._ruta_archivo if os.path.isdir(self._ruta_archivo) else os.path.expanduser("~/Documents")
        self._ruta_archivo = os.path.join(directorio, nombre_archivo)

        # Generar ticket y guardarlo
        ticket = self.generar_ticket() if not self._ticket_simple else self.generar_ticket_simple()
        try:
            with open(self._ruta_archivo, "w", encoding="utf-8") as file:
                file.write(ticket)
            print(f"Ticket guardado en '{self._ruta_archivo}'.")
        except Exception as e:
            print(f"Error al guardar el ticket: {e}")
            return

        # Preparar y enviar comando de impresión
        print("Enviando ticket a la impresora...")
        try:
            if os.name == 'nt':  # Windows
                # Forzar el uso de notepad /p
                comando = ['notepad', '/p', self._ruta_archivo]
                subprocess.run(comando, check=True)
            else:  # macOS / Linux
                comando = ['lp']
                if fuente_tamano:
                    comando.extend(['-o', f'cpi={fuente_tamano}'])
                if nombre_impresora:
                    comando.extend(['-d', nombre_impresora])
                comando.append(self._ruta_archivo)
                subprocess.run(comando, check=True)
            print("Ticket enviado a la impresora correctamente.")
        except subprocess.CalledProcessError as e:
            print(f"Error al enviar el ticket a la impresora: {e}")
        except Exception as e:
            print(f"Error inesperado al imprimir: {e}")
        finally:
            self._ticket_simple = False