import subprocess
import re

# Patterns indicating potentially destructive shell commands
DESTRUCTIVE_PATTERNS = [
    r'\brm\b', r'\bdel\b', r'\berase\b', r'\bformat\b',
    r'\bshutdown\b', r'\breboot\b', r'\brmdir\b', r'\brd\b',
    r'\bmkfs\b', r'\bfdisk\b', r'\bdrop\b', r'\btruncate\b',
    r'>\s*/dev/', r'Remove-Item\s+-Recurse'
]

def is_destructive_command(command: str) -> bool:
    """Check if command contains potentially destructive operations."""
    for pattern in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False

def run_shell(command: str, confirmed: bool = False) -> str:
    """
    Execute a shell command safely.
    If the command is potentially destructive and not confirmed, abort with a warning.
    """
    command = command.strip()
    
    if is_destructive_command(command) and not confirmed:
        return f"CONFIRMATION_REQUIRED: Dangerous command detected ('{command}'). Please confirm to execute."

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd="."
        )
        output = result.stdout.strip() or result.stderr.strip() or "Command completed with no output."
        return output
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Error executing shell command: {str(e)}"
