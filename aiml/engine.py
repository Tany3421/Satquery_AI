"""
aiml/engine.py
Thin wrapper around the Gemini vision API. Kept separate from backend/main.py
so the AI/ML person on your team can work in this folder without touching
API/routing code, and so this is the one place to swap in a different model
or add real segmentation/detection later.
"""

import base64
import json
import os
from pathlib import Path

# Automatically load backend/.env if available
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()
except ImportError:
    pass

from . import prompts

# Support google-genai (preferred official SDK) and google-generativeai (fallback)
genai_sdk = None
try:
    from google import genai
    from google.genai import types
    genai_sdk = "google-genai"
except ImportError:
    try:
        import google.generativeai as genai_legacy
        genai_sdk = "google-generativeai"
    except ImportError:
        genai_sdk = None

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
FALLBACK_MODELS = [GEMINI_MODEL, "gemini-flash-latest", "gemini-2.5-flash-lite", "gemini-1.5-flash"]



class EngineError(Exception):
    pass


def _get_api_key() -> str:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise EngineError(
            "GEMINI_API_KEY is not set. Add your Gemini API key to backend/.env "
            "(get one at https://aistudio.google.com/app/apikey)."
        )
    if api_key.startswith("your_") or api_key == "sk-ant-your-key-here" or api_key.startswith("yoAQ."):
        raise EngineError(
            "GEMINI_API_KEY in backend/.env is set to a placeholder key. "
            "Please replace it with your actual Gemini API key from https://aistudio.google.com/app/apikey (keys typically start with AIzaSy...)."
        )
    return api_key



def _parse_json_response(raw_text: str) -> dict:
    if not raw_text:
        raise EngineError("Gemini returned an empty response.")
    cleaned = (
        raw_text.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise EngineError(f"Model returned a non-JSON response: {exc}") from exc


def analyze_image(image_b64: str, media_type: str, question: str, mode: str) -> dict:
    """Single-image analysis: question in, structured answer out."""
    if genai_sdk is None:
        raise EngineError(
            "The 'google-genai' package isn't installed. Run: pip install google-genai"
        )

    api_key = _get_api_key()
    system_prompt = prompts.get_system_prompt(mode)
    image_bytes = base64.b64decode(image_b64)

    last_error = None
    preferred_models = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-flash-lite-latest"]
    models_to_try = [GEMINI_MODEL] + [m for m in preferred_models if m != GEMINI_MODEL]

    for model_name in models_to_try:
        for attempt in range(2):
            try:
                if genai_sdk == "google-genai":
                    client = genai.Client(api_key=api_key)
                    image_part = types.Part.from_bytes(data=image_bytes, mime_type=media_type)
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[image_part, f"Question: {question}"],
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            response_mime_type="application/json",
                        ),
                    )
                    raw_text = response.text
                else:
                    genai_legacy.configure(api_key=api_key)
                    model = genai_legacy.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_prompt,
                        generation_config={"response_mime_type": "application/json"},
                    )
                    response = model.generate_content(
                        [{"mime_type": media_type, "data": image_bytes}, f"Question: {question}"]
                    )
                    raw_text = response.text
                return _parse_json_response(raw_text)
            except EngineError:
                raise
            except Exception as exc:
                last_error = exc
                err_str = str(exc)
                if "503" in err_str or "UNAVAILABLE" in err_str:
                    import time
                    time.sleep(1)
                    continue
                if "404" in err_str or "NOT_FOUND" in err_str:
                    break
                raise EngineError(f"Analysis failed with {model_name}: {exc}") from exc

    raise EngineError(f"Analysis failed across all models. Last error: {last_error}")


def compare_images(
    before_b64: str,
    before_media_type: str,
    after_b64: str,
    after_media_type: str,
    label_before: str = "",
    label_after: str = "",
) -> dict:
    """Two-image change detection / anomaly flagging."""
    if genai_sdk is None:
        raise EngineError(
            "The 'google-genai' package isn't installed. Run: pip install google-genai"
        )

    api_key = _get_api_key()
    label_text = ""
    if label_before or label_after:
        label_text = f"\n\nBEFORE label: {label_before or 'not given'}. AFTER label: {label_after or 'not given'}."

    before_bytes = base64.b64decode(before_b64)
    after_bytes = base64.b64decode(after_b64)
    prompt_text = f"Compare these.{label_text}"

    last_error = None
    preferred_models = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-flash-lite-latest"]
    models_to_try = [GEMINI_MODEL] + [m for m in preferred_models if m != GEMINI_MODEL]

    for model_name in models_to_try:
        for attempt in range(2):
            try:
                if genai_sdk == "google-genai":
                    client = genai.Client(api_key=api_key)
                    contents = [
                        "BEFORE image:",
                        types.Part.from_bytes(data=before_bytes, mime_type=before_media_type),
                        "AFTER image:",
                        types.Part.from_bytes(data=after_bytes, mime_type=after_media_type),
                        prompt_text,
                    ]
                    response = client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=prompts.COMPARISON_SYSTEM_PROMPT,
                            response_mime_type="application/json",
                        ),
                    )
                    raw_text = response.text
                else:
                    genai_legacy.configure(api_key=api_key)
                    model = genai_legacy.GenerativeModel(
                        model_name=model_name,
                        system_instruction=prompts.COMPARISON_SYSTEM_PROMPT,
                        generation_config={"response_mime_type": "application/json"},
                    )
                    contents = [
                        "BEFORE image:",
                        {"mime_type": before_media_type, "data": before_bytes},
                        "AFTER image:",
                        {"mime_type": after_media_type, "data": after_bytes},
                        prompt_text,
                    ]
                    response = model.generate_content(contents)
                    raw_text = response.text
                return _parse_json_response(raw_text)
            except EngineError:
                raise
            except Exception as exc:
                last_error = exc
                err_str = str(exc)
                if "503" in err_str or "UNAVAILABLE" in err_str:
                    import time
                    time.sleep(1)
                    continue
                if "404" in err_str or "NOT_FOUND" in err_str:
                    break
                raise EngineError(f"Comparison failed with {model_name}: {exc}") from exc

    raise EngineError(f"Comparison failed across all models. Last error: {last_error}")


