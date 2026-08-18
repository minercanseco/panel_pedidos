import ttkbootstrap as ttk
from buscar_generales_cliente_cartera import BuscarGeneralesCliente
from cayal.parametros_contpaqi import ParametrosContpaqi


if __name__ == '__main__':
    parametros = ParametrosContpaqi()
    ventana = ttk.Window()

    instancia = BuscarGeneralesCliente(ventana, parametros)
    ventana.wait_window()


