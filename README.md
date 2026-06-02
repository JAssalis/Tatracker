# TatáTracker

A personal finance Telegram bot that logs expenses and investments to Google Sheets. Inspired by my sister, who is more financially disciplined than anyone I know.

## Features

- Log expenses by sending `amount category` (e.g. `50 Almoco`)
- Log investments using `Investimentos` as category
- Register installment purchases split across future months
- Track stock purchases with automatic average price calculation
- Track dividends per ticker
- Track multiple fixed income assets with monthly deposits and yields
- Monthly spending goal read dynamically from the spreadsheet
- Fuzzy matching for categories, tickers and fixed income asset names
- Auto-updating dashboard with charts via Google Apps Script
- Single-user security filter by Telegram chat ID

## Commands

| Command | Description | Example |
|---|---|---|
| `value category` | Log an expense | `50 Almoco` |
| `value Investimentos` | Log a direct investment | `1000 Investimentos` |
| `/parcelar value installments category` | Log installment purchase | `/parcelar 300 3 Eletronico` |
| `/compra ticker quantity price` | Log stock purchase | `/compra BBAS3 3 19.50` |
| `/dividendo ticker value` | Log dividend received | `/dividendo BBAS3 0.30` |
| `/aporte value asset` | Log fixed income deposit | `/aporte 1000 Tesouro Selic` |
| `/rendimento value asset` | Log fixed income yield | `/rendimento 45.30 Tesouro Selic` |
| `/carteira` | View investment portfolio | |
| `/resumo` | View monthly spending summary | |
| `/ajuda` | Show usage instructions | |

## Spreadsheet Structure

| Sheet | Purpose |
|---|---|
| `YYYY-MM` | Monthly expenses and investments |
| `investimentos` | Stock positions with average price and dividends |
| `renda_fixa` | Fixed income assets by month |
| `config` | Dynamic settings (monthly goal) |
| `dashboard` | Auto-updated expenses dashboard |
| `dashboard_investimentos` | Auto-updated investments dashboard |

## Stack

Python 3.12, aiogram 3.x, gspread, oauth2client, rapidfuzz, Google Sheets, Google Apps Script.

## Files

**main.py** — entry point. **config.py** — environment variables. **handlers.py** — Telegram message handlers. **filters.py** — single user security filter. **sheet.py** — Google Sheets integration. **investments.py** — investment logic. **categories.py** — fuzzy matching for categories and assets.

## Environment Variables

| Variable | Description |
|---|---|
| `TELEGRAM_TOKEN` | Bot token from BotFather |
| `SPREADSHEET_ID` | Google Sheets document ID |
| `ALLOWED_CHAT_ID` | Your Telegram user ID |
| `MONTHLY_GOAL` | Fallback monthly spending goal |
| `GOOGLE_CREDENTIALS` | Google service account JSON |
