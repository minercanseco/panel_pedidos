from capturar_documento.herramientas.depositos.llamar_instancia_deposito import LlamarInstanciaDeposito
from capturar_documento.buscar_generales_cliente import BuscarGeneralesCliente
from capturar_documento.herramientas.cobrar_cartera.buscar_generales_cliente_cartera import BuscarGeneralesClienteCartera

from capturar_documento.herramientas.verificador.controlador_verificador import ControladorVerificador
from capturar_documento.herramientas.verificador.interfaz_verificador import InterfazVerificador
from capturar_documento.llamar_instancia_captura import LlamarInstanciaCaptura
from capturar_documento.selector_modulo.servicio_impresion_silenciosa import ServicioImpresionSilenciosa
from capturar_documento.herramientas.cobro_rapido.llamar_instancia_cobro_rapido import LlamarInstanciaCobroRapido


class ControladorSelectorModulo:
    def __init__(self, interfaz, modelo):
        self._interfaz = interfaz
        self._modelo = modelo

        self._TABLAS = {'tbv_facturas':None, 'tbv_tickets':None, 'tbv_depositos':None, 'tbv_cobros':None}
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
        self._configurar_aplicativo()
        self._inyectar_funciones_barra_herramientas()

    def _configurar_aplicativo(self):
        self._actualizar_etiquetas_tablas()
        self._actualizar_tablas()

    def _actualizar_etiquetas_tablas(self):

        texto = f"PAQUETE: panel_ventas_minisuper OPERADOR: {self._modelo.obtener_nombre_usuario()}"

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
            'cobrar_cartera': self._cobrar_cartera
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
        for tabla in self._TABLAS:
            columnas_str, ancho_columnas_str, primary_key = self._modelo.obtener_columnas(tabla)
            if not columnas_str:
                continue

            columnas = self._crear_columnas_tabla(columnas_str, ancho_columnas_str)
            self._TABLAS[tabla] = columnas

            registros = self._modelo.obtener_registros(tabla, columnas_str, primary_key)
            _registros = self._procesar_registros_consultas(registros)
            self._interfaz.ventanas.rellenar_table_view(tabla, columnas, _registros)

        self._interfaz.ventanas.refrescar_tamano_forma()

    def _reiniciar_parametros(self):
        self._modelo.parametros.id_modulo = 0
        self._modelo.parametros.id_principal = 0

    def _ejecutar_accion(self, funcion, id_modulo=0, id_principal=0, esperar_ventana=False):
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
                ventana.wait_window()

            return resultado

        finally:
            self._reiniciar_parametros()
            self._ejecutando = False

    def _nuevo_ticket(self):
        return self._ejecutar_accion(
            funcion=lambda ventana: LlamarInstanciaCaptura(
                ventana,
                self._modelo.parametros
            ),
            id_modulo=158
        )

    def _nueva_factura(self):
        return self._ejecutar_accion(
            funcion=lambda ventana: BuscarGeneralesCliente(
                ventana,
                self._modelo.parametros
            ),
            id_modulo=1400,
            esperar_ventana=True
        )

    def _nuevo_deposito(self):
        return self._ejecutar_accion(
            funcion=lambda ventana: LlamarInstanciaDeposito(
                ventana,
                self._modelo.parametros,
                self._modelo.base_de_datos
            )
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

        id_principal = fila.get('DocumentID', 0)

        return self._ejecutar_accion(
            funcion=lambda ventana: LlamarInstanciaCobroRapido(
               ventana,
                self._modelo.parametros,
                self._modelo.base_de_datos
            ),
            id_modulo=158 if fila['Tabla'] == 'tbv_tickets' else 1400,
            id_principal=id_principal
        )

    def _imprimir(self):
        fila = self._obtener_valores_fila()

        servicio = ServicioImpresionSilenciosa(
            parametros=self._modelo.parametros,
            modelo=self._modelo
        )

        servicio.imprimir(
            id_modulo=1400 if fila['Tabla'] == 'tbv_facturas' else 158,
            id_principal=fila.get("DocumentID", 0),
            id_usuario=self._modelo.parametros.id_usuario
        )

    def _cobrar_cartera(self):
        return self._ejecutar_accion(
            funcion=lambda ventana: BuscarGeneralesClienteCartera(ventana,
                self._modelo.parametros
            ),
            id_modulo=1400,
            id_principal=0
        )

