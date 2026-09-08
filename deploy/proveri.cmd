@echo off
REM Provera jedne rute na pokrenutom sistemu (bez curl-a, samo Docker).
REM   deploy\proveri.cmd director /report
REM   deploy\proveri.cmd employee /search name=Ferrari
setlocal
cd /d "%~dp0.."

if "%AUTHENTICATION_URL%"=="" set AUTHENTICATION_URL=http://host.docker.internal:5000
if "%EMPLOYEE_URL%"=="" set EMPLOYEE_URL=http://host.docker.internal:5001
if "%DIRECTOR_URL%"=="" set DIRECTOR_URL=http://host.docker.internal:5002

docker run --rm --add-host=host.docker.internal:host-gateway ^
  -e AUTHENTICATION_URL=%AUTHENTICATION_URL% ^
  -e EMPLOYEE_URL=%EMPLOYEE_URL% ^
  -e DIRECTOR_URL=%DIRECTOR_URL% ^
  -v "%cd%\deploy\proveri.py:/proveri.py" ^
  --entrypoint python director /proveri.py %*
endlocal
