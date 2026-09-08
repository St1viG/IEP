#!/bin/sh
# Provera jedne rute na pokrenutom sistemu (bez curl-a, samo Docker).
#   sh deploy/proveri.sh director /report
#   sh deploy/proveri.sh employee /search post '{"name": "Ferrari"}'
set -e
cd "$(dirname "$0")/.."

docker run --rm --add-host=host.docker.internal:host-gateway \
  -e AUTHENTICATION_URL="${AUTHENTICATION_URL:-http://host.docker.internal:5000}" \
  -e EMPLOYEE_URL="${EMPLOYEE_URL:-http://host.docker.internal:5001}" \
  -e DIRECTOR_URL="${DIRECTOR_URL:-http://host.docker.internal:5002}" \
  -v "$(pwd)/deploy/proveri.py:/proveri.py" \
  --entrypoint python director /proveri.py "$@"
