import tkinter as tk

import ttkbootstrap as ttk

from cayal.ventanas import Ventanas


class DireccionCliente:
    """Previsualiza y cambia la dirección asociada al documento."""

    def __init__(
            self, master, documento, base_de_datos,
            componentes_captura=None, al_actualizar=None,
    ):
        self._master = master
        self._componentes_captura = componentes_captura
        self.documento = documento
        self._base_de_datos = base_de_datos
        self._al_actualizar = al_actualizar
        self._consulta_direcciones = []
        self._direccion_previsualizada = None
        self._ventanas = Ventanas(self._master)

        self._crear_interfaz()
        self._rellenar_cbx_direcciones()
        self._seleccionar_direccion_actual()
        self._previsualizar_direccion()

        self._ventanas.configurar_ventana_ttkbootstrap(
            titulo='Dirección cliente'
        )
        self._master.resizable(False, False)

    def _crear_interfaz(self):
        principal = ttk.Frame(self._master, padding=12)
        principal.grid(row=0, column=0, sticky=tk.NSEW)

        seleccion = ttk.LabelFrame(
            principal, text='Seleccionar dirección', padding=10
        )
        seleccion.grid(row=0, column=0, sticky=tk.EW)
        ttk.Label(seleccion, text='Dirección:').grid(
            row=0, column=0, padx=(0, 8), sticky=tk.W
        )
        self.cbx_direcciones = ttk.Combobox(
            seleccion, width=48, state='readonly'
        )
        self.cbx_direcciones.grid(row=0, column=1, sticky=tk.EW)
        self.cbx_direcciones.bind(
            '<<ComboboxSelected>>', self._previsualizar_direccion
        )

        detalle = ttk.LabelFrame(
            principal, text='Vista previa', padding=10
        )
        detalle.grid(row=1, column=0, pady=(10, 0), sticky=tk.EW)
        detalle.grid_columnconfigure(1, weight=1)

        self._variables = {
            'nombre': tk.StringVar(value=''),
            'domicilio': tk.StringVar(value=''),
            'telefono': tk.StringVar(value=''),
            'sucursal': tk.StringVar(value=''),
            'envio': tk.StringVar(value=''),
        }
        campos = (
            ('Nombre:', 'nombre'),
            ('Domicilio:', 'domicilio'),
            ('Teléfono:', 'telefono'),
            ('Sucursal:', 'sucursal'),
            ('Costo de envío:', 'envio'),
        )
        for fila, (etiqueta, clave) in enumerate(campos):
            ttk.Label(detalle, text=etiqueta).grid(
                row=fila, column=0, padx=(0, 10), pady=3, sticky=tk.NE
            )
            ttk.Label(
                detalle,
                textvariable=self._variables[clave],
                wraplength=440,
                justify=tk.LEFT,
                font=('TkDefaultFont', 9, 'bold'),
            ).grid(row=fila, column=1, pady=3, sticky=tk.W)

        ttk.Label(detalle, text='Comentarios:').grid(
            row=len(campos), column=0, padx=(0, 10), pady=3, sticky=tk.NE
        )
        self.txt_comentarios = tk.Text(
            detalle, width=55, height=4, wrap=tk.WORD
        )
        self.txt_comentarios.grid(
            row=len(campos), column=1, pady=3, sticky=tk.EW
        )
        self.txt_comentarios.configure(state='disabled')

        botones = ttk.Frame(principal)
        botones.grid(row=2, column=0, pady=(12, 0), sticky=tk.E)
        self.btn_actualizar = ttk.Button(
            botones,
            text='Actualizar dirección',
            bootstyle='success',
            command=self._asignar_direccion,
        )
        self.btn_actualizar.grid(row=0, column=0, padx=4)
        ttk.Button(
            botones,
            text='Cancelar',
            bootstyle='danger',
            command=self._master.destroy,
        ).grid(row=0, column=1, padx=4)

        self._master.bind('<Return>', lambda _event: self._asignar_direccion())
        self._master.bind('<Escape>', lambda _event: self._master.destroy())

    @staticmethod
    def _valor(direccion, *claves, predeterminado=''):
        for clave in claves:
            valor = direccion.get(clave)
            if valor not in (None, ''):
                return valor
        return predeterminado

    def _rellenar_cbx_direcciones(self):
        self._consulta_direcciones = (
            self._base_de_datos.rellenar_cbx_direcciones(
                self.documento.business_entity_id,
                self.cbx_direcciones,
            ) or []
        )

    def _seleccionar_direccion_actual(self):
        valores = list(self.cbx_direcciones.cget('values') or [])
        if not valores:
            self.btn_actualizar.configure(state='disabled')
            return

        nombre_actual = str(
            getattr(self.documento, 'address_name', '') or ''
        ).strip()
        coincidencia = next(
            (valor for valor in valores
             if str(valor).strip().casefold() == nombre_actual.casefold()),
            None,
        )
        self.cbx_direcciones.set(coincidencia or valores[0])

    def _obtener_direccion_seleccionada(self, mostrar_error=True):
        seleccion = self.cbx_direcciones.get()
        if not seleccion or seleccion.strip().casefold() == 'seleccione':
            if mostrar_error:
                self._mostrar_error('Debe seleccionar una dirección.')
            return None

        referencia = (
            self._base_de_datos.procesar_direccion_seleccionada_cbx(
                seleccion, self._consulta_direcciones
            )
        )
        if not referencia:
            if mostrar_error:
                self._mostrar_error(
                    'No fue posible obtener la dirección seleccionada.'
                )
            return None

        address_detail_id = self._valor(
            referencia, 'address_detail_id', 'AddressDetailID',
            predeterminado=0,
        )
        direccion = self._base_de_datos.buscar_detalle_direccion_formateada(
            address_detail_id
        )
        if not direccion:
            if mostrar_error:
                self._mostrar_error(
                    'La dirección seleccionada ya no está disponible.'
                )
            return None

        direccion = dict(direccion)
        direccion['address_detail_id'] = address_detail_id
        costo_envio = self._obtener_costo_envio(address_detail_id)
        if costo_envio is not None:
            # Se conservan ambas convenciones porque el documento y las
            # consultas históricas pueden utilizar cualquiera de ellas.
            direccion['delivery_cost'] = costo_envio
            direccion['DeliveryCost'] = costo_envio
        return direccion

    def _obtener_costo_envio(self, address_detail_id):
        """Consulta directamente el cargo configurado para la dirección."""
        if not address_detail_id:
            return None

        resultado = self._base_de_datos.fetchone(
            'SELECT CargoEnvio '
            'FROM [dbo].[zvwBuscarCargoEnvio-AddressDetailID](?)',
            (address_detail_id,),
        )
        if resultado in (None, ''):
            return None
        if isinstance(resultado, dict):
            return resultado.get(
                'CargoEnvio', resultado.get('cargo_envio')
            )
        if isinstance(resultado, (tuple, list)):
            return resultado[0] if resultado else None
        return resultado

    def _previsualizar_direccion(self, event=None):
        direccion = self._obtener_direccion_seleccionada(
            mostrar_error=False
        )
        self._direccion_previsualizada = direccion
        self.btn_actualizar.configure(
            state='normal' if direccion else 'disabled'
        )
        if not direccion:
            for variable in self._variables.values():
                variable.set('')
            self._establecer_comentarios('')
            return

        calle = self._valor(direccion, 'calle', 'Street')
        numero = self._valor(direccion, 'numero', 'ExtNumber')
        colonia = self._valor(direccion, 'colonia', 'City')
        municipio = self._valor(direccion, 'municipio', 'Municipality')
        estado = self._valor(direccion, 'estado', 'StateProvince')
        cp = self._valor(direccion, 'cp', 'ZipCode')
        partes = [
            str(valor).strip() for valor in (
                f'{calle} {numero}'.strip(), colonia, municipio, estado,
                f'C.P. {cp}' if cp else '',
            ) if str(valor).strip()
        ]

        self._variables['nombre'].set(self._valor(
            direccion, 'address_name', 'AddressName',
            predeterminado='Dirección',
        ))
        self._variables['domicilio'].set(', '.join(partes).upper())
        self._variables['telefono'].set(self._valor(
            direccion, 'telefono', 'Phone', 'CellPhone',
            predeterminado='Sin teléfono',
        ))
        self._variables['sucursal'].set(self._valor(
            direccion, 'depot_name', 'DepotName',
            predeterminado='Sin sucursal asignada',
        ))
        costo_envio = self._valor(
            direccion, 'delivery_cost', 'DeliveryCost',
            predeterminado=None,
        )
        self._variables['envio'].set(
            'No especificado' if costo_envio is None
            else f'$ {float(costo_envio):,.2f}'
        )
        self._establecer_comentarios(self._valor(
            direccion, 'comentario', 'Comments',
            predeterminado='Sin comentarios',
        ))

    def _establecer_comentarios(self, texto):
        self.txt_comentarios.configure(state='normal')
        self.txt_comentarios.delete('1.0', tk.END)
        self.txt_comentarios.insert('1.0', texto)
        self.txt_comentarios.configure(state='disabled')

    def _mostrar_error(self, mensaje):
        self._ventanas.mostrar_mensaje(mensaje, self._master)

    def _asignar_direccion(self):
        direccion = self._direccion_previsualizada
        if direccion is None:
            direccion = self._obtener_direccion_seleccionada()
        if not direccion:
            return False

        address_detail_id = self._valor(
            direccion, 'address_detail_id', 'AddressDetailID',
            predeterminado=0,
        )
        self.documento.address_details = direccion
        self.documento.address_detail_id = address_detail_id
        self.documento.address_name = self._valor(
            direccion, 'address_name', 'AddressName',
            predeterminado='Dirección',
        )
        self.documento.depot_id = self._valor(
            direccion, 'depot_id', 'DepotID', predeterminado=0
        )
        self.documento.depot_name = self._valor(
            direccion, 'depot_name', 'DepotName'
        )

        parametros = getattr(self.documento, 'order_parameters', None)
        if isinstance(parametros, dict):
            parametros['AddressDetailID'] = address_detail_id
            parametros['DepotID'] = self.documento.depot_id

        if callable(self._al_actualizar):
            self._al_actualizar(direccion)

        self._master.destroy()
        return True
