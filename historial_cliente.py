from cayal.ventanas import Ventanas


class HistorialCliente:
    def __init__(self, master, base_de_datos, utilerias):

        self._master = master
        self._ventanas = Ventanas(self._master)
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias

    def _cargar_componentes(self):
        pass

    def _buscar_historial_cliente(self, business_entity_id):
        return self._base_de_datos.fetchall(
            """
            SELECT  
                FORMAT(D.CreatedOn, 'dd-MM-yy') AS Fecha, 
                ISNULL(D.FolioPrefix,'') + ISNULL(D.Folio,'') DocFolio,
                CASE WHEN D.chkCustom1 = 1 THEN 'Remisión' ELSE 'Factura' END Tipo, 
                FORMAT(D.Total, 'C', 'es-MX') Total,                                               
                
                CFD.FormaPago, cfd.MetodoPago, CFD.ReceptorUsoCFDI UsoCFDI,
                CASE WHEN X.AddressDetailID = 0 THEN  ADE.AddressName ELSE   ad.AddressName END Dirección, 
                CASE WHEN X.AddressDetailID = 0 THEN  ADTE.City ELSE   ADT.City END Colonia, D.DocumentID
            FROM docDocument D INNER JOIN
                docDocumentCFD CFD ON D.DocumentID = CFD.DocumentID INNER JOIN
                orgBusinessEntity E ON D.BusinessEntityID = E.BusinessEntityID INNER JOIN
                orgBusinessEntityMainInfo EM ON E.BusinessEntityID = EM.BusinessEntityID LEFT OUTER JOIN
                orgAddressDetail ADTE ON EM.AddressFiscalDetailID = ADTE.AddressDetailID LEFT OUTER JOIN
                orgAddress ADE ON ADTE.AddressDetailID = ADE.AddressDetailID LEFT OUTER JOIN
                docDocumentExtra X ON D.DocumentID = X.DocumentID LEFT OUTER JOIN
                orgAddressDetail ADT ON X.AddressDetailID = ADT.AddressDetailID LEFT OUTER JOIN
                orgAddress AD ON ADT.AddressDetailID = AD.AddressDetailID
            
            WHERE D.CancelledOn IS NULL AND D.ModuleID IN (21,1400,1316,1319) AND D.BusinessEntityID=?
            ORDER By D.DocumentID DESC
            """,(business_entity_id,)
        )