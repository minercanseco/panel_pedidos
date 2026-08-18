import ttkbootstrap
from cayal.parametros_contpaqi import ParametrosContpaqi
from capturar_documento.herramientas.archivo_cayal.archivo_cayal import (
    ArchivoCayal,
)


def abrir_archivo(master, parametros):
    modulos_archivo = {
        1572: 21,
        1640: 1400,
    }
    parametros.id_modulo = modulos_archivo.get(
        parametros.id_modulo,
        parametros.id_modulo,
    )
    return ArchivoCayal(master, parametros)


if __name__ == '__main__':
    parametros = ParametrosContpaqi()
    ventana = ttkbootstrap.Window()

    #parametros.id_modulo = 21
    #parametros.id_usuario = 19

    _ = abrir_archivo(ventana, parametros)
    ventana.mainloop()
