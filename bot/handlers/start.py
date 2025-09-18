from aiogram import Router
from aiogram.types import (
    Message,
)
from aiogram.filters import CommandStart, Command
from aiogram.filters.command import CommandObject
from utils.telemost import TelemostClient

# Создаем роутер для обработчиков
router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    🎯 ОБРАБОТЧИК КОМАНДЫ /START
    
    Первая команда, которую видит пользователь при запуске бота.
    Выполняет приветствие и знакомство с функциональностью.
    
    Args:
        message (Message): Объект сообщения от пользователя
        
    Логика:
    1. Извлекает имя пользователя (first_name)
    2. Формирует приветственное сообщение
    3. Показывает доступные команды
    """
    user_name = message.from_user.first_name or "friend"
    
    await message.answer(
        f"🤖 Hello, {user_name}!\n\n"
        f"📹 I will help you create video meetings!\n\n"
        f"💡 Use the /call command to create a meeting!",
    )


@router.message(Command("telemost_auth"))
async def cmd_telemost_auth(message: Message):
    """
    Выдаёт ссылку авторизации OAuth для Telemost.
    """
    try:
        client = TelemostClient()
        url = client.get_authorization_url()
        if not url:
            # Диагностика недостающих параметров
            missing = []
            if not client.auth_url:
                missing.append("TELEMOST_AUTH_URL")
            if not client.client_id:
                missing.append("TELEMOST_CLIENT_ID")
            if not client.redirect_uri:
                missing.append("TELEMOST_REDIRECT_URI")
            details = ", ".join(missing) if missing else "unknown"
            await message.answer(
                f"❌ Failed to generate authorization link. Missing: {details}"
            )
            return
        await message.answer(
            "🔐 Authorization for Telemost access:\n"
            "1) Follow the link and grant access\n"
            "2) After redirect, copy the code parameter from the address bar\n"
            "3) Send the command: /telemost_code CODE"
        )
        await message.answer(url)
    except Exception as e:
        await message.answer(f"💥 Error /telemost_auth: {e}")


@router.message(Command("telemost_code"))
async def cmd_telemost_code(message: Message, command: CommandObject):
    """
    Обмен кода авторизации на токен и его сохранение.
    """
    code = (command.args or "").strip()
    if not code:
        await message.answer("❗ Usage: /telemost_code AUTHORIZATION_CODE")
        return
    client = TelemostClient()
    # Поддержка 2 форматов: code (authorization_code) и готовый access_token (implicit)
    if code.startswith("y0_") or len(code) > 50:
        # Похоже на access_token из implicit flow
        client.set_access_token(code)
        await message.answer("✅ Debug token saved. Now /call will return a live link.")
        return
    token = await client.exchange_code(code)
    if token:
        await message.answer("✅ Telemost access configured. Now /call will return a live link.")
        return
    await message.answer("❌ Failed to exchange code/token. Check the data and try again.")


@router.message(Command("telemost_reset"))
async def cmd_telemost_reset(message: Message):
    """
    Удаляет сохраненный токен Telemost.
    """
    try:
        client = TelemostClient()
        deleted = client.delete_token()
        
        if deleted:
            await message.answer(
                "🗑️ <b>Telemost token deleted</b>\n\n"
                "✅ Saved token successfully deleted.\n"
                "🔄 For reconfiguration use:\n"
                "• /telemost_auth - to get authorization link\n"
                "• /telemost_code - to enter new code\n\n"
                "💡 Now the /call command will show setup instructions.",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "ℹ️ <b>Token not found</b>\n\n"
                "📝 Saved Telemost token not found or already deleted.\n"
                "🔧 For setup use commands:\n"
                "• /telemost_auth - authorization\n"
                "• /telemost_code - enter code",
                parse_mode="HTML"
            )
    except Exception as e:
        await message.answer(f"💥 Error deleting token: {e}")


