#!/usr/bin/env bash
set -euo pipefail

# build all images using minikube's docker daemon
# must run "eval $(minikube docker-env)" before executing this script

for svc in loan-service credit-service property-service decision-service insurance-service agreement-service notification-service; do
  echo "Building image $svc..."
  docker build -t "$svc:latest" -f "services/$svc/Dockerfile" .
done

# apply namespace and infrastructure
kubectl apply -f namespace.yaml
kubectl apply -f rabbitmq-deployment.yaml
kubectl apply -f redis-deployment.yaml

# apply microservices + workers
kubectl apply -f services-deployments.yaml

echo "all resources applied"

echo "use 'kubectl -n loan-app get pods,svc' to inspect,"
echo "and port-forward services individually (eg: kubectl -n loan-app port-forward svc/loan-service 8001:8000)"