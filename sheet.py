import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import json
import os
import logging
from config import CREDENTIALS_FILE, SPREADSHEET_ID, INVESTMENT_CATEGORY, MONTHLY_GOAL

BRAZIL_TZ = pytz.timezone("America/Sao_Paulo")

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def parse_float(value) -> float:
    """Converts string to float handling BR decimal separator."""
    return float(str(value).replace(",", ".")) if value else 0.0


def get_worksheet():
    """Authenticates and returns the current month worksheet."""
    google_credentials = os.getenv("GOOGLE_CREDENTIALS")

    if google_credentials:
        creds_dict = json.loads(google_credentials)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)

    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    sheet_name = datetime.now(BRAZIL_TZ).strftime("%Y-%m")

    try:
        worksheet = spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=5)
        worksheet.append_row(["Data", "Hora", "Valor", "Categoria", "Tipo"])

    return worksheet


def save_expense(value: float, category: str) -> None:
    """Saves an expense or investment to the spreadsheet."""
    worksheet = get_worksheet()
    now = datetime.now(BRAZIL_TZ)
    logging.info(f"DEBUG categoria: '{category}' | INVESTMENT_CATEGORY: '{INVESTMENT_CATEGORY}'")
    tipo = "Investimento" if category.lower() == INVESTMENT_CATEGORY.lower() else "Gasto"

    row = [
        now.strftime("%d/%m/%Y"),
        now.strftime("%H:%M"),
        value,
        category.capitalize(),
        tipo,
    ]

    worksheet.append_row(row)


def get_monthly_expenses() -> float:
    """Returns total expenses for the current month (excludes investments)."""
    worksheet = get_worksheet()
    records = worksheet.get_all_values()

    total = 0.0
    for i, row in enumerate(records):
        if i == 0:
            continue
        if row[4] == "Gasto":
            try:
                total += parse_float(row[2])
            except ValueError:
                continue

    return total


def get_monthly_goal() -> float:
    """Reads monthly goal from config sheet."""
    try:
        google_credentials = os.getenv("GOOGLE_CREDENTIALS")

        if google_credentials:
            creds_dict = json.loads(google_credentials)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)

        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        config_sheet = spreadsheet.worksheet("config")
        all_values = config_sheet.get_all_values()

        for row in all_values[1:]:
            if str(row[0]).lower() == "monthly_goal":
                return parse_float(row[1])

    except Exception as e:
        logging.warning(f"Error reading goal from spreadsheet: {e}. Using default.")

    return MONTHLY_GOAL


def get_summary() -> dict:
    """Returns a summary dict of current month expenses."""
    worksheet = get_worksheet()
    all_values = worksheet.get_all_values()

    meta = get_monthly_goal()
    categorias = {}
    total_gastos = 0.0
    total_investimentos = 0.0

    for i, row in enumerate(all_values):
        if i == 0:
            continue
        if len(row) < 5:
            continue

        valor = parse_float(row[2])
        categoria = row[3]
        tipo = row[4]

        if tipo == "Gasto":
            total_gastos += valor
            categorias[categoria] = categorias.get(categoria, 0) + valor
        elif tipo == "Investimento":
            total_investimentos += valor

    ranking = sorted(categorias.items(), key=lambda x: x[1], reverse=True)
    ranking_texto = "\n".join(
        f"  {i+1}. {cat}: R$ {val:.2f}"
        for i, (cat, val) in enumerate(ranking[:5])
    )

    percentual = (total_gastos / meta * 100) if meta > 0 else 0
    saldo = meta - total_gastos
    mes = datetime.now(BRAZIL_TZ).strftime("%Y-%m")

    return {
        "mes": mes,
        "meta": meta,
        "total_gastos": total_gastos,
        "total_investimentos": total_investimentos,
        "saldo": saldo,
        "percentual": percentual,
        "ranking": ranking_texto if ranking_texto else "Nenhum gasto registrado ainda."
    }


def get_known_categories() -> list[str]:
    """Returns list of categories already used in the current month."""
    try:
        worksheet = get_worksheet()
        all_values = worksheet.get_all_values()
        categories = list(set(row[3] for row in all_values[1:] if len(row) > 3 and row[3]))
        return categories
    except Exception:
        return []


def save_installments(value: float, category: str, installments: int) -> list[str]:
    """Saves installment purchases across future months."""
    from dateutil.relativedelta import relativedelta

    installment_value = round(value / installments, 2)
    months_recorded = []

    google_credentials = os.getenv("GOOGLE_CREDENTIALS")
    if google_credentials:
        creds_dict = json.loads(google_credentials)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)

    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    now = datetime.now(BRAZIL_TZ)

    for i in range(installments):
        target_date = now + relativedelta(months=i)
        sheet_name = target_date.strftime("%Y-%m")

        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=5)
            worksheet.append_row(["Data", "Hora", "Valor", "Categoria", "Tipo"])

        row = [
            target_date.strftime("%d/%m/%Y"),
            now.strftime("%H:%M"),
            installment_value,
            category,
            "Gasto",
        ]
        worksheet.append_row(row)
        months_recorded.append(sheet_name)

    return months_recorded