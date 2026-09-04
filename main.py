"""
Jarvis — Minimal Local Personal AI Assistant
Unified Entrypoint
"""
import sys
import os

# Add root directory to Python path
sys.path.insert(0, os.path.abspath("."))

from backend.main import run_cli, start_server, config

if __name__ == "__main__":
    if "--cli" in sys.argv or "-c" in sys.argv:
        run_cli()
    else:
        server_cfg = config.get("server", {})
        host = os.getenv("HOST", server_cfg.get("host", "0.0.0.0"))
        port = int(os.getenv("PORT", server_cfg.get("port", 8000)))
        print(f"[+] Starting Jarvis Web Server on http://{host}:{port} (Local: http://127.0.0.1:{port})")
        print("  To launch Terminal CLI instead, run: python main.py --cli\n")
        start_server(host=host, port=port)
