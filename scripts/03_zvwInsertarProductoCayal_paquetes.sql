-- Basado en la definición de zvwInsertarProductoCayal proporcionada.
-- Aplicar después de 02_kardex_componentes_paquete.sql y comparar con
-- la definición activa de cada base antes del despliegue.
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE OR ALTER PROCEDURE [dbo].[zvwInsertarProductoCayal]
    @DocumentID INT,
    @ProductID INT,
    @DepotID INT,
    @Cantidad FLOAT,
    @Precio FLOAT,
    @Costo FLOAT,
    @Total FLOAT,
    @TipoCaptura INT,
    @ModuleID INT,
    @Comments NVARCHAR(MAX) = NULL,
    -- Parámetros opcionales exclusivos para compras (ModuleID = 152).
    -- DiscountPerc se recibe como factor: 2.25 % = 0.0225.
    @DiscountPerc DECIMAL(19, 18) = 0,
    @ApplyGlobalDiscount BIT = 0,
    @ProductSupplierKey NVARCHAR(100) = NULL,
    @SupplierBusinessEntityID INT = 0,
    @ExpenseTypeID INT = 0,
    @DateItem DATETIME = NULL,
    -- Cero inserta una partida; un valor existente actualiza esa partida.
    @DocumentItemID BIGINT = 0,
    @IsComponent SMALLINT = 0,
    @OrderComponentTransactionID INT = NULL,
    @OrderPackageDocumentItemID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @LineNumber INT;
    DECLARE @EsActualizacion BIT = CASE
        WHEN ISNULL(@DocumentItemID, 0) <> 0 THEN 1
        ELSE 0
    END;

    DECLARE @ProductTypeID INT;
    DECLARE @ProductName NVARCHAR(MAX);
    DECLARE @TaxTypeID INT;
    DECLARE @TaxPerc DECIMAL(19, 6);
    DECLARE @ProductKey NVARCHAR(100);
    DECLARE @Unit NVARCHAR(100);
    DECLARE @ClaveUnidad NVARCHAR(100);

    BEGIN TRY
        BEGIN TRANSACTION;

        /*
        Validar que el documento exista y que el módulo recibido
        corresponda con el módulo del documento.
        */
        IF NOT EXISTS (
            SELECT 1
            FROM dbo.docDocument
            WHERE DocumentID = @DocumentID
        )
        BEGIN
            THROW 50001, 'El documento indicado no existe.', 1;
        END;

        IF NOT EXISTS (
            SELECT 1
            FROM dbo.docDocument
            WHERE DocumentID = @DocumentID
              AND ModuleID = @ModuleID
        )
        BEGIN
            THROW 50002,
                'El ModuleID recibido no corresponde con el documento.',
                1;
        END;

        /*
        Obtener la información del producto antes de insertar.
        */
        SELECT
            @ProductTypeID = P.ProductTypeID,
            @ProductName = P.ProductName,
            @TaxTypeID = P.TaxTypeID,
            @TaxPerc = P.TaxPerc,
            @ProductKey = P.ProductKey,
            @Unit = P.Unit,
            @ClaveUnidad = P.ClaveUnidad
        FROM dbo.orgProduct AS P
        WHERE P.ProductID = @ProductID;

        IF @ProductName IS NULL
        BEGIN
            THROW 50003, 'El producto indicado no existe.', 1;
        END;

        IF @ModuleID = 152
           AND (ISNULL(@DiscountPerc, 0) < 0 OR ISNULL(@DiscountPerc, 0) > 1)
        BEGIN
            THROW 50005,
                'DiscountPerc debe ser un factor entre 0 y 1.',
                1;
        END;

        IF @ModuleID = 152
           AND ISNULL(@SupplierBusinessEntityID, 0) < 0
        BEGIN
            THROW 50006,
                'SupplierBusinessEntityID no puede ser negativo.',
                1;
        END;

        IF ISNULL(@DocumentItemID, 0) <> 0
           AND NOT EXISTS (
                SELECT 1
                FROM dbo.docDocumentItem AS DI
                WHERE DI.DocumentItemID = @DocumentItemID
                  AND DI.DocumentID = @DocumentID
                  AND DI.DeletedOn IS NULL
           )
        BEGIN
            THROW 50007,
                'La partida no existe, está eliminada o no pertenece al documento.',
                1;
        END;

        -- Un paquete surtido no puede convertirse en otro producto mediante
        -- la edición genérica: dejaría movimientos de ingredientes ajenos.
        IF @ModuleID IN (1400, 158, 1316, 21)
           AND @EsActualizacion = 1
           AND EXISTS (
               SELECT 1
               FROM dbo.docDocumentItem DI
               JOIN dbo.orgProduct P ON P.ProductID = DI.ProductID
               WHERE DI.DocumentItemID = @DocumentItemID
                 AND DI.DocumentID = @DocumentID
                 AND DI.ProductID <> @ProductID
                 AND (P.ProductTypeID = 3 OR @ProductTypeID = 3)
           )
            THROW 50008,
                'No se puede cambiar el producto de una partida de paquete.',
                1;

        IF ISNULL(@DocumentItemID, 0) <> 0
        BEGIN
            UPDATE DI
            SET
                DI.Quantity = @Cantidad,
                DI.ProductID = @ProductID,
                DI.Description = @ProductName,
                DI.DiscountPerc = CASE
                    WHEN @ModuleID = 152
                        THEN ISNULL(@DiscountPerc, 0)
                    ELSE 0
                END,
                DI.TaxTypeID = @TaxTypeID,
                DI.TaxPerc = ISNULL(@TaxPerc, 0),
                DI.UnitPrice = CASE
                    WHEN ISNULL(@Precio, 0) = 0
                        THEN ISNULL(@Costo, 0)
                    ELSE @Precio
                END,
                DI.Total = @Total,
                DI.CostPrice = ISNULL(@Costo, 0),
                DI.ApplyGlobalDiscount = CASE
                    WHEN @ModuleID = 152
                        THEN ISNULL(@ApplyGlobalDiscount, 0)
                    ELSE 0
                END,
                DI.ProductKey = @ProductKey,
                DI.ProductSupplierKey = CASE
                    WHEN @ModuleID = 152
                        THEN NULLIF(@ProductSupplierKey, '')
                    ELSE NULL
                END,
                DI.SupplierBusinessEntityID = CASE
                    WHEN @ModuleID = 152
                        THEN ISNULL(@SupplierBusinessEntityID, 0)
                    ELSE 0
                END,
                DI.ExpenseTypeID = CASE
                    WHEN @ModuleID = 152
                        THEN ISNULL(@ExpenseTypeID, 0)
                    ELSE 0
                END,
                -- Si no se recibe fecha durante una edición, se conserva.
                DI.DateItem = CASE
                    WHEN @ModuleID = 152
                        THEN COALESCE(@DateItem, DI.DateItem, GETDATE())
                    ELSE DI.DateItem
                END,
                DI.Comments = @Comments,
                DI.DepotID = @DepotID,
                DI.Unit = @Unit,
                DI.ClaveUnidad = @ClaveUnidad,
                DI.ObjetoImpuesto = '02',
                DI.TipoCaptura = @TipoCaptura,
                DI.OrderPackageDocumentItemID = COALESCE(
                    @OrderPackageDocumentItemID, DI.OrderPackageDocumentItemID
                )
            FROM dbo.docDocumentItem AS DI
            WHERE DI.DocumentItemID = @DocumentItemID
              AND DI.DocumentID = @DocumentID
              AND DI.DeletedOn IS NULL;
        END
        ELSE
        BEGIN

        /*
        Calcular el siguiente número de línea.

        UPDLOCK y HOLDLOCK reducen el riesgo de que dos procesos
        asignen simultáneamente el mismo LineNumber.
        */
        SELECT
            @LineNumber = ISNULL(MAX(DocumentItem.LineNumber), 0) + 1
        FROM dbo.docDocumentItem AS DocumentItem
            WITH (UPDLOCK, HOLDLOCK)
        WHERE DocumentItem.DocumentID = @DocumentID
          AND DocumentItem.DeletedOn IS NULL;

        /*
        Insertar la partida.

        Cambios principales:
        - CostPrice recibe @Costo.
        - DepotID recibe @DepotID.
        */
        INSERT INTO dbo.docDocumentItem
        (
            DocumentID,
            Quantity,
            ProductID,
            Description,
            DiscountPerc,
            TaxTypeID,
            TaxPerc,
            RetentionPerc,
            UnitPrice,
            Total,
            MustBeDelivered,
            CostPrice,
            LineNumber,
            DeletedBy,
            DeliverDocumentItemID,
            ApplyGlobalDiscount,
            ProductKey,
            ProductSupplierKey,
            CostCenterID,
            SupplierBusinessEntityID,
            ExpenseTypeID,
            DateItem,
            RetentionTypeID,
            StatusID,
            ContactEmployeeID,
            AssistantEmployeeID,
            WorkAreaID,
            ColorMixDocumentID,
            IsConsigned,
            Comments,
            DeductiblePerc,
            IsBusinessOperation,
            Refund,
            Promocion,
            CurrencyID,
            DepotID,
            EmployeeContactID,
            AltID,
            QuantityInventory,
            CorporateAmount,
            ExtraCommission,
            PayrollTypeID,
            Exento,
            Gravado,
            Unit,
            IEPSPerc,
            FinancialEntityID,
            Sector,
            ProductImportID,
            SourceDocumentID,
            CantidadGarantia,
            IEPSAmount,
            IVABase,
            IEPSNoDesglosado,
            CoefUnit,
            ClaveUnidad,
            SourceDocumentItemID,
            IsConsignmentNote,
            ObjetoImpuesto,
            TipoCaptura,
            OrderPackageDocumentItemID
        )
        VALUES
        (
            @DocumentID,                       -- DocumentID
            @Cantidad,                         -- Quantity
            @ProductID,                        -- ProductID
            @ProductName,                      -- Description
            CASE
                WHEN @ModuleID = 152
                    THEN ISNULL(@DiscountPerc, 0)
                ELSE 0
            END,                               -- DiscountPerc
            @TaxTypeID,                        -- TaxTypeID
            ISNULL(@TaxPerc, 0),               -- TaxPerc
            0,                                 -- RetentionPerc

            CASE
                WHEN ISNULL(@Precio, 0) = 0
                    THEN ISNULL(@Costo, 0)
                ELSE @Precio
            END,                               -- UnitPrice

            @Total,                            -- Total
            1,                                 -- MustBeDelivered
            ISNULL(@Costo, 0),                 -- CostPrice
            @LineNumber,                       -- LineNumber
            0,                                 -- DeletedBy
            0,                                 -- DeliverDocumentItemID
            CASE
                WHEN @ModuleID = 152
                    THEN ISNULL(@ApplyGlobalDiscount, 0)
                ELSE 0
            END,                               -- ApplyGlobalDiscount
            @ProductKey,                       -- ProductKey
            CASE
                WHEN @ModuleID = 152
                    THEN NULLIF(@ProductSupplierKey, '')
                ELSE NULL
            END,                               -- ProductSupplierKey
            0,                                 -- CostCenterID
            CASE
                WHEN @ModuleID = 152
                    THEN ISNULL(@SupplierBusinessEntityID, 0)
                ELSE 0
            END,                               -- SupplierBusinessEntityID
            CASE
                WHEN @ModuleID = 152
                    THEN ISNULL(@ExpenseTypeID, 0)
                ELSE 0
            END,                               -- ExpenseTypeID
            CASE
                WHEN @ModuleID = 152
                    THEN ISNULL(@DateItem, GETDATE())
                ELSE GETDATE()
            END,                               -- DateItem
            0,                                 -- RetentionTypeID
            0,                                 -- StatusID
            0,                                 -- ContactEmployeeID
            0,                                 -- AssistantEmployeeID
            0,                                 -- WorkAreaID
            0,                                 -- ColorMixDocumentID
            0,                                 -- IsConsigned
            @Comments,                         -- Comments
            0,                                 -- DeductiblePerc
            0,                                 -- IsBusinessOperation
            0,                                 -- Refund
            0,                                 -- Promocion
            0,                                 -- CurrencyID
            @DepotID,                          -- DepotID
            0,                                 -- EmployeeContactID
            0,                                 -- AltID
            0,                                 -- QuantityInventory
            0,                                 -- CorporateAmount
            0,                                 -- ExtraCommission
            0,                                 -- PayrollTypeID
            0,                                 -- Exento
            0,                                 -- Gravado
            @Unit,                             -- Unit
            0,                                 -- IEPSPerc
            0,                                 -- FinancialEntityID
            0,                                 -- Sector
            0,                                 -- ProductImportID
            0,                                 -- SourceDocumentID
            0,                                 -- CantidadGarantia
            0,                                 -- IEPSAmount
            0,                                 -- IVABase
            0,                                 -- IEPSNoDesglosado
            0,                                 -- CoefUnit
            @ClaveUnidad,                      -- ClaveUnidad
            0,                                 -- SourceDocumentItemID
            0,                                 -- IsConsignmentNote
            '02',                              -- ObjetoImpuesto
            @TipoCaptura,                      -- TipoCaptura
            @OrderPackageDocumentItemID        -- OrderPackageDocumentItemID
        );

        SET @DocumentItemID = CONVERT(
            BIGINT,
            SCOPE_IDENTITY()
        );

        IF @DocumentItemID IS NULL
        BEGIN
            THROW 50004,
                'No fue posible obtener el identificador de la partida.',
                1;
        END;
        END;

        /*
        Generar el movimiento de kardex para los módulos autorizados.
        */
        IF @ModuleID IN (
            1400,
            202,
            203,
            158,
            1316,
            21,
            152
        )
           AND NOT (@ProductTypeID = 3 AND @ModuleID IN (1400, 158, 1316, 21))
        BEGIN
            IF @EsActualizacion = 1
            BEGIN
                UPDATE K
                SET
                    K.DateTransaction = D.DateDocument,
                    K.DepotID = @DepotID,
                    K.ProductID = DI.ProductID,
                    K.Quantity = CASE
                        WHEN @ModuleID IN (152, 202)
                            THEN ABS(DI.Quantity)
                        WHEN @ModuleID = 203
                            THEN ABS(DI.Quantity) * -1
                        WHEN ISNULL(@Precio, 0) = 0
                            THEN ABS(DI.Quantity)
                        ELSE ABS(DI.Quantity) * -1
                    END,
                    K.QuantityToBeDelivered = 0,
                    K.AmountPrice = CASE
                        WHEN @ModuleID IN (202, 203)
                        THEN CASE
                            WHEN ISNULL(@Costo, 0) > 0
                                THEN @Costo
                            ELSE ISNULL(@Precio, 0)
                        END
                        WHEN ISNULL(@Precio, 0) = 0
                            THEN ISNULL(@Costo, 0)
                        ELSE @Precio
                    END
                FROM dbo.orgProductKardex AS K
                INNER JOIN dbo.docDocumentItem AS DI
                    ON DI.DocumentItemID = K.DocumentItemID
                   AND DI.DocumentID = K.DocumentID
                INNER JOIN dbo.docDocument AS D
                    ON D.DocumentID = DI.DocumentID
                WHERE K.DocumentID = @DocumentID
                  AND K.DocumentItemID = @DocumentItemID;
            END
            ELSE
            BEGIN
            INSERT INTO dbo.orgProductKardex
            (
                DateTransaction,
                DepotID,
                ProductID,
                DocumentID,
                DocumentItemID,
                Quantity,
                QuantityToBeDelivered,
                AmountPrice,
                Cancelled,
                ProductImportID,
                DepotValue,
                DepotValueAverage,
                QuantityImport
            )
            SELECT
                D.DateDocument,
                @DepotID,
                DI.ProductID,
                @DocumentID,
                @DocumentItemID,

                CASE
                    WHEN @ModuleID IN(152, 202)
                        THEN ABS(DI.Quantity)

                    WHEN @ModuleID = 203
                        THEN ABS(DI.Quantity) * -1

                    WHEN ISNULL(@Precio, 0) = 0
                        THEN ABS(DI.Quantity)

                    ELSE ABS(DI.Quantity) * -1
                END,

                0,

                CASE
                    WHEN @ModuleID IN (202, 203)
                    THEN
                        CASE
                            WHEN ISNULL(@Costo, 0) > 0
                                THEN @Costo
                            ELSE ISNULL(@Precio, 0)
                        END

                    WHEN ISNULL(@Precio, 0) = 0
                        THEN ISNULL(@Costo, 0)

                    ELSE @Precio
                END,

                0, -- Cancelled
                0, -- ProductImportID
                0, -- DepotValue
                0, -- DepotValueAverage
                0  -- QuantityImport

            FROM dbo.docDocumentItem AS DI
            INNER JOIN dbo.docDocument AS D
                ON D.DocumentID = DI.DocumentID
            WHERE DI.DocumentID = @DocumentID
              AND DI.DocumentItemID = @DocumentItemID;
            END;
        END;

        -- En documentos nacidos de pedidos el detalle de surtido ya existe:
        -- la partida fiscal y el kardex se confirman en la misma transacción.
        IF @OrderPackageDocumentItemID IS NOT NULL
        BEGIN
            IF @ModuleID <> 21 OR ISNULL(@ProductTypeID, 0) <> 3
                THROW 50009,
                    'La partida origen sólo aplica a paquetes de facturación.',
                    1;

            EXEC dbo.sp_SincronizarKardexPaqueteCayal
                @DocumentID, @DocumentItemID,
                @OrderPackageDocumentItemID, 0;
        END;

        COMMIT TRANSACTION;

        SELECT
            @DocumentItemID AS DocumentItemID;

    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        THROW;
    END CATCH;
END;
GO
