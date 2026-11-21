"""Consulta de uso de TPV por fecha de salida, independiente de la custodia actual."""
from datetime import date, datetime, timedelta
from cayal.ventanas import Ventanas


def consultar_historial_terminales(db, fecha):
    if isinstance(fecha, datetime):
        fecha = fecha.date()
    elif not isinstance(fecha, date):
        try:
            fecha = date.fromisoformat(str(fecha).strip())
        except ValueError as exc:
            raise ValueError('Seleccione una fecha válida (AAAA-MM-DD).') from exc
    return db.fetchall(SQL_HISTORIAL, (fecha, fecha + timedelta(days=1))) or []


SQL_HISTORIAL = '''
WITH Salidas AS (
    SELECT D.LiquidationID, D.DeliveryNumber, MIN(D.DepartureToDelivery) FechaSalida,
           COUNT(*) Asignaciones
    FROM dbo.DetailLiquitationOrdersCayal D
    WHERE D.DepartureToDelivery >= ? AND D.DepartureToDelivery < ?
      AND D.DeliveryNumber IS NOT NULL
    GROUP BY D.LiquidationID, D.DeliveryNumber
)
SELECT DISTINCT A.TerminalID, ISNULL(T.Referencia, 'Terminal sin referencia') Referencia,
       ISNULL(T.Barcode, '') Barcode, L.VendorUserID,
       ISNULL(E.OfficialName, 'Colaborador sin nombre') Colaborador,
       S.LiquidationID, S.DeliveryNumber, S.FechaSalida, S.Asignaciones
FROM Salidas S
JOIN dbo.TPVLiquidationOrdersCayal A ON A.LiquidationID = S.LiquidationID AND A.DeliveryNumber = S.DeliveryNumber
JOIN dbo.LiquidationOrdersCayal L ON L.LiquidationID = S.LiquidationID
LEFT JOIN dbo.zvwTerminalesBancariasCayal T ON T.ID = A.TerminalID
OUTER APPLY (SELECT TOP 1 EM.OfficialName FROM dbo.zvwEmpleadosCayalMenu EM
             WHERE EM.UserID = L.VendorUserID ORDER BY EM.OfficialName) E
ORDER BY Referencia, A.TerminalID, S.FechaSalida, S.LiquidationID, S.DeliveryNumber;
'''


def resumir_terminales(filas):
    terminales = {}
    for f in filas:
        r = terminales.setdefault(f['TerminalID'], {
            'TerminalID': f['TerminalID'], 'Referencia': str(f.get('Referencia') or '').strip(),
            'Barcode': str(f.get('Barcode') or '').strip(), 'Salidas': set(), 'Colaboradores': set()})
        r['Salidas'].add((f['LiquidationID'], f['DeliveryNumber']))
        r['Colaboradores'].add(f['VendorUserID'])
    return [dict(TerminalID=r['TerminalID'], Referencia=r['Referencia'], Barcode=r['Barcode'],
                 Salidas=len(r['Salidas']), Colaboradores=len(r['Colaboradores']))
            for r in sorted(terminales.values(), key=lambda r:(r['Referencia'].casefold(),r['TerminalID']))]


def formato_hora(valor):
    if valor is None:
        return 'Sin registro'
    if isinstance(valor, datetime):
        return valor.strftime('%d/%m/%Y %H:%M:%S')
    return str(valor)


class HistorialTerminales:
    def __init__(self, master, db):
        self._master, self.db, self.v = master, db, Ventanas(master)
        self.filas, self.terminales = [], []
        self.v.crear_frames({
            'frame_principal': ('master',None,dict(row=0,column=0,sticky='nsew')),
            'frame_fecha': ('frame_principal','Fecha de salida a reparto',dict(row=0,column=0,columnspan=2,padx=8,pady=5,sticky='ew')),
            'frame_terminales': ('frame_principal','Terminales utilizadas',dict(row=1,column=0,padx=8,pady=5,sticky='nsew')),
            'frame_detalle': ('frame_principal','Colaboradores y salidas',dict(row=1,column=1,padx=8,pady=5,sticky='nsew')),
            'frame_botones': ('frame_principal',None,dict(row=2,column=0,columnspan=2,padx=8,pady=5)),
            'frame_estado': ('frame_principal',None,dict(row=3,column=0,columnspan=2,padx=8,pady=5,sticky='ew')),
        })
        columna = lambda c,w:dict(text=c,width=w,stretch=False,column_anchor='w',heading_anchor='w',hide=0)
        self.columnas_terminales = [columna(c,w) for c,w in [('Referencia',140),('Código',145),('Salidas',65),('Colaboradores',95)]]
        self.columnas_detalle = [columna(c,w) for c,w in [('Colaborador',235),('Liquidación',85),('Salida',60),('Salida a reparto',155),('Asignaciones',90)]]
        self.v.crear_componentes({
            'den_fecha': ('frame_fecha',None,'Fecha:',None),
            'tvw_terminales': ('frame_terminales',self.columnas_terminales,14,'primary'),
            'tvw_detalle': ('frame_detalle',self.columnas_detalle,14,'info'),
            'btn_buscar': ('frame_botones','primary','Buscar',None),
            'btn_cerrar': ('frame_botones','danger','Cerrar',None),
            'lbl_estado': ('frame_estado',{'text':'Seleccione una fecha y una terminal para ver sus salidas.'},None,None),
        })
        for nombre in ('tvw_terminales','tvw_detalle'):
            self.v.componentes_forma[nombre].configure(selectmode='browse')
            self.v.agregar_barra_desplazamiento_horizontal_treeview(self.v.componentes_forma[nombre])
        self.v.cargar_eventos({'btn_buscar':self.buscar,'btn_cerrar':master.destroy,
            'den_fecha':lambda event:self.buscar(), 'tvw_terminales':(self.mostrar_detalle,'seleccion')})
        self.v.insertar_input_componente('den_fecha',date.today().isoformat())
        self.v.configurar_ventana_ttkbootstrap(titulo='Historial de terminales',nombre_icono='History32.ico')
        self.buscar()

    def buscar(self):
        self.filas, self.terminales = [], []
        self.v.rellenar_treeview('tvw_terminales',self.columnas_terminales,[])
        self.v.rellenar_treeview('tvw_detalle',self.columnas_detalle,[])
        try:
            self.filas = consultar_historial_terminales(self.db,self.v.obtener_input_componente('den_fecha'))
        except Exception as exc:
            self.v.mostrar_mensaje(f'No se pudo consultar el historial.\n{exc}')
            return
        self.terminales = resumir_terminales(self.filas)
        self.v.rellenar_treeview('tvw_terminales',self.columnas_terminales,[{
            'Referencia':r['Referencia'],'Código':r['Barcode'],'Salidas':r['Salidas'],
            'Colaboradores':r['Colaboradores']} for r in self.terminales])
        self.v.insertar_input_componente('lbl_estado',f'{len(self.terminales)} terminales con salidas registradas en la fecha elegida.')

    def mostrar_detalle(self, event=None):
        self.v.rellenar_treeview('tvw_detalle',self.columnas_detalle,[])
        tabla = self.v.componentes_forma['tvw_terminales']
        seleccion = tabla.selection()
        if len(seleccion)!=1:
            return
        indice = tabla.index(seleccion[0])
        if indice>=len(self.terminales):
            return
        terminal = self.terminales[indice]
        filas = [r for r in self.filas if r['TerminalID']==terminal['TerminalID']]
        datos = [{'Colaborador':r['Colaborador'],'Liquidación':r['LiquidationID'],
                  'Salida':r['DeliveryNumber'],'Salida a reparto':formato_hora(r.get('FechaSalida')),
                  'Asignaciones':r['Asignaciones']} for r in filas]
        self.v.rellenar_treeview('tvw_detalle',self.columnas_detalle,datos)
        self.v.insertar_input_componente('lbl_estado',f"{terminal['Referencia']}: {terminal['Salidas']} salidas y {terminal['Colaboradores']} colaboradores.")
