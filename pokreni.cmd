@echo off
REM Ceo sistem u jednoj komandi: build + podizanje + provera.
REM   pokreni.cmd
setlocal
cd /d "%~dp0"

docker info >nul 2>&1
if errorlevel 1 (
    echo GRESKA: Docker daemon ne radi.
    exit /b 1
)

if "%AUTHENTICATION_PORT%"=="" set AUTHENTICATION_PORT=5000
if "%EMPLOYEE_PORT%"=="" set EMPLOYEE_PORT=5001
if "%DIRECTOR_PORT%"=="" set DIRECTOR_PORT=5002

echo [1/3] Ciscenje starog stanja...
docker compose -f deploy/deployment.yaml down -v >nul 2>&1

echo [2/3] Podizanje servisa (prvi put i build, ~2-15 min)...
docker compose -f deploy/deployment.yaml up -d --build
if errorlevel 1 exit /b 1

echo [3/3] Cekanje da svi servisi prihvataju konekcije...
for /l %%i in (1,1,90) do (
    curl -s -o NUL -m 3 -X POST "localhost:%DIRECTOR_PORT%/login" -H "Content-Type: application/json" -d "{}" >nul 2>&1
    if not errorlevel 1 goto ready
    timeout /t 2 /nobreak >nul
)
echo GRESKA: servisi se nisu podigli. Pogledaj: docker compose -f deploy/deployment.yaml logs
exit /b 1

:ready
echo.
echo Sistem radi:
echo   authentication  http://localhost:%AUTHENTICATION_PORT%
echo   employee        http://localhost:%EMPLOYEE_PORT%
echo   director        http://localhost:%DIRECTOR_PORT%
echo   ganache         http://localhost:8545
echo   adminer         http://localhost:8080
echo.
echo Jedna ruta:  deploy\proveri.cmd director /report
endlocal
