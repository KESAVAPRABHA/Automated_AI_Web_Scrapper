"""
pytest configuration — makes the project root importable during tests.
"""
import sys
from pathlib import Path

# Add project root to sys.path so 'from scraper.crawler import ...' works
sys.path.insert(0, str(Path(__file__).parent.parent))
