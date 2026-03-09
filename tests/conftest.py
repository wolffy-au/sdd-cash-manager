"""Test configuration shared fixtures and helpers."""
import pathlib
import sys

ROOT_DIR = pathlib.Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
