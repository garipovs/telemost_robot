import json
import os
import time
import logging
from typing import Optional, Dict, Any

import aiohttp

from config import (
    TELEMOST_CLIENT_ID,
    TELEMOST_CLIENT_SECRET,
    TELEMOST_REDIRECT_URI,
    TELEMOST_AUTH_URL,
    TELEMOST_TOKEN_URL,
    TELEMOST_MEETINGS_URL,
    TELEMOST_SCOPE,
    TELEMOST_TOKEN_STORE,
    TELEMOST_OAUTH_TOKEN,
)


logger = logging.getLogger(__name__)


class TelemostClient:
    """
    Небольшой клиент для Telemost API (Яндекс 360) с хранением токена.
    Поддерживает:
      - попытку Client Credentials (если разрешено в организации)
      - использование заранее выданного токена (TELEMOST_OAUTH_TOKEN)
      - чтение/запись токена в файл (access_token, refresh_token, expires_at)
    """

    def __init__(self) -> None:
        self.client_id = TELEMOST_CLIENT_ID
        self.client_secret = TELEMOST_CLIENT_SECRET
        self.redirect_uri = TELEMOST_REDIRECT_URI
        self.auth_url = TELEMOST_AUTH_URL
        self.token_url = TELEMOST_TOKEN_URL
        self.meetings_url = TELEMOST_MEETINGS_URL
        self.scope = TELEMOST_SCOPE
        self.token_store = TELEMOST_TOKEN_STORE
        self.static_token = TELEMOST_OAUTH_TOKEN
        # Telemost client initialized
        # Authorization Code Flow реализуем вручную через OAuth endpoints

    def _load_token(self) -> Optional[Dict[str, Any]]:
        if self.static_token:
            # Using static token from env
            return {"access_token": self.static_token, "expires_at": time.time() + 3600}
        if os.path.exists(self.token_store):
            try:
                with open(self.token_store, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Token loaded from file
                return data
            except Exception as e:
                # Failed to read token file
                pass
        return None

    def _save_token(self, token: Dict[str, Any]) -> None:
        try:
            os.makedirs(os.path.dirname(self.token_store), exist_ok=True)
            with open(self.token_store, "w", encoding="utf-8") as f:
                json.dump(token, f, ensure_ascii=False, indent=2)
        except Exception as e:
            # Failed to save Telemost token
            pass

    def delete_token(self) -> bool:
        """
        Удаляет сохраненный токен Telemost.
        
        Returns:
            bool: True если токен был удален, False если файл не существовал
        """
        try:
            if os.path.exists(self.token_store):
                os.remove(self.token_store)
                # Token deleted from file
                return True
            else:
                # Token file does not exist
                return False
        except Exception as e:
            # Error deleting token
            return False

    async def _fetch_token_client_credentials(self, session: aiohttp.ClientSession) -> Optional[Dict[str, Any]]:
        # Предпочтём Authorization Code Flow через библиотеку YandexOAuth
        # client_credentials не поддерживается на oauth.yandex.ru для большинства организаций
        return None

    async def _ensure_token(self, session: aiohttp.ClientSession) -> Optional[str]:
        # Ensuring token validity
        token = self._load_token()
        if token and token.get("access_token") and token.get("expires_at", 0) > time.time():
            # Token is valid, using cache
            return token["access_token"]
        # Если есть оффлайн-refresh в файле — пробуем обновить через стандартный OAuth endpoint
        cached = self._load_token()
        if cached and cached.get("refresh_token") and self.token_url and self.client_id and self.client_secret:
            try:
                # Updating token via refresh_token
                data = {
                    "grant_type": "refresh_token",
                    "refresh_token": cached["refresh_token"],
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }
                async with session.post(self.token_url, data=data, timeout=20) as resp:
                    text = await resp.text()
                    # Token refresh response received
                    if resp.status == 200:
                        new_token = json.loads(text)
                        expires_in = new_token.get("expires_in", 3600)
                        new_token["expires_at"] = time.time() + int(expires_in) - 30
                        # Сохраняем новый refresh_token, если пришёл
                        if not new_token.get("refresh_token") and cached.get("refresh_token"):
                            new_token["refresh_token"] = cached["refresh_token"]
                        self._save_token(new_token)
                        return new_token["access_token"]
            except Exception as e:
                # Error refreshing token
                pass
        # No valid token, authorization required
        return None

    def get_authorization_url(self) -> Optional[str]:
        if not (self.auth_url and self.client_id and self.redirect_uri):
            return None
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
        }
        if self.scope:
            params["scope"] = self.scope
        # Собираем URL вручную
        from urllib.parse import urlencode
        url = f"{self.auth_url}?{urlencode(params)}"
        # Authorization URL generated
        return url

    async def exchange_code(self, code: str) -> Optional[str]:
        if not (self.token_url and self.client_id and self.client_secret and self.redirect_uri):
            return None
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.token_url, data=data, timeout=20) as resp:
                    text = await resp.text()
                    # Code exchange response received
                    if resp.status != 200:
                        return None
                    token = json.loads(text)
                    if token.get("access_token"):
                        expires_in = token.get("expires_in", 3600)
                        token["expires_at"] = time.time() + int(expires_in) - 30
                        self._save_token(token)
                        return token["access_token"]
        except Exception as e:
            # Exception during code exchange
            pass
        return None

    def set_access_token(self, access_token: str, expires_in: int = 31536000, refresh_token: Optional[str] = None) -> None:
        """Сохранить заранее полученный access_token (например, отладочный)."""
        token: Dict[str, Any] = {
            "access_token": access_token,
            "expires_in": expires_in,
            "expires_at": time.time() + int(expires_in) - 30,
        }
        if refresh_token:
            token["refresh_token"] = refresh_token
        self._save_token(token)

    async def create_conference(self, title: str = "Встреча", settings: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Создаёт конференцию и возвращает join_url (ссылку на вход).
        Если не удаётся — вернёт None.
        """
        if not self.meetings_url:
            logger.error("TELEMOST_MEETINGS_URL не настроен")
            return None

        async with aiohttp.ClientSession() as session:
            access_token = await self._ensure_token(session)
            if not access_token:
                logger.error("[Telemost] Нет access_token. Проверьте OAuth настройки/доступы.")
                return None

            payload: Dict[str, Any] = {"title": title}
            # Настройки по умолчанию: мгновенный вход без комнаты ожидания и без подтверждения
            default_settings: Dict[str, Any] = {
                "immediateJoin": True,
                "waitingRoom": False,
                "joinWithoutConfirmation": True
            }
            # Поддерживаем как формат settings={...}, так и settings={"settings": {...}}
            if settings:
                nested = settings.get("settings") if isinstance(settings, dict) else None
                if isinstance(nested, dict):
                    default_settings.update(nested)
                elif isinstance(settings, dict):
                    default_settings.update(settings)
            payload["settings"] = default_settings
            payload["waiting_room_level"] = "PUBLIC"

            headers = {
                # Согласно инструкции OAuth Яндекса для отладочного токена используется схема OAuth
                "Authorization": f"OAuth {access_token}",
                "Content-Type": "application/json",
            }
            try:
                # Creating meeting
                async with session.post(self.meetings_url, headers=headers, json=payload, timeout=20) as resp:
                    text = await resp.text()
                    # Meeting creation response received
                    if resp.status not in (200, 201):
                        logger.error("[Telemost] ошибка создания встречи %s", resp.status)
                        return None
                    data = json.loads(text)
                    # предполагаем, что ссылка в одном из полей
                    join_url = (
                        data.get("join_url")
                        or data.get("joinUrl")
                        or data.get("url")
                        or data.get("link")
                    )
                    if not join_url:
                        logger.warning("[Telemost] не нашли ссылку на встречу в ответе: %s", data)
                        return None
                    # Meeting link generated
                    return join_url
            except Exception as e:
                # Exception during meeting creation
                return None


