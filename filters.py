from aiogram.filters import BaseFilter
from aiogram.types import Message
from config import ALLOWED_CHAT_ID

# Only authorized user
class IsAllowedUser(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.chat.id == ALLOWED_CHAT_ID