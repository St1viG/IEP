#!/bin/sh
# Napravi arhivu za predaju, u tocompress/, ne dirajuci ovaj repozitorijum.
#   sh spakuj-predaju.sh              sa docs/materials
#   sh spakuj-predaju.sh bez-docs     bez njih, ako je limit tesan
#
# Iz kopije se izbacuje .git (polovina tezine) i wheels/ (druga polovina), pa se
# dockerfile-ovi u kopiji vracaju na obican `pip install`, da se predata verzija
# gradi iz PyPI-ja kao svaka druga.
set -e
cd "$(dirname "$0")"

TARGET=tocompress
NAME=IEP
LIMIT_MB=25

rm -rf "$TARGET"
mkdir -p "$TARGET"

echo "[1/4] Kloniram trenutno stanje..."
git clone -q . "$TARGET/$NAME"

echo "[2/4] Izbacujem sto ne ide u predaju..."
rm -rf "$TARGET/$NAME/.git"
rm -rf "$TARGET/$NAME/wheels"
find "$TARGET/$NAME" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$TARGET/$NAME" -name "*.pyc" -delete 2>/dev/null || true

if [ "$1" = "bez-docs" ]; then
    rm -rf "$TARGET/$NAME/docs/materials"
    echo "  bez docs/materials"
fi

echo "[3/4] Vracam dockerfile-ove na instalaciju sa PyPI-ja..."
for file in "$TARGET/$NAME"/deploy/*.dockerfile; do
    case "$file" in *tests.dockerfile) continue ;; esac

    python3 - "$file" <<'PYEOF'
import sys, pathlib

path = pathlib.Path(sys.argv[1])
text = path.read_text()

# wheels/ is not in the archive, so the COPY would fail. PIP_ARGS defaults to
# empty, so what is left installs from PyPI.
path.write_text(text.replace("COPY wheels /wheels\n", "", 1))
PYEOF
done
grep -h "pip install" "$TARGET/$NAME"/deploy/employee.dockerfile | sed 's/^/  /'

echo "[4/4] Pakujem..."
( cd "$TARGET" && zip -qr "$NAME.zip" "$NAME" )

size_kb=$(du -k "$TARGET/$NAME.zip" | cut -f1)
size_mb=$((size_kb / 1024))

echo
echo "  $TARGET/$NAME.zip  ${size_mb} MB  (limit ${LIMIT_MB} MB)"

if [ "$size_mb" -ge "$LIMIT_MB" ]; then
    echo "  PREKO LIMITA - probaj: sh spakuj-predaju.sh bez-docs" >&2
    exit 1
fi

echo "  OK"
