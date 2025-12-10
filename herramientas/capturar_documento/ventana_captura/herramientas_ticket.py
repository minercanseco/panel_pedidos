import tkinter as tk
from cayal.ventanas import Ventanas


class HerramientasTicket:
    def __init__(self, master, modelo, interfaz):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._modelo = modelo
        self._interfaz = interfaz

        self._base_de_datos = self._modelo.base_de_datos
        self._parametros = self._modelo.parametros
        self._utilerias = self._modelo.utilerias


        self._crear_frames()
        self._crear_barra_herramientas()
        self._agregar_atajos()

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'pady': 5, 'padx': 5, 'sticky': tk.NSEW}),

            'frame_herramientas': ('frame_principal', None,
                                  {'row': 0, 'column': 0, 'columnspan': 2, 'pady': 2, 'padx': 2,
                                   'sticky': tk.NSEW})
        }
        self._ventanas.crear_frames(frames)

    def _crear_barra_herramientas(self):
        herramientas = [
            {
                'nombre_icono': 'Barcode32.ico',
                'etiqueta': 'V.Precios',
                'nombre': 'verificador_precios',
                'hotkey': '[F3]',
                'comando': self._verificador_precios,
            },
            {
                'nombre_icono': 'Finance32.ico',
                'etiqueta': 'Cobrar',
                'nombre': 'cobrar_nota',
                'hotkey': '[F12]',
                'comando': self._cobrar_nota,
            },
        ]

        self.barra_herramientas_pedido = herramientas
        self.elementos_barra_herramientas = self._ventanas.crear_barra_herramientas(
            self.barra_herramientas_pedido,
            'frame_herramientas'
        )
        self.iconos_barra_herramientas = self.elementos_barra_herramientas[0]
        self.hotkeys_barra_herramientas = self.elementos_barra_herramientas[1]
        self.etiquetas_barra_herramientas = self.elementos_barra_herramientas[2]

    def _agregar_atajos(self):
        eventos = {
            'F3': lambda: self._verificador_precios(),
            'F12': lambda: self._cobrar_nota(),
        }

        self._ventanas.agregar_hotkeys_forma(eventos)

    # -----------------------------------------------------------
    # Funciones relacionadas con la sección
    # -----------------------------------------------------------
    def _verificador_precios(self):
        ventana = self._ventanas.crear_popup_ttkbootstrap(self._master)
        vista = InterfazVerificador(ventana)
        controlador = ControladorVerificador(vista, self._parametros)

    def _cobrar_nota(self):
        if self.documento.document_id == 0:
            self._ventanas.mostrar_mensaje('Debe por lo menos capturar un producto.')
            return

        if not self._cobrando:
            try:
                self._cobrando = True

                self.base_de_datos.command("""
                    UPDATE docDocument SET Balance = ?,
                                            Total = ?,
                                            TotalPaid = ?  
                    WHERE DocumentID = ?
                """, (
                    self.documento.total,
                    self.documento.total,
                    0,
                    self.documento.document_id
                ))

                self._parametros.id_principal = self.documento.document_id

                ventana = self._ventanas.crear_popup_ttkbootstrap()
                interfaz = InterfazCobroRapido(ventana)
                controlador = ControladorCobroRapido(interfaz, self._parametros)
                ventana.wait_window()

                self._documento_cobrado = controlador.documento_cobrado
                self.documento.amount_received = controlador.monto_recibido
                self.documento.customer_change = controlador.cambio_cliente

            finally:
                self._cobrando = False

                self._parametros.id_principal = 0

                if self._documento_cobrado:
                    self._interfaz.master.destroy()

