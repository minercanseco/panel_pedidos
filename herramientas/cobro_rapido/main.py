import ttkbootstrap as ttk
from controlador_cobro_rapido import ControladorCobroRapido
from interfaz_cobro_rapido import InterfazCobroRapido
from cayal.parametros_contpaqi import ParametrosContpaqi
from cayal.comandos_base_datos import ComandosBaseDatos
from panel_principal import PanelPrincipal
from cayal.util import Utilerias


if __name__ == '__main__':

    parametros = ParametrosContpaqi()
    parametros.id_principal = 97947
    parametros.id_usuario = 65
    parametros.id_modulo = 1400

    base_de_datos = ComandosBaseDatos(parametros.cadena_conexion)
    utilerias = Utilerias()
    saldo = base_de_datos.fetchone('SELECT ISNULL(Balance,0) FROM docDocument WHERE DocumentID = ?',(
        parametros.id_principal,))

    saldo_decimal = utilerias.redondear_valor_cantidad_a_decimal(saldo)

    ventana = ttk.Window()

    if saldo_decimal != 0:
        interfaz = InterfazCobroRapido(ventana)
        controlador = ControladorCobroRapido(interfaz, parametros)
    else:
        instancia = PanelPrincipal(ventana, base_de_datos, utilerias, parametros)

    ventana.mainloop()