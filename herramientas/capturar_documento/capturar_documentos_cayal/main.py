import ttkbootstrap as ttk 

from cayal.actualizador_de_paquetes import ActualizadorDePaquetes
from cayal.generar_contexto_ia import GenerarContextoIA
from cayal.parametros_contpaqi import ParametrosContpaqi
from capturar_documento.buscar_generales_cliente import BuscarGeneralesCliente
from capturar_documento.buscar_generales_proveedor import BuscarGeneralesProveedor
from capturar_documento.llamar_instancia_captura import LlamarInstanciaCaptura
from capturar_documento.llamar_instancia_captura_pedido import LlamarInstanciaCapturaPedido

from capturar_documento.selector_modulo.controlador_selector_modulo import ControladorSelectorModulo
from capturar_documento.selector_modulo.modelo_selector_modulo import ModeloSelectorModulo
from capturar_documento.selector_modulo.interfaz_selector_modulo import InterfazSelectorModulo

from cayal.login import Login



def si_acceso_exitoso(parametros=None, master=None):
    llamar_instancia_fuera_del_sistema(master, parametros)

def llamar_instancia_fuera_del_sistema(ventana, parametros):
    interfaz = InterfazSelectorModulo(ventana)
    modelo = ModeloSelectorModulo(parametros)
    ControladorSelectorModulo(interfaz, modelo)
    ventana.mainloop()


if __name__ == '__main__':
    ventana_login = ttk.Window()
    parametros_login = ParametrosContpaqi()

    NOMBRE_PAQUETE_DESARROLLO = 'pos_ventas_cayal_v119'

    parametros_login.version_paquete = NOMBRE_PAQUETE_DESARROLLO

    actualizador = ActualizadorDePaquetes(NOMBRE_PAQUETE_DESARROLLO)
    nueva_version = actualizador.verificar_version_actualizada()
    solo_contexto = False

    if solo_contexto:
        gen = GenerarContextoIA(root='.', out='contexto.md')
        ruta = gen.build()
        print('Contexto generado en:', ruta)

    if nueva_version:
        actualizador.actualizar_con_interfaz(ventana_login)


    if not nueva_version:
        if parametros_login.id_modulo == 0:
            parametros_login.id_modulo = 1687
            instancia_login = Login(
                ventana_login,
                parametros_login,
                si_acceso_exitoso,
            )

        elif (
                parametros_login.id_modulo == 1687
                and parametros_login.id_principal != 0):
            instancia = LlamarInstanciaCapturaPedido(
                ventana_login, parametros_login
            )

        elif (
                parametros_login.id_principal != 0
                and parametros_login.id_modulo in (152, 158)):
            # Invocación desde la base de datos.
            instancia = LlamarInstanciaCaptura(
                ventana_login, parametros_login
            )

        elif parametros_login.id_modulo == 158:  # módulo de tickets
            instancia = LlamarInstanciaCaptura(
                ventana_login, parametros_login
            )

        elif parametros_login.id_modulo in (21, 967, 1400, 1316, 1687):
            instancia = BuscarGeneralesCliente(
                ventana_login, parametros_login
            )

        elif parametros_login.id_modulo == 152:  # compras
            instancia = BuscarGeneralesProveedor(
                ventana_login, parametros_login
            )

        ventana_login.mainloop()
