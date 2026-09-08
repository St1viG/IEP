#!/bin/sh
# Put the four locally built images into the cluster's own image store.
#
# k8s.yaml pins them to imagePullPolicy: Never, so the node has to already hold
# them. Every local cluster keeps that store somewhere different, and none of
# them can see the Docker daemon's images, so "docker build" alone is never
# enough. Run this from the repository root, after building.

set -eu

IMAGES="authentication employee director migration"

context=$(kubectl config current-context)

echo "cluster context: ${context}"

for image in ${IMAGES}; do
    if ! docker image inspect "${image}:latest" >/dev/null 2>&1; then
        echo "missing image ${image}:latest, run: docker compose -f deploy/deployment.yaml build" >&2
        exit 1
    fi
done

case "${context}" in
    minikube)
        echo "loading with: minikube image load"
        for image in ${IMAGES}; do
            minikube image load "${image}:latest"
            echo "  ${image}"
        done
        ;;
    kind-*)
        echo "loading with: kind load docker-image"
        for image in ${IMAGES}; do
            kind load docker-image "${image}:latest" --name "${context#kind-}"
            echo "  ${image}"
        done
        ;;
    k3d-*)
        echo "loading with: k3d image import"
        for image in ${IMAGES}; do
            k3d image import "${image}:latest" --cluster "${context#k3d-}"
            echo "  ${image}"
        done
        ;;
    docker-desktop)
        # Docker Desktop runs Kubernetes on a kind node these days, and that node
        # has a containerd store of its own that the daemon's images never reach.
        # Quote "${image}", never $image:latest, or zsh reads :l as the lowercase
        # modifier and mangles the tag.
        echo "loading with: docker save | ctr images import (desktop-control-plane)"
        for image in ${IMAGES}; do
            docker save "${image}:latest" |
                docker exec -i desktop-control-plane ctr -n k8s.io images import -
            echo "  ${image}"
        done
        ;;
    *)
        echo "unrecognised context '${context}'." >&2
        echo "Load these four into the node's image store by hand: ${IMAGES}" >&2
        exit 1
        ;;
esac

echo
echo "done. Now: kubectl apply -f deploy/k8s.yaml"
