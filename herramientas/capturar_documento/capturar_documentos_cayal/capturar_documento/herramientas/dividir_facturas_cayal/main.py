import ttkbootstrap as ttk
from cayal.parametros_contpaqi import ParametrosContpaqi
from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.util import Utilerias

from .dividir_facturas_modelo import ModeloDividirFacturas
from .dividir_facturas_controlador import ControladorDividirFacturas
from .dividir_facturas_interface import InterfaceDividirFacturas


def abrir_division_documento(ventana, parametros, base_de_datos=None):
    """Abre la herramienta embebida usando el documento del selector."""
    utilerias = Utilerias()
    base_de_datos = base_de_datos or ComandosBaseDatos()
    interfaz = InterfaceDividirFacturas(ventana)
    modelo = ModeloDividirFacturas(parametros, base_de_datos, utilerias)
    return ControladorDividirFacturas(interfaz, modelo)

if __name__ == '__main__':
    parametros = ParametrosContpaqi()
    #parametros.base_de_datos = 'Prueba_CC'

    #parametros.id_usuario = 64
    #parametros.id_principal = 25452 #307544  #307106# 306891
    #parametros.id_modulo = 21

    ventana = ttk.Window()
    abrir_division_documento(ventana, parametros)
    ventana.mainloop()
