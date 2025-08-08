FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копируем только необходимые файлы
COPY telegram_bot_client.py ./
COPY entrypoint.sh ./
COPY health_server.py ./
COPY profiles.json ./

# Порт для Cloud Run
ENV PORT=8080

# Стартовый скрипт — поднимем простой HTTP-сервер для healthcheck и запустим бота
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Не запускаем как root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["/entrypoint.sh"]