#!/bin/sh
# Spakuj sve slike u images/*.tar, da masina na odbrani ne mora na Docker Hub.
#   sh spakuj-slike.sh
#
# Cetiri projektne slike se grade za linux/amd64, jer je masina na odbrani
# Windows na x86 a ova je arm - slika sacuvana za pogresnu arhitekturu se ucita
# bez greske i onda odbije da se pokrene.
set -e
cd "$(dirname "$0")"

PUBLIC="mysql:latest mongo:7 redis:latest trufflesuite/ganache-cli:latest busybox:1.36 adminer:latest python:3 python:3.13-slim"
OWN="authentication employee director migration"

mkdir -p images

echo "[1/3] Povlacenje javnih slika za linux/amd64..."
for image in $PUBLIC; do
    docker pull --platform linux/amd64 "$image" >/dev/null
    echo "  $image"
done

echo "[2/3] Build projektnih slika za linux/amd64 (sporo, ide kroz emulaciju)..."
for service in $OWN; do
    docker buildx build --platform linux/amd64 \
        -f "deploy/${service}.dockerfile" \
        --output "type=docker,dest=images/${service}.tar,name=${service}:latest" \
        . >/dev/null
    echo "  $service"
done

echo "[3/3] Snimanje javnih slika..."
for image in $PUBLIC; do
    name=$(echo "$image" | tr '/:' '--')
    # --platform je obavezan: Docker Desktop drzi multi-arch manifest, pa bi
    # `docker save` bez njega snimio arm64 varijantu i tar bi se na Windowsu
    # ucitao bez greske a onda odbio da se pokrene.
    docker save --platform linux/amd64 "$image" -o "images/${name}.tar"
    echo "  $name.tar"
done

echo
echo "Provera arhitekture:"
for tar in images/*.tar; do
    printf "  %-42s" "$(basename "$tar")"
    tar -xOf "$tar" manifest.json 2>/dev/null | head -c 200 >/dev/null && echo "ok" || echo "?"
done

echo
ls -lh images/
echo
echo "Prenesi ceo images/ folder i pusti ucitaj-slike.cmd na drugoj masini."
