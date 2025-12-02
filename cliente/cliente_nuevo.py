import tkinter as tk
from cayal.cliente import Cliente
from cayal.ventanas import Ventanas
from cliente.buscar_info_cif import BuscarInfoCif
from cliente.notebook_cliente import NoteBookCliente


class ClienteNuevo:
    def __init__(self, master, parametros, base_de_datos, utilerias):
        self._master = master

        self._parametros = parametros
        self._utilerias = utilerias
        self._base_de_datos = base_de_datos
        self._cliente = Cliente()
        self._ventanas = Ventanas(self._master)

        self._crear_frames()
        self._crear_componentes()
        self._rellenar_componentes()
        self._cargar_eventos()
        self._ajustar_apariencia()
        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Nuevo')


    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.W}),

            'frame_componentes': ('frame_principal', 'Generales:',
                                  {'row': 1, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.W}),

            'frame_tipo': ('frame_componentes', 'Tipo captura:',
                             {'row': 0, 'column': 0, 'columnspan': 2,'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_manual': ('frame_componentes', 'Manual:',
                                  {'row': 1, 'column': 0, 'columnspan': 2, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_cedula': ('frame_componentes', 'Cedula:',
                                  {'row': 2, 'column': 0, 'columnspan': 2,'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_botones': ('frame_componentes', None,
                              {'row': 4, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW})
        }

        self._ventanas.crear_frames(frames)

    def _crear_componentes(self):
        componentes = {
            'cbx_tipo': ('frame_tipo', None, '     ', None),

            'tbx_cliente': ('frame_manual', None, 'Cliente:', None),
            'cbx_documento': ('frame_manual', None, 'Documento:', None),

            'tbx_cif': ('frame_cedula', None, 'CIF', None),
            'tbx_rfc': ('frame_cedula', None, 'RFC:', None),

            'btn_aceptar': ('frame_botones', None, 'Aceptar', None),
            'btn_cancelar': ('frame_botones', 'danger', 'Cancelar', None),
        }

        self._ventanas.crear_componentes(componentes)

    def _rellenar_componentes(self):
        tipos = ['Manual','Cédula Fiscal']
        self._ventanas.rellenar_cbx('cbx_tipo', tipos, sin_seleccione=False)

        documentos = ['Remisión', 'Factura']
        self._ventanas.rellenar_cbx('cbx_documento', documentos, sin_seleccione=True)

    def _cargar_eventos(self):
        eventos = {
            'btn_cancelar':self._master.destroy,
            'btn_aceptar':self._capturar_cliente,
            'cbx_tipo': lambda event:self._ajustar_apariencia()
        }

        self._ventanas.cargar_eventos(eventos)

    def _ajustar_apariencia(self):

        def apariencia_inicial():
            self._ventanas.ocultar_frame('frame_manual')
            self._ventanas.ocultar_frame('frame_cedula')

        tipo = self._ventanas.obtener_input_componente('cbx_tipo')
        if tipo == 'Seleccione':
            apariencia_inicial()

        if tipo == 'Cédula Fiscal':
            apariencia_inicial()
            self._ventanas.posicionar_frame('frame_cedula')

        if tipo == 'Manual':
            apariencia_inicial()
            self._ventanas.posicionar_frame('frame_manual')

    def _capturar_cliente(self):
        tipo = self._ventanas.obtener_input_componente('cbx_tipo')

        if tipo == 'Cédula Fiscal':
            if not self._validaciones_captura_cedula_fiscal():
                return

            rfc = self._ventanas.obtener_input_componente('tbx_rfc').strip()
            cif = self._ventanas.obtener_input_componente('tbx_cif').strip()

            ventana = self._ventanas.crear_popup_ttkbootstrap('Scrapper CIF',ocultar_master=True)
            instancia = BuscarInfoCif(ventana, self._parametros, rfc, cif, self._cliente)
            ventana.wait_window()

            self._settear_valores_cliente_factura(
                self._cliente.official_name,
                self._cliente.official_number,
                self._cliente.cif

            )
            self._llamar_formulario_cliente()

        else:
            if not self._validaciones_captura_manual():
                return

            tipo_documento = self._ventanas.obtener_input_componente('cbx_documento')
            if tipo_documento == 'Remisión':
                self._settear_valores_cliente_remision()

            if tipo_documento == 'Factura':
                self._settear_valores_cliente_factura()

            self._llamar_formulario_cliente()

    def _validaciones_captura_manual(self):
        nombre_cliente = self._ventanas.obtener_input_componente('tbx_cliente')
        if not nombre_cliente:
            self._ventanas.mostrar_mensaje('Debe capturar nombre.')
            return

        if len(nombre_cliente)<5:
            self._ventanas.mostrar_mensaje('Debe abundar en el nombre del cliente.')
            return

        return True

    def _validaciones_captura_cedula_fiscal(self):
        rfc = self._ventanas.obtener_input_componente('tbx_rfc')
        cif = self._ventanas.obtener_input_componente('tbx_cif')

        if not rfc:
            self._ventanas.mostrar_mensaje('Debe capturar un RFC.')
            return

        if not self._utilerias.es_rfc(rfc) or rfc == 'XAXX010101000':
            self._ventanas.mostrar_mensaje('Debe capturar un RFC válido.')
            return

        if not cif:
            self._ventanas.mostrar_mensaje('Debe capturar un CIF.')
            return

        if not self._utilerias.es_cif(cif):
            self._ventanas.mostrar_mensaje('Debe capturar un CIF válido.')
            return

        return True

    def _settear_valores_cliente_remision(self):

        cliente = self._ventanas.obtener_input_componente('tbx_cliente')
        self._cliente.official_name = cliente.upper()
        self._cliente.company_type_name = '616 - Sin obligaciones fiscales'
        self._cliente.official_number = 'XAXX010101000'
        self._cliente.forma_pago = '01'
        self._cliente.metodo_pago = 'PUE'
        self._cliente.receptor_uso_cfdi = 'S01'
        self._cliente.reference = 'REMISIÓN'
        self._cliente.customer_type_id = 2

    def _settear_valores_cliente_factura(self, cliente=None, rfc=None, cif=None):

        # Obtener valores desde la interfaz SOLO si los parámetros vienen vacíos
        cliente = cliente or self._ventanas.obtener_input_componente('tbx_cliente')
        rfc = rfc or self._ventanas.obtener_input_componente('tbx_rfc')
        cif = cif or self._ventanas.obtener_input_componente('tbx_cif')

        # Normalizar valores
        cliente = (cliente or '').strip().upper()
        rfc = (rfc or '').strip().upper()
        cif = (cif or '').strip()

        # Asignar valores al objeto cliente (Modelo)
        self._cliente.official_name = cliente
        self._cliente.forma_pago = '99'
        self._cliente.metodo_pago = 'PPD'
        self._cliente.reference = 'FACTURA'
        self._cliente.customer_type_id = 2
        self._cliente.official_number = rfc
        self._cliente.cif = cif

    def _llamar_formulario_cliente(self):
        nueva_ventana = self._ventanas.crear_popup_ttkbootstrap('Nuevo cliente', ocultar_master=True)
        NoteBookCliente(nueva_ventana,
                        self._base_de_datos,
                        self._parametros,
                        self._utilerias,
                        self._cliente
                        )

        nueva_ventana.wait_window()
        self._master.destroy()
