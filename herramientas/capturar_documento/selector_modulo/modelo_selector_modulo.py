from cayal.comandos_base_datos import ComandosBaseDatos

class ModeloSelectorModulo:
    def __init__(self, parametros):
        self.parametros = parametros
        self.base_de_datos = ComandosBaseDatos()
        self.user_id = self.parametros.id_usuario


    def obtener_nombre_usuario(self):
        return self.base_de_datos.buscar_nombre_de_usuario(self.user_id)

    def obtener_columnas(self, tabla):

        modulos = {
            'tbv_tickets': 158,
            'tbv_facturas': 1400,
            'tbv_depositos': 1664

        }

        modulo = modulos.get(tabla, 0)
        if modulo == 0:
            return None, None, None

        info_columnas = self.base_de_datos.fetchall("""
            SELECT TOP 1
                    UV.Columns, UV.ColumnsSize, MP.[Value] PrimaryKey
            FROM	engDrlGridViews GV INNER JOIN
                        engDrlGridUserViews UV ON GV.ViewID=UV.ViewID INNER JOIN
                        engUser U ON UV.UserID=U.UserID INNER JOIN
                        engModuleParameter MP ON GV.ModuleID = MP.ModuleID
            WHERE GV.ModuleID=? AND UserGroupID = 11 AND ParameterKey = 'PrimaryKey'
        """, (modulo,))

        # agregamos el primary key de la consulta sobre la que se realizará el procesamiento de la info
        columnas = info_columnas[0]['Columns']
        anchos_columnas = info_columnas[0]['ColumnsSize']
        primary_key = info_columnas[0]['PrimaryKey']

        columnas = f"{columnas}, [{primary_key}]"
        anchos_columnas = f"{anchos_columnas}, 0"

        return columnas, anchos_columnas, primary_key

    def obtener_registros(self, tabla, columnas_str, primary_key):
        consultas = {
            'tbv_tickets': ('vwLBSDocCustomerSaleList',"AND CAST(Fecha as date) = CAST(GETDATE() as date)"),
            'tbv_facturas': ('vwLBSDocCustomerInvoiceList1400',"AND CAST(Fecha as date) = CAST(GETDATE() as date)"),
            'tbv_depositos': ('zvwDepositosDiariosCayalMenu', "AND CAST(Fecha as date) = CAST(GETDATE() as date)")
        }

        consulta = consultas.get(tabla, None)[0]
        if not consulta:
            return
        filtro = consultas.get(tabla, None)[1]

        query = f"""
                SELECT {columnas_str}
                FROM {consulta}
                WHERE CreatedBy = {self.user_id}
                {filtro}
                ORDER BY {primary_key} DESC
            """

        return self.base_de_datos.fetchall(query)



