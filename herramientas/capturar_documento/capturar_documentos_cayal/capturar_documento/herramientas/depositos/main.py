import datetime

import ttkbootstrap as ttk
from cayal.login import Login
from cayal.parametros_contpaqi import ParametrosContpaqi
from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.util import Utilerias
from capturar_documento.herramientas.depositos.aceptar_depositos_vendedores import AceptarDepositosVendedores
from capturar_documento.herramientas.depositos.agregar_depositos import AgregarDeposito


def si_acceso_exitoso(parametros=None, master=None):

    llamar_instancia_principal(master, parametros)

def llamar_instancia_principal(ventana, parametros):
    base_de_datos = ComandosBaseDatos()
    parametros.id_grupo_usuario = base_de_datos.fetchone('SELECT UserGroupID FROM engUser WHERE UserID = ?',
                                                         (parametros.id_usuario,)
                                                         )
    pendientes = base_de_datos.fetchone("""
        SELECT COUNT(ID)
        FROM  zvwDepositosDiariosCayalNoAceptados M
        WHERE 
            CAST(M.Fecha AS DATE) = CAST(GETDATE() AS DATE)
            AND ISNULL(M.StatusAceptado,0) = 0;

        """)

    # Día 6 es domingo
    dia = datetime.datetime.weekday(datetime.datetime.today())
    grupo_usuario = parametros.id_grupo_usuario
    aceptar_depositos = 0

    if dia == 6 and pendientes != 0 and grupo_usuario == 11:
        ventana.position_center()
        respuesta = ttk.dialogs.Messagebox.yesno(
            message= '¿Desea recepcionar depósitos de vendedores?.',
            parent=ventana)

        if respuesta != 'No':
            aceptar_depositos = 1

    if grupo_usuario != 11 and pendientes != 0:
        ventana.position_center()
        respuesta = ttk.dialogs.Messagebox.yesno(
            message='¿Desea recepcionar depósitos de vendedores?.',
            parent=ventana)

        if respuesta != 'No':
            aceptar_depositos = 1

    utilerias = Utilerias()

    if aceptar_depositos == 0:
        instancia = AgregarDeposito(ventana, base_de_datos, utilerias, parametros)

    if aceptar_depositos == 1:
        instancia = AceptarDepositosVendedores(ventana, base_de_datos, utilerias, parametros)

    ventana.mainloop()

if __name__ == '__main__':
    parametros = ParametrosContpaqi()

    ventana_login = ttk.Window()
    #parametros.id_usuario = 100
    if parametros.id_usuario > 0:
        llamar_instancia_principal(ventana_login, parametros)

    else:
        instancia = Login(ventana_login, parametros, si_acceso_exitoso)
        ventana_login.mainloop()
