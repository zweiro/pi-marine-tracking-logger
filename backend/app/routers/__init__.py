"""
API Routers

This module exports all API routers for the application.
"""

from app.routers.turtles import router as turtles_router
from app.routers.dives import router as dives_router
from app.routers.samples import router as samples_router

__all__ = ["turtles_router", "dives_router", "samples_router"]
