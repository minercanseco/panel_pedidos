SET XACT_ABORT ON;
BEGIN TRANSACTION;

IF OBJECT_ID(N'dbo.CustomerFollowUpCayal', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.CustomerFollowUpCayal
    (
        CustomerFollowUpID INT IDENTITY(1, 1) NOT NULL
            CONSTRAINT PK_CustomerFollowUpCayal PRIMARY KEY,
        BusinessEntityID INT NOT NULL,
        UserID INT NOT NULL,
        FollowUpReasonID INT NOT NULL,
        Comments NVARCHAR(1000) NOT NULL,
        Recovered BIT NOT NULL
            CONSTRAINT DF_CustomerFollowUpCayal_Recovered DEFAULT (0),
        CreatedOn DATETIME2(0) NOT NULL
            CONSTRAINT DF_CustomerFollowUpCayal_CreatedOn DEFAULT (SYSDATETIME())
    );
END;

IF COL_LENGTH(N'dbo.CustomerFollowUpCayal', N'FollowUpReasonID') IS NULL
BEGIN
    ALTER TABLE dbo.CustomerFollowUpCayal
        ADD FollowUpReasonID INT NULL;
END;

COMMIT TRANSACTION;
