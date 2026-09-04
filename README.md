# J.A.R.V.I.S — Futuristic Personal AI Assistant

> **Dark HUD Interface • Animated AI Orb • Voice Interaction • Minimal Backend**

JARVIS is a futuristic, personal AI assistant inspired by sci-fi HUD computer interfaces. It features an interactive animated central AI Orb, full speech-to-text (STT) and voice synthesis (TTS), local AI intelligence, and safe everyday tools.

---

## ⚡ Key Capabilities

- **🎙️ Voice-First Interaction**: Click the central AI Orb or press `Space` to speak. Jarvis responds with voice and text.
- **🔮 Animated Central AI Orb**: Dynamic visual states (**READY**, **LISTENING**, **THINKING**, **SPEAKING**, **ERROR**) with concentric holographic HUD rings and particle mesh background.
- **🧮 Safe Math Engine**: AST-based math evaluation (percentages, unit conversions, functions). No `eval()`.
- **🌐 Live Web Search**: Fast internet queries via Tavily or DuckDuckGo.
- **⚡ System Diagnostics**: Live CPU, RAM, OS, and Python runtime metrics.
- **📁 Workspace Files**: Read, create, append, and list files safely confined within the workspace.
- **🔒 Protected Shell**: Executes terminal commands with automatic confirmation gating for destructive operations (`rm`, `del`, `format`, `shutdown`).
- **📧 Gmail & 📅 Calendar**: Unread email checks, schedule lookups, and message dispatch with safety confirmation.
- **🧠 SQLite Memory**: Remembers user preferences (`user_name`, `preferred_language`, custom notes).

---

## 🚀 Quick Start (Local)

### 1. Web Dashboard (Live UI)
```powershell
.\.python\python.exe main.py
```
> Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser (Google Chrome or Edge recommended for voice STT/TTS).

### 2. Terminal REPL (Rich CLI)
```powershell
.\.python\python.exe main.py --cli
```

### 3. Run Self-Verification Tests (25 Tests)
```powershell
.\.python\python.exe test_jarvis.py
```

---

## ☁️ Deployment Guide

### Option A: 1-Click Cloud Deployment (Render / Railway / Koyeb)

1. Push this repository to GitHub.
2. In **[Render](https://render.com)** or **[Railway](https://railway.app)**:
   - Create a new **Web Service**.
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`
3. Add any optional environment variables (`TAVILY_API_KEY`, `OPENAI_API_KEY`, `OLLAMA_URL`).

### Option B: Docker Container Deployment

Build and run the production container:
```bash
docker build -t jarvis-assistant .
docker run -d -p 8000:8000 --name jarvis jarvis-assistant
```

Or using `docker-compose`:
```bash
docker-compose up -d
```

---

## 📁 Clean Repository Structure

```text
Jarvis/
├── backend/
│   ├── main.py              # FastAPI server & Terminal CLI REPL
│   ├── config.py            # YAML + .env loader
│   ├── agent.py             # Single central Agent brain
│   ├── ai.py                # AIClient (Ollama + OpenAI + offline fallback)
│   ├── memory.py            # SQLite preferences & history storage
│   ├── static/
│   │   └── index.html       # Futuristic Animated Orb HUD Interface
│   ├── tools/
│   │   ├── __init__.py      # Minimal Tool class & catalog
│   │   ├── calculator.py    # Safe AST math parser
│   │   ├── search.py        # Web search with fast timeout
│   │   ├── files.py         # Workspace-restricted file operations
│   │   ├── system.py        # CPU, RAM, OS diagnostic tool
│   │   └── shell.py         # Safe shell runner with destructive gating
│   └── integrations/
│       ├── gmail.py         # Gmail integration with confirmation
│       └── calendar.py      # Google Calendar integration
│
├── config.yaml              # Single user configuration
├── .env.example             # Environment template
├── Dockerfile               # Container deployment specification
├── docker-compose.yml       # 1-command container orchestration
├── Procfile                 # Cloud web process entrypoint
├── render.yaml              # Render infrastructure-as-code
├── requirements.txt         # Minimal dependencies
├── main.py                  # Unified launcher entry point
└── test_jarvis.py           # 25-test verification test suite
```
