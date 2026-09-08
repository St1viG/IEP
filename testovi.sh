#!/bin/sh
# Ceo test paket u kontejneru - masini treba samo Docker.
#   sh testovi.sh                 sve (174 testa)
#   sh testovi.sh -m "not integration"   samo oni bez servisa
#   sh testovi.sh -k report -v    pojedinacni
# Trazi da deploy/development.yaml radi (baze, redis, ganache).
set -e
cd "$(dirname "$0")"

docker build -q -f deploy/tests.dockerfile --tag tests . >/dev/null

docker run --rm --add-host=host.docker.internal:host-gateway \
  -e DATABASE_URL=host.docker.internal \
  -e MONGO_HOST=host.docker.internal \
  -e REDIS_HOST=host.docker.internal \
  -e BLOCKCHAIN_URL=http://host.docker.internal:8545 \
  tests "$@"
