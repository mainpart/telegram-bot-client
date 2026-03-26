# Telegram User Client CLI

CLI для работы с Telegram через пользовательский аккаунт. Для автоматизации, скриптов и интеграций.

## Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Дополнительные зависимости для адаптеров (ставить по необходимости):

```bash
pip install aiohttp    # для http адаптера
pip install motor      # для mongodb адаптера
pip install aio-pika   # для rabbitmq адаптера
```

## Настройка

1. Получите `api_id` и `api_hash` на [my.telegram.org](https://my.telegram.org)

2. Создайте `config.yaml` (или скопируйте из `config.yaml-default`):

```yaml
telegram:
  api_id: 12345678
  api_hash: "a1b2c3d4e5f6..."
```

3. Сгенерируйте сессию:

```bash
python telegram_bot_client.py --init
```

Токен автоматически запишется в `config.yaml`. Можно также задать через переменную окружения:

```bash
export TELEGRAM_SESSION="..."
```

## Команды

### --init

Интерактивный логин и генерация StringSession токена. Спросит номер телефона, код подтверждения и 2FA пароль (если включён). Токен сохраняется в `config.yaml`.

```bash
# Логин с номером из конфига
python telegram_bot_client.py --init

# Номер телефона можно указать в config.yaml:
# telegram:
#   phone_number: "+79001234567"
```

### --chat

Чтение сообщений из чата. Без дополнительных параметров выводит последние 20 сообщений.

`--chat` принимает username (`mike_kuleshov`) или числовой ID (`1744485600`, `-1001605174968`). У групп часто нет username — используйте ID (найти через `--searchContacts` или `--list-chats`).

```bash
# Последние 20 сообщений (по умолчанию)
python telegram_bot_client.py --chat mike_kuleshov

# По числовому ID
python telegram_bot_client.py --chat -1001605174968

# Указать количество
python telegram_bot_client.py --chat mike_kuleshov --limit 100

# Все сообщения без лимита
python telegram_bot_client.py --chat mike_kuleshov --limit 0

# Читать назад (старее) от сообщения ID 5000
python telegram_bot_client.py --chat mike_kuleshov --fromId 5000

# Читать вперёд (новее) от сообщения ID 5000
python telegram_bot_client.py --chat mike_kuleshov --fromId 5000 --forward

# Диапазон от 1000 до 2000 (границы не включены)
python telegram_bot_client.py --chat mike_kuleshov --fromId 1000 --toId 2000 --forward

# Диапазон с включением границ
python telegram_bot_client.py --chat mike_kuleshov --fromId 1000 --toId 2000 --forward --inclusive

# С фильтром по профилю
python telegram_bot_client.py --chat mike_kuleshov --limit 50 --profile dialogue

# Только входящие сообщения с медиа
python telegram_bot_client.py --chat mike_kuleshov --limit 50 --incoming-only --has-media

# Только сообщения с текстом по регулярному выражению
python telegram_bot_client.py --chat mike_kuleshov --pattern "привет|hello"

# Сообщения от конкретного пользователя
python telegram_bot_client.py --chat mike_kuleshov --from-user 809799943

# Только пересланные
python telegram_bot_client.py --chat mike_kuleshov --forwarded-only

# Только ответы
python telegram_bot_client.py --chat mike_kuleshov --replies-only

# Только с реакциями
python telegram_bot_client.py --chat mike_kuleshov --has-reactions

# Только исходящие
python telegram_bot_client.py --chat mike_kuleshov --outgoing-only
```

### --listen

Подписка на новые сообщения в реальном времени. Выводит JSON каждого нового или отредактированного сообщения. Ctrl+C для остановки.

```bash
# Конкретный чат по username
python telegram_bot_client.py --listen mike_kuleshov

# Конкретный чат по ID
python telegram_bot_client.py --listen -1001605174968

# С профилем фильтрации
python telegram_bot_client.py --listen mike_kuleshov --profile dialogue

# Только входящие с медиа
python telegram_bot_client.py --listen mike_kuleshov --incoming-only --has-media
```

### --listen-private

Подписка на все входящие личные сообщения.

```bash
python telegram_bot_client.py --listen-private

# С фильтром по паттерну
python telegram_bot_client.py --listen-private --pattern "срочно"
```

### --listen-all

Подписка на все сообщения из всех чатов и каналов.

```bash
python telegram_bot_client.py --listen-all

# С профилем
python telegram_bot_client.py --listen-all --profile dialogue
```

### --searchMessages

Поиск по тексту сообщений во всех чатах. Результаты группируются по чатам.

```bash
# Простой поиск
python telegram_bot_client.py --searchMessages "текст запроса"

# С лимитом результатов (по умолчанию 100)
python telegram_bot_client.py --searchMessages "текст запроса" --limit 50

# С профилем для очистки вывода
python telegram_bot_client.py --searchMessages "текст запроса" --profile dialogue
```

### --searchContacts

Поиск контактов, пользователей, каналов и групп по имени или username. Использует `contacts.Search` API Telegram.

```bash
# Поиск по имени
python telegram_bot_client.py --searchContacts "Михаил Кулешов"

# Поиск по части имени
python telegram_bot_client.py --searchContacts "Кулешов"

# С лимитом (по умолчанию 20)
python telegram_bot_client.py --searchContacts "марс и венера" --limit 5
```

### --list-chats

Список последних диалогов с информацией о чате и последнем сообщении.

```bash
# Последние 100 диалогов (по умолчанию)
python telegram_bot_client.py --list-chats

# Больше диалогов
python telegram_bot_client.py --list-chats --limit 500

# С профилем
python telegram_bot_client.py --list-chats --profile dialogue
```

### --get-entities

Полная информация о пользователях, чатах или каналах. Включает bio, фото, дату рождения, количество общих чатов.

```bash
# По username
python telegram_bot_client.py --get-entities mike_kuleshov

# По числовому ID
python telegram_bot_client.py --get-entities 1744485600

# Несколько сущностей
python telegram_bot_client.py --get-entities mike_kuleshov Kuleshov 123456789

# С профилем
python telegram_bot_client.py --get-entities mike_kuleshov --profile dialogue
```

### --sendMessage / --sendFiles

Отправка текста и файлов в чат.

```bash
# Текстовое сообщение
python telegram_bot_client.py --chat mike_kuleshov --sendMessage "Привет!"

# Файл
python telegram_bot_client.py --chat mike_kuleshov --sendFiles photo.jpg

# Несколько файлов
python telegram_bot_client.py --chat mike_kuleshov --sendFiles photo1.jpg photo2.jpg video.mp4

# Файлы с подписью
python telegram_bot_client.py --chat mike_kuleshov --sendFiles doc.pdf --sendMessage "Документ"

# Ответ на сообщение
python telegram_bot_client.py --chat mike_kuleshov --sendMessage "Спасибо!" --replyTo 12345

# Файл как ответ
python telegram_bot_client.py --chat mike_kuleshov --sendFiles result.pdf --replyTo 12345
```

### --forwardMessage

Пересылка сообщения из одного чата в другой.

```bash
# Переслать сообщение 123 из чата A в чат B
python telegram_bot_client.py --chat -1001605174968 --messageId 123 --forwardMessage --targetChat 1744485600

# По числовым ID
python telegram_bot_client.py --chat -1001234567890 --messageId 456 --forwardMessage --targetChat -1009876543210
```

### --replyMessage

Ответ на сообщение. Без `--targetChat` — отвечает в том же чате. С `--targetChat` — кросс-чат ответ.

```bash
# Ответ в том же чате
python telegram_bot_client.py --chat mike_kuleshov --messageId 123 --replyMessage "Ответ"

# Кросс-чат ответ (ответить в другом чате на сообщение из --chat)
python telegram_bot_client.py --chat -1001605174968 --messageId 123 --replyMessage "Смотри это" --targetChat 1744485600
```

### --editMessage

Редактирование своего сообщения.

```bash
# Заменить текст сообщения
python telegram_bot_client.py --chat mike_kuleshov --messageId 123 --editMessage "Исправленный текст"
```

### --addReaction

Добавление реакции (эмодзи) на сообщение.

```bash
# Поставить огонь
python telegram_bot_client.py --chat mike_kuleshov --messageId 123 --addReaction "🔥"

# Поставить лайк
python telegram_bot_client.py --chat mike_kuleshov --messageId 123 --addReaction "👍"
```

### --clickButton

Нажатие инлайн-кнопки на сообщении.

```bash
# Нажать кнопку с текстом
python telegram_bot_client.py --chat mike_kuleshov --messageId 123 --clickButton "Подтвердить"
```

### --download

Скачивание файла из сообщения (фото, видео, документ, голосовое). Сохраняет в текущую директорию.

```bash
# Скачать вложение
python telegram_bot_client.py --chat mike_kuleshov --messageId 123 --download

# Скачать голосовое из личного чата
python telegram_bot_client.py --chat 1744485600 --messageId 211175 --download
```

## Фильтры сообщений

Работают с `--chat` и `--listen*`:

| Фильтр | Описание |
|---|---|
| `--incoming-only` | Только входящие |
| `--outgoing-only` | Только исходящие |
| `--from-user <id>` | От конкретного пользователя |
| `--pattern <regex>` | По регулярному выражению |
| `--has-media` | Только с медиа |
| `--forwarded-only` | Только пересланные |
| `--replies-only` | Только ответы |
| `--has-reactions` | Только с реакциями |

## Профили фильтрации

`--profile <name>` применяет профиль из `profiles.json` для очистки JSON. Удаляет ненужные ключи и типы объектов:

```json
{
  "dialogue": {
    "stop_keys": ["access_hash", "file_reference", "dc_id"],
    "stop_objects": ["MessageEntityBold", "MessageActionPinMessage"]
  }
}
```

## Бот-режим

Для работы как бот (обработка CallbackQuery). Сессия не требуется.

```bash
# Бот слушает все чаты (--listen-all включается автоматически если не указано другое действие)
python telegram_bot_client.py --botToken "123456:ABC-DEF..."

# Бот слушает конкретный чат
python telegram_bot_client.py --botToken "123456:ABC-DEF..." --listen -1001605174968

# Бот слушает только личные сообщения
python telegram_bot_client.py --botToken "123456:ABC-DEF..." --listen-private
```

## Адаптеры вывода

Настраиваются в `config.yaml`. Если секция `adapters` отсутствует — используется stdout по умолчанию. Закомментированный адаптер — выключен.

```yaml
adapters:
  - type: stdout
    pretty: true          # форматированный JSON (по умолчанию true)

  - type: http
    url: "https://example.com/webhook"
    method: POST          # по умолчанию POST
    headers:
      Authorization: "Bearer token"
    timeout: 10           # секунды, по умолчанию 10

  - type: mongodb
    uri: "mongodb://user:pass@mongo:27017"
    database: "telegram"
    collection: "messages" # по умолчанию "messages"

  - type: rabbitmq
    url: "amqp://guest:guest@localhost/"  # по умолчанию localhost
    routing_key: "telegram"               # по умолчанию "telegram"
```

Адаптеры работают параллельно — сообщение отправляется во все активные адаптеры одновременно.
