import os
from cayal.comandos_base_datos import ComandosBaseDatos
from cayal.informe import Informe


class CrearListasPrecios:
    def __init__(self, parametros):
        self._parametros = parametros
        self._informe = Informe()
        self._base_de_datos = ComandosBaseDatos()
        self._user_name = self._base_de_datos.buscar_nombre_de_usuario(self._parametros.id_usuario)
        self._categorias = {
            'AGUA PURIFICADA': [],
            'ARTIC. DE LIMPIEZA': [],
            'ARTIC. NO COMESTIBLES': [],
            'ARTICULOS DE HIGIENE PERSONAL': [],
            'BEBIDAS': [],
            'BOTANAS': [],
            'CERDO': [],
            'COMESTIBLES': [],
            'COMIDA DE ANIMALES': [],
            'CONDIMENTOS': [],
            'DULCES Y CHOCOLATES': [],
            'EMBOLSADOS': [],
            'GALLETAS': [],
            'GATORADE': [],
            'HUEVO': [],
            'IMPORTADOS': [],
            'LATERIA Y COMESTIBLE': [],
            'LICORES Y HIELO': [],
            'LIQUIDOS ( REFRESCOS )': [],
            'LISTAS PARA COCINAR': [],
            'PANADERIA': [],
            'PANES Y PANECILLOS': [],
            'PAVOS': [],
            'POLLO': [],
            'PLASTICOS Y DESECHABLES': [],
            'PREPARADOS': [],
            'RES LOCAL': [],
            'SALSAS': [],
            'SOPAS Y PASTAS': [],
            'TARJETAS TELEFONICAS': [],
            'VEGETALES CONGELADOS': [],
            'VERDURAS': []
        }

        self._settear_rutas()
        self._buscar_informacion()
        self._generar_informe()

    def _buscar_productos_por_linea(self, linea):
        return self._base_de_datos.fetchall("""
            SELECT 
                P.ProductName AS Producto, 
                P.ProductKey AS Clave,
            
                -- Precio Lista 2
                '$' + FORMAT(
                    MAX(CASE WHEN PRECIOS.CustomerTypeID = 2 THEN
                        CASE 
                            WHEN P.TaxTypeID = 16 THEN ((PRECIOS.SalePrice) * 1.08) * 1.16 
                            WHEN P.TaxTypeID = 5  THEN PRECIOS.SalePrice * 1.16 
                            WHEN P.TaxTypeID = 10 AND P.ProductID NOT IN (907, 1162, 1165, 1166) 
                                THEN PRECIOS.SalePrice 
                            
                            WHEN P.ProductID = 907 THEN PRECIOS.SalePrice
                            WHEN P.ProductID = 1162 THEN PRECIOS.SalePrice * 15 
                            WHEN P.ProductID = 1165 THEN PRECIOS.SalePrice * 360 
                            WHEN P.ProductID = 1166 THEN PRECIOS.SalePrice * 30
                            
                            WHEN P.TaxTypeID = 15 THEN PRECIOS.SalePrice * 1.08 
                            WHEN P.TaxTypeID = 18 THEN (PRECIOS.SalePrice + ISNULL(Tax20.TaxAmount, 0)) * 1.16
                            WHEN P.TaxTypeID = 19 THEN (PRECIOS.SalePrice + ISNULL(Tax21.TaxAmount, 0)) * 1.16
                            WHEN P.TaxTypeID = 20 THEN (PRECIOS.SalePrice + ISNULL(Tax22.TaxAmount, 0)) * 1.16
                        END
                    END), 'N2', 'es-MX') AS Lista2,
            
                -- Precio Lista 4
                '$' + FORMAT(
                    MAX(CASE WHEN PRECIOS.CustomerTypeID = 4 THEN
                        CASE 
                            WHEN P.TaxTypeID = 16 THEN ((PRECIOS.SalePrice) * 1.08) * 1.16 
                            WHEN P.TaxTypeID = 5  THEN PRECIOS.SalePrice * 1.16 
                            
                            WHEN P.TaxTypeID = 10 AND P.ProductID NOT IN (907, 1162, 1165, 1166) 
                                THEN PRECIOS.SalePrice 
                            
                            WHEN P.ProductID = 907 THEN PRECIOS.SalePrice
                            WHEN P.ProductID = 1162 THEN PRECIOS.SalePrice * 15 
                            WHEN P.ProductID = 1165 THEN PRECIOS.SalePrice * 360 
                            WHEN P.ProductID = 1166 THEN PRECIOS.SalePrice * 30
                            
                            WHEN P.TaxTypeID = 15 THEN PRECIOS.SalePrice * 1.08 
                            WHEN P.TaxTypeID = 18 THEN (PRECIOS.SalePrice + ISNULL(Tax20.TaxAmount, 0)) * 1.16
                            WHEN P.TaxTypeID = 19 THEN (PRECIOS.SalePrice + ISNULL(Tax21.TaxAmount, 0)) * 1.16
                            WHEN P.TaxTypeID = 20 THEN (PRECIOS.SalePrice + ISNULL(Tax22.TaxAmount, 0)) * 1.16
                        END
                    END), 'N2', 'es-MX') AS Lista4
            
            FROM 
                orgProduct P
            INNER JOIN 
                orgProductCustomerTypeSalePrice PRECIOS ON P.ProductID = PRECIOS.ProductID
            INNER JOIN 
                vwLBSProductQuantityList EX ON P.ProductID = EX.ProductID
            
            -- JOINS con los montos de impuestos según ID
            OUTER APPLY (SELECT TaxAmount FROM engTaxItem WHERE TaxItemID = 20) AS Tax20
            OUTER APPLY (SELECT TaxAmount FROM engTaxItem WHERE TaxItemID = 21) AS Tax21
            OUTER APPLY (SELECT TaxAmount FROM engTaxItem WHERE TaxItemID = 22) AS Tax22
            
            WHERE 
                PRECIOS.CustomerTypeID IN (2, 4)
                AND PRECIOS.SalePrice > 0
                AND EX.DepotID = 2
                AND (ISNULL(EX.QtyAvailable, 0) - ISNULL(P.CantidadAjustes, 0)) > 0
                AND P.DeletedOn IS NULL
                AND P.Category1 = ?
            
            GROUP BY 
                P.ProductName, P.ProductKey
            ORDER BY 
                P.ProductName
        """, (linea,))

    def _settear_rutas(self):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self._informe.plantilla = os.path.join(BASE_DIR, 'plantilla_lista_precios.html')
        self._informe.archivo = os.path.join(BASE_DIR, 'lista_precios.html')

    def _buscar_informacion(self):
        for linea, lista in self._categorias.items():
            productos = self._buscar_productos_por_linea(linea)
            self._categorias[linea] = productos

        self._buscar_informacion_carnes_frias()

    def _buscar_informacion_carnes_frias(self):
        lineas_carnes_frias = ['JAMONES', 'YOGHURTS', 'QUESOS', 'SALCHICHA', 'CHORIZOS',
			        'TOCINO, CHULETAS', 'PIZZAS Y PRIMAVERAS']

        productos_acumulados = []
        for carnes in lineas_carnes_frias:
            productos = self._buscar_productos_por_linea(carnes)
            productos_acumulados.extend(productos)

        productos_ordenados = sorted(productos_acumulados, key=lambda x: x['Producto'])
        self._categorias['CARNES FRIAS'] = productos_ordenados



    def _generar_informe(self):

        for linea, productos in self._categorias.items():
            self._informe.agregar_tabla(productos, linea, None)

        self._informe.parametros = [{'usuario': self._user_name}]

        self._informe.generar_informe_html()
        self._informe.abrir_html_en_navegador(eliminar_archivo=True)

