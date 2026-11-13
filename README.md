# 🅿️ ParkSense AI — Smart Parking Analytics Platform

> **An AI-powered web application for multi-floor parking management, live analytics, and hybrid RAG conversational assistance.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Builtin-003B57?style=flat&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![LangChain](https://img.shields.io/badge/LangChain-Enabled-1C3C3C?style=flat)](https://www.langchain.com/)
[![FAISS](https://img.shields.io/badge/FAISS-CPU-0467DF?style=flat)](https://github.com/facebookresearch/faiss)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-black?style=flat)](https://ollama.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📷 Screenshots

| Dashboard Analytics | Slots Grid & Reservation |
|---|---|
| ![Dashboard Overview](docs/screenshots/dashboard.png) | ![Slots Grid](docs/screenshots/slots.png) |

| Facility Bookings | AI Parking Assistant |
|---|---|
| ![Bookings Management](docs/screenshots/bookings.png) | ![AI Assistant](docs/screenshots/assistant.png) |

---

## 📌 Overview & Problem Statement

Modern urban parking facilities face operational inefficiencies due to fragmented slot tracking, unpredictable revenue visibility, and customer query bottlenecks.

**ParkSense AI** addresses these challenges by offering a unified, high-performance platform that combines real-time multi-floor parking slot management, Pandas-powered analytical dashboards, and a **Hybrid Intent AI Assistant**. The assistant deterministically routes real-time slot/revenue queries to pure SQL, while directing policy queries through a locally hosted **FAISS Retrieval-Augmented Generation (RAG)** pipeline—eliminating paid API dependencies and preventing LLM hallucination.

---

## ✨ Features Grouped by Module

### 1. Multi-Floor Parking Management
- **60 Designated Slots:** Distributed across 4 floors with specialized classifications (EV Charging ⚡, Accessible ♿, Designated Reserved 🔒, Near-Exit 🚪).
- **Interactive Slots Grid:** Instant color-coded status badges (`available`, `occupied`, `reserved`), floor filters, vehicle type filters, and real-time search.
- **One-Click Slot Booking & Release:** Modal slot reservation, automated duration calculation, single-source billing logic, and instant slot status synchronization.

### 2. Live Facility Analytics & Dashboard
- **6 Key Performance Indicator (KPI) Cards:** Overall occupancy %, today's revenue, active vehicles, available slots, EV availability, today's bookings.
- **Interactive Plotly Visualizations:**
  - 14-day historical revenue trend line.
  - Occupancy percentage bar chart by floor.
  - 24-hour vehicle movement grouped bar chart (entries vs exits).
- **Floor-Wise Breakdown Table:** Complete capacity and occupancy rate monitoring.

### 3. Hybrid Intent AI Assistant
- **Deterministic Intent Router:** Classifies incoming questions into Live Data (SQL), Policy (RAG), or Out of Scope without LLM overhead.
- **Grounded SQL Live Data Retrieval:** Injects real-time database facts directly into the prompt for natural language rephrasing (or formatted fallbacks).
- **FAISS Policy RAG Pipeline:** Retrieves context from 5 official markdown documents using `all-MiniLM-L6-v2` embeddings and local Ollama (`llama3.2:3b`).
- **Graceful Offline Degradation:** Live SQL queries work even if Ollama is stopped.

---

## 🏗️ Architecture Diagram

```
                              +---------------------------------------+
                              |         Browser Client (Vanilla JS)   |
                              +------------------+--------------------+
                                                 | REST / JSON
                                                 v
                              +---------------------------------------+
                              |          FastAPI Server (main.py)     |
                              +------------------+--------------------+
                                                 |
             +-----------------------------------+-----------------------------------+
             |                                   |                                   |
             v                                   v                                   v
  +--------------------+               +--------------------+               +--------------------+
  |    Slots Router    |               |  Bookings Router   |               |  Analytics Router  |
  +---------+----------+               +---------+----------+               +---------+----------+
            |                                    |                                   |
            v                                    v                                   v
  +----------------------------------------------------------------------------------------------+
  |                                 SQLite Database (parksense.db)                               |
  +----------------------------------------------------------------------------------------------+
                                                 ^
                                                 |
                                     +-----------+-----------+
                                     |   AI Assistant Router |
                                     +-----------+-----------+
                                                 |
               +---------------------------------+---------------------------------+
               | (Type A: LIVE DATA)             | (Type B: POLICY)                | (Type C: OUT OF SCOPE)
               v                                 v                                 v
     +-------------------+             +-------------------+             +-------------------+
     | SQL Query Exec    |             | FAISS Vector Store|             |  System Refusal   |
     +---------+---------+             +---------+---------+             +-------------------+
               |                                 |
               +----------------+----------------+
                                |
                                v
                     +-------------------+
                     | Ollama LLM Engine | (Local llama3.2:3b)
                     +-------------------+
```

---

## 🛠️ Tech Stack & Rationales

| Layer | Technology | Justification |
|---|---|---|
| **Backend** | Python 3.11+ / FastAPI | Async performance, automated OpenAPI validation, lightweight footprint |
| **Database** | SQLite3 (Built-in) | Zero-configuration file database with strict ACID transaction guarantees |
| **Data Analytics** | Pandas / NumPy / Plotly | High-speed array manipulations, data aggregations, dynamic SVG/Canvas charting |
| **AI / RAG** | LangChain / FAISS / SentenceTransformers | Industrial-grade vector search and prompt templating running 100% on CPU |
| **Local LLM** | Ollama (`llama3.2:3b`) | Completely free, offline, private local inference without paid API keys |
| **Frontend** | Vanilla HTML5 / CSS3 / JavaScript | Zero build step, instant page loads, clean DOM manipulation |

---

## 📂 Folder Structure

```
parksense-ai/
├── main.py                          # FastAPI application initialization & static mount
├── config/
│   ├── __init__.py
│   └── settings.py                  # Typed configuration & environment settings loader
├── api/
│   ├── __init__.py
│   ├── routes_slots.py              # GET /api/slots, /api/floors handlers
│   ├── routes_bookings.py           # POST/GET/PUT/DELETE /api/bookings handlers
│   ├── routes_analytics.py          # GET /api/statistics, /api/health handlers
│   ├── routes_chat.py               # POST /api/chat AI assistant handler
│   └── schemas.py                   # Pydantic request and response schemas
├── database/
│   ├── __init__.py
│   ├── connection.py                # SQLite connection manager & WAL mode setup
│   ├── schema.sql                   # Database DDL & index declarations
│   ├── seed.py                      # Deterministic 60-slot & 14-day historical seeding
│   └── queries.py                   # Parameterized SQL query functions
├── services/
│   ├── __init__.py
│   ├── slot_service.py              # Slot retrieval and floor business logic
│   ├── booking_service.py           # Single-source billing calculation & slot updates
│   ├── analytics_service.py         # Pandas/NumPy aggregations & revenue trend processing
│   ├── intent_router.py             # Deterministic rule-based Type A / B / C classifier
│   └── assistant_service.py         # Assistant orchestration & fallback handler
├── rag/
│   ├── __init__.py
│   ├── llm_provider.py              # Ollama LLM wrapper with offline check
│   ├── embeddings.py                # HuggingFace SentenceTransformers wrapper
│   ├── vector_store.py              # FAISS index construction, persistence, and auto-rebuild
│   ├── rag_engine.py                # RAG context retrieval and policy answer synthesis
│   ├── prompts.py                   # Grounded SQL & Policy prompt templates
│   └── knowledge_base/              # 5 official policy markdown documents
├── utils/
│   ├── __init__.py
│   ├── logger.py                    # Standardized application logger
│   └── helpers.py                   # Math ceiling billing & timestamp helpers
├── static/
│   ├── index.html                   # Single-page dashboard HTML
│   ├── css/styles.css               # Modern dark theme styles
│   └── js/                          # Modular frontend JavaScript files
├── tests/
│   └── test_api.py                  # Automated pytest suite covering all endpoints
├── requirements.txt                 # Project dependencies
├── .env.example                     # Environment template
├── .gitignore                       # Git ignore list
├── LICENSE                          # MIT License
├── README.md                        # Primary project documentation
├── DOCUMENTATION.md                 # Interview prep & architecture deep-dive
└── SETUP.md                         # Step-by-step setup guide
```

---

## ⚡ Quickstart

1. Clone the repository and navigate to the project directory:
   ```powershell
   git clone https://github.com/yourusername/parksense-ai.git
   cd parksense-ai
   ```
2. Follow the detailed step-by-step installation instructions in **[SETUP.md](SETUP.md)**.
3. Launch the application server:
   ```powershell
   python main.py
   ```
4. Access the web dashboard at `http://127.0.0.1:8000`.

---

## 📡 API Reference Overview

| Method | Endpoint | Description | Sample Status |
|---|---|---|---|
| `GET` | `/api/health` | Check service, Ollama, and FAISS readiness | `200 OK` |
| `GET` | `/api/slots` | List slots with optional query filters | `200 OK` |
| `GET` | `/api/slots/{id}` | Fetch single slot details | `200 OK` / `404 Not Found` |
| `GET` | `/api/floors` | Fetch floor-wise summaries | `200 OK` |
| `GET` | `/api/statistics` | Fetch dashboard KPI & analytics payload | `200 OK` |
| `POST` | `/api/bookings` | Book an available slot | `201 Created` / `409 Conflict` |
| `GET` | `/api/bookings` | List all facility bookings | `200 OK` |
| `PUT` | `/api/bookings/{id}/release` | Release booking & compute duration fee | `200 OK` / `409 Conflict` |
| `DELETE` | `/api/bookings/{id}` | Cancel active booking | `200 OK` / `404 Not Found` |
| `POST` | `/api/chat` | Query the AI assistant | `200 OK` |

---

## 💬 Sample Assistant Prompts & Answers

### Live Data Questions (SQL Routed)
- **Q:** *"Which parking slots are available?"*
  - **Answer:** *"Total Available Slots: 42. Floor 1 has 10 available slots (F1-A01, F1-A03...). Floor 2 has 11 available slots..."*
- **Q:** *"Show today's parking revenue"*
  - **Answer:** *"Today's Revenue is ₹1,480.00 across 12 completed bookings with an average ticket value of ₹123.33."*

### Policy Questions (FAISS RAG Routed)
- **Q:** *"What are today's parking charges?"*
  - **Answer:** *"According to pricing_policy.md, Two-Wheelers are ₹20/hr, Standard Cars are ₹40/hr (Floors 1-2) or ₹35/hr (Floors 3-4), and SUVs are ₹60/hr."*
- **Q:** *"What happens if I overstay?"*
  - **Answer:** *"Per overstay_and_penalty.md, a 15-minute grace period is provided. Overstaying beyond 2 hours incurs a 1.5x hourly penalty rate. Occupancy over 24 hours results in wheel clamping and a ₹1,000 fine."*

### Out-of-Scope Questions (Refused)
- **Q:** *"Who is the CEO of Google?"*
  - **Answer:** *"I am ParkSense AI, dedicated specifically to assisting with parking management, live slot availability, pricing, and facility policies. I cannot answer questions outside of parking operations."*

---

## ⚠️ Known Limitations
- Single-instance SQLite database (not designed for multi-region active-active database clusters).
- Keyword intent router relies on explicit parking domain vocabulary.

## 🚀 Future Improvements
- License Plate Recognition (ALPR) camera stream integration.
- Dynamic peak-hour pricing algorithms.
- WebSocket live push notifications for slot status updates.

---

## 💡 Suggested GitHub Metadata
- **Repo Description:** *AI-powered smart parking analytics platform with real-time SQLite tracking, Plotly dashboards, and local RAG assistant.*
- **Suggested Topics:** `fastapi`, `sqlite`, `pandas`, `plotly`, `langchain`, `faiss`, `ollama`, `rag`, `ai-assistant`, `python`, `vanilla-js`, `smart-parking`.

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
