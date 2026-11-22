-- Actualización compatible con impresión y Saldar cartera.
-- Ejecutar en la base de datos del ERP; sustituye la versión anterior.
-- Debt, DocumentsWithBalance y antigüedad: TODOS los pendientes de cobro.
-- CreditDebt: deuda que consume crédito; excluye Mayoreo de contado en reparto.
-- RemainingCredit: límite autorizado menos CreditDebt.
-- CreditDebt se agrega al final para conservar el orden de columnas existentes.

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

ALTER FUNCTION [dbo].[zvwBuscarInfoCliente-BusinessEntityID]
(
    @BusinessEntityID INT
)
RETURNS TABLE
AS
RETURN
(
    SELECT
        E.BusinessEntityID,
        C.CustomerID,
        E.CommercialName,
        E.OfficialName,
        Z.ZoneName,
        C.FormaPago,
        C.MetodoPago,
        C.ReceptorUsoCFDI,
        EM.OfficialNumber,
        E.Custom3            AS OfficialNumberBackup,
        E.CIDCayal           AS Cif,
        C.Reference,
        Debe.Saldo           AS Debt,
        Z.ZoneID,
        C.CustomerTypeID,
        CT.CustomerTypeName,
        C.PaymentTermID      AS PaymentTermID,

        CASE WHEN CMAntigua.Folio IS NULL THEN '' ELSE CMAntigua.Folio END AS OldestPurchaseFolio,
        CASE WHEN CMAntigua.Dias  IS NULL THEN '' ELSE CMAntigua.Dias  END AS OldestPurchaseDays,

        CASE WHEN E.Custom4 IS NULL THEN 0 ELSE E.Custom4 END AS StoreCredit,

        CASE WHEN E.CompanyTypeName IS NULL THEN 'NO DEFINIDO' ELSE E.CompanyTypeName END AS CompanyTypeName,
         E.ResRegimenFiscal  CompanyTypeNameBackup,

        CASE WHEN C.CreditLimit IS NULL THEN 0
             ELSE CAST(ROUND(CONVERT(MONEY, C.CreditLimit, 1), 2, 0) AS DECIMAL(18,2))
        END AS AuthorizedCredit,

        CASE WHEN C.CreditLimit IS NULL THEN 0
             ELSE CAST(ROUND(CONVERT(MONEY, C.CreditLimit - ISNULL(CreditoUtilizado.Saldo, 0), 1), 2, 0) AS DECIMAL(18,2))
        END AS RemainingCredit,

        CASE WHEN C.ComentarioCredito IS NULL THEN '' ELSE C.ComentarioCredito END AS CreditComments,

        CASE
            WHEN EM.OfficialNumber = 'XAXX010101000' AND Z.ZoneID = 1040
              OR (EM.OfficialNumber = 'XAXX010101000' AND C.CreditLimit IS NOT NULL AND C.CreditLimit > 0 AND E.Custom3 IS NULL) THEN 1
            WHEN E.Custom3 IS NULL AND EM.OfficialNumber = 'XAXX010101000' THEN 0
            WHEN LEN(E.Custom3) = 0 AND EM.OfficialNumber = 'XAXX010101000' THEN 0
            ELSE 2
        END AS CayalCustomerTypeID,

        CASE WHEN SC.Usuario IS NULL THEN 0 ELSE 1 END AS CreditBlock,

        CASE WHEN TP.PaymentTermName IS NULL THEN 'NO DEFINIDO' ELSE TP.PaymentTermName END AS PaymentTermName,

        EM.AddressFiscalDetailID,
        EM.AddressFiscalCity,
        EM.AddressFiscalZipCode,
        EM.AddressFiscalMunicipality,
        EM.AddressFiscalStateProvince,
        EM.AddressFiscalStreet,
        EM.AddressFiscalExtNumber,
        EM.AddressFiscalComments,

        Correo       AS Email,
        TelCasa      AS Phone,
        TelCel       AS CellPhone,
        C.CustomerCategory,
        C.DeliveryTypeID,
        Direcciones.Addresses,
        ISNULL(Sucursales.Depots, 0) AS Depots,
        docs.Documentos              AS DocumentsWithBalance,

        ISNULL(CargoEnvio.CargoEnvio, 0) AS DeliveryCost,
        ISNULL(Vales.Docs, 0)              AS Coupons,
        CONVERT(DECIMAL(18,2), ISNULL(Vales.Total, 0)) AS CouponsMountDebt,
        CAST(ISNULL(C.CouponsMount, 0) AS DECIMAL(18,2)) AS CouponsMount,
        CAST(
    ISNULL(C.CouponsMount, 0) 
    - ISNULL(Vales.Total, 0) 
AS DECIMAL(18,2)) AS RemainingCoupons,
ISNULL(E.Vales,0) AS CouponsBlock,
        CAST(ISNULL(CreditoUtilizado.Saldo, 0) AS DECIMAL(18,2)) AS CreditDebt


    FROM orgCustomer C
    INNER JOIN orgBusinessEntity          E  ON C.BusinessEntityID = E.BusinessEntityID
    INNER JOIN orgZone                    Z  ON C.ZoneID          = Z.ZoneID
    INNER JOIN orgBusinessEntityMainInfo  EM ON E.BusinessEntityID = EM.BusinessEntityID

    LEFT OUTER JOIN (
        SELECT @BusinessEntityID AS BusinessEntityID, DB.Saldo
        FROM (
            SELECT CASE WHEN SUM(D.Balance) IS NULL THEN 0
                        ELSE SUM(CAST(ROUND(CONVERT(MONEY, D.Balance, 1), 2, 0) AS DECIMAL(18,2)))
                   END AS Saldo
            FROM docDocument D
            LEFT OUTER JOIN docDocumentExt X ON D.DocumentID = X.IDExtra
            WHERE
                (
                    D.CancelledOn IS NULL
                    AND D.StatusPaidID <> 1
                    AND D.BusinessEntityID = @BusinessEntityID
                    AND D.ModuleID IN (21, 1400, 1319)
                )
                OR
                (
                    D.CancelledOn IS NULL
                    AND D.StatusPaidID <> 1
                    AND D.Balance <> 0
                    AND X.CustomerID = @BusinessEntityID
                    AND D.ModuleID IN (21, 1400, 1319)
                )
        ) AS DB
    ) AS Debe
        ON C.BusinessEntityID = Debe.BusinessEntityID

    LEFT OUTER JOIN (
        SELECT @BusinessEntityID AS BusinessEntityID, DB.Saldo
        FROM (
            SELECT CASE WHEN SUM(D.Balance) IS NULL THEN 0
                        ELSE SUM(CAST(ROUND(CONVERT(MONEY, D.Balance, 1), 2, 0) AS DECIMAL(18,2)))
                   END AS Saldo
            FROM docDocument D
            LEFT OUTER JOIN docDocumentExt X ON D.DocumentID = X.IDExtra
            WHERE
                (
                    D.CancelledOn IS NULL
                    AND D.StatusPaidID <> 1
                    AND D.BusinessEntityID = @BusinessEntityID
                    AND D.ModuleID IN (21, 1400, 1319)
                AND NOT EXISTS (
                    SELECT 1
                    FROM dbo.docDocumentOrderCayal AS PedidoContado
                    WHERE D.ModuleID = 21
                      AND PedidoContado.OrderDocumentID = D.OrderDocumentID
                      AND PedidoContado.WayToPayID > 0
                      AND PedidoContado.WayToPayID <> 5
                )
                )
                OR
                (
                    D.CancelledOn IS NULL
                    AND D.StatusPaidID <> 1
                    AND D.Balance <> 0
                    AND X.CustomerID = @BusinessEntityID
                    AND D.ModuleID IN (21, 1400, 1319)
                AND NOT EXISTS (
                    SELECT 1
                    FROM dbo.docDocumentOrderCayal AS PedidoContado
                    WHERE D.ModuleID = 21
                      AND PedidoContado.OrderDocumentID = D.OrderDocumentID
                      AND PedidoContado.WayToPayID > 0
                      AND PedidoContado.WayToPayID <> 5
                )
                )
        ) AS DB
    ) AS CreditoUtilizado
        ON C.BusinessEntityID = CreditoUtilizado.BusinessEntityID

    LEFT OUTER JOIN (
        SELECT
            @BusinessEntityID AS BusinessEntityID,
            ISNULL(D.FolioPrefix, '') + ISNULL(D.Folio, '') AS Folio,
            DATEDIFF(DAY, D.CreatedOn, GETDATE())           AS Dias
        FROM (
            SELECT CASE WHEN MIN(D.DocumentID) IS NULL THEN 0 ELSE MIN(D.DocumentID) END AS Documento
            FROM docDocument D
            LEFT OUTER JOIN docDocumentExt X ON D.DocumentID = X.IDExtra
            WHERE
                (
                    D.CancelledOn IS NULL
                    AND D.StatusPaidID <> 1
                    AND D.Balance <> 0
                    AND D.BusinessEntityID = @BusinessEntityID
                    AND D.ModuleID IN (21, 1400, 1319)
                )
                OR
                (
                    D.CancelledOn IS NULL
                    AND D.StatusPaidID <> 1
                    AND D.Balance <> 0
                    AND X.CustomerID = @BusinessEntityID
                    AND D.ModuleID IN (21, 1400, 1319)
                )
        ) AS DB
        INNER JOIN docDocument D ON DB.Documento = D.DocumentID
    ) AS CMAntigua
        ON C.BusinessEntityID = CMAntigua.BusinessEntityID

    LEFT OUTER JOIN orgCustomerType  CT ON C.CustomerTypeID = CT.CustomerTypeID
    LEFT OUTER JOIN engPaymentTerm   TP ON C.PaymentTermID  = TP.PaymentTermID
    LEFT OUTER JOIN dbo.zvwStatusCreditoCayal AS SC ON C.BusinessEntityID = SC.IDEmpresa

    LEFT OUTER JOIN (
        SELECT Correo.BusinessEntityID,
               CASE WHEN Correo.ChannelValue IS NULL THEN '' ELSE Correo.ChannelValue END AS Correo
        FROM orgCommunicationChannel Correo
        WHERE Correo.BusinessEntityID = @BusinessEntityID
          AND Correo.ChannelTypeID = 1
          AND Correo.DeletedOn IS NULL
    ) Crr ON E.BusinessEntityID = Crr.BusinessEntityID

    LEFT OUTER JOIN (
        SELECT TelCasa.BusinessEntityID,
               CASE WHEN TelCasa.ChannelValue IS NULL THEN '' ELSE TelCasa.ChannelValue END AS TelCasa
        FROM orgCommunicationChannel TelCasa
        WHERE TelCasa.BusinessEntityID = @BusinessEntityID
          AND TelCasa.ChannelTypeID = 2
          AND TelCasa.DeletedOn IS NULL
    ) TC ON E.BusinessEntityID = TC.BusinessEntityID

    LEFT OUTER JOIN (
        SELECT TelCel.BusinessEntityID,
               CASE WHEN TelCel.ChannelValue IS NULL THEN '' ELSE TelCel.ChannelValue END AS TelCel
        FROM orgCommunicationChannel TelCel
        WHERE TelCel.BusinessEntityID = @BusinessEntityID
          AND TelCel.ChannelTypeID = 3
          AND TelCel.DeletedOn IS NULL
    ) TCel ON E.BusinessEntityID = TCel.BusinessEntityID

    LEFT OUTER JOIN (
        SELECT COUNT(AddressID) AS Addresses, BusinessEntityID
        FROM orgAddress
        WHERE BusinessEntityID = @BusinessEntityID
          AND DeletedOn IS NULL
        GROUP BY BusinessEntityID
    ) Direcciones ON E.BusinessEntityID = Direcciones.BusinessEntityID

    LEFT OUTER JOIN (
        SELECT COUNT(DepotID) AS Depots, BusinessEntityID
        FROM orgDepot
        WHERE BusinessEntityID = @BusinessEntityID
          AND DeletedOn IS NULL
        GROUP BY BusinessEntityID
    ) Sucursales ON E.BusinessEntityID = Sucursales.BusinessEntityID

    LEFT OUTER JOIN (
        SELECT
            COUNT(D.DocumentID) AS Documentos,
            @BusinessEntityID   AS BusinessEntityID
        FROM docDocument D
        LEFT OUTER JOIN docDocumentExt X ON D.DocumentID = X.IDExtra
        WHERE
            (
                D.CancelledOn IS NULL
                AND D.StatusPaidID <> 1
                AND D.Balance <> 0
                AND D.BusinessEntityID = @BusinessEntityID
                AND D.ModuleID IN (21, 1400, 1319)
            )
            OR
            (
                D.CancelledOn IS NULL
                AND D.StatusPaidID <> 1
                AND D.Balance <> 0
                AND X.CustomerID = @BusinessEntityID
                AND D.ModuleID IN (21, 1400, 1319)
            )
    ) docs ON E.BusinessEntityID = docs.BusinessEntityID

    -- Vales (mes y año actuales, devolviendo 0 si no hay filas)
    LEFT OUTER JOIN (
        SELECT
            COALESCE(COUNT(DocumentID), 0) AS Docs,
            COALESCE(SUM(Total), 0)        AS Total,
            BusinessEntityID
        FROM docDocument
        WHERE ModuleID = 1692
          AND BusinessEntityID = @BusinessEntityID
          AND CancelledOn IS NULL
          AND COALESCE(DATEPART(MONTH, CreatedOn), 0) = DATEPART(MONTH, GETDATE())
          AND COALESCE(DATEPART(YEAR,  CreatedOn), 0) = DATEPART(YEAR,  GETDATE())
        GROUP BY BusinessEntityID
    ) Vales ON E.BusinessEntityID = Vales.BusinessEntityID

    -- Cargo de envío (función table-valued con guion en el nombre)
    OUTER APPLY (
        SELECT TOP (1) *
        FROM dbo.[zvwBuscarCargoEnvio-AddressDetailID](
            (SELECT AddressFiscalDetailID
             FROM orgBusinessEntityMainInfo
             WHERE BusinessEntityID = @BusinessEntityID)
        )
    ) CargoEnvio

    WHERE E.BusinessEntityID = @BusinessEntityID
);
GO
