import datetime
from cayal.cobros import Cobros
from cayal.ventanas import Ventanas

class SaldarDocumentos:

    def __init__(self, master, parametros, base_de_datos, parametros_saldado):
        self._parametros = parametros
        self._user_id = self._parametros.id_usuario

        self._parametros_saldado = parametros_saldado
        self._inicializar_parametros_generales()

        self._cobros = Cobros(self._parametros.cadena_conexion)
        self._base_de_datos = base_de_datos

        self._master = master
        self._ventanas = Ventanas(self._master)

        # Crear la barra de progreso
        self._ventanas.crear_progressbar('pgb_barra', bootstyle='info')
        self._ventanas.configurar_ventana_ttkbootstrap('Saldando cobros')

        # Iniciar procesamiento paso a paso
        self._ventanas.procesar_con_barra(
            nombre_barra='pgb_barra',
            total_elementos=len(self._documents),
            funcion_procesamiento=self.procesar_cobros,  # ← sin paréntesis
            fin_callback= self._cerrar_ventana
        )

    def _inicializar_parametros_generales(self):
        self._documents = self._parametros_saldado['Documentos']
        self._official_name = self._parametros_saldado['OfficialName']
        self._official_number = self._parametros_saldado['OfficalNumber']
        self._business_entity_id = self._parametros_saldado['BusinessEntityID']
        self._modalidad = self._parametros_saldado['Modalidad']
        self._barcode =  self._parametros_saldado['Barcode']
        self._afiliacion = self._parametros_saldado['Afiliacion']
        self._financial_entity_id = self._parametros_saldado['BancoID']
        self._payment_method_id = self._parametros_saldado['FormaCobro']
        self._date_affectation = self._parametros_saldado['FechaAfectacion']
        self._amount_total = 0

        if self._modalidad == 0: # agrupado
            monto_total = [documento['Pagado'] for documento in self._documents]
            monto_total = sum(monto_total)
            self._amount_total = monto_total

    def _cerrar_ventana(self):
        # aqui abrimos el cajon
        self._master.destroy()

    def procesar_cobros(self, indice, continuar):
        cobro = self._documents[indice]

        self._insertar_cobro(cobro)
        # Simulación de lógica que tarda (puedes reemplazar esto por tu lógica real)

        def finalizar():
            cobro['procesado'] = True  # ejemplo de modificación
            continuar()

        self._master.after(300, finalizar)

    def _insertar_cobro(self, cobro):

        document_id = cobro['DocumentID']
        pagado =  cobro['Pagado']

        self._cobros.modality = self._modalidad

        # si es un solo cobro todos los documentos aplia el self._amount_total si no el monto de cada cobro
        self._cobros.total_amount = self._amount_total if self._modalidad == 0 else pagado
        self._cobros.barcode = self._barcode
        self._cobros.document_id = document_id
        self._cobros.payment_method_id = self._payment_method_id
        self._cobros.amount = pagado
        self._cobros.financial_entity_id = self._financial_entity_id
        self._cobros.business_entity_id = self._business_entity_id
        self._cobros.official_number = self._official_number
        self._cobros.official_name = self._official_name
        self._cobros.afiliacion = self._afiliacion
        self._cobros.created_by = self._user_id
        self._cobros.date_operation = self._date_affectation
        self._cobros.total = cobro['Total']
        self._cobros.total_paid = (cobro['Total'] - cobro['Saldo'])
        self._cobros.create_payment()


        self._insertar_para_recalcular(document_id)

    def _insertar_para_recalcular(self, document_id):
        self._base_de_datos.exec_stored_procedure('zvwRecalcularDocumentos',
                                                      (document_id, document_id))
