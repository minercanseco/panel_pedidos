import platform
import tempfile
import tkinter as tk
import os
from datetime import datetime, date, time
from cayal.ventanas import Ventanas
from cayal.comandos_base_datos import BaseDatos
from cayal.informe import Informe


class ArchivoCayal:
    def __init__(self, master, parametros):

        self._declarar_clases_auxiliares(parametros, master)
        self._declarar_variables_de_instancia(master)

        self._crear_frames()
        self._crear_componentes()
        self._ajustar_componentes()
        self._rellenar_componentes()
        self._cargar_eventos()
        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Acrhivo cayal')
        self._actualizar_info_componentes()
        self._bloquear_componentes()

    def _declarar_clases_auxiliares(self, parametros, master):
        self._ventanas = Ventanas(master)
        self._parametros = parametros
        self._base_de_datos = BaseDatos()
        self._informe = Informe()

    def _declarar_variables_de_instancia(self, master):
        self._master = master
        self._user_id = self._parametros.id_usuario
        self._module_id = self._parametros.id_modulo
        self._user_group_id = self._buscar_grupo_usuario()

        self._modulos = [21,1400,1316,1319]

        self._consulta_usuarios_timbrado = []
        self._minimo = 0
        self._maximo = 0

        self._folio_minimo = ''
        self._folio_maximo = ''

        self._minimo_21 = 0
        self._minimo_1400 = 0
        self._minimo_1316 = 0
        self._minimo_1319 = 0

        self._maximo_21 = 0
        self._maximo_1400 = 0
        self._maximo_1316 = 0
        self._maximo_1319 = 0

    def _crear_frames(self):
        frames = {
            'frame_principal': ('master', None,
                                {'row': 0, 'column': 0, 'sticky': tk.W}),

            'frame_componentes': ('frame_principal', None,
                                  {'row': 0, 'column': 0, 'columnspan': 2, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_comp1': ('frame_componentes', 'Generales',
                         {'row': 1, 'column': 0, 'columnspan': 2, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_21': ('frame_componentes', 'Facturas Mayoreo',
                                  {'row': 2, 'column': 0, 'columnspan': 2, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_1400': ('frame_componentes', 'Facturas Minisuper',
                         {'row': 3, 'column': 0, 'columnspan': 2, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_1316': ('frame_componentes', 'Notas Entregadas',
                         {'row': 4, 'column': 0, 'columnspan': 2, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_1319': ('frame_componentes', 'Facturas Entregadas',
                         {'row': 5, 'column': 0, 'columnspan': 2, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_tabla': ('frame_principal', 'Historial',
                            {'row': 1, 'column': 0, 'columnspan': 2, 'padx': 5, 'pady': 5, 'sticky': tk.NSEW}),

            'frame_botones': ('frame_principal', None,
                              {'row': 2, 'column': 1, 'sticky': tk.W}),



        }
        self._ventanas.crear_frames(frames)

    def _crear_componentes(self):

        componentes = {
            'tbx_modulo':('frame_comp1', None,  'Módulo:',None),
            'den_fecha':('frame_comp1', None,  'Fecha:',None),
            'cbx_cajeros': ('frame_comp1', None, 'Cajeros:', None),
            'tbx_docs_21': ('frame_21', {'row': 0, 'column': 1, 'padx': 1, 'pady': 1,'sticky': tk.W}, 'N#:',None),
            'tbx_inicial_21':('frame_21', {'row': 0, 'column': 3, 'padx': 1, 'pady': 1,'sticky': tk.W},  'Inicial:',None),
            'tbx_final_21':('frame_21',{'row': 0, 'column': 5, 'padx': 1, 'pady': 1,'sticky': tk.W},  'Final:',None),
            'tbx_docs_1400': ('frame_1400', {'row': 0, 'column': 1, 'padx': 1, 'pady': 1,'sticky': tk.W}, 'N#:', None),
            'tbx_inicial_1400': ('frame_1400', {'row': 0, 'column': 3, 'padx': 1, 'pady': 1,'sticky': tk.W}, 'Inicial:',None),
            'tbx_final_1400':('frame_1400',{'row': 0, 'column': 5, 'padx': 1, 'pady': 1, 'sticky': tk.W},  'Final:',None),
            'tbx_docs_1316': ('frame_1316', {'row': 0, 'column': 1, 'padx': 1, 'pady': 1,'sticky': tk.W}, 'N#:', None),
            'tbx_inicial_1316': ('frame_1316', {'row': 0, 'column': 3, 'padx': 1, 'pady': 1,'sticky': tk.W},  'Inicial:',None),
            'tbx_final_1316': ('frame_1316',{'row': 0, 'column': 5, 'padx': 1, 'pady': 1,'sticky': tk.W}, 'Final:',None),
            'tbx_docs_1319': ('frame_1319', {'row': 0, 'column': 1, 'padx': 1, 'pady': 1,'sticky': tk.W}, 'N#:', None),
            'tbx_inicial_1319': ('frame_1319', {'row': 0, 'column': 3, 'padx': 1, 'pady': 1,'sticky': tk.W}, 'Inicial:',None),
            'tbx_final_1319': ('frame_1319', {'row': 0, 'column': 5, 'padx': 1, 'pady': 1, 'sticky': tk.W},  'Final:',None),
            'tvw_historial': ('frame_tabla', self._crear_columnas(),5, None),
            'btn_generar': ('frame_botones', None, 'Generar',None),
            'btn_cancelar': ('frame_botones', 'danger', 'Cancelar', None),

        }

        self._ventanas.crear_componentes(componentes)

    def _limpiar_componentes(self):
        componentes = [
            'tbx_docs',
            'tbx_inicial',
            'tbx_final',
            'cbx_cajeros'
        ]
        self._ventanas.limpiar_componentes(componentes)

    def _crear_columnas(self):
        return [
            {'text': 'Usuario', "stretch": False, 'width': 100, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'ImpresoPor', "stretch": False, 'width': 100, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'Impreso', "stretch": False, 'width': 80, 'column_anchor': tk.W, 'heading_anchor': tk.W,
             'hide': 0},
            {'text': 'Inicial', "stretch": False, 'width': 80, 'column_anchor': tk.E,
             'heading_anchor': tk.E,
             'hide': 0},
            {'text': 'Final', "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 0},
            {'text': 'DocumentIDInicial', "stretch": False, 'width': 80, 'column_anchor': tk.E,
             'heading_anchor': tk.E,
             'hide': 1},
            {'text': 'DocumentIDFinal', "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1},
            {'text': 'ModuleID', "stretch": False, 'width': 80, 'column_anchor': tk.E, 'heading_anchor': tk.E,
             'hide': 1}
        ]

    def _rellenar_componentes(self):
        module_name = self._base_de_datos.fetchone(
            'SELECT ModuleName FROM engModule WHERE ModuleID = ?',
            (self._module_id,)
        )
        self._ventanas.insertar_input_componente('tbx_modulo', module_name)

    def _bloquear_componentes(self):
        for clave, valor in self._ventanas.componentes_forma.items():
            if 'tbx' in clave:
                self._ventanas.bloquear_componente(clave)

    def _ajustar_componentes(self):
        for clave, valor in self._ventanas.componentes_forma.items():
            if clave != 'tbx_modulo' and 'tbx' in clave:
                self._ventanas.ajustar_ancho_componente(clave,10)

    def _cargar_eventos(self):
        eventos = {
            'den_fecha': lambda event:self._actualizar_info_componentes(),
            'btn_cancelar': self._master.destroy,
            'btn_generar': self._generar_arhivo,
        }
        self._ventanas.cargar_eventos(eventos)

    def _buscar_usuarios_timbrado(self):
        fecha = self._ventanas.obtener_input_componente('den_fecha')

        return self._base_de_datos.fetchall("""
            SELECT CFD.UserID, U.UserName
            FROM docDocument D
                INNER JOIN docDocumentCFD CFD ON D.DocumentID = CFD.DocumentID
                INNER JOIN engUser U ON CFD.UserID = U.UserID
            WHERE CAST(D.CreatedOn as date) = CAST( ? as date)
                AND D.ModuleID = ?
            GROUP BY CFD.UserID, U.UserName 
        """,(fecha, self._module_id))

    def _actualizar_info_componentes(self):

        self._consulta_usuarios_timbrado = self._buscar_usuarios_timbrado()
        self._folios_todos_usuarios_por_fecha()

        if self._consulta_usuarios_timbrado:
            self._limpiar_componentes()

            usuarios_timbrado = [reg['UserName'] for reg in self._consulta_usuarios_timbrado
                                 if reg['UserID'] != self._user_id]


            self._ventanas.rellenar_cbx('cbx_cajeros', usuarios_timbrado)

            historial = self._buscar_historial()
            self._ventanas.rellenar_treeview(
                'tvw_historial',
                self._crear_columnas(),
                historial,
                valor_barra_desplazamiento=5)

        self._bloquear_componentes()

    def _folios_todos_usuarios_por_fecha(self):
        fecha = self._ventanas.obtener_input_componente('den_fecha')
        resultados = []  # para impresión final

        for module_id in self._modulos:
            valores = self._buscar_folios_intervalos_folios(fecha, module_id) or {}
            maximo = valores.get('maximo', 0) or 0
            minimo = valores.get('minimo', 0) or 0
            numero = valores.get('numero', 0) or 0

            folio_max = self._buscar_folio_documento(maximo) if maximo else 'No aplica'
            folio_min = self._buscar_folio_documento(minimo) if minimo else 'No aplica'

            nombre_max = f'tbx_final_{module_id}'
            nombre_min = f'tbx_inicial_{module_id}'
            nombre_docs = f'tbx_docs_{module_id}'

            self._ventanas.insertar_input_componente(nombre_max, folio_max)
            self._ventanas.insertar_input_componente(nombre_min, folio_min)
            self._ventanas.insertar_input_componente(nombre_docs, numero)

            resultados.append({
                "Módulo": module_id,
                "MínimoID": minimo,
                "MáximoID": maximo,
                "FolioInicial": folio_min,
                "FolioFinal": folio_max,
                "Documentos": numero
            })

        # 🔹 Print tabular para depuración legible
        print(f"\n{'Módulo':<10} {'MínimoID':<10} {'MáximoID':<10} {'FolioInicial':<15} {'FolioFinal':<15} {'Docs':<6}")
        print("-" * 70)
        for r in resultados:
            print(
                f"{r['Módulo']:<10} {r['MínimoID']:<10} {r['MáximoID']:<10} {str(r['FolioInicial']):<15} {str(r['FolioFinal']):<15} {r['Documentos']:<6}")
        print("-" * 70)

    def _folios_individuales_usuario_por_fecha(self, user_id):
        fecha = self._ventanas.obtener_input_componente('den_fecha')

        for module_id in self._modulos:
            valores = self._buscar_folios_intervalos_folios(fecha, module_id, user_id)

            maximo = valores.get('maximo', 0) or 0
            minimo = valores.get('minimo', 0) or 0
            numero = valores.get('numero', 0) or 0

            # Mapeo dinámico de atributos
            if module_id == 21:
                self._minimo_21, self._maximo_21 = minimo, maximo
            elif module_id == 1400:
                self._minimo_1400, self._maximo_1400 = minimo, maximo
            elif module_id == 1316:
                self._minimo_1316, self._maximo_1316 = minimo, maximo
            elif module_id == 1319:
                self._minimo_1319, self._maximo_1319 = minimo, maximo

        self._definir_folio_inicial_y_final(user_id)
        print(
            f"{'Módulo':<10} {'Mínimo':<12} {'Máximo':<12}",
            f"\n{'21':<10} {self._minimo_21:<12} {self._maximo_21:<12}",
            f"\n{'1400':<10} {self._minimo_1400:<12} {self._maximo_1400:<12}",
            f"\n{'1316':<10} {self._minimo_1316:<12} {self._maximo_1316:<12}",
            f"\n{'1319':<10} {self._minimo_1319:<12} {self._maximo_1319:<12}",
            f"\n{'Actual:':<10} {self._minimo:<12} {self._maximo:<12}"
        )
        return True

    def _definir_folio_inicial_y_final(self, userid):
        """
        Define los DocumentID inicial y final a imprimir para el usuario y módulo actuales,
        respetando impresiones previas del mismo día y módulo:
        - Si ya hubo impresión, comienza en (último DocumentIDFinal + 1).
        - Si no hay pendiente (inicio > máximo), no imprime.
        Devuelve True si hay algo por imprimir, False en caso contrario.
        """

        print("\n[🔍 INICIO] _definir_folio_inicial_y_final -----------------------------")

        # 1) Resolver user_id si viene como nombre de usuario
        if isinstance(userid, str):
            uid = self._resolver_user_id(userid)
            if uid is None:
                self._ventanas.mostrar_mensaje('No se pudo resolver el UserID del usuario seleccionado.')
                print("❌ No se pudo resolver el UserID para:", userid)
                return False
        else:
            try:
                uid = int(userid)
            except Exception:
                self._ventanas.mostrar_mensaje('Parámetro userid inválido.')
                print("❌ Parámetro userid inválido:", userid)
                return False

        module_id = int(self._module_id)
        fecha = self._ventanas.obtener_input_componente('den_fecha')
        usuario_seleccionado = self._ventanas.obtener_input_componente('cbx_cajeros')

        print(f"📅 Fecha: {fecha} | 👤 Usuario: {usuario_seleccionado} ({uid}) | 🧩 Módulo: {module_id}")

        # 2) Obtener rango del día (min/max) para el usuario + módulo actuales
        intervalos = self._buscar_folios_intervalos_folios(fecha, module_id, uid) or {}
        maximo = int(intervalos.get('maximo') or 0)
        minimo = int(intervalos.get('minimo') or 0)
        numero = int(intervalos.get('numero') or 0)

        print(f"📄 Intervalos obtenidos → Mínimo: {minimo} | Máximo: {maximo} | Documentos: {numero}")

        if not (minimo and maximo and numero):
            print("⚠️ No hay datos para el usuario/módulo especificado.")
            self._minimo = self._maximo = 0
            self._folio_minimo = self._folio_maximo = 'No aplica'
            print("[FIN] ❌ Sin rango definido.\n")
            return False

        # 3) Buscar en historial el ÚLTIMO DocumentIDFinal del mismo usuario y módulo
        ult_final = 0
        filas = self._ventanas.obtener_filas_treeview('tvw_historial')
        print(f"📋 Analizando historial ({len(filas)} filas)...")

        for fila in filas:
            valores = self._ventanas.procesar_fila_treeview('tvw_historial', fila)
            user_hist = valores.get('Usuario')
            mod_hist = int(valores.get('ModuleID') or 0)
            doc_final = int(valores.get('DocumentIDFinal') or 0)

            if user_hist == usuario_seleccionado and mod_hist == module_id:
                if doc_final > ult_final:
                    ult_final = doc_final

        print(f"📘 Último DocumentIDFinal encontrado: {ult_final if ult_final else 'Ninguno'}")

        # 4) Calcular inicio efectivo: si hubo impresión, arranca en (ult_final + 1)
        # bucar el folio siguiente valido para el usuario

        start_id = 0
        if ult_final == 0:
            start_id = minimo
        else:
            start_id = self._base_de_datos.fetchone("""
                    SELECT COALESCE(D.DocumentID, 0) AS DocumentID
                    FROM docDocument D
                        INNER JOIN docDocumentCFD CFD ON D.DocumentID = CFD.DocumentID
                        INNER JOIN engUser U ON CFD.UserID = U.UserID
                    WHERE 
                      D.ModuleID = ?
                      AND U.UserID = ?
                      AND D.CancelledON IS NULL
                      AND D.DocumentID > ?;
                """,(self._module_id, userid, ult_final,))
        print(f"🧾 DocumentID de inicio calculado: {start_id}")

        # Si ya no queda nada por imprimir
        if not start_id or start_id == 0 or start_id > maximo:
            print("✅ Todos los documentos ya fueron impresos (inicio > máximo).")
            self._minimo = self._maximo = 0
            self._folio_minimo = self._folio_maximo = 'No aplica'
            print("[FIN] ❌ Sin documentos pendientes.\n")
            return False

        # 5) Asignar rango efectivo y folios legibles (usar los IDs efectivos)
        self._minimo = start_id
        self._maximo = maximo

        self._folio_minimo = self._buscar_folio_documento(self._minimo)
        self._folio_maximo = self._buscar_folio_documento(self._maximo)

        print("\n🧩 RESULTADO FINAL")
        print(f"   🔹 Mínimo ID: {self._minimo}")
        print(f"   🔹 Máximo ID: {self._maximo}")
        print(f"   🔹 Folio inicial: {self._folio_minimo}")
        print(f"   🔹 Folio final: {self._folio_maximo}")
        print("--------------------------------------------------------[FIN OK]\n")

        return True

    def _buscar_folios_intervalos_folios(self, fecha, module_id, user_id=0):

        if user_id == 0:
            consulta = self._base_de_datos.fetchall("""
                SELECT 
                    MIN(D.DocumentID) AS Minimo, 
                    MAX(D.DocumentID) AS Maximo, 
                    COUNT(D.DocumentID) AS Numero
                FROM docDocument D
                INNER JOIN docDocumentCFD CFD ON D.DocumentID = CFD.DocumentID
                WHERE CAST(D.CreatedOn AS date) = CAST(? AS date)
                  AND D.ModuleID = ?
                  AND D.CancelledON IS NULL
            """, (fecha, module_id))

            if consulta and consulta[0]['Maximo'] and consulta[0]['Minimo']:
                return {
                    'maximo': consulta[0]['Maximo'],
                    'minimo': consulta[0]['Minimo'],
                    'numero': consulta[0]['Numero']
                }

        if user_id != 0 and module_id in (1400,21,1319):
            consulta = self._base_de_datos.fetchall("""
                SELECT 
                    MIN(D.DocumentID) AS Minimo, 
                    MAX(D.DocumentID) AS Maximo, 
                    COUNT(D.DocumentID) AS Numero
                FROM docDocument D
                INNER JOIN docDocumentCFD CFD ON D.DocumentID = CFD.DocumentID
                INNER JOIN engUser U ON CFD.UserID = U.UserID
                WHERE CAST(D.CreatedOn AS date) = CAST(? AS date)
                  AND D.ModuleID = ?
                  AND U.UserID = ?
                  AND D.CancelledON IS NULL
            """, (fecha, module_id, user_id))

            if consulta and consulta[0]['Maximo'] and consulta[0]['Minimo']:
                return {
                    'maximo': consulta[0]['Maximo'],
                    'minimo': consulta[0]['Minimo'],
                    'numero': consulta[0]['Numero']
                }

        if user_id != 0 and module_id in (1316,):
            consulta = self._base_de_datos.fetchall("""
                SELECT 
                    MIN(D.DocumentID) AS Minimo, 
                    MAX(D.DocumentID) AS Maximo, 
                    COUNT(D.DocumentID) AS Numero
                FROM docDocument D
                INNER JOIN engUser U ON D.CreatedBy= U.UserID
                WHERE CAST(D.CreatedOn AS date) = CAST(? AS date)
                  AND D.ModuleID = ?
                  AND U.UserID = ?
                  AND D.CancelledON IS NULL
            """, (fecha, module_id, user_id))

            if consulta and consulta[0]['Maximo'] and consulta[0]['Minimo']:
                return {
                    'maximo': consulta[0]['Maximo'],
                    'minimo': consulta[0]['Minimo'],
                    'numero': consulta[0]['Numero']
                }

        # Si no hay datos o error, devuelve 0
        return {'maximo': 0, 'minimo': 0, 'numero': 0}

    def _buscar_grupo_usuario(self):
        return self._base_de_datos.fetchone(
            'SELECT UserGroupID FROM engUser WHERE UserID = ?',
            (self._user_id,)
        )

    def _resolver_user_id(self, username: str):
        return next((r['UserID'] for r in self._consulta_usuarios_timbrado
                     if r['UserName'] == username), None)

    def _buscar_folio_documento(self, document_id):
        return self._base_de_datos.fetchone(
            "SELECT ISNULL(FolioPrefix,'') + ISNULL(Folio,'') FROM docDocument WHERE DocumentID = ?"
            , (document_id,))

    def _buscar_historial(self):
        fecha = self._ventanas.obtener_input_componente('den_fecha')

        return self._base_de_datos.fetchall("""
            SELECT 
                U.UserName Timbrado,
                UM.UserName ImpresoPor,
                CONVERT(CHAR(5), Impreso, 108) AS Hora,
                AR.Inicial,
                AR.Final,
                AR.DocumentIDInicial,
                AR.DocumentIDFinal,
                AR.ModuleID
            FROM zvwArchivoImpresoCayal AR
                INNER JOIN engUser U ON AR.UserID = U.UserID
                INNER JOIN engUser UM ON AR.ImpresoPor = UM.UserID
            WHERE CAST( ?  as date) = CAST(Fecha as date)
            AND AR.ModuleID = ?
        """,(fecha, self._module_id))

    def _generar_arhivo(self):
        """
        Genera el HTML de validación usando la clase Informe y lo abre en el navegador.
        Flujo:
        - Encabezado por documento en UNA sola fila.
        - Comentarios (si existen) en una segunda fila (colspan total).
        - Encabezados del detalle y sus partidas.
        - Omite DocumentID / DocumentItemID.
        - Muestra por documento solo una vez: Cliente, TotalFac, RFC, Capturista, TimbradoPor,
          MetodoPago, FormaPago, StatusDocto, Comentarios, StatusTimbrado, PedFolio, ReceptorUsoCFDI.
        """
        if not self._validar_impresion_previa():
            return

        from html import escape
        from datetime import datetime, date, time
        import os

        def _render_tabla_encabezado_linea(filas):
            """Construye una sola tabla con un encabezado por documento y sus partidas."""

            # --- clave de agrupamiento por documento ---
            def kdoc(r):
                fol = r.get('DocFolio') or ''
                if fol:
                    return ('FOL', fol)
                # Fallback estable cuando no hay folio (muy raro)
                return ('NF', f"{r.get('Cliente', '')}|{r.get('Fecha', '')}|{r.get('Hora', '')}")

            # Orden consistente: primero grupo (doc), luego descripción de partida
            filas_orden = sorted(filas, key=lambda r: (kdoc(r), str(r.get('Descripcion', ''))))

            # Agrupar manualmente
            grupos = {}
            for r in filas_orden:
                grupos.setdefault(kdoc(r), []).append(r)

            out = []
            out.append('''
    <table class="tabla-agrupada" style="width:100%; border-collapse:collapse; table-layout:fixed;">
      <colgroup>
        <col style="width:7%;">     <!-- Cantidad -->
        <col style="width:7%;">     <!-- Unidad   -->
        <col>                       <!-- Descripción (flex) -->
        <col style="width:10%;">    <!-- Precio -->
        <col style="width:12%;">    <!-- Importe -->
        <col style="width:18%;">    <!-- Comentarios -->
      </colgroup>
      <tbody>
    ''')

            # Recorre documentos (grupos)
            first_group = True
            for _, items in grupos.items():
                first = items[0]
                partes = []

                def add_val(value, fmt=None, prefix=None, clase=None):
                    if value in (None, ''):
                        return
                    if fmt == 'money':
                        try:
                            value = f"{float(value):,.2f}"
                        except Exception:
                            pass
                    if prefix:
                        value = f"{prefix} {value}"
                    span = f"<span class='{clase}'>{escape(str(value))}</span>" if clase else f"<span class='v'>{escape(str(value))}</span>"
                    partes.append(span)

                # --- Fila de encabezado del documento ---
                add_val(first.get('DocFolio', ''))
                add_val(first.get('PedFolio', ''))
                add_val(first.get('Cliente', ''), clase='cliente')
                add_val(first.get('Capturista', ''), prefix='Captura:')
                add_val(first.get('TimbradoPor', ''), prefix='Timbra:')
                add_val(first.get('TotalFac', ''), fmt='money')
                add_val(first.get('RFC', ''))
                add_val(first.get('MetodoPago', ''))
                add_val(first.get('FormaPago', ''))
                add_val(first.get('ReceptorUsoCFDI', ''))
                add_val(first.get('StatusTimbrado', ''))
                add_val(first.get('StatusDocto', ''))

                linea = " · ".join(partes)
                # Separador superior solo entre documentos (no antes del primero)
                if not first_group:
                    out.append("<tr class='sep'><td colspan='6'><hr></td></tr>")
                first_group = False

                out.append("<tr class='docline-row'><td class='docline' colspan='6'>")
                out.append(linea)
                out.append("</td></tr>")

                # --- Comentarios del documento (opcional) ---
                comentarios_doc = (first.get('Comentarios') or '').strip()
                if comentarios_doc:
                    out.append("<tr class='doc-comments-row'><td class='doccomments' colspan='6'>")
                    out.append(f"{escape(comentarios_doc)}")
                    out.append("</td></tr>")

                # --- Encabezado del detalle del documento ---
                out.append('''
    <tr class="det-head">
      <th class="num">Cant</th>
      <th class="num">Unidad</th>
      <th>Producto</th>
      <th class="num">Precio</th>
      <th class="num">Importe</th>
      <th>Comentarios</th>
    </tr>''')

                # --- Partidas del documento ---
                for it in items:
                    cant = it.get('Cantidad', '')
                    unid = it.get('Unidad', '')
                    desc = it.get('Descripcion', '')
                    precio = it.get('Precio', '')
                    importe = it.get('Importe', '')
                    cmt_partida = it.get('ComentariosPartida', it.get('ComentariosPartirda', ''))

                    try:
                        precio = f"{float(precio):,.2f}" if precio not in ('', None) else ''
                    except Exception:
                        pass
                    try:
                        importe = f"{float(importe):,.2f}" if importe not in ('', None) else ''
                    except Exception:
                        pass

                    out.append('<tr class="det-row">')
                    out.append(f'<td class="num">{escape(str(cant))}</td>')
                    out.append(f'<td class="num">{escape(str(unid))}</td>')
                    out.append(f'<td class="desc-1">{escape(str(desc))}</td>')
                    out.append(f'<td class="num">{escape(str(precio))}</td>')
                    out.append(f'<td class="num">{escape(str(importe))}</td>')
                    out.append(f'<td class="cmt-ptd">{escape(str(cmt_partida or ""))}</td>')
                    out.append('</tr>')

            # Cierre de tabla (fuera de los bucles)
            out.append('''
      </tbody>
    </table>
    ''')
            return ''.join(out)

        # -----------------------------------------------------------------------
        usuario = self._ventanas.obtener_input_componente('cbx_cajeros')
        if not usuario or usuario == 'Seleccione':
            self._ventanas.mostrar_mensaje('Debe seleccionar un usuario.')
            return

        try:
            user_id = next(reg['UserID'] for reg in self._consulta_usuarios_timbrado if reg['UserName'] == usuario)
        except StopIteration:
            self._ventanas.mostrar_mensaje('No se encontró el usuario seleccionado.')
            return

        # Define rangos por usuario (llena _min/_max por módulo y calcula _min/_max efectivos para el módulo actual)
        self._folios_individuales_usuario_por_fecha(user_id)

        # Detalles del módulo actual
        consulta = self._buscar_detalles_documentos(self._minimo, self._maximo, user_id)

        # Si el módulo activo es 21, agregar también NVR (1316) y FGR (1319)
        consulta_nvr = []
        consulta_fgr = []
        folio_ini_nvr = folio_fin_nvr = 'No aplica'
        folio_ini_fgr = folio_fin_fgr = 'No aplica'

        if self._module_id == 21:
            # --- NVR (1316) por CreatedBy ---
            if self._minimo_1316 and self._maximo_1316 and self._maximo_1316 >= self._minimo_1316:
                consulta_nvr = self._buscar_detalles_documentos_especial(
                    1316, self._minimo_1316, self._maximo_1316, user_id
                ) or []
                folio_ini_nvr = self._buscar_folio_documento(self._minimo_1316) or 'No aplica'
                folio_fin_nvr = self._buscar_folio_documento(self._maximo_1316) or 'No aplica'

            # --- FGR (1319) por CFD.UserID ---
            if self._minimo_1319 and self._maximo_1319 and self._maximo_1319 >= self._minimo_1319:
                consulta_fgr = self._base_de_datos.fetchall("""
                    SELECT 
                        D.DocumentID,
                        DT.DocumentItemID,
                        DT.Quantity                AS Cantidad,
                        DT.Unit                    AS Unidad,
                        ISNULL(D.FolioPrefix, '') + ISNULL(D.Folio, '') AS DocFolio,
                        DT.[Description]           AS Producto,
                        DT.UnitPrice               AS Precio,
                        ROUND(
                            CASE
                                WHEN DT.TaxTypeID = 16 THEN (DT.UnitPrice * 1.08) * 1.16
                                WHEN DT.TaxTypeID = 5  THEN (DT.UnitPrice * 1.16)
                                WHEN DT.TaxTypeID = 15 THEN (DT.UnitPrice * 1.08)
                                WHEN DT.TaxTypeID = 18 THEN (DT.UnitPrice + (SELECT TaxAmount FROM engTaxItem WHERE TaxItemID = 20)) * 1.16
                                WHEN DT.TaxTypeID = 19 THEN (DT.UnitPrice + (SELECT TaxAmount FROM engTaxItem WHERE TaxItemID = 21)) * 1.16
                                WHEN DT.TaxTypeID = 20 THEN (DT.UnitPrice + (SELECT TaxAmount FROM engTaxItem WHERE TaxItemID = 22)) * 1.16
                                ELSE DT.UnitPrice
                            END * DT.Quantity, 2
                        ) AS Importe,
                        D.Total,
                        D.Balance                   AS Saldo,
                        D.TotalPaid                 AS Cobrado,
                        E.OfficialName              AS Cliente,
                        CAST(D.CreatedOn AS date)   AS Fecha,
                        CONVERT(time, D.CreatedOn)  AS Hora,
                        U.UserName                  AS TimbradoPor,
                        UC.UserName                 AS Capturista,
                        CFD.RFC,
                        CFD.MetodoPago,
                        CFD.FormaPago,
                        CFD.ReceptorUsoCFDI         AS UsoCFDI,
                        CASE 
                            WHEN CFD.CFDCancelledStatusID = 0 THEN 'Vigente'
                            WHEN CFD.CFDCancelledStatusID = 3 THEN 'Cancelado'
                        END AS StatusDocto,
                        ISNULL(REPLACE(REPLACE(D.Comments, '[', ''), ']', ''), '') AS Comentarios,
                        CASE 
                            WHEN CFD.CFDStatusID = 3 THEN 'Timbrado'
                            WHEN CFD.CFDStatusID = 0 THEN 'No Enviado'
                        END AS StatusTimbrado,
                        ISNULL(P.FolioPrefix, '') + ISNULL(P.Folio, '') AS PedFolio,
                        ISNULL(REPLACE(REPLACE(DT.Comments, '[', ''), ']', ''), '') AS ComentariosPartida
                    FROM docDocument D
                        INNER JOIN docDocumentItem DT ON D.DocumentID = DT.DocumentID
                        INNER JOIN dbo.orgBusinessEntity AS E ON D.BusinessEntityID = E.BusinessEntityID
                        LEFT OUTER JOIN docDocumentOrderCayal P ON D.OrderDocumentID = P.OrderDocumentID
                        LEFT OUTER JOIN dbo.docDocumentCFD AS CFD ON D.DocumentID = CFD.DocumentID
                        LEFT OUTER JOIN dbo.engUser AS U ON CFD.UserID = U.UserID 
                        INNER JOIN dbo.engUser AS uc ON D.CreatedBy = uc.UserID
                    WHERE D.ModuleID = ?
                      AND DT.DeletedOn IS NULL
                      AND D.DocumentID BETWEEN ? AND ?
                      AND CFD.UserID = ?
                      AND D.CancelledOn IS NULL
                    ORDER BY DT.DocumentItemID
                """, (1319, self._minimo_1319, self._maximo_1319, user_id)) or []
                folio_ini_fgr = self._buscar_folio_documento(self._minimo_1319) or 'No aplica'
                folio_fin_fgr = self._buscar_folio_documento(self._maximo_1319) or 'No aplica'

        # Si no hay datos del módulo actual ni extras, aborta
        if not (consulta or consulta_nvr or consulta_fgr):
            print('No hay datos para generar el informe.')
            self._ventanas.mostrar_mensaje('No hay datos para generar el informe.')
            return

        # ---------- Normalización común ----------
        def _normalizar(reg):
            d = dict(reg)
            if 'Producto' in d and 'Descripcion' not in d:
                d['Descripcion'] = d.pop('Producto')
            if 'Total' in d and 'TotalFac' not in d:
                d['TotalFac'] = d.pop('Total')
            if 'UsoCFDI' in d and 'ReceptorUsoCFDI' not in d:
                d['ReceptorUsoCFDI'] = d.pop('UsoCFDI')
            if 'ComentariosPartida' not in d and 'ComentariosPartirda' in d:
                d['ComentariosPartida'] = d.pop('ComentariosPartirda')

            f, h = d.get('Fecha'), d.get('Hora')
            d['Fecha'] = f.strftime('%Y-%m-%d') if isinstance(f, date) else str(f or '')
            d['Hora'] = h.strftime('%H:%M:%S') if isinstance(h, time) else str(h or '')
            d['PedFolio'] = d.get('PedFolio', '') or ''
            d.pop('DocumentID', None)
            d.pop('DocumentItemID', None)
            return d

        normalizados = []
        for r in (consulta or []):
            normalizados.append(_normalizar(r))
        for r in (consulta_nvr or []):
            normalizados.append(_normalizar(r))
        for r in (consulta_fgr or []):
            normalizados.append(_normalizar(r))

        # Parámetros para la plantilla
        parametros = [{
            'Fecha': self._ventanas.obtener_input_componente('den_fecha'),
            'TimbradoPor': usuario,
            'FolioInicial': self._folio_minimo,
            'FolioFinal': self._folio_maximo,
        }]

        # Para módulo 21, agrega folios NVR/FGR al encabezado
        if self._module_id == 21:
            parametros[0].update({
                'FolioInicialNVR': folio_ini_nvr,
                'FolioFinalNVR': folio_fin_nvr,
                'FolioInicialFGR': folio_ini_fgr,
                'FolioFinalFGR': folio_fin_fgr,
            })
            print("📎 Folios extra (mód.21):",
                  f"NVR[{self._minimo_1316}-{self._maximo_1316}] -> {folio_ini_nvr}..{folio_fin_nvr} |",
                  f"FGR[{self._minimo_1319}-{self._maximo_1319}] -> {folio_ini_fgr}..{folio_fin_fgr}")

        # Rutas
        base_dir = os.path.dirname(os.path.abspath(__file__))
        plantilla = getattr(self, '_plantilla_validacion', None) or os.path.join(base_dir, 'plantilla_archivo.html')

        if not os.path.exists(plantilla):
            self._ventanas.mostrar_mensaje(f'No se encontró la plantilla: {plantilla}')
            return

        nombre_salida = f"ValidacionArchivoCayal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        carpeta_salida = self._obtener_directorio_documentos(temporal=True)
        ruta_salida = os.path.join(carpeta_salida, nombre_salida)

        # Render
        tabla_html = _render_tabla_encabezado_linea(normalizados)

        self._informe.plantilla = plantilla
        self._informe.archivo = ruta_salida
        self._informe.parametros = parametros
        self._informe.agregar_tabla_html(tabla_html, titulo='tabla', encabezado=None)

        self._informe.generar_informe_html()
        self._informe.abrir_html_en_navegador(eliminar_archivo=False)
        self._insertar_registro(user_id)
        self._master.destroy()

    def _insertar_registro(self, user_id):
        fecha = self._ventanas.obtener_input_componente('den_fecha')
        self._base_de_datos.command("""
            INSERT INTO zvwArchivoImpresoCayal
                (Fecha, UserID, Impreso, ImpresoPor, ModuleID, Inicial, Final, DocumentIDInicial, DocumentIDFinal)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (fecha,
         user_id,
         datetime.now(),
         self._user_id,
         self._module_id,
         self._folio_minimo,
         self._folio_maximo,
         self._minimo,
         self._maximo
         ))

    def _buscar_detalles_documentos(self,  minimo, maximo, user_id):
        return self._base_de_datos.fetchall("""
            SELECT 
                D.DocumentID,
                DT.DocumentItemID,
                DT.Quantity                AS Cantidad,
                DT.Unit                    AS Unidad,
                ISNULL(D.FolioPrefix, '') + ISNULL(D.Folio, '') AS DocFolio,
                DT.[Description]           AS Producto,
                DT.UnitPrice               AS Precio,
            
                -- Importe total de la partida (precio unitario + impuestos unitarios) * cantidad
                ROUND(
                    CASE
                        -- IEPS% + IVA
                        WHEN DT.TaxTypeID = 16 THEN (DT.UnitPrice * 1.08) * 1.16
            
                        -- IVA 16% directo
                        WHEN DT.TaxTypeID = 5  THEN (DT.UnitPrice * 1.16)
            
                        -- Sólo IEPS% (sin IVA)
                        WHEN DT.TaxTypeID = 15 THEN (DT.UnitPrice * 1.08)
            
                        -- IEPS fijo + IVA
                        WHEN DT.TaxTypeID = 18 THEN (DT.UnitPrice + (SELECT TaxAmount FROM engTaxItem WHERE TaxItemID = 20)) * 1.16
                        WHEN DT.TaxTypeID = 19 THEN (DT.UnitPrice + (SELECT TaxAmount FROM engTaxItem WHERE TaxItemID = 21)) * 1.16
                        WHEN DT.TaxTypeID = 20 THEN (DT.UnitPrice + (SELECT TaxAmount FROM engTaxItem WHERE TaxItemID = 22)) * 1.16
            
                        -- Sin impuestos
                        ELSE DT.UnitPrice
                    END * DT.Quantity, 2
                ) AS Importe,
            
                D.Total,
                D.Balance                   AS Saldo,
                D.TotalPaid                 AS Cobrado,
                E.OfficialName              AS Cliente,
                CAST(D.CreatedOn AS date)   AS Fecha,
                CONVERT(time, D.CreatedOn)  AS Hora,
                U.UserName                  AS TimbradoPor,
                UC.UserName                 AS Capturista,
                CFD.RFC,
                CFD.MetodoPago,
                CFD.FormaPago,
                CFD.ReceptorUsoCFDI         AS UsoCFDI,
            
                CASE 
                    WHEN CFD.CFDCancelledStatusID = 0 THEN 'Vigente'
                    WHEN CFD.CFDCancelledStatusID = 3 THEN 'Cancelado'
                END AS StatusDocto,
            
                ISNULL(REPLACE(REPLACE(D.Comments, '[', ''), ']', ''), '') AS Comentarios,
            
                CASE 
                    WHEN CFD.CFDStatusID = 3 THEN 'Timbrado'
                    WHEN CFD.CFDStatusID = 0 THEN 'No Enviado'
                END AS StatusTimbrado,
            
                ISNULL(P.FolioPrefix, '') + ISNULL(P.Folio, '') AS PedFolio,
                ISNULL(REPLACE(REPLACE(DT.Comments, '[', ''), ']', ''), '') AS ComentariosPartida
                
            FROM docDocument D
                INNER JOIN docDocumentItem DT ON D.DocumentID = DT.DocumentID
                INNER JOIN dbo.orgBusinessEntity AS E ON D.BusinessEntityID = E.BusinessEntityID
                LEFT OUTER JOIN docDocumentOrderCayal P ON D.OrderDocumentID = P.OrderDocumentID
                LEFT OUTER JOIN dbo.docDocumentCFD AS CFD ON D.DocumentID = CFD.DocumentID
                LEFT OUTER JOIN dbo.engUser AS U ON CFD.UserID = U.UserID
                INNER JOIN dbo.engUser AS uc ON D.CreatedBy = uc.UserID 
            WHERE D.ModuleID = ?
            AND DT.DeletedOn IS NULL
            AND D.DocumentID BETWEEN ?  AND ?
            AND CFD.UserID = ?
            AND D.CancelledOn IS NULL
            ORDER BY DT.DocumentItemID
        """,(self._module_id, minimo, maximo, user_id))

    def _buscar_detalles_documentos_especial(self, module_id, minimo, maximo, user_id):
        return self._base_de_datos.fetchall("""
            SELECT 
                D.DocumentID,
                DT.DocumentItemID,
                DT.Quantity                AS Cantidad,
                DT.Unit                    AS Unidad,
                ISNULL(D.FolioPrefix, '') + ISNULL(D.Folio, '') AS DocFolio,
                DT.[Description]           AS Producto,
                DT.UnitPrice               AS Precio,

                -- Importe total de la partida (precio unitario + impuestos unitarios) * cantidad
                ROUND(
                    CASE
                        -- IEPS% + IVA
                        WHEN DT.TaxTypeID = 16 THEN (DT.UnitPrice * 1.08) * 1.16

                        -- IVA 16% directo
                        WHEN DT.TaxTypeID = 5  THEN (DT.UnitPrice * 1.16)

                        -- Sólo IEPS% (sin IVA)
                        WHEN DT.TaxTypeID = 15 THEN (DT.UnitPrice * 1.08)

                        -- IEPS fijo + IVA
                        WHEN DT.TaxTypeID = 18 THEN (DT.UnitPrice + (SELECT TaxAmount FROM engTaxItem WHERE TaxItemID = 20)) * 1.16
                        WHEN DT.TaxTypeID = 19 THEN (DT.UnitPrice + (SELECT TaxAmount FROM engTaxItem WHERE TaxItemID = 21)) * 1.16
                        WHEN DT.TaxTypeID = 20 THEN (DT.UnitPrice + (SELECT TaxAmount FROM engTaxItem WHERE TaxItemID = 22)) * 1.16

                        -- Sin impuestos
                        ELSE DT.UnitPrice
                    END * DT.Quantity, 2
                ) AS Importe,

                D.Total,
                D.Balance                   AS Saldo,
                D.TotalPaid                 AS Cobrado,
                E.OfficialName              AS Cliente,
                CAST(D.CreatedOn AS date)   AS Fecha,
                CONVERT(time, D.CreatedOn)  AS Hora,
                ISNULL(U.UserName, 'No timbrado')   AS TimbradoPor,
                UC.UserName                 AS Capturista,
                ISNULL(CFD.RFC,'XAXX010101000') RFC,
                CFD.MetodoPago,
                CFD.FormaPago,
                CFD.ReceptorUsoCFDI         AS UsoCFDI,

                CASE 
                    WHEN CFD.CFDCancelledStatusID = 0 THEN 'Vigente'
                    WHEN CFD.CFDCancelledStatusID = 3 THEN 'Cancelado'
                END AS StatusDocto,

                ISNULL(REPLACE(REPLACE(D.Comments, '[', ''), ']', ''), '') AS Comentarios,

                CASE 
                    WHEN CFD.CFDStatusID = 3 THEN 'Timbrado'
                    WHEN CFD.CFDStatusID = 0 THEN 'No Enviado'
                END AS StatusTimbrado,

                ISNULL(P.FolioPrefix, '') + ISNULL(P.Folio, '') AS PedFolio,
                ISNULL(REPLACE(REPLACE(DT.Comments, '[', ''), ']', ''), '') AS ComentariosPartida

            FROM docDocument D
                INNER JOIN docDocumentItem DT ON D.DocumentID = DT.DocumentID
                INNER JOIN dbo.orgBusinessEntity AS E ON D.BusinessEntityID = E.BusinessEntityID
                LEFT OUTER JOIN docDocumentOrderCayal P ON D.OrderDocumentID = P.OrderDocumentID
                LEFT OUTER JOIN dbo.docDocumentCFD AS CFD ON D.DocumentID = CFD.DocumentID
                LEFT OUTER JOIN dbo.engUser AS U ON CFD.UserID = U.UserID
                INNER JOIN dbo.engUser AS uc ON D.CreatedBy = uc.UserID
                INNER JOIN orgCustomer C ON D.BusinessEntityID = C.BusinessEntityID
            WHERE D.ModuleID = ?
            AND DT.DeletedOn IS NULL
            AND D.DocumentID BETWEEN ?  AND ?
            AND D.CreatedBy = ?
            ORDER BY DT.DocumentItemID
        """, (module_id, minimo, maximo, user_id))

    def _obtener_directorio_documentos(self, temporal=False):
        """
        Devuelve la ruta al directorio de documentos del usuario.
        Si temporal=True y el sistema es Windows, devuelve la carpeta temporal (%TEMP%).
        """
        # Si se solicita la carpeta temporal del sistema
        if temporal:
            return tempfile.gettempdir()

        sistema = platform.system()

        if sistema == "Windows":
            # Ejemplo: C:\Users\TuUsuario\Documents
            documentos = os.path.join(os.path.expanduser("~"), "Documents")

        elif sistema == "Darwin":
            # macOS → /Users/TuUsuario/Documents
            documentos = os.path.join(os.path.expanduser("~"), "Documents")

        else:
            # Linux u otros sistemas → /home/usuario/Documentos o Documents
            posibles = [
                os.path.join(os.path.expanduser("~"), "Documents"),
                os.path.join(os.path.expanduser("~"), "Documentos")
            ]
            documentos = next((ruta for ruta in posibles if os.path.exists(ruta)), posibles[0])

        return documentos

    def _validar_impresion_previa(self):
        usuario_seleccionado = self._ventanas.obtener_input_componente('cbx_cajeros')
        uid_sel = self._resolver_user_id(usuario_seleccionado)
        if uid_sel is None:
            self._ventanas.mostrar_mensaje('No se pudo resolver el UserID del usuario seleccionado.')
            return False

        # Admin/grupos privilegiados: imprime todo el rango del día
        if self._user_group_id in (1, 26, 6):
            self._folios_individuales_usuario_por_fecha(uid_sel)  # fija _minimo/_maximo del día
            return True

        return True
