"""Vales de facturas anticipadas: captura libre con métodos nativos de Cayal."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from cayal.comandos_base_datos import ComandosBaseDatos


def decimal(valor):
    try:
        resultado = Decimal(str(valor if valor is not None else 0))
    except (InvalidOperation, ValueError, TypeError) as error:
        raise ValueError('Se encontró una cantidad inválida.') from error
    if not resultado.is_finite():
        raise ValueError('Se encontró una cantidad inválida.')
    return resultado


def moneda(valor):
    return decimal(valor).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class ModeloVales:
    # NumeroVales es el total autorizado; los registros activos consumen uno.
    CONSULTA = """
        SELECT F.DocumentID, F.FolioFactura, F.Empresa, F.Pedido,
               F.BusinessEntityID, F.TotalFactura, F.NumeroVales,
               ISNULL(F.RestringirProductos, 0) AS RestringirProductos,
               ISNULL(V.Aplicados, 0) AS Aplicados,
               ISNULL(V.Surtido, 0) AS Surtido,
               F.NumeroVales - ISNULL(V.Aplicados, 0) AS Pendientes,
               F.TotalFactura - ISNULL(V.Surtido, 0) AS Saldo,
               ISNULL(X.AddressDetailID, 0) AS AddressDetailID,
               ISNULL(X.BusinessEntityDepotID, 0) AS SucursalID
        FROM dbo.zvwFacturacionAnticipada2 F
        JOIN dbo.docDocument D ON D.DocumentID = F.DocumentID
        LEFT JOIN dbo.docDocumentExtra X ON X.DocumentID = D.DocumentID
        OUTER APPLY (
            SELECT COUNT(*) AS Aplicados, SUM(TotalPrecio) AS Surtido
            FROM dbo.zvwValesFacturasActicipadas V
            WHERE V.DocumentID = F.DocumentID
              AND V.Status = 0 AND V.DeletedOn IS NULL
        ) V
        WHERE F.TypeID = 2 AND F.Status = 0
          AND D.DeletedOn IS NULL AND D.CancelledOn IS NULL
    """

    def __init__(self, parametros, base_de_datos=None, utilerias=None):
        from cayal.util import Utilerias
        self.parametros = parametros
        self.bd = base_de_datos if base_de_datos is not None else ComandosBaseDatos()
        self.utilerias = utilerias or Utilerias()

    def facturas(self, document_id=None):
        consulta = self.CONSULTA
        params = ()
        if document_id is not None:
            consulta += ' AND F.DocumentID = ?'
            params = (int(document_id),)
        return self.bd.fetchall(consulta + ' ORDER BY F.DocumentID DESC', params)

    @staticmethod
    def validar_disponibilidad(factura):
        if not factura:
            raise ValueError('La factura ya no está disponible para surtir.')
        autorizados = decimal(factura.get('NumeroVales'))
        if autorizados <= 0 or autorizados != autorizados.to_integral_value():
            raise ValueError('La factura no tiene un NumeroVales autorizado válido.')
        if decimal(factura['Pendientes']) <= 0 or moneda(factura['Saldo']) <= 0:
            raise ValueError('La factura no tiene saldo o vales pendientes por surtir.')

    def cliente(self, factura):
        filas = self.bd.fetchall(
            'SELECT * FROM dbo.[zvwBuscarInfoCliente-BusinessEntityID](?)',
            (factura['BusinessEntityID'],),
        )
        if not filas or not filas[0].get('CustomerTypeID'):
            raise ValueError('El cliente no tiene una lista de precios válida.')
        return filas[0]

    def _producto(self, product_id, cliente):
        datos = self.bd.buscar_info_productos(
            product_id, cliente['CustomerTypeID'], no_en_venta=True,
            business_entity_id=cliente['BusinessEntityID'],
        )
        if len(datos) != 1:
            raise ValueError('No se pudo determinar un precio único para el producto.')
        producto = dict(datos[0])
        if not producto.get('AvailableForSale') or decimal(producto.get('SalePrice')) <= 0:
            raise ValueError('El producto no está disponible o no tiene precio vigente.')
        # Las salidas requieren un producto físico; no se consume una receta virtual.
        if int(producto.get('ProductTypeID', 0)) != 1:
            raise ValueError('Capture los productos físicos del paquete por su código de barras.')
        if decimal(producto.get('CostPrice')) < 0:
            raise ValueError('El costo del producto no es válido.')
        return producto

    def validar_producto_factura(self, factura, product_id):
        if int(factura.get('RestringirProductos') or 0) != 1:
            return
        if not self.bd.fetchone("""
            SELECT COUNT(*) FROM dbo.docDocumentItem
            WHERE DocumentID = ? AND ProductID = ? AND DeletedOn IS NULL
        """, (factura['DocumentID'], product_id)):
            raise ValueError(
                f"El producto no está incluido en la factura anticipada {factura['FolioFactura']}. "
                'Esta factura solo permite surtir los productos que contiene.'
            )

    def capturar_codigo(self, codigo, factura):
        self.validar_disponibilidad(factura)
        if not self.utilerias.es_codigo_barras(codigo):
            raise ValueError('Ha introducido un código de barras inválido.')
        valores = self.utilerias.validar_codigo_barras(codigo)
        coincidencias = self.bd.buscar_product_id_clave(valores['clave'])
        if len(coincidencias or []) != 1:
            raise ValueError('El código no corresponde a un producto único.')
        product_id = coincidencias[0]['ProductID']
        self.validar_producto_factura(factura, product_id)
        cliente = self.cliente(factura)
        producto = self._producto(product_id, cliente)
        cantidad = decimal(valores.get('cantidad', 1))
        equivalencia = self.utilerias.equivalencias_productos_especiales(product_id)
        if equivalencia:
            cantidad = decimal(equivalencia[1])
        if cantidad <= 0:
            raise ValueError('La cantidad del código debe ser mayor que cero.')
        partida = self.utilerias.crear_partida(producto, cantidad)
        partida['TipoCaptura'] = 0
        return partida

    @staticmethod
    def validar_clave(clave):
        clave = str(clave).strip()
        if not clave.isascii() or not clave.isdigit() or int(clave) <= 0:
            raise ValueError('Capture un número entero de vale mayor que cero.')
        # El proyecto de referencia usa una clave numérica.
        if int(clave) > 2147483647:
            raise ValueError('El número de vale excede el límite permitido.')
        return int(clave)

    def validar_numero_vale(self, factura, clave):
        clave = self.validar_clave(clave)
        if self.bd.fetchone("""
            SELECT COUNT(*) FROM dbo.zvwValesFacturasActicipadas
            WHERE DocumentID = ? AND Clave = ? AND Status = 0 AND DeletedOn IS NULL
        """, (factura['DocumentID'], clave)):
            raise ValueError(
                f"El vale {clave} ya fue aplicado a esta factura ({factura['FolioFactura']})."
            )
        return clave

    def guardar(self, factura, clave, partidas):
        clave = self.validar_clave(clave)
        if not partidas:
            raise ValueError('Capture al menos un producto.')
        self.validar_disponibilidad(factura)
        bd = self.bd
        actuales = self.facturas(factura['DocumentID'])
        actual = actuales[0] if len(actuales) == 1 else None
        self.validar_disponibilidad(actual)
        if actual['BusinessEntityID'] != factura['BusinessEntityID']:
            raise ValueError('El cliente cambió. Vuelva a seleccionar la factura.')
        # La consulta de duplicados es informativa en la interfaz.
        cliente = self.cliente(actual)
        revisadas = []
        for partida in partidas:
            cantidad = decimal(partida['cantidad'])
            if cantidad <= 0:
                raise ValueError('La cantidad debe ser mayor que cero.')
            self.validar_producto_factura(actual, partida['ProductID'])
            producto = self._producto(partida['ProductID'], cliente)
            vigente = self.utilerias.crear_partida(producto, cantidad)
            if (decimal(vigente['precio']) != decimal(partida['precio'])
                    or moneda(vigente['total']) != moneda(partida['total'])):
                raise ValueError('Cambió el precio del cliente. Vuelva a capturar el producto.')
            revisadas.append(vigente)
        total = moneda(sum(decimal(p['total']) for p in revisadas))
        if total <= 0:
            raise ValueError('El importe debe ser positivo.')
        usuario = int(self.parametros.id_usuario)
        if usuario <= 0:
            raise ValueError('El usuario no es válido.')
        salida = bd.crear_documento(
            0, 'SA', actual['BusinessEntityID'], 203, usuario,
            actual['SucursalID'], address_detail_id=actual['AddressDetailID'],
        )
        if not salida:
            raise RuntimeError('No se pudo crear la salida de inventario.')
        bd.command('''
            UPDATE dbo.docDocument SET SourceDocumentID = ?, Custom1 = ?,
                Title = 'SALIDA POR VALE DE FACTURA ANTICIPADA', Comments = ?
            WHERE DocumentID = ? AND ModuleID = 203;
            IF @@ROWCOUNT <> 1 THROW 50000, 'La salida creada no es válida.', 1;
        ''', (actual['DocumentID'], actual['FolioFactura'],
              f"Factura {actual['FolioFactura']} - Vale {clave}", salida))
        for partida in revisadas:
            costo = decimal(partida['CostPrice'])
            item_id = bd.insertar_partida_documento_cayal((
                salida, partida['ProductID'], 2, partida['cantidad'],
                0, costo, costo * decimal(partida['cantidad']), 0, 203,
                f'Vale {clave}',
            ))
            if not item_id:
                raise RuntimeError('No se pudo insertar una partida de la salida.')
            # Insertar a costo conserva el comportamiento nativo del inventario.
            # Después se persiste exclusivamente el precio comercial para reportes.
            precio = decimal(partida['precio'])
            bd.command("""
                UPDATE dbo.docDocumentItem SET UnitPrice = ?
                WHERE DocumentID = ? AND DocumentItemID = ?
                  AND ProductID = ? AND DeletedOn IS NULL;
                IF @@ROWCOUNT <> 1
                    THROW 50000, 'No se pudo guardar el precio de la partida de salida.', 1;
            """, (precio, salida, item_id, partida['ProductID']))
            precio_guardado = bd.fetchone("""
                SELECT COUNT(*) FROM dbo.docDocumentItem
                WHERE DocumentID = ? AND DocumentItemID = ?
                  AND ProductID = ? AND DeletedOn IS NULL
                  AND UnitPrice IS NOT NULL AND CostPrice IS NOT NULL
                  AND ABS(UnitPrice - ?) < 0.000001
                  AND ABS(CostPrice - ?) < 0.000001
            """, (salida, item_id, partida['ProductID'], precio, costo))
            if precio_guardado != 1:
                raise RuntimeError(
                    f'No se confirmó el precio y costo de la partida {item_id} '
                    f'en la salida {salida}. Revise la salida antes de reintentar.'
                )
        # Verificar inventario antes de confirmar el control del vale.
        faltantes = bd.fetchone('''
            SELECT COUNT(*) FROM dbo.docDocumentItem I
            WHERE I.DocumentID = ? AND I.DeletedOn IS NULL AND NOT EXISTS (
                SELECT 1 FROM dbo.orgProductKardex K
                WHERE K.DocumentID = I.DocumentID AND K.DocumentItemID = I.DocumentItemID
                  AND K.ProductID = I.ProductID AND K.DepotID = 2
                  AND ABS(K.Quantity + ABS(I.Quantity)) < 0.000001
                  AND ABS(K.AmountPrice - I.CostPrice) < 0.000001)
        ''', (salida,))
        if faltantes:
            raise RuntimeError('La salida no generó el movimiento de inventario esperado.')
        bd.command('''
            UPDATE dbo.docDocument SET CostosCalculados = 1, TotalCost = (
                SELECT SUM(CostPrice * Quantity) FROM dbo.docDocumentItem
                WHERE DocumentID = ? AND DeletedOn IS NULL)
            WHERE DocumentID = ?;
        ''', (salida, salida))
        folio = bd.fetchone('SELECT CONCAT(FolioPrefix, Folio) FROM dbo.docDocument WHERE DocumentID = ?', (salida,))
        if not folio:
            raise RuntimeError('No se obtuvo el folio de la salida.')
        bd.command('''
            INSERT INTO dbo.zvwValesFacturasActicipadas
                (DocumentID, Salida, TotalPrecio, MontoVale, Clave, Status, CreatedOn, CreatedBy, Pedido)
            VALUES (?, ?, ?, 0, ?, 0, GETDATE(), ?, ?)
        ''', (actual['DocumentID'], folio, total, clave, usuario, actual['Pedido']))
        # No se modifica NumeroVales: conserva el cupo original autorizado.
        if decimal(actual['Pendientes']) <= 1 or moneda(actual['Saldo']) <= total:
            bd.command('UPDATE dbo.zvwFacturacionAnticipada2 SET Status = 1 WHERE DocumentID = ?', (actual['DocumentID'],))
        return folio
