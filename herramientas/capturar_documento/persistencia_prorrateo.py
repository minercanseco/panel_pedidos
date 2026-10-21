def revertir_prorrateo_maniobras(
        base_de_datos, document_id, operation_id, user_id
):
    """Restaura una operacion usando Total de docDocumentItem."""
    if not document_id or not operation_id:
        raise ValueError(
            'Se requieren DocumentID y OperationID para revertir.'
        )

    sql = """
    SET XACT_ABORT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        UPDATE I
        SET I.Quantity = P.Quantity,
            I.UnitPrice = P.UnitPriceBefore,
            I.CostPrice = P.CostPriceBefore,
            I.Total = P.SubTotalBefore,
            I.DiscountPerc = P.DiscountPerc,
            I.DeletedOn = CASE
                WHEN P.IsManeuverItem = 1 THEN NULL
                ELSE I.DeletedOn
            END,
            I.DeletedBy = CASE
                WHEN P.IsManeuverItem = 1 THEN NULL
                ELSE I.DeletedBy
            END
        FROM dbo.docDocumentItem AS I
        INNER JOIN dbo.docDocumentProrrateoManiobras AS P
            ON P.DocumentID = I.DocumentID
           AND P.DocumentItemID = I.DocumentItemID
        WHERE P.DocumentID = ?
          AND P.OperationID = ?
          AND P.ItemExistedBefore = 1;

        UPDATE I
        SET I.DeletedOn = COALESCE(I.DeletedOn, GETDATE()),
            I.DeletedBy = COALESCE(I.DeletedBy, ?)
        FROM dbo.docDocumentItem AS I
        INNER JOIN dbo.docDocumentProrrateoManiobras AS P
            ON P.DocumentID = I.DocumentID
           AND P.DocumentItemID = I.DocumentItemID
        WHERE P.DocumentID = ?
          AND P.OperationID = ?
          AND P.IsManeuverItem = 1
          AND P.ItemExistedBefore = 0;

        UPDATE dbo.docDocumentProrrateoManiobras
        SET RevertedOn = COALESCE(RevertedOn, GETDATE()),
            RevertedBy = COALESCE(RevertedBy, ?)
        WHERE DocumentID = ?
          AND OperationID = ?
          AND RevertedOn IS NULL;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH;
    """
    base_de_datos.command(
        sql,
        (
            document_id,
            operation_id,
            user_id,
            document_id,
            operation_id,
            user_id,
            document_id,
            operation_id,
        ),
    )


def persistir_prorrateo_maniobras(
        base_de_datos, document_id, user_id, registros
):
    """Materializa reversiones y conserva la bitacora del prorrateo."""
    operaciones_revertidas = {
        str(registro.get('OperationID'))
        for registro in (registros or [])
        if str(registro.get('DatabaseAction', '')).upper() == 'REVERT'
        and registro.get('OperationID')
    }
    for operation_id in operaciones_revertidas:
        revertir_prorrateo_maniobras(
            base_de_datos,
            document_id,
            operation_id,
            user_id,
        )

    base_de_datos.guardar_prorrateo_maniobras(
        document_id,
        user_id,
        registros,
    )
