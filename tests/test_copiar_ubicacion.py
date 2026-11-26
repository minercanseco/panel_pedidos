import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import unittest

ROOT = Path(__file__).resolve().parents[1]
FORM = ROOT / 'herramientas/capturar_documento/herramientas/capturar_cliente'
spec = importlib.util.spec_from_file_location("ubicacion_copiar_test", FORM / "ubicacion.py")
ubicacion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ubicacion)


class CopiarUbicacionTests(unittest.TestCase):
    def test_existing_saved_location_is_a_whatsapp_link_for_selected_address(self):
        db = Mock()
        db.fetchall.return_value = [{"Latitude": "19.8568040", "Longitude": "-90.5192870"}]
        text = ubicacion.texto_ubicacion_guardada_whatsapp(db, 9760, 9863)
        self.assertTrue(text.startswith("📍 *Ubicación del domicilio:*\nhttps://www.google.com/maps/"))
        self.assertIn("19.8568040", text)
        self.assertNotIn("por favor", text)
        sql, params = db.fetchall.call_args.args
        self.assertEqual((9863, 9760), params)
        self.assertIn("A.BusinessEntityID = ?", sql)
        self.assertIn("A.DeletedOn IS NULL", sql)

    def test_missing_partial_invalid_or_deleted_address_requests_location(self):
        for rows in ([], [{"Latitude": None,"Longitude": None}], [{"Latitude": 19,"Longitude": None}], [{"Latitude": 91,"Longitude": -90}], [{"Latitude": "NaN","Longitude": -90}]):
            db = Mock()
            db.fetchall.return_value = rows
            self.assertEqual(ubicacion.LEYENDA_UBICACION_WHATSAPP,
                ubicacion.texto_ubicacion_guardada_whatsapp(db, 12, 55))
        self.assertEqual("📍 Para facilitar tu entrega, por favor compártenos por WhatsApp la ubicación de este domicilio.", ubicacion.LEYENDA_UBICACION_WHATSAPP)

    def test_new_address_never_borrows_another_saved_location(self):
        db = Mock()
        self.assertEqual(ubicacion.LEYENDA_UBICACION_WHATSAPP, ubicacion.texto_ubicacion_guardada_whatsapp(db, 12, 0))
        db.fetchall.assert_not_called()

    def test_database_failure_does_not_misrepresent_missing_location(self):
        db = Mock()
        db.fetchall.side_effect = RuntimeError("Database unavailable")
        with self.assertRaises(RuntimeError):
            ubicacion.texto_ubicacion_guardada_whatsapp(db, 12, 55)

    def test_fiscal_and_additional_messages_keep_confirmation_and_fiscal_fields(self):
        for filename, expected_address in (("formulario_cliente_controlador.py", 55), ("direccion_adicional.py", 56)):
            with self.subTest(filename=filename):
                tree = ast.parse((FORM/filename).read_text())
                method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "_buscar_informacion_direccion_whatsapp")
                reader = Mock(return_value="📍 *Ubicación del domicilio:*\nhttps://www.google.com/maps/?q=19,-90")
                namespace = {"texto_ubicacion_guardada_whatsapp": reader, "LEYENDA_UBICACION_WHATSAPP": ubicacion.LEYENDA_UBICACION_WHATSAPP}
                exec(compile(ast.Module(body=[method], type_ignores=[]), str(FORM/filename), "exec"), namespace)
                client = SimpleNamespace(official_name="Cliente", address_fiscal_street="Calle", address_fiscal_ext_number="10", address_fiscal_zip_code="24000", address_fiscal_city="Colonia", address_fiscal_municipality="Campeche", address_fiscal_state_province="Campeche", phone="9810000000", cellphone="9811111111", address_fiscal_comments="Referencia", delivery_cost=20, cayal_customer_type_id=2, email="cliente@example.com", official_number="RFC", receptor_uso_cfdi="G03", business_entity_id=12, address_fiscal_detail_id=55)
                db = Mock()
                obj = SimpleNamespace(_modelo=SimpleNamespace(cliente=client, base_de_datos=db), _address_detail_id=56,
                    _ubicacion={"Latitude": 88, "Longitude": 99}, info_direccion={"Latitude": 88,"Longitude": 99},
                    _ventanas=SimpleNamespace(obtener_input_componente=lambda field: "Dato"))
                message = namespace[method.name](obj)
                reader.assert_called_once_with(db, 12, expected_address)
                self.assertIn("¿Podría confirmar si los datos de su dirección son correctos?", message)
                self.assertIn("*Correo:*", message)
                self.assertIn("*RFC:*", message)
                self.assertIn("*Uso CFDI:*", message)
                self.assertIn("correctos?  \n\n📍 *Ubicación del domicilio:*\nhttps://www.google.com/maps/?q=19,-90\n\n👤 *Cliente:*", message)
                self.assertNotIn("88", message)
                reader.return_value = ubicacion.LEYENDA_UBICACION_WHATSAPP
                message = namespace[method.name](obj)
                self.assertTrue(message.startswith(ubicacion.LEYENDA_UBICACION_WHATSAPP + "\n\n📍 ¿Podría confirmar"))
                self.assertEqual(1, message.count(ubicacion.LEYENDA_UBICACION_WHATSAPP))


class SeleccionarClienteCopiarTests(unittest.TestCase):
    def run_copy(self, location):
        tree = ast.parse((ROOT / 'herramientas/capturar_documento/buscar_generales_cliente.py').read_text())
        method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "_copiar_informacion_direccion")
        copy = Mock()
        location_reader = Mock(return_value=location)
        namespace = {"pyperclip": SimpleNamespace(copy=copy),
            "texto_ubicacion_guardada_whatsapp": location_reader,
            "LEYENDA_UBICACION_WHATSAPP": ubicacion.LEYENDA_UBICACION_WHATSAPP}
        exec(compile(ast.Module(body=[method], type_ignores=[]), "selector_cliente", "exec"), namespace)
        db = Mock()
        db.buscar_informacion_direccion_whatsapp.return_value = "📍 ¿Podría confirmar si los datos de su dirección son correctos?\n\nCliente y dirección\n"
        window = Mock()
        obj = SimpleNamespace(_base_de_datos=db, _info_cliente_seleccionado=[{"BusinessEntityID": 12}],
            _documento=SimpleNamespace(address_detail_id=56), _master=window)
        namespace[method.name](obj)
        location_reader.assert_called_once_with(db, 12, 56)
        db.buscar_informacion_direccion_whatsapp.assert_called_once_with(56, 12)
        window.iconify.assert_called_once()
        copy.assert_called_once()
        return copy.call_args.args[0]

    def test_selector_places_missing_location_request_before_confirmation(self):
        message = self.run_copy(ubicacion.LEYENDA_UBICACION_WHATSAPP)
        self.assertTrue(message.startswith(ubicacion.LEYENDA_UBICACION_WHATSAPP + "\n\n📍 ¿Podría confirmar"))
        self.assertEqual(1, message.count(ubicacion.LEYENDA_UBICACION_WHATSAPP))

    def test_selector_appends_saved_point_without_requesting_location(self):
        link = "📍 *Ubicación del domicilio:*\nhttps://www.google.com/maps/?q=19,-90"
        message = self.run_copy(link)
        self.assertTrue(message.startswith("📍 ¿Podría confirmar"))
        self.assertIn("correctos?\n\n" + link + "\n\nCliente y dirección", message)
        self.assertNotIn(ubicacion.LEYENDA_UBICACION_WHATSAPP, message)
