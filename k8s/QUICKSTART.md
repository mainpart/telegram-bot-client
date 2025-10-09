# Быстрый старт Telegram Bot Client в Kubernetes

## 🚀 Быстрое развертывание

```bash
cd k8s
./deploy-all.sh
```

## 🔑 Инициализация (первый запуск)

```bash
# 1. Найти pod
kubectl get pods -n duke

# 2. Подключиться к init-контейнеру
kubectl attach -it -n duke <POD_NAME> -c telegram-init

# 3. Ввести код из Telegram
```

## 📝 Основные команды

### Проверка статуса
```bash
kubectl get pods -n duke
kubectl logs -n duke <POD_NAME> -c telegram-bot
```

### Список чатов
```bash
kubectl exec -n duke deployment/telegram-bot-client -- \
  python telegram_bot_client.py --list-chats --limit 20
```

### Получить сообщения
```bash
kubectl exec -n duke deployment/telegram-bot-client -- \
  python telegram_bot_client.py --chat @username --limit 10
```

### Отправить сообщение
```bash
kubectl exec -n duke deployment/telegram-bot-client -- \
  python telegram_bot_client.py --chat @username --sendMessage "Hello!"
```

### Поиск
```bash
kubectl exec -n duke deployment/telegram-bot-client -- \
  python telegram_bot_client.py --search "keyword"
```

## 🔧 Управление секретами

### Создать
```bash
./secret-create.sh
```

### Просмотреть
```bash
kubectl get secrets -n duke
kubectl get secret telegram-credentials -n duke -o yaml
```

### Удалить
```bash
kubectl delete secret telegram-credentials -n duke
```

## 🗑️ Удаление

```bash
./undeploy-all.sh
```

## 🐛 Отладка

### Логи init-контейнера
```bash
kubectl logs -n duke <POD_NAME> -c telegram-init
```

### Логи основного контейнера
```bash
kubectl logs -f -n duke <POD_NAME> -c telegram-bot
```

### Проверить session файл
```bash
kubectl exec -n duke deployment/telegram-bot-client -- ls -la /data/
```

### События
```bash
kubectl get events -n duke --sort-by='.lastTimestamp'
```

### Описание пода
```bash
kubectl describe pod -n duke <POD_NAME>
```

## 🔄 Перезапуск

```bash
kubectl rollout restart deployment/telegram-bot-client -n duke
```

## 📦 Все ресурсы

```bash
kubectl get all,pvc,secrets -n duke
```

---

📖 Полная документация: см. [README.md](README.md)

