
"""
⚙️ МОДУЛЬ КОНФИГУРАЦИИ TELEGRAM БОТА

Этот модуль отвечает за:
- Загрузку переменных окружения из файла .env
- Получение и валидацию токена бота
- Централизованное хранение настроек приложения
- Обеспечение безопасности через переменные окружения

Структура:
1. Импорт необходимых библиотек
2. Загрузка переменных из .env файла
3. Извлечение и проверка токена бота
4. Валидация обязательных параметров

Переменные окружения:
- BOT_TOKEN: Токен бота, полученный от @BotFather в Telegram

Безопасность:
- Токен хранится в .env файле (исключен из git)
- Валидация предотвращает запуск без токена
- Нет хардкода чувствительных данных в коде
"""
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# 🔐 Извлечение токена бота из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🌐 Параметры webhook и веб-приложения (Mini App)
# Примечание: для polling режима WEBHOOK_* не обязательны
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "")  # пример: https://example.com
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/bot")
WEBAPP_HOST = os.getenv("WEBAPP_HOST", "0.0.0.0")
WEBAPP_PORT = int(os.getenv("WEBAPP_PORT", "8443"))

# 🌐 Base URL Configuration
BASE_URL = os.getenv("BASE_URL", "")
APP_URL = os.getenv("APP_URL", "")
REDIRECT_URL = os.getenv("REDIRECT_URL", "")


# 🔗 Telemost (Yandex 360) OAuth2 / API настройки
TELEMOST_CLIENT_ID = os.getenv("TELEMOST_CLIENT_ID", "")
TELEMOST_CLIENT_SECRET = os.getenv("TELEMOST_CLIENT_SECRET", "")
TELEMOST_REDIRECT_URI = os.getenv("TELEMOST_REDIRECT_URI", "")

# Базовые URLы OAuth2/API. Дайте точные значения при интеграции
TELEMOST_AUTH_URL = os.getenv("TELEMOST_AUTH_URL", "")  # пример: https://org-id.360.yandex.ru/oauth/authorize
TELEMOST_TOKEN_URL = os.getenv("TELEMOST_TOKEN_URL", "")  # пример: https://org-id.360.yandex.ru/oauth/token
TELEMOST_MEETINGS_URL = os.getenv("TELEMOST_MEETINGS_URL", "")  # пример: https://api.telemost.yandex.net/v1/meetings
TELEMOST_SCOPE = os.getenv("TELEMOST_SCOPE", "")
TELEMOST_TOKEN_STORE = os.getenv("TELEMOST_TOKEN_STORE", "./bot/utils/telemost_token.json")
TELEMOST_OAUTH_TOKEN = os.getenv("TELEMOST_OAUTH_TOKEN", "")  # Если уже есть готовый OAuth-токен

# ✅ Валидация обязательных параметров
if not BOT_TOKEN:
    raise ValueError(
        "❌ BOT_TOKEN не найден в переменных окружения!\n"
        "📝 Убедитесь что файл .env содержит:\n"
        "   BOT_TOKEN=ваш_токен_от_botfather"
    )
