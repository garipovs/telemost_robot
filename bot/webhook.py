import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultVideo, FSInputFile
from urllib.parse import quote_plus
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from pathlib import Path

# Импортируем конфигурацию и обработчики
from config import (
    BOT_TOKEN,
    WEBHOOK_HOST,
    WEBHOOK_PATH,
    WEBAPP_HOST,
    WEBAPP_PORT,
)
from handlers import start, common
from utils.telemost import TelemostClient

# 🌐 Настройки webhook для продакшена (из переменных окружения)
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else ""

# 💾 Словарь для хранения подготовленных сообщений по пользователям
prepared_messages = {}

# 📝 Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_prepared_message_for_user(user_id: int, bot: Bot, video_call_url: str = ""):
    """Создает шаблонное сообщение для конкретного пользователя"""
    try:
        # Создаем inline-результат с шаблонным сообщением

        share_text = quote_plus(f"👋 Join my video call!")
        share_url = f"https://t.me/share/url?text={share_text}&url={quote_plus(video_call_url)}"
        keyboard_rows = InlineKeyboardMarkup(
            inline_keyboard=[
                [ InlineKeyboardButton(text="▶️ Open Call", url=video_call_url),],
                [ InlineKeyboardButton(text="➕ Invite Friends", url=share_url),],
            ]
        )

        text=(f"✅ Join my video  <a href='{video_call_url}'>call!</a>\n")
    
        
        video_url = f"https://tlemst.ru/bot/telemost/app/friends.mp4"
        thumbnail_url = f"https://tlemst.ru/bot/telemost/app/assets/friends-thumb.jpg"  # Если есть превью

        inline_result = InlineQueryResultVideo(
            id=f"video_call_invitation_{user_id}",
            video_url=video_url,  # Публичный URL (обязательно)
            thumbnail_url=thumbnail_url,  # Превью URL (обязательно)
            mime_type="video/mp4",
            title="🎥 Video Call Invitation",
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard_rows,
            video_width=640,  # Укажите реальные размеры вашего видео
            video_height=480,
            video_duration=10,  # Длительность в секундах
        )
        print(1)
        # Сохраняем подготовленное сообщение для конкретного пользователя
        result = await bot.save_prepared_inline_message(
            user_id=user_id,
            result=inline_result,
            allow_user_chats=True,
            allow_group_chats=True,
 
        )
        
        prepared_messages[user_id] = result.id
        logger.info(f"[OK] Подготовленное сообщение создано для пользователя {user_id} с ID: {result.id}")
        return result.id
        
    except Exception as e:
        logger.error(f"[ERROR] Ошибка создания подготовленного сообщения для пользователя {user_id}: {e}")
        return None


async def on_startup(bot: Bot) -> None:
    """
    🚀 ФУНКЦИЯ ЗАПУСКА WEBHOOK
    Устанавливает webhook URL в Telegram при старте приложения.
    """
    try:
        # Устанавливаем webhook, если указан хост
        if not WEBHOOK_URL:
            raise ValueError("WEBHOOK_HOST not set. Specify WEBHOOK_HOST in .env")

        await bot.set_webhook(
            url=WEBHOOK_URL,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query" ]
        )
        # Webhook set successfully
        
        # Получаем информацию о боте
        me = await bot.get_me()
        # Bot started successfully
        
    except Exception as e:
        # Не падаем при временной недоступности DNS/домена; пробуем позже в фоне
        logger.error(f"❌ Error setting webhook: {e}. Background retry will be performed")
        async def _retry_set_webhook() -> None:
            backoffs_seconds = [30, 60, 120, 300, 600]
            for delay in backoffs_seconds:
                try:
                    await asyncio.sleep(delay)
                    await bot.set_webhook(
                        url=WEBHOOK_URL,
                        drop_pending_updates=True,
                        allowed_updates=["message", "callback_query", "inline_query"]
                    )
                    me = await bot.get_me()
                    # Webhook set after retry
                    return
                except Exception as retry_err:
                    logger.warning(f"🔁 Failed to set webhook (waiting {delay}s): {retry_err}")
            logger.error("⛔ Exhausted webhook retry attempts. Try manually later.")
        asyncio.create_task(_retry_set_webhook())


async def on_shutdown(bot: Bot) -> None:
    """
    🛑 ФУНКЦИЯ ОСТАНОВКИ WEBHOOK
    
    Удаляет webhook из Telegram при остановке приложения.
    """
    try:
        await bot.delete_webhook()
        # Webhook removed
    except Exception as e:
        logger.error(f"❌ Error removing webhook: {e}")


async def health_check(request):
    """
    🏥 HEALTH CHECK ENDPOINT
    
    Проверка состояния сервиса для мониторинга.
    """
    return web.json_response({
        "status": "ok",
        "service": "telegram-bot",
        "version": "1.0.0"
    })


def create_app() -> web.Application:
    """
    🏗️ СОЗДАНИЕ WEB-ПРИЛОЖЕНИЯ
    
    Создает aiohttp приложение для обработки webhook запросов.
    
    Returns:
        web.Application: Настроенное веб-приложение
    """
    # Создаем бота
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Создаем диспетчер
    dp = Dispatcher()
    
    # Регистрируем роутеры
    dp.include_router(start.router)
    dp.include_router(common.router)
    
    # Регистрируем функции запуска/остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Создаем веб-приложение
    app = web.Application()
    
    # Настраиваем webhook handler
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    ).register(app, path=WEBHOOK_PATH)
    
    # Добавляем health check
    app.router.add_get("/health", health_check)
    
    # Раздача статических файлов
    assets_path = Path(__file__).parent / "assets"
    app.router.add_static("/assets/", assets_path, name="assets")

    # API: создание встречи Telemost
    async def api_create_telemost(request: web.Request) -> web.Response:
        try:
            # Читаем user_id из JSON тела (передаётся из Mini App)
            try:
                payload = await request.json()
            except Exception:
                payload = {}
            user_id = payload.get("user_id")

            client = TelemostClient()
            url = await client.create_conference(title="Meeting without confirmation")
            if not url:
                logger.error("❌ Telemost did not return meeting URL")
                return web.json_response({"ok": False, "error": "create_failed"}, status=500)

            # Если знаем пользователя, продублируем сообщение в чат с кнопками
            if user_id:
                try:
         
                    share_text = quote_plus(f"👋 Join my video call!")
                    share_url = f"https://t.me/share/url?text={share_text}&url={quote_plus(url)}"
                    keyboard_inline = InlineKeyboardMarkup(
                        inline_keyboard=[[
                            InlineKeyboardButton(text="▶️ Open Call", url=url),],[
                            InlineKeyboardButton(text="➕ Invite Friends", url=share_url),
                        ]]
                    )
                    video_path = Path(__file__).parent / "assets" / "call.mp4"
                    logger.info(f"Video path: {video_path}")
                    text=(
                            f"✅ Your video call is <a href='{url}'>ready!</a>\n"
                            f"📢 <a href='{share_url}'>Invite your</a> friends to join.\n"
                    )
          

                    # Проверяем, что видео существует и не пустое
                    if video_path.exists() and video_path.stat().st_size > 0:
                        try:
                            await bot.send_video(
                                chat_id=int(user_id),
                                video=FSInputFile(video_path),
                                caption=text,
                                supports_streaming=True,
                                reply_markup=keyboard_inline,
                                parse_mode=ParseMode.HTML,
    
                            )
                        except Exception as video_err:
                            logger.warning("Failed to send video, fallback to text: %s", video_err)
                            # Fallback на текстовое сообщение
                            await bot.send_message(
                                chat_id=int(user_id),
                                text=text,
                                reply_markup=keyboard_inline,
                                parse_mode=ParseMode.HTML,
                                disable_web_page_preview=True,
                            )
                    else:
                        logger.warning("Video not found, sending text message")
                        await bot.send_message(
                            chat_id=int(user_id),
                            text=text,
                            reply_markup=keyboard_inline,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True,
                        )
                except Exception as send_err:
                    logger.warning("Failed to send message to user %s: %s", user_id, send_err)

            return web.json_response({"ok": True, "url": url})
        except Exception as e:
            logger.error(f"❌ API error /api/telemost/create: {e}")
            return web.json_response({"ok": False, "error": str(e)}, status=500)

    app.router.add_post("/api/telemost/create", api_create_telemost)

    # API: получение ID подготовленного сообщения
    async def api_get_prepared_message_id(request: web.Request) -> web.Response:
        """API endpoint для получения ID подготовленного сообщения"""
        try:
            # Получаем user_id из query параметров
            user_id = request.query.get("user_id")
            
            if not user_id:
                return web.json_response({"ok": False, "error": "User ID is required"}, status=400)
            
            try:
                user_id = int(user_id)
            except ValueError:
                return web.json_response({"ok": False, "error": "Invalid user ID format"}, status=400)
            
            # Получаем video_call_url из query параметров (опционально)
            video_call_url = request.query.get("video_call_url", "")
            
            # Создаем новое подготовленное сообщение для пользователя каждый раз
            message_id = await create_prepared_message_for_user(user_id, bot, video_call_url)
            if not message_id:
                return web.json_response({"ok": False, "error": "Failed to create prepared message"}, status=500)

            logger.info(f"[DEBUG] Prepared message ID for user {user_id}: {message_id}")

            return web.json_response({
                "ok": True,
                "id": message_id,
                "status": "ready"
            })
            
        except Exception as e:
            logger.error(f"❌ API error /api/prepared-message-id: {e}")
            return web.json_response({"ok": False, "error": str(e)}, status=500)

    app.router.add_get("/api/prepared-message-id", api_get_prepared_message_id)
    
    setup_application(app, dp, bot=bot)
    
    return app


def main():
    app = create_app()
    if WEBHOOK_URL:
        pass
    
    web.run_app(
        app,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
        access_log=logger
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Webhook server stopped
        pass
    except Exception as e:
        logger.error(f"💥 Critical error: {e}")
        raise
