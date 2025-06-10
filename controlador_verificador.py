import pyperclip
from cayal.util import Utilerias
from cayal.comandos_base_datos import ComandosBaseDatos

from informacion_producto import InformacionProducto


class ControladorVerificador:
    def __init__(self, interfaz, parametros):
        self._parametros = parametros

        # instancias a utilizar
        self._interfaz =  interfaz
        self._parametros = parametros
        self._base_de_datos = ComandosBaseDatos(self._parametros.cadena_conexion)
        self._utilerias = Utilerias()
        self._ventanas = interfaz.ventanas
        self._master = interfaz.master

        self._consulta_ofertas = []

        # variables globales
        self._consulta_productos = []
        self._consulta_productos_ofertados = []
        self._consulta_precios_producto = []

        self._consulta_lista_de_precios = []
        self._productos_ofertados_ids = []
        self._productos_ofertados_nombres = []
        self._termino_buscado = ''
        self._buscar_linea = 0

        self._EQUIVALENCIA_UNIDADES = {
            'PIEZA': 'Pz',
            'KILO': 'Kg',
            'LITRO': 'Lt',
            'PAQUETE': 'Pq'
        }
        self._PRODUCTOS_ESPECIALES = {
            1162: ('Pz', 15),  # Huevo media reja
            1165: ('Cj', 360),  # Huevo caja
            1166: ('Rj', 30)  # Huevo reja

        }

        self._rellenar_cbx_listas()
        self._cargar_eventos()
        self._buscar_productos_ofertados()

    def _cargar_eventos(self):
        eventos = {
            'tbx_buscar': lambda event: self._buscar_info_producto(),
            'cbx_resultado': lambda event: self._seleccionar_producto(),
            'cbx_lista': lambda event: self._seleccionar_producto(),
            'btn_ofertas': self._cargar_ofertas_en_cbx_resultado,
            'btn_info': self._llamar_informacion_producto,
            'tbx_cantidad': lambda event: self._calcular_cantidad_producto(),
            'btn_copiar': self._copiar_precio_producto
        }
        self._ventanas.cargar_eventos(eventos)

    def _buscar_productos_ofertados(self):

        consulta = self._base_de_datos.buscar_productos_en_oferta()
        self._productos_ofertados_ids = [producto['ProductID'] for producto in consulta]
        self._productos_ofertados_ids = list(set(self._productos_ofertados_ids))


        self._consulta_productos_ofertados = consulta

    def _buscar_listas_de_precios(self):
        self._consulta_lista_de_precios = self._base_de_datos.fetchall("""
            SELECT CustomerTypeID, CustomerTypeName 
            FROM orgCustomerType
            WHERE CustomerTypeID BETWEEN 2 AND 10 
        """,())

    def _rellenar_cbx_listas(self):
        self._buscar_listas_de_precios()
        listas =  [lista['CustomerTypeName'] for lista in self._consulta_lista_de_precios]

        self._ventanas.rellenar_cbx('cbx_lista', listas, sin_seleccione=True)

    def _buscar_info_producto(self):

        termino_buscado = self._ventanas.obtener_input_componente('tbx_buscar')

        # busca por linea de productos si el control esta habilitado
        buscar_linea = self._ventanas.obtener_input_componente('chk_linea')

        if not self._validar_termino_buscado(termino_buscado):
            return

        if self._termino_buscado == termino_buscado and self._buscar_linea == buscar_linea:
            return

        # evita la consulta de innecesaria a la bd
        self._termino_buscado = termino_buscado
        self._buscar_linea = buscar_linea

        if buscar_linea == 1:
            consulta = self._base_de_datos.buscar_product_id_linea(termino_buscado)
        else:
            consulta = self._base_de_datos.buscar_product_id_termino(termino_buscado)

        if not consulta:
            self._ventanas.mostrar_mensaje('El término de búsqueda no arrojó ningún resultado')
            return
        else:
            productos = [producto['ProductID'] for producto in consulta]
            consulta_productos = self._base_de_datos.buscar_info_productos(productos)

            self._consulta_productos = consulta_productos
            self._rellenar_cbx_resultado()

        if self._utilerias.es_cantidad(termino_buscado):
            self._ventanas.limpiar_componentes('tbx_buscar')

    def _validar_termino_buscado(self, termino_buscado):

        if not termino_buscado:
            self._ventanas.mostrar_mensaje('Debe introducir un término a buscar.')
            return False

        termino_buscado = str(termino_buscado)
        termino_buscado = termino_buscado.strip()

        if len(termino_buscado) < 4:
            self._ventanas.mostrar_mensaje('Debe abundar en el término a buscar.')
            return False

        return True

    def _rellenar_cbx_resultado(self):

        productos = [producto['ProductName'] for producto in self._consulta_productos]

        if not productos:
            return

        if len(productos) == 1:
            self._ventanas.rellenar_cbx('cbx_resultado', productos, sin_seleccione=True)
            self._seleccionar_producto()
        else:
            self._ventanas.rellenar_cbx('cbx_resultado', productos)

    def _seleccionar_producto(self, seleccion = None):

        if not seleccion:
            seleccion = self._ventanas.obtener_input_componente('cbx_resultado')

        if seleccion == 'Seleccione':
            self._interfaz.configurar_posicion_frames()

        if seleccion != 'Seleccione':

            product_id = self._obtener_product_id_seleccionado(seleccion)

            # busca la correspondencia de la lista de precios seleccionadas
            customer_type_id = self._obtener_customer_type_id_seleccionado()

            precios = self._obtener_precio_producto_seleccionado(customer_type_id, product_id)
            ofertado = precios['ofertado']

            info_producto = self._consolidar_info_productos_seleccionado(product_id, precios)
            self._interfaz.configurar_posicion_frames('oferta') if ofertado else self._interfaz.configurar_posicion_frames('producto')

            self._cargar_informacion_producto_seleccionado_forma(info_producto, ofertado)

    def _obtener_product_id_seleccionado(self, seleccion):
        return [producto['ProductID'] for producto in self._consulta_productos
                          if producto['ProductName'] == seleccion][0]

    def _obtener_customer_type_id_seleccionado(self):
        lista_seleccionada = self._ventanas.obtener_input_componente('cbx_lista')

        # busca la correspondencia de la lista de precios seleccionadas
        customer_type_id = [listas['CustomerTypeID'] for listas in self._consulta_lista_de_precios
                            if listas['CustomerTypeName'] == lista_seleccionada][0]
        return customer_type_id

    def _obtener_precio_producto_seleccionado(self, customer_type_id, product_id):

        ofertado_en_lista = [producto for producto in self._consulta_productos_ofertados
                             if producto['ProductID'] == product_id and customer_type_id == producto['Lista']]

        ofertado = True if ofertado_en_lista else False

        if not ofertado:

            self._consulta_precios_producto = self._base_de_datos.buscar_precios_producto(product_id)

            precio = [precios['SalePrice'] for precios in self._consulta_precios_producto
                      if precios['CustomerTypeID'] == customer_type_id][0]

            return {'ofertado': ofertado , 'precio': precio}

        if ofertado:
            info_producto_ofertado = ofertado_en_lista[0]

            precio_previo = info_producto_ofertado['SalePriceBefore']
            precio_oferta = info_producto_ofertado['SalePrice']
            vigencia_inicio = str(info_producto_ofertado['FechaAlta'])
            vigencia_termino = str(info_producto_ofertado['FechaBaja'])
            tipo_oferta = info_producto_ofertado['Tipo']

            return {'ofertado': ofertado,
                    'precio_previo': precio_previo,
                    'precio_oferta': precio_oferta,
                    'vigencia_inicio' : vigencia_inicio[0:10],
                    'vigencia_termino' : vigencia_termino[0:10],
                    'tipo_oferta': tipo_oferta
                    }

    def _consolidar_info_productos_seleccionado(self, product_id, precios):

        # busca el producto seleccionado por el cliente

        info_producto = [producto for producto in self._consulta_productos
                      if producto['ProductID'] == product_id][0]

        tax_type_id = info_producto['TaxTypeID']
        cantidad = 1

        ofertado = precios['ofertado']

        if ofertado:

            precio_previo = precios['precio_previo']
            precio_oferta = precios['precio_oferta']

            totales = self._utilerias.calcular_totales_partida(precio_previo, cantidad, tax_type_id)
            totales_oferta = self._utilerias.calcular_totales_partida(precio_oferta, cantidad, tax_type_id)

            info_producto['total'] = totales['total']
            info_producto['total_oferta'] = totales_oferta['total']

            info_producto['vigencia_inicio'] = precios['vigencia_inicio']
            info_producto['vigencia_termino'] = precios['vigencia_termino']
            info_producto['tipo_oferta'] = precios['tipo_oferta']
            info_producto['ofertado'] = ofertado
        else:
            totales = self._utilerias.calcular_totales_partida(precios['precio'], cantidad, tax_type_id)
            info_producto['total'] = totales['total']
            info_producto['ofertado'] = ofertado

        return info_producto

    def _cargar_informacion_producto_seleccionado_forma(self, info_producto, ofertado):

        def actualizar_etiqueta(nombre_etiqueta, valor, info_producto):
            # Redondear y convertir valor a moneda si se trata de precio estándar
            if 'precio' in nombre_etiqueta:
                if info_producto['ProductID'] not in self._PRODUCTOS_ESPECIALES.keys():
                    valor = self._utilerias.redondear_valor_cantidad_a_decimal(valor)
                    valor = self._utilerias.convertir_decimal_a_moneda(valor)
                else:
                    # Aplicar ajustes especiales para productos especiales
                    valor = self._utilerias.redondear_valor_cantidad_a_decimal(valor)
                    valor *= self._PRODUCTOS_ESPECIALES[info_producto['ProductID']][1]
                    valor = self._utilerias.convertir_decimal_a_moneda(valor)

            # Calcular y mostrar existencia con ajustes
            if 'existencia' in nombre_etiqueta:
                existencia = info_producto['QtyPresent'] - info_producto['CantidadAjustes']
                existencia = self._utilerias.redondear_valor_cantidad_a_decimal(existencia)

                if info_producto['ProductID'] not in self._PRODUCTOS_ESPECIALES.keys():
                    # Mostrar existencia estándar
                    unidad = self._EQUIVALENCIA_UNIDADES[info_producto['Unit']]
                    valor = f"{existencia} {unidad}"
                else:
                    # Mostrar existencia ajustada para productos especiales
                    existencia /= self._PRODUCTOS_ESPECIALES[info_producto['ProductID']][1]
                    existencia = self._utilerias.redondear_valor_cantidad_a_decimal(existencia)
                    unidad = self._PRODUCTOS_ESPECIALES[info_producto['ProductID']][0]
                    valor = f"{existencia} {unidad}"

            if 'validez' in nombre_etiqueta:

                if info_producto['tipo_oferta'] == 'Semanal':
                    valor = f"válida del {info_producto['vigencia_inicio']} al{valor}"
                else:
                    valor = f"oferta válida hasta el{valor}"

            if 'tipo_oferta' in nombre_etiqueta:
                valor = f'tipo oferta -{valor}'

            # Actualizar la etiqueta con el valor calculado
            etiqueta = self._ventanas.componentes_forma[nombre_etiqueta]

            if 'precio' in nombre_etiqueta:
                etiqueta.config(font=('consolas', 25, 'bold'), text=valor)
            else:
                etiqueta.config(text=valor)

        actualizar_etiqueta('lbl_producto', info_producto['ProductName'], info_producto)
        actualizar_etiqueta('lbl_clave', f"clave {info_producto['ProductKey']}", info_producto)
        actualizar_etiqueta('lbl_precio', f" {info_producto['total']}", info_producto)
        actualizar_etiqueta('lbl_existencia', "", info_producto)

        if ofertado:
            actualizar_etiqueta('lbl_validez_oferta', f" {info_producto['vigencia_termino']}", info_producto)
            actualizar_etiqueta('lbl_tipo_oferta', f" {info_producto['tipo_oferta']}", info_producto)
            actualizar_etiqueta('lbl_precio_oferta', f" {info_producto['total_oferta']}", info_producto)

    def _cargar_ofertas_en_cbx_resultado(self):

        valores = [producto['ProductName'] for producto in self._consulta_productos_ofertados]
        valores = list(set(valores))
        valores.sort()

        cbx_resultado = self._ventanas.componentes_forma['cbx_resultado']
        cbx_resultado['values'] = valores
        cbx_resultado.set(valores[0])

        productos = [producto['ProductID'] for producto in self._consulta_productos_ofertados]
        consulta_productos = self._base_de_datos.buscar_info_productos(productos)
        self._consulta_productos = consulta_productos

        self._seleccionar_producto()

    def _llamar_informacion_producto(self):
        seleccion = self._ventanas.obtener_input_componente('cbx_resultado')

        if seleccion:
            product_id = self._obtener_product_id_seleccionado(seleccion)
            informacion = self._base_de_datos.buscar_informacion_usos_producto(product_id)

            if not informacion:
                self._ventanas.mostrar_mensaje('No se encontró información de uso relacionada al producto'
                                                  'seleccionado.')
            else:
                ventana = self._ventanas.crear_popup_ttkbootstrap()
                instancia = InformacionProducto(ventana, informacion[0])
                ventana.wait_window()

    def _calcular_cantidad_producto(self):

        seleccion = self._ventanas.obtener_input_componente('cbx_resultado')

        if not seleccion:
            return

        cantidad = self._ventanas.obtener_input_componente('tbx_cantidad')

        if not cantidad:
            self._ventanas.mostrar_mensaje('Debe introducir una valor.')
            return

        if not self._utilerias.es_cantidad(cantidad):
            self._ventanas.mostrar_mensaje('Debe introducir una cantidad válida')
            return

        cantidad = self._utilerias.redondear_valor_cantidad_a_decimal(cantidad)

        if cantidad <= 0:
            self._ventanas.mostrar_mensaje('Debe introducir mayor a cero')
            return

        product_id = self._obtener_product_id_seleccionado(seleccion)
        customer_type_id = self._obtener_customer_type_id_seleccionado()
        precios = self._obtener_precio_producto_seleccionado(customer_type_id, product_id)
        precios_impuestos = self._consolidar_info_productos_seleccionado(product_id, precios)

        def calcular_precio_cantidad(nombre_etiqueta, cantidad, precio):
            valor = precio * cantidad

            precio_moneda = self._utilerias.convertir_decimal_a_moneda(precio)
            valor_moneda = self._utilerias.convertir_decimal_a_moneda(valor)
            cantidad = int(cantidad) if cantidad % 2 == 0 else cantidad
            texto = f"{precio_moneda} x {cantidad} = {valor_moneda}"

            self._ventanas.insertar_input_componente('lbl_precio', texto)

        def calcular_precio_cantidad_monto(nombre_etiqueta, cantidad, precio):
            valor = cantidad
            cantidad = valor / precio
            cantidad = self._utilerias.redondear_valor_cantidad_a_decimal(cantidad)

            precio_moneda = self._utilerias.convertir_decimal_a_moneda(precio)
            valor_moneda = self._utilerias.convertir_decimal_a_moneda(valor)
            cantidad = int(cantidad) if cantidad % 2 == 0 else cantidad
            texto = f"{precio_moneda} x {cantidad} = {valor_moneda}"

            self._ventanas.insertar_input_componente('lbl_precio', texto)

        calcular_monto = self._ventanas.obtener_input_componente('chk_monto')

        if calcular_monto == 0:
            if not precios_impuestos['ofertado']:
                calcular_precio_cantidad('lbl_precio', cantidad, precios_impuestos['total'])
            else:
                calcular_precio_cantidad('lbl_precio', cantidad, precios_impuestos['total'])
                calcular_precio_cantidad('lbl_precio_oferta', cantidad, precios_impuestos['total_oferta'])
        else:
            if not precios_impuestos['ofertado']:
                calcular_precio_cantidad_monto('lbl_precio', cantidad, precios_impuestos['total'])
            else:
                calcular_precio_cantidad_monto('lbl_precio', cantidad, precios_impuestos['total'])
                calcular_precio_cantidad_monto('lbl_precio_oferta', cantidad, precios_impuestos['total_oferta'])

    def _copiar_precio_producto(self):

        # recupera el valor de la variable para efectuar un comportamiento anidado
        copiar_todo = self._ventanas.obtener_input_componente('chk_copiar')
        seleccion = self._ventanas.obtener_input_componente('cbx_resultado')

        if not seleccion:
            self._ventanas.mostrar_mensaje('Debe buscar por lo menos un producto.')
            return

        if seleccion == 'Seleccione' and copiar_todo == 0:
            self._ventanas.mostrar_mensaje('Debe seleccionar un producto.')
            return

        pyperclip.copy(self._procesar_valores_etiquetas(copiar_todo))

        self._master.iconify()

    def _procesar_valores_etiquetas(self, copiar_todo):

        def generar_texto_producto(ofertado):

            valores_etiquetas = {}

            for nombre, componente in self._ventanas.componentes_forma.items():
                if 'lbl' in nombre:
                    valor = componente.cget("text")
                    valores_etiquetas[nombre[4::]] = valor

            if ofertado:
                texto = f"Producto: {valores_etiquetas['producto']}\n" \
                        f"{valores_etiquetas['tipo_oferta']}\n" \
                        f"Precio oferta: {valores_etiquetas['precio_oferta']}\n" \
                        f"Precio regular: {valores_etiquetas['precio']}\n" \
                        f"Oferta {valores_etiquetas['validez_oferta']} o hasta agotar existencias.\n" \
                        f''
            else:
                texto = f"Producto: {valores_etiquetas['producto']}\n" \
                        f"Precio: {valores_etiquetas['precio']}\n"

            return texto

        cbx_resultado = self._ventanas.componentes_forma['cbx_resultado']

        if copiar_todo == 1:

            productos = cbx_resultado['values']

            texto_concatenado = ''

            for seleccion in productos:
                if seleccion == 'Seleccione':
                    continue

                self._seleccionar_producto(seleccion)

                ofertado = self._esta_producto_seleccionado_en_oferta(seleccion)

                texto = generar_texto_producto(ofertado)

                texto_concatenado += f"{texto}\n"

            texto_resultante = texto_concatenado

        else:
            ofertado = self._esta_producto_seleccionado_en_oferta(cbx_resultado.get())
            texto_resultante = generar_texto_producto(ofertado)

        return texto_resultante

    def _esta_producto_seleccionado_en_oferta(self, seleccion):

        if not self._productos_ofertados_nombres:
            self._productos_ofertados_nombres = [producto['ProductName'] for producto in
                                                 self._consulta_productos_ofertados]
            self._productos_ofertados_nombres = list(set(self._productos_ofertados_nombres))

        return True if seleccion in self._productos_ofertados_nombres else False