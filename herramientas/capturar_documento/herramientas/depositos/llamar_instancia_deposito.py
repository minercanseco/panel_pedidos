import datetime

import ttkbootstrap as ttk
from cayal.util import Utilerias

from capturar_documento.herramientas.depositos.aceptar_depositos_vendedores import AceptarDepositosVendedores
from capturar_documento.herramientas.depositos.agregar_depositos import AgregarDeposito


class LlamarInstanciaDeposito:

    def __init__(self, ventana, parametros, base_de_datos):
        self.ventana = ventana
        self.parametros = parametros
        self.base_de_datos = base_de_datos
        self.utilerias = Utilerias()
        self.instancia = None

        self._iniciar()

    def _iniciar(self):
        self._cargar_grupo_usuario()

        aceptar_depositos = self._validar_aceptar_depositos()

        if aceptar_depositos == 1:
            self.instancia = AceptarDepositosVendedores(
                self.ventana,
                self.base_de_datos,
                self.utilerias,
                self.parametros
            )
        else:
            self.instancia = AgregarDeposito(
                self.ventana,
                self.base_de_datos,
                self.utilerias,
                self.parametros
            )

    def _cargar_grupo_usuario(self):
        self.parametros.id_grupo_usuario = self.base_de_datos.fetchone(
            """
            SELECT UserGroupID
            FROM engUser
            WHERE UserID = ?
            """,
            (self.parametros.id_usuario,)
        )

    def _obtener_depositos_pendientes(self):
        return self.base_de_datos.fetchone(
            """
            SELECT COUNT(ID)
            FROM zvwDepositosDiariosCayalNoAceptados M
            WHERE CAST(M.Fecha AS DATE) = CAST(GETDATE() AS DATE)
              AND ISNULL(M.StatusAceptado, 0) = 0;
            """
        )

    def _validar_aceptar_depositos(self):
        pendientes = self._obtener_depositos_pendientes()

        if pendientes == 0:
            return 0

        dia = datetime.datetime.weekday(datetime.datetime.today())
        grupo_usuario = self.parametros.id_grupo_usuario

        es_domingo = dia == 6
        es_grupo_corte = grupo_usuario == 11

        if es_domingo and es_grupo_corte:
            return self._preguntar_recepcion_depositos()

        if not es_grupo_corte:
            return self._preguntar_recepcion_depositos()

        return 0

    def _preguntar_recepcion_depositos(self):
        self.ventana.position_center()

        respuesta = ttk.dialogs.Messagebox.yesno(
            message='¿Desea recepcionar depósitos de vendedores?',
            parent=self.ventana
        )

        return 0 if respuesta == 'No' else 1


