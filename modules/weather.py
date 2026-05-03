# ─────────────────────────────────────────────────────────────
# modules/weather.py  —  OpenWeatherMap Integration
# ─────────────────────────────────────────────────────────────

import json
import os
from dotenv import load_dotenv
import requests
from config import USE_REAL_WEATHER_API, WEATHER_CITY, WEATHER_COUNTRY

load_dotenv()
OPENWEATHER_API_KEY=os.getenv("OPENWEATHER_API_KEY")

def get_weather_context() -> dict:
    """
    Returns: { condition, humidity_pct, rain_expected, advice, temperature_c }
    """
    if not USE_REAL_WEATHER_API:
        return _mock_weather_response()

    return _call_openweather()


def _call_openweather() -> dict:
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={WEATHER_CITY},{WEATHER_COUNTRY}&appid={OPENWEATHER_API_KEY}&units=metric"
    )
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        humidity     = data["main"]["humidity"]
        temp         = round(data["main"]["temp"], 1)
        condition    = data["weather"][0]["main"]
        rain_expected = "rain" in condition.lower()

        advice = (
            "Rain expected — avoid spraying today, reschedule to tomorrow morning."
            if rain_expected else
            f"No rain forecast. Humidity at {humidity}%. Safe to apply treatment before 6 PM."
        )

        return {
            "condition":    condition,
            "humidity_pct": humidity,
            "rain_expected": rain_expected,
            "advice":       advice,
            "temperature_c": temp
        }
    except Exception as e:
        return {"condition": f"Error: {e}", "humidity_pct": 0,
                "rain_expected": False, "advice": "Weather unavailable.", "temperature_c": 0}


def _mock_weather_response() -> dict:
    with open("mock/mock_data.json") as f:
        return json.load(f)["weather"]