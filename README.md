# Tatrácker

A personal finance Telegram bot that logs expenses and investments to Google Sheets.

## Features

- Log expenses by sending `amount category` (e.g. `50 Lunch`)
- Log investments with the same format using `Investimentos` as category
- Register installment purchases split across future months
- Track stock purchases with automatic average price calculation
- Track dividends and fixed income yields
- Monthly spending goal with percentage tracking
- Fuzzy category matching to handle typos
- Auto-updating dashboard via Google Apps Script

## Commands

| Command | Description | Example |
|---|---|---|
| `amount category` | Log an expense | `50 Lunch` |
| `/parcelar value installments category` | Log installment purchase | `/parcelar 300 3 Electronics` |
| `/compra ticker quantity price` | Log stock purchase | `/compra BBAS3 3 19.50` |
| `/dividendo ticker value` | Log dividend received | `/dividendo BBAS3 0.30` |
| `/rendimento value` | Log fixed income yield | `/rendimento 45.30` |
| `/carteira` | View investment portfolio | |
| `/resumo` | View monthly spending summary | |
| `/ajuda` | Show usage instructions | |

## Stack

- Python 3.12
- aiogram 3.x
- gspread + oauth2client
- Google Sheets as database
- Railway for hosting

## Project Structure
```
├── main.py           # Entry point
├── config.py         # Environment variables
├── handlers.py       # Telegram message handlers
├── filters.py        # Security filters
├── sheet.py          # Google Sheets integration
├── investments.py    # Investment logic
├── categories.py     # Fuzzy category matching
└── requirements.txt
```



## Environment Variables

| Variable | Description |
|---|---|
| `TELEGRAM_TOKEN` | Bot token from BotFather |
| `SPREADSHEET_ID` | Google Sheets document ID |
| `ALLOWED_CHAT_ID` | Your Telegram user ID |
| `MONTHLY_GOAL` | Fallback monthly spending goal |
| `GOOGLE_CREDENTIALS` | Google service account JSON |
