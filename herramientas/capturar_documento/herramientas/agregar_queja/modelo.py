from cayal.comandos_base_datos import ComandosBaseDatos


class Modelo:
    MODULOS_COMPRAS = (152, 202, 203, 187)
    GRUPOS_ADMIN = (5,3,15,7,6,1)


    def __init__(self, parametros):
        self.parametros = parametros
        self.base_de_datos = ComandosBaseDatos()

        self.document_id = self.parametros.id_principal
        self.module_id = self.parametros.id_modulo
        self.user_id = self.parametros.id_usuario

        self._user_group_id = None

    def user_group_id(self):
        if self._user_group_id is not None:
            return self._user_group_id

        consulta = self.base_de_datos.fetchone(
            """
            SELECT UserGroupID 
            FROM engUser 
            WHERE UserID = ?
            """,
            (self.user_id,)
        )

        if isinstance(consulta, dict):
            self._user_group_id = consulta.get('UserGroupID', 0)
        else:
            self._user_group_id = consulta or 0

        return self._user_group_id

    def es_admin(self):
        return self.user_group_id() in self.GRUPOS_ADMIN

    def obtener_empleados(self):
        return self.base_de_datos.fetchall("""
            SELECT 
                OfficialName, 
                BusinessEntityID, 
                EmployeeTypeID, 
                UserID, 
                UserName
            FROM zvwEmpleadosCayalMenu
        """)

    def obtener_areas(self):
        return self.base_de_datos.fetchall("""
            SELECT ID, Value 
            FROM zvwAreasQuejasDeptosCayal
        """)

    def obtener_sub_areas(self, area_id):
        return self.base_de_datos.fetchall("""
            SELECT ID, Value 
            FROM zvwSubAreasQuejasDeptosCayal 
            WHERE AreaID = ?
        """, (area_id,))

    def obtener_tipos_queja(self):
        if self.module_id in self.MODULOS_COMPRAS:
            sql = """
                SELECT ItemValue, ComboID 
                FROM engRefCombo 
                WHERE CboGroupName = 'Tipos de quejas de proveedores'
            """
        else:
            sql = """
                SELECT ItemValue, ComboID 
                FROM engRefCombo 
                WHERE CboGroupName = 'Tipos de quejas clientes'
            """

        return self.base_de_datos.fetchall(sql)

    def obtener_productos_documento(self):
        return self.base_de_datos.fetchall("""
            SELECT 
                DI.ProductID,
                P.ProductName AS Producto
            FROM docDocumentItem DI
            INNER JOIN orgProduct P ON DI.ProductID = P.ProductID
            WHERE DI.DocumentID = ?
            ORDER BY P.ProductName
        """, (self.document_id,))

    def obtener_quejas_documento(self):
        return self.base_de_datos.fetchall("""
            SELECT  
                Q.ID, 
                Q.TipoDeError,
                Q.Producto,
                Q.Responsable,
                Q.DocumentID,
                Q.Fecha, 
                Q.Comentario,
                Q.Usuario,
                Q.Salio,
                Q.Seguimiento,
                U.UserName,
                U.UserGroupID, 
                Q.ProductID, 
                CASE 
                WHEN CAST(Q.Fecha AS date) = CAST(GETDATE() AS date)
                THEN 1 
                ELSE 0 
                END AS Editable,
                CASE WHEN Q.Area IS NULL THEN '' ELSE Q.Area END AS Area,
                CASE WHEN Q.SubArea IS NULL THEN '' ELSE Q.SubArea END AS SubArea
            FROM zvwQuejasventasCayal Q 
            INNER JOIN engUser U ON Q.Usuario = U.UserID 
            INNER JOIN docDocument D ON Q.DocumentID = D.DocumentID
            WHERE Q.DocumentID = ?
            ORDER BY Q.ID
        """, (self.document_id,))

    def guardar_queja(self, queja):
        salio = self._normalizar_bit(queja.get('Salio', 0))

        parametros = (
            queja.get('QuejaID'),
            queja.get('Tipo'),
            queja.get('Producto', ''),
            queja.get('Responsable'),
            salio,
            queja.get('Seguimiento', '').upper(),
            self.document_id,
            queja.get('Comentario', '').upper(),
            self.user_id,
            queja.get('ProductID', 0),
            queja.get('Area'),
            queja.get('SubArea')
        )

        self.base_de_datos.command("""
            DECLARE @QuejaID INT = ?;
            DECLARE @TipoError NVARCHAR(100) = ?;
            DECLARE @Producto NVARCHAR(200) = ?;
            DECLARE @Responsable NVARCHAR(100) = ?;
            DECLARE @Salio INT = ?;
            DECLARE @Seguimiento NVARCHAR(200) = ?;
            DECLARE @Documento INT = ?;
            DECLARE @Comentario NVARCHAR(MAX) = ?;
            DECLARE @UsuarioID INT = ?;
            DECLARE @ProductoID INT = ?;
            DECLARE @Area NVARCHAR(100) = ?;
            DECLARE @SubArea NVARCHAR(100) = ?;

            SET @Salio = ISNULL(@Salio, 0);

            IF EXISTS (
                SELECT 1 
                FROM zvwQuejasventasCayal 
                WHERE ID = @QuejaID
            )
            BEGIN
                INSERT INTO zvwBitacoraQuejasCayal2 (
                    Fecha,
                    Incidencia,
                    Usuario,
                    DocumentID,
                    QuejaID,
                    ValorAnterior,
                    ValorNuevo
                )
                SELECT 
                    GETDATE(),
                    Cambio.Incidencia,
                    @UsuarioID,
                    Q.DocumentID,
                    Q.ID,
                    Cambio.ValorAnterior,
                    Cambio.ValorNuevo
                FROM zvwQuejasventasCayal Q
                CROSS APPLY (
                    VALUES
                        ('CAMBIO TIPO DE QUEJA', ISNULL(Q.TipoDeError, ''), ISNULL(@TipoError, '')),
                        ('CAMBIO PRODUCTO', ISNULL(Q.Producto, ''), ISNULL(@Producto, '')),
                        ('CAMBIO RESPONSABLE', ISNULL(Q.Responsable, ''), ISNULL(@Responsable, '')),
                        ('CAMBIO SALIÓ', CAST(ISNULL(Q.Salio, 0) AS NVARCHAR(20)), CAST(ISNULL(@Salio, 0) AS NVARCHAR(20))),
                        ('CAMBIO SEGUIMIENTO', ISNULL(Q.Seguimiento, ''), ISNULL(@Seguimiento, '')),
                        ('CAMBIO COMENTARIO', ISNULL(Q.Comentario, ''), ISNULL(@Comentario, '')),
                        ('CAMBIO PRODUCT ID', CAST(ISNULL(Q.ProductID, 0) AS NVARCHAR(20)), CAST(ISNULL(@ProductoID, 0) AS NVARCHAR(20))),
                        ('CAMBIO ÁREA', ISNULL(Q.Area, ''), ISNULL(@Area, '')),
                        ('CAMBIO SUB ÁREA', ISNULL(Q.SubArea, ''), ISNULL(@SubArea, ''))
                ) Cambio(Incidencia, ValorAnterior, ValorNuevo)
                WHERE Q.ID = @QuejaID
                  AND ISNULL(Cambio.ValorAnterior, '') <> ISNULL(Cambio.ValorNuevo, '');

                UPDATE zvwQuejasventasCayal
                SET 
                    TipoDeError = @TipoError,
                    Producto = @Producto,
                    Responsable = @Responsable,
                    Salio = @Salio,
                    Seguimiento = @Seguimiento,
                    Comentario = @Comentario,
                    ProductID = @ProductoID,
                    Area = @Area,
                    SubArea = @SubArea,
                    Fecha = GETDATE(),
                    UsuarioMod = @UsuarioID,
                    FechaMod = GETDATE()
                WHERE ID = @QuejaID;
            END
            ELSE
            BEGIN
                INSERT INTO zvwQuejasventasCayal (
                    TipoDeError, 
                    Producto, 
                    Responsable, 
                    Salio, 
                    Seguimiento, 
                    DocumentID, 
                    Fecha, 
                    Comentario, 
                    Usuario, 
                    ProductID, 
                    Area, 
                    SubArea
                )
                VALUES (
                    @TipoError, 
                    @Producto, 
                    @Responsable, 
                    @Salio, 
                    @Seguimiento, 
                    @Documento, 
                    GETDATE(), 
                    @Comentario, 
                    @UsuarioID, 
                    @ProductoID, 
                    @Area, 
                    @SubArea
                );

                DECLARE @NuevaQuejaID INT = SCOPE_IDENTITY();

                INSERT INTO zvwBitacoraQuejasCayal2 (
                    Fecha,
                    Incidencia,
                    Usuario,
                    DocumentID,
                    QuejaID,
                    ValorAnterior,
                    ValorNuevo
                )
                VALUES (
                    GETDATE(),
                    'CAPTURA DE QUEJA',
                    @UsuarioID,
                    @Documento,
                    @NuevaQuejaID,
                    '',
                    ISNULL(@TipoError, '')
                );
            END;

            UPDATE docDocument
            SET ConQueja = 1
            WHERE DocumentID = @Documento 
              AND ISNULL(ConQueja, 0) <> 1;
        """, parametros)

    def guardar_quejas(self, quejas):
        for queja in quejas:
            self.guardar_queja(queja)

    def obtener_modificaciones_quejas(self):
        return self.base_de_datos.fetchall("""
            SELECT
                B.Fecha,
                B.Incidencia,
                U.UserName AS Usuario,
                ISNULL(B.ValorAnterior, '') AS ValorAnterior,
                ISNULL(B.ValorNuevo, '') AS ValorNuevo,
                B.DocumentID,
                B.Usuario AS UsuarioID
            FROM zvwBitacoraQuejasCayal2 B
            LEFT JOIN engUser U ON B.Usuario = U.UserID
            WHERE B.DocumentID = ?
            ORDER BY B.Fecha DESC
        """, (self.document_id,))

    def _normalizar_bit(self, valor):
        if valor in (1, True, '1', 'true', 'True', 'SI', 'Sí', 'si', 'sí', 'on', 'ON', 'seleccionado'):
            return 1

        return 0

    def obtener_historial_quejas_cliente(self):
        return self.base_de_datos.fetchall("""
            DECLARE @DocumentID INT = ?;

            WITH ClienteDocumento AS (
                SELECT D.BusinessEntityID
                FROM docDocument D
                WHERE D.DocumentID = @DocumentID
            ),

            QuejasCliente AS (
                SELECT DISTINCT
                    QJ.ID,
                    QJ.DocumentID,
                    ISNULL(D.FolioPrefix, '') + ISNULL(CAST(D.Folio AS VARCHAR(50)), '') AS DocFolio,
                    D.BusinessEntityID,
                    E.OfficialName,
                    QJ.Fecha,
                    QJ.TipoDeError,
                    QJ.Producto,
                    QJ.Responsable,
                    QJ.Comentario,
                    QJ.Seguimiento,
                    QJ.Area,
                    QJ.SubArea,
                    QJ.Salio,
                    QJ.Usuario
                FROM zvwQuejasventasCayal QJ
                INNER JOIN docDocument D
                    ON D.DocumentID = QJ.DocumentID
                INNER JOIN ClienteDocumento CD
                    ON CD.BusinessEntityID = D.BusinessEntityID
                INNER JOIN orgBusinessEntity E
                    ON E.BusinessEntityID = D.BusinessEntityID
            )

            SELECT
                QC.Fecha,
                QC.DocFolio,
                QC.OfficialName,
                QC.TipoDeError,
                QC.Producto,
                QC.Responsable,
                QC.Area,
                QC.SubArea,
                U.UserName AS Usuario,
                QC.Comentario,
                QC.Seguimiento,
                QC.Salio,
                QC.ID AS QuejaID,
                QC.Usuario AS UsuarioID
            FROM QuejasCliente QC
            LEFT JOIN engUser U
                ON U.UserID = QC.Usuario
            ORDER BY
                QC.Fecha DESC,
                QC.DocumentID DESC,
                QC.ID DESC;
        """, (self.document_id,))

    def eliminar_queja(self, queja_id):
        self.base_de_datos.command("""
            DECLARE @QuejaID INT = ?;
            DECLARE @UsuarioID INT = ?;
            DECLARE @UserGroupID INT = ?;

            DECLARE @Documento INT;
            DECLARE @UsuarioQueja INT;
            DECLARE @FechaQueja DATETIME;

            SELECT 
                @Documento = DocumentID,
                @UsuarioQueja = Usuario,
                @FechaQueja = Fecha
            FROM zvwQuejasventasCayal
            WHERE ID = @QuejaID;

            IF @Documento IS NULL
                RETURN;

            IF NOT (
                @UserGroupID IN (1, 5, 6, 7, 15, 20)
                OR (
                    @UsuarioQueja = @UsuarioID
                    AND CAST(@FechaQueja AS date) = CAST(GETDATE() AS date)
                )
            )
                RETURN;

            DELETE FROM zvwQuejasventasCayal 
            WHERE ID = @QuejaID;

            INSERT INTO zvwBitacoraQuejasCayal2 (
                Fecha,
                Incidencia,
                Usuario,
                DocumentID,
                QuejaID,
                ValorAnterior,
                ValorNuevo
            )
            VALUES (
                GETDATE(),
                'QUEJA ELIMINADA',
                @UsuarioID,
                @Documento,
                @QuejaID,
                '',
                'QUEJA ELIMINADA'
            );

            IF NOT EXISTS (
                SELECT 1 
                FROM zvwQuejasventasCayal 
                WHERE DocumentID = @Documento
            )
            BEGIN
                UPDATE docDocument 
                SET ConQueja = 0 
                WHERE DocumentID = @Documento;
            END;
        """, (
            queja_id,
            self.user_id,
            self.user_group_id()
        ))

        return True