import re
from datetime import datetime, time, timedelta
from threading import Thread

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
from capturar_documento.herramientas.imprimir_modulo.definir_impresoras import (
    DefinirImpresoras,
)
from capturar_documento.herramientas.imprimir_modulo.corte_caja import MODULO_CORTE_CAJA
from capturar_documento.herramientas.cobro_rapido.llamar_instancia_cobro_rapido import LlamarInstanciaCobroRapido
from capturar_documento.herramientas.abrir_cajon import CajonCobro
from capturar_documento.herramientas.editar_generales.controlador import (
    ControladorEditarDocumento,
)
from capturar_documento.herramientas.editar_generales.interfaz import (
    InterfazEditarDocumento,
)
from capturar_documento.herramientas.editar_generales.modelo import (
    ModeloEditarDocumento,
)
from capturar_documento.herramientas.agregar_queja.controlador import (
    ControladorAgregarQueja,
)
from capturar_documento.herramientas.agregar_queja.interfaz import (
    Interfaz as InterfazAgregarQueja,
)
from capturar_documento.herramientas.agregar_queja.modelo import (
    Modelo as ModeloAgregarQueja,
)
from capturar_documento.herramientas.corte_de_caja.main import (
    abrir_corte_de_caja,
)
from capturar_documento.herramientas.capturar_cliente.main import (
    abrir_captura_cliente,
)
from capturar_documento.herramientas.dividir_facturas_cayal.main import (
    abrir_division_documento,
)
from capturar_documento.herramientas.cfdi_relacionados.controlador import (
    ControladorRelacionarFactura,
)
from capturar_documento.herramientas.cfdi_relacionados.interfaz import (
    InterfazRelacionarFactura,
)
from capturar_documento.herramientas.cfdi_relacionados.modelo import (
    ModeloRelacionarFactura,
)
from capturar_documento.herramientas.intercambiar_rfc.controlador_intercambio_rfc import (
    ControladorIntercambioRFC,
)
from capturar_documento.herramientas.intercambiar_rfc.interfaz_intercambio_rfc import (
    InterfazIntercambioRfc,
)
from capturar_documento.herramientas.intercambiar_rfc.modelo_intercambio_rfc import (
    ModeloIntercambioRFC,
)
from capturar_documento.herramientas.convertir_documento.controlador import (
    ControladorConvertirDocumento,
)
from capturar_documento.herramientas.convertir_documento.interfaz import (
    InterfazConvertirDocumento,
)
from capturar_documento.herramientas.convertir_documento.modelo import (
    ModeloConvertirDocumento,
)
class ControladorSelectorModulo:
    def __init__(self, interfaz, modelo):
        self._interfaz = interfaz
        self._modelo = modelo

        self._TABLAS = {
            'tbv_tickets': None,
            'tbv_facturas': None,
            'tbv_facturas_globales': None,
            'tbv_depositos': None,
            'tbv_cortes': None,
        }
        self._ICONOS_ESPECIALES = {
            'CanceladoIcon': 'Cancelled16.ico',
            'CancelledIcon': 'Cancelled16.ico',
            'ConQuejaIcon': 'warning16.ico',
            'CobroTarjetaIcon': 'CreditCard16.ico',
            'ConDescuentoCayalIcon': 'Ecommerce16.ico',
            'PrintedIcon': 'print16.ico',
            'CorreoEnviadoIcon': 'Email16.ico',
            'RecalculadoIcon': 'Valid16.ico'
        }

        self._ICONOS_TEXTO = {
            "CanceladoIcon": "❌",
            "CancelledIcon": "❌",
            "ConQuejaIcon": "⚠️",
            "CobroTarjetaIcon": "💳",
            "ConDescuentoCayalIcon": "🏷️",
            "CorreoEnviadoIcon": "📧",
            "PrintedIcon": "🖨️",
            'RecalculadoIcon': "✓"
        }

        self._ejecutando = False
        self._globalizacion_en_curso = False
        self._configuracion_impresoras_abierta = False
        self._seguimiento_timbrado = None
        self._consulta_timbrado_en_curso = None
        self._inyectar_funciones_barra_herramientas()
        self._agregar_eventos_tablas()
        self._configurar_aplicativo()
        self._agregar_atajos()
        self._programar_actualizacion()
        self._programar_configuracion_impresoras()

    def _programar_configuracion_impresoras(self):
        if existe_archivo_impresoras():
            return

        # Permite que el selector termine de mostrarse y maximizarse antes de
        # colocar encima la configuración obligatoria.
        self._interfaz._master.after(
            350,
            self._asegurar_impresoras_configuradas,
        )

    def _asegurar_impresoras_configuradas(self):
        if existe_archivo_impresoras():
            return True
        if self._configuracion_impresoras_abierta:
            return False

        self._configuracion_impresoras_abierta = True
        ventana = (
            self._interfaz.ventanas.crear_popup_ttkbootstrap_async(
                titulo='Configuración obligatoria de impresoras',
                master=self._interfaz._master,
                cascade=False,
            )
        )
        DefinirImpresoras(
            ventana,
            obligatoria=True,
            bloquear=False,
            al_guardar=self._impresoras_configuradas,
        )
        return False

    def _impresoras_configuradas(self, primaria, secundaria, ruta_archivo):
        self._configuracion_impresoras_abierta = False
        self._interfaz.mostrar_estado(
            'Impresoras principal y secundaria configuradas'
        )

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

                nombre_normalizado = re.sub(
                    r'[^a-z]',
                    '',
                    str(clave).lower(),
                )
                if nombre_normalizado in ('hora', 'horaventa'):
                    nuevo_reg[clave] = self._formatear_hora_selector(valor)
                    continue

                if clave not in self._ICONOS_ESPECIALES:
                    nuevo_reg[clave] = valor
                    continue

                if valor not in (0, None, False, "", "0"):
                    nuevo_reg[clave] = self._ICONOS_TEXTO.get(clave, "✓")
                else:
                    nuevo_reg[clave] = ""

            data.append(nuevo_reg)

        return data

    @staticmethod
    def _formatear_hora_selector(valor):
        """Convierte valores de hora de SQL al formato visual HH:MM:SS."""
        if valor in (None, ''):
            return ''

        if isinstance(valor, (datetime, time)):
            return valor.strftime('%H:%M:%S')

        if isinstance(valor, timedelta):
            segundos = int(valor.total_seconds()) % (24 * 60 * 60)
            horas, resto = divmod(segundos, 60 * 60)
            minutos, segundos = divmod(resto, 60)
            return '{:02d}:{:02d}:{:02d}'.format(
                horas,
                minutos,
                segundos,
            )

        texto = str(valor).strip()
        coincidencia = re.search(
            r'(?:^|[ T])(\d{1,2}):(\d{2})(?::(\d{2}))?',
            texto,
        )
        if not coincidencia:
            return texto

        horas = int(coincidencia.group(1))
        minutos = int(coincidencia.group(2))
        segundos = int(coincidencia.group(3) or 0)
        if horas > 23 or minutos > 59 or segundos > 59:
            return texto

        return '{:02d}:{:02d}:{:02d}'.format(
            horas,
            minutos,
            segundos,
        )

    def _inyectar_funciones_barra_herramientas(self):
        funciones = {
            'nuevo_ticket': self._nuevo_ticket,
            'nueva_factura': self._nueva_factura,
            'nuevo_deposito': self._nuevo_deposito,
            'nuevo_corte_caja': self._nuevo_corte_caja,
            'editar_cliente': self._editar_cliente,
            'capturar_cliente': self._capturar_cliente,
            'actualizar':self._actualizar_tablas,
            'verificador': self._verificador,
            'imprimir':self._imprimir,
            'cobro_rapido':self._cobro_rapido,
            'cobrar_cartera': self._cobrar_cartera,
            'abrir_cajon': self._abrir_cajon,
            'editar_generales': self._editar_generales,
            'agregar_queja': self._agregar_queja,
            'globalizar': self._globalizar,
            'dividir_documento': self._dividir_documento,
            'timbrar': self._timbrar,
            'cfdi_relacionados': self._cfdi_relacionados,
            'intercambiar_rfc': self._intercambiar_rfc,
            'enviar_correos': self._enviar_correos,
            'convertir_documento': self._convertir_documento,
            'listas_precios': self._listas_precios,
            'archivo_mayoreo': self._archivo_mayoreo,
            'archivo_minisuper': self._archivo_minisuper,
            'archivo_complementos': self._archivo_complementos,
        }

        for item in self._interfaz.barra_herramientas:
            nombre = item.get('nombre')

            if nombre in funciones:
                item['comando'] = funciones[nombre]

        iconos = []
        hotkeys = []
        etiquetas = []

        for seccion, nombre_frame in (
            self._interfaz.frames_barra_herramientas.items()
        ):
            herramientas = [
                item for item in self._interfaz.barra_herramientas
                if item.get('seccion', 'generales') == seccion
            ]
            if not herramientas:
                continue

            elementos = self._interfaz.ventanas.crear_barra_herramientas(
                herramientas,
                nombre_frame,
            )
            if not elementos:
                continue

            iconos.extend(elementos[0])
            hotkeys.extend(elementos[1])
            etiquetas.extend(elementos[2])

        self._interfaz.elementos_barra_herramientas = (
            iconos,
            hotkeys,
            etiquetas,
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

    def _obtener_folios_documentos(self, documentos):
        """Obtiene referencias amigables sin interrumpir la herramienta."""
        documentos = [
            int(document_id) for document_id in (documentos or [])
            if document_id
        ]
        try:
            folios = self._modelo.obtener_folios_documentos(documentos)
        except Exception:
            folios = {}
        return {
            document_id: str(folios.get(document_id) or document_id)
            for document_id in documentos
        }

    def _actualizar_tablas(self):
        if self._ejecutando or self._configuracion_impresoras_abierta:
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
        if tabla == 'tbv_facturas_globales':
            registros = self._modelo.obtener_facturas_globales() or []
            nombres_columnas = [
                'DocumentID', 'BusinessEntityName', 'DocFolio',
                'DateDocument', 'CancelledIcon', 'CFDStatusID',
                'CFDStatusName',
                'CFDStatusCancelledName', 'CFDStatusError',
                'CFDCancelledStatusID', 'Usuario', 'TimbradoPor',
                'HoraVenta', 'Comentarios', 'CanceladoPor', 'CreatedBy',
                'EstadoTimbrado',
            ]
            anchos_columnas = [
                0, 210, 100, 100, 55, 0, 105,
                130, 200, 0, 105, 110, 150, 220, 120, 0, 165,
            ]
            columnas_str = ', '.join(
                '[{}]'.format(nombre) for nombre in nombres_columnas
            )
            ancho_columnas_str = ', '.join(
                str(ancho) for ancho in anchos_columnas
            )
            columnas = self._crear_columnas_tabla(
                columnas_str, ancho_columnas_str,
            )
            self._TABLAS[tabla] = columnas
            registros_procesados = self._procesar_registros_consultas(
                registros
            )
            self._interfaz.ventanas.rellenar_table_view(
                tabla, columnas, registros_procesados,
            )
            self._interfaz.actualizar_contador_tabla(tabla, len(registros))
            return len(registros)

        if tabla == 'tbv_cortes':
            registros = self._modelo.obtener_cortes_caja() or []
            nombres_columnas = [
                'ID', 'Fecha', 'Mes', 'Hora', 'Documentos', 'Ventas',
                'Depositos', 'Tarjetas', 'EfectivoSistema',
                'EfectivoCajero', 'Faltante', 'Sobrante',
                'Transferencias', 'Cheques', 'Gastos', 'Anticipos',
                'Comentario', 'Cajero', 'Validado', 'ValidadoPor',
                'Incidencia', 'Folio', 'CreatedBy',
            ]
            anchos_columnas = [
                0, 95, 75, 145, 85, 100,
                100, 100, 115, 115, 95, 95,
                110, 95, 95, 95,
                220, 110, 75, 110,
                180, 90, 0,
            ]
            columnas_str = ', '.join(
                '[{}]'.format(nombre) for nombre in nombres_columnas
            )
            ancho_columnas_str = ', '.join(
                str(ancho) for ancho in anchos_columnas
            )
            columnas = self._crear_columnas_tabla(
                columnas_str,
                ancho_columnas_str,
            )
            self._TABLAS[tabla] = columnas
            self._interfaz.ventanas.rellenar_table_view(
                tabla,
                columnas,
                self._procesar_registros_consultas(registros),
            )
            self._interfaz.actualizar_contador_tabla(tabla, len(registros))
            return len(registros)

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

    def _agregar_eventos_tablas(self):
        self._interfaz.ventanas.cargar_eventos({
            'tbv_cortes': (
                lambda _event: self._visualizar_corte_caja(),
                'doble_click',
            ),
        })

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
            id_modulo=1664,
            tabla_actualizar='tbv_depositos',
        )

    def _nuevo_corte_caja(self):
        return self._ejecutar_accion(
            funcion=lambda ventana: abrir_corte_de_caja(
                ventana,
                self._modelo.parametros,
            ),
            id_principal=0,
            tabla_actualizar='tbv_cortes',
        )

    def _capturar_cliente(self):
        business_entity_id = 0

        return self._ejecutar_accion(
            funcion=lambda ventana: abrir_captura_cliente(
                ventana,
                self._modelo.parametros,
            ),
            id_principal=business_entity_id,
            tabla_actualizar='tbv_facturas' if business_entity_id else None,
        )

    def _editar_cliente(self):
        tabla = self._interfaz.obtener_tabla_activa()
        business_entity_id = 0

        if tabla == 'tbv_facturas':
            filas = self._interfaz.ventanas.procesar_filas_table_view(
                tabla,
                seleccionadas=True,
            )


            if len(filas) > 1:
                self._interfaz.ventanas.mostrar_mensaje(
                    'Seleccione una sola factura para editar su cliente.'
                )
                return None

            if len(filas) == 1:
                document_id = int(filas[0].get('DocumentID', 0) or 0)
                business_entity_id = self._modelo.obtener_cliente_documento(
                    document_id
                )
                if business_entity_id <= 0:
                    self._interfaz.ventanas.mostrar_mensaje(
                        'No fue posible identificar el cliente de la factura.'
                    )
                    return None

        return self._ejecutar_accion(
            funcion=lambda ventana: abrir_captura_cliente(
                ventana,
                self._modelo.parametros,
            ),
            id_principal=business_entity_id,
            tabla_actualizar='tbv_facturas' if business_entity_id else None,
        )

    def _visualizar_corte_caja(self):
        fila = self._obtener_valores_fila()
        if not fila or fila.get('Tabla') != 'tbv_cortes':
            return None

        corte_id = int(fila.get('ID', 0) or 0)
        if corte_id <= 0:
            self._interfaz.ventanas.mostrar_mensaje(
                'No fue posible identificar el corte seleccionado.'
            )
            return None

        return self._ejecutar_accion(
            funcion=lambda ventana: abrir_corte_de_caja(
                ventana,
                self._modelo.parametros,
            ),
            id_principal=corte_id,
            tabla_actualizar='tbv_cortes',
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

    def _agregar_queja(self):
        fila = self._obtener_valores_fila()
        if not fila:
            self._interfaz.ventanas.mostrar_mensaje(
                'Seleccione un solo documento para agregar o consultar sus quejas.'
            )
            return None

        document_id = int(fila.get('DocumentID', 0) or 0)
        if document_id <= 0:
            self._interfaz.ventanas.mostrar_mensaje(
                'No fue posible identificar el documento seleccionado.'
            )
            return None

        modulos = {
            'tbv_tickets': 158,
            'tbv_facturas': 1400,
            'tbv_depositos': 1664,
        }
        module_id = modulos.get(fila['Tabla'], 0)

        return self._ejecutar_accion(
            funcion=lambda ventana: ControladorAgregarQueja(
                InterfazAgregarQueja(ventana),
                ModeloAgregarQueja(self._modelo.parametros),
            ),
            id_modulo=module_id,
            id_principal=document_id,
            tabla_actualizar=fila['Tabla'],
        )

    def _dividir_documento(self):
        fila = self._obtener_valores_fila()
        if not fila:
            self._interfaz.ventanas.mostrar_mensaje(
                'Seleccione un solo ticket o factura para dividir.'
            )
            return None

        modulos = {
            'tbv_tickets': 158,
            'tbv_facturas': 1400,
        }
        module_id = modulos.get(fila['Tabla'], 0)
        if module_id == 0:
            self._interfaz.ventanas.mostrar_mensaje(
                'La división sólo está disponible para tickets y facturas.'
            )
            return None

        document_id = int(fila.get('DocumentID', 0) or 0)
        estado = self._modelo.obtener_estado_division_documento(document_id)
        if not estado:
            self._interfaz.ventanas.mostrar_mensaje(
                'No fue posible validar el documento seleccionado.'
            )
            return None

        if int(estado.get('ModuleID', 0) or 0) != module_id:
            self._interfaz.ventanas.mostrar_mensaje(
                'El documento ya no pertenece al módulo seleccionado.'
            )
            return None
        if int(estado.get('ExportID', 0) or 0) != 1:
            self._interfaz.ventanas.mostrar_mensaje(
                'El documento está en proceso de actualización; permita '
                'que dicho proceso concluya.'
            )
            return None
        if int(estado.get('Cancelado', 0) or 0) == 1:
            self._interfaz.ventanas.mostrar_mensaje(
                'El documento está cancelado y no puede dividirse.'
            )
            return None
        if int(estado.get('Borrado', 0) or 0) == 1:
            self._interfaz.ventanas.mostrar_mensaje(
                'El documento está borrado y no puede dividirse.'
            )
            return None
        if int(estado.get('CFDStatusID', 0) or 0) == 3:
            self._interfaz.ventanas.mostrar_mensaje(
                'El documento está timbrado y no puede dividirse.'
            )
            return None

        return self._ejecutar_accion(
            funcion=lambda ventana: abrir_division_documento(
                ventana,
                self._modelo.parametros,
                self._modelo.base_de_datos,
            ),
            id_modulo=module_id,
            id_principal=document_id,
            tabla_actualizar=fila['Tabla'],
        )

    def _timbrar(self):
        solicitud_intentada = False
        if self._seguimiento_timbrado:
            self._interfaz.ventanas.mostrar_mensaje(
                'Ya se está consultando una solicitud de timbrado. Espere a '
                'que termine el seguimiento antes de enviar otra.'
            )
            return None
        tabla = self._interfaz.obtener_tabla_activa()
        modulos = {
            'tbv_facturas': 1400,
            'tbv_facturas_globales': 50,
        }
        module_id = modulos.get(tabla)
        if module_id is None:
            self._interfaz.ventanas.mostrar_mensaje(
                'El timbrado sólo aplica a facturas y facturas globales.'
            )
            return None

        filas = self._interfaz.ventanas.procesar_filas_table_view(
            tabla,
            seleccionadas=True,
        )
        documentos = sorted(set(
            int(fila.get('DocumentID', 0) or 0) for fila in filas
            if int(fila.get('DocumentID', 0) or 0) > 0
        ))
        if not documentos:
            self._interfaz.ventanas.mostrar_mensaje(
                'Seleccione por lo menos un documento para timbrar.'
            )
            return None

        if tabla == 'tbv_facturas_globales' and len(documentos) != 1:
            self._interfaz.ventanas.mostrar_mensaje(
                'Las facturas globales deben enviarse a timbrar una por una. '
                'Seleccione una sola factura global.'
            )
            return None

        try:
            folios = self._obtener_folios_documentos(documentos)
            estados = self._modelo.obtener_estados_timbrado(documentos)
            por_documento = {
                int(estado['DocumentID']): estado for estado in estados
            }
            errores = []
            reintentos = []

            for document_id in documentos:
                folio = folios.get(document_id, str(document_id))
                estado = por_documento.get(document_id)
                if not estado:
                    errores.append('{}: no fue encontrado.'.format(folio))
                    continue
                if int(estado.get('ModuleID', 0) or 0) != module_id:
                    errores.append(
                        '{}: ya no pertenece al módulo seleccionado.'.format(
                            folio
                        )
                    )
                    continue
                if int(estado.get('Cancelado', 0) or 0) == 1:
                    errores.append('{}: está cancelado.'.format(folio))
                    continue
                if int(estado.get('Borrado', 0) or 0) == 1:
                    errores.append('{}: está borrado.'.format(folio))
                    continue

                invoice_id = int(estado.get('InvoiceID', 0) or 0)
                if invoice_id == 1:
                    errores.append(
                        '{}: ya está en espera de timbrado.'.format(folio)
                    )
                    continue
                if invoice_id == 2:
                    errores.append('{}: ya está timbrado.'.format(folio))
                    continue
                if invoice_id == 3:
                    if int(estado.get('CFDStatusID', 0) or 0) == 3:
                        errores.append(
                            '{}: el ERP indica que ya está timbrado.'.format(
                                folio
                            )
                        )
                    else:
                        reintentos.append(folio)
                    continue
                if invoice_id == 4:
                    errores.append(
                        '{}: el servidor está procesando el timbrado.'.format(
                            folio
                        )
                    )
                    continue
                if invoice_id != 0:
                    errores.append(
                        '{}: tiene un estado InvoiceID no válido ({}).'.format(
                            folio, invoice_id
                        )
                    )
                    continue

                cfd_status_id = int(estado.get('CFDStatusID', 0) or 0)
                cfd_status_name = str(
                    estado.get('CFDStatusName', '') or ''
                ).strip()
                if cfd_status_id == 3:
                    errores.append(
                        '{}: el ERP indica que ya está timbrado.'.format(
                            folio
                        )
                    )
                elif cfd_status_name not in ('No enviado', 'Error'):
                    errores.append(
                        '{}: estado CFD no permitido ({}).'.format(
                            folio, cfd_status_name or 'sin estado'
                        )
                    )

            if errores:
                self._interfaz.ventanas.mostrar_mensaje(
                    'No se enviaron documentos:\n\n{}'.format(
                        '\n'.join(errores)
                    )
                )
                return None

            detalle_reintentos = ''
            if reintentos:
                detalle_reintentos = (
                    '\n\nSe reintentará el timbrado de: {}'.format(
                        ', '.join(reintentos)
                    )
                )
            if not self._interfaz.ventanas.mostrar_mensaje_pregunta(
                'Se enviarán {} documento(s) a la cola de timbrado. '
                '¿Desea continuar?{}'.format(
                    len(documentos), detalle_reintentos
                ),
                master=self._interfaz._master,
            ):
                return None

            solicitud_intentada = True
            afectados = self._modelo.solicitar_timbrado(documentos, self._modelo.user_id)
            self._interfaz.ventanas.mostrar_mensaje(
                tipo='info',
                mensaje=(
                    '{} documento(s) quedaron en espera de timbrado.'.format(
                        afectados
                    )
                ),
            )
            self._interfaz.mostrar_estado(
                '{} solicitud(es) registradas; esperando al servidor...'.format(
                    afectados
                )
            )
            self._iniciar_seguimiento_timbrado(documentos, tabla, folios)
            return afectados
        except Exception as error:
            if (
                    not solicitud_intentada
                    or not self._resolver_resultado_ambiguo(documentos, error)
            ):
                self._interfaz.ventanas.mostrar_mensaje(
                    'No fue posible solicitar el timbrado:\n{}'.format(error),
                    self._interfaz._master,
                )
            return None
        finally:
            try:
                self._actualizar_tabla(tabla)
                self._interfaz.ventanas.refrescar_tamano_forma()
            except Exception as error:
                self._interfaz.mostrar_estado(
                    'Solicitud procesada; no fue posible actualizar: {}'.format(
                        error
                    )
                )

    def _resolver_resultado_ambiguo(self, documentos, error):
        """Aclara si la solicitud se guardó pese a perder la respuesta."""
        try:
            estados = self._modelo.obtener_resultado_timbrado(documentos)
        except Exception:
            return False
        if len(estados) != len(documentos):
            return False
        invoice_ids = {
            int(estado.get('InvoiceID', 0) or 0) for estado in estados
        }
        if invoice_ids and 0 not in invoice_ids:
            self._interfaz.ventanas.mostrar_mensaje(
                'La comunicación se interrumpió, pero la solicitud sí quedó '
                'registrada. Se continuará consultando su resultado.\n\n{}'.format(
                    error
                ),
                self._interfaz._master,
            )
            tabla = self._interfaz.obtener_tabla_activa()
            self._iniciar_seguimiento_timbrado(documentos, tabla, {})
            return True
        return False

    def _iniciar_seguimiento_timbrado(self, documentos, tabla, folios):
        self._seguimiento_timbrado = {
            'documentos': tuple(documentos),
            'tabla': tabla,
            'folios': folios,
            'limite': datetime.now() + timedelta(seconds=90),
        }
        self._interfaz._master.after(1500, self._consultar_seguimiento_timbrado)

    def _consultar_seguimiento_timbrado(self):
        seguimiento = self._seguimiento_timbrado
        if not seguimiento or self._consulta_timbrado_en_curso:
            return

        resultado = {}

        def consultar():
            try:
                resultado['estados'] = self._modelo.obtener_resultado_timbrado(
                    seguimiento['documentos']
                )
            except Exception as error:
                resultado['error'] = error

        hilo = Thread(target=consultar, daemon=True)
        consulta = (hilo, resultado, seguimiento)
        self._consulta_timbrado_en_curso = consulta
        hilo.start()
        self._interfaz._master.after(
            100, lambda: self._recibir_seguimiento_timbrado(consulta)
        )

    def _recibir_seguimiento_timbrado(self, consulta):
        if self._consulta_timbrado_en_curso is not consulta:
            return
        hilo, resultado, seguimiento = consulta
        if hilo.is_alive():
            self._interfaz._master.after(
                100, lambda: self._recibir_seguimiento_timbrado(consulta)
            )
            return

        self._consulta_timbrado_en_curso = None
        error = resultado.get('error')
        if error is not None:
            if datetime.now() < seguimiento['limite']:
                self._interfaz.mostrar_estado(
                    'Esperando al servidor de timbrado... ({})'.format(error)
                )
                self._interfaz._master.after(
                    5000, self._consultar_seguimiento_timbrado
                )
            else:
                self._seguimiento_timbrado = None
                self._interfaz.mostrar_estado(
                    'No fue posible confirmar el resultado del timbrado'
                )
            return

        estados = resultado.get('estados') or []

        pendientes = []
        timbrados = []
        errores = []
        encontrados = set()
        for estado in estados:
            document_id = int(estado['DocumentID'])
            encontrados.add(document_id)
            folio = seguimiento['folios'].get(document_id, str(document_id))
            invoice_id = int(estado.get('InvoiceID', 0) or 0)
            cfd_status_id = int(estado.get('CFDStatusID', 0) or 0)
            if invoice_id == 2 or cfd_status_id == 3:
                timbrados.append(folio)
            elif invoice_id == 3:
                # Algunas versiones del proceso del servidor utilizan 3 de
                # forma transitoria antes de que el PAC termine. Durante el
                # seguimiento se conserva como pendiente para evitar mostrar
                # un falso error; si no cambia, se confirma al vencer el plazo.
                if datetime.now() < seguimiento['limite']:
                    pendientes.append(folio)
                else:
                    errores.append(folio)
            else:
                pendientes.append(folio)

        for document_id in seguimiento['documentos']:
            if document_id not in encontrados:
                pendientes.append(
                    seguimiento['folios'].get(document_id, str(document_id))
                )

        if pendientes and datetime.now() < seguimiento['limite']:
            self._interfaz.mostrar_estado(
                'Timbrando: {} listo(s), {} pendiente(s), {} error(es)'.format(
                    len(timbrados), len(pendientes), len(errores)
                )
            )
            self._interfaz._master.after(
                3000, self._consultar_seguimiento_timbrado
            )
            return

        self._seguimiento_timbrado = None
        try:
            self._actualizar_tabla(seguimiento['tabla'])
        except Exception:
            pass
        if pendientes:
            mensaje = (
                '{} timbrado(s), {} error(es) y {} todavía pendiente(s). '
                'El servicio podría no estar disponible; actualice antes de '
                'volver a intentar.'.format(
                    len(timbrados), len(errores), len(pendientes)
                )
            )
        else:
            mensaje = '{} timbrado(s) y {} error(es).'.format(
                len(timbrados), len(errores)
            )
        self._interfaz.mostrar_estado(mensaje)
        if errores or pendientes:
            self._interfaz.ventanas.mostrar_mensaje(
                mensaje, self._interfaz._master
            )

    def _cfdi_relacionados(self):
        fila = self._obtener_valores_fila()
        if not fila:
            self._interfaz.ventanas.mostrar_mensaje(
                'Seleccione una sola factura para consultar o relacionar CFDI.'
            )
            return None

        if fila.get('Tabla') != 'tbv_facturas':
            self._interfaz.ventanas.mostrar_mensaje(
                'CFDI relacionados sólo está disponible para facturas del '
                'módulo 1400.'
            )
            return None

        document_id = int(fila.get('DocumentID', 0) or 0)
        module_id = self._modelo.obtener_modulo_documento(document_id)
        if module_id != 1400:
            self._interfaz.ventanas.mostrar_mensaje(
                'El documento seleccionado ya no pertenece al módulo 1400.'
            )
            return None

        return self._ejecutar_accion(
            funcion=lambda ventana: ControladorRelacionarFactura(
                InterfazRelacionarFactura(ventana),
                ModeloRelacionarFactura(self._modelo.parametros),
            ),
            id_modulo=1400,
            id_principal=document_id,
            tabla_actualizar='tbv_facturas',
        )

    def _intercambiar_rfc(self):
        fila = self._obtener_valores_fila()
        if not fila:
            self._interfaz.ventanas.mostrar_mensaje(
                'Seleccione una sola factura para intercambiar el RFC.'
            )
            return None

        if fila.get('Tabla') != 'tbv_facturas':
            self._interfaz.ventanas.mostrar_mensaje(
                'Intercambiar RFC sólo está disponible para facturas del '
                'módulo 1400.'
            )
            return None

        document_id = int(fila.get('DocumentID', 0) or 0)
        module_id = self._modelo.obtener_modulo_documento(document_id)
        if module_id != 1400:
            self._interfaz.ventanas.mostrar_mensaje(
                'El documento seleccionado ya no pertenece al módulo 1400.'
            )
            return None

        return self._ejecutar_accion(
            funcion=lambda ventana: ControladorIntercambioRFC(
                InterfazIntercambioRfc(ventana),
                ModeloIntercambioRFC(self._modelo.parametros),
            ),
            id_modulo=1400,
            id_principal=document_id,
            tabla_actualizar='tbv_facturas',
        )

    def _enviar_correos(self):
        fila = self._obtener_valores_fila()
        if not fila:
            self._interfaz.ventanas.mostrar_mensaje(
                'Seleccione una sola factura para enviar por correo.'
            )
            return None

        if fila.get('Tabla') != 'tbv_facturas':
            self._interfaz.ventanas.mostrar_mensaje(
                'Enviar correos sólo está disponible para facturas del '
                'módulo 1400.'
            )
            return None

        document_id = int(fila.get('DocumentID', 0) or 0)
        module_id = self._modelo.obtener_modulo_documento(document_id)
        if module_id != 1400:
            self._interfaz.ventanas.mostrar_mensaje(
                'El documento seleccionado ya no pertenece al módulo 1400.'
            )
            return None

        try:
            from capturar_documento.herramientas.enviar_correos.controlador_enviar_correo import (
                ControladorEnviarCorreo,
            )
        except Exception as error:
            self._interfaz.ventanas.mostrar_mensaje(
                'No fue posible cargar la herramienta Enviar correos:\n{}'
                .format(error)
            )
            return None

        self._modelo.parametros.id_seleccionados = [document_id]
        return self._ejecutar_accion(
            funcion=lambda ventana: ControladorEnviarCorreo(
                ventana,
                self._modelo.parametros,
            ),
            id_modulo=1400,
            id_principal=document_id,
            tabla_actualizar='tbv_facturas',
        )

    def _convertir_documento(self):
        fila = self._obtener_valores_fila()
        if not fila:
            self._interfaz.ventanas.mostrar_mensaje(
                'Seleccione una sola factura para convertir.'
            )
            return None

        if fila.get('Tabla') != 'tbv_facturas':
            self._interfaz.ventanas.mostrar_mensaje(
                'Convertir documento sólo está disponible para facturas del '
                'módulo 1400.'
            )
            return None

        document_id = int(fila.get('DocumentID', 0) or 0)
        module_id = self._modelo.obtener_modulo_documento(document_id)
        if module_id != 1400:
            self._interfaz.ventanas.mostrar_mensaje(
                'El documento seleccionado ya no pertenece al módulo 1400.'
            )
            return None

        return self._ejecutar_accion(
            funcion=lambda ventana: ControladorConvertirDocumento(
                InterfazConvertirDocumento(ventana),
                ModeloConvertirDocumento(self._modelo.parametros),
            ),
            id_modulo=1400,
            id_principal=document_id,
            tabla_actualizar='tbv_facturas',
        )

    def _listas_precios(self):
        if self._ejecutando:
            return None

        try:
            self._ejecutando = True
            self._interfaz.mostrar_estado('Generando lista de precios...')
            from capturar_documento.herramientas.listas_precios.crear_listas_precios import (
                CrearListasPrecios,
            )
            resultado = CrearListasPrecios(self._modelo.parametros)
            self._interfaz.mostrar_estado('Lista de precios generada')
            return resultado
        except Exception as error:
            self._interfaz.mostrar_estado(
                'No fue posible generar la lista de precios'
            )
            self._interfaz.ventanas.mostrar_mensaje(
                'No fue posible generar la lista de precios:\n{}'.format(error),
                self._interfaz._master,
            )
            return None
        finally:
            self._ejecutando = False

    def _abrir_archivo(self, id_modulo):
        from capturar_documento.herramientas.archivo_cayal.main import (
            abrir_archivo,
        )

        return self._ejecutar_accion(
            funcion=lambda ventana: abrir_archivo(
                ventana,
                self._modelo.parametros,
            ),
            id_modulo=id_modulo,
        )

    def _archivo_mayoreo(self):
        return self._abrir_archivo(1572)

    def _archivo_minisuper(self):
        return self._abrir_archivo(1640)

    def _archivo_complementos(self):
        from capturar_documento.herramientas.archivo_complementos.main import (
            abrir_archivo_complementos,
        )

        return self._ejecutar_accion(
            funcion=lambda ventana: abrir_archivo_complementos(
                ventana,
                self._modelo.parametros,
                self._modelo.base_de_datos,
            ),
        )

    def _imprimir(self):
        fila = self._obtener_valores_fila()
        if not fila:
            self._interfaz.ventanas.mostrar_mensaje(
                'Seleccione un ticket, factura, factura global o corte de '
                'caja para imprimir.'
            )
            return None
        if fila['Tabla'] not in (
                'tbv_tickets', 'tbv_facturas',
                'tbv_facturas_globales', 'tbv_cortes',
        ):
            self._interfaz.ventanas.mostrar_mensaje(
                'La impresión desde este panel sólo aplica a tickets, '
                'facturas, facturas globales y cortes de caja.'
            )
            return None

        es_corte = fila['Tabla'] == 'tbv_cortes'
        id_seleccionado = int(
            fila.get('ID' if es_corte else 'DocumentID', 0) or 0
        )
        if id_seleccionado <= 0:
            self._interfaz.ventanas.mostrar_mensaje(
                'No fue posible identificar el registro seleccionado.'
            )
            return None

        self._modelo.parametros.id_seleccionados = [id_seleccionado]
        modulos = {
            'tbv_tickets': 158,
            'tbv_facturas': 1400,
            'tbv_facturas_globales': 50,
            'tbv_cortes': MODULO_CORTE_CAJA,
        }
        return self._ejecutar_accion(
            funcion=lambda ventana: ImprimirModulo(
                ventana,
                self._modelo.parametros,
                predeterminar=False,
                configuracion=existe_archivo_impresoras(),
                impresion_silenciosa=True,
            ),
            id_modulo=modulos[fila['Tabla']],
            id_principal=id_seleccionado,
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

    def _globalizar(self):
        if self._ejecutando or self._globalizacion_en_curso:
            return None

        # Se activa antes de consultar o confirmar para que dos clics seguidos
        # no puedan abrir dos ejecuciones del proceso.
        self._globalizacion_en_curso = True

        try:
            documentos = self._modelo.obtener_tickets_pendientes_globalizar()
            if not documentos:
                self._interfaz.ventanas.mostrar_mensaje(
                    'No hay tickets vigentes pendientes de globalizar.'
                )
                return None

            no_saldados = self._modelo.obtener_tickets_no_saldados(documentos)
            if no_saldados:
                self._interfaz.ventanas.mostrar_mensaje(
                    self._modelo._mensaje_tickets_no_saldados(no_saldados),
                    self._interfaz._master,
                )
                return None

            if not self._interfaz.ventanas.mostrar_mensaje_pregunta(
                'Se globalizarán todos los tickets pendientes del día '
                '({}). ¿Desea continuar?'.format(len(documentos)),
                master=self._interfaz._master,
            ):
                return None

            self._ejecutando = True
            self._interfaz.mostrar_estado('Globalizando tickets...')
            facturas = self._modelo.globalizar_tickets(documentos)
            facturas = facturas if isinstance(facturas, (list, tuple)) else [facturas]
            folios = self._obtener_folios_documentos(facturas)
            self._interfaz.ventanas.mostrar_mensaje(
                tipo='info',mensaje=
                'Globalización terminada correctamente. Documento(s): {}'.format(
                    ', '.join(
                        folios.get(int(valor), str(valor))
                        for valor in facturas if valor
                    )
                ),
            )
            return facturas
        except Exception as error:
            self._interfaz.ventanas.mostrar_mensaje(
                'No fue posible globalizar los tickets:\n{}'.format(error),
                self._interfaz._master,
            )
            return None
        finally:
            self._ejecutando = False
            self._globalizacion_en_curso = False
            self._actualizar_despues_de_accion(
                ('tbv_tickets', 'tbv_facturas')
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

    def _editar_generales(self):
        fila = self._obtener_valores_fila()
        if not fila:
            self._interfaz.ventanas.mostrar_mensaje(
                'Seleccione una factura para editar sus datos generales.'
            )
            return None
        if fila['Tabla'] != 'tbv_facturas':
            self._interfaz.ventanas.mostrar_mensaje(
                'Editar generales sólo está disponible para el módulo Facturas Minisuper.'
            )
            return None

        document_id = int(fila.get('DocumentID', 0) or 0)
        estado = self._modelo.obtener_estado_edicion_factura(document_id)
        if not estado:
            self._interfaz.ventanas.mostrar_mensaje(
                'No fue posible validar el estado de la factura.'
            )
            return None

        cfd_status_name = str(
            estado.get('CFDStatusName', '') or ''
        ).strip().casefold()
        cancelado = estado.get('CanceladoIcon', 0)
        cancelado = str(cancelado or '').strip().casefold() not in (
            '', '0', 'false', 'none',
        )
        if cancelado or cfd_status_name != 'no enviado':
            self._interfaz.ventanas.mostrar_mensaje(
                'Sólo pueden editarse facturas no canceladas y con estado '
                'CFDI "No Enviado".'
            )
            return None

        return self._ejecutar_accion(
            funcion=lambda ventana: ControladorEditarDocumento(
                interfaz=InterfazEditarDocumento(ventana),
                modelo=ModeloEditarDocumento(self._modelo.parametros),
            ),
            id_modulo=1400,
            id_principal=document_id,
            tabla_actualizar='tbv_facturas',
        )
