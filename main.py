import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

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

    # Defining the commands menu
    await bot.set_my_commands([
        BotCommand(command="start", description="Iniciar o bot"),
        BotCommand(command="resumo", description="Ver resumo do mês"),
        BotCommand(command="parcelar", description="Registrar compra parcelada"),
        BotCommand(command="ajuda", description="Ver como usar o bot"),
    ])

    logging.info("Bot iniciado! Aguardando mensagens...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())