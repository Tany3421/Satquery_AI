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

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
FALLBACK_MODELS = [GEMINI_MODEL, "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.1-flash-lite"]



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
    cleaned = raw_text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: find first '{' and last '}'
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start:end+1])
            except Exception:
                pass
        raise EngineError(f"Model returned a non-JSON response: {raw_text[:200]}")


import urllib.parse
import urllib.request

try:
    from PIL import ExifTags, Image
    has_pillow = True
except ImportError:
    has_pillow = False


def _extract_exif_gps(image_bytes: bytes) -> dict | None:
    """Extract embedded EXIF GPS tags from satellite / drone photo bytes."""
    if not has_pillow:
        return None
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            exif = img._getexif()
            if not exif:
                return None
            gps_info = {}
            for tag_id, value in exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                if tag_name == "GPSInfo":
                    for key in value:
                        sub_tag = ExifTags.GPSTAGS.get(key, key)
                        gps_info[sub_tag] = value[key]

            if "GPSLatitude" in gps_info and "GPSLongitude" in gps_info:
                def _to_deg(val):
                    return float(val[0]) + (float(val[1]) / 60.0) + (float(val[2]) / 3600.0)

                lat = _to_deg(gps_info["GPSLatitude"])
                if gps_info.get("GPSLatitudeRef") == "S":
                    lat = -lat
                lng = _to_deg(gps_info["GPSLongitude"])
                if gps_info.get("GPSLongitudeRef") == "W":
                    lng = -lng

                return {
                    "lat": round(lat, 6),
                    "lng": round(lng, 6),
                    "location_name": "Embedded Satellite EXIF GPS",
                    "bounding_box": [round(lat - 0.02, 6), round(lng - 0.02, 6), round(lat + 0.02, 6), round(lng + 0.02, 6)],
                    "source": "EXIF GPS (Exact Metadata)"
                }
    except Exception:
        pass
    return None


def _resolve_location_coordinates(location_name: str, question: str, answer_text: str = "") -> dict | None:
    """Query OpenStreetMap Nominatim for exact real-world latitude, longitude, and bounding box."""
    search_query = (location_name or "").strip()
    
    # Extract place mentions if location_name is generic
    combined_text = f"{location_name or ''} {question} {answer_text}".lower()
    
    # Priority region keywords
    known_places = [
        "nepal", "kathmandu", "pokhara", "everest", "annapurna",
        "badrinath", "kedarnath", "uttarakhand", "himachal", "ladakh", "sikkim",
        "kochi", "mumbai", "delhi", "bengaluru", "chennai", "kolkata", "hyderabad",
        "sundarbans", "western ghats", "himalayas", "ganga", "yamuna"
    ]
    
    for place in known_places:
        if place in combined_text:
            search_query = place.title()
            break

    if not search_query or search_query.lower() in ("unknown region", "unknown", "none", "n/a"):
        for word in ["in ", "near ", "at ", "around ", "of "]:
            if word in question.lower():
                part = question.lower().split(word, 1)[1].split("?")[0].split(".")[0].strip()
                if len(part) > 3 and not part.startswith("this"):
                    search_query = part.title()
                    break

    if not search_query or len(search_query) < 2:
        return None

    try:
        encoded = urllib.parse.quote(search_query)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "SatQuery-AI/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            if data and len(data) > 0:
                item = data[0]
                bb = item.get("boundingbox")
                bbox = None
                if bb and len(bb) == 4:
                    bbox = [float(bb[0]), float(bb[2]), float(bb[1]), float(bb[3])]
                return {
                    "lat": round(float(item["lat"]), 6),
                    "lng": round(float(item["lon"]), 6),
                    "location_name": item.get("display_name", search_query),
                    "bounding_box": bbox,
                    "source": f"Geocoded Region ({search_query})"
                }
    except Exception:
        pass
    return None


def _optimize_image_bytes(image_bytes: bytes, max_dim: int = 800) -> tuple[bytes, str]:
    """Downscale large satellite images to max 800px to dramatically reduce network payload & VLM inference latency."""
    if not has_pillow:
        return image_bytes, "image/jpeg"
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            w, h = img.size
            if max(w, h) <= max_dim:
                return image_bytes, "image/jpeg"

            ratio = max_dim / float(max(w, h))
            new_size = (int(w * ratio), int(h * ratio))

            resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
            if resized_img.mode in ("RGBA", "P"):
                resized_img = resized_img.convert("RGB")

            out = io.BytesIO()
            resized_img.save(out, format="JPEG", quality=80, optimize=True)
            return out.getvalue(), "image/jpeg"
    except Exception:
        return image_bytes, "image/jpeg"


def analyze_image(
    image_b64: str,
    media_type: str,
    question: str,
    mode: str = "general",
    data_source: str = "sentinel2",
    engine_type: str = "auto"
) -> dict:
    """Single-image analysis: question + data source in, structured answer out."""
    if genai_sdk is None:
        raise EngineError(
            "The 'google-genai' package isn't installed. Run: pip install google-genai"
        )

    api_key = _get_api_key()
    system_prompt = prompts.get_system_prompt(mode, data_source)
    raw_bytes = base64.b64decode(image_b64)
    image_bytes, media_type = _optimize_image_bytes(raw_bytes, max_dim=800)

    last_error = None
    preferred_models = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-flash-latest"]
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
                parsed = _parse_json_response(raw_text)
                parsed["engine_used"] = f"Gemini API ({model_name})"
                parsed["data_source"] = data_source

                # Location Precision Resolution Pipeline
                exif_coords = _extract_exif_gps(raw_bytes)
                if exif_coords:
                    parsed["coordinates"] = exif_coords
                else:
                    loc_name = parsed.get("coordinates", {}).get("location_name") if isinstance(parsed.get("coordinates"), dict) else None
                    geocoded = _resolve_location_coordinates(loc_name, question, parsed.get("answer", ""))
                    if geocoded:
                        parsed["coordinates"] = geocoded
                    elif isinstance(parsed.get("coordinates"), dict) and parsed["coordinates"].get("lat") is not None:
                        parsed["coordinates"]["source"] = "Estimated Region"

                return parsed
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


def run_groq_fast_query(question: str, context: str = "") -> dict:
    """Fast text-only query engine using Groq API with fallback to Gemini."""
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key and not groq_key.startswith("your_"):
        try:
            import httpx
            prompt_input = f"{question}\n\nContext: {context}" if context else question
            resp = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": prompts.FAST_QUERY_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt_input}
                    ],
                    "temperature": 0.3
                },
                timeout=15.0
            )
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                return {
                    "answer": content,
                    "engine_used": "Groq API (llama-3.3-70b-versatile)",
                    "speed": "Ultra-Fast (<500ms)",
                    "status": "success"
                }
        except Exception:
            pass

    # Fallback to Gemini if Groq key missing or request failed
    api_key = _get_api_key()
    prompt_input = f"Question: {question}\nContext: {context}" if context else question
    preferred_models = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-flash-lite-latest"]
    models_to_try = [GEMINI_MODEL] + [m for m in preferred_models if m != GEMINI_MODEL]

    last_error = None
    for model_name in models_to_try:
        for attempt in range(2):
            try:
                if genai_sdk == "google-genai":
                    client = genai.Client(api_key=api_key)
                    response = client.models.generate_content(
                        model=model_name,
                        contents=[prompt_input],
                        config=types.GenerateContentConfig(
                            system_instruction=prompts.FAST_QUERY_SYSTEM_PROMPT,
                        ),
                    )
                    raw_text = response.text
                else:
                    genai_legacy.configure(api_key=api_key)
                    model = genai_legacy.GenerativeModel(
                        model_name=model_name,
                        system_instruction=prompts.FAST_QUERY_SYSTEM_PROMPT,
                    )
                    response = model.generate_content(prompt_input)
                    raw_text = response.text
                return {
                    "answer": raw_text,
                    "engine_used": f"Gemini API ({model_name})",
                    "speed": "Fast",
                    "status": "success"
                }
            except Exception as exc:
                last_error = exc
                err_str = str(exc)
                if "503" in err_str or "UNAVAILABLE" in err_str:
                    import time
                    time.sleep(1)
                    continue
                if "404" in err_str or "NOT_FOUND" in err_str:
                    break

    raise EngineError(f"Fast query failed across all models. Last error: {last_error}")


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

    raw_before = base64.b64decode(before_b64)
    raw_after = base64.b64decode(after_b64)
    before_bytes, before_media_type = _optimize_image_bytes(raw_before, max_dim=1024)
    after_bytes, after_media_type = _optimize_image_bytes(raw_after, max_dim=1024)
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


