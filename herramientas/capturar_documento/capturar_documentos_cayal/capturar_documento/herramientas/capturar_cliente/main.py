import ttkbootstrap as ttk
from cayal.parametros_contpaqi import ParametrosContpaqi
from cayal.cliente import Cliente
from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.util import Utilerias
from .notebook_cliente import NoteBookCliente
from .cliente_nuevo import ClienteNuevo


def abrir_captura_cliente(ventana, parametros):
    """Abre alta o edición según el BusinessEntityID recibido."""
    base_de_datos = ComandosBaseDatos()
    utilerias = Utilerias()

    if int(parametros.id_principal or 0) > 0:
        return NoteBookCliente(
            ventana,
            base_de_datos,
            parametros,
            utilerias,
            Cliente(),
        )

    return ClienteNuevo(
        ventana,
        parametros,
        base_de_datos,
        utilerias,
    )


if __name__ == '__main__':
    parametros = ParametrosContpaqi()
    #parametros.id_principal = 19219
    #parametros.id_usuario =64

    ventana = ttk.Window()
    instancia = abrir_captura_cliente(ventana, parametros)
    ventana.wait_window()
