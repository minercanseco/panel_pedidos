import ttkbootstrap as ttk
import tkinter as tk
import ttkbootstrap.dialogs
import pyperclip

from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.util import Utilerias
from cayal.ventanas import Ventanas

from herramientas.verificador_precios.informacion_producto import InformacionProducto


class VerificadorPrecios:

    def __init__(self, master, parametros):
        self._master = master

        # instancias a utilizar
        self._parametros = parametros
        self._base_de_datos = ComandosBaseDatos(self._parametros.cadena_conexion)
        self._utilerias = Utilerias()
        self._ventanas = Ventanas(self._master)

        self._consulta_ofertas = []

        # variables globales
        self._componentes_forma = {}
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
            'PAQUETE':'Pq'
        }

        self._PRODUCTOS_ESPECIALES = {
            1162: ('Pz', 15),  #Huevo media reja
            1165: ('Cj', 360), #Huevo caja
            1166: ('Rj', 30) #Huevo reja

        }

        # diseño de interfaz
        self._cargar_componentes_forma()
        self._cargar_eventos_componentes_forma()
        self._cargar_info_componentes_forma()
        self._ventanas.configurar_ventana_ttkbootstrap('Verificador de precios')
        self._buscar_productos_ofertados()

        tbx_buscar = self._componentes_forma['tbx_buscar']
        tbx_buscar.focus()

    def _buscar_productos_ofertados(self):

        consulta = self._base_de_datos.buscar_productos_en_oferta()

        self._productos_ofertados_ids = [producto['ProductID'] for producto in consulta]
        self._productos_ofertados_ids = list(set(self._productos_ofertados_ids))


        self._consulta_productos_ofertados = consulta

    def _cargar_componentes_forma(self):

        frame_principal = ttk.LabelFrame(self._master, text='Verificador precios')
        frame_principal.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)

        frame_busqueda = ttk.Frame(frame_principal)
        frame_busqueda.grid(row=0, column=0, columnspan=2, pady=5, sticky=tk.NSEW)

        linea = ttk.IntVar()

        frame_general = ttk.Frame(frame_principal)
        frame_general.grid(row=1, column=0, columnspan=2,  pady=5, sticky=tk.NSEW)

        frame_acciones = ttk.Frame(frame_principal)
        frame_acciones.grid(row=2, column=0,  pady=5, sticky=tk.W)

        monto = ttk.IntVar()
        copiar = ttk.IntVar()

        frame_etiqueta_producto = ttk.Frame(frame_principal)

        frame_detalles = ttk.Frame(frame_principal)

        frame_detalles_oferta = ttk.Frame(frame_principal)

        self._componentes_forma['frame_etiqueta_producto'] = frame_etiqueta_producto
        self._componentes_forma['frame_detalles'] = frame_detalles
        self._componentes_forma['frame_detalles_oferta'] = frame_detalles_oferta
        self._componentes_forma['chk_var_linea'] = linea
        self._componentes_forma['chk_var_monto'] = monto
        self._componentes_forma['chk_var_copiar'] = copiar

        estilo_lbl_roja = {
            'width': 44,
            'foreground': 'white',
            'background': '#E30421',
            'font': ('consolas', 12, 'bold'),
            'anchor': 'center'
        }

        estilo_lbl_azul = {
            'width': 22,
            'foreground': 'white',
            'background': '#2A569A',
            'font': ('consolas', 25, 'bold'),
            'anchor': 'center'
        }

        estilo_lbl_naranja = {
            'width': 22,
            'foreground': 'white',
            'background': '#FE7F00',
            'font': ('consolas', 25, 'bold'),
            'anchor': 'center'
        }

        nombres_componentes = {
            'tbx_buscar':(frame_busqueda, 'Entry', None),
            'chk_linea': (frame_busqueda, 'CheckButton', linea),
            'cbx_resultado':(frame_general, 'Combobox', 'readonly'),
            'cbx_lista':(frame_general, 'Combobox', 'readonly'),
            'tbx_cantidad':(frame_acciones, 'Entry', None),
            'chk_monto': (frame_acciones, 'CheckButton', monto),
            'btn_copiar': (frame_acciones, 'Button', 'danger'),
            'chk_copiar': (frame_acciones, 'CheckButton', copiar),
            'btn_ofertas': (frame_acciones, 'Button', 'warning'),
            'btn_info': (frame_acciones, 'Button', 'info'),
            'lbl_nombre_producto':(frame_etiqueta_producto, 'Label', estilo_lbl_roja),
            'lbl_precio': (frame_detalles, 'Label', estilo_lbl_azul),
            'lbl_clave': (frame_detalles, 'Label', estilo_lbl_azul),
            'lbl_existencia': (frame_detalles, 'Label', estilo_lbl_azul),
            'lbl_existencia_texto': (frame_detalles, 'Label', estilo_lbl_azul),
            'lbl_titulo_oferta': (frame_detalles_oferta, 'Label', estilo_lbl_naranja),
            'lbl_tipo_oferta': (frame_detalles_oferta, 'Label', estilo_lbl_naranja),
            'lbl_vigencia': (frame_detalles_oferta, 'Label', estilo_lbl_naranja),
            'lbl_precio_oferta': (frame_detalles_oferta, 'Label', estilo_lbl_naranja),

        }

        for i, (nombre, (frame, tipo, configuracion)) in enumerate(nombres_componentes.items()):
            etiqueta = nombre[4::].capitalize()

            if 'tbx' in nombre:

                if nombre != 'tbx_cantidad':
                    componente = ttk.Entry(frame)
                    componente.grid(row=0, column=i, pady=5, padx=5, sticky=tk.W)

                if nombre == 'tbx_cantidad':
                    componente = ttk.Entry(frame, width=10)
                    componente.grid(row=0, column=i+1, pady=5, padx=5, sticky=tk.W)

            if 'chk' in nombre:

                if 'linea' in nombre:
                    componente = ttk.Checkbutton(frame,
                                                 bootstyle='success, round-toggle',
                                                 text='Línea',
                                                 variable=configuracion)

                if 'monto' in nombre:
                    componente = ttk.Checkbutton(frame,
                                                 bootstyle='success, round-toggle',
                                                 text='Monto',
                                                 variable=configuracion)

                if 'copiar' in nombre:
                    componente = ttk.Checkbutton(frame,
                                                 bootstyle='success, round-toggle',
                                                 text='Todos',
                                                 variable=configuracion)
                    componente.grid(row=1, column=i-1, pady=5, padx=5, sticky=tk.W)

                if 'copiar' not in nombre:
                    componente.grid(row=0, column=i+1, pady=5, padx=5, sticky=tk.W)

            if 'cbx' in nombre:
                componente = ttk.Combobox(frame, state=configuracion)

                if nombre == 'cbx_resultado':
                    componente.config(width=30)

            if 'btn' in nombre:
                componente = ttk.Button(frame, width=8, text=etiqueta, style=configuracion)
                componente.grid(row=1, column=i-1, pady=5, padx=5, sticky=tk.W)

            if 'lbl' in nombre:
                if nombre not in ('lbl_existencia_texto', 'lbl_tipo_oferta', 'lbl_titulo_oferta'):
                    componente = ttk.Label(frame, **configuracion)

                if nombre == 'lbl_existencia_texto':
                    componente = ttk.Label(frame, text='EXISTENCIA', **configuracion)

                if nombre == 'lbl_titulo_oferta':
                    componente = ttk.Label(frame, text='OFERTA', **configuracion)

                if nombre == 'lbl_tipo_oferta':
                    componente = ttk.Label(frame, text='OFERTA SEMANAL', **configuracion)
                    componente.config(font=('consolas', 12, 'bold'))

                if nombre == 'lbl_vigencia':
                    componente = ttk.Label(frame, text='OFERTA SEMANAL', **configuracion)
                    componente.config(font=('consolas', 12, 'bold'))

                componente.grid(row=i, column=0, sticky=tk.NSEW)

            if tipo not in ('CheckButton', 'Button', 'Label'):

                if 'cantidad' in nombre:
                    lbl = ttk.Label(frame, width=9, text=etiqueta)
                    lbl.grid(row=0, column=i, padx=5, pady=5, sticky=tk.W)
                else:
                    lbl = ttk.Label(frame, width=9, text=etiqueta)
                    lbl.grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)

                    componente.grid(row=i, column=1, pady=5, padx=5, sticky=tk.W)

            self._componentes_forma[nombre] = componente

    def _cargar_eventos_componentes_forma(self):

        tbx_buscar = self._componentes_forma['tbx_buscar']
        tbx_buscar.bind('<Return>', lambda event: self._buscar_info_producto())

        tbx_cantidad = self._componentes_forma['tbx_cantidad']
        tbx_cantidad.config(validate='focus',
                   validatecommand=(self._master.register(
                       lambda text: self._utilerias.validar_entry(tbx_cantidad, 'cantidad')), '%P'))

        tbx_cantidad.bind('<Return>', lambda event: self._calcular_cantidad_producto())

        cbx_resultado = self._componentes_forma['cbx_resultado']
        cbx_resultado.bind('<<ComboboxSelected>>', lambda event: self._seleccionar_producto(cbx_resultado.get()))

        cbx_lista = self._componentes_forma['cbx_lista']
        cbx_lista.bind('<<ComboboxSelected>>', lambda event: self._seleccionar_producto(cbx_resultado.get()))

        btn_ofertas = self._componentes_forma['btn_ofertas']
        btn_ofertas.config(command=lambda: self._cargar_ofertas_en_cbx_resultado())

        btn_copiar = self._componentes_forma['btn_copiar']
        btn_copiar.config(command=lambda: self._copiar_precio_producto())

        btn_info = self._componentes_forma['btn_info']
        btn_info.config(command=lambda: self._llamar_informacion_producto())

    def _cargar_info_componentes_forma(self):
        self._buscar_listas_de_precios()

        cbx_lista = self._componentes_forma['cbx_lista']
        listas =  [lista['CustomerTypeName'] for lista in self._consulta_lista_de_precios]
        cbx_lista['values'] = listas
        cbx_lista.set(listas[0])

    def _seleccionar_producto(self, seleccion = None):

        if not seleccion:
            cbx_resultado = self._componentes_forma['cbx_resultado']
            valores = cbx_resultado['values']
            seleccion = valores[0]

        if seleccion == 'Seleccione':

            frame_detalles_oferta = self._componentes_forma['frame_detalles_oferta']
            frame_detalles = self._componentes_forma['frame_detalles']
            frame_etiqueta_producto = self._componentes_forma['frame_etiqueta_producto']

            frame_detalles_oferta.grid_forget()
            frame_detalles.grid_forget()
            frame_etiqueta_producto.grid_forget()

        if seleccion != 'Seleccione':

            product_id = self._obtener_product_id_seleccionado(seleccion)

            # busca la correspondencia de la lista de precios seleccionadas
            customer_type_id = self._obtener_customer_type_id_seleccionado()

            precios = self._obtener_precio_producto_seleccionado(customer_type_id, product_id)
            ofertado = precios['ofertado']

            info_producto = self._consolidar_info_productos_seleccionado(product_id, precios)

            self._cambiar_apariencia_forma(ofertado)

            self._cargar_informacion_producto_seleccionado_forma(info_producto, ofertado)

    def _obtener_product_id_seleccionado(self, seleccion):
        return [producto['ProductID'] for producto in self._consulta_productos
                          if producto['ProductName'] == seleccion][0]

    def _obtener_customer_type_id_seleccionado(self):
        cbx_lista = self._componentes_forma['cbx_lista']
        lista_seleccionada = cbx_lista.get()

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

            if 'vigencia' in nombre_etiqueta:

                if info_producto['tipo_oferta'] == 'Semanal':
                    valor = f"válida del {info_producto['vigencia_inicio']} al{valor}"
                else:
                    valor = f"oferta válida hasta el{valor}"

            if 'tipo_oferta' in nombre_etiqueta:
                valor = f'tipo oferta -{valor}'

            # Actualizar la etiqueta con el valor calculado
            etiqueta = self._componentes_forma[nombre_etiqueta]

            if 'precio' in nombre_etiqueta:
                etiqueta.config(font=('consolas', 25, 'bold'), text=valor)
            else:
                etiqueta.config(text=valor)

        actualizar_etiqueta('lbl_nombre_producto', info_producto['ProductName'], info_producto)
        actualizar_etiqueta('lbl_clave', f"clave {info_producto['ProductKey']}", info_producto)
        actualizar_etiqueta('lbl_precio', f" {info_producto['total']}", info_producto)
        actualizar_etiqueta('lbl_existencia', "", info_producto)

        if ofertado:
            actualizar_etiqueta('lbl_vigencia', f" {info_producto['vigencia_termino']}", info_producto)
            actualizar_etiqueta('lbl_tipo_oferta', f" {info_producto['tipo_oferta']}", info_producto)
            actualizar_etiqueta('lbl_precio_oferta', f" {info_producto['total_oferta']}", info_producto)

    def _cambiar_apariencia_forma(self, ofertado):

        frame_detalles_oferta = self._componentes_forma['frame_detalles_oferta']
        frame_detalles = self._componentes_forma['frame_detalles']
        frame_etiqueta_producto = self._componentes_forma['frame_etiqueta_producto']

        frame_detalles_oferta.grid_forget()
        frame_detalles.grid_forget()
        frame_etiqueta_producto.grid_forget()

        if not ofertado:
            frame_etiqueta_producto.grid(row=3, column=0, columnspan=2, sticky=tk.NSEW)
            frame_detalles.grid(row=4, column=0, columnspan=2, sticky=tk.NSEW)

        if ofertado:
            frame_etiqueta_producto.grid(row=3, column=0, columnspan=2, sticky=tk.NSEW)
            frame_detalles.grid(row=5, column=0, columnspan=2, sticky=tk.NSEW)
            frame_detalles_oferta.grid(row=4, column=0, columnspan=2, sticky=tk.NSEW)

    def _rellenar_cbx_resultado(self):

        cbx_resultado = self._componentes_forma['cbx_resultado']

        productos = [producto['ProductName'] for producto in self._consulta_productos]

        if not productos:
            return

        if len(productos) > 1:
            productos.insert(0, 'Seleccione')

        cbx_resultado['values'] = productos
        cbx_resultado.set(productos[0])

    def _buscar_listas_de_precios(self):
        self._consulta_lista_de_precios = self._base_de_datos.fetchall("""
            SELECT CustomerTypeID, CustomerTypeName 
            FROM orgCustomerType
            WHERE CustomerTypeID BETWEEN 2 AND 10 
        """,())

    def _buscar_info_producto(self):

        tbx_buscar = self._componentes_forma['tbx_buscar']
        termino_buscado = tbx_buscar.get()

        # busca por linea de productos si el control esta habilitado
        chk_linea = self._componentes_forma['chk_var_linea']
        buscar_linea = chk_linea.get()

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
            ttk.dialogs.Messagebox.show_error('El término de búsqueda no arrojó ningún resultado')
            return
        else:
            productos = [producto['ProductID'] for producto in consulta]
            consulta_productos = self._base_de_datos.buscar_info_productos(productos)

            self._consulta_productos = consulta_productos
            self._rellenar_cbx_resultado()

            if len(self._consulta_productos) == 1:
                self._seleccionar_producto()

    def _validar_termino_buscado(self, termino_buscado):

        if not termino_buscado:
            ttk.dialogs.Messagebox.show_error('Debe introducir un término a buscar.')
            return False

        termino_buscado = str(termino_buscado)
        termino_buscado = termino_buscado.strip()

        if len(termino_buscado) < 4:
            ttk.dialogs.Messagebox.show_error('Debe abundar en el término a buscar.')
            return False

        return True

    def _validar_seleccion_resultado(self):

        cbx_resultado = self._componentes_forma['cbx_resultado']
        seleccion = cbx_resultado.get()

        if not seleccion:
            ttk.dialogs.Messagebox.show_error('Debe buscar por lo menos un producto.')
            return False

        if seleccion == 'Seleccione':
            ttk.dialogs.Messagebox.show_error('Debe seleccionar un producto.')
            return False

        return seleccion

    def _calcular_cantidad_producto(self):

        seleccion = self._validar_seleccion_resultado()

        if not seleccion:
            return

        tbx_cantidad = self._componentes_forma['tbx_cantidad']
        cantidad = tbx_cantidad.get()

        if not cantidad:
            ttk.dialogs.Messagebox.show_error('Debe introducir una valor.')
            return

        if not self._utilerias.es_cantidad(cantidad):
            ttk.dialogs.Messagebox.show_error('Debe introducir una cantidad válida')
            return

        cantidad = self._utilerias.redondear_valor_cantidad_a_decimal(cantidad)

        if cantidad <= 0:
            ttk.dialogs.Messagebox.show_error('Debe introducir mayor a cero')
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

            lbl_precio = self._componentes_forma[nombre_etiqueta]
            lbl_precio.config(text=texto, font=('consolas', 18, 'bold'))

        def calcular_precio_cantidad_monto(nombre_etiqueta, cantidad, precio):
            valor = cantidad
            cantidad = valor / precio
            cantidad = self._utilerias.redondear_valor_cantidad_a_decimal(cantidad)

            precio_moneda = self._utilerias.convertir_decimal_a_moneda(precio)
            valor_moneda = self._utilerias.convertir_decimal_a_moneda(valor)
            cantidad = int(cantidad) if cantidad % 2 == 0 else cantidad
            texto = f"{precio_moneda} x {cantidad} = {valor_moneda}"

            lbl_precio = self._componentes_forma[nombre_etiqueta]
            lbl_precio.config(text=texto, font=('consolas', 18, 'bold'))

        chk_var_monto = self._componentes_forma['chk_var_monto']
        calcular_monto = chk_var_monto.get()

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

    def _cargar_ofertas_en_cbx_resultado(self):

        valores = [producto['ProductName'] for producto in self._consulta_productos_ofertados]
        valores = list(set(valores))
        valores.sort()

        cbx_resultado = self._componentes_forma['cbx_resultado']
        cbx_resultado['values'] = valores
        cbx_resultado.set(valores[0])

        productos = [producto['ProductID'] for producto in self._consulta_productos_ofertados]
        consulta_productos = self._base_de_datos.buscar_info_productos(productos)
        self._consulta_productos = consulta_productos

        self._seleccionar_producto()

    def _copiar_precio_producto(self):

        # recupera el valor de la variable para efecturar un comportamiento anidado
        chk_copiar = self._componentes_forma['chk_var_copiar']
        copiar_todo = chk_copiar.get()

        cbx_resultado = self._componentes_forma['cbx_resultado']
        seleccion = cbx_resultado.get()

        if not seleccion:
            ttk.dialogs.Messagebox.show_error('Debe buscar por lo menos un producto.')
            return

        if seleccion == 'Seleccione' and copiar_todo == 0:
            ttk.dialogs.Messagebox.show_error('Debe seleccionar un producto.')
            return

        pyperclip.copy(self._procesar_valores_etiquetas(copiar_todo))

        self._master.iconify()

    def _procesar_valores_etiquetas(self, copiar_todo):

        def generar_texto_producto(ofertado):

            valores_etiquetas = {}

            for nombre, componente in self._componentes_forma.items():
                if 'lbl' in nombre:
                    valor = componente.cget("text")
                    valores_etiquetas[nombre[4::]] = valor

            if ofertado:
                texto = f"Producto: {valores_etiquetas['nombre_producto']}\n" \
                        f"{valores_etiquetas['tipo_oferta']}\n" \
                        f"Precio oferta: {valores_etiquetas['precio_oferta']}\n" \
                        f"Precio regular: {valores_etiquetas['precio']}\n" \
                        f"Oferta {valores_etiquetas['vigencia']} o hasta agotar existencias.\n" \
                        f''
            else:
                texto = f"Producto: {valores_etiquetas['nombre_producto']}\n" \
                        f"Precio: {valores_etiquetas['precio']}\n"

            return texto

        cbx_resultado = self._componentes_forma['cbx_resultado']

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

    def _llamar_informacion_producto(self):
        seleccion = self._validar_seleccion_resultado()

        if seleccion:

            product_id = self._obtener_product_id_seleccionado(seleccion)
            informacion = self._base_de_datos.buscar_informacion_usos_producto(product_id)

            if not informacion:
                ttk.dialogs.Messagebox.show_error('No se encontró información de uso relacionada al producto'
                                                  'seleccionado.')
            else:
                ventana = ttk.Toplevel()
                instancia = InformacionProducto(ventana, informacion[0])

    def _esta_producto_seleccionado_en_oferta(self, seleccion):

        if not self._productos_ofertados_nombres:
            self._productos_ofertados_nombres = [producto['ProductName'] for producto in
                                                 self._consulta_productos_ofertados]
            self._productos_ofertados_nombres = list(set(self._productos_ofertados_nombres))

        return True if seleccion in self._productos_ofertados_nombres else False