import datetime
import platform
import subprocess
import tkinter as tk
from decimal import Decimal, ROUND_HALF_UP
import re
import base64
from io import BytesIO
from PIL import Image
import qrcode
import gzip
import json
import os
import shutil
import tempfile
import uuid

# Si eliges python-barcode: pip install python-barcode pillow
import barcode
from barcode.writer import ImageWriter

from herramientas.capturar_documento.herramientas.imprimir_modulo.ticket_158 import (
    Ticket158,
)
from cayal.util import Utilerias
from cayal.comandos_base_datos import ComandosBaseDatos
from herramientas.capturar_documento.plantillas.cfdi_ticket import CFDITicket
from herramientas.capturar_documento.herramientas.imprimir_modulo.consignacion import Consignacion
from herramientas.capturar_documento.herramientas.imprimir_modulo.definir_impresoras import (
    DefinirImpresoras,
)
from herramientas.capturar_documento.herramientas.imprimir_modulo.corte_caja import (
    ImpresionCorteCaja,
    MODULO_CORTE_CAJA,
)

try:
    import win32print  # Solo en Windows
except Exception:
    win32print = None

from cayal.ventanas import Ventanas


class ImprimirModulo:
    """
    Selector de impresoras multiplataforma (Windows / macOS / Linux CUPS).
    Si predeterminar=True, al confirmar se define como impresora predeterminada del SO.
    """

    def __init__(
            self, master, parametros, predeterminar: bool = False,
            configuracion=None, impresion_silenciosa=True,
    ):

        self._declarar_clases_auxiliares(master, parametros)
        self._declarar_variables_instancia(
            predeterminar, configuracion, impresion_silenciosa
        )

        self._buscar_historial()

        self._crear_frames()
        self._cargar_componentes_forma()
        self._cargar_eventos()
        self._rellenar_componentes()
        self._ajustar_componentes()
        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Impresoras')
        self._ventanas.enfocar_componente('btn_guardar')

    # ---------------- Variables ----------------
    def _declarar_clases_auxiliares(self, master, parametros):
        self._master = master
        self._ventanas = Ventanas(self._master)
        self._utilerias = Utilerias()
        self._parametros = parametros
        self._base_de_datos = ComandosBaseDatos()

    def _declarar_variables_instancia(
            self, predeterminar, configuracion, impresion_silenciosa,
    ):
        self._predeterminar = bool(predeterminar)
        self.selected_printer = None
        self._user_id = self._parametros.id_usuario
        self._user_name = self._base_de_datos.fetchone(
            'SELECT UserName FROM engUser WHERE UserID = ?', (self._user_id,)
        )
        self._module_id = self._parametros.id_modulo
        self._seleccionados = self._parametros.id_seleccionados
        self._seleccionados_historial = []
        self._seleccionados_remisiones = []
        self._historial = []
        self._motivos_reimpresion = []
        self._user_group_id = self._base_de_datos.fetchone(
            'SELECT UserGroupID FROM engUser WHERE UserID = ?', (self._user_id,)
        )
        self._seleccionados_cancelados = []
        self._ruta_configuracion = configuracion
        self._impresion_silenciosa = bool(impresion_silenciosa)

        self._info_impresoras = None

    # ---------------- UI ----------------
    def _crear_frames(self):
        frames = {
            # --- raíz ---
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.NSEW}),

            # --- contenedor que aloja Generales y Reimpresión ---
            'frame_contenedor': ('frame_principal', None,
                                 {'row': 0, 'column': 0, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            # =======================
            #      GENERALES
            # =======================
            'frame_generales': ('frame_contenedor', 'Generales',
                                {'row': 0, 'column': 0, 'padx': 5, 'pady': (5, 2), 'sticky': tk.NSEW}),

            'frame_chk': ('frame_generales', None,
                          {'row': 2, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.E}),

            'frame_botones': ('frame_generales', None,
                              {'row': 4, 'column': 1, 'padx': 5, 'pady': 5, 'sticky': tk.W}),
        }

        if self._historial:
            frames.update(
            {
                # =======================
                #     REIMPRESIÓN
                # =======================
                'frame_reimpresion': ('frame_contenedor', 'Reimpresión',
                                      {'row': 1, 'column': 0, 'padx': 5, 'pady': (2, 5), 'sticky': tk.NSEW}),

                'frame_cbx_motivo': ('frame_reimpresion', None,
                                     {'row': 0, 'column': 0, 'columnspan': 2, 'padx': 5, 'pady': 5, 'sticky': tk.EW}),

                'frame_tvw_historial': ('frame_reimpresion', None,
                                        {'row': 1, 'column': 0, 'columnspan': 2, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),
            }
            )

        self._ventanas.crear_frames(frames)

    def _cargar_componentes_forma(self):
        componentes = {
            'cbx_impresora1': ('frame_generales', None, 'Principal:', None),
            'cbx_impresora2': ('frame_generales', None, 'Secundaria:', None),
            'btn_guardar': ('frame_botones', None, 'Imprimir', None),
            'btn_cancelar': ('frame_botones', 'danger', 'Cancelar', None),
            'btn_configurar': ('frame_botones', 'warning', 'Configurar', None),

        }

        if self._historial:
            componentes.update(
                {
                    'cbx_motivo': ('frame_cbx_motivo', None, 'Motivo:', None),
                    'tvw_historial': ('frame_tvw_historial', self._crear_columnas(), 5, None)
                }
            )

        self._ventanas.crear_componentes(componentes)
        self._ventanas.ajustar_ancho_componente('cbx_impresora2',25)
        self._ventanas.ajustar_ancho_componente('cbx_impresora1', 25)

    def _crear_columnas(self):
        return [
            {'text': 'Folio', "stretch": False, 'width': 100, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'ImpresoPor', "stretch": False, 'width': 110, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'Fecha', "stretch": False, 'width': 85, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'Hora', "stretch": False, 'width': 85, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'Motivo', "stretch": False, 'width': 100, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'DocumentID', "stretch": False, 'width': 85, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 1},
        ]

    def _cargar_eventos(self):
        eventos = {
            'btn_cancelar': self._master.destroy,
            'btn_guardar':  self._procesar_documentos_seleccionados,
            'btn_configurar': self._configurar_impresoras,
        }
        self._ventanas.cargar_eventos(eventos)

    def _configurar_impresoras(self):
        ruta = self._ruta_archivo_configuracion()
        ventana = self._ventanas.crear_popup_ttkbootstrap()
        DefinirImpresoras(
            ventana,
            ruta_archivo=ruta,
            al_guardar=self._aplicar_impresoras_configuradas,
            impresora_primaria=(
                self._ventanas.obtener_input_componente('cbx_impresora1')
            ),
            impresora_secundaria=(
                self._ventanas.obtener_input_componente('cbx_impresora2')
            ),
        )

    def _ruta_archivo_configuracion(self):
        ruta = self._ruta_configuracion
        if ruta and os.path.isdir(ruta):
            return os.path.join(ruta, 'impresoras.gz')
        if ruta:
            return ruta
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'impresoras.gz',
        )

    def _aplicar_impresoras_configuradas(
            self, primaria, secundaria, ruta_archivo,
    ):
        self._ruta_configuracion = ruta_archivo
        self._info_impresoras = (primaria, secundaria)
        self._rellenar_cbx_impresoras()
        self._ventanas.insertar_input_componente(
            'cbx_impresora1', primaria
        )
        self._ventanas.insertar_input_componente(
            'cbx_impresora2', secundaria
        )
        self._bloquear_componentes()

    def _ajustar_componentes(self):
        self._ventanas.ajustar_ancho_componente('tbx_copias',5)

    def _rellenar_cbx_motivos_reimpresion(self):
        self._motivos_reimpresion = self._base_de_datos.fetchall(
            'SELECT ID,	Motivo FROM zvwMotivosReimpresion WHERE ID != 1'
        )
        if self._motivos_reimpresion:
            motivos = [reg['Motivo'] for reg in self._motivos_reimpresion]
            self._ventanas.rellenar_cbx('cbx_motivo', motivos)

    def _rellenar_componentes(self):

        if self._historial:
            self._rellenar_cbx_motivos_reimpresion()
            self._ventanas.rellenar_treeview('tvw_historial', self._crear_columnas(), self._historial,5)

        if self._ruta_configuracion:
            self._info_impresoras = self._cargar_impresoras(self._ruta_configuracion)
            if self._info_impresoras:
                self._rellenar_cbx_impresoras()
                self._ventanas.insertar_input_componente(
                    'cbx_impresora1', self._info_impresoras[0]
                )
                self._ventanas.insertar_input_componente('cbx_impresora2', self._info_impresoras[1])
                self._bloquear_componentes()

    def _bloquear_componentes(self):
        self._ventanas.bloquear_componente('cbx_impresora1')
        if self._user_group_id not in (5,6,15,1):
            self._ventanas.bloquear_componente('cbx_impresora2')

    def _rellenar_cbx_impresoras(self):
        impresoras = self._listar_impresoras()
        self._ventanas.rellenar_cbx('cbx_impresora1', impresoras or [], True)
        self._ventanas.rellenar_cbx('cbx_impresora2', impresoras or [], True)

    # ------------- Acciones -------------

    def _cargar_impresoras(self, ruta_archivo: str = "impresoras.gz"):
        """
        Carga los nombres de las impresoras primaria y secundaria desde impresoras.gz
        y adicionalmente guarda el archivo descomprimido como 'impresoras'
        en la misma carpeta que el .gz para que otro programa (IronPython) lo pueda leer.

        Devuelve (primaria, secundaria).
        """
        try:
            # Si ruta_archivo es una carpeta, armamos la ruta al .gz dentro de ella
            if os.path.isdir(ruta_archivo):
                gz_path = os.path.join(ruta_archivo, "impresoras.gz")
            else:
                gz_path = ruta_archivo

            # Directorio base donde están los archivos de configuración
            base_dir = os.path.dirname(gz_path) or "."

            # --- Leer y descomprimir normalmente ---
            with gzip.open(gz_path, "rt", encoding="utf-8") as f:
                contenido = f.read()

            # Decodificar JSON como antes
            datos = json.loads(contenido)
            primaria = datos.get("primaria")
            secundaria = datos.get("secundaria")

            # --- Guardar archivo descomprimido con el mismo contenido ---
            ruta_salida = os.path.join(base_dir, "impresoras")
            with open(ruta_salida, "w", encoding="utf-8") as f2:
                f2.write(contenido)

            return primaria, secundaria

        except Exception as e:
            print(f"⚠️ Error al leer archivo de impresoras: {e}")
            return None, None

    def _seleccionar_impresora(self, nombre_impresora):
        self.selected_printer = nombre_impresora

        if not self.selected_printer:
            self._ventanas.mostrar_mensaje("Selecciona una impresora.", self._master)
            return

        if self._predeterminar:
            ok = self._establecer_impresora_predeterminada(self.selected_printer)
            if ok:
                self._ventanas.mostrar_mensaje(
                    f"Impresora predeterminada establecida: {self.selected_printer}", self._master
                )
            else:
                self._ventanas.mostrar_mensaje(
                    f"No se pudo establecer como predeterminada:\n{self.selected_printer}", self._master
                )

        self._master.destroy()

    # ----------- Backend impresoras -----------

    def _listar_impresoras(self):
        so = platform.system()
        try:
            if so == 'Windows' and win32print is not None:
                # PRINTER_ENUM_LOCAL (2) | PRINTER_ENUM_CONNECTIONS (4)
                flags = 2 | 4
                return sorted({p[2] for p in win32print.EnumPrinters(flags)})
            else:
                # macOS / Linux con CUPS
                salida = subprocess.check_output(['lpstat', '-a'], stderr=subprocess.DEVNULL)
                nombres = []
                for linea in salida.decode(errors='ignore').splitlines():
                    linea = linea.strip()
                    if not linea:
                        continue
                    nombre = linea.split()[0]
                    nombres.append(nombre)
                return sorted(set(nombres))
        except Exception:
            return []

    def _impresora_predeterminada(self):
        so = platform.system()
        try:
            if so == 'Windows' and win32print is not None:
                return win32print.GetDefaultPrinter()
            else:
                salida = subprocess.check_output(['lpstat', '-d'], stderr=subprocess.DEVNULL).decode(errors='ignore')
                partes = salida.strip().split(':', 1)
                if len(partes) == 2:
                    return partes[1].strip()
                return None
        except Exception:
            impresoras = self._listar_impresoras()
            return impresoras[0] if impresoras else None

    def _configurar_impresion_doble_cara(self):
        """
        Activa o desactiva la impresión doble cara (dúplex) en la impresora predeterminada.

        Parámetros:
            activar (bool): True para habilitar doble cara, False para deshabilitarla.
        """
        import platform
        try:
            so = platform.system()
            if so != 'Windows':
                print("⚠️ La configuración de doble cara solo aplica en Windows.")
                return False

            import win32print

            # Obtener impresora predeterminada
            printer_name = self._impresora_predeterminada()
            if not printer_name:
                print("❌ No se encontró una impresora predeterminada.")
                return False

            activar = True if self._ventanas.obtener_input_componente('chk_caras') == 1 else False

            # Abrir impresora y leer configuración
            hPrinter = win32print.OpenPrinter(printer_name)
            props = win32print.GetPrinter(hPrinter, 2)
            devmode = props['pDevMode']

            # Configurar modo dúplex
            devmode.Duplex = 2 if activar else 1  # 2=borde largo, 1=una cara
            props['pDevMode'] = devmode

            # Aplicar configuración
            win32print.SetPrinter(hPrinter, 2, props, 0)
            win32print.ClosePrinter(hPrinter)

            estado = "activada" if activar else "desactivada"
            print(f"✅ Impresión doble cara {estado} en: {printer_name}")
            return True

        except Exception as e:
            print(f"❌ Error al configurar la impresión doble cara: {e}")
            return False

    def _establecer_impresora_predeterminada(self, nombre_impresora: str) -> bool:
        """Establece la impresora predeterminada del sistema (Windows/macOS/Linux)."""
        so = platform.system()
        try:
            if so == "Windows" and win32print is not None:
                win32print.SetDefaultPrinter(nombre_impresora)
                return True
            elif so in ("Darwin", "Linux"):
                # CUPS
                subprocess.run(
                    ["lpoptions", "-d", nombre_impresora],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )
                return True
            else:
                return False
        except Exception:
            return False

    # ----------- Backend documentos -----------

    def _procesar_documentos_seleccionados(self):
        """
        Para cada documento seleccionado:
          1) Obtiene placeholders y partidas con _buscar_info_documento_seleccionado.
          2) Carga la plantilla ticket_modulo_158.html del directorio del proyecto.
          3) Renderiza el HTML (incluye <DETAIL> por partida).
          4) Aplica los bloques condicionales IF_PAGADO e IF_COPIA (este último según motivo_id).
          5) Guarda el archivo en la carpeta de Documentos del usuario.
        """

        if self._module_id == MODULO_CORTE_CAJA:
            return self._procesar_cortes_caja_seleccionados()

        # obtener id del motivo (trazabilidad)
        motivo_id = self._buscar_motivo_id()
        if not motivo_id:
            self._ventanas.mostrar_mensaje('Debe seleccionar un motivo de reimpresión de la lista')
            return

        impresora_primaria = self._ventanas.obtener_input_componente(
            'cbx_impresora1'
        )
        impresora_secundaria = self._ventanas.obtener_input_componente(
            'cbx_impresora2'
        ) or impresora_primaria
        if self._impresion_silenciosa and not impresora_primaria:
            self._ventanas.mostrar_mensaje(
                'Debe seleccionar la impresora principal.', self._master
            )
            return

        # El UUID recibido desde el ERP relaciona los documentos y debe
        # conservarse. Sólo creamos uno local cuando la herramienta se abrió
        # desde el selector sin identificador externo.
        if not getattr(self._parametros, 'uuid', None):
            self._parametros.uuid = str(uuid.uuid4())
        self._archivos_generados = []

        try:
            if self._module_id == 158:
                self._imprimir_modulo_158(motivo_id)

            elif self._module_id in (21, 1400, 1319):
                self._imprimir_cfdi(motivo_id)

            elif self._module_id in (1316, 1692, 967):
                self._imprimir_consignacion(motivo_id)

            else:
                self._imprimir_modulo_50(motivo_id)

            if self._impresion_silenciosa:
                self._enviar_archivos_silenciosamente(
                    impresora_primaria,
                    impresora_secundaria,
                )
        except Exception as error:
            self._ventanas.mostrar_mensaje(
                f'No fue posible imprimir el documento:\n{error}',
                self._master,
            )
            return

        self._master.destroy()

    def _procesar_cortes_caja_seleccionados(self):
        impresora_primaria = self._ventanas.obtener_input_componente(
            'cbx_impresora1'
        )
        impresora_secundaria = (
            self._ventanas.obtener_input_componente('cbx_impresora2')
            or impresora_primaria
        )
        if self._impresion_silenciosa and not impresora_primaria:
            self._ventanas.mostrar_mensaje(
                'Debe seleccionar la impresora principal.', self._master
            )
            return

        if not getattr(self._parametros, 'uuid', None):
            self._parametros.uuid = str(uuid.uuid4())
        directorio = os.path.join(
            tempfile.gettempdir(), str(self._parametros.uuid)
        )
        self._archivos_generados = []

        try:
            generador = ImpresionCorteCaja(
                parametros=self._parametros,
                base_de_datos=self._base_de_datos,
            )
            for corte_id in self._seleccionados:
                ruta = generador.generar(corte_id, directorio=directorio)
                self._archivos_generados.append((str(ruta), 0))

            if self._impresion_silenciosa:
                self._enviar_archivos_silenciosamente(
                    impresora_primaria, impresora_secundaria
                )
        except Exception as error:
            self._ventanas.mostrar_mensaje(
                f'No fue posible imprimir el corte de caja:\n{error}',
                self._master,
            )
            return

        self._master.destroy()

    def _enviar_archivos_silenciosamente(
            self, impresora_primaria, impresora_secundaria,
    ):
        directorio = os.path.join(
            tempfile.gettempdir(), str(self._parametros.uuid)
        )
        if not os.path.isdir(directorio):
            raise FileNotFoundError(
                f'No se generó la carpeta de impresión: {directorio}'
            )

        archivos = [ruta for ruta, _ in self._archivos_generados]
        if not archivos:
            raise FileNotFoundError(
                'No se generaron archivos para enviar a la impresora.'
            )

        # Importación local para evitar un ciclo durante la carga de módulos.
        from capturar_documento.selector_modulo.servicio_impresion_silenciosa import (
            ServicioImpresionSilenciosa,
        )

        servicio = ServicioImpresionSilenciosa(
            parametros=self._parametros,
            modelo=self._base_de_datos,
        )
        servicio.imprimir_archivos_generados(
            archivos,
            impresora_primaria=impresora_primaria,
            impresora_secundaria=impresora_secundaria,
            cantidades_partidas={
                ruta: cantidad
                for ruta, cantidad in self._archivos_generados
            },
        )
        shutil.rmtree(directorio, ignore_errors=True)

    def _imprimir_consignacion(self, motivo_id, mostrar_precios=True):
        """
        Imprime formato de consignación con plantilla HTML.
        - COPIA/ORIGINAL/CANCELADO: según motivo_id (1=ORIGINAL, 2=CANCELADO, otros=COPIA).
        - Número de copias: según placeholder [Impresiones] del documento cuando motivo_id == 1.
        - Si [Saldo] == 0, fuerza impresión sencilla (1 copia).
        - Los precios se pueden ocultar con mostrar_precios=False (bloque IF_MOSTRAR_PRECIOS).
        """

        import os

        # Ruta de la plantilla de consigna
        base_dir = os.path.dirname(os.path.abspath(__file__))
        plantilla_path = getattr(self, 'consignacion', None) or os.path.join(
            base_dir,
            'consignacion.html'
        )

        seleccionados = self._seleccionados

        for idx, document_id in enumerate(seleccionados):
            # 1) Validación de restricciones (si aplica la misma lógica que CFDI)
            restriccion = self._validar_restricciones(motivo_id, document_id)
            if restriccion:
                continue  # no detenemos toda la corrida

            motivo_id = self._validar_reeimpresion_original(motivo_id, document_id)

            # 2) Datos de la consignación
            #    Debes tener una función similar a _buscar_info_factura_seleccionada,
            #    por ejemplo: _buscar_info_consignacion(document_id)
            info = self._buscar_info_consignacion(document_id)
            placeholders = info.get("placeholders", {}) or {}
            partidas = info.get("detalle", []) or []

            # 3) Determinar si es impresión doble o única
            cantidad = self._determinar_cantidad_impresiones(placeholders, motivo_id, document_id)

            for copia_idx in range(cantidad):
                # Nueva instancia por cada copia para evitar "arrastre" de datos
                cons = Consignacion()
                cons.set_plantilla(plantilla_path)

                titulo = 'DOCUMENTO'
                if self._module_id == 1316:
                    titulo = 'NOTA ENTREGADA'
                if self._module_id == 967:
                    titulo = 'DOCUMENTO'
                if self._module_id == 1692:
                    titulo = 'COMPRAS EMPLEADOS'

                if self._module_id == 50:
                    titulo = 'FACTURA GLOBAL'

                cons._set_titulo(titulo)

                # 4) Marca de agua / tipo de copia
                texto, marca_id = self._determinar_texto_marca(cantidad=cantidad, motivo_id=motivo_id,
                                                               copia_idx=copia_idx, esta_cancelado=(
                            document_id in self._seleccionados_cancelados))

                cons.set_marca_agua(motivo_id=marca_id)

                # 5) Control de precios (bloque IF_MOSTRAR_PRECIOS en la plantilla)
                cons.set_mostrar_precios(bool(mostrar_precios))

                # 6) UUID para nombre de archivo (mismo patrón que CFDI)
                uuid_archivo = f'{texto}-{self._parametros.uuid}-{copia_idx}({cantidad})'

                placeholders_extra = {
                    'uuid': uuid_archivo,
                    # Aquí puedes agregar más flags específicos para consigna si los necesitas,
                    # por ejemplo: 'MOSTRAR_DESCUENTO', etc. Si no, la clase lo infiere.
                }

                # 7) Renderizar
                cons.set_datos(**placeholders, **placeholders_extra)
                cons.set_partidas(partidas)

                html = cons.generar_html()

                # 8) Guardar archivo con nombre ÚNICO por documento/copia
                base = cons._obtener_directorio_salida(temporal=True, uuid=self._parametros.uuid)
                nombre_base = cons._nombre_archivo()  # p.ej. COPIA-uuid-285694-0(1).html
                nombre_sin_ext, _ = os.path.splitext(nombre_base)

                # Sanitizar un poco el nombre base (por si acaso)
                safe_base = re.sub(r'[^A-Za-z0-9_.()\-\ ]', '_', nombre_sin_ext)

                # Nombre final: base + document_id
                nombre = f"{safe_base}_{document_id}.html"
                ruta = os.path.join(base, nombre)

                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(html)
                self._archivos_generados.append((ruta, len(partidas)))

            # 9) Registrar impresión (una sola vez por documento)
            self._crear_registro_impresion(document_id, motivo_id)

    def _imprimir_cfdi(self, motivo_id):
        """
        Imprime CFDI(s) con plantilla HTML.
        - COPIA/ORIGINAL: según motivo_id (1 = ORIGINAL, !=1 = COPIA).
        - PAGADO: según 'mostrar_pagado' devuelto por _buscar_info_factura_seleccionada(document_id).
        - REMISIÓN: según el placeholder TipoCFD (0 = factura, 1 = remisión).
        """

        import os, re

        # Ruta de la plantilla CFDI
        base_dir = os.path.dirname(os.path.abspath(__file__))
        plantilla_path = getattr(self, 'cfdi_ticket', None) or os.path.join(base_dir, 'cfdi_ticket.html')

        # Construir el ticket CFDI
        ticket = CFDITicket()
        ticket.set_plantilla(plantilla_path)

        seleccionados = self._seleccionados  # ya es lista

        for idx, document_id in enumerate(seleccionados):
            # 1) Validación de restricciones
            restriccion = self._validar_restricciones(motivo_id, document_id)
            if restriccion:
                continue  # no detenemos toda la corrida

            motivo_id = self._validar_reeimpresion_original(motivo_id, document_id)

            # 2) Datos del CFDI
            info = self._buscar_info_factura(document_id)
            placeholders = info.get("placeholders", {}) or {}
            partidas = info.get("detalle", []) or []
            mostrar_pagado = bool(info.get("mostrar_pagado", False))

            # 3) Determinar si es remisión o factura según TipoCFD
            es_remision_doc = 0 if placeholders.get("TipoCFD", 'FACTURA') == 'FACTURA' else 1

            # 4) Determinar si es impresión doble o única
            cantidad = self._determinar_cantidad_impresiones(placeholders, motivo_id, document_id)

            # 5) Determinar si hay descuento en el documento
            hay_descuento = self._utilerias.redondear_valor_cantidad_a_decimal(
                placeholders.get("DescuentoCayal", 0)
            )

            for copia_idx in range(cantidad):
                # texto de marca de agua y configuración según caso
                texto, marca_id = self._determinar_texto_marca(cantidad=cantidad, motivo_id=motivo_id,
                                                               copia_idx=copia_idx, esta_cancelado=(
                                document_id in self._seleccionados_cancelados))

                ticket.set_marca_agua(motivo_id=marca_id)


                uuid_archivo = f'{texto}-{self._parametros.uuid}-{document_id}-{copia_idx}({cantidad})'

                placeholders_extra = {
                    'uuid': uuid_archivo,
                    'ES_REMISION': es_remision_doc,
                    'TextoRemision': 'REMISIÓN',
                    'MOSTRAR_PAGADO': mostrar_pagado,
                    'MOSTRAR_DESCUENTO': hay_descuento
                }

                # 6) Renderizar
                ticket.set_datos(**placeholders, **placeholders_extra)
                ticket.set_partidas(partidas)
                html = ticket.generar_html()  # maneja IF_COPIA dentro de CFDITicket

                # 7) Bloques condicionales de la plantilla
                if not mostrar_pagado:
                    html = re.sub(r"<!--IF_PAGADO-->.*?<!--END_IF-->\s*", "", html, flags=re.DOTALL)

                if hay_descuento == 0:
                    html = re.sub(r"<!--IF_DESCUENTO-->.*?<!--END_IF-->\s*", "", html, flags=re.DOTALL)

                if es_remision_doc == 0:
                    html = re.sub(r"<!--IF_NO_REMISION-->.*?<!--END_IF_NO_REMISION-->\s*", "", html, flags=re.DOTALL)
                else:
                    html = re.sub(r"<!--IF_REMISION-->.*?<!--END_IF-->\s*", "", html, flags=re.DOTALL)


                # 8) Guardar archivo con nombre ÚNICO por documento/copia
                base = ticket._obtener_directorio_salida(temporal=True, uuid=self._parametros.uuid)
                nombre_base = ticket._nombre_archivo()  # p.ej. COPIA-uuid-285694-0(1).html
                nombre_sin_ext, _ = os.path.splitext(nombre_base)

                # Sanitizar un poco el nombre base (por si acaso)
                safe_base = re.sub(r'[^A-Za-z0-9_.()\-\ ]', '_', nombre_sin_ext)

                # Nombre final: base + document_id
                nombre = f"{safe_base}_{document_id}.html"
                ruta = os.path.join(base, nombre)

                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(html)
                self._archivos_generados.append((ruta, len(partidas)))

            # 9) Registrar impresión (una sola vez por documento)
            self._crear_registro_impresion(document_id, motivo_id)

            # 10) Afectar hora de impresion para pedidos relacionados a doc de mayoreo
            order_document_id = placeholders.get("OrderDocumentID", 0)

            if order_document_id != 0:
                self._update_to_delivery(order_document_id)

    def _imprimir_modulo_158(self, motivo_id):
        # Plantilla en el directorio del proyecto
        base_dir = os.path.dirname(os.path.abspath(__file__))
        plantilla_path = getattr(self, 'ticket_modulo_158', None) or os.path.join(base_dir, 'ticket_modulo_158.html')

        # Construir el ticket (puede reutilizarse entre iteraciones)
        ticket = Ticket158()
        ticket.set_plantilla(plantilla_path)

        # Activa o no la marca de agua: si motivo_id != 1 => es copia
        es_copia = (motivo_id != 1)
        ticket.set_copia(es_copia=es_copia, texto="COPIA")

        for i, document_id in enumerate(getattr(self, "_seleccionados", [])):
            # valida si existe alguna restricción por la cual no se puede imprimir el documento
            restriccion = self._validar_restricciones(motivo_id, document_id)
            if restriccion:
                return

            info = self._buscar_info_ticket(document_id)
            placeholders = info.get("placeholders", {})
            partidas = info.get("detalle", [])
            mostrar_pagado = bool(info.get("mostrar_pagado", False))

            uuid_archivo = f'{self._parametros.uuid}-{i}(1)'
            ticket.set_datos(**placeholders, uuid=uuid_archivo)
            ticket.set_partidas(partidas)

            # Renderizar HTML base (ya aplica IF_COPIA internamente en generar_html)
            html = ticket.generar_html()

            # Manejo del bloque condicional de pago (IF_PAGADO)
            if not mostrar_pagado:
                html = re.sub(r"<!--IF_PAGADO-->.*?<!--END_IF-->\s*", "", html, flags=re.DOTALL)

            # Guardar
            base = ticket._obtener_directorio_salida(temporal=True, uuid=self._parametros.uuid)
            nombre = ticket._nombre_archivo()
            ruta = os.path.join(base, nombre)
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(html)
            self._archivos_generados.append((ruta, len(partidas)))

            # Registrar impresión
            self._crear_registro_impresion(document_id, motivo_id)

    def _imprimir_modulo_50(self, motivo_id):
        import os

        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            plantilla_path = getattr(self, 'factura_global', None) or os.path.join(
                base_dir,
                'factura_global.html'
            )

            seleccionados = self._seleccionados

            for idx, document_id in enumerate(seleccionados):
                restriccion = self._validar_restricciones(motivo_id, document_id)
                if restriccion:
                    continue

                info = self._buscar_info_factura_global(document_id)
                placeholders = info.get("placeholders", {}) or {}
                partidas = info.get("detalle", []) or []

                cantidad = self._determinar_cantidad_impresiones(placeholders, motivo_id, document_id)

                for copia_idx in range(cantidad):
                    cons = Consignacion()
                    cons.set_plantilla(plantilla_path)
                    cons._set_titulo('FACTURA GLOBAL NV')

                    texto, marca_id = self._determinar_texto_marca(
                        cantidad=cantidad,
                        motivo_id=motivo_id,
                        copia_idx=copia_idx,
                        esta_cancelado=(document_id in self._seleccionados_cancelados)
                    )

                    cons.set_marca_agua(motivo_id=marca_id)

                    uuid_archivo = f'{texto}-{self._parametros.uuid}-{copia_idx}({cantidad})'
                    placeholders_extra = {'uuid': uuid_archivo}

                    cons.set_datos(**placeholders, **placeholders_extra)
                    cons.set_partidas(partidas)

                    html = cons.generar_html()

                    # mismo flujo que otros módulos
                    base = cons._obtener_directorio_salida(temporal=True, uuid=self._parametros.uuid)

                    nombre_base = cons._nombre_archivo()
                    nombre_sin_ext, _ = os.path.splitext(nombre_base)
                    safe_base = re.sub(r'[^A-Za-z0-9_.()\-\ ]', '_', nombre_sin_ext)
                    nombre = f"{safe_base}_{document_id}.html"
                    ruta = os.path.join(base, nombre)

                    with open(ruta, "w", encoding="utf-8") as f:
                        f.write(html)
                    self._archivos_generados.append(
                        (ruta, len(partidas))
                    )

                self._crear_registro_impresion(document_id, motivo_id)

        except Exception as e:
            self._ventanas.mostrar_mensaje(f'Error al imprimir módulo 50:\n{e}')
            print(f'Error al imprimir módulo 50: {e}')
            raise
    # ---------- Helpers ------------
    def _update_to_delivery(self, order_document_id):
        resultado = self._base_de_datos.fetchone(
            """
            MERGE dbo.docDocumentOrderCayal AS target
            USING (
                SELECT 
                    ? AS ToDeliverBy,
                    ? AS OrderDocumentID
            ) AS source
                ON target.OrderDocumentID = source.OrderDocumentID

            WHEN MATCHED 
                AND target.ToDeliver IS NULL
            THEN
                UPDATE SET
                    target.ToDeliver = GETDATE(),
                    target.ToDeliverBy = source.ToDeliverBy

            OUTPUT 
                1 AS Actualizado;
            """,
            (self._user_id, order_document_id)
        )

        if not resultado:
            return False

        comentarios = f'Documento(s) impreso(s) por {self._user_name}'
        change_type_id = 58  # correspondiente a impresion de documento

        self._base_de_datos.insertar_registro_bitacora_pedidos(
            order_document_id,
            change_type_id,
            self._user_id,
            comments=comentarios
        )

        return True


    def _fmt_money(self, v):
        """Devuelve string con 2 decimales, nulos como '0.00'."""
        if v is None:
            v = Decimal('0')
        if not isinstance(v, Decimal):
            v = Decimal(str(v))
        return str(v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    def _fmt_qty(self, v):
        """Cantidad compacta: quita ceros a la derecha (1.0000 -> '1'; 0.2500 -> '0.25')."""
        if v is None:
            return '0'
        d = Decimal(str(v))
        d = d.normalize()  # elimina ceros innecesarios
        s = format(d, 'f')  # evita notación científica
        if '.' in s:
            s = s.rstrip('0').rstrip('.')
        return s if s else '0'

    def _safe_str(self, s):
        return '' if s is None else str(s)

    def _img_pil_to_data_url_png(self, img: Image.Image) -> str:
        buf = BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"

    def _make_qr_data_url(self, texto: str) -> str:
        qr = qrcode.QRCode(
            version=None, box_size=3, border=2,
            error_correction=qrcode.constants.ERROR_CORRECT_M
        )
        qr.add_data(texto or "")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        return self._img_pil_to_data_url_png(img)

    def _make_ean13_data_url(self, ean13_digits: str) -> str:
        """Representa literalmente el código del documento como Code 128.

        El nombre se conserva para no afectar los puntos de llamada actuales.
        Code 128 evita que los lectores conviertan los valores que comienzan
        con cero a UPC-A y conserva el último dígito entregado por SQL.
        """
        digits = ''.join(ch for ch in str(ean13_digits or '') if ch.isdigit())[:13]
        if len(digits) != 13:
            raise ValueError("El código debe contener exactamente 13 dígitos.")

        codigo_barra = barcode.get('code128', digits, writer=ImageWriter())
        buf = BytesIO()
        codigo_barra.write(buf, options={
            "write_text": False,
            "module_height": 12.0,
            "quiet_zone": 3.0,
        })
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"

    # ---------- Creadores de data para plantilla ----------+
    def _crear_detalle_partidas(self, partidas):
       """
       Construye la lista de partidas para el bloque <DETAIL>.
       Cada item incluye: Cantidad, Descripcion, PrecioUnCIVA, ImporteCIVA.
       """
       detalle = []
       for it in (partidas or []):
           qty = it.get('cantidad') if it.get('cantidad') is not None else it.get('Quantity', 0)
           qty_dec = Decimal(str(qty or 0))
           total_renglon = Decimal(str(it.get('total', 0) or 0))
           clave = it.get('ProductKey')

           if qty_dec == 0:
               precio_c_iva = total_renglon
           else:
               precio_c_iva = (total_renglon / qty_dec).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)

           detalle.append({
               'Cantidad': self._fmt_qty(qty_dec),
               'ClaveUnidad': it.get('ClaveUnidad','H87'),
               'Clave': clave,
               'Descripcion': self._safe_str(it.get('Description') or it.get('ProductName') or ''),
               'PrecioUnCIVA': self._fmt_money(precio_c_iva),
               'ImporteCIVA': self._fmt_money(total_renglon),
               'PrecioUnSIVA': self._fmt_money(it.get('UnitPrice'))
           })
       return detalle

    def _buscar_info_factura_global(self, document_id):
        # ---------- Consulta de generales ----------
        generales_documento = self._base_de_datos.fetchall("""
                    SELECT
                        -- Identificación y fechas
                        CONCAT(ISNULL(D.FolioPrefix, ''), ISNULL(D.Folio, ''))                   AS folio,
                        CAST(D.CreatedOn AS date)                                                AS FechaExpedicion,
                        CONVERT(char(5), D.CreatedOn, 108)                                       AS HoraExpedicion, -- HH:mm
                        D.FolioPrefix                                                            AS Serie,
                        D.Folio,

                        ISNULL(DD.FolioPrefix,'')+ISNULL(DD.Folio,'')                            AS FolioDestino,
                        ISNULL(SD.FolioPrefix,'')+ISNULL(SD.Folio,'')                            AS FolioOrigen,

                        -- Totales y leyenda
                        CAST(ISNULL(D.CambioCayal,    0) AS DECIMAL(18,2))                       AS CambioCayal,
                        CAST(ISNULL(D.SubTotal,       0) AS DECIMAL(18,2))                       AS SubTotal,
                        CAST(ISNULL(Tax.IVA_T,        0) AS DECIMAL(18,2))                       AS IVA,
                        CAST(ISNULL(Tax.IEPS_T,       0) AS DECIMAL(18,2))                       AS IEPS,
                        CAST(ISNULL(D.Total,          0) AS DECIMAL(18,2))                       AS Total,
                        CAST(ISNULL(D.DescuentoCayal, 0) AS DECIMAL(18,2))                       AS DescuentoCayal,
                        CAST(ISNULL(D.Balance,        0) AS DECIMAL(18,2))                       AS Saldo,
                        CASE WHEN ISNULL(D.DescuentoCayal, 0) <> 0 THEN 'Descuento:' ELSE '' END AS DescuentoCayalTitulo,
                        ISNULL(D.TotalLetter, '')                                                AS CantidadConLetra,
                        ISNULL(D.Comments, '')                                                   AS Comments,

                        -- Datos CFDI (por si la plantilla los usa)
                        CASE WHEN D.chkCustom1 = 1 THEN 'REMISION' ELSE 'FACTURA' END AS TipoCFD,
                        CFD.CFDITimbreImage,
                        CFD.MetodoPago,
                        CFD.FormaPago,
                        CFD.ReceptorUsoCFDI,

                        CASE WHEN D.chkCustom1 = 0 THEN E.CompanyTypeName ELSE '616 - Sin obligaciones fiscales' END AS RegimenReceptor,
                        CASE WHEN D.chkCustom1 = 0 THEN CFD.CFDISelloDigitalSAT ELSE '' END                           AS SelloDigitalSATCayal,
                        CASE WHEN D.chkCustom1 = 0 THEN CFD.CFDSello           ELSE '' END                           AS SelloDigitalCayal,
                        CASE WHEN D.chkCustom1 = 0 THEN CFD.CFDCadenaOriginal  ELSE '' END                           AS CadenaOriginalCayal,
                        CASE WHEN CFD.CFDTipoRelacion        IS NULL THEN '' ELSE CFD.CFDTipoRelacion       END      AS TipoRelacion,
                        CASE WHEN CFD.CFDUUIDRelacionados    IS NULL THEN '' ELSE CFD.CFDUUIDRelacionados   END      AS CFDIRelacionados,
                        CASE WHEN CFD.CFDTipoRelacion        IS NULL THEN '' ELSE 'TIPO RELACIÓN:'           END      AS TipoRelacionTitulo,
                        CASE WHEN CFD.CFDUUIDRelacionados    IS NULL THEN '' ELSE 'CFDI RELACIONADOS:'   END      AS CFDIRelacionadosTitulo,
                        CFD.CFDIFolioFiscal                                                                 AS Uuid,
                        CFD.CFDINumSerieCertificadoSAT                                                      AS NoCertificadoSAT,
                        CFD.CFDIFechaCertificacion                                                          AS FechaTimbrado,
                        OCFD.CSDnoCertificado                                                               AS NoCertificado,

                        -- Receptor (nombre/RFC)
                        E.OfficialName     AS ReceptorCayal,
                        1 PapelID,
                        1 Impresiones,
                        CASE WHEN D.chkCustom1 = 1 THEN 'XAXX010101000' ELSE EM.OfficialNumber END           AS RFCReceptorCayal,

                        -- Receptor (domicilio fiscal mostrado)
                        EM.AddressFiscalStreet AS ReceptorCalleCayal,
                        EM.AddressFiscalExtNumber ReceptorDomicilioNoExteriorCayal,
                        EM.AddressFiscalIntNumber AS ReceptorDomicilioNoInteriorCayal,
                        EM.AddressFiscalCity AS ReceptorDomicilioColoniaCayal,
                        EM.AddressFiscalZipCode AS ReceptorDomicilioCodigoPostalCayal,

                        -- Comentarios fiscales (bloque mostrado)
                        EM.AddressFiscalComments AS FiscalAddresMainInfoCommentsCayal,

                        -- Teléfonos
                        EM.BusinessEntityPhone AS ReceptorTelefonoEmpresa,
                        OCC.ChannelValue AS CelularCliente,

                        -- Usuarios
                        U.UserName  AS Capturista,
                        UT.UserName AS TimbradoPor,
                        dbo.fn_GenerarCodigoEAN13DesdeDocumento(D.DocumentID) AS CodigoEAN13,
                        OCE.OfficialName AS EmisorNombre,
                        OCE.CompanyTypeName AS RegimenEmisor,
                        OCEM.OfficialNumber RFCEmisor,
                        ISNULL(D.Custom3,0) ZoneID
                    FROM docDocument AS D
                    LEFT JOIN docDocumentTax               AS Tax  ON Tax.DocumentID        = D.DocumentID
                    LEFT JOIN docDocumentCFD               AS CFD  ON CFD.DocumentID        = D.DocumentID
                    LEFT JOIN orgBusinessEntity            AS E    ON E.BusinessEntityID    = D.BusinessEntityID
                    LEFT JOIN orgBusinessEntityMainInfo    AS EM   ON EM.BusinessEntityID   = E.BusinessEntityID

                    LEFT JOIN docDocumentExtra             AS X    ON X.DocumentID          = D.DocumentID
                    LEFT JOIN orgAddressDetail             AS ADT  ON ADT.AddressDetailID   = X.AddressDetailID
                    LEFT JOIN docDocumentExt               AS EX   ON EX.IDExtra            = D.DocumentID
                    LEFT JOIN orgBusinessEntityMainInfo    AS EM2  ON EM2.BusinessEntityID  = EX.CustomerID
                    LEFT JOIN orgBusinessEntity            AS E2   ON E2.BusinessEntityID   = EX.CustomerID

                    LEFT JOIN engUser                      AS U    ON U.UserID              = D.CreatedBy
                    LEFT JOIN engUser                      AS UT   ON UT.UserID             = CFD.UserID

                    LEFT JOIN orgBusinessEntityCFD         AS OCFD ON OCFD.BusinessEntityID = D.OwnedBusinessEntityID
                    LEFT JOIN orgBusinessEntity            AS OCE  ON OCFD.BusinessEntityID = OCE.BusinessEntityID
                    LEFT JOIN orgBusinessEntityMainInfo    AS OCEM ON OCE.BusinessEntityID  = OCEM.BusinessEntityID
                    LEFT JOIN docDocument                  AS DD   ON D.DestinationDocumentID = DD.DocumentID
                    LEFT JOIN docDocument                  AS SD   ON D.SourceDocumentID      = SD.DocumentID

                    OUTER APPLY (
                        SELECT TOP (1) oc.ChannelValue
                        FROM orgCommunicationChannel AS oc
                        WHERE oc.BusinessEntityID = D.BusinessEntityID
                          AND oc.ChannelTypeID    = 3
                        ORDER BY oc.ChannelTypeID DESC
                    ) AS OCC
                    WHERE D.DocumentID = ?
                """, (document_id,))

        # ---------- Partidas (puedes reutilizar las mismas que CFDI) ----------
        partidas_documento = self._base_de_datos.fetchall(
            'SELECT * FROM [dbo].[zvwBuscarPartidasDocumentoCayal-DocumentID](?) ORDER BY DocumentItemID',
            (document_id,)
        )
        partidas_documento_impuestos = self._utilerias.agregar_impuestos_productos(partidas_documento)
        # ---------- Normalización de generales ----------
        g = (generales_documento[0] if generales_documento else {})

        emisor = self._safe_str(g.get('EmisorNombre', ''))
        regimen_emisor = self._safe_str(g.get('RegimenEmisor', ''))
        rfc_emisor = self._safe_str(g.get('RFCEmisor', ''))

        folio = self._safe_str(g.get('folio'))
        fecha_expedicion = g.get('FechaExpedicion')
        hora_expedicion = self._safe_str(g.get('HoraExpedicion'))
        serie = self._safe_str(g.get('Serie'))
        folio_num = self._safe_str(g.get('Folio'))

        folio_destino = self._safe_str(g.get('FolioDestino'))
        folio_origen = self._safe_str(g.get('FolioOrigen'))

        # Texto RELACIONADO: se arma con FolioOrigen y FolioDestino
        relacionado = ''
        if folio_origen and folio_destino:
            relacionado = u"%s → %s" % (folio_origen, folio_destino)
        elif folio_origen:
            relacionado = folio_origen
        elif folio_destino:
            relacionado = folio_destino

        zone_id = g.get('ZoneID', 0)
        papel_id = g.get('PapelID', 0)
        impresiones_cfg = g.get('Impresiones', 1)

        pagado_cayal = g.get('CambioCayal', Decimal('0'))
        subtotal = g.get('SubTotal', Decimal('0'))
        iva_total = g.get('IVA', Decimal('0'))
        ieps_total = g.get('IEPS', Decimal('0'))
        total = g.get('Total', Decimal('0'))
        descuento = g.get('DescuentoCayal', Decimal('0'))
        saldo = g.get('Saldo', Decimal('0'))
        descuento_titulo = self._safe_str(g.get('DescuentoCayalTitulo'))
        cantidad_con_letra = self._safe_str(g.get('CantidadConLetra'))
        comentarios = self._safe_str(g.get('Comments'))

        metodo_pago = self._safe_str(g.get('MetodoPago'))
        forma_pago = self._safe_str(g.get('FormaPago'))
        uso_cfdi = self._safe_str(g.get('ReceptorUsoCFDI'))
        regimen_receptor = self._safe_str(g.get('RegimenReceptor'))

        sello_sat = self._safe_str(g.get('SelloDigitalSATCayal'))
        sello_cfd = self._safe_str(g.get('SelloDigitalCayal'))
        cadena_original = self._safe_str(g.get('CadenaOriginalCayal'))
        tipo_relacion = self._safe_str(g.get('TipoRelacion'))
        uuids_relacionados = self._safe_str(g.get('CFDIRelacionados'))
        uuid = self._safe_str(g.get('Uuid'))
        no_cert_sat = self._safe_str(g.get('NoCertificadoSAT'))
        fecha_timbrado = self._safe_str(g.get('FechaTimbrado'))
        no_cert_emisor = self._safe_str(g.get('NoCertificado'))
        tipo_cfd = g.get('TipoCFD', 'FACTURA')
        qr_base_64 = self._safe_str(g.get('CFDITimbreImage', ''))
        codigo_ean_13 = self._safe_str(g.get('CodigoEAN13', ''))

        # Código EAN13 (si tu plantilla lo usa)
        codigo_ean_13_clean = ''.join(ch for ch in codigo_ean_13 if ch.isdigit())[:13]
        codigo_ean_img = ''
        if len(codigo_ean_13_clean) == 13:
            try:
                codigo_ean_img = self._make_ean13_data_url(codigo_ean_13_clean)
            except Exception:
                codigo_ean_img = ''

        # Receptor
        receptor_nombre = self._safe_str(g.get('ReceptorCayal'))
        rfc_receptor = self._safe_str(g.get('RFCReceptorCayal'))

        rec_calle = self._safe_str(g.get('ReceptorCalleCayal'))
        rec_no_ext = self._safe_str(g.get('ReceptorDomicilioNoExteriorCayal'))
        rec_no_int = self._safe_str(g.get('ReceptorDomicilioNoInteriorCayal'))
        rec_colonia = self._safe_str(g.get('ReceptorDomicilioColoniaCayal'))
        rec_cp = self._safe_str(g.get('ReceptorDomicilioCodigoPostalCayal'))

        fiscal_comments = self._safe_str(g.get('FiscalAddresMainInfoCommentsCayal'))
        tel_empresa = self._safe_str(g.get('ReceptorTelefonoEmpresa'))
        tel_celular = self._safe_str(g.get('CelularCliente'))

        capturista = self._safe_str(g.get('Capturista'))
        timbrado_por = self._safe_str(g.get('TimbradoPor'))

        # Fecha string para placeholder
        fecha_str = '' if not fecha_expedicion else str(fecha_expedicion)

        # ---------- Detalle ----------
        detalle = self._crear_detalle_partidas(partidas_documento_impuestos)
        total_pzas = sum([reg['Quantity'] for reg in partidas_documento])

        # ---------- Bloque de pago condicional (si en algún momento lo usas) ----------
        pagado = Decimal(str(pagado_cayal or 0))
        cambio_cayal = (Decimal(str(pagado_cayal or 0)) - Decimal(str(total)))
        hay_pago = (pagado > 0 or Decimal(str(cambio_cayal or 0)) > 0)

        # ---------- Placeholders para la plantilla de consignación ----------
        placeholders = {
            # Emisor
            'EmisorNombre': emisor,
            'EmisorRFC': rfc_emisor,
            'EmisorRegimen': regimen_emisor,
            'EmisorDomicilio': 'Av. Gustavo Diaz Ordaz N 207 Col. La Ermita, C.P. 24020',

            # Documento
            'folio': folio,
            'Serie': serie,
            'Folio': folio_num,
            'FechaExpedicion': fecha_str,
            'HoraExpedicion': hora_expedicion,
            'FechaImpresion': datetime.datetime.now().strftime('%Y-%m-%d'),
            'HoraImpresion': datetime.datetime.now().strftime('%H:%M'),
            'LugarExpedicion': 'San Francisco de Campeche, Campeche',

            # Relacionado / Folios
            'FolioOrigen': folio_origen,
            'FolioDestino': folio_destino,
            'Relacionado': relacionado,

            # Totales / Impuestos / Saldo
            'SubTotal': self._fmt_money(subtotal),
            'IEPS': self._fmt_money(ieps_total),
            'IVA': self._fmt_money(iva_total),
            'Total': self._fmt_money(total),
            'DescuentoCayalTitulo': descuento_titulo,
            'DescuentoCayal': self._fmt_money(descuento),
            'Saldo': self._fmt_money(saldo),
            'TotalPzas': str(total_pzas),
            'CantidadConLetra': cantidad_con_letra,
            'Comentarios': comentarios,

            # Configuración de ruta / papel / copias
            'ZoneID': zone_id,
            'PapelID': papel_id,
            'Impresiones': impresiones_cfg,

            # Pago (si algún día se usa en la plantilla)
            'cliente_pago_ticket': 'Pagado' if hay_pago else '',
            'pagado_ticket': self._fmt_money(pagado) if hay_pago else '',
            'cliente_cambio_ticket': 'Cambio' if hay_pago else '',
            'cambio_venta': self._fmt_money(cambio_cayal) if hay_pago else '',

            # CFDI opcionales (por si la plantilla los usa)
            'MetodoPago': metodo_pago,
            'FormaPago': forma_pago,
            'ReceptorUsoCFDI': uso_cfdi,
            'ReceptorRegimen': regimen_receptor,
            'SelloDigitalSATCayal': sello_sat,
            'SelloDigitalCayal': sello_cfd,
            'CadenaOriginalCayal': cadena_original,
            'TipoRelacion': tipo_relacion,
            'CFDIRelacionados': uuids_relacionados,
            'Uuid': uuid,
            'NoCertificadoSAT': no_cert_sat,
            'FechaTimbrado': fecha_timbrado,
            'NoCertificado': no_cert_emisor,
            'TipoCFD': tipo_cfd,

            # Código de barras
            'CodigoEAN13': codigo_ean_img,

            # Receptor
            'ReceptorCayal': receptor_nombre,
            'RFCReceptorCayal': rfc_receptor,
            'ReceptorCalleCayal': rec_calle,
            'ReceptorDomicilioNoExteriorCayal': rec_no_ext,
            'ReceptorDomicilioNoInteriorCayal': rec_no_int,
            'ReceptorDomicilioColoniaCayal': rec_colonia,
            'ReceptorDomicilioCodigoPostalCayal': rec_cp,

            'FiscalAddresMainInfoCommentsCayal': fiscal_comments,
            'ReceptorTelefonoEmpresa': tel_empresa,
            'CelularCliente': tel_celular,

            # Usuarios
            'Capturista': capturista,
            'TimbradoPor': timbrado_por,
            'ImpresoPor': self._user_name
        }

        return {
            'placeholders': placeholders,
            'detalle': detalle,
            # Si más adelante decides usar pagado/cancelado como condicional, lo tienes listo:
            'mostrar_pagado': hay_pago
        }

    def _buscar_info_consignacion(self, document_id):
        # ---------- Consulta de generales ----------
        generales_documento = self._base_de_datos.fetchall("""
                    SELECT
                        -- Identificación y fechas
                        CONCAT(ISNULL(D.FolioPrefix, ''), ISNULL(D.Folio, ''))                   AS folio,
                        CAST(D.CreatedOn AS date)                                                AS FechaExpedicion,
                        CONVERT(char(5), D.CreatedOn, 108)                                       AS HoraExpedicion, -- HH:mm
                        D.FolioPrefix                                                            AS Serie,
                        D.Folio,

                        ISNULL(DD.FolioPrefix,'')+ISNULL(DD.Folio,'')                            AS FolioDestino,
                        ISNULL(SD.FolioPrefix,'')+ISNULL(SD.Folio,'')                            AS FolioOrigen,

                        -- Totales y leyenda
                        CAST(ISNULL(D.CambioCayal,    0) AS DECIMAL(18,2))                       AS CambioCayal,
                        CAST(ISNULL(D.SubTotal,       0) AS DECIMAL(18,2))                       AS SubTotal,
                        CAST(ISNULL(Tax.IVA_T,        0) AS DECIMAL(18,2))                       AS IVA,
                        CAST(ISNULL(Tax.IEPS_T,       0) AS DECIMAL(18,2))                       AS IEPS,
                        CAST(ISNULL(D.Total,          0) AS DECIMAL(18,2))                       AS Total,
                        CAST(ISNULL(D.DescuentoCayal, 0) AS DECIMAL(18,2))                       AS DescuentoCayal,
                        CAST(ISNULL(D.Balance,        0) AS DECIMAL(18,2))                       AS Saldo,
                        CASE WHEN ISNULL(D.DescuentoCayal, 0) <> 0 THEN 'Descuento:' ELSE '' END AS DescuentoCayalTitulo,
                        ISNULL(D.TotalLetter, '')                                                AS CantidadConLetra,
                        ISNULL(D.Comments, '')                                                   AS Comments,

                        -- Datos CFDI (por si la plantilla los usa)
                        CASE WHEN D.chkCustom1 = 1 THEN 'REMISION' ELSE 'FACTURA' END AS TipoCFD,
                        CFD.CFDITimbreImage,
                        CFD.MetodoPago,
                        CFD.FormaPago,
                        CFD.ReceptorUsoCFDI,

                        CASE WHEN D.chkCustom1 = 0 THEN E.CompanyTypeName ELSE '616 - Sin obligaciones fiscales' END AS RegimenReceptor,
                        CASE WHEN D.chkCustom1 = 0 THEN CFD.CFDISelloDigitalSAT ELSE '' END                           AS SelloDigitalSATCayal,
                        CASE WHEN D.chkCustom1 = 0 THEN CFD.CFDSello           ELSE '' END                           AS SelloDigitalCayal,
                        CASE WHEN D.chkCustom1 = 0 THEN CFD.CFDCadenaOriginal  ELSE '' END                           AS CadenaOriginalCayal,
                        CASE WHEN CFD.CFDTipoRelacion        IS NULL THEN '' ELSE CFD.CFDTipoRelacion       END      AS TipoRelacion,
                        CASE WHEN CFD.CFDUUIDRelacionados    IS NULL THEN '' ELSE CFD.CFDUUIDRelacionados   END      AS CFDIRelacionados,
                        CASE WHEN CFD.CFDTipoRelacion        IS NULL THEN '' ELSE 'TIPO RELACIÓN:'           END      AS TipoRelacionTitulo,
                        CASE WHEN CFD.CFDUUIDRelacionados    IS NULL THEN '' ELSE 'CFDI RELACIONADOS:'   END      AS CFDIRelacionadosTitulo,
                        CFD.CFDIFolioFiscal                                                                 AS Uuid,
                        CFD.CFDINumSerieCertificadoSAT                                                      AS NoCertificadoSAT,
                        CFD.CFDIFechaCertificacion                                                          AS FechaTimbrado,
                        OCFD.CSDnoCertificado                                                               AS NoCertificado,

                        -- Receptor (nombre/RFC)
                        CASE WHEN D.BusinessEntityID = 8179 THEN E2.OfficialName ELSE E.OfficialName END     AS ReceptorCayal,
                        CASE 
                            WHEN D.BusinessEntityID = 8179 
                                 THEN CASE WHEN ISNULL(E2.Custom2, 0) = 1 THEN 1 ELSE 0 END
                            ELSE CASE WHEN ISNULL(E.Custom2, 0) = 1 THEN 1 ELSE 0 END
                        END AS PapelID,
                        CASE 
                            WHEN D.BusinessEntityID = 8179 
                                 THEN CASE WHEN ISNULL(E2.Impresiones, 1) = 1 THEN 1 ELSE 2 END
                            ELSE CASE WHEN ISNULL(E.Impresiones, 1) = 1 THEN 1 ELSE 2 END
                        END AS Impresiones,
                        CASE WHEN D.chkCustom1 = 1 THEN 'XAXX010101000' ELSE EM.OfficialNumber END           AS RFCReceptorCayal,

                        -- Receptor (domicilio fiscal mostrado)
                        CASE
                            WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.AddressFiscalStreet
                            WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.AddressFiscalStreet
                            ELSE ADT.Street
                        END AS ReceptorCalleCayal,

                        CASE
                            WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.AddressFiscalExtNumber
                            WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.AddressFiscalExtNumber
                            ELSE ADT.ExtNumber
                        END AS ReceptorDomicilioNoExteriorCayal,

                        CASE
                            WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.AddressFiscalIntNumber
                            WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.AddressFiscalIntNumber
                            ELSE ADT.IntNumber
                        END AS ReceptorDomicilioNoInteriorCayal,

                        CASE
                            WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.AddressFiscalCity
                            WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.AddressFiscalCity
                            ELSE ADT.City
                        END AS ReceptorDomicilioColoniaCayal,

                        CASE
                            WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.AddressFiscalZipCode
                            WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.AddressFiscalZipCode
                            ELSE ADT.ZipCode
                        END AS ReceptorDomicilioCodigoPostalCayal,

                        -- Comentarios fiscales (bloque mostrado)
                        CASE
                            WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.AddressFiscalComments
                            WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.AddressFiscalComments
                            ELSE ADT.Comments
                        END AS FiscalAddresMainInfoCommentsCayal,

                        -- Teléfonos
                        CASE
                            WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.BusinessEntityPhone
                            WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.BusinessEntityPhone
                            ELSE ADT.Telefono
                        END AS ReceptorTelefonoEmpresa,

                        CASE
                            WHEN X.AddressDetailID <> 0 AND ISNULL(ADT.Telefono, '') <> '' THEN ADT.Telefono
                            ELSE OCC.ChannelValue
                        END AS CelularCliente,

                        -- Usuarios
                        U.UserName  AS Capturista,
                        UT.UserName AS TimbradoPor,
                        dbo.fn_GenerarCodigoEAN13DesdeDocumento(D.DocumentID) AS CodigoEAN13,
                        OCE.OfficialName AS EmisorNombre,
                        OCE.CompanyTypeName AS RegimenEmisor,
                        OCEM.OfficialNumber RFCEmisor,
                        ISNULL(D.Custom3,0) ZoneID
                    FROM docDocument AS D
                    LEFT JOIN docDocumentTax               AS Tax  ON Tax.DocumentID        = D.DocumentID
                    LEFT JOIN docDocumentCFD               AS CFD  ON CFD.DocumentID        = D.DocumentID
                    LEFT JOIN orgBusinessEntity            AS E    ON E.BusinessEntityID    = D.BusinessEntityID
                    LEFT JOIN orgBusinessEntityMainInfo    AS EM   ON EM.BusinessEntityID   = E.BusinessEntityID

                    LEFT JOIN docDocumentExtra             AS X    ON X.DocumentID          = D.DocumentID
                    LEFT JOIN orgAddressDetail             AS ADT  ON ADT.AddressDetailID   = X.AddressDetailID
                    LEFT JOIN docDocumentExt               AS EX   ON EX.IDExtra            = D.DocumentID
                    LEFT JOIN orgBusinessEntityMainInfo    AS EM2  ON EM2.BusinessEntityID  = EX.CustomerID
                    LEFT JOIN orgBusinessEntity            AS E2   ON E2.BusinessEntityID   = EX.CustomerID

                    LEFT JOIN engUser                      AS U    ON U.UserID              = D.CreatedBy
                    LEFT JOIN engUser                      AS UT   ON UT.UserID             = CFD.UserID

                    LEFT JOIN orgBusinessEntityCFD         AS OCFD ON OCFD.BusinessEntityID = D.OwnedBusinessEntityID
                    LEFT JOIN orgBusinessEntity            AS OCE  ON OCFD.BusinessEntityID = OCE.BusinessEntityID
                    LEFT JOIN orgBusinessEntityMainInfo    AS OCEM ON OCE.BusinessEntityID  = OCEM.BusinessEntityID
                    LEFT JOIN docDocument                  AS DD   ON D.DestinationDocumentID = DD.DocumentID
                    LEFT JOIN docDocument                  AS SD   ON D.SourceDocumentID      = SD.DocumentID

                    OUTER APPLY (
                        SELECT TOP (1) oc.ChannelValue
                        FROM orgCommunicationChannel AS oc
                        WHERE oc.BusinessEntityID = D.BusinessEntityID
                          AND oc.ChannelTypeID    = 3
                        ORDER BY oc.ChannelTypeID DESC
                    ) AS OCC
                    WHERE D.DocumentID = ?
                """, (document_id,))

        # ---------- Partidas (puedes reutilizar las mismas que CFDI) ----------
        partidas_documento = self._base_de_datos.fetchall(
            'SELECT * FROM [dbo].[zvwBuscarPartidasDocumentoCayal-DocumentID](?) ORDER BY DocumentItemID',
            (document_id,)
        )
        partidas_documento_impuestos = self._utilerias.agregar_impuestos_productos(partidas_documento)
        # ---------- Normalización de generales ----------
        g = (generales_documento[0] if generales_documento else {})

        emisor = self._safe_str(g.get('EmisorNombre', ''))
        regimen_emisor = self._safe_str(g.get('RegimenEmisor', ''))
        rfc_emisor = self._safe_str(g.get('RFCEmisor', ''))

        folio = self._safe_str(g.get('folio'))
        fecha_expedicion = g.get('FechaExpedicion')
        hora_expedicion = self._safe_str(g.get('HoraExpedicion'))
        serie = self._safe_str(g.get('Serie'))
        folio_num = self._safe_str(g.get('Folio'))

        folio_destino = self._safe_str(g.get('FolioDestino'))
        folio_origen = self._safe_str(g.get('FolioOrigen'))

        # Texto RELACIONADO: se arma con FolioOrigen y FolioDestino
        relacionado = ''
        if folio_origen and folio_destino:
            relacionado = u"%s → %s" % (folio_origen, folio_destino)
        elif folio_origen:
            relacionado = folio_origen
        elif folio_destino:
            relacionado = folio_destino

        zone_id = g.get('ZoneID', 0)
        papel_id = g.get('PapelID', 0)
        impresiones_cfg = g.get('Impresiones', 1)

        pagado_cayal = g.get('CambioCayal', Decimal('0'))
        subtotal = g.get('SubTotal', Decimal('0'))
        iva_total = g.get('IVA', Decimal('0'))
        ieps_total = g.get('IEPS', Decimal('0'))
        total = g.get('Total', Decimal('0'))
        descuento = g.get('DescuentoCayal', Decimal('0'))
        saldo = g.get('Saldo', Decimal('0'))
        descuento_titulo = self._safe_str(g.get('DescuentoCayalTitulo'))
        cantidad_con_letra = self._safe_str(g.get('CantidadConLetra'))
        comentarios = self._safe_str(g.get('Comments'))

        metodo_pago = self._safe_str(g.get('MetodoPago'))
        forma_pago = self._safe_str(g.get('FormaPago'))
        uso_cfdi = self._safe_str(g.get('ReceptorUsoCFDI'))
        regimen_receptor = self._safe_str(g.get('RegimenReceptor'))

        sello_sat = self._safe_str(g.get('SelloDigitalSATCayal'))
        sello_cfd = self._safe_str(g.get('SelloDigitalCayal'))
        cadena_original = self._safe_str(g.get('CadenaOriginalCayal'))
        tipo_relacion = self._safe_str(g.get('TipoRelacion'))
        uuids_relacionados = self._safe_str(g.get('CFDIRelacionados'))
        uuid = self._safe_str(g.get('Uuid'))
        no_cert_sat = self._safe_str(g.get('NoCertificadoSAT'))
        fecha_timbrado = self._safe_str(g.get('FechaTimbrado'))
        no_cert_emisor = self._safe_str(g.get('NoCertificado'))
        tipo_cfd = g.get('TipoCFD', 'FACTURA')
        qr_base_64 = self._safe_str(g.get('CFDITimbreImage', ''))
        codigo_ean_13 = self._safe_str(g.get('CodigoEAN13', ''))

        # Código EAN13 (si tu plantilla lo usa)
        codigo_ean_13_clean = ''.join(ch for ch in codigo_ean_13 if ch.isdigit())[:13]
        codigo_ean_img = ''
        if len(codigo_ean_13_clean) == 13:
            try:
                codigo_ean_img = self._make_ean13_data_url(codigo_ean_13_clean)
            except Exception:
                codigo_ean_img = ''

        # Receptor
        receptor_nombre = self._safe_str(g.get('ReceptorCayal'))
        rfc_receptor = self._safe_str(g.get('RFCReceptorCayal'))

        rec_calle = self._safe_str(g.get('ReceptorCalleCayal'))
        rec_no_ext = self._safe_str(g.get('ReceptorDomicilioNoExteriorCayal'))
        rec_no_int = self._safe_str(g.get('ReceptorDomicilioNoInteriorCayal'))
        rec_colonia = self._safe_str(g.get('ReceptorDomicilioColoniaCayal'))
        rec_cp = self._safe_str(g.get('ReceptorDomicilioCodigoPostalCayal'))

        fiscal_comments = self._safe_str(g.get('FiscalAddresMainInfoCommentsCayal'))
        tel_empresa = self._safe_str(g.get('ReceptorTelefonoEmpresa'))
        tel_celular = self._safe_str(g.get('CelularCliente'))

        capturista = self._safe_str(g.get('Capturista'))
        timbrado_por = self._safe_str(g.get('TimbradoPor'))

        # Fecha string para placeholder
        fecha_str = '' if not fecha_expedicion else str(fecha_expedicion)

        # ---------- Detalle ----------
        detalle = self._crear_detalle_partidas(partidas_documento_impuestos)
        total_pzas = sum([reg['Quantity'] for reg in partidas_documento])

        # ---------- Bloque de pago condicional (si en algún momento lo usas) ----------
        pagado = Decimal(str(pagado_cayal or 0))
        cambio_cayal = (Decimal(str(pagado_cayal or 0)) - Decimal(str(total)))
        hay_pago = (pagado > 0 or Decimal(str(cambio_cayal or 0)) > 0)

        # ---------- Placeholders para la plantilla de consignación ----------
        placeholders = {
            # Emisor
            'EmisorNombre': emisor,
            'EmisorRFC': rfc_emisor,
            'EmisorRegimen': regimen_emisor,
            'EmisorDomicilio': 'Av. Gustavo Diaz Ordaz N 207 Col. La Ermita, C.P. 24020',

            # Documento
            'folio': folio,
            'Serie': serie,
            'Folio': folio_num,
            'FechaExpedicion': fecha_str,
            'HoraExpedicion': hora_expedicion,
            'FechaImpresion': datetime.datetime.now().strftime('%Y-%m-%d'),
            'HoraImpresion': datetime.datetime.now().strftime('%H:%M'),
            'LugarExpedicion': 'San Francisco de Campeche, Campeche',

            # Relacionado / Folios
            'FolioOrigen': folio_origen,
            'FolioDestino': folio_destino,
            'Relacionado': relacionado,

            # Totales / Impuestos / Saldo
            'SubTotal': self._fmt_money(subtotal),
            'IEPS': self._fmt_money(ieps_total),
            'IVA': self._fmt_money(iva_total),
            'Total': self._fmt_money(total),
            'DescuentoCayalTitulo': descuento_titulo,
            'DescuentoCayal': self._fmt_money(descuento),
            'Saldo': self._fmt_money(saldo),
            'TotalPzas': str(total_pzas),
            'CantidadConLetra': cantidad_con_letra,
            'Comentarios': comentarios,

            # Configuración de ruta / papel / copias
            'ZoneID': zone_id,
            'PapelID': papel_id,
            'Impresiones': impresiones_cfg,

            # Pago (si algún día se usa en la plantilla)
            'cliente_pago_ticket': 'Pagado' if hay_pago else '',
            'pagado_ticket': self._fmt_money(pagado) if hay_pago else '',
            'cliente_cambio_ticket': 'Cambio' if hay_pago else '',
            'cambio_venta': self._fmt_money(cambio_cayal) if hay_pago else '',

            # CFDI opcionales (por si la plantilla los usa)
            'MetodoPago': metodo_pago,
            'FormaPago': forma_pago,
            'ReceptorUsoCFDI': uso_cfdi,
            'ReceptorRegimen': regimen_receptor,
            'SelloDigitalSATCayal': sello_sat,
            'SelloDigitalCayal': sello_cfd,
            'CadenaOriginalCayal': cadena_original,
            'TipoRelacion': tipo_relacion,
            'CFDIRelacionados': uuids_relacionados,
            'Uuid': uuid,
            'NoCertificadoSAT': no_cert_sat,
            'FechaTimbrado': fecha_timbrado,
            'NoCertificado': no_cert_emisor,
            'TipoCFD': tipo_cfd,

            # Código de barras
            'CodigoEAN13': codigo_ean_img,

            # Receptor
            'ReceptorCayal': receptor_nombre,
            'RFCReceptorCayal': rfc_receptor,
            'ReceptorCalleCayal': rec_calle,
            'ReceptorDomicilioNoExteriorCayal': rec_no_ext,
            'ReceptorDomicilioNoInteriorCayal': rec_no_int,
            'ReceptorDomicilioColoniaCayal': rec_colonia,
            'ReceptorDomicilioCodigoPostalCayal': rec_cp,

            'FiscalAddresMainInfoCommentsCayal': fiscal_comments,
            'ReceptorTelefonoEmpresa': tel_empresa,
            'CelularCliente': tel_celular,

            # Usuarios
            'Capturista': capturista,
            'TimbradoPor': timbrado_por,
            'ImpresoPor': self._user_name
        }

        return {
            'placeholders': placeholders,
            'detalle': detalle,
            # Si más adelante decides usar pagado/cancelado como condicional, lo tienes listo:
            'mostrar_pagado': hay_pago
        }

    def _buscar_info_ticket(self, document_id):
        generales_documento = self._base_de_datos.fetchall("""
            SELECT
                CONCAT(ISNULL(D.FolioPrefix, ''), ISNULL(D.Folio, ''))              AS folio,
                CAST(D.CreatedOn AS date)                                           AS FechaExpedicion,
                CONVERT(char(5), D.CreatedOn, 108)                                  AS HoraExpedicion,
                CAST(ISNULL(D.CambioCayal,      0) AS DECIMAL(18,2))                AS CambioCayal,
                CAST(ISNULL(D.SubTotal,         0) AS DECIMAL(18,2))                AS SubTotal,
                ISNULL(D.TotalLetter, '')                                           AS CantidadConLetra,
                CAST(ISNULL(Tax.IVA_T,          0) AS DECIMAL(18,2))                AS IVA,
                CAST(ISNULL(Tax.IEPS_T,         0) AS DECIMAL(18,2))                AS IEPS,
                CAST(ISNULL(D.Total,            0) AS DECIMAL(18,2))                AS Total,
                CAST(ISNULL(D.DescuentoCayal,   0) AS DECIMAL(18,2))                AS DescuentoCayal,
                CASE WHEN ISNULL(D.DescuentoCayal, 0) <> 0 THEN 'Descuento:' ELSE '' END AS DescuentoCayalTitulo
            FROM docDocument AS D
            LEFT JOIN docDocumentTax AS Tax
                ON Tax.DocumentID = D.DocumentID
            WHERE D.DocumentID = ?;
        """, (document_id,))
        partidas_documento = self._base_de_datos.fetchall(
            'SELECT * FROM [dbo].[zvwBuscarPartidasDocumentoCayal-DocumentID](?) ORDER BY DocumentItemID',
            (document_id,)
        )
        partidas_documento_impuestos = self._utilerias.agregar_impuestos_productos(partidas_documento)
        g = (generales_documento[0] if generales_documento else {})
        folio = self._safe_str(g.get('folio'))
        fecha_expedicion = g.get('FechaExpedicion')
        hora_expedicion = self._safe_str(g.get('HoraExpedicion'))
        pagado_cayal = g.get('CambioCayal', Decimal('0'))
        subtotal = g.get('SubTotal', Decimal('0'))
        iva_total = g.get('IVA', Decimal('0'))
        ieps_total = g.get('IEPS', Decimal('0'))
        total = g.get('Total', Decimal('0'))
        descuento = g.get('DescuentoCayal', Decimal('0'))
        descuento_titulo = self._safe_str(g.get('DescuentoCayalTitulo'))
        cantidad_con_letra = self._safe_str(g.get('CantidadConLetra'))
        fecha_str = '' if not fecha_expedicion else str(fecha_expedicion)
        # ---- Generación del detalle usando método reutilizable ----
        detalle = self._crear_detalle_partidas(partidas_documento_impuestos)
        total_pzas = sum([reg['Quantity'] for reg in partidas_documento])
        pagado =  Decimal(str(pagado_cayal or 0))
        cambio_cayal =  (Decimal(str(pagado_cayal or 0)) - Decimal(str(total)))

        hay_pago = (pagado > 0 or Decimal(str(cambio_cayal or 0)) > 0)
        placeholders = {
            'FechaExpedicion': fecha_str,
            'HoraExpedicion': hora_expedicion,
            'folio': folio,
            'FechaImpresion': datetime.datetime.now().strftime('%Y-%m-%d'),
            'HoraImpresion': datetime.datetime.now().strftime('%H:%M'),
            'SubTotal': self._fmt_money(subtotal),
            'IEPS': self._fmt_money(ieps_total),
            'IVA': self._fmt_money(iva_total),
            'Total': self._fmt_money(total),
            'DescuentoCayalTitulo': descuento_titulo,
            'DescuentoCayal': self._fmt_money(descuento),
            'TotalPzas': str(total_pzas),
            'CantidadConLetra': cantidad_con_letra,
            # Bloque de pago condicional
            'cliente_pago_ticket': 'Pagado' if hay_pago else '',
            'pagado_ticket': self._fmt_money(pagado) if hay_pago else '',
            'cliente_cambio_ticket': 'Cambio' if hay_pago else '',
            'cambio_venta': self._fmt_money(cambio_cayal) if hay_pago else '',
        }
        return {
            'placeholders': placeholders,
            'detalle': detalle,
            'mostrar_pagado': hay_pago
        }

    def _buscar_info_factura(self, document_id):
        # ---------- Consulta de generales ----------
        generales_documento = self._base_de_datos.fetchall("""
            SELECT
                -- Identificación y fechas
                CONCAT(ISNULL(D.FolioPrefix, ''), ISNULL(D.Folio, ''))                   AS folio,
                CAST(D.CreatedOn AS date)                                                AS FechaExpedicion,
                CONVERT(char(5), D.CreatedOn, 108)                                       AS HoraExpedicion, -- HH:mm
                D.FolioPrefix                                                            AS Serie,
                D.Folio,

                -- Totales y leyenda
                CAST(ISNULL(D.CambioCayal,    0) AS DECIMAL(18,2))                       AS CambioCayal,
                CAST(ISNULL(D.SubTotal,       0) AS DECIMAL(18,2))                       AS SubTotal,
                CAST(ISNULL(Tax.IVA_T,        0) AS DECIMAL(18,2))                       AS IVA,
                CAST(ISNULL(Tax.IEPS_T,       0) AS DECIMAL(18,2))                       AS IEPS,
                CAST(ISNULL(D.Total,          0) AS DECIMAL(18,2))                       AS Total,
                CAST(ISNULL(D.DescuentoCayal, 0) AS DECIMAL(18,2))                       AS DescuentoCayal,
                CAST(ISNULL(D.Balance,        0) AS DECIMAL(18,2))                       AS Saldo,
                CASE WHEN ISNULL(D.DescuentoCayal, 0) <> 0 THEN 'Descuento:' ELSE '' END AS DescuentoCayalTitulo,
                ISNULL(D.TotalLetter, '')                                                AS CantidadConLetra,
                ISNULL(D.Comments, '')                                                   AS Comments,

                -- Datos CFDI
                CASE WHEN D.chkCustom1 = 1 THEN 'REMISION' ELSE 'FACTURA' END AS TipoCFD,
                CFD.CFDITimbreImage,
                CFD.MetodoPago,
                CFD.FormaPago,
                CFD.ReceptorUsoCFDI,
                
                CASE WHEN D.chkCustom1 = 0 THEN E.CompanyTypeName ELSE '616 - Sin obligaciones fiscales' END AS RegimenReceptor,
                CASE WHEN D.chkCustom1 = 0 THEN CFD.CFDISelloDigitalSAT ELSE '' END                           AS SelloDigitalSATCayal,
                CASE WHEN D.chkCustom1 = 0 THEN CFD.CFDSello           ELSE '' END                           AS SelloDigitalCayal,
                CASE WHEN D.chkCustom1 = 0 THEN CFD.CFDCadenaOriginal  ELSE '' END                           AS CadenaOriginalCayal,
                CASE WHEN CFD.CFDTipoRelacion        IS NULL THEN '' ELSE CFD.CFDTipoRelacion       END      AS TipoRelacion,
                CASE WHEN CFD.CFDUUIDRelacionados    IS NULL THEN '' ELSE CFD.CFDUUIDRelacionados   END      AS CFDIRelacionados,
                CASE WHEN CFD.CFDTipoRelacion        IS NULL THEN '' ELSE 'TIPO RELACIÓN:'           END      AS TipoRelacionTitulo,
                CASE WHEN CFD.CFDUUIDRelacionados    IS NULL THEN '' ELSE 'CFDI RELACIONADOS:'   END      AS CFDIRelacionadosTitulo,
                CFD.CFDIFolioFiscal                                                                 AS Uuid,
                CFD.CFDINumSerieCertificadoSAT                                                      AS NoCertificadoSAT,
                CFD.CFDIFechaCertificacion                                                          AS FechaTimbrado,
                OCFD.CSDnoCertificado                                                               AS NoCertificado,

                -- Receptor (nombre/RFC)
                CASE WHEN D.BusinessEntityID = 8179 THEN E2.OfficialName ELSE E.OfficialName END     AS ReceptorCayal,
                CASE 
                    WHEN D.BusinessEntityID = 8179 
                         THEN CASE WHEN ISNULL(E2.Custom2, 0) = 1 THEN 1 ELSE 0 END
                    ELSE CASE WHEN ISNULL(E.Custom2, 0) = 1 THEN 1 ELSE 0 END
                END AS PapelID,
                CASE 
                    WHEN D.BusinessEntityID = 8179 
                         THEN CASE WHEN ISNULL(E2.Impresiones, 1) = 1 THEN 1 ELSE 2 END
                    ELSE CASE WHEN ISNULL(E.Impresiones, 1) = 1 THEN 1 ELSE 2 END
                END AS Impresiones,
                CASE WHEN D.chkCustom1 = 1 THEN 'XAXX010101000' ELSE EM.OfficialNumber END           AS RFCReceptorCayal,

                -- Receptor (domicilio fiscal mostrado)
                CASE
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.AddressFiscalStreet
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.AddressFiscalStreet
                    ELSE ADT.Street
                END AS ReceptorCalleCayal,

                CASE
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.AddressFiscalExtNumber
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.AddressFiscalExtNumber
                    ELSE ADT.ExtNumber
                END AS ReceptorDomicilioNoExteriorCayal,

                CASE
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.AddressFiscalIntNumber
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.AddressFiscalIntNumber
                    ELSE ADT.IntNumber
                END AS ReceptorDomicilioNoInteriorCayal,

                CASE
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.AddressFiscalCity
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.AddressFiscalCity
                    ELSE ADT.City
                END AS ReceptorDomicilioColoniaCayal,

                CASE
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.AddressFiscalZipCode
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.AddressFiscalZipCode
                    ELSE ADT.ZipCode
                END AS ReceptorDomicilioCodigoPostalCayal,

                -- Comentarios fiscales (bloque mostrado)
                CASE
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.AddressFiscalComments
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.AddressFiscalComments
                    ELSE ADT.Comments
                END AS FiscalAddresMainInfoCommentsCayal,

                -- Teléfonos
                CASE
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID = 8179 THEN EM2.BusinessEntityPhone
                    WHEN X.AddressDetailID = 0 AND D.BusinessEntityID <> 8179 THEN EM.BusinessEntityPhone
                    ELSE ADT.Telefono
                END AS ReceptorTelefonoEmpresa,

                CASE
                    WHEN X.AddressDetailID <> 0 AND ISNULL(ADT.Telefono, '') <> '' THEN ADT.Telefono
                    ELSE OCC.ChannelValue
                END AS CelularCliente,

                -- Usuarios
                U.UserName  AS Capturista,
                UT.UserName AS TimbradoPor,
                dbo.fn_GenerarCodigoEAN13DesdeDocumento(D.DocumentID) AS CodigoEAN13,
                OCE.OfficialName AS EmisorNombre,
                OCE.CompanyTypeName AS RegimenEmisor,
                OCEM.OfficialNumber RFCEmisor,
                ISNULL(D.Custom3,0) ZoneID,
                D.OrderDocumentID
            FROM docDocument AS D
            LEFT JOIN docDocumentTax               AS Tax  ON Tax.DocumentID        = D.DocumentID
            LEFT JOIN docDocumentCFD               AS CFD  ON CFD.DocumentID        = D.DocumentID
            LEFT JOIN orgBusinessEntity            AS E    ON E.BusinessEntityID    = D.BusinessEntityID
            LEFT JOIN orgBusinessEntityMainInfo    AS EM   ON EM.BusinessEntityID   = E.BusinessEntityID

            LEFT JOIN docDocumentExtra             AS X    ON X.DocumentID          = D.DocumentID
            LEFT JOIN orgAddressDetail             AS ADT  ON ADT.AddressDetailID   = X.AddressDetailID
            LEFT JOIN docDocumentExt               AS EX   ON EX.IDExtra            = D.DocumentID
            LEFT JOIN orgBusinessEntityMainInfo    AS EM2  ON EM2.BusinessEntityID  = EX.CustomerID
            LEFT JOIN orgBusinessEntity            AS E2   ON E2.BusinessEntityID   = EX.CustomerID

            LEFT JOIN engUser                      AS U    ON U.UserID              = D.CreatedBy
            LEFT JOIN engUser                      AS UT   ON UT.UserID             = CFD.UserID

            LEFT JOIN orgBusinessEntityCFD         AS OCFD ON OCFD.BusinessEntityID = D.OwnedBusinessEntityID
            LEFT JOIN orgBusinessEntity            AS OCE ON OCFD.BusinessEntityID = OCE.BusinessEntityID
            LEFT JOIN orgBusinessEntityMainInfo    AS OCEM ON OCE.BusinessEntityID = OCEM.BusinessEntityID
            
            OUTER APPLY (
                SELECT TOP (1) oc.ChannelValue
                FROM orgCommunicationChannel AS oc
                WHERE oc.BusinessEntityID = D.BusinessEntityID
                  AND oc.ChannelTypeID    = 3
                ORDER BY oc.ChannelTypeID DESC
            ) AS OCC
            WHERE D.DocumentID = ?;
        """, (document_id,))

        # ---------- Partidas ----------
        partidas_documento = self._base_de_datos.fetchall(
            'SELECT * FROM [dbo].[zvwBuscarPartidasDocumentoCayal-DocumentID](?) ORDER BY DocumentItemID',
            (document_id,)
        )
        partidas_documento_impuestos = self._utilerias.agregar_impuestos_productos(partidas_documento)

        # ---------- Normalización de generales ----------
        g = (generales_documento[0] if generales_documento else {})

        order_document_id = g.get('OrderDocumentID',0)
        emisor = self._safe_str(g.get('EmisorNombre',''))
        regimen_emisor = self._safe_str(g.get('RegimenEmisor',''))
        rfc_emisor = self._safe_str(g.get('RFCEmisor',''))
        folio = self._safe_str(g.get('folio'))
        fecha_expedicion = g.get('FechaExpedicion')
        hora_expedicion = self._safe_str(g.get('HoraExpedicion'))
        serie = self._safe_str(g.get('Serie'))
        folio_num = self._safe_str(g.get('Folio'))
        zone_id = g.get('ZoneID',0)
        papel_id = g.get('PapelID', 0)
        impresiones = g.get('Impresiones', 1)

        pagado_cayal = g.get('CambioCayal', Decimal('0'))
        subtotal = g.get('SubTotal', Decimal('0'))
        iva_total = g.get('IVA', Decimal('0'))
        ieps_total = g.get('IEPS', Decimal('0'))
        total = g.get('Total', Decimal('0'))
        descuento = g.get('DescuentoCayal', Decimal('0'))
        saldo = g.get('Saldo', Decimal('0'))
        descuento_titulo = self._safe_str(g.get('DescuentoCayalTitulo'))
        cantidad_con_letra = self._safe_str(g.get('CantidadConLetra'))
        comentarios = self._safe_str(g.get('Comments'))

        # CFDI extras (opcionales en placeholders por si tu plantilla los usa)
        metodo_pago = self._safe_str(g.get('MetodoPago'))
        forma_pago = self._safe_str(g.get('FormaPago'))
        uso_cfdi = self._safe_str(g.get('ReceptorUsoCFDI'))
        regimen_receptor = self._safe_str(g.get('RegimenReceptor'))

        sello_sat = self._safe_str(g.get('SelloDigitalSATCayal'))
        sello_cfd = self._safe_str(g.get('SelloDigitalCayal'))
        cadena_original = self._safe_str(g.get('CadenaOriginalCayal'))
        tipo_relacion = self._safe_str(g.get('TipoRelacion'))
        uuids_relacionados = self._safe_str(g.get('CFDIRelacionados'))
        uuid = self._safe_str(g.get('Uuid'))
        no_cert_sat = self._safe_str(g.get('NoCertificadoSAT'))
        fecha_timbrado = self._safe_str(g.get('FechaTimbrado'))
        no_cert_emisor = self._safe_str(g.get('NoCertificado'))
        tipo_cfd =  g.get('TipoCFD','FACTURA')
        qr_base_64 = self._safe_str(g.get('CFDITimbreImage', ''))
        codigo_ean_13 = self._safe_str(g.get('CodigoEAN13', ''))

        qr_data_uri = (f"data:image/png;base64,{qr_base_64.replace('\n', '').replace('\r', '')}"
                       if qr_base_64 and not qr_base_64.startswith('data:') else qr_base_64)

        # Asegurar 13 dígitos exactos para EAN-13
        codigo_ean_13_clean = ''.join(ch for ch in codigo_ean_13 if ch.isdigit())[:13]
        # Receptor
        receptor_nombre = self._safe_str(g.get('ReceptorCayal'))
        rfc_receptor = self._safe_str(g.get('RFCReceptorCayal'))

        rec_calle = self._safe_str(g.get('ReceptorCalleCayal'))
        rec_no_ext = self._safe_str(g.get('ReceptorDomicilioNoExteriorCayal'))
        rec_no_int = self._safe_str(g.get('ReceptorDomicilioNoInteriorCayal'))
        rec_colonia = self._safe_str(g.get('ReceptorDomicilioColoniaCayal'))
        rec_cp = self._safe_str(g.get('ReceptorDomicilioCodigoPostalCayal'))

        fiscal_comments = self._safe_str(g.get('FiscalAddresMainInfoCommentsCayal'))
        tel_empresa = self._safe_str(g.get('ReceptorTelefonoEmpresa'))
        tel_celular = self._safe_str(g.get('CelularCliente'))

        capturista = self._safe_str(g.get('Capturista'))
        timbrado_por = self._safe_str(g.get('TimbradoPor'))

        # Fecha string para placeholder
        fecha_str = '' if not fecha_expedicion else str(fecha_expedicion)

        # ---------- Detalle reutilizable ----------
        detalle = self._crear_detalle_partidas(partidas_documento_impuestos)
        total_pzas = sum([reg['Quantity'] for reg in partidas_documento])

        # ---------- Bloque de pago condicional (igual que ticket) ----------
        pagado = Decimal(str(pagado_cayal or 0))
        cambio_cayal = (Decimal(str(pagado_cayal or 0)) - Decimal(str(total)))

        hay_pago = (pagado > 0 or Decimal(str(cambio_cayal or 0)) > 0)

        # ---------- Placeholders (alineados a ticket) ----------
        placeholders = {
            # Generales
            'OrderDocumentID':order_document_id,
            'EmisorNombre':emisor,
            'EmisorRFC':rfc_emisor,
            'EmisorRegimen': regimen_emisor,
            'EmisorDomicilio':'Av. Gustavo Diaz Ordaz N 207 Col. La Ermita, C.P. 24020',
            'folio': folio,
            'Serie': serie,
            'Folio': folio_num,
            'FechaExpedicion': fecha_str,
            'HoraExpedicion': hora_expedicion,
            'FechaImpresion': datetime.datetime.now().strftime('%Y-%m-%d'),
            'HoraImpresion': datetime.datetime.now().strftime('%H:%M'),
            'LugarExpedicion': 'San Francisco de Campeche, Campeche',

            # Totales / Impuestos
            'SubTotal': self._fmt_money(subtotal),
            'IEPS': self._fmt_money(ieps_total),
            'IVA': self._fmt_money(iva_total),
            'Total': self._fmt_money(total),
            'DescuentoCayalTitulo': descuento_titulo,
            'DescuentoCayal': self._fmt_money(descuento),
            'TotalPzas': str(total_pzas),
            'CantidadConLetra': cantidad_con_letra,
            'Comentarios': comentarios,
            'ZoneID': zone_id,
            'PapelID': papel_id,
            'Impresiones': impresiones,
            'Saldo': saldo,

            # Pago (condicional como en ticket)
            'cliente_pago_ticket': 'Pagado' if hay_pago else '',
            'pagado_ticket': self._fmt_money(pagado) if hay_pago else '',
            'cliente_cambio_ticket': 'Cambio' if hay_pago else '',
            'cambio_venta': self._fmt_money(cambio_cayal) if hay_pago else '',

            # CFDI opcionales
            'MetodoPago': metodo_pago,
            'FormaPago': forma_pago,
            'ReceptorUsoCFDI': uso_cfdi,
            'ReceptorRegimen': regimen_receptor,
            'SelloDigitalSATCayal': sello_sat,
            'SelloDigitalCayal': sello_cfd,
            'CadenaOriginalCayal': cadena_original,
            'TipoRelacion': tipo_relacion,
            'CFDIRelacionados': uuids_relacionados,
            'Uuid': uuid,
            'NoCertificadoSAT': no_cert_sat,
            'FechaTimbrado': fecha_timbrado,
            'NoCertificado': no_cert_emisor,
            'TipoCFD':tipo_cfd,

            'QrBase64': qr_data_uri,
            'CodigoEAN13': self._make_ean13_data_url(codigo_ean_13_clean),

            # Receptor
            'ReceptorCayal': receptor_nombre,
            'RFCReceptorCayal': rfc_receptor,
            'ReceptorCalleCayal': rec_calle,
            'ReceptorDomicilioNoExteriorCayal': rec_no_ext,
            'ReceptorDomicilioNoInteriorCayal': rec_no_int,
            'ReceptorDomicilioColoniaCayal': rec_colonia,
            'ReceptorDomicilioCodigoPostalCayal': rec_cp,

            'FiscalAddresMainInfoCommentsCayal': fiscal_comments,
            'ReceptorTelefonoEmpresa': tel_empresa,
            'CelularCliente': tel_celular,

            # Usuarios
            'Capturista': capturista,
            'TimbradoPor': timbrado_por,
            'ImpresoPor': self._user_name
        }

        return {
            'placeholders': placeholders,
            'detalle': detalle,  # lista para el bloque <DETAIL>
            'mostrar_pagado': hay_pago
        }

    # ----------- Historial -----------
    def _buscar_historial(self):
        if self._module_id == MODULO_CORTE_CAJA:
            self._historial = []
            self._seleccionados_historial = []
            return

        documentos = self._seleccionados
        """
        Consulta el historial de impresión para una lista de DocumentID.
        Usa parámetros preparados y evita inyección SQL.
        """
        if not documentos:
            return []

        # Asegurar que todos los IDs sean enteros o convertibles a int
        documentos = [int(d) for d in documentos if d is not None]

        # Crear placeholders dinámicos (?, ?, ?, ...)
        placeholders = ",".join("?" for _ in documentos)

        query = f"""
            SELECT 
                DocFolio,
                ImpresoPor,
                Fecha,
                Hora,
                Motivo,
                DocumentID
            FROM zvwBitacoraImpresionesDoctosCayal
            WHERE DocumentID IN ({placeholders})
            ORDER BY DocumentID,  Fecha ASC, Hora ASC;
        """

        # Ejecutar con parámetros
        resultados = self._base_de_datos.fetchall(query, tuple(documentos))
        self._seleccionados_historial = [reg['DocumentID'] for reg in resultados]
        self._historial = resultados

    def _buscar_motivo_id(self):

        if not self._historial:
            return 1

        seleccion = self._ventanas.obtener_input_componente('cbx_motivo')

        if seleccion == 'Seleccione':
            return

        return [reg['ID'] for reg in self._motivos_reimpresion if reg['Motivo'] == seleccion][0]

    def _crear_registro_impresion(self, document_id, motivo_id):
        self._base_de_datos.command("""
                DECLARE @DocumentID INT = ?
                DECLARE @UserID INT = ?
                DECLARE @ModuleID INT = ?
                DECLARE @MotivoID INT = ?
                
                INSERT INTO zvwhistorialimpresiones (DocumentID, Impreso, ImpresoPor, ModuloID, MotivoID)
                        VALUES (@DocumentID, GETDATE(), @UserID, @ModuleID, @MotivoID)

                UPDATE docDocument SET PrintedOn = GETDATE(), PrintedBy = @UserID WHERE DocumentID = @DocumentID
                
                """,(document_id, self._user_id, self._module_id, motivo_id))

    def _documento_esta_cancelado(self, document_id):
        status = self._base_de_datos.fetchone(
            """
                SELECT 
                    CASE 
                        WHEN CancelledOn IS NULL THEN 0 
                        ELSE 1 
                    END AS C
                FROM docDocument
                WHERE DocumentID = ?;
            """, (document_id,)
        )

        return True if status == 1 else False

    def _validar_reeimpresion_original(self, motivo_id, document_id):
        hoy = datetime.datetime.now().today()
        fecha_docto = self._base_de_datos.fetchone(
            'SELECT CAST(CreatedOn as date) FROM docDocument WHERE DocumentID = ?', (document_id,))

        impreso_previamente = False

        # determina si alguno de dichos documentos está en el historial
        if document_id in self._seleccionados_historial:
            impreso_previamente = True

        if impreso_previamente and self._user_group_id in (15, 6, 1, 7) and fecha_docto == hoy:
            return 1

        return motivo_id

    def _validar_restricciones(self, motivo_id, document_id):

        # si es la primera vez que se imprime entonces permite la iteracion
        if motivo_id == 1:
            return False

        impreso_previamente = False
        mensaje = self._ventanas.mostrar_mensaje

        # determina si alguno de dichos documentos está en el historial
        if document_id in self._seleccionados_historial:
            impreso_previamente = True

        # si no son cajeros y forman parte de administracion, cobranza, admin, contabilidad o no se ha impreso
        if not impreso_previamente or self._user_group_id  in (15,6,1,7):
            return False



        # en el caso de los documentos que tienen configuracion de papel hay que validar la restricción
        if self._module_id in (21,1400,1319,961,1316) and motivo_id not in (1,2):
            if self._restriccion_por_papel_id(document_id):
                mensaje('Los documentos de clientes con configuración de impresión en hoja no se pueden reimprimir.')
                return True

        # los documentos cancelados se permite re-impresión
        cancelado = self._documento_esta_cancelado(document_id)
        if cancelado:
            self._seleccionados_cancelados.append(document_id)
            return False

        return False

    def _restriccion_por_papel_id(self, document_id):
        papel_id = self._base_de_datos.fetchone("""
            SELECT
                CASE 
                    WHEN D.BusinessEntityID = 8179 
                         THEN CASE WHEN ISNULL(E2.Custom2, 0) = 1 THEN 1 ELSE 0 END
                    ELSE CASE WHEN ISNULL(E.Custom2, 0) = 1 THEN 1 ELSE 0 END
                END AS PapelID
            FROM docDocument D
            INNER JOIN orgBusinessEntity E 
                ON D.BusinessEntityID = E.BusinessEntityID
            LEFT JOIN docDocumentExt X 
                ON D.DocumentID = X.IDExtra
            LEFT JOIN orgBusinessEntity E2 
                ON X.CustomerID = E2.BusinessEntityID
            WHERE D.DocumentID = ?
        """, (document_id,))

        return True if papel_id == 1 else False

    def _normalizar_nombre_impresora(self, nombre_impresora):
        # este paso es para garantizar que el nombre no tenga espacios y para que los archivos se puedan mandar a imprimir
        return nombre_impresora.replace(' ', '_')

    def _determinar_cantidad_impresiones(self, placeholders, motivo_id, document_id):
        # Convertir valores a números seguros
        impresiones = placeholders.get("Impresiones", 1)
        zone_id = int(placeholders.get('ZoneID',0))
        saldo = placeholders.get("Saldo", 0)

        if zone_id == 1040:
            credit_block = self._base_de_datos.fetchone(
                """
                SELECT CASE  WHEN CreditBlock = 1 THEN 'Bloqueado' ELSE 'Desbloqueado' END Credit
                FROM [dbo].[zvwBuscarInfoCliente-BusinessEntityID](?)
                """,(zone_id,))

            if credit_block == 'Bloqueado':
                return 1

        try:
            impresiones = int(impresiones)
        except Exception:
            impresiones = 1

        try:
            saldo = float(saldo)
        except Exception:
            saldo = 0

        # Regla principal: solo motivo 1 permite doble impresión
        cantidad = impresiones if motivo_id == 1 else 1

        # Forzar 1 si está pagado
        if saldo == 0:
            return 1

        # Forzar 1 si se canceló
        if document_id in self._seleccionados_cancelados:
            return 1

        # Forzar 1 si ya se imprimió previamente
        if document_id in self._seleccionados_historial:
            return 1

        return cantidad

    def _determinar_texto_marca(self, cantidad, motivo_id, copia_idx=0, esta_cancelado=False):
        """
        Retorna el texto de marca ('ORIGINAL', 'COPIA', 'CANCELADO')
        y el motivo_id que debe usarse para ticket.set_marca_agua().
        """
        # --- Reglas para una sola impresión ---
        if cantidad == 1:
            # Cancelado → siempre CANCELADO
            if motivo_id == 2 or esta_cancelado:
                return "CANCELADO", 2

            # Motivo 1 → ORIGINAL
            if motivo_id == 1:
                return "ORIGINAL", 1

            # Cualquier otro → COPIA
            return "REIMPRESO", 3

        # --- Reglas cuando hay 2 impresiones ---
        # (caso típico: motivo_id == 1, ORIGINAL + COPIA)
        else:
            if copia_idx == 0:
                return "ORIGINAL", 1
            else:
                return "COPIA", 4
