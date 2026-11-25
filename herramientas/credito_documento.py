"""Evaluación crediticia sobre saldos persistidos, contando el actual una vez."""
from decimal import Decimal, ROUND_HALF_UP
import re

_PATRON = re.compile(
    r'^\s*--(?:CRÉDITO VÁLIDO|CRÉDITO RESTRINGIDO|SE ELIGIO FORMA DE PAGO:|'
    r'DEBE:|NO TIENE CRÉDITO|DEBE PAGAR OBLIGATORIAMENTE:)[^\r\n]*?--\s*',
    re.IGNORECASE,
)


def limpiar_leyenda(comentarios):
    texto = comentarios or ''
    while True:
        nuevo = _PATRON.sub('', texto, count=1)
        if nuevo == texto:
            return texto
        texto = nuevo


def tiene_evaluacion(comentarios):
    return bool(re.match(
        r'^\s*--(?:CRÉDITO VÁLIDO|CRÉDITO RESTRINGIDO|SE ELIGIO FORMA DE PAGO:)',
        comentarios or '', re.IGNORECASE,
    ))


def moneda(valor):
    return Decimal(str(valor or 0)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def resolver_credito(registro, pagos):
    """Separa el cálculo puro de la lectura de SQL Server."""
    autorizado = moneda(registro.get('AuthorizedCredit'))
    saldo_actual = moneda(registro.get('SaldoActual'))
    formas = {int(p.get('WayToPayID') or 0) for p in pagos}
    contado = (int(registro.get('ModuleID') or 0) == 21
               and bool(formas) and all(f > 0 and f != 5 for f in formas))
    # Mayoreo de contado en reparto no consume crédito aunque aún tenga saldo.
    deuda = moneda(registro.get('DeudaOtros')) + (moneda(0) if contado else saldo_actual)
    disponible = autorizado - deuda
    leyenda = ''
    restringido = False
    if contado and int(registro.get('ZoneID') or 0) == 1040:
        nombres = []
        for pago in pagos:
            nombre = pago.get('PaymentTermName')
            if not nombre:
                raise ValueError('La forma de pago del pedido no existe en OrdersPaymentTermCayal.')
            if nombre not in nombres:
                nombres.append(nombre)
        leyenda = '--SE ELIGIO FORMA DE PAGO: ' + ' / '.join(nombres) + '--'
    elif int(registro.get('ZoneID') or 0) == 1040:
        restringido = autorizado <= 0 or int(registro.get('CreditBlock') or 0) == 1 or disponible < 0
        estado = 'CRÉDITO RESTRINGIDO' if restringido else 'CRÉDITO VÁLIDO'
        leyenda = f'--{estado} | DEBE: {deuda:.2f} | CRÉDITO DISPONIBLE: {max(disponible, Decimal(0)):.2f}'
        if disponible < 0:
            leyenda += f' | DEBE PAGAR CONTADO: {-disponible:.2f}'
        if int(registro.get('CreditBlock') or 0) == 1:
            leyenda += ' | SUSPENSIÓN CREDITICIA'
        leyenda += '--'
    return dict(Deuda=deuda, Disponible=disponible, Restringido=restringido,
                Leyenda=leyenda, Contado=contado)


def evaluar_credito_documento(base_de_datos, document_id, order_document_ids=None):
    registros = base_de_datos.fetchall("""
        SELECT D.Comments, D.ModuleID, Cliente.ZoneID, Cliente.CreditBlock,
               Cliente.AuthorizedCredit,
               CASE WHEN D.CancelledOn IS NULL THEN ISNULL(D.Balance, 0)
                    ELSE 0 END AS SaldoActual,
               ISNULL(Deuda.Saldo, 0) AS DeudaOtros
        FROM docDocument AS D
        LEFT JOIN docDocumentExt AS X ON X.IDExtra = D.DocumentID
        CROSS APPLY (SELECT CASE WHEN D.BusinessEntityID = 8179
                                 THEN X.CustomerID ELSE D.BusinessEntityID END AS ID) AS Receptor
        CROSS APPLY [dbo].[zvwBuscarInfoCliente-BusinessEntityID](Receptor.ID) AS Cliente
        OUTER APPLY (
            SELECT SUM(CAST(ROUND(CONVERT(MONEY, P.Balance, 1), 2, 0)
                            AS DECIMAL(18,2))) AS Saldo
            FROM docDocument AS P
            WHERE P.DocumentID <> D.DocumentID
              AND P.CancelledOn IS NULL AND P.StatusPaidID <> 1
              AND P.ModuleID IN (21, 1400, 1319)
              AND NOT EXISTS (
                  SELECT 1 FROM docDocumentOrderCayal AS PedidoContado
                  WHERE P.ModuleID = 21
                    AND PedidoContado.OrderDocumentID = P.OrderDocumentID
                    AND PedidoContado.WayToPayID > 0
                    AND PedidoContado.WayToPayID <> 5
              )
              AND (P.BusinessEntityID = Receptor.ID OR EXISTS (
                  SELECT 1 FROM docDocumentExt AS PX
                  WHERE PX.IDExtra = P.DocumentID AND PX.CustomerID = Receptor.ID
              ))
        ) AS Deuda
        WHERE D.DocumentID = ?
    """, (document_id,))
    if not registros:
        raise ValueError(f'No se pudo evaluar el crédito del documento {document_id}.')
    registro = registros[0]
    pagos = []
    if int(registro.get('ModuleID') or 0) == 21:
        if order_document_ids:
            ids = tuple(sorted({int(i) for i in order_document_ids if int(i) > 0}))
            if ids:
                marcas = ','.join('?' for _ in ids)
                pagos = base_de_datos.fetchall(f"""
                    SELECT P.WayToPayID, T.PaymentTermName
                    FROM docDocumentOrderCayal AS P
                    LEFT JOIN OrdersPaymentTermCayal AS T ON T.PaymentTermID = P.WayToPayID
                    WHERE P.OrderDocumentID IN ({marcas})
                """, ids)
        else:
            pagos = base_de_datos.fetchall("""
                SELECT P.WayToPayID, T.PaymentTermName
                FROM docDocument AS D
                INNER JOIN docDocumentOrderCayal AS P ON P.OrderDocumentID = D.OrderDocumentID
                LEFT JOIN OrdersPaymentTermCayal AS T ON T.PaymentTermID = P.WayToPayID
                WHERE D.DocumentID = ?
            """, (document_id,))
    resultado = resolver_credito(registro, pagos)
    resultado['ComentariosOriginales'] = registro.get('Comments') or ''
    return resultado


def componer_comentarios(resultado, comentarios):
    texto = limpiar_leyenda(comentarios)
    return '\n'.join(p for p in (resultado['Leyenda'], texto) if p)


def guardar_leyenda_credito(base_de_datos, document_id):
    resultado = evaluar_credito_documento(base_de_datos, document_id)
    comentarios = componer_comentarios(resultado, resultado['ComentariosOriginales'])
    base_de_datos.command('UPDATE docDocument SET Comments = ? WHERE DocumentID = ?',
                         (comentarios, document_id))
    return comentarios
