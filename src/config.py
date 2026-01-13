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
from dotenv import load_dotenv

# Automatically load .env file from project root if it exists
# In production (Streamlit Cloud), use environment variables instead
load_dotenv()


class Config:
    """
    Application configuration class.
    
    All settings are read from environment variables with sensible defaults.
    For local development, create a .env file in the project root.
    For production, set environment variables in your deployment platform.
    
    Attributes:
        TMDB_API_KEY (str): API key for The Movie Database (TMDB) API
        DATA_PATH (str): Path to data directory (default: "data/")
        CACHE_PATH (str): Path to cache directory (default: "cache/")
        PORT (int): Port number for local development (default: 8501)
        DEBUG (bool): Enable debug mode (default: True)
    """
    TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
    DATA_PATH = os.getenv("DATA_PATH", "data/")
    CACHE_PATH = os.getenv("CACHE_PATH", "cache/")
    PORT = int(os.getenv("PORT", 8501))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

    @classmethod
    def validate(cls):
        """
        Validate that required configuration is set.
        
        Raises:
            ValueError: If TMDB_API_KEY is not set
            
        Example:
            >>> Config.validate()
            # Raises ValueError if TMDB_API_KEY is missing
        """
        if not cls.TMDB_API_KEY:
            raise ValueError(
                "TMDB_API_KEY not set in environment! "
                "Please set it in your .env file or environment variables."
            )

