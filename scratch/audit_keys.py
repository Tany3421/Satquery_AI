import re
from pathlib import Path

html = Path("frontend/index.html").read_text(encoding="utf-8")
i18n_code = Path("frontend/i18n.js").read_text(encoding="utf-8")

keys = set(re.findall(r'data-i18n(?:-placeholder|-title)?="([^"]+)"', html))
print(f"Total keys in index.html: {len(keys)}")
missing = [k for k in sorted(keys) if f'"{k}"' not in i18n_code and f'{k}:' not in i18n_code]
print(f"Missing from KEY_ALIASES: {missing}")
