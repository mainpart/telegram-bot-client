#!/bin/bash

# Полный скрипт развертывания Telegram Bot Client в Kubernetes
set -e

NAMESPACE="duke"
echo "🚀 Deploying Telegram Bot Client to Kubernetes (namespace: $NAMESPACE)"

# Шаг 1: Создать namespace если не существует
echo ""
echo "📦 Step 1: Creating namespace..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
echo "✓ Namespace '$NAMESPACE' ready"

# Шаг 2: Создать секреты
echo ""
echo "🔐 Step 2: Creating secrets..."
./secret-create.sh
echo "✓ Secrets created"

# Шаг 3: Создать PVC
echo ""
echo "💾 Step 3: Creating PersistentVolumeClaim..."
kubectl apply -f pvc.yaml
echo "✓ PVC created"

# Подождать пока PVC будет Bound
echo "⏳ Waiting for PVC to be bound..."
kubectl wait --for=jsonpath='{.status.phase}'=Bound pvc/telegram-session-storage -n $NAMESPACE --timeout=60s
echo "✓ PVC is bound"

# Шаг 4: Развернуть приложение
echo ""
echo "🎯 Step 4: Deploying application..."
kubectl apply -f deployment.yaml
echo "✓ Deployment created"

# Шаг 5: Показать статус
echo ""
echo "📊 Deployment status:"
kubectl get all -n $NAMESPACE

echo ""
echo "⚠️  IMPORTANT: Init container is waiting for interactive authentication!"
echo ""
echo "To complete initialization, run:"
echo "  1. Get pod name: kubectl get pods -n $NAMESPACE"
echo "  2. Attach to init container: kubectl attach -it -n $NAMESPACE POD_NAME -c telegram-init"
echo "  3. Enter the Telegram code when prompted"
echo ""
echo "After successful authentication, the main container will start automatically."

