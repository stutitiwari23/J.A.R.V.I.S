from backend.tools.calculator import calculate
from backend.tools.search import search_web
from backend.tools.files import read_file, create_file, append_file, list_files
from backend.tools.system import get_system_info
from backend.tools.shell import run_shell, is_destructive_command
from backend.integrations.gmail import gmail_client
from backend.integrations.calendar import calendar_client

class Tool:
    def __init__(self, name: str, description: str, function):
        self.name = name
        self.description = description
        self.function = function

    def execute(self, *args, **kwargs):
        return self.function(*args, **kwargs)

    def run(self, *args, **kwargs):
        return self.function(*args, **kwargs)

# Available tools catalog
ALL_TOOLS = {
    "calculator": Tool(
        name="calculator",
        description="Calculate math expressions, percentages, and conversions. E.g. '25 * 48', '15% of 800', '5 km to m'",
        function=calculate
    ),
    "web_search": Tool(
        name="web_search",
        description="Search the live internet for recent information, news, and queries.",
        function=search_web
    ),
    "read_file": Tool(
        name="read_file",
        description="Read the text content of a file in the workspace.",
        function=read_file
    ),
    "create_file": Tool(
        name="create_file",
        description="Create or overwrite a file in the workspace with content.",
        function=create_file
    ),
    "append_file": Tool(
        name="append_file",
        description="Append text to an existing file in the workspace.",
        function=append_file
    ),
    "list_files": Tool(
        name="list_files",
        description="List files in a workspace directory.",
        function=list_files
    ),
    "system_info": Tool(
        name="system_info",
        description="Get operating system, CPU, memory, and runtime metrics.",
        function=get_system_info
    ),
    "run_shell": Tool(
        name="run_shell",
        description="Run safe terminal commands (e.g. git status, python --version, dir).",
        function=run_shell
    ),
    "gmail_unread": Tool(
        name="gmail_unread",
        description="Check unread emails from Gmail inbox.",
        function=lambda **kwargs: gmail_client.get_unread_emails()
    ),
    "gmail_send": Tool(
        name="gmail_send",
        description="Send an email to a recipient with confirmation check.",
        function=lambda to, subject, body, confirmed=False, **kwargs: gmail_client.send_email(to, subject, body, confirmed)
    ),
    "calendar_events": Tool(
        name="calendar_events",
        description="List today's and upcoming calendar events.",
        function=lambda **kwargs: calendar_client.get_events()
    ),
    "calendar_create": Tool(
        name="calendar_create",
        description="Create a calendar event with confirmation check.",
        function=lambda title, date_time, confirmed=False, **kwargs: calendar_client.create_event(title, date_time, confirmed)
    )
}

def get_enabled_tools(tools_config: dict) -> list[Tool]:
    """Return enabled tool objects based on config.yaml."""
    enabled = []
    if tools_config.get("calculator", True):
        enabled.append(ALL_TOOLS["calculator"])
    if tools_config.get("web_search", True):
        enabled.append(ALL_TOOLS["web_search"])
    if tools_config.get("files", True):
        enabled.extend([ALL_TOOLS["read_file"], ALL_TOOLS["create_file"], ALL_TOOLS["append_file"], ALL_TOOLS["list_files"]])
    if tools_config.get("system_info", True):
        enabled.append(ALL_TOOLS["system_info"])
    if tools_config.get("shell", True):
        enabled.append(ALL_TOOLS["run_shell"])
    # Integrations
    enabled.extend([ALL_TOOLS["gmail_unread"], ALL_TOOLS["gmail_send"], ALL_TOOLS["calendar_events"], ALL_TOOLS["calendar_create"]])
    return enabled
