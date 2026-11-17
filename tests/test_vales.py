import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'herramientas'))

from decimal import Decimal
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from herramientas.capturar_documento.herramientas.vales import modelo as m


def factura(**cambios):
    datos = dict(DocumentID=100, BusinessEntityID=50, FolioFactura='FM100',
                 NumeroVales=3, Aplicados=1, Pendientes=2, Saldo=Decimal('200'),
                 TotalFactura=300, Pedido='PM10', SucursalID=0, AddressDetailID=0,
                 RestringirProductos=0)
    datos.update(cambios)
    return datos


def partida(**cambios):
    datos = dict(ProductID=20, cantidad=Decimal(1), precio=Decimal(100), total=Decimal(100),
                 SalePrice=Decimal(100), CostPrice=Decimal(40), AvailableForSale=1,
                 ProductTypeID=1)
    datos.update(cambios)
    return datos


class Util:
    def crear_partida(self, producto, cantidad):
        return dict(producto, cantidad=cantidad, precio=producto['SalePrice'], total=cantidad * producto['SalePrice'])
    def es_codigo_barras(self, valor):
        return valor == 'codigo'
    def validar_codigo_barras(self, valor):
        return dict(clave='20', cantidad='0.500')
    def equivalencias_productos_especiales(self, producto):
        return None


class Datos:
    def __init__(self):
        self.actual = factura()
        self.duplicado = 0
        self.faltantes = 0
        self.precio = Decimal(100)
        self.comandos = []
        self.items = []
        self.fallo = False
        self.productos_factura = {20}
        self.precios_confirmados = 1
    def fetchall(self, sql, params=()):
        if 'zvwBuscarInfoCliente' in sql:
            return [dict(BusinessEntityID=50, CustomerTypeID=4)]
        return [self.actual] if self.actual else []
    def fetchone(self, sql, params=()):
        if 'ABS(UnitPrice - ?)' in sql:
            return self.precios_confirmados
        if 'FROM dbo.docDocumentItem' in sql and 'ProductID = ?' in sql:
            return int(params[1] in self.productos_factura)
        if 'Clave = ?' in sql:
            return self.duplicado
        if 'orgProductKardex' in sql:
            return self.faltantes
        if 'CONCAT' in sql:
            return 'SA123'
        raise AssertionError(sql)
    def command(self, sql, params=()):
        self.comandos.append((sql, params))
        if self.fallo and 'INSERT INTO dbo.zvwVales' in sql:
            raise RuntimeError('fallo al registrar vale')
    def crear_documento(self, *args, **kwargs):
        return 123
    def insertar_partida_documento_cayal(self, params):
        self.items.append(params)
        return 456
    def buscar_info_productos(self, *args, **kwargs):
        self.lista = (args, kwargs)
        return [partida(SalePrice=self.precio)]
    def buscar_product_id_clave(self, clave):
        return [dict(ProductID=20)]


class ValesTest(unittest.TestCase):
    def setUp(self):
        self.datos = Datos()
        self.modelo = m.ModeloVales(SimpleNamespace(id_usuario=64), self.datos, Util())
    def test_instancia_la_clase_nativa_sin_redefinir_conexion(self):
        with patch.object(m, 'ComandosBaseDatos', return_value=self.datos) as clase:
            modelo = m.ModeloVales(SimpleNamespace(id_usuario=64), utilerias=Util())
        clase.assert_called_once_with()
        self.assertIs(modelo.bd, self.datos)
    def guardar(self, **cambios):
        return self.modelo.guardar(factura(), '139', [partida(**cambios)])
    def test_captura_usa_peso_y_lista_del_cliente(self):
        p = self.modelo.capturar_codigo('codigo', factura())
        self.assertEqual(p['cantidad'], Decimal('.500'))
        self.assertEqual(p['total'], Decimal(50))
        self.assertEqual(self.datos.lista, ((20, 4), dict(no_en_venta=True, business_entity_id=50)))
    def test_captura_restringida_acepta_producto_de_factura(self):
        p = self.modelo.capturar_codigo('codigo', factura(RestringirProductos=1))
        self.assertEqual(p['ProductID'], 20)
    def test_captura_restringida_rechaza_producto_ajeno(self):
        self.datos.productos_factura = set()
        with self.assertRaisesRegex(ValueError, 'no está incluido.*FM100'):
            self.modelo.capturar_codigo('codigo', factura(RestringirProductos=1))
        self.assertFalse(self.datos.items)
    def test_bandera_cero_preserva_captura_libre(self):
        self.datos.productos_factura = set()
        with patch.object(self.datos, 'fetchone') as consulta:
            p = self.modelo.capturar_codigo('codigo', factura(RestringirProductos=0))
        self.assertEqual(p['ProductID'], 20)
        consulta.assert_not_called()
    def test_restriccion_consulta_solo_partidas_vigentes_de_la_factura(self):
        with patch.object(self.datos, 'fetchone', return_value=1) as consulta:
            self.modelo.validar_producto_factura(factura(RestringirProductos=1), 20)
        sql, parametros = consulta.call_args.args
        self.assertEqual(parametros, (100, 20))
        self.assertIn('DeletedOn IS NULL', sql)
    def test_guardado_revalida_bandera_activada_durante_captura(self):
        self.datos.actual = factura(RestringirProductos=1)
        self.datos.productos_factura = set()
        with patch.object(self.datos, 'crear_documento') as crear:
            with self.assertRaisesRegex(ValueError, 'no está incluido'):
                self.guardar()
        crear.assert_not_called()
        self.assertFalse(self.datos.items)
        self.assertFalse(self.datos.comandos)
    def test_guardado_restringido_acepta_producto_de_factura(self):
        self.datos.actual = factura(RestringirProductos=1)
        self.assertEqual(self.guardar(), 'SA123')
    def test_guardado_libre_acepta_producto_ajeno(self):
        self.datos.productos_factura = set()
        self.assertEqual(self.guardar(), 'SA123')
    def test_salida_y_control_usan_metodos_nativos(self):
        self.assertEqual(self.guardar(), 'SA123')
        self.assertEqual(self.datos.items[0][4:7], (0, Decimal(40), Decimal(40)))
        registros = [p for sql, p in self.datos.comandos if 'INSERT INTO dbo.zvwVales' in sql]
        self.assertEqual(registros[0], (100, 'SA123', Decimal('100.00'), 139, 64, 'PM10'))
        sql_control = next(sql for sql, _ in self.datos.comandos if 'INSERT INTO dbo.zvwVales' in sql)
        self.assertIn('Pedido', sql_control)
    def test_guarda_precio_cliente_y_conserva_costo_de_inventario(self):
        self.guardar()
        actualizaciones = [(sql, params) for sql, params in self.datos.comandos
                           if 'UPDATE dbo.docDocumentItem SET UnitPrice' in sql]
        self.assertEqual(len(actualizaciones), 1)
        sql, params = actualizaciones[0]
        self.assertEqual(params, (Decimal(100), 123, 456, 20))
        self.assertNotIn('SET CostPrice', sql)
        self.assertNotIn('orgProductKardex', sql)
        self.assertEqual(self.datos.items[0][4:7], (0, Decimal(40), Decimal(40)))
    def test_precio_no_confirmado_impide_registrar_control_y_cerrar_factura(self):
        self.datos.precios_confirmados = 0
        with self.assertRaisesRegex(RuntimeError, 'No se confirmó el precio y costo'):
            self.guardar()
        self.assertFalse(any('INSERT INTO dbo.zvwVales' in sql for sql, _ in self.datos.comandos))
        self.assertFalse(any('SET Status = 1' in sql for sql, _ in self.datos.comandos))
    def test_fallo_actualizacion_precio_no_registra_control(self):
        comando_original = self.datos.command
        def comando(sql, params=()):
            if 'UPDATE dbo.docDocumentItem SET UnitPrice' in sql:
                raise RuntimeError('Error al guardar UnitPrice')
            return comando_original(sql, params)
        with patch.object(self.datos, 'command', side_effect=comando):
            with self.assertRaisesRegex(RuntimeError, 'UnitPrice'):
                self.guardar()
        self.assertFalse(any('INSERT INTO dbo.zvwVales' in sql for sql, _ in self.datos.comandos))
    def test_precio_comercial_conserva_precision_de_seis_decimales(self):
        self.datos.precio = Decimal('100.123456')
        self.guardar(precio=self.datos.precio, total=self.datos.precio)
        params = next(params for sql, params in self.datos.comandos
                      if 'UPDATE dbo.docDocumentItem SET UnitPrice' in sql)
        self.assertEqual(params[0], Decimal('100.123456'))
    def test_sin_vales_bloquea(self):
        self.datos.actual = factura(Pendientes=0)
        with self.assertRaisesRegex(ValueError, 'pendientes'):
            self.guardar()
        self.assertFalse(self.datos.items)
    def test_sin_saldo_bloquea(self):
        with self.assertRaises(ValueError):
            self.modelo.validar_disponibilidad(factura(Saldo=0))
    def test_cupo_no_configurado_bloquea(self):
        with self.assertRaises(ValueError):
            self.modelo.validar_disponibilidad(factura(NumeroVales=None))
    def test_numero_duplicado_no_impide_guardar_el_vale_real(self):
        self.datos.duplicado = 1
        self.assertEqual(self.guardar(), 'SA123')
        self.assertTrue(self.datos.items)
    def test_avisa_numero_duplicado_antes_de_capturar_productos(self):
        self.datos.duplicado = 1
        with self.assertRaisesRegex(ValueError, r'El vale 49 ya fue aplicado.*FM100'):
            self.modelo.validar_numero_vale(factura(), '49')
        self.assertFalse(self.datos.items)
        self.assertFalse(self.datos.comandos)
    def test_numero_libre_normaliza_ceros_y_consulta_factura(self):
        with patch.object(self.datos, 'fetchone', return_value=0) as consulta:
            self.assertEqual(self.modelo.validar_numero_vale(factura(), '049'), 49)
        sql, parametros = consulta.call_args.args
        self.assertEqual(parametros, (100, 49))
        self.assertIn('Status = 0 AND DeletedOn IS NULL', sql)
    def test_numero_invalido_no_consulta_base(self):
        with patch.object(self.datos, 'fetchone') as consulta:
            with self.assertRaises(ValueError):
                self.modelo.validar_numero_vale(factura(), '')
        consulta.assert_not_called()
    def test_desborde_de_saldo_permite_guardar_y_cierra_factura(self):
        self.datos.actual = factura(Saldo=Decimal('99.99'))
        self.assertEqual(self.guardar(), 'SA123')
        registro = next(params for sql, params in self.datos.comandos
                        if 'INSERT INTO dbo.zvwVales' in sql)
        self.assertEqual(registro[2], Decimal('100.00'))
        self.assertTrue(any('SET Status = 1' in sql for sql, _ in self.datos.comandos))
    def test_no_se_impone_un_tope_de_desborde_no_especificado(self):
        self.datos.actual = factura(Saldo=Decimal('90.00'))
        self.assertEqual(self.guardar(), 'SA123')
    def test_importe_redondeado_a_cero_sigue_bloqueado(self):
        with self.assertRaisesRegex(ValueError, 'El importe debe ser positivo'):
            self.guardar(cantidad=Decimal('0.000001'), total=Decimal('0.000100'))
        self.assertFalse(self.datos.items)
    def test_precio_cambiado_bloquea(self):
        self.datos.precio = Decimal(101)
        with self.assertRaisesRegex(ValueError, 'Cambió el precio'):
            self.guardar()
    def test_sin_kardex_no_registra_vale(self):
        self.datos.faltantes = 1
        with self.assertRaisesRegex(RuntimeError, 'inventario'):
            self.guardar()
        self.assertFalse(any('INSERT INTO dbo.zvwVales' in sql for sql, _ in self.datos.comandos))
    def test_fallo_control_no_cierra_factura(self):
        self.datos.fallo = True
        with self.assertRaises(RuntimeError):
            self.guardar()
        self.assertTrue(self.datos.items)
        self.assertFalse(any('SET Status = 1' in sql for sql, _ in self.datos.comandos))
    def test_ultimo_vale_cierra_factura(self):
        self.datos.actual = factura(Pendientes=1)
        self.guardar()
        self.assertTrue(any('SET Status = 1' in sql for sql, _ in self.datos.comandos))
    def test_saldo_agotado_cierra_factura(self):
        self.datos.actual = factura(Saldo=100)
        self.guardar()
        self.assertTrue(any('SET Status = 1' in sql for sql, _ in self.datos.comandos))
    def test_surtido_parcial_deja_abierta(self):
        self.guardar()
        self.assertFalse(any('SET Status = 1' in sql for sql, _ in self.datos.comandos))
    def test_claves_invalidas(self):
        for clave in ('', '-1', '1.5', 'NaN', '0', '2147483648', '１２３'):
            with self.subTest(clave=clave), self.assertRaises(ValueError):
                self.modelo.validar_clave(clave)
    def test_cantidad_invalida_no_afecta_inventario(self):
        with self.assertRaises(ValueError):
            self.guardar(cantidad=Decimal('-1'))
        self.assertFalse(self.datos.items)
    def test_nan_rechazado(self):
        with self.assertRaises(ValueError):
            m.decimal('NaN')
    def test_factura_desactivada_durante_captura(self):
        self.datos.actual = None
        with self.assertRaises(ValueError):
            self.guardar()
        self.assertFalse(self.datos.items)


class AvisoValeTest(unittest.TestCase):
    def pantalla(self):
        from unittest.mock import Mock
        return SimpleNamespace(
            _validando_vale=False, guardando=False, factura=factura(),
            clave=Mock(), modelo=Mock(), info=Mock(), codigo=Mock(),
            _estado=Mock(), error=Mock(), master=Mock(),
        )
    def test_aviso_duplicado_no_bloquea_controles_ni_roba_foco(self):
        from herramientas.capturar_documento.herramientas.vales.main import Vales
        pantalla = self.pantalla()
        pantalla.clave.get.return_value = '49'
        pantalla.modelo.validar_numero_vale.side_effect = ValueError('El vale 49 ya fue aplicado.')
        Vales.validar_numero_vale(pantalla)
        pantalla.info.configure.assert_called_once_with(text='Aviso: El vale 49 ya fue aplicado.')
        pantalla._estado.assert_not_called()
        pantalla.error.assert_not_called()
        pantalla.clave.focus_set.assert_not_called()
        pantalla.master.after_idle.assert_not_called()
        self.assertFalse(pantalla._validando_vale)
    def test_captura_permite_desborde_y_refresca_total_visible(self):
        from unittest.mock import Mock
        from herramientas.capturar_documento.herramientas.vales.main import Vales
        pantalla = self.pantalla()
        pantalla.factura = factura(Saldo=Decimal('99.99'))
        pantalla.codigo.get.return_value = 'codigo'
        pantalla.modelo.capturar_codigo.return_value = partida()
        pantalla.partidas = []
        pantalla.refrescar_partidas = Mock()
        Vales.capturar(pantalla)
        self.assertEqual(pantalla.partidas, [partida()])
        pantalla.refrescar_partidas.assert_called_once()
        pantalla.error.assert_not_called()
    def test_fallo_consulta_tambien_es_informativo(self):
        from herramientas.capturar_documento.herramientas.vales.main import Vales
        pantalla = self.pantalla()
        pantalla.clave.get.return_value = '49'
        pantalla.modelo.validar_numero_vale.side_effect = RuntimeError('No se pudo consultar el vale.')
        Vales.validar_numero_vale(pantalla)
        pantalla._estado.assert_not_called()
        pantalla.error.assert_not_called()
        self.assertFalse(pantalla._validando_vale)


if __name__ == '__main__':
    unittest.main()
