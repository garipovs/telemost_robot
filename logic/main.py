import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram import Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, InlineQueryResultArticle, InputTextMessageContent
from aiogram.webhook.aiohttp_server import SimpleRequestHandler
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, JSONResponse
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles

from .config import settings


# Логирование конфигурации при старте
print(f"[CONFIG] Загружена конфигурация:\n{settings}")

# Импортируем бота для создания подготовленных сообщений
bot = Bot(token=settings.bot_token)
dp = Dispatcher()
router = Router()

# Словарь для хранения подготовленных сообщений по пользователям
prepared_messages = {}

async def create_prepared_message_for_user(user_id: int):
    """Создает шаблонное сообщение для конкретного пользователя"""
    try:
        # Создаем inline-результат с шаблонным сообщением
        inline_result = InlineQueryResultArticle(
            id=f"template_message_{user_id}",
            title="🚀 Сообщение из Mini App",
            description="Отправить подготовленное сообщение",
            input_message_content=InputTextMessageContent(
                message_text=" <b>Сообщение из Mini App</b>\n\n"
                           " <b>От:</b> {user_name}\n"
                           "🕐 <b>Время:</b> {timestamp}\n\n"
                           "💬 <b>Текст:</b>\n{message_text}\n\n"
                           "✨ <i>Отправлено через Telegram Mini App</i>",
                parse_mode="HTML"
            )
        )
        
        # Сохраняем подготовленное сообщение для конкретного пользователя
        result = await bot.save_prepared_inline_message(
            user_id=user_id,
            result=inline_result,
            allow_user_chats=True,
            allow_group_chats=True
        )
        
        prepared_messages[user_id] = result.id
        print(f"[OK] Подготовленное сообщение создано для пользователя {user_id} с ID: {result.id}")
        return result.id
        
    except Exception as e:
        print(f"[ERROR] Ошибка создания подготовленного сообщения для пользователя {user_id}: {e}")
        return None

@router.message(CommandStart())
async def on_start_command(message: types.Message):
    # Создаем кнопку для открытия Mini App
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Открыть Mini App", web_app=WebAppInfo(url=f"{settings.app_base_url}:{settings.app_port}"))]
    ])
    
    await message.answer(
        " Привет! Я бот с Mini App.\n\n"
        "Нажмите кнопку ниже, чтобы открыть Mini App и отправить сообщение:",
        reply_markup=keyboard
    )


@router.message()
async def echo(message: types.Message):
    await message.answer(message.text or "Бот работает. Напишите /start")


def build_public_webhook_url() -> str:
    base = (settings.app_base_url or "").rstrip("/")
    port = settings.bot_port
    if not base:
        return ""
    # Если порт уже указан в base — не добавляем
    if base.startswith("http://") or base.startswith("https://"):
        hostpart = base.split("://", 1)[1]
        if ":" in hostpart:
            return f"{base}{settings.webhook_path}"
        # Не добавляем стандартные порты
        if (base.startswith("https://") and port == 443) or (
            base.startswith("http://") and port == 80
        ):
            return f"{base}{settings.webhook_path}"
    return f"{base}:{port}{settings.webhook_path}"


@asynccontextmanager
async def lifespan(_: FastAPI):
    public_url = build_public_webhook_url()
    if public_url and not settings.skip_auto_webhook:
        last_error = None
        for attempt in range(1, 6):
            try:
                # Пропускаем установку, если уже такой же URL
                try:
                    info = await bot.get_webhook_info()
                    if info.url == public_url:
                        print(f"[OK] Webhook уже установлен: {public_url}")
                        last_error = None
                        break
                except Exception:
                    pass
                await bot.set_webhook(
                    url=public_url,
                    secret_token=settings.secret_token,
                    drop_pending_updates=True,
                    allowed_updates=["message", "callback_query", "inline_query"],
                )
                print(
                    f"[OK] Webhook установлен: {public_url} (порт бота: {settings.bot_port}), попытка {attempt}"
                )
                last_error = None
                break
            except Exception as e:
                last_error = e
                wait_seconds = min(30, attempt * 2)
                print(f"[WARN] set_webhook failed (try {attempt}/5): {e}. Retry in {wait_seconds}s...")
                await asyncio.sleep(wait_seconds)
        if last_error:
            print(f"[ERROR] Не удалось установить webhook после 5 попыток: {last_error}")
    try:
        print("[OK] Bot процесс стартует. Ожидание обновлений...")
        yield
    finally:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.session.close()


app = FastAPI(title="TelegramBot", lifespan=lifespan)

# Настройка CORS для Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://leaalex.ru:3020",  # Mini App
        "https://leaalex.ru",       # Основной домен
        "http://localhost:3020",    # Dev режим
        "http://localhost:3000",    # Dev режим
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-User-ID",
        "X-Telegram-Bot-Api-Secret-Token",
    ],
)
dp.include_router(router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.options("/api/prepared-message-id")
async def options_prepared_message_id():
    """Обработка preflight запросов для CORS"""
    return JSONResponse({"status": "ok"})


@app.get("/api/prepared-message-id")
async def get_prepared_message_id(request: Request):
    print(f"[DEBUG] Request: {request}")
    print(f"[DEBUG] Headers: {dict(request.headers)}")
    print(f"[DEBUG] Origin: {request.headers.get('origin')}")
    """API endpoint для получения ID подготовленного сообщения"""
    # Получаем user_id из заголовков или параметров запроса
    user_id = request.headers.get("X-User-ID")
    if not user_id:
        # Пробуем получить из query параметров
        user_id = request.query_params.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    try:
        user_id = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    # Создаем новое подготовленное сообщение для пользователя каждый раз
    message_id = await create_prepared_message_for_user(user_id)
    if not message_id:
        raise HTTPException(status_code=500, detail="Failed to create prepared message")

    print(f"[DEBUG] Prepared message ID for user {user_id}: {message_id}")
    
    return JSONResponse({
        "id": message_id,
        "status": "ready"
    })


@app.post(settings.webhook_path)
async def telegram_webhook(request: Request):
    # Validate Telegram secret token header if configured
    if settings.secret_token:
        header_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if not header_token or header_token != settings.secret_token:
            print("[WARN] Invalid or missing secret token header")
            raise HTTPException(status_code=401, detail="Invalid secret token")
    update = await request.json()
    aiogram_update = types.Update.model_validate(update)
    print(f"[OK] Update received: {aiogram_update.event_type}")
    await dp.feed_update(bot, aiogram_update)
    return JSONResponse({"ok": True})


@app.post("/api/send-message")
async def send_message_from_mini_app(request: Request):
    """API endpoint для получения сообщений от Mini App"""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        message = data.get("message")
        username = data.get("username")
        first_name = data.get("first_name")
        
        if not user_id or not message:
            raise HTTPException(status_code=400, detail="Missing user_id or message")
        
        # Отправляем сообщение пользователю от имени бота
        response_text = f"📱 <b>Сообщение из Mini App:</b>\n\n"
        response_text += f"👤 <b>От:</b> {first_name or 'Пользователь'}"
        if username:
            response_text += f" (@{username})"
        response_text += f"\n\n💬 <b>Сообщение:</b>\n{message}"
        
        await bot.send_message(
            chat_id=user_id,
            text=response_text,
            parse_mode="HTML"
        )
        
        print(f"[OK] Message sent to user {user_id} from Mini App")
        return JSONResponse({"ok": True, "message": "Message sent successfully"})
        
    except Exception as e:
        print(f"[ERROR] Failed to send message from Mini App: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")


# No static here. Static is served by bot.server


def get_ssl_params() -> dict:
    ssl_params: dict[str, Optional[str]] = {}
    if settings.ssl_certfile and settings.ssl_keyfile:
        cert_path = Path(settings.ssl_certfile)
        key_path = Path(settings.ssl_keyfile)
        if cert_path.exists() and key_path.exists():
            ssl_params["ssl_certfile"] = str(cert_path)
            ssl_params["ssl_keyfile"] = str(key_path)
    return ssl_params

def run():
    import uvicorn

    uvicorn.run(
        "bot.main:app",
        host=settings.host,
        port=settings.bot_port,
        reload=False,
        **get_ssl_params(),
    )

if __name__ == "__main__":
    run()


