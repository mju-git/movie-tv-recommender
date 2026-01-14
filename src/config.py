"""
Centralized configuration management for the Movie & TV Recommender System.

This module handles all configuration settings, reading from environment variables
for security and flexibility. Supports both local development (.env file) and
production deployment (environment variables).

Usage:
    from src.config import Config
    Config.validate()  # Check required settings at startup
"""
import os

# Try to load .env file from project root if it exists (optional)
# In production (Streamlit Cloud), use environment variables instead
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed - fine for production (uses env vars directly)
    pass


class Config:
    """
    Application configuration class.
    
    All settings are read from environment variables with sensible defaults.
    For local development, create a .env file in the project root.
    For production, set environment variables in your deployment platform.
    
    Attributes:
        TMDB_API_KEY (str): API key for The Movie Database (TMDB) API v3 (query parameter method)
        TMDB_ACCESS_TOKEN (str): Access token for TMDB API v4 (Bearer token method, preferred)
        DATA_PATH (str): Path to data directory (default: "data/")
        CACHE_PATH (str): Path to cache directory (default: "cache/")
        PORT (int): Port number for local development (default: 8501)
        DEBUG (bool): Enable debug mode (default: True)
    """
    TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
    TMDB_ACCESS_TOKEN = os.getenv("TMDB_ACCESS_TOKEN", "")
    DATA_PATH = os.getenv("DATA_PATH", "data/")
    CACHE_PATH = os.getenv("CACHE_PATH", "cache/")
    PORT = int(os.getenv("PORT", 8501))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    @classmethod
    def get_tmdb_auth(cls):
        """
        Get TMDB authentication method (Bearer token preferred, falls back to API key).
        
        Returns:
            tuple: (headers dict, use_bearer bool) for making requests
        """
        if cls.TMDB_ACCESS_TOKEN:
            return {"Authorization": f"Bearer {cls.TMDB_ACCESS_TOKEN}"}, True
        elif cls.TMDB_API_KEY:
            return {}, False
        else:
            return {}, False

    @classmethod
    def validate(cls):
        """
        Validate that required configuration is set.
        
        Raises:
            ValueError: If neither TMDB_ACCESS_TOKEN nor TMDB_API_KEY is set
            
        Example:
            >>> Config.validate()
            # Raises ValueError if neither token nor key is set
        """
        if not cls.TMDB_ACCESS_TOKEN and not cls.TMDB_API_KEY:
            raise ValueError(
                "TMDB authentication not set! "
                "Please set either TMDB_ACCESS_TOKEN (Bearer token, preferred) "
                "or TMDB_API_KEY (API key) in your .env file or environment variables."
            )

