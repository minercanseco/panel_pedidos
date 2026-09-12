SET XACT_ABORT ON;
GO

IF OBJECT_ID('dbo.docDocumentItemComponentCayal', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.docDocumentItemComponentCayal (
        DocumentItemComponentID INT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_docDocumentItemComponentCayal PRIMARY KEY,
        DocumentID INT NOT NULL,
        DocumentItemID INT NOT NULL,
        ProductComponentID INT NOT NULL,
        ParentProductID INT NOT NULL,
        ComponentProductID INT NOT NULL,
        Description NVARCHAR(255) NOT NULL,
        RequiredQuantity DECIMAL(18,4) NOT NULL,
        SuppliedQuantity DECIMAL(18,4) NOT NULL,
        UnitPrice DECIMAL(18,4) NOT NULL,
        ProductKey NVARCHAR(100) NULL,
        Unit NVARCHAR(50) NULL,
        ClaveUnidad NVARCHAR(20) NULL,
        CreatedBy INT NOT NULL,
        CreatedOn DATETIME2(3) NOT NULL
            CONSTRAINT DF_DocumentItemComponent_CreatedOn
            DEFAULT SYSDATETIME(),
        DeletedBy INT NULL,
        DeletedOn DATETIME2(3) NULL,
        CONSTRAINT FK_DocumentItemComponent_Document
            FOREIGN KEY (DocumentID) REFERENCES dbo.docDocument(DocumentID),
        CONSTRAINT FK_DocumentItemComponent_DocumentItem
            FOREIGN KEY (DocumentItemID)
            REFERENCES dbo.docDocumentItem(DocumentItemID),
        CONSTRAINT CK_DocumentItemComponent_Required_Positive
            CHECK (RequiredQuantity > 0),
        CONSTRAINT CK_DocumentItemComponent_Supplied_Positive
            CHECK (
                SuppliedQuantity > 0
                AND (
                    UPPER(ISNULL(ClaveUnidad, '')) = 'KGM'
                    OR SuppliedQuantity = RequiredQuantity
                )
            )
    );
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID('dbo.docDocumentItemComponentCayal')
      AND name = 'UX_DocumentItemComponent_Active'
)
BEGIN
    CREATE UNIQUE INDEX UX_DocumentItemComponent_Active
        ON dbo.docDocumentItemComponentCayal
           (DocumentItemID, ProductComponentID)
        WHERE DeletedOn IS NULL;
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE object_id = OBJECT_ID('dbo.docDocumentItemComponentCayal')
      AND name = 'IX_DocumentItemComponent_Document'
)
BEGIN
    CREATE INDEX IX_DocumentItemComponent_Document
        ON dbo.docDocumentItemComponentCayal
           (DocumentID, DocumentItemID, DeletedOn)
        INCLUDE (ComponentProductID, RequiredQuantity, SuppliedQuantity);
END;
GO
