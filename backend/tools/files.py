import os
from pathlib import Path

WORKSPACE_ROOT = Path(os.getcwd()).resolve()

def _resolve_safe_path(filepath: str) -> Path:
    """Ensure path is within the designated workspace root."""
    target = (WORKSPACE_ROOT / filepath).resolve()
    if not str(target).startswith(str(WORKSPACE_ROOT)):
        raise PermissionError("Access denied: File path is outside the allowed workspace.")
    return target

def read_file(filepath: str) -> str:
    """Read the content of a local file in the workspace."""
    try:
        path = _resolve_safe_path(filepath)
        if not path.exists():
            return f"Error: File not found: {filepath}"
        if not path.is_file():
            return f"Error: {filepath} is not a file."
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"Error reading file: {str(e)}"

def create_file(filepath: str, content: str = "") -> str:
    """Create a new file in the workspace with content."""
    try:
        path = _resolve_safe_path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Successfully created {filepath}"
    except Exception as e:
        return f"Error creating file: {str(e)}"

def append_file(filepath: str, content: str) -> str:
    """Append content to an existing file in the workspace."""
    try:
        path = _resolve_safe_path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n" + content)
        return f"Successfully appended to {filepath}"
    except Exception as e:
        return f"Error appending to file: {str(e)}"

def list_files(directory: str = ".") -> str:
    """List files in a workspace directory."""
    try:
        path = _resolve_safe_path(directory)
        if not path.exists() or not path.is_dir():
            return f"Error: Directory not found: {directory}"
        items = os.listdir(path)
        return f"Files in {directory}:\n" + "\n".join(f"- {item}" for item in items if not item.startswith("."))
    except Exception as e:
        return f"Error listing files: {str(e)}"
