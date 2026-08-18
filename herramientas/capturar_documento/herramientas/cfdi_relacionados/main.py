import ttkbootstrap as ttk
from cayal.parametros_contpaqi import ParametrosContpaqi

from controlador import ControladorRelacionarFactura
from interfaz import InterfazRelacionarFactura
from modelo import ModeloRelacionarFactura

if __name__ == '__main__':
    parametros = ParametrosContpaqi()
    parametros.id_principal = 106174
    ventana = ttk.Window()

    _interfaz = InterfazRelacionarFactura(ventana)
    _modelo = ModeloRelacionarFactura(parametros)
    _controlador = ControladorRelacionarFactura(_interfaz, _modelo)

    ventana.mainloop()