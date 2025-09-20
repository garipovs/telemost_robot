"""

КОМАНДЫ:
/call - Создание комнаты с интерактивными кнопками

Особенности модуля:
- Использует InlineKeyboardMarkup для интерактивных элементов
- HTML-разметка для красивого форматирования сообщений
- Модульная структура с Router для легкого расширения

Технические детали:
- Все функции асинхронные (async/await)
- Типизация с использованием aiogram.types
- Обработка исключений и валидация входных данных
"""
from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputTextMessageContent,
    FSInputFile,
)
from aiogram.filters import Command
import json
from utils.telemost import TelemostClient
from config import BASE_URL, APP_URL
from urllib.parse import quote_plus


from pathlib import Path

# Создаем роутер для общих обработчиков
router = Router()


async def send_video_call_message(message: Message):
    """
      
    Создает виртуальную комнату с интерактивными кнопками.
    Демонстрирует использование InlineKeyboard в Telegram боте.
    
    Args:
        message (Message): Контекст сообщения, куда отправить ответ
        
    Функциональность:
    - Создает InlineKeyboardMarkup с двумя кнопками
    - Кнопка "Перейти по ссылке" открывает URL
    - Красивое сообщение с подтверждением создания
    
    Интерактивные элементы:
    - 📤 Поделиться - позволяет поделиться приглашением в чат
    - 🔗 Перейти по ссылке - открывает внешнюю ссылку
    """

    # Пытаемся получить реальную ссылку Телемоста
    telemost_url = None
    try:
        client = TelemostClient()
        telemost_url = await client.create_conference(title="Telemost Meeting")
    except Exception:
        telemost_url = None

    # Если API недоступен, отправляем инструкцию по настройке
    if not telemost_url:
        await message.answer(
            "🔧 <b>Telemost is not configured</b>\n\n"
            "To create video calls, you need to set up integration with Yandex 360:\n\n"
            "1️⃣ <b>Authorization:</b>\n"
            "• Use the /telemost_auth command to get the authorization link\n"
            "• Follow the link and grant access\n\n"
            "2️⃣ <b>Enter code:</b>\n"
            "• Copy the 'code' parameter from the address bar\n"
            "• Send the command: /telemost_code CODE\n\n"
            "3️⃣ <b>Verification:</b>\n"
            "• After setup, the /call command will create real meetings\n\n"
            "💡 <i>Contact the administrator to get OAuth settings</i>",
            parse_mode="HTML"
        )
        return

    # Используем полученную ссылку на встречу
    video_call_url = telemost_url

    share_text = quote_plus(f"👋 Join my video call!")
    share_url = f"https://t.me/share/url?text={share_text}&url={quote_plus(video_call_url)}"

    keyboard_inline = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="▶️ Open Call", url=video_call_url),],[
            InlineKeyboardButton(text="➕ Invite Friends", url=share_url),
        ]]
    )

    
    video_call_text = (
        f"✅ Your video call is <a href='{video_call_url}'>ready!</a>\n"
        f"📢 <a href='{share_url}'>Invite your</a> friends to join.\n"
    )
    
    video_path = Path(__file__).parent.parent / "assets" / "call.mp4"
    try:
        if video_path.exists() and video_path.stat().st_size > 0:
            await message.answer_video(
                video=FSInputFile(video_path),
                caption=video_call_text,
                supports_streaming=True,
                reply_markup=keyboard_inline,
                parse_mode="HTML",
            )
        else:
            raise FileNotFoundError("Video file not found or empty")
    except Exception:
        # Fallback на текстовое сообщение
        await message.answer(
            video_call_text,
            reply_markup=keyboard_inline,
            parse_mode="HTML",
        )




@router.message(Command("call"))
async def cmd_call(message: Message):
    """
    Команда /call — просто отправляет сообщение с кнопками комнаты
    """
    await send_video_call_message(message)




@router.message(F.web_app_data)
async def handle_web_app_data(message: Message):
    """
    📱 ОБРАБОТЧИК ДАННЫХ ОТ MINI APP
    
    Обрабатывает данные, отправленные из Telegram Mini App.
    Позволяет Mini App взаимодействовать с ботом напрямую.
    
    Args:
        message (Message): Сообщение с данными от Mini App
        
    Поддерживаемые команды:
    - video call: создание видеозвонка
    """
    try:
        # Парсим данные от Mini App
        data = json.loads(message.web_app_data.data)
        command = data.get('command', '').lower()
        action = data.get('action', '')
        
        # Реакция на старт Mini App
        if action == 'app_started':
            await message.answer('✅ Ваше Mini App запущено')
            return

        if action == 'video_call_created':
            # Прилетела ссылка комнаты из Mini App — отправим сообщение в чат
            video_call_url = data.get('url')
            if video_call_url:
                # deep link в другой Mini App отключен
                deep_link_other = None

                app_base = (APP_URL or f"{BASE_URL}/app").rstrip('/')
                share_page_url = f"{app_base}/index.html?url={quote_plus(video_call_url)}"

                kb_rows = [[ 
                    InlineKeyboardButton(text="🔗 Video call link (VKS)", url=video_call_url),
                    InlineKeyboardButton(text="📤 Share", url=share_page_url)
                ]]
                if deep_link_other:
                    kb_rows.append([
                        InlineKeyboardButton(text="🧩 Open in another Mini App", url=deep_link_other)
                    ])

                keyboard_inline = InlineKeyboardMarkup(inline_keyboard=kb_rows)
                await message.answer(
                    (
                        "🏠 <b>Your room has been created!</b>\n\n"
                        f"🔗 Link: {room_url}\n"
                        "👥 Invite friends or open the VKS link\n\n"
                        "✨ Choose an action:"
                    ),
                    reply_markup=keyboard_inline,
                    parse_mode="HTML",
                )
                return


        if action == 'send_command':
            # Убираем слэш из команды если есть
            command = command.lstrip('/')
            
            if command == 'call':
                await send_video_call_message(message)
            else:
                await message.answer(
                    f"❌ Unknown command: {command}\n\n"
                    "Available commands:\n"
                    "• /call - create video call"
                )
        else:
            # Обработка других типов данных от Mini App
            await message.answer(
                "📱 Data from Mini App received!\n\n"
                f"🔍 Action type: {action}\n"
                f"📊 Data: {command}"
            )
            
    except json.JSONDecodeError as e:
        await message.answer(
            "❌ Error processing data from Mini App\n"
            "Check the format of the data being sent"
        )
    except Exception as e:
        await message.answer(
            "❌ An error occurred while processing the request from Mini App"
        )


