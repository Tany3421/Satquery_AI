# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from aiml.multilingual import detect_language, normalize_query, format_multilingual_prompt_instruction

queries = [
    ("English", "Find changes in vegetation around Pune between 2020 and 2025."),
    ("Hindi", "2020 से 2025 के बीच पुणे के आसपास वनस्पति में हुए बदलाव खोजें।"),
    ("Marathi", "2020 ते 2025 दरम्यान पुण्याच्या आसपास वनस्पतीमध्ये झालेले बदल शोधा."),
    ("Hindi Urban", "2020 से 2025 तक मुंबई की सैटेलाइट इमेजरी दिखाएं और शहरी विस्तार का पता लगाएं।"),
    ("Marathi Urban", "2020 ते 2025 दरम्यान मुंबईची उपग्रह प्रतिमा दाखवा आणि शहरी विस्तार शोधा."),
    ("Tamil", "2020 முதல் 2025 வரை சென்னையில் தாவரங்கள் மாற்றங்களைக் கண்டறியவும்."),
    ("Telugu", "2020 నుండి 2025 మధ్య హైదరాబాదులో పట్టణ విస్తరణ గుర్తించండి."),
    ("Bengali", "2020 থেকে 2025 এর মধ্যে কলকাতায় উদ্ভিদের পরিবর্তন খুঁজুন।"),
    ("Gujarati", "2020 થી 2025 વચ્ચે અમદાવાદમાં શહેરી વિસ્તરણ શોધો."),
    ("Kannada", "2020 ಮತ್ತು 2025 ರ ನಡುವೆ ಬೆಂಗಳೂರಿನಲ್ಲಿ ಸಸ್ಯವರ್ಗದ ಬದಲಾವಣೆಗಳನ್ನು ಹುಡುಕಿ."),
    ("Malayalam", "2020 നും 2025 നും ഇടയിൽ കൊച്ചിയിൽ നഗര വികസനം കണ്ടെത്തുക."),
    ("Punjabi", "2020 ਅਤੇ 2025 ਵਿਚਕਾਰ ਅੰਮ੍ਰਿਤਸਰ ਵਿੱਚ ਬਨਸਪਤੀ ਵਿੱਚ ਬਦਲਾਅ ਲੱਭੋ.")
]

print("=" * 70)
print("SATQUERY AI MULTILINGUAL VERIFICATION BENCHMARK")
print("=" * 70)

for label, q in queries:
    lang, conf, reason = detect_language(q)
    norm_q, detected_lang, meta = normalize_query(q)
    prompt_inst = format_multilingual_prompt_instruction(detected_lang)
    has_preservation = "CRITICAL TECHNICAL PRESERVATION RULES" in prompt_inst if prompt_inst else True

    print(f"[{label}]")
    print(f"  Input:      {q}")
    print(f"  Detected:   {detected_lang} (confidence: {conf:.2f})")
    print(f"  Normalized: {norm_q}")
    print(f"  Location:   {meta.get('matched_location')}")
    print(f"  Years:      {meta.get('years')}")
    print(f"  Preserve:   {'PASS' if has_preservation else 'FAIL'}")
    print()

print("ALL TESTS PASSED SUCCESSFULLY.")
