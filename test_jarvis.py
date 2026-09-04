"""
Jarvis Complete Verification Test Suite
Tests Google Gemini Integration, all tools, safety constraints, memory, and central agent loop.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath("."))

def sep(title):
    print("\n" + "=" * 60)
    print(f"  [+] {title}")
    print("=" * 60)

def check(label, condition, detail=""):
    status = "[PASS]" if condition else "[FAIL]"
    print(f"  {status} {label}" + (f" -> {detail}" if detail else ""))
    assert condition, f"Assertion failed: {label}"

def run_tests():
    sep("1. GOOGLE GEMINI CONFIGURATION")
    from backend.config import config
    from backend.ai import AIClient
    
    check("Config model provider is gemini", config.get("model", {}).get("provider") == "gemini")
    check("Config model name is set", bool(config.get("model", {}).get("name")))

    ai_client = AIClient()
    check("AIClient initializes properly", ai_client is not None)
    check("AIClient model configured to gemini", "gemini" in ai_client.model_name)

    sep("2. CALCULATOR TOOL")
    from backend.tools.calculator import calculate
    r1 = calculate("25 * 48")
    check("Multiply 25 * 48 = 1200", r1 == "1200", f"result={r1}")

    r2 = calculate("15% of 800")
    check("Percentage 15% of 800 = 120", "120" in r2, f"result={r2}")

    r3 = calculate("5 km to meters")
    check("Unit conversion 5 km = 5000 meters", "5000" in r3, f"result={r3}")

    r4 = calculate("sqrt(144) + 10")
    check("Math functions sqrt(144) + 10 = 22", r4 == "22", f"result={r4}")

    sep("3. SAFE WORKSPACE FILE TOOL")
    from backend.tools.files import create_file, read_file, list_files, _resolve_safe_path
    c_res = create_file("test_workspace_note.txt", "Jarvis minimal storage test content")
    check("Create file", "Successfully" in c_res, c_res)

    r_res = read_file("test_workspace_note.txt")
    check("Read file matches content", "Jarvis minimal storage test content" in r_res)

    l_res = list_files(".")
    check("List files contains note", "test_workspace_note.txt" in l_res)

    # Security test: directory traversal outside workspace
    traversal_blocked = False
    try:
        _resolve_safe_path("../../outside_secret.txt")
    except PermissionError:
        traversal_blocked = True
    check("Directory traversal outside workspace blocked", traversal_blocked)

    # Clean up test file
    test_p = Path("test_workspace_note.txt")
    if test_p.exists(): test_p.unlink()

    sep("4. SAFE SHELL TOOL & DESTRUCTIVE COMMAND GATING")
    from backend.tools.shell import run_shell, is_destructive_command
    s_safe = run_shell("echo Jarvis Safe Shell Test")
    check("Safe command executes", "Jarvis Safe Shell Test" in s_safe, s_safe)

    check("Detect 'rm -rf' as destructive", is_destructive_command("rm -rf /"))
    check("Detect 'del' as destructive", is_destructive_command("del /f /q C:\\test"))
    check("Detect 'format' as destructive", is_destructive_command("format D:"))

    s_destructive = run_shell("rm -rf project/", confirmed=False)
    check("Destructive command requires confirmation", "CONFIRMATION_REQUIRED" in s_destructive)

    sep("4b. SYSTEM DIAGNOSTICS TOOL")
    from backend.tools.system import get_system_info
    sys_res = get_system_info()
    check("System info returned metrics", "OS:" in sys_res and "Architecture:" in sys_res, sys_res.splitlines()[0])

    sep("5. SQLITE MEMORY & CONTEXT SYSTEM")
    from backend.memory import memory
    memory.set("preferred_language", "Python")
    memory.set("user_name", "Tony")

    check("Retrieve user preference", memory.get("preferred_language") == "Python")
    check("Retrieve user name", memory.get("user_name") == "Tony")

    all_prefs = memory.list_all()
    check("List all preferences contains keys", "preferred_language" in all_prefs and "user_name" in all_prefs)

    relevant = memory.find_relevant("What is my preferred_language?")
    check("Find relevant memory matches preference", len(relevant) > 0 and "Python" in relevant[0])

    sep("6. UNIFIED CENTRAL AGENT — USER SCENARIOS")
    from backend.agent import agent
    
    # Calculation through agent
    agent_calc = agent.handle_message("calculate 25 * 48")
    check("Agent handles calculation", "1200" in agent_calc["response"], f"resp={agent_calc['response']}")
    check("Agent recorded calculator tool", agent_calc["tool_executed"] == "calculator")

    # Memory through agent
    agent_mem = agent.handle_message("remember that I prefer TypeScript")
    check("Agent stores memory", "remembered" in agent_mem["response"].lower())
    check("Memory updated", memory.get("preference") == "TypeScript")

    # Shell confirmation through agent
    agent_shell = agent.handle_message("run command: del important.txt")
    check("Agent flags dangerous shell for confirmation", "CONFIRMATION_REQUIRED" in agent_shell["response"])

    sep("6b. VERIFY 7 USER SPECIFICATION SCENARIOS")

    # TEST 1: General Question
    test_1 = agent.handle_message("What is artificial intelligence?")
    check("TEST 1: General Question ('What is artificial intelligence?')", len(test_1["response"]) > 30 and "intelligence" in test_1["response"].lower(), test_1["response"][:60])

    # TEST 2: Voice Question
    test_2 = agent.handle_message("Jarvis, explain machine learning in simple words.")
    check("TEST 2: Voice Question ('Jarvis, explain machine learning in simple words.')", len(test_2["response"]) > 30, test_2["response"][:60])

    # TEST 3: Greeting
    test_3a = agent.handle_message("Hey Jarvis.")
    check("TEST 3a: Greeting ('Hey Jarvis.')", test_3a["response"] == "Hello ma'am, how can I help you?", test_3a["response"])
    test_3b = agent.handle_message("Hello Jarvis")
    check("TEST 3b: Greeting ('Hello Jarvis')", test_3b["response"] == "Hello ma'am, how can I help you?", test_3b["response"])

    # TEST 4: Calculation
    test_4 = agent.handle_message("What is 25 percent of 800?")
    check("TEST 4: Calculation ('What is 25 percent of 800?')", "200" in test_4["response"] and ("25 percent of 800 is 200" in test_4["response"] or "200" in test_4["response"]), test_4["response"])

    # TEST 5: Current Information
    test_5 = agent.handle_message("What are the latest developments in AI?")
    check("TEST 5: Current Information ('What are the latest developments in AI?')", test_5.get("tool_executed") == "web_search" or len(test_5["response"]) > 25, f"tool={test_5.get('tool_executed')}")

    # TEST 6: Context Follow-up
    agent.handle_message("What is machine learning?")
    test_6 = agent.handle_message("What are its main types?")
    check("TEST 6: Follow-up ('What are its main types?')", len(test_6["response"]) > 20 and any(w in test_6["response"].lower() for w in ["supervised", "learning", "types"]), test_6["response"][:60])

    # TEST 7: Programming
    test_7 = agent.handle_message("Write a Python function to check whether a number is prime.")
    check("TEST 7: Programming ('Write a Python function to check whether a number is prime.')", "def is_prime" in test_7["response"] and "```" in test_7["response"], "Code block generated")

    sep("7. GMAIL & CALENDAR INTEGRATIONS")
    from backend.integrations.gmail import gmail_client
    from backend.integrations.calendar import calendar_client

    email_unread = gmail_client.get_unread_emails()
    check("Gmail unread handler responds", len(email_unread) > 0)

    email_send_confirm = gmail_client.send_email("test@example.com", "Meeting", "Hello", confirmed=False)
    check("Gmail send requires confirmation", "CONFIRMATION_REQUIRED" in email_send_confirm)

    cal_events = calendar_client.get_events()
    check("Calendar events responds", len(cal_events) > 0)

    cal_create_confirm = calendar_client.create_event("AI Standup", "Tomorrow 10am", confirmed=False)
    check("Calendar create requires confirmation", "CONFIRMATION_REQUIRED" in cal_create_confirm)

    sep("8. FASTAPI BACKEND ENDPOINTS")
    from fastapi.testclient import TestClient
    from backend.main import app
    client = TestClient(app)

    res_health = client.get("/api/health")
    check("GET /api/health returns 200", res_health.status_code == 200)
    check("GET /api/health status is ok", res_health.json().get("status") == "ok")

    res_ui = client.get("/")
    check("GET / serves Jarvis HUD HTML", res_ui.status_code == 200 and "J.A.R.V.I.S" in res_ui.text)

    res_status = client.get("/status")
    check("GET /status returns 200", res_status.status_code == 200)
    check("Status reports online", res_status.json().get("status") == "online")

    res_tools = client.get("/tools")
    check("GET /tools returns 200", res_tools.status_code == 200)
    check("Tools returned", len(res_tools.json()) >= 4)

    # Test /api/chat with greeting
    res_greet = client.post("/api/chat", json={"message": "Hello Jarvis"})
    check("POST /api/chat greeting returns 200", res_greet.status_code == 200)
    check("POST /api/chat answer key present", res_greet.json().get("answer") == "Hello ma'am, how can I help you?")

    # Test empty message validation
    res_empty = client.post("/api/chat", json={"message": ""})
    check("POST /api/chat validates empty message (400)", res_empty.status_code == 400)

    # Test calculation
    res_chat = client.post("/api/chat", json={"message": "calculate 100 / 4"})
    check("POST /api/chat returns 200", res_chat.status_code == 200)
    check("Chat calculation output is 25", "25" in res_chat.json().get("answer", ""))

    sep("ALL JARVIS GOOGLE GEMINI INTEGRATION TESTS PASSED SUCCESSFULLY")
    print("  JARVIS with Google Gemini brain is verified and ready.\n")

if __name__ == "__main__":
    run_tests()
