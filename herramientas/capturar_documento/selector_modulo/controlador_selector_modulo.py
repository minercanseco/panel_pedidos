from capturar_documento.herramientas.depositos.llamar_instancia_deposito import LlamarInstanciaDeposito
from capturar_documento.buscar_generales_cliente import BuscarGeneralesCliente
from capturar_documento.herramientas.cobrar_cartera.buscar_generales_cliente_cartera import BuscarGeneralesClienteCartera

from capturar_documento.herramientas.verificador.controlador_verificador import ControladorVerificador
from capturar_documento.herramientas.verificador.interfaz_verificador import InterfazVerificador
from capturar_documento.llamar_instancia_captura import LlamarInstanciaCaptura
from capturar_documento.herramientas.imprimir_modulo.main import (
    ImprimirModulo,
    existe_archivo_impresoras,
)
from capturar_documento.herramientas.cobro_rapido.llamar_instancia_cobro_rapido import LlamarInstanciaCobroRapido
from capturar_documento.herramientas.abrir_cajon import CajonCobro


class ControladorSelectorModulo:
    def __init__(self, interfaz, modelo):
        self._interfaz = interfaz
        self._modelo = modelo

        self._TABLAS = {
            'tbv_tickets': None,
            'tbv_facturas': None,
            'tbv_depositos': None,
        }
        self._ICONOS_ESPECIALES = {
            'CanceladoIcon': 'Cancelled16.ico',
            'CancelledIcon': 'Cancelled16.ico',
            'ConQuejaIcon': 'warning16.ico',
            'CobroTarjetaIcon': 'CreditCard16.ico',
            'ConDescuentoCayalIcon': 'Ecommerce16.ico',
            'PrintedIcon': 'print16.ico',
            'CorreoEnviadoIcon': 'Email16.ico'
        }

        self._ICONOS_TEXTO = {
            "CanceladoIcon": "❌",
            "CancelledIcon": "❌",
            "ConQuejaIcon": "⚠️",
            "CobroTarjetaIcon": "💳",
            "ConDescuentoCayalIcon": "🏷️",
            "CorreoEnviadoIcon": "📧",
            "PrintedIcon": "🖨️",
        }

        self._ejecutando = False
        self._inyectar_funciones_barra_herramientas()
        self._configurar_aplicativo()
        self._agregar_atajos()
        self._programar_actualizacion()

    def _configurar_aplicativo(self):
        self._interfaz.actualizar_titulo_usuario(
            self._modelo.user_name
        )
        self._actualizar_etiquetas_tablas()
        self._actualizar_tablas()

    def _actualizar_etiquetas_tablas(self):

        texto = (
            'PAQUETE: panel_ventas_minisuper '
            f'OPERADOR: {self._modelo.user_name}'
        )

        for tabla, campos in self._TABLAS.items():
            self._interfaz.ventanas.actualizar_etiqueta_externa_tabla_view(tabla,texto)

    def _crear_columnas_tabla(self, columnas_str, ancho_columnas_str):

        columnas = [
            columna.strip()
            for columna in columnas_str.replace('[', '').replace(']', '').split(',')
        ]

        anchos_columnas = [
            ancho.strip()
            for ancho in ancho_columnas_str.split(',')
        ]

        if len(columnas) != len(anchos_columnas):
            raise ValueError(
                f"Columnas ({len(columnas)}) y anchos ({len(anchos_columnas)}) no coinciden."
            )



        if not hasattr(self, '_iconos_columnas'):
            self._iconos_columnas = {}

        columnas_tabla = []

        for i, col in enumerate(columnas):

            es_icono = col.endswith('Icon')

            columna = {
                "text": "" if es_icono else col,
                "stretch": False,
                "width": int(anchos_columnas[i])
            }

            nombre_icono = self._ICONOS_ESPECIALES.get(col)

            if nombre_icono:
                icono = self._interfaz.ventanas.obtener_icono(nombre_icono)

                self._iconos_columnas[col] = icono

                columna["image"] = icono
                columna["text"] = ""

            columnas_tabla.append(columna)

        return  self._interfaz.ventanas.ajustar_columnas_a_resolucion(
            columnas_tabla,
            margen=80,
            factor_maximo=1.25,
            escalar_solo_si_excede=True
        )

    def _procesar_registros_consultas(self, consulta):
        data = []



        for reg in consulta:
            nuevo_reg = {}

            for clave, valor in reg.items():

                if clave not in self._ICONOS_ESPECIALES:
                    nuevo_reg[clave] = valor
                    continue

                if valor not in (0, None, False, "", "0"):
                    nuevo_reg[clave] = self._ICONOS_TEXTO.get(clave, "✓")
                else:
                    nuevo_reg[clave] = ""

            data.append(nuevo_reg)

        return data

    def _inyectar_funciones_barra_herramientas(self):
        funciones = {
            'nuevo_ticket': self._nuevo_ticket,
            'nueva_factura': self._nueva_factura,
            'nuevo_deposito': self._nuevo_deposito,
            'actualizar':self._actualizar_tablas,
            'verificador': self._verificador,
            'imprimir':self._imprimir,
            'cobro_rapido':self._cobro_rapido,
            'cobrar_cartera': self._cobrar_cartera,
            'abrir_cajon': self._abrir_cajon,
        }

        for item in self._interfaz.barra_herramientas:
            nombre = item.get('nombre')

            if nombre in funciones:
                item['comando'] = funciones[nombre]

        self._interfaz.elementos_barra_herramientas = (
            self._interfaz.ventanas.crear_barra_herramientas(
                self._interfaz.barra_herramientas,
                'frame_herramientas'
            )
        )

        self._interfaz.etiquetas_barra_herramientas = (
            self._interfaz.elementos_barra_herramientas[2]
        )

        self._interfaz.hotkeys_barra_herramientas = (
            self._interfaz.elementos_barra_herramientas[1]
        )

    def _obtener_valores_fila(self):
        tabla = self._interfaz.obtener_tabla_activa()
        filas = self._interfaz.ventanas.procesar_filas_table_view(tabla, seleccionadas=True)
        if not filas:
            return False

        if len(filas) != 1:
            return False

        fila = filas[0]
        fila['Tabla'] = tabla

        return fila

    def _actualizar_tablas(self):
        if self._ejecutando:
            return

        self._interfaz.mostrar_estado('Actualizando documentos...')
        total_registros = 0
        errores = []
        for tabla in self._TABLAS:
            try:
                cantidad = self._actualizar_tabla(tabla)
                total_registros += cantidad
            except Exception as error:
                errores.append(f'{tabla}: {error}')

        self._interfaz.ventanas.refrescar_tamano_forma()
        if errores:
            self._interfaz.mostrar_estado(
                f'Actualización parcial ({total_registros} documentos)'
            )
            self._interfaz.ventanas.mostrar_mensaje(
                'No fue posible actualizar todas las tablas:\n'
                + '\n'.join(errores),
                self._interfaz._master,
            )
        else:
            self._interfaz.mostrar_estado(
                f'{total_registros} documentos cargados'
            )

    def _actualizar_tabla(self, tabla):
        columnas_str, ancho_columnas_str, primary_key = (
            self._modelo.obtener_columnas(tabla)
        )
        if not columnas_str:
            self._interfaz.actualizar_contador_tabla(tabla, 0)
            return 0

        columnas = self._crear_columnas_tabla(
            columnas_str, ancho_columnas_str
        )
        self._TABLAS[tabla] = columnas

        registros = self._modelo.obtener_registros(
            tabla, columnas_str, primary_key
        ) or []
        registros_procesados = self._procesar_registros_consultas(
            registros
        )
        self._interfaz.ventanas.rellenar_table_view(
            tabla, columnas, registros_procesados
        )
        self._interfaz.actualizar_contador_tabla(
            tabla, len(registros_procesados)
        )
        return len(registros_procesados)

    def _agregar_atajos(self):
        self._interfaz.ventanas.agregar_hotkeys_forma({
            'F2': self._nuevo_ticket,
            'F3': self._nueva_factura,
            'F4': self._nuevo_deposito,
            'F5': self._actualizar_tablas,
            'F6': self._cobrar_cartera,
            'F7': self._abrir_cajon,
            'Ctrl+P': self._imprimir,
        })

    def _programar_actualizacion(self):
        def actualizar():
            try:
                if not self._ejecutando:
                    self._actualizar_tablas()
                self._interfaz._master.after(60000, actualizar)
            except Exception:
                # La ventana probablemente fue destruida.
                return

        self._interfaz._master.after(60000, actualizar)

    def _reiniciar_parametros(self):
        self._modelo.parametros.id_modulo = 0
        self._modelo.parametros.id_principal = 0
        self._modelo.parametros.id_seleccionados = []

    def _ejecutar_accion(
            self, funcion, id_modulo=0, id_principal=0,
            esperar_ventana=True, tabla_actualizar=None,
    ):
        if self._ejecutando:
            return None

        ventana = None

        try:
            self._ejecutando = True

            self._modelo.parametros.id_modulo = id_modulo
            self._modelo.parametros.id_principal = id_principal

            ventana = self._interfaz.ventanas.crear_popup_ttkbootstrap()

            resultado = funcion(ventana)

            if esperar_ventana and ventana:
                # Varias capturas esperan y destruyen internamente la misma
                # ventana. No debemos volver a esperar un Toplevel destruido.
                try:
                    if ventana.winfo_exists():
                        ventana.wait_window()
                except Exception:
                    # La ventana pudo cerrarse entre winfo_exists y wait_window.
                    pass

            return resultado

        finally:
            self._reiniciar_parametros()
            self._ejecutando = False
            self._actualizar_despues_de_accion(tabla_actualizar)

    def _actualizar_despues_de_accion(self, tablas):
        if not tablas:
            return

        if isinstance(tablas, str):
            tablas = (tablas,)

        try:
            for tabla in tablas:
                self._actualizar_tabla(tabla)
            self._interfaz.ventanas.refrescar_tamano_forma()
            self._interfaz.mostrar_estado(
                'Operación terminada; información actualizada'
            )
        except Exception as error:
            self._interfaz.mostrar_estado(
                f'Operación terminada; no fue posible actualizar: {error}'
            )

    def _nuevo_ticket(self):
        return self._ejecutar_accion(
            funcion=lambda ventana: LlamarInstanciaCaptura(
                ventana,
                self._modelo.parametros
            ),
            id_modulo=158,
            tabla_actualizar='tbv_tickets',
        )

    def _nueva_factura(self):
        return self._ejecutar_accion(
            funcion=lambda ventana: BuscarGeneralesCliente(
                ventana,
                self._modelo.parametros
            ),
            id_modulo=1400,
            tabla_actualizar='tbv_facturas',
        )

    def _nuevo_deposito(self):
        return self._ejecutar_accion(
            funcion=lambda ventana: LlamarInstanciaDeposito(
                ventana,
                self._modelo.parametros,
                self._modelo.base_de_datos
            ),
            tabla_actualizar='tbv_depositos',
        )

    def _verificador(self):
        return self._ejecutar_accion(
            funcion=lambda ventana: ControladorVerificador(
                InterfazVerificador(ventana),
                self._modelo.parametros
            )
        )

    def _cobro_rapido(self):
        fila = self._obtener_valores_fila()
        if not fila:
            self._interfaz.ventanas.mostrar_mensaje(
                'Seleccione un ticket o factura para realizar el cobro.'
            )
            return None
        if fila['Tabla'] not in ('tbv_tickets', 'tbv_facturas'):
            self._interfaz.ventanas.mostrar_mensaje(
                'El cobro rápido sólo aplica a tickets y facturas.'
            )
            return None

        id_principal = fila.get('DocumentID', 0)

        return self._ejecutar_accion(
            funcion=lambda ventana: LlamarInstanciaCobroRapido(
               ventana,
                self._modelo.parametros,
                self._modelo.base_de_datos
            ),
            id_modulo=158 if fila['Tabla'] == 'tbv_tickets' else 1400,
            id_principal=id_principal,
            tabla_actualizar=fila['Tabla'],
        )

    def _imprimir(self):
        fila = self._obtener_valores_fila()
        if not fila:
            self._interfaz.ventanas.mostrar_mensaje(
                'Seleccione un ticket o factura para imprimir.'
            )
            return None
        if fila['Tabla'] not in ('tbv_tickets', 'tbv_facturas'):
            self._interfaz.ventanas.mostrar_mensaje(
                'La impresión desde este panel sólo aplica a tickets y facturas.'
            )
            return None

        document_id = int(fila.get('DocumentID', 0) or 0)
        self._modelo.parametros.id_seleccionados = [document_id]
        return self._ejecutar_accion(
            funcion=lambda ventana: ImprimirModulo(
                ventana,
                self._modelo.parametros,
                predeterminar=False,
                configuracion=existe_archivo_impresoras(),
                impresion_silenciosa=True,
            ),
            id_modulo=(
                1400 if fila['Tabla'] == 'tbv_facturas' else 158
            ),
            id_principal=document_id,
            tabla_actualizar=fila['Tabla'],
        )

    def _cobrar_cartera(self):
        return self._ejecutar_accion(
            funcion=lambda ventana: BuscarGeneralesClienteCartera(ventana,
                self._modelo.parametros
            ),
            id_modulo=1400,
            id_principal=0,
            tabla_actualizar=('tbv_tickets', 'tbv_facturas'),
        )

    def _abrir_cajon(self):
        cajon = CajonCobro('Tickets')
        if cajon.abrir_cajon():
            self._interfaz.mostrar_estado(
                'Cajón abierto mediante la impresora Tickets'
            )
            return
        self._interfaz.mostrar_estado('No fue posible abrir el cajón')
        self._interfaz.ventanas.mostrar_mensaje(
            f'No fue posible abrir el cajón:\n{cajon.ultimo_error}',
            self._interfaz._master,
        )
