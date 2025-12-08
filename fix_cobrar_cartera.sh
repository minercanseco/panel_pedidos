#!/bin/bash
set -e

# Ruta absoluta del proyecto
PROYECTO="/Users/minercansecomanuel/PycharmProjects/panel_pedidos"

echo "== Navegando al proyecto =="
cd "$PROYECTO"

echo "== Eliminando submódulo herramientas/cobrar_cartera del índice =="
git rm --cached -f herramientas/cobrar_cartera || true

# 2. Limpiar .gitmodules si existe
if [ -f .gitmodules ]; then
  echo "== Limpiando .gitmodules =="
  # macOS usa sed diferente, por eso -i.bak
  sed -i.bak '/herramientas\/cobrar_cartera/,+2d' .gitmodules
  git add .gitmodules
fi

# 3. Quitar configuración de git del submódulo
echo "== Eliminando configuración del submódulo desde git config =="
git config --remove-section submodule.herramientas/cobrar_cartera 2>/dev/null || true

# 4. Borrar metadata del submódulo almacenada en .git/modules
if [ -d .git/modules/herramientas/cobrar_cartera ]; then
  echo "== Borrando .git/modules/herramientas/cobrar_cartera =="
  rm -rf .git/modules/herramientas/cobrar_cartera
fi

# 5. Agregar carpeta como elemento normal del repositorio
echo "== Agregando carpeta como archivos normales =="
git add herramientas/cobrar_cartera

echo "== Realizando commit =="
git commit -m "Eliminar submódulo y agregar carpeta cobrar_cartera como carpeta normal" || echo "== Nada que commitear =="

echo "== Proceso terminado. Verifica el estado con: git status =="