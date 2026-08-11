from cayal.comandos_base_datos import ComandosBaseDatos

class ModeloSelectorModulo:
    def __init__(self, parametros):
        self.parametros = parametros
        self.base_de_datos = ComandosBaseDatos()
        self.user_id = self.parametros.id_usuario
        self.user_name = self.obtener_nombre_usuario()


    def obtener_nombre_usuario(self):
        return self.base_de_datos.buscar_nombre_de_usuario(self.user_id)

    def obtener_estado_edicion_factura(self, document_id):
        registros = self.base_de_datos.fetchall(
            """
            SELECT TOP 1
                ISNULL(M.CFDStatusName, '') AS CFDStatusName,
                ISNULL(M.CancelledIcon, 0) AS CanceladoIcon
            FROM vwLBSDocCustomerInvoiceList1400 M
            WHERE M.DocumentID = ?
            """,
            (int(document_id),),
        )
        return registros[0] if registros else None

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

        if not info_columnas:
            return None, None, None

        # agregamos el primary key de la consulta sobre la que se realizará el procesamiento de la info
        columnas = info_columnas[0]['Columns']
        anchos_columnas = info_columnas[0]['ColumnsSize']
        primary_key = info_columnas[0]['PrimaryKey']

        columnas = f"{columnas}, [{primary_key}]"
        anchos_columnas = f"{anchos_columnas}, 0"

        return columnas, anchos_columnas, primary_key

    def obtener_registros(self, tabla, columnas_str, primary_key):
        consultas = {
            'tbv_tickets': (
                'vwLBSDocCustomerSaleList',
                'M.CreatedBy = ? AND ISNULL(M.CanceladoIcon, 0) <> 1',
                (self.user_id,),
            ),
            'tbv_facturas': (
                'vwLBSDocCustomerInvoiceList1400',
                'M.CreatedBy = ?',
                (self.user_id,),
            ),
            'tbv_depositos': (
                'zvwDepositosDiariosCayalMenu',
                '''(
                    M.CreatedBy = ?
                    OR EXISTS (
                        SELECT 1
                        FROM zvwDepositosDiariosCayal D
                        WHERE D.ID = M.ID
                          AND D.ReceptorUserID = ?
                    )
                )''',
                (self.user_id, self.user_id),
            ),
        }

        configuracion = consultas.get(tabla)
        if not configuracion:
            return []
        consulta, filtro_usuario, parametros = configuracion

        query = f"""
                SELECT {columnas_str}
                FROM {consulta} M
                WHERE {filtro_usuario}
                AND CAST(M.Fecha as date) = CAST(GETDATE() as date)
                ORDER BY {primary_key} DESC
            """
        print(query, self.user_id)
        return self.base_de_datos.fetchall(query, parametros)
