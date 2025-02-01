import ttkbootstrap as ttk
from cayal.parametros_contpaqi import ParametrosContpaqi
from interfaz_panel_pedidos import InterfacPanelPedidos
from modelo_panel_pedidos import ModeloPanelPedidos
from controlador_panel_pedidos import ControladorPanelPedidos


if __name__ == '__main__':
    parametros = ParametrosContpaqi()
    parametros.cadena_conexion = 'Mac'
    parametros.id_usuario = 64
    parametros.id_modulo = 1687

    ventana = ttk.Window()
    interfaz = InterfacPanelPedidos(ventana)
    modelo = ModeloPanelPedidos(interfaz, parametros)
    controlador = ControladorPanelPedidos(modelo)
    ventana.mainloop()


    # ------------------------------------------

