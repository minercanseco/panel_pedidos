import tkinter as tk
from cayal.ventanas import Ventanas
from cayal.cliente import Cliente

from formulario_cliente import FormularioCliente


class BuscarClientes:
    def __init__(self, master, base_de_datos, parametros, utilerias):
        self._master = master
        self._base_de_datos = base_de_datos
        self._ventanas = Ventanas(self._master)
        self._parametros = parametros
        self._utilerias = utilerias
        self._cliente = Cliente()

        self._crear_frames()
        self._cargar_componentes()
        self._cargar_eventos()
        self._rellenar_tabla_clientes()
        self._ventanas.configurar_ventana_ttkbootstrap('Clientes')


    def _crear_frames(self):
        frames = {

            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            'frame_captura': ('frame_principal', 'Clientes',
                              {'row': 0, 'columnspan': 2, 'column': 0, 'pady': 2, 'padx': 2,
                               'sticky': tk.NSEW}),
            'frame_botones': ('frame_principal', None,
                              {'row': 1, 'column': 1, 'padx': 0, 'pady': 5, 'sticky': tk.W}),

        }
        self._ventanas.crear_frames(frames)

    def _cargar_componentes(self):
        componentes = {
            'tbv_clientes': ('frame_captura', self._crear_columnas_tabla(), None, None)
        }
        self._ventanas.crear_componentes(componentes)

    def _cargar_eventos(self):
        eventos = {
            'tbv_clientes': (lambda event:self._llamar_a_info_cliente(), 'doble_click')
        }
        self._ventanas.cargar_eventos(eventos)

    def _llamar_a_info_cliente(self):

        filas = self._ventanas.procesar_filas_table_view('tbv_clientes', seleccionadas=True)
        if not filas:
            return

        if len(filas) > 1:
            return

        business_entity_id = filas[0]['BusinessEntityID']
        info_cliente = self._base_de_datos.buscar_info_cliente(business_entity_id)

        self._cliente.consulta = info_cliente
        self._cliente.settear_valores_consulta()


        self._parametros.id_principal = business_entity_id

        ventana = self._ventanas.crear_popup_ttkbootstrap(self._master, 'Cliente')
        tipo_captura = 'Remisión' if self._cliente.official_number == 'XAXX010101000' else 'Factura'
        parametros_cliente = {'TipoCaptura': tipo_captura}
        instancia = FormularioCliente(ventana,
                                      self._parametros,
                                      parametros_cliente,
                                      self._cliente)
        ventana.wait_window()

    def _rellenar_tabla_clientes(self):
        consulta = self._buscar_info_clientes()
        self._ventanas.rellenar_table_view('tbv_clientes', self._crear_columnas_tabla(), consulta)
        texto = f'CLIENTES CARNES CAYAL'
        self._ventanas.actualizar_etiqueta_externa_tabla_view('tbv_clientes', texto)

    def _buscar_info_clientes(self):
        return self._base_de_datos.fetchall("""
            SELECT DISTINCT 
                [BusinessEntityID],
                ISNULL([BusinessEntity], '') AS Nombre,
                ISNULL([CommercialName], '') AS NombreComercial,
                ISNULL([RegimenFiscal], '') AS Regimen,
                ISNULL([MainContactPhoneS], '') AS Teléfonos,
                ISNULL([AddressFiscalCity], '') AS Colonia,
                ISNULL([AddressFiscalZipCode], '') AS CP,
                ISNULL([AddressFiscalStateProvince], '') AS Estado,
                ISNULL([AddressFiscalStreett], '') AS Calle,
                ISNULL([AddressFiscalComments], '') AS Comentarios,
                ISNULL([CustomerTypeName], '') AS Lista,
                ISNULL([RFC], '') AS RFC,
                ISNULL([ZoneName], '') AS Ruta,
                ISNULL([FormaPago], '') AS FP,
                ISNULL([MetodoPago], '') AS MP,
                ISNULL([ReceptorUsoCFDI], '') AS CFDI,
                ISNULL([Mail], '') AS EMail,
                ISNULL([FechaCompra], '') AS FechaCompra,
                ISNULL([Usuario], '') AS Usuario,
                ISNULL([Creado], '') AS Creado,
                ISNULL([PaymentTermName], '') AS Condiciones,
                ISNULL([Comments], '') AS Comentarios,
                ISNULL([CreditLimit], '') AS Crédito,
                ISNULL([CIF], '') AS CIF
            FROM vwLBSCustomerList
            WHERE BusinessEntityID NOT IN (9277,6211,8179) and ZoneName<>'Proveedores' and CustomerID<>9578
            ORDER BY BusinessEntityID DESC 

        """)

    def _crear_columnas_tabla(self):
        return [
            {"text": "BusinessEntityID", "stretch": False, "width": 0},
            {"text": "Nombre", "stretch": True, "width": 180},
            {"text": "NombreComercial", "stretch": True, "width": 80},
            {"text": "Regimen", "stretch": True, "width": 30},
            {"text": "Telefonos", "stretch": True, "width": 50},
            {"text": "Colonia", "stretch": True, "width": 80},
            {"text": "CP", "stretch": True, "width": 50},
            {"text": "Estado", "stretch": True, "width": 50},
            {"text": "Calle", "stretch": True, "width": 50},
            {"text": "Comentarios", "stretch": True, "width": 50},
            {"text": "Lista", "stretch": True, "width": 65},
            {"text": "RFC", "stretch": True, "width": 115},
            {"text": "Ruta", "stretch": True, "width": 35},
            {"text": "FP", "stretch": True, "width": 30},
            {"text": "MP", "stretch": True, "width": 35},
            {"text": "CFDI", "stretch": True, "width": 40},
            {"text": "EMail", "stretch": True, "width": 50},
            {"text": "FechaCompra", "stretch": True, "width": 95},
            {"text": "Usuario", "stretch": True, "width": 50},
            {"text": "Creado", "stretch": True, "width": 95},
            {"text": "Condiciones", "stretch": True, "width": 50},
            {"text": "Crédito", "stretch": True, "width": 50},
            {"text": "CIF", "stretch": True, "width": 30}
        ]