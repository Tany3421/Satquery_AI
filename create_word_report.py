#!/usr/bin/env python3
"""
create_word_report.py
Generates a comprehensive, professional Word document (.docx) of the full
SatQuery AI prototype technical report with deep component descriptions.
"""

import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def create_full_prototype_report(output_path="SatQuery_AI_Full_Prototype_Technical_Report.docx"):
    doc = docx.Document()

    # Colors
    NAVY = RGBColor(26, 54, 93)      # #1A365D
    SLATE = RGBColor(43, 108, 176)    # #2B6CB0
    TEAL = RGBColor(13, 148, 136)     # #0D9488
    CHARCOAL = RGBColor(30, 41, 59)   # #1E293B
    MUTED = RGBColor(100, 116, 139)   # #64748B
    
    PRIMARY_HEX = "1A365D"
    SECONDARY_HEX = "2B6CB0"
    TEAL_HEX = "0D9488"
    BG_LIGHT_HEX = "F8FAFC"
    BORDER_HEX = "CBD5E1"

    # Helpers
    def set_cell_background(cell, fill_hex):
        tcPr = cell._tc.get_or_add_tcPr()
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
        tcPr.append(shd)

    def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = parse_xml(f'''
            <w:tcMar {nsdecls("w")}>
                <w:top w:w="{top}" w:type="dxa"/>
                <w:bottom w:w="{bottom}" w:type="dxa"/>
                <w:left w:w="{left}" w:type="dxa"/>
                <w:right w:w="{right}" w:type="dxa"/>
            </w:tcMar>
        ''')
        tcPr.append(tcMar)

    def set_table_borders(table, color=BORDER_HEX, sz="4"):
        tblPr = table._tbl.tblPr
        borders = parse_xml(f'''
            <w:tblBorders {nsdecls("w")}>
                <w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
                <w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
                <w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>
                <w:insideV w:val="none"/>
                <w:left w:val="none"/>
                <w:right w:val="none"/>
            </w:tblBorders>
        ''')
        tblPr.append(borders)

    # Page layout
    for section in doc.sections:
        section.top_margin = Inches(0.9)
        section.bottom_margin = Inches(0.9)
        section.left_margin = Inches(0.9)
        section.right_margin = Inches(0.9)
        section.page_width = Inches(8.5)
        section.page_height = Inches(11.0)
        
        # Header & Footer
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hr = hp.add_run("SatQuery AI · Comprehensive Prototype Technical Specification · SIH26167 (ISRO)")
        hr.font.name = "Calibri"
        hr.font.size = Pt(8.5)
        hr.font.color.rgb = MUTED

        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        fr = fp.add_run("Lead Architect: Tanishq Shukla | Smart India Hackathon & ISRO Earth Observation")
        fr.font.name = "Calibri"
        fr.font.size = Pt(8.5)
        fr.font.color.rgb = MUTED

    # Typography builders
    def h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(20)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.name = "Calibri"
        r.font.bold = True
        r.font.size = Pt(17)
        r.font.color.rgb = NAVY
        pPr = p._p.get_or_add_pPr()
        pBdr = parse_xml(f'''
            <w:pBdr {nsdecls("w")}>
                <w:bottom w:val="single" w:sz="12" w:space="4" w:color="{SECONDARY_HEX}"/>
            </w:pBdr>
        ''')
        pPr.append(pBdr)
        return p

    def h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.name = "Calibri"
        r.font.bold = True
        r.font.size = Pt(13.5)
        r.font.color.rgb = SLATE
        return p

    def h3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.font.name = "Calibri"
        r.font.bold = True
        r.font.size = Pt(11.5)
        r.font.color.rgb = TEAL
        return p

    def para(text, bold_prefix="", space_after=6, italic=False):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            rp = p.add_run(bold_prefix)
            rp.font.name = "Calibri"
            rp.font.bold = True
            rp.font.color.rgb = NAVY
        rt = p.add_run(text)
        rt.font.name = "Calibri"
        rt.font.size = Pt(10.5)
        rt.font.italic = italic
        rt.font.color.rgb = CHARCOAL
        return p

    def bullet(title, desc):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.15
        rt = p.add_run(title)
        rt.font.name = "Calibri"
        rt.font.bold = True
        rt.font.size = Pt(10.5)
        rt.font.color.rgb = NAVY
        rd = p.add_run(f": {desc}")
        rd.font.name = "Calibri"
        rd.font.size = Pt(10.5)
        rd.font.color.rgb = CHARCOAL
        return p

    def callout(text, title="NOTE"):
        tbl = doc.add_table(rows=1, cols=1)
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl.autofit = False
        tbl.columns[0].width = Inches(6.7)
        cell = tbl.cell(0, 0)
        set_cell_background(cell, "F0FDF4" if "KEY" in title or "IMPORTANT" in title or "SUCCESS" in title else "F8FAFC")
        set_cell_margins(cell, top=120, bottom=120, left=180, right=160)
        tcPr = cell._tc.get_or_add_tcPr()
        tcBorders = parse_xml(f'''
            <w:tcBorders {nsdecls("w")}>
                <w:top w:val="none"/>
                <w:left w:val="single" w:sz="24" w:space="0" w:color="{TEAL_HEX}"/>
                <w:bottom w:val="none"/>
                <w:right w:val="none"/>
            </w:tcBorders>
        ''')
        tcPr.append(tcBorders)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.15
        rt = p.add_run(f"[{title}] ")
        rt.font.name = "Calibri"
        rt.font.bold = True
        rt.font.size = Pt(10)
        rt.font.color.rgb = TEAL
        rc = p.add_run(text)
        rc.font.name = "Calibri"
        rc.font.size = Pt(10)
        rc.font.color.rgb = CHARCOAL
        ps = doc.add_paragraph()
        ps.paragraph_format.space_after = Pt(4)

    # ------------------ COVER / DOCUMENT HEADER ------------------
    tp = doc.add_paragraph()
    tp.paragraph_format.space_before = Pt(15)
    tp.paragraph_format.space_after = Pt(4)
    tr = tp.add_run("🛰️ SatQuery AI: Full Prototype Technical Deep Dive & System Architecture Report")
    tr.font.name = "Calibri"
    tr.font.bold = True
    tr.font.size = Pt(22)
    tr.font.color.rgb = NAVY

    subp = doc.add_paragraph()
    subp.paragraph_format.space_after = Pt(12)
    subr = subp.add_run("Comprehensive Engineering Specification of All AI/ML Models, Software Tools, Geospatial Engines, Database Collections & Official Reporting Suites")
    subr.font.name = "Calibri"
    subr.font.italic = True
    subr.font.size = Pt(12)
    subr.font.color.rgb = SLATE

    # Meta Table
    meta_table = doc.add_table(rows=4, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.autofit = False
    meta_table.columns[0].width = Inches(2.2)
    meta_table.columns[1].width = Inches(4.5)
    set_table_borders(meta_table, BORDER_HEX, "6")
    
    meta_data = [
        ("Problem Statement ID", "SIH26167 (Smart India Hackathon / ISRO Earth Observation Division)"),
        ("Lead Architect & Author", "Tanishq Shukla"),
        ("Prototype Version & State", "v2.5 Full-Stack Deployed Prototype (FastAPI + MongoDB Compass + Web Studio)"),
        ("Date of Publication", "September 2026 · Official System Documentation")
    ]
    for i, (k, v) in enumerate(meta_data):
        c0 = meta_table.cell(i, 0)
        c1 = meta_table.cell(i, 1)
        set_cell_background(c0, "F1F5F9")
        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c0, 60, 60, 100, 100)
        set_cell_margins(c1, 60, 60, 100, 100)
        p0 = c0.paragraphs[0]
        p0.paragraph_format.space_after = Pt(0)
        r0 = p0.add_run(k)
        r0.font.bold = True
        r0.font.size = Pt(9.5)
        r0.font.color.rgb = NAVY
        p1 = c1.paragraphs[0]
        p1.paragraph_format.space_after = Pt(0)
        r1 = p1.add_run(v)
        r1.font.size = Pt(9.5)
        r1.font.color.rgb = CHARCOAL

    doc.add_paragraph().paragraph_format.space_after = Pt(10)

    # ------------------ SECTION 1 ------------------
    h1("1. Executive Summary & Operational Mission")
    para(
        "Earth Observation (EO) satellites—such as ISRO's Cartosat-2S, Cartosat-3, and RISAT-1A (EOS-04), alongside "
        "the European Space Agency's Sentinel-1 (C-band SAR) and Sentinel-2 (Multispectral Optical)—acquire vast streams of "
        "multi-gigabyte geospatial raster imagery on an hourly basis. However, transforming these raw spectral and microwave data streams "
        "into actionable decisions currently presents significant operational hurdles. Traditional pipelines require specialized GIS "
        "personnel, manual radiometric contrast stretching, offline GDAL/QGIS scripts, and complex temporal co-registrations."
    )
    para(
        "SatQuery AI resolves this operational bottleneck by introducing an enterprise-grade, vision-language powered geospatial "
        "intelligence platform. Through conversational natural language queries (via keyboard or hands-free voice dictation via OpenAI Whisper), "
        "analysts can perform immediate visual question answering, text-guided spatial object grounding with 2D bounding boxes, automated "
        "bi-temporal change detection, all-weather cloud penetration via optical+SAR microwave fusion, and real-time global location analysis. "
        "Every analysis is backed by an observable auditable execution trace, persistent document storage in MongoDB (visually inspectable "
        "in MongoDB Compass), and one-click generation of official ISRO/NRSC-compliant technical engineering reports."
    )
    callout(
        "SatQuery AI bridges the divide between petabytes of raw satellite sensor pixels and mission-critical decision-making for "
        "defense commanders, emergency rescue operations, district collectors, and agricultural planning officers.",
        "OPERATIONAL GOAL"
    )

    # ------------------ SECTION 2 ------------------
    h1("2. Exhaustive Description of Every AI & ML Model Used")
    para("SatQuery AI deploys a multi-tier, multi-model AI architecture designed to balance ultra-low latency, fine-grained remote sensing grounding, and 100% offline air-gapped capability:")

    models_info = [
        ("Google Gemini 2.0 Flash (gemini-2.0-flash)", 
         "Cloud Multimodal Foundation VLM",
         "Acts as the primary conversational and geospatial reasoning backbone. Ingests raw satellite rasters and coordinates to deliver structured JSON outputs containing detailed analytical findings, land-cover percentages, and evidence points. In the Live Location Explorer, Gemini 2.0 Flash synthesizes full strategic terrain dossiers from viewport canvas snapshots in under 280 milliseconds."),
        ("Qwen2.5-VL (qwen2.5-vl)", 
         "Open-Weights Vision-Language Model with Native Spatial Grounding",
         "Specialized in high-resolution visual grounding. Unlike standard chat models, Qwen2.5-VL natively predicts discrete, normalized 2D bounding box coordinates [ymin, xmin, ymax, xmax] mapped to visual features, identifying individual vessels, storage tanks, runways, and urban structures without external object detection heads."),
        ("EarthGPT & GeoChat", 
         "Remote Sensing Domain-Adapted Vision-Language Backbones",
         "Trained specifically on remote sensing datasets (DIOR, RSICD, BigEarthNet, SAR-Fish). Understands specialized aerospace terminology, multi-spectral band reflections, and synthetic aperture radar backscatter mechanics (VV/VH polarizations, double-bounce reflections, and volume scattering)."),
        ("OpenAI Whisper", 
         "Sequence-to-Sequence Audio Speech-to-Text Engine",
         "Provides hands-free voice input. Field operators in emergency, tactical, or mobile disaster response scenarios wearing protective gear can dictate natural language queries, which are transcribed with high acoustic noise tolerance directly into the query prompt."),
        ("Meta SAM 2.1 & HQ-SAM (Segment Anything Model)", 
         "Promptable Zero-Shot Foundation Segmentation Model",
         "Converts interactive user clicks, bounding boxes, or rough strokes into pixel-precise vector polygon masks. Enables analysts to isolate and measure exact geographic geometries such as water reservoir perimeters, agricultural plot boundaries, and airport taxiways."),
        ("SegFormer-B2-RS & Mask2Former-Swin", 
         "Transformer Semantic Segmentation Models",
         "Generates dense, per-pixel semantic class probability maps across canonical remote sensing land-cover categories (Urban Built-up, Water Bodies, Tree Canopy, Agricultural Land, and Road Networks)."),
        ("ChangeFormer-V2-RS & CDVQA Diff Engine", 
         "Siamese Difference Transformer & Radiometric Diff Engine",
         "Evaluates bi-temporal observation pairs (T1 Baseline and T2 Post-Event). Computes pixel-level Euclidean spectral shift vectors to isolate newly constructed buildings, demolished structures, flood inundation zones, and illegal deforestation areas, automatically generating a 4-channel transparent RGBA heatmap."),
        ("BigEarthNet-19 / CORINE Adaptation Layer", 
         "Multi-Spectral Radiometric Land-Cover Classifier",
         "Implements the official European Space Agency / CORINE 19-class land cover taxonomy. Evaluates spectral vegetation indices (NDVI), water indices (NDWI), and built-up indices (NDBI) combined with spatial texture gradients.")
    ]

    for title, role, desc in models_info:
        h2(title)
        para(f"Role: {role}", bold_prefix="Architecture Classification: ")
        para(desc)

    # ------------------ SECTION 3 ------------------
    h1("3. Exhaustive Description of Every Software Tool & Library Used")
    
    tools_table_data = [
        ("FastAPI (v0.115.0)", "Python Async Web Framework", "High-throughput REST API gateway with asynchronous endpoints, streaming response handling, and automatic OpenAPI documentation."),
        ("Uvicorn (v0.30.6)", "ASGI Production Server", "Lightning-fast ASGI server implementation powered by uvloop and httptools handling concurrent satellite query connections."),
        ("Pydantic (v2.x)", "Data Validation & Typing", "Enforces strict runtime data contract validation and serializes complex nested JSON payloads for queries and ISRO reports."),
        ("Rasterio & GDAL", "Geospatial Data Abstraction", "Reads multi-band GeoTIFFs, extracts Coordinate Reference Systems (CRS EPSG:4326/WGS84), and transforms tiepoints to geographic lat/lng."),
        ("Tifffile (v2026.8.0)", "High-Bitrate TIFF Ingestion", "Parses 1-band SAR, 3-band RGB, and N-band multispectral rasters with arbitrary bit depths (float32, uint16, int16)."),
        ("NumPy (v1.26+)", "Vectorized Numerical Computing", "Executes matrix operations, 2%-98% radiometric percentile stretching, and 3D Euclidean color distance calculations."),
        ("OpenCV (v4.10.0)", "Computer Vision Library", "Performs image spatial co-registration, bilinear resizing, color-space transformations, and edge contour vectorization."),
        ("Pillow (PIL v10.0+)", "Raster Manipulation", "Handles client image compression, transparent RGBA heatmap compositing, and thumbnail extraction."),
        ("Shapely (v2.0+)", "Computational Geometry", "Calculates polygon intersections, bounding box Intersection-over-Union (IoU), and vector boundary simplification."),
        ("MongoDB & PyMongo", "NoSQL Document Database", "Stores persistent user accounts, query histories, bi-temporal comparisons, cross-modal telemetry, and auditable traces."),
        ("MongoDB Compass", "Visual Database GUI Inspector", "Desktop application used during live operations to monitor, query, and verify document records in satquery_db in real-time."),
        ("SQLite3 (satquery.db)", "Resilient Embedded Database", "Embedded SQL database serving as an automated, zero-configuration fallback when MongoDB is offline during field deployment."),
        ("MapLibre GL (v3.6.2)", "WebGL Vector/Raster Map Canvas", "Hardware-accelerated 3D geospatial canvas rendering smooth 60 FPS orbital fly-to animations and coordinate markers."),
        ("Esri World Imagery", "Satellite Tile Service", "High-resolution, unblocked, zero-watermark global satellite imagery tile server providing base visual maps."),
        ("Esri World Street Map", "Vector Road/Label Tile Service", "High-clarity administrative and road boundary tile layer switchable on the live location canvas."),
        ("Nominatim / OSM", "Global Geocoding API", "Open reverse/forward geocoding API providing instant search autocomplete and coordinate bounding box calculation."),
        ("PyJWT & Passlib", "Stateless Security & Auth", "Issues HMAC-SHA256 signed JWT tokens and hashes user passwords using PBKDF2/SHA-256 with unique cryptographic salts.")
    ]

    tbl_tools = doc.add_table(rows=len(tools_table_data)+1, cols=3)
    tbl_tools.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_tools.autofit = False
    tbl_tools.columns[0].width = Inches(1.8)
    tbl_tools.columns[1].width = Inches(1.8)
    tbl_tools.columns[2].width = Inches(3.1)
    set_table_borders(tbl_tools, BORDER_HEX, "4")

    headers = ["Tool / Library", "Category", "Operational Role in SatQuery AI"]
    for j, h in enumerate(headers):
        c = tbl_tools.cell(0, j)
        set_cell_background(c, "1A365D")
        set_cell_margins(c, 80, 80, 100, 100)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        r.font.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    for i, (tool, cat, desc) in enumerate(tools_table_data):
        row = i + 1
        bg = "FFFFFF" if row % 2 != 0 else "F8FAFC"
        for col_idx, text_val in enumerate([tool, cat, desc]):
            c = tbl_tools.cell(row, col_idx)
            set_cell_background(c, bg)
            set_cell_margins(c, 60, 60, 100, 100)
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(text_val)
            r.font.size = Pt(9)
            if col_idx == 0:
                r.font.bold = True
                r.font.color.rgb = NAVY
            else:
                r.font.color.rgb = CHARCOAL

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # ------------------ SECTION 4 ------------------
    h1("4. Exhaustive Walkthrough of the 4 Core Functional Modules")

    h2("Module 1: Single Image VQA & Spatial Grounding")
    para(
        "This module ingests multispectral optical imagery from Sentinel-2, Cartosat-2S, or Bhuvan in standard image formats "
        "or multi-band GeoTIFFs (.tif, .tiff). High-bitrate 12-bit/16-bit satellite rasters are dynamically normalized via "
        "a 2%-98% percentile stretch to prevent image clipping. Analysts select from seven specialized domain modes (General VQA, "
        "Agriculture & Crop Health, Disaster & Flood Hazards, Urban & Built-Up Footprint, Vegetation & Forest Ecosystems, "
        "Spatial Grounding, and BigEarthNet Segmentation). The VLM produces quantitative surface coverage breakdowns "
        "(Urban %, Vegetation %, Water %, Farmland %, Bare Ground %) and spatial bounding polygons directly over the map canvas."
    )

    h2("Module 2: Bi-Temporal Change Detection & Hazard Anomaly Flagging")
    para(
        "Designed for rapid disaster damage assessment and monitoring environmental disruption, this module accepts a baseline reference "
        "scene (T1) and a follow-up observation (T2). The change engine co-registers the image pair, evaluates 3D Euclidean spectral deltas, "
        "and classifies transitions into flood inundation (Cyan/Blue), vegetation loss (Red), vegetation regrowth (Green), and new built-up "
        "infrastructure (Amber). If significant rapid changes occur in populated or hazardous regions, the system flags a CRITICAL ANOMALY, "
        "generating an interactive RGBA difference heatmap and actionable satellite revisit recommendations."
    )

    h2("Module 3: Co-Registered Optical + SAR Cross-Modal Sensor Fusion")
    para(
        "Monsoon cloud occlusion, atmospheric haze, and fire smoke frequently obscure optical sensors. This module combines co-registered "
        "Optical imagery (Cartosat-2S / Sentinel-2) with Synthetic Aperture Radar microwave data (RISAT-1A / Sentinel-1 C-band). While the optical "
        "channel captures true-color surface vegetation and roads, the active microwave radar channel penetrates dense cloud formations, "
        "measuring dielectric constants, specular water scattering, and urban double-bounce reflections to achieve 24/7 all-weather intelligence."
    )

    h2("Module 4: Live Location Explorer & Gemini Viewport Area Intelligence")
    para(
        "A standalone geospatial interface (frontend/location-search.html) featuring a 60 FPS MapLibre GL 3D vector/raster canvas with Esri "
        "satellite basemaps. Users can search any city, military base, or geographic coordinates worldwide with geocoding autocomplete, or click "
        "'Detect My Location' for one-touch GPS acquisition. Upon flying to the location, the system captures a compressed 512x512 JPEG snapshot "
        "of the active viewport, transmitting it to Gemini 2.0 Flash to synthesize a complete Strategic Terrain Dossier in under 280ms."
    )

    # ------------------ SECTION 5 ------------------
    h1("5. Official ISRO / NRSC Quantitative Technical Report Suite")
    para(
        "SatQuery AI bridges automated artificial intelligence with official governmental reporting standards. Every analysis across all four "
        "modules can be compiled with one click into an official ISRO / NRSC Quantitative Technical Report featuring:"
    )
    bullet("Serialized Document Reference Numbers", "Generates official tracking codes: REF: ISRO-NRSC-VQA-[ID], ISRO-NRSC-CHG-[ID], and ISRO-NRSC-FUS-[ID].")
    bullet("Core Telemetry HUD", "Displays prominent Vision-Language Model Confidence (%) and End-to-End Latency (ms) metrics.")
    bullet("Quantitative Surface Coverage Matrix", "Breaks down urban density classifications, vegetation canopy biomass, and water footprint percentages.")
    bullet("Official Print & PDF Engine (@media print)", "Clicking 'Print / Save PDF' triggers specialized print CSS rules that hide web UI chrome, dark glassmorphic backgrounds, and buttons, rendering a pristine, high-contrast, black-and-white A4 government technical dossier.")
    bullet("Machine-Readable JSON Export", "Clicking 'Export JSON' downloads the full structured payload, including geographic coordinates, bounding polygon vertices, confidence metrics, and auditable traces with official timestamped filenames.")

    # ------------------ SECTION 6 ------------------
    h1("6. Database Architecture & MongoDB Compass Live Observability")
    para(
        "SatQuery AI maintains permanent data persistence in MongoDB under the database name satquery_db. The database structure "
        "is split across four indexed collections:"
    )
    bullet("users", "Stores registered usernames, email addresses, salted PBKDF2/SHA-256 password hashes, user roles (analyst, commander, admin), and creation dates.")
    bullet("queries", "Stores single-image VQA queries, analytical answers, model confidence scores, land-cover percentage arrays, detected feature lists, and full auditable traces.")
    bullet("comparisons", "Stores bi-temporal image pair URLs, change narrative summaries, anomaly flags, hazard justifications, and macro transition rows.")
    bullet("crossmodals", "Stores optical and SAR raster URLs, joint fusion findings, cloud penetration indicators, and dual-sensor insights.")
    callout(
        "During live prototype demonstrations, judges and evaluators can view MongoDB Compass connected to mongodb://localhost:27017 "
        "to witness queries, bi-temporal records, and user sessions persisting in real-time as permanent JSON documents.",
        "LIVE DATABASE VERIFICATION"
    )

    # ------------------ SECTION 7 ------------------
    h1("7. Verified API Endpoints & System Performance Metrics")
    
    api_data = [
        ("POST /api/auth/register", "User registration with salted password hashing", "200 OK (~45ms)"),
        ("POST /api/auth/login", "User authentication & JWT bearer issuance", "200 OK (~35ms)"),
        ("POST /api/analyze", "Single-image VQA, spatial grounding & land-cover", "200 OK (~350ms)"),
        ("POST /api/compare", "Bi-temporal change detection & anomaly flagging", "200 OK (~380ms)"),
        ("POST /api/crossmodal", "Optical + SAR multimodal cloud-penetrating fusion", "200 OK (~360ms)"),
        ("POST /api/analyze_location", "Live viewport capture & Gemini 2.0 Flash dossier", "200 OK (~280ms)"),
        ("GET /api/report/{id}", "Serialized ISRO Single Image VQA technical report", "200 OK (~15ms)"),
        ("GET /api/report/compare/{id}", "Serialized ISRO Bi-Temporal Change Detection report", "200 OK (~15ms)"),
        ("GET /api/report/crossmodal/{id}", "Serialized ISRO Optical+SAR Fusion technical report", "200 OK (~15ms)"),
        ("GET /api/history", "User query and comparison history list", "200 OK (~20ms)"),
        ("GET /api/benchmark", "Evaluates system accuracy against ground-truth rubric", "200 OK (~520ms)")
    ]

    tbl_api = doc.add_table(rows=len(api_data)+1, cols=3)
    tbl_api.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_api.autofit = False
    tbl_api.columns[0].width = Inches(2.2)
    tbl_api.columns[1].width = Inches(3.2)
    tbl_api.columns[2].width = Inches(1.3)
    set_table_borders(tbl_api, BORDER_HEX, "4")

    api_headers = ["Endpoint Route", "Functionality Description", "Latency / Status"]
    for j, h in enumerate(api_headers):
        c = tbl_api.cell(0, j)
        set_cell_background(c, "1A365D")
        set_cell_margins(c, 80, 80, 100, 100)
        p = c.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h)
        r.font.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    for i, (route, desc, status) in enumerate(api_data):
        row = i + 1
        bg = "FFFFFF" if row % 2 != 0 else "F8FAFC"
        for col_idx, text_val in enumerate([route, desc, status]):
            c = tbl_api.cell(row, col_idx)
            set_cell_background(c, bg)
            set_cell_margins(c, 60, 60, 100, 100)
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(text_val)
            r.font.size = Pt(9)
            if col_idx == 0:
                r.font.bold = True
                r.font.color.rgb = NAVY
            elif col_idx == 2:
                r.font.bold = True
                r.font.color.rgb = TEAL
            else:
                r.font.color.rgb = CHARCOAL

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # ------------------ SECTION 8 ------------------
    h1("8. Strategic Value for SIH26167 & ISRO Deployment")
    bullet("Democratization of Complex Earth Observation Data", "Allows non-GIS experts (disaster responders, district magistrates, ground defense units) to query high-resolution satellite imagery using plain language or hands-free voice.")
    bullet("Mitigation of Weather Occlusions", "Solves the chronic tropical monsoon and cloud problem through active microwave radar backscatter fusion.")
    bullet("Production-Grade Full-Stack Engineering", "Combines high-performance FastAPI backends with MongoDB persistence, real-time Compass visibility, and graceful SQLite offline fallback.")
    bullet("Standardized Handover Reporting", "Bridges the gap between raw machine learning output and official governmental documentation via one-click ISRO/NRSC print-ready PDF and JSON exports.")

    doc.save(output_path)
    print(f"Successfully generated: {output_path}")

if __name__ == "__main__":
    out = "SatQuery_AI_Full_Prototype_Technical_Report.docx"
    if len(sys.argv) > 1:
        out = sys.argv[1]
    create_full_prototype_report(out)
