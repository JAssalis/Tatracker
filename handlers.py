from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from filters import IsAllowedUser
from categories import normalize_category
from sheet import save_expense, get_monthly_expenses, get_monthly_goal, get_summary, get_known_categories, save_installments
from investments import buy_stock, register_dividend, register_fixed_income, register_fixed_income_deposit, get_investments_summary

router = Router()


def parse_value(raw: str) -> float:
    """Converts string value to float handling BR and EN separators."""
    raw = raw.strip()
    if "." in raw and "," in raw:
        # Format: 1.000,50 → 1000.50
        raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        # Format: 49,90 → 49.90
        raw = raw.replace(",", ".")
    elif "." in raw and len(raw.split(".")[-1]) == 3:
        # Format: 1.000 → 1000
        raw = raw.replace(".", "")
    return float(raw)


# /start
@router.message(CommandStart(), IsAllowedUser())
async def handle_start(message: Message) -> None:
    await message.answer(
        "Oi! Sou a TatáTracker.\n\n"
        "*Como usar:*\n"
        "Mande uma mensagem no formato:\n"
        "`[Valor] [Categoria]`\n\n"
        "*Exemplos:*\n"
        "`50 Almoço`\n"
        "`200 Mercado`\n"
        "`1000 Investimentos`\n\n"
        f"*Meta mensal:* R$ {get_monthly_goal():.2f}",
        parse_mode="Markdown"
    )


# /resumo
@router.message(Command("resumo"), IsAllowedUser())
async def handle_resumo(message: Message) -> None:
    summary = get_summary()
    await message.answer(
        f"*Resumo de {summary['mes']}*\n\n"
        f"*Meta do mês:* R$ {summary['meta']:.2f}\n"
        f"*Total gasto:* R$ {summary['total_gastos']:.2f}\n"
        f"*Saldo restante:* R$ {summary['saldo']:.2f}\n"
        f"*% utilizado:* {summary['percentual']:.1f}%\n\n"
        f"*Total investido:* R$ {summary['total_investimentos']:.2f}\n\n"
        f"*Onde você mais gastou:*\n{summary['ranking']}",
        parse_mode="Markdown"
    )


# /ajuda
@router.message(Command("ajuda"), IsAllowedUser())
async def handle_ajuda(message: Message) -> None:
    await message.answer(
        "*Como usar o bot:*\n\n"
        "*Registrar gasto:*\n"
        "`valor categoria`\n"
        "Exemplo: `50 Almoço`\n\n"
        "*Registrar investimento direto:*\n"
        "`valor Investimentos`\n"
        "Exemplo: `1000 Investimentos`\n\n"
        "*Aporte em renda fixa:*\n"
        "`/aporte valor ativo`\n"
        "Exemplo: `/aporte 1000 Tesouro Selic`\n\n"
        "*Rendimento renda fixa:*\n"
        "`/rendimento valor ativo`\n"
        "Exemplo: `/rendimento 45,30 Tesouro Selic`\n\n"
        "*Registrar parcela:*\n"
        "`/parcelar valor parcelas categoria`\n"
        "Exemplo: `/parcelar 300 3 Eletronico`\n\n"
        "*Compra de acao:*\n"
        "`/compra TICKER quantidade preco`\n"
        "Exemplo: `/compra BBAS3 3 20`\n\n"
        "*Dividendo recebido:*\n"
        "`/dividendo TICKER valor_por_acao`\n"
        "Exemplo: `/dividendo BBAS3 0,30`\n\n"
        "*Ver carteira:*\n"
        "`/carteira`\n\n"
        "*Ver resumo do mes:*\n"
        "`/resumo`\n\n"
        f"*Meta mensal:* configurada na aba `config` da planilha",
        parse_mode="Markdown"
    )


# /parcelar
@router.message(Command("parcelar"), IsAllowedUser())
async def handle_installment(message: Message) -> None:
    if not message.text:
        return

    parts = message.text.strip().split(maxsplit=3)

    # Validating format
    if len(parts) != 4:
        await message.answer(
            "Formato invalido.\n"
            "Use: `/parcelar valor parcelas categoria`\n"
            "Exemplo: `/parcelar 300 3 Eletronico`",
            parse_mode="Markdown"
        )
        return

    # Validating value
    try:
        value = parse_value(parts[1])
    except ValueError:
        await message.answer("Valor precisa ser um numero.\nExemplo: `/parcelar 300 3 Eletronico`")
        return

    # Validating installments
    try:
        installments = int(parts[2])
        if installments < 2:
            raise ValueError
    except ValueError:
        await message.answer("Numero de parcelas precisa ser inteiro maior que 1.")
        return

    # Normalizing category
    raw_category = parts[3].strip()
    extra_categories = get_known_categories()
    category, was_corrected = normalize_category(raw_category, extra_categories)
    installment_value = round(value / installments, 2)

    # Saving installments on the spreadsheet
    months = save_installments(value, category, installments)

    correction_note = f"_Categoria corrigida: '{raw_category}' para '{category}'_\n\n" if was_corrected else ""
    months_text = "\n".join(f"  {m}: R$ {installment_value:.2f}" for m in months)

    await message.answer(
        f"*Compra parcelada registrada*\n"
        f"Valor total: R$ {value:.2f}\n"
        f"Categoria: {category}\n"
        f"Parcelas: {installments}x de R$ {installment_value:.2f}\n\n"
        f"{correction_note}"
        f"*Meses registrados:*\n{months_text}",
        parse_mode="Markdown"
    )


# /compra
@router.message(Command("compra"), IsAllowedUser())
async def handle_buy_stock(message: Message) -> None:
    if not message.text:
        return

    parts = message.text.strip().split()

    # Validating format
    if len(parts) != 4:
        await message.answer(
            "Formato invalido.\n"
            "Use: `/compra TICKER quantidade preco`\n"
            "Exemplo: `/compra BBAS3 3 20`",
            parse_mode="Markdown"
        )
        return

    ticker = parts[1].upper()

    # Validating quantity
    try:
        quantity = int(parts[2])
        if quantity < 1:
            raise ValueError
    except ValueError:
        await message.answer("Quantidade precisa ser um numero inteiro positivo.")
        return

    # Validating price
    try:
        price = parse_value(parts[3])
    except ValueError:
        await message.answer("Preco precisa ser um numero.\nExemplo: `20` ou `19,50`")
        return

    # Save to monthly sheet as investment
    save_expense(quantity * price, "Investimentos")

    position = buy_stock(ticker, quantity, price)
    status = "Nova posicao criada" if position["is_new"] else "Posicao atualizada"

    await message.answer(
        f"*{status}*\n\n"
        f"Ticker: {position['ticker']}\n"
        f"Quantidade: {position['quantity']} acoes\n"
        f"Preco medio: R$ {position['avg_price']:.2f}\n"
        f"Total investido: R$ {position['total_invested']:.2f}",
        parse_mode="Markdown"
    )


# /dividendo
@router.message(Command("dividendo"), IsAllowedUser())
async def handle_dividend(message: Message) -> None:
    if not message.text:
        return

    parts = message.text.strip().split()

    # Validating format
    if len(parts) != 3:
        await message.answer(
            "Formato invalido.\n"
            "Use: `/dividendo TICKER valor_por_acao`\n"
            "Exemplo: `/dividendo BBAS3 0,30`",
            parse_mode="Markdown"
        )
        return

    ticker = parts[1].upper()

    # Validating value
    try:
        value_per_share = parse_value(parts[2])
    except ValueError:
        await message.answer("Valor precisa ser um numero.\nExemplo: `/dividendo BBAS3 0,30`")
        return

    result = register_dividend(ticker, value_per_share)

    if not result:
        await message.answer(
            f"Ticker *{ticker}* nao encontrado na carteira.\n"
            f"Registre a compra primeiro com `/compra {ticker} quantidade preco`",
            parse_mode="Markdown"
        )
        return

    await message.answer(
        f"*Dividendo registrado*\n\n"
        f"Ticker: {result['ticker']}\n"
        f"Quantidade: {result['quantity']:.0f} acoes\n"
        f"Valor por acao: R$ {result['value_per_share']:.2f}\n"
        f"Total recebido: R$ {result['total_dividend']:.2f}\n"
        f"Dividendos acumulados: R$ {result['accumulated_dividends']:.2f}",
        parse_mode="Markdown"
    )


# /aporte
@router.message(Command("aporte"), IsAllowedUser())
async def handle_deposit(message: Message) -> None:
    if not message.text:
        return

    parts = message.text.strip().split(maxsplit=2)

    # Validating format
    if len(parts) != 3:
        await message.answer(
            "Formato invalido.\n"
            "Use: `/aporte valor ativo`\n"
            "Exemplo: `/aporte 1000 Tesouro Selic`",
            parse_mode="Markdown"
        )
        return

    # Validating value
    try:
        value = parse_value(parts[1])
    except ValueError:
        await message.answer("Valor precisa ser um numero.\nExemplo: `/aporte 1000 Tesouro Selic`")
        return

    asset = parts[2].strip()

    # Save to monthly sheet as investment
    save_expense(value, "Investimentos")

    # Save to fixed income sheet
    result = register_fixed_income_deposit(value, asset)
    status = "Aporte atualizado" if result["updated"] else "Aporte registrado"

    await message.answer(
        f"*{status}*\n\n"
        f"Mes: {result['mes']}\n"
        f"Ativo: {result['asset']}\n"
        f"Total aportado: R$ {result['aporte']:.2f}\n"
        f"Total acumulado: R$ {result['total_acumulado']:.2f}",
        parse_mode="Markdown"
    )


# /rendimento
@router.message(Command("rendimento"), IsAllowedUser())
async def handle_fixed_income(message: Message) -> None:
    if not message.text:
        return

    parts = message.text.strip().split(maxsplit=2)

    # Validating format
    if len(parts) != 3:
        await message.answer(
            "Formato invalido.\n"
            "Use: `/rendimento valor ativo`\n"
            "Exemplo: `/rendimento 45,30 Tesouro Selic`",
            parse_mode="Markdown"
        )
        return

    # Validating value
    try:
        value = parse_value(parts[1])
    except ValueError:
        await message.answer("Valor precisa ser um numero.\nExemplo: `/rendimento 45,30 Tesouro Selic`")
        return

    asset = parts[2].strip()
    result = register_fixed_income(value, asset)
    status = "Rendimento atualizado" if result["updated"] else "Rendimento registrado"

    await message.answer(
        f"*{status}*\n\n"
        f"Mes: {result['mes']}\n"
        f"Ativo: {result['asset']}\n"
        f"Rendimento: R$ {result['rendimento']:.2f}\n"
        f"Total acumulado: R$ {result['total_acumulado']:.2f}",
        parse_mode="Markdown"
    )


# /carteira
@router.message(Command("carteira"), IsAllowedUser())
async def handle_portfolio(message: Message) -> None:
    summary = get_investments_summary()

    if not summary:
        await message.answer("Erro ao buscar dados de investimentos.")
        return

    # Building stocks text
    if summary["stocks"]:
        stocks_text = "\n".join(
            f"  *{r['Ticker']}* — {r['Quantidade']:.0f} acoes | "
            f"PM: R$ {r['Preço Médio']:.2f} | "
            f"Div: R$ {r['Total Dividendos']:.2f}"
            for r in summary["stocks"]
        )
    else:
        stocks_text = "  Nenhuma acao registrada ainda."

    # Building fixed income text
    if summary.get("fixed_assets"):
        fixed_text = "\n".join(
            f"  *{a['asset']}*\n"
            f"  Aporte: R$ {a['total_aporte']:.2f} | "
            f"Rendimento: R$ {a['total_rendimento']:.2f} | "
            f"Total: R$ {a['total_acumulado']:.2f}"
            for a in summary["fixed_assets"]
        )
    else:
        fixed_text = "  Nenhum ativo de renda fixa registrado ainda."

    await message.answer(
        f"*Carteira de Investimentos*\n\n"
        f"*Acoes:*\n{stocks_text}\n\n"
        f"Total investido em acoes: R$ {summary['total_invested_stocks']:.2f}\n"
        f"Total em dividendos: R$ {summary['total_dividends']:.2f}\n\n"
        f"*Renda Fixa:*\n{fixed_text}\n\n"
        f"Total renda fixa: R$ {summary['total_fixed']:.2f}",
        parse_mode="Markdown"
    )


# Free expense handler
@router.message(IsAllowedUser())
async def handle_expense(message: Message) -> None:
    if not message.text:
        return

    parts = message.text.strip().split(maxsplit=1)

    # Validating format
    if len(parts) != 2:
        await message.answer(
            "Formato invalido.\n"
            "Use: `[Valor] [Categoria]`\n"
            "Exemplo: `50 Almoco`",
            parse_mode="Markdown"
        )
        return

    # Validating value
    try:
        value = parse_value(parts[0])
    except ValueError:
        await message.answer(
            "Valor precisa ser um numero.\n"
            "Exemplo: `50` ou `49,90`",
            parse_mode="Markdown"
        )
        return

    # Normalizing category
    raw_category = parts[1].strip()
    extra_categories = get_known_categories()
    category, was_corrected = normalize_category(raw_category, extra_categories)
    is_investment = category == "Investimentos"

    # Saving on the spreadsheet
    save_expense(value, category)

    # Building the response
    if is_investment:
        await message.answer(
            f"*Investimento registrado*\n"
            f"Valor: R$ {value:.2f}\n"
            f"Categoria: {category}",
            parse_mode="Markdown"
        )
    else:
        total_spent = get_monthly_expenses()
        goal = get_monthly_goal()
        percentage = (total_spent / goal) * 100

        # Emoji changes based on % of goal
        if percentage < 70:
            emoji = "🟢"
        elif percentage < 90:
            emoji = "🟡"
        else:
            emoji = "🔴"

        correction_note = f"_Categoria corrigida: '{raw_category}' para '{category}'_\n\n" if was_corrected else ""

        await message.answer(
            f"*Gasto registrado*\n"
            f"Valor: R$ {value:.2f}\n"
            f"Categoria: {category}\n\n"
            f"{correction_note}"
            f"{emoji} *Meta do mes:* {percentage:.1f}% utilizado\n"
            f"R$ {total_spent:.2f} de R$ {goal:.2f}",
            parse_mode="Markdown"
        )