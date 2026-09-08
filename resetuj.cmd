@echo off
REM Vrati baze na prazno. Grader je stateful i pretpostavlja praznu bazu, pa se
REM drugi prolaz bez ovoga zavrsi na ~79% zbog podataka iz prvog.
REM   resetuj.cmd          Compose
REM   resetuj.cmd k8s      Kubernetes
setlocal
cd /d "%~dp0"

if "%1"=="k8s" goto kubernetes

echo Rusim stack sa podacima...
docker compose -f deploy/deployment.yaml down -v >nul 2>&1

if "%AUTHENTICATION_PORT%"=="" set AUTHENTICATION_PORT=5000
if "%EMPLOYEE_PORT%"=="" set EMPLOYEE_PORT=5001
if "%DIRECTOR_PORT%"=="" set DIRECTOR_PORT=5002

echo Podizem ponovo...
docker compose -f deploy/deployment.yaml up -d
if errorlevel 1 exit /b 1

for /l %%i in (1,1,90) do (
    curl -s -o NUL -m 3 -X POST "localhost:%DIRECTOR_PORT%/login" -H "Content-Type: application/json" -d "{}" >nul 2>&1
    if not errorlevel 1 goto spremno
    timeout /t 2 /nobreak >nul
)
:spremno
echo Spremno.
goto end

:kubernetes
echo Rusim manifest...
kubectl delete -f deploy/k8s.yaml --wait=true >nul 2>&1

echo Brisem podatke sa cvora...
docker exec desktop-control-plane sh -c "rm -rf /var/local/investment-fund/mysql/* /var/local/investment-fund/mongo/*"

echo Podizem ponovo...
kubectl apply -f deploy/k8s.yaml >nul
kubectl wait --for=condition=available --timeout=300s deployment/mysql deployment/mongo deployment/redis deployment/ganache >nul
kubectl wait --for=condition=complete --timeout=300s job/migration-job >nul
kubectl wait --for=condition=available --timeout=300s deployment/authentication deployment/employee deployment/director >nul
kubectl get pods
echo.
echo Port-forward-ovi su pukli sa starim podovima - pusti ih ponovo ili pokreni-k8s.cmd.

:end
endlocal
