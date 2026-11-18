#!/usr/bin/env bash
# Espera a que /api/health de una app responda la versión (SHA) esperada.
# Uso: scripts/esperar-version.sh <url-base> <sha> [intentos]   (cada intento espera 10 s; por defecto 30 = 5 min)
set -u

url="${1:?Falta la URL base}"
esperada="${2:?Falta la versión esperada}"
intentos="${3:-30}"

for intento in $(seq 1 "$intentos"); do
  version="$(curl -fsS --max-time 10 "${url}/api/health" 2>/dev/null \
    | python3 -c 'import json,sys; print(json.load(sys.stdin).get("version",""))' 2>/dev/null || true)"
  echo "Intento ${intento}/${intentos}: versión desplegada = '${version}'"
  if [ "$version" = "$esperada" ]; then
    echo "La versión ${esperada} ya está desplegada."
    exit 0
  fi
  sleep 10
done

echo "::error::${url} no respondió la versión ${esperada} a tiempo"
exit 1
