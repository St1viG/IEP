@echo off
REM Ubaci cetiri lokalno izgradjene slike u image store samog klastera.
REM k8s.yaml koristi imagePullPolicy: Never, pa "docker build" nije dovoljan -
REM klaster ima svoj store koji ne vidi slike Docker demona.
setlocal
cd /d "%~dp0.."

set IMAGES=authentication employee director migration

for /f "tokens=*" %%c in ('kubectl config current-context') do set CONTEXT=%%c
if not defined CONTEXT (
    echo GRESKA: kubectl nema aktivan kontekst. Da li je Kubernetes ukljucen?
    exit /b 1
)
echo cluster context: %CONTEXT%

for %%i in (%IMAGES%) do (
    docker image inspect %%i:latest >nul 2>&1
    if errorlevel 1 (
        echo GRESKA: nedostaje slika %%i:latest
        echo Pokreni: docker compose -f deploy/deployment.yaml build
        exit /b 1
    )
)

if "%CONTEXT%"=="minikube" goto minikube
if "%CONTEXT%"=="docker-desktop" goto dockerdesktop
if "%CONTEXT:~0,5%"=="kind-" goto kind
if "%CONTEXT:~0,4%"=="k3d-" goto k3d

echo GRESKA: nepoznat kontekst "%CONTEXT%".
echo Ubaci ove slike u image store klastera rucno: %IMAGES%
exit /b 1

:minikube
echo loading with minikube image load
for %%i in (%IMAGES%) do (
    minikube image load %%i:latest
    echo   %%i
)
goto done

:kind
set CLUSTER=%CONTEXT:~5%
echo loading with kind load docker-image, cluster %CLUSTER%
for %%i in (%IMAGES%) do (
    kind load docker-image %%i:latest --name %CLUSTER%
    echo   %%i
)
goto done

:k3d
set CLUSTER=%CONTEXT:~4%
echo loading with k3d image import, cluster %CLUSTER%
for %%i in (%IMAGES%) do (
    k3d image import %%i:latest --cluster %CLUSTER%
    echo   %%i
)
goto done

:dockerdesktop
REM Docker Desktop vrti Kubernetes na kind cvoru, koji ima svoj containerd
REM store i ne vidi slike Docker demona.
echo loading through desktop-control-plane containerd
for %%i in (%IMAGES%) do (
    docker save %%i:latest | docker exec -i desktop-control-plane ctr -n k8s.io images import -
    echo   %%i
)
goto done

:done
echo.
echo Gotovo. Sada: kubectl apply -f deploy/k8s.yaml
endlocal
