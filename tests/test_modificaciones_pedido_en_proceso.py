import unittest
from types import SimpleNamespace

from herramientas.capturar_documento.llamar_instancia_captura_pedido import (
    LlamarInstanciaCapturaPedido,
)


class BaseDeDatosFalsa:
    def __init__(self):
        self.comandos = []

    def command(self, sql, parametros):
        self.comandos.append((sql, parametros))


class ModificacionesPedidoEnProcesoTest(unittest.TestCase):
    def crear_captura(self, estados):
        captura = object.__new__(LlamarInstanciaCapturaPedido)
        captura._documento = SimpleNamespace(
            items_extra=[
                {'ItemProductionStatusModified': estado}
                for estado in estados
            ]
        )
        captura._base_de_datos = BaseDeDatosFalsa()
        return captura

    def test_marca_la_cabecera_si_hay_agregado_editado_o_eliminado(self):
        for estado in (1, 2, 3):
            with self.subTest(estado=estado):
                captura = self.crear_captura([estado])

                captura._marcar_modificaciones_en_proceso(25)

                self.assertEqual(len(captura._base_de_datos.comandos), 1)
                sql, parametros = captura._base_de_datos.comandos[0]
                self.assertIn('SET WithModifications = 1', sql)
                self.assertIn('AND StatusID = 2', sql)
                self.assertEqual(parametros, (25,))

    def test_no_marca_la_cabecera_si_no_hay_cambios_de_partidas(self):
        captura = self.crear_captura([0, 4])

        captura._marcar_modificaciones_en_proceso(25)

        self.assertEqual(captura._base_de_datos.comandos, [])


if __name__ == '__main__':
    unittest.main()
