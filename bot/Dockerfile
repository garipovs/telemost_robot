# 🐳 DOCKERFILE ДЛЯ TELEGRAM БОТА

FROM python:3.13-slim

# 📝 Метаданные
LABEL maintainer="lea_alex"
LABEL description="Telegram Bot на aiogram 3.x"
LABEL version="1.0.0"

# 🔧 Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 📁 Создание рабочей директории
WORKDIR /app

# 📦 Копирование файлов зависимостей
COPY bot/requirements.txt .

# 🚀 Установка Python зависимостей
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 📋 Копирование исходного кода (плоская структура для импортов)
COPY bot/config.py ./
COPY bot/webhook.py ./
COPY bot/handlers/ ./handlers/
COPY bot/utils/ ./utils/
COPY bot/assets/ ./assets/
COPY __init__.py ./

# 👤 Создание непривилегированного пользователя
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# 🌐 Открытие порта
EXPOSE 8443

# 🎯 Команда запуска
CMD ["python", "webhook.py"]
