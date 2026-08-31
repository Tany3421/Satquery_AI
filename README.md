# SatQuery AI — Working Prototype

SIH26167: Interactive Vision-Language Assistant for Multimodal Remote Sensing
Image Analysis through Text Queries.

This is a **real, end-to-end prototype** — not a mock. Every analysis
actually calls Gemini's vision API, and the differentiation features from
your competitor analysis (explainability, confidence/uncertainty, cloud
quality, domain modes, change detection) are already wired in, not just
planned.

## Folder structure

```
satquery-ai/
├── backend/            API layer only — routing, file handling, validation
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example    → copy to .env and add your Gemini API key
├── aiml/                All prompt engineering + model calls live here
│   ├── prompts.py       Domain-mode system prompts (the differentiation layer)
│   └── engine.py        Gemini vision API wrapper (analyze + compare)
├── database/            SQLite persistence
│   └── db.py            Schema + queries — swap for Postgres/Mongo later
└── frontend/
    └── index.html        Single-file dashboard, no build step needed
```

This split exists so your team can work in parallel without merge
conflicts: AI/ML person owns `aiml/`, backend person owns `backend/` +
`database/`, frontend person owns `frontend/`.

## Run it

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```


Get a key at https://aistudio.google.com/app/apikey.


Then open `frontend/index.html` in a browser. It talks to
`http://localhost:8000` — change `API_BASE` at the top of the `<script>`
block if you deploy the backend elsewhere.

A SQLite file (`database/satquery.db`) is created automatically on first
run — no setup needed.

## What's already built (vs. what's next)

| Feature | Status |
|---|---|
| Natural-language querying + vision-language understanding | ✅ Built |
| Land cover breakdown, detected features | ✅ Built |
| **Evidence + confidence/uncertainty layer** | ✅ Built |
| **Cloud cover / image quality awareness** | ✅ Built |
| **Domain modes** (General / Agriculture / Disaster / Urban / Environment) | ✅ Built |
| **Multi-temporal change detection + anomaly flagging** | ✅ Built (`/api/compare`) |
| **ISRO-style analysis report** | ✅ Built (`/api/report/:id`, rendered as a modal in the dashboard) |
| SQLite persistence | ✅ Built |
| India-specific example queries / framing | 🟡 Prompts mention Indian context — sharpen with real Indian sample imagery |
| GeoTIFF / real coordinates | ⬜ Not built — needs rasterio/GDAL |
| Cross-modal (optical + SAR) reasoning | ⬜ Not built — needs a second data source |
| Auth / user accounts | ⬜ Not built |
| Automatic anomaly *scanning* across a sequence of images | ⬜ Stub noted in `backend/main.py` |

## 7-day build plan

**Day 1 — Restructure + persistence.** Already done in this drop — get it
running, make sure everyone can pull it and start the server.

**Day 2 — Explainability + confidence.** Already done — but test it against
real imagery and tighten `aiml/prompts.py` if evidence/confidence feel
generic. This is your highest-ROI prompt to iterate on.

**Day 3 — Cloud/image-quality awareness.** Already done — verify the
cloud-cover estimate is plausible against real cloudy/clear test images.

**Day 4 — Domain-specific query modes.** Already wired (mode selector in
the frontend, mode-specific prompts in `aiml/prompts.py`). Spend the day
tuning each mode's prompt with domain-specific example questions.

**Day 5 — Multi-temporal change detection.** `/api/compare` is built —
test it with real before/after imagery of the same location and tune
`COMPARISON_SYSTEM_PROMPT` in `aiml/prompts.py`.

**Day 6 — India/ISRO framing + anomaly polish + report.** The report
endpoint and anomaly flagging are built. Spend the day on: (1) example
queries and copy that reference Indian geography, (2) testing the anomaly
threshold isn't too trigger-happy, (3) polishing the report modal.

**Day 7 — Testing, polish, demo prep.** No new features. Run the full flow
end-to-end with real sample imagery, fix rough edges, rehearse the pitch
around explainability + confidence + domain modes + India focus — not "AI
understands satellite images," which every competitor platform already has.

## Extension notes

- `# EXTEND:` comments throughout the code mark the intended seams — a
  segmentation model, a stretch cross-modal (optical+SAR) endpoint, GeoTIFF
  support, auth.
- The `evidence`, `confidence`, `uncertainty_reason`, `cloud_cover_percent`,
  and `image_quality` fields are the direct implementation of your
  differentiation doc's "Explainable AI" and "Confidence + uncertainty"
  points (MEDIUM-HIGH differentiation) — lean on these in your pitch.
- `/api/compare`'s `anomaly_flagged` field is the seed of the "automatic
  anomaly investigation" wow-feature; the noted extension
  (`/api/anomaly-scan`) would run it across a sequence of images instead of
  just two.
- No auth, single SQLite file — fine for a hackathon prototype and demo,
  not for production.
