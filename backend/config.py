import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
env_path = ROOT_DIR / ".env"
load_dotenv(dotenv_path=env_path)
load_dotenv()

key_raw = os.getenv("GROQ_API_KEY", "").strip()
key_detected = bool(key_raw and key_raw.lower() not in ["put_your_groq_api_key_here", "your_groq_api_key_here", "your_api_key_here", "none", ""])
print(f"[AI] Groq API key detected: {'YES' if key_detected else 'NO'}")

CONFIG_PATH = ROOT_DIR / "config.yaml"

def load_config():
    """Load configuration from config.yaml with environment variable overrides."""
    cfg = {
        "assistant": {"name": "Jarvis"},
        "model": {"provider": "groq", "name": os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"), "temperature": 0.7},
        "tools": {"calculator": True, "web_search": True, "files": True, "shell": True},
        "memory": {"enabled": True},
        "server": {"host": "0.0.0.0", "port": 8000}
    }
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            file_cfg = yaml.safe_load(f)
            if file_cfg:
                cfg.update(file_cfg)

    # Apply environment variable overrides
    if "model" in cfg:
        if os.getenv("GROQ_MODEL"):
            cfg["model"]["name"] = os.getenv("GROQ_MODEL")
        cfg["model"]["provider"] = "groq"

    return cfg

config = load_config()
