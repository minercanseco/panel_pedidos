import ttkbootstrap as ttk
from cayal.parametros_contpaqi import ParametrosContpaqi
from datetime import datetime
from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.util import Utilerias
from .panel_principal import PanelPrincipal
from .corte_de_caja import CorteDeCaja


def abrir_corte_de_caja(ventana, parametros):
    """Abre el flujo de alta o consulta según el identificador recibido."""
    if int(parametros.id_principal or 0) == 0:
        parametros.fecha = str(datetime.today().date())
        return PanelPrincipal(ventana, parametros)

    return CorteDeCaja(
        ventana,
        parametros,
        ComandosBaseDatos(),
        Utilerias(),
    )

if __name__ == '__main__':

    parametros = ParametrosContpaqi()

    # parametros de prueba
    #parametros.id_principal =0
    #parametros.id_usuario =  97
    #parametros.cadena_conexion = 'Mac'

    ventana = ttk.Window()
    instancia = abrir_corte_de_caja(ventana, parametros)
    ventana.mainloop()
