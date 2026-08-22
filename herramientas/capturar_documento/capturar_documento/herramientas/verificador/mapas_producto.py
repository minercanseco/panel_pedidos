import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple, Union

from PIL import Image, ImageDraw


Coordenada = Tuple[int, int]


class PintorProductoCarnico:
    """
    Pinta sobre una imagen las zonas asociadas con un producto.

    Responsabilidades:
        - recibir la imagen;
        - recibir el producto;
        - recibir sus zonas;
        - pintar únicamente los polígonos correspondientes.
    """

    def __init__(
            self,
            imagen: Union[str, Path, Image.Image],
            producto: Dict[str, Any],
            zonas: Iterable[Dict[str, Any]]
    ):
        self.imagen_original = self._normalizar_imagen(imagen)
        self.producto = producto or {}
        self.zonas = list(zonas or [])

    @staticmethod
    def _normalizar_imagen(
            imagen: Union[str, Path, Image.Image]
    ) -> Image.Image:
        if isinstance(imagen, Image.Image):
            return imagen.convert("RGBA")

        ruta = Path(imagen)

        if not ruta.exists():
            raise FileNotFoundError(
                "No se encontró la imagen: {}".format(ruta)
            )

        return Image.open(ruta).convert("RGBA")

    @staticmethod
    def _convertir_coordenadas(
            coordenadas: Any
    ) -> List[Coordenada]:
        if coordenadas is None:
            return []

        if isinstance(coordenadas, str):
            coordenadas = coordenadas.strip()

            if not coordenadas:
                return []

            try:
                coordenadas = json.loads(coordenadas)
            except json.JSONDecodeError as error:
                raise ValueError(
                    "Coordinates no contiene JSON válido."
                ) from error

        if not isinstance(coordenadas, (list, tuple)):
            raise TypeError(
                "Coordinates debe ser una lista o texto JSON."
            )

        poligono = []

        for punto in coordenadas:
            if (
                    not isinstance(punto, (list, tuple))
                    or len(punto) != 2
            ):
                raise ValueError(
                    "Cada coordenada debe contener [x, y]."
                )

            try:
                x = int(punto[0])
                y = int(punto[1])
            except (TypeError, ValueError) as error:
                raise ValueError(
                    "Las coordenadas deben ser numéricas."
                ) from error

            poligono.append((x, y))

        return poligono

    def pintar(
            self,
            color_relleno=(0, 255, 255, 130),
            color_contorno = (0, 0, 255, 255),
            ancho_contorno = 6
    ) -> Image.Image:
        """
        Pinta únicamente las zonas asociadas con el producto.
        """
        imagen = self.imagen_original.copy()

        zonas_validas = self._obtener_zonas_validas()

        if not zonas_validas:
            return imagen

        capa = Image.new(
            mode="RGBA",
            size=imagen.size,
            color=(0, 0, 0, 0)
        )

        dibujo = ImageDraw.Draw(capa)

        for zona in zonas_validas:
            dibujo.polygon(
                zona["Coordinates"],
                fill=color_relleno,
                outline=color_contorno,
                width=ancho_contorno
            )

        return Image.alpha_composite(
            imagen,
            capa
        )

    def _obtener_zonas_validas(
            self
    ) -> List[Dict[str, Any]]:
        categoria_producto = str(
            self.producto.get("Category1", "")
        ).strip().upper()

        resultado = []

        for zona in self.zonas:
            categoria_zona = str(
                zona.get("Category1", "")
            ).strip().upper()

            if (
                    categoria_producto
                    and categoria_zona
                    and categoria_producto != categoria_zona
            ):
                continue

            poligono = self._convertir_coordenadas(
                zona.get("Coordinates")
            )

            if len(poligono) < 3:
                continue

            resultado.append({
                "ZoneID": int(
                    zona.get("ZoneID", 0) or 0
                ),
                "ZoneName": str(
                    zona.get("ZoneName", "")
                ).strip(),
                "Category1": categoria_zona,
                "Coordinates": poligono,
            })

        return resultado