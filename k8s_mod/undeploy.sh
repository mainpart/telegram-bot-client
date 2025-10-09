#!/bin/bash
# Удаление Telegram Bot Client из Kubernetes

set -e

echo "🗑️  Undeploying Telegram Bot Client"
echo ""
read -p "⚠️  Delete deployment, PVC (session data), and secrets? [y/N] " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

# Удалить deployment
echo ""
echo "📦 Deleting deployment..."
kubectl delete deployment telegram-bot-client --ignore-not-found=true
echo "✓ Deployment deleted"

# Удалить PVC
echo ""
echo "💾 Deleting PVC..."
kubectl delete pvc telegram-session-storage --ignore-not-found=true
echo "✓ PVC deleted"

# Удалить secrets
echo ""
echo "🔐 Deleting secrets..."
kubectl delete secret telegram-credentials --ignore-not-found=true
echo "✓ Secrets deleted"

echo ""
echo "✅ Undeployment complete!"
echo ""
