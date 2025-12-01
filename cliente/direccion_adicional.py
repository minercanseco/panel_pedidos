import tkinter as tk
from cayal.ventanas import Ventanas

class DireccionAdicional:
    def __init__(self, master,modelo, info_direccion):
        self.master = master

        self._ventanas = Ventanas(self.master)
        self._modelo = modelo

        self._info_direccion =  info_direccion

        self._nombre_direccion = self._info_direccion.get('AddressName', '')
        self._address_detail_id = self._info_direccion['AddressDetailID']

        self._crear_frames()
        self._cargar_componentes()
        self._ajustar_ancho_componentes()
        self._rellenar_componentes()

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.W}),

            'frame_generales': ('frame_principal', f'Dirección {self._nombre_direccion}:',
                                  {'row': 0, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.W}),

            'frame_lbl_estado': ('frame_generales', None,
                                    {'row': 11, 'column': 1, 'sticky': tk.NSEW}),

            'frame_btn_domicilios': ('frame_generales', None,
                                 {'row': 12, 'column': 1, 'sticky': tk.NSEW}),

            'frame_domicilios': ('frame_generales', None,
                              {'row': 13, 'column': 0, 'columnspan': 2,  'padx': 5, 'pady': 5,  'sticky': tk.NSEW}),

            'frame_fiscal': ('frame_principal', 'Datos Fiscales:',
                              {'row': 0, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_fiscal1': ('frame_fiscal', None,
                             {'row': 40, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_botones': ('frame_principal', None,
                              {'row': 2, 'column': 0, 'sticky': tk.E}),

        }

        self._ventanas.crear_frames(frames)

    def _cargar_componentes(self):

        estilo_label = {
            'foreground': 'black',
            'background': 'white',
            'font': ('Consolas', 12, 'bold'),
            'text': '',
            'anchor': 'w'
        }

        posicion_label = {
            'sticky': tk.W, 'pady': 0, 'padx': 0,
        }

        componentes = {
            'tbx_cliente': ('frame_generales', None, 'Cliente:', None),
            'tbx_ncomercial': ('frame_generales', None, 'N.Comercial:', None),
            'tbx_telefono': ('frame_generales', None, 'Teléfono:', None),
            'tbx_celular': ('frame_generales', None, 'Celular:', None),
            'tbx_calle': ('frame_generales', None, 'Calle:', None),
            'tbx_numero': ('frame_generales', None, 'Número:', None),
            'txt_comentario': ('frame_generales', None, 'Comentarios:', None),
            'tbx_cp': ('frame_generales', None, 'CP:', None),

            'lbl_estado': ('frame_lbl_estado', estilo_label, posicion_label, None),
            'lbl_municipio': ('frame_lbl_estado', estilo_label, posicion_label, None),
            'cbx_colonia': ('frame_generales', None, 'Colonia:', None),

            'tbx_envio': ('frame_domicilios', None, 'Envío:          ', None),
            'cbx_ruta': ('frame_domicilios', None, 'Ruta:          ', None),

            'tbx_rfc': ('frame_fiscal', None, 'RFC:     ', None),
            'tbx_cif': ('frame_fiscal', None, 'CIF:     ', None),
            'cbx_regimen': ('frame_fiscal', None, 'Régimen:', None),
            'cbx_formapago': ('frame_fiscal', None, 'FormaPago:', None),
            'cbx_metodopago': ('frame_fiscal', None, 'MétodoPago:', None),
            'cbx_usocfdi': ('frame_fiscal', None, 'UsoCFDI:', None),
            'txt_correo': ('frame_fiscal', None, 'Email:', None),


            'btn_guardar': ('frame_botones', 'success', 'Guardar', None),
            'btn_cancelar': ('frame_botones', 'danger', 'Cancelar', None),
            'btn_copiar': ('frame_botones', 'warning', 'Copiar', None),
        }

        self._ventanas.crear_componentes(componentes)

    def _ajustar_ancho_componentes(self):
        componentes = {
            # --- GENERALES ---
            'tbx_cliente':25,
            'tbx_ncomercial':25,
            'tbx_telefono': 0,
            'tbx_celular': 0,
            'tbx_calle': 25,
            'tbx_numero': 5,
            'txt_comentario': 35,
            'tbx_cp': 10,

            'tbx_envio': 5,
            'tbx_domicilios':5,
            'cbx_ruta': 30,

            # --- FISCAL ---
            'tbx_rfc': 0,
            'tbx_cif': 0,
            'btn_cif': 0,

            'cbx_colonia':30,
            'cbx_regimen': 30,
            'cbx_formapago': 30,
            'cbx_metodopago': 30,
            'cbx_usocfdi': 30,

            'txt_correo': 25,
        }

        for componente, valor in componentes.items():
            if valor == 0:
                continue

            self._ventanas.ajustar_ancho_componente(componente, valor)

    def _rellenar_componentes(self):
        componentes = {
            'tbx_cliente': '',
            'tbx_ncomercial': '',
            'tbx_telefono': 'Telefono',
            'tbx_celular': '',
            'tbx_calle': 'Street',
            'tbx_numero': 'ExtNumber',
            'txt_comentario': 'Comments',
            'tbx_cp': 'ZipCode',

            'lbl_estado': 'StateProvince',
            'lbl_municipio': 'Municipality',
            'cbx_colonia': '',

            'tbx_domicilios': '',
            'tbx_envio': '',
            'cbx_ruta': '',

            'tbx_rfc': '',
            'tbx_cif': '',
            'cbx_regimen': '',
            'cbx_formapago': '',
            'cbx_metodopago': '',
            'cbx_usocfdi': '',
            'txt_correo': '',

        }
        for componente, clave in componentes.items():
            valor = self._info_direccion.get(clave,'')
            self._ventanas.insertar_input_componente(componente, valor)
        print(self._info_direccion)