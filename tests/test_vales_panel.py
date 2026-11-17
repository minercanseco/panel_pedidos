import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from panel.herramientas_generales import HerramientasGenerales


class ValesPanelTest(unittest.TestCase):
    def herramienta(self):
        herramienta = object.__new__(HerramientasGenerales)
        herramienta._master = Mock()
        herramienta._ventanas = Mock()
        herramienta._parametros = SimpleNamespace(id_usuario=64, id_modulo=1687, id_principal=999)
        herramienta._callbacks_autorefresco = {'pausar': Mock(), 'reanudar': Mock()}
        return herramienta

    def test_abre_copia_embebida_sin_cambiar_parametros_del_pedido(self):
        herramienta = self.herramienta()
        with patch('herramientas.capturar_documento.herramientas.vales.main.Vales') as vales:
            herramienta._vales()
        ventana = herramienta._ventanas.crear_popup_ttkbootstrap.return_value
        vales.assert_called_once_with(ventana, herramienta._parametros)
        ventana.wait_window.assert_called_once()
        herramienta._callbacks_autorefresco['pausar'].assert_called_once()
        herramienta._callbacks_autorefresco['reanudar'].assert_called_once()
        self.assertFalse(herramienta._vales_abierto)
        self.assertEqual(herramienta._parametros.id_principal, 999)
        self.assertEqual(herramienta._parametros.id_modulo, 1687)

    def test_error_al_abrir_cierra_popup_y_reanuda_panel(self):
        herramienta = self.herramienta()
        with patch('herramientas.capturar_documento.herramientas.vales.main.Vales', side_effect=RuntimeError('Error de apertura')):
            herramienta._vales()
        ventana = herramienta._ventanas.crear_popup_ttkbootstrap.return_value
        ventana.destroy.assert_called_once()
        ventana.wait_window.assert_not_called()
        herramienta._ventanas.mostrar_mensaje.assert_called_once()
        herramienta._callbacks_autorefresco['reanudar'].assert_called_once()
        self.assertFalse(herramienta._vales_abierto)

    def test_no_abre_segunda_transaccion_mientras_esta_activa(self):
        herramienta = self.herramienta()
        herramienta._vales_abierto = True
        with patch('herramientas.capturar_documento.herramientas.vales.main.Vales') as vales:
            herramienta._vales()
        vales.assert_not_called()
        herramienta._ventanas.crear_popup_ttkbootstrap.assert_not_called()
        herramienta._callbacks_autorefresco['pausar'].assert_not_called()


if __name__ == '__main__':
    unittest.main()
