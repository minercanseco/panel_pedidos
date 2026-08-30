import ttkbootstrap as ttk
from cayal.parametros_contpaqi import ParametrosContpaqi
from cayal.comandos_base_datos import ComandosBaseDatos
from capturar_documento.herramientas.archivo_complementos.interfaz import Interfaz
from capturar_documento.herramientas.archivo_complementos.modelo import Modelo
from capturar_documento.herramientas.archivo_complementos.controlador import Controlador


def abrir_archivo_complementos(master, parametros, base_de_datos=None):
    """Abre la herramienta dentro del selector de módulos."""
    base_de_datos = base_de_datos or ComandosBaseDatos()
    interfaz = Interfaz(master)
    modelo = Modelo(base_de_datos, plantilla=parametros.plantilla)
    return Controlador(interfaz, modelo, parametros)


if __name__ == '__main__':
    parametros = ParametrosContpaqi()
    ventana = ttk.Window()
    base_de_datos = ComandosBaseDatos()

    _controlador = abrir_archivo_complementos(
        ventana,
        parametros,
        base_de_datos,
    )

    ventana.mainloop()
