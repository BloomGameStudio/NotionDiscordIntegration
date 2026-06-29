from typing import Optional

import aiohttp


class DiscordRestClient:
    """Send messages to Discord channels via REST API using a bot token."""

    def __init__(self, bot_token: str, session: Optional[aiohttp.ClientSession] = None):
        self._bot_token = bot_token
        self._session = session
        self._owns_session = session is None

    async def __aenter__(self) -> "DiscordRestClient":
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_session and self._session is not None:
            await self._session.close()
            self._session = None

    async def send_message(self, channel_id: int, content: str) -> None:
        if self._session is None:
            self._session = aiohttp.ClientSession()

        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        headers = {
            "Authorization": f"Bot {self._bot_token}",
            "Content-Type": "application/json",
        }

        async with self._session.post(url, headers=headers, json={"content": content}) as response:
            response.raise_for_status()
