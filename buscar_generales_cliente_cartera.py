import tkinter as tk
import ttkbootstrap as ttk
import ttkbootstrap.dialogs
from cayal.datos import BaseDatos
from cayal.util import Utilerias
from cayal.cliente import Cliente
from controlador_saldar_cartera import ControladorSaldarCartera
from interfaz_saldar_cartera import InterfazSaldarCartera


class BuscarGeneralesClienteCartera:

    def __init__(self, master, parametros):
        self._parametros = parametros
        self._cadena_conexion = self._parametros.cadena_conexion
        self._id_usuario = self._parametros.id_usuario
        self._base_de_datos = BaseDatos(self._cadena_conexion)
        self._utilerias = Utilerias()
        self._cliente = Cliente()

        self.master = master
        self.master.geometry('352x185')
        self.master.title('Cartera cliente')
        self.master.place_window_center()
        self.master.resizable(False, False)
        self.master.bind("<Escape>", lambda event: self.master.destroy())
        self.master.bind("<F1>", lambda event: self.llamar_saldar_cartera())
        #self._utilerias.agregar_icono_ventana(self.master)

        self.consulta_buscar_cliente = []
        self.nombres_de_clientes = []
        self.termino_buscado = None
        self.business_entity_id = 0

        self.frame_principal =  ttk.LabelFrame(self.master, text='Buscar cliente:')
        self.frame_principal.grid(row=0, column=0, sticky=tk.NSEW, pady=5, padx=5)

        self.frame_buscar = ttk.Frame(self.frame_principal)
        self.frame_buscar.grid(row=0, column=0, sticky=tk.NSEW, pady=5, padx=5)

        etq_buscar = ttk.Label(self.frame_buscar, text='Buscar:')
        etq_buscar.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.buscar = ttk.Entry(self.frame_buscar)
        self.buscar.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.buscar.bind("<Return>", lambda event: self.buscar_cliente())

        self.cbx_resultados = ttk.Combobox(self.frame_buscar, width=40, state='disabled')
        self.cbx_resultados.grid(row=1, column=1, pady=5, padx=5, sticky=tk.W)
        self.cbx_resultados.bind('<<ComboboxSelected>>', lambda event: self.cambio_de_seleccion_cliente(event))

        frame_botones = ttk.Frame(self.frame_buscar)
        frame_botones.grid(row=3, column=1, pady=5, padx=3, sticky=tk.W)

        self.btn_seleccionar = ttk.Button(frame_botones, text='Seleccionar', state='disabled',
                                          command=lambda : self.llamar_saldar_cartera())
        self.btn_seleccionar.grid(row=0, column=0, pady=5, padx=5, sticky=tk.W)

        etq_seleccionar = ttk.Label(frame_botones, text='[F1]')
        etq_seleccionar.grid(row=1, column=0,  padx=5, sticky=tk.W)

        self.btn_cancelar = ttk.Button(frame_botones, text='Cancelar',style='danger', command=lambda:self.master.destroy())
        self.btn_cancelar.grid(row=0, column=1, padx=5, pady=5,sticky=tk.W)

        etq_cancelar = ttk.Label(frame_botones, text='[Esc]')
        etq_cancelar.grid(row=1, column=1, padx=5, sticky=tk.W)

        self.buscar.focus()

    def buscar_cliente(self, event=None):

        termino_buscado_tbx = self.buscar.get()

        if not termino_buscado_tbx:
            ttkbootstrap.dialogs.Messagebox.show_error('Debe introducir un termino a buscar')
        elif len(termino_buscado_tbx)<5:
            ttkbootstrap.dialogs.Messagebox.show_error('Insuficientes letras en el termino a buscar')
        elif termino_buscado_tbx != self.termino_buscado:
            self.termino_buscado = self.buscar.get()
            self.consulta_buscar_cliente = self._base_de_datos.fetchall("""
                DECLARE @Valor NVARCHAR(255) = ?
                SELECT E.BusinessEntityID,E.OfficialName
                FROM orgCustomer C INNER JOIN
                    orgBusinessEntity E ON C.BusinessEntityID=E.BusinessEntityID
                WHERE E.OfficialName LIKE '%'+@Valor+'%' AND C.DeletedOn IS NULL
                    AND E.DeletedOn IS NULL AND E.BusinessEntityID NOT IN(1,8179,9277)
            """, (self.buscar.get()))

            if not self.consulta_buscar_cliente:
                ttk.dialogs.Messagebox.show_error('El término de búsqueda no arrojó resultados.')
                self.buscar.delete(0,tk.END)
            else:
                self.nombres_de_clientes = [cliente['OfficialName'] for cliente in self.consulta_buscar_cliente]
                if len(self.nombres_de_clientes) > 1:
                    self.nombres_de_clientes.insert(0, 'Seleccione')

                self.cbx_resultados['values'] = self.nombres_de_clientes
                self.cbx_resultados.set(self.nombres_de_clientes[0])


                self.cbx_resultados.config(state='readonly')

                if len(self.nombres_de_clientes) == 1:
                    self.cambio_de_seleccion_cliente()
                    self.btn_seleccionar.config(state='normal')
                    self.btn_seleccionar.focus()
                else:
                    self.cbx_resultados.focus()

                self.buscar.delete(0,tk.END)

    def cambio_de_seleccion_cliente(self, event = None):
        if self.cbx_resultados.get() == 'Seleccione':
            ttkbootstrap.dialogs.Messagebox.show_error('Debe seleccionar un cliente de la lista')
            self.btn_seleccionar.config(state='disabled')
            if hasattr(self, 'frame_informacion') and self.frame_informacion.winfo_exists():
                self.frame_informacion.destroy()
                self.master.geometry('352x185')
                self.master.place_window_center()
        else:
            cliente = self.cbx_resultados.get()
            self.seleccionar_cliente(cliente)
            self.buscar_info_cliente_seleccionado()
            self.setear_valores_cliente_seleccionado()
            self.actualizar_apariencia_segun_tipo_cliente()
            self.btn_seleccionar.config(state='normal')

    def seleccionar_cliente(self, cliente):
        business_entity_id = [valor['BusinessEntityID'] for valor in self.consulta_buscar_cliente if valor['OfficialName'] == cliente]
        business_entity_id = business_entity_id[0]
        self.business_entity_id = business_entity_id

    def buscar_info_cliente_seleccionado(self):
        self.consulta_buscar_cliente_seleccionado =self._base_de_datos.fetchall("""
          SELECT * FROM [dbo].[zvwBuscarInfoCliente-BusinessEntityID](?)
        """, (self.business_entity_id,))

    def setear_valores_cliente_seleccionado(self):
        self._cliente.business_entity_id = self.business_entity_id
        self._cliente.cayal_customer_type_ID = self.consulta_buscar_cliente_seleccionado[0]['CayalCustomerTypeID']

        nombre_cliente = self.consulta_buscar_cliente_seleccionado[0]['OfficialName']
        nombre_cliente = self._utilerias.limitar_caracteres(nombre_cliente, 20)
        self._cliente.official_name = nombre_cliente

        ruta_cliente = self.consulta_buscar_cliente_seleccionado[0]['ZoneName']
        ruta_cliente = self._utilerias.limitar_caracteres(ruta_cliente, 28)
        self._cliente.zone_name = ruta_cliente
        self._cliente.authorized_credit = self.consulta_buscar_cliente_seleccionado[0]['AuthorizedCredit']
        self._cliente.debt = self.consulta_buscar_cliente_seleccionado[0]['Debt']
        self._cliente.remaining_credit = self.consulta_buscar_cliente_seleccionado[0]['RemainingCredit']
        self._cliente.payment_term_name = self.consulta_buscar_cliente_seleccionado[0]['PaymentTermName']
        self._cliente.oldest_purchase_folio = self.consulta_buscar_cliente_seleccionado[0]['OldestPurchaseFolio']
        self._cliente.oldest_purchase_days = self.consulta_buscar_cliente_seleccionado[0]['OldestPurchaseDays']
        self._cliente.credit_comments = self.consulta_buscar_cliente_seleccionado[0]['CreditComments']
        self._cliente.store_credit = self.consulta_buscar_cliente_seleccionado[0]['StoreCredit']
        self._cliente.customer_type_id = self.consulta_buscar_cliente_seleccionado[0]['CustomerTypeID']
        self._cliente.customer_type_name = self.consulta_buscar_cliente_seleccionado[0]['CustomerTypeName']

    def actualizar_apariencia_segun_tipo_cliente(self):

        if hasattr(self, 'frame_informacion') and self.frame_informacion.winfo_exists():
            self.frame_informacion.destroy()

        self.frame_informacion = ttk.LabelFrame(self.frame_buscar, text='Detalles cliente:')
        self.frame_informacion.grid(row=2, column=0, columnspan=2, sticky=tk.NSEW, pady=5, padx=5)

        if self._cliente.cayal_customer_type_ID == 0:
            self.master.geometry('352x300')
            self.master.place_window_center()

            etq_cliente = ttk.Label(self.frame_informacion, text='Nombre:')
            etq_cliente.grid(row=0, column=0, pady=5, padx=5, sticky=tk.W)

            cliente = ttk.Label(self.frame_informacion, text=self._cliente.official_name)
            cliente.grid(row=0, column=1, pady=5, padx=5, sticky=tk.W)

            etq_ruta_nombre = ttk.Label(self.frame_informacion, text='Ruta:')
            etq_ruta_nombre.grid(row=1, column=0, pady=5, padx=5, sticky=tk.W)

            ruta_nombre = ttk.Label(self.frame_informacion, text=self._cliente.zone_name)
            ruta_nombre.grid(row=1, column=1, pady=5, padx=5, sticky=tk.W)

            etq_lista_precio = ttk.Label(self.frame_informacion, text='Lista:')
            etq_lista_precio.grid(row=2, column=0, pady=5, padx=5, sticky=tk.W)

            lista_precio = ttk.Label(self.frame_informacion, text=self._cliente.customer_type_name)
            lista_precio.grid(row=2, column=1, pady=5, padx=5, sticky=tk.W)

        else:
            self.master.geometry('352x473')
            self.master.place_window_center()

            etq_cliente = ttk.Label(self.frame_informacion, text='Nombre:')
            etq_cliente.grid(row=0, column=0, pady=5, padx=5, sticky=tk.W)

            cliente = ttk.Label(self.frame_informacion, text=self._cliente.official_name)
            cliente.grid(row=0, column=1, pady=5, padx=5, sticky=tk.W)

            etq_ruta_nombre = ttk.Label(self.frame_informacion, text='Ruta:')
            etq_ruta_nombre.grid(row=1, column=0, pady=5, padx=5, sticky=tk.W)

            ruta_nombre = ttk.Label(self.frame_informacion, text=self._cliente.zone_name)
            ruta_nombre.grid(row=1, column=1, pady=5, padx=5, sticky=tk.W)

            self.etq_autorizado = ttk.Label(self.frame_informacion, text='Autorizado:')
            self.etq_autorizado.grid(row=2, column=0, pady=5, padx=5, sticky=tk.W)

            autorizado = self._utilerias.redondear_valor_cantidad_a_decimal(self._cliente.authorized_credit)
            autorizado = self._utilerias.convertir_decimal_a_moneda(autorizado)

            self.autorizado = ttk.Label(self.frame_informacion, text=autorizado)
            self.autorizado.grid(row=2, column=1, pady=5, padx=5, sticky=tk.W)

            self.etq_debe = ttk.Label(self.frame_informacion, text='Debe:')
            self.etq_debe.grid(row=3, column=0, pady=5, padx=5, sticky=tk.W)

            debe = self._utilerias.redondear_valor_cantidad_a_decimal(self._cliente.debt)
            debe = self._utilerias.convertir_decimal_a_moneda(debe)

            self.debe = ttk.Label(self.frame_informacion, text=debe)
            self.debe.grid(row=3, column=1, pady=5, padx=5, sticky=tk.W)

            self.etq_restante = ttk.Label(self.frame_informacion, text='Restante:')
            self.etq_restante.grid(row=4, column=0, pady=5, padx=5, sticky=tk.W)

            restante = self._utilerias.redondear_valor_cantidad_a_decimal(self._cliente.remaining_credit)
            restante = self._utilerias.convertir_decimal_a_moneda(restante)

            self.restante = ttk.Label(self.frame_informacion, text=restante)
            self.restante.grid(row=4, column=1, pady=5, padx=5, sticky=tk.W)

            self.etq_condicion = ttk.Label(self.frame_informacion, text='Condición:')
            self.etq_condicion.grid(row=5, column=0, pady=5, padx=5, sticky=tk.W)

            self.condicion = ttk.Label(self.frame_informacion, text=self._cliente.payment_term_name)
            self.condicion.grid(row=5, column=1, pady=5, padx=5, sticky=tk.W)

            self.etq_compra_periodo = ttk.Label(self.frame_informacion, text='P.Compra:')
            self.etq_compra_periodo.grid(row=6, column=0, pady=5, padx=5, sticky=tk.W)

            if self._cliente.oldest_purchase_days == 0 and self._cliente.oldest_purchase_folio == '':
                documento_mas_antiguo = 'No tiene compras en el periodo.'
            else:
                documento_mas_antiguo = f'Documento más antiguo: {self._cliente.oldest_purchase_days} días, {self._cliente.oldest_purchase_folio}.'

            self.compra_periodo = ttk.Label(self.frame_informacion,text=documento_mas_antiguo)
            self.compra_periodo.grid(row=6, column=1, pady=5, padx=5, sticky=tk.W)

            self.etq_credito_super = ttk.Label(self.frame_informacion, text='Minisuper:')
            self.etq_credito_super.grid(row=7, column=0, pady=5, padx=5, sticky=tk.W)

            comentario_super = 'CRÉDITO EN SUPER AUTORIZADO' if self._cliente.store_credit == 1 else 'CRÉDITO EN SUPER NO PERMITIDO'

            if self._cliente.store_credit == 1:
                self.credito_super = ttk.Label(self.frame_informacion, text=comentario_super)
            else:
                self.credito_super = ttk.Label(self.frame_informacion, style='danger', text=comentario_super)

            self.credito_super.grid(row=7, column=1, pady=5, padx=5, sticky=tk.W)

            etq_lista_precio = ttk.Label(self.frame_informacion, text='Lista:')
            etq_lista_precio.grid(row=8, column=0, pady=5, padx=5, sticky=tk.W)

            lista_precio = ttk.Label(self.frame_informacion, text=self._cliente.customer_type_name)
            lista_precio.grid(row=8, column=1, pady=5, padx=5, sticky=tk.W)

    def llamar_saldar_cartera(self):
        if self.business_entity_id != 0:
            if self.buscar_documentos_en_cartera() == 0:
                ttk.dialogs.Messagebox.show_error('El cliente no tiene documentos en cartera.')
            else:
                self._parametros.id_principal = self.business_entity_id

                nueva_ventana = ttk.Toplevel()
                controlador =  ControladorSaldarCartera(self._parametros)
                interfaz = InterfazSaldarCartera(nueva_ventana, controlador)
                #self.master.withdraw()
                nueva_ventana.wait_window()
                self.master.destroy()

    def buscar_documentos_en_cartera(self):
        return self._base_de_datos.fetchone("""
        SELECT COUNT(D.DocumentID) AS Documentos
                FROM docDocument D
                    INNER JOIN docDocumentExtra X ON D.DocumentID=X.DocumentID
                    LEFT OUTER JOIN orgDepot A ON X.BusinessEntityDepotID=A.DepotID
                    INNER JOIN docDocumentCFD CFD ON D.DocumentID=CFD.DocumentID
                    INNER JOIN vwcboAnexo20v33_FormaPago FP ON CFD.FormaPago=FP.Clave
                    WHERE D.CancelledOn IS NULL
                      AND D.StatusPaidID<>1
                      AND D.BusinessEntityID=?
                      AND D.ModuleID IN (21,1400,1319)
                      AND D.Balance<>0
        """, (self.business_entity_id,))