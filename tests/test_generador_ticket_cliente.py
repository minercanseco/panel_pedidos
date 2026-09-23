import os
import struct
import unittest

from herramientas.herramientas_panel.generador_ticket_cliente import (
    GeneradorTicketCliente,
)


class GeneradorTicketClienteTest(unittest.TestCase):
    def test_genera_una_pagina_por_cada_quince_partidas(self):
        generador = GeneradorTicketCliente()
        productos = [{'ProductID': numero} for numero in range(31)]
        generador.productos = productos
        bloques_renderizados = []
        partidas_renderizadas = []

        def generar_ticket():
            partidas_renderizadas.append([
                producto['ProductID'] for producto in generador.productos
            ])
            return str(len(generador.productos))

        generador.generar_ticket = generar_ticket
        generador._html_a_imagen = lambda html, ruta: bloques_renderizados.append(
            (int(html), os.path.basename(ruta))
        )

        paginas = generador._generar_paginas_ticket('/tmp/pedido.png')

        self.assertEqual([cantidad for cantidad, _ in bloques_renderizados], [15, 15, 1])
        self.assertEqual(
            partidas_renderizadas,
            [list(range(15)), list(range(15, 30)), [30]],
        )
        self.assertEqual(
            [nombre for _, nombre in bloques_renderizados],
            ['pedido_pagina_01.png', 'pedido_pagina_02.png', 'pedido_pagina_03.png'],
        )
        self.assertEqual(paginas[-1], '/tmp/pedido_pagina_03.png')
        self.assertIs(generador.productos, productos)

    def test_quince_partidas_conservan_una_sola_imagen(self):
        generador = GeneradorTicketCliente()
        generador.productos = [{'ProductID': numero} for numero in range(15)]
        rutas = []
        generador.generar_ticket = lambda: 'ticket'
        generador._html_a_imagen = lambda html, ruta: rutas.append(ruta)

        paginas = generador._generar_paginas_ticket('/tmp/pedido.png')

        self.assertEqual(paginas, ['/tmp/pedido.png'])
        self.assertEqual(rutas, ['/tmp/pedido.png'])

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
