#!/bin/bash

# Script to connect to telegram-bot-client main container shell
# Usage: ./connect-shell.sh

NAMESPACE="duke"
DEPLOYMENT="telegram-bot-client"

echo "🔗 Connecting to $DEPLOYMENT shell..."
echo ""

kubectl exec -it -n $NAMESPACE deployment/$DEPLOYMENT -- /bin/sh

