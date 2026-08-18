from cayal.parametros_contpaqi import ParametrosContpaqi
from capturar_documento.herramientas.listas_precios.crear_listas_precios import (
    CrearListasPrecios,
)


if __name__ == '__main__':
    parametros = ParametrosContpaqi()
    #parametros.cadena_conexion = 'Mac'
    #parametros.id_usuario = 65
    instancia = CrearListasPrecios(parametros)
