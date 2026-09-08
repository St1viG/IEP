@echo off
REM Ucitaj sve slike iz images\*.tar. Za masinu bez pristupa Docker Hub-u.
setlocal
cd /d "%~dp0"

if not exist images (
    echo GRESKA: nema images\ foldera. Prenesi ga sa masine na kojoj je pravljen.
    exit /b 1
)

set FOUND=0
for %%t in (images\*.tar) do (
    set FOUND=1
    echo ucitavam %%t
    docker load -i "%%t"
)

if exist images\*.tar goto tagcheck
echo GRESKA: images\ je prazan.
exit /b 1

:tagcheck
REM Ako je na masini samo jedna verzija Pythona, a dockerfile trazi drugu.
docker image inspect python:3 >nul 2>&1
if errorlevel 1 (
    for /f "tokens=*" %%p in ('docker images --format "{{.Repository}}:{{.Tag}}" ^| findstr /b "python:"') do (
        docker tag %%p python:3
        echo tag %%p -^> python:3
        goto tagged
    )
)
:tagged

echo.
docker images
endlocal
