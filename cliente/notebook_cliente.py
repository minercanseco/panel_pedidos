import tkinter as tk
from cayal.ventanas import Ventanas
from cayal.cliente import Cliente
from cliente.formulario_cliente_interfaz import FormularioClienteInterfaz
from cliente.formulario_cliente_modelo import FormularioClienteModelo
from cliente.formulario_cliente_controlador import FormularioClienteControlador


class NoteBookCliente:
    def __init__(self, master, base_de_datos, parametros, utilerias):
        self._master = master
        self._ventanas = Ventanas(self._master)

        self._cliente = Cliente()
        self._base_de_datos = base_de_datos
        self._parametros = parametros
        self._utilerias = utilerias

        self._business_entity_id = self._parametros.id_principal
        self._homologar_direccion_fiscal(self._business_entity_id)
        self._settar_info_cliente()

        self._crear_frames()
        self._cargar_componentes()
        self._ventanas.configurar_ventana_ttkbootstrap()

    def _crear_frames(self):
        frames = {
            'frame_principal': (
                'master',
                'Direcciones:',
                {'row': 0, 'column': 0, 'sticky': tk.NSEW}
            ),

            'frame_notebook': (
                'frame_principal',
                None,
                {'row': 1, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}
            ),
        }
        self._ventanas.crear_frames(frames)

        frame_principal = self._ventanas.componentes_forma['frame_principal']
        frame_principal.rowconfigure(1, weight=1)
        frame_principal.columnconfigure(0, weight=1)

    def _cargar_componentes(self):
        # 1) Definir pestañas del notebook
        info_pestanas = {
            # Texto de la pestaña con emoji de dirección fiscal
            'tab_direccion_fiscal': ('Dirección fiscal 🧾📍', None),
        }

        # 2) Crear notebook dentro de frame_notebook
        self._ventanas.crear_notebook(
            nombre_notebook='nb_formulario_cliente',
            info_pestanas=info_pestanas,
            nombre_frame_padre='frame_notebook',
            config_notebook={
                'row': 0,
                'column': 0,
                'sticky': tk.NSEW,
                'padx': 5,
                'pady': 5,
                'bootstyle': 'primary',
            }
        )

        # 3) Crear frames internos por cada pestaña
        frames_tabs = {
            'frm_direccion_fiscal': (
                'tab_direccion_fiscal',
                None,
                {'row': 0, 'column': 0, 'sticky': tk.NSEW, 'padx': 5, 'pady': 5}
            )
        }

        self._ventanas.crear_frames(frames_tabs)

        # ============================================================
        # 4) MONTAR CADA MÓDULO EN SU CORRESPONDIENTE PESTAÑA
        # ============================================================

        # ========== DIRECCIÓN FISCAL ==========

        frame_direccion_fiscal = self._ventanas.componentes_forma['frm_direccion_fiscal']
        self._interfaz = FormularioClienteInterfaz(frame_direccion_fiscal)
        self._modelo = FormularioClienteModelo(self._parametros,
                                               self._utilerias,
                                               self._base_de_datos,
                                               self._cliente)

        self._controlador = FormularioClienteControlador(
            self._interfaz,
            self._modelo
        )

    def _buscar_info_cliente(self):
        return self._base_de_datos.fetchall("""
                SELECT * FROM [dbo].[zvwBuscarInfoCliente-BusinessEntityID](?)
            """, (self._business_entity_id,))

    def _settar_info_cliente(self):
        if self._business_entity_id <= 0:
            return

        info_cliente = self._buscar_info_cliente()

        info_cliente[0]['DeliveryCost'] = self._utilerias.redondear_valor_cantidad_a_decimal(info_cliente[0]['DeliveryCost'])
        self._cliente.consulta = info_cliente
        self._cliente.settear_valores_consulta()

    def _homologar_direccion_fiscal(self, business_entity_id):
        if business_entity_id <= 0:
            return
        # esta funcion es deuda tecnica de la homologacion entre la direccion fiscal
        # y orgbusinessentitymaininfo que es la tabla donde nace los parametros
        # de la direccion fiscal del cliente, esto es necesario para coherencia en
        # la información y la impresion de los formatos del cliente

        self._base_de_datos.command("""
           DECLARE @business_entity_id INT = ?
           UPDATE ADT
            SET
                ADT.StateProvince      = EM.AddressFiscalStateProvince, 
                ADT.City               = EM.AddressFiscalCity,
                ADT.Municipality       = EM.AddressFiscalMunicipality,
                ADT.Street             = EM.AddressFiscalStreet,
                ADT.Comments           = EM.AddressFiscalComments,
                ADT.CountryCode        = EM.AddressFiscalCountryCode,
                ADT.CityCode           = EM.AddressFiscalCityCode, 
                ADT.MunicipalityCode   = EM.AddressFiscalMunicipalityCode, 
                ADT.Telefono           = EM.BusinessEntityPhone
            FROM orgBusinessEntityMainInfo EM
            INNER JOIN orgAddressDetail ADT ON EM.AddressFiscalDetailID = ADT.AddressDetailID
            WHERE
                ADT.AddressDetailID = (SELECT AddressFiscalDetailID from orgBusinessEntityMainInfo WHERE BusinessEntityID = @business_entity_id)
                AND (
                    ISNULL(ADT.StateProvince, '')       <> ISNULL(EM.AddressFiscalStateProvince, '') OR
                    ISNULL(ADT.City, '')                <> ISNULL(EM.AddressFiscalCity, '') OR
                    ISNULL(ADT.Municipality, '')        <> ISNULL(EM.AddressFiscalMunicipality, '') OR
                    ISNULL(ADT.Street, '')              <> ISNULL(EM.AddressFiscalStreet, '') OR
                    ISNULL(ADT.Comments, '')            <> ISNULL(EM.AddressFiscalComments, '') OR
                    ISNULL(ADT.CountryCode, '')         <> ISNULL(EM.AddressFiscalCountryCode, '') OR
                    ISNULL(ADT.CityCode, '')            <> ISNULL(EM.AddressFiscalCityCode, '') OR
                    ISNULL(ADT.MunicipalityCode, '')    <> ISNULL(EM.AddressFiscalMunicipalityCode, '') OR
                    ISNULL(ADT.Telefono, '')            <> ISNULL(EM.BusinessEntityPhone, '')
                );
        """, (business_entity_id,))

