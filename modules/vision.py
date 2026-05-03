import os
import base64
import json
import io
import requests
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

HF_API_TOKEN = os.environ.get("HF_API_TOKEN") or os.environ.get("HF_TOKEN")

from config import USE_REAL_VISION_MODEL, VISION_MODEL_ID

# ── Validation model — checks if image is actually a plant ──────────────────
VALIDATION_MODEL = "google/vit-base-patch16-224"

PLANT_KEYWORDS = [
    "plant", "leaf", "flower", "tree", "crop", "vegetable",
    "fruit", "herb", "grass", "shrub", "weed", "fungus",
    "tomato", "potato", "wheat", "rice", "corn", "maize",
    "cotton", "chili", "pepper", "strawberry", "grape",
    "peach", "apple", "squash", "garden", "farm", "field",
    "stem", "root", "seed", "petal", "branch", "bush"
]


def image_to_base64(image_file) -> str:
    image_file.seek(0)
    return base64.b64encode(image_file.read()).decode("utf-8")


def _prepare_image_bytes(image_file) -> bytes:
    """Convert any image input to resized JPEG bytes."""
    if isinstance(image_file, bytes):
        img = Image.open(io.BytesIO(image_file))
    else:
        image_file.seek(0)
        img = Image.open(image_file)

    img = img.convert("RGB")
    img = img.resize((224, 224))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()


def _is_plant_image(image_bytes: bytes) -> tuple[bool, str]:
    """
    Use a general image classifier to verify the image
    contains a plant before running disease detection.
    Returns (is_plant, detected_label)
    """
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "image/jpeg"
    }

    api_url = f"https://router.huggingface.co/hf-inference/models/{VALIDATION_MODEL}"

    try:
        response = requests.post(
            api_url,
            headers=headers,
            data=image_bytes,
            timeout=30
        )
        response.raise_for_status()
        results = response.json()

        print("Validation model response:", results)

        # Check top 3 results for any plant-related label
        top_labels = [r.get("label", "").lower() for r in results[:3]]
        top_label_str = ", ".join(top_labels)

        for label in top_labels:
            for keyword in PLANT_KEYWORDS:
                if keyword in label:
                    return True, top_label_str

        return False, top_label_str

    except Exception as e:
        print(f"Validation error: {e}")
        # If validation fails, allow through (fail open)
        return True, "validation unavailable"


def classify_disease(image_file) -> dict:
    if not USE_REAL_VISION_MODEL:
        return _mock_vision_response()
    return _call_huggingface(image_file)


def _call_huggingface(image_file) -> dict:
    # ── Step 1: Prepare image ───────────────────────────────────────────────
    image_bytes = _prepare_image_bytes(image_file)

    # ── Step 2: Validate it is a plant image ────────────────────────────────
    is_plant, detected_label = _is_plant_image(image_bytes)

    if not is_plant:
        return {
            "disease_name": "Not a Plant",
            "confidence":   0.0,
            "crop_type":    "N/A",
            "severity":     "N/A",
            "error":        True,
            "message":      (
                f"⚠️ This image does not appear to be a plant or crop.\n"
                f"Detected: {detected_label}\n\n"
                f"Please upload a clear photo of a plant leaf or crop."
            )
        }

    # ── Step 3: Run plant disease classification ─────────────────────────────
    api_url = f"https://router.huggingface.co/hf-inference/models/{VISION_MODEL_ID}"
    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "image/jpeg"
    }

    try:
        response = requests.post(
            api_url,
            headers=headers,
            data=image_bytes,
            timeout=60
        )
        response.raise_for_status()
        results = response.json()

        print("Disease model raw response:", results)

        top = results[0] if isinstance(results, list) and results else {}
        label = top.get("label", "Unknown")
        score = top.get("score", 0.0)

        # ── Step 4: Extra confidence check ───────────────────────────────────
        # Even if it passed validation, low confidence = uncertain result
        if score < 0.30:
            return {
                "disease_name": "Uncertain",
                "confidence":   round(score, 2),
                "crop_type":    "Unknown",
                "severity":     "N/A",
                "error":        True,
                "message":      (
                    "⚠️ Could not confidently identify a plant disease.\n"
                    "Please upload a clearer, closer photo of the affected leaf."
                )
            }

        return {
            "disease_name": label,
            "confidence":   round(score, 2),
            "crop_type":    _extract_crop(label),
            "severity":     _infer_severity(score),
            "error":        False,
            "message":      ""
        }

    except Exception as e:
        return {
            "disease_name": f"Error: {e}",
            "confidence":   0.0,
            "crop_type":    "Unknown",
            "severity":     "Unknown",
            "error":        True,
            "message":      str(e)
        }


def _extract_crop(label: str) -> str:
    crops = ["Tomato", "Wheat", "Rice", "Maize", "Cotton",
             "Potato", "Chili", "Apple", "Corn", "Grape",
             "Peach", "Pepper", "Strawberry", "Squash"]
    for crop in crops:
        if crop.lower() in label.lower():
            return crop
    return "Unknown Crop"


def _infer_severity(confidence: float) -> str:
    if confidence >= 0.85: return "High"
    if confidence >= 0.60: return "Medium"
    return "Low"


def _mock_vision_response() -> dict:
    with open("mock/mock_data.json") as f:
        return json.load(f)["vision"]