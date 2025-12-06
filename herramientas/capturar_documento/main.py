import ttkbootstrap as ttk

from cayal.parametros_contpaqi import ParametrosContpaqi
from buscar_generales_cliente import BuscarGeneralesCliente
from llamar_instancia_captura import LlamarInstanciaCaptura


if __name__ == '__main__':
    parametros = ParametrosContpaqi()
    #parametros.id_modulo = 1400 # modulo de compras empleados o vales de despensa
    #parametros.id_usuario = 104
    #parametros.uuid ='c9f8b6b4-6f2b-4d92-96fb-33a5awww562'

    ventana = ttk.Window()

    if parametros.id_modulo == 158: # modulo de tickets
        instancia = LlamarInstanciaCaptura(ventana, parametros)
    else:
        instancia = BuscarGeneralesCliente(ventana, parametros)

    ventana.mainloop()
