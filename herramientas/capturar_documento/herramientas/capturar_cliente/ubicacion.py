"""Captura opcional de coordenadas y enlaces compartidos; sin API de mapas."""
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from urllib.parse import urlsplit, parse_qs, unquote
from urllib.request import Request, HTTPRedirectHandler, build_opener

CAMPOS = ('Latitude', 'Longitude', 'AccuracyMeters')
NUMERO = r'[+-]?\d+(?:\.\d+)?'
PAR = re.compile(rf'\s*({NUMERO})\s*,\s*({NUMERO})\s*')


def normalizar(latitud=None, longitud=None, precision=None):
    valores = []
    for valor, limite, decimales in zip((latitud, longitud, precision), (90, 180, 99999999.99), (7, 7, 2)):
        if valor is None or str(valor).strip() == '':
            valores.append(None)
            continue
        try:
            numero = Decimal(str(valor).strip())
            if not numero.is_finite() or abs(numero) > Decimal(str(limite)):
                raise ValueError('Las coordenadas o la precisión están fuera de rango.')
            if len(valores) == 2 and numero < 0:
                raise ValueError('La precisión no puede ser negativa.')
            valores.append(numero.quantize(Decimal(10) ** -decimales, rounding=ROUND_HALF_UP))
        except InvalidOperation as exc:
            raise ValueError('Capture números válidos para la ubicación.') from exc
    if (valores[0] is None) != (valores[1] is None):
        raise ValueError('Capture latitud y longitud, o deje ambas vacías.')
    if valores[0] is None and valores[2] is not None:
        raise ValueError('La precisión necesita una ubicación.')
    return dict(zip(CAMPOS, valores))


def _url_permitida(url):
    p = urlsplit(url)
    host = (p.hostname or '').lower()
    return (p.scheme == 'https' and p.username is None and p.password is None
            and p.port in (None, 443) and host in {
                'maps.app.goo.gl', 'goo.gl', 'maps.google.com', 'www.google.com',
                'google.com', 'maps.google.com.mx', 'www.google.com.mx', 'google.com.mx'})


class _RedireccionSegura(HTTPRedirectHandler):
    max_redirections = 5

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _url_permitida(newurl):
            raise ValueError('El enlace redirige fuera de Google Maps.')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def resolver_enlace(url):
    if not _url_permitida(url):
        raise ValueError('Utilice un enlace HTTPS de Google Maps o pegue las coordenadas.')
    try:
        with build_opener(_RedireccionSegura()).open(
                Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=5) as respuesta:
            return respuesta.geturl()
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError('No se pudo expandir el enlace. Ábralo en el navegador y copie el enlace completo o las coordenadas del marcador.') from exc


def extraer_ubicacion(texto, resolver=resolver_enlace):
    texto = texto.strip()
    par = PAR.fullmatch(texto)
    if par:
        return normalizar(*par.groups())
    urls = re.findall(r'https?://[^\s<>"\u200e\u200f]+', texto)
    if len(urls) != 1:
        raise ValueError('Pegue un solo enlace de ubicación o las coordenadas «latitud, longitud».')
    url = urls[0]
    if not _url_permitida(url):
        raise ValueError('Utilice un enlace HTTPS de Google Maps o pegue las coordenadas.')
    if urlsplit(url).hostname in ('maps.app.goo.gl', 'goo.gl'):
        url = resolver(url)
        if not _url_permitida(url):
            raise ValueError('El enlace no corresponde a Google Maps.')
    p = urlsplit(url)
    parametros = parse_qs(p.query)
    candidatos = []
    # Los datos del marcador tienen prioridad sobre el centro de la vista (@).
    for latitud, longitud in re.findall(rf'!3d({NUMERO})!4d({NUMERO})', unquote(url)):
        candidatos.append((latitud, longitud))
    if not candidatos:
        for clave in ('q', 'query', 'destination'):
            for valor in parametros.get(clave, []):
                par = PAR.fullmatch(valor)
                if par:
                    candidatos.append(par.groups())
    ubicaciones = {tuple(normalizar(*par).values()) for par in candidatos}
    if len(ubicaciones) == 1:
        return dict(zip(CAMPOS, ubicaciones.pop()))
    if len(ubicaciones) > 1:
        raise ValueError('El enlace contiene varios puntos. Copie las coordenadas del destino exacto.')
    raise ValueError('El enlace no contiene coordenadas de un marcador. Abra Maps, seleccione el punto y copie sus coordenadas. El centro del mapa no identifica la dirección.')


def enlace_mapa(ubicacion):
    from urllib.parse import urlencode
    return 'https://www.google.com/maps/search/?' + urlencode({
        'api': 1, 'query': f"{ubicacion['Latitude']:f},{ubicacion['Longitude']:f}"})


def enlace_desde_texto(texto):
    """Abre el enlace pegado sin confundir el centro del mapa con su marcador."""
    urls = re.findall(r'https?://[^\s<>"\u200e\u200f]+', texto.strip())
    if len(urls) == 1 and _url_permitida(urls[0]):
        return urls[0]
    if not urls and PAR.fullmatch(texto.strip()):
        return enlace_mapa(extraer_ubicacion(texto))
    raise ValueError('Pegue un solo enlace de ubicación de Google Maps o WhatsApp.')
