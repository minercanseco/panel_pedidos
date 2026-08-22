from cayal.predeterminar_impresora import PredeterminarImpresora
from cayal.parametros_contpaqi import ParametrosContpaqi



if __name__ == '__main__':
    parametros = ParametrosContpaqi()
    impresora = parametros.impresora

    PredeterminarImpresora(nombre_impresora=impresora)
