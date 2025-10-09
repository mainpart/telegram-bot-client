# Настройка автоматической сборки Docker образов

## Шаг 1: Настройка Docker Hub

1. Зайдите на [hub.docker.com](https://hub.docker.com)
2. Войдите или создайте аккаунт
3. Создайте Access Token:
   - Account Settings → Security → New Access Token
   - Description: `GitHub Actions`
   - Access permissions: Read, Write, Delete
   - **Скопируйте токен** (он показывается один раз!)

## Шаг 2: Настройка GitHub Secrets

1. Откройте: https://github.com/mainpart/telegram-bot-client/settings/secrets/actions
2. Добавьте **Repository secrets**:
   
   **Первый секрет:**
   - Name: `DOCKERHUB_USERNAME`
   - Value: `ваш_логин_dockerhub`
   
   **Второй секрет:**
   - Name: `DOCKERHUB_TOKEN`  
   - Value: `токен_из_шага_1`

## Шаг 3: Закоммитить workflow

```bash
git add .github/workflows/docker-build.yml
git commit -m "Add GitHub Actions workflow for Docker build"
git push origin main
```

## Шаг 4: Проверка

1. Откройте: https://github.com/mainpart/telegram-bot-client/actions
2. Вы увидите запущенный workflow "Build and Push Docker Image"
3. После успешной сборки образ появится в Docker Hub: `https://hub.docker.com/r/ваш_логин/telegram-bot-client`

## Использование в Kubernetes

После настройки используйте образ в ваших манифестах:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: telegram-bot-client
spec:
  replicas: 1
  selector:
    matchLabels:
      app: telegram-bot-client
  template:
    metadata:
      labels:
        app: telegram-bot-client
    spec:
      containers:
      - name: telegram-bot-client
        image: ваш_логин_dockerhub/telegram-bot-client:latest
        # или с конкретным тегом:
        # image: ваш_логин_dockerhub/telegram-bot-client:main-abc1234
        imagePullPolicy: Always
        env:
        - name: TELEGRAM_API_ID
          valueFrom:
            secretKeyRef:
              name: telegram-bot-secrets
              key: api-id
        - name: TELEGRAM_API_HASH
          valueFrom:
            secretKeyRef:
              name: telegram-bot-secrets
              key: api-hash
        # добавьте другие env переменные из config.ini
```

## Доступные теги

Workflow создает несколько тегов:
- `latest` - последняя версия из ветки main
- `main-abc1234` - версия с хешем коммита (для точного деплоя)
- `main` - последняя версия ветки main

**Рекомендация для production:** используйте теги с хешем коммита для воспроизводимости деплоев.

