import ttkbootstrap as ttk
from cayal.parametros_contpaqi import ParametrosContpaqi

from controlador_intercambio_rfc import ControladorIntercambioRFC
from modelo_intercambio_rfc import ModeloIntercambioRFC
from interfaz_intercambio_rfc import InterfazIntercambioRfc

if __name__ == '__main__':
    ventana = ttk.Window()
    parametros = ParametrosContpaqi()


    interfaz = InterfazIntercambioRfc(ventana)
    modelo = ModeloIntercambioRFC(parametros)
    ControladorIntercambioRFC(interfaz, modelo)

    ventana.mainloop()
