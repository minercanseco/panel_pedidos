
from capturar_documento.herramientas.verificador.informacion_producto import InformacionProducto
from capturar_documento.herramientas.verificador.mapas_producto import PintorProductoCarnico
from capturar_documento.herramientas.verificador.modelo_verificador import ModeloVerificador

import os
import tkinter as tk

import pyperclip
from PIL import Image, ImageTk

class ControladorVerificador:
    VALOR_SELECCIONE = 'Seleccione'

    BASE = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'mapas'
    )

    MAPA_CERDO = os.path.join(
        BASE,
        'mapa_cerdo.png'
    )

    MAPA_RES_LOCAL = os.path.join(
        BASE,
        'mapa_res.png'
    )

    MAPA_POLLO = os.path.join(
        BASE,
        'mapa_pollo.png'
    )

    MAPAS = {
        'CERDO': MAPA_CERDO,
        'RES LOCAL': MAPA_RES_LOCAL,
        'POLLO': MAPA_POLLO
    }


    def __init__(
            self,
            interfaz,
            parametros,
            modelo=None
    ):
        self._imagen_mapa_tk = None
        self._imagen_mapa_original = None
        self._tamano_actual_mapa = None
        self._after_redimension_mapa = None
        self._widget_mapa_configurado = None
        self._bind_redimension_mapa = None

        self._product_id_seleccionado = 0
        self._category_1 = ''

        self._interfaz = interfaz
        self._parametros = parametros

        self._ventanas = interfaz.ventanas
        self._master = interfaz.master

        self._modelo = (
            modelo
            if modelo is not None
            else ModeloVerificador(parametros)
        )

        self._cargar_listas_precios()
        self._inyectar_funciones_barra_herramienta()
        self._cargar_eventos()

    # ------------------------------------------------------------------
    # Inicialización
    # ------------------------------------------------------------------

    def _cargar_eventos(self):
        eventos = {
            'tbx_buscar': (
                lambda event:
                self._buscar_info_producto()
            ),

            'cbx_resultado': (
                lambda event:
                self._seleccionar_producto()
            ),

            'cbx_lista': (
                lambda event:
                self._seleccionar_producto()
            ),

            'tbx_cantidad': (
                lambda event:
                self._calcular_cantidad_producto()
            )
        }

        self._ventanas.cargar_eventos(eventos)

    def _cargar_listas_precios(self):
        listas = self._modelo.nombres_listas_precios

        self._ventanas.rellenar_cbx(
            'cbx_lista',
            listas,
            sin_seleccione=True
        )

    # ------------------------------------------------------------------
    # Búsqueda
    # ------------------------------------------------------------------

    def _buscar_info_producto(self):
        termino = self._ventanas.obtener_input_componente(
            'tbx_buscar'
        )

        buscar_linea = (
            self._ventanas.obtener_input_componente(
                'chk_linea'
            )
        )

        valido, mensaje = (
            self._modelo.validar_termino_busqueda(termino)
        )

        if not valido:
            self._ventanas.mostrar_mensaje(mensaje)
            return

        if self._modelo.es_busqueda_repetida(
                termino,
                buscar_linea
        ):
            return

        productos = self._modelo.buscar_productos(
            termino,
            buscar_linea
        )

        if not productos:
            self._interfaz.configurar_posicion_frames(
                'inicial'
            )

            self._ventanas.mostrar_mensaje(
                'El término de búsqueda no arrojó '
                'ningún resultado.'
            )

            return

        self._rellenar_cbx_resultado()

        if self._modelo.utilerias.es_cantidad(termino):
            self._ventanas.limpiar_componentes(
                'tbx_buscar'
            )

    def _rellenar_cbx_resultado(self):
        productos = self._modelo.nombres_productos

        if not productos:
            return

        if len(productos) == 1:
            self._ventanas.rellenar_cbx(
                'cbx_resultado',
                productos,
                sin_seleccione=True
            )

            self._seleccionar_producto(
                productos[0]
            )

            return

        self._ventanas.rellenar_cbx(
            'cbx_resultado',
            productos
        )

    # ------------------------------------------------------------------
    # Selección de producto
    # ------------------------------------------------------------------

    def _seleccionar_producto(self, seleccion=None):
        if seleccion is None:
            seleccion = (
                self._ventanas.obtener_input_componente(
                    'cbx_resultado'
                )
            )

        if (
                not seleccion
                or seleccion == self.VALOR_SELECCIONE
        ):
            self._ocultar_mapa_producto()

            self._interfaz.configurar_posicion_frames(
                'inicial'
            )
            return None

        # Ocultar el mapa del producto anterior
        self._ocultar_mapa_producto()

        informacion = self._procesar_producto(seleccion)

        if not informacion:
            return

        if informacion['ofertado']:
            self._interfaz.configurar_posicion_frames(
                'oferta'
            )
        else:
            self._interfaz.configurar_posicion_frames(
                'producto'
            )

        self._mostrar_informacion_producto(informacion)
        self._product_id_seleccionado = informacion.get('ProductID', 0)
        self._category_1 = str(
            informacion.get('Category1', '')
        ).strip().upper()

        self._mapa_producto()

        return informacion

    def _procesar_producto(self, seleccion):
        " a partir de una seleccion valida del combo box regresa la informacion del producto para ser presentada"

        product_id = self._modelo.obtener_product_id(
            seleccion
        )

        if product_id is None:
            self._ventanas.mostrar_mensaje(
                'No se encontró el producto seleccionado.'
            )
            return None

        customer_type_id = (
            self._obtener_customer_type_id_seleccionado()
        )

        if customer_type_id is None:
            return None

        try:
            informacion = (
                self._modelo.obtener_informacion_producto(
                    product_id,
                    customer_type_id
                )
            )
        except ValueError as error:
            self._ventanas.mostrar_mensaje(str(error))
            return None

        return informacion


    def _ocultar_mapa_producto(self):
        """
        Limpia el mapa mostrado y reinicia las referencias relacionadas
        con el redimensionamiento.
        """
        lbl_mapa = self._ventanas.componentes_forma.get(
            'lbl_mapa_producto'
        )

        after_pendiente = getattr(
            self,
            '_after_redimension_mapa',
            None
        )

        if after_pendiente and lbl_mapa is not None:
            try:
                lbl_mapa.after_cancel(after_pendiente)
            except tk.TclError:
                pass

        self._after_redimension_mapa = None
        self._tamano_actual_mapa = None
        self._imagen_mapa_original = None
        self._imagen_mapa_tk = None

        if lbl_mapa is None:
            return

        try:
            lbl_mapa.configure(
                image='',
                text=''
            )
        except tk.TclError:
            pass

    def _obtener_customer_type_id_seleccionado(self):
        lista = self._ventanas.obtener_input_componente(
            'cbx_lista'
        )

        if (
                not lista
                or lista == self.VALOR_SELECCIONE
        ):
            self._ventanas.mostrar_mensaje(
                'Debe seleccionar una lista de precios.'
            )
            return None

        customer_type_id = (
            self._modelo.obtener_customer_type_id(lista)
        )

        if customer_type_id is None:
            self._ventanas.mostrar_mensaje(
                'No se encontró la lista de precios '
                'seleccionada.'
            )

        return customer_type_id

    # ------------------------------------------------------------------
    # Presentación
    # ------------------------------------------------------------------

    def _mostrar_informacion_producto(self, informacion):
        product_id = informacion['ProductID']

        existencia = informacion.get(
            'existencia',
            {}
        )

        texto_existencia = '{0} {1}'.format(
            existencia.get('cantidad', 0),
            existencia.get('unidad', '')
        )

        precio_regular = (
            self._modelo.formatear_precio_producto(
                product_id,
                informacion['total']
            )
        )

        valores = {
            'lbl_producto': informacion.get(
                'ProductName',
                ''
            ),

            'lbl_clave': 'Clave {0}'.format(
                informacion.get('ProductKey', '')
            ),

            'lbl_precio': precio_regular,
            'lbl_existencia': texto_existencia
        }

        for componente, valor in valores.items():
            self._actualizar_etiqueta(
                componente,
                valor
            )

        if informacion['ofertado']:
            self._mostrar_informacion_oferta(
                informacion
            )

    def _mostrar_informacion_oferta(self, informacion):
        precio_oferta = (
            self._modelo.formatear_precio_producto(
                informacion['ProductID'],
                informacion['total_oferta']
            )
        )

        tipo_oferta = informacion.get(
            'tipo_oferta',
            ''
        )

        vigencia_inicio = informacion.get(
            'vigencia_inicio',
            ''
        )

        vigencia_termino = informacion.get(
            'vigencia_termino',
            ''
        )

        if str(tipo_oferta).lower() == 'semanal':
            texto_vigencia = (
                'Válida del {0} al {1}'.format(
                    vigencia_inicio,
                    vigencia_termino
                )
            )
        else:
            texto_vigencia = (
                'Oferta válida hasta el {0}'.format(
                    vigencia_termino
                )
            )

        valores = {
            'lbl_tipo_oferta': (
                'Tipo de oferta - {0}'.format(
                    tipo_oferta
                )
            ),

            'lbl_validez_oferta': texto_vigencia,
            'lbl_precio_oferta': precio_oferta
        }

        for componente, valor in valores.items():
            self._actualizar_etiqueta(
                componente,
                valor
            )

    def _actualizar_etiqueta(
            self,
            nombre_componente,
            valor
    ):
        componente = (
            self._ventanas.componentes_forma[
                nombre_componente
            ]
        )

        if 'precio' in nombre_componente:
            componente.config(
                font=('consolas', 25, 'bold'),
                text=valor
            )
        else:
            componente.config(text=valor)

    # ------------------------------------------------------------------
    # Ofertas
    # ------------------------------------------------------------------

    def _cargar_ofertas_en_cbx_resultado(self):
        nombres = (
            self._modelo.nombres_productos_ofertados
        )

        if not nombres:
            self._ventanas.mostrar_mensaje(
                'No se encontraron productos en oferta.'
            )
            return

        productos = (
            self._modelo.cargar_productos_en_oferta()
        )

        if not productos:
            self._ventanas.mostrar_mensaje(
                'No fue posible recuperar la información '
                'de los productos ofertados.'
            )
            return

        nombres_disponibles = (
            self._modelo.nombres_productos
        )

        cbx_resultado = (
            self._ventanas.componentes_forma[
                'cbx_resultado'
            ]
        )

        cbx_resultado['values'] = nombres_disponibles
        cbx_resultado.set(nombres_disponibles[0])

        self._seleccionar_producto(
            nombres_disponibles[0]
        )

    # ------------------------------------------------------------------
    # Información adicional
    # ------------------------------------------------------------------

    def _llamar_informacion_producto(self):
        seleccion = (
            self._ventanas.obtener_input_componente(
                'cbx_resultado'
            )
        )

        if (
                not seleccion
                or seleccion == self.VALOR_SELECCIONE
        ):
            self._ventanas.mostrar_mensaje(
                'Debe seleccionar un producto.'
            )
            return

        product_id = self._modelo.obtener_product_id(
            seleccion
        )

        if product_id is None:
            self._ventanas.mostrar_mensaje(
                'No se encontró el producto seleccionado.'
            )
            return

        informacion = (
            self._modelo.buscar_informacion_usos_producto(
                product_id
            )
        )

        if not informacion:
            self._ventanas.mostrar_mensaje(
                'No se encontró información de uso '
                'relacionada con el producto seleccionado.'
            )
            return

        ventana = (
            self._ventanas.crear_popup_ttkbootstrap()
        )

        InformacionProducto(
            ventana,
            informacion[0]
        )

        ventana.wait_window()

    # ------------------------------------------------------------------
    # Cálculos
    # ------------------------------------------------------------------

    def _calcular_cantidad_producto(self):
        seleccion = (
            self._ventanas.obtener_input_componente(
                'cbx_resultado'
            )
        )

        if (
                not seleccion
                or seleccion == self.VALOR_SELECCIONE
        ):
            return

        cantidad_ingresada = (
            self._ventanas.obtener_input_componente(
                'tbx_cantidad'
            )
        )

        valido, cantidad, mensaje = (
            self._modelo.validar_cantidad(
                cantidad_ingresada
            )
        )

        if not valido:
            self._ventanas.mostrar_mensaje(mensaje)
            return

        product_id = self._modelo.obtener_product_id(
            seleccion
        )

        customer_type_id = (
            self._obtener_customer_type_id_seleccionado()
        )

        if (
                product_id is None
                or customer_type_id is None
        ):
            return

        calcular_por_monto = bool(
            self._ventanas.obtener_input_componente(
                'chk_monto'
            )
        )

        try:
            resultado = self._modelo.calcular_importes(
                product_id=product_id,
                customer_type_id=customer_type_id,
                cantidad=cantidad,
                calcular_por_monto=calcular_por_monto
            )
        except ValueError as error:
            self._ventanas.mostrar_mensaje(str(error))
            return

        texto_regular = (
            self._modelo.formatear_detalle_importe(
                resultado['regular']
            )
        )

        self._ventanas.insertar_input_componente(
            'lbl_precio',
            texto_regular
        )

        if resultado['ofertado']:
            texto_oferta = (
                self._modelo.formatear_detalle_importe(
                    resultado['oferta']
                )
            )

            self._ventanas.insertar_input_componente(
                'lbl_precio_oferta',
                texto_oferta
            )

    # ------------------------------------------------------------------
    # Copiar
    # ------------------------------------------------------------------


    def _copiar_precio_producto(self):
        seleccion = (
            self._ventanas.obtener_input_componente(
                'cbx_resultado'
            )
        )

        if not seleccion:
            self._ventanas.mostrar_mensaje(
                'Debe buscar por lo menos un producto.'
            )
            return

        if (
                seleccion == self.VALOR_SELECCIONE

        ):
            self._ventanas.mostrar_mensaje(
                'Debe seleccionar un producto.'
            )
            return

        texto = self._procesar_valores_etiquetas(copiar_todo=False
        )

        if not texto:
            return

        pyperclip.copy(texto)
        self._master.iconify()

    def _copiar_precios_multiples_productos(self):
        """
        Recupera y copia los precios de todos los productos disponibles en
        cbx_resultado sin cambiar la selección, etiquetas, mapa ni distribución
        visible de la interfaz.
        """
        cbx_resultado = self._ventanas.componentes_forma.get(
            'cbx_resultado'
        )

        if cbx_resultado is None:
            self._ventanas.mostrar_mensaje(
                'No se encontró el componente de resultados.'
            )
            return

        productos = [
            seleccion
            for seleccion in cbx_resultado['values']
            if seleccion
               and seleccion != self.VALOR_SELECCIONE
        ]

        if not productos:
            self._ventanas.mostrar_mensaje(
                'Debe buscar por lo menos un producto.'
            )
            return

        customer_type_id = (
            self._obtener_customer_type_id_seleccionado()
        )

        if customer_type_id is None:
            return

        textos = []
        productos_omitidos = []

        for seleccion in productos:
            informacion = (
                self._obtener_informacion_producto_para_copiar(
                    seleccion=seleccion,
                    customer_type_id=customer_type_id
                )
            )

            if informacion is None:
                productos_omitidos.append(str(seleccion))
                continue

            texto = self._generar_texto_desde_informacion(
                informacion
            )

            if texto:
                textos.append(texto)

        if not textos:
            self._ventanas.mostrar_mensaje(
                'No fue posible recuperar la información '
                'de los productos encontrados.'
            )
            return

        pyperclip.copy(
            '\n\n'.join(textos)
        )

        if productos_omitidos:
            print(
                'No fue posible copiar los siguientes productos: {0}'.format(
                    ', '.join(productos_omitidos)
                )
            )

        self._master.iconify()

    def _obtener_informacion_producto_para_copiar(
            self,
            seleccion,
            customer_type_id
    ):
        """
        Recupera la información de un producto sin modificar ningún componente
        de la interfaz.
        """
        product_id = self._modelo.obtener_product_id(
            seleccion
        )

        if product_id is None:
            return None

        try:
            informacion = (
                self._modelo.obtener_informacion_producto(
                    product_id,
                    customer_type_id
                )
            )
        except ValueError as error:
            print(
                'No fue posible recuperar {0}: {1}'.format(
                    seleccion,
                    error
                )
            )
            return None
        except Exception as error:
            print(
                'Error al recuperar {0}: {1}'.format(
                    seleccion,
                    error
                )
            )
            return None

        return informacion

    def _generar_texto_desde_informacion(
            self,
            informacion
    ):
        """
        Genera el texto copiable directamente desde la información del modelo,
        sin modificar la selección, las etiquetas, el mapa ni la vista.
        """
        if not informacion:
            return ''

        product_id = informacion.get(
            'ProductID'
        )

        producto = str(
            informacion.get(
                'ProductName',
                ''
            )
        ).strip()

        linea = str(
            informacion.get(
                'Category1',
                ''
            )
        ).strip()

        icono_linea = (
            self._modelo.utilerias.resolver_iconos_lineas(
                linea
            )
        )

        precio_regular = (
            self._modelo.formatear_precio_producto(
                product_id,
                informacion.get(
                    'total',
                    0
                )
            )
        )

        if informacion.get('ofertado'):
            precio_oferta = (
                self._modelo.formatear_precio_producto(
                    product_id,
                    informacion.get(
                        'total_oferta',
                        0
                    )
                )
            )

            tipo_oferta = str(
                informacion.get(
                    'tipo_oferta',
                    ''
                )
            ).strip()

            vigencia_inicio = informacion.get(
                'vigencia_inicio',
                ''
            )

            vigencia_termino = informacion.get(
                'vigencia_termino',
                ''
            )

            if tipo_oferta.lower() == 'semanal':
                texto_vigencia = (
                    'Válida del {0} al {1}'.format(
                        vigencia_inicio,
                        vigencia_termino
                    )
                )
            else:
                texto_vigencia = (
                    'Oferta válida hasta el {0}'.format(
                        vigencia_termino
                    )
                )

            return (
                '{icono} Producto: {producto}\n'
                '🏷️ Tipo de oferta: {tipo_oferta}\n'
                '🔥 Precio oferta: {precio_oferta}\n'
                '💰 Precio regular: {precio_regular}\n'
                '📅 {texto_vigencia} o hasta agotar existencias.'
            ).format(
                icono=icono_linea,
                producto=producto,
                tipo_oferta=tipo_oferta,
                precio_oferta=precio_oferta,
                precio_regular=precio_regular,
                texto_vigencia=texto_vigencia
            )

        return (
            '{icono} Producto: {producto}\n'
            '💰 Precio: {precio_regular}'
        ).format(
            icono=icono_linea,
            producto=producto,
            precio_regular=precio_regular
        )


    # ------------------------------------------------------------------
    # Mapas
    # ------------------------------------------------------------------

    def _mapa_producto(self):


        # Ocultar el mapa y liberar el espacio mientras se valida el producto.
        self._interfaz.ocultar_mapa()

        if not self._product_id_seleccionado:
            print('sin productid')
            return

        try:
            datos = self._modelo.obtener_producto_mapa_carnico(
                self._product_id_seleccionado
            )
        except Exception as error:
            print(
                'No fue posible obtener el mapa del producto.\n\n{0}'.format(
                    error
                )
            )
            return

        if not datos:
            print(
                'El producto no tiene información de mapa relacionada.'
            )
            return

        producto = datos.get('producto') or {}
        zonas = datos.get('zonas') or []

        categoria = str(
            producto.get('Category1', '')
        ).strip().upper()

        ruta_imagen = self.MAPAS.get(
            categoria,
            ''
        )

        if not ruta_imagen:
            print(
                'No existe un mapa configurado para la categoría: {0}'.format(
                    categoria or 'SIN CATEGORÍA'
                )
            )
            return

        if not os.path.isfile(ruta_imagen):
            print(
                'No se encontró el archivo del mapa:\n{0}'.format(
                    ruta_imagen
                )
            )
            return

        lbl_mapa = self._ventanas.componentes_forma.get(
            'lbl_mapa_producto'
        )

        if lbl_mapa is None:
            self._ventanas.mostrar_mensaje(
                'No se encontró el componente lbl_mapa_producto.'
            )
            return

        try:
            if not lbl_mapa.winfo_exists():
                return
        except tk.TclError:
            return

        try:
            pintor = PintorProductoCarnico(
                imagen=ruta_imagen,
                producto=producto,
                zonas=zonas
            )

            self._imagen_mapa_original = pintor.pintar(
                color_relleno=(0, 220, 255, 105),
                color_contorno=(0, 60, 180, 255),
                ancho_contorno=6
            )

        except Exception as error:
            print(
                'No fue posible generar la imagen del mapa.\n\n{0}'.format(
                    error
                )
            )
            return

        if self._imagen_mapa_original is None:
            print(
                'El pintor no devolvió una imagen válida.'
            )
            return

        # Mostrar el frame únicamente cuando ya existe una imagen válida.
        self._interfaz.mostrar_mapa()

        # Fuerza la reconstrucción de PhotoImage aunque el tamaño sea igual
        # al del producto anterior.
        self._tamano_actual_mapa = None

        after_pendiente = getattr(
            self,
            '_after_redimension_mapa',
            None
        )

        if after_pendiente:
            try:
                lbl_mapa.after_cancel(after_pendiente)
            except tk.TclError:
                pass

            self._after_redimension_mapa = None

        widget_anterior = getattr(
            self,
            '_widget_mapa_configurado',
            None
        )

        if widget_anterior is not lbl_mapa:
            if widget_anterior is not None:
                bind_anterior = getattr(
                    self,
                    '_bind_redimension_mapa',
                    None
                )

                if bind_anterior:
                    try:
                        widget_anterior.unbind(
                            '<Configure>',
                            bind_anterior
                        )
                    except tk.TclError:
                        pass

            self._bind_redimension_mapa = lbl_mapa.bind(
                '<Configure>',
                self._redimensionar_mapa_producto,
                add='+'
            )

            self._widget_mapa_configurado = lbl_mapa

        try:
            lbl_mapa.update_idletasks()
        except tk.TclError:
            self._interfaz.ocultar_mapa()
            return

        self._after_redimension_mapa = lbl_mapa.after(
            10,
            lambda: self._redimensionar_mapa_producto(
                type(
                    'EventoMapa',
                    (),
                    {
                        'widget': lbl_mapa
                    }
                )()
            )
        )

    def _redimensionar_mapa_producto(self, evento):
        imagen_original = getattr(
            self,
            '_imagen_mapa_original',
            None
        )

        if imagen_original is None:
            return

        lbl_mapa = getattr(
            evento,
            'widget',
            None
        )

        if lbl_mapa is None:
            return

        try:
            if not lbl_mapa.winfo_exists():
                return
        except tk.TclError:
            return

        after_pendiente = getattr(
            self,
            '_after_redimension_mapa',
            None
        )

        if after_pendiente:
            try:
                lbl_mapa.after_cancel(after_pendiente)
            except tk.TclError:
                pass

        def aplicar_redimension():
            try:
                if not lbl_mapa.winfo_exists():
                    return

                ancho_widget = lbl_mapa.winfo_width()
                alto_widget = lbl_mapa.winfo_height()

            except tk.TclError:
                return

            # Cuando el label todavía no está visible, puede reportar 1x1.
            if ancho_widget <= 1 or alto_widget <= 1:
                self._after_redimension_mapa = lbl_mapa.after(
                    100,
                    aplicar_redimension
                )
                return

            margen = 20

            ancho_disponible = max(
                1,
                ancho_widget - margen
            )

            alto_disponible = max(
                1,
                alto_widget - margen
            )

            ancho_original, alto_original = (
                imagen_original.size
            )

            if ancho_original <= 0 or alto_original <= 0:
                return

            escala = min(
                ancho_disponible / float(ancho_original),
                alto_disponible / float(alto_original)
            )

            # Evita ampliar excesivamente imágenes pequeñas.
            escala = min(
                escala,
                1.0
            )

            nuevo_tamaño = (
                max(1, int(ancho_original * escala)),
                max(1, int(alto_original * escala))
            )

            tamaño_anterior = getattr(
                self,
                '_tamano_actual_mapa',
                None
            )

            # Solo se omite si el tamaño es igual y el label aún conserva
            # una imagen configurada.
            tiene_imagen = bool(
                lbl_mapa.cget('image')
            )

            if (
                    tamaño_anterior == nuevo_tamaño
                    and tiene_imagen
                    and self._imagen_mapa_tk is not None
            ):
                self._after_redimension_mapa = None
                return

            try:
                imagen_redimensionada = imagen_original.resize(
                    nuevo_tamaño,
                    Image.Resampling.LANCZOS
                )

                self._imagen_mapa_tk = ImageTk.PhotoImage(
                    imagen_redimensionada,
                    master=lbl_mapa
                )

                lbl_mapa.configure(
                    image=self._imagen_mapa_tk,
                    text=''
                )

                # Referencia adicional sobre el propio widget.
                lbl_mapa.image = self._imagen_mapa_tk

                self._tamano_actual_mapa = nuevo_tamaño
                self._after_redimension_mapa = None

            except (tk.TclError, ValueError) as error:
                self._after_redimension_mapa = None

                self._ventanas.mostrar_mensaje(
                    'No fue posible mostrar el mapa.\n\n{0}'.format(
                        error
                    )
                )

        self._after_redimension_mapa = lbl_mapa.after(
            80,
            aplicar_redimension
        )

    def _procesar_valores_etiquetas(
            self,
            copiar_todo
    ):
        if copiar_todo:
            return self._generar_texto_todos_productos()

        seleccion = (
            self._ventanas.obtener_input_componente(
                'cbx_resultado'
            )
        )

        ofertado = (
            self._modelo.producto_esta_ofertado(
                seleccion
            )
        )

        return self._generar_texto_producto(
            ofertado
        )

    def _generar_texto_todos_productos(self):
        cbx_resultado = (
            self._ventanas.componentes_forma[
                'cbx_resultado'
            ]
        )

        productos = cbx_resultado['values']
        textos = []

        for seleccion in productos:
            if seleccion == self.VALOR_SELECCIONE:
                continue

            informacion = self._seleccionar_producto(
                seleccion
            )

            if informacion is None:
                continue

            texto = self._generar_texto_producto(
                informacion['ofertado']
            )

            textos.append(texto)

        return '\n\n'.join(textos)

    def _generar_texto_producto(self, ofertado):
        valores = self._obtener_valores_etiquetas()

        icono_linea = (
            self._modelo.utilerias.resolver_iconos_lineas(
                self._category_1
            )
        )

        if ofertado:
            return (
                '{icono} Producto: {producto}\n'
                '🏷️ {tipo_oferta}\n'
                '🔥 Precio oferta: {precio_oferta}\n'
                '💰 Precio regular: {precio}\n'
                '📅 {validez_oferta} o hasta agotar existencias.'
            ).format(
                icono=icono_linea,
                producto=valores.get(
                    'producto',
                    ''
                ),
                tipo_oferta=valores.get(
                    'tipo_oferta',
                    ''
                ),
                precio_oferta=valores.get(
                    'precio_oferta',
                    ''
                ),
                precio=valores.get(
                    'precio',
                    ''
                ),
                validez_oferta=valores.get(
                    'validez_oferta',
                    ''
                )
            )

        return (
            '{icono} Producto: {producto}\n'
            '💰 Precio: {precio}'
        ).format(
            icono=icono_linea,
            producto=valores.get(
                'producto',
                ''
            ),
            precio=valores.get(
                'precio',
                ''
            )
        )

    def _obtener_valores_etiquetas(self):
        valores = {}

        for nombre, componente in (
                self._ventanas.componentes_forma.items()
        ):
            if not nombre.startswith('lbl_'):
                continue

            clave = nombre[4:]
            valores[clave] = componente.cget('text')

        return valores



    def _inyectar_funciones_barra_herramienta(self):
        """
        Inyecta las acciones del controlador en la barra declarada por la
        interfaz y crea visualmente la toolbar.

        Ajusta únicamente los tres nombres de métodos del lado derecho cuando
        en tu controlador actual tengan una denominación distinta.
         'btn_ofertas': (
                self._cargar_ofertas_en_cbx_resultado
            ),

            'btn_info': (
                self._llamar_informacion_producto
            ),

            'tbx_cantidad': (
                lambda event:
                self._calcular_cantidad_producto()
            ),

            'btn_copiar': (
                self._copiar_precio_producto
            )
        """
        funciones = {
            'copiar': self._copiar_precio_producto,
            'copiar_todo': self._copiar_precios_multiples_productos,
            'ofertas': self._cargar_ofertas_en_cbx_resultado,
            'informacion': self._llamar_informacion_producto,
        }

        for herramienta in self._interfaz.barra_herramientas:
            nombre = herramienta['nombre']
            herramienta['comando'] = funciones.get(nombre)

        herramientas_sin_funcion = [
            herramienta['nombre']
            for herramienta in self._interfaz.barra_herramientas
            if herramienta['comando'] is None
        ]

        if herramientas_sin_funcion:
            raise ValueError(
                'No se asignó función a las herramientas: {0}'.format(
                    ', '.join(herramientas_sin_funcion)
                )
            )

        self._interfaz.elementos_barra_herramientas = (
            self._ventanas.crear_barra_herramientas(
                self._interfaz.barra_herramientas,
                'frame_botones'
            )
        )

        self._interfaz.hotkeys_barra_herramientas = (
            self._interfaz.elementos_barra_herramientas[1]
        )

        self._interfaz.etiquetas_barra_herramientas = (
            self._interfaz.elementos_barra_herramientas[2]
        )
