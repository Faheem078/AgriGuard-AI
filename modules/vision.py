import os
import base64
import json
import io
import importlib.util
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

HF_API_TOKEN = os.environ.get("HF_API_TOKEN") or os.environ.get("HF_TOKEN")

from config import USE_REAL_VISION_MODEL, VISION_MODEL_ID

# Defer importing heavy HuggingFace/transformers components until needed


def _torch_is_available() -> bool:
    return importlib.util.find_spec("torch") is not None


USE_REAL_VISION_RUNTIME = USE_REAL_VISION_MODEL and _torch_is_available()

@st.cache_resource(show_spinner=False)
def _load_disease_pipeline():
    """
    Load the disease model once and reuse it across Streamlit reruns.
    This removes dependency on HF router authentication.
    """
    model_name = VISION_MODEL_ID

    if not USE_REAL_VISION_RUNTIME:
        raise RuntimeError(
            "PyTorch is required for the live vision model. Install the packages in requirements.txt and restart the app."
        )
    # Import transformers objects lazily to avoid heavy startup time
    from transformers import pipeline, MobileNetV2ImageProcessor, AutoModelForImageClassification

    if HF_API_TOKEN:
        try:
            processor = MobileNetV2ImageProcessor.from_pretrained(model_name, token=HF_API_TOKEN)
            model = AutoModelForImageClassification.from_pretrained(model_name, token=HF_API_TOKEN)
        except TypeError:
            processor = MobileNetV2ImageProcessor.from_pretrained(model_name, use_auth_token=HF_API_TOKEN)
            model = AutoModelForImageClassification.from_pretrained(model_name, use_auth_token=HF_API_TOKEN)
    else:
        processor = MobileNetV2ImageProcessor.from_pretrained(model_name)
        model = AutoModelForImageClassification.from_pretrained(model_name)

    return pipeline(
        "image-classification",
        model=model,
        feature_extractor=processor,
    )


def image_to_base64(image_file) -> str:
    image_file.seek(0)
    return base64.b64encode(image_file.read()).decode("utf-8")


def _prepare_image(image_file) -> Image.Image:
    """Convert uploader input to RGB PIL image expected by the pipeline."""
    if isinstance(image_file, bytes):
        img = Image.open(io.BytesIO(image_file))
    else:
        image_file.seek(0)
        img = Image.open(image_file)
    return img.convert("RGB")


def _is_likely_plant(img: Image.Image) -> bool:
    """Heuristic to detect whether an image contains plant/leaf content.
    Uses HSV green-pixel ratio when numpy is available, otherwise falls back
    to simple channel means via PIL ImageStat.
    """
    try:
        import numpy as np
        hsv = np.array(img.convert("HSV"))
        if hsv.ndim != 3 or hsv.shape[2] < 3:
            return False
        h = hsv[:, :, 0]
        s = hsv[:, :, 1]
        v = hsv[:, :, 2]
        # green hue roughly between 35-100 (OpenCV/HSL-ish); require some saturation/value
        green_mask = ((h >= 35) & (h <= 100)) & (s >= 40) & (v >= 30)
        green_pct = float(green_mask.mean())
        return green_pct >= 0.03  # require >=3% green-ish pixels
    except Exception:
        from PIL import ImageStat
        stat = ImageStat.Stat(img.convert("RGB"))
        r_mean, g_mean, b_mean = stat.mean
        return (g_mean > r_mean and g_mean > b_mean and g_mean >= 60)


def warmup_vision_model() -> None:
    """Eagerly warm the cached model. Safe to call at app startup."""
    if USE_REAL_VISION_RUNTIME:
        _load_disease_pipeline()


def classify_disease(image_file) -> dict:
    if not USE_REAL_VISION_RUNTIME:
        return _mock_vision_response()
    try:
        img = _prepare_image(image_file)

        # Quick plant detection to avoid misclassifying humans/objects as crop diseases
        try:
            if not _is_likely_plant(img):
                return {
                    "disease_name": "Not a Plant",
                    "confidence": 0.0,
                    "crop_type": "Unknown",
                "severity": "Unknown",
                "error": True,
                "is_plant": False,
                "message": "Image does not appear to contain a plant. Try a close-up photo of a leaf or crop.",
            }

        except Exception:
            # If the heuristic fails, continue to model inference rather than blocking.
            pass

        clf_pipe = _load_disease_pipeline()
        results = clf_pipe(img, top_k=5)

        if not isinstance(results, list) or not results:
            return {
                "disease_name": "Error: empty model response",
                "confidence": 0.0,
                "crop_type": "Unknown",
            "severity": "Unknown",
            "error": True,
            "is_plant": True,
            "message": "Model did not return predictions.",
        }


        top = results[0] if isinstance(results[0], dict) else {}
        label = top.get("label", "Unknown")
        score = float(top.get("score", 0.0) or 0.0)

        if score < 0.30:
            return {
                "disease_name": "Uncertain",
                "confidence": round(score, 2),
                "crop_type": "Unknown",
                "severity": "N/A",
                "error": True,
                "is_plant": True,
                "message": "Could not confidently identify a plant disease. Please upload a clearer, closer photo.",
            }


        return {
            "disease_name": label,
            "confidence": round(score, 2),
            "crop_type": _extract_crop(label),
            "severity": _infer_severity(score),
            "error": False,
            "message": "",
        }
    except RuntimeError as e:
        if "PyTorch" in str(e) or "torch" in str(e).lower():
            mock = _mock_vision_response()
            mock["error"] = True
            mock["message"] = str(e)
            mock["disease_name"] = "Vision model unavailable"
            mock["confidence"] = 0.0
            mock["crop_type"] = "Unknown"
            mock["severity"] = "Unknown"
            mock["is_plant"] = True
            return mock

        raise
    except Exception as e:
        return {
            "disease_name": f"Error: {e}",
            "confidence": 0.0,
            "crop_type": "Unknown",
            "severity": "Unknown",
            "error": True,
            "is_plant": True,
            "message": str(e),
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
