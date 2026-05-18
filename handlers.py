from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

from filters import IsAllowedUser
from sheet import save_expense, get_monthly_expenses, get_monthly_goal
from config import MONTHLY_GOAL, INVESTMENT_CATEGORY

router = Router()

# Creating /start message
@router.message(CommandStart(), IsAllowedUser())
async def handle_start(message: Message) -> None:
    await message.answer(
         "Oi! Sou a GiovaninhaBot.\n\n"
        "*Como usar:*\n"
        "Mande uma mensagem no formato:\n"
        "`[Valor] [Categoria]`\n\n"
        "*Exemplos:*\n"
        "`50 Almoço`\n"
        "`200 Mercado`\n"
        "`1000 Investimentos`\n\n"
        f"🎯 *Meta mensal:* R$ {MONTHLY_GOAL:.2f}",
        parse_mode="Markdown"
    )

# Validating the message
@router.message(IsAllowedUser())
async def handle_expense(message: Message) -> None:

    if not message.text:
        return
    
    parts = message.text.strip().split(maxsplit=1)

    if len(parts) !=2:
        await message.answer(
            "*Formato inválido*\n"
            "Use: `[Valor] [Categoria]`\n"
            "Exemplo: `50 Almoço`",
            parse_mode="Markdown"
        )
        return

    # Validating the value
    try:
        value = float(parts[0].replace(",", "."))
    except ValueError:
        await message.answer(
           "Valor precisa ser um *número*\n"
           "Exemplo: [50] ou [49,9]. ",
           parse_mode="Markdown" 
        )
        return
    
    category = parts[1].strip()
    is_investment = category.lower() in ["investimento", "investimentos"]
    category = "Investimentos" if is_investment else category.capitalize()

    # Saving on the spreadsheet
    save_expense(value, category)

    is_investment = category.lower() == INVESTMENT_CATEGORY.lower()

    # Creating the response
    if is_investment:
        await message.answer(
            f"*Investimento Registrado!*\n"
            f"Valor: R$ {value:.2f}\n"
            f"Categoria: {category}",
            parse_mode="Markdown"
        )
    else:
        total_spent = get_monthly_expenses()
        goal = get_monthly_goal()
        percentage = (total_spent / goal) * 100
        if percentage < 70:
            emoji = "🟢"
        elif percentage < 90:
            emoji = "🟡"
        else:
            emoji = "🔴"

        await message.answer(
            f"*Gasto registrado!*\n"
            f"Valor: R$ {value:.2f}\n"
            f"Categoria: {category}\n\n"
            f"*Meta do mês:* {percentage:.1f}% utilizado\n"
            f"📊 R$ {total_spent:.2f} de R$ {goal:.2f}",
            parse_mode="Markdown"
        )