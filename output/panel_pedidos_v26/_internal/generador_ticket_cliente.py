import os
import subprocess
import sys
import urllib.parse


class GeneradorTicketCliente:
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
        self._calle = ''
        self._numero = ''
        self._total = 0
        self._comentario = ''
        self._forma_pago = ''
        self._forma_pago_id = 0

    @property
    def forma_pago_id(self):
        return self._forma_pago_id

    @forma_pago_id.setter
    def forma_pago_id(self, value):
        self._forma_pago_id = value

    @property
    def comentario(self):
        """Obtiene el comentario."""
        return self._comentario

    @comentario.setter
    def comentario(self, value):
        """Establece el comentario."""
        self._comentario = value

    @property
    def calle(self):
        return self._calle

    @calle.setter
    def calle(self, value):
        self._calle = value

    @property
    def numero(self):
        return self._numero

    @numero.setter
    def numero(self, value):
        self._numero = value

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
    def venta(self):
        return self._venta

    @venta.setter
    def venta(self, value):
        self._venta = value

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
    def ruta_archivo(self):
        return self._ruta_archivo

    @ruta_archivo.setter
    def ruta_archivo(self, value):
        self._ruta_archivo = value

    @property
    def forma_pago(self):
        return self._forma_pago

    @forma_pago.setter
    def forma_pago(self, value):
        self._forma_pago = value

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
    def total(self):
        return self._total

    @total.setter
    def total(self, value):
        self._total = value

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

    def generar_ticket(self):
        # Crear el encabezado del ticket
        encabezado = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ticket de Venta</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                font-size: 12px;
                margin: 0;
                padding: 0;
            }}
            .ticket {{
                max-width: 300px;
                margin: 0 auto;
                border: 1px solid #000;
                padding: 10px;
                box-shadow: 0 0 5px rgba(0, 0, 0, 0.3);
            }}
            .separator {{
                border-top: 1px dashed #000;
                margin: 10px 0;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            table th, table td {{
                text-align: left;
                padding: 5px;
            }}
            table th {{
                border-bottom: 1px solid #000;
            }}
            .observacion {{
                font-size: 10px; /* Tamaño de fuente 8px */
                color: #000000; /* Color negro */
                font-weight: bold; /* Negritas */
                margin-top: 5px;
            }}
            .footer {{
                text-align: center;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
    <div class="ticket">
        <div class="header" style="text-align: center;">
        <img src="data:image/png;base64, {self._icono_cayal()}" alt="Imagen" style="max-width: 100%; height: auto;">
            <p><strong>{self.cliente}</strong></p>
            <p><strong>FOLIO:</strong> {self.pedido}</p>
            <p><strong>TIPO PEDIDO:</strong> {self._tipo}</p>
            <p><strong>VENTA:</strong> {self.venta}</p>
            <p><strong>ENTREGA:</strong> {self.entrega}</p>
            <p><strong>CAPTURISTA:</strong> {self.capturista}</p>
             <p><strong>FORMA PAGO:</strong> {self.forma_pago}</p>
            <p><strong>DIRECCIÓN:</strong></p>
            <p>{self.calle} {self.numero}, {self.colonia}</p>
        </div>
        <div class="separator"></div>
        <p>{self.comentario}</p>
        <div class="separator"></div>
        <table>
            <thead>
                <tr>
                    <th>Cantidad</th>
                    <th>Unidad</th>
                    <th>Producto</th>
                    <th>Precio</th>
                    <th>Total</th> <!-- Nueva columna Total -->
                </tr>
            </thead>
            <tbody>
    """

        # Crear el cuerpo del ticket
        total_general = 0  # Variable para acumular el total general
        cuerpo = ""
        for producto in self.productos:
            cantidad = producto['cantidad']
            unidad = producto['ClaveUnidad']
            descripcion = producto['ProductName']
            precio = producto.get('precio', 0.00)
            total_producto = cantidad * precio  # Calcular el total por producto
            total_general += total_producto  # Acumular el total general

            observacion = producto.get("Comments", "").replace('\n', '').replace('\r', '').strip()
            observacion = observacion.replace('ESPECIFICACIÓN:', '').strip()

            # Fila del producto
            cuerpo += f"""
                <tr>
                    <td>{cantidad}</td>
                    <td>{unidad}</td>
                    <td>{descripcion}</td>
                    <td style="text-align: right;">${precio:.2f}</td>
                    <td style="text-align: right;">${total_producto:.2f}</td> <!-- Total por producto -->
                </tr>
            """
            # Observación debajo del producto (si existe)
            if observacion:
                cuerpo += f"""
                <tr>
                    <td colspan="5" class="observacion">OBS: {observacion}</td>
                </tr>
                """
            # Separador entre productos
            cuerpo += """
                <tr>
                    <td colspan="5"><div class="separator"></div></td>
                </tr>
            """

        # Crear el pie del ticket con el total
        footer = f"""
            </tbody>
        </table>
        <div class="separator"></div>
        <p style="text-align: right;"><strong>TOTAL APROXIMADO:</strong> ${self._total:.2f}</p> <!-- Total general -->
        <div class="separator"></div>
        <div class="footer">
            <p><strong><em>Nota:</em></strong> <em>El monto es aproximado, ya que los productos de gramaje pueden variar el total al momento de surtir el pedido.</em></p>
            <p><strong><em>Nota:</em></strong> <em>Este documento es una orden de pedido y no es un comprobante fiscal.</em></p>
            <p><strong><em>Gracias por su preferencia.</em></strong></p>
        </div>
    </div>
    </body>
    </html>
    """

        # Retornar el HTML completo
        return encabezado + cuerpo + footer

    def generar_ticket_transferencia(self):
        # Crear el encabezado del ticket
        encabezado = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ticket de Venta</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                font-size: 12px;
                margin: 0;
                padding: 0;
            }}
            .ticket {{
                max-width: 300px;
                margin: 0 auto;
                border: 1px solid #000;
                padding: 10px;
                box-shadow: 0 0 5px rgba(0, 0, 0, 0.3);
            }}
            .separator {{
                border-top: 1px dashed #000;
                margin: 10px 0;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            table th, table td {{
                text-align: left;
                padding: 5px;
            }}
            table th {{
                border-bottom: 1px solid #000;
            }}
            .observacion {{
                font-size: 10px; /* Tamaño de fuente 8px */
                color: #000000; /* Color negro */
                font-weight: bold; /* Negritas */
                margin-top: 5px;
            }}
            .footer {{
                text-align: center;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
    <div class="ticket">
        <div class="header" style="text-align: center;">
        <img src="data:image/png;base64, {self._icono_cayal()}" alt="Imagen" style="max-width: 100%; height: auto;">
            <p><strong>{self.cliente}</strong></p>
            <p><strong>FOLIO:</strong> {self.pedido}</p>
            <p><strong>TIPO PEDIDO:</strong> {self._tipo}</p>
            <p><strong>VENTA:</strong> {self.venta}</p>
            <p><strong>ENTREGA:</strong> {self.entrega}</p>
            <p><strong>CAPTURISTA:</strong> {self.capturista}</p>
             <p><strong>FORMA PAGO:</strong> {self.forma_pago}</p>
            <p><strong>DIRECCIÓN:</strong></p>
            <p>{self.calle} {self.numero}, {self.colonia}</p>
        </div>
        <div class="separator"></div>
        <p>{self.comentario}</p>
        <div class="separator"></div>
        <table>
            <thead>
                <tr>
                    <th>Cantidad</th>
                    <th>Unidad</th>
                    <th>Producto</th>
                    <th>Precio</th>
                    <th>Total</th> <!-- Nueva columna Total -->
                </tr>
            </thead>
            <tbody>
    """

        # Crear el cuerpo del ticket
        total_general = 0  # Variable para acumular el total general
        cuerpo = ""
        for producto in self.productos:
            cantidad = producto['cantidad']
            unidad = producto['ClaveUnidad']
            descripcion = producto['ProductName']
            precio = producto.get('precio', 0.00)
            total_producto = cantidad * precio  # Calcular el total por producto
            total_general += total_producto  # Acumular el total general

            observacion = producto.get("Comments", "").replace('\n', '').replace('\r', '').strip()
            observacion = observacion.replace('ESPECIFICACIÓN:', '').strip()

            # Fila del producto
            cuerpo += f"""
                <tr>
                    <td>{cantidad}</td>
                    <td>{unidad}</td>
                    <td>{descripcion}</td>
                    <td style="text-align: right;">${precio:.2f}</td>
                    <td style="text-align: right;">${total_producto:.2f}</td> <!-- Total por producto -->
                </tr>
            """
            # Observación debajo del producto (si existe)
            if observacion:
                cuerpo += f"""
                <tr>
                    <td colspan="5" class="observacion">OBS: {observacion}</td>
                </tr>
                """
            # Separador entre productos
            cuerpo += """
                <tr>
                    <td colspan="5"><div class="separator"></div></td>
                </tr>
            """

        # Crear el pie del ticket con el total
        footer = f"""
            </tbody>
        </table>
        <div class="separator"></div>
        
        <div class="separator"></div>
        <div class="footer">
            <p><strong><em>Nota:</em></strong> <em>El monto es aproximado, ya que los productos de gramaje pueden variar el total al momento de surtir el pedido.</em></p>
            <p><strong><em>Nota:</em></strong> <em>Este documento es una orden de pedido y no es un comprobante fiscal.</em></p>
            <p><strong><em>Gracias por su preferencia.</em></strong></p>
        </div>
    </div>
    </body>
    </html>
    """

        # Retornar el HTML completo
        return encabezado + cuerpo + footer


    def _nombre_archivo(self):
        cliente = self.cliente.strip().replace('\n', '').replace(' ', '')
        return f"{cliente}_{self.pedido}.html"

    def guardar_archivo(self):
        # Verifica y ajusta la ruta del archivo
        nombre_archivo = self._nombre_archivo()
        directorio = self._ruta_archivo if os.path.isdir(self._ruta_archivo) else os.path.expanduser("~/Documents")
        self._ruta_archivo = os.path.join(directorio, nombre_archivo)

        # Generar ticket y guardarlo
        ticket = self.generar_ticket() if self.forma_pago_id != 6 else self.generar_ticket_transferencia()
        try:
            with open(self._ruta_archivo, "w", encoding="utf-8") as file:
                file.write(ticket)
            print(f"Ticket guardado en '{self._ruta_archivo}'.")
            self.copy_file_to_clipboard(self._ruta_archivo)
        except Exception as e:
            print(f"Error al guardar el ticket: {e}")
            return

    def _icono_cayal(self):
        return """
        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
        """

    def copy_file_to_clipboard(self, file_path):
        # Detectar el sistema operativo
        if sys.platform == "darwin":  # macOS
            # Usar AppleScript para copiar el archivo al portapapeles
            applescript = f'''
            set theFile to POSIX file "{file_path}"
            set the clipboard to theFile
            '''
            try:
                subprocess.run(['osascript', '-e', applescript], check=True)
                print("El archivo ha sido copiado al portapapeles en macOS.")
            except subprocess.CalledProcessError:
                print("Error al intentar copiar el archivo al portapapeles en macOS.")

        elif sys.platform == "win32":  # Windows
            # En Windows, no podemos copiar el archivo directamente al portapapeles con facilidad.
            # Vamos a copiar solo la ruta del archivo al portapapeles usando pyperclip.
            file_path = self.url_to_windows_path(file_path)
            import pyperclip
            try:
                pyperclip.copy(file_path)
                print("La ruta del archivo ha sido copiada al portapapeles en Windows.")
            except pyperclip.PyperclipException:
                print("Error al intentar copiar la ruta del archivo al portapapeles en Windows.")
        else:
            print(f"El sistema operativo {sys.platform} no es compatible con esta función.")

    def url_to_windows_path(self, url):
        try:
            # Remover el prefijo "file:///"
            if url.startswith("file:///"):
                url = url[8:]  # Remueve "file://"

            # Decodificar caracteres escapados (%20 -> espacio, etc.)
            path = urllib.parse.unquote(url)

            # Convertir las barras inclinadas (/) en barras invertidas (\)
            windows_path = path.replace("/", "\\")
            return windows_path
        except Exception as e:
            print(f"Error al convertir la URL a ruta de Windows: {e}")
            return None

