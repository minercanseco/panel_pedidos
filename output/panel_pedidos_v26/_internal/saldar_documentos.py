import ttkbootstrap as ttk
import tkinter as tk
from cayal.util import Utilerias
from cayal.cobros import Cobros
import threading


class SaldarDocumentos:

    def __init__(self, master, parametros_saldado, cadena_de_conexion, business_entity_id, usuario_id):

        self._cadena_de_conexion = cadena_de_conexion
        self._parametros_saldado = parametros_saldado
        self._cobros = Cobros(self._cadena_de_conexion)
        self._usuario_id = usuario_id
        self._documentos_a_recalcular = []
        self._business_entity_id = business_entity_id

        self._utilerias = Utilerias()

        self.master = master
        self.master.geometry('363x55')
        self.master.title('Cartera cliente')
        self.master.place_window_center()
        self.master.resizable(False, False)
        self.master.bind("<Escape>", lambda event: self.master.destroy())
        #self._utilerias.agregar_icono_ventana(self.master)
        self.master.focus()
        self.master.grab_set()

        frame_principal = ttk.LabelFrame(master=self.master, text='Cobrando:')
        frame_principal.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)

        self.barra_progreso = ttk.Progressbar(master=frame_principal, bootstyle="danger-striped", length=342,
                                              mode='determinate')
        self.barra_progreso.grid(row=0, column=0, pady=5, padx=5)

        # Iniciar el temporizador de 0 segundos
        timer_thread = threading.Timer(0, self.procesar_saldados)
        timer_thread.daemon = True  # Marcar el hilo como daemon
        timer_thread.start()

    def procesar_saldados(self):
        barcode = self._parametros_saldado['Barcode']
        afiliacion = self._parametros_saldado['Afiliacion']
        financial_entity_id = self._parametros_saldado['BancoID']
        documentos = self._parametros_saldado['Documentos']
        forma_cobro_id = self._parametros_saldado['FormaCobro']
        fecha_afectacion = self._parametros_saldado['FechaAfectacion']
        modalidad = self._parametros_saldado['Modalidad']
        cantidad_documentos = len(documentos)
        incremento_barra = 100 / cantidad_documentos
        rfc = self._cobros.fetchone('SELECT OfficialNumber FROM orgBusinessEntityMainInfo WHERE BusinessEntityID = ?',
                                    (self._business_entity_id,))
        official_name = self._cobros.fetchone('SELECT OfficialName FROM orgBusinessEntity WHERE BusinessEntityID = ?',
                                              (self._business_entity_id,))

        monto_total = [documento['Cobrado'] for documento in documentos]
        monto_total = sum(monto_total)

        for documento in documentos:
                self._cobros.modality = modalidad
                self._cobros.total_amount =monto_total
                self._cobros.barcode = barcode
                self._cobros.document_id = documento['DocumentID']
                self._cobros.payment_method_id = forma_cobro_id
                self._cobros.amount = documento['Cobrado']
                self._cobros.financial_entity_id = financial_entity_id
                self._cobros.business_entity_id = self._business_entity_id
                self._cobros.official_number = rfc
                self._cobros.official_name = official_name
                self._cobros.afiliacion = afiliacion
                self._cobros.created_by = self._usuario_id
                self._cobros.date_operation = fecha_afectacion
                self._cobros.total = documento['Total']
                self._cobros.total_paid = (documento['Total'] - documento['Saldo'])
                self._cobros.create_payment()

                self._documentos_a_recalcular.append(documento['DocumentID'])
                self.incrementar_barra(incremento_barra)

        self.insertar_documentos_a_recalcular()
        self.master.destroy()
        
    def incrementar_barra(self, incremento):
        valor = self.barra_progreso['value']
        valor += incremento
        self.barra_progreso['value'] = valor

    def insertar_documentos_a_recalcular(self):

        # inserta los documentos que se recalcularan en contpaq cuando finalice la ejecucion del programa
        for documento in self._documentos_a_recalcular:
            self._cobros.exec_stored_procedure('zvwRecalcularDocumentos', (documento, 0))


