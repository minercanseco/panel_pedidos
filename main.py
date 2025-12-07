
import ttkbootstrap as ttk
from cayal.parametros_contpaqi import ParametrosContpaqi
from panel.interfaz_panel_pedidos import InterfazPanelPedidos
from panel.modelo_panel_pedidos import ModeloPanelPedidos
from panel.controlador_panel_pedidos import ControladorPanelPedidos
from cayal.actualizador_de_paquetes import ActualizadorDePaquetes
from cayal.login import Login
from cayal.generar_contexto_ia import GenerarContextoIA


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

    version_paquete = 'panel_pedidos_v104'
    actualizador = ActualizadorDePaquetes(version_paquete)
    nueva_version = actualizador.verificar_version_actualizada()
    solo_contexto = False

    if solo_contexto:
        gen = GenerarContextoIA(root=".", out="contexto.md")
        ruta = gen.build()
        print("Contexto generado en:", ruta)

    if nueva_version:
        actualizador.actualizar_con_interfaz(ventana_login)

    if not nueva_version:
        parametros_login.id_modulo = 1687

        instancia_login = Login(ventana_login, parametros_login, si_acceso_exitoso)
        ventana_login.mainloop()