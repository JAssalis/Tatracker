import os

# Tokens and IDs
TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
SPREADSHEET_ID: str = os.getenv("SPREADSHEET_ID", "")
CREDENTIALS_FILE: str = "credentials.json"

# Safety measures
ALLOWED_CHAT_ID: int = int(os.getenv("ALLOWED_CHAT_ID", "0"))

# Metrics to follow
MONTHLY_GOAL: float = float(os.getenv("MONTHLY_GOAL", "600"))

# Investment category: doesn't affect the monthly budget
INVESTMENT_CATEGORY: str = "Investimentos"


# Confirming all variables
def validate_config() -> None:
    missing = []
    if not TELEGRAM_TOKEN:
        missing.append("TELEGRAM_TOKEN")
    if not SPREADSHEET_ID:
        missing.append("SPREADSHEET_ID")
    if not ALLOWED_CHAT_ID:
        missing.append("ALLOWED_CHAT_ID")
    if missing:
        raise EnvironmentError(
            f"The following variables are missing: {', '.join(missing)}"
        )
