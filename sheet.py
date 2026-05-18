import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz
import json
import os
import logging
from config import CREDENTIALS_FILE, SPREADSHEET_ID, INVESTMENT_CATEGORY, MONTHLY_GOAL

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

def get_monthly_goal() -> float:
    try:
        creds_dict_str = os.getenv("GOOGLE_CREDENTIALS")

        if creds_dict_str:
            creds_dict = json.loads(creds_dict_str)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)

        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        config_sheet = spreadsheet.worksheet("config")
        records = config_sheet.get_all_records()

        for row in records:
            if str(row["Chave"]).lower() == "monthly_goal":
                return float(row["Valor"])

    except Exception as e:
        logging.warning(f"Erro ao ler meta da planilha: {e}. Usando valor padrão.")

    return MONTHLY_GOAL

def get_summary() -> dict:
    """Retorna um dicionário com o resumo do mês atual."""
    worksheet = get_worksheet()
    records = worksheet.get_all_records()

    meta = get_monthly_goal()
    categorias = {}
    total_gastos = 0.0
    total_investimentos = 0.0

    for row in records:
        valor = float(row["Valor"])
        categoria = row["Categoria"]
        tipo = row["Tipo"]

        if tipo == "Gasto":
            total_gastos += valor
            categorias[categoria] = categorias.get(categoria, 0) + valor
        elif tipo == "Investimento":
            total_investimentos += valor

    # Ordena categorias por valor
    ranking = sorted(categorias.items(), key=lambda x: x[1], reverse=True)
    ranking_texto = "\n".join(
        f"  {i+1}. {cat}: R$ {val:.2f}"
        for i, (cat, val) in enumerate(ranking[:5])  # top 5
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