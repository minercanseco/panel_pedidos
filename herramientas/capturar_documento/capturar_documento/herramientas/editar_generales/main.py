import ttkbootstrap as ttk
from cayal.parametros_contpaqi import ParametrosContpaqi

from controlador import ControladorEditarDocumento
from interfaz import InterfazEditarDocumento
from modelo import ModeloEditarDocumento

if __name__ == '__main__':
    ventana = ttk.Window()
    parametros = ParametrosContpaqi()

    _modelo = ModeloEditarDocumento(parametros)
    _interfaz = InterfazEditarDocumento(ventana)
    _controlador = ControladorEditarDocumento(modelo=_modelo,interfaz=_interfaz)
    ventana.mainloop()