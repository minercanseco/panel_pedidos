import unittest
from decimal import Decimal

from herramientas.capturar_documento.herramientas.partida_paquete_promocional import (
    PartidaPaquetePromocional,
)
from herramientas.capturar_documento.modelo_captura import ModeloCaptura


class BaseDatosComponentes:
    def buscar_product_id_clave(self, clave):
        if clave == '070122':
            return [{'ProductID': 250}]
        return []

    def fetchall(self, consulta, parametros):
        if 'orgProductComponent' in consulta:
            return [{
                'ProductComponentID': 72,
                'ParentProductID': 4431,
                'ComponentProductID': 250,
                'Description': 'CEBOLLA BLANCA',
                'Quantity': Decimal('0.6'),
                'UnitPrice': Decimal('20'),
                'ProductKey': '070122',
                'Unit': 'KILO',
                'ClaveUnidad': 'KGM',
            }]
        return []


class PaquetesPromocionalesTest(unittest.TestCase):
    def test_multiplica_componentes_por_cantidad_del_paquete(self):
        modelo = object.__new__(ModeloCaptura)
        modelo.base_de_datos = BaseDatosComponentes()

        componentes = modelo.buscar_componentes_paquete(4431, 2)

        self.assertEqual(componentes[0]['RequiredQuantity'], Decimal('1.2'))
        self.assertIsNone(componentes[0]['SuppliedQuantity'])

    def test_kilos_aceptan_cualquier_cantidad_mayor_que_cero(self):
        validar = PartidaPaquetePromocional.cantidad_valida
        self.assertTrue(validar(Decimal('0.1'), Decimal('1'), 'KGM'))
        self.assertTrue(validar(Decimal('1.2'), Decimal('1'), 'KGM'))
        self.assertFalse(validar(Decimal('0'), Decimal('1'), 'KGM'))

    def test_piezas_exigen_la_cantidad_completa(self):
        validar = PartidaPaquetePromocional.cantidad_valida
        self.assertTrue(validar(Decimal('2'), Decimal('2'), 'H87'))
        self.assertFalse(validar(Decimal('1'), Decimal('2'), 'H87'))
        self.assertFalse(validar(Decimal('3'), Decimal('2'), 'H87'))

    def test_codigo_de_barras_resuelve_el_producto_del_componente(self):
        modelo = object.__new__(ModeloCaptura)
        modelo.base_de_datos = BaseDatosComponentes()

        self.assertEqual(modelo.buscar_product_id_codigo('070122'), 250)
        self.assertIsNone(modelo.buscar_product_id_codigo('NO-EXISTE'))

    def test_una_pieza_parcial_continua_pendiente_para_otro_escaneo(self):
        componente = {
            'RequiredQuantity': Decimal('2'),
            'SuppliedQuantity': Decimal('1'),
            'ClaveUnidad': 'H87',
        }
        self.assertFalse(
            PartidaPaquetePromocional.componente_completo(componente)
        )

        componente['SuppliedQuantity'] = Decimal('2')
        self.assertTrue(
            PartidaPaquetePromocional.componente_completo(componente)
        )


if __name__ == '__main__':
    unittest.main()
