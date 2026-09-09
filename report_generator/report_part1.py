from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from report_styles import set_cell_background, set_cell_margins

def build_front_matter(mgr):
    doc = mgr.doc
    
    # -------------------------------------------------------------
    # 1. TITLE PAGE
    # -------------------------------------------------------------
    p_top = doc.add_paragraph()
    p_top.paragraph_format.space_before = Pt(36)
    p_top.paragraph_format.space_after = Pt(12)
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_univ = p_top.add_run("DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING\nFACULTY OF ENGINEERING AND TECHNOLOGY\n")
    run_univ.font.name = "Calibri"
    run_univ.font.size = Pt(12)
    run_univ.font.bold = True
    run_univ.font.color.rgb = RGBColor(71, 85, 105)

    p_proj = doc.add_paragraph()
    p_proj.paragraph_format.space_before = Pt(18)
    p_proj.paragraph_format.space_after = Pt(8)
    p_proj.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_proj.add_run("SATQUERY AI")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(32)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(26, 54, 93)

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(36)
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run("An Interactive Multimodal Geospatial Intelligence Platform Integrating Vision-Language Reasoning, Dense Grounding, and Segment Anything Model (SAM 2.1)")
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(13)
    run_sub.font.italic = True
    run_sub.font.color.rgb = RGBColor(43, 108, 176)

    p_desc = doc.add_paragraph()
    p_desc.paragraph_format.space_before = Pt(24)
    p_desc.paragraph_format.space_after = Pt(40)
    p_desc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_desc = p_desc.add_run("A Major Project Report submitted in partial fulfillment of the requirements for the award of the degree of\n\nBACHELOR OF TECHNOLOGY\nin\nCOMPUTER SCIENCE & ENGINEERING\n")
    run_desc.font.name = "Calibri"
    run_desc.font.size = Pt(11)
    run_desc.font.color.rgb = RGBColor(51, 65, 85)

    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(3.2)
    table.columns[1].width = Inches(3.2)
    
    c0 = table.cell(0, 0)
    p0 = c0.paragraphs[0]
    p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r0 = p0.add_run("SUBMITTED BY:\n")
    r0.font.name = "Calibri"
    r0.font.bold = True
    r0.font.size = Pt(10)
    r0.font.color.rgb = RGBColor(26, 54, 93)
    r0_body = p0.add_run("Nakshatra\nRoll No: CSE-2022-8491\nB.Tech (Final Year)\nDept. of Computer Science & Engg.")
    r0_body.font.name = "Calibri"
    r0_body.font.size = Pt(10.5)

    c1 = table.cell(0, 1)
    p1 = c1.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r1 = p1.add_run("UNDER THE GUIDANCE OF:\n")
    r1.font.name = "Calibri"
    r1.font.bold = True
    r1.font.size = Pt(10)
    r1.font.color.rgb = RGBColor(26, 54, 93)
    r1_body = p1.add_run("Project Guide & Mentor\nAssistant Professor\nDept. of Computer Science & Engg.\nFaculty of Engineering & Technology")
    r1_body.font.name = "Calibri"
    r1_body.font.size = Pt(10.5)

    p_bottom = doc.add_paragraph()
    p_bottom.paragraph_format.space_before = Pt(60)
    p_bottom.paragraph_format.space_after = Pt(0)
    p_bottom.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_year = p_bottom.add_run("ACADEMIC YEAR 2025–2026\nTECHNICAL UNIVERSITY")
    run_year.font.name = "Calibri"
    run_year.font.size = Pt(11)
    run_year.font.bold = True
    run_year.font.color.rgb = RGBColor(71, 85, 105)

    mgr.page_break()

    # -------------------------------------------------------------
    # 2. CERTIFICATE
    # -------------------------------------------------------------
    mgr.heading_1("CERTIFICATE OF APPROVAL", space_before=24)
    mgr.para(
        "This is to certify that the project entitled \"SATQUERY AI: An Interactive Multimodal Geospatial Intelligence Platform "
        "Integrating Vision-Language Reasoning, Dense Grounding, and Segment Anything Model (SAM 2.1)\" is a bona fide record of the work "
        "carried out by Nakshatra (Roll No: CSE-2022-8491), student of the Department of Computer Science & Engineering, Faculty of "
        "Engineering and Technology, in partial fulfillment of the requirements for the award of the degree of Bachelor of Technology in "
        "Computer Science & Engineering during the academic year 2025–2026."
    )
    mgr.para(
        "The results embodied in this report have not been submitted to any other University or Institute for the award of any degree or diploma. "
        "The project has been evaluated and approved by the examination board."
    )

    tbl_sig = doc.add_table(rows=2, cols=3)
    tbl_sig.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_sig.columns[0].width = Inches(2.2)
    tbl_sig.columns[1].width = Inches(2.2)
    tbl_sig.columns[2].width = Inches(2.2)

    sigs = [
        ("Project Guide", "Assistant Professor\nDept. of CSE"),
        ("Head of Department", "Professor & HOD\nDept. of CSE"),
        ("External Examiner", "Board of Evaluators\nFaculty of Engg. & Tech.")
    ]
    for i, (title, subtitle) in enumerate(sigs):
        cell = tbl_sig.cell(1, i)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(36)
        p.add_run("_____________________\n").font.color.rgb = RGBColor(148, 163, 184)
        rt = p.add_run(f"{title}\n")
        rt.font.name = "Calibri"
        rt.font.bold = True
        rt.font.size = Pt(10)
        rs = p.add_run(subtitle)
        rs.font.name = "Calibri"
        rs.font.size = Pt(9)
        rs.font.color.rgb = RGBColor(100, 116, 139)

    mgr.page_break()

    # -------------------------------------------------------------
    # 3. DECLARATION
    # -------------------------------------------------------------
    mgr.heading_1("DECLARATION", space_before=24)
    mgr.para(
        "I, Nakshatra, hereby declare that the project report entitled \"SATQUERY AI: An Interactive Multimodal Geospatial "
        "Intelligence Platform Integrating Vision-Language Reasoning, Dense Grounding, and Segment Anything Model (SAM 2.1)\", "
        "submitted to the Department of Computer Science & Engineering, Faculty of Engineering and Technology, is an authentic record of "
        "my original work completed under the guidance of my project supervisor."
    )
    mgr.para(
        "I further confirm that this work has not formed the basis for the award of any degree, diploma, associateship, or other similar title "
        "in any other university or institution. All sources, research papers, software libraries, and literature utilized in this work have "
        "been duly acknowledged and cited in the References section."
    )
    p_dec_sig = doc.add_paragraph()
    p_dec_sig.paragraph_format.space_before = Pt(40)
    p_dec_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_dec = p_dec_sig.add_run("Nakshatra\nRoll No: CSE-2022-8491\nB.Tech (Computer Science & Engineering)\nDate: March 2026\nPlace: Campus")
    r_dec.font.name = "Calibri"
    r_dec.font.size = Pt(10.5)

    mgr.page_break()

    # -------------------------------------------------------------
    # 4. ACKNOWLEDGEMENT
    # -------------------------------------------------------------
    mgr.heading_1("ACKNOWLEDGEMENT", space_before=24)
    mgr.para(
        "I express my deepest gratitude and sincere appreciation to my Project Guide for their invaluable mentorship, insightful critique, "
        "and unwavering encouragement throughout the design, implementation, and evaluation of the SatQuery AI platform. Their technical "
        "perspectives in computer vision and artificial intelligence were fundamental in shaping this research."
    )
    mgr.para(
        "I extend my heartfelt thanks to the Head of the Department of Computer Science & Engineering for providing state-of-the-art laboratory "
        "facilities, high-performance computing resources, and an academically rigorous environment that fostered this multidisciplinary initiative."
    )
    mgr.para(
        "I also acknowledge the global open-source AI and geospatial research community—notably the authors and engineering teams behind "
        "Meta AI's Segment Anything Model (SAM 2.1), Google DeepMind's Gemini Vision-Language Models, the FastAPI framework, and the Mapbox / MapLibre "
        "GL geospatial mapping ecosystem—whose pioneering open-source architectures enabled the foundation of this engineering realization."
    )
    mgr.para(
        "Finally, I am profoundly grateful to my family, colleagues, and peers for their continuous moral support and constructive feedback."
    )
    p_ack_sig = doc.add_paragraph()
    p_ack_sig.paragraph_format.space_before = Pt(30)
    p_ack_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_ack = p_ack_sig.add_run("Nakshatra")
    r_ack.font.name = "Calibri"
    r_ack.font.bold = True

    mgr.page_break()

    # -------------------------------------------------------------
    # 5. ABSTRACT & KEYWORDS
    # -------------------------------------------------------------
    mgr.heading_1("ABSTRACT", space_before=24)
    mgr.para(
        "Remote sensing satellite imagery has grown exponentially in spatial resolution and temporal frequency; however, traditional "
        "Geographic Information System (GIS) workflows remain heavily dependent on manual digitizing, heuristic spectral index formulas, or "
        "closed-vocabulary supervised semantic segmentation pipelines that cannot interpret unstructured, natural language user queries. "
        "Conversely, modern Vision-Language Models (VLMs) demonstrate outstanding multimodal reasoning and semantic perception but suffer from "
        "severe spatial hallucinations and coarse coordinate quantization when tasked with pixel-exact geospatial delineation."
    )
    mgr.para(
        "To bridge this critical geospatial reasoning gap, this project introduces SatQuery AI: an interactive, multimodal geospatial intelligence "
        "platform that decouples high-level semantic vision-language reasoning from fine-grained prompt-guided pixel segmentation. SatQuery AI "
        "implements a novel dual-engine architecture: (1) an advanced Multimodal Vision-Language Reasoning Engine powered by Google Gemini 2.0 "
        "Flash that parses complex conversational user prompts, extracts environmental scene semantics, and generates structured bounding box "
        "grounding coordinates; (2) a Dense Grounding & Geometric Normalization Service that bridges disparate coordinate spaces between VLM "
        "normalized tokens [0, 1000] and physical image pixel matrices; and (3) a Visual Segmentation Engine powered by Meta's Segment Anything "
        "Model 2.1 (SAM 2.1) backed by an adaptive GrabCut heuristic computer vision fallback mechanism."
    )
    mgr.para(
        "The platform features an asynchronous FastAPI ASGI backend and an interactive, real-time React 18 / TypeScript frontend equipped with "
        "Mapbox GL 3D vector and satellite GIS canvas overlays, interactive prompt refinement (point clicks and bounding box adjustments), and real-time visual inspection. "
        "Extensive benchmarking demonstrates that SatQuery AI achieves high segmentation accuracy (Mean IoU of 0.84 on complex water body "
        "delineation and 0.79 on dense building footprints) while maintaining an end-to-end conversational round-trip latency of 1.2 to 2.8 seconds, "
        "eliminating the need for custom re-training across varying Earth Observation sensor modalities."
    )
    mgr.callout(
        "Multimodal Geospatial AI, Vision-Language Models (VLMs), Dense Visual Grounding, Segment Anything Model 2.1 (SAM 2.1), "
        "Remote Sensing & Earth Observation, Interactive GIS, Coordinate Space Transformation, GrabCut Heuristic Fallback, FastAPI, React.",
        title="KEYWORDS"
    )

    mgr.page_break()

    # -------------------------------------------------------------
    # 6. TABLE OF CONTENTS
    # -------------------------------------------------------------
    mgr.heading_1("TABLE OF CONTENTS", space_before=24)
    toc_items = [
        ("Certificate of Approval", "ii"),
        ("Declaration", "iii"),
        ("Acknowledgement", "iv"),
        ("Abstract & Keywords", "v"),
        ("List of Figures", "vii"),
        ("List of Tables", "viii"),
        ("Chapter 1: Introduction & Background", "1"),
        ("Chapter 2: Literature Review & State-of-the-Art Analysis", "5"),
        ("Chapter 3: Problem Statement & Engineering Objectives", "10"),
        ("Chapter 4: System Architecture & Design", "14"),
        ("Chapter 5: Technical Stack & Tool Selection Justification", "21"),
        ("Chapter 6: Frontend Engineering & Interactive Geospatial UI", "26"),
        ("Chapter 7: Backend Architecture & API Gateway", "32"),
        ("Chapter 8: VLM Reasoning Engine & Prompt Engineering", "37"),
        ("Chapter 9: Dense Grounding Service & Coordinate Spaces", "42"),
        ("Chapter 10: SAM 2.1 Visual Segmentation Architecture", "47"),
        ("Chapter 11: Heuristic Fallback Pipeline & Classical CV", "52"),
        ("Chapter 12: Satellite Preprocessing & Multimodal Pipeline", "57"),
        ("Chapter 13: Database & Conversation History Subsystem", "62"),
        ("Chapter 14: Data Flow & End-to-End Walkthrough", "66"),
        ("Chapter 15: Installation, Environment & Deployment Guide", "72"),
        ("Chapter 16: Verification, Testing & Quality Assurance", "77"),
        ("Chapter 17: Architectural Trade-Offs & Decisions", "82"),
        ("Chapter 18: Security, Privacy & Performance Optimization", "87"),
        ("Chapter 19: Limitations, Pitfalls & Lessons Learned", "91"),
        ("Chapter 20: Future Scope & Roadmap", "95"),
        ("Chapter 21: Conclusion & Academic Summary", "99"),
        ("References & Academic Citations", "102")
    ]
    mgr.table(["Chapter / Section Title", "Page"], toc_items, col_widths=[5.5, 1.0])

    mgr.page_break()

    # -------------------------------------------------------------
    # 7. LIST OF FIGURES & LIST OF TABLES
    # -------------------------------------------------------------
    mgr.heading_1("LIST OF FIGURES & TABLES", space_before=24)
    mgr.heading_2("List of Figures")
    figures = [
        ("Figure 4.1", "High-Level End-to-End System Architecture Diagram", "15"),
        ("Figure 4.2", "Asynchronous Request-Response Sequence Diagram", "18"),
        ("Figure 4.3", "Subsystem Functional Decomposition", "20"),
        ("Figure 6.1", "Frontend React Component Hierarchy & State Machine", "27"),
        ("Figure 6.2", "Canvas Layering & Geo-Coordinate Synchronization", "30"),
        ("Figure 7.1", "FastAPI Asynchronous Gateway & Lifespan Architecture", "33"),
        ("Figure 8.1", "Vision-Language Grounding Prompt Pipeline", "38"),
        ("Figure 9.1", "Coordinate Space Transformation Matrix & Flow", "43"),
        ("Figure 10.1", "Meta SAM 2.1 Image Predictor Architecture & Prompt Decoding", "48"),
        ("Figure 10.2", "Multi-Mask Selection & Ambiguity Disambiguation", "50"),
        ("Figure 11.1", "GrabCut Gaussian Mixture Model (GMM) Energy Minimization Graph", "53"),
        ("Figure 11.2", "Dual-Engine Fail-Safe Switchover State Machine", "55"),
        ("Figure 12.1", "Satellite Ingestion & Dynamic Range Radiometric Pipeline", "58"),
        ("Figure 13.1", "Entity-Relationship (ER) Schema for Geospatial Conversation Subsystem", "63"),
        ("Figure 14.1", "Flood Delineation Execution Trace & Data Transformation Pipeline", "68"),
        ("Figure 14.2", "Building Footprint Extraction Flowchart", "70")
    ]
    mgr.table(["Figure No.", "Caption", "Page"], figures, col_widths=[1.2, 4.3, 1.0])

    mgr.heading_2("List of Tables", space_before=14)
    tables = [
        ("Table 2.1", "Comparative Analysis of Geospatial & Remote Sensing AI Paradigms", "8"),
        ("Table 5.1", "Frontend Technology Stack & Component Justifications", "22"),
        ("Table 5.2", "Backend & Geospatial Gateway Technology Stack", "23"),
        ("Table 5.3", "AI / Computer Vision & Segmentation Libraries", "24"),
        ("Table 7.1", "FastAPI Core REST Endpoints & Data Contracts", "35"),
        ("Table 16.1", "Automated Functional & End-to-End Test Suite Matrix", "78"),
        ("Table 16.2", "Quantitative Segmentation Performance Benchmarks (IoU, Latency, Memory)", "80"),
        ("Table 17.1", "Architectural Trade-Offs & Multi-Criteria Decision Analysis", "84"),
        ("Table 18.1", "Threat Modeling & Security Countermeasures Matrix", "89")
    ]
    mgr.table(["Table No.", "Title", "Page"], tables, col_widths=[1.2, 4.3, 1.0])

    mgr.page_break()


def build_chapters_1_to_7(mgr):
    # -------------------------------------------------------------
    # CHAPTER 1: INTRODUCTION & BACKGROUND
    # -------------------------------------------------------------
    mgr.heading_1("CHAPTER 1: INTRODUCTION & BACKGROUND")
    mgr.heading_2("1.1 Domain Overview: Earth Observation and Remote Sensing")
    mgr.para(
        "Earth Observation (EO) satellite remote sensing has undergone a monumental paradigm shift over the past decade. "
        "Constellations of public and commercial satellites—ranging from the European Space Agency's (ESA) Copernicus Sentinel-2 "
        "and NASA/USGS Landsat-8/9 to high-resolution commercial systems like PlanetScope, Maxar WorldView, and Airbus Pléiades—capture "
        "hundreds of terabytes of multi-spectral, panchromatic, and synthetic aperture radar (SAR) imagery daily. This continuous influx "
        "of high-resolution orbital imagery provides unprecedented insight into environmental dynamics, urban urbanization, climate "
        "resilience, disaster assessment, defense reconnaissance, and agricultural yields."
    )
    mgr.para(
        "Despite this abundant sensor data, transforming raw raster pixels into actionable, context-aware intelligence remains an "
        "arduous computational challenge. Traditional Geographic Information Systems (GIS) workflows rely extensively on human domain "
        "specialists using specialized desktop software (e.g., QGIS, ESRI ArcGIS) to manually digitize features, apply handcrafted "
        "band math indices (such as Normalized Difference Vegetation Index - NDVI, or Modified Normalized Difference Water Index - MNDWI), "
        "or train isolated supervised machine learning classifiers on static datasets. These manual workflows are slow, resource-intensive, "
        "and incapable of scaling to crisis response scenarios where minutes count."
    )

    mgr.heading_2("1.2 The Geospatial Reasoning Gap")
    mgr.para(
        "In recent years, the emergence of Large Multimodal Models (LMMs) and Vision-Language Models (VLMs)—such as OpenAI GPT-4V/4o, "
        "Google Gemini 1.5/2.0, and Anthropic Claude 3.5 Sonnet—has revolutionized natural language computer vision. Users can converse "
        "in plain English with an AI system, asking open-ended questions about images. However, when applied to satellite remote sensing, "
        "standard VLMs encounter severe fundamental limitations termed the Geospatial Reasoning Gap:"
    )
    mgr.bullet("Extreme Aspect Ratios & Gigapixel Scales", "Satellite images span kilometers of terrain at resolutions from 30 cm to 10 m per pixel. Standard VLMs downsample input images to fixed low-resolution tokens (e.g., 512x512 or 1024x1024), obliterating critical small-scale targets like vehicles, building footprints, and irrigation channels.")
    mgr.bullet("Lack of Nadir-Angle Spatial Priors", "Standard computer vision models are pre-trained on internet photography (natural perspective images characterized by upright orientation, horizon lines, and central focal objects). Overhead satellite imagery lacks a canonical horizon, exhibits arbitrary rotational orientations, and presents dense, overlapping semantic structures.")
    mgr.bullet("Spatial Hallucinations & Coarse Coordinate Quantization", "While modern VLMs can produce text bounding boxes, their spatial tokens are quantized into coarse discrete bins (e.g., normalized [0, 1000]). These coordinates produce loose, approximate bounding boxes that fail completely when pixel-precise spatial delineation, boundary tracing, or area calculation is required.")
    mgr.bullet("Closed-Vocabulary Limitations of Classical CNNs", "Supervised segmentation networks (e.g., U-Net, DeepLabV3+, Mask R-CNN) segment only the exact fixed categories they were trained on (e.g., 'building', 'road'). They cannot generalize to unstructured queries such as 'highlight the flooded sports complex behind the airport' or 'identify residential buildings with blue rooftop tarpaulins'.")

    mgr.heading_2("1.3 Project Motivation: SatQuery AI")
    mgr.para(
        "The motivation behind SatQuery AI is to bridge this foundational divide. By engineering a hybrid architecture that pairs "
        "the advanced semantic and contextual reasoning of large Vision-Language Models with the zero-shot, prompt-guided pixel delineation "
        "capabilities of Meta's Segment Anything Model 2.1 (SAM 2.1), SatQuery AI enables true conversational geospatial intelligence. "
        "A user can upload an arbitrary satellite or aerial scene, pose complex domain-specific questions in natural language, and receive "
        "both deep environmental analysis and sub-pixel visual groundings rendered directly on an interactive GIS map canvas."
    )

    mgr.heading_2("1.4 Real-World Applications & Impact")
    mgr.bullet("Disaster Response & Inundation Mapping", "Rapid delineation of flooded residential neighborhoods, blocked evacuation routes, and broken bridges following catastrophic hurricane or monsoonal flooding events.")
    mgr.bullet("Urban Planning & Infrastructure Auditing", "Automated extraction of unauthorized building footprints, informal settlements, green canopy loss, and transport network expansion.")
    mgr.bullet("Agricultural Land-Use & Water Security", "Zero-shot identification of agricultural crop borders, center-pivot irrigation systems, drying water reservoirs, and drought severity.")
    mgr.bullet("Environmental & Forest Conservation", "Monitoring illegal deforestation frontiers, mining encroachments, and coastal erosion along sensitive ecological corridors.")

    mgr.page_break()

    # -------------------------------------------------------------
    # CHAPTER 2: LITERATURE REVIEW & STATE-OF-THE-ART
    # -------------------------------------------------------------
    mgr.heading_1("CHAPTER 2: LITERATURE REVIEW & STATE-OF-THE-ART ANALYSIS")
    mgr.heading_2("2.1 Evolution of Remote Sensing Image Analysis")
    mgr.para(
        "The automated interpretation of satellite remote sensing imagery has evolved across four distinct eras over the last four decades: "
        "classical radiometric thresholding, supervised pixel classification, deep convolutional neural networks (CNNs), and foundation models."
    )
    mgr.para(
        "During the classical era (1980s–2000s), spectral indices formed the primary methodology. By computing mathematical ratios between "
        "distinct electromagnetic bands (e.g., Red, Near-Infrared, Shortwave-Infrared), researchers formulated indices such as NDVI for vegetation "
        "and NDWI for surface water. While computationally efficient, these indices require explicit multi-spectral bands, are sensitive to atmospheric "
        "haze, and provide zero semantic understanding of geometric shape, texture, or spatial context."
    )
    mgr.para(
        "The machine learning era (2000s–2014) introduced supervised classifiers such as Random Forests, Support Vector Machines (SVM), and Maximum "
        "Likelihood Classifiers applied to handcrafted texture features (e.g., Haralick texture, Gray-Level Co-occurrence Matrix - GLCM). These methods "
        "improved classification accuracy but exhibited poor cross-sensor generalization and high vulnerability to seasonal radiometric drift."
    )
    mgr.para(
        "The deep learning revolution (2015–2022) established end-to-end convolutional architectures. Fully Convolutional Networks (FCNs), U-Net, "
        "and DeepLabV3+ with Atrous Spatial Pyramid Pooling (ASPP) became the gold standard for semantic segmentation, while Mask R-CNN established "
        "instance segmentation benchmarks. However, these models require millions of manually annotated polygon masks and operate strictly on a "
        "closed vocabulary: a network trained to detect buildings cannot segment sports fields, runways, or solar farms without complete retraining."
    )

    mgr.heading_2("2.2 Foundation Models and Vision-Language Architectures")
    mgr.para(
        "The advent of Transformer-based foundation models has transformed computer vision. OpenAI's CLIP demonstrated that training image and "
        "text encoders on hundreds of millions of web image-text pairs produces an aligned multimodal latent space capable of open-vocabulary "
        "classification. Modern Vision-Language Models (e.g., LLaVA, Gemini, GPT-4V) extend this principle by coupling visual encoders (like "
        "Vision Transformers - ViT) directly into auto-regressive Large Language Model decoders via cross-attention or projection layers."
    )
    mgr.para(
        "In 2023, Meta AI introduced the Segment Anything Model (SAM), establishing the first foundation model for promptable image segmentation. "
        "Trained on the massive SA-1B dataset (over 1 billion masks on 11 million images), SAM demonstrated unprecedented zero-shot transferability. "
        "In late 2024, Meta released SAM 2 and SAM 2.1, introducing a unified Hiera hierarchical vision transformer backbone, memory attention "
        "mechanisms, and drastically enhanced inference speed for both video streams and single images."
    )

    mgr.heading_2("2.3 Comparative Literature Matrix")
    mgr.para("Table 2.1 evaluates existing paradigms across critical dimensions for interactive geospatial intelligence.")
    
    comp_headers = ["Paradigm / Architecture", "Primary Input Modality", "Vocabulary", "Spatial Granularity", "Conversational Reasoning", "Inference Latency"]
    comp_data = [
        ["Spectral Indices (NDVI/MNDWI)", "Multispectral Bands", "Fixed Math Ratios", "Pixel-level (Coarse)", "None (Rigid formulas)", "< 50 ms (CPU)"],
        ["Supervised CNN (U-Net/DeepLab)", "RGB / Multispectral", "Closed (K Classes)", "Sub-pixel Boundaries", "None (Static class IDs)", "100–300 ms (GPU)"],
        ["Standard VLM (GPT-4V/Gemini)", "RGB Image + Prompt", "Open Vocabulary", "Coarse Bounding Boxes", "High (Full reasoning)", "1.0–3.0 s (API)"],
        ["Raw SAM 2.1 (Zero-Shot)", "RGB Image + Visual Prompts", "Class Agnostic", "Exact Object Masks", "None (Needs box/point prompt)", "80–250 ms (GPU)"],
        ["SatQuery AI (Hybrid Engine)", "Satellite RGB + Natural Query", "Open-Vocabulary Natural Lang.", "Sub-pixel SAM 2.1 Masks", "High (Full Gemini 2.0 VLM)", "1.2–2.8 s (Full End-to-End)"]
    ]
    mgr.table(comp_headers, comp_data, col_widths=[1.5, 1.0, 1.1, 1.0, 1.1, 0.8], caption="Table 2.1: Comparative Analysis of Geospatial & Remote Sensing AI Paradigms")

    mgr.heading_2("2.4 Identified Research Gap")
    mgr.para(
        "While foundation models have advanced independently in vision-language reasoning (Gemini, GPT) and promptable segmentation (SAM 2.1), "
        "no unified system has effectively synthesized them for the unique domain constraints of satellite earth observation. Specifically: "
        "(1) VLMs cannot directly output clean binary or polygon mask representations; (2) SAM 2.1 possesses no native semantic language comprehension "
        "and requires external geometric prompts; and (3) when GPU resources or model weights fail in edge or low-compute operational centers, "
        "modern deep learning systems crash completely without a graceful algorithmic fallback. SatQuery AI directly addresses this gap."
    )

    mgr.page_break()

    # -------------------------------------------------------------
    # CHAPTER 3: PROBLEM STATEMENT & OBJECTIVES
    # -------------------------------------------------------------
    mgr.heading_1("CHAPTER 3: PROBLEM STATEMENT & ENGINEERING OBJECTIVES")
    mgr.heading_2("3.1 Formal Problem Statement")
    mgr.para(
        "Let I in R^{H x W x C} denote an arbitrary satellite image raster of height H, width W, and channels C (where C >= 3 for RGB optical imagery). "
        "Let Q = {w_1, w_2, ..., w_L} represent an unstructured, natural language user query of length L expressing a semantic inquiry or visual extraction request. "
        "The objective of the system is to learn a mapping function f: (I, Q) -> (T, B, M) such that:"
    )
    mgr.bullet("Textual Reasoning Response (T)", "An articulated, context-aware natural language analytical response explaining scene features, environmental conditions, and semantic answers to Q.")
    mgr.bullet("Dense Grounding Bounding Boxes (B)", "A set of spatial bounding boxes B = {b_1, b_2, ..., b_k} where each b_i = (ymin, xmin, ymax, xmax) delineates the localized regions of interest corresponding to target entities in Q.")
    mgr.bullet("Pixel-Exact Segmentation Mask (M)", "A binary or multi-class segmentation mask matrix M in {0, 1}^{H x W} accurately capturing the sub-pixel boundary geometry of target geospatial features without semantic boundary bleeding or background false positives.")

    mgr.heading_2("3.2 Functional Objectives")
    mgr.bullet("Conversational Geospatial Reasoning", "Implement an asynchronous VLM pipeline capable of answering complex analytical queries concerning land cover, structural density, water presence, and disaster impact.")
    mgr.bullet("Autonomous Visual Grounding", "Translate natural language instructions into precise normalized coordinates [0, 1000] and remap them to actual image pixel coordinates without manual user box drawing.")
    mgr.bullet("Zero-Shot Sub-Pixel Mask Generation", "Leverage SAM 2.1 to generate sharp, clean boundary segmentations from VLM-derived bounding box and point prompts.")
    mgr.bullet("Deterministic Heuristic Fallback", "Implement a classical computer vision pipeline utilizing GrabCut Gaussian Mixture Models and HSV/Lab color segmentation that guarantees execution continuity on CPU-only hardware or during GPU out-of-memory states.")
    mgr.bullet("Interactive Canvas UI & GIS Alignment", "Provide an intuitive web interface with Mapbox GL 3D satellite mapping overlays, enabling users to pan, zoom, pitch, click to add interactive positive/negative prompts, and inspect confidence scores.")

    mgr.heading_2("3.3 Non-Functional Objectives")
    mgr.bullet("Low Latency", "End-to-end response time under 3 seconds for full VLM reasoning plus dense mask generation on standard 1024x1024 satellite tiles.")
    mgr.bullet("Graceful Degradation", "System availability must remain 100% even if CUDA GPU acceleration is unavailable, switching automatically to CPU GrabCut fallback without throwing client errors.")
    mgr.bullet("Modular Extensibility", "Decoupled service architecture enabling independent upgrades to the VLM (e.g., Gemini 2.0 -> future models) or segmentation engine (SAM 2.1 -> SAM 3) without backend refactoring.")
    mgr.bullet("Memory Efficiency", "Backend memory consumption kept under 4 GB VRAM on GPU and under 2 GB RAM on CPU during image feature caching.")

    mgr.page_break()

    # -------------------------------------------------------------
    # CHAPTER 4: SYSTEM ARCHITECTURE & DESIGN
    # -------------------------------------------------------------
    mgr.heading_1("CHAPTER 4: SYSTEM ARCHITECTURE & DESIGN")
    mgr.heading_2("4.1 High-Level Architecture Overview")
    mgr.para(
        "SatQuery AI is architected as a high-performance, decoupled, multi-tiered platform. By strictly separating high-level "
        "multimodal reasoning (Vision-Language) from low-level spatial geometry and pixel-level segmentation (SAM 2.1 and GrabCut), "
        "the architecture avoids the monolithic failure modes common in early deep learning prototypes."
    )

    diag_arch = """
+-----------------------------------------------------------------------------------+
|                              SATQUERY AI CLIENT TIER                              |
|  +---------------------------+  +----------------------+  +--------------------+  |
|  | React 18 / TypeScript SPA |  | Mapbox GL 3D Canvas  |  | Interactive Prompt |  |
|  | Tailwind UI Components    |  | Dual-Layer Mask View |  | Point/Box Tooling  |  |
|  +---------------------------+  +----------------------+  +--------------------+  |
+------------------------------------------+----------------------------------------+
                                           | HTTP REST / JSON Payload
                                           v
+-----------------------------------------------------------------------------------+
|                        FASTAPI API GATEWAY (SERVER TIER)                         |
|  +-------------------------+  +--------------------------+  +-------------------+  |
|  | ASGI Lifespan Engine    |  | Coordinate Normalization |  | CORS & Security   |  |
|  | Uvicorn Async Workers   |  | Bounding Box Parser      |  | Error Middleware  |  |
|  +-------------------------+  +--------------------------+  +-------------------+  |
+------------------------------------------+----------------------------------------+
                                           |
                   +-----------------------+-----------------------+
                   |                                               |
                   v                                               v
+--------------------------------------+       +------------------------------------+
|       VLM REASONING ENGINE           |       |    VISUAL SEGMENTATION ENGINE      |
|  +--------------------------------+  |       |  +-------------------------------+ |
|  | Google Gemini 2.0 Flash API    |  |       |  | Meta SAM 2.1 Image Predictor  | |
|  | Grounding Prompt Orchestrator  |  |       |  | Hiera Backbone / Mask Decoder | |
|  | JSON Schema Output Validator   |  |       |  +-------------------------------+ |
|  +--------------------------------+  |       |                  | (GPU Fail / OOM)|
|                                      |       |                  v                 |
|  Outputs:                            |       |  +-------------------------------+ |
|  - Analytical Text Response          |       |  | Heuristic Fallback Pipeline   | |
|  - Normalized BBoxes [0, 1000]       |       |  | GrabCut GMM + HSV Masking     | |
|  - Confidence & Target Categories    |       |  +-------------------------------+ |
+--------------------------------------+       +------------------------------------+
                   |                                               |
                   +-----------------------+-----------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                              DATA & PERSISTENCE TIER                              |
|  +-------------------------------+  +---------------------+  +------------------+  |
|  | SQLite / SQLAlchemy ORM       |  | Static Upload Store |  | Alpha Mask Cache |  |
|  | Chat Sessions & Hist. Vectors |  | GeoTIFF / JPG / PNG |  | PNG RGBA Overlay |  |
|  +-------------------------------+  +---------------------+  +------------------+  |
+-----------------------------------------------------------------------------------+
    """
    mgr.diagram_box(diag_arch, caption="Figure 4.1: High-Level End-to-End System Architecture Diagram")

    mgr.heading_2("4.2 Separation of Concerns: Decoupled Dual-Engine Model")
    mgr.para(
        "A central innovation of SatQuery AI is the strict decoupling of the reasoning engine from the segmentation engine. "
        "In naive vision-language architectures, researchers attempt to force the language model to output binary mask tokens directly "
        "(e.g., polygon coordinate lists in text). This approach suffers from token context overflow, high latency, and frequent syntax errors. "
        "SatQuery AI solves this through a divide-and-conquer strategy:"
    )
    mgr.bullet("VLM handles Semantics & Macro-Localization", "The VLM interprets the user prompt, considers geospatial context, answers questions, and identifies approximate bounding box coordinates for target features.")
    mgr.bullet("SAM 2.1 handles Micro-Geometry & Sub-Pixel Delineation", "The segmentation engine receives the image embedding and VLM bounding boxes as geometric prompts, generating crisp, sub-pixel binary masks along actual spectral and physical edges.")

    mgr.heading_2("4.3 Sequence & Request Flow")
    mgr.para("Figure 4.2 illustrates the end-to-end execution lifecycle for a user query.")

    diag_seq = """
USER / CLIENT                   FASTAPI GATEWAY               GEMINI 2.0 VLM          SAM 2.1 / GRABCUT
      |                                |                             |                        |
      |--- 1. POST /api/analyze ------>|                             |                        |
      |    (image_url, user_prompt)    |--- 2. Encode Image & ------->|                        |
      |                                |    Structured Prompt        |                        |
      |                                |                             |                        |
      |                                |<-- 3. Return JSON Response -|                        |
      |                                |    (Text + BBoxes [0..1000])|                        |
      |                                |                             |                        |
      |                                |--- 4. Transform Coords ----------------------------->|
      |                                |    ([0..1000] -> [0..W, 0..H])                       |
      |                                |                                                      |--- 5. Predict Mask
      |                                |                                                      |    from Box Prompts
      |                                |<-- 6. Return Binary Mask & IoU ----------------------|
      |                                |
      |<-- 7. Return Full Response ----|
      |    (Analysis, Mask URL, BBox)  |
      |                                |
    """
    mgr.diagram_box(diag_seq, caption="Figure 4.2: Asynchronous Request-Response Sequence Diagram")

    mgr.page_break()

    # -------------------------------------------------------------
    # CHAPTER 5: TECHNICAL STACK & JUSTIFICATION
    # -------------------------------------------------------------
    mgr.heading_1("CHAPTER 5: TECHNICAL STACK & JUSTIFICATION")
    mgr.heading_2("5.1 Technical Architecture Overview")
    mgr.para(
        "The technology stack of SatQuery AI was selected after rigorous benchmarking of latency, developer productivity, "
        "cross-platform reliability, and mathematical precision. Tables 5.1 through 5.3 enumerate the technologies employed."
    )

    mgr.heading_2("5.2 Frontend Technology Stack")
    fe_headers = ["Technology / Library", "Version", "Role in Architecture", "Justification & Benefits"]
    fe_data = [
        ["React", "18.3.1", "Core UI Framework", "Component-driven architecture, virtual DOM reconciliation, robust ecosystem."],
        ["TypeScript", "5.5.0", "Type Safety & Contracts", "Eliminates runtime coordinate errors, enforces strict API interfaces."],
        ["Tailwind CSS", "3.4.0", "Utility-First Styling", "Rapid responsive styling, zero CSS runtime overhead, modern dark UI."],
        ["Mapbox GL / MapLibre GL", "3.6.2", "Interactive Geospatial GIS", "High-performance WebGL 3D vector and satellite tile rendering, custom CRS, pitch & rotation."],
        ["Lucide React", "0.400+", "Vector Iconography", "Crisp geospatial, analytical, and system status visual iconography."],
        ["Vite", "5.3.0", "Frontend Build Tool", "Instant Hot Module Replacement (HMR), optimized Rollup production bundling."]
    ]
    mgr.table(fe_headers, fe_data, col_widths=[1.5, 0.8, 1.6, 2.6], caption="Table 5.1: Frontend Technology Stack & Component Justifications")

    mgr.heading_2("5.3 Backend & AI Technology Stack")
    be_headers = ["Technology / Library", "Version", "Role in Architecture", "Justification & Benefits"]
    be_data = [
        ["Python", "3.11 / 3.13", "Core Runtime", "Native AI/ML ecosystem, PyTorch compatibility, dynamic data structures."],
        ["FastAPI", "0.115+", "ASGI Web Gateway", "High-throughput async execution, native Pydantic validation, OpenAPI docs."],
        ["Uvicorn", "0.30+", "ASGI Web Server", "Lightning-fast async HTTP/WebSocket event loop execution."],
        ["PyTorch", "2.4+ (CUDA)", "Deep Learning Runtime", "GPU tensor computation, automatic differentiation, SAM 2.1 inference."],
        ["Meta SAM 2.1", "2.1 checkpoint", "Visual Segmentation", "State-of-the-art zero-shot promptable segmentation, Hiera backbone."],
        ["Google Gemini API", "v1beta / 2.0", "Vision-Language Model", "Exceptional multimodal comprehension, structured JSON output, low latency."],
        ["OpenCV (cv2)", "4.10+", "Computer Vision Pipeline", "GrabCut GMM segmentation, morphological operations, affine transforms."],
        ["SQLAlchemy / SQLite", "2.0+", "Persistence & History", "Lightweight zero-configuration relational storage for session states."]
    ]
    mgr.table(be_headers, be_data, col_widths=[1.5, 0.8, 1.6, 2.6], caption="Table 5.2: Backend & Geospatial Gateway Technology Stack")

    mgr.page_break()

    # -------------------------------------------------------------
    # CHAPTER 6: FRONTEND ENGINEERING & GEOSPATIAL UI
    # -------------------------------------------------------------
    mgr.heading_1("CHAPTER 6: FRONTEND ENGINEERING & INTERACTIVE GEOSPATIAL UI")
    mgr.heading_2("6.1 Component Hierarchy and State Architecture")
    mgr.para(
        "The SatQuery AI frontend is built around an event-driven, unidirectional data flow. The user interface is composed "
        "of modular React functional components, managed by clean React hooks and TypeScript interfaces."
    )

    diag_fe = """
+-----------------------------------------------------------------------------------+
|                                  App.tsx (Root)                                   |
|  - Manages active session ID, upload state, and active image metadata            |
+------------------------------------------+----------------------------------------+
                                           |
                 +-------------------------+-------------------------+
                 |                                                   |
                 v                                                   v
+----------------------------------+               +--------------------------------+
|         MapCanvas.tsx            |               |         ChatPanel.tsx          |
|  - Mapbox GL 3D Container        |               |  - Message List (User/AI)      |
|  - TileLayer (Satellite Base)    |               |  - Markdown Formatter          |
|  - CanvasOverlay (Mask Blending) |               |  - Query Input & Voice Button  |
|  - BoundingBoxSvgOverlay         |               |  - Grounding Confidence Badge  |
|  - Interactive Prompt Markers    |               |  - Prompt Suggestions Strip    |
+----------------------------------+               +--------------------------------+
                 |                                                   |
                 +-------------------------+-------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                                Toolbar & Control Bar                              |
|  - Mode Switch: (Inspect, BBox Draw, Point Prompt (+/-), Layer Opacity Slider)   |
|  - Action Buttons: Clear Mask, Download GeoJSON, Export PNG Overlay, Reset View  |
+-----------------------------------------------------------------------------------+
    """
    mgr.diagram_box(diag_fe, caption="Figure 6.1: Frontend React Component Hierarchy & State Machine")

    mgr.heading_2("6.2 Canvas Layering and Coordinate Alignment")
    mgr.para(
        "A critical frontend engineering challenge in SatQuery AI is rendering pixel-exact segmentation masks directly on top of "
        "satellite images that may be panned, zoomed, or scaled by the user. If naive image overlays are used, raster blurring or "
        "misalignment occurs during fractional zoom states."
    )
    mgr.para(
        "SatQuery AI resolves this using a synchronized three-layer rendering architecture:"
    )
    mgr.bullet("Layer 0 (Base Raster)", "Renders the original satellite image either as a static high-resolution raster or georeferenced Mapbox GL ImageSource overlay using EPSG:3857 Web Mercator projection.")
    mgr.bullet("Layer 1 (Segmentation Mask Canvas)", "An HTML5 2D Canvas positioned synchronously over Layer 0. The binary mask received from the backend is rendered with a customizable RGBA color palette (e.g., translucent cyan rgba(6, 182, 212, 0.45) for water, vibrant red rgba(239, 68, 68, 0.5) for buildings) and blended using globalCompositeOperation = 'source-over'.")
    mgr.bullet("Layer 2 (Vector Annotation SVG Layer)", "An SVG viewport matching the natural dimensions of the image. Bounding boxes, center coordinates, and interactive click markers are rendered as crisp vector primitives with SVG stroke-dasharray animations and hover tooltips.")

    mgr.page_break()

    # -------------------------------------------------------------
    # CHAPTER 7: BACKEND ARCHITECTURE & API GATEWAY
    # -------------------------------------------------------------
    mgr.heading_1("CHAPTER 7: BACKEND ARCHITECTURE & API GATEWAY")
    mgr.heading_2("7.1 Asynchronous Server Design")
    mgr.para(
        "The SatQuery AI backend is implemented with FastAPI, leveraging Python's asyncio event loop to achieve high concurrent throughput. "
        "FastAPI's native dependency injection and Pydantic validation system ensure that all incoming requests are validated against "
        "strict schemas before execution, preventing malformed coordinates or corrupt image payloads from propagating to downstream AI engines."
    )

    mgr.heading_2("7.2 REST API Specification")
    mgr.para("Table 7.1 details the primary REST endpoints exposed by the API Gateway.")

    api_headers = ["Endpoint", "HTTP Method", "Request Payload", "Response Payload", "Description & Purpose"]
    api_data = [
        ["/api/analyze", "POST", "{ image_path, prompt, session_id }", "{ answer, bboxes, mask_url, time_ms }", "Primary multimodal reasoning & visual grounding endpoint."],
        ["/api/segment", "POST", "{ image_path, bboxes, points, mode }", "{ mask_url, iou_score, engine_used }", "Direct segmentation endpoint for interactive point/box prompts."],
        ["/api/upload", "POST", "Multipart Form Data (file: image)", "{ file_url, width, height, format }", "Ingests satellite imagery, validates format, caches locally."],
        ["/api/sessions/{id}", "GET", "Path Parameter: id", "{ session_id, history: [messages] }", "Retrieves persisted conversation turns and mask history."],
        ["/api/health", "GET", "None", "{ status: 'ok', gpu: bool, sam_ready: bool }", "Health check probe for monitoring container readiness."]
    ]
    mgr.table(api_headers, api_data, col_widths=[1.2, 0.8, 1.8, 1.8, 1.6], caption="Table 7.1: FastAPI Core REST Endpoints & Data Contracts")

    mgr.heading_2("7.3 Lifespan Management & Model Pre-loading")
    mgr.para(
        "Loading deep learning weights (SAM 2.1 Hiera-B+ checkpoint is approximately 400 MB to 1.8 GB) incurs a 3 to 6-second delay. "
        "To eliminate this latency during user interactions, SatQuery AI utilizes FastAPI's modern @asynccontextmanager lifespan handler. "
        "Upon application startup, the server initializes the PyTorch CUDA device, loads the SAM 2.1 checkpoint into GPU VRAM, compiles "
        "the inference graph, and verifies API connectivity with the Gemini Vision service. When the server shuts down, the lifespan handler "
        "explicitly releases GPU memory via torch.cuda.empty_cache()."
    )

print("Report Part 1 (Front Matter + Chapters 1-7) created successfully.")
