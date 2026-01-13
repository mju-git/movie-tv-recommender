"""
Streamlit Movie & TV Show Recommender Application.

Main entry point for the recommendation web application. Provides a clean,
professional interface for discovering movies and TV shows based on content
similarity using TF-IDF and cosine similarity.

Features:
    - Content-based recommendations for movies and TV shows
    - Multi-item recommendation mode
    - Genre filtering
    - Analytics dashboard
    - Light/dark theme support
    - Responsive design

Data Sources:
    - Primary: SQLite database (recommended for production)
    - Fallback: Pickle files (for development/testing)

Author: Movie Recommender Team
License: MIT
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import streamlit as st

# CRITICAL: st.set_page_config() MUST be the FIRST Streamlit command
st.set_page_config(
    page_title="Movie Recommender", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

import requests
import pickle
import pandas as pd
from ast import literal_eval

from src.config import Config

# Check if database exists
DB_PATH = Path(Config.DATA_PATH) / "movies.db"
USE_DATABASE = DB_PATH.exists()

if USE_DATABASE:
    from src.database import (
        get_all_titles,
        get_all_genres,
        get_movie_by_title,
        get_recommendations_from_cache,
        filter_by_genre,
        get_all_movies,
        get_database_stats,
        get_all_tv_titles,
        get_tv_by_title,
        get_tv_recommendations_from_cache,
        get_connection,
        migrate_add_poster_and_providers,
        get_movie_genres,
        get_tv_genres
    )
    
    # Run migration once per session if needed (quiet mode for Streamlit)
    if 'migration_run' not in st.session_state:
        migrate_add_poster_and_providers(quiet=True)
        st.session_state.migration_run = True

# Import analytics module for dialog (use importlib for path flexibility)
import importlib.util
analytics_path = Path(__file__).parent / "app" / "components" / "analytics.py"
spec = importlib.util.spec_from_file_location("analytics", analytics_path)
analytics_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analytics_module)
render_analytics = analytics_module.render_analytics

# Validate config (non-blocking - app will work without API key, just without poster images)
try:
    Config.validate()
except ValueError:
    # API key not set - app will still work but poster images won't load
    pass

# ============ THEME ============

def get_theme_css(is_dark):
    """Industry standard themes."""
    
    if is_dark:
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
            
            :root {
                --scale-factor: 1;
                --available-width: 100vw;
            }
            
            .stApp { background-color: #141414; }
            #MainMenu, footer, header { visibility: hidden; }
            
            html, body, [class*="css"], p, span, label, div {
                font-family: 'Inter', sans-serif;
                color: #ffffff !important;
            }
            
            section[data-testid="stSidebar"] { 
                background-color: #0d0d0d; 
            }
            section[data-testid="stSidebar"] * { color: #ffffff !important; }
            section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.2) !important; margin: 0.5rem 0 !important; }
            section[data-testid="stSidebar"] .stMarkdown { margin-bottom: 0.25rem !important; margin-top: 0.25rem !important; }
            section[data-testid="stSidebar"] .stRadio, section[data-testid="stSidebar"] .stMultiSelect, section[data-testid="stSidebar"] .stSlider, section[data-testid="stSidebar"] .stToggle, section[data-testid="stSidebar"] .stButton { margin-bottom: 0.5rem !important; }
            section[data-testid="stSidebar"] .stRadio[data-baseweb="radio"] { margin-top: 0 !important; margin-bottom: 0 !important; }
            [data-testid="collapsedControl"] { display: none !important; visibility: hidden !important; }
            
            section[data-testid="stMain"] .block-container { max-width: 1100px !important; margin: 0 auto !important; }
            
            .main-title { text-align: center; font-size: clamp(1.5rem, calc(3rem * var(--scale-factor)), 3rem); font-weight: 800; color: #e50914 !important; margin: 0; padding: 1rem 0 0.5rem 0; transition: font-size 0.3s ease; }
            .subtitle { text-align: center; color: #ffffff !important; font-size: clamp(0.9rem, calc(1.1rem * var(--scale-factor)), 1.1rem); font-weight: 400; margin-bottom: 2rem; opacity: 0.9; transition: font-size 0.3s ease; }
            .data-source { text-align: center; color: #ffffff !important; font-size: 0.8rem; opacity: 0.5; margin-bottom: 1rem; }
            
            .poster-card { border-radius: 12px; overflow: hidden; transition: transform 0.3s ease, box-shadow 0.3s ease; }
            .poster-card:hover { transform: translateY(-8px); box-shadow: 0 12px 30px rgba(229, 9, 20, 0.3); }
            .poster-card img { width: 100%; display: block; border-radius: 12px; }
            
            .movie-title { text-align: center; color: #ffffff !important; font-size: 0.9rem; font-weight: 500; margin-top: 10px; }
            .movie-year { color: #ffffff !important; opacity: 0.7; }
            
            .rec-header { color: #ffffff !important; font-size: 1.5rem; font-weight: 600; text-align: center; margin: 2rem 0 0.5rem 0; }
            .rec-subheader { color: #ffffff !important; opacity: 0.7; font-size: 1rem; text-align: center; margin-bottom: 2rem; }
            
            .stButton > button { background: #e50914 !important; color: #ffffff !important; border: none !important; border-radius: 8px; font-weight: 600; padding: clamp(0.5rem, calc(0.75rem * var(--scale-factor)), 0.75rem) clamp(1rem, calc(2rem * var(--scale-factor)), 2rem); font-size: clamp(0.85rem, calc(1rem * var(--scale-factor)), 1rem); white-space: nowrap !important; transition: padding 0.3s ease, font-size 0.3s ease; }
            .stButton > button:hover { background: #f40612 !important; }
            
            .no-poster { width: 100%; aspect-ratio: 2/3; background: #2a2a2a; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #ffffff !important; }
            
            .stSelectbox [data-baseweb="select"] span, .stSelectbox [data-baseweb="select"] div, .stSelectbox input,
            .stMultiSelect [data-baseweb="select"] span, .stMultiSelect [data-baseweb="select"] div, .stMultiSelect input { color: #1a1a1a !important; }
            
            [data-baseweb="popover"] li, [data-baseweb="popover"] span, [data-baseweb="popover"] div,
            [data-baseweb="menu"] li, [data-baseweb="menu"] span, [data-baseweb="menu"] div,
            ul[role="listbox"] li, ul[role="listbox"] span, ul[role="listbox"] div { color: #1a1a1a !important; }
            
            .footer { text-align: center; color: #ffffff !important; opacity: 0.6; padding: 3rem 0 1rem 0; }
            details { background: #1a1a1a !important; border-radius: 8px; }
            details summary, details div { color: #ffffff !important; }
        </style>
        """
    else:
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
            
            :root {
                --scale-factor: 1;
                --available-width: 100vw;
            }
            
            .stApp { background-color: #fafafa; }
            #MainMenu, footer, header { visibility: hidden; }
            
            html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #1a1a1a; }
            
            section[data-testid="stSidebar"] { 
                background-color: #ffffff; 
            }
            section[data-testid="stSidebar"] hr { border-color: #e0e0e0 !important; margin: 0.5rem 0 !important; }
            section[data-testid="stSidebar"] .stMarkdown { margin-bottom: 0.25rem !important; margin-top: 0.25rem !important; }
            section[data-testid="stSidebar"] .stRadio, section[data-testid="stSidebar"] .stMultiSelect, section[data-testid="stSidebar"] .stSlider, section[data-testid="stSidebar"] .stToggle, section[data-testid="stSidebar"] .stButton { margin-bottom: 0.5rem !important; }
            section[data-testid="stSidebar"] .stRadio[data-baseweb="radio"] { margin-top: 0 !important; margin-bottom: 0 !important; }
            [data-testid="collapsedControl"] { display: none !important; visibility: hidden !important; }
            
            section[data-testid="stMain"] .block-container { max-width: 1100px !important; margin: 0 auto !important; }
            
            .main-title { text-align: center; font-size: clamp(1.5rem, calc(3rem * var(--scale-factor)), 3rem); font-weight: 800; color: #e50914 !important; margin: 0; padding: 1rem 0 0.5rem 0; transition: font-size 0.3s ease; }
            .subtitle { text-align: center; color: #666666; font-size: clamp(0.9rem, calc(1.1rem * var(--scale-factor)), 1.1rem); font-weight: 400; margin-bottom: 2rem; transition: font-size 0.3s ease; }
            .data-source { text-align: center; color: #999999; font-size: 0.8rem; margin-bottom: 1rem; }
            
            .poster-card { border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); transition: transform 0.3s ease, box-shadow 0.3s ease; }
            .poster-card:hover { transform: translateY(-8px); box-shadow: 0 12px 30px rgba(229, 9, 20, 0.2); }
            .poster-card img { width: 100%; display: block; border-radius: 12px; }
            
            .movie-title { text-align: center; color: #1a1a1a; font-size: 0.9rem; font-weight: 500; margin-top: 10px; }
            .movie-year { color: #666666; }
            
            .rec-header { color: #1a1a1a; font-size: 1.5rem; font-weight: 600; text-align: center; margin: 2rem 0 0.5rem 0; }
            .rec-subheader { color: #666666; font-size: 1rem; text-align: center; margin-bottom: 2rem; }
            
            .stButton > button { background: #e50914 !important; color: #ffffff !important; border: none !important; border-radius: 8px; font-weight: 600; padding: clamp(0.5rem, calc(0.75rem * var(--scale-factor)), 0.75rem) clamp(1rem, calc(2rem * var(--scale-factor)), 2rem); font-size: clamp(0.85rem, calc(1rem * var(--scale-factor)), 1rem); white-space: nowrap !important; transition: padding 0.3s ease, font-size 0.3s ease; }
            .stButton > button:hover { background: #c7000d !important; }
            
            .no-poster { width: 100%; aspect-ratio: 2/3; background: #f0f0f0; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #999999; }
            .footer { text-align: center; color: #999999; padding: 3rem 0 1rem 0; }
        </style>
        """

# ============ DATA FUNCTIONS ============

@st.cache_data(show_spinner=False)
def load_pickle(file):
    with open(file, 'rb') as f:
        return pickle.load(f)

@st.cache_data(show_spinner=False)
def fetch_poster(movie_id):
    """
    Fetch movie poster URL from TMDB API.
    Supports both Bearer token (v4) and API key (v3) authentication methods.
    """
    headers, use_bearer = Config.get_tmdb_auth()
    
    if use_bearer:
        # Use Bearer token authentication (v4 API - preferred method)
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US"
        headers["accept"] = "application/json"
    elif Config.TMDB_API_KEY:
        # Use API key authentication (v3 API - fallback method)
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={Config.TMDB_API_KEY}&language=en-US"
    else:
        # No authentication available
        return ""
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            poster_path = data.get('poster_path', '')
            if poster_path:
                return f"https://image.tmdb.org/t/p/w500/{poster_path}"
    except:
        pass
    return ""
