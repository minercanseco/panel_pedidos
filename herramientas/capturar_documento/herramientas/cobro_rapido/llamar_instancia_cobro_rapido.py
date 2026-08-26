
from capturar_documento.herramientas.cobro_rapido.controlador_cobro_rapido import ControladorCobroRapido
from capturar_documento.herramientas.cobro_rapido.interfaz_cobro_rapido import InterfazCobroRapido
from capturar_documento.herramientas.cobro_rapido.panel_principal import PanelPrincipal
from cayal.impuestos import Impuestos
from cayal.util import Utilerias


class LlamarInstanciaCobroRapido:

    def __init__(self, ventana, parametros, base_de_datos):
        self.ventana = ventana
        self.parametros = parametros

        self.base_de_datos = base_de_datos
        self.utilerias = Utilerias()

        self.instancia = None
        self.interfaz = None
        self.controlador = None

        self._iniciar()

    def _iniciar(self):
        self._sincronizar_documento_para_cobro()
        self._normalizar_residuo_pago()
        saldo_decimal = self._obtener_saldo_documento()

        if saldo_decimal != 0:
            self._abrir_cobro_rapido()
        else:
            self._abrir_panel_principal()

    def _sincronizar_documento_para_cobro(self):
        """Deja impuestos, encabezado y saldo listos antes de abrir el atajo."""
        document_id = int(self.parametros.id_principal or 0)
        if document_id <= 0:
            raise ValueError(
                'No se proporcionó un documento válido para el cobro rápido.'
            )

        Impuestos.afectar_y_sincronizar_totales_documento(
            self.base_de_datos,
            document_id,
        )

    def _normalizar_residuo_pago(self):
        """Corrige documentos ya pagados cuyo saldo sólo contiene subcentavos."""
        self.base_de_datos.command(
            """
            UPDATE dbo.docDocument
            SET Balance = 0,
                StatusPaidID = 1,
                TotalPaid = CAST(ROUND(ISNULL(TotalPaid, 0), 2)
                                 AS decimal(18, 2))
            WHERE DocumentID = ?
              AND CAST(ROUND(ISNULL(Balance, 0), 2) AS decimal(18, 2)) = 0
              AND CAST(ROUND(ISNULL(TotalPaid, 0), 2) AS decimal(18, 2))
                  = CAST(ROUND(ISNULL(Total, 0), 2) AS decimal(18, 2))
              AND ISNULL(TotalPaid, 0) > 0
            """,
            (self.parametros.id_principal,),
        )

    def _obtener_saldo_documento(self):
        saldo = self.base_de_datos.fetchone(
            """
            SELECT CAST(ROUND(ISNULL(Balance, 0), 2) AS decimal(18, 2))
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
        )

    def _abrir_panel_principal(self):
        self.instancia = PanelPrincipal(
            self.ventana,
            self.base_de_datos,
            self.utilerias,
            self.parametros
        )
