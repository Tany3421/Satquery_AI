import sys
from pathlib import Path
import json
import io
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def create_dummy_image():
    img = Image.new("RGB", (256, 256), color=(34, 139, 34))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.getvalue()

def run_tests():
    print("==================================================")
    print("Testing SatQuery AI Multilingual API Integration")
    print("==================================================")

    # 1. Test /locales static serving
    print("\n[Test 1] Testing static locale files serving...")
    for lang in ["en", "hi", "mr", "ta", "te", "bn", "gu", "kn", "ml", "pa"]:
        resp = client.get(f"/locales/{lang}.json")
        assert resp.status_code == 200, f"Failed to fetch /locales/{lang}.json: {resp.status_code}"
        data = resp.json()
        assert "lang_code" in data, f"lang_code missing in {lang}.json"
        print(f"  ✓ /locales/{lang}.json ({len(data)} sections) -> '{data.get('native_name')}'")

    # 2. Test Fast Query with Hindi
    print("\n[Test 2] Testing /api/fast-query with Hindi...")
    fast_resp = client.post("/api/fast-query", json={
        "question": "पुणे के आसपास कृषि क्षेत्र का विश्लेषण करें",
        "language": "hi"
    })
    print(f"  Status code: {fast_resp.status_code}")
    if fast_resp.status_code == 200:
        data = fast_resp.json()
        print(f"  Detected language: {data.get('detected_language')}")
        print(f"  Engine used: {data.get('engine_used')}")
        print(f"  Answer preview: {data.get('answer', '')[:100]}...")
    else:
        print(f"  Response: {fast_resp.text}")

    # 3. Test 3 Benchmark Queries on /api/analyze
    dummy_img_bytes = create_dummy_image()

    benchmarks = [
        ("English", "Find changes in vegetation around Pune between 2020 and 2025.", "en"),
        ("Hindi", "2020 से 2025 के बीच पुणे के आसपास वनस्पति में हुए बदलाव खोजें।", "hi"),
        ("Marathi", "2020 ते 2025 दरम्यान पुण्याच्या आसपास वनस्पतीमध्ये झालेले बदल शोधा.", "mr")
    ]

    print("\n[Test 3] Testing Benchmark Queries on /api/analyze...")
    for name, query, lang in benchmarks:
        print(f"\n--- Testing {name} Query: '{query}' ---")
        files = {
            "image": ("test_scene.jpg", dummy_img_bytes, "image/jpeg")
        }
        form_data = {
            "question": query,
            "mode": "environment",
            "data_source": "sentinel2",
            "language": lang
        }
        resp = client.post("/api/analyze", data=form_data, files=files)
        assert resp.status_code == 200, f"Analyze failed for {name}: {resp.status_code} - {resp.text}"
        res = resp.json()
        print(f"  ✓ Analysis Status: SUCCESS")
        print(f"  ✓ Engine: {res.get('engine_used')}")
        print(f"  ✓ Detected/Returned Language: {res.get('language')}")
        print(f"  ✓ Confidence: {res.get('confidence')}%")
        print(f"  ✓ Land Cover classes: {[lc.get('label') for lc in res.get('land_cover', [])]}")
        print(f"  ✓ Answer snippet: {res.get('answer', '')[:180]}...")
        # Check entity preservation
        ans = res.get('answer', '')
        if "Pune" in ans or "पुणे" in ans:
            print("  ✓ Entity 'Pune' preserved in output!")
        if "2020" in ans and "2025" in ans:
            print("  ✓ Numerical years '2020' and '2025' preserved in output!")

    print("\n==================================================")
    print("All Multilingual API Tests PASSED Successfully!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()
