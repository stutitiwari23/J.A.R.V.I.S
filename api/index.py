import sys
import os
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).parent.parent.resolve()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Import the main FastAPI application
from backend.main import app

# Vercel ASGI serverless handler
# The 'app' object is automatically recognized by @vercel/python
