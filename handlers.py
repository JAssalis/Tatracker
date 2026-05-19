from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from filters import IsAllowedUser
from categories import normalize_category
from sheet import save_expense, get_monthly_expenses, get_monthly_goal, get_summary, get_known_categories

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

@router.message(Command("resumo"), IsAllowedUser())
async def handle_resumo(message: Message) -> None:
    """Retorna um resumo dos gastos do mês atual."""
    summary = get_summary()

    await message.answer(
        f"📊 *Resumo de {summary['mes']}*\n\n"
        f"*Meta do mês:* R$ {summary['meta']:.2f}\n"
        f"*Total gasto:* R$ {summary['total_gastos']:.2f}\n"
        f"*Saldo restante:* R$ {summary['saldo']:.2f}\n"
        f"*% utilizado:* {summary['percentual']:.1f}%\n\n"
        f"*Total investido:* R$ {summary['total_investimentos']:.2f}\n\n"
        f"*Onde você mais gastou:*\n{summary['ranking']}",
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
    
    raw_category = parts[1].strip()
    extra_categories = get_known_categories()
    category, was_corrected = normalize_category(raw_category, extra_categories)
    is_investment = category == "Investimentos"

    # Saving on the spreadsheet
    save_expense(value, category)

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

        correction_note = f"📝 _Categoria corrigida: '{raw_category}' → '{category}'_\n\n" if was_corrected else ""

        await message.answer(
            f"*Gasto registrado!*\n"
            f"Valor: R$ {value:.2f}\n"
            f"Categoria: {category}\n\n"
            f"*Meta do mês:* {percentage:.1f}% utilizado\n"
            f"📊 R$ {total_spent:.2f} de R$ {goal:.2f}",
            parse_mode="Markdown"
        )