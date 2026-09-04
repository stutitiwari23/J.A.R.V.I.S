import re
from backend.config import config
from backend.ai import AIClient
from backend.tools import get_enabled_tools, ALL_TOOLS
from backend.memory import memory

SYSTEM_PROMPT = """You are JARVIS, a personal AI assistant.

You are intelligent, calm, concise, professional and helpful.

Address the user as 'ma'am' when appropriate.

Answer questions directly.

Do not unnecessarily explain that you are an AI.

For simple questions, give concise answers.

For complex questions, provide a clear explanation.

For calculations, provide accurate results.

For coding questions, provide practical solutions.

For casual conversation, respond naturally."""

class Agent:
    def __init__(self):
        self.assistant_name = config.get("assistant", {}).get("name", "Jarvis")
        self.ai = AIClient()
        self.tools = get_enabled_tools(config.get("tools", {}))
        self.tools_map = {t.name: t for t in self.tools}
        self.system_prompt = SYSTEM_PROMPT

    def handle_message(self, user_message: str, confirmed: bool = False) -> dict:
        """
        Main Unified Agent Execution Loop:
        1. Check exact/approximate greeting triggers ("Hey Jarvis", "Hello Jarvis", etc.)
        2. Check explicit memory commands (e.g. 'remember that...')
        3. Build conversation context from recent session history
        4. Send to Gemini brain (which executes search grounding / tools and synthesizes answer)
        5. Store history and return structured result
        """
        user_message = user_message.strip()
        if not user_message:
            return {"response": "Please enter a message.", "tool_executed": None, "tool_output": None}

        print(f"[+] Received message: '{user_message}'")

        # 1. Special Greeting Behavior (Case-insensitive)
        clean_greet = re.sub(r'[^a-zA-Z\s]', '', user_message.lower()).strip()
        if clean_greet in ["hey jarvis", "hello jarvis", "hi jarvis", "jarvis", "hey jarvis how are you", "hi jarvis how are you"]:
            greeting_resp = "Hello ma'am, how can I help you?"
            print(f"[+] Greeting triggered: '{greeting_resp}'")
            memory.add_history("user", user_message)
            memory.add_history("assistant", greeting_resp)
            return {"response": greeting_resp, "tool_executed": None, "tool_output": None}

        # 1b. Fast Local Tool: Calculator / Math
        clean_msg = user_message.lower().strip()
        calc_match = re.match(r'^(?:calculate|compute)\s+(.+)', user_message, re.IGNORECASE)
        is_pct_calc = any(k in clean_msg for k in ["percent of", "% of"])
        if calc_match or is_pct_calc or (clean_msg.startswith("what is") and any(op in clean_msg for op in ["divided by", "times", "plus", "minus", "%", "+", "-", "*", "/"])):
            expr = calc_match.group(1).strip() if calc_match else user_message
            from backend.tools.calculator import calculate
            ans = calculate(expr)
            if ans and not str(ans).startswith("Calculation error"):
                resp = str(ans)
                if not any(k in resp for k in ["is", "="]) and not resp.endswith("."):
                    resp = f"The result is {resp}."
                memory.add_history("user", user_message)
                memory.add_history("assistant", resp)
                return {"response": resp, "answer": resp, "tool_executed": "calculator", "tool_output": ans}

        # 1c. Fast Local Tool: Shell Command Execution
        shell_match = re.search(r'(?:run command|execute command|shell command|run shell)\s*:\s*(.+)', user_message, re.IGNORECASE)
        if shell_match:
            cmd = shell_match.group(1).strip()
            from backend.tools.shell import run_shell
            res = run_shell(cmd, confirmed=confirmed)
            memory.add_history("user", user_message)
            memory.add_history("assistant", res)
            return {"response": res, "answer": res, "tool_executed": "shell_command", "tool_output": res}

        # 2. Handle explicit memory store intent
        mem_store_match = re.search(r'remember\s+that\s+(.+)', user_message, re.IGNORECASE)
        if mem_store_match:
            mem_text = mem_store_match.group(1).strip()
            if "prefer" in mem_text:
                val = mem_text.split("prefer", 1)[-1].strip()
                memory.set("preference", val)
            elif "is" in mem_text:
                parts = mem_text.split("is", 1)
                memory.set(parts[0].strip().replace("my ", ""), parts[1].strip())
            else:
                memory.set("note", mem_text)
            resp = "I have remembered that, ma'am."
            memory.add_history("user", user_message)
            memory.add_history("assistant", resp)
            return {"response": resp, "tool_executed": "memory", "tool_output": mem_text}

        # 2b. Handle memory recall query
        if any(q in user_message.lower() for q in ["what is my preference", "what do i prefer", "what programming language do i prefer", "what language do i prefer"]):
            pref = memory.get("preference") or memory.get("preferred_language")
            if pref:
                resp = f"You prefer {pref}, ma'am."
            else:
                all_p = memory.list_all()
                if all_p:
                    items = [f"{k}: {v}" for k, v in all_p.items()]
                    resp = f"Stored preferences:\n" + "\n".join(items)
                else:
                    resp = "You haven't told me your preferences yet, ma'am."
            memory.add_history("user", user_message)
            memory.add_history("assistant", resp)
            return {"response": resp, "tool_executed": "memory", "tool_output": pref}

        # 3. Check memory for relevant preferences
        relevant_prefs = memory.find_relevant(user_message)
        context_prefix = ""
        if relevant_prefs:
            context_prefix = f"[Stored user preferences: {', '.join(relevant_prefs)}]\n"

        # 4. Build messages list with recent conversation history
        recent_history = memory.get_recent_history(limit=8)
        messages = [{"role": "system", "content": self.system_prompt}]
        for h in recent_history:
            messages.append({"role": h["role"], "content": h["content"]})

        current_content = f"{context_prefix}{user_message}" if context_prefix else user_message
        messages.append({"role": "user", "content": current_content})

        # Save user message to memory history
        memory.add_history("user", user_message)

        # 5. Call Gemini Brain
        print(f"[+] Calling Gemini Brain service...")
        ai_res = self.ai.chat(messages, tools_map=self.tools_map, confirmed=confirmed)

        final_response = ai_res.get("content", "I am standing by, ma'am.")
        executed_tool = ai_res.get("tool_executed")
        tool_output = ai_res.get("tool_output")

        print(f"[+] Returning response: '{final_response[:100]}...'")

        # Save assistant message to memory history
        memory.add_history("assistant", final_response)

        return {
            "response": final_response,
            "answer": final_response,
            "tool_executed": executed_tool,
            "tool_output": tool_output
        }

# Shared singleton agent instance
agent = Agent()
