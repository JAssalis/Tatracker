from rapidfuzz import process, fuzz

# Know categories
KNOWN_CATEGORIES = [
    "Almoço",
    "Lanche",
    "Mercado",
    "Transporte",
    "Suplementos",
    "Cosméticos",
    "Lazer",
    "Assinaturas",
    "Investimentos",
]

# Similiarity threshold for corrections
SIMILARITY_THRESHOLD = 75

# Normalizes categories that are comparing with the know ones
def normalize_category(input_category: str, extra_categories: list[str] = []) -> tuple[str, bool]:
    all_categories = list(set(KNOWN_CATEGORIES + extra_categories))

    # Verifies if its an investment
    if input_category.lower() in ["investimento", "investimentos"]:
        return "Investimentos", False

    result = process.extractOne(
        input_category,
        all_categories,
        scorer=fuzz.WRatio,
        score_cutoff=SIMILARITY_THRESHOLD
    )

    if result:
        best_match, score, _ = result
        was_corrected = best_match.lower() != input_category.lower()
        return best_match, was_corrected
    
    return input_category.capitalize(), False