# 📚 ParkSense AI — Deep Technical Documentation & Interview Guide

This document is designed as a comprehensive technical reference and interview preparation guide for **ParkSense AI (Smart Parking Analytics Platform)**.

---

## 1. DESIGN RATIONALE & ARCHITECTURAL TRADE-OFFS

### Why FastAPI over Flask or Django?
FastAPI was selected for its native asynchronous performance (ASGI), automatic OpenAPI specification generation via Pydantic schema validation, and lightweight footprint. Django introduces heavy ORM overhead and monolithic boilerplates unnecessary for a high-performance REST API. Flask requires numerous third-party extensions for request validation and serialization. The primary trade-off is that FastAPI requires explicit architectural structure for dependency management compared to Django's batteries-included framework.

### Why raw SQLite via `sqlite3` over an ORM like SQLAlchemy?
Raw SQLite with parameterized queries provides absolute transparency, maximum query execution speed, and zero abstraction overhead. ORMs often hide inefficient `N+1` query patterns and generate complex SQL statements that are harder to debug and defend in technical interviews. By writing pure SQL in `database/queries.py`, query logic is explicitly testable and performance-optimized. The trade-off is writing manual mapping logic and lacking multi-database dialect abstraction.

### Why FAISS over Chroma or Pinecone?
FAISS (Facebook AI Similarity Search) runs completely in-memory on CPU with vector persistence to local disk (`rag/index/`). It eliminates cloud network latency, requires zero paid subscription keys (unlike Pinecone), and has minimal memory consumption compared to heavy Java/Docker-backed vector engines like Chroma or Qdrant. The trade-off is that FAISS is an indexer rather than a full database management system; metadata filtering is limited compared to Pinecone.

### Why LangChain?
LangChain provides clean abstractions for text splitters, prompt formatting, document loaders, and embedding model wrappers. It standardizes the pipeline structure while allowing modular replacement of vector stores or LLM backends. The trade-off is LangChain's rapidly evolving API surface, which requires careful version pinning to maintain stability.

### Why Retrieval-Augmented Generation (RAG) instead of Fine-Tuning?
Fine-tuning an LLM changes its parametric knowledge, which is expensive, slow, requires massive training datasets, and still suffers from hallucinations. Parking policies, rates, and overstay rules change over time; RAG allows instant updates simply by editing standard markdown files in `rag/knowledge_base/` without retraining models. RAG also guarantees strict factual grounding through explicit source citations.

### Why a local LLM via Ollama (`llama3.2:3b`)?
Ollama provides local, private, zero-cost LLM inference without sending sensitive facility data to third-party APIs. It guarantees 100% offline functionality, eliminating API rate limits and paid key dependencies. The trade-off is that local execution depends on host CPU/RAM capabilities, resulting in higher latency compared to cloud-hosted GPT-4 APIs.

### Why Sentence Transformers `all-MiniLM-L6-v2`?
`all-MiniLM-L6-v2` produces high-quality 384-dimensional dense vector embeddings with an extremely light memory footprint (~90 MB) and fast inference speed on standard CPUs. It maps sentence semantic similarity accurately for short and medium context passages without requiring GPU acceleration.

### Why REST over GraphQL?
REST provides straightforward HTTP verb semantics (`GET`, `POST`, `PUT`, `DELETE`), deterministic status codes (`200`, `201`, `404`, `409`, `422`), and seamless browser caching. GraphQL introduces complex query parsing overhead and client-side complexity that is unnecessary for defined dashboard payloads.

### Why Vanilla JS over React, Next.js, or Vue?
Vanilla JavaScript combined with static HTML/CSS eliminates build steps (`npm`, `webpack`, `vite`), node_modules bloat, and hydration mismatches. The entire frontend loads instantly as static assets served by FastAPI. It proves core fundamental knowledge of DOM manipulation, fetch API, and event delegation without framework abstractions.

---

## 2. THE HYBRID INTENT ROUTER — DEEP DIVE

### The Core Problem: Why RAG Alone Fails for Live Data
A common architectural flaw in beginner GenAI applications is passing real-time questions (e.g., *"How many slots are free on Floor 2 right now?"*) to a RAG vector store. Vector embeddings index static semantic text, not live state in a relational database. Vector search cannot compute `COUNT(*)`, execute SUM aggregations over today's transactions, or query current slot states (`occupied` vs `available`).

### Hybrid Architecture Solution
ParkSense AI implements a deterministic, rule-based **Intent Router** (`services/intent_router.py`) that acts as a traffic controller before any LLM or vector retrieval step.

```
                      User Question
                            │
                            ▼
              services/intent_router.py
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
         ▼                  ▼                  ▼
    [Type A]             [Type B]           [Type C]
    LIVE DATA             POLICY          OUT OF SCOPE
         │                  │                  │
         ▼                  ▼                  ▼
  Parameterized       FAISS Retrieval       Direct System
   SQL Query          + RAG Engine             Refusal
         │                  │                  │
         ▼                  ▼                  ▼
   LLM Rephrase       Grounded LLM         No LLM Call
  (or Template)         Answer
```

### Classification Rules & Regex Matching
1. **Live Data (Type A):** Evaluated against regex patterns capturing keywords like `available slots`, `floor 1-4`, `ev slots`, `today's revenue`, `occupancy`, and `vehicle movement`. Triggers immediate execution of parameterized SQL functions in `database/queries.py`.
2. **Policy (Type B):** Evaluated against policy keywords like `charges`, `rates`, `overstay`, `penalty`, `rules`, `ev charging fee`, and `cancellation`. Triggers similarity search against `rag/index/`.
3. **Out of Scope (Type C):** Any prompt lacking parking domain terminology (e.g., *"Who is the CEO of Google?"*). Instantly returns a polite system refusal message **without invoking any LLM call**, saving computational cycles and preventing arbitrary usage.

### Grounding & Hallucination Prevention
For Type A queries, the raw SQL result set is formatted as a structured text block and injected into `LIVE_DATA_PROMPT`. The prompt strictly instructs the LLM: *"Present the answer based ONLY on the provided live data. Do NOT invent numbers."* If Ollama is offline, the raw SQL text block is returned directly as a formatted markdown response.

---

## 3. STEP-BY-STEP DATA FLOW WALKTHROUGHS

### (a) Loading the Dashboard
1. Browser fires `DOMContentLoaded` event in `static/js/ui.js` and calls `DashboardModule.load()` in `static/js/dashboard.js`.
2. `DashboardModule.load()` calls `API.getStatistics()`, sending an HTTP `GET /api/statistics` request.
3. FastAPI matches route in `api/routes_analytics.py`, opening a database context via `database/connection.py`.
4. `services/analytics_service.py` calls `queries.get_raw_slots_for_analytics()` and `queries.get_raw_bookings_for_analytics()`.
5. Pandas loads raw records into DataFrames `df_slots` and `df_bookings`.
6. NumPy and Pandas calculate overall occupancy %, revenue trends (grouped by day for 14 days), hourly vehicle entry/exit distributions (0-23 hours), and floor breakdowns.
7. Function returns `StatisticsResponse` payload serialized as JSON.
8. `dashboard.js` updates DOM stat cards, renders 3 Plotly charts, and populates the floor breakdown table.

### (b) Creating a Slot Booking
1. User clicks an `available` slot card on the Slots Grid view (`static/js/slots.js`).
2. `SlotsModule.openBookingModal()` opens the modal overlay and sets slot ID metadata.
3. User fills in plate number (e.g. `MH02-AB1234`) and submits the form.
4. `SlotsModule` sends an HTTP `POST /api/bookings` payload to FastAPI.
5. `api/routes_bookings.py` validates request via Pydantic model `BookingCreateRequest`.
6. `services/booking_service.py` checks slot status in database:
   - If slot is missing -> raises `NotFoundError` (mapped to HTTP `404`).
   - If slot status != `available` -> raises `ConflictError` (mapped to HTTP `409`).
7. If available, `booking_service` calls `queries.create_booking()` with ISO entry timestamp, inserts row into `bookings`, and calls `queries.update_slot_status(slot_id, 'occupied')`.
8. Returns created booking model with HTTP `201 Created`.
9. `slots.js` displays success toast notification, closes modal, and refreshes the slot grid.

### (c) Asking "Show EV charging slots"
1. User submits question in Assistant chat view (`static/js/assistant.js`).
2. JS sends HTTP `POST /api/chat` with body `{"question": "Show EV charging slots"}`.
3. `api/routes_chat.py` delegates to `services/assistant_service.py`.
4. `services/intent_router.py` classifies question as `intent_type = "LIVE_DATA"`, `action_key = "EV_SLOTS"`.
5. `assistant_service.py` calls `queries.get_all_slots(conn, is_ev=1)`.
6. Formats query output into text summary of EV slots.
7. If Ollama is online, LLM rephrases text into natural language; if offline, fallback text block is returned.
8. Returns JSON response: `{ "answer": "...", "intent": "LIVE_DATA", "source": "live_database", "retrieved_docs": ["database/parksense.db"] }`.
9. `assistant.js` renders message bubble with database source tag.

### (d) Asking "What happens if I overstay?"
1. User submits question via chat.
2. `services/intent_router.py` classifies question as `intent_type = "POLICY"`.
3. `services/assistant_service.py` calls `rag/rag_engine.py:answer_policy_question()`.
4. `rag_engine` queries FAISS vector store `similarity_search_with_score()`, retrieving top-4 relevant chunk passages from `overstay_and_penalty.md`.
5. Passes formatted context passages into `POLICY_RAG_PROMPT`.
6. Ollama synthesizes grounded answer citing grace period, 1.5x penalty slab, and clamping rules.
7. Returns response with `retrieved_docs: ["overstay_and_penalty.md"]`.
8. Chat view renders message bubble with document source tags.

### (e) Asking "Who won the 2024 election?"
1. User submits question via chat.
2. `services/intent_router.py` checks keywords; domain check fails. Classifies as `intent_type = "OUT_OF_SCOPE"`.
3. `assistant_service.py` immediately constructs polite refusal text without invoking vector search or LLM.
4. Returns JSON: `{ "answer": "I am ParkSense AI...", "intent": "OUT_OF_SCOPE", "source": "system_refusal", "retrieved_docs": [] }`.
5. Chat view renders refusal message immediately.

---

## 4. INTERVIEW QUESTION & ANSWER PREPARATION (30+ Q&A)

### Category A: Python & FastAPI
1. **Q: How does FastAPI handle async requests under the hood?**
   - *A:* FastAPI is built on Starlette and Pydantic. Async endpoint handlers run on an asyncio event loop. Synchronous def endpoints are run inside an external thread pool (ThreadPoolExecutor) automatically, preventing blocking calls from stalling the main looper thread.
2. **Q: What is Pydantic and how is it used in ParkSense AI?**
   - *A:* Pydantic provides data validation and settings management using Python type hints. It parses incoming JSON request bodies, enforces types, raises automatic `422 Unprocessable Entity` errors on validation failures, and serializes response bodies.
3. **Q: Explain the lifespan context manager in `main.py`.**
   - *A:* The `@asynccontextmanager` lifespan handler replaces old startup/shutdown event decorators. It executes pre-flight tasks (database migration/seeding check and FAISS index initialization) before the application begins accepting HTTP requests.

### Category B: SQL & Data Modeling
4. **Q: Why are transactions wrapped in context managers in `database/connection.py`?**
   - *A:* The `@contextmanager` yields a SQLite connection. If the block completes cleanly, it automatically issues `conn.commit()`. If an exception occurs, it issues `conn.rollback()` and logs the error, ensuring database integrity.
5. **Q: Why use WAL mode (`PRAGMA journal_mode = WAL`) in SQLite?**
   - *A:* Write-Ahead Logging allows concurrent readers to read the database while a writer is writing, dramatically improving read performance and reducing `database is locked` errors.
6. **Q: How is billing calculated safely across the system?**
   - *A:* Billing logic is consolidated in `utils/helpers.py:calculate_parking_fee()`. It computes exact duration from entry/exit ISO timestamps, applies `math.ceil()` with a 1-hour minimum, and multiplies by the slot's hourly rate. Reused in seed generation, manual releases, and API calculations to prevent logic duplication.

### Category C: RAG, Embeddings & Vector Search
7. **Q: What is the embedding dimension of `all-MiniLM-L6-v2`?**
   - *A:* 384 dimensions. It outputs a normalized 384-length floating-point vector for every text chunk.
8. **Q: How does FAISS perform vector similarity search?**
   - *A:* FAISS computes vector inner product (cosine similarity when vectors are L2-normalized) between the query vector and indexed document vectors to return the top-K closest matches.
9. **Q: Why chunk documents with overlap?**
   - *A:* Overlap (e.g. 50 characters) ensures that semantic context split across chunk boundaries is preserved, preventing lost information during retrieval.

### Category D: System Design & Architecture
10. **Q: How does the system handle Ollama being offline?**
    - *A:* Graceful degradation. `rag/llm_provider.py:is_ollama_available()` checks server connectivity. Live data queries fall back to structured SQL text output; policy queries return top retrieved document excerpts with an informative note.

---

## 5. HARD CROSS-QUESTIONS & HONEST ANSWERS

### 1. "How would this system scale to 10,000 slots and 100,000 daily bookings?"
- *Honest Answer:* SQLite would become a write bottleneck under high concurrent write loads. I would migrate the database layer to PostgreSQL with horizontal read replicas, replace in-memory FAISS with Milvus or Pgvector, and introduce Redis caching for slot availability counts.

### 2. "What happens during concurrent booking requests for the exact same slot?"
- *Honest Answer:* In the current single-instance setup, SQLite handles atomic table locks. However, to handle distributed concurrency, I would implement database row-level locking (`SELECT ... FOR UPDATE`) or a Redis distributed lock (`redlock`) on `slot_id`.

### 3. "How do you evaluate RAG response quality?"
- *Honest Answer:* RAG quality can be evaluated using the RAGAS framework across three metrics: **Faithfulness** (is the answer grounded in context?), **Answer Relevance** (does it address the prompt?), and **Context Precision** (are top-K retrieved chunks relevant?).

---

## 6. SUGGESTED COMMIT HISTORY (2-3 WEEK BUILD STORY)

1. `feat: initialize project structure, configuration settings, and logger`
2. `feat(database): define schema.sql for slots and bookings tables`
3. `feat(database): implement SQLite connection manager with WAL mode`
4. `feat(database): implement parameterized SQL query functions`
5. `feat(database): create deterministic seed generator with 14-day history`
6. `docs(rag): write official knowledge base markdown policy documents`
7. `feat(rag): setup SentenceTransformers embedding loader and FAISS vector store`
8. `feat(rag): implement RAG retrieval engine and prompt templates`
9. `feat(services): implement slot and booking business logic with billing helper`
10. `feat(services): implement Pandas and NumPy analytics aggregations`
11. `feat(services): implement rule-based hybrid intent router`
12. `feat(services): implement AI assistant service with offline fallback`
13. `feat(api): create Pydantic schemas and FastAPI slot route handlers`
14. `feat(api): create booking creation, release, and cancellation routes`
15. `feat(api): create statistics, health, and AI chat endpoints`
16. `feat(frontend): build dark theme HTML dashboard with sidebar layout`
17. `feat(frontend): implement Plotly charts and dynamic stat cards in JS`
18. `feat(frontend): implement interactive slots grid and booking modal`
19. `feat(frontend): implement AI assistant chat UI with suggestion chips`
20. `test: add automated pytest suite for API endpoints and billing logic`
21. `docs: create comprehensive README.md, SETUP.md, and DOCUMENTATION.md`
