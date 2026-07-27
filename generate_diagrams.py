import os
from PIL import Image, ImageDraw, ImageFont

os.makedirs("images", exist_ok=True)

# Helper to load font
def get_font(size, bold=False):
    try:
        # Standard Windows fonts
        font_name = "arialbd.ttf" if bold else "arial.ttf"
        return ImageFont.truetype(font_name, size)
    except Exception:
        return ImageFont.load_default()

# ---------------------------------------------------------
# 1. SYSTEM ARCHITECTURE DIAGRAM (1200 x 700)
# ---------------------------------------------------------
w, h = 1200, 720
img1 = Image.new("RGB", (w, h), color="#0f172a")
draw1 = ImageDraw.Draw(img1)

# Fonts
font_title = get_font(24, bold=True)
font_sub = get_font(14, bold=True)
font_text = get_font(13, bold=False)
font_bold = get_font(13, bold=True)

# Title Banner
draw1.rectangle([0, 0, w, 65], fill="#1e1b4b")
draw1.text((w//2, 32), "PATENTPILOT — SYSTEM ARCHITECTURE", fill="#ffffff", font=font_title, anchor="mm")

# Layer 1: Frontend
draw1.rounded_rectangle([50, 95, 1150, 175], radius=10, fill="#1e293b", outline="#6366f1", width=2)
draw1.text((70, 115), "PRESENTATION LAYER (FRONTEND)", fill="#818cf8", font=font_sub)
draw1.text((70, 140), "React 18 SPA + TypeScript + Vite", fill="#f8fafc", font=font_bold)
draw1.text((450, 140), "Routes: / (Submit), /workspace/:id, /workspace/:id/patent/:pid, /report/:id, /history, /about", fill="#94a3b8", font=font_text)

# Arrow 1
draw1.line([(w//2, 175), (w//2, 210)], fill="#38bdf8", width=3)
draw1.polygon([(w//2 - 6, 204), (w//2 + 6, 204), (w//2, 212)], fill="#38bdf8")

# Layer 2: API Gateway
draw1.rounded_rectangle([50, 212, 1150, 285], radius=10, fill="#1e293b", outline="#06b6d4", width=2)
draw1.text((70, 230), "API GATEWAY & ROUTING CORE", fill="#38bdf8", font=font_sub)
draw1.text((70, 255), "FastAPI Backend (Python 3.11)", fill="#f8fafc", font=font_bold)
draw1.text((450, 255), "Endpoints: /api/v1/molecule, /api/v1/patents, /api/v1/report, /api/v1/history, /api/v1/dashboard", fill="#94a3b8", font=font_text)

# Arrow split
x1, x2, x3 = 230, w//2, 970
draw1.line([(x1, 285), (x1, 325)], fill="#818cf8", width=2)
draw1.line([(x2, 285), (x2, 325)], fill="#06b6d4", width=2)
draw1.line([(x3, 285), (x3, 325)], fill="#34d399", width=2)

# Layer 3: Subsystems (3 cards)
# Card 1
draw1.rounded_rectangle([50, 325, 410, 480], radius=8, fill="#1e293b", outline="#818cf8", width=2)
draw1.text((70, 345), "MOLECULE SUBSYSTEM", fill="#818cf8", font=font_sub)
draw1.text((70, 375), "• SMILES Validation Engine", fill="#f8fafc", font=font_text)
draw1.text((70, 400), "• PubChem Name-to-SMILES", fill="#f8fafc", font=font_text)
draw1.text((70, 425), "• RDKit 2D Structure Render", fill="#f8fafc", font=font_text)
draw1.text((70, 450), "• Fingerprint Generation", fill="#f8fafc", font=font_text)

# Card 2
draw1.rounded_rectangle([440, 325, 760, 480], radius=8, fill="#1e293b", outline="#06b6d4", width=2)
draw1.text((460, 345), "DUAL RETRIEVAL ENGINE", fill="#38bdf8", font=font_sub)
draw1.text((460, 375), "• PubChem 2D Structure API", fill="#f8fafc", font=font_text)
draw1.text((460, 400), "• Europe PMC Literature API", fill="#f8fafc", font=font_text)
draw1.text((460, 425), "• Parallel asyncio.gather()", fill="#f8fafc", font=font_text)
draw1.text((460, 450), "• Deduplication & Verify", fill="#f8fafc", font=font_text)

# Card 3
draw1.rounded_rectangle([790, 325, 1150, 480], radius=8, fill="#1e293b", outline="#34d399", width=2)
draw1.text((810, 345), "MULTI-AGENT AI ENGINE", fill="#34d399", font=font_sub)
draw1.text((810, 375), "• Explanation Agent (LLM)", fill="#f8fafc", font=font_text)
draw1.text((810, 400), "• Scorer & Decision Agent", fill="#f8fafc", font=font_text)
draw1.text((810, 425), "• Report Agent (FTO Report)", fill="#f8fafc", font=font_text)
draw1.text((810, 450), "• Groq Llama 3.1 Inference", fill="#f8fafc", font=font_text)

# Layer 4: Storage
draw1.line([(w//2, 480), (w//2, 520)], fill="#fbbf24", width=2)
draw1.polygon([(w//2 - 6, 514), (w//2 + 6, 514), (w//2, 522)], fill="#fbbf24")

draw1.rounded_rectangle([300, 522, 900, 595], radius=10, fill="#1e293b", outline="#fbbf24", width=2)
draw1.text((w//2, 545), "DATA PERSISTENCE LAYER", fill="#fbbf24", font=font_sub, anchor="mm")
draw1.text((w//2, 570), "SQLite / PostgreSQL DB — Analyses, Patents, Reports, Review Status", fill="#f8fafc", font=font_text, anchor="mm")

img1.save("images/system_architecture.png")
print("Saved images/system_architecture.png")

# ---------------------------------------------------------
# 2. DUAL PIPELINE & AGENTIC AI WORKFLOW DIAGRAM (1200 x 700)
# ---------------------------------------------------------
img2 = Image.new("RGB", (w, h), color="#0f172a")
draw2 = ImageDraw.Draw(img2)

# Title Banner
draw2.rectangle([0, 0, w, 65], fill="#065f46")
draw2.text((w//2, 32), "DUAL RETRIEVAL & MULTI-AGENT AI WORKFLOW", fill="#ffffff", font=font_title, anchor="mm")

# Step 1: Input
draw2.rounded_rectangle([350, 90, 850, 145], radius=25, fill="#1e1b4b", outline="#818cf8", width=2)
draw2.text((w//2, 117), "1. User Submission (Molecule Name/SMILES + Target + Indication)", fill="#ffffff", font=font_bold, anchor="mm")

# Arrow 1
draw2.line([(w//2, 145), (w//2, 175)], fill="#818cf8", width=2)

# Step 2: Vocabulary
draw2.rounded_rectangle([250, 175, 950, 225], radius=8, fill="#1e293b", outline="#06b6d4", width=2)
draw2.text((w//2, 200), "2. SMILES Pre-Processing & PubChem Search Vocabulary Expansion", fill="#38bdf8", font=font_bold, anchor="mm")

# Split lines
draw2.line([(400, 225), (280, 265)], fill="#38bdf8", width=3)
draw2.line([(800, 225), (920, 265)], fill="#a855f7", width=3)

# Pipeline A
draw2.rounded_rectangle([50, 265, 510, 365], radius=10, fill="#1e293b", outline="#38bdf8", width=2)
draw2.text((70, 285), "PRIMARY STRUCTURAL PIPELINE", fill="#38bdf8", font=font_sub)
draw2.text((70, 310), "• PubChem 2D Fast Similarity API", fill="#f8fafc", font=font_bold)
draw2.text((70, 335), "• Tanimoto Fingerprints (>=75% Overlap) -> PatentID xrefs", fill="#94a3b8", font=font_text)

# Pipeline B
draw2.rounded_rectangle([690, 265, 1150, 365], radius=10, fill="#1e293b", outline="#a855f7", width=2)
draw2.text((710, 285), "SECONDARY SEMANTIC PIPELINE", fill="#a855f7", font=font_sub)
draw2.text((710, 310), "• Europe PMC Core Literature API", fill="#f8fafc", font=font_bold)
draw2.text((710, 335), "• Full text & synonym search -> Core abstracts & claims", fill="#94a3b8", font=font_text)

# Join lines
draw2.line([(280, 365), (450, 405)], fill="#38bdf8", width=3)
draw2.line([(920, 365), (750, 405)], fill="#a855f7", width=3)

# Step 3: Deduplicate
draw2.rounded_rectangle([250, 405, 950, 455], radius=8, fill="#1e293b", outline="#34d399", width=2)
draw2.text((w//2, 430), "3. Merge, Deduplicate & Strict Patent Verification", fill="#34d399", font=font_bold, anchor="mm")

# Arrow
draw2.line([(w//2, 455), (w//2, 485)], fill="#34d399", width=2)

# Step 4: Scoring
draw2.rounded_rectangle([150, 485, 1050, 545], radius=8, fill="#1e293b", outline="#fbbf24", width=2)
draw2.text((w//2, 505), "4. 5-Pillar Deterministic Hybrid Scoring Engine", fill="#fbbf24", font=font_sub, anchor="mm")
draw2.text((w//2, 528), "Chem Sim (40%) + Target (25%) + Semantic (20%) + Disease (10%) + Recency (5%)", fill="#cbd5e1", font=font_text, anchor="mm")

# Arrow
draw2.line([(w//2, 545), (w//2, 575)], fill="#fbbf24", width=2)

# Step 5: AI & Report
draw2.rounded_rectangle([150, 575, 1050, 635], radius=25, fill="#064e3b", outline="#34d399", width=2)
draw2.text((w//2, 605), "5. Grounded Groq LLM Explanations & Structured FTO Report Generation", fill="#ffffff", font=font_bold, anchor="mm")

img2.save("images/dual_pipeline_workflow.png")
print("Saved images/dual_pipeline_workflow.png")
