import ttkbootstrap as ttk
from cayal.parametros_contpaqi import ParametrosContpaqi
from controlador_enviar_correo import ControladorEnviarCorreo


if __name__ == '__main__':

    parametros = ParametrosContpaqi()
    #---------------------------------------
    #Parametros de prueba de la aplicacion

    #parametros.id_seleccionados = [307402]
    #parametros.id_modulo = 1400
    #parametros.id_usuario = 64
    modo_prueba = False
    # ---------------------------------------

    ventana = ttk.Window()

    controlador = ControladorEnviarCorreo(ventana, parametros, modo_prueba)
    ventana.mainloop()
