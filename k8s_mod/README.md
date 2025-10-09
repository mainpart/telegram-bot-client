# Telegram Bot Client - Kubernetes Deployment

Конфигурация для развертывания в Kubernetes.

## 🚀 Установка

```bash
# Создать namespace
kubectl create namespace duke
kubectl config set-context --current --namespace=duke

# Получить API credentials: https://my.telegram.org/apps
export TELEGRAM_PHONE_NUMBER="+1234567890"
export TELEGRAM_API_ID="12345678"
export TELEGRAM_API_HASH="abcdef1234567890abcdef1234567890"
./deploy.sh
```

Затем подключитесь для ввода кода из Telegram:

```bash
kubectl attach -it $(kubectl get pod -l app=telegram-bot-client -o jsonpath='{.items[0].metadata.name}') -c telegram-init
```

После успешной инициализации бот автоматически запустится в режиме `--listen-all` (слушает все чаты).

## 📝 Логи

```bash
kubectl logs deployment/telegram-bot-client -c telegram-init
kubectl logs -f deployment/telegram-bot-client -c telegram-bot
kubectl logs deployment/telegram-bot-client -c telegram-bot --tail=50
```

## 🔧 Команды

```bash
kubectl exec deployment/telegram-bot-client -- python telegram_bot_client.py --list-chats --limit 20
kubectl exec deployment/telegram-bot-client -- python telegram_bot_client.py --chat @username --limit 10
kubectl exec deployment/telegram-bot-client -- python telegram_bot_client.py --chat @username --sendMessage "Привет!"
kubectl exec -it deployment/telegram-bot-client -- /bin/sh

```

## 🗑️ Удаление

```bash
./undeploy.sh && kubectl delete namespace duke
```
