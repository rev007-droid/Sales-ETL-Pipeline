"""
dependencies.py
---------------
Reusable FastAPI dependencies for database sessions, authentication (extensible),
and request validation.
"""

from typing import Generator
from sqlalchemy.orm import Session
from backend.app.database import get_db

# Re-export get_db for clean modular imports
__all__ = ["get_db"]
