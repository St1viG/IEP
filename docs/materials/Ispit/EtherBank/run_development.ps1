Start-Process docker -ArgumentList "compose","-f","development.yaml","up"
Read-Host -Prompt "Press enter to start applications when services are up"

./venv/Scripts/activate.ps1
$env:PORT = 5000
Start-Process python -ArgumentList "authentication.py"
$env:PORT = 5001
Start-Process python -ArgumentList "administrator.py"
$env:PORT = 5002
Start-Process python -ArgumentList "user.py"
