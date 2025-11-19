# 2-Tier Application Demo - Pod Interconnection in Kubernetes

This project demonstrates **how pods interconnect with each other** in a Kubernetes cluster using a simple 2-tier architecture:
- **Database Layer (MySQL)**: Stores key-value pairs
- **Frontend Layer (Flask Web UI)**: Accepts user input and communicates with the database

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                    │
│                                                          │
│  ┌─────────────────┐         ┌──────────────────┐     │
│  │   Web App Pod   │────────>│   MySQL Pod      │     │
│  │   (Frontend)    │         │   (Database)     │     │
│  │                 │         │                  │     │
│  │  Flask + HTML   │   DNS   │  MySQL 8.0       │     │
│  │  Port: 5000     │ Lookup  │  Port: 3306      │     │
│  └─────────────────┘         └──────────────────┘     │
│         │                            │                 │
│         │                            │                 │
│  ┌──────▼──────────┐         ┌──────▼─────────┐      │
│  │ webapp-service  │         │ mysql-service   │      │
│  │  (NodePort)     │         │  (ClusterIP)    │      │
│  │  Port: 30080    │         │  Port: 3306     │      │
│  └─────────────────┘         └─────────────────┘      │
│                                                          │
└─────────────────────────────────────────────────────────┘
         │
         │ External Access
         ▼
    User Browser
 http://localhost:30080
```

## 🔄 Pod Interconnection Explained

1. **Service Discovery**: The webapp pods discover the MySQL pod using Kubernetes DNS
   - MySQL service name: `mysql-service`
   - Resolves to: `mysql-service.default.svc.cluster.local`

2. **Network Communication**: 
   - Webapp pods communicate with MySQL via the ClusterIP service
   - Connection string: `mysql-service:3306`
   - All traffic stays within the cluster network

3. **Configuration Management**:
   - Database credentials stored in Kubernetes Secrets
   - Connection details in ConfigMaps
   - Environment variables injected into pods

## 📁 Project Structure

```
2-tier-app/
├── app/
│   ├── app.py                 # Flask application
│   ├── templates/
│   │   └── index.html        # Web UI
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile           # Container image definition
├── k8s/
│   ├── mysql-deployment.yaml    # MySQL deployment & service
│   └── webapp-deployment.yaml   # Web app deployment & service
├── deploy.sh                    # Deployment script
├── cleanup.sh                   # Cleanup script
└── README.md                    # This file
```

## 🚀 Prerequisites

- Docker
- kind (Kubernetes in Docker)
- kubectl

### Install kind (if not already installed)

```bash
# On Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Verify installation
kind version
```

## 🎯 Quick Start

### 1. Create a kind cluster

```bash
kind create cluster --name demo-cluster
```

### 2. Deploy the application

```bash
chmod +x deploy.sh
./deploy.sh
```

This script will:
- Build the Docker image for the web application
- Load the image into the kind cluster
- Deploy MySQL with persistent storage
- Deploy the web application (2 replicas)
- Wait for all pods to be ready

### 3. Access the application

Open your browser and navigate to:
```
http://localhost:30080
```

## 🧪 Testing Pod Interconnection

### 1. View all pods and services

```bash
kubectl get pods,svc
```

Expected output:
```
NAME                         READY   STATUS    RESTARTS   AGE
pod/mysql-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
pod/webapp-xxxxxxxxx-xxxxx   1/1     Running   0          1m
pod/webapp-xxxxxxxxx-xxxxx   1/1     Running   0          1m

NAME                     TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/kubernetes       ClusterIP   10.96.0.1       <none>        443/TCP        5m
service/mysql-service    ClusterIP   10.96.xxx.xxx   <none>        3306/TCP       2m
service/webapp-service   NodePort    10.96.xxx.xxx   <none>        80:30080/TCP   1m
```

### 2. Test database connectivity from webapp pod

```bash
# Get webapp pod name
WEBAPP_POD=$(kubectl get pod -l app=webapp -o jsonpath="{.items[0].metadata.name}")

# Test DNS resolution
kubectl exec -it $WEBAPP_POD -- nslookup mysql-service

# Test MySQL connection
kubectl exec -it $WEBAPP_POD -- python -c "
import mysql.connector
conn = mysql.connector.connect(
    host='mysql-service',
    port=3306,
    user='dbuser',
    password='dbpassword',
    database='keyvaluedb'
)
print('✅ Connection successful!')
conn.close()
"
```

### 3. View application logs

```bash
# View webapp logs
kubectl logs -f deployment/webapp

# View MySQL logs
kubectl logs -f deployment/mysql
```

### 4. Use the application

1. Open http://localhost:30080 in your browser
2. The status should show "✅ Connected to Database"
3. Enter a key-value pair (e.g., key: "username", value: "john")
4. Click "Store" - the data is sent to webapp pod, which stores it in MySQL pod
5. Click "Load All" to see all stored data
6. Try retrieving or deleting entries

### 5. Scale the webapp and observe load distribution

```bash
# Scale to 3 replicas
kubectl scale deployment webapp --replicas=3

# Watch the pods
kubectl get pods -l app=webapp -w

# All pods connect to the same MySQL instance
```

## 🔍 Deep Dive: How It Works

### Service Discovery

The webapp connects to MySQL using the service name `mysql-service`:

```python
DB_CONFIG = {
    'host': 'mysql-service',  # Kubernetes DNS name
    'port': 3306,
    'user': 'dbuser',
    'password': 'dbpassword',
    'database': 'keyvaluedb'
}
```

Kubernetes DNS automatically resolves `mysql-service` to the ClusterIP of the MySQL service.

### Network Policies (Implicit)

- **mysql-service**: ClusterIP (only accessible within the cluster)
- **webapp-service**: NodePort (accessible from outside via port 30080)
- All pods in the same namespace can communicate by default

### Data Flow

1. User enters data in browser → HTTP request to NodePort 30080
2. NodePort routes to webapp-service (ClusterIP)
3. Service load balances to one of the webapp pods
4. Webapp pod connects to mysql-service using DNS
5. mysql-service routes to MySQL pod
6. MySQL pod processes query and returns data
7. Response travels back through the chain to user

## 🛠️ Troubleshooting

### Pods not starting

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Can't access the application

```bash
# Check if services are running
kubectl get svc

# On some systems, you might need port forwarding instead
kubectl port-forward service/webapp-service 8080:80
# Then access: http://localhost:8080
```

### Database connection issues

```bash
# Check MySQL pod is ready
kubectl get pod -l app=mysql

# Check MySQL logs
kubectl logs -l app=mysql

# Verify secrets are created
kubectl get secret mysql-secret
```

### Check connectivity between pods

```bash
# Enter webapp pod
kubectl exec -it deployment/webapp -- /bin/bash

# Inside pod, test connection
apt-get update && apt-get install -y mysql-client
mysql -h mysql-service -u dbuser -pdbpassword keyvaluedb
```

## 🧹 Cleanup

To remove all resources:

```bash
chmod +x cleanup.sh
./cleanup.sh
```

Or manually:

```bash
kubectl delete -f k8s/webapp-deployment.yaml
kubectl delete -f k8s/mysql-deployment.yaml
```

To delete the kind cluster:

```bash
kind delete cluster --name demo-cluster
```

## 📚 Key Concepts Demonstrated

1. **Pod-to-Pod Communication**: How pods communicate using Kubernetes services
2. **Service Discovery**: Using DNS for service discovery within the cluster
3. **ClusterIP vs NodePort**: Different service types for internal and external access
4. **ConfigMaps & Secrets**: Managing configuration and sensitive data
5. **Persistent Storage**: Using PVCs for database data persistence
6. **Health Checks**: Liveness and readiness probes for reliability
7. **Resource Limits**: CPU and memory management for pods
8. **Multi-tier Architecture**: Separating frontend and backend concerns

## 🎓 Learning Exercises

Try these to deepen your understanding:

1. **Scale the application**: Increase webapp replicas and observe load distribution
2. **Add network policies**: Restrict which pods can talk to MySQL
3. **Use Ingress**: Replace NodePort with an Ingress controller
4. **Add monitoring**: Deploy Prometheus to monitor pod metrics
5. **Implement caching**: Add Redis as a middle tier
6. **Use StatefulSet**: Convert MySQL deployment to StatefulSet
7. **Add authentication**: Implement user login with session storage

## 📖 Additional Resources

- [Kubernetes Networking](https://kubernetes.io/docs/concepts/services-networking/)
- [Service Discovery](https://kubernetes.io/docs/concepts/services-networking/service/)
- [DNS for Services](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
- [kind Documentation](https://kind.sigs.k8s.io/)

## 📄 License

This is a demo project for educational purposes.
