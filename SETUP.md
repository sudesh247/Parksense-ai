# ParkSense AI — Local Environment Setup Guide

This document provides step-by-step instructions to set up, configure, and launch **ParkSense AI** on Windows PowerShell.

---

## 📋 Prerequisites

Before starting, ensure your machine meets the following requirements:
- **Operating System:** Windows 10/11
- **Python:** 3.11 or higher
- **RAM:** Minimum 8 GB RAM (16 GB recommended for Ollama LLM execution)

---

## 🚀 Step-by-Step Setup Instructions

> [!IMPORTANT]
> All commands listed below are formatted for **Windows PowerShell**. Run PowerShell as Administrator if you encounter permission errors.

### Step 1: Verify Python Installation
Check that Python 3.11+ is installed and accessible in your system PATH:
```powershell
python --version
```
*If skipped:* The application will not run. Install Python 3.11+ from [python.org](https://www.python.org/downloads/).

---

### Step 2: Create & Activate Virtual Environment
Navigate to the project root directory and create an isolated Python virtual environment:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*If script execution is disabled on PowerShell, run `Set-ExecutionPolicy Unrestricted -Scope Process` first.*

---

### Step 3: Install Python Dependencies
Install all required libraries specified in `requirements.txt`:
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```
> [!WARNING]
> This command will download **PyTorch (~2.5 GB)** as a core dependency for SentenceTransformers (`all-MiniLM-L6-v2`). Ensure a stable internet connection.

---

### Step 4: Install & Launch Ollama (Local AI Engine)
1. Download and install **Ollama for Windows** from [ollama.com](https://ollama.com/download/windows).
2. Once installed, open a PowerShell terminal and verify Ollama is active:
```powershell
ollama --version
curl http://localhost:11434/api/tags
```
*If skipped:* ParkSense AI will operate in **Graceful Offline Mode**. Live SQL data queries and dashboard analytics will work fully, but policy questions will show a prompt to start Ollama.

---

### Step 5: Pull the Local LLM Model
Download the lightweight `llama3.2:3b` model (~2.0 GB):
```powershell
ollama pull llama3.2:3b
```

---

### Step 6: Configure Environment Variables
Copy the provided `.env.example` template to `.env`:
```powershell
Copy-Item .env.example .env
```
> [!NOTE]
> **ZERO Paid API Keys Required!** The application is pre-configured to use local SQLite, local HuggingFace embeddings, and local Ollama LLM. Nothing inside `.env` needs editing for default execution.

---

### Step 7: Launch ParkSense AI Application
Start the Uvicorn web server:
```powershell
python main.py
```
*(Or alternatively: `uvicorn main:app --reload --host 127.0.0.1 --port 8000`)*

Open your browser and navigate to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## ℹ️ First-Run Initialization Note

On the very first launch:
1. The SQLite database (`database/parksense.db`) will be automatically created and populated with **60 slots** and **14 days of realistic historical booking data**.
2. The embedding model `all-MiniLM-L6-v2` (~90 MB) will download automatically.
3. The FAISS vector index will be built from knowledge base documents and saved to `rag/index/`.

*Subsequent application starts will load instantaneously from disk.*

---

## 🛠️ Troubleshooting Guide

| Issue | Root Cause | Solution Command / Action |
|---|---|---|
| `Address already in use` | Port 8000 is occupied by another process | Run `Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force` or edit `APP_PORT=8001` in `.env` |
| `Ollama not reachable` | Ollama background service is stopped | Launch Ollama application from Start menu or run `ollama serve` |
| `Model llama3.2:3b not found` | LLM model not downloaded | Run `ollama pull llama3.2:3b` in PowerShell |
| `database is locked` | Concurrent lock on SQLite DB | Restart the Uvicorn server (`Ctrl+C` then `python main.py`) |
| `FAISS index corrupt / loading error` | Stale or partial vector index | Delete the folder `rag/index/` and restart the application to trigger automatic rebuild |
