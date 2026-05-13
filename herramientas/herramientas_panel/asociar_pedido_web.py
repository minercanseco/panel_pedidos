from cayal.ventanas import Ventanas



class AsociarPedidoWeb:
    def __init__(self, master, base_de_datos, utilerias, info_pedido):
        self._master = master
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias
        self._ventanas = Ventanas(self._master)

        self._info_pedido = info_pedido
        self._crear_componentes()
        self._rellenar_cbx_acciones()
        self._rellenar_tabla()

        self._ventanas.configurar_ventana_ttkbootstrap()


    def _crear_componentes(self):
        componentes = [
            ('tbx_nombre', 'Nombre:'),
            ('tbx_telefono', 'Teléfono:'),
            ('cbx_accion', 'Acción:'),
            ('tbv_clientes', self._crear_columnas_tabla()),
            ('btn_guardar', 'Guardar')
        ]

        self._ventanas.crear_formulario_simple(componentes)
        self._ventanas.ajustar_ancho_componente('tbx_nombre', 45)

    def _crear_columnas_tabla(self):
        return [
            {"text": "BusinessEntityID", "stretch": False, "width": 0},
            {"text": "Cliente", "stretch": False, "width": 350},
            {"text": "NComercial", "stretch": False, "width": 350},
            {"text": "Teléfono", "stretch": False, "width": 120},
            {"text": 'Correo', "stretch": False, "width": 170}
        ]

    def _rellenar_cbx_acciones(self):
        acciones = ['Asociar', 'Crear cliente']
        self._ventanas.rellenar_cbx('cbx_accion', acciones)

    def _rellenar_tabla(self):
        info = self._obtener_info_usuario()
        nombre = info.get('FullName',None)
        telefono = info.get('Telefono', None)
        correo = info.get('Email', None)

        self._ventanas.insertar_input_componente('')

        consulta = self._buscar_clientes_probables(nombre, telefono, correo)
        if consulta:
            self._ventanas.rellenar_table_view('tbv_clientes', self._crear_columnas_tabla(), consulta)

    def _obtener_info_usuario(self):
        info = self._base_de_datos.fetchall("""
            SELECT FullName, Email, NULL Telefono
            FROM engUserClient
            WHERE FirstOrderUUID='c4ffe74e-3d7b-4486-9b83-d979b6635e9c'
        """)
        return info[0] if info else {}


    def _buscar_clientes_probables(self, nombre, telefono, correo):
        return  self._base_de_datos.fetchall("""
            DECLARE @NombreBuscado   NVARCHAR(200) = ?;
            DECLARE @TelefonoBuscado NVARCHAR(50)  = ?;
            DECLARE @CorreoBuscado   NVARCHAR(200) = ?;
            
            SELECT 
                E.BusinessEntityID,
                E.OfficialName,
                E.CommercialName,
                Correo.ChannelValue   AS Correo,
                Telefono.ChannelValue AS Telefono
            FROM orgBusinessEntity E
            
            LEFT JOIN (
                SELECT 
                    CH.BusinessEntityID,
                    CH.ChannelValue
                FROM orgCommunicationChannel CH
                WHERE 
                    CH.DeletedOn IS NULL
                    AND CH.ChannelTypeID = 1
            ) Correo 
                ON E.BusinessEntityID = Correo.BusinessEntityID
            
            LEFT JOIN (
                SELECT 
                    CH.BusinessEntityID,
                    CH.ChannelValue
                FROM orgCommunicationChannel CH
                WHERE 
                    CH.DeletedOn IS NULL
                    AND CH.ChannelTypeID = 2
            ) Telefono 
                ON E.BusinessEntityID = Telefono.BusinessEntityID
            
            WHERE 
                E.DeletedOn IS NULL
            
                AND
                (
                    (
                        @NombreBuscado IS NOT NULL
                        AND @NombreBuscado <> ''
                        AND
                        (
                            E.OfficialName LIKE '%' + REPLACE(@NombreBuscado, ' ', '%') + '%'
                            OR E.CommercialName LIKE '%' + REPLACE(@NombreBuscado, ' ', '%') + '%'
                        )
                    )
            
                    OR
            
                    (
                        @TelefonoBuscado IS NOT NULL
                        AND @TelefonoBuscado <> ''
                        AND
                        REPLACE(
                            REPLACE(
                                REPLACE(
                                    REPLACE(ISNULL(Telefono.ChannelValue, ''), ' ', ''),
                                '-', ''),
                            '(', ''),
                        ')', '')
                        LIKE '%' + @TelefonoBuscado + '%'
                    )
            
                    OR
            
                    (
                        @CorreoBuscado IS NOT NULL
                        AND @CorreoBuscado <> ''
                        AND
                        ISNULL(Correo.ChannelValue, '') LIKE '%' + @CorreoBuscado + '%'
                    )
                )
            
            ORDER BY 
                E.OfficialName;
        """,(nombre, telefono, correo))