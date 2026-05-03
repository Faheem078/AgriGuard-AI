import os
import requests
import json
import re

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL   = "llama-3.3-70b-versatile"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"

from config import USE_REAL_FLOWISE_AGENT

# ─────────────────────────────────────────────────────────────
# MULTILINGUAL SUPPORT
# ─────────────────────────────────────────────────────────────
SUPPORTED_LANGUAGES = {
    "English": "en",
    "Urdu":    "ur",
    "Hindi":   "hi",
    "Swahili": "sw",
    "French":  "fr",
    "Arabic":  "ar",
}

# ─────────────────────────────────────────────────────────────
# YIELD LOSS TABLES
# ─────────────────────────────────────────────────────────────
YIELD_LOSS_TABLE = {
    "late blight":      {"High": 80,  "Medium": 40, "Low": 15},
    "early blight":     {"High": 45,  "Medium": 25, "Low": 10},
    "bacterial spot":   {"High": 35,  "Medium": 18, "Low": 8},
    "leaf mold":        {"High": 30,  "Medium": 15, "Low": 5},
    "septoria":         {"High": 40,  "Medium": 20, "Low": 8},
    "spider mite":      {"High": 35,  "Medium": 18, "Low": 7},
    "target spot":      {"High": 25,  "Medium": 12, "Low": 5},
    "yellow leaf curl": {"High": 70,  "Medium": 40, "Low": 20},
    "mosaic virus":     {"High": 60,  "Medium": 35, "Low": 15},
    "gray leaf spot":   {"High": 45,  "Medium": 25, "Low": 10},
    "common rust":      {"High": 30,  "Medium": 15, "Low": 5},
    "northern leaf":    {"High": 50,  "Medium": 30, "Low": 12},
    "black rot":        {"High": 70,  "Medium": 40, "Low": 15},
    "powdery mildew":   {"High": 25,  "Medium": 12, "Low": 5},
    "apple scab":       {"High": 60,  "Medium": 35, "Low": 15},
    "citrus greening":  {"High": 100, "Medium": 100,"Low": 80},
    "healthy":          {"High": 0,   "Medium": 0,  "Low": 0},
}

CROP_ECONOMICS = {
    "Tomato":       {"yield_kg_acre": 8000,  "price_pkr_kg": 80},
    "Potato":       {"yield_kg_acre": 10000, "price_pkr_kg": 50},
    "Corn":         {"yield_kg_acre": 4000,  "price_pkr_kg": 45},
    "Maize":        {"yield_kg_acre": 4000,  "price_pkr_kg": 45},
    "Apple":        {"yield_kg_acre": 5000,  "price_pkr_kg": 150},
    "Grape":        {"yield_kg_acre": 4000,  "price_pkr_kg": 200},
    "Pepper":       {"yield_kg_acre": 3000,  "price_pkr_kg": 120},
    "Wheat":        {"yield_kg_acre": 3500,  "price_pkr_kg": 55},
    "Rice":         {"yield_kg_acre": 3000,  "price_pkr_kg": 70},
    "Strawberry":   {"yield_kg_acre": 2500,  "price_pkr_kg": 300},
    "Unknown Crop": {"yield_kg_acre": 4000,  "price_pkr_kg": 80},
}


def estimate_yield_loss(disease_name: str, severity: str,
                        crop_type: str, acres: float = 1.0) -> dict:
    """
    Returns a dict with estimated % loss, kg lost, and PKR impact.
    severity should be 'High', 'Medium', or 'Low'.
    """
    dl = disease_name.lower()
    loss_pct = 15  # sensible default if disease not in table

    for keyword, levels in YIELD_LOSS_TABLE.items():
        if keyword in dl:
            loss_pct = levels.get(severity, levels.get("Medium", 15))
            break

    econ = CROP_ECONOMICS.get(crop_type, CROP_ECONOMICS["Unknown Crop"])
    full_yield_kg = econ["yield_kg_acre"] * acres
    lost_kg       = full_yield_kg * loss_pct / 100
    full_pkr      = full_yield_kg * econ["price_pkr_kg"]
    lost_pkr      = lost_kg * econ["price_pkr_kg"]

    return {
        "loss_pct":      loss_pct,
        "lost_kg":       round(lost_kg, 1),
        "lost_pkr":      round(lost_pkr),
        "full_crop_pkr": round(full_pkr),
        "saved_pkr":     round(full_pkr - lost_pkr),
        "acres":         acres,
        "crop_type":     crop_type,
        "severity":      severity,
    }


# ─────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────
def get_treatment_plan(disease_name: str, weather: dict,
                       language_code: str = "en") -> dict:
    if not USE_REAL_FLOWISE_AGENT:
        return _mock_agent_response()
    return _call_groq(disease_name, weather, language_code)


# ─────────────────────────────────────────────────────────────
# GROQ CALL
# ─────────────────────────────────────────────────────────────
def _call_groq(disease_name: str, weather: dict,
               language_code: str = "en") -> dict:

    # Build language instruction for the prompt
    if language_code == "en":
        lang_instruction = ""
    else:
        lang_names = {v: k for k, v in SUPPORTED_LANGUAGES.items()}
        lang_label = lang_names.get(language_code, language_code)
        lang_instruction = (
            f"IMPORTANT: You must respond entirely in {lang_label}. "
            f"Translate ALL text in your JSON values to {lang_label}. "
            f"Keep only the JSON keys in English.\n\n"
        )

    prompt = f"""{lang_instruction}You are an expert agricultural advisor.
Disease detected: {disease_name}
Weather in Karachi: {weather.get('condition')}, \
humidity {weather.get('humidity_pct')}%, \
rain expected: {weather.get('rain_expected')}.

Respond ONLY in valid JSON with exactly these keys:
treatment, precautions, urgency, rag_source

Do not include any text outside the JSON object.
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 600,
        "temperature": 0.3,
    }

    try:
        resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]

        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())

        return {
            "treatment":   raw,
            "precautions": "",
            "urgency":     "",
            "rag_source":  "Groq Llama 3",
        }
    except Exception as e:
        return {
            "treatment":   f"Error: {e}",
            "precautions": "",
            "urgency":     "",
            "rag_source":  "",
        }


def _mock_agent_response() -> dict:
    with open("mock/mock_data.json") as f:
        return json.load(f)["agent"]