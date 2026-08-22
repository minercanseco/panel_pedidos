import ttkbootstrap as tkk
from cayal.parametros_contpaqi import ParametrosContpaqi
from controlador import ControladorAgregarQueja
from interfaz import Interfaz
from modelo import Modelo


if __name__ == '__main__':
    parametros = ParametrosContpaqi()

    #parametros.id_principal = 122633
    #parametros.id_usuario = 1

    ventana = tkk.Window()

    interfaz = Interfaz(ventana)
    modelo = Modelo(parametros)
    instancia = ControladorAgregarQueja(interfaz, modelo)

    ventana.mainloop()

