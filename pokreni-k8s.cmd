@echo off
REM Kubernetes varijanta u jednoj komandi (Docker Desktop Kubernetes).
setlocal
cd /d "%~dp0"

echo [1/5] Build slika...
docker compose -f deploy/deployment.yaml build
if errorlevel 1 exit /b 1

echo [2/5] Ubacivanje slika u klaster...
call deploy\load-images.cmd
if errorlevel 1 exit /b 1

echo [3/5] Primena manifesta...
kubectl apply -f deploy/k8s.yaml
if errorlevel 1 exit /b 1

echo [4/5] Cekanje podova...
kubectl wait --for=condition=available --timeout=300s deployment/mysql deployment/mongo deployment/redis deployment/ganache
kubectl wait --for=condition=complete --timeout=300s job/migration-job
kubectl wait --for=condition=available --timeout=300s deployment/authentication deployment/employee deployment/director
kubectl get pods

echo [5/5] Port-forward...
start /b kubectl port-forward service/authentication-service 5000:5000
start /b kubectl port-forward service/employee-service 5001:5000
start /b kubectl port-forward service/director-service 5002:5000
start /b kubectl port-forward service/ganache-service 8545:8545
timeout /t 5 /nobreak >nul

echo.
echo Sistem radi na 5000 / 5001 / 5002, ganache na 8545.
echo Rusenje: kubectl delete -f deploy/k8s.yaml
endlocal
