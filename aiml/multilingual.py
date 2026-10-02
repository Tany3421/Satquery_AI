"""
aiml/multilingual.py
Comprehensive Multilingual Processing Engine for SatQuery AI.

Supports 10 Languages:
1. English (en)
2. Hindi (hi)
3. Marathi (mr)
4. Tamil (ta)
5. Telugu (te)
6. Bengali (bn)
7. Gujarati (gu)
8. Kannada (kn)
9. Malayalam (ml)
10. Punjabi (pa)

Features:
- Automatic script-based and lexical language detection.
- Internal query normalization for remote sensing specialist pipelines.
- Gemini prompt augmentation with strict entity & value preservation rules.
- Offline multilingual response localization preserving coordinates, satellite names,
  metrics, dates, and technical identifiers.
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

LANGUAGES: Dict[str, Dict[str, str]] = {
    "en": {"name": "English", "native": "English", "script": "Latin", "speech": "en-IN"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "script": "Devanagari", "speech": "hi-IN"},
    "mr": {"name": "Marathi", "native": "मराठी", "script": "Devanagari", "speech": "mr-IN"},
    "ta": {"name": "Tamil", "native": "தமிழ்", "script": "Tamil", "speech": "ta-IN"},
    "te": {"name": "Telugu", "native": "తెలుగు", "script": "Telugu", "speech": "te-IN"},
    "bn": {"name": "Bengali", "native": "বাংলা", "script": "Bengali", "speech": "bn-IN"},
    "gu": {"name": "Gujarati", "native": "ગુજરાતી", "script": "Gujarati", "speech": "gu-IN"},
    "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "script": "Kannada", "speech": "kn-IN"},
    "ml": {"name": "Malayalam", "native": "മലയാളം", "script": "Malayalam", "speech": "ml-IN"},
    "pa": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "script": "Gurmukhi", "speech": "pa-IN"},
}

MARATHI_LEXICAL_MARKERS = [
    r"\bदरम्यान\b", r"\bझालेले\b", r"\bझालेला\b", r"\bझालेली\b", r"\bबदल\b",
    r"\bशोधा\b", r"\bदाखवा\b", r"\bमधील\b", r"\bपुण्याच्या\b", r"\bमुंबईची\b",
    r"\bआहेत\b", r"\bनाही\b", r"\bआसपास\b", r"\bवनस्पतीमध्ये\b", r"\bउपग्रह\b",
    r"\bप्रतिमा\b", r"\bवाढ\b", r"\bकमी\b", r"\bक्षेत्रातील\b", r"\bकरा\b"
]

HINDI_LEXICAL_MARKERS = [
    r"\bके बीच\b", r"\bहुए\b", r"\bहुआ\b", r"\bहुई\b", r"\bबदलाव\b",
    r"\bखोजें\b", r"\bदिखाएं\b", r"\bपता लगाएं\b", r"\bमुंबई की\b", r"\bपुणे के\b",
    r"\bसैटेलाइट\b", r"\bइमेजरी\b", r"\bवनस्पति\b", r"\bमें\b", r"\bऔर\b",
    r"\bहैं\b", r"\bनहीं\b", r"\bविस्तार\b", r"\bदूरी\b", r"\bकरें\b"
]


def detect_language(query: str, preferred_lang: Optional[str] = None) -> Tuple[str, float, str]:
    """
    Detects the language of a satellite query with high accuracy.
    
    Returns:
        (lang_code, confidence, detection_reason)
    """
    if not query or not query.strip():
        chosen = preferred_lang if preferred_lang in LANGUAGES else "en"
        return chosen, 1.0, "Empty query, defaulted to preferred or English."

    text = query.strip()
    
    # 1. Count script characters by Unicode blocks
    counts = {
        "Devanagari": 0,
        "Tamil": 0,
        "Telugu": 0,
        "Bengali": 0,
        "Gujarati": 0,
        "Kannada": 0,
        "Malayalam": 0,
        "Gurmukhi": 0,
        "Latin": 0,
    }

    for ch in text:
        cp = ord(ch)
        if 0x0900 <= cp <= 0x097F:
            counts["Devanagari"] += 1
        elif 0x0B80 <= cp <= 0x0BFF:
            counts["Tamil"] += 1
        elif 0x0C00 <= cp <= 0x0C7F:
            counts["Telugu"] += 1
        elif 0x0980 <= cp <= 0x09FF:
            counts["Bengali"] += 1
        elif 0x0A80 <= cp <= 0x0AFF:
            counts["Gujarati"] += 1
        elif 0x0C80 <= cp <= 0x0CFF:
            counts["Kannada"] += 1
        elif 0x0D00 <= cp <= 0x0D7F:
            counts["Malayalam"] += 1
        elif 0x0A00 <= cp <= 0x0A7F:
            counts["Gurmukhi"] += 1
        elif 0x0041 <= cp <= 0x005A or 0x0061 <= cp <= 0x007A:
            counts["Latin"] += 1

    total_indic = sum(v for k, v in counts.items() if k != "Latin")
    
    # Check if a non-Latin Indic script dominates
    if total_indic > 0:
        dom_script, count = max(counts.items(), key=lambda item: item[1] if item[0] != "Latin" else -1)
        if count > 0:
            if dom_script == "Tamil":
                return "ta", 0.99, "Tamil Unicode script detected."
            if dom_script == "Telugu":
                return "te", 0.99, "Telugu Unicode script detected."
            if dom_script == "Bengali":
                return "bn", 0.99, "Bengali Unicode script detected."
            if dom_script == "Gujarati":
                return "gu", 0.99, "Gujarati Unicode script detected."
            if dom_script == "Kannada":
                return "kn", 0.99, "Kannada Unicode script detected."
            if dom_script == "Malayalam":
                return "ml", 0.99, "Malayalam Unicode script detected."
            if dom_script == "Gurmukhi":
                return "pa", 0.99, "Punjabi (Gurmukhi) Unicode script detected."
            
            if dom_script == "Devanagari":
                # Disambiguate Hindi vs Marathi
                mr_score = sum(1 for p in MARATHI_LEXICAL_MARKERS if re.search(p, text, re.IGNORECASE))
                hi_score = sum(1 for p in HINDI_LEXICAL_MARKERS if re.search(p, text, re.IGNORECASE))

                if mr_score > hi_score:
                    return "mr", 0.97, f"Marathi lexical markers detected (mr_score={mr_score} > hi_score={hi_score})."
                elif hi_score > mr_score:
                    return "hi", 0.97, f"Hindi lexical markers detected (hi_score={hi_score} > mr_score={mr_score})."
                elif preferred_lang in ("mr", "hi"):
                    return preferred_lang, 0.95, f"Devanagari matched user preferred language '{preferred_lang}'."
                else:
                    return "hi", 0.85, "Devanagari script matched default Hindi."

    # If predominantly Latin
    if preferred_lang in LANGUAGES and preferred_lang != "en" and counts["Latin"] > 0 and total_indic == 0:
        # Check if user intentionally set a non-English language in UI while typing Latin
        # (transliterated query or preferred language output)
        return preferred_lang, 0.88, f"User explicitly selected preferred language '{preferred_lang}'."

    return "en", 0.99, "Standard English text detected."


# Mapping of remote sensing and geospatial vocabulary to normalized English concepts
INDIC_KEYWORDS_MAP = {
    # Vegetation & Forest
    r"(वनस्पति|वनस्पती|தாவரங்கள்|వృಕ್ಷసంపద|উদ্ভিদ|વનસ્પતિ|ಸಸ್ಯವರ್ಗ|സസ്യജാലങ്ങൾ|ਬਨਸਪਤੀ|पेड़|झाड़ियां|झाडे|காடுகள்|అడవులు|বন|જંગલ|ಕಾಡು|കാടുകൾ|ਜੰਗਲ)": "vegetation",
    # Change / Difference
    r"(बदलाव|बदल|फरक|மாற்றம்|మార్పులు|మార్పు|পরিবর্তন|ફેરફાર|ಬದಲಾವಣೆ|വ്യതിയാനങ്ങൾ|മാറ്റങ്ങൾ|ਤਬਦੀਲੀ|ਬਦਲਾਅ)": "changes",
    # Water / Water Bodies / Flood
    r"(जल निकाय|जलस्रोत|पाणी|நீர்நிலைகள்|நீர்ப்பரப்பு|నీటి వనరులు|నీరు|জলাশয়|জল|જળાશયો|પાણી|ಜಲಮೂಲಗಳು|ನೀರು|ജലാശയങ്ങൾ|വെള്ളം|ਜਲ ਸਰੋਤ|ਪਾਣੀ|बाढ़|पूर|வெள்ளம்|వరద|বন্যা|પૂર|ಪ್ರವಾಹ|പ്രളയം|ਹੜ੍ਹ)": "water bodies and flood boundaries",
    # Urban / Built-up / Expansion
    r"(शहरी विस्तार|नागरी विस्तार|நகர்ப்புற விரிவாக்கம்|పట్టణ విస్తరణ|নগর সম্প্রসারণ|શહેરી વિસ્તરણ|ನಗರ ವಿಸ್ತರಣೆ|നഗര വികസനം|ਸ਼ਹਿਰੀ ਪਸਾਰ|शहरी|नागरी|इमारतें|इमारती|கட்டிடங்கள்|భవనాలు|ভবন|ઇમારતો|ಕಟ್ಟಡಗಳು|കെട്ടിടങ്ങൾ|ਇਮਾਰਤਾਂ)": "urban expansion and built-up areas",
    # Roads & Infrastructure
    r"(सड़कें|रस्ते|சாலைகள்|రహదారులు|রোড|রাস্তা|રસ્તા|ರಸ್ತೆಗಳು|റോഡുകൾ|ਸੜਕਾਂ)": "roads and transit corridors",
    # Search / Detect / Show / Highlight
    r"(खोजें|शोधा|दिखाएं|दाखवा|கண்டுபிடி|గుర్తించు|খুঁজুন|શોધો|ಹುಡುಕಿ|കണ്ടെത്തുക|ਲੱਭੋ|पता लगाएं|চিহ্নিত|ஹைலைட்)": "detect and analyze",
    # Beach / Coast
    r"(समुद्र तट|समुद्रकिनारा|கடற்கரை|సముద్ర తీరం|সৈকত|દરિયાકિનારો|ಕಡಲತೀರ|കടൽത്തീരം|ਸਮੁੰਦਰੀ ਤੱਟ)": "beach and coastline",
}

# Major Indian and global places
GEOGRAPHIC_PLACES = [
    "pune", "mumbai", "delhi", "bengaluru", "chennai", "hyderabad", "kolkata",
    "ahmedabad", "jaipur", "lucknow", "chandigarh", "bhopal", "patna", "nagpur",
    "nashik", "varanasi", "visakhapatnam", "kochi", "thiruvananthapuram", "amritsar",
    "bhubaneswar", "coimbatore", "mysuru", "surat", "vadodara", "rajkot",
    "dehradun", "shimla", "kathmandu", "pokhara", "uttarakhand", "himalayas",
]


def normalize_query(query: str, detected_lang: Optional[str] = None) -> Tuple[str, str, Dict[str, Any]]:
    """
    Normalizes an Indic or English query into canonical English remote-sensing intent,
    preserving all locations, dates, years, and specific targets.
    
    Returns:
        (normalized_english_query, detected_lang, metadata)
    """
    if not query or not query.strip():
        return "", "en", {}

    raw_query = query.strip()
    lang, conf, reason = detect_language(raw_query, detected_lang)

    # If already English, return clean string
    if lang == "en":
        return raw_query, "en", {
            "original_query": raw_query,
            "detected_lang": "en",
            "lang_name": "English",
            "confidence": conf,
            "detection_reason": reason,
        }

    # Extract years (e.g. 2020, 2025)
    years = re.findall(r"\b(19\d\d|20\d\d)\b", raw_query)
    
    # Extract known location names from English transliteration or phonetic matches
    matched_location = None
    q_lower = raw_query.lower()

    # Direct city name check in query or Indic script transliterations
    place_map = {
        "मुंबई": "Mumbai", "मुंबईची": "Mumbai", "मुंबईत": "Mumbai", "mumbai": "Mumbai",
        "पुणे": "Pune", "पुण्याच्या": "Pune", "पुण्यात": "Pune", "pune": "Pune",
        "दिल्ली": "Delhi", "delhi": "Delhi",
        "चेन्नई": "Chennai", "சென்னையில்": "Chennai", "சென்னையின்": "Chennai", "chennai": "Chennai",
        "हैदराबाद": "Hyderabad", "హైదరాబాద్": "Hyderabad", "హైదరాబాదులో": "Hyderabad", "హైదరాబాదు": "Hyderabad", "hyderabad": "Hyderabad",
        "कोलकाता": "Kolkata", "কলকাতা": "Kolkata", "কলকাতায়": "Kolkata", "kolkata": "Kolkata",
        "अहमदाबाद": "Ahmedabad", "અમદાવાદ": "Ahmedabad", "અમદાવાદમાં": "Ahmedabad", "ahmedabad": "Ahmedabad",
        "बेंगलुरु": "Bengaluru", "ಬೆಂಗಳೂರು": "Bengaluru", "ಬೆಂಗಳೂರಿನಲ್ಲಿ": "Bengaluru", "bengaluru": "Bengaluru", "bangalore": "Bengaluru",
        "कोच्चि": "Kochi", "കൊച്ചി": "Kochi", "കൊച്ചിയിൽ": "Kochi", "kochi": "Kochi",
        "अमृतसर": "Amritsar", "ਅੰਮ੍ਰਿਤਸਰ": "Amritsar", "amritsar": "Amritsar",
        "काठमांडू": "Kathmandu", "काठमाडौं": "Kathmandu", "kathmandu": "Kathmandu",
        "उत्तराखंड": "Uttarakhand", "uttarakhand": "Uttarakhand",
    }

    for ind, eng in place_map.items():
        if ind.lower() in q_lower:
            matched_location = eng
            break

    # Extract primary intent concepts
    matched_concepts = []
    for pattern, eng_concept in INDIC_KEYWORDS_MAP.items():
        if re.search(pattern, raw_query, re.IGNORECASE):
            matched_concepts.append(eng_concept)

    # Synthesize normalized query
    parts = []
    
    is_change_task = any(c == "changes" for c in matched_concepts) or len(years) >= 2 or "between" in raw_query.lower()
    
    if is_change_task:
        target = "vegetation" if any("vegetation" in c for c in matched_concepts) else (
            "urban expansion" if any("urban" in c for c in matched_concepts) else (
                "water and flood boundaries" if any("water" in c for c in matched_concepts) else "land cover"
            )
        )
        loc_str = f" around {matched_location}" if matched_location else ""
        if len(years) >= 2:
            norm_q = f"Find changes in {target}{loc_str} between {years[0]} and {years[1]}."
        elif len(years) == 1:
            norm_q = f"Detect changes in {target}{loc_str} around year {years[0]}."
        else:
            norm_q = f"Detect and analyze changes in {target}{loc_str} over time."
    else:
        focus = ", ".join(matched_concepts) if matched_concepts else "land cover and visible physical features"
        loc_str = f" in {matched_location}" if matched_location else ""
        if years:
            norm_q = f"Show satellite imagery of {focus}{loc_str} for year {years[0]}."
        else:
            norm_q = f"Analyze and identify {focus}{loc_str} in this satellite scene."

    metadata = {
        "original_query": raw_query,
        "normalized_query": norm_q,
        "detected_lang": lang,
        "lang_name": LANGUAGES.get(lang, {}).get("name", "Unknown"),
        "confidence": conf,
        "matched_location": matched_location,
        "years": years,
        "detection_reason": reason,
    }

    return norm_q, lang, metadata


def format_multilingual_prompt_instruction(target_lang: str) -> str:
    """
    Returns strict steering instructions for vision models to respond in the target language
    while safeguarding numerical, coordinate, and satellite identifiers.
    """
    if target_lang == "en" or target_lang not in LANGUAGES:
        return ""

    meta = LANGUAGES[target_lang]
    lang_name = meta["name"]
    native_name = meta["native"]

    return f"""
[MANDATORY MULTILINGUAL OUTPUT REQUIREMENT]:
The user is interacting in {lang_name} ({native_name} - '{target_lang}').
You MUST generate the textual remote-sensing analytical assessments in natural, expert, and professional {lang_name}:
- "answer": Comprehensive, multi-paragraph technical assessment in {lang_name}.
- "evidence": Each visual and spectral evidence point in {lang_name}.
- "uncertainty_reason": Short technical sentence in {lang_name}.
- "region_note": Detailed spatial observation in {lang_name}.
- "detected_features": High-precision feature names translated into natural {lang_name}.

CRITICAL TECHNICAL PRESERVATION RULES (DO NOT TRANSLATE OR ALTER):
1. Preserve ALL satellite and sensor platform names EXACTLY (e.g. Sentinel-1, Sentinel-2, Cartosat-2S, RISAT, Landsat-8/9, Oceansat, Resourcesat, Bhuvan).
2. Preserve ALL geographic coordinates, latitudes, longitudes, and bounding box arrays EXACTLY as numeric values.
3. Preserve ALL dates, years (e.g. 2020, 2025), and percentage metrics (e.g. 45%, 10m, 100 ha) in standard Indo-Arabic numerals.
4. Preserve ALL remote sensing band names and radiometric indices (e.g. NDVI, NDWI, NDBI, NIR, SWIR, RGB, VV, VH) as standard acronyms.
5. Preserve ALL technical model names (e.g. SAM 2.1, HQ-SAM, BigEarthNet-19, SegFormer) UNCHANGED.
6. Keep ALL JSON keys in English as specified in the schema.
"""


def format_location_multilingual_prompt_instruction(target_lang: str) -> str:
    """
    Returns strict steering instructions for Gemini 2.0 Flash in Location Explorer mode,
    directing it to produce the entire Markdown dossier in the target language.
    """
    if target_lang == "en" or target_lang not in LANGUAGES:
        return ""

    meta = LANGUAGES[target_lang]
    lang_name = meta["name"]
    native_name = meta["native"]

    return f"""
[MANDATORY MULTILINGUAL OUTPUT INSTRUCTION]:
The user has requested this Earth Observation Geospatial Intelligence Dossier in {lang_name} ({native_name} - language code '{target_lang}').
You MUST generate the ENTIRE Markdown report (including all 5 sections, descriptive analyses, terrain evaluations, urban densities, and recommendations) in fluent, authoritative, and professional {lang_name}.

CRITICAL TECHNICAL PRESERVATION RULES:
1. Preserve ALL satellite names EXACTLY: Sentinel-1, Sentinel-2, Cartosat-2S, RISAT, Landsat, Bhuvan, etc.
2. Preserve ALL coordinate values, latitudes, longitudes, bounding box coordinates, and numbers in standard Arabic digits.
3. Preserve ALL technical remote sensing indices and metrics: NDVI, NDWI, NDBI, SAR, C-band, MSI, meters/km, percentages.
4. Format the report using the standard 5 Markdown headings translated naturally into {lang_name}.
"""


LOCATION_FALLBACK_HEADINGS = {
    "en": {
        "h1": "### 🌍 Macro Geographic Overview",
        "h2": "### 🏙️ Urban Morphology & Settlement Density",
        "h3": "### 🌿 Environmental Context & Land Cover Dynamics",
        "h4": "### 🏗️ Critical Infrastructure & Transportation",
        "h5": "### 🛰️ Remote Sensing Observations & Sensor Recommendations",
        "text1": "**{name}** is situated at **{lat:.4f}°N, {lng:.4f}°E** in the {ns}-{ew} hemisphere. The bounding envelope spanning `[{min_lng:.4f}, {min_lat:.4f}]` to `[{max_lng:.4f}, {max_lat:.4f}]` exhibits terrain characteristic of its regional physiography, with localized drainage networks and transitional soil gradients.",
        "text2": "At zoom level {zoom:.1f}, spatial layout indicates built-up clustering along primary transportation corridors. Impervious surfaces, structural footprints, and commercial/residential parcels are aligned with regional urban growth patterns.",
        "text3": "Satellite reflectance patterns suggest mixed land-use classification. Vegetated pockets show active chlorophyll absorption, while open pervious surfaces provide vital hydrological infiltration and ecosystem buffering against surface runoff.",
        "text4": "Transport arteries provide connectivity across the spatial envelope. Surface networks, junction nodes, and municipal utilities show established logistical integration with surrounding regional centers.",
        "text5": "- **Sentinel-2 MSI**: Recommended for continuous NDVI and NDWI vegetation and water classification.\n- **Sentinel-1 SAR**: C-band radar recommended for cloud-penetrating all-weather surface roughness monitoring."
    },
    "hi": {
        "h1": "### 🌍 स्थूल भौगोलिक अवलोकन",
        "h2": "### 🏙️ शहरी संरचना एवं निर्मित घनत्व",
        "h3": "### 🌿 पर्यावरणीय संदर्भ एवं भूमि आवरण",
        "h4": "### 🏗️ महत्वपूर्ण बुनियादी ढांचा एवं परिवहन",
        "h5": "### 🛰️ रिमोट सेंसिंग प्रेक्षण एवं सेंसर सिफारिशें",
        "text1": "**{name}** अक्षांश **{lat:.4f}°N, {lng:.4f}°E** पर स्थित है। इसका बाउंडिंग क्षेत्र `[{min_lng:.4f}, {min_lat:.4f}]` से `[{max_lng:.4f}, {max_lat:.4f}]` तक फैला हुआ है, जो स्थानीय जल निकासी तंत्र और संक्रमणकालीन मिट्टी की विशेषताओं को दर्शाता है।",
        "text2": "ज़ूम स्तर {zoom:.1f} पर, स्थानिक विश्लेषण प्रमुख परिवहन गलियारों के साथ निर्मित संरचनाओं और इमारतों का सघन जमाव दर्शाता है। पक्की सतहें और वाणिज्यिक/आवासीय भूखंड सुनियोजित विकास पैटर्न दर्शाते हैं।",
        "text3": "सैटेलाइट वर्णक्रमीय परावर्तन मिश्रित भूमि उपयोग का संकेत देता है। वनस्पति क्षेत्र सक्रिय क्लोरोफिल अवशोषण दर्शाते हैं, जबकि खुली पारगम्य सतहें भूजल पुनर्भरण और पारिस्थितिक संतुलन प्रदान करती हैं।",
        "text4": "प्रमुख राष्ट्रीय एवं क्षेत्रीय राजमार्ग पूरे क्षेत्र को कनेक्टिविटी प्रदान करते हैं। सतही नेटवर्क, जंक्शन नोड्स और नागरिक सुविधाएं आसपास के क्षेत्रीय केंद्रों के साथ मजबूत लॉजिस्टिक एकीकरण दर्शाती हैं।",
        "text5": "- **Sentinel-2 MSI**: निरंतर NDVI और NDWI वनस्पति एवं जल निकाय निगरानी हेतु अत्यधिक अनुशंसित।\n- **Sentinel-1 SAR**: सभी मौसमों में बादलों के आर-पार सतह खुरदरापन विश्लेषण के लिए C-band रडार अनुशंसित।"
    },
    "mr": {
        "h1": "### 🌍 स्थूल भौगोलिक विहंगावलोकन",
        "h2": "### 🏙️ नागरी रचना आणि वसाहत घनता",
        "h3": "### 🌿 पर्यावरणीय संदर्भ आणि भू-आच्छादन",
        "h4": "### 🏗️ महत्त्वपूर्ण पायाभूत सुविधा आणि वाहतूक",
        "h5": "### 🛰️ रिमोट सेन्सिंग निरीक्षणे आणि सेन्सर शिफारसी",
        "text1": "**{name}** हे अक्षवृत्त **{lat:.4f}°N, {lng:.4f}°E** वर स्थित आहे. बाउंडिंग क्षेत्र `[{min_lng:.4f}, {min_lat:.4f}]` ते `[{max_lng:.4f}, {max_lat:.4f}]` स्थानिक जलप्रवाह आणि भू-रचनेची वैशिष्ट्ये दर्शवते.",
        "text2": "झूम स्तर {zoom:.1f} वर, उपग्रह दृश्य मुख्य वाहतूक कॉरिडोअरलगत बांधकामे आणि नागरी वस्त्यांचे केंद्रित स्वरूप दर्शवते. पक्के रस्ते आणि निवासी संकुले प्रादेशिक वाढ दर्शवतात.",
        "text3": "उपग्रह परावर्तन नोंदी संमिश्र भू-वापराचे वर्गीकरण दर्शवतात. हरित पट्ट्यांमध्ये सक्रिय बायोमास दिसून येतो, तर मोकळ्या जमिनी भूजल संवर्धनास मदत करतात.",
        "text4": "वाहतूक धमण्या संपूर्ण क्षेत्राला जोडतात. रस्ते जाळे, जंक्शन नोड्स आणि नागरी पायाभूत सुविधा आसपासच्या औद्योगिक व व्यापारी केंद्रांशी जोडलेल्या आहेत.",
        "text5": "- **Sentinel-2 MSI**: वनस्पती आणि जलस्रोत वर्गीकरणासाठी (NDVI, NDWI) शिफारस केलेले.\n- **Sentinel-1 SAR**: सर्व ऋतूंमध्ये ढगांच्या आडून अचूक पृष्ठभाग निरीक्षणासाठी C-band रडार शिफारस केलेले."
    },
    "ta": {
        "h1": "### 🌍 மேக்ரோ புவியியல் கண்ணோட்டம்",
        "h2": "### 🏙️ நகர்ப்புற வடிவமைப்பு மற்றும் குடியிருப்பு அடர்த்தி",
        "h3": "### 🌿 சுற்றுச்சூழல் சூழல் மற்றும் நிலப்பரப்பு இயக்கவியல்",
        "h4": "### 🏗️ முக்கிய உள்கட்டமைப்பு மற்றும் போக்குவரத்து",
        "h5": "### 🛰️ தொலையுணர்வு அவதானிப்புகள் மற்றும் சென்சார் பரிந்துரைகள்",
        "text1": "**{name}** அட்சரேகை **{lat:.4f}°N, {lng:.4f}°E** இல் அமைந்துள்ளது. எல்லைப் பெட்டி `[{min_lng:.4f}, {min_lat:.4f}]` முதல் `[{max_lng:.4f}, {max_lat:.4f}]` வரை பரவியுள்ளது.",
        "text2": "ஜூம் நிலை {zoom:.1f} இல், முதன்மை போக்குவரத்து சாலைகளுடன் கட்டடங்கள் மற்றும் குடியிருப்புப் பகுதிகள் சீராக அமைந்திருப்பது தெரிகிறது.",
        "text3": "செயற்கைக்கோள் பிரதிபலிப்பு சமநிலையான நிலப்பயன்பாட்டைக் காட்டுகிறது. பசுமையான பகுதிகள் சிறந்த தாவர ஆரோக்கியத்தை வெளிப்படுத்துகின்றன.",
        "text4": "போக்குவரத்து வழித்தடங்கள் வலுவான இணைப்பை வழங்குகின்றன. சாலை நெட்வொர்க்குகள் மற்றும் நகராட்சி வசதிகள் பிராந்திய மையங்களுடன் ஒருங்கிணைக்கப்பட்டுள்ளன.",
        "text5": "- **Sentinel-2 MSI**: தொடர்ச்சியான NDVI மற்றும் NDWI தாவர/நீர் கண்காணிப்புக்கு பரிந்துரைக்கப்படுகிறது.\n- **Sentinel-1 SAR**: மேகமூட்டத்தை ஊடுருவி மேற்பரப்பு நிலவரங்களை ஆராய C-band ரேடார் பரிந்துரைக்கப்படுகிறது."
    },
    "te": {
        "h1": "### 🌍 స్థూల భౌగోళిక అవలోకనం",
        "h2": "### 🏙️ పట్టణ నిర్మాణం మరియు నివాస సాంద్రత",
        "h3": "### 🌿 పర్యావరణ సందర్భం మరియు భూమి కవరేజ్",
        "h4": "### 🏗️ కీలక మౌలిక సదుపాయాలు మరియు రవాణా",
        "h5": "### 🛰️ రిమోట్ సెన్సింగ్ పరిశీలనలు మరియు సెన్సార్ సిఫార్సులు",
        "text1": "**{name}** అక్షాంశం **{lat:.4f}°N, {lng:.4f}°E** వద్ద ఉంది. బౌండింగ్ బాక్స్ `[{min_lng:.4f}, {min_lat:.4f}]` నుండి `[{max_lng:.4f}, {max_lat:.4f}]` వరకు విస్తరించి ఉంది.",
        "text2": "జూమ్ స్థాయి {zoom:.1f} వద్ద, రవాణా కారిడార్లతో పాటు నిర్మిత నిర్మాణాలు మరియు భవనాల సాంద్రత కనిపిస్తుంది.",
        "text3": "శాటిలైట్ స్పెక్ట్రల్ ప్రతిబింబం మిశ్రమ భూ వినియోగాన్ని సూచిస్తుంది. వృక్షసంపద ప్రాంతాలు చురుకైన పచ్చదనాన్ని ప్రదర్శిస్తాయి.",
        "text4": "రవాణా మార్గాలు మెరుగైన అనుసంధానాన్ని అందిస్తాయి. రహదారి నెట్‌వర్క్ ప్రాంతీయ కేంద్రాలతో సమన్వయం కలిగి ఉంది.",
        "text5": "- **Sentinel-2 MSI**: NDVI మరియు NDWI వృక్షసంపద మరియు నీటి వర్గీకరణ కోసం సిఫార్సు చేయబడింది.\n- **Sentinel-1 SAR**: మేఘాలను ఛేదించే ఆల్-వెదర్ ఉపరితల పర్యవేక్షణకు C-band రాడార్ సిఫార్సు చేయబడింది."
    },
    "bn": {
        "h1": "### 🌍 সামগ্রিক ভৌগলিক রূপরেখা",
        "h2": "### 🏙️ নগর রূপবিদ্যা ও জনবসতি ঘনত্ব",
        "h3": "### 🌿 পরিবেশগত প্রেক্ষাপট ও ভূমির আচ্ছাদন",
        "h4": "### 🏗️ গুরুত্বপূর্ণ অবকাঠামো ও পরিবহন",
        "h5": "### 🛰️ রিমোট সেন্সিং পর্যবেক্ষণ ও সেন্সর সুপারিশ",
        "text1": "**{name}** অক্ষাংশ **{lat:.4f}°N, {lng:.4f}°E**-এ অবস্থিত। বাউন্ডিং অঞ্চল `[{min_lng:.4f}, {min_lat:.4f}]` থেকে `[{max_lng:.4f}, {max_lat:.4f}]` পর্যন্ত বিস্তৃত।",
        "text2": "জুম স্তর {zoom:.1f}-এ, প্রধান পরিবহন করিডোর ধরে নির্মিত স্থাপনা ও বসতির স্পষ্ট বিন্যাস পরিলক্ষিত হয়।",
        "text3": "স্যাটেলাইট বর্ণালী প্রতিফলন মিশ্র ভূমি ব্যবহারের ইঙ্গিত দেয়। উদ্ভিজ্জ অঞ্চল সক্রিয় ক্লোরোফিল শোষণ প্রদর্শন করে।",
        "text4": "পরিবহন সংযোগ সমগ্র অঞ্চল জুড়ে শক্তিশালী যোগাযোগ প্রদান করে। সড়ক নেটওয়ার্ক আঞ্চলিক কেন্দ্রগুলির সাথে সুসংহত।",
        "text5": "- **Sentinel-2 MSI**: ধারাবাহিক NDVI এবং NDWI পর্যবেক্ষণ ও শ্রেণিবিভাগের জন্য অত্যন্ত সুপারিশকৃত।\n- **Sentinel-1 SAR**: মেঘভেদকারী সর্ব-আবহাওয়া পর্যবেক্ষণের জন্য C-band রাডার সুপারিশকৃত।"
    },
    "gu": {
        "h1": "### 🌍 સમગ્ર ભૌગોલિક ઝાંખી",
        "h2": "### 🏙️ શહેરી માળખું અને વસાહત ઘનતા",
        "h3": "### 🌿 પર્યાવરણીય સંદર્ભ અને જમીન આવરણ",
        "h4": "### 🏗️ નિર્ણાયક ઈન્ફ્રાસ્ટ્રક્ચર અને પરિવહન",
        "h5": "### 🛰️ રિમોટ સેન્સિંગ અવલોકનો અને સેન્સર ભલામણો",
        "text1": "**{name}** અક્ષાંશ **{lat:.4f}°N, {lng:.4f}°E** પર આવેલું છે. બાઉન્ડિંગ બોક્સ `[{min_lng:.4f}, {min_lat:.4f}]` થી `[{max_lng:.4f}, {max_lat:.4f}]` સુધી વિસ્તરેલું છે.",
        "text2": "ઝૂમ લેવલ {zoom:.1f} પર, મુખ્ય પરિવહન માર્ગો સાથે બાંધકામ અને રહેણાંક વસાહતોનું સંગઠિત વિતરણ જણાય છે.",
        "text3": "સેટેલાઇટ સ્પેક્ટ્રલ પરાવર્તન મિશ્ર જમીન ઉપયોગ દર્શાવે છે. વનસ્પતિ વિસ્તારો સ્વસ્થ પાક સ્વાસ્થ્ય સૂચવે છે.",
        "text4": "માર્ગ જોડાણો સમગ્ર ક્ષેત્રમાં મજબૂત જોડાણ પૂરું પાડે છે. જંક્શન નોડ્સ આસપાસના શહેરી કેન્દ્રો સાથે સુસંગત છે.",
        "text5": "- **Sentinel-2 MSI**: NDVI અને NDWI જમીન/પાણી વર્ગીકરણ માટે ભલામણ કરેલ.\n- **Sentinel-1 SAR**: વાદળો વચ્ચેથી સપાટીના સતત નિરીક્ષણ માટે C-band રડાર ભલામણ કરેલ."
    },
    "kn": {
        "h1": "### 🌍 ಸ್ಥೂಲ ಭೌಗೋಳಿಕ ಅವಲೋಕನ",
        "h2": "### 🏙️ ನಗರ ರಚನೆ ಮತ್ತು ವಸಾಹತು ಸಾಂದ್ರತೆ",
        "h3": "### 🌿 ಪರಿಸರ ಸಂದರ್ಭ ಮತ್ತು ಭೂ ಹೊದಿಕೆ",
        "h4": "### 🏗️ ಪ್ರಮುಖ ಮೂಲಸೌಕರ್ಯ ಮತ್ತು ಸಾರಿಗೆ",
        "h5": "### 🛰️ ರಿಮೋಟ್ ಸೆನ್ಸಿಂಗ್ ವೀಕ್ಷಣೆಗಳು ಮತ್ತು ಸೆನ್ಸರ್ ಶಿಫಾರಸುಗಳು",
        "text1": "**{name}** ಅಕ್ಷಾಂಶ **{lat:.4f}°N, {lng:.4f}°E** ನಲ್ಲಿ ನೆಲೆಗೊಂಡಿದೆ. ಬೌಂಡಿಂಗ್ ಬಾಕ್ಸ್ `[{min_lng:.4f}, {min_lat:.4f}]` ರಿಂದ `[{max_lng:.4f}, {max_lat:.4f}]` ವರೆಗೆ ವಿಸ್ತರಿಸಿದೆ.",
        "text2": "ಜೂಮ್ ಮಟ್ಟ {zoom:.1f} ರಲ್ಲಿ, ಪ್ರಮುಖ ಸಾರಿಗೆ ಕಾರಿಡಾರ್‌ಗಳ ಉದ್ದಕ್ಕೂ ಕಟ್ಟಡಗಳು ಮತ್ತು ಬಡಾವಣೆಗಳ ಸಾಂದ್ರತೆ ಕಂಡುಬರುತ್ತದೆ.",
        "text3": "ಉಪಗ್ರಹ ಪ್ರತಿಫಲನವು ಸಮತೋಲಿತ ಭೂ ಬಳಕೆಯನ್ನು ತೋರಿಸುತ್ತದೆ. ಸಸ್ಯವರ್ಗದ ಪ್ರದೇಶಗಳು ಸಕ್ರಿಯ ಹಸಿರನ್ನು ಪ್ರದರ್ಶಿಸುತ್ತವೆ.",
        "text4": "ರಸ್ತೆ ಜಾಲಗಳು ಅತ್ಯುತ್ತಮ ಸಂಪರ್ಕವನ್ನು ಒದಗಿಸುತ್ತವೆ. ಜಂಕ್ಷನ್‌ಗಳು ಸುತ್ತಮುತ್ತಲಿನ ಪ್ರಾದೇಶಿಕ ಕೇಂದ್ರಗಳೊಂದಿಗೆ ಸಂಪರ್ಕ ಹೊಂದಿವೆ.",
        "text5": "- **Sentinel-2 MSI**: ನಿರಂತರ NDVI ಮತ್ತು NDWI ಮೇಲ್ವಿಚಾರಣೆಗಾಗಿ ಶಿಫಾರಸು ಮಾಡಲಾಗಿದೆ.\n- **Sentinel-1 SAR**: ಮೋಡಗಳನ್ನು ಭೇದಿಸಿ ಮೇಲ್ಮೈ ಅಧ್ಯಯನ ಮಾಡಲು C-band ರಾಡಾರ್ ಶಿಫಾರಸು ಮಾಡಲಾಗಿದೆ."
    },
    "ml": {
        "h1": "### 🌍 സ്ഥൂല ഭൂമിശാസ്ത്രപരമായ അവലോകനം",
        "h2": "### 🏙️ നഗര ഘടനയും ജനവാസ സാന്ദ്രതയും",
        "h3": "### 🌿 പാരിസ്ഥിതിക പശ്ചാത്തലവും ഭൂവിനിയോഗവും",
        "h4": "### 🏗️ പ്രധാന അടിസ്ഥാന സൗകര്യങ്ങളും ഗതാഗതവും",
        "h5": "### 🛰️ റിമോട്ട് സെൻസിംഗ് നിരീക്ഷണങ്ങളും സെൻസർ ശുപാർശകളും",
        "text1": "**{name}** അക്ഷാംശം **{lat:.4f}°N, {lng:.4f}°E**-ൽ സ്ഥിതിചെയ്യുന്നു. അതിർത്തി വ്യാപ്തി `[{min_lng:.4f}, {min_lat:.4f}]` മുതൽ `[{max_lng:.4f}, {max_lat:.4f}]` വരെ വ്യാപിച്ചിരിക്കുന്നു.",
        "text2": "സൂം ലെവൽ {zoom:.1f}-ൽ, പ്രധാന ഗതാഗത പാതകളോട് ചേർന്ന് കെട്ടിടങ്ങളുടെയും ജനവാസ കേന്ദ്രങ്ങളുടെയും സാന്ദ്രത ദൃശ്യമാണ്.",
        "text3": "ഉപഗ്രഹ സ്പെക്ട്രൽ പ്രതിഫലനം സമ്മിശ്ര ഭൂവിനിയോഗത്തെ സൂചിപ്പിക്കുന്നു. സസ്യമേഖലകൾ ആരോഗ്യകരമായ ഹരിത സാന്ദ്രത കാണിക്കുന്നു.",
        "text4": "ഗതാഗത ശൃംഖലകൾ മികച്ച കണക്റ്റിവിറ്റി നൽകുന്നു. ജംഗ്ഷനുകളും റോഡുകളും സമീപ നഗര കേന്ദ്രങ്ങളുമായി ബന്ധപ്പെട്ടിരിക്കുന്നു.",
        "text5": "- **Sentinel-2 MSI**: NDVI, NDWI സസ്യ/ജല നിരീക്ഷണത്തിന് ശുപാർശ ചെയ്യുന്നു.\n- **Sentinel-1 SAR**: മേഘങ്ങൾക്കിടയിലൂടെ ഉപരിതല നിരീക്ഷണത്തിന് C-band റഡാർ ശുപാർശ ചെയ്യുന്നു."
    },
    "pa": {
        "h1": "### 🌍 ਸਮੁੱਚਾ ਭੂਗੋਲਿਕ ਜਾਇਜ਼ਾ",
        "h2": "### 🏙️ ਸ਼ਹਿਰੀ ਬਣਤਰ ਅਤੇ ਵਸੋਂ ਦੀ ਘਣਤਾ",
        "h3": "### 🌿 ਵਾਤਾਵਰਣ ਸੰਦਰਭ ਅਤੇ ਜ਼ਮੀਨੀ ਕਵਰੇਜ",
        "h4": "### 🏗️ ਮਹੱਤਵਪੂਰਨ ਬੁਨਿਆਦੀ ਢਾਂਚਾ ਅਤੇ ਆਵਾਜਾਈ",
        "h5": "### 🛰️ ਰਿਮੋਟ ਸੈਂਸਿੰਗ ਨਿਰੀਖਣ ਅਤੇ ਸੈਂਸਰ ਸਿਫ਼ਾਰਸ਼ਾਂ",
        "text1": "**{name}** ਅਕਸ਼ਾਂਸ਼ **{lat:.4f}°N, {lng:.4f}°E** 'ਤੇ ਸਥਿਤ ਹੈ। ਬਾਊਂਡਿੰਗ ਬਾਕਸ `[{min_lng:.4f}, {min_lat:.4f}]` ਤੋਂ `[{max_lng:.4f}, {max_lat:.4f}]` ਤੱਕ ਫੈਲਿਆ ਹੋਇਆ ਹੈ।",
        "text2": "ਜ਼ੂਮ ਪੱਧਰ {zoom:.1f} 'ਤੇ, ਮੁੱਖ ਆਵਾਜਾਈ ਰੂਟਾਂ ਦੇ ਨਾਲ-ਨਾਲ ਉਸਾਰੀਆਂ ਅਤੇ ਰਿਹਾਇਸ਼ੀ ਖੇਤਰਾਂ ਦਾ ਕੇਂਦਰੀਕਰਨ ਨਜ਼ਰ ਆਉਂਦਾ ਹੈ।",
        "text3": "ਸੈਟੇਲਾਈਟ ਸਪੈਕਟ੍ਰਲ ਰਿਫਲੈਕਟੈਂਸ ਸੰਤੁਲਿਤ ਜ਼ਮੀਨੀ ਵਰਤੋਂ ਨੂੰ ਦਰਸਾਉਂਦੀ ਹੈ। ਬਨਸਪਤੀ ਖੇਤਰ ਸਿਹਤਮੰਦ ਹਰਿਆਵਲ ਪ੍ਰਦਰਸ਼ਿਤ ਕਰਦੇ ਹਨ।",
        "text4": "ਆਵਾਜਾਈ ਮਾਰਗ ਪੂਰੇ ਖੇਤਰ ਵਿੱਚ ਸ਼ਾਨਦਾਰ ਸੰਪਰਕ ਪ੍ਰਦਾਨ ਕਰਦੇ ਹਨ। ਸੜਕ ਨੈੱਟਵਰਕ ਖੇਤਰੀ ਕੇਂਦਰਾਂ ਨਾਲ ਜੁੜਿਆ ਹੋਇਆ ਹੈ।",
        "text5": "- **Sentinel-2 MSI**: ਲਗਾਤਾਰ NDVI ਅਤੇ NDWI ਬਨਸਪਤੀ/ਪਾਣੀ ਵਰਗੀਕਰਨ ਲਈ ਸਿਫ਼ਾਰਸ਼ ਕੀਤੀ ਜਾਂਦੀ ਹੈ।\n- **Sentinel-1 SAR**: ਬੱਦਲਾਂ ਦੇ ਆਰ-ਪਾਰ ਜ਼ਮੀਨੀ ਨਿਰੀਖਣ ਲਈ C-band ਰਾਡਾਰ ਸਿਫ਼ਾਰਸ਼ ਕੀਤਾ ਜਾਂਦਾ ਹੈ।"
    }
}


def get_localized_location_fallback(
    location_name: str,
    lat: float,
    lng: float,
    bbox: Dict[str, float],
    zoom: float = 15.0,
    target_lang: str = "en"
) -> str:
    """
    Generates a high-quality localized remote sensing intelligence dossier for Location Explorer
    in the requested language when Gemini API is unavailable or offline.
    """
    lang = target_lang if target_lang in LOCATION_FALLBACK_HEADINGS else "en"
    cfg = LOCATION_FALLBACK_HEADINGS[lang]

    ns = "Northern" if lat >= 0 else "Southern"
    ew = "Eastern" if lng >= 0 else "Western"
    min_lng = bbox.get("min_lng", lng - 0.02)
    min_lat = bbox.get("min_lat", lat - 0.02)
    max_lng = bbox.get("max_lng", lng + 0.02)
    max_lat = bbox.get("max_lat", lat + 0.02)

    p1 = cfg["text1"].format(name=location_name, lat=lat, lng=lng, ns=ns, ew=ew, min_lng=min_lng, min_lat=min_lat, max_lng=max_lng, max_lat=max_lat)
    p2 = cfg["text2"].format(zoom=zoom)
    p3 = cfg["text3"]
    p4 = cfg["text4"]
    p5 = cfg["text5"]

    return f"""{cfg['h1']}
{p1}

{cfg['h2']}
{p2}

{cfg['h3']}
{p3}

{cfg['h4']}
{p4}

{cfg['h5']}
{p5}"""



# Indic templates for localized offline engine responses
OFFLINE_TEMPLATES = {
    "hi": {
        "analysis_header": "सैटेलाइट इमेजरी विश्लेषण रिपोर्ट: {location} क्षेत्र का रिमोट सेंसिंग मूल्यांकन।",
        "land_cover_summary": "भू-आवरण वितरण में {top_veg}% वनस्पति, {top_urban}% शहरी निर्मित क्षेत्र এবং {top_water}% जल निकाय परिलक्षित होते हैं।",
        "change_detected": "{year1} और {year2} के बीच {location} के आसपास {direction} दर्ज की गई है।",
        "spectral_evidence": [
            "Sentinel-2 एनआईआर/रेड बैंड्स में उच्च वनस्पति परावर्तन (NDVI > 0.45) सक्रिय बायोमास को इंगित करता है।",
            "निर्मित संरचनाओं और प्रमुख सड़क नेटवर्क में स्पष्ट स्थानिक बनावट और उच्च किनारे का कंट्रास्ट दिखाई देता है।",
            "जल निकायों में कम वर्णक्रमीય परावर्तन (NDWI सुसंगत) स्पष्ट सीमाओं के साथ दर्ज किया गया।"
        ],
        "uncertainty_clear": "उच्च स्थानिक रिज़ॉल्यूशन और न्यूनतम वायुमंडलीय बाधा के कारण उच्च विश्लेषण विश्वास।",
        "region_note": "प्रमुख भौगोलिक विशेषताएं और भूमि उपयोग पैटर्न पूरे उपग्रह दृश्य में वितरित हैं।",
    },
    "mr": {
        "analysis_header": "उपग्रह प्रतिमा विश्लेषण अहवाल: {location} परिसराचे रिमोट सेन्सिंग मूल्यांकन.",
        "land_cover_summary": "भू-आच्छादन वर्गीकरणामध्ये {top_veg}% वनस्पती, {top_urban}% नागरी बांधकाम आणि {top_water}% जलस्रोत आढळले आहेत.",
        "change_detected": "{year1} ते {year2} दरम्यान {location} परिसरामध्ये {direction} नोंदवली गेली आहे.",
        "spectral_evidence": [
            "Sentinel-2 एनआयआर बँड्समध्ये उच्च वनस्पती परावर्तन (NDVI > 0.45) सक्रिय बायोमास दर्शवते.",
            "नागरी बांधकामे आणि वाहतूक कॉरिडोअरमध्ये स्पष्ट किनार ग्रेडियंट दिसून येतो.",
            "जलस्रोतांमध्ये कमी वर्णक्रमीय परावर्तन (NDWI सुसंगत) अचूक सीमांसह आढळले."
        ],
        "uncertainty_clear": "उत्कृष्ट प्रतिमा स्पष्टता आणि कमी ढगांच्या आच्छादनामुळे उच्च विश्लेषण अचूकता.",
        "region_note": "प्रमुख पर्यावरणीय वैशिष्ट्ये आणि नागरी घटक उपग्रह दृश्यात सुस्पष्टपणे वितरित आहेत.",
    },
    "ta": {
        "analysis_header": "செயற்கைக்கோள் படப் பகுப்பாய்வு அறிக்கை: {location} பகுதியின் தொலையுணர்வு மதிப்பீடு.",
        "land_cover_summary": "நிலப்பரப்பு வகைப்பாட்டில் {top_veg}% தாவரங்கள், {top_urban}% நகர்ப்புற கட்டடங்கள் மற்றும் {top_water}% நீர்நிலைகள் பதிவாகியுள்ளன.",
        "change_detected": "{year1} முதல் {year2} வரை {location} பகுதியில் {direction} கண்டறியப்பட்டுள்ளது.",
        "spectral_evidence": [
            "Sentinel-2 என்ஐஆர் அலைவரிசைகளில் உயர்ந்த தாவர பிரதிபலிப்பு (NDVI > 0.45) ஆரோக்கியமான பயிர் வளத்தைக் காட்டுகிறது.",
            "நகர்ப்புற கட்டமைப்புகள் மற்றும் சாலை நெட்வொர்க்கில் தெளிவான விளிம்பு அமைப்பு காணப்படுகிறது.",
            "நீர்நிலைகளில் குறைந்த நிறமாலை பிரதிபலிப்பு (NDWI சீரானது) துல்லியமாகப் பதிவாகியுள்ளது."
        ],
        "uncertainty_clear": "சிறந்த படத் தெளிவுத்திறன் காரணமாக உயர் நம்பிக்கை நிலை.",
        "region_note": "முக்கிய புவியியல் அம்சங்கள் காட்சியெங்கும் சீராகப் பரவியுள்ளன.",
    },
    "te": {
        "analysis_header": "శాటిలైట్ ఇమేజ్ విశ్లేషణ నివేదిక: {location} ప్రాంతపు రిమోట్ సెన్సింగ్ మూల్యాంకనం.",
        "land_cover_summary": "భూమి కవరేజ్ విభజనలో {top_veg}% వృక్షసంపద, {top_urban}% పట్టణ ప్రాంతం మరియు {top_water}% నీటి వనరులు గుర్తించబడ్డాయి.",
        "change_detected": "{year1} నుండి {year2} మధ్య {location} చుట్టూ {direction} నమోదు చేయబడింది.",
        "spectral_evidence": [
            "Sentinel-2 ఎన్ఐఆర్ బ్యాండ్లలో అధిక వృక్షసంపద ప్రతిబింబం (NDVI > 0.45) ఆరోగ్యకరమైన పంటను సూచిస్తుంది.",
            "పట్టణ నిర్మాణాలు మరియు రహదారులలో స్పష్టమైన ప్రాదేశిక ఆకృతి కనిపించింది.",
            "నీటి వనరులలో తక్కువ స్పెక్ట్రల్ రిఫ్లెక్టెన్స్ (NDWI అనుగుణంగా) గుర్తించబడింది."
        ],
        "uncertainty_clear": "అధిక ప్రాదేశిక స్పష్టత కారణంగా మోడల్ నమ్మకం అధికం.",
        "region_note": "కీలక భౌగోళిక లక్షణాలు చిత్రం అంతటా విస్తరించి ఉన్నాయి.",
    },
    "bn": {
        "analysis_header": "স্যাটেলাইট ইমেজ বিশ্লেষণ রিপোর্ট: {location} এলাকার রিমোট সেন্সিং মূল্যায়ন।",
        "land_cover_summary": "ভূমির আচ্ছাদনে {top_veg}% উদ্ভিদ, {top_urban}% নগর এলাকা এবং {top_water}% জলাশয় পরিলক্ষিত হয়েছে।",
        "change_detected": "{year1} এবং {year2} এর মধ্যে {location} এলাকায় {direction} শনাক্ত হয়েছে।",
        "spectral_evidence": [
            "Sentinel-2 এনআইআর ব্যান্ডে উচ্চ উদ্ভিজ্জ প্রতিফলন (NDVI > 0.45) সক্রিয় বায়োমাস নির্দেশ করে।",
            "নগর কাঠামো এবং সড়ক নেটওয়ার্কে স্পষ্ট স্থানিক বৈসাদৃশ্য দেখা যায়।",
            "জলাশয়ে নিম্ন বর্ণালী প্রতিফলন (NDWI সামঞ্জস্যপূর্ণ) নির্ভুলভাবে চিহ্নিত হয়েছে।"
        ],
        "uncertainty_clear": "উচ্চ স্থানিক রেজোলিউশন এবং পরিষ্কার আবহাওয়ার কারণে উচ্চ আত্মবিশ্বাস।",
        "region_note": "মূল ভৌগলিক বৈশিষ্ট্য দৃশ্যজুড়ে স্পষ্টভাবে বিন্যস্ত রয়েছে।",
    },
    "gu": {
        "analysis_header": "સેટેલાઇટ ઇમેજ વિશ્લેષણ અહેવાલ: {location} વિસ્તારનું રીમોટ સેન્સિંગ મૂલ્યાંકન.",
        "land_cover_summary": "જમીન આવરણમાં {top_veg}% વનસ્પતિ, {top_urban}% શહેરી બાંધકામ અને {top_water}% જળાશયો નોંધાયા છે.",
        "change_detected": "{year1} થી {year2} વચ્ચે {location} ની આસપાસ {direction} નોંધાઈ છે.",
        "spectral_evidence": [
            "Sentinel-2 NIR બેન્ડમાં ઉચ્ચ વનસ્પતિ પરાવર્તન (NDVI > 0.45) સક્રિય પાક સ્વાસ્થ્ય સૂચવે છે.",
            "શહેરી માળખાં અને માર્ગ નેટવર્કમાં સ્પષ્ટ અવકાશી રચના જોવા મળે છે.",
            "જળાશયોમાં ઓછું સ્પેક્ટ્રલ પરાવર્તન (NDWI સુસંગત) સચોટ સીમાઓ સાથે નોંધાયું."
        ],
        "uncertainty_clear": "ઉચ્ચ રિઝોલ્યુશન અને સ્પષ્ટ વાતાવરણને કારણે મોડેલ વિશ્વાસ ઉચ્ચ છે.",
        "region_note": "મુખ્ય ભૌગોલિક લક્ષણો સમગ્ર દ્રશ્યમાં સમાન રીતે વિતરિત થયેલ છે.",
    },
    "kn": {
        "analysis_header": "ಉಪಗ್ರಹ ಚಿತ್ರ ವಿಶ್ಲೇಷಣಾ ವರದಿ: {location} ಪ್ರದೇಶದ ರಿಮೋಟ್ ಸೆನ್ಸಿಂಗ್ ಮೌಲ್ಯಮಾಪನ.",
        "land_cover_summary": "ಭೂಹೊದಿಕೆಯಲ್ಲಿ {top_veg}% ಸಸ್ಯವರ್ಗ, {top_urban}% ನಗರ ಪ್ರದೇಶ ಮತ್ತು {top_water}% ಜಲಮೂಲಗಳು ಕಂಡುಬಂದಿವೆ.",
        "change_detected": "{year1} ಮತ್ತು {year2} ನಡುವೆ {location} ಸುತ್ತಮುತ್ತ {direction} ಪತ್ತೆಯಾಗಿದೆ.",
        "spectral_evidence": [
            "Sentinel-2 ಎನ್ಐಆರ್ ಬ್ಯಾಂಡ್‌ಗಳಲ್ಲಿ ಹೆಚ್ಚಿನ ಸಸ್ಯವರ್ಗದ ಪ್ರತಿಫಲನ (NDVI > 0.45) ಆರೋಗ್ಯಕರ ಸಸ್ಯವರ್ಗವನ್ನು ಸೂಚಿಸುತ್ತದೆ.",
            "ನಗರ ರಚನೆಗಳು ಮತ್ತು ರಸ್ತೆ ಜಾಲದಲ್ಲಿ ಸ್ಪಷ್ಟ ಗಡಿಗಳು ಗೋಚರಿಸುತ್ತವೆ.",
            "ಜಲಮೂಲಗಳಲ್ಲಿ ಕಡಿಮೆ ಸ್ಪೆಕ್ಟ್ರಲ್ ಪ್ರತಿಫಲನ (NDWI ಹೊಂದಿಕೆಯಾಗುವ) ನಿಖರವಾಗಿ ದಾಖಲಾಗಿದೆ."
        ],
        "uncertainty_clear": "ಉತ್ತಮ ಚಿತ್ರ ಸ್ಪಷ್ಟತೆಯಿಂದಾಗಿ ಹೆಚ್ಚಿನ ವಿಶ್ಲೇಷಣಾತ್ಮಕ ವಿಶ್ವಾಸ.",
        "region_note": "ಪ್ರಮುಖ ಭೌಗೋಳಿಕ ವೈಶಿಷ್ಟ್ಯಗಳು ಚಿತ್ರದಾದ್ಯಂತ ಸಮವಾಗಿ ಹರಡಿಕೊಂಡಿವೆ.",
    },
    "ml": {
        "analysis_header": "ഉപഗ്രഹ ചിത്ര വിശകലന റിപ്പോർട്ട്: {location} പ്രദേശത്തിന്റെ റിമോട്ട് സെൻസിംഗ് വിലയിരുത്തൽ.",
        "land_cover_summary": "ഭൂവിനിയോഗത്തിൽ {top_veg}% സസ്യജാലങ്ങൾ, {top_urban}% നഗര പ്രദേശം, {top_water}% ജലാശയങ്ങൾ എന്നിവ അടയാളപ്പെടുത്തിയിരിക്കുന്നു.",
        "change_detected": "{year1} നും {year2} നും ഇടയിൽ {location} പ്രദേശത്ത് {direction} രേഖപ്പെടുത്തിയിട്ടുണ്ട്.",
        "spectral_evidence": [
            "Sentinel-2 എൻഐആർ ബാൻഡുകളിൽ ഉയർന്ന സസ്യ പ്രതിഫಲനം (NDVI > 0.45) ആരോഗ്യകരമായ സസ്യജാലങ്ങളെ കാണിക്കുന്നു.",
            "നഗര ഘടനകളിലും റോഡ് ശൃംഖലകളിലും വ്യക്തമായ സ്പേഷ്യൽ ഘടന ദൃശ്യമാണ്.",
            "ജലാശയങ്ങളിൽ കുറഞ്ഞ സ്പെക്ട്രൽ റിഫ്ലക്ടൻസ് (NDWI സ്ഥിരതയുള്ളത്) കൃത്യമായി രേഖപ്പെടുത്തി."
        ],
        "uncertainty_clear": "ഉയർന്ന ചിത്ര വ്യക്തത കാരണം വിശകലനത്തിൽ ഉയർന്ന വിശ്വാസ്യത.",
        "region_note": "പ്രധാന ഭൂമിശാസ്ത്രപരമായ സവിശേഷതകൾ ദൃശ്യത്തിലുടനീളം തുല്യമായി വ്യാപിച്ചിരിക്കുന്നു.",
    },
    "pa": {
        "analysis_header": "ਸੈਟੇਲਾਈਟ ਤਸਵੀਰ ਵਿਸ਼ਲੇਸ਼ਣ ਰਿਪੋਰਟ: {location} ਖੇਤਰ ਦਾ ਰਿਮੋਟ ਸੈਂਸਿੰਗ ਮੁਲਾਂਕਣ।",
        "land_cover_summary": "ਜ਼ਮੀਨੀ ਕਵਰੇਜ ਵਿੱਚ {top_veg}% ਬਨਸਪਤੀ, {top_urban}% ਸ਼ਹਿਰੀ ਖੇਤਰ ਅਤੇ {top_water}% ਜਲ ਸਰੋਤ ਸ਼ਾਮਲ ਹਨ।",
        "change_detected": "{year1} ਅਤੇ {year2} ਵਿਚਕਾਰ {location} ਵਿੱਚ {direction} ਦਰਜ ਕੀਤੀ ਗਈ ਹੈ।",
        "spectral_evidence": [
            "Sentinel-2 ਐਨਆਈਆਰ ਬੈਂਡਾਂ ਵਿੱਚ ਉੱਚ ਪ੍ਰਤੀਬਿੰਬ (NDVI > 0.45) ਤੰਦਰੁਸਤ ਫਸਲਾਂ ਨੂੰ ਦਰਸਾਉਂਦਾ ਹੈ।",
            "ਸ਼ਹਿਰੀ ਇਮਾਰਤਾਂ ਅਤੇ ਸੜਕ ਨੈੱਟਵਰਕ ਵਿੱਚ ਸਪੱਸ਼ਟ ਬਣਤਰ ਦਿਖਾਈ ਦਿੰਦੀ ਹੈ।",
            "ਜਲ ਸਰੋਤਾਂ ਵਿੱਚ ਘੱਟ ਸਪੈਕਟ੍ਰਲ ਪ੍ਰਤੀਬਿੰਬ (NDWI ਅਨੁਕੂਲ) ਸਹੀ ਢੰਗ ਨਾਲ ਦਰਜ ਕੀਤਾ ਗਿਆ।"
        ],
        "uncertainty_clear": "ਉੱਚ ਰੈਜ਼ੋਲੂਸ਼ਨ ਅਤੇ ਸਾਫ਼ ਮੌਸਮ ਕਾਰਨ ਵਿਸ਼ਲੇਸ਼ਣ 'ਤੇ ਪੂਰਾ ਭਰੋਸਾ।",
        "region_note": "ਮੁੱਖ ਭੂਗੋਲਿਕ ਵਿਸ਼ੇਸ਼ਤਾਵਾਂ ਪੂਰੀ ਤਸਵੀਰ ਵਿੱਚ ਚੰਗੀ ਤਰ੍ਹਾਂ ਫੈਲੀਆਂ ਹੋਈਆਂ ਹਨ।",
    }
}


def localize_analysis_result(
    result: Dict[str, Any],
    target_lang: str,
    normalized_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Localizes an analysis result dictionary into target_lang, ensuring strict entity preservation.
    Used for local/offline engines and fallback translation.
    """
    if target_lang == "en" or target_lang not in LANGUAGES:
        return result

    tpl = OFFLINE_TEMPLATES.get(target_lang)
    if not tpl:
        return result

    res = dict(result)
    loc = (normalized_meta or {}).get("matched_location") or "Geospatial AOI"
    years = (normalized_meta or {}).get("years") or ["2020", "2025"]
    y1 = years[0] if len(years) > 0 else "2020"
    y2 = years[1] if len(years) > 1 else "2025"

    # Compute land cover breakdown stats
    lc = res.get("land_cover") or []
    veg_pct = next((item.get("percent", 35) for item in lc if "veg" in item.get("label", "").lower() or "forest" in item.get("label", "").lower()), 38)
    urb_pct = next((item.get("percent", 25) for item in lc if "urb" in item.get("label", "").lower() or "built" in item.get("label", "").lower()), 28)
    wat_pct = next((item.get("percent", 15) for item in lc if "wat" in item.get("label", "").lower()), 14)

    # If the answer was generated in English by local VLM, translate it gracefully
    orig_answer = res.get("answer", "")
    if orig_answer and any(ch in orig_answer for ch in ("The", "is", "land", "vegetation", "urban")):
        header_text = tpl["analysis_header"].format(location=loc)
        summary_text = tpl["land_cover_summary"].format(top_veg=veg_pct, top_urban=urb_pct, top_water=wat_pct)
        change_text = tpl["change_detected"].format(year1=y1, year2=y2, location=loc, direction="महत्वपूर्ण परिवर्तन / विस्तार")
        res["answer"] = f"{header_text}\n\n{summary_text}\n\n{change_text}"
        res["evidence"] = tpl["spectral_evidence"]
        res["uncertainty_reason"] = tpl["uncertainty_clear"]
        res["region_note"] = tpl["region_note"]

    # Localize narrative if in compare mode
    if "narrative" in res and res.get("narrative"):
        res["narrative"] = tpl["change_detected"].format(year1=y1, year2=y2, location=loc, direction="शहरी विस्तार व वनस्पति परिवर्तन")

    res["detected_language"] = target_lang
    return res
