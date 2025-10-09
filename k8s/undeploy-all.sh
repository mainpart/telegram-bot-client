#!/bin/bash

# Скрипт удаления всех ресурсов Telegram Bot Client из Kubernetes
set -e

NAMESPACE="duke"

echo "🗑️  Undeploying Telegram Bot Client from Kubernetes (namespace: $NAMESPACE)"
echo ""
read -p "⚠️  This will delete the deployment, PVC (session data), and secrets. Continue? [y/N] " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Cancelled."
    exit 1
fi

# Удалить deployment
echo ""
echo "📦 Deleting deployment..."
kubectl delete deployment telegram-bot-client -n $NAMESPACE --ignore-not-found=true
echo "✓ Deployment deleted"

# Удалить PVC (это удалит session файл!)
echo ""
read -p "⚠️  Delete PVC (this will remove session data)? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "💾 Deleting PVC..."
    kubectl delete pvc telegram-session-storage -n $NAMESPACE --ignore-not-found=true
    echo "✓ PVC deleted"
else
    echo "⏭️  Skipping PVC deletion"
fi

# Удалить secrets
echo ""
read -p "⚠️  Delete secrets? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "🔐 Deleting secrets..."
    kubectl delete secret telegram-credentials -n $NAMESPACE --ignore-not-found=true
    echo "✓ Secrets deleted"
else
    echo "⏭️  Skipping secrets deletion"
fi

echo ""
echo "✅ Undeployment complete!"
echo ""
echo "Remaining resources in namespace '$NAMESPACE':"
kubectl get all,pvc,secrets -n $NAMESPACE

