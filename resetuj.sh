#!/bin/sh
# Vrati baze na prazno. Grader je stateful i pretpostavlja praznu bazu, pa se
# drugi prolaz bez ovoga zavrsi na ~79% zbog podataka iz prvog.
#   sh resetuj.sh          Compose
#   sh resetuj.sh k8s      Kubernetes
set -e
cd "$(dirname "$0")"

if [ "$1" = "k8s" ]; then
    echo "Rusim manifest..."
    kubectl delete -f deploy/k8s.yaml --wait=true >/dev/null 2>&1 || true

    echo "Brisem podatke sa cvora..."
    context=$(kubectl config current-context)

    case "$context" in
        docker-desktop)
            docker exec desktop-control-plane \
                sh -c 'rm -rf /var/local/investment-fund/mysql/* /var/local/investment-fund/mongo/*'
            ;;
        minikube)
            minikube ssh -- sudo rm -rf /var/local/investment-fund/mysql/\* /var/local/investment-fund/mongo/\*
            ;;
        *)
            echo "Nepoznat kontekst $context - obrisi /var/local/investment-fund/* na cvoru rucno." >&2
            ;;
    esac

    echo "Podizem ponovo..."
    kubectl apply -f deploy/k8s.yaml >/dev/null
    kubectl wait --for=condition=available --timeout=300s \
        deployment/mysql deployment/mongo deployment/redis deployment/ganache >/dev/null
    kubectl wait --for=condition=complete --timeout=300s job/migration-job >/dev/null
    kubectl wait --for=condition=available --timeout=300s \
        deployment/authentication deployment/employee deployment/director >/dev/null

    kubectl get pods
    echo
    echo "Port-forward-ovi su pukli sa starim podovima - pusti ih ponovo ili pokreni-k8s.sh."
    exit 0
fi

echo "Rusim stack sa podacima..."
docker compose -f deploy/deployment.yaml down -v >/dev/null 2>&1 || true

echo "Podizem ponovo..."
AUTHENTICATION_PORT=${AUTHENTICATION_PORT:-5000} \
EMPLOYEE_PORT=${EMPLOYEE_PORT:-5001} \
DIRECTOR_PORT=${DIRECTOR_PORT:-5002} \
    docker compose -f deploy/deployment.yaml up -d >/dev/null

i=0
while [ $i -lt 90 ]; do
    curl -s -o /dev/null -m 3 -X POST "localhost:${DIRECTOR_PORT:-5002}/login" \
        -H 'Content-Type: application/json' -d '{}' && break
    i=$((i + 1))
    sleep 2
done

echo "Spremno."
