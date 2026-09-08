docker build -f .\authentication.dockerfile --tag authentication .
docker build -f .\administrator.dockerfile --tag administrator .
docker build -f .\user.dockerfile --tag user .

docker compose -f .\deployment.yaml up
