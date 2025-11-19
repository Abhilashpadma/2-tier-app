#!/bin/bash

echo "Cleaning up resources..."

kubectl delete -f k8s/webapp-deployment.yaml
kubectl delete -f k8s/mysql-deployment.yaml

echo "✅ Cleanup complete!"
