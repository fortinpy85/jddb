# Kubernetes Deployment

Kubernetes manifests and Helm charts for orchestrated JDDB deployment.

## Quick Start

```bash
# Install with Helm
helm install jddb ./helm-chart

# Or apply manifests directly
kubectl apply -f k8s/
```

## Architecture

### Components
- **Deployment**: Backend API (3 replicas)
- **Deployment**: Frontend (2 replicas)
- **StatefulSet**: PostgreSQL with persistent volumes
- **Service**: Load balancer for external access
- **Ingress**: HTTPS with cert-manager
- **ConfigMap**: Application configuration
- **Secret**: Sensitive credentials

### Resource Requirements

```yaml
backend:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 4Gi

frontend:
  requests:
    cpu: 200m
    memory: 512Mi
  limits:
    cpu: 1000m
    memory: 2Gi
```

## Helm Chart

### Installation
```bash
helm repo add jddb https://charts.jddb.example.com
helm install jddb jddb/jddb --values values.yaml
```

### Configuration
- `values.yaml` - Default configuration
- `values.prod.yaml` - Production overrides
- `values.dev.yaml` - Development overrides

## High Availability

### Database
- PostgreSQL with read replicas
- Automated backups to S3/Azure Blob
- Point-in-time recovery

### Application
- Horizontal Pod Autoscaler (HPA)
- Pod Disruption Budget (PDB)
- Multi-zone deployment

### Monitoring
- Prometheus operator
- Grafana dashboards
- Alert rules

## Scaling

```bash
# Manual scaling
kubectl scale deployment jddb-backend --replicas=5

# Autoscaling
kubectl autoscale deployment jddb-backend --min=3 --max=10 --cpu-percent=70
```

## Troubleshooting

```bash
# Check pod status
kubectl get pods -l app=jddb

# View logs
kubectl logs -f deployment/jddb-backend

# Describe issues
kubectl describe pod <pod-name>

# Port forward for debugging
kubectl port-forward service/jddb-backend 8000:8000
```

---

*Last Updated: September 30, 2025*
