# Развертывание Telegram Bot Client в Kubernetes

Это руководство описывает процесс развертывания Telegram Bot Client в Kubernetes кластере с использованием двухфазного запуска (init-контейнер + основной контейнер).

## Архитектура решения

- **Init-контейнер**: Создает сессию аутентификации Telegram (файл `anon.session`)
- **Основной контейнер**: Использует созданную сессию для работы с Telegram API
- **PVC (Longhorn)**: Хранит файл сессии между перезапусками
- **Secret**: Хранит конфиденциальные данные (номер телефона, API ID, API Hash)

## Предварительные требования

1. Kubernetes кластер с установленным Longhorn storage
2. Namespace `duke` (будет создан автоматически при применении манифестов)
3. Docker образ `dmitry138/telegram-bot-client:latest` в Docker Hub
4. Telegram API credentials (API ID и API Hash от https://my.telegram.org)

## Шаг 1: Создание Namespace

```bash
kubectl create namespace duke
```

Проверка:
```bash
kubectl get namespaces | grep duke
```

## Шаг 2: Создание Secret с учетными данными

### Вариант A: Автоматическое создание через скрипт

```bash
cd k8s
chmod +x secret-create.sh
./secret-create.sh
```

### Вариант B: Ручное создание через kubectl

```bash
kubectl create secret generic telegram-credentials \
  --from-literal=phone_number=YOUR_PHONE_NUMBER \
  --from-literal=api_id=YOUR_API_ID \
  --from-literal=api_hash=YOUR_API_HASH \
  --namespace=duke
```

### Проверка секрета

Просмотр созданных секретов:
```bash
kubectl get secrets -n duke
```

Просмотр содержимого секрета (декодированное):
```bash
kubectl get secret telegram-credentials -n duke -o jsonpath='{.data.phone_number}' | base64 -d
kubectl get secret telegram-credentials -n duke -o jsonpath='{.data.api_id}' | base64 -d
kubectl get secret telegram-credentials -n duke -o jsonpath='{.data.api_hash}' | base64 -d
```

Полный вывод секрета в YAML:
```bash
kubectl get secret telegram-credentials -n duke -o yaml
```

### Удаление секрета (если нужно пересоздать)

```bash
kubectl delete secret telegram-credentials -n duke
```

## Шаг 3: Создание PVC для хранения сессии

```bash
kubectl apply -f k8s/pvc.yaml
```

Проверка:
```bash
kubectl get pvc -n duke
```

Вы должны увидеть:
```
NAME                       STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
telegram-session-storage   Bound    pvc-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx   100Mi      RWO            longhorn       10s
```

## Шаг 4: Развертывание приложения

```bash
kubectl apply -f k8s/deployment.yaml
```

Проверка статуса:
```bash
kubectl get pods -n duke
kubectl describe pod -n duke -l app=telegram-bot-client
```

## Шаг 5: Инициализация сессии (ВАЖНО!)

При первом запуске init-контейнер будет ожидать ввода кода подтверждения от Telegram.

### 5.1. Найти имя пода

```bash
kubectl get pods -n duke
```

Пример вывода:
```
NAME                                  READY   STATUS     RESTARTS   AGE
telegram-bot-client-xxxxxxxxx-xxxxx   0/1     Init:0/1   0          30s
```

### 5.2. Подключиться к init-контейнеру

```bash
kubectl attach -it -n duke POD_NAME -c telegram-init
```

Например:
```bash
kubectl attach -it -n duke telegram-bot-client-xxxxxxxxx-xxxxx -c telegram-init
```

### 5.3. Ввести код подтверждения

После подключения вы увидите запрос:
```
Enter the code you received:
```

1. Откройте Telegram на вашем телефоне/другом устройстве
2. Вы получите код подтверждения
3. Введите код в терминале и нажмите Enter

Если у вас включена двухфакторная аутентификация (2FA):
```
Enter your 2FA password:
```
Введите пароль облачной авторизации.

### 5.4. Проверка успешной инициализации

После успешной аутентификации init-контейнер завершится с кодом 0, и запустится основной контейнер.

```bash
kubectl get pods -n duke
```

Должно быть:
```
NAME                                  READY   STATUS    RESTARTS   AGE
telegram-bot-client-xxxxxxxxx-xxxxx   1/1     Running   0          2m
```

Просмотр логов:
```bash
# Логи init-контейнера
kubectl logs -n duke POD_NAME -c telegram-init

# Логи основного контейнера
kubectl logs -n duke POD_NAME -c telegram-bot
```

## Шаг 6: Использование клиента

После успешной инициализации вы можете выполнять команды Telegram клиента через `kubectl exec`.

### Список чатов

```bash
kubectl exec -n duke deployment/telegram-bot-client -- \
  python telegram_bot_client.py --list-chats --limit 20
```

### Получить сообщения из чата

```bash
kubectl exec -n duke deployment/telegram-bot-client -- \
  python telegram_bot_client.py --chat @username --limit 10
```

### Отправить сообщение

```bash
kubectl exec -n duke deployment/telegram-bot-client -- \
  python telegram_bot_client.py --chat @username --sendMessage "Hello from Kubernetes!"
```

### Поиск сообщений

```bash
kubectl exec -n duke deployment/telegram-bot-client -- \
  python telegram_bot_client.py --search "keyword"
```

### Прослушивание сообщений в реальном времени

Для режима прослушивания нужно изменить команду в deployment.yaml:

```yaml
command:
  - python
  - telegram_bot_client.py
  - --listen-all  # или --listen @chatname
```

Затем применить изменения:
```bash
kubectl apply -f k8s/deployment.yaml
kubectl logs -f -n duke deployment/telegram-bot-client
```

## Управление развертыванием

### Перезапуск пода

```bash
kubectl rollout restart deployment/telegram-bot-client -n duke
```

### Масштабирование (НЕ рекомендуется!)

⚠️ **ВАЖНО**: Не запускайте более 1 реплики! Файл сессии не может использоваться несколькими подами одновременно.

### Обновление образа

После публикации нового образа в Docker Hub:

```bash
kubectl rollout restart deployment/telegram-bot-client -n duke
```

Или принудительно:
```bash
kubectl delete pod -n duke -l app=telegram-bot-client
```

### Просмотр статуса развертывания

```bash
kubectl rollout status deployment/telegram-bot-client -n duke
```

## Отладка

### Проверка состояния PVC

```bash
kubectl describe pvc telegram-session-storage -n duke
```

### Проверка файла сессии внутри контейнера

```bash
kubectl exec -n duke deployment/telegram-bot-client -- ls -la /data/
```

Должен быть файл `anon.session`:
```
-rw-r--r-- 1 appuser appuser 8192 Oct  9 12:34 anon.session
```

### Проверка секретов в контейнере

```bash
kubectl exec -n duke deployment/telegram-bot-client -- env | grep TELEGRAM
```

### Логи init-контейнера

```bash
kubectl logs -n duke POD_NAME -c telegram-init
```

### Логи основного контейнера

```bash
kubectl logs -n duke POD_NAME -c telegram-bot
kubectl logs -f -n duke POD_NAME -c telegram-bot  # follow mode
```

### События кластера

```bash
kubectl get events -n duke --sort-by='.lastTimestamp'
```

## Удаление развертывания

### Удалить только deployment (сохранить данные)

```bash
kubectl delete deployment telegram-bot-client -n duke
```

### Удалить всё включая данные сессии

```bash
kubectl delete deployment telegram-bot-client -n duke
kubectl delete pvc telegram-session-storage -n duke
kubectl delete secret telegram-credentials -n duke
```

### Удалить namespace полностью

⚠️ **ОСТОРОЖНО**: Это удалит ВСЁ в namespace duke!

```bash
kubectl delete namespace duke
```

## Проблемы и решения

### Init-контейнер зависает

Если init-контейнер не завершается:
1. Проверьте, подключились ли вы к нему через `kubectl attach`
2. Убедитесь, что ввели правильный код
3. Проверьте логи: `kubectl logs -n duke POD_NAME -c telegram-init`

### Ошибка "Session file not found"

1. Проверьте, что PVC примонтирован: `kubectl describe pod POD_NAME -n duke`
2. Проверьте содержимое `/data`: `kubectl exec -n duke POD_NAME -- ls -la /data/`
3. Возможно, нужно пересоздать сессию - удалите pod и пройдите инициализацию заново

### Ошибка "User not authorized"

Сессия могла устареть. Удалите pod и пройдите инициализацию заново:
```bash
kubectl delete pod -n duke -l app=telegram-bot-client
```

### Pod в статусе CrashLoopBackOff

Проверьте логи обоих контейнеров:
```bash
kubectl logs -n duke POD_NAME -c telegram-init
kubectl logs -n duke POD_NAME -c telegram-bot
```

## Интеграция с CI/CD

Для автоматического обновления при пуше в Docker Hub можно добавить ImagePullPolicy:

```yaml
imagePullPolicy: Always
```

Это уже настроено в deployment.yaml.

## Безопасность

1. **Секреты**: Учетные данные хранятся в Kubernetes Secret (base64, но не зашифрованы)
2. **Session файл**: Критически важен! Хранится в PVC с Longhorn
3. **Backup**: Рекомендуется регулярно делать backup PVC через Longhorn UI
4. **Не коммитьте**: Никогда не коммитьте реальные credentials в Git!

## Мониторинг

Для продакшена рекомендуется добавить:
- Liveness/Readiness probes
- Resource limits
- Prometheus metrics
- Alerting

Пример добавления в deployment.yaml:

```yaml
livenessProbe:
  exec:
    command:
    - python
    - -c
    - "import os; exit(0 if os.path.exists('/data/anon.session') else 1)"
  initialDelaySeconds: 30
  periodSeconds: 60
```

## Полезные ссылки

- [Telegram API Documentation](https://core.telegram.org/api)
- [Telethon Documentation](https://docs.telethon.dev/)
- [Longhorn Documentation](https://longhorn.io/docs/)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
