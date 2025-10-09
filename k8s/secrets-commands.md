# Управление секретами Kubernetes для Telegram Bot Client

## Создание секрета

### Вариант 1: Через скрипт (рекомендуется)

```bash
cd k8s
chmod +x secret-create.sh
./secret-create.sh
```

### Вариант 2: Через kubectl напрямую

```bash
kubectl create secret generic telegram-credentials \
  --from-literal=phone_number=YOUR_PHONE_NUMBER \
  --from-literal=api_id=YOUR_API_ID \
  --from-literal=api_hash=YOUR_API_HASH \
  --namespace=duke
```

### Вариант 3: Из файла

Создайте файл `telegram-credentials.env`:
```
phone_number=YOUR_PHONE_NUMBER
api_id=YOUR_API_ID
api_hash=YOUR_API_HASH
```

Затем создайте секрет:
```bash
kubectl create secret generic telegram-credentials \
  --from-env-file=telegram-credentials.env \
  --namespace=duke
```

⚠️ **Не забудьте удалить файл после создания секрета!**
```bash
rm telegram-credentials.env
```

### Вариант 4: Из YAML манифеста

**Внимание:** Значения должны быть в base64!

```bash
# Кодируем значения в base64
echo -n "YOUR_PHONE_NUMBER" | base64
echo -n "YOUR_API_ID" | base64
echo -n "YOUR_API_HASH" | base64
```

Создайте файл `telegram-secret.yaml`:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: telegram-credentials
  namespace: duke
type: Opaque
data:
  phone_number: ODkxMzc5OTQ3NjI=
  api_id: MjQyNDIyODY=
  api_hash: NGIyNGZhNDMyYTQ4NjZjNTRiMDEzZjg0MTk3YzJiNDE=
```

Применить:
```bash
kubectl apply -f telegram-secret.yaml
```

---

## Просмотр секретов

### Список всех секретов в namespace

```bash
kubectl get secrets -n duke
```

Вывод:
```
NAME                   TYPE     DATA   AGE
telegram-credentials   Opaque   3      5m
```

### Детальная информация о секрете

```bash
kubectl describe secret telegram-credentials -n duke
```

### Просмотр секрета в формате YAML

```bash
kubectl get secret telegram-credentials -n duke -o yaml
```

### Просмотр содержимого секрета (декодированное)

#### Все значения сразу

```bash
kubectl get secret telegram-credentials -n duke -o json | jq -r '.data | map_values(@base64d)'
```

Вывод:
```json
{
  "api_hash": "YOUR_API_HASH",
  "api_id": "YOUR_API_ID",
  "phone_number": "YOUR_PHONE_NUMBER"
}
```

#### Отдельные поля

```bash
# Phone number
kubectl get secret telegram-credentials -n duke -o jsonpath='{.data.phone_number}' | base64 -d
echo

# API ID
kubectl get secret telegram-credentials -n duke -o jsonpath='{.data.api_id}' | base64 -d
echo

# API Hash
kubectl get secret telegram-credentials -n duke -o jsonpath='{.data.api_hash}' | base64 -d
echo
```

#### Один лайнер для всех полей

```bash
echo "Phone: $(kubectl get secret telegram-credentials -n duke -o jsonpath='{.data.phone_number}' | base64 -d)"
echo "API ID: $(kubectl get secret telegram-credentials -n duke -o jsonpath='{.data.api_id}' | base64 -d)"
echo "API Hash: $(kubectl get secret telegram-credentials -n duke -o jsonpath='{.data.api_hash}' | base64 -d)"
```

---

## Обновление секрета

### Полная замена секрета

```bash
# Сначала удалите старый
kubectl delete secret telegram-credentials -n duke

# Создайте новый
kubectl create secret generic telegram-credentials \
  --from-literal=phone_number=НОВЫЙ_НОМЕР \
  --from-literal=api_id=НОВЫЙ_API_ID \
  --from-literal=api_hash=НОВЫЙ_API_HASH \
  --namespace=duke
```

### Обновление отдельного поля

```bash
# Получить текущий секрет в YAML
kubectl get secret telegram-credentials -n duke -o yaml > /tmp/secret-backup.yaml

# Изменить нужное значение (закодировать в base64)
echo -n "НОВОЕ_ЗНАЧЕНИЕ" | base64

# Отредактировать секрет напрямую
kubectl edit secret telegram-credentials -n duke
```

### Patch секрета

```bash
kubectl patch secret telegram-credentials -n duke \
  -p '{"data":{"phone_number":"'$(echo -n "НОВЫЙ_НОМЕР" | base64)'"}}'
```

---

## Удаление секрета

### Удалить конкретный секрет

```bash
kubectl delete secret telegram-credentials -n duke
```

### Удалить все секреты в namespace (ОСТОРОЖНО!)

```bash
kubectl delete secrets --all -n duke
```

### Удалить секрет с подтверждением

```bash
kubectl delete secret telegram-credentials -n duke --wait=true
```

---

## Проверка использования секрета

### Проверить, какие поды используют секрет

```bash
kubectl get pods -n duke -o json | \
  jq -r '.items[] | select(.spec.containers[].env[]?.valueFrom.secretKeyRef.name == "telegram-credentials") | .metadata.name'
```

### Проверить переменные окружения в работающем поде

```bash
kubectl exec -n duke deployment/telegram-bot-client -- env | grep TELEGRAM
```

Вывод:
```
TELEGRAM_PHONE_NUMBER=YOUR_PHONE_NUMBER
TELEGRAM_API_ID=YOUR_API_ID
TELEGRAM_API_HASH=YOUR_API_HASH
```

---

## Резервное копирование и восстановление

### Backup секрета

```bash
# Экспорт в YAML
kubectl get secret telegram-credentials -n duke -o yaml > telegram-secret-backup.yaml

# Экспорт в JSON
kubectl get secret telegram-credentials -n duke -o json > telegram-secret-backup.json
```

### Restore секрета

```bash
kubectl apply -f telegram-secret-backup.yaml
```

---

## Безопасность

### Проверка прав доступа к секретам

```bash
# Кто может читать секреты в namespace duke?
kubectl auth can-i get secrets -n duke --as system:serviceaccount:duke:default

# Кто может создавать секреты?
kubectl auth can-i create secrets -n duke
```

### Шифрование секретов at rest

Убедитесь, что в вашем кластере включено шифрование:
```bash
kubectl get encryptionconfig -o yaml
```

### Использование Sealed Secrets (опционально)

Для безопасного хранения секретов в Git рекомендуется использовать [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets).

---

## Troubleshooting

### Секрет не найден

```bash
# Проверить namespace
kubectl get secrets --all-namespaces | grep telegram-credentials

# Проверить имя секрета
kubectl get secrets -n duke
```

### Проблемы с base64 кодированием

```bash
# Правильное кодирование (без переноса строки)
echo -n "значение" | base64

# НЕправильное (с переносом строки)
echo "значение" | base64  # ❌
```

### Секрет не применяется к подам

После изменения секрета нужно перезапустить поды:
```bash
kubectl rollout restart deployment/telegram-bot-client -n duke
```

---

## Полезные команды

### Быстрая проверка всех секретов

```bash
kubectl get secrets -n duke -o custom-columns=NAME:.metadata.name,TYPE:.type,DATA:.data,AGE:.metadata.creationTimestamp
```

### Посмотреть размер секрета

```bash
kubectl get secret telegram-credentials -n duke -o json | jq '.data | to_entries[] | {key: .key, size: (.value | length)}'
```

### Экспорт всех секретов namespace

```bash
kubectl get secrets -n duke -o yaml > all-secrets-backup.yaml
```

