@echo off
REM Ceo test paket u kontejneru - masini treba samo Docker.
REM   testovi.cmd                        sve (174 testa)
REM   testovi.cmd -m "not integration"   samo oni bez servisa
REM   testovi.cmd -k report -v           pojedinacni
REM Trazi da deploy/development.yaml radi (baze, redis, ganache).
setlocal
cd /d "%~dp0"

docker build -q -f deploy/tests.dockerfile --tag tests . >nul
if errorlevel 1 exit /b 1

docker run --rm --add-host=host.docker.internal:host-gateway ^
  -e DATABASE_URL=host.docker.internal ^
  -e MONGO_HOST=host.docker.internal ^
  -e REDIS_HOST=host.docker.internal ^
  -e BLOCKCHAIN_URL=http://host.docker.internal:8545 ^
  tests %*
endlocal
