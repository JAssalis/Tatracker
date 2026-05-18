import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import TELEGRAM_TOKEN, validate_config
from handlers import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


async def main() -> None:
    validate_config()

    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher()

  
    dp.include_router(router)
    logging.info("Bot iniciado! Aguardando mensagens...")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())