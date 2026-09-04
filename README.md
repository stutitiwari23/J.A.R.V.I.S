## ⚡ Overview

**J.A.R.V.I.S** (*Just A Rather Very Intelligent System*) is a personal AI assistant inspired by Tony Stark's iconic AI. It blends a futuristic holographic HUD interface with state-of-the-art **Google Gemini** generative intelligence, ultra-low latency response times, real-time Web Speech recognition, and complete local privacy controls.

---

## 🌟 Key Features

### 🧠 Ultra-Fast Google Gemini Brain
- Powered by **`gemini-3.1-flash-lite`** for rapid token generation (~2.4s initial response time).
- Intelligent fallback cascade across `gemini-flash-lite-latest`, `gemini-3.5-flash-lite`, and `gemini-3.6-flash`.
- **Persistent Connection Pooling**: Caches the official `google-genai` client to eliminate repeated TLS handshake delays.
- Dynamic Google Search grounding for live/current real-world information.

### 🎙️ Real-Time Voice Interaction (STT & TTS)
- **Live Interim Speech Transcription**: Transcribes words on-screen in real time as you speak with zero silence delays.
- **Natural Male American Voice Output**: Custom-filtered Web Speech Synthesis with natural pauses and clean markdown stripping.
- **Hands-Free Hotkeys**: Tap `Spacebar` to toggle voice listening, `Esc` to halt speech, and `Enter` to send.

### 🕒 Local Search History & Privacy Management
- **Local SQLite Persistence**: Stores every search and command with timestamps in `memory.db`.
- **Browser Mirroring**: Backed by `localStorage` for instant offline and cold-boot recovery.
- **HUD History Modal**:
  - Click **`🕒 HISTORY`** in the top navigation bar to inspect past queries.
  - **Click-to-Load**: Tap any query to instantly insert or re-run it.
  - **Individual Deletion**: Remove any entry with the **🗑** button.
  - **Wipe All**: Clear complete local search logs with one click.

### 🔮 Futuristic Holographic HUD Interface
- Central animated **AI Core Orb** with concentric spinning telemetry rings and particle mesh background.
- Dynamic visual feedback states: `READY` (Cyan), `LISTENING` (Neon Blue pulse), `THINKING` (Amber spin), `SPEAKING` (Audio waveform pulse), and `ERROR` (Red alert).
- Integrated markdown renderer with syntax highlighting, lists, and collapsible conversation stream drawer.
- Spacious, clean bottom status bar and input dock.

### 🛠️ Built-in Safe Tools & Long-Term Memory
- **🧮 Fast Math Engine**: Evaluates calculations, percentages, and conversions locally in `0ms` using safe AST parsing.
- **🔒 Guarded Shell Runner**: Safe command execution with automatic confirmation alerts for destructive operations (`rm`, `del`, `format`, `shutdown`).
- **📁 Workspace Files**: Read, create, and list project files safely restricted within the workspace.
- **📊 System Diagnostics**: Reports live CPU, RAM, and operating system metrics.
- **🧠 SQLite Preferences**: Remembers user preferences (`name`, `preferred_language`, custom notes).

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- A Google Gemini API Key ([Get one free from Google AI Studio](https://aistudio.google.com/))

### 1. Clone the Repository
```bash
git clone https://github.com/stutitiwari23/J.A.R.V.I.S.git
cd J.A.R.V.I.S
```

### 2. Set Up Virtual Environment & Dependencies
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the sample environment file:
```bash
cp .env.example .env
```
Open `.env` and add your Gemini API key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
```

### 4. Launch Jarvis
```bash
python main.py
```
Open your browser to **[http://127.0.0.1:8000](http://127.0.0.1:8000)** (Chrome or Edge recommended for optimal Web Speech support).

> **CLI Mode**: To launch the interactive Terminal REPL instead of the web dashboard:
> ```bash
> python main.py --cli
> ```

---

## ☁️ Deployment

### Deploy to Vercel (One-Click Serverless)

Jarvis is already deployed on Vercel.

Live Link- https://jarvis-livid-psi.vercel.app/
  ```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Space` | Toggle Voice Microphone (Click to speak / stop) |
| `Enter` | Send message in prompt input |
| `Esc` | Stop Jarvis from speaking / Cancel voice recognition |

---

## 📁 Project Structure

```text
J.A.R.V.I.S/
├── api/
│   └── index.py             # Vercel serverless ASGI handler
├── backend/
│   ├── main.py              # FastAPI application & API endpoints
│   ├── agent.py             # Central unified agent loop
│   ├── ai.py                # Gemini AI brain & connection pooling
│   ├── memory.py            # SQLite database & search history manager
│   ├── config.py            # Configuration & environment loader
│   ├── static/
│   │   └── index.html       # Futuristic holographic HUD web interface
│   ├── tools/
│   │   ├── __init__.py      # Tool registry & catalog
│   │   ├── calculator.py    # Safe AST-based math evaluation
│   │   ├── search.py        # Web search integration
│   │   ├── files.py         # Workspace safe file operations
│   │   ├── shell.py         # Guarded command runner
│   │   └── system.py        # System health & diagnostic metrics
│   └── integrations/
│       ├── gmail.py         # Email checks & message drafting
│       └── calendar.py      # Calendar event queries
│
├── config.yaml              # Assistant & tool settings
├── .env.example             # Sample environment template
├── requirements.txt         # Python package dependencies
├── vercel.json              # Vercel deployment configuration
├── render.yaml              # Render infrastructure specification
├── Dockerfile               # Container build configuration
├── docker-compose.yml       # Docker compose orchestration
├── main.py                  # Main application entrypoint
└── test_jarvis.py           # Automated test suite (25+ tests)
```

---

## 🧪 Testing & Verification

Run the full automated test suite covering Gemini integration, safe tools, destructive gating, memory, and FastAPI endpoints:

```bash
python test_jarvis.py
```

---

## 🛡️ Security & Privacy

- **API Keys**: Never committed to version control (`.env` is excluded via `.gitignore`).
- **Destructive Gating**: Commands such as `rm -rf`, `del`, `format`, or `shutdown` trigger an explicit confirmation prompt before execution.
- **Directory Traversal Defense**: File operations are strictly restricted to the workspace boundary.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
