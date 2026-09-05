import unittest
import sys
from pathlib import Path

import barcode

# La aplicación agrega ``herramientas`` a la ruta al cargar la copia
# embebida de capturar_documento. Replicamos ese arranque en la prueba.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'herramientas'))

from herramientas.capturar_documento.herramientas.imprimir_modulo.imprimir_modulo import (
    ImprimirModulo,
)
from herramientas.capturar_documento.herramientas.cobrar_cartera.buscar_generales_cliente_cartera import (
    BuscarGeneralesClienteCartera,
)


class UtileriasPrueba:
    @staticmethod
    def es_cantidad(valor):
        return str(valor).isdigit()


class VentanasPrueba:
    def __init__(self):
        self.mensajes = []

    def mostrar_mensaje(self, mensaje):
        self.mensajes.append(mensaje)

    def enfocar_componente(self, _nombre):
        pass


class CodigosBarrasCapturarDocumentoTest(unittest.TestCase):
    def herramienta_cartera(self):
        herramienta = object.__new__(BuscarGeneralesClienteCartera)
        herramienta._utilerias = UtileriasPrueba()
        herramienta._ventanas = VentanasPrueba()
        return herramienta

    def test_impresion_conserva_code128_completo(self):
        herramienta = object.__new__(ImprimirModulo)
        codigo = '0000001923889'

        resultado = herramienta._make_ean13_data_url(codigo)

        self.assertTrue(resultado.startswith('data:image/png;base64,'))
        self.assertEqual(barcode.get('code128', codigo).get_fullcode(), codigo)

    def test_cartera_acepta_code128_nuevo(self):
        self.assertEqual(
            self.herramienta_cartera()._procesar_codigo_barras(
                '0000001923889'
            ),
            192388,
        )

    def test_cartera_conserva_compatibilidad_upca(self):
        self.assertEqual(
            self.herramienta_cartera()._procesar_codigo_barras(
                '000001923889'
            ),
            192388,
        )

    def test_cartera_rechaza_lectura_incompleta(self):
        herramienta = self.herramienta_cartera()

        self.assertEqual(
            herramienta._procesar_codigo_barras('00000192388'),
            0,
        )
        self.assertTrue(herramienta._ventanas.mensajes)


if __name__ == '__main__':
    unittest.main()
