#!/bin/bash

# Script to connect to telegram-bot-client init container
# Usage: ./connect-init.sh

NAMESPACE="duke"
APP_LABEL="app=telegram-bot-client"

echo "🔍 Searching for telegram-bot-client pod..."

POD_NAME=$(kubectl get pod -n $NAMESPACE -l $APP_LABEL -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$POD_NAME" ]; then
    echo "❌ Pod not found in namespace '$NAMESPACE'"
    echo ""
    echo "Available pods:"
    kubectl get pods -n $NAMESPACE
    exit 1
fi

echo "📦 Found pod: $POD_NAME"
echo ""

# Check if init container is running
INIT_STATE=$(kubectl get pod -n $NAMESPACE $POD_NAME -o jsonpath='{.status.initContainerStatuses[0].state}' 2>/dev/null)

if echo "$INIT_STATE" | grep -q "running"; then
    echo "✅ Init container is running."
    echo ""
    echo "=== LOGS FROM START ==="
    kubectl logs -n $NAMESPACE $POD_NAME -c telegram-init 2>/dev/null || echo "(no logs yet)"
    echo "======================="
    echo ""
    echo "After connecting:"
    echo "  1. Enter the Telegram code when prompted"
    echo "  2. Enter 2FA password if required"
    echo "  3. Press Ctrl+D to disconnect"
    echo ""
    echo "⚠️  IMPORTANT: Look at logs above to see current prompt!"
    echo ""
    echo "Connecting in 5 seconds..."
    sleep 5
    kubectl attach -it -n $NAMESPACE $POD_NAME -c telegram-init
elif echo "$INIT_STATE" | grep -q "terminated"; then
    EXIT_CODE=$(kubectl get pod -n $NAMESPACE $POD_NAME -o jsonpath='{.status.initContainerStatuses[0].state.terminated.exitCode}')
    if [ "$EXIT_CODE" = "0" ]; then
        echo "✅ Init container already completed successfully!"
        echo ""
        echo "Main container should be running. Try:"
        echo "  kubectl exec -it -n $NAMESPACE deployment/telegram-bot-client -- /bin/sh"
    else
        echo "❌ Init container failed with exit code: $EXIT_CODE"
        echo ""
        echo "View logs:"
        echo "  kubectl logs -n $NAMESPACE $POD_NAME -c telegram-init"
    fi
else
    echo "⏳ Init container status: $INIT_STATE"
    echo ""
    echo "Waiting for init container to start..."
fi

