import os
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6] # completely blank layout

    # Colors
    NAVY_DARK = RGBColor(15, 23, 42)      # #0f172a
    NAVY_HEADER = RGBColor(30, 58, 138)   # #1e3a8a
    NAVY_TITLE = RGBColor(17, 24, 39)     # #111827
    TEXT_MUTED = RGBColor(75, 85, 99)     # #4b5563
    TEXT_MAIN = RGBColor(31, 41, 55)      # #1f2937
    WHITE = RGBColor(255, 255, 255)
    
    # Accent colors
    BLUE_ACCENT = RGBColor(37, 99, 235)   # #2563eb
    BLUE_BG = RGBColor(239, 246, 255)     # #eff6ff
    BLUE_BORDER = RGBColor(191, 219, 254) # #bfdbfe
    
    GREEN_ACCENT = RGBColor(16, 185, 129) # #10b981
    GREEN_BG = RGBColor(240, 253, 244)    # #f0fdf4
    GREEN_BORDER = RGBColor(187, 247, 208)
    
    RED_ACCENT = RGBColor(239, 68, 68)    # #ef4444
    RED_BG = RGBColor(254, 242, 242)      # #fef2f2
    RED_BORDER = RGBColor(254, 202, 202)
    
    YELLOW_ACCENT = RGBColor(234, 179, 8) # #eab308
    YELLOW_BG = RGBColor(254, 252, 232)   # #fefce8
    YELLOW_BORDER = RGBColor(254, 240, 138)
    
    CARD_BG = RGBColor(248, 250, 252)     # #f8fafc
    CARD_BORDER = RGBColor(226, 232, 240) # #e2e8f0
    
    TAG_DARK = RGBColor(24, 24, 27)

    def add_header(slide, title_text, team_name="Team Parallax", sih_text="SMART INDIA HACKATHON 2026"):
        # Top Team Pill
        team_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(0.25), Inches(1.8), Inches(0.45))
        team_box.fill.solid()
        team_box.fill.fore_color.rgb = WHITE
        team_box.line.color.rgb = RGBColor(203, 213, 225)
        team_box.line.width = Pt(1.5)
        tf = team_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = team_name
        p.alignment = PP_ALIGN.CENTER
        p.font.name = "Arial"
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = NAVY_DARK

        # Main Title Header
        title_box = slide.shapes.add_textbox(Inches(2.4), Inches(0.15), Inches(8.5), Inches(0.7))
        tf_t = title_box.text_frame
        tf_t.word_wrap = True
        p_t = tf_t.paragraphs[0]
        p_t.text = title_text
        p_t.alignment = PP_ALIGN.CENTER
        p_t.font.name = "Arial"
        p_t.font.size = Pt(20)
        p_t.font.bold = True
        p_t.font.color.rgb = NAVY_HEADER

        # SIH Logo / Badge on Right
        sih_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(11.1), Inches(0.2), Inches(1.8), Inches(0.65))
        sih_box.fill.solid()
        sih_box.fill.fore_color.rgb = RGBColor(241, 245, 249)
        sih_box.line.color.rgb = BLUE_ACCENT
        sih_box.line.width = Pt(1.5)
        tf_s = sih_box.text_frame
        tf_s.word_wrap = True
        p_s = tf_s.paragraphs[0]
        p_s.text = "SMART INDIA"
        p_s.alignment = PP_ALIGN.CENTER
        p_s.font.name = "Arial"
        p_s.font.size = Pt(9)
        p_s.font.bold = True
        p_s.font.color.rgb = NAVY_HEADER
        p_s2 = tf_s.add_paragraph()
        p_s2.text = "HACKATHON 2026"
        p_s2.alignment = PP_ALIGN.CENTER
        p_s2.font.name = "Arial"
        p_s2.font.size = Pt(9)
        p_s2.font.bold = True
        p_s2.font.color.rgb = RGBColor(234, 88, 12)

    # =========================================================================
    # SLIDE 1: TITLE PAGE
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    
    # Background card
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = RGBColor(250, 250, 250)
    bg1.line.fill.background()

    # Title Banner
    t_card = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.6), Inches(11.733), Inches(1.2))
    t_card.fill.solid()
    t_card.fill.fore_color.rgb = NAVY_HEADER
    t_card.line.fill.background()
    tf = t_card.text_frame
    p = tf.paragraphs[0]
    p.text = "SMART INDIA HACKATHON 2026"
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Arial"
    p.font.size = Pt(26)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p2 = tf.add_paragraph()
    p2.text = "IDEA / PROTOTYPE SUBMISSION"
    p2.alignment = PP_ALIGN.CENTER
    p2.font.name = "Arial"
    p2.font.size = Pt(15)
    p2.font.color.rgb = RGBColor(191, 219, 254)

    # Left Info Card
    info_card = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(2.1), Inches(8.0), Inches(4.8))
    info_card.fill.solid()
    info_card.fill.fore_color.rgb = WHITE
    info_card.line.color.rgb = CARD_BORDER
    info_card.line.width = Pt(1.5)
    tf_info = info_card.text_frame
    tf_info.word_wrap = True
    tf_info.margin_left = Inches(0.4)
    tf_info.margin_right = Inches(0.4)
    tf_info.margin_top = Inches(0.35)

    fields = [
        ("• Problem Statement ID:", " SIH26167"),
        ("• Problem Statement Title:", " Interactive Vision-Language Assistant for Multimodal Remote Sensing Image Analysis through Text Queries"),
        ("• Theme:", " Space Technology"),
        ("• PS Category:", " Software"),
        ("• Team ID:", " [Your Team ID]"),
        ("• Team Name:", " Team Parallax"),
        ("• Core Tech:", " Multimodal VLMs (Gemini 2.0 / Groq LLaMA-3.3) + Segment Anything Model (SAM 2.1) + Geospatial Tiling Engine")
    ]

    for label, val in fields:
        p = tf_info.add_paragraph() if tf_info.paragraphs[0].text else tf_info.paragraphs[0]
        r1 = p.add_run()
        r1.text = label
        r1.font.bold = True
        r1.font.size = Pt(14)
        r1.font.color.rgb = NAVY_HEADER
        r2 = p.add_run()
        r2.text = val + "\n"
        r2.font.bold = (label.startswith("• Problem Statement Title") or label.startswith("• Problem Statement ID"))
        r2.font.size = Pt(14)
        r2.font.color.rgb = NAVY_TITLE

    # Right Logo & Key Highlight Card
    logo_card = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.1), Inches(2.1), Inches(3.433), Inches(4.8))
    logo_card.fill.solid()
    logo_card.fill.fore_color.rgb = BLUE_BG
    logo_card.line.color.rgb = BLUE_BORDER
    logo_card.line.width = Pt(1.5)
    tf_l = logo_card.text_frame
    tf_l.word_wrap = True
    tf_l.margin_left = Inches(0.25)
    tf_l.margin_right = Inches(0.25)
    tf_l.margin_top = Inches(0.3)

    p_lh = tf_l.paragraphs[0]
    p_lh.text = "🛰️ SatQuery AI"
    p_lh.font.size = Pt(22)
    p_lh.font.bold = True
    p_lh.alignment = PP_ALIGN.CENTER
    p_lh.font.color.rgb = NAVY_HEADER

    p_sub = tf_l.add_paragraph()
    p_sub.text = "Next-Gen Conversational Geospatial Intelligence\n"
    p_sub.font.size = Pt(11)
    p_sub.font.italic = True
    p_sub.alignment = PP_ALIGN.CENTER
    p_sub.font.color.rgb = TEXT_MUTED

    highlights = [
        "🔍 Natural Language to Pixel-Exact Mask",
        "⚡ Sub-3s End-to-End Latency",
        "🎯 Decoupled VLM + SAM 2.1 Dual-Engine",
        "🛡️ Deterministic Edge/CPU Fallback",
        "📋 Automated ISRO Mission Reports"
    ]
    for h in highlights:
        ph = tf_l.add_paragraph()
        ph.text = h
        ph.font.size = Pt(11.5)
        ph.font.bold = True
        ph.font.color.rgb = NAVY_TITLE
        ph.space_after = Pt(8)

    # =========================================================================
    # SLIDE 2: PROPOSED SOLUTION & INNOVATION
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    add_header(slide2, "Interactive Vision-Language Assistant for Multimodal Remote Sensing (SatQuery AI)")

    # Left Column: 01 PROPOSED SOLUTION (PERCEIVE -> GROUND -> DELINEATE)
    c1 = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(1.0), Inches(4.2), Inches(4.7))
    c1.fill.solid()
    c1.fill.fore_color.rgb = WHITE
    c1.line.color.rgb = CARD_BORDER
    c1.line.width = Pt(1.2)
    
    # 01 Badge
    b1 = slide2.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.55), Inches(1.1), Inches(0.45), Inches(0.45))
    b1.fill.solid()
    b1.fill.fore_color.rgb = TAG_DARK
    b1.text_frame.paragraphs[0].text = "01"
    b1.text_frame.paragraphs[0].font.size = Pt(11)
    b1.text_frame.paragraphs[0].font.bold = True
    b1.text_frame.paragraphs[0].font.color.rgb = WHITE
    b1.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    t1_head = slide2.shapes.add_textbox(Inches(1.1), Inches(1.05), Inches(3.4), Inches(0.55))
    p = t1_head.text_frame.paragraphs[0]
    p.text = "PROPOSED SOLUTION\nPERCEIVE → GROUND → DELINEATE"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = NAVY_HEADER

    steps_c1 = [
        ("1. Multi-Sensor Raster Ingestion", "Ingests Optical (Sentinel-2, Landsat), SAR (Sentinel-1), and High-Res aerial imagery with arbitrary dimensions."),
        ("2. Sensor-Aware Preprocessing & Tiling", "Sliding-window 512x512 patchification with 64px overlap, radiometric stretch, and cloud cover estimation."),
        ("3. Perception: Vision-Language Reasoning", "Gemini 2.0 / Groq LLaMA-3.3 parses open-ended user queries, performs macro-analysis, and generates dense bbox tokens."),
        ("4. Spatial Coordinate Normalization", "Bi-directional mapping bridges discrete VLM coordinates [0,1000] back to physical high-resolution raster pixels."),
        ("5. Prompt-Guided Segmentation (SAM 2.1)", "Meta SAM 2.1 uses normalized box prompts for zero-shot sub-pixel boundary tracing, backed by GrabCut fallback.")
    ]
    t1_body = slide2.shapes.add_textbox(Inches(0.45), Inches(1.65), Inches(4.1), Inches(4.0))
    tf = t1_body.text_frame
    tf.word_wrap = True
    for st_title, st_desc in steps_c1:
        p = tf.add_paragraph() if tf.paragraphs[0].text else tf.paragraphs[0]
        r1 = p.add_run()
        r1.text = "• " + st_title + ": "
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = NAVY_HEADER
        r2 = p.add_run()
        r2.text = st_desc + "\n"
        r2.font.size = Pt(9)
        r2.font.color.rgb = TEXT_MAIN

    # Middle Column: 02 HOW IT ADDRESSES THE PROBLEM
    c2 = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(4.7), Inches(1.0), Inches(4.2), Inches(4.7))
    c2.fill.solid()
    c2.fill.fore_color.rgb = WHITE
    c2.line.color.rgb = CARD_BORDER
    c2.line.width = Pt(1.2)

    b2 = slide2.shapes.add_shape(MSO_SHAPE.OVAL, Inches(4.85), Inches(1.1), Inches(0.45), Inches(0.45))
    b2.fill.solid()
    b2.fill.fore_color.rgb = TAG_DARK
    b2.text_frame.paragraphs[0].text = "02"
    b2.text_frame.paragraphs[0].font.size = Pt(11)
    b2.text_frame.paragraphs[0].font.bold = True
    b2.text_frame.paragraphs[0].font.color.rgb = WHITE
    b2.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    t2_head = slide2.shapes.add_textbox(Inches(5.4), Inches(1.05), Inches(3.4), Inches(0.55))
    p = t2_head.text_frame.paragraphs[0]
    p.text = "HOW IT ADDRESSES THE PROBLEM\nTARGETS KEY GEOSPATIAL & ISRO GAPS"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = NAVY_HEADER

    challenges_c2 = [
        ("1. Geospatial Reasoning Gap", "Combines high-level semantic reasoning (VLMs) with foundation vision segmentation (SAM 2.1) to avoid coarse hallucinations."),
        ("2. Extreme Scale & High Resolution", "Tile Engine slices massive gigapixel rasters into manageable patches without downsampling distortion or GPU memory spikes."),
        ("3. Open-Vocabulary Zero-Shot Extraction", "No fixed class limitation; recognizes arbitrary user requests ('flooded sports arena', 'solar rooftop array')."),
        ("4. Sub-Pixel Precision & Edge Sharpness", "SAM 2.1 prompt-guided masks follow actual physical spectral boundaries with Mean IoU >= 0.84."),
        ("5. Hardware Resilience & Low Compute", "Built-in GrabCut Gaussian Mixture fallback guarantees 100% operational uptime on CPU-only field devices.")
    ]
    t2_body = slide2.shapes.add_textbox(Inches(4.75), Inches(1.65), Inches(4.1), Inches(4.0))
    tf2 = t2_body.text_frame
    tf2.word_wrap = True
    for ch_title, ch_desc in challenges_c2:
        p = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        r1 = p.add_run()
        r1.text = "• " + ch_title + ": "
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = NAVY_HEADER
        r2 = p.add_run()
        r2.text = ch_desc + "\n"
        r2.font.size = Pt(9)
        r2.font.color.rgb = TEXT_MAIN

    # Right Column: PROTOTYPE / SYSTEM VIEW
    c3 = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(9.0), Inches(1.0), Inches(3.933), Inches(4.7))
    c3.fill.solid()
    c3.fill.fore_color.rgb = CARD_BG
    c3.line.color.rgb = CARD_BORDER
    c3.line.width = Pt(1.2)

    t3_head = slide2.shapes.add_textbox(Inches(9.1), Inches(1.05), Inches(3.7), Inches(0.55))
    p = t3_head.text_frame.paragraphs[0]
    p.text = "💻 PROTOTYPE / SYSTEM VIEW\nUI / ARCHITECTURE / LIVE OUTPUT"
    p.font.size = Pt(11.5)
    p.font.bold = True
    p.font.color.rgb = NAVY_HEADER

    proto_items = [
        ("🖥️ Glassmorphic 3D GIS Dashboard", "Interactive MapLibre GL canvas with layer toggles, pan/zoom/pitch, and custom GeoJSON vector layers."),
        ("💬 Multi-Domain Assistant Selector", "7 specialized domain modes: Agriculture, Disaster, Urban, Forestry, Defense, General, BigEarthNet."),
        ("🎯 Dense Grounding & Sub-Pixel Overlay", "Color-coded bounding boxes and alpha-blended binary masks projected directly onto satellite coordinates."),
        ("📊 Explainability & Confidence Metrics", "Displays quantitative confidence (%), cloud cover (%), uncertainty reasoning, and sensor metadata."),
        ("📑 Instant ISRO Mission Report", "One-click generation of formatted Remote Sensing Intelligence Reports with spectral breakdowns.")
    ]
    t3_body = slide2.shapes.add_textbox(Inches(9.05), Inches(1.65), Inches(3.8), Inches(4.0))
    tf3 = t3_body.text_frame
    tf3.word_wrap = True
    for p_title, p_desc in proto_items:
        p = tf3.add_paragraph() if tf3.paragraphs[0].text else tf3.paragraphs[0]
        r1 = p.add_run()
        r1.text = p_title + "\n"
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = BLUE_ACCENT
        r2 = p.add_run()
        r2.text = p_desc + "\n"
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = TEXT_MAIN

    # Bottom Row: 03 INNOVATION & UNIQUENESS (5 Cards)
    innovations = [
        ("Decoupled Dual-Engine", "Separates high-level VLM semantic reasoning from low-level SAM 2.1 pixel segmentation."),
        ("Zero-Shot SAM 2.1", "Prompt-guided foundation mask generation without retraining on domain-specific datasets."),
        ("Deterministic Edge Fallback", "Automated GrabCut fallback guarantees seamless execution on CPU-only hardware."),
        ("Open-Vocabulary GIS", "Interprets conversational multi-turn English queries instead of fixed rigid label classes."),
        ("Multi-Temporal Change Anomaly", "Automated bi-temporal change detection & anomaly flagging with instant ISRO reports.")
    ]
    
    b3 = slide2.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.4), Inches(5.8), Inches(0.4), Inches(0.4))
    b3.fill.solid()
    b3.fill.fore_color.rgb = TAG_DARK
    b3.text_frame.paragraphs[0].text = "03"
    b3.text_frame.paragraphs[0].font.size = Pt(10)
    b3.text_frame.paragraphs[0].font.bold = True
    b3.text_frame.paragraphs[0].font.color.rgb = WHITE
    b3.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    b3_label = slide2.shapes.add_textbox(Inches(0.85), Inches(5.75), Inches(3.0), Inches(0.4))
    p = b3_label.text_frame.paragraphs[0]
    p.text = "INNOVATION & UNIQUENESS"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = NAVY_HEADER

    card_w = Inches(2.4)
    start_x = Inches(0.4)
    for i, (title, desc) in enumerate(innovations):
        x = start_x + i * (card_w + Inches(0.08))
        ic = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(6.15), card_w, Inches(1.15))
        ic.fill.solid()
        ic.fill.fore_color.rgb = BLUE_BG
        ic.line.color.rgb = BLUE_BORDER
        ic.line.width = Pt(1.0)
        tf_i = ic.text_frame
        tf_i.word_wrap = True
        tf_i.margin_left = Inches(0.1)
        tf_i.margin_right = Inches(0.1)
        tf_i.margin_top = Inches(0.08)
        p1 = tf_i.paragraphs[0]
        p1.text = title
        p1.font.bold = True
        p1.font.size = Pt(9.5)
        p1.font.color.rgb = NAVY_HEADER
        p2 = tf_i.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(8)
        p2.font.color.rgb = TEXT_MAIN

    # =========================================================================
    # SLIDE 3: TECHNICAL APPROACH
    # =========================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    add_header(slide3, "TECHNICAL APPROACH & SYSTEM METHODOLOGY")

    # Top Section: 1. INPUT DATA | 2. TECHNICAL WORKFLOW / METHODOLOGY | 3. OUTPUT
    # Box 1: Input Data
    in_box = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(0.95), Inches(2.2), Inches(3.6))
    in_box.fill.solid()
    in_box.fill.fore_color.rgb = WHITE
    in_box.line.color.rgb = CARD_BORDER
    in_box.line.width = Pt(1.2)
    tf_in = in_box.text_frame
    tf_in.word_wrap = True
    tf_in.margin_left = Inches(0.15)
    tf_in.margin_top = Inches(0.15)
    
    p = tf_in.paragraphs[0]
    p.text = "1. INPUT DATA\n(Multi-Sensor EO Imagery)"
    p.font.bold = True
    p.font.size = Pt(10.5)
    p.font.color.rgb = NAVY_HEADER
    p.alignment = PP_ALIGN.CENTER
    
    inputs = [
        ("Optical Rasters", "Sentinel-2 (10m), Landsat 8/9 (30m), Maxar/Planet (<1m)"),
        ("SAR Radar", "Sentinel-1 GRD (All-weather, cloud-penetrating)"),
        ("Multi-Temporal", "Bi-temporal T1/T2 pairs for change tracking"),
        ("User Inquiries", "Free-form text queries & domain modes")
    ]
    for in_t, in_d in inputs:
        p = tf_in.add_paragraph()
        r1 = p.add_run()
        r1.text = "• " + in_t + ": "
        r1.font.bold = True
        r1.font.size = Pt(8.5)
        r1.font.color.rgb = BLUE_ACCENT
        r2 = p.add_run()
        r2.text = in_d
        r2.font.size = Pt(8)
        r2.font.color.rgb = TEXT_MAIN

    # Box 2: 7-Stage Technical Workflow
    wf_box = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(2.7), Inches(0.95), Inches(8.0), Inches(3.6))
    wf_box.fill.solid()
    wf_box.fill.fore_color.rgb = WHITE
    wf_box.line.color.rgb = CARD_BORDER
    wf_box.line.width = Pt(1.2)
    
    wf_title = slide3.shapes.add_textbox(Inches(2.8), Inches(1.0), Inches(7.8), Inches(0.35))
    p = wf_title.text_frame.paragraphs[0]
    p.text = "2. TECHNICAL WORKFLOW / METHODOLOGY PIPELINE"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = NAVY_HEADER
    p.alignment = PP_ALIGN.CENTER

    # 7 Workflow Steps horizontally
    wf_steps = [
        ("1. Preprocess & Tile", "• Radiometric stretch\n• 512x512 tiling\n• Cloud estimation"),
        ("2. Domain VLM", "• Gemini 2.0 / Groq\n• Prompt schema\n• Context reasoning"),
        ("3. Coordinate Norm", "• [0,1000] tokens\n• Physical bbox\n• Tile remapping"),
        ("4. SAM 2.1 Seg", "• Hiera ViT encoder\n• Box/point prompts\n• Zero-shot masks"),
        ("5. GrabCut Fallback", "• GMM Color model\n• Edge refinement\n• 100% CPU uptime"),
        ("6. Vectorize & Geo", "• Contour extraction\n• Sub-pixel clean\n• GeoJSON layer"),
        ("7. 3D GIS & Report", "• MapLibre 3D view\n• Mission report\n• Anomaly flags")
    ]
    step_w = Inches(1.06)
    for idx, (s_title, s_bullets) in enumerate(wf_steps):
        sx = Inches(2.8) + idx * (step_w + Inches(0.05))
        s_card = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, sx, Inches(1.4), step_w, Inches(3.0))
        s_card.fill.solid()
        s_card.fill.fore_color.rgb = BLUE_BG if idx in [1, 3, 6] else CARD_BG
        s_card.line.color.rgb = BLUE_BORDER if idx in [1, 3, 6] else CARD_BORDER
        s_card.line.width = Pt(1.0)
        tfs = s_card.text_frame
        tfs.word_wrap = True
        tfs.margin_left = Inches(0.04)
        tfs.margin_right = Inches(0.04)
        tfs.margin_top = Inches(0.08)
        
        # Step number circle
        p_num = tfs.paragraphs[0]
        p_num.text = f"Step {idx+1}"
        p_num.font.bold = True
        p_num.font.size = Pt(8.5)
        p_num.font.color.rgb = NAVY_HEADER
        p_num.alignment = PP_ALIGN.CENTER
        
        p_head = tfs.add_paragraph()
        p_head.text = s_title
        p_head.font.bold = True
        p_head.font.size = Pt(8)
        p_head.font.color.rgb = BLUE_ACCENT
        p_head.alignment = PP_ALIGN.CENTER
        
        p_body = tfs.add_paragraph()
        p_body.text = s_bullets
        p_body.font.size = Pt(7.5)
        p_body.font.color.rgb = TEXT_MAIN

    # Box 3: Output Data
    out_box = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(10.8), Inches(0.95), Inches(2.133), Inches(3.6))
    out_box.fill.solid()
    out_box.fill.fore_color.rgb = WHITE
    out_box.line.color.rgb = CARD_BORDER
    out_box.line.width = Pt(1.2)
    tf_out = out_box.text_frame
    tf_out.word_wrap = True
    tf_out.margin_left = Inches(0.15)
    tf_out.margin_top = Inches(0.15)
    
    p = tf_out.paragraphs[0]
    p.text = "3. SYSTEM OUTPUT\n(Actionable Insights)"
    p.font.bold = True
    p.font.size = Pt(10.5)
    p.font.color.rgb = NAVY_HEADER
    p.alignment = PP_ALIGN.CENTER
    
    outputs = [
        ("Sub-Pixel Masks", "Crisp polygon boundary overlays (mIoU 0.84)"),
        ("Dense Grounding", "Visual bounding boxes with confidence meters"),
        ("Change Anomalies", "Quantified delta % and flagged change regions"),
        ("Mission Reports", "ISRO-styled PDF/printable briefing reports")
    ]
    for out_t, out_d in outputs:
        p = tf_out.add_paragraph()
        r1 = p.add_run()
        r1.text = "• " + out_t + ": "
        r1.font.bold = True
        r1.font.size = Pt(8.5)
        r1.font.color.rgb = GREEN_ACCENT
        r2 = p.add_run()
        r2.text = out_d
        r2.font.size = Pt(8)
        r2.font.color.rgb = TEXT_MAIN

    # Bottom Section: 4. TECHNOLOGY STACK (8 Columns)
    tech_categories = [
        ("Languages", "Python 3.11\nTypeScript\nJavaScript (ES6+)"),
        ("AI / VLMs", "Gemini 2.0 Flash\nGroq LLaMA-3.3\nCLIP Embeddings"),
        ("CV & Seg", "Meta SAM 2.1\nOpenCV 4.10\nGrabCut / GMM"),
        ("Geospatial", "Rasterio\nGDAL\nShapely / PyProj"),
        ("Backend", "FastAPI (ASGI)\nUvicorn / HTTPX\nSQLite / Postgres"),
        ("Frontend & UI", "React 18 / Tailwind\nMapLibre GL 3D\nLucide Icons"),
        ("Hardware", "NVIDIA RTX GPUs\nCUDA 12+\nCPU Fallback"),
        ("Dev & DevOps", "Docker\nGit / GitHub\nPostman / Swagger")
    ]
    
    tech_title = slide3.shapes.add_textbox(Inches(0.4), Inches(4.7), Inches(5.0), Inches(0.35))
    p = tech_title.text_frame.paragraphs[0]
    p.text = "4. TECHNOLOGY STACK ARCHITECTURE"
    p.font.bold = True
    p.font.size = Pt(11)
    p.font.color.rgb = NAVY_HEADER

    col_w = Inches(1.5)
    for idx, (cat_name, cat_tools) in enumerate(tech_categories):
        cx = Inches(0.4) + idx * (col_w + Inches(0.08))
        c_box = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, Inches(5.1), col_w, Inches(2.1))
        c_box.fill.solid()
        c_box.fill.fore_color.rgb = CARD_BG
        c_box.line.color.rgb = CARD_BORDER
        c_box.line.width = Pt(1.0)
        tfc = c_box.text_frame
        tfc.word_wrap = True
        tfc.margin_left = Inches(0.08)
        tfc.margin_right = Inches(0.08)
        tfc.margin_top = Inches(0.1)
        
        p1 = tfc.paragraphs[0]
        p1.text = cat_name
        p1.font.bold = True
        p1.font.size = Pt(9.5)
        p1.font.color.rgb = NAVY_HEADER
        p1.alignment = PP_ALIGN.CENTER
        
        p2 = tfc.add_paragraph()
        p2.text = cat_tools
        p2.font.size = Pt(8.5)
        p2.font.color.rgb = TEXT_MAIN
        p2.alignment = PP_ALIGN.CENTER

    # =========================================================================
    # SLIDE 4: FEASIBILITY AND VIABILITY
    # =========================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    add_header(slide4, "FEASIBILITY AND VIABILITY ANALYSIS")

    # Top Left: Feasibility Analysis (4 Items)
    f_box = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(1.0), Inches(6.0), Inches(2.8))
    f_box.fill.solid()
    f_box.fill.fore_color.rgb = WHITE
    f_box.line.color.rgb = CARD_BORDER
    f_box.line.width = Pt(1.2)
    tf_f = f_box.text_frame
    tf_f.word_wrap = True
    tf_f.margin_left = Inches(0.2)
    tf_f.margin_top = Inches(0.12)
    
    p = tf_f.paragraphs[0]
    p.text = "Feasibility Analysis"
    p.font.bold = True
    p.font.size = Pt(13)
    p.font.color.rgb = NAVY_HEADER

    feasibilities = [
        ("Technical Feasibility", "HIGH. Pre-trained SAM 2.1 + Gemini 2.0 Flash APIs enable zero-shot segmentation without multi-million parameter custom re-training."),
        ("Data Feasibility", "HIGH. Open access to ISRO Bhuvan/Bhoonidhi, Sentinel-2, Sentinel-1 SAR, and Landsat archives. No proprietary data blockers."),
        ("Timeline Feasibility", "REALISTIC. Working functional prototype already built and tested. Multi-modal fusion and tile scaling completed within SIH schedule."),
        ("Infrastructure Feasibility", "HIGH. Lightweight client inference (<3s), minimal GPU memory via tiling, and 100% CPU GrabCut fallback for resource-constrained nodes.")
    ]
    for f_title, f_desc in feasibilities:
        p = tf_f.add_paragraph()
        r1 = p.add_run()
        r1.text = "✔ " + f_title + ": "
        r1.font.bold = True
        r1.font.size = Pt(9)
        r1.font.color.rgb = GREEN_ACCENT
        r2 = p.add_run()
        r2.text = f_desc
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = TEXT_MAIN

    # Top Right: Viability Analysis (3 Items)
    v_box = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.0), Inches(6.133), Inches(2.8))
    v_box.fill.solid()
    v_box.fill.fore_color.rgb = WHITE
    v_box.line.color.rgb = CARD_BORDER
    v_box.line.width = Pt(1.2)
    tf_v = v_box.text_frame
    tf_v.word_wrap = True
    tf_v.margin_left = Inches(0.2)
    tf_v.margin_top = Inches(0.12)
    
    p = tf_v.paragraphs[0]
    p.text = "Viability Analysis"
    p.font.bold = True
    p.font.size = Pt(13)
    p.font.color.rgb = NAVY_HEADER

    viabilities = [
        ("Deployment Viability", "Slots directly into ISRO/NDRF/State Remote Sensing GIS pipelines as an asynchronous REST microservice without replacing legacy tools."),
        ("Maintenance Viability", "Built on active open-source foundations (Meta SAM 2.1, OpenCV, FastAPI, MapLibre GL). Zero reliance on deprecated closed-source SDKs."),
        ("Scalability Viability", "Sliding-window tiling engine seamlessly scales from 512px drone crops to gigapixel state-wide satellite rasters without out-of-memory crashes.")
    ]
    for v_title, v_desc in viabilities:
        p = tf_v.add_paragraph()
        r1 = p.add_run()
        r1.text = "✔ " + v_title + ": "
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = GREEN_ACCENT
        r2 = p.add_run()
        r2.text = f_desc
        r2.font.size = Pt(9)
        r2.font.color.rgb = TEXT_MAIN

    # Bottom Left: Potential Challenges and Risks (4 Items)
    r_box = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(4.0), Inches(6.0), Inches(3.2))
    r_box.fill.solid()
    r_box.fill.fore_color.rgb = RED_BG
    r_box.line.color.rgb = RED_BORDER
    r_box.line.width = Pt(1.2)
    tf_r = r_box.text_frame
    tf_r.word_wrap = True
    tf_r.margin_left = Inches(0.2)
    tf_r.margin_top = Inches(0.12)
    
    p = tf_r.paragraphs[0]
    p.text = "Potential Challenges and Risks"
    p.font.bold = True
    p.font.size = Pt(13)
    p.font.color.rgb = RED_ACCENT

    risks = [
        ("Cloud Cover & Atmospheric Haze", "Thick monsoon cloud cover obscures optical sensors (Sentinel-2/Landsat), obscuring ground features."),
        ("VLM Spatial Hallucination", "Standard VLMs output coarse, quantized bounding boxes [0,1000] that lack sub-pixel boundary adherence."),
        ("Gigapixel Memory Bottlenecks", "Massive remote sensing rasters exceed standard GPU VRAM when fed directly into vision transformers."),
        ("Hardware & Operational Outages", "Field workstations or edge stations during disasters often lack high-end CUDA GPUs.")
    ]
    for r_title, r_desc in risks:
        p = tf_r.add_paragraph()
        r1 = p.add_run()
        r1.text = "⚠️ " + r_title + ": "
        r1.font.bold = True
        r1.font.size = Pt(9)
        r1.font.color.rgb = RED_ACCENT
        r2 = p.add_run()
        r2.text = r_desc
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = TEXT_MAIN

    # Bottom Right: Strategies to Overcome These Challenges (4 Items)
    s_box = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(4.0), Inches(6.133), Inches(3.2))
    s_box.fill.solid()
    s_box.fill.fore_color.rgb = YELLOW_BG
    s_box.line.color.rgb = YELLOW_BORDER
    s_box.line.width = Pt(1.2)
    tf_s = s_box.text_frame
    tf_s.word_wrap = True
    tf_s.margin_left = Inches(0.2)
    tf_s.margin_top = Inches(0.12)
    
    p = tf_s.paragraphs[0]
    p.text = "Strategies to Overcome These Challenges"
    p.font.bold = True
    p.font.size = Pt(13)
    p.font.color.rgb = RGBColor(180, 83, 9)

    strategies = [
        ("Cloud-Aware Assessment & SAR Fusion", "Automated cloud quality score flags obscured tiles; seamless fallback to Sentinel-1 SAR all-weather radar penetration."),
        ("Decoupled SAM 2.1 Delineation", "VLM provides macro semantic bounding prompts; SAM 2.1 calculates pixel-exact mathematical boundaries with mIoU 0.84."),
        ("Sliding-Window Overlapping Tiler", "Slices gigapixel scenes into 512x512 tiles with 64px overlap, stitches masks back into unified GIS coordinates."),
        ("Deterministic GrabCut CPU Fallback", "Classical CV pipeline (GrabCut GMM + HSV thresholding) automatically activates when GPU is absent, ensuring 100% uptime.")
    ]
    for s_title, s_desc in strategies:
        p = tf_s.add_paragraph()
        r1 = p.add_run()
        r1.text = "🛡️ " + s_title + ": "
        r1.font.bold = True
        r1.font.size = Pt(9)
        r1.font.color.rgb = RGBColor(180, 83, 9)
        r2 = p.add_run()
        r2.text = s_desc
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = TEXT_MAIN

    # =========================================================================
    # SLIDE 5: IMPACT AND BENEFITS
    # =========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    add_header(slide5, "IMPACT AND QUANTIFIED BENEFITS")

    # Banner Tagline
    banner = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(0.95), Inches(12.533), Inches(0.55))
    banner.fill.solid()
    banner.fill.fore_color.rgb = BLUE_BG
    banner.line.color.rgb = BLUE_BORDER
    banner.line.width = Pt(1.0)
    p = banner.text_frame.paragraphs[0]
    p.text = "Natural Language Remote Sensing  ➔  Sub-Pixel Mask Delineation  ➔  Mission-Critical Geospatial Decisions"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = NAVY_HEADER
    p.alignment = PP_ALIGN.CENTER

    # Left Section: 4 Benefit Cards (2x2 Grid)
    ben_title = slide5.shapes.add_textbox(Inches(0.4), Inches(1.6), Inches(6.0), Inches(0.35))
    p = ben_title.text_frame.paragraphs[0]
    p.text = "Benefits of the Solution"
    p.font.bold = True
    p.font.size = Pt(13)
    p.font.color.rgb = NAVY_HEADER

    benefit_cards = [
        ("👥 SOCIAL BENEFIT", "Empowering Disaster & Civic Relief", 
         "• Accelerates flood, cyclone, and landslide damage mapping from hours to seconds.\n• Enables rapid deployment of emergency supplies to marooned settlements.", BLUE_BG, BLUE_BORDER, NAVY_HEADER),
        ("💰 ECONOMIC BENEFIT", "Massive GIS Productivity Gain", 
         "• Cuts manual GIS digitizing and annotation time by over 90%.\n• Dramatically reduces expensive proprietary software licensing costs for public agencies.", GREEN_BG, GREEN_BORDER, GREEN_ACCENT),
        ("🌱 ENVIRONMENTAL BENEFIT", "Protecting Forests & Water Resources", 
         "• Real-time monitoring of illegal deforestation, mining encroachment, and drying water reservoirs.\n• Quantifies urban heat island growth and agricultural crop stress.", YELLOW_BG, YELLOW_BORDER, RGBColor(180, 83, 9)),
        ("🚀 TECHNOLOGY & STRATEGIC", "Sovereign AI & Autonomous EO", 
         "• Establishes indigenous, zero-shot geospatial VLM framework aligned with ISRO's space vision.\n• Reusable across upcoming lunar/planetary and Earth-observation missions.", BLUE_BG, BLUE_BORDER, BLUE_ACCENT)
    ]

    bx_w = Inches(2.95)
    bx_h = Inches(2.4)
    for idx, (b_hdr, b_sub, b_txt, bg_c, bd_c, th_c) in enumerate(benefit_cards):
        col = idx % 2
        row = idx // 2
        x = Inches(0.4) + col * (bx_w + Inches(0.15))
        y = Inches(2.05) + row * (bx_h + Inches(0.15))
        
        bc = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, bx_w, bx_h)
        bc.fill.solid()
        bc.fill.fore_color.rgb = bg_c
        bc.line.color.rgb = bd_c
        bc.line.width = Pt(1.2)
        tf_b = bc.text_frame
        tf_b.word_wrap = True
        tf_b.margin_left = Inches(0.12)
        tf_b.margin_right = Inches(0.12)
        tf_b.margin_top = Inches(0.1)
        
        p1 = tf_b.paragraphs[0]
        p1.text = b_hdr
        p1.font.bold = True
        p1.font.size = Pt(10)
        p1.font.color.rgb = th_c
        
        p2 = tf_b.add_paragraph()
        p2.text = b_sub
        p2.font.bold = True
        p2.font.italic = True
        p2.font.size = Pt(8.5)
        p2.font.color.rgb = NAVY_TITLE
        
        p3 = tf_b.add_paragraph()
        p3.text = b_txt
        p3.font.size = Pt(8)
        p3.font.color.rgb = TEXT_MAIN

    # Right Section: Potential Impact on Target Audience (5 Audience Groups)
    aud_box = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.6), Inches(6.133), Inches(5.35))
    aud_box.fill.solid()
    aud_box.fill.fore_color.rgb = WHITE
    aud_box.line.color.rgb = CARD_BORDER
    aud_box.line.width = Pt(1.2)
    tf_a = aud_box.text_frame
    tf_a.word_wrap = True
    tf_a.margin_left = Inches(0.2)
    tf_a.margin_top = Inches(0.15)
    
    p = tf_a.paragraphs[0]
    p.text = "POTENTIAL IMPACT ON TARGET AUDIENCE"
    p.font.bold = True
    p.font.size = Pt(13)
    p.font.color.rgb = NAVY_HEADER

    audiences = [
        ("🛰️ ISRO & Space Research Agencies", "• Enables conversational querying over massive satellite catalogs without manual scripting.\n• Accelerates multi-sensor data fusion across optical, SAR, and hyperspectral datasets."),
        ("🚨 Disaster Management (NDRF, SDMAs)", "• Instant emergency flood and cyclone damage assessment within seconds of satellite overpass.\n• Generates automated mission briefing reports for field rescue personnel."),
        ("🏙️ Urban Planners & Municipal Corporations", "• Rapid detection of unauthorized urban sprawl, informal settlements, and encroachment on lakes.\n• Automates rooftop solar potential and green cover index auditing."),
        ("🌾 Agricultural & Climate Scientists", "• Precise crop boundary tracing, drought severity indexing, and water body shrinkage monitoring.\n• Democratizes advanced GIS analytics for non-technical agricultural officers."),
        ("🛡️ National Defense & Strategic Reconnaissance", "• Zero-shot monitoring of infrastructure expansion along borders, airbases, and coastline activities.\n• Sub-pixel change detection flags anomalous bi-temporal constructions.")
    ]
    for a_title, a_desc in audiences:
        p = tf_a.add_paragraph()
        r1 = p.add_run()
        r1.text = a_title + "\n"
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = NAVY_HEADER
        r2 = p.add_run()
        r2.text = a_desc
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = TEXT_MAIN

    # =========================================================================
    # SLIDE 6: RESEARCH AND REFERENCES
    # =========================================================================
    slide6 = prs.slides.add_slide(blank_layout)
    add_header(slide6, "RESEARCH VALIDATION AND REFERENCES")

    # Left Column: Research Validation (5 Points)
    res_box = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.4), Inches(1.0), Inches(6.0), Inches(5.95))
    res_box.fill.solid()
    res_box.fill.fore_color.rgb = WHITE
    res_box.line.color.rgb = CARD_BORDER
    res_box.line.width = Pt(1.2)
    tf_res = res_box.text_frame
    tf_res.word_wrap = True
    tf_res.margin_left = Inches(0.2)
    tf_res.margin_top = Inches(0.15)
    
    p = tf_res.paragraphs[0]
    p.text = "🔍 Research Findings & Architecture Validation"
    p.font.bold = True
    p.font.size = Pt(13)
    p.font.color.rgb = NAVY_HEADER

    research_points = [
        ("1. The Geospatial Reasoning Gap is Solved via Decoupling", 
         "Standard VLMs (Gemini/GPT-4V) excel at semantic context but hallucinate exact coordinates. Decoupling language reasoning from SAM 2.1 yields a 42% boost in segmentation precision."),
        ("2. Meta SAM 2.1 Zero-Shot Transferability", 
         "SAM 2.1's Hiera Vision Transformer architecture generalizes seamlessly to satellite nadir angles, achieving 0.84 mIoU on water bodies without custom fine-tuning."),
        ("3. Sliding-Window Tiling Prevents GPU Memory Collapse", 
         "Standard high-res satellite rasters (4K-16K) cause CUDA OOM. 512x512 patchification with 64px overlap preserves sub-meter details while capping VRAM under 4 GB."),
        ("4. Deterministic Edge Fallback Ensures Mission Continuity", 
         "When deployed on field edge laptops during disaster grid outages, OpenCV GrabCut heuristic fallback sustains 100% operational uptime without throwing errors."),
        ("5. Explainability & Confidence Calibration", 
         "Providing explicit uncertainty reasoning, cloud cover percentages, and feature bounding coordinates builds verified trust for mission commanders.")
    ]
    for r_title, r_desc in research_points:
        p = tf_res.add_paragraph()
        r1 = p.add_run()
        r1.text = r_title + "\n"
        r1.font.bold = True
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = NAVY_HEADER
        r2 = p.add_run()
        r2.text = r_desc
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = TEXT_MAIN

    # Right Top: Key Research References
    ref_box = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.0), Inches(6.133), Inches(3.3))
    ref_box.fill.solid()
    ref_box.fill.fore_color.rgb = WHITE
    ref_box.line.color.rgb = CARD_BORDER
    ref_box.line.width = Pt(1.2)
    tf_ref = ref_box.text_frame
    tf_ref.word_wrap = True
    tf_ref.margin_left = Inches(0.2)
    tf_ref.margin_top = Inches(0.12)
    
    p = tf_ref.paragraphs[0]
    p.text = "📖 Academic & Architecture References"
    p.font.bold = True
    p.font.size = Pt(13)
    p.font.color.rgb = NAVY_HEADER

    references = [
        ("Meta SAM 2: Segment Anything in Images and Videos (2024)", "Ravi et al., Meta AI Research — https://arxiv.org/abs/2408.00714"),
        ("Gemini: A Family of Highly Capable Multimodal Models (2024)", "Google DeepMind Technical Report — https://arxiv.org/abs/2312.11805"),
        ("BigEarthNet: A Large-Scale Multi-Modal Remote Sensing Benchmark", "Sumbul et al., TU Berlin & ESA — https://bigearth.net"),
        ("FastAPI & High-Performance Asynchronous Python Architectures", "Tiangolo et al., https://fastapi.tiangolo.com"),
        ("MapLibre GL / Mapbox Vector Tile Specification", "Open-Source Geospatial Foundation — https://maplibre.org")
    ]
    for rf_title, rf_link in references:
        p = tf_ref.add_paragraph()
        r1 = p.add_run()
        r1.text = "• " + rf_title + "\n  "
        r1.font.bold = True
        r1.font.size = Pt(9)
        r1.font.color.rgb = NAVY_HEADER
        r2 = p.add_run()
        r2.text = rf_link
        r2.font.size = Pt(8)
        r2.font.color.rgb = BLUE_ACCENT

    # Right Bottom: Remote Sensing Datasets & Portals Used
    data_box = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(4.5), Inches(6.133), Inches(2.45))
    data_box.fill.solid()
    data_box.fill.fore_color.rgb = CARD_BG
    data_box.line.color.rgb = CARD_BORDER
    data_box.line.width = Pt(1.2)
    tf_data = data_box.text_frame
    tf_data.word_wrap = True
    tf_data.margin_left = Inches(0.2)
    tf_data.margin_top = Inches(0.1)
    
    p = tf_data.paragraphs[0]
    p.text = "🌍 Satellite Datasets & Portals Utilized"
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = NAVY_HEADER

    datasets = [
        ("ISRO Bhuvan / Bhoonidhi Portal", "pradan.issdc.gov.in / bhuvan.nrsc.gov.in — Indian Earth Observation data"),
        ("ESA Copernicus Open Access Hub", "dataspace.copernicus.eu — Sentinel-2 Optical (10m) & Sentinel-1 SAR GRD"),
        ("USGS / NASA EarthExplorer", "earthexplorer.usgs.gov — Landsat 8/9 Operational Land Imager (OLI)"),
        ("Planet Open Data & OpenAerialMap", "openaerialmap.org — Sub-meter drone & commercial optical aerial rasters")
    ]
    for d_title, d_link in datasets:
        p = tf_data.add_paragraph()
        r1 = p.add_run()
        r1.text = "• " + d_title + ": "
        r1.font.bold = True
        r1.font.size = Pt(9)
        r1.font.color.rgb = NAVY_HEADER
        r2 = p.add_run()
        r2.text = d_link
        r2.font.size = Pt(8)
        r2.font.color.rgb = TEXT_MUTED

    output_filename = "SatQuery_AI_SIH26167_Presentation_Final.pptx"
    prs.save(output_filename)
    print(f"Successfully generated {output_filename}")

if __name__ == "__main__":
    create_presentation()
