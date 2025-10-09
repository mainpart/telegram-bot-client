#!/bin/bash

# Script to check Telegram Bot Client status in Kubernetes

NAMESPACE="duke"
POD_NAME=$(kubectl get pods -n $NAMESPACE -l app=telegram-bot-client -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

echo "=== Telegram Bot Client Status ==="
echo ""

if [ -z "$POD_NAME" ]; then
    echo "❌ Pod not found in namespace '$NAMESPACE'"
    exit 1
fi

echo "📦 Pod: $POD_NAME"
echo ""

# Get pod status
STATUS=$(kubectl get pod -n $NAMESPACE $POD_NAME -o jsonpath='{.status.phase}')
READY=$(kubectl get pod -n $NAMESPACE $POD_NAME -o jsonpath='{.status.containerStatuses[0].ready}')
INIT_STATUS=$(kubectl get pod -n $NAMESPACE $POD_NAME -o jsonpath='{.status.initContainerStatuses[0].state}')

echo "Status: $STATUS"
echo ""

# Check init container
echo "=== Init Container ==="
if echo "$INIT_STATUS" | grep -q "running"; then
    echo "⏳ Init container is running (waiting for interactive input)"
    echo ""
    echo "To connect and enter Telegram code:"
    echo "  kubectl attach -it -n $NAMESPACE $POD_NAME -c telegram-init"
elif echo "$INIT_STATUS" | grep -q "terminated"; then
    EXIT_CODE=$(kubectl get pod -n $NAMESPACE $POD_NAME -o jsonpath='{.status.initContainerStatuses[0].state.terminated.exitCode}')
    if [ "$EXIT_CODE" = "0" ]; then
        echo "✅ Init container completed successfully"
    else
        echo "❌ Init container failed with exit code: $EXIT_CODE"
        echo ""
        echo "Logs:"
        kubectl logs -n $NAMESPACE $POD_NAME -c telegram-init --tail=20
    fi
else
    echo "Status: $INIT_STATUS"
fi

echo ""

# Check main container
if [ "$READY" = "true" ]; then
    echo "=== Main Container ==="
    echo "✅ Main container is running"
    echo ""
    echo "Check session file:"
    kubectl exec -n $NAMESPACE $POD_NAME -- ls -lh /data/
    echo ""
    echo "Test command:"
    echo "  kubectl exec -n $NAMESPACE deployment/telegram-bot-client -- python telegram_bot_client.py --list-chats --limit 5"
elif [ "$STATUS" = "Running" ]; then
    echo "=== Main Container ==="
    echo "⏳ Waiting for init container to complete..."
else
    echo "Pod status: $STATUS"
fi

echo ""
echo "=== Recent Events ==="
kubectl get events -n $NAMESPACE --field-selector involvedObject.name=$POD_NAME --sort-by='.lastTimestamp' | tail -5

