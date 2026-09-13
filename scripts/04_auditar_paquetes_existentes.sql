-- Sólo diagnóstico. No altera documentos ni kardex.
SELECT D.DocumentID, DI.DocumentItemID, DI.ProductID,
       D.OrderDocumentID, DI.OrderPackageDocumentItemID,
       SUM(CASE WHEN K.PackageComponentSource IS NULL
                THEN 1 ELSE 0 END) AS MovimientosSinOrigen,
       SUM(CASE WHEN K.PackageComponentSource IN (1, 2)
                THEN 1 ELSE 0 END) AS MovimientosIngredientes,
       (SELECT COUNT(*) FROM dbo.docDocumentItemComponentCayal C
        WHERE C.DocumentItemID = DI.DocumentItemID
          AND C.DeletedOn IS NULL) AS ComponentesVenta
FROM dbo.docDocumentItem DI
JOIN dbo.docDocument D ON D.DocumentID = DI.DocumentID
JOIN dbo.orgProduct P ON P.ProductID = DI.ProductID
LEFT JOIN dbo.orgProductKardex K
       ON K.DocumentID = DI.DocumentID
      AND K.DocumentItemID = DI.DocumentItemID
WHERE P.ProductTypeID = 3
  AND DI.DeletedOn IS NULL
GROUP BY D.DocumentID, DI.DocumentItemID, DI.ProductID,
         D.OrderDocumentID, DI.OrderPackageDocumentItemID
ORDER BY D.DocumentID, DI.DocumentItemID;
