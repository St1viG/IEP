#!/bin/sh
# Pusti zvanicni grader (iep_grader) na pokrenut sistem.
#   sh oceni.sh                      compose, portovi 5000/5001/5002
#   sh oceni.sh k8s                  kroz port-forward, sa duzim timeout-om
#   AUTHENTICATION_PORT=5100 EMPLOYEE_PORT=5101 DIRECTOR_PORT=5102 sh oceni.sh
#
# Trazi docs/ProjekatExample/iep_grader/ (nije u git-u, prenosi se zasebno).
set -e
cd "$(dirname "$0")"

GRADER_DIRECTORY=${GRADER_DIRECTORY:-docs/ProjekatExample/iep_grader}

if [ ! -f "$GRADER_DIRECTORY/grader.dockerfile" ]; then
    echo "GRESKA: nema grader-a u $GRADER_DIRECTORY" >&2
    echo "Prekopiraj docs/ProjekatExample/ ili postavi GRADER_DIRECTORY." >&2
    exit 1
fi

A=${AUTHENTICATION_PORT:-5000}
E=${EMPLOYEE_PORT:-5001}
D=${DIRECTOR_PORT:-5002}
B=${BLOCKCHAIN_PORT:-8545}

# k8s DNS ume da napravi pauzu od tacno pet sekundi, koliko je i podrazumevani
# timeout grader-a, pa zahtev istekne umesto da samo bude spor.
TIMEOUT=5
REPORT=grade_report.json

if [ "$1" = "k8s" ]; then
    TIMEOUT=15
    REPORT=grade_report_k8s.json
fi

echo "Build grader slike..."
docker build -q -t grader -f "$GRADER_DIRECTORY/grader.dockerfile" "$GRADER_DIRECTORY" >/dev/null

# Zaostao izvestaj zbuni pytest oko rootdir-a i sve opcije postanu nepoznate.
rm -f "$REPORT"

docker run --rm --add-host=host.docker.internal:host-gateway -v "$(pwd):/out" grader \
    -q --type all \
    --authentication-url "http://host.docker.internal:$A" \
    --jwt-secret investment-fund-signing-key \
    --roles-field roles --employee-role employee --director-role director \
    --with-authentication \
    --employee-url "http://host.docker.internal:$E" \
    --director-url "http://host.docker.internal:$D" \
    --with-blockchain --provider-url "http://host.docker.internal:$B" \
    --wait-for-services --service-timeout 180 \
    --request-timeout "$TIMEOUT" \
    --grade-exit-zero \
    --grade-report-file "/out/$REPORT"

echo
echo "Izvestaj: $REPORT"
