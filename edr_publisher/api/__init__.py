"""API route handlers for EDR API."""

from .edr_routes import router, initialize_data_accessor

__all__ = ["router", "initialize_data_accessor"]

