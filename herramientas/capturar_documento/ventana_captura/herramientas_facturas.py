import tkinter as tk

from cayal.cliente import Cliente
from cayal.ventanas import Ventanas

from herramientas.capturar_documento.herramientas_captura.editar_direccion_documento import EditarDireccionDocumento
from herramientas.capturar_documento.herramientas_captura.historial_cliente import HistorialCliente
from herramientas.cliente.notebook_cliente import NoteBookCliente
from herramientas.verificador_precios.controlador_verificador import ControladorVerificador
from herramientas.verificador_precios.interfaz_verificador import InterfazVerificador


class HerramientasFacturas:
    def __init__(self, master, modelo, interfaz, cargar_shortcuts):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._modelo = modelo
        self._interfaz = interfaz
        self._cargar_shortcuts = cargar_shortcuts

        self._base_de_datos = self._modelo.base_de_datos
        self._parametros = self._modelo.parametros
        self._utilerias = self._modelo.utilerias


        self._crear_frames()
        self._crear_barra_herramientas()
        self._cargar_eventos()
        if self._cargar_shortcuts:
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
                'nombre_icono': 'EditAddress32.ico',
                'etiqueta': 'E.Dirección',
                'nombre': 'editar_direccion',
                'hotkey': '[F4]',
                'comando': self._editar_direccion_documento,
            },
            {
                'nombre_icono': 'DocumentEdit32.ico',
                'etiqueta': 'Editar Cliente',
                'nombre': 'editar_cliente',
                'hotkey': '[F6]',
                'comando': self._editar_cliente,
            },
            {
                'nombre_icono': 'CampaignFlow32.ico',
                'etiqueta': 'H.Cliente',
                'nombre': 'historial_cliente',
                'hotkey': '[F7]',
                'comando': self._historial_cliente,
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

    def _cargar_eventos(self):
        eventos = {
            'cbx_formapago': lambda event: self._actualizar_forma_pago()
        }
        self._ventanas.cargar_eventos(eventos)

        ancho, alto = self._interfaz.ventanas.obtener_resolucion_pantalla()

        if ancho > 1367:
            txt_comentario_pedido = self._interfaz.ventanas.componentes_forma['txt_comentario_documento']
            txt_comentario_pedido.bind("<FocusOut>", lambda event: self._actualizar_comentario_pedido())

    def _agregar_atajos(self):
        eventos = {
            'F3': lambda: self._verificador_precios(),
            'F4': lambda: self._editar_direccion_documento(),
            'F6': lambda: self._editar_cliente(),
            'F7': lambda: self._historial_cliente(),
            'F12': lambda: self._cobrar_nota(),
        }

        self._ventanas.agregar_hotkeys_forma(eventos)

    def _actualizar_comentario_pedido(self):
        comentario = self._ventanas.obtener_input_componente('txt_comentario_documento')
        comentario = comentario.upper().strip() if comentario else ''
        self._modelo.documento.comments = comentario

    def _actualizar_forma_pago(self):
        if self._modelo.documento.cfd_type_id == 1:
            return

        clave = self._modelo.documento.forma_pago
        fp_seleccionada = self._ventanas.obtener_input_componente('cbx_formapago')
        consulta_clave_seleccionada =  [reg['Clave'] for reg in self._modelo.consulta_formas_pago
                                        if fp_seleccionada == reg['Value']]
        if consulta_clave_seleccionada:
            clave_seleccionada = str(consulta_clave_seleccionada[0])

            if clave != '99' and clave_seleccionada == '99':
                consulta_valor_documento = [reg['Value'] for reg in self._modelo.consulta_formas_pago
                                        if clave == reg['Clave']]
                if consulta_valor_documento:
                    valor_documento = consulta_valor_documento[0]

                    self._ventanas.mostrar_mensaje('La forma de pago 99 solo es válida con método de pago PPD.')
                    self._ventanas.insertar_input_componente('cbx_formapago', valor_documento)
                    return

            self._modelo.documento.forma_pago = clave_seleccionada
            self._ventanas.insertar_input_componente('cbx_formapago', fp_seleccionada)

    # -----------------------------------------------------------
    # Funciones relacionadas con la sección
    # -----------------------------------------------------------
    def _verificador_precios(self):
        ventana = self._ventanas.crear_popup_ttkbootstrap(titulo='Verificador precios')
        interfaz = InterfazVerificador(ventana)
        controlador = ControladorVerificador(interfaz, self._parametros)


    def _editar_direccion_documento(self):
        if self._modelo.cliente.addresses == 1:
            self._ventanas.mostrar_mensaje('Use la herramienta editar cliente para agregar una dirección adicional.')
            return

        try:
            ventana = self._ventanas.crear_popup_ttkbootstrap(titulo='Editar Dirección')
            instancia = EditarDireccionDocumento(ventana,
                                                 self._modelo,
                                                 self._interfaz
                                                 )
            ventana.wait_window()
        except Exception as e:
            self._ventanas.mostrar_mensaje(
                f'Ocurrió un error al editar la dirección:\n{e}'
            )

    def _editar_cliente(self):

        self._parametros.id_principal = self._modelo.cliente.business_entity_id
        try:
            ventana = self._ventanas.crear_popup_ttkbootstrap()
            cliente = Cliente()
            NoteBookCliente(
                ventana,
                self._base_de_datos,
                self._parametros,
                self._utilerias,
                cliente
            )
            ventana.wait_window()
        finally:
            self._parametros.id_principal = 0

    def _historial_cliente(self):

        ventana = self._ventanas.crear_popup_ttkbootstrap(titulo='Historial cliente')
        HistorialCliente(ventana,
                         self._modelo.base_de_datos,
                         self._modelo.utilerias,
                         self._modelo.cliente.business_entity_id
                         )
        ventana.wait_window()

    def _cobrar_nota(self):
        pass