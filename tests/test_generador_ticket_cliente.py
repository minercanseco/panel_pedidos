import os
import struct
import tempfile
import unittest

from PIL import Image, ImageDraw

from herramientas.herramientas_panel.generador_ticket_cliente import (
    GeneradorTicketCliente,
)


class GeneradorTicketClienteTest(unittest.TestCase):
    def test_tabla_ajusta_todas_las_columnas_al_ancho_del_ticket(self):
        generador = GeneradorTicketCliente()

        tickets = (
            generador.generar_ticket(),
            generador.generar_ticket_transferencia(),
        )

        for html in tickets:
            self.assertIn('table-layout: fixed', html)
            self.assertIn('table td:nth-child(5)', html)
            self.assertIn('width: 18%; white-space: nowrap', html)

    def test_ticket_alto_se_divide_sin_reducir_el_ancho(self):
        with tempfile.TemporaryDirectory() as directorio:
            ruta = os.path.join(directorio, 'ticket.png')
            imagen = Image.new('RGB', (600, 3300), 'white')
            dibujo = ImageDraw.Draw(imagen)
            dibujo.line((0, 1400, 599, 1400), fill='black', width=2)
            dibujo.line((0, 2800, 599, 2800), fill='black', width=2)
            imagen.save(ruta)

            paginas = GeneradorTicketCliente._dividir_imagen_ticket(ruta)

            self.assertEqual(len(paginas), 3)
            for pagina in paginas:
                with Image.open(pagina) as resultado:
                    self.assertEqual(resultado.width, 600)
                    self.assertLessEqual(resultado.height, 1500)

    def test_lista_de_archivos_windows_contiene_todas_las_paginas(self):
        rutas = [r'C:\Tickets\pagina_01.png', r'C:\Tickets\pagina_02.png']

        bloque = GeneradorTicketCliente._crear_lista_archivos_windows(rutas)

        desplazamiento, _, _, _, unicode = struct.unpack('IiiII', bloque[:20])
        nombres = bloque[desplazamiento:].decode('utf-16le')
        self.assertEqual(unicode, 1)
        self.assertIn('pagina_01.png\0', nombres)
        self.assertIn('pagina_02.png\0', nombres)
        self.assertTrue(nombres.endswith('\0\0'))


if __name__ == '__main__':
    unittest.main()
