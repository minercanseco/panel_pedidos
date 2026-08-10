
from capturar_documento.herramientas.cobro_rapido.controlador_cobro_rapido import ControladorCobroRapido
from capturar_documento.herramientas.cobro_rapido.interfaz_cobro_rapido import InterfazCobroRapido
from capturar_documento.herramientas.cobro_rapido.panel_principal import PanelPrincipal
from cayal.util import Utilerias


class LlamarInstanciaCobroRapido:

    def __init__(
            self,
            ventana,
            parametros,
            base_de_datos,
            registrar_documento_para_recalculo=True,
    ):
        self.ventana = ventana
        self.parametros = parametros
        self.registrar_documento_para_recalculo = bool(
            registrar_documento_para_recalculo
        )

        self.base_de_datos = base_de_datos
        self.utilerias = Utilerias()

        self.instancia = None
        self.interfaz = None
        self.controlador = None

        self._iniciar()

    def _iniciar(self):
        saldo_decimal = self._obtener_saldo_documento()

        if saldo_decimal != 0:
            self._abrir_cobro_rapido()
        else:
            self._abrir_panel_principal()

    def _obtener_saldo_documento(self):
        saldo = self.base_de_datos.fetchone(
            """
            SELECT ISNULL(Balance, 0)
            FROM docDocument
            WHERE DocumentID = ?
            """,
            (self.parametros.id_principal,)
        )

        return self.utilerias.redondear_valor_cantidad_a_decimal(saldo)

    def _abrir_cobro_rapido(self):
        self.interfaz = InterfazCobroRapido(self.ventana)
        self.controlador = ControladorCobroRapido(
            self.interfaz,
            self.parametros,
            registrar_documento_para_recalculo=(
                self.registrar_documento_para_recalculo
            ),
        )

    def _abrir_panel_principal(self):
        self.instancia = PanelPrincipal(
            self.ventana,
            self.base_de_datos,
            self.utilerias,
            self.parametros
        )
