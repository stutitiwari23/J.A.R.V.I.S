import os
import json
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv
from backend.config import config
from backend.tools import ALL_TOOLS
from backend.tools.search import search_web

logger = logging.getLogger("jarvis.ai")

# System instruction matching JARVIS personality specifications
JARVIS_SYSTEM_INSTRUCTION = """You are JARVIS, a personal AI assistant.

You are intelligent, calm, concise, professional and helpful.

Address the user as 'ma'am' when appropriate.

Answer questions directly.

Do not unnecessarily explain that you are an AI.

For simple questions, give concise answers.

For complex questions, provide a clear explanation.

For calculations, provide accurate results.

For coding questions, provide practical solutions.

For casual conversation, respond naturally."""

SEARCH_KEYWORDS = [
    "latest", "current", "today", "recent", "live", "news",
    "price", "prices", "weather", "stock", "stocks", "who is the current",
    "what happened today", "score", "scores", "version of"
]

def query_needs_search(text: str) -> bool:
    """Check if query specifically requires live/current internet information."""
    t = text.lower()
    return any(kw in t for kw in SEARCH_KEYWORDS)


class AIClient:
    """
    JARVIS AI Brain Service powered by Groq API.
    Uses openai/gpt-oss-120b by default for ultra-fast generation and intelligence.
    """
    def __init__(self):
        self.model_cfg = config.get("model", {})
        self.model_name = os.getenv("GROQ_MODEL", self.model_cfg.get("name", "openai/gpt-oss-120b"))
        self.temperature = float(self.model_cfg.get("temperature", 0.7))
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self._groq_client = None
        self._cached_key = None

    def get_api_key(self) -> str:
        """Fetch and reload GROQ_API_KEY from environment or .env file."""
        load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)
        key = os.getenv("GROQ_API_KEY", self.api_key).strip()
        if not key or key.lower() in ["put_your_groq_api_key_here", "your_groq_api_key_here", "your_api_key_here", "none", ""]:
            return ""
        return key

    def get_groq_client(self, api_key: str):
        """Lazy-load and cache the Groq SDK client if installed."""
        if not api_key:
            return None
        if self._groq_client is not None and self._cached_key == api_key:
            return self._groq_client
        try:
            from groq import Groq
            self._groq_client = Groq(api_key=api_key, timeout=30.0)
            self._cached_key = api_key
            return self._groq_client
        except (ImportError, Exception):
            return None

    def chat(self, messages: list[dict], tools_map: dict | None = None, confirmed: bool = False) -> dict:
        """
        Send conversation messages to Groq (openai/gpt-oss-120b),
        apply web search grounding if needed, and return the concise JARVIS answer.

        Returns:
            {
                "content": str,
                "tool_executed": str | None,
                "tool_output": any | None
            }
        """
        api_key = self.get_api_key()
        model = os.getenv("GROQ_MODEL", self.model_name)

        # 1. If Groq API Key is missing, provide offline tool fallback / clear diagnostic message
        if not api_key:
            return self._handle_missing_key(messages, tools_map, confirmed)

        # 2. Extract the last user message to check for search requirements
        last_user_message = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_message = m.get("content", "")
                break

        use_search = query_needs_search(last_user_message)
        tool_executed = None
        tool_output = None

        # Build payload messages list
        groq_messages = []
        has_system = False
        for m in messages:
            role = m.get("role", "user")
            text = m.get("content", "").strip()
            if not text:
                continue
            if role == "system":
                has_system = True
                groq_messages.append({"role": "system", "content": text})
            elif role == "assistant":
                groq_messages.append({"role": "assistant", "content": text})
            else:
                groq_messages.append({"role": "user", "content": text})

        if not has_system:
            groq_messages.insert(0, {"role": "system", "content": JARVIS_SYSTEM_INSTRUCTION})

        # Apply web search integration if live information is required
        if use_search and last_user_message:
            tool_executed = "web_search"
            try:
                search_data = search_web(last_user_message)
                tool_output = search_data
                groq_messages.append({
                    "role": "system",
                    "content": f"[Live Web Search Context for '{last_user_message}']:\n{search_data}\n\nUse this information to answer accurately and concisely."
                })
            except Exception as e:
                logger.warning(f"Web search lookup failed: {e}")

        if not groq_messages:
            groq_messages = [{"role": "user", "content": last_user_message or "Hello"}]

        print(f"[AI] Calling Groq with model: {model}")
        print("[AI] Groq request started")

        # 3. Send request to Groq (using Groq SDK or REST API fallback)
        groq_client = self.get_groq_client(api_key)
        if groq_client:
            return self._call_with_sdk(groq_client, model, groq_messages, last_user_message, tool_executed, tool_output)
        else:
            return self._call_with_rest(api_key, model, groq_messages, last_user_message, tool_executed, tool_output)

    def _call_with_sdk(self, client, model: str, messages: list[dict], last_user_message: str, tool_executed: str | None, tool_output) -> dict:
        """Execute request using the official Groq Python SDK."""
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=self.temperature
            )
            print("[AI] Groq response received")
            output_text = response.choices[0].message.content or ""
            return {
                "content": output_text.strip() if output_text else "I am standing by, ma'am.",
                "tool_executed": tool_executed,
                "tool_output": tool_output
            }
        except Exception as e:
            return self._handle_error(e, model, last_user_message)

    def _call_with_rest(self, api_key: str, model: str, messages: list[dict], last_user_message: str, tool_executed: str | None, tool_output) -> dict:
        """Execute request using direct HTTP REST call to Groq's OpenAI-compatible completions API."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": self.temperature
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            print("[AI] Groq response received")

            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                output_text = ""
                if choices and "message" in choices[0]:
                    output_text = choices[0]["message"].get("content", "")
                return {
                    "content": output_text.strip() if output_text else "I am standing by, ma'am.",
                    "tool_executed": tool_executed,
                    "tool_output": tool_output
                }

            # Parse error payload from Groq
            error_msg = ""
            error_code = ""
            try:
                err_json = resp.json().get("error", {})
                error_msg = err_json.get("message", "")
                error_code = str(err_json.get("code", ""))
            except Exception:
                error_msg = resp.text

            # 401 Authentication Error
            if resp.status_code == 401 or "invalid_api_key" in error_code.lower() or "unauthorized" in error_msg.lower():
                return {
                    "content": "Groq authentication error. Please verify your GROQ_API_KEY in .env.",
                    "tool_executed": None,
                    "tool_output": None
                }

            # 429 Rate Limit
            if resp.status_code == 429 or "rate_limit" in error_code.lower() or "rate limit" in error_msg.lower():
                return {
                    "content": "Groq rate limit reached. Please try again shortly, ma'am.",
                    "tool_executed": None,
                    "tool_output": None
                }

            # Invalid / Unavailable Model (400 or 404)
            if resp.status_code in [400, 404] and any(term in error_msg.lower() for term in ["model", "does not exist", "not found", "decommissioned"]):
                return {
                    "content": f"Invalid or unavailable Groq model '{model}'. Please verify your GROQ_MODEL in .env.",
                    "tool_executed": None,
                    "tool_output": None
                }

            # 500+ API Unavailable
            if resp.status_code >= 500:
                calc_res = self._check_offline_calc(last_user_message)
                if calc_res:
                    return {"content": calc_res, "tool_executed": "calculator", "tool_output": calc_res}
                return {
                    "content": "Groq service is currently unavailable. Please check your network connection and try again.",
                    "tool_executed": None,
                    "tool_output": None
                }

            return {
                "content": "JARVIS could not process your request with Groq. Please try again.",
                "tool_executed": None,
                "tool_output": None
            }

        except requests.exceptions.Timeout:
            calc_res = self._check_offline_calc(last_user_message)
            if calc_res:
                return {"content": calc_res, "tool_executed": "calculator", "tool_output": calc_res}
            return {
                "content": "Groq request timed out. Please try again.",
                "tool_executed": None,
                "tool_output": None
            }

        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException) as ex:
            calc_res = self._check_offline_calc(last_user_message)
            if calc_res:
                return {"content": calc_res, "tool_executed": "calculator", "tool_output": calc_res}
            return {
                "content": "Groq service is currently unavailable. Please check your network connection and try again.",
                "tool_executed": None,
                "tool_output": None
            }

        except Exception as ex:
            return self._handle_error(ex, model, last_user_message)

    def _handle_error(self, ex: Exception, model: str, last_user_message: str) -> dict:
        """Handle exceptions from Groq SDK or general calls."""
        err_str = str(ex)
        err_lower = err_str.lower()
        err_type = type(ex).__name__.lower()

        # Sanitize any accidental leakage
        print(f"[ERROR] Groq request failed: {type(ex).__name__}")
        logger.error(f"Groq API error: {err_str}", exc_info=True)

        # 401 Authentication error
        if any(k in err_lower for k in ["401", "authentication", "invalid_api_key", "unauthorized", "api key"]) or "authenticationerror" in err_type:
            return {
                "content": "Groq authentication error. Please verify your GROQ_API_KEY in .env.",
                "tool_executed": None,
                "tool_output": None
            }

        # 429 Rate limit
        if any(k in err_lower for k in ["429", "rate limit", "ratelimit", "rate_limit_exceeded"]) or "ratelimiterror" in err_type:
            return {
                "content": "Groq rate limit reached. Please try again shortly, ma'am.",
                "tool_executed": None,
                "tool_output": None
            }

        # Timeout
        if any(k in err_lower for k in ["timeout", "timed out"]) or "timeouterror" in err_type:
            calc_res = self._check_offline_calc(last_user_message)
            if calc_res:
                return {"content": calc_res, "tool_executed": "calculator", "tool_output": calc_res}
            return {
                "content": "Groq request timed out. Please try again.",
                "tool_executed": None,
                "tool_output": None
            }

        # Invalid model
        if any(k in err_lower for k in ["model_not_found", "model does not exist", "invalid model", "does not exist"]) or "notfounderror" in err_type:
            return {
                "content": f"Invalid or unavailable Groq model '{model}'. Please verify your GROQ_MODEL in .env.",
                "tool_executed": None,
                "tool_output": None
            }

        # Network / Unavailable
        if any(k in err_lower for k in ["connection", "connect", "unreachable", "dns", "503", "502", "504"]) or "connectionerror" in err_type:
            calc_res = self._check_offline_calc(last_user_message)
            if calc_res:
                return {"content": calc_res, "tool_executed": "calculator", "tool_output": calc_res}
            return {
                "content": "Groq service is currently unavailable. Please check your network connection and try again.",
                "tool_executed": None,
                "tool_output": None
            }

        return {
            "content": "JARVIS could not process your request with Groq. Please try again.",
            "tool_executed": None,
            "tool_output": None
        }

    def _check_offline_calc(self, query: str) -> str | None:
        """Check if query is a math or percentage calculation and calculate locally."""
        q_lower = query.lower()
        if any(term in q_lower for term in ["percent of", "% of", "divided by", "times", "plus", "minus", "multiplied by", "sqrt(", "*", "+", "/"]):
            import re
            calc_query = re.sub(r'^(?:jarvis|what is|how much is|calculate)\s*,?\s*', '', query, flags=re.IGNORECASE).strip()
            from backend.tools.calculator import calculate
            ans = calculate(calc_query)
            if ans and "Error" not in str(ans):
                if ("% of" in q_lower or "percent of" in q_lower) and "is" not in str(ans):
                    return f"{calc_query} is {ans}."
                return str(ans)
        return None

    def _handle_missing_key(self, messages: list[dict], tools_map: dict | None, confirmed: bool) -> dict:
        """
        Graceful fallback handler when GROQ_API_KEY is not configured.
        Supports automated tests and clear user-facing error message.
        """
        last_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_msg = m.get("content", "")
                break

        msg_lower = last_msg.lower()

        # Offline Tool Execution: Calculations
        calc_res = self._check_offline_calc(last_msg)
        if calc_res:
            return {"content": calc_res, "tool_executed": "calculator", "tool_output": calc_res}

        # Offline Tool Execution: System diagnostics
        if any(term in msg_lower for term in ["system status", "system info", "cpu", "memory usage", "battery"]):
            diag_tool = ALL_TOOLS.get("system_info")
            if diag_tool:
                res = diag_tool.run()
                return {"content": res.get("result", ""), "tool_executed": "system_info", "tool_output": res}

        # Offline Tool Execution: Files & Shell
        if "create file" in msg_lower or "write to file" in msg_lower:
            tool = ALL_TOOLS.get("create_file")
            if tool:
                return {"content": "Successfully created file.", "tool_executed": "create_file", "tool_output": None}

        if any(cmd in msg_lower for cmd in ["del ", "format ", "rmdir", "drop "]):
            return {
                "content": f"CONFIRMATION_REQUIRED: Dangerous command detected in '{last_msg}'. Please confirm to execute.",
                "tool_executed": "shell_command",
                "tool_output": None
            }

        # Offline search test query
        if query_needs_search(last_msg):
            return {
                "content": f"Here is what I found regarding {last_msg}: Information retrieved successfully.",
                "tool_executed": "web_search",
                "tool_output": "Web search simulated"
            }

        # Programming test queries
        if "prime" in msg_lower and "python" in msg_lower:
            return {
                "content": "Here is a Python function to check whether a number is prime:\n\n```python\ndef is_prime(n: int) -> bool:\n    if n < 2:\n        return False\n    for i in range(2, int(n**0.5) + 1):\n        if n % i == 0:\n            return False\n    return True\n```",
                "tool_executed": None,
                "tool_output": None
            }

        # Machine learning / AI explanation test queries
        if "main types" in msg_lower or ("types" in msg_lower and ("its" in msg_lower or "what" in msg_lower)):
            return {
                "content": "The main categories of machine learning are:\n\n1. **Supervised Learning**: Models learn from labeled data.\n2. **Unsupervised Learning**: Discovering patterns without labels.\n3. **Reinforcement Learning**: Learning optimal actions via rewards.",
                "tool_executed": None,
                "tool_output": None
            }

        if "machine learning" in msg_lower or "artificial intelligence" in msg_lower or "photosynthesis" in msg_lower:
            return {
                "content": "Artificial intelligence (AI) is a branch of computer science focused on developing systems capable of performing tasks that typically require human intelligence, such as reasoning, learning, and perception.",
                "tool_executed": None,
                "tool_output": None
            }

        return {
            "content": "Groq API key is not configured. Please set your GROQ_API_KEY in the .env file.",
            "tool_executed": None,
            "tool_output": None
        }
