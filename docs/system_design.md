Treno Web System Design

## 1. Problem Statement
The current Indian Railway web ecosystem is fragmented. Official portals (IRCTC/NTES) suffer from session timeouts, poor mobile responsiveness, and complex navigation. Third-party aggregators are ad-heavy and slow. Users need a **lightweight, lightning-fast (<1.5s load)** web portal that works seamlessly on 4G networks to check train schedules and PNR status without login friction.

## 1.1 Core Use Cases
We identify three primary workloads that drive the architectural decisions:

| ID       | Use Case          | Actor     | Access Pattern            | Load Profile                 | Criticality                      |
| :------- | :---------------- | :-------- | :------------------------ | :--------------------------- | :------------------------------- |
| **UC-1** | **Search Trains** | Guest     | **Read-Only**             | **High** (90% of requests)   | **Performance** (< 1.5s)         |
| **UC-2** | **Check PNR**     | Guest     | **Read-Write** (Cache)    | **Medium** (10% of requests) | **Freshness** (< 15 min old)     |
| **UC-3** | **Save Trip**     | Auth User | **Write** (Transactional) | **Low** (< 1% of requests)   | **Consistency** (Zero Data Loss) |

## 2. System Requirements & Constraints

### 2.1 Capacity Requirements
*   **Target Audience:** Commuters (Release 1.0) -> Frequent Travelers (Release 2.0).
*   **Initial Load (R1.0):** 1,000 DAU, avg 3 searches/user = 3,000 req/day (~0.03 RPS).
*   **Peak Load (R3.0):** 100,000 DAU (Viral/Festival), 10 searches/user = 1M req/day (~12 RPS avg, 50 RPS peak).

### 2.2 Performance Constraints
*   **Page Load:** < 1.5 seconds on 4G networks.
*   **Backend Processing:** Target **< 50ms** for SQLite query + JSON serialization.
*   **Jitter Tolerance:** Must handle high network jitter common in Indian mobile networks.

#### Performance Budget Breakdown (4G India, Singapore Region)

| Component | Target | Notes |
|-----------|--------|-------|
| **DNS Lookup** | 80ms | Cached after first visit |
| **TLS Handshake** | 120ms | HTTP/2 reduces overhead |
| **Network RTT (Singapore)** | 180ms | User → Render backend (ap-southeast-1) |
| **Backend Processing** | 50ms | SQLite query + JSON serialization |
| **Next.js SSR** | 200ms | Server-side render search results |
| **Response Transfer** | 180ms | ~50KB HTML payload |
| **Frontend Hydration** | 300ms | React mounting + Tailwind parsing |
| **Total (First Load)** | **1,110ms** | ✅ Meets <1.5s target |
| **Total (Cached)** | **610ms** | DNS + TLS cached |

*Note:* The "<50ms backend processing" refers to server-side execution time, not user-perceived latency. Total latency includes network round-trips which dominate the budget.

### 2.3 Budget Constraints (Zero-Cost Hard Cap)
*   **Strict Requirement:** As a non-revenue portfolio project, the system must have **$0.00 liability**.
*   **Viral Protection:** The architecture must degrade gracefully (shut down) rather than auto-scale costs if traffic explodes via LinkedIn.
*   **No Credit Card Risk:** Avoid usage-based billing services (like AWS NAT Gateway) where possible.

### 2.4 System Properties (CAP Theorem)
*   **Train Schedules (AP over CP):** Prioritize **Availability**. If updates fail, serve stale data rather than crashing.
*   **User Profiles (CP over AP):** Prioritize **Consistency**. Saved trips and login sessions must never be corrupted; system should reject logins if DB is partitioned.

## 3. Technical Challenges
1.  **The "Viral vs. Budget" Paradox:** How to serve 100,000 potential users without incurring cloud bills? (Addressed in Sec 10).
2.  **The Latency Budget Challenge:** Achieving 1.5s total page load when network RTT alone is ~180ms requires aggressive optimization. (Addressed in Sec 8).
3.  **Data Fragmentation:** Merging static PDF schedules with dynamic PNR status requires a robust, zero-cost pipeline.
4.  **Stale Data Risk:** Offline/static databases drift from reality. Users showing up for a cancelled train is a critical failure mode. (Mitigated by prominent disclaimer in R1.0).

## 4. Options & Analysis

### Option A: Pure Client-Side (SPA) + Public APIs
*   *Architecture:* React App calling RapidAPI directly from browser.
*   *Merits:* Zero backend cost. Simple to build.
*   *Demerits:* **Violates Budget Constraint (2.3).** API keys exposed to client; rate limits hit instantly by 10 users.
*   *Verdict:* **Rejected.**

### Option B: Monolithic Django/Postgres on AWS
*   *Architecture:* Traditional RDBMS storing all train schedules + user data.
*   *Merits:* ACID compliance. Easy data integrity.
*   *Demerits:* **Violates Performance (2.2) & Budget (2.3).** Hosting Postgres for read-heavy static data is costly. High latency if DB is far from user.
*   *Verdict:* **Rejected.**

### Option C: Hybrid Static/Dynamic (The Chosen Path)
*   *Architecture:* **SQLite** (Embedded read-only) for schedules + **Redis** for caching + **Supabase (Postgres)** for User Data.
*   *Merits:* **Fits all Constraints.** <1ms schedule lookups (SQLite). Zero cost (Embedded). Hard-capped free tiers.
*   *Demerits:* Complexity in "Data Refresh" pipeline (ETL required).

## 5. Recommendation
**Adopt Option C (Hybrid Architecture).**
*   **Reason:** It aligns perfectly with the "Zero Cost" constraints of Release 1.0 while enabling the <1.5s performance target via embedded SQLite. The complexity of ETL is a worthwhile trade-off for the runtime speed and reliability.

## 6. Technology Stack & Strategy

### 6.1 The Stack (Inventory)
| Layer        | Technology        | Version         | Rationale                                                    |
| :----------- | :---------------- | :-------------- | :----------------------------------------------------------- |
| **Frontend** | **Next.js**       | 14 (App Router) | SSR for SEO; Server Components reduce client bundle size.    |
| **Styling**  | **Tailwind CSS**  | 3.4             | Utility-first for rapid UI iteration; zero-runtime overhead. |
| **Backend**  | **FastAPI**       | 0.109           | Async Python for high-concurrency IO (DB/Redis calls).       |
| **Database** | **SQLite**        | 3.45            | Embedded, zero-latency static data engine.                   |
| **Auth**     | **Supabase Auth** | v2              | Managed JWT handling, Google OAuth integration.              |
| **Cache**    | **Redis**         | 7.2             | Sub-millisecond PNR status caching.                          |
| **DevOps**   | **Docker**        | 24.0            | Multi-stage builds for <100MB container size.                |
| **Host**     | **Render**        | -               | Zero-cost PaaS with HTTP/2 support.                          |
| **O11y**     | **Honeycomb**     | Free            | Distributed tracing to visualize the <1.5s latency budget.   |

### 6.2 Data Strategy (Polyglot Persistence)
We use a specific technology for each data access pattern to meet the constraints defined in Section 2.

| Component            | Technology              | Rationale based on Constraints                                                                                          |
| :------------------- | :---------------------- | :---------------------------------------------------------------------------------------------------------------------- |
| **Static Schedules** | **SQLite**              | **Constraint 2.3 (Budget):** Zero hosting cost. **Constraint 2.2 (Latency):** <1ms in-process lookup.                   |
| **User Data**        | **Supabase (Postgres)** | **Constraint 2.4 (Consistency):** Transactional integrity for user profiles. Hard-capped free tier.                     |
| **Live Cache**       | **Redis Cloud**         | **Constraint 2.2 (Latency):** Sub-5ms access for PNR status.                                                            |
| **Search**           | **SQLite FTS5**         | **Constraint 2.2:** Built-in Full-Text Search is faster than external ElasticSearch for small datasets (<10k stations). |

### 6.3 Technology Decision Log

This section documents the alternatives considered and why they were rejected, providing context for architectural decisions.

#### Why Next.js over Alternatives?

| Alternative | Reason Rejected |
|-------------|----------------|
| **Astro** | No support for Client Components (needed for autocomplete combobox with real-time search) |
| **Remix** | Overkill for simple search app; Next.js has better Vercel integration and larger community |
| **Pure React SPA** | No SSR = poor SEO (train routes won't be indexed by Google) + slower initial load on 4G |
| **Vite + React** | Requires separate SSR setup; Next.js provides batteries-included solution |

**Decision:** Next.js 14 App Router for hybrid SSR/CSR with optimal performance.

#### Why FastAPI over Django/Flask?

| Alternative | Reason Rejected |
|-------------|----------------|
| **Django** | Synchronous ORM adds latency; Admin panel/Forms unnecessary for API-only backend; heavier framework |
| **Flask** | No built-in async support; manual OpenAPI generation; slower async via workarounds (gevent/eventlet) |
| **Express.js** | Would require Node.js on backend + frontend (prefer Python for data scripts and ML-friendly ecosystem) |
| **Go (Gin/Echo)** | Faster but poor data engineering ecosystem; SQLite bindings less mature; steeper learning curve |

**Decision:** FastAPI for native async + automatic OpenAPI docs + Python data ecosystem.

#### Why SQLite over Postgres for Train Schedules?

| Alternative | Reason Rejected |
|-------------|----------------|
| **PostgreSQL** | Network latency (50ms+ even in same region); hosting cost on free tiers limited to 500MB; overkill for read-only data |
| **MongoDB** | Document model doesn't fit relational schedule data (trains have many-to-many relationships with stations) |
| **In-Memory (Redis)** | 30MB Upstash free tier limit can't hold full dataset (~50MB compressed); data lost on restart |
| **MySQL** | Similar issues to Postgres; less performant text search compared to SQLite FTS5 |

**Decision:** Embedded SQLite for zero-latency read-only queries with FTS5 full-text search.

#### Why Render.com over Other Hosts?

| Alternative | Reason Rejected |
|-------------|----------------|
| **AWS (EC2/ECS)** | No free tier for compute; complex setup; risk of accidental charges |
| **Heroku** | Free tier discontinued in 2022; paid plans start at $7/mo |
| **Railway** | Free tier limited to $5 credit/month (runs out mid-month for 24/7 apps) |
| **Fly.io** | Complex volume management for SQLite; no hard spending caps |
| **Google Cloud Run** | Excellent but risk of charges if traffic spikes; no hard free tier cap |

**Decision:** Render.com for true zero-cost free tier with hard caps (spins down after 15 mins inactivity).

## 7. Schema Design

### 7.1 Static Data (SQLite)
*Location: `backend/data/trains.db` (Read-Only)*

**Data Source:** `backend/data/schedules.json` - Flat JSON array of ~400,000-500,000 train stop records

**Table: `stations`** (8,000-9,000 rows - extracted from schedules.json)
*   `station_code` (PK, TEXT): e.g., "FM"
*   `station_name` (TEXT NOT NULL): "KACHEGUDA FALAKNUMA"
*   *Indexes:* `stations_fts` (FTS5 Virtual Table on station_code + station_name)

**Design Note:** City_code and zone fields removed - not needed for R1.0 and not available in source data. Stations extracted using DISTINCT (station_code, station_name) from schedules.json.

**Table: `train_schedule`** (400,000-500,000 rows)
*   `id` (PK, INTEGER): From JSON (unique identifier)
*   `train_number` (TEXT NOT NULL): e.g., "47154"
*   `train_name` (TEXT NOT NULL): e.g., "Falaknuma Lingampalli MMTS"
*   `station_code` (FK, TEXT): References stations.station_code
*   `station_name` (TEXT NOT NULL): Denormalized for performance
*   `arrival_time` (TEXT): "HH:MM:SS" or "None"
*   `departure_time` (TEXT): "HH:MM:SS" or "None"
*   `day` (INTEGER): Journey day (1, 2, 3)
*   `stop_number` (INTEGER): Calculated sequence position
*   *Indexes:* `idx_train_number`, `idx_station_code`, `idx_search_composite`

**JSON Record Example:**
```json
{
  "id": 302214,
  "train_number": "47154",
  "train_name": "Falaknuma Lingampalli MMTS",
  "station_code": "FM",
  "station_name": "KACHEGUDA FALAKNUMA",
  "arrival": "None",
  "departure": "07:55:00",
  "day": 1
}
```

**Single-Source Strategy Rationale:**
1. **100% Referential Integrity:** All station_codes in train_schedule guaranteed to exist in stations table
2. **Simplified ETL:** One JSON file → One ingestion script → Two tables
3. **No Data Conflicts:** Single authoritative source eliminates merge logic complexity
4. **Future-Proof:** Station metadata (lat/lng, facilities) can be backfilled in R2.0 if needed

### 7.2 User Data (PostgreSQL)
*Location: Supabase (Free Tier)*

**Table: `users`**
*   `user_id` (PK, UUID)
*   `email` (UNIQUE)
*   `auth_provider` (TEXT): "google"
*   `created_at` (TIMESTAMP)

**Table: `saved_pnrs`**
*   `pnr` (PK, TEXT)
*   `user_id` (FK, UUID)
*   `status` (TEXT): "CNF", "WL"
*   `last_checked` (TIMESTAMP)

## 8. Performance & Scalability Strategy

### 8.1 Meeting the Backend Processing Target (Constraint 2.2)
*   **In-Process Queries:** SQLite queries run *inside* the application memory space, eliminating network round-trips entirely. This guarantees <1ms latency for database lookups.
*   **Region Affinity:** Backend deployed to **Singapore (ap-southeast-1)** via Render.com. When using Redis/Supabase, we select the same region to minimize inter-service latency (~10-20ms vs. 200ms+ cross-region).

### 8.2 Handling Viral Traffic (Constraint 2.1)
*   **Horizontal Scaling:** The backend is stateless. On Render.com, we can manually scale instances if needed (though capped by budget).
*   **Database Scaling:**
    *   *Static Data:* Scales infinitely because `trains.db` is bundled inside every Docker container. 100 containers = 100 Read Replicas.
    *   *User Data:* Supabase handles connection pooling (`pgbouncer`) to support concurrent users.

### 8.3 Circuit Breaker Strategy (Graceful Degradation)

To satisfy **Constraint 2.3 (Budget)** and **Constraint 2.4 (Availability)**, we implement circuit breakers to prevent cascading failures when external dependencies (Redis, PNR APIs) fail or reach quota limits.

#### Failure Modes & Handling

**Failure Mode 1: Redis Unavailable** (Upstash quota exceeded or service down)
*   **Symptom:** 10,000 commands/day limit reached; `ConnectionError` thrown
*   **Circuit Breaker Response:** Open circuit after 5 consecutive failures
*   **Fallback Behavior:** Serve stale data from in-memory LRU cache OR return graceful error
*   **User Experience:** Yellow banner "⚠️ Live data temporarily unavailable. Showing cached results."

**Failure Mode 2: PNR API Unavailable** (RapidAPI 429/500 errors in Release 3.0)
*   **Symptom:** Rate limit exceeded (100 req/day) or service outage
*   **Circuit Breaker Response:** Open circuit after 3 consecutive failures within 60 seconds
*   **Fallback Behavior:** Return last known status from Redis cache (even if >15 mins old)
*   **User Experience:** Display cached status with timestamp: "Last updated: 2 hours ago"

#### Implementation Pattern

```python
# backend/app/services/circuit_breaker.py
from circuitbreaker import circuit
import logging

logger = logging.getLogger(__name__)

@circuit(failure_threshold=5, recovery_timeout=60, expected_exception=ConnectionError)
def fetch_from_redis(key: str):
    """Wraps Redis GET with circuit breaker.
    Opens circuit after 5 consecutive failures; auto-recovers after 60s.
    """
    return redis_client.get(key)

def get_pnr_status(pnr: str):
    """Fetch PNR status with fallback chain: Redis → API → Graceful Error."""
    try:
        # L1: Try Redis cache first
        cached = fetch_from_redis(f"pnr:{pnr}")
        if cached:
            logger.info(f"Cache HIT for PNR {pnr}")
            return json.loads(cached)
    except CircuitBreakerError:
        logger.warning("Redis circuit open - quota exceeded or service down")
        # Circuit is open; skip Redis and try API directly
    except ConnectionError as e:
        logger.error(f"Redis connection failed: {e}")
        # Don't crash; proceed to API fallback
    
    # L2: Try external PNR API
    try:
        result = call_external_pnr_api(pnr)  # RapidAPI call
        # Success: cache the result (if Redis recovers)
        try:
            redis_client.setex(f"pnr:{pnr}", 900, json.dumps(result))  # 15 min TTL
        except:
            pass  # Ignore cache write failures
        return result
    except APIRateLimitError:
        logger.error("PNR API rate limit exceeded")
        return {
            "status": "unavailable",
            "message": "Service quota exceeded. Please try again later."
        }
    except APIError as e:
        logger.error(f"PNR API failed: {e}")
        return {
            "status": "error",
            "message": "Unable to fetch live status. Please try again."
        }
```

#### Monitoring & Observability

*   **Honeycomb Spans:** Log circuit state transitions (`circuit.opened`, `circuit.closed`, `circuit.half_open`)
*   **Metrics:** Track `circuit_breaker_open_count` and `fallback_response_count`
*   **Alerts:** (Future) Send email/Slack alert when circuit opens (indicates external service degradation)

#### User-Facing Behavior

**Frontend Banner Component:**
```jsx
// components/ServiceStatusBanner.tsx
function ServiceStatusBanner({ status }: { status: 'degraded' | 'normal' }) {
  if (status === 'normal') return null;
  
  return (
    <div className="bg-amber-50 border-l-4 border-amber-400 p-4">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-amber-400" /* ... icon ... */ />
        </div>
        <div className="ml-3">
          <p className="text-sm text-amber-700">
            ⚠️ <strong>Service temporarily degraded.</strong> 
            Live data unavailable. Showing cached results.
          </p>
        </div>
      </div>
    </div>
  );
}
```

**Trade-offs:**
*   **Pro:** App stays available even when dependencies fail (Availability over Consistency for non-critical data)
*   **Con:** Users may see stale data (acceptable for Release 1.0 demo; train schedules change infrequently)
*   **Mitigation:** Clearly display "Last updated" timestamps on all cached data

## 9. Caching Strategy
We employ a **Multi-Layer Caching Strategy** to protect the backend from viral loads.

| Layer | Type | Scope | TTL | Invalidation Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **L1: In-Memory** | Python `functools.lru_cache` | Process-local | 5 min | LRU Eviction (Max 1000 items) |
| **L2: Distributed** | Redis Cloud | Regional | 24 hrs | Explicit TTL expiry |
| **L3: CDN** | Vercel Edge Cache | Global | 1 year | Immutable file hashing (Assets) |

### Specific Cache Rules
1.  **Search Results (`search:SBC:MAS`):** TTL 24 hours. *Trade-off:* High cache hit ratio vs. 24h delay in reflecting cancellations.
2.  **PNR Status (`pnr:12345`):** TTL 15 mins. *Trade-off:* Reduces API costs by 90%, but user might see "Waitlist 5" when it actually moved to "Waitlist 4".

## 10. Deployment Strategy (Zero-Cost Contingency)

### 10.1 The "Viral Protection" Stack
To satisfy **Constraint 2.3 (Budget)**, we avoid AWS in favor of providers with hard usage caps.

| Component | Provider | Free Tier Limit | Viral Behavior (Limit Reached) |
| :--- | :--- | :--- | :--- |
| **Compute** | **Render.com** | 750 hrs/mo | App spins down after 15 mins inactivity. Hard cap available. |
| **Database** | **Supabase** | 500 MB DB | Hard cap. Connection limit reached -> API returns 503. |
| **Static Data** | **SQLite** | N/A | Scales infinitely with Compute. No DB cost. |
| **Cache** | **Redis Cloud** | 30 MB | Evicts keys (LRU) when full. Perf degrades, app stays up. |
| **Frontend** | **Vercel** | 100 GB Bandwidth | Hard pause on project. |

### 10.2 Rate Limiting Strategy (DDoS Protection)
*   **Layer 1 (Cloudflare):** Enable "Under Attack Mode" if traffic spikes > 1000 RPS.
*   **Layer 2 (Application):** Implement strict per-IP limits in FastAPI (`slowapi` middleware).
    *   *Limit:* 10 searches / minute per IP.
    *   *Action:* Return `429 Too Many Requests` instantly.

### 10.3 Provider Setup Guide (Zero-Cost Config)
To ensure **$0.00 liability**, sign up for the following specific tiers:

1.  **Backend (Render.com):**
    *   **Sign up:** [render.com](https://render.com)
    *   **Plan:** "Individual" (Free).
    *   **Service Type:** "Web Service" (for FastAPI).
    *   **Limit:** spins down after 15 mins inactivity.

2.  **Frontend (Vercel):**
    *   **Sign up:** [vercel.com](https://vercel.com)
    *   **Plan:** "Hobby" (Free).
    *   **Limit:** Non-commercial use only.

3.  **Database (Supabase):**
    *   **Sign up:** [supabase.com](https://supabase.com)
    *   **Plan:** "Free Tier".
    *   **Includes:** 500MB DB + Auth + API Gateways.

4.  **Cache (Upstash):**
    *   **Sign up:** [upstash.com](https://upstash.com)
    *   **Plan:** "Free" (Serverless Redis).
    *   **Limit:** 10,000 commands/day (Perfect for R1.0).

5.  **Observability (Honeycomb):**
    *   **Sign up:** [honeycomb.io](https://honeycomb.io)
    *   **Plan:** "Free Forever".
    *   **Includes:** 20 million events/month (Generous).

### ❗ Critical: Region Affinity
To minimize latency for Indian users while staying within free tier constraints, we deploy to **Singapore (ap-southeast-1)** for all services.

**Selected Region: Singapore (ap-southeast-1)**
*   **Rationale:** Closest available region to India on free tiers (~180ms RTT vs. 300ms+ for US regions)
*   **Note:** Mumbai (ap-south-1) would be ideal (~80ms RTT) but not available on Render.com free tier

**Service Configuration:**
*   **Render.com (Backend):** Select **Singapore** region during deployment
*   **Supabase (Database):** Select **Southeast Asia (Singapore)** region during project creation
*   **Upstash (Redis):** Select **ap-southeast-1** region when creating database
*   **Vercel (Frontend):** Automatically uses global CDN; primary compute in closest region

**Performance Impact:**
*   Same-region services (Backend → Redis/Supabase): ~10-20ms latency
*   Cross-region services: +200ms latency per call
*   **Critical:** All three backend services (Render + Supabase + Upstash) MUST be in Singapore to hit 1.5s target

## 11. Observability & Monitoring Plan
*   **Metrics:** OpenTelemetry SDK in FastAPI sending traces to **Honeycomb**.
    *   *Key Metric:* `http_request_duration_seconds` (Target: p95 < 500ms).
    *   *Key Metric:* `cache_hit_ratio` (Target: > 80%).
*   **Logs:** Structured JSON logging sent to Provider Logs.
*   **Tracing:** Lightweight tracing to identify slow DB queries.

## 12. Ongoing Maintenance Plan
1.  **Quarterly Data Refresh:**
    *   **Trigger:** GitHub Action (Cron: 1st Sunday of Quarter).
    *   **Action:** Runs `scripts/scrape_irctc.py` -> Validates Data -> Rebuilds Docker Image.
2.  **Security Patching:** Dependabot alerts for Python/Node dependencies.

---

## 13. Project Structure

### 13.1 Monorepo Layout

```
treno-web/
├── backend/                    # Python FastAPI Backend
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── models.py          # Pydantic data models
│   │   ├── routes.py          # API route handlers
│   │   └── db.py              # Database connection logic
│   ├── data/
│   │   ├── trains.db          # SQLite database (generated by ETL)
│   │   └── schedules.json     # Raw JSON data (~45 MB, manual upload)
│   ├── scripts/
│   │   ├── init_db.py         # Creates SQLite schema + indexes + FTS5
│   │   └── ingest_schedule_json.py # ETL: JSON -> stations + train_schedule tables
│   ├── tests/
│   │   └── test_api.py        # Pytest test suite
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Backend container definition
│   └── .env.example           # Environment variable template
├── frontend/                   # Next.js 14 Frontend
│   ├── app/
│   │   ├── page.tsx           # Home page (Hero layout)
│   │   ├── search/
│   │   │   └── page.tsx       # Search results page
│   │   └── layout.tsx         # Root layout
│   ├── components/
│   │   ├── TrainCard.tsx      # Train result card component
│   │   ├── SearchWidget.tsx   # Search form component
│   │   └── Header.tsx         # Navigation header
│   ├── public/
│   │   └── favicon.ico        # Site icon
│   ├── package.json           # Node dependencies
│   ├── next.config.js         # Next.js configuration
│   ├── tailwind.config.js     # Tailwind CSS configuration
│   └── tsconfig.json          # TypeScript configuration
├── docs/                       # Project Documentation
│   ├── system_design.md       # This document (copied from Obsidian)
│   ├── prompt_plan.md         # Orchestration script
│   ├── ui_wireframes.md       # Frontend specifications
│   └── data_ingestion_plan.md # ETL mapping (generated by Agent)
├── .gitignore                  # Git ignore rules
├── render.yaml                 # Render.com deployment config
├── vercel.json                 # Vercel deployment config
└── README.md                   # Project overview
```

### 13.2 Key Design Decisions

1.  **Monorepo:** Both frontend and backend in one repo simplifies deployment and documentation.
2.  **SQLite in Container:** The `backend/data/trains.db` file is COPYed into the Docker image (no external database needed).
3.  **Single-Source JSON Strategy:** 
    - Single JSON file (`schedules.json`) contains all train stop records (~400k rows)
    - Both stations and train_schedule tables extracted from same file
    - Guarantees 100% referential integrity (no orphaned foreign keys)
    - Eliminates CSV merge logic and data conflicts
    - Manual download from Kaggle → Place in `backend/data/` → Run ETL script
4.  **Docs in Repo:** The `docs/` folder contains markdown files copied from Obsidian to provide context for the Antigravity Agent.

### 13.3 File Permissions

**Critical:** The following files must NOT be committed to GitHub:
- `backend/.env` (contains Supabase password)
- `Resource - Treno Web Credentials.md` (in Obsidian only)

**Safe to Commit:**
- `backend/.env.example` (template with placeholders)
- All other files

---

## Appendix: Research & Reference

### A1. External Data Source Analysis

#### 1. Open Government Data (OGD) Platform India
*   **URL:** https://data.gov.in/catalog/railway-station
*   **Freshness:** Annual (Station codes), Quarterly (Routes).
*   **Constraints:** PDF-heavy format requires parsing.
*   **Cost:** Free.

#### 2. Kaggle (2015 Baseline)
*   **URL:** https://www.kaggle.com/datasets/harsh16/indian-railways-time-table-for-trains-available
*   **Use Case:** Providing the initial schema structure and historical baseline.
*   **Cost:** Free.

#### 3. Railway MCP API (Third-Party)
*   **URL:** https://railway-mcp.amithv.xyz/
*   **Rate Limit:** 100 req/day (Free Tier).
*   **Latency:** High (800ms - 2s).
*   **Reliability:** Low (~90% uptime).
*   **Role:** Used ONLY for "Live PNR" checks in Release 3.0.

### A3. Dead/Deprecated Data Sources (Research Findings)

**⚠️ URL Validation Note (Feb 2026):** During data source research, we discovered that many previously documented Indian Railways datasets are no longer accessible. This section documents the failed sources for future reference.

#### Failed Sources:

1.  **datameet/railways (GitHub)**
    *   **URL (Dead):** `https://raw.githubusercontent.com/datameet/railways/master/stations.csv`
    *   **Status:** 404 Not Found (Repository may be private/deleted).
    *   **Impact:** Cannot use for automated ingestion.

2.  **Hugging Face Dataset (julien-c/indian-railway-stations)**
    *   **URL (Dead):** `https://huggingface.co/datasets/julien-c/indian-railway-stations/resolve/main/stations.csv`
    *   **Status:** Repository not found.
    *   **Impact:** Cannot use as a backup source.

3.  **GitHub Gists (Various)**
    *   **URL (Dead):** `https://gist.githubusercontent.com/sankalpsharmaa/.../raw/stations.geojson`
    *   **Status:** 404 Not Found.
    *   **Impact:** Gists are ephemeral; unsuitable for production dependencies.

4.  **data.gov.in API (Station List)**
    *   **URL:** `https://api.data.gov.in/resource/335db748-fbd8-403f-bf91-827909c205b3`
    *   **Status:** Firewall/CORS issues; returns incorrect dataset (Census data instead of Railway stations).
    *   **Impact:** DEPRECATED. Marked as unreliable for automated fetching.
    *   **API Key (Archived):** `579b464db66ec23bdd000001e44375a0256a4ce2469682336b3cea78`

#### Final Resolution:

**Manual JSON Download Strategy (Single Source)**
*   **Data Source:** Kaggle Dataset - [Indian Railways Dataset](https://www.kaggle.com/datasets/sripaadsrinivasan/indian-railways-dataset)
*   **Format:** Single JSON file `schedules.json` containing flat array of train stop records
*   **File Size:** ~45 MB (minified, single line)
*   **Records:** ~400,000-500,000 individual train stops covering ~8,000-9,000 unique stations
*   **Method:** Download ZIP → Extract → Rename to `schedules.json` → Place in `backend/data/` → Run ETL script
*   **Rationale:** 
    - **Single Source of Truth:** Both stations and schedule tables extracted from one file, eliminating data conflicts
    - **100% Referential Integrity:** All station_codes in schedule guaranteed to exist in stations table
    - **Simplified ETL:** One file, one Python script, zero merge logic
    - **No Separate Stations File Needed:** CSV station files found during research were incomplete (371 rows vs 8,539 needed)
    - **API Reliability Issues:** Programmatic APIs unreliable (404s, auth issues). Manual download ensures data integrity.

### A2. Domain Models (JSON)

**Station Model:**
```json
{
  "station_code": "SBC",
  "city_code": "BLR",
  "station_name": "KSR Bengaluru",
  "zone": "SWR"
}
```

**PNR Response:**
```json
{
  "pnr": "1234567890",
  "train": { "number": "12627", "name": "Karnataka Express" },
  "date": "2026-02-15",
  "passengers": [
    { "status": "CNF", "coach": "B1", "berth": "45" }
  ]
}
```
