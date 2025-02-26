from cayal.ventanas import Ventanas
from cayal.util import Utilerias


class DireccionCliente:
    def __init__(self, master, documento, base_de_datos, componentes_captura):
        self._master = master
        self._componentes_captura = componentes_captura
        self.documento = documento
        self._base_de_datos = base_de_datos

        self._consulta_direcciones = None

        self._ventanas = Ventanas(self._master)
        self._utilerias = Utilerias()

        self._cargar_componentes_forma()
        self._rellenar_cbx_direcciones()
        self._agregar_eventos()

        self._ventanas.configurar_ventana_ttkbootstrap(titulo='Dirección cliente')

    def _cargar_componentes_forma(self):
        componentes = [('cbx_direcciones', 'Dirección:'),
                       ('btn_actualizar', 'Actualizar'),
                       ]
        self._ventanas.crear_formulario_simple(componentes, 'Direcciones')

    def _rellenar_componentes(self):
        self._rellenar_cbx_direcciones()

    def _rellenar_cbx_direcciones(self):
        cbx_direcciones = self._ventanas.componentes_forma['cbx_direcciones']
        business_entity_id = self.documento.business_entity_id
        self._consulta_direcciones = self._base_de_datos.rellenar_cbx_direcciones(business_entity_id,
                                                                                  cbx_direcciones)

    def _agregar_eventos(self):
        eventos = {
            'btn_actualizar': lambda: self._asignar_direccion(),
            'btn_cancelar': lambda: self._master.destroy(),
        }
        self._ventanas.cargar_eventos(eventos)

    def _asignar_direccion(self):
        seleccion = self._ventanas.obtener_input_componente('cbx_direcciones')
        direcccion_seleccionada = self._base_de_datos.procesar_direccion_seleccionada_cbx(seleccion,
                                                                            self._consulta_direcciones)

        address_detail_id = direcccion_seleccionada.get('address_detail_id', 0)
        direccion = self._base_de_datos.buscar_detalle_direccion_formateada(address_detail_id)

        self.documento.address_details = direccion
        self.documento.address_detail_id = address_detail_id
        self.documento.address_name = direccion.get('address_name', 'Dirección')
        self.documento.depot_id = direccion.get('depot_id', 0)
        self.documento.depot_name = direccion.get('depot_name', '')

        self._master.destroy()


