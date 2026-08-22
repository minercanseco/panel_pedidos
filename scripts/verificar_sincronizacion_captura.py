"""Verifica que la captura embebida coincida con el proyecto canonico."""

from pathlib import Path
import sys


PANEL = Path(__file__).resolve().parents[1]
CAPTURA_PANEL = PANEL / 'herramientas' / 'capturar_documento'
CAPTURA_CANONICA = PANEL.parent / 'capturar_documentos_cayal' / 'capturar_documento'


def normalizar_imports(contenido):
    return contenido.replace(
        'from herramientas.capturar_documento',
        'from capturar_documento',
    ).replace(
        'import herramientas.capturar_documento',
        'import capturar_documento',
    )


def archivos_python(raiz):
    archivos = {}
    for archivo in raiz.rglob('*.py'):
        relativo = archivo.relative_to(raiz)
        if '__pycache__' in relativo.parts:
            continue
        # Existe una copia anidada accidental dentro del panel. No forma
        # parte del paquete importado y no debe considerarse como fuente.
        if relativo.parts and relativo.parts[0] == 'capturar_documento':
            continue
        archivos[relativo] = archivo
    return archivos


def main():
    if not CAPTURA_CANONICA.exists():
        print(f'No existe el proyecto canonico: {CAPTURA_CANONICA}')
        return 2

    canonicos = archivos_python(CAPTURA_CANONICA)
    embebidos = archivos_python(CAPTURA_PANEL)
    diferencias = []

    for relativo in sorted(canonicos.keys() | embebidos.keys()):
        if relativo not in canonicos:
            diferencias.append(f'Solo panel: {relativo}')
            continue
        if relativo not in embebidos:
            diferencias.append(f'Solo canonico: {relativo}')
            continue

        canonico = canonicos[relativo].read_text(encoding='utf-8')
        embebido = embebidos[relativo].read_text(encoding='utf-8')
        if canonico != normalizar_imports(embebido):
            diferencias.append(f'Contenido diferente: {relativo}')

    if diferencias:
        print('La captura del panel no esta sincronizada:')
        for diferencia in diferencias:
            print(f'  - {diferencia}')
        return 1

    print('La captura del panel coincide con el proyecto canonico.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
