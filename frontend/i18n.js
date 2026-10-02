/**
 * SatQuery AI - Centralized Internationalization (i18n) Engine
 * Supports 10 languages: English, Hindi, Marathi, Tamil, Telugu, Bengali, Gujarati, Kannada, Malayalam, Punjabi.
 * Features:
 * - Proper i18n structure with external JSON locale files + bundled fallback
 * - Automatic fallback to English for any missing keys
 * - Full preservation of original English HTML layout & styling
 * - Dynamic UI translation across labels, placeholders, tooltips, buttons
 * - Speech-to-text Web Speech API integration with Indic BCP-47 codes
 * - LocalStorage persistence and reactive change events
 */

(function (window) {
  "use strict";

  const SUPPORTED_LANGUAGES = [
    { code: "en", name: "English", nativeName: "English", display: "English", speech: "en-IN" },
    { code: "hi", name: "Hindi", nativeName: "हिन्दी", display: "हिन्दी – Hindi", speech: "hi-IN" },
    { code: "mr", name: "Marathi", nativeName: "मराठी", display: "मराठी – Marathi", speech: "mr-IN" },
    { code: "ta", name: "Tamil", nativeName: "தமிழ்", display: "தமிழ் – Tamil", speech: "ta-IN" },
    { code: "te", name: "Telugu", nativeName: "తెలుగు", display: "తెలుగు – Telugu", speech: "te-IN" },
    { code: "bn", name: "Bengali", nativeName: "বাংলা", display: "বাংলা – Bengali", speech: "bn-IN" },
    { code: "gu", name: "Gujarati", nativeName: "ગુજરાતી", display: "ગુજરાતી – Gujarati", speech: "gu-IN" },
    { code: "kn", name: "Kannada", nativeName: "ಕನ್ನಡ", display: "ಕನ್ನಡ – Kannada", speech: "kn-IN" },
    { code: "ml", name: "Malayalam", nativeName: "മലയാളം", display: "മലയാളം – Malayalam", speech: "ml-IN" },
    { code: "pa", name: "Punjabi", nativeName: "ਪੰਜਾਬੀ", display: "ਪੰਜਾਬੀ – Punjabi", speech: "pa-IN" },
  ];

  // Map flat data-i18n keys to nested JSON dictionary paths
  const KEY_ALIASES = {
    header_subtitle: "app.subtitle",
    nav_benchmarks: "header.benchmarks",
    nav_history: "header.history",
    nav_location_explorer: "header.location_explorer",
    nav_reset: "header.reset",
    nav_logout: "header.logout",
    tab_analyze: "tabs.analyze",
    tab_compare: "tabs.compare",
    tab_crossmodal: "tabs.crossmodal",
    tab_location: "tabs.location_explorer",
    source_label: "analyze.data_source_label",
    source_s2: "analyze.ds_sentinel2",
    source_s1: "analyze.ds_sentinel1",
    source_fusion: "analyze.ds_fusion",
    source_bhuvan: "analyze.ds_bhuvan",
    domain_mode_label: "analyze.mode_label",
    mode_general: "analyze.mode_general",
    mode_agri: "analyze.mode_agriculture",
    mode_disaster: "analyze.mode_disaster",
    mode_urban: "analyze.mode_urban",
    mode_env: "analyze.mode_environment",
    mode_grounding: "analyze.mode_grounding",
    mode_seg: "analyze.mode_segmentation",
    image_upload_label: "analyze.upload_label",
    dropzone_hint: "analyze.dropzone_hint",
    dropzone_hint_sm: "analyze.dropzone_hint_sm",
    question_label: "analyze.question_label",
    question_placeholder: "analyze.question_placeholder",
    voice_input: "analyze.voice_input",
    run_analysis_btn: "analyze.run_btn",
    loading_text: "analyze.running_reasoning",
    analysis_output_header: "analyze.output_header",
    results_empty: "analyze.empty_results",
    btn_report: "analyze.report_btn",
    date_before_label: "compare.date1_before",
    date_after_label: "compare.date2_after",
    run_compare_btn: "compare.run_btn",
    change_analysis_header: "compare.title",
    compare_empty: "compare.empty",
    optical_upload_label: "crossmodal.opt_label",
    sar_upload_label: "crossmodal.sar_label",
    run_crossmodal_btn: "crossmodal.run_btn",
    multimodal_synthesis_header: "crossmodal.title",
    crossmodal_empty: "crossmodal.empty",
    home_studio: "header.home_studio",
  };

  const EXPLORER_TRANSLATIONS = {
    en: {
      loc_title: "Location Explorer",
      loc_subtitle: "Gemini 2.0 Flash · Interactive Earth Observation",
      home_studio: "← Home Studio",
      theme_toggle: "🌓 Theme",
      search_placeholder: "Search any place or coordinates (e.g., Pune, Dubai)...",
      detect_my_location: "Detect My Location",
      detect_tooltip: "Detect Current Location (GPS / Network)",
      voice_tooltip: "Voice Search (Click and Speak)",
      layer_sat: "Satellite",
      layer_hybrid: "Hybrid",
      layer_street: "Streets",
      hud_terrain: "3D TERRAIN ON",
      area_intel: "Area Intelligence",
      empty_title: "No Area Selected",
      empty_desc: "Type a city or click a preset chip to fly to coordinates and synthesize Gemini 2.0 Flash geospatial intelligence.",
      analyzing_title: "Analyzing Viewport Raster...",
      analyzing_desc: "Querying Gemini 2.0 Flash Earth Observation Engine",
      meta_coords: "COORDINATES",
      meta_bbox: "BOUNDING BOX",
      meta_latency: "LATENCY",
      meta_sensors: "SENSOR BANDS",
      print_dossier: "🖨️ Print ISRO Dossier",
      export_json: "📥 Export JSON",
      copy_summary: "📋 Copy Summary",
      followup_placeholder: "Ask about this area (e.g. flood hazard, vegetation density)...",
      btn_ask: "ASK",
    },
    hi: {
      loc_title: "लोकेशन एक्सप्लोरर",
      loc_subtitle: "Gemini 2.0 Flash · इंटरएक्टिव रिमोट सेंसिंग व भू-स्थानिक अन्वेषण",
      home_studio: "← मुख्य स्टूडियो",
      theme_toggle: "🌓 थीम",
      search_placeholder: "स्थान या निर्देशांक खोजें (जैसे: पुणे, मुंबई, दुबई)...",
      detect_my_location: "मेरा स्थान पहचानें",
      detect_tooltip: "वर्तमान GPS/नेटवर्क स्थान का पता लगाएं",
      voice_tooltip: "वॉयस इनपुट (बोलकर खोजें)",
      layer_sat: "सैटेलाइट",
      layer_hybrid: "हाइब्रिड",
      layer_street: "सड़कें",
      hud_terrain: "3D भू-भाग सक्रिय",
      area_intel: "क्षेत्रीय उपग्रह बुद्धिमत्ता",
      empty_title: "कोई क्षेत्र चयनित नहीं",
      empty_desc: "निर्देशांकों पर जाने और Gemini 2.0 Flash भू-स्थानिक बुद्धिमत्ता रिपोर्ट प्राप्त करने के लिए शहर खोजें या प्रीसेट चुनें।",
      analyzing_title: "व्यूपोर्ट रास्टर का विश्लेषण हो रहा है...",
      analyzing_desc: "Gemini 2.0 Flash अर्थ ऑब्जर्वेशन इंजन से विश्लेषण जारी है",
      meta_coords: "निर्देशांक",
      meta_bbox: "बाउंडिंग बॉक्स",
      meta_latency: "विलंबता",
      meta_sensors: "सेंसर बैंड्स",
      print_dossier: "🖨️ ISRO डॉसियर प्रिंट करें",
      export_json: "📥 JSON डाउनलोड करें",
      copy_summary: "📋 सारांश कॉपी करें",
      followup_placeholder: "इस क्षेत्र के बारे में पूछें (जैसे: बाढ़ जोखिम, वनस्पति घनत्व)...",
      btn_ask: "पूछें",
    },
    mr: {
      loc_title: "स्थान अन्वेषक",
      loc_subtitle: "Gemini 2.0 Flash · परस्परसंवादी उपग्रह भू-स्थानिक अन्वेषण",
      home_studio: "← मुख्य स्टुडिओ",
      theme_toggle: "🌓 थीम",
      search_placeholder: "ठिकाण किंवा समन्वय शोधा (उदा. पुणे, मुंबई, दुबई)...",
      detect_my_location: "माझे स्थान शोधा",
      detect_tooltip: "सद्य GPS/नेटवर्क स्थानाचा शोध घ्या",
      voice_tooltip: "व्हॉइस इनपुट (बोलून शोधा)",
      layer_sat: "उपग्रह",
      layer_hybrid: "हायब्रिड",
      layer_street: "रस्ते",
      hud_terrain: "3D भूप्रदेश सुरू",
      area_intel: "क्षेत्रीय उपग्रह बुद्धिमत्ता",
      empty_title: "कोणतेही क्षेत्र निवडलेले नाही",
      empty_desc: "समन्वयांवर जाण्यासाठी आणि Gemini 2.0 Flash भू-स्थानिक विश्लेषण मिळवण्यासाठी शहर शोधा किंवा प्रीसेट निवडा.",
      analyzing_title: "व्यूपोर्ट रॅस्टरचे विश्लेषण सुरू आहे...",
      analyzing_desc: "Gemini 2.0 Flash अर्थ ऑब्झर्व्हेशन इंजिनकडून विश्लेषण सुरू आहे",
      meta_coords: "समन्वय",
      meta_bbox: "बाउंडिंग बॉक्स",
      meta_latency: "लेटन्सी",
      meta_sensors: "सेंसर बँड्स",
      print_dossier: "🖨️ ISRO डॉसियर प्रिंट करा",
      export_json: "📥 JSON डाउनलोड करा",
      copy_summary: "📋 सारांश कॉपी करा",
      followup_placeholder: "या क्षेत्राबद्दल विचारा (उदा. पूर धोका, वनस्पती घनता)...",
      btn_ask: "विचारा",
    },
    ta: {
      loc_title: "இருப்பிட ஆய்வாளர்",
      loc_subtitle: "Gemini 2.0 Flash · ஊடாடும் பூமி கண்காணிப்பு நுண்ணறிவு",
      home_studio: "← முதன்மை ஸ்டுடியோ",
      theme_toggle: "🌓 தீம்",
      search_placeholder: "இடம் அல்லது ஒருங்கிணைப்புகளைத் தேடுங்கள் (எ.கா. சென்னை, மதுரை)...",
      detect_my_location: "என் இருப்பிடத்தைக் கண்டறி",
      detect_tooltip: "தற்போதைய GPS இருப்பிடத்தைக் கண்டறியவும்",
      voice_tooltip: "குரல் உள்ளீடு (பேசித் தேடவும்)",
      layer_sat: "செயற்கைக்கோள்",
      layer_hybrid: "ஹைப்ரிட்",
      layer_street: "சாலைகள்",
      hud_terrain: "3D நிலப்பரப்பு இயங்குகிறது",
      area_intel: "பகுதி செயற்கைக்கோள் நுண்ணறிவு",
      empty_title: "பகுதி தேர்ந்தெடுக்கப்படவில்லை",
      empty_desc: "ஒரு நகரத்தைத் தட்டச்சு செய்யவும் அல்லது செயற்கைக்கோள் நுண்ணறிவைப் பெற முன்னமைவைத் தேர்ந்தெடுக்கவும்.",
      analyzing_title: "காட்சிப் பகுதி பகுப்பாய்வு செய்யப்படுகிறது...",
      analyzing_desc: "Gemini 2.0 Flash பூமி கண்காணிப்பு இயந்திரம் செயல்படுகிறது",
      meta_coords: "ஆயத்தொலைவுகள்",
      meta_bbox: "எல்லைப் பெட்டி",
      meta_latency: "மறைநிலை",
      meta_sensors: "சென்சார் பட்டைகள்",
      print_dossier: "🖨️ ISRO ஆவணத்தை அச்சிடுக",
      export_json: "📥 JSON ஏற்றுமதி",
      copy_summary: "📋 சுருக்கத்தை நகலெடு",
      followup_placeholder: "இப்பகுதி பற்றி கேளுங்கள் (எ.கா. வெள்ள அபாயம், தாவர அடர்த்தி)...",
      btn_ask: "கேள்",
    },
    te: {
      loc_title: "లొకేషన్ ఎక్స్‌ప్లోరర్",
      loc_subtitle: "Gemini 2.0 Flash · ఇంటరాక్టివ్ ఎర్త్ అబ్జర్వేషన్",
      home_studio: "← హోమ్ స్టూడియో",
      theme_toggle: "🌓 థీమ్",
      search_placeholder: "ప్రదేశం లేదా కోఆర్డినేట్లను శోధించండి (ఉదా. హైదరాబాద్, విశాఖ)...",
      detect_my_location: "నా లొకేషన్‌ను గుర్తించు",
      detect_tooltip: "ప్రస్తుత GPS స్థానాన్ని గుర్తించండి",
      voice_tooltip: "వాయిస్ ఇన్పుట్ (మాట్లాడి శోధించండి)",
      layer_sat: "శాటిలైట్",
      layer_hybrid: "హైబ్రిడ్",
      layer_street: "రోడ్లు",
      hud_terrain: "3D భూభాగం ఆన్",
      area_intel: "ప్రాంత శాటిలైట్ సమాచారం",
      empty_title: "ఏ ప్రాంతం ఎంపిక కాలేదు",
      empty_desc: "Gemini 2.0 Flash జియోస్పేషియల్ సమాచారం కోసం నగరాన్ని నమోదు చేయండి లేదా ప్రీసెట్‌పై క్లిక్ చేయండి.",
      analyzing_title: "రాస్టర్ విశ్లేషణ జరుగుతోంది...",
      analyzing_desc: "Gemini 2.0 Flash ఎర్త్ అబ్జర్వేషన్ ఇంజిన్ విశ్లేషిస్తోంది",
      meta_coords: "కోఆర్డినేట్లు",
      meta_bbox: "బౌండింగ్ బాక్స్",
      meta_latency: "లేటెన్సీ",
      meta_sensors: "సెన్సార్ బ్యాండ్లు",
      print_dossier: "🖨️ ISRO పత్రం ప్రింట్ చేయండి",
      export_json: "📥 JSON ఎగుమతి",
      copy_summary: "📋 కాపీ సారాంశం",
      followup_placeholder: "ఈ ప్రాంతం గురించి అడగండి (ఉదా. వరద ప్రమాదం, పచ్చదనం సాంద్రత)...",
      btn_ask: "అడుగు",
    },
    bn: {
      loc_title: "লোকেশন এক্সপ্লোরার",
      loc_subtitle: "Gemini 2.0 Flash · ইন্টারেক্টিভ আর্থ অবজারভেশন",
      home_studio: "← হোম স্টুডিও",
      theme_toggle: "🌓 থিম",
      search_placeholder: "স্থান বা স্থানাঙ্ক অনুসন্ধান করুন (যেমন: কলকাতা, ঢাকা, পুনে)...",
      detect_my_location: "আমার অবস্থান শনাক্ত করুন",
      detect_tooltip: "বর্তমান GPS অবস্থান নির্ণয় করুন",
      voice_tooltip: "ভয়েস ইনপুট (কথা বলে অনুসন্ধান করুন)",
      layer_sat: "স্যাটেলাইট",
      layer_hybrid: "হাইব্রিড",
      layer_street: "রাস্তা",
      hud_terrain: "3D ভূখণ্ড সক্রিয়",
      area_intel: "এলাকার স্যাটেলাইট বুদ্ধিমত্তা",
      empty_title: "কোনো এলাকা নির্বাচিত নেই",
      empty_desc: "Gemini 2.0 Flash স্যাটেলাইট বিশ্লেষণ তৈরি করতে একটি শহর টাইপ করুন বা প্রিসেট নির্বাচন করুন।",
      analyzing_title: "রাস্টার বিশ্লেষণ চলছে...",
      analyzing_desc: "Gemini 2.0 Flash আর্থ অবজারভেশন ইঞ্জিন কাজ করছে",
      meta_coords: "স্থানাঙ্ক",
      meta_bbox: "বাউন্ডিং বক্স",
      meta_latency: "বিলম্ব",
      meta_sensors: "সেন্সর ব্যান্ড",
      print_dossier: "🖨️ ISRO ডসিয়ার প্রিন্ট করুন",
      export_json: "📥 JSON এক্সপোর্ট",
      copy_summary: "📋 কপি সারাংশ",
      followup_placeholder: "এই এলাকা সম্পর্কে জিজ্ঞাসা করুন (যেমন: বন্যা ঝুঁকি, গাছপালার ঘনত্ব)...",
      btn_ask: "জিজ্ঞাসা করুন",
    },
    gu: {
      loc_title: "લોકેશન એક્સપ્લોરર",
      loc_subtitle: "Gemini 2.0 Flash · ઇન્ટરેક્ટિવ અર્થ ઓબ્ઝર્વેશન",
      home_studio: "← મુખ્ય સ્ટુડિયો",
      theme_toggle: "🌓 થીમ",
      search_placeholder: "સ્થળ અથવા કોઓર્ડિનેટ્સ શોધો (દા.ત. અમદાવાદ, સુરત, પુણે)...",
      detect_my_location: "મારું સ્થાન શોધો",
      detect_tooltip: "વર્તમાન GPS સ્થાન શોધો",
      voice_tooltip: "વૉઇસ ઇનપુટ (બોલીને શોધો)",
      layer_sat: "સેટેલાઇટ",
      layer_hybrid: "હાઇબ્રિડ",
      layer_street: "રસ્તાઓ",
      hud_terrain: "3D ભૂપ્રદેશ ચાલુ",
      area_intel: "વિસ્તાર સેટેલાઇટ વિશ્લેષણ",
      empty_title: "કોઈ વિસ્તાર પસંદ કરેલ નથી",
      empty_desc: "Gemini 2.0 Flash સેટેલાઇટ ઇન્ટેલિજન્સ મેળવવા માટે શહેર લખો અથવા પ્રીસેટ પર ક્લિક કરો.",
      analyzing_title: "રાસ્ટરનું વિશ્લેષણ થઈ રહ્યું છે...",
      analyzing_desc: "Gemini 2.0 Flash અર્થ ઓબ્ઝર્વેશન એન્જિન કાર્યરત છે",
      meta_coords: "કોઓર્ડિનેટ્સ",
      meta_bbox: "બાઉન્ડિંગ બોક્સ",
      meta_latency: "લેટન્સી",
      meta_sensors: "સેન્સર બેન્ડ્સ",
      print_dossier: "🖨️ ISRO દસ્તાવેજ પ્રિન્ટ કરો",
      export_json: "📥 JSON ડાઉનલોડ",
      copy_summary: "📋 સારાંશ કૉપિ કરો",
      followup_placeholder: "આ વિસ્તાર વિશે પૂછો (દા.ત. પૂરનું જોખમ, વનસ્પતિ ઘનતા)...",
      btn_ask: "પૂછો",
    },
    kn: {
      loc_title: "ಸ್ಥಳ ಪರಿಶೋಧಕ",
      loc_subtitle: "Gemini 2.0 Flash · ಸಂವಾದಾತ್ಮಕ ಭೂ ವೀಕ್ಷಣೆ",
      home_studio: "← ಮುಖ್ಯ ಸ್ಟುಡಿಯೋ",
      theme_toggle: "🌓 ಥೀಮ್",
      search_placeholder: "ಸ್ಥಳ ಅಥವಾ ನಿರ್ದೇಶಾಂಕಗಳನ್ನು ಹುಡುಕಿ (ಉದಾ. ಬೆಂಗಳೂರು, ಮೈಸೂರು)...",
      detect_my_location: "ನನ್ನ ಸ್ಥಳವನ್ನು ಗುರುತಿಸಿ",
      detect_tooltip: "ಪ್ರಸ್ತುತ GPS ಸ್ಥಳವನ್ನು ಪತ್ತೆಹಚ್ಚಿ",
      voice_tooltip: "ಧ್ವನಿ ಇನ್‌ಪುಟ್ (ಮಾತನಾಡಿ ಹುಡುಕಿ)",
      layer_sat: "ಉಪಗ್ರಹ",
      layer_hybrid: "ಹೈಬ್ರಿಡ್",
      layer_street: "ರಸ್ತೆಗಳು",
      hud_terrain: "3D ಭೂಪ್ರದೇಶ ಆನ್ ಆಗಿದೆ",
      area_intel: "ಪ್ರದೇಶ ಉಪಗ್ರಹ ಬುದ್ಧಿಮತ್ತೆ",
      empty_title: "ಯಾವುದೇ ಪ್ರದೇಶ ಆಯ್ಕೆಯಾಗಿಲ್ಲ",
      empty_desc: "Gemini 2.0 Flash ಉಪಗ್ರಹ ವರದಿಗಾಗಿ ನಗರವನ್ನು ನಮೂದಿಸಿ ಅಥವಾ ಪೂರ್ವನಿಗದಿತ ಸ್ಥಳವನ್ನು ಕ್ಲಿಕ್ ಮಾಡಿ.",
      analyzing_title: "ರಾಸ್ಟರ್ ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...",
      analyzing_desc: "Gemini 2.0 Flash ಭೂ ವೀಕ್ಷಣಾ ಎಂಜಿನ್ ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತಿದೆ",
      meta_coords: "ನಿರ್ದೇಶಾಂಕಗಳು",
      meta_bbox: "ಬೌಂಡಿಂಗ್ ಬಾಕ್ಸ್",
      meta_latency: "ಲೇಟೆನ್ಸಿ",
      meta_sensors: "ಸೆನ್ಸರ್ ಬ್ಯಾಂಡ್‌ಗಳು",
      print_dossier: "🖨️ ISRO ಡಾಕ್ಯುಮೆಂಟ್ ಮುದ್ರಿಸಿ",
      export_json: "📥 JSON ರಫ್ತು ಮಾಡಿ",
      copy_summary: "📋 ಸಾರಾಂಶ ಕಾಪಿ ಮಾಡಿ",
      followup_placeholder: "ಈ ಪ್ರದೇಶದ ಬಗ್ಗೆ ಕೇಳಿ (ಉದಾ. ಪ್ರವಾಹ ಅಪಾಯ, ಹಸಿರು ಸಾಂದ್ರತೆ)...",
      btn_ask: "ಕೇಳಿ",
    },
    ml: {
      loc_title: "ലൊക്കേഷൻ എക്സ്പ്ലോറർ",
      loc_subtitle: "Gemini 2.0 Flash · സംവേദനാത്മക ഭൂനിരീക്ഷണ ഇന്റലിജൻസ്",
      home_studio: "← ഹോം സ്റ്റുഡിയോ",
      theme_toggle: "🌓 തീം",
      search_placeholder: "സ്ഥലമോ കോർഡിനേറ്റുകളോ തിരയുക (ഉദാ. കൊച്ചി, തിരുവനന്തപുരം)...",
      detect_my_location: "എന്റെ സ്ഥാനം കണ്ടെത്തുക",
      detect_tooltip: "നിലവിലെ GPS സ്ഥാനം കണ്ടെത്തുക",
      voice_tooltip: "വോയ്സ് ഇൻപുട്ട് (സംസാരിച്ച് തിരയുക)",
      layer_sat: "ഉപഗ്രഹം",
      layer_hybrid: "ഹൈബ്രിഡ്",
      layer_street: "റോഡുകൾ",
      hud_terrain: "3D ഭൂപ്രദേശം സജീവം",
      area_intel: "പ്രദേശ ഉപഗ്രഹ ഇന്റലിജൻസ്",
      empty_title: "പ്രദേശം തിരഞ്ഞെടുത്തിട്ടില്ല",
      empty_desc: "Gemini 2.0 Flash ഉപഗ്രഹ റിപ്പോർട്ട് ലഭിക്കുന്നതിന് ഒരു നഗരം നൽകുകയോ പ്രീസെറ്റ് ക്ലിക്ക് ചെയ്യുകയോ ചെയ്യുക.",
      analyzing_title: "റാസ്റ്റർ വിശകലനം ചെയ്യുന്നു...",
      analyzing_desc: "Gemini 2.0 Flash എർത്ത് ഒബ്സർവേഷൻ എഞ്ചിൻ പ്രവർത്തിക്കുന്നു",
      meta_coords: "കോർഡിനേറ്റുകൾ",
      meta_bbox: "ബൗണ്ടിംഗ് ബോക്സ്",
      meta_latency: "ലേറ്റൻസി",
      meta_sensors: "സെൻസർ ബാൻഡുകൾ",
      print_dossier: "🖨️ ISRO രേഖ പ്രിന്റ് ചെയ്യുക",
      export_json: "📥 JSON ഡൗൺലോഡ്",
      copy_summary: "📋 സംഗ്രഹം പകർത്തുക",
      followup_placeholder: "ഈ പ്രദേശത്തെക്കുറിച്ച് ചോദിക്കുക (ഉദാ. വെള്ളപ്പൊക്ക സാധ്യത, സസ്യ സാന്ദ്രത)...",
      btn_ask: "ചോദിക്കുക",
    },
    pa: {
      loc_title: "ਸਥਾਨ ਖੋਜਕਰਤਾ",
      loc_subtitle: "Gemini 2.0 Flash · ਇੰਟਰਐਕਟਿਵ ਅਰਥ ਆਬਜ਼ਰਵੇਸ਼ਨ",
      home_studio: "← ਮੁੱਖ ਸਟੂਡੀਓ",
      theme_toggle: "🌓 ਥੀਮ",
      search_placeholder: "ਸਥਾਨ ਜਾਂ ਕੋਆਰਡੀਨੇਟ ਖੋਜੋ (ਜਿਵੇਂ: ਅੰਮ੍ਰਿਤਸਰ, ਲੁਧਿਆਣਾ, ਪੁਣੇ)...",
      detect_my_location: "ਮੇਰਾ ਸਥਾਨ ਲੱਭੋ",
      detect_tooltip: "ਮੌਜੂਦਾ GPS ਸਥਾਨ ਦਾ ਪਤਾ ਲਗਾਓ",
      voice_tooltip: "ਆਵਾਜ਼ ਇਨਪੁਟ (ਬੋਲ ਕੇ ਖੋਜੋ)",
      layer_sat: "ਸੈਟੇਲਾਈਟ",
      layer_hybrid: "ਹਾਈਬ੍ਰਿਡ",
      layer_street: "ਸੜਕਾਂ",
      hud_terrain: "3D ਖੇਤਰ ਚਾਲੂ",
      area_intel: "ਖੇਤਰੀ ਸੈਟੇਲਾਈਟ ਵਿਸ਼ਲੇਸ਼ਣ",
      empty_title: "ਕੋਈ ਖੇਤਰ ਚੁਣਿਆ ਨਹੀਂ",
      empty_desc: "Gemini 2.0 Flash ਸੈਟੇਲਾਈਟ ਰਿਪੋਰਟ ਪ੍ਰਾਪਤ ਕਰਨ ਲਈ ਸ਼ਹਿਰ ਲਿਖੋ ਜਾਂ ਪ੍ਰੀਸੈੱਟ ਚੁਣੋ।",
      analyzing_title: "ਰਾਸਟਰ ਦਾ ਵਿਸ਼ਲੇਸ਼ਣ ਕੀਤਾ ਜਾ ਰਿਹਾ ਹੈ...",
      analyzing_desc: "Gemini 2.0 Flash ਅਰਥ ਆਬਜ਼ਰਵੇਸ਼ਨ ਇੰਜਣ ਕੰਮ ਕਰ ਰਿਹਾ ਹੈ",
      meta_coords: "ਕੋਆਰਡੀਨੇਟ",
      meta_bbox: "ਬਾਊਂਡਿੰਗ ਬਾਕਸ",
      meta_latency: "ਲੇਟੈਂਸੀ",
      meta_sensors: "ਸੈਂਸਰ ਬੈਂਡ",
      print_dossier: "🖨️ ISRO ਦਸਤਾਵੇਜ਼ ਪ੍ਰਿੰਟ ਕਰੋ",
      export_json: "📥 JSON ਡਾਊਨਲੋਡ",
      copy_summary: "📋 ਸਾਰਾਂਸ਼ ਕਾਪੀ ਕਰੋ",
      followup_placeholder: "ਇਸ ਖੇਤਰ ਬਾਰੇ ਪੁੱਛੋ (ਜਿਵੇਂ: ਹੜ੍ਹ ਦਾ ਖਤਰਾ, ਬਨਸਪਤੀ ਘਣਤਾ)...",
      btn_ask: "ਪੁੱਛੋ",
    }
  };

  const EXPLORER_FALLBACK_TEMPLATES = {
    en: (d) => `### 🌍 Macro Geographic Overview\n**${d.name}** is positioned at **${d.lat}°N, ${d.lng}°E**. Bounding envelope spans **[${d.min_lng}, ${d.min_lat}]** to **[${d.max_lng}, ${d.max_lat}]**.\n\n### 🏙️ Urban Morphology & Settlement Density\nActive high-resolution raster tiles confirm mixed density settlement pattern aligned along primary roadway networks.\n\n### 🌿 Environmental Context & Land Cover Dynamics\nSatellite reflectance signatures indicate vegetative cover balanced with built impervious surfaces.\n\n### 🏗️ Critical Infrastructure\nRegional transportation links and municipal connectivity hubs are clearly resolved in the current viewport.\n\n### 🛰️ Remote Sensing Observations & Sensor Recommendations\n- **Sentinel-2 MSI**: Recommended for continuous NDVI and NDWI vegetation/water classification.\n- **Sentinel-1 SAR**: C-band radar recommended for cloud-penetrating surface roughness monitoring.`,
    hi: (d) => `### 🌍 स्थूल भौगोलिक अवलोकन\n**${d.name}** अक्षांश **${d.lat}°N, ${d.lng}°E** पर स्थित है। इसका बाउंडिंग क्षेत्र **[${d.min_lng}, ${d.min_lat}]** से **[${d.max_lng}, ${d.max_lat}]** तक फैला हुआ है।\n\n### 🏙️ शहरी संरचना एवं निर्मित घनत्व\nसक्रिय हाई-रिज़ॉल्यूशन रास्टर टाइलें मुख्य सड़क नेटवर्क के साथ मध्यम से सघन निर्मित संरचनाएं दर्शाती हैं।\n\n### 🌿 पर्यावरणीय संदर्भ एवं भूमि आवरण\nसैटेलाइट परावर्तन पैटर्न निर्मित सतहों के साथ संतुलित वनस्पति और हरियाली आवरण का संकेत देते हैं।\n\n### 🏗️ महत्वपूर्ण बुनियादी ढांचा\nप्रमुख परिवहन संपर्क, सड़कें और नागरिक सुविधाएं वर्तमान व्यूपोर्ट में स्पष्ट रूप से दिखाई दे रही हैं।\n\n### 🛰️ रिमोट सेंसिंग प्रेक्षण एवं सेंसर सिफारिशें\n- **Sentinel-2 MSI**: निरंतर NDVI और NDWI वनस्पति/जल वर्गीकरण हेतु अनुशंसित।\n- **Sentinel-1 SAR**: बादलों के पार सतह खुरदरापन विश्लेषण के लिए C-band रडार अनुशंसित।`,
    mr: (d) => `### 🌍 स्थूल भौगोलिक विहंगावलोकन\n**${d.name}** हे अक्षवृत्त **${d.lat}°N, ${d.lng}°E** वर स्थित आहे. बाउंडिंग क्षेत्र **[${d.min_lng}, ${d.min_lat}]** ते **[${d.max_lng}, ${d.max_lat}]** पर्यंत पसरलेले आहे.\n\n### 🏙️ नागरी रचना आणि वसाहत घनता\nसक्रिय हाय-रिझोल्यूशन रास्टर टाईल्स मुख्य रस्ते नेटवर्कसह नागरी बांधकामांचे अस्तित्व दर्शवतात.\n\n### 🌿 पर्यावरणीय संदर्भ आणि भू-आच्छादन\nउपग्रह परावर्तन नोंदी वनस्पती आणि सिमेंटच्या पक्क्या जमिनीचे संतुलित प्रमाण दर्शवतात.\n\n### 🏗️ महत्त्वपूर्ण पायाभूत सुविधा\nप्रादेशिक वाहतूक मार्ग, महामार्ग आणि नागरी सुविधा वर्तमान व्यूपोर्टमध्ये स्पष्टपणे दृश्यमान आहेत.\n\n### 🛰️ रिमोट सेन्सिंग निरीक्षणे आणि सेन्सर शिफारसी\n- **Sentinel-2 MSI**: सातत्यपूर्ण NDVI आणि NDWI वनस्पती/पाणी वर्गीकरणासाठी शिफारस केलेले.\n- **Sentinel-1 SAR**: ढगांच्या आडून पृष्ठभागाच्या निरीक्षणासाठी C-band रडार शिफारस केलेले.`,
    ta: (d) => `### 🌍 மேக்ரோ புவியியல் கண்ணோட்டம்\n**${d.name}** அட்சரேகை **${d.lat}°N, ${d.lng}°E** இல் அமைந்துள்ளது. எல்லைப் பெட்டி **[${d.min_lng}, ${d.min_lat}]** முதல் **[${d.max_lng}, ${d.max_lat}]** வரை பரவியுள்ளது.\n\n### 🏙️ நகர்ப்புற வடிவமைப்பு மற்றும் குடியிருப்பு அடர்த்தி\nஉயர் தெளிவுத்திறன் கொண்ட செயற்கைக்கோள் ஓடுகள் முதன்மை சாலை நெட்வொர்க்குகளுடன் குடியிருப்பு அடர்த்தியை உறுதிப்படுத்துகின்றன.\n\n### 🌿 சுற்றுச்சூழல் சூழல் மற்றும் நிலப்பரப்பு\nசெயற்கைக்கோள் பிரதிபலிப்பு சமநிலையான தாவர மற்றும் கட்டப்பட்ட பரப்புகளைக் காட்டுகிறது.\n\n### 🏗️ முக்கிய உள்கட்டமைப்பு\nபோக்குவரத்து இணைப்புகள் மற்றும் நகராட்சி மையங்கள் தெளிவாகத் தெரிகின்றன.\n\n### 🛰️ தொலையுணர்வு அவதானிப்புகள் & சென்சார் பரிந்துரைகள்\n- **Sentinel-2 MSI**: தொடர்ச்சியான NDVI மற்றும் NDWI தாவர/நீர் கண்காணிப்புக்கு பரிந்துரைக்கப்படுகிறது.\n- **Sentinel-1 SAR**: மேகமூட்டத்தை ஊடுருவி மேற்பரப்பை கண்காணிக்க C-band ரேடார் பரிந்துரைக்கப்படுகிறது.`,
    te: (d) => `### 🌍 స్థూల భౌగోళిక అవలోకనం\n**${d.name}** అక్షాంశం **${d.lat}°N, ${d.lng}°E** వద్ద ఉంది. బౌండింగ్ బాక్స్ **[${d.min_lng}, ${d.min_lat}]** నుండి **[${d.max_lng}, ${d.max_lat}]** వరకు విస్తరించి ఉంది.\n\n### 🏙️ పట్టణ నిర్మాణం మరియు నివాస సాంద్రత\nహై-రిజల్యూషన్ రాస్టర్ టైల్స్ రహదారి నెట్‌వర్క్‌ల వెంబడి నిర్మాణాలను ధృవీకరిస్తాయి.\n\n### 🌿 పర్యావరణ సందర్భం మరియు భూమి కవరేజ్\nశాటిలైట్ రిఫ్లెక్టెన్స్ సంకేతాలు సమతుల్య వృక్షసంపదను సూచిస్తాయి.\n\n### 🏗️ కీలక మౌలిక సదుపాయాలు\nరవాణా మార్గాలు ప్రస్తుత వ్యూపోర్ట్‌లో స్పష్టంగా కనిపిస్తాయి.\n\n### 🛰️ రిమోట్ సెన్సింగ్ పరిశీలనలు & సెన్సార్ సిఫార్సులు\n- **Sentinel-2 MSI**: నిరంతర NDVI మరియు NDWI వర్గీకరణకు సిఫార్సు చేయబడింది.\n- **Sentinel-1 SAR**: ఆల్-వెదర్ ఉపరితల పర్యవేక్షణకు C-band రాడార్ సిఫార్సు చేయబడింది.`,
    bn: (d) => `### 🌍 সামগ্রিক ভৌগলিক রূপরেখা\n**${d.name}** অক্ষাংশ **${d.lat}°N, ${d.lng}°E**-এ অবস্থিত। বাউন্ডিং অঞ্চল **[${d.min_lng}, ${d.min_lat}]** থেকে **[${d.max_lng}, ${d.max_lat}]** পর্যন্ত বিস্তৃত।\n\n### 🏙️ নগর রূপবিদ্যা ও জনবসতি ঘনত্ব\nসক্রিয় হাই-রেজোলিউশন রাস্টার টাইলস প্রধান সড়ক নেটওয়ার্ক ধরে বসতির বিন্যাস নিশ্চিত করে।\n\n### 🌿 পরিবেশগত প্রেক্ষাপট ও ভূমির আচ্ছাদন\nস্যাটেলাইট প্রতিফলন সংকেত উদ্ভিজ্জ আচ্ছাদন ও নির্মিত পৃষ্ঠের ভারসাম্য নির্দেশ করে।\n\n### 🏗️ গুরুত্বপূর্ণ অবকাঠামো\nআঞ্চলিক যোগাযোগ সংযোগ বর্তমান ভিউপোর্টে স্পষ্টভাবে দৃশ্যমান।\n\n### 🛰️ রিমোট সেন্সিং পর্যবেক্ষণ ও সেন্সর সুপারিশ\n- **Sentinel-2 MSI**: অবিচ্ছিন্ন NDVI এবং NDWI শ্রেণিবিভাগের জন্য অত্যন্ত সুপারিশকৃত।\n- **Sentinel-1 SAR**: মেঘভেদকারী পৃষ্ঠ পর্যবেক্ষণের জন্য C-band রাডার সুপারিশকৃত।`,
    gu: (d) => `### 🌍 સમગ્ર ભૌગોલિક ઝાંખી\n**${d.name}** અક્ષાંશ **${d.lat}°N, ${d.lng}°E** પર આવેલું છે. બાઉન્ડિંગ બોક્સ **[${d.min_lng}, ${d.min_lat}]** થી **[${d.max_lng}, ${d.max_lat}]** સુધી વિસ્તરેલું છે.\n\n### 🏙️ શહેરી માળખું અને વસાહત ઘનતા\nહાઇ-રિઝોલ્યુશન રાસ્ટર ટાઇલ્સ મુખ્ય માર્ગો સાથે બાંધકામની સંગઠિત રચના દર્શાવે છે.\n\n### 🌿 પર્યાવરણીય સંદર્ભ અને જમીન આવરણ\nસેટેલાઇટ સ્પેક્ટ્રલ પરાવર્તન વનસ્પતિ અને ખુલ્લી સપાટીઓનું સંતુલન દર્શાવે છે.\n\n### 🏗️ નિર્ણાયક ઈન્ફ્રાસ્ટ્રક્ચર\nપરિવહન લિંક્સ વર્તમાન વ્યુપોર્ટમાં સ્પષ્ટપણે જોઈ શકાય છે.\n\n### 🛰️ રિમોટ સેન્સિંગ અવલોકનો અને ભલામણો\n- **Sentinel-2 MSI**: NDVI અને NDWI જમીન/પાણી વર્ગીકરણ માટે ભલામણ કરેલ.\n- **Sentinel-1 SAR**: સપાટીની ચોક્કસ દેખરેખ માટે C-band રડાર ભલામણ કરેલ.`,
    kn: (d) => `### 🌍 ಸ್ಥೂಲ ಭೌಗೋಳಿಕ ಅವಲೋಕನ\n**${d.name}** ಅಕ್ಷಾಂಶ **${d.lat}°N, ${d.lng}°E** ನಲ್ಲಿ ನೆಲೆಗೊಂಡಿದೆ. ಬೌಂಡಿಂಗ್ ಬಾಕ್ಸ್ **[${d.min_lng}, ${d.min_lat}]** ರಿಂದ **[${d.max_lng}, ${d.max_lat}]** ವರೆಗೆ ವಿಸ್ತರಿಸಿದೆ.\n\n### 🏙️ ನಗರ ರಚನೆ ಮತ್ತು ವಸಾಹತು ಸಾಂದ್ರತೆ\nಹೈ-ರೆಸಲ್ಯೂಶನ್ ರಾಸ್ಟರ್ ಟೈಲ್ಸ್ ಪ್ರಮುಖ ರಸ್ತೆಗಳ ಉದ್ದಕ್ಕೂ ಕಟ್ಟಡಗಳ ರಚನೆಯನ್ನು ಖಚಿತಪಡಿಸುತ್ತವೆ.\n\n### 🌿 ಪರಿಸರ ಸಂದರ್ಭ ಮತ್ತು ಭೂ ಹೊದಿಕೆ\nಉಪಗ್ರಹ ಪ್ರತಿಫಲನವು ಸಸ್ಯವರ್ಗ ಮತ್ತು ನಿರ್ಮಿತ ಪ್ರದೇಶಗಳ ಸಮತೋಲನವನ್ನು ತೋರಿಸುತ್ತದೆ.\n\n### 🏗️ ಪ್ರಮುಖ ಮೂಲಸೌಕರ್ಯ\nಸಾರಿಗೆ ಸಂಪರ್ಕಗಳು ಪ್ರಸ್ತುತ ವೀಕ್ಷಣೆಯಲ್ಲಿ ಸ್ಪಷ್ಟವಾಗಿ ಕಂಡುಬರುತ್ತವೆ.\n\n### 🛰️ ರಿಮೋಟ್ ಸೆನ್ಸಿಂಗ್ ವೀಕ್ಷಣೆಗಳು & ಶಿಫಾರಸುಗಳು\n- **Sentinel-2 MSI**: ನಿರಂತರ NDVI ಮತ್ತು NDWI ವರ್ಗೀಕರಣಕ್ಕೆ ಶಿಫಾರಸು ಮಾಡಲಾಗಿದೆ.\n- **Sentinel-1 SAR**: ಮೋಡ ರಹಿತ ಮೇಲ್ಮೈ ಅಧ್ಯಯನಕ್ಕೆ C-band ರಾಡಾರ್ ಶಿಫಾರಸು ಮಾಡಲಾಗಿದೆ.`,
    ml: (d) => `### 🌍 സ്ഥൂല ഭൂമിശാസ്ത്രപരമായ അവലോകനം\n**${d.name}** അക്ഷാംശം **${d.lat}°N, ${d.lng}°E**-ൽ സ്ഥിതിചെയ്യുന്നു. അതിർത്തി വ്യാപ്തി **[${d.min_lng}, ${d.min_lat}]** മുതൽ **[${d.max_lng}, ${d.max_lat}]** വരെ വ്യാപിച്ചിരിക്കുന്നു.\n\n### 🏙️ നഗര ഘടനയും ജനവാസ സാന്ദ്രതയും\nഹൈ-റെസല്യൂഷൻ റാസ്റ്റർ ടൈലുകൾ പ്രധാന റോഡ് ശൃംഖലകൾക്ക് സമീപമുള്ള നിർമ്മിതികൾ വ്യക്തമാക്കുന്നു.\n\n### 🌿 പാരിസ്ഥിതിക പശ്ചാത്തലവും ഭൂവിനിയോഗവും\nഉപഗ്രഹ പ്രതിഫലനം സസ്യമേഖലകളുടെയും കെട്ടിടങ്ങളുടെയും സന്തുലിതാവസ്ഥ കാണിക്കുന്നു.\n\n### 🏗️ പ്രധാന അടിസ്ഥാന സൗകര്യങ്ങൾ\nഗതാഗത പാതകൾ നിലവിലെ വ്യൂപോർട്ടിൽ വ്യക്തമായി ദൃശ്യമാണ്.\n\n### 🛰️ റിമോട്ട് സെൻസിംഗ് നിരീക്ഷണങ്ങളും ശുപാർശകളും\n- **Sentinel-2 MSI**: തുടർച്ചയായ NDVI, NDWI സസ്യ/ജല നിരീക്ഷണത്തിന് ശുപാർശ ചെയ്യുന്നു.\n- **Sentinel-1 SAR**: ഉപരിതല നിരീക്ഷണത്തിന് C-band റഡാർ ശുപാർശ ചെയ്യുന്നു.`,
    pa: (d) => `### 🌍 ਸਮੁੱਚਾ ਭੂਗੋਲਿਕ ਜਾਇਜ਼ਾ\n**${d.name}** ਅਕਸ਼ਾਂਸ਼ **${d.lat}°N, ${d.lng}°E** 'ਤੇ ਸਥਿਤ ਹੈ। ਬਾਊਂਡਿੰਗ ਬਾਕਸ **[${d.min_lng}, ${d.min_lat}]** ਤੋਂ **[${d.max_lng}, ${d.max_lat}]** ਤੱਕ ਫੈਲਿਆ ਹੋਇਆ ਹੈ।\n\n### 🏙️ ਸ਼ਹਿਰੀ ਬਣਤਰ ਅਤੇ ਵਸੋਂ ਦੀ ਘਣਤਾ\nਹਾਈ-ਰੈਜ਼ੋਲੂਸ਼ਨ ਰਾਸਟਰ ਟਾਈਲਾਂ ਮੁੱਖ ਆਵਾਜਾਈ ਰੂਟਾਂ ਦੇ ਨਾਲ-ਨਾਲ ਉਸਾਰੀਆਂ ਦੀ ਪੁਸ਼ਟੀ ਕਰਦੀਆਂ ਹਨ।\n\n### 🌿 ਵਾਤਾਵਰਣ ਸੰਦਰਭ ਅਤੇ ਜ਼ਮੀਨੀ ਕਵਰੇਜ\nਸੈਟੇਲਾਈਟ ਸਪੈਕਟ੍ਰਲ ਰਿਫਲੈਕਟੈਂਸ ਸੰਤੁਲਿਤ ਬਨਸپਤੀ ਨੂੰ ਦਰਸਾਉਂਦੀ ਹੈ।\n\n### 🏗️ ਮਹੱਤਵਪੂਰਨ ਬੁਨਿਆਦੀ ਢਾਂਚਾ\nਆਵਾਜਾਈ ਲਿੰਕ ਮੌਜੂਦਾ ਵਿਊਪੋਰਟ ਵਿੱਚ ਸਪੱਸ਼ਟ ਤੌਰ 'ਤੇ ਦਿਖਾਈ ਦਿੰਦੇ ਹਨ।\n\n### 🛰️ ਰਿਮੋਟ ਸੈਂਸਿੰਗ ਨਿਰੀਖਣ ਅਤੇ ਸਿਫ਼ਾਰਸ਼ਾਂ\n- **Sentinel-2 MSI**: ਲਗਾਤਾਰ NDVI ਅਤੇ NDWI ਵਰਗੀਕਰਨ ਲਈ ਸਿਫ਼ਾਰਸ਼ ਕੀਤੀ ਜਾਂਦੀ ਹੈ।\n- **Sentinel-1 SAR**: ਸਤ੍ਹਾ ਦੇ ਨਿਰੀਖਣ ਲਈ C-band ਰਾਡਾਰ ਸਿਫ਼ਾਰਸ਼ ਕੀਤਾ ਜਾਂਦਾ ਹੈ।`
  };

  class I18nManager {
    constructor() {
      this.languages = SUPPORTED_LANGUAGES;
      this.currentLang = localStorage.getItem("satquery_lang") || "en";
      this.locales = {};
      this.speechRecognition = null;
      this.isListening = false;
      this.initialized = false;
    }

    async init() {
      this.injectStyles();

      // 1. Seed locales from pre-bundled catalogue if present
      if (window.SATQUERY_LOCALES) {
        this.locales = { ...window.SATQUERY_LOCALES };
      }

      // 2. Load locales if needed
      await Promise.all([
        this.loadLocale("en"),
        this.currentLang !== "en" ? this.loadLocale(this.currentLang) : Promise.resolve(),
      ]);

      this.initialized = true;
      this.applyTranslations();
      this.updateLanguageSelectorUI();
      document.dispatchEvent(new CustomEvent("satquery:i18nReady", { detail: { lang: this.currentLang } }));
    }

    async loadLocale(lang) {
      if (this.locales[lang] && Object.keys(this.locales[lang]).length > 5) {
        return this.locales[lang];
      }

      // Check bundled fallback first
      if (window.SATQUERY_LOCALES && window.SATQUERY_LOCALES[lang]) {
        this.locales[lang] = window.SATQUERY_LOCALES[lang];
        return this.locales[lang];
      }

      try {
        const res = await fetch(`locales/${lang}.json`).catch(() => fetch(`/locales/${lang}.json`));
        if (res && res.ok) {
          const data = await res.json();
          this.locales[lang] = data;
          return data;
        }
      } catch (err) {
        // Fallback silently if offline or file:// protocol
      }

      return null;
    }

    /**
     * Resolves a key like "analyze.title" or flat alias like "nav_benchmarks".
     */
    t(keyPath, fallback = "") {
      if (!keyPath) return fallback;

      // 0. Check Location Explorer direct dictionary table
      if (EXPLORER_TRANSLATIONS[this.currentLang] && EXPLORER_TRANSLATIONS[this.currentLang][keyPath] !== undefined) {
        return EXPLORER_TRANSLATIONS[this.currentLang][keyPath];
      }
      if (this.currentLang === "en" && EXPLORER_TRANSLATIONS["en"] && EXPLORER_TRANSLATIONS["en"][keyPath] !== undefined) {
        return EXPLORER_TRANSLATIONS["en"][keyPath];
      }

      const resolvedPath = KEY_ALIASES[keyPath] || keyPath;

      const resolve = (obj, path) => {
        if (!obj) return undefined;
        // Direct property check
        if (obj[path] !== undefined && obj[path] !== null && obj[path] !== "") {
          return obj[path];
        }
        // Nested dot notation
        const parts = path.split(".");
        let curr = obj;
        for (const p of parts) {
          if (curr == null || typeof curr !== "object") return undefined;
          curr = curr[p];
        }
        return curr;
      };

      // 1. Check current language
      let val = resolve(this.locales[this.currentLang], resolvedPath);
      if (val !== undefined && val !== null && val !== "") {
        return val;
      }

      // 2. Fall back to English
      val = resolve(this.locales["en"], resolvedPath);
      if (val !== undefined && val !== null && val !== "") {
        return val;
      }

      // 3. Fall back to Explorer English if exists
      if (EXPLORER_TRANSLATIONS["en"] && EXPLORER_TRANSLATIONS["en"][keyPath] !== undefined) {
        return EXPLORER_TRANSLATIONS["en"][keyPath];
      }

      // 4. Fall back to supplied fallback or null (NEVER RETURN RAW KEY STRING)
      return fallback || null;
    }

    getLocationFallback(name, lat, lng, bbox, zoom = 15, langCode = this.currentLang) {
      const code = EXPLORER_FALLBACK_TEMPLATES[langCode] ? langCode : "en";
      const tpl = EXPLORER_FALLBACK_TEMPLATES[code];
      const min_lng = (bbox && bbox.min_lng !== undefined) ? Number(bbox.min_lng).toFixed(3) : (lng - 0.02).toFixed(3);
      const min_lat = (bbox && bbox.min_lat !== undefined) ? Number(bbox.min_lat).toFixed(3) : (lat - 0.02).toFixed(3);
      const max_lng = (bbox && bbox.max_lng !== undefined) ? Number(bbox.max_lng).toFixed(3) : (lng + 0.02).toFixed(3);
      const max_lat = (bbox && bbox.max_lat !== undefined) ? Number(bbox.max_lat).toFixed(3) : (lat + 0.02).toFixed(3);

      return tpl({
        name: name || "Target AOI",
        lat: Number(lat).toFixed(4),
        lng: Number(lng).toFixed(4),
        min_lng,
        min_lat,
        max_lng,
        max_lat,
        zoom: Number(zoom).toFixed(1)
      });
    }

    getLangMeta(code = this.currentLang) {
      return this.languages.find((l) => l.code === code) || this.languages[0];
    }

    async setLanguage(langCode) {
      if (!this.languages.some((l) => l.code === langCode)) {
        console.warn(`[i18n] Unsupported language: ${langCode}`);
        return;
      }

      this.currentLang = langCode;
      localStorage.setItem("satquery_lang", langCode);
      document.documentElement.setAttribute("lang", langCode);

      // Load language resource if not loaded yet
      await this.loadLocale(langCode);

      // Re-apply DOM translations
      this.applyTranslations();
      this.updateLanguageSelectorUI();

      // Dispatch event for components that dynamically render text
      const eventDetail = { lang: langCode, meta: this.getLangMeta(langCode) };
      document.dispatchEvent(new CustomEvent("satquery:languageChanged", { detail: eventDetail }));
      window.dispatchEvent(new CustomEvent("satquery:language_changed", { detail: eventDetail }));
    }

    applyTranslations(root = document) {
      const isEnglish = (this.currentLang === "en");

      // 1. Text / HTML elements
      const elements = root.querySelectorAll("[data-i18n]");
      elements.forEach((el) => {
        const key = el.getAttribute("data-i18n");

        // Cache original English HTML on initial load so English is always 100% exact
        if (!el.hasAttribute("data-original-content")) {
          el.setAttribute("data-original-content", el.innerHTML);
        }

        if (isEnglish) {
          el.innerHTML = el.getAttribute("data-original-content");
          return;
        }

        const translation = this.t(key);
        if (translation && translation !== key && !translation.includes("_")) {
          const keepIcon = el.getAttribute("data-i18n-keep-icon");
          if (keepIcon) {
            el.innerHTML = `${keepIcon} ${translation}`;
          } else {
            el.textContent = translation;
          }
        }
      });

      // 2. Placeholders
      const placeholders = root.querySelectorAll("[data-i18n-placeholder]");
      placeholders.forEach((el) => {
        const key = el.getAttribute("data-i18n-placeholder");
        if (!el.hasAttribute("data-original-placeholder")) {
          el.setAttribute("data-original-placeholder", el.getAttribute("placeholder") || "");
        }
        if (isEnglish) {
          el.setAttribute("placeholder", el.getAttribute("data-original-placeholder"));
          return;
        }
        const translation = this.t(key);
        if (translation && translation !== key && !translation.includes("_")) {
          el.setAttribute("placeholder", translation);
        }
      });

      // 3. Titles / Tooltips
      const titles = root.querySelectorAll("[data-i18n-title]");
      titles.forEach((el) => {
        const key = el.getAttribute("data-i18n-title");
        if (!el.hasAttribute("data-original-title")) {
          el.setAttribute("data-original-title", el.getAttribute("title") || "");
        }
        if (isEnglish) {
          el.setAttribute("title", el.getAttribute("data-original-title"));
          return;
        }
        const translation = this.t(key);
        if (translation && translation !== key && !translation.includes("_")) {
          el.setAttribute("title", translation);
        }
      });

      this.updateQuickQuestions();
    }

    updateQuickQuestions() {
      if (this.currentLang === "en") return;
      const qMap = {
        q1: { short: this.t("analyze.q1"), full: this.t("analyze.q1_full") },
        q2: { short: this.t("analyze.q2"), full: this.t("analyze.q2_full") },
        q3: { short: this.t("analyze.q3"), full: this.t("analyze.q3_full") },
        q4: { short: this.t("analyze.q4"), full: this.t("analyze.q4_full") },
        q5: { short: this.t("analyze.q5"), full: this.t("analyze.q5_full") },
        q6: { short: this.t("analyze.q6"), full: this.t("analyze.q6_full") },
      };

      document.querySelectorAll("#tab-analyze .quick-qs button[data-qkey]").forEach((btn) => {
        const qKey = btn.getAttribute("data-qkey");
        if (qMap[qKey] && qMap[qKey].short) {
          btn.textContent = qMap[qKey].short;
          btn.setAttribute("data-q", qMap[qKey].full || qMap[qKey].short);
        }
      });
    }

    createLanguageSelector(containerId = "langSelectorContainer") {
      const container = typeof containerId === "string" ? document.getElementById(containerId) : containerId;
      if (!container) return;
      this.renderLanguageSelector(container);
    }

    renderLanguageSelector(container) {
      if (!container) return;
      const meta = this.getLangMeta();

      container.innerHTML = `
        <div class="satquery-lang-dropdown" id="satqueryLangDropdown">
          <button type="button" class="satquery-lang-btn" id="satqueryLangBtn" aria-haspopup="true" aria-expanded="false" title="Change Language / भाषा">
            <span class="lang-icon">🌐</span>
            <span class="lang-current" id="satqueryLangCurrent">${meta.nativeName || meta.name}</span>
            <span class="lang-arrow">▾</span>
          </button>
          <div class="satquery-lang-menu" id="satqueryLangMenu" role="menu">
            ${this.languages
              .map(
                (l) => `
              <button type="button" class="satquery-lang-item ${l.code === this.currentLang ? "active" : ""}" data-lang="${l.code}" role="menuitem">
                <span class="lang-item-native">${l.display}</span>
                ${l.code === this.currentLang ? '<span class="lang-check">✓</span>' : ""}
              </button>
            `
              )
              .join("")}
          </div>
        </div>
      `;

      const btn = container.querySelector("#satqueryLangBtn");
      const menu = container.querySelector("#satqueryLangMenu");

      if (btn && menu) {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          const isOpen = menu.classList.contains("open");
          menu.classList.toggle("open", !isOpen);
          btn.setAttribute("aria-expanded", !isOpen ? "true" : "false");
        });

        menu.querySelectorAll(".satquery-lang-item").forEach((item) => {
          item.addEventListener("click", (e) => {
            e.stopPropagation();
            const chosen = item.getAttribute("data-lang");
            this.setLanguage(chosen);
            menu.classList.remove("open");
            btn.setAttribute("aria-expanded", "false");
          });
        });

        window.addEventListener("click", (e) => {
          if (!container.contains(e.target)) {
            menu.classList.remove("open");
            btn.setAttribute("aria-expanded", "false");
          }
        });
      }
    }

    updateLanguageSelectorUI() {
      const currentEl = document.getElementById("satqueryLangCurrent");
      if (currentEl) {
        const meta = this.getLangMeta();
        currentEl.textContent = meta.nativeName || meta.name;
      }

      document.querySelectorAll(".satquery-lang-item").forEach((item) => {
        const code = item.getAttribute("data-lang");
        const isActive = code === this.currentLang;
        item.classList.toggle("active", isActive);
        let check = item.querySelector(".lang-check");
        if (isActive && !check) {
          check = document.createElement("span");
          check.className = "lang-check";
          check.textContent = "✓";
          item.appendChild(check);
        } else if (!isActive && check) {
          check.remove();
        }
      });
    }

    injectStyles() {
      if (document.getElementById("satquery-lang-styles")) return;
      const style = document.createElement("style");
      style.id = "satquery-lang-styles";
      style.textContent = `
        .satquery-lang-dropdown {
          position: relative;
          display: inline-flex;
          align-items: center;
          font-family: 'JetBrains Mono', monospace;
          z-index: 1001;
        }
        .satquery-lang-btn {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          background: var(--bg-surface);
          border: 1px solid var(--panel-line);
          color: var(--ink-dim);
          padding: 6px 12px;
          border-radius: 20px;
          font-family: 'JetBrains Mono', monospace;
          font-size: 11px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
          backdrop-filter: blur(8px);
        }
        .satquery-lang-btn:hover {
          border-color: var(--panel-line-hover);
          color: var(--ink);
          background: var(--bg-card-hover);
          transform: translateY(-1px);
          box-shadow: var(--shadow-sm);
        }
        .satquery-lang-btn .lang-icon {
          font-size: 12px;
        }
        .satquery-lang-btn .lang-current {
          font-weight: 700;
          color: var(--primary);
        }
        .satquery-lang-btn .lang-arrow {
          font-size: 9px;
          opacity: 0.7;
          transition: transform 0.2s;
        }
        .satquery-lang-menu {
          position: absolute;
          top: calc(100% + 6px);
          right: 0;
          left: auto;
          min-width: 175px;
          max-height: 380px;
          overflow-y: auto;
          background: var(--modal-bg, #0B1424);
          border: 1px solid var(--panel-line);
          border-radius: 10px;
          box-shadow: 0 12px 36px rgba(0, 0, 0, 0.65);
          padding: 6px;
          display: none;
          flex-direction: column;
          gap: 2px;
          backdrop-filter: blur(16px);
          z-index: 10002;
        }
        .satquery-lang-menu.open {
          display: flex;
        }
        .satquery-lang-menu::-webkit-scrollbar {
          width: 5px;
        }
        .satquery-lang-menu::-webkit-scrollbar-thumb {
          background: var(--panel-line);
          border-radius: 4px;
        }
        .satquery-lang-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: transparent;
          border: none;
          color: var(--ink-dim, #8EA4BF);
          padding: 8px 12px;
          font-size: 12px;
          font-weight: 500;
          border-radius: 6px;
          cursor: pointer;
          text-align: left;
          width: 100%;
          transition: all 0.15s ease;
          font-family: inherit;
        }
        .satquery-lang-item:hover {
          background: rgba(0, 217, 255, 0.12);
          color: var(--ink, #EAF6FF);
        }
        .satquery-lang-item.active {
          background: rgba(0, 217, 255, 0.18);
          color: var(--primary, #00D9FF);
          font-weight: 700;
        }
        .satquery-lang-item .lang-check {
          color: var(--teal, #27E0C0);
          font-weight: 800;
          font-size: 12px;
        }
        .voice-btn.listening {
          background: rgba(255, 82, 106, 0.2) !important;
          border-color: #FF526A !important;
          color: #FF526A !important;
          animation: voicePulse 1s infinite alternate;
        }
        @keyframes voicePulse {
          0% { transform: scale(1); box-shadow: 0 0 4px rgba(255, 82, 106, 0.3); }
          100% { transform: scale(1.05); box-shadow: 0 0 14px rgba(255, 82, 106, 0.7); }
        }
      `;
      document.head.appendChild(style);
    }

    setupSpeechInput(btnId = "voiceBtn", inputId = "questionInput") {
      const btn = document.getElementById(btnId);
      const input = document.getElementById(inputId);
      if (!btn || !input) return;

      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {
        btn.title = "Speech recognition is not supported in this browser.";
        btn.addEventListener("click", () => {
          alert("Speech recognition is not supported in this browser. Please use Chrome or Edge.");
        });
        return;
      }

      let recognition = null;

      const stopListening = () => {
        if (recognition) {
          try {
            recognition.stop();
          } catch (_) {}
        }
        this.isListening = false;
        btn.classList.remove("listening");
        const icon = btn.querySelector("#voiceIcon") || btn;
        if (icon) icon.textContent = "🎤";
      };

      const startListening = () => {
        try {
          recognition = new SpeechRecognition();
          const meta = this.getLangMeta();
          recognition.lang = meta.speech || "en-IN";
          recognition.continuous = false;
          recognition.interimResults = true;

          btn.classList.add("listening");
          const icon = btn.querySelector("#voiceIcon") || btn;
          if (icon) icon.textContent = "🔴";
          this.isListening = true;

          recognition.onresult = (event) => {
            let interimTranscript = "";
            let finalTranscript = "";

            for (let i = event.resultIndex; i < event.results.length; ++i) {
              if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript;
              } else {
                interimTranscript += event.results[i][0].transcript;
              }
            }

            const currentVal = finalTranscript || interimTranscript;
            if (currentVal) {
              input.value = currentVal;
            }
          };

          recognition.onerror = (event) => {
            console.warn("[Voice Input] Error:", event.error);
            stopListening();
          };

          recognition.onend = () => {
            stopListening();
          };

          recognition.start();
        } catch (err) {
          console.error("[Voice Input] Start failed:", err);
          stopListening();
        }
      };

      btn.addEventListener("click", (e) => {
        e.preventDefault();
        if (this.isListening) {
          stopListening();
        } else {
          startListening();
        }
      });
    }
  }

  // Expose singleton instance to window
  window.i18n = new I18nManager();
})(window);
