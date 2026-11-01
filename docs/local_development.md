# DocSentry — Local Development Guide
**Version:** 1.0.0-dev  
**Platform:** macOS (Apple Silicon M-Series) / Linux / Windows WSL2

---

## 1. Prerequisites
- Python 3.12+ (or 3.14)
- Node.js 18+ and npm
- Git 2.38+
- (Optional) Ollama running locally with `qwen3:8b` for AI-assisted semantic verification

---

## 2. Quickstart

### 2.1 Backend Setup
```bash
cd DocSentary
source .venv/bin/activate
pip install -e .
pip install fastapi uvicorn sqlalchemy alembic pydantic-settings pyjwt cryptography psycopg[binary] bcrypt httpx
alembic upgrade head
uvicorn backend.app.main:app --reload --port 8000
```
- API Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/api/v1/health`

### 2.2 Frontend Setup
```bash
cd DocSentary/web
npm install
npm run dev
```
- Web Application: `http://localhost:3000`

---

## 3. Running Automated Tests

```bash
cd DocSentary
# Run all tests (Track A core detection + Track B backend platform & security)
PYTHONPATH=. .venv/bin/pytest tests/unit/ backend/tests/
```
