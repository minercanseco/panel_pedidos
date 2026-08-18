import gzip
import os
import pickle
from datetime import datetime
from pathlib import Path


class GestorOfertasCliente:
    CACHE_DIR = "../../.offers_cache"

    def __init__(self, base_de_datos, utilerias):
        self._base_de_datos = base_de_datos
        self._utilerias = utilerias

        # Acumulador en memoria por lista de precios
        self._ofertas_por_lista = {}
        self._customer_types_ids_ofertas = set()

        try:
            from zoneinfo import ZoneInfo
            self._tz = ZoneInfo("America/Merida")
        except Exception:
            self._tz = None

    @property
    def ofertas_por_lista(self):
        return self._ofertas_por_lista

    @property
    def customer_types_ids_ofertas(self):
        return self._customer_types_ids_ofertas

    def obtener_ofertas_cliente(self, cliente) -> dict:
        customer_type_id = cliente.customer_type_id
        return self.obtener_ofertas_por_lista(customer_type_id)

    def obtener_ofertas_por_lista(self, customer_type_id: int) -> dict:
        """
        Devuelve las ofertas empaquetadas para una lista de precios.
        Si ya existen en memoria, no consulta disco ni base de datos.
        """

        if customer_type_id in self._ofertas_por_lista:
            self._customer_types_ids_ofertas.add(customer_type_id)
            return self._ofertas_por_lista[customer_type_id]

        ofertas_disk = self._cache_load_if_today(customer_type_id)

        if ofertas_disk is not None:
            self._ofertas_por_lista[customer_type_id] = ofertas_disk
            self._customer_types_ids_ofertas.add(customer_type_id)
            self._cache_cleanup_not_today()
            return ofertas_disk

        ofertas = self._consultar_y_empaquetar_ofertas(customer_type_id)

        self._ofertas_por_lista[customer_type_id] = ofertas
        self._customer_types_ids_ofertas.add(customer_type_id)

        self._cache_save_today(customer_type_id, ofertas)
        self._cache_cleanup_not_today()

        return ofertas

    def existe_oferta_para_lista(self, customer_type_id: int) -> bool:
        return customer_type_id in self._ofertas_por_lista

    def limpiar_memoria(self):
        self._ofertas_por_lista.clear()
        self._customer_types_ids_ofertas.clear()

    def _consultar_y_empaquetar_ofertas(self, customer_type_id: int) -> dict:
        consulta_productos_ofertados = (
            self._base_de_datos.buscar_productos_en_oferta(
                lista_precios=customer_type_id
            )
        )

        productos_ids = list({
            reg["ProductID"]
            for reg in consulta_productos_ofertados
        })

        consulta_productos = (
            self._buscar_info_productos_por_ids(
                productos_ids
            )
        )

        consulta_procesada = (
            self._agregar_impuestos_productos(
                consulta_productos
            )
        )

        return {
            "consulta_productos": consulta_procesada,
            "consulta_productos_ofertados": consulta_productos_ofertados,
            "consulta_productos_ofertados_btn": consulta_procesada,
            "products_ids_ofertados": productos_ids
        }

    def _today_str(self):
        now = datetime.now(self._tz) if self._tz else datetime.now()
        return now.strftime("%Y%m%d")

    def _cache_dir(self):
        ruta = Path(self.CACHE_DIR)
        ruta.mkdir(parents=True, exist_ok=True)
        return ruta

    def _cache_path(self, customer_type_id: int, day: str):
        return self._cache_dir() / f"ofertas_{customer_type_id}_{day}.pkl.gz"

    def _cache_load_if_today(self, customer_type_id: int):
        day = self._today_str()
        archivo = self._cache_path(customer_type_id, day)

        if not archivo.exists():
            return None

        try:
            with gzip.open(archivo, "rb") as fh:
                return pickle.load(fh)
        except Exception:
            try:
                archivo.unlink(missing_ok=True)
            except Exception:
                pass

            return None

    def _cache_save_today(self, customer_type_id: int, data: dict):
        day = self._today_str()
        archivo = self._cache_path(customer_type_id, day)
        temporal = archivo.with_suffix(".tmp")

        with gzip.open(temporal, "wb") as fh:
            pickle.dump(data, fh, protocol=pickle.HIGHEST_PROTOCOL)

        os.replace(temporal, archivo)

    def _cache_cleanup_not_today(self):
        day = self._today_str()

        for archivo in self._cache_dir().glob("ofertas_*.pkl.gz"):
            if not archivo.name.endswith(f"_{day}.pkl.gz"):
                try:
                    archivo.unlink(missing_ok=True)
                except Exception:
                    pass

    def _buscar_info_productos_por_ids(self, productos_ids, no_en_venta=None):

        if no_en_venta:
            return self._base_de_datos.buscar_info_productos(productos_ids,
                                                            no_en_venta=True)
        return self._base_de_datos.buscar_info_productos(productos_ids)

    def _agregar_impuestos_productos(self, consulta_productos):
        consulta_procesada = []
        for producto in consulta_productos:
            producto_procesado = self._utilerias.calcular_precio_con_impuesto_producto(producto)
            consulta_procesada.append(producto_procesado)
        return consulta_procesada