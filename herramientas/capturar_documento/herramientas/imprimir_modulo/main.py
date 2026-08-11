import os

import ttkbootstrap as ttk
from herramientas.capturar_documento.herramientas.imprimir_modulo.imprimir_modulo import ImprimirModulo
from herramientas.capturar_documento.herramientas.imprimir_modulo.definir_impresoras import DefinirImpresoras
from cayal.parametros_contpaqi import ParametrosContpaqi


def existe_archivo_impresoras() -> bool:
    """
    Valida si el archivo de configuración de impresoras existe.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ruta_archivo_comprimido = os.path.join(base_dir, "impresoras.gz")

    return ruta_archivo_comprimido  if os.path.exists(ruta_archivo_comprimido) else False

if __name__ == '__main__':
    ventana = ttk.Window()
    parametros = ParametrosContpaqi()
    configuracion = existe_archivo_impresoras()

    # parametros de prueba user dayanac
    #parametros.id_usuario =71
    #parametros.id_seleccionados = [315238]
    #parametros.uuid = 'e8ce4c85-579a-4a19-ad6a-6040578cf31e'
    #parametros.id_modulo = 21

    if not configuracion:
        _ = DefinirImpresoras(ventana)
    else:
        _ = ImprimirModulo(ventana, parametros, predeterminar=False, configuracion=configuracion)

    ventana.mainloop()

