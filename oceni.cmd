@echo off
REM Pusti zvanicni grader (iep_grader) na pokrenut sistem.
REM   oceni.cmd            compose, portovi 5000/5001/5002
REM   oceni.cmd k8s        kroz port-forward, sa duzim timeout-om
REM Trazi docs\ProjekatExample\iep_grader\ (nije u git-u, prenosi se zasebno).
setlocal
cd /d "%~dp0"

if "%GRADER_DIRECTORY%"=="" set GRADER_DIRECTORY=docs\ProjekatExample\iep_grader

if not exist "%GRADER_DIRECTORY%\grader.dockerfile" (
    echo GRESKA: nema grader-a u %GRADER_DIRECTORY%
    echo Prekopiraj docs\ProjekatExample\ ili postavi GRADER_DIRECTORY.
    exit /b 1
)

if "%AUTHENTICATION_PORT%"=="" set AUTHENTICATION_PORT=5000
if "%EMPLOYEE_PORT%"=="" set EMPLOYEE_PORT=5001
if "%DIRECTOR_PORT%"=="" set DIRECTOR_PORT=5002
if "%BLOCKCHAIN_PORT%"=="" set BLOCKCHAIN_PORT=8545

REM k8s DNS ume da napravi pauzu od tacno pet sekundi, koliko je i podrazumevani
REM timeout grader-a, pa zahtev istekne umesto da samo bude spor.
set TIMEOUT=5
set REPORT=grade_report.json
if "%1"=="k8s" set TIMEOUT=15
if "%1"=="k8s" set REPORT=grade_report_k8s.json

echo Build grader slike...
docker build -q -t grader -f "%GRADER_DIRECTORY%\grader.dockerfile" "%GRADER_DIRECTORY%" >nul
if errorlevel 1 exit /b 1

REM Zaostao izvestaj zbuni pytest oko rootdir-a i sve opcije postanu nepoznate.
if exist "%REPORT%" del "%REPORT%"

docker run --rm --add-host=host.docker.internal:host-gateway -v "%cd%:/out" grader ^
    -q --type all ^
    --authentication-url http://host.docker.internal:%AUTHENTICATION_PORT% ^
    --jwt-secret investment-fund-signing-key ^
    --roles-field roles --employee-role employee --director-role director ^
    --with-authentication ^
    --employee-url http://host.docker.internal:%EMPLOYEE_PORT% ^
    --director-url http://host.docker.internal:%DIRECTOR_PORT% ^
    --with-blockchain --provider-url http://host.docker.internal:%BLOCKCHAIN_PORT% ^
    --wait-for-services --service-timeout 180 ^
    --request-timeout %TIMEOUT% ^
    --grade-exit-zero ^
    --grade-report-file /out/%REPORT%

echo.
echo Izvestaj: %REPORT%
endlocal
