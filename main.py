import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox

from cayal.parametros_contpaqi import ParametrosContpaqi
from interfaz_panel_pedidos import InterfazPanelPedidos
from modelo_panel_pedidos import ModeloPanelPedidos
from controlador_panel_pedidos import ControladorPanelPedidos
from cayal.actualizador_de_paquetes import ActualizadorDePaquetes
from cayal.login import Login


def mostrar_mensaje(mensaje, titulo="Actualización"):
    Messagebox.show_info(title=titulo, message=mensaje, alert=True)

def si_acceso_exitoso(parametros=None, master=None):
    #xmaster.grab_release()
    llamar_instancia_principal(master, parametros)

def llamar_instancia_principal(ventana, parametros):
    vista = InterfazPanelPedidos(ventana)
    modelo = ModeloPanelPedidos(vista, parametros)
    controlador = ControladorPanelPedidos(modelo)
    ventana.mainloop()

if __name__ == '__main__':
    ventana_login = ttk.Window()
    parametros_login = ParametrosContpaqi()

    actualizar = ActualizadorDePaquetes('panel_pedidos_v48')

    if actualizar.actualizar_paquete():
        mostrar_mensaje("Se actualizará el paquete, por favor espere.")
        ventana_login.update_idletasks()
        ventana_login.withdraw()  # Oculta la ventana sin destruirla
        actualizar.actualizar_paquete()
        ventana_login.destroy()

    if not actualizar.actualizar_paquete():
        # ------------------------------------------
        # parametros de prueba
        parametros_login.cadena_conexion = 'Mac'
        #parametros_login.base_de_datos = 'ComercialSP'
        parametros_login.id_modulo = 1687
        # ------------------------------------------
        instancia_login = Login(ventana_login, parametros_login, si_acceso_exitoso)
        ventana_login.mainloop()