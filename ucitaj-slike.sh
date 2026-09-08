#!/bin/sh
# Ucitaj sve slike iz images/*.tar. Za masinu bez pristupa Docker Hub-u.
#   sh ucitaj-slike.sh
set -e
cd "$(dirname "$0")"

if [ ! -d images ]; then
    echo "GRESKA: nema images/ foldera. Prenesi ga sa masine na kojoj je pravljen." >&2
    exit 1
fi

for tar in images/*.tar; do
    [ -e "$tar" ] || { echo "GRESKA: images/ je prazan." >&2; exit 1; }
    echo "ucitavam $tar"
    docker load -i "$tar"
done

# Ako je na masini samo jedna verzija Pythona, a dockerfile trazi drugu.
for want in "python:3" "python:3.13-slim"; do
    docker image inspect "$want" >/dev/null 2>&1 || {
        have=$(docker images --format '{{.Repository}}:{{.Tag}}' | grep '^python:' | head -1)
        [ -n "$have" ] && docker tag "$have" "$want" && echo "tag $have -> $want"
    }
done

echo
docker images
