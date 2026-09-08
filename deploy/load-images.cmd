@echo off
REM Ubaci cetiri lokalno izgradjene slike u image store samog klastera.
REM k8s.yaml koristi imagePullPolicy: Never, pa "docker build" nije dovoljan -
REM klaster ima svoj store koji ne vidi slike Docker demona.
setlocal enabledelayedexpansion
cd /d "%~dp0.."

for /f "tokens=*" %%c in ('kubectl config current-context') do set CONTEXT=%%c
echo cluster context: %CONTEXT%

for %%i in (authentication employee director migration) do (
    docker image inspect %%i:latest >nul 2>&1
    if errorlevel 1 (
        echo Nedostaje slika %%i:latest - pokreni: docker compose -f deploy/deployment.yaml build
        exit /b 1
    )
)

if "%CONTEXT%"=="minikube" (
    echo loading with: minikube image load
    for %%i in (authentication employee director migration) do (
        minikube image load %%i:latest && echo   %%i
    )
    goto done
)

if "%CONTEXT%"=="docker-desktop" (
    echo loading with: docker save ^| ctr images import (desktop-control-plane)
    for %%i in (authentication employee director migration) do (
        docker save %%i:latest | docker exec -i desktop-control-plane ctr -n k8s.io images import -
        echo   %%i
    )
    goto done
)

echo Nepoznat kontekst "%CONTEXT%". Ubaci rucno: authentication employee director migration
exit /b 1

:done
echo.
echo Gotovo. Sada: kubectl apply -f deploy/k8s.yaml
endlocal
