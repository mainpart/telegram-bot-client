#!/bin/sh
set -e

cd /app

# Собираем config.ini из переменных окружения (секреты зададите при деплое)
if [ -n "$TELEGRAM_PHONE_NUMBER" ] && [ -n "$TELEGRAM_API_ID" ] && [ -n "$TELEGRAM_API_HASH" ]; then
  # Убедимся, что есть права на запись
  touch /app/config.ini 2>/dev/null || true
  cat > /app/config.ini <<EOF
[telegram]
phone_number = ${TELEGRAM_PHONE_NUMBER}
api_id = ${TELEGRAM_API_ID}
api_hash = ${TELEGRAM_API_HASH}
EOF
fi

# Сессия Telethon на примонтированном томе Cloud Storage (/sessions)
# Симлинк позволит Telethon читать/писать файл на том
mkdir -p /sessions
ln -sf /sessions/anon.session /app/anon.session

# Лёгкий HTTP-сервер healthcheck без листинга файлов
python /app/health_server.py >/dev/null 2>&1 &

# Запускаем вашего клиента с аргументами из переменной окружения BOT_ARGS
# Пример: BOT_ARGS="--listen-all --profile dialogue"
echo "[startup] Starting telegram_bot_client.py with args: ${BOT_ARGS}" 1>&2
ls -la /app 1>&2 || true
echo "[startup] profiles.json presence:" 1>&2; [ -f /app/profiles.json ] && echo "OK" 1>&2 || echo "MISS" 1>&2
echo "[startup] anon.session symlink:" 1>&2; ls -l /app/anon.session 1>&2 || true
exec python /app/telegram_bot_client.py ${BOT_ARGS} --debug