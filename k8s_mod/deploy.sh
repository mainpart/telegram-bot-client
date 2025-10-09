#!/bin/bash
# Развертывание Telegram Bot Client в Kubernetes

set -e

echo "🚀 Deploying Telegram Bot Client"
echo ""

# Проверка обязательных переменных
REQUIRED_VARS="TELEGRAM_PHONE_NUMBER TELEGRAM_API_ID TELEGRAM_API_HASH"
for var in $REQUIRED_VARS; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var is not set"
        echo ""
        echo "Please export required variables:"
        echo "  export TELEGRAM_PHONE_NUMBER=\"+1234567890\""
        echo "  export TELEGRAM_API_ID=\"12345678\""
        echo "  export TELEGRAM_API_HASH=\"abcdef...\""
        exit 1
    fi
done

echo "✓ Credentials loaded"
echo ""

# Создать секреты
echo "🔐 Creating secrets..."
envsubst < secret.yaml | kubectl apply -f -
echo "✓ Secrets created"
echo ""

# Создать PVC
echo "💾 Creating PersistentVolumeClaim..."
kubectl apply -f pvc.yaml
echo "✓ PVC created"
echo ""

# Дождаться пока PVC будет Bound
echo "⏳ Waiting for PVC to be bound..."
kubectl wait --for=jsonpath='{.status.phase}'=Bound pvc/telegram-session-storage --timeout=60s
echo "✓ PVC is bound"
echo ""

# Развернуть приложение
echo "🎯 Deploying application..."
kubectl apply -f deployment.yaml
echo "✓ Deployment created"
echo ""

# Показать статус
echo "📊 Status:"
kubectl get all,pvc,secrets | grep telegram
echo ""

echo "⚠️  IMPORTANT: Init container needs authentication!"
echo ""
echo "To initialize, run:"
echo "  kubectl attach -it \$(kubectl get pod -l app=telegram-bot-client -o jsonpath='{.items[0].metadata.name}') -c telegram-init"
echo ""
