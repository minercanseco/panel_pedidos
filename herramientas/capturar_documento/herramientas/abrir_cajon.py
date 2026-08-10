import platform
if platform.system() != 'Darwin':
    import win32print


class CajonCobro:
    def __init__(self, nombre_impresora):
        """
        Inicializa la clase con el nombre de la impresora térmica.
        """
        self.nombre_impresora = nombre_impresora
        self.ultimo_error = ''

    def abrir_cajon(self):
        """
        Abre el cajón de dinero enviando un comando ESC/POS a la impresora térmica.
        """
        hprinter = None
        try:
            self.ultimo_error = ''
            # Código de escape para abrir el cajón (puede variar según la impresora)
            comando_abrir_cajon = b'\x1B\x70\x00\x19\xFA'  # Epson estándar

            # Enviar comando a la impresora
            hprinter = win32print.OpenPrinter(self.nombre_impresora)
            win32print.StartDocPrinter(
                hprinter, 1, ("Abrir Cajón", None, "RAW")
            )
            win32print.StartPagePrinter(hprinter)
            win32print.WritePrinter(hprinter, comando_abrir_cajon)
            win32print.EndPagePrinter(hprinter)
            win32print.EndDocPrinter(hprinter)
            print("Cajón de dinero abierto correctamente.")
            return True
        except Exception as e:
            self.ultimo_error = str(e)
            print(f"Error al abrir el cajón: {e}")
            return False
        finally:
            if hprinter is not None:
                try:
                    win32print.ClosePrinter(hprinter)
                except Exception:
                    pass
