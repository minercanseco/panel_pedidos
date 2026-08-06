import ttkbootstrap as ttk
from cayal.parametros_contpaqi import ParametrosContpaqi
from cayal.cliente import Cliente
from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.util import Utilerias
from notebook_cliente import NoteBookCliente
from cliente_nuevo import ClienteNuevo


if __name__ == '__main__':
    parametros = ParametrosContpaqi()
    #parametros.id_principal = 19219
    #parametros.id_usuario =64

    cliente = Cliente()
    utilerias = Utilerias()
    base_de_datos = ComandosBaseDatos()

    ventana = ttk.Window()

    if parametros.id_principal != 0:
        NoteBookCliente(ventana,
                        base_de_datos,
                        parametros,
                        utilerias,
                        cliente
                        )
    else:
        ClienteNuevo(ventana,
                     parametros,
                     base_de_datos,
                     utilerias)

    ventana.wait_window()

