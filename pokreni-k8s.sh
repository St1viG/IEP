#!/bin/sh
# Kubernetes varijanta u jednoj komandi.
#   sh pokreni-k8s.sh
set -e
cd "$(dirname "$0")"

echo "[1/5] Build slika..."
docker compose -f deploy/deployment.yaml build

echo "[2/5] Ubacivanje slika u klaster..."
sh deploy/load-images.sh

echo "[3/5] Primena manifesta..."
kubectl apply -f deploy/k8s.yaml

echo "[4/5] Cekanje podova..."
kubectl wait --for=condition=available --timeout=300s \
    deployment/mysql deployment/mongo deployment/redis deployment/ganache
kubectl wait --for=condition=complete --timeout=300s job/migration-job
kubectl wait --for=condition=available --timeout=300s \
    deployment/authentication deployment/employee deployment/director

kubectl get pods

echo "[5/5] Port-forward (NodePort 30000-30002 nije objavljen na hostu u kind rezimu)..."
pkill -f "kubectl port-forward" 2>/dev/null || true
kubectl port-forward service/authentication-service 5000:5000 >/dev/null 2>&1 &
kubectl port-forward service/employee-service       5001:5000 >/dev/null 2>&1 &
kubectl port-forward service/director-service       5002:5000 >/dev/null 2>&1 &
kubectl port-forward service/ganache-service        8545:8545 >/dev/null 2>&1 &
sleep 5

echo
echo "Sistem radi na 5000 / 5001 / 5002, ganache na 8545."
echo "Zaustavljanje port-forward-ova: pkill -f 'kubectl port-forward'"
echo "Rusenje:                        kubectl delete -f deploy/k8s.yaml"
