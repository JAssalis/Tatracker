import json
import os
import logging
from datetime import datetime

import gspread
import pytz
from oauth2client.service_account import ServiceAccountCredentials

from config import CREDENTIALS_FILE, SPREADSHEET_ID

# Timezone
BRAZIL_TZ = pytz.timezone("America/Sao_Paulo")

# Scopes
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def get_client() -> gspread.Client:
    """Authenticates and returns the gspread client."""
    google_credentials = os.getenv("GOOGLE_CREDENTIALS")
    if google_credentials:
        creds_dict = json.loads(google_credentials)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
    return gspread.authorize(creds)


def get_stocks_worksheet() -> gspread.Worksheet:
    """Returns the stocks worksheet."""
    client = get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    return spreadsheet.worksheet("investimentos")


def get_fixed_income_worksheet() -> gspread.Worksheet:
    """Returns the fixed income worksheet."""
    client = get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    return spreadsheet.worksheet("renda_fixa")


def buy_stock(ticker: str, quantity: int, price: float) -> dict:
    """
    Registers a stock purchase and recalculates average price.
    Returns updated position data.
    """
    worksheet = get_stocks_worksheet()
    records = worksheet.get_all_records()
    ticker = ticker.upper()

    # Check if ticker already exists
    for i, row in enumerate(records):
        if row["Ticker"].upper() == ticker:
            # Recalculate average price
            old_qty = float(row["Quantidade"])
            old_avg = float(row["Preço Médio"])
            old_total = float(row["Total Investido"])

            new_qty = old_qty + quantity
            new_total = old_total + (quantity * price)
            new_avg = new_total / new_qty

            # Update row (i+2 because row 1 is header and gspread is 1-indexed)
            row_index = i + 2
            worksheet.update(f"B{row_index}:D{row_index}", [[new_qty, round(new_avg, 2), round(new_total, 2)]])

            return {
                "ticker": ticker,
                "quantity": new_qty,
                "avg_price": round(new_avg, 2),
                "total_invested": round(new_total, 2),
                "is_new": False
            }

    # New ticker — append row
    total_invested = quantity * price
    worksheet.append_row([ticker, quantity, price, round(total_invested, 2), 0])

    return {
        "ticker": ticker,
        "quantity": quantity,
        "avg_price": price,
        "total_invested": round(total_invested, 2),
        "is_new": True
    }


def register_dividend(ticker: str, value_per_share: float) -> dict:
    """
    Registers dividends received for a ticker.
    Returns total dividend amount.
    """
    worksheet = get_stocks_worksheet()
    records = worksheet.get_all_records()
    ticker = ticker.upper()

    for i, row in enumerate(records):
        if row["Ticker"].upper() == ticker:
            quantity = float(row["Quantidade"])
            total_dividend = round(quantity * value_per_share, 2)
            old_dividends = float(row["Total Dividendos"])
            new_dividends = round(old_dividends + total_dividend, 2)

            # Update dividends column (E)
            row_index = i + 2
            worksheet.update(f"E{row_index}", [[new_dividends]])

            return {
                "ticker": ticker,
                "quantity": quantity,
                "value_per_share": value_per_share,
                "total_dividend": total_dividend,
                "accumulated_dividends": new_dividends
            }

    return None


def register_fixed_income(rendimento: float) -> dict:
    """
    Registers monthly fixed income yield.
    Returns updated fixed income data.
    """
    worksheet = get_fixed_income_worksheet()
    records = worksheet.get_all_records()
    mes_atual = datetime.now(BRAZIL_TZ).strftime("%Y-%m")

    # Check if current month already exists
    for i, row in enumerate(records):
        if str(row["Mês"]) == mes_atual:
            old_rendimento = float(row["Rendimento"])
            new_rendimento = round(old_rendimento + rendimento, 2)
            total = round(float(row["Total Acumulado"]) - old_rendimento + new_rendimento, 2)

            row_index = i + 2
            worksheet.update(f"C{row_index}:D{row_index}", [[new_rendimento, total]])

            return {
                "mes": mes_atual,
                "rendimento": new_rendimento,
                "total_acumulado": total,
                "updated": True
            }

    # New month — calculate accumulated total
    last_total = 0.0
    if records:
        last_total = float(records[-1]["Total Acumulado"])

    new_total = round(last_total + rendimento, 2)
    worksheet.append_row([mes_atual, 0, rendimento, new_total])

    return {
        "mes": mes_atual,
        "rendimento": rendimento,
        "total_acumulado": new_total,
        "updated": False
    }


def get_investments_summary() -> dict:
    """Returns a summary of all investments."""
    try:
        # Stocks
        stocks_ws = get_stocks_worksheet()
        stocks = stocks_ws.get_all_records()

        total_invested_stocks = sum(float(r["Total Investido"]) for r in stocks)
        total_dividends = sum(float(r["Total Dividendos"]) for r in stocks)

        # Fixed income
        fixed_ws = get_fixed_income_worksheet()
        fixed_records = fixed_ws.get_all_records()
        total_fixed = float(fixed_records[-1]["Total Acumulado"]) if fixed_records else 0.0
        last_yield = float(fixed_records[-1]["Rendimento"]) if fixed_records else 0.0

        return {
            "stocks": stocks,
            "total_invested_stocks": round(total_invested_stocks, 2),
            "total_dividends": round(total_dividends, 2),
            "total_fixed": round(total_fixed, 2),
            "last_yield": round(last_yield, 2),
        }
    except Exception as e:
        logging.error(f"Error fetching investments summary: {e}")
        return None