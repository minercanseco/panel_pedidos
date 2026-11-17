# Vales de facturas anticipadas

Accesos en Panel de pedidos:

- Panel principal → Generales → Vales.
- Selector de módulo de la captura embebida → Generales → Factura → Vales
  (Vales aparece inmediatamente después de Factura).

El panel pausa su actualización automática mientras está abierta la herramienta
y la reanuda al cerrar. No requiere seleccionar un pedido en la tabla del panel
ni modifica los parámetros de su captura de pedidos.

Seleccione la factura en el combo de solo lectura, capture un número entero de
vale y lea los códigos de barras de los productos entregados. El combo identifica
cada factura por folio, cliente, pedido e ID. Los datos de la factura se muestran
en un formulario de solo lectura: cliente, pedido, lista de precios, importes,
vales autorizados, aplicados, pendientes y saldo disponible. Se muestran cantidad, precio sin impuestos,
importe con impuestos, total y saldo restante. Los códigos con peso usan
`Utilerias.validar_codigo_barras` y las equivalencias especiales del flujo de
captura existente. Con `RestringirProductos = 0` (o NULL), la captura de
productos físicos es libre. Con `RestringirProductos = 1`, solo se aceptan
productos incluidos en las partidas vigentes de la factura anticipada
(`docDocumentItem`, mismo `DocumentID` y `ProductID`, `DeletedOn IS NULL`).
La pertenencia se valida al leer el código y nuevamente al guardar con la
bandera actual de la factura, antes de crear la salida. Esta bandera limita
los productos permitidos; no establece un límite adicional de cantidades. Los paquetes virtuales se surten leyendo
los códigos de sus productos físicos.

## Control

- Origen: `zvwFacturacionAnticipada2`, `TypeID = 2`, `Status = 0`.
- `NumeroVales` se interpreta como el cupo total autorizado, sin decrementarlo.
- Vales utilizados: cantidad de registros con `Status = 0` y `DeletedOn IS NULL`
  en `zvwValesFacturasActicipadas` para la factura.
- Saldo: `TotalFactura - SUM(TotalPrecio)` de esos registros activos.
- Se bloquea la selección y el guardado cuando cualquiera de los dos límites
  está agotado al iniciar la operación. Se permite que el surtido supere el
  saldo disponible; no hay un límite adicional de desborde configurado.
  La pantalla conserva el saldo real después del surtido, aunque sea negativo.
- Un número ya registrado muestra un aviso informativo dentro de la pantalla,
  sin mensajes modales, bloqueos de captura ni cambios forzados de foco.
  El aviso no impide guardar el número real del vale aunque esté repetido.
- Se establece `Status = 1` al consumir el último vale autorizado o al alcanzar
  o superar el saldo, para impedir un nuevo surtido después de agotarlo.
- Se conserva `MontoVale = 0`, como en el ejemplo proporcionado. La aplicación
  no solicita un monto nominal del vale y no lo deduce de la clave.
- `TotalPrecio` guarda el importe de venta de los productos con impuestos;
  `Salida` guarda el folio SA; `Pedido` conserva el folio de pedido de la
  factura anticipada para los reportes y la continuidad del flujo.

Los precios se obtienen con `buscar_info_productos`, usando `CustomerTypeID` y
`BusinessEntityID` del cliente de la factura, incluidos sus precios especiales.
Los cálculos reutilizan `Utilerias.crear_partida`. Se revalida el precio al guardar;
si cambió, se rechaza la operación y se solicita recapturar el producto.

## Inventario y persistencia

Se crea un documento del módulo 203, prefijo SA, almacén 2, a costo, con
`SourceDocumentID` apuntando a la factura y el número de vale en comentarios.
No se genera una segunda factura ni un pedido adicional.

Cada partida se inserta mediante el método nativo a costo para generar el kardex.
Después se actualiza únicamente `docDocumentItem.UnitPrice` con el precio del
cliente sin impuestos, conservando `CostPrice`, el importe de costo de la partida
y el movimiento de inventario. La actualización identifica salida, partida y
producto, exige una fila afectada y vuelve a consultar para confirmar precio y
costo antes de registrar el control del vale. También se verifica que el importe
unitario del kardex (`AmountPrice`) corresponda al costo de la partida.
Si falla el guardado o la comprobación del precio, no se registra el control del
vale ni se cierra la factura. Las operaciones previas siguen sujetas a la
persistencia por operación de los métodos nativos descrita abajo.

Se usa directamente `ComandosBaseDatos()` y sus métodos `fetchall`, `fetchone`,
`command`, `buscar_info_productos`, `buscar_product_id_clave`, `crear_documento`
e `insertar_partida_documento_cayal`, tal como están implementados. No se
redefinen conexiones, métodos de acceso ni ejecución de procedimientos.

Se revalidan cupo, saldo, formato numérico de la clave y precios antes de generar la salida. Después de
insertar las partidas se comprueba su movimiento negativo en `orgProductKardex`
antes de registrar el vale.

Los métodos nativos abren y confirman una conexión por operación: el guardado
completo no es una transacción única ni mantiene bloqueos entre llamadas.
Un fallo posterior a crear la salida puede dejar operaciones parciales y debe
revisarse antes de reintentar. La revalidación previa tampoco garantiza exclusión
entre sesiones simultáneas. No se simula un rollback o bloqueo global desde Vales.

## Validación pendiente en la instalación

Las pruebas automáticas utilizan dobles de base de datos. No se pudo consultar
la instancia SQL durante el desarrollo por tiempo de espera de conexión.
Antes de usar en producción, comprobar en una base de pruebas:

1. Que `NumeroVales` contiene el cupo autorizado total y que `Status = 1` es el
   estado de cierre esperado en los reportes de facturación anticipada.
2. Que `zvwCrearDocumentoCayal` y `zvwInsertarProductoCayal` devuelven sus IDs y
   generan las partidas y el kardex esperado. Se usa su interfaz existente sin migraciones.
3. Surtido parcial, segundo vale, último vale, clave repetida y saldo agotado.
4. Dos sesiones intentando consumir el último vale o el último saldo.
5. Precios con impuestos y precios especiales del cliente; salida negativa en
   kardex y valorización comercial en el control, con `MontoVale = 0`.

No se ejecutaron salidas, inserciones ni cambios de esquema contra la base real.
