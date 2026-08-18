import uuid
from decimal import Decimal, ROUND_HALF_UP

from cayal.impuestos import Impuestos


class ModeloDividirFacturas:
    def __init__(self, parametros, base_de_datos, utilerias):
        self.parametros = parametros
        self.base_de_datos = base_de_datos
        self.utilerias = utilerias
        self.document_id = self.parametros.id_principal
        self.user_id = self.parametros.id_usuario
        self.module_id = self.parametros.id_modulo
        self.info_documento = {}
        self.info_cliente = {}

        self.obtener_info_documento(self.document_id)
        self.obtener_info_cliente(self.info_documento.get('BusinessEntityID',0))

    def obtener_opciones_division(self):
        return ['Por Monto', 'Por Impuestos', 'Por Producto', 'Facturar y Remisionar', 'Especial Pagoda']

    def obtener_info_documento(self, document_id):
        if not self.info_documento:
            consulta = self.base_de_datos.buscar_info_documento(document_id)
            if consulta:
                self.info_documento = consulta[0]

        return self.info_documento

    def obtener_partidas_documento(self, document_id):
        return self.base_de_datos.buscar_partidas_documento(document_id)

    def determinar_numero_documentos(self, partidas, impuestos=False, monto=0, total_documento=0, productos=False):

        if impuestos:
            tax_type_ids = [reg['TaxTypeID'] for reg in partidas]
            tax_type_ids = list(set(tax_type_ids))
            return len(tax_type_ids)

        if monto != 0 and total_documento != 0:
            if not isinstance(total_documento, Decimal):
                total_documento = self.utilerias.convertir_valor_a_decimal(total_documento)

            if not isinstance(monto, Decimal):
                monto = self.utilerias.convertir_valor_a_decimal(monto)

            return int(total_documento / monto)

        if productos:
            return len(partidas)

    def obtener_partidas_tabla(self, document_id):
        partidas = self.base_de_datos.buscar_partidas_documento(documento=document_id)

        partidas_con_impuestos = []
        for partida in partidas:
            partidas_con_impuestos.append(self.utilerias.crear_partida(partida))

        total_acumulado = 0
        nuevas_partidas = []
        for partida in partidas_con_impuestos:
            nuevas_partidas.append(
                {
                    'Quantity':f"{partida['cantidad']:.2f}",
                    'ProductID': partida['ProductID'],
                    'ProductKey':partida['ProductKey'],
                    'ProductName':partida['ProductName'],
                    'UnitPrice':f"{partida['precio']:.2f}",
                    'Subtotal': f"{partida['subtotal']:.2f}",
                    'Total':f"{partida['total']:.2f}",
                    'TaxTypeID':partida['TaxTypeID'],
                    'ClaveProdServ':partida['ClaveProdServ'],
                    'ClaveUnidad':partida['ClaveUnidad'],
                    'UUID': str(uuid.uuid4())
                }
            )
        return total_acumulado, nuevas_partidas

    def obtener_info_cliente(self, business_entity_id):

        consulta = self.base_de_datos.buscar_info_cliente(business_entity_id)
        if consulta:
            self.info_cliente = consulta[0]
        return self.info_cliente

    def crear_documentos(self, documentos, plan_tipos_documentos, module_id):
        # plan_tipos_documentos[numero] -> 0 FACTURA, 1 REMISION

        prefijos = {21: 'FM', 1400: 'FG', 1316: 'NVR', 158: 'NV', 1319: 'FGR'}

        def borrar_partidas_documento_base(document_id, module_id, user_id):
            self.base_de_datos.command(
                'EXEC [dbo].[zvwBorrarPartidasDocumentoCayal] ?, ?, 0, ?',
                (document_id, module_id, user_id)
            )

        def crear_cabecera_documento(business_entity_id, module_id):
            # IMPORTANTE:
            # Creamos SIEMPRE con el mismo DocumentTypeID del documento base y luego "convertimos"
            # (así no dependes de IDs de tipo por factura/remisión).
            document_type_id_base = 0 if not self.info_documento.get('TipoCFD', 0) else 1

            document_id = self.base_de_datos.crear_documento(
                tipo_cfd=document_type_id_base,
                prefijo=prefijos[module_id],
                business_entity_id=business_entity_id,
                modulo_id=module_id,
                usuario_id= self.info_documento.get('CreatedBy',1),  # quien capturó
                sucursal_id=self.info_documento.get('BusinessEntityDepotID',0),
                address_detail_id=self.info_documento.get('AddressDetailID',0),
                send_to_invoice=self.user_id,  # quien crea (envía a timbrar)
            )
            return document_id

        def insertar_partida(document_id, partida, module_id):
            funcion = self.utilerias.convertir_valor_a_decimal

            qty_raw = partida.get('Quantity', 0)
            price_raw = partida.get('UnitPrice', 0)

            cantidad = qty_raw if isinstance(qty_raw, Decimal) else funcion(qty_raw)
            precio = price_raw if isinstance(price_raw, Decimal) else funcion(price_raw)

            # subtotal decimal con tolerancia hasta 6 decimales
            try:
                subtotal = (precio * cantidad).quantize(
                    Decimal("0.000001"),
                    rounding=ROUND_HALF_UP
                )
            except Exception:
                subtotal = (funcion(precio) * funcion(cantidad)).quantize(
                    Decimal("0.000001"),
                    rounding=ROUND_HALF_UP
                )

            parametros = (
                int(document_id),
                int(partida.get('ProductID', 0) or 0),
                2,  # depot_id
                cantidad,
                precio,
                Decimal("0.00"),  # costo
                subtotal,
                1,  # tipo captura
                int(module_id),
                (partida.get('Comments') or "")
            )

            self.base_de_datos.insertar_partida_documento_cayal(parametros)

        def actualizar_comentario_document_id(comments, destination_document_id):
            self.base_de_datos.command(
                'UPDATE docDocument SET Comments = ? WHERE DocumentID = ?',
                (comments or '', destination_document_id)
            )

        def relacionar_pedido_document_id(order_document_id, document_id):
            self.base_de_datos.command(
                """
                DECLARE @OrderDocumentID INT = ?
                DECLARE @DocumentID      INT = ?

                UPDATE docDocument
                SET OrderDocumentID = @OrderDocumentID
                WHERE DocumentID = @DocumentID;

                UPDATE X
                    SET AddressDetailID = P.AddressDetailID
                FROM docDocument D
                INNER JOIN docDocumentExtra X       ON D.DocumentID = X.DocumentID
                INNER JOIN docDocumentOrderCayal P  ON D.OrderDocumentID = P.OrderDocumentID
                WHERE D.DocumentID = @DocumentID;
                """,
                (order_document_id, document_id)
            )

        def actualizar_datos_fiscales_document_id(destination_document_id, tipo_doc):
            # 0 factura 1 remision FormaPago	MetodoPago	ReceptorUsoCFDI
            forma_pago_doc_base = self.info_documento.get('FormaPago',"")
            tipo_doc_base = self.info_documento.get("TipoCFD", 0)

            # Normalizar TipoCFD a int
            try:
                tipo_doc_base = int(tipo_doc_base)
            except (TypeError, ValueError):
                tipo_doc_base = 0

            if tipo_doc_base == 1 and tipo_doc == 0: # si es remision
                forma_pago = self.info_cliente.get("FormaPago","")
            elif tipo_doc_base == 0 and tipo_doc == 0:
                forma_pago = forma_pago_doc_base
            else:
                forma_pago = '01'

            metodo_pago = self.info_cliente.get("MetodoPago","") if tipo_doc == 0 else 'PUE'
            uso_cfdi = self.info_cliente.get("ReceptorUsoCFDI","") if tipo_doc == 0 else 'S01'

            self.base_de_datos.command(
                """
                UPDATE docDocumentCFD
                SET FormaPago = ?, MetodoPago = ?, ReceptorUsoCFDI = ?
                WHERE DocumentID = ?
                """,
                (
                    forma_pago,
                    metodo_pago,
                    uso_cfdi,
                    destination_document_id,
                )
            )

        def convertir_en_factura(document_id, business_entity_id, forma_pago):
            self.base_de_datos.command("""
                DECLARE @Documento INT =  ?
                DECLARE @IDEmpresa INT =  ?
                DECLARE @FormaPago NVARCHAR(20) =  ?

                UPDATE docDocument SET BusinessEntityID=@IDEmpresa, chkCustom1=0,
                        Custom3 = (SELECT ZoneID FROM orgCustomer WHERE BusinessEntityID=@IDEmpresa)
                WHERE DocumentID=@Documento

                UPDATE docDocumentExt SET CustomerID=0 WHERE IDExtra=@Documento

                UPDATE docDocumentCFD SET MetodoPago=(SELECT MetodoPago FROM orgCustomer WHERE BusinessEntityID=@IDEmpresa),
                        FormaPago=@FormaPago,
                        ReceptorUsoCFDI=(SELECT ReceptorUsoCFDI FROM orgCustomer WHERE BusinessEntityID=@IDEmpresa)
                WHERE DocumentID=@Documento
            """, (document_id, business_entity_id, forma_pago))

        def convertir_en_remision(document_id, business_entity_id, forma_pago):
            self.base_de_datos.command("""
                DECLARE @Documento INT =  ?
                DECLARE @IDEmpresa INT =  ?
                DECLARE @FormaPago NVARCHAR(20) =  ?

                IF NOT EXISTS(SELECT CustomerID FROM docDocumentExt WHERE IDExtra=@Documento)
                    BEGIN INSERT INTO docDocumentExt (IDExtra,CustomerID) VALUES (@Documento,@IDEmpresa) END
                ELSE
                    BEGIN UPDATE docDocumentExt SET CustomerID=@IDEmpresa WHERE IDExtra=@Documento END

                UPDATE docDocument SET BusinessEntityID=8179, chkCustom1=1,
                                        Custom3 = (SELECT ZoneID FROM orgCustomer WHERE BusinessEntityID=@IDEmpresa)
                WHERE DocumentID=@Documento

                UPDATE docDocumentCFD SET MetodoPago='PUE',
                    FormaPago=(CASE WHEN @FormaPago NOT IN('01','04','28') THEN '01' ELSE @FormaPago END),
                    ReceptorUsoCFDI='S01'
                WHERE DocumentID=@Documento
            """, (document_id, business_entity_id, forma_pago))

        def eliminar_cobros(document_id, user_id):
            self.base_de_datos.command("""
                        BEGIN TRY
            BEGIN TRAN;

            DECLARE @DocumentID int = ?;
            DECLARE @UserID     int = ?;

            /* 1) Borrar TODAS las aplicaciones (cobros) del documento */
            UPDATE docDocumentPayment
            SET DeletedBy = @UserID,
                DeletedOn = GETDATE()
            WHERE DocumentID = @DocumentID
              AND DeletedOn IS NULL;

            /* 2) Marcar como borradas las FinancialOperation que ya no tengan aplicaciones vivas */
            ;WITH FO AS (
                SELECT DISTINCT FinancialOperationID
                FROM docDocumentPayment
                WHERE DocumentID = @DocumentID
            )
            UPDATE F
            SET DeletedBy = @UserID,
                DeletedOn = GETDATE()
            FROM docFinancialOperation F
            INNER JOIN FO ON FO.FinancialOperationID = F.FinancialOperationID
            WHERE F.DeletedOn IS NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM docDocumentPayment DDP
                  WHERE DDP.FinancialOperationID = F.FinancialOperationID
                    AND DDP.DeletedOn IS NULL
              );

            /* 3) Recalcular totales del documento */
            DECLARE @NewTotalPaid decimal(18,2) =
                ISNULL((
                    SELECT SUM(Amount)
                    FROM docDocumentPayment
                    WHERE DocumentID = @DocumentID
                      AND DeletedOn IS NULL
                ), 0);

            DECLARE @Total decimal(18,2), @CancelledOn datetime;
            SELECT @Total = Total, @CancelledOn = CancelledOn
            FROM docDocument WITH (UPDLOCK, ROWLOCK)
            WHERE DocumentID = @DocumentID;

            DECLARE @EffectiveTotal decimal(18,2) = CASE WHEN @CancelledOn IS NULL THEN @Total ELSE 0 END;
            DECLARE @NewBalance decimal(18,2)     = @EffectiveTotal - @NewTotalPaid;

            DECLARE @NewStatusPaidID int =
                CASE
                    WHEN @NewTotalPaid = 0 THEN 3
                    WHEN @NewBalance   = 0 THEN 1
                    ELSE 2
                END;

            UPDATE docDocument
            SET TotalPaid    = @NewTotalPaid,
                Balance      = @NewBalance,
                StatusPaidID = @NewStatusPaidID
            WHERE DocumentID = @DocumentID;

            COMMIT;
        END TRY
        BEGIN CATCH
            IF XACT_STATE() <> 0 ROLLBACK;
            THROW;
        END CATCH;
                        """, (document_id, user_id))

        def finalizar_documento(document_id):
            """Afecta impuestos y deja sincronizados los totales de cabecera."""
            Impuestos.afectar_impuestos_documento(
                self.base_de_datos,
                int(document_id),
            )

            filas = self.base_de_datos.fetchall(
                '''
                SELECT
                    CAST(ROUND(ISNULL(P.SubTotal, 0), 2)
                         AS decimal(18, 2)) AS SubTotal,
                    CAST(ROUND(ISNULL(P.SubTotalWithDiscount, 0), 2)
                         AS decimal(18, 2)) AS SubTotalWithDiscount,
                    CAST(ROUND(ISNULL(P.TotalDiscount, 0), 2)
                         AS decimal(18, 2)) AS TotalDiscount,
                    CAST(ROUND(
                        ISNULL(T.IVA_T, 0) + ISNULL(T.IEPS_T, 0)
                        + ISNULL(T.Otro, 0) + ISNULL(T.Local_T, 0), 2
                    ) AS decimal(18, 2)) AS TotalTax,
                    CAST(ROUND(
                        ISNULL(T.IVA_R, 0) + ISNULL(T.ISR_R, 0)
                        + ISNULL(T.IEPS_R, 0) + ISNULL(T.Local_R, 0), 2
                    ) AS decimal(18, 2)) AS TotalRetention,
                    CAST(ROUND(
                        ISNULL(P.SubTotalWithDiscount, 0)
                        + ISNULL(T.IVA_T, 0) + ISNULL(T.IEPS_T, 0)
                        + ISNULL(T.Otro, 0) + ISNULL(T.Local_T, 0)
                        - ISNULL(T.IVA_R, 0) - ISNULL(T.ISR_R, 0)
                        - ISNULL(T.IEPS_R, 0) - ISNULL(T.Local_R, 0), 2
                    ) AS decimal(18, 2)) AS Total,
                    CAST(ROUND(ISNULL(D.TotalPaid, 0), 2)
                         AS decimal(18, 2)) AS TotalPaid
                FROM dbo.docDocument D
                OUTER APPLY (
                    SELECT
                        SUM(CAST(ISNULL(I.Total, 0)
                                 AS decimal(28, 8))) AS SubTotal,
                        SUM(
                            CAST(ISNULL(I.Total, 0) AS decimal(28, 8))
                            * (1 - CAST(ISNULL(I.DiscountPerc, 0)
                                        AS decimal(28, 8)))
                        ) AS SubTotalWithDiscount,
                        SUM(
                            CAST(ISNULL(I.Total, 0) AS decimal(28, 8))
                            * CAST(ISNULL(I.DiscountPerc, 0)
                                   AS decimal(28, 8))
                        ) AS TotalDiscount
                    FROM dbo.docDocumentItem I
                    WHERE I.DocumentID = D.DocumentID
                      AND I.DeletedOn IS NULL
                ) P
                LEFT JOIN dbo.docDocumentTax T
                    ON T.DocumentID = D.DocumentID
                WHERE D.DocumentID = ?
                  AND D.DeletedOn IS NULL
                ''',
                (int(document_id),),
            )
            if not filas:
                raise RuntimeError(
                    'No fue posible calcular los totales del documento {}.'
                    .format(document_id)
                )

            totales = filas[0]
            subtotal = float(totales['SubTotal'] or 0)
            subtotal_descuento = float(
                totales['SubTotalWithDiscount'] or 0
            )
            descuento = float(totales['TotalDiscount'] or 0)
            total_impuestos = float(totales['TotalTax'] or 0)
            total_retenciones = float(totales['TotalRetention'] or 0)
            total = float(totales['Total'] or 0)
            total_pagado = float(totales['TotalPaid'] or 0)
            saldo = round(total - total_pagado, 2)

            if total_pagado <= 0:
                status_paid_id = 3
            elif saldo > 0:
                status_paid_id = 2
            elif saldo < 0:
                status_paid_id = 4
            else:
                status_paid_id = 1

            self.base_de_datos.command(
                '''
                UPDATE dbo.docDocument
                SET SubTotal = ?,
                    SubTotalWithDiscount = ?,
                    TotalDiscount = ?,
                    TotalTax = ?,
                    TotalRetention = ?,
                    Total = ?,
                    TotalLetter = ?,
                    Balance = ?,
                    StatusPaidID = ?
                WHERE DocumentID = ?
                ''',
                (
                    subtotal,
                    subtotal_descuento,
                    descuento,
                    total_impuestos,
                    total_retenciones,
                    total,
                    self.utilerias.cantidad_con_letra(total),
                    saldo,
                    status_paid_id,
                    int(document_id),
                ),
            )

        # =========================
        # FLUJO
        # =========================

        borrar_partidas_documento_base(self.info_documento['DocumentID'], module_id, self.user_id)

        forma_pago = self.info_documento.get('FormaPago')

        base_usado = False  # <- CLAVE: controla el uso del documento base

        for numero, partidas in (documentos or {}).items():
            info_plan = plan_tipos_documentos[numero]
            tipo_doc = int(info_plan[0]) # 0=factura, 1=remision
            business_entity_id = info_plan[1]

            if not partidas:
                continue

            if not base_usado:
                document_id = self.info_documento['DocumentID']
                eliminar_cobros(document_id, user_id=90)
                base_usado = True
            else:
                document_id = crear_cabecera_documento(business_entity_id, module_id)

            # convertir SIEMPRE según plan
            if tipo_doc == 0:
                convertir_en_factura(document_id, business_entity_id, forma_pago)
            else:
                convertir_en_remision(document_id, business_entity_id, forma_pago)

            actualizar_comentario_document_id(self.info_documento.get('Comments', ''), document_id)


            actualizar_datos_fiscales_document_id(document_id, tipo_doc)

            if module_id == 21:
                relacionar_pedido_document_id(self.info_documento.get('OrderDocumentID', 0), document_id)

            for partida in (partidas or []):
                insertar_partida(document_id, partida, module_id)

            finalizar_documento(document_id)

    def obtener_info_pedido(self, order_document_id):
        consulta = self.base_de_datos.buscar_info_documento_pedido_cayal(order_document_id)
        if consulta:
            return  consulta[0]
        return {}

    #------------------------------------------------------------------------------------------------------------------
    # Helpers para vaidacion de proceso de division
    # ------------------------------------------------------------------------------------------------------------------
    def _fmt_money(self,x):
        x = Decimal(str(x))
        return f"${x:,.2f}"

    def _fmt_qty(self,x):
        x = Decimal(str(x))
        # 3 decimales para KGM; si es entero se verá limpio por strip
        s = f"{x:.3f}".rstrip('0').rstrip('.')
        return s if s else "0"

    def _total_partida(self,p):
        # total “real” sin depender de Subtotal viejo:
        qty = Decimal(str(p.get('Quantity', 0)))
        price = Decimal(str(p.get('UnitPrice', 0)))
        taxp = Decimal(str(p.get('TaxPerc', 0)))
        subtotal = qty * price
        total = subtotal * (Decimal('1') + taxp)
        return subtotal, total

    def imprimir_documentos(self,documentos: dict):
        gran_total = Decimal('0')
        print("\n=== RESUMEN DIVISIÓN POR MONTO ===\n")

        for doc_id in sorted(documentos.keys()):
            partidas = documentos[doc_id]
            doc_sub = Decimal('0')
            doc_tot = Decimal('0')

            # Header doc
            print(f"DOCUMENTO {doc_id}  |  partidas: {len(partidas)}")
            print("-" * 120)
            print(
                f"{'#':>2}  {'ProdID':>6}  {'Clave':<10}  {'Unidad':<4}  {'Qty':>10}  {'P.Unit':>10}  {'Tax%':>6}  {'Subtotal':>12}  {'Total':>12}  {'Producto'}")
            print("-" * 120)

            for i, p in enumerate(partidas, 1):
                unidad = str(p.get('ClaveUnidad', '') or '')
                qty = p.get('Quantity', 0)
                price = p.get('UnitPrice', 0)
                taxp = Decimal(str(p.get('TaxPerc', 0)))

                sub, tot = self._total_partida(p)
                doc_sub += sub
                doc_tot += tot

                clave = str(p.get('ProductKey', '') or '')
                nombre = str(p.get('ProductName', '') or '')

                print(
                    f"{i:>2}  "
                    f"{int(p.get('ProductID', 0)):>6}  "
                    f"{clave:<10.10}  "
                    f"{unidad:<4}  "
                    f"{self._fmt_qty(qty):>10}  "
                    f"{self._fmt_money(price):>10}  "
                    f"{(taxp * 100):>5.1f}%  "
                    f"{self._fmt_money(sub):>12}  "
                    f"{self._fmt_money(tot):>12}  "
                    f"{nombre}"
                )

            print("-" * 120)
            print(f"TOTAL DOC {doc_id}:  Subtotal={self._fmt_money(doc_sub)}   Total={self._fmt_money(doc_tot)}\n")
            gran_total += doc_tot

        print("=" * 120)
        print(f"GRAN TOTAL (suma de docs): {self._fmt_money(gran_total)}")
        print("=" * 120)
