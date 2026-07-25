# PatentPilot

> **AI-assisted Freedom-to-Operate (FTO) screening for drug discovery researchers**

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React+Vite-61DAFB?style=flat-square)](https://vitejs.dev/)
[![Groq](https://img.shields.io/badge/LLM-Groq+Llama3.3-orange?style=flat-square)](https://groq.com/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

---

## Overview

PatentPilot is a full-stack, AI-powered web application that helps drug discovery researchers perform an initial **Freedom-to-Operate (FTO) / patentability screen** for a small molecule. Given a SMILES string, it:

1. **Retrieves** the most relevant patents from PubChem and PatentsView using a hybrid parallel pipeline
2. **Ranks** them using a four-component relevance score (structural + functional + semantic similarity)
3. **Explains** each patent's relevance using grounded LLM analysis (Groq / Llama-3.3-70b)
4. **Generates** a structured, decision-ready patentability report with a risk recommendation

> ⚠️ **Legal Disclaimer**: PatentPilot is a preliminary screening tool, not a formal FTO opinion. Consult a qualified patent attorney before making development or commercialization decisions.

---

## Architecture

```
User Browser (React + Vite SPA)
        │
        │  REST/JSON over HTTP
        ▼
FastAPI Backend (/api/v1/)
        │
        ├── SMILES Validation (RDKit / fallback)
        ├── Molecule Fingerprinting (Morgan/ECFP4)
        │
        ├── Retrieval Layer ──────────────────────────────────────────────┐
        │   ├── PubChem PUG-REST (structural similarity search)           │
        │   └── PatentsView API (target/disease text search)              │ parallel
        │   [both run concurrently via asyncio.gather()]                  │
        │                                                                  │
        ├── Ranking Agent ←────────────────────────────────────────────┘
        │   ├── Merge + Deduplicate
        │   └── Four-component hybrid scoring formula
        │
        ├── AI Layer
        │   ├── Explanation Agent (per-patent grounded LLM analysis)
        │   ├── Report Agent (full structured patentability report)
        │   └── Recommendation Agent (risk label + rationale)
        │
        └── Data Layer (SQLite / PostgreSQL)
            ├── analyses
            ├── patents
            ├── reports
            └── review_status
```

### Full Pipeline (per submission)

```
User Input (SMILES + optional target/indication)
    ↓
SMILES Validation (RDKit → canonical SMILES + 2D SVG)
    ↓
Molecule Fingerprinting (Morgan/ECFP4 via RDKit)
    ↓
Hybrid Patent Retrieval ──── PubChem similarity search
    (parallel)            └── PatentsView text search (target + disease)
    ↓
Patent Ranking Engine (merge → dedupe → four-component score → top-10)
    ↓
Evidence Extraction (per-patent score breakdown + flags)
    ↓
LLM Grounded Explanation (Groq: why_retrieved, similar_aspects, overlap, confidence)
    ↓
Risk Scoring + Recommendation (threshold-based label + rationale)
    ↓
Patentability Report Assembly (six required sections + enrichments)
    ↓
History & Analytics (persisted to DB, queryable from dashboard)
```

---

## Modular Agent Design

| Agent | Module | Responsibility | Input | Output |
|---|---|---|---|---|
| **Retrieval Agent** | `backend/retrieval/agent.py` | Parallel PubChem + PatentsView fetch | SMILES, target, indication | Raw patent list |
| **Ranking Agent** | `backend/ranking/agent.py` | Merge, dedupe, four-component score | Raw patent list + fingerprint | Ranked list with sub-scores |
| **Explanation Agent** | `backend/ai/explanation_agent.py` | Grounded per-patent "why" | Patent fields + scores | Structured explanation JSON |
| **Report Agent** | `backend/ai/report_agent.py` | Full report assembly | All patents + explanations | Structured report |
| **Recommendation Agent** | `backend/ai/report_agent.py` | Risk thresholds → label | Report data + scores | Risk label + rationale |

Each agent is an independent module with a clear `input → output` contract. Swapping the LLM provider, the retrieval source, or the scoring formula only touches the relevant module.

---

## Sequence Diagram

```
User          Frontend        Backend API       Retrieval       AI Layer         DB
 │                │               │                │               │              │
 │──submit SMILES─►               │                │               │              │
 │                │──POST /submit─►                │               │              │
 │                │               │──validate SMILES               │              │
 │                │               │──create Analysis record────────────────────── ►
 │                │               │──spawn background task         │              │
 │                │◄──analysisId──│                │               │              │
 │                │               │                │               │              │
 │                │  (background) │──gather()──────►PubChem search │              │
 │                │               │                │PatentsView────►               │
 │                │               │                │◄─────results──│              │
 │                │               │──rank_patents()─│               │              │
 │                │               │──explain(batch)────────────────►Groq API      │
 │                │               │◄───────────────────────────────explanations   │
 │                │               │──persist patents+explanations──────────────── ►
 │                │               │──update status=complete────────────────────── ►
 │                │               │                │               │              │
 │──poll status──►│──GET /patents─►                │               │              │
 │                │◄──patent list─│                │               │              │
 │                │               │                │               │              │
 │──generate────► │──POST /report─►                │               │              │
 │                │               │──report_agent()────────────────►Groq API      │
 │                │               │◄───────────────────────────────report JSON    │
 │                │               │──persist report────────────────────────────── ►
 │                │◄──report──────│                │               │              │
```

---

## Database ER Diagram

```
┌─────────────────┐       ┌──────────────────┐
│    analyses     │       │     patents       │
│─────────────────│       │──────────────────│
│ id (PK)         │──┐    │ id (PK)          │
│ smiles          │  └───►│ analysis_id (FK) │
│ molecule_name   │       │ patent_number    │
│ target          │       │ title            │
│ indication      │       │ abstract         │
│ status          │       │ assignee         │
│ structure_svg   │       │ publication_date │
│ created_at      │       │ source           │
│ updated_at      │       │ chemical_sim     │──────┐
└─────────────────┘       │ target_match     │      │
         │                │ disease_match    │      │
         │                │ semantic_rel     │      │
         │                │ overall_score    │      │  ┌──────────────────┐
         │                │ confidence_score │      │  │  review_status   │
         │                │ evidence_flags   │      │  │──────────────────│
         │                │ explanation      │      └─►│ patent_id (FK)   │
         │                │ rank             │         │ analysis_id (FK) │
         │                └──────────────────┘         │ status           │
         │                                             │ notes            │
         │   ┌──────────────────────────────────┐     └──────────────────┘
         └──►│            reports               │
             │──────────────────────────────────│
             │ id (PK)                          │
             │ analysis_id (FK, unique)         │
             │ executive_summary                │
             │ key_similar_patents (JSON)       │
             │ novelty_concerns (JSON)          │
             │ potential_novel_regions          │
             │ recommended_next_actions (JSON)  │
             │ manual_review_checklist (JSON)   │
             │ key_evidence (JSON)              │
             │ recommendation                   │
             │ risk_score                       │
             │ confidence_score                 │
             │ recommendation_rationale         │
             │ scoring_methodology_explanation  │
             └──────────────────────────────────┘
```

---

## Retrieval Strategy

PatentPilot uses a **hybrid parallel retrieval pipeline** combining structural and use-case searches:

1. **Structural search (PubChem)**: Compute Morgan/ECFP4 fingerprint → similarity search for compounds with Tanimoto similarity ≥ 0.6 → fetch associated patent IDs
2. **Target/disease text search (PatentsView)**: Query USPTO full-text API for patents mentioning the target and indication keywords
3. **Both run concurrently** via `asyncio.gather()` — not sequentially — reducing latency significantly
4. **Merge + deduplicate** by patent number (preserving richer data from duplicates)
5. **Four-component hybrid re-ranking** (see Scoring Methodology below)
6. Return **top 10** by overall overlap score

**Why parallel retrieval?** Structural-only search misses use-case-similar patents (same target, different scaffold). Text-only search misses structurally similar compounds. Combining both catches both failure modes, with parallel execution preventing the latency from doubling.

**Limitations**: SureChEMBL full-text integration is not included (API availability issues). Full claim-level NLP is not performed — the scoring uses title + abstract text. Both are logged as known trade-offs.

---

## AI Workflow

**LLM**: Groq API with `llama-3.3-70b-versatile` (configurable via `GROQ_MODEL` env var)

### Explanation Agent (per patent)
- **Input**: Patent title, abstract, claims + four computed sub-scores
- **Prompt strategy**: All retrieved fields are injected directly into the prompt. The LLM is explicitly instructed to reference specific data (never invent). Temperature = 0.2 for factual, consistent output.
- **Output**: Structured JSON with `why_retrieved`, `similar_aspects`, `possible_overlap`, `confidence_assessment`

### Report Agent (full report)
- **Input**: All ranked patents with explanations, risk scores, molecule context
- **Prompt strategy**: Pre-computed risk label and scores are included so LLM focuses on *explanation quality* not score computation (prevents hallucination of different numbers)
- **Output**: Six structured report sections + enrichment fields

### Grounding principle
Every LLM call includes the actual retrieved data as context. The LLM is instructed to cite specific patent numbers, scores, and text fields — making outputs traceable to real evidence, not generic templated summaries.

**Example prompt excerpt** (Explanation Agent):
```
Patent Number: US20230123456
Title: Selective COX-2 Inhibitor for Inflammatory Disease Treatment
Computed Scores:
  Chemical Structural Similarity (Tanimoto): 72%
  Target Keyword Match: 85%
  Overall Overlap Score: 76%

Task: Explain specifically why this patent was retrieved, 
citing the above data. Do not generalize.
```

---

## Scoring Methodology

```
overlap_score =
    0.35 × chemical_similarity   (Tanimoto over Morgan ECFP4 fingerprints, 0–1)
  + 0.25 × target_match          (fuzzy Jaccard token overlap on submitted target, 0–1)
  + 0.20 × disease_match         (fuzzy Jaccard token overlap on submitted indication, 0–1)
  + 0.20 × semantic_relevance    (heuristic text relevance, 0–1)

confidence_score = 1.0
  − 0.25  (if no abstract available)
  − 0.10  (if no claims available)
  − 0.15  (if no target provided by researcher)
  − 0.10  (if no indication provided by researcher)
  − 0.05  (if no assignee or publication date)
  → clipped to [0.1, 1.0]

Risk thresholds:
  overlap_score ≥ 0.75 on ≥1 patent   → High Patent Risk
  overlap_score 0.40–0.75 on ≥1 patent → Requires Expert Review
  all overlap scores < 0.40            → Low Patent Risk
```

**Why these weights?** Chemical similarity (35%) is the primary signal for a structure-based FTO screen. Target match (25%) catches functionally equivalent but structurally distinct patents — a common failure mode of pure structure search. Disease/indication (20%) catches use-case patents. Semantic relevance (20%) adds coverage for patents that describe similar mechanisms using different terminology.

---

## API Documentation

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health check — DB status + version |
| `POST` | `/api/v1/molecule/validate` | Validate SMILES, return properties + SVG |
| `POST` | `/api/v1/molecule/submit` | Submit molecule, start FTO pipeline (async) |
| `GET` | `/api/v1/patents/{analysis_id}` | List ranked patents for an analysis |
| `PUT` | `/api/v1/patents/{patent_id}/review` | Update review status (reviewed/flagged/dismissed) |
| `GET` | `/api/v1/patents/{patent_id}/detail` | Get full patent detail + explanation |
| `POST` | `/api/v1/report/generate` | Generate patentability report for analysis |
| `GET` | `/api/v1/report/{analysis_id}` | Retrieve existing report |
| `GET` | `/api/v1/history` | List all analyses (paginated, searchable) |
| `GET` | `/api/v1/history/{analysis_id}` | Get full analysis detail |
| `GET` | `/api/v1/dashboard` | Aggregate analytics stats |

Interactive docs: `http://localhost:8000/api/docs`

---

## Technologies Used

| Layer | Technology | Justification |
|---|---|---|
| Frontend | React 18 + Vite + TypeScript | Fast HMR, type safety, ecosystem |
| Routing | React Router v6 | Client-side SPA routing |
| Charts | Recharts | Lightweight, composable React charts |
| Backend | FastAPI (Python 3.11) | Async support, automatic OpenAPI docs, Pydantic validation |
| Database | SQLAlchemy + SQLite / PostgreSQL | Relational storage; SQLite for local dev, Postgres for production |
| LLM | Groq API (Llama-3.3-70b) | Ultra-low latency inference; OpenAI-compatible API; easily swappable |
| Patent Sources | PubChem PUG-REST + PatentsView API | Both free, well-documented, no API key required |
| Cheminformatics | RDKit (optional, graceful fallback) | Industry-standard Morgan fingerprints + 2D structure rendering |
| HTTP Client | httpx | Async-native, essential for parallel API calls |
| Containerization | Docker + Docker Compose | One-command local setup |

---

## Assumptions Made

- Public patent search (PubChem + PatentsView) is sufficient for an initial FTO screen; full-text claim analysis requires a licensed patent database (e.g., Derwent Innovation)
- Groq's `llama-3.3-70b-versatile` is capable enough for grounded patent analysis; a chemistry-fine-tuned model (e.g., ChemBERTa) would improve semantic accuracy
- SMILES validation requires RDKit; the app degrades gracefully (basic bracket validation) if RDKit is not installed
- SQLite is adequate for single-user/local use; PostgreSQL is used in Docker for multi-user production
- PatentsView covers US patents only — international coverage would require additional sources (EPO, WIPO)

---

## Trade-offs

| Trade-off | Choice Made | Reason |
|---|---|---|
| Speed vs. coverage | Parallel retrieval, top-10 results | Acceptable for initial screen; sequential would add 30+ sec |
| Accuracy vs. availability | PubChem + PatentsView (free) vs. licensed databases | Free APIs enable zero-cost deployment; flag for escalation |
| LLM accuracy vs. cost | Groq (fast, cheap) vs. GPT-4 | Groq's Llama-3.3-70b is sufficient for grounded extraction |
| DB complexity | SQLite (local) / Postgres (prod) | SQLite removes Docker dependency for getting started |
| Semantic scoring | Heuristic keyword overlap vs. embeddings | Embeddings would need a vector DB; heuristic is fast and deterministic |
| Claim parsing | Title + abstract only vs. full claim NLP | Full claims not available via basic PatentsView query; flagged |

---

## Future Improvements

1. **Full-text claim NLP**: Use PatentsView claims API + NLP to extract claim scope for more accurate overlap detection
2. **Chemistry-specific embeddings**: Use ChemBERTa or MolBERT for true semantic similarity between molecule descriptions
3. **Multi-user auth**: Add JWT-based authentication for team use
4. **International patent coverage**: Add EPO (via Open Patent Services API) and WIPO sources
5. **Batch molecule screening**: Submit a library of candidates and rank by overall risk profile
6. **SureChEMBL integration**: Add structure-exact and substructure search via SureChEMBL when their API is stable
7. **Scaffold analysis**: Identify and visualize the Murcko scaffold of the submitted molecule and flag patents covering that scaffold
8. **Real-time streaming**: Stream LLM explanations token-by-token to the frontend for faster perceived response

---

## Setup & Local Run Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- (Optional) Conda for RDKit: `conda install -c conda-forge rdkit`

### 1. Clone & Navigate
```bash
git clone <repo-url>
cd patentpilot
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and set your GROQ_API_KEY
```

### 3. Run Backend
```bash
pip install -r backend/requirements.txt
# Optionally: pip install rdkit (or conda install -c conda-forge rdkit)
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Backend runs at `http://localhost:8000` · API docs at `http://localhost:8000/api/docs`

### 4. Run Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173`

### 5. Docker (Full Stack)
```bash
# In project root
docker-compose up --build
```
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- PostgreSQL: port 5432

### 6. Test with Example Molecule
Submit Aspirin: `CC(=O)Oc1ccccc1C(=O)O` with target `COX-2` and indication `pain inflammation`

---

## Screenshots

*(Generated after running the application)*

---

## Demo

Submit any SMILES string on the home page to see the full pipeline in action. The analysis takes 30–90 seconds (parallel retrieval + LLM explanations for up to 10 patents).

---

*Built for the Centella AI Therapeutics — AI Product Engineer Internship Assessment, July 2026.*
