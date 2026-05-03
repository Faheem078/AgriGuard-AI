# ─────────────────────────────────────────────────────────────
# config.py  —  AgriGuard AI
# Single source of truth for all API URLs, keys, and feature flags.
# When a teammate hands you a URL, change it HERE only.
# ─────────────────────────────────────────────────────────────
import os

# ── API Keys ──────────────────────────────────────────
HF_TOKEN           = os.environ.get("HF_TOKEN", "")
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
GROQ_API_KEY       = os.environ.get("GROQ_API_KEY", "")

# ── Feature Flags ─────────────────────────────────────────────
# Set to True once the corresponding module is live
USE_REAL_VISION_MODEL   = True   # M1 — flip when HuggingFace model is ready
USE_REAL_FLOWISE_AGENT  = True   # M4 — flip when Flowise URL is confirmed
USE_REAL_WEATHER_API    = True   # flip when OpenWeatherMap key is added

# ── M1: Vision Model (HuggingFace) ────────────────────────────
VISION_MODEL_ID = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"        # e.g. "google/vit-base-patch16-224"

# ── Weather: OpenWeatherMap ────────────────────────────────────
WEATHER_CITY        = "Karachi"
WEATHER_COUNTRY     = "PK"
# ── Groq Chatbot ──────────────────────────────────────────────
USE_REAL_GROQ_CHATBOT = True   # False = mock replies, True = live Groq Llama 3
