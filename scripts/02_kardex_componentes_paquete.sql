SET XACT_ABORT ON;
GO

-- Ejecutar antes de desplegar los cambios de las aplicaciones.
IF COL_LENGTH('dbo.docDocumentItem', 'OrderPackageDocumentItemID') IS NULL
    ALTER TABLE dbo.docDocumentItem ADD OrderPackageDocumentItemID INT NULL;
GO

IF COL_LENGTH('dbo.orgProductKardex', 'PackageComponentSource') IS NULL
    ALTER TABLE dbo.orgProductKardex ADD PackageComponentSource TINYINT NULL;
GO
IF COL_LENGTH('dbo.orgProductKardex', 'PackageComponentID') IS NULL
    ALTER TABLE dbo.orgProductKardex ADD PackageComponentID INT NULL;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.check_constraints
    WHERE parent_object_id = OBJECT_ID('dbo.orgProductKardex')
      AND name = 'CK_Kardex_PackageComponentSource')
    ALTER TABLE dbo.orgProductKardex WITH CHECK
    ADD CONSTRAINT CK_Kardex_PackageComponentSource
    CHECK (
        (PackageComponentSource IS NULL AND PackageComponentID IS NULL)
        OR (PackageComponentSource IN (1, 2) AND PackageComponentID IS NOT NULL)
    );
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE object_id = OBJECT_ID('dbo.orgProductKardex')
               AND name = 'UX_Kardex_PackageComponent')
    CREATE UNIQUE INDEX UX_Kardex_PackageComponent
    ON dbo.orgProductKardex (DocumentItemID, PackageComponentSource, PackageComponentID)
    WHERE PackageComponentSource IS NOT NULL AND PackageComponentID IS NOT NULL;
GO

CREATE OR ALTER PROCEDURE dbo.sp_SincronizarKardexPaqueteCayal
    @DocumentID INT,
    @DocumentItemID BIGINT,
    @OrderDocumentItemID INT = NULL,
    @Quitar BIT = 0,
    @UserID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @ModuleID INT, @DepotID INT, @ProductID INT, @ProductTypeID INT,
            @OrderDocumentID INT, @OrderOrigen INT, @DateDocument DATETIME,
            @CancelledOn DATETIME,
            @Source TINYINT;

    BEGIN TRY
        BEGIN TRANSACTION;

        SELECT @ModuleID = D.ModuleID, @DepotID = DI.DepotID,
               @ProductID = DI.ProductID, @ProductTypeID = P.ProductTypeID,
               @OrderDocumentID = D.OrderDocumentID,
               @OrderOrigen = DI.OrderPackageDocumentItemID,
               @DateDocument = D.DateDocument,
               @CancelledOn = D.CancelledOn
        FROM dbo.docDocumentItem DI WITH (UPDLOCK, HOLDLOCK)
        JOIN dbo.docDocument D ON D.DocumentID = DI.DocumentID
        JOIN dbo.orgProduct P ON P.ProductID = DI.ProductID
        WHERE DI.DocumentID = @DocumentID AND DI.DocumentItemID = @DocumentItemID;

        IF @ProductID IS NULL OR ISNULL(@ProductTypeID, 0) <> 3
            THROW 51001, 'La partida indicada no es un paquete promocional.', 1;

        IF @Quitar = 1
        BEGIN
            DELETE FROM dbo.orgProductKardex
            WHERE DocumentID = @DocumentID AND DocumentItemID = @DocumentItemID;
            IF @OrderOrigen IS NULL
                UPDATE dbo.docDocumentItemComponentCayal
                SET DeletedOn = SYSDATETIME(), DeletedBy = @UserID
                WHERE DocumentID = @DocumentID
                  AND DocumentItemID = @DocumentItemID AND DeletedOn IS NULL;
            COMMIT TRANSACTION;
            RETURN;
        END;

        -- Se preserva la lista de módulos que ya afecta inventario en ventas.
        IF @ModuleID NOT IN (1400, 158, 1316, 21)
        BEGIN
            COMMIT TRANSACTION;
            RETURN;
        END;

        IF @CancelledOn IS NOT NULL
            THROW 51006, 'No se puede surtir un documento cancelado.', 1;

        IF EXISTS (SELECT 1 FROM dbo.docDocumentItem
                   WHERE DocumentItemID = @DocumentItemID AND DeletedOn IS NOT NULL)
            THROW 51002, 'No se puede surtir un paquete eliminado.', 1;

        IF @OrderDocumentItemID IS NOT NULL
        BEGIN
            -- En facturas combinadas y refacturaciones la cabecera fiscal no
            -- identifica necesariamente esta orden; la partida origen sí.
            SET @OrderDocumentID = NULL;
            SELECT @OrderDocumentID = O.DocumentID
            FROM dbo.docDocumentItemOrderCayal O
            WHERE O.DocumentItemID = @OrderDocumentItemID
              AND O.ProductID = @ProductID AND O.DeletedOn IS NULL;

            IF ISNULL(@OrderDocumentID, 0) <= 0
               OR (@OrderOrigen IS NOT NULL AND @OrderOrigen <> @OrderDocumentItemID)
                THROW 51003, 'La partida origen del paquete no corresponde al documento.', 1;

            UPDATE dbo.docDocumentItem
            SET OrderPackageDocumentItemID = @OrderDocumentItemID
            WHERE DocumentItemID = @DocumentItemID;
            SET @Source = 2;
        END
        ELSE IF @OrderOrigen IS NOT NULL
        BEGIN
            SET @OrderDocumentItemID = @OrderOrigen;
            SET @OrderDocumentID = NULL;
            SELECT @OrderDocumentID = O.DocumentID
            FROM dbo.docDocumentItemOrderCayal O
            WHERE O.DocumentItemID = @OrderOrigen
              AND O.ProductID = @ProductID AND O.DeletedOn IS NULL;
            IF ISNULL(@OrderDocumentID, 0) <= 0
                THROW 51003, 'La partida origen del paquete no corresponde al documento.', 1;
            SET @Source = 2;
        END
        ELSE
            SET @Source = 1;

        CREATE TABLE #Componentes (
            ComponentID INT NOT NULL PRIMARY KEY,
            ProductID INT NOT NULL,
            Quantity DECIMAL(18, 4) NOT NULL,
            UnitPrice DECIMAL(18, 4) NOT NULL
        );

        IF @Source = 1
        BEGIN
            INSERT #Componentes (ComponentID, ProductID, Quantity, UnitPrice)
            SELECT DocumentItemComponentID, ComponentProductID,
                   SuppliedQuantity, UnitPrice
            FROM dbo.docDocumentItemComponentCayal WITH (HOLDLOCK)
            WHERE DocumentID = @DocumentID AND DocumentItemID = @DocumentItemID
              AND ParentProductID = @ProductID AND DeletedOn IS NULL;
        END
        ELSE
        BEGIN
            IF EXISTS (
                SELECT 1 FROM dbo.docDocumentItemOrderComponentCayal
                WHERE OrderDocumentID = @OrderDocumentID
                  AND DocumentItemID = @OrderDocumentItemID AND DeletedOn IS NULL
                  AND (SuppliedQuantity IS NULL OR FulfillmentRecordedOn IS NULL))
                THROW 51004, 'El paquete contiene ingredientes pendientes de surtir.', 1;

            INSERT #Componentes (ComponentID, ProductID, Quantity, UnitPrice)
            SELECT TransactionComponentID, ComponentProductID,
                   SuppliedQuantity, UnitPrice
            FROM dbo.docDocumentItemOrderComponentCayal WITH (HOLDLOCK)
            WHERE OrderDocumentID = @OrderDocumentID
              AND DocumentItemID = @OrderDocumentItemID
              AND ParentProductID = @ProductID AND DeletedOn IS NULL;
        END;

        IF NOT EXISTS (SELECT 1 FROM #Componentes)
           OR EXISTS (SELECT 1 FROM #Componentes WHERE Quantity <= 0)
            THROW 51005, 'El paquete no tiene ingredientes surtidos válidos.', 1;

        -- El kardex de una partida promocional sólo debe contener ingredientes.
        DELETE FROM dbo.orgProductKardex
        WHERE DocumentID = @DocumentID AND DocumentItemID = @DocumentItemID
          AND (PackageComponentSource IS NULL
               OR PackageComponentSource <> @Source
               OR NOT EXISTS (
                   SELECT 1 FROM #Componentes C
                   WHERE C.ComponentID = PackageComponentID));

        -- Un paquete de venta consume ingredientes aun si su precio fiscal es cero.
        UPDATE K
        SET K.DateTransaction = @DateDocument, K.DepotID = @DepotID,
            K.ProductID = C.ProductID,
            K.Quantity = -ABS(C.Quantity),
            K.QuantityToBeDelivered = 0, K.AmountPrice = C.UnitPrice
        FROM dbo.orgProductKardex K
        JOIN #Componentes C ON C.ComponentID = K.PackageComponentID
        WHERE K.DocumentID = @DocumentID AND K.DocumentItemID = @DocumentItemID
          AND K.PackageComponentSource = @Source;

        INSERT dbo.orgProductKardex
            (DateTransaction, DepotID, ProductID, DocumentID, DocumentItemID,
             Quantity, QuantityToBeDelivered, AmountPrice, Cancelled,
             ProductImportID, DepotValue, DepotValueAverage, QuantityImport,
             PackageComponentSource, PackageComponentID)
        SELECT @DateDocument, @DepotID, C.ProductID, @DocumentID, @DocumentItemID,
               -ABS(C.Quantity),
               0, C.UnitPrice, 0, 0, 0, 0, 0, @Source, C.ComponentID
        FROM #Componentes C
        WHERE NOT EXISTS (
            SELECT 1 FROM dbo.orgProductKardex K WITH (UPDLOCK, HOLDLOCK)
            WHERE K.DocumentID = @DocumentID AND K.DocumentItemID = @DocumentItemID
              AND K.PackageComponentSource = @Source
              AND K.PackageComponentID = C.ComponentID);

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

-- La captura de ventas se confirma completa en una sola transacción.
-- Requiere SQL Server 2016 o posterior (OPENJSON).
CREATE OR ALTER PROCEDURE dbo.sp_GuardarComponentesPaqueteCayal
    @DocumentID INT,
    @DocumentItemID BIGINT,
    @ParentProductID INT,
    @ComponentsJson NVARCHAR(MAX),
    @UserID INT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        IF NOT EXISTS (
            SELECT 1
            FROM dbo.docDocumentItem DI WITH (UPDLOCK, HOLDLOCK)
            JOIN dbo.orgProduct P ON P.ProductID = DI.ProductID
            WHERE DI.DocumentID = @DocumentID
              AND DI.DocumentItemID = @DocumentItemID
              AND DI.ProductID = @ParentProductID
              AND DI.DeletedOn IS NULL AND P.ProductTypeID = 3)
            THROW 51010, 'La partida fiscal del paquete no existe o no corresponde.', 1;

        DECLARE @Componentes TABLE (
            ProductComponentID INT NOT NULL PRIMARY KEY,
            ComponentProductID INT NOT NULL,
            Description NVARCHAR(255) NOT NULL,
            RequiredQuantity DECIMAL(18, 4) NOT NULL,
            SuppliedQuantity DECIMAL(18, 4) NOT NULL,
            UnitPrice DECIMAL(18, 4) NOT NULL,
            ProductKey NVARCHAR(100) NULL,
            Unit NVARCHAR(50) NULL,
            ClaveUnidad NVARCHAR(20) NULL
        );

        INSERT @Componentes
        SELECT ProductComponentID, ComponentProductID, Description,
               RequiredQuantity, SuppliedQuantity, UnitPrice,
               ProductKey, Unit, ClaveUnidad
        FROM OPENJSON(@ComponentsJson)
        WITH (
            ProductComponentID INT '$.ProductComponentID',
            ComponentProductID INT '$.ComponentProductID',
            Description NVARCHAR(255) '$.Description',
            RequiredQuantity DECIMAL(18, 4) '$.RequiredQuantity',
            SuppliedQuantity DECIMAL(18, 4) '$.SuppliedQuantity',
            UnitPrice DECIMAL(18, 4) '$.UnitPrice',
            ProductKey NVARCHAR(100) '$.ProductKey',
            Unit NVARCHAR(50) '$.Unit',
            ClaveUnidad NVARCHAR(20) '$.ClaveUnidad'
        );

        IF NOT EXISTS (SELECT 1 FROM @Componentes)
           OR EXISTS (
               SELECT 1 FROM @Componentes
               WHERE RequiredQuantity <= 0 OR SuppliedQuantity <= 0
                 OR (UPPER(ISNULL(ClaveUnidad, '')) <> 'KGM'
                     AND SuppliedQuantity <> RequiredQuantity))
            THROW 51011, 'Las cantidades surtidas del paquete no son válidas.', 1;

        -- En una edición se respeta la receta registrada originalmente.
        -- Sólo en el alta se toma la receta vigente de orgProductComponent.
        IF EXISTS (
            SELECT 1 FROM dbo.docDocumentItemComponentCayal
            WHERE DocumentItemID = @DocumentItemID AND DeletedOn IS NULL)
        BEGIN
            IF EXISTS (
                SELECT ProductComponentID, ComponentProductID,
                       RequiredQuantity, UnitPrice
                FROM dbo.docDocumentItemComponentCayal
                WHERE DocumentItemID = @DocumentItemID AND DeletedOn IS NULL
                EXCEPT
                SELECT ProductComponentID, ComponentProductID,
                       RequiredQuantity, UnitPrice FROM @Componentes)
               OR EXISTS (
                SELECT ProductComponentID, ComponentProductID,
                       RequiredQuantity, UnitPrice FROM @Componentes
                EXCEPT
                SELECT ProductComponentID, ComponentProductID,
                       RequiredQuantity, UnitPrice
                FROM dbo.docDocumentItemComponentCayal
                WHERE DocumentItemID = @DocumentItemID AND DeletedOn IS NULL)
                THROW 51012, 'No se pueden cambiar los ingredientes ni precios del paquete.', 1;
        END
        ELSE
        BEGIN
            IF EXISTS (
                SELECT PC.ProductComponentID, PC.ComponentProductID,
                       CAST(PC.Quantity * DI.Quantity AS DECIMAL(18, 4)),
                       CAST(PC.UnitPrice AS DECIMAL(18, 4))
                FROM dbo.orgProductComponent PC
                JOIN dbo.docDocumentItem DI ON DI.DocumentItemID = @DocumentItemID
                WHERE PC.ProductID = @ParentProductID
                EXCEPT
                SELECT ProductComponentID, ComponentProductID,
                       RequiredQuantity, UnitPrice FROM @Componentes)
               OR EXISTS (
                SELECT ProductComponentID, ComponentProductID,
                       RequiredQuantity, UnitPrice FROM @Componentes
                EXCEPT
                SELECT PC.ProductComponentID, PC.ComponentProductID,
                       CAST(PC.Quantity * DI.Quantity AS DECIMAL(18, 4)),
                       CAST(PC.UnitPrice AS DECIMAL(18, 4))
                FROM dbo.orgProductComponent PC
                JOIN dbo.docDocumentItem DI ON DI.DocumentItemID = @DocumentItemID
                WHERE PC.ProductID = @ParentProductID)
                THROW 51013, 'El surtido no coincide con la receta vigente del paquete.', 1;
        END;

        UPDATE dbo.docDocumentItemComponentCayal
        SET DeletedOn = SYSDATETIME(), DeletedBy = @UserID
        WHERE DocumentID = @DocumentID
          AND DocumentItemID = @DocumentItemID AND DeletedOn IS NULL;

        INSERT dbo.docDocumentItemComponentCayal
            (DocumentID, DocumentItemID, ProductComponentID, ParentProductID,
             ComponentProductID, Description, RequiredQuantity, SuppliedQuantity,
             UnitPrice, ProductKey, Unit, ClaveUnidad, CreatedBy)
        SELECT @DocumentID, @DocumentItemID, ProductComponentID, @ParentProductID,
               ComponentProductID, Description, RequiredQuantity, SuppliedQuantity,
               UnitPrice, ProductKey, Unit, ClaveUnidad, @UserID
        FROM @Componentes;

        EXEC dbo.sp_SincronizarKardexPaqueteCayal
            @DocumentID, @DocumentItemID, NULL, 0;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
END;
GO

-- Cubre también las bajas lógicas realizadas fuera de estas dos interfaces.
CREATE OR ALTER TRIGGER dbo.tr_DocumentItemPackage_KardexDelete
ON dbo.docDocumentItem
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT UPDATE(DeletedOn) RETURN;

    DELETE K
    FROM dbo.orgProductKardex K
    JOIN inserted I ON I.DocumentItemID = K.DocumentItemID
                   AND I.DocumentID = K.DocumentID
    JOIN deleted D ON D.DocumentItemID = I.DocumentItemID
    JOIN dbo.orgProduct P ON P.ProductID = I.ProductID
    WHERE D.DeletedOn IS NULL AND I.DeletedOn IS NOT NULL
      AND P.ProductTypeID = 3;
END;
GO

-- La cancelación de la cabecera no siempre elimina lógicamente sus partidas.
CREATE OR ALTER TRIGGER dbo.tr_DocumentPackage_KardexCancel
ON dbo.docDocument
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT UPDATE(CancelledOn) RETURN;

    UPDATE K SET Cancelled = 1
    FROM dbo.orgProductKardex K
    JOIN inserted I ON I.DocumentID = K.DocumentID
    JOIN deleted D ON D.DocumentID = I.DocumentID
    WHERE D.CancelledOn IS NULL AND I.CancelledOn IS NOT NULL
      AND K.PackageComponentSource IN (1, 2);
END;
GO
