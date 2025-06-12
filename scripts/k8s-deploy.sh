#!/bin/bash
# Kubernetes deployment script for Job URL Analyzer MCP Server

set -e

NAMESPACE="job-analyzer"
CHART_VERSION="0.1.0"

echo "☸️  Deploying Job URL Analyzer to Kubernetes..."

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is required but not installed."
    echo "Please install kubectl from https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Check if cluster is accessible
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster."
    echo "Please configure kubectl to connect to your cluster."
    exit 1
fi

# Create namespace if it doesn't exist
echo "📁 Creating namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Apply secrets (you should customize this)
echo "🔐 Applying secrets..."
echo "⚠️  Please customize kubernetes/secrets.yaml with your actual secrets before running this script."
read -p "Have you customized the secrets? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please edit kubernetes/secrets.yaml and run this script again."
    exit 1
fi

# Apply Kubernetes manifests
echo "📦 Applying Kubernetes manifests..."
kubectl apply -f kubernetes/ -n $NAMESPACE

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/job-analyzer -n $NAMESPACE

# Get service information
echo "📊 Getting service information..."
kubectl get all -n $NAMESPACE

# Get ingress information
echo "🌐 Getting ingress information..."
kubectl get ingress -n $NAMESPACE

echo "✅ Deployment complete!"
echo ""
echo "Useful commands:"
echo "- Check pods: kubectl get pods -n $NAMESPACE"
echo "- View logs: kubectl logs -f deployment/job-analyzer -n $NAMESPACE"
echo "- Port forward: kubectl port-forward service/job-analyzer-service 8000:80 -n $NAMESPACE"
echo "- Delete deployment: kubectl delete namespace $NAMESPACE"
echo ""
echo "If using ingress, make sure to:"
echo "1. Configure DNS to point to your ingress controller"
echo "2. Set up SSL certificates (cert-manager recommended)"
echo "3. Update CORS_ORIGINS in the ConfigMap"