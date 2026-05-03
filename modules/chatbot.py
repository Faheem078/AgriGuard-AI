import os

from groq import Groq


CHATBOT_SYSTEM_PROMPT = """
You are AgriGuard AI Assistant, a friendly agricultural advisor for smallholder farmers in Pakistan.

Your job is to help with crop diseases, symptoms, causes, treatments, and prevention.
Keep answers practical, clear, and concise.
If the user asks in Urdu, respond naturally in Urdu.

Always structure advice clearly and end with a safety reminder if chemicals are mentioned.
"""


def _get_groq_client():
    api_key = os.environ.get("GROQ_api_key") or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_api_key not found in environment variables.")
    return Groq(api_key=api_key)


def get_chatbot_response(
    user_message: str,
    chat_history: list[dict],
    disease_context: str | None = None,
    weather_context: dict | None = None,
    language_code: str = "en",
) -> str:
    client = _get_groq_client()

    context_block = ""
    if disease_context:
        context_block += f"\nCurrent diagnosis: {disease_context}."
    if weather_context:
        context_block += (
            f"\nWeather: {weather_context.get('condition', 'N/A')}, "
            f"humidity {weather_context.get('humidity_pct', 'N/A')}%, "
            f"temp {weather_context.get('temperature_c', 'N/A')}°C, "
            f"rain expected {weather_context.get('rain_expected', False)}."
        )
    if language_code and language_code != "en":
        context_block += f"\nReply in the user's selected language code: {language_code}."

    messages = [{"role": "system", "content": CHATBOT_SYSTEM_PROMPT + context_block}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=600,
        temperature=0.6,
    )
    return response.choices[0].message.content.strip()


def get_mock_chatbot_response(user_message: str) -> str:
    message = user_message.lower()
    if any(word in message for word in ["blight", "spot", "fungus", "mold"]):
        return (
            "For fungal diseases like blight or leaf spot, remove infected leaves, "
            "avoid overhead watering, and use a suitable fungicide as directed on the label."
        )
    if any(word in message for word in ["yellow", "curl", "virus", "mosaic"]):
        return (
            "Yellowing or leaf curl can be linked to viral infection or pest pressure. "
            "Check for whiteflies, remove badly affected plants, and prevent spread."
        )
    return (
        "I can help with crop diseases, treatment timing, prevention, and weather-aware spraying advice."
    )


QUICK_QUESTIONS = [
    "What are the symptoms of tomato late blight?",
    "How do I stop fungal disease in rainy weather?",
    "Which spray is safe for potato blight?",
    "Why are my crop leaves turning yellow?",
    "میری فصل کے پتے پیلے ہو رہے ہیں، کیا کروں؟",
    "How often should I spray fungicide?",
] 
