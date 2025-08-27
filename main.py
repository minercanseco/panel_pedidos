
import ttkbootstrap as ttk
from cayal.parametros_contpaqi import ParametrosContpaqi
from interfaz_panel_pedidos import InterfazPanelPedidos
from modelo_panel_pedidos import ModeloPanelPedidos
from controlador_panel_pedidos import ControladorPanelPedidos
from cayal.actualizador_de_paquetes import ActualizadorDePaquetes
from cayal.login import Login


def si_acceso_exitoso(parametros=None, master=None):
    llamar_instancia_principal(master, parametros)

def llamar_instancia_principal(ventana, parametros):
    vista = InterfazPanelPedidos(ventana)
    modelo = ModeloPanelPedidos(vista, parametros)
    controlador = ControladorPanelPedidos(modelo)
    ventana.mainloop()

if __name__ == '__main__':
    ventana_login = ttk.Window()
    parametros_login = ParametrosContpaqi()

    actualizador = ActualizadorDePaquetes('panel_pedidos_v100')
    version_actualizada = actualizador.verificar_version_actualizada()

    if version_actualizada:
        actualizador.actualizar_con_interfaz(ventana_login)

    if not version_actualizada:
        parametros_login.id_modulo = 1687

        instancia_login = Login(ventana_login, parametros_login, si_acceso_exitoso)
        ventana_login.mainloop()