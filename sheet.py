import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import json
import os
from config import CREDEDENTIALS_FILE, SPREADSHEET_ID, INVESTMENT_CATEGORY

BRAZIL_TZ = pytz.timezone("America/Sao_Paulo")
# Permissons 

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# Creating the worksheet
def get_worksheet():
    google_credentials = os.getenv("GOOGLE_CREDENTIALS")

    if google_credentials:
        # Railway — lê as credenciais da variável de ambiente
        creds_dict = json.loads(google_credentials)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
    else:
        # Codespace — lê do arquivo local
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
    worksheet = get_worksheet()
    now = datetime.now(BRAZIL_TZ)
    tipo = "Investimento" if category.lower() == INVESTMENT_CATEGORY.lower() else "Gasto"

    row = [
        now.strftime("%d/%m/%Y"),  # Date
        now.strftime("%H:%M"),     # Hour
        value,                     #
        category.capitalize(),     # Category
        tipo,                      # Investment or spent
    ]

    worksheet.append_row(row)

# Returns all costs from the month (withouth investments)
def get_monthly_expenses() -> float:
    worksheet = get_worksheet()
    records = worksheet.get_all_records()

    total = sum(
        float(row["Valor"])
        for row in records
        if row["Tipo"] == "Gasto"
    )

    return total