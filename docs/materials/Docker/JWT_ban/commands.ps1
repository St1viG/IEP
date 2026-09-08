docker build -f user.dockerfile --tag user .
docker build -f admin.dockerfile --tag admin .

docker swarm init

docker stack deploy -c deployment.yaml jwt
