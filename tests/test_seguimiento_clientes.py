from panel.panel_pedidos_modelo import ModeloPanelPedidos


class BaseDeDatosFalsa:
    def __init__(self):
        self.sql = ''
        self.parametros = None

    def fetchall(self, sql, parametros=()):
        self.sql = sql
        self.parametros = parametros
        return [{'BusinessEntityID': 10}]

    def command(self, sql, parametros=()):
        self.sql = sql
        self.parametros = parametros
        return 25


def crear_modelo():
    modelo = ModeloPanelPedidos.__new__(ModeloPanelPedidos)
    modelo.base_de_datos = BaseDeDatosFalsa()
    modelo.user_id = 7
    return modelo


def test_buscar_clientes_sin_compra_usa_dias_como_parametro():
    modelo = crear_modelo()

    resultado = modelo.buscar_clientes_sin_compra(120)

    assert resultado == [{'BusinessEntityID': 10}]
    assert modelo.base_de_datos.parametros == (120,)
    assert 'CustomerFollowUpCayal' in modelo.base_de_datos.sql
    assert 'DATEADD(DAY, -?, GETDATE())' in modelo.base_de_datos.sql
    assert 'Motivo.ItemValue AS MotivoSeguimiento' in modelo.base_de_datos.sql


def test_obtener_motivos_seguimiento_consulta_catalogo_general():
    modelo = crear_modelo()

    resultado = modelo.obtener_motivos_seguimiento()

    assert resultado == [{'BusinessEntityID': 10}]
    assert "CboGroupName = 'Seguimiento'" in modelo.base_de_datos.sql
    assert 'SELECT ItemData, ItemValue' in modelo.base_de_datos.sql


def test_guardar_seguimiento_audita_cliente_usuario_y_resultado():
    modelo = crear_modelo()

    seguimiento_id = modelo.guardar_seguimiento_cliente(
        55, 3, 'El cliente cambió temporalmente de proveedor.', True,
    )

    assert seguimiento_id == 25
    assert modelo.base_de_datos.parametros == (
        55,
        7,
        3,
        'El cliente cambió temporalmente de proveedor.',
        True,
    )
    assert 'INSERT INTO dbo.CustomerFollowUpCayal' in modelo.base_de_datos.sql
    assert 'FollowUpReasonID' in modelo.base_de_datos.sql
