#!/bin/sh
# Ceo sistem u jednoj komandi: build + podizanje + provera.
#   sh pokreni.sh
# Portovi se mogu pomeriti (na macOS-u 5000 drzi AirPlay):
#   AUTHENTICATION_PORT=5100 EMPLOYEE_PORT=5101 DIRECTOR_PORT=5102 sh pokreni.sh
set -e
cd "$(dirname "$0")"

if ! docker info >/dev/null 2>&1; then
    echo "GRESKA: Docker daemon ne radi." >&2
    exit 1
fi

A=${AUTHENTICATION_PORT:-5000}
E=${EMPLOYEE_PORT:-5001}
D=${DIRECTOR_PORT:-5002}

echo "[1/3] Ciscenje starog stanja..."
docker compose -f deploy/deployment.yaml down -v >/dev/null 2>&1 || true

echo "[2/3] Podizanje servisa (prvi put i build, ~2-15 min)..."
AUTHENTICATION_PORT=$A EMPLOYEE_PORT=$E DIRECTOR_PORT=$D \
    docker compose -f deploy/deployment.yaml up -d --build

echo "[3/3] Cekanje da svi servisi prihvataju konekcije..."
i=0
while [ $i -lt 90 ]; do
    ok=1
    for p in $A $E $D; do
        curl -s -o /dev/null -m 3 -X POST "localhost:$p/login" \
            -H 'Content-Type: application/json' -d '{}' || ok=0
    done
    [ "$ok" = 1 ] && break
    i=$((i + 1))
    sleep 2
done

if [ "$ok" != 1 ]; then
    echo "GRESKA: servisi se nisu podigli. Pogledaj: docker compose -f deploy/deployment.yaml logs" >&2
    exit 1
fi

echo
echo "Sistem radi:"
echo "  authentication  http://localhost:$A"
echo "  employee        http://localhost:$E"
echo "  director        http://localhost:$D"
echo "  ganache         http://localhost:8545"
echo "  adminer         http://localhost:8080"
echo
echo "Ceo scenario:   AUTHENTICATION_URL=http://localhost:$A EMPLOYEE_URL=http://localhost:$E DIRECTOR_URL=http://localhost:$D python scenario.py"
echo "Jedna ruta:     sh deploy/proveri.sh director /report"
