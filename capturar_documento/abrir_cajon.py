import platform
if platform.system() != 'Darwin':
    import win32print


class CajonCobro:
    def __init__(self, nombre_impresora):
        """
        Inicializa la clase con el nombre de la impresora térmica.
        """
        self.nombre_impresora = nombre_impresora

    def abrir_cajon(self):
        """
        Abre el cajón de dinero enviando un comando ESC/POS a la impresora térmica.
        """
        try:
            # Código de escape para abrir el cajón (puede variar según la impresora)
            comando_abrir_cajon = b'\x1B\x70\x00\x19\xFA'  # Epson estándar

            # Abrir conexión con la impresora
            handle = win32print.OpenPrinter(self.nombre_impresora)
            printer_info = win32print.GetPrinter(handle, 2)
            printer_name = printer_info["pPrinterName"]

            # Enviar comando a la impresora
            hprinter = win32print.OpenPrinter(printer_name)
            hprinter_job = win32print.StartDocPrinter(hprinter, 1, ("Abrir Cajón", None, "RAW"))
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(hprinter, comando_abrir_cajon)
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
            win32print.ClosePrinter(hprinter)
            print("Cajón de dinero abierto correctamente.")
        except Exception as e:
            print(f"Error al abrir el cajón: {e}")