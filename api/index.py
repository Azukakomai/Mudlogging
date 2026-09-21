import sys
import os

# Add root directory to sys.path so app.py, parser.py, and engine.py are importable
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import server as app
