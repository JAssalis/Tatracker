import json
import os
import logging
from datetime import datetime

import gspread
import pytz
from oauth2client.service_account import ServiceAccountCredentials

from config import CREDENTIALS_FILE, SPREADSHEET_ID

def parse_float(value) -> float:
    """Converts string to float handling BR decimal separator."""
    return float(str(value).replace(",", ".")) if value else 0.0

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
    """Registers a stock purchase and recalculates average price."""
    worksheet = get_stocks_worksheet()
    all_values = worksheet.get_all_values()
    ticker = ticker.upper()

    for i, row in enumerate(all_values):
        if i == 0:
            continue  # Skip header
        if row[0].upper() == ticker:
            old_qty = parse_float(row[1])
            old_total = parse_float(row[3])

            new_qty = old_qty + quantity
            new_total = old_total + (quantity * price)
            new_avg = new_total / new_qty

            row_index = i + 1
            worksheet.update(f"B{row_index}:D{row_index}", [[new_qty, round(new_avg, 2), round(new_total, 2)]])

            return {
                "ticker": ticker,
                "quantity": new_qty,
                "avg_price": round(new_avg, 2),
                "total_invested": round(new_total, 2),
                "is_new": False
            }

    # New ticker
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
    """Registers dividends received for a ticker."""
    worksheet = get_stocks_worksheet()
    all_values = worksheet.get_all_values()
    ticker = ticker.upper()

    for i, row in enumerate(all_values):
        if i == 0:
            continue  # Skip header
        if row[0].upper() == ticker:
            quantity = parse_float(row[1])
            total_dividend = round(quantity * value_per_share, 2)
            old_dividends = parse_float(row[4])
            new_dividends = round(old_dividends + total_dividend, 2)

            row_index = i + 1
            worksheet.update(f"E{row_index}", [[new_dividends]])

            return {
                "ticker": ticker,
                "quantity": quantity,
                "value_per_share": value_per_share,
                "total_dividend": total_dividend,
                "accumulated_dividends": new_dividends
            }

    return None

def register_fixed_income_deposit(value: float, asset: str) -> dict:
    """Registers a fixed income deposit for the current month and asset."""
    worksheet = get_fixed_income_worksheet()
    mes_atual = datetime.now(BRAZIL_TZ).strftime("%Y-%m")
    asset = asset.strip().title()

    all_values = worksheet.get_all_values()

    for i, row in enumerate(all_values):
        if i == 0:
            continue
        if row[0].strip() == mes_atual and row[1].strip().lower() == asset.lower():
            old_aporte = parse_float(row[2])
            rendimento = parse_float(row[3])
            new_aporte = round(old_aporte + value, 2)
            total = round(new_aporte + rendimento, 2)

            row_index = i + 1
            worksheet.update(f"C{row_index}:E{row_index}", [[new_aporte, rendimento, total]])

            return {
                "mes": mes_atual,
                "asset": asset,
                "aporte": new_aporte,
                "total_acumulado": total,
                "updated": True
            }

    # New month or new asset
    worksheet.append_row([mes_atual, asset, value, 0, value])

    return {
        "mes": mes_atual,
        "asset": asset,
        "aporte": value,
        "total_acumulado": value,
        "updated": False
    }


def get_investments_summary() -> dict:
    """Returns a summary of all investments."""
    try:
        # Stocks
        stocks_ws = get_stocks_worksheet()
        all_values = stocks_ws.get_all_values()
        stocks = []
        total_invested_stocks = 0.0
        total_dividends = 0.0

        for i, row in enumerate(all_values):
            if i == 0 or not row[0]:
                continue

            ticker = row[0]
            quantidade = parse_float(row[1])
            preco_medio = parse_float(row[2])
            total_investido = parse_float(row[3])
            dividendos = parse_float(row[4])

            stocks.append({
                "Ticker": ticker,
                "Quantidade": quantidade,
                "Preço Médio": preco_medio,
                "Total Investido": total_investido,
                "Total Dividendos": dividendos
            })
            total_invested_stocks += total_investido
            total_dividends += dividendos

        # Fixed income — Mês | Ativo | Aporte | Rendimento | Total Acumulado
        fixed_ws = get_fixed_income_worksheet()
        fixed_values = fixed_ws.get_all_values()
        fixed_assets_dict = {}
        total_fixed = 0.0

        for i, row in enumerate(fixed_values):
            if i == 0 or not row[0]:
                continue

            asset = row[1]          # Ativo
            aporte = parse_float(row[2])
            rendimento = parse_float(row[3])
            total_acumulado = parse_float(row[4])

            if asset not in fixed_assets_dict:
                fixed_assets_dict[asset] = {
                    "asset": asset,
                    "total_aporte": 0.0,
                    "total_rendimento": 0.0,
                    "total_acumulado": 0.0
                }

            fixed_assets_dict[asset]["total_aporte"] += aporte
            fixed_assets_dict[asset]["total_rendimento"] += rendimento
            fixed_assets_dict[asset]["total_acumulado"] = round(
                fixed_assets_dict[asset]["total_aporte"] + fixed_assets_dict[asset]["total_rendimento"], 2
            )

        fixed_assets = list(fixed_assets_dict.values())
        total_fixed = sum(a["total_acumulado"] for a in fixed_assets)

        return {
            "stocks": stocks,
            "total_invested_stocks": round(total_invested_stocks, 2),
            "total_dividends": round(total_dividends, 2),
            "fixed_assets": fixed_assets,
            "total_fixed": round(total_fixed, 2),
        }

    except Exception as e:
        logging.error(f"Error fetching investments summary: {e}")
        return None

def register_fixed_income(rendimento: float, asset: str) -> dict:
    """Registers monthly fixed income yield for a specific asset."""
    worksheet = get_fixed_income_worksheet()
    mes_atual = datetime.now(BRAZIL_TZ).strftime("%Y-%m")
    asset = asset.strip().title()

    all_values = worksheet.get_all_values()

    for i, row in enumerate(all_values):
        if i == 0:
            continue
        if row[0].strip() == mes_atual and row[1].strip().lower() == asset.lower():
            aporte = parse_float(row[2])
            old_rendimento = parse_float(row[3])
            new_rendimento = round(old_rendimento + rendimento, 2)
            total = round(aporte + new_rendimento, 2)

            row_index = i + 1
            worksheet.update(f"D{row_index}:E{row_index}", [[new_rendimento, total]])

            return {
                "mes": mes_atual,
                "asset": asset,
                "rendimento": new_rendimento,
                "total_acumulado": total,
                "updated": True
            }

    # New month or new asset
    worksheet.append_row([mes_atual, asset, 0, rendimento, rendimento])

    return {
        "mes": mes_atual,
        "asset": asset,
        "rendimento": rendimento,
        "total_acumulado": rendimento,
        "updated": False
    }