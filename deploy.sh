#!/bin/bash

# Build and load Docker image into kind cluster
echo "Building Docker image..."
docker build -t webapp:latest ./app

echo "Loading image into kind cluster..."
kind load docker-image webapp:latest

echo "Deploying MySQL..."
kubectl apply -f k8s/mysql-deployment.yaml

echo "Waiting for MySQL to be ready..."
kubectl wait --for=condition=ready pod -l app=mysql --timeout=180s

echo "Deploying Web Application..."
kubectl apply -f k8s/webapp-deployment.yaml

echo "Waiting for webapp to be ready..."
kubectl wait --for=condition=ready pod -l app=webapp --timeout=120s

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Access the application at: http://localhost:30080"
echo ""
echo "Check pod status with: kubectl get pods"
echo "Check services with: kubectl get svc"
echo "View logs: kubectl logs -f deployment/webapp"
