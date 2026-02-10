# Treno Web: Engineering Prototype 🚆

> **Reference Implementation:** High-performance Indian Railways search engine built with Next.js (App Router), FastAPI, and SQLite.

> [!IMPORTANT]
> **Project Date:** 2026-02-10
> This branch (`starter`) is the **starting point** for the AI-Driven Development tutorial.
>
> If you want to see the **final, completed project**, please switch to the `main` branch:
> ```bash
> git checkout main
> ```

## 1. Project Overview

- **Problem:** Existing rail portals are heavy and slow on 4G networks.
- **Solution:** A hybrid architecture delivering <1.5s latency using embedded static data and optimized minimal payloads.
- **Status:** Engineering Prototype / Proof of Concept.

### Architecture
- **Frontend:** Next.js 16 + Tailwind CSS 3.4 (Vercel)
- **Backend:** FastAPI + Python 3.11 (Render)
- **Database:** SQLite (Static Schedules) + Redis (Live PNR Cache)
- **Data Strategy:** Single-source JSON ingestion (~500k records) to embedded SQLite.

---

## 2. Replication Guide (Build from Scratch)

This project was built using **AI-Driven Development** (Antigravity/Cursor). You can replicate this build process entirely by following these steps.

### 🛑 Prerequisites (Install First)
Ensure these tools are installed and running before you begin:
- **Docker Desktop** (Required for containerization)
- **Python 3.11+** (Backend runtime)
- **Node.js 20+** (Frontend runtime)
- **A Code Editor** (VS Code, Cursor, or Windsurf)

### Step 1: The Clean Slate
If rebuilding, keep ONLY these files and delete everything else:
1. `docs/system_design.md` (Architecture Source of Truth)
2. `docs/ui_wireframes.md` (UI Specs)
3. `backend/data/schedules.json` (Raw Data Source)

### Step 2: Execution Prompts
Paste these prompts into your AI Agent sequentially to scaffold and build the app.

<details>
<summary><strong>Phase 1: Backend & Data Layer</strong></summary>

**Prompt 1.1: Project Initialization**
> Copy inputs: `docs/system_design.md`
> Prompt:
> "Role: Senior DevOps Architect. Context: Initializing Treno Web. Goal: Scaffold project structure.
> **Constraint:** Initialize `frontend/package.json` with these EXACT dependencies to avoid conflicts:
> - next: ^16.1.6
> - react: ^19.2.4
> - tailwindcss: ^3.4.17 (Do NOT install v4)
> - concurrently: ^9.2.1 (For running tailwind CLI)
>
> Create empty placeholders for backend main.py and frontend package.json."

**Prompt 1.2: ETL & Database**
> Copy inputs: `docs/system_design.md`, `backend/data/schedules.json`
> Prompt:
> "Role: Data Engineer. Goal: Initialize the SQLite database and ingest data.
> 1. Create `init_db.py`: Initialize `backend/data/trains.db` with `stations` (incl FTS) and `train_schedule` tables.
> 2. Create `ingest_schedule_json.py`: Parse `schedules.json` to:
>    - Extract unique stations (code, name) and populate `stations` table.
>    - Populate `train_schedule` table with schedule data.
> Constraint: Use `json.load` and `executemany` for speed. Verify with SQL count checks."
</details>

<details>
<summary><strong>Phase 2: Core API</strong></summary>

**Prompt 2.1: FastAPI Setup**
> Prompt:
> "Role: Backend Architect. Goal: Create `backend/app/main.py` with FastAPI. Endpoint: `GET /api/search?from=X&to=Y&date=Z`. Logic: Query SQLite `train_schedule` table. constraint: Return JSON strictly matching System Design Section 14.1."
</details>

<details>
<summary><strong>Phase 3: Frontend UI</strong></summary>

**Prompt 3.1: Components**
> Prompt:
> "Role: Frontend Lead. Goal: Create `TrainCard` and `SearchWidget` components using Tailwind 3.4 utility classes. Style: Clean, minimal, Apple-esque (Slate-50)."

**Prompt 3.2: Page Assembly & Navigation**
> Prompt:
> "Role: Frontend Engineer. Goal: Build `app/page.tsx` (Home) and `app/search/page.tsx` (Results). Implement shared Header with active route detection (Show 'Search' link on Home, 'Home' link on Search). Add Privacy page at `/privacy`."
</details>

<details>
<summary><strong>Phase 4: Deployment Config</strong></summary>

**Prompt 4.1: Infrastructure as Code**
> Prompt:
> "Role: DevOps. Goal: Create `backend/Dockerfile` (optimize for Python/SQLite) and `render.yaml`. Create `vercel.json` for frontend. Generate `.env.example` with `NEXT_PUBLIC_API_URL`."
</details>

---

## 3. Local Development

### Backend (FastAPI)
```bash
cd backend
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run ETL (First time only)
python3 scripts/init_db.py
python3 scripts/ingest_schedule_json.py

# Start Server
uvicorn app.main:app --reload --port 8000
```

### Frontend (Next.js)
```bash
cd frontend
npm install

# Run dev server (using concurrent tailwind + next)
npm run dev
# App running at http://localhost:3000
```

---

## 4. Deployment

### Backend (Render.com)
1. Create a new **Web Service** on Render.
2. Connect your repository.
3. Render will auto-detect `render.yaml`.
4. **Environment:** Python 3.11 / Docker.
5. **Copy the URL:** e.g., `https://treno-backend.onrender.com`

### Frontend (Vercel)
1. Import repository to Vercel.
2. Root Directory: `frontend`.
3. **Environment Variables:**
   - `NEXT_PUBLIC_API_URL`: Paste your Render Backend URL.
4. Deploy.

---

## 5. Privacy & Data

**Disclaimer:** This is a technical demonstration / engineering prototype.
- **No PNR Data is stored** permanently in this version.
- **Not affiliated** with Indian Railways or IRCTC.
- **Data Source:** Publicly available datasets (Kaggle).

---

## License
MIT License. Free for educational use.
