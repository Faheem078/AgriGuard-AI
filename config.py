# ─────────────────────────────────────────────────────────────
# config.py  —  AgriGuard AI
# Single source of truth for all API URLs, keys, and feature flags.
# When a teammate hands you a URL, change it HERE only.
# ─────────────────────────────────────────────────────────────
import os
from dotenv import load_dotenv

try:
	import streamlit as st
except Exception:
	st = None

# Load environment variables from .env file
load_dotenv()


def _secret(key: str, default=None):
	if st is None:
		return default
	try:
		return st.secrets.get(key, default)
	except Exception:
		return default

# ── API Keys ──────────────────────────────────────────
HF_TOKEN            = os.environ.get("HF_TOKEN") or _secret("HF_TOKEN")
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY") or _secret("OPENWEATHER_API_KEY")

GROQ_API_KEY        = os.environ.get("GROQ_API_KEY") or _secret("GROQ_API_KEY")

# ── Feature Flags ─────────────────────────────────────────────
# Set to True once the corresponding module is live
USE_REAL_VISION_MODEL   = True   # M1 — use the live HuggingFace vision model
USE_REAL_FLOWISE_AGENT  = True   # M4 — flip when Flowise URL is confirmed
USE_REAL_WEATHER_API    = True   # flip when OpenWeatherMap key is added

# ── M1: Vision Model (HuggingFace) ────────────────────────────
VISION_MODEL_ID = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"        # original crop disease dataset/model

# ── Weather: OpenWeatherMap ────────────────────────────────────
# Use Lahore so the live weather represents Punjab in the UI, chatbot context, and reports.
WEATHER_CITY         = "Lahore"
WEATHER_COUNTRY      = "PK"
WEATHER_REGION_LABEL = "Punjab, Pakistan"
# ── Groq Chatbot ──────────────────────────────────────────────
USE_REAL_GROQ_CHATBOT = True   # False = mock replies, True = live Groq Llama 3
