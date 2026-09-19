import unittest
from decimal import Decimal
from types import SimpleNamespace

from herramientas.capturar_documento.controlador_captura import ControladorCaptura
from herramientas.capturar_documento.herramientas.historial_cliente import HistorialCliente


class UtileriasFalsas:
    @staticmethod
    def convertir_valor_a_decimal(valor):
        return Decimal(str(valor))

    @staticmethod
    def crear_partida(producto, cantidad):
        return {
            'ProductID': producto['ProductID'],
            'ProductName': producto['ProductName'],
            'cantidad': cantidad,
        }


class CopiarDesdeHistorialTest(unittest.TestCase):
    def test_aceptar_entrega_el_documento_seleccionado(self):
        historial = object.__new__(HistorialCliente)
        llamados = []
        historial._al_aceptar = llamados.append
        historial._master = SimpleNamespace(destroy=lambda: llamados.append('cerrar'))
        historial._ventanas = SimpleNamespace(
            validar_seleccion_una_fila_treeview=lambda nombre: True,
            obtener_seleccion_filas_treeview=lambda nombre: 'fila-1',
            procesar_fila_treeview=lambda nombre, fila: {'DocumentID': 321},
            mostrar_mensaje=lambda mensaje: llamados.append(mensaje),
        )

        historial._aceptar_documento()

        self.assertEqual(llamados, [321, 'cerrar'])

    def test_copia_productos_con_precio_actual_y_omite_servicio(self):
        controlador = object.__new__(ControladorCaptura)
        controlador._utilerias = UtileriasFalsas()
        controlador.documento = SimpleNamespace(items=[])
        mensajes = []
        controlador._ventanas = SimpleNamespace(mostrar_mensaje=mensajes.append)
        controlador._modelo = SimpleNamespace(
            base_de_datos=SimpleNamespace(
                buscar_partidas_documento=lambda document_id: [
                    {
                        'ProductID': 11,
                        'ProductName': 'Producto anterior',
                        'cantidad': Decimal('2.5'),
                        'Comments': 'Sin cebolla',
                    },
                    {
                        'ProductID': 5606,
                        'ProductName': 'Servicio a domicilio',
                        'cantidad': Decimal('1'),
                    },
                ]
            ),
            buscar_info_productos_por_ids=lambda product_id: [{
                'ProductID': product_id,
                'ProductName': 'Producto vigente',
                'SalePrice': Decimal('25'),
            }],
        )

        def agregar(partida, **kwargs):
            controlador.documento.items.append(partida)

        controlador._agregar_partida_tabla = agregar

        copiado = controlador._copiar_documento_historial(123)

        self.assertTrue(copiado)
        self.assertEqual(len(controlador.documento.items), 1)
        self.assertEqual(
            controlador.documento.items[0]['ProductName'],
            'Producto vigente',
        )
        self.assertEqual(
            controlador.documento.items[0]['Comments'], 'Sin cebolla'
        )
        self.assertEqual(mensajes, [])

    def test_no_cierra_historial_si_no_se_pudo_copiar(self):
        historial = object.__new__(HistorialCliente)
        llamados = []
        historial._al_aceptar = lambda document_id: False
        historial._master = SimpleNamespace(destroy=lambda: llamados.append('cerrar'))
        historial._ventanas = SimpleNamespace(
            validar_seleccion_una_fila_treeview=lambda nombre: True,
            obtener_seleccion_filas_treeview=lambda nombre: 'fila-1',
            procesar_fila_treeview=lambda nombre, fila: {'DocumentID': 321},
            mostrar_mensaje=lambda mensaje: llamados.append(mensaje),
        )

        historial._aceptar_documento()

        self.assertEqual(llamados, [])


if __name__ == '__main__':
    unittest.main()
