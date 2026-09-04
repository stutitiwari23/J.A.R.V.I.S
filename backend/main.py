import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from backend.config import config
from backend.agent import agent
from backend.memory import memory
from backend.tools import ALL_TOOLS

# FastAPI Application
app = FastAPI(title="Jarvis API", version="1.0.0")

@app.middleware("http")
async def add_cors_and_pna_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response(status_code=204)
    else:
        response = await call_next(request)
    
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    confirmed: bool = False

class MemoryRequest(BaseModel):
    key: str
    value: str

STATIC_FILE = Path(__file__).parent / "static" / "index.html"
STATIC_DIR = Path(__file__).parent / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
def serve_ui():
    """Serve the futuristic Jarvis HUD interface."""
    if STATIC_FILE.exists():
        return HTMLResponse(content=STATIC_FILE.read_text(encoding="utf-8"), status_code=200)
    return HTMLResponse(content="<h1>Jarvis UI Loading Error: index.html missing.</h1>", status_code=500)

@app.get("/health")
@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/status")
@app.get("/api/status")
def get_status():
    """Get system and capability status."""
    return {
        "status": "online",
        "assistant": config.get("assistant", {}).get("name", "Jarvis"),
        "model": config.get("model", {}),
        "tools_count": len(agent.tools),
        "memory_enabled": config.get("memory", {}).get("enabled", True),
        "memory_items": len(memory.list_all())
    }

@app.get("/tools")
@app.get("/api/tools")
def get_tools():
    """List all available tools and their active status."""
    enabled_names = {t.name for t in agent.tools}
    return [
        {
            "name": t.name,
            "description": t.description,
            "enabled": t.name in enabled_names
        }
        for t in ALL_TOOLS.values()
    ]

@app.post("/chat")
@app.post("/api/chat")
def chat(request: ChatRequest):
    """Send a message to the unified Jarvis Agent."""
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    print("[API] Chat request received")
    print(f"[API] Message: {request.message}")
    # Record query in local search history
    memory.add_search(request.message)
    res = agent.handle_message(request.message, confirmed=request.confirmed)
    if "answer" not in res and "response" in res:
        res["answer"] = res["response"]
    elif "response" not in res and "answer" in res:
        res["response"] = res["answer"]
    print("[API] Response returned")
    return res

@app.get("/api/history")
@app.get("/history")
def get_search_history(limit: int = 50):
    """Retrieve stored search / command history."""
    return {"history": memory.get_search_history(limit=limit)}

@app.delete("/api/history/{item_id}")
@app.delete("/history/{item_id}")
def delete_search_item(item_id: int):
    """Delete a single search history item by ID."""
    memory.delete_search(item_id)
    return {"success": True, "deleted_id": item_id}

@app.delete("/api/history")
@app.delete("/history")
def clear_search_history():
    """Clear all stored search history."""
    memory.clear_search_history()
    return {"success": True, "message": "Search history cleared."}

@app.get("/memory")
@app.get("/api/memory")
def get_memory():
    """Retrieve all stored user preferences."""
    return {"preferences": memory.list_all(), "recent_history": memory.get_recent_history(5)}

@app.post("/memory")
@app.post("/api/memory")
def set_memory(req: MemoryRequest):
    """Store a key-value preference."""
    memory.set(req.key, req.value)
    return {"success": True, "key": req.key, "value": req.value}

# Mount static folder if exists
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static_assets")


# ─── Terminal CLI REPL ──────────────────────────────────────────────────────────

def run_cli():
    from rich.console import Console
    from rich.panel import Panel
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import InMemoryHistory

    console = Console()
    session = PromptSession(history=InMemoryHistory())

    header = """[bold cyan]✦ JARVIS[/bold cyan] — Futuristic Personal AI Assistant
[dim]Type [bold white]/help[/bold white] for commands or [bold white]/exit[/bold white] to quit.[/dim]"""
    console.print(Panel(header, border_style="cyan", expand=False))

    while True:
        try:
            user_input = session.prompt("\nYou: ").strip()
            if not user_input:
                continue

            if user_input.lower() in ["/exit", "exit", "quit", ":q"]:
                console.print("[dim]Jarvis standing down. Goodbye, Sir.[/dim]")
                break

            elif user_input.lower() == "/clear":
                console.clear()
                continue

            elif user_input.lower() == "/help":
                help_text = """
[bold cyan]Commands:[/bold cyan]
• [bold white]/tools[/bold white]  - View active tools
• [bold white]/memory[/bold white] - View stored user preferences
• [bold white]/clear[/bold white]  - Clear screen
• [bold white]/exit[/bold white]   - Exit Jarvis
"""
                console.print(Panel(help_text, title="Help", border_style="dim"))
                continue

            elif user_input.lower() == "/tools":
                tools_list = "\n".join([f"• [bold green]{t.name}[/bold green]: {t.description}" for t in agent.tools])
                console.print(Panel(tools_list, title="Active Tools", border_style="cyan"))
                continue

            elif user_input.lower() == "/memory":
                prefs = memory.list_all()
                if prefs:
                    pref_str = "\n".join([f"• [bold]{k}[/bold]: {v}" for k, v in prefs.items()])
                else:
                    pref_str = "[dim]No stored preferences yet. Tell Jarvis 'remember that I prefer Python'.[/dim]"
                console.print(Panel(pref_str, title="Memory Preferences", border_style="magenta"))
                continue

            # Process with Agent
            result = agent.handle_message(user_input, confirmed=False)
            response_text = result.get("response", "")

            # Check if confirmation required for destructive command
            if "CONFIRMATION_REQUIRED:" in response_text:
                console.print(f"[bold yellow]⚠️  {response_text}[/bold yellow]")
                confirm = session.prompt("Execute? [y/N]: ").strip().lower()
                if confirm in ["y", "yes"]:
                    result = agent.handle_message(user_input, confirmed=True)
                    response_text = result.get("response", "")
                else:
                    response_text = "Operation cancelled."

            # Output response
            tool_used = result.get("tool_executed")
            if tool_used:
                console.print(f"[dim cyan]⚙  Executed tool: [{tool_used}][/dim cyan]")
            
            console.print(f"\n[bold cyan]Jarvis:[/bold cyan] {response_text}")

        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Session terminated.[/dim]")
            break

def start_server(host: str = "0.0.0.0", port: int = 8000):
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    if "--cli" in sys.argv or "-c" in sys.argv:
        run_cli()
    else:
        server_cfg = config.get("server", {})
        host = os.getenv("HOST", server_cfg.get("host", "0.0.0.0"))
        port = int(os.getenv("PORT", server_cfg.get("port", 8000)))
        start_server(host=host, port=port)
