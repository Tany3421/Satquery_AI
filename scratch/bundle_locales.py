"""
scratch/bundle_locales.py
Bundles all 10 locale JSONs into frontend/locales_bundle.js for zero-latency, 
offline-first, and file:// compatible i18n support.
"""
import json
from pathlib import Path

LOCALES_DIR = Path(r"d:\Nakshatra\satquery-ai\frontend\locales")
BUNDLE_FILE = Path(r"d:\Nakshatra\satquery-ai\frontend\locales_bundle.js")

bundle = {}
for json_file in LOCALES_DIR.glob("*.json"):
    lang = json_file.stem
    bundle[lang] = json.loads(json_file.read_text(encoding="utf-8"))

js_content = f"""// Auto-generated locale bundle for SatQuery AI
window.SATQUERY_LOCALES = {json.dumps(bundle, ensure_ascii=False, indent=2)};
"""

BUNDLE_FILE.write_text(js_content, encoding="utf-8")
print(f"Bundled {len(bundle)} languages into {BUNDLE_FILE}")
