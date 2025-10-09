#!/bin/bash
set -e

echo "🚀 Deploying telegram-bot-client to Kubernetes..."

# Проверка что kubectl доступен
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Проверка что подключен к кластеру
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
fi

echo "✅ Connected to cluster: $(kubectl config current-context)"

# Проверка существования секрета
if ! kubectl get secret telegram-bot-secrets &> /dev/null; then
    echo ""
    echo "⚠️  Secret 'telegram-bot-secrets' not found!"
    echo ""
    echo "Please create it first:"
    echo ""
    echo "  kubectl create secret generic telegram-bot-secrets \\"
    echo "    --from-literal=api-id=\"YOUR_API_ID\" \\"
    echo "    --from-literal=api-hash=\"YOUR_API_HASH\" \\"
    echo "    --from-literal=phone-number=\"+1234567890\""
    echo ""
    read -p "Do you want to continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Применяем манифесты
echo ""
echo "📦 Applying Kubernetes manifests..."

if command -v kustomize &> /dev/null; then
    echo "Using kustomize..."
    kubectl apply -k .
else
    echo "Using kubectl apply..."
    kubectl apply -f pvc.yaml
    kubectl apply -f secret.yaml
    kubectl apply -f deployment.yaml
    kubectl apply -f service.yaml
fi

echo ""
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/telegram-bot-client || true

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Status:"
kubectl get pods -l app=telegram-bot-client
echo ""
echo "📝 View logs:"
echo "  kubectl logs -f deployment/telegram-bot-client"
echo ""
echo "🔍 Check health:"
echo "  kubectl port-forward service/telegram-bot-client 8080:80"
echo "  curl http://localhost:8080/health"

