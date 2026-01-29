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
# CLOUD-SAFE: Only Streamlit imports and config at module level
import streamlit as st

# CRITICAL: st.set_page_config() MUST be the FIRST Streamlit command
st.set_page_config(
    page_title="Movie Recommender", 
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    """
    Main application function.
    ALL non-Streamlit code must be inside this function to ensure
    Streamlit Cloud can start the server before executing any logic.
    """
    # Import everything inside main() - safe for Cloud
    import sys
    from pathlib import Path
    import requests
    import pickle
    import pandas as pd
    from ast import literal_eval
    import importlib.util
    
    # Setup paths
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Import config
    from src.config import Config
    
    # Validate config (non-blocking)
    try:
        Config.validate()
    except ValueError:
        pass  # App will work without API key, just without poster images
    
    # Check if database exists
    DB_PATH = Path(Config.DATA_PATH) / "movies.db"
    USE_DATABASE = DB_PATH.exists()
    
    # Import database functions if database exists
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
            try:
                migrate_add_poster_and_providers(quiet=True)
                st.session_state.migration_run = True
            except Exception:
                st.session_state.migration_run = True
    else:
        # Set dummy functions if database not available
        get_all_titles = None
        get_all_genres = None
        get_movie_by_title = None
        get_recommendations_from_cache = None
        filter_by_genre = None
        get_all_movies = None
        get_database_stats = None
        get_all_tv_titles = None
        get_tv_by_title = None
        get_tv_recommendations_from_cache = None
        get_connection = None
        get_movie_genres = None
        get_tv_genres = None
    
    # Load analytics module safely (lazy load, handle errors)
    render_analytics = None
    try:
        analytics_path = Path(__file__).parent / "app" / "components" / "analytics.py"
        if analytics_path.exists():
            spec = importlib.util.spec_from_file_location("analytics", analytics_path)
            analytics_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(analytics_module)
            render_analytics = analytics_module.render_analytics
    except Exception:
        # Analytics not available - app will still work
        pass
    
    # ============ THEME ============
    
    def get_theme_css(is_dark):
        """Industry standard themes."""
        
        if is_dark:
            return """
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
                
                /* ============================================
                   CSS Theme Variables & Base Styling
                   ============================================
                   Defines scaling factor and base styles for responsive design.
                   Increased scale-factor for Streamlit Cloud to match local appearance.
                */
                :root {
                    --scale-factor: 1.4;
                    --available-width: 100vw;
                }
                
                /* ============================================
                   App Layout & Visibility Controls
                   ============================================
                   Hides default Streamlit UI elements and ensures sidebar toggle is visible.
                */
                /* Force dark color scheme to prevent system theme interference */
                html, body, .stApp {
                    color-scheme: dark !important;
                }
                .stApp { background-color: #2d2d2d; }
                html { scroll-behavior: auto !important; }
                #MainMenu, footer, header { visibility: hidden; }
                button[data-testid="baseButton-header"], [data-testid="collapsedControl"] { display: block !important; visibility: visible !important; opacity: 1 !important; }
                
                /* ============================================
                   Typography
                   ============================================
                   Base font: 17px, headings proportionally sized.
                */
                html, body, [class*="css"], p, span, label, div {
                    font-family: 'Inter', system-ui, sans-serif;
                    font-size: 17px !important;
                    color: #ffffff !important;
                }
                
                h1 { font-size: 2.4rem !important; }
                h2 { font-size: 2.0rem !important; }
                h3 { font-size: 1.6rem !important; }
                p, span, label, div {
                    font-size: 1.0rem !important;
                }
                
                /* ============================================
                   Sidebar Styling
                   ============================================
                   Customizes sidebar appearance with dark theme colors and spacing.
                */
                section[data-testid="stSidebar"] { 
                    background-color: #333333; 
                    min-width: 280px !important;
                    display: block !important;
                }
                section[data-testid="stSidebar"] * { color: #ffffff !important; }
                section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.2) !important; margin: 0.5rem 0 !important; }
                section[data-testid="stSidebar"] .stMarkdown { margin-bottom: 0.25rem !important; margin-top: 0.25rem !important; }
                section[data-testid="stSidebar"] .stRadio, section[data-testid="stSidebar"] .stMultiSelect, section[data-testid="stSidebar"] .stSlider, section[data-testid="stSidebar"] .stToggle, section[data-testid="stSidebar"] .stButton { margin-bottom: 0.5rem !important; }
                section[data-testid="stSidebar"] .stRadio[data-baseweb="radio"] { margin-top: 0 !important; margin-bottom: 0 !important; }
                
                /* Radio alignment (Dark Theme) */
                .stRadio label {
                    display: inline-flex !important;
                    align-items: center !important;
                    gap: 4px !important;
                }
                .stRadio [role="radiogroup"] {
                    gap: 8px !important;
                    row-gap: 4px !important;
                }
                
                /* ============================================
                   Main Content Centering & Layout (Option 2)
                   ============================================
                   Ensures main content is centered regardless of sidebar state.
                   Uses block-container centering without flexbox to avoid scroll issues.
                */
                section[data-testid="stMain"] {
                    flex: 1 1 0% !important;
                    min-width: 0 !important;
                    overflow-y: auto !important;
                }
                
                section[data-testid="stMain"] .block-container { 
                    max-width: 1100px !important; 
                    width: 100% !important;
                    margin-left: auto !important;
                    margin-right: auto !important;
                    padding-left: 2rem !important;
                    padding-right: 2rem !important;
                }
                
                /* ============================================
                   Dialog Styling
                   ============================================
                   Hides default dialog title and reduces padding for cleaner appearance.
                   Explicit background color to match app theme.
                */
                [data-testid="stDialog"],
                [data-testid="stDialog"] > div,
                [role="dialog"],
                [role="dialog"] > div {
                    background-color: #2d2d2d !important;
                }
                [data-testid="stDialog"] h2:first-child,
                [data-testid="stDialog"] header h2 {
                    display: none !important;
                }
                
                [data-testid="stDialog"] .block-container {
                    padding-top: 0.5rem !important;
                    background-color: #2d2d2d !important;
                }
                
                /* ============================================
                   Custom Component Styling
                   ============================================
                   Styles for titles, posters, buttons, and other UI elements.
                   Font sizes balanced for readability.
                */
                .main-title { text-align: center; font-size: clamp(1.6rem, calc(2.8rem * var(--scale-factor)), 2.8rem); font-weight: 800; color: #e50914 !important; margin: 0; padding: 1rem 0 0.5rem 0; transition: font-size 0.3s ease; }
                .subtitle { text-align: center; color: #ffffff !important; font-size: clamp(0.9rem, calc(1.1rem * var(--scale-factor)), 1.1rem); font-weight: 400; margin-bottom: 2rem; opacity: 0.9; transition: font-size 0.3s ease; }
                .data-source { text-align: center; color: #ffffff !important; font-size: 0.85rem; opacity: 0.5; margin-bottom: 1rem; }
                
                .poster-card { border-radius: 12px; overflow: hidden; transition: transform 0.3s ease, box-shadow 0.3s ease; }
                .poster-card:hover { transform: translateY(-8px); box-shadow: 0 12px 30px rgba(229, 9, 20, 0.3); }
                .poster-card img { width: 100%; display: block; border-radius: 12px; }
                
                .movie-title { text-align: center; color: #ffffff !important; font-size: 0.9rem; font-weight: 500; margin-top: 10px; }
                .movie-year { color: #ffffff !important; opacity: 0.7; }
                
                .rec-header { color: #ffffff !important; font-size: 1.5rem; font-weight: 600; text-align: center; margin: 2rem 0 0.5rem 0; }
                .rec-subheader { color: #ffffff !important; opacity: 0.7; font-size: 1.0rem; text-align: center; margin-bottom: 2rem; }
                
                .stButton > button { background: #e50914 !important; color: #ffffff !important; border: none !important; border-radius: 8px; font-weight: 600; padding: clamp(0.5rem, calc(0.75rem * var(--scale-factor)), 0.75rem) clamp(1rem, calc(2rem * var(--scale-factor)), 2rem); font-size: clamp(0.85rem, calc(1.0rem * var(--scale-factor)), 1.0rem); white-space: nowrap !important; transition: padding 0.3s ease, font-size 0.3s ease; }
                .stButton > button:hover { background: #f40612 !important; }
                
                .no-poster { width: 100%; aspect-ratio: 2/3; background: #2a2a2a; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #ffffff !important; }
                
                /* Fix dropdown styling in dark mode */
                .stSelectbox [data-baseweb="select"],
                .stMultiSelect [data-baseweb="select"] {
                    background-color: #333333 !important;
                    border: 1px solid rgba(255,255,255,0.2) !important;
                    border-radius: 8px !important;
                }
                .stSelectbox [data-baseweb="select"] span, 
                .stSelectbox [data-baseweb="select"] div, 
                .stSelectbox input,
                .stMultiSelect [data-baseweb="select"] span, 
                .stMultiSelect [data-baseweb="select"] div, 
                .stMultiSelect input { 
                    color: #ffffff !important; 
                    background-color: #333333 !important;
                }
                
                /* Fix dropdown arrow visibility */
                .stMultiSelect [data-baseweb="select"] svg,
                .stSelectbox [data-baseweb="select"] svg {
                    fill: #ffffff !important;
                    color: #ffffff !important;
                }
                
                /* Fix dropdown popover/menu - force explicit colors */
                [data-baseweb="popover"],
                [data-baseweb="popover"] > div,
                [data-baseweb="menu"],
                ul[role="listbox"],
                [class*="st-emotion-cache"][role="listbox"] {
                    background-color: #333333 !important;
                    border: 1px solid rgba(255,255,255,0.2) !important;
                }
                /* Dropdown menu items - force white text, no outline/border */
                [data-baseweb="popover"] li, 
                [data-baseweb="popover"] span, 
                [data-baseweb="popover"] div,
                [data-baseweb="menu"] li, 
                [data-baseweb="menu"] span, 
                [data-baseweb="menu"] div,
                ul[role="listbox"] li, 
                ul[role="listbox"] span, 
                ul[role="listbox"] div,
                li[role="option"],
                li[role="option"] span,
                li[role="option"] div,
                [data-baseweb="option"],
                [data-baseweb="option"] span,
                [data-baseweb="option"] div { 
                    color: #ffffff !important; 
                    background-color: #333333 !important;
                    outline: none !important;
                    border: none !important;
                    box-shadow: none !important;
                }
                /* Remove focus outline on dropdown items */
                li[role="option"]:focus,
                li[role="option"]:focus-visible,
                [data-baseweb="option"]:focus,
                [data-baseweb="option"]:focus-visible,
                [data-highlighted="true"] {
                    outline: none !important;
                    border: none !important;
                    box-shadow: none !important;
                }
                /* Dropdown hover state - full red background */
                li[role="option"]:hover,
                li[role="option"]:hover span,
                li[role="option"]:hover div,
                li[role="option"]:hover *,
                [data-baseweb="option"]:hover,
                [data-baseweb="option"]:hover *,
                [data-highlighted="true"],
                [data-highlighted="true"] * {
                    background-color: #e50914 !important;
                    background: #e50914 !important;
                    color: #ffffff !important;
                    outline: none !important;
                    border: none !important;
                }
                /* Selected option - solid red background */
                li[role="option"][aria-selected="true"],
                li[role="option"][aria-selected="true"] span,
                li[role="option"][aria-selected="true"] div,
                li[role="option"][aria-selected="true"] *,
                [data-baseweb="option"][aria-selected="true"],
                [data-baseweb="option"][aria-selected="true"] * {
                    background-color: #e50914 !important;
                    background: #e50914 !important;
                    color: #ffffff !important;
                    outline: none !important;
                    border: none !important;
                }
                
                /* Fix toggle button visibility in dark mode - aggressive targeting */
                .stToggle > label > div:first-of-type,
                .stToggle > label > div:first-of-type > div,
                .stToggle span[data-baseweb="switch"],
                .stToggle span[data-baseweb="switch"] > div,
                .stToggle [data-testid="stToggle"] > div,
                div[data-baseweb="switch"],
                div[data-baseweb="switch"] > div {
                    background-color: #505050 !important;
                }
                .stToggle > label > div:first-of-type[aria-checked="true"],
                .stToggle > label > div:first-of-type[aria-checked="true"] > div,
                .stToggle span[data-baseweb="switch"][aria-checked="true"],
                .stToggle span[data-baseweb="switch"][aria-checked="true"] > div,
                div[data-baseweb="switch"][aria-checked="true"],
                div[data-baseweb="switch"][aria-checked="true"] > div {
                    background-color: #e50914 !important;
                }
                /* Target the track background specifically */
                .stToggle [class*="Track"],
                .stToggle [class*="track"],
                [class*="st-emotion-cache"][data-baseweb="switch"],
                [class*="st-emotion-cache"][data-baseweb="switch"] > div:first-child {
                    background-color: #505050 !important;
                }
                [class*="st-emotion-cache"][data-baseweb="switch"][aria-checked="true"],
                [class*="st-emotion-cache"][data-baseweb="switch"][aria-checked="true"] > div:first-child {
                    background-color: #e50914 !important;
                }
                
                /* Multiselect tags - selected items with red background */
                [data-baseweb="tag"],
                span[data-baseweb="tag"],
                div[data-baseweb="tag"],
                .stMultiSelect [data-baseweb="tag"],
                [class*="st-emotion-cache"][data-baseweb="tag"] {
                    background-color: #e50914 !important;
                    border-color: #e50914 !important;
                    border: none !important;
                }
                [data-baseweb="tag"] > span,
                [data-baseweb="tag"] > div,
                [data-baseweb="tag"] span,
                [data-baseweb="tag"] div,
                [data-baseweb="tag"] *,
                .stMultiSelect [data-baseweb="tag"] *,
                [class*="st-emotion-cache"][data-baseweb="tag"] * {
                    background-color: transparent !important;
                    background: transparent !important;
                    color: #ffffff !important;
                }
                /* Tag close button */
                [data-baseweb="tag"] svg,
                [data-baseweb="tag"] path {
                    fill: #ffffff !important;
                    color: #ffffff !important;
                }
                /* Target emotion-cache classes for tags */
                .stMultiSelect [class*="Tag"],
                .stMultiSelect [class*="tag"] {
                    background-color: #e50914 !important;
                    background: #e50914 !important;
                }
                
                /* Hide scrollbar in dropdown menus */
                [data-baseweb="popover"] > div,
                [data-baseweb="menu"],
                ul[role="listbox"] {
                    scrollbar-width: none !important;
                    -ms-overflow-style: none !important;
                }
                [data-baseweb="popover"] > div::-webkit-scrollbar,
                [data-baseweb="menu"]::-webkit-scrollbar,
                ul[role="listbox"]::-webkit-scrollbar {
                    display: none !important;
                    width: 0 !important;
                }
                
                /* Dropdown border more visible */
                .stSelectbox [data-baseweb="select"],
                .stMultiSelect [data-baseweb="select"] {
                    border: 1px solid rgba(255,255,255,0.35) !important;
                }
                
                .footer { text-align: center; color: #ffffff !important; opacity: 0.6; padding: 3rem 0 1rem 0; }
                /* Expander/Details styling - matches sidebar background */
                details, 
                [data-testid="stExpander"],
                [data-testid="stExpander"] > div {
                    background: #3a3a3a !important; 
                    border-radius: 8px;
                }
                details summary, 
                details div,
                [data-testid="stExpander"] summary,
                [data-testid="stExpander"] div,
                [data-testid="stExpander"] * { 
                    color: #ffffff !important; 
                    background-color: transparent !important;
                }
            </style>
            <script>
                // Dynamic centering based on sidebar state
                function centerMainContent() {
                    const sidebar = document.querySelector('section[data-testid="stSidebar"]');
                    const main = document.querySelector('section[data-testid="stMain"]');
                    const container = main?.querySelector('.block-container');
                    
                    if (!main || !container) return;
                    
                    // Check if sidebar is visible/expanded
                    const sidebarVisible = sidebar && window.getComputedStyle(sidebar).display !== 'none';
                    
                    if (sidebarVisible) {
                        // Sidebar is open - ensure content is centered in remaining space
                        container.style.marginLeft = 'auto';
                        container.style.marginRight = 'auto';
                    } else {
                        // Sidebar is closed - center in full width
                        container.style.marginLeft = 'auto';
                        container.style.marginRight = 'auto';
                    }
                }
                
                // Run on load and when sidebar state changes
                window.addEventListener('load', centerMainContent);
                setInterval(centerMainContent, 100);
                
                function enableSelectClearOnFocus() {
                    const selects = document.querySelectorAll(
                        '.stSelectbox [data-baseweb="select"], .stMultiSelect [data-baseweb="select"], [role="combobox"]'
                    );
                    selects.forEach((select) => {
                        if (select.dataset.clearOnFocus === 'true') return;
                        select.dataset.clearOnFocus = 'true';
                        const input = select.querySelector('input');
                        if (!input) return;
                        const clearValue = () => {
                            input.value = '';
                            input.placeholder = 'Type to search...';
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                        };
                        select.addEventListener('pointerdown', clearValue);
                        select.addEventListener('mousedown', clearValue);
                        input.addEventListener('focus', clearValue);
                        input.addEventListener('keydown', clearValue);
                    });
                }
                
                window.addEventListener('load', enableSelectClearOnFocus);
                setInterval(enableSelectClearOnFocus, 500);
                
                // Watch for sidebar toggle
                const observer = new MutationObserver(centerMainContent);
                const sidebar = document.querySelector('section[data-testid="stSidebar"]');
                if (sidebar) {
                    observer.observe(sidebar, { attributes: true, attributeFilter: ['style', 'class'] });
                }
            </script>
            """
        else:
            return """
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
                
                /* ============================================
                   CSS Theme Variables & Base Styling (Light Theme)
                   ============================================
                   Defines scaling factor and base styles for responsive design.
                   Increased scale-factor for Streamlit Cloud to match local appearance.
                */
                :root {
                    --scale-factor: 1.4;
                    --available-width: 100vw;
                }
                
                /* ============================================
                   App Layout & Visibility Controls (Light Theme)
                   ============================================
                   Hides default Streamlit UI elements and ensures sidebar toggle is visible.
                   Force light color scheme to prevent system theme interference.
                */
                html, body, .stApp {
                    color-scheme: light !important;
                }
                .stApp { background-color: #fafafa; }
                html { scroll-behavior: auto !important; }
                #MainMenu, footer, header { visibility: hidden; }
                button[data-testid="baseButton-header"], [data-testid="collapsedControl"] { display: block !important; visibility: visible !important; opacity: 1 !important; }
                
                /* ============================================
                   Typography (Light Theme)
                   ============================================
                   Base font: 17px, headings proportionally sized.
                */
                html, body, [class*="css"] { 
                    font-family: 'Inter', system-ui, sans-serif; 
                    font-size: 17px !important;
                    color: #1a1a1a; 
                }
                
                h1 { font-size: 2.4rem !important; }
                h2 { font-size: 2.0rem !important; }
                h3 { font-size: 1.6rem !important; }
                p, span, label, div {
                    font-size: 1.0rem !important;
                }
                
                /* ============================================
                   Sidebar Styling (Light Theme)
                   ============================================
                   Customizes sidebar appearance with light theme colors and spacing.
                   Slightly darker than main area for subtle separation without border.
                */
                section[data-testid="stSidebar"] { 
                    background-color: #f0f0f0; 
                    min-width: 280px !important;
                    display: block !important;
                }
                /* Force dark text on all sidebar elements */
                section[data-testid="stSidebar"] * { 
                    color: #1a1a1a !important; 
                }
                section[data-testid="stSidebar"] hr { border-color: #d0d0d0 !important; margin: 0.5rem 0 !important; }
                section[data-testid="stSidebar"] .stMarkdown { margin-bottom: 0.25rem !important; margin-top: 0.25rem !important; }
                section[data-testid="stSidebar"] .stRadio, section[data-testid="stSidebar"] .stMultiSelect, section[data-testid="stSidebar"] .stSlider, section[data-testid="stSidebar"] .stToggle, section[data-testid="stSidebar"] .stButton { margin-bottom: 0.5rem !important; }
                section[data-testid="stSidebar"] .stRadio[data-baseweb="radio"] { margin-top: 0 !important; margin-bottom: 0 !important; }
                
                /* ============================================
                   Main Content Centering & Layout (Light Theme) (Option 2)
                   ============================================
                   Ensures main content is centered regardless of sidebar state.
                   Uses block-container centering without flexbox to avoid scroll issues.
                */
                section[data-testid="stMain"] {
                    flex: 1 1 0% !important;
                    min-width: 0 !important;
                    overflow-y: auto !important;
                }
                
                section[data-testid="stMain"] .block-container { 
                    max-width: 1100px !important; 
                    width: 100% !important;
                    margin-left: auto !important;
                    margin-right: auto !important;
                    padding-left: 2rem !important;
                    padding-right: 2rem !important;
                }
                
                /* ============================================
                   Dialog Styling (Light Theme)
                   ============================================
                   Hides default dialog title and reduces padding for cleaner appearance.
                   Explicit background and TEXT colors for visibility.
                */
                [data-testid="stDialog"],
                [data-testid="stDialog"] > div,
                [role="dialog"],
                [role="dialog"] > div {
                    background-color: #fafafa !important;
                }
                [data-testid="stDialog"] h2:first-child,
                [data-testid="stDialog"] header h2 {
                    display: none !important;
                }
                
                [data-testid="stDialog"] .block-container {
                    padding-top: 0.5rem !important;
                    background-color: #fafafa !important;
                }
                
                /* Analytics/Dialog - Force ALL text to be dark */
                [data-testid="stDialog"] h1,
                [data-testid="stDialog"] h2,
                [data-testid="stDialog"] h3,
                [data-testid="stDialog"] h4,
                [data-testid="stDialog"] p,
                [data-testid="stDialog"] span,
                [data-testid="stDialog"] div,
                [data-testid="stDialog"] label,
                [role="dialog"] h1,
                [role="dialog"] h2,
                [role="dialog"] h3,
                [role="dialog"] h4,
                [role="dialog"] p,
                [role="dialog"] span,
                [role="dialog"] div,
                [role="dialog"] label {
                    color: #1a1a1a !important;
                }
                /* Dialog title styling */
                [data-testid="stDialog"] .main-title,
                [role="dialog"] .main-title {
                    color: #e50914 !important;
                }
                /* Plotly charts - ensure axis labels visible */
                [data-testid="stDialog"] .js-plotly-plot text,
                [data-testid="stDialog"] .plotly text,
                [role="dialog"] .js-plotly-plot text,
                [role="dialog"] .plotly text {
                    fill: #1a1a1a !important;
                }
                /* Expander inside dialog */
                [data-testid="stDialog"] details,
                [data-testid="stDialog"] [data-testid="stExpander"] {
                    background-color: #e8e8e8 !important;
                    border: 1px solid #999999 !important;
                }
                [data-testid="stDialog"] details summary,
                [data-testid="stDialog"] [data-testid="stExpander"] summary {
                    color: #1a1a1a !important;
                }
                
                /* Expander/Details styling (Light Theme) - matches sidebar */
                details, 
                [data-testid="stExpander"],
                [data-testid="stExpander"] > div {
                    background: #e8e8e8 !important; 
                    border-radius: 8px;
                }
                details summary, 
                details div,
                [data-testid="stExpander"] summary,
                [data-testid="stExpander"] div,
                [data-testid="stExpander"] * { 
                    color: #1a1a1a !important; 
                    background-color: transparent !important;
                }
                
                /* ============================================
                   Custom Component Styling (Light Theme)
                   ============================================
                   Styles for titles, posters, buttons, and other UI elements.
                   Font sizes balanced for readability.
                */
                .main-title { text-align: center; font-size: clamp(1.6rem, calc(2.8rem * var(--scale-factor)), 2.8rem); font-weight: 800; color: #e50914 !important; margin: 0; padding: 1rem 0 0.5rem 0; transition: font-size 0.3s ease; }
                .subtitle { text-align: center; color: #666666; font-size: clamp(0.9rem, calc(1.1rem * var(--scale-factor)), 1.1rem); font-weight: 400; margin-bottom: 2rem; transition: font-size 0.3s ease; }
                .data-source { text-align: center; color: #999999; font-size: 0.85rem; margin-bottom: 1rem; }
                
                .poster-card { border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); transition: transform 0.3s ease, box-shadow 0.3s ease; }
                .poster-card:hover { transform: translateY(-8px); box-shadow: 0 12px 30px rgba(229, 9, 20, 0.2); }
                .poster-card img { width: 100%; display: block; border-radius: 12px; }
                
                .movie-title { text-align: center; color: #1a1a1a; font-size: 0.9rem; font-weight: 500; margin-top: 10px; }
                .movie-year { color: #666666; }
                
                .rec-header { color: #1a1a1a; font-size: 1.5rem; font-weight: 600; text-align: center; margin: 2rem 0 0.5rem 0; }
                .rec-subheader { color: #666666; font-size: 1.0rem; text-align: center; margin-bottom: 2rem; }
                
                .stButton > button { background: #e50914 !important; color: #ffffff !important; border: none !important; border-radius: 8px; font-weight: 600; padding: clamp(0.5rem, calc(0.75rem * var(--scale-factor)), 0.75rem) clamp(1rem, calc(2rem * var(--scale-factor)), 2rem); font-size: clamp(0.85rem, calc(1.0rem * var(--scale-factor)), 1.0rem); white-space: nowrap !important; transition: padding 0.3s ease, font-size 0.3s ease; }
                .stButton > button:hover { background: #c7000d !important; }
                
                .no-poster { width: 100%; aspect-ratio: 2/3; background: #f0f0f0; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #999999; }
                
                /* ============================================
                   LABELS - Make all labels visible (dark text)
                   ============================================ */
                .stSelectbox label,
                .stMultiSelect label,
                [data-testid="stWidgetLabel"],
                [data-testid="stWidgetLabel"] p,
                [data-testid="stWidgetLabel"] span,
                .stSelectbox > label > div,
                .stMultiSelect > label > div {
                    color: #1a1a1a !important;
                }
                
                /* ============================================
                   DROPDOWNS - Styling (Lighter borders)
                   ============================================ */
                /* All dropdowns - light gray border */
                .stSelectbox [data-baseweb="select"],
                .stMultiSelect [data-baseweb="select"] { 
                    border: 1px solid #c0c0c0 !important;
                    border-radius: 8px !important; 
                    background-color: #ffffff !important;
                }
                /* Sidebar dropdown - even lighter */
                section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] {
                    border: 1px solid #d0d0d0 !important;
                }
                .stSelectbox [data-baseweb="select"] span, 
                .stSelectbox [data-baseweb="select"] div, 
                .stSelectbox input,
                .stMultiSelect [data-baseweb="select"] span, 
                .stMultiSelect [data-baseweb="select"] div, 
                .stMultiSelect input { 
                    color: #1a1a1a !important; 
                    background-color: #ffffff !important;
                }
                /* Dropdown arrow */
                .stMultiSelect [data-baseweb="select"] svg,
                .stSelectbox [data-baseweb="select"] svg {
                    fill: #1a1a1a !important;
                    color: #1a1a1a !important;
                }
                
                /* ============================================
                   DROPDOWN MENU - Clean, no black edges
                   ============================================ */
                /* Container - clean white, light border */
                [data-baseweb="popover"],
                [data-baseweb="popover"] > div,
                [data-baseweb="menu"],
                [data-baseweb="menu"] > div,
                ul[role="listbox"],
                div[role="listbox"] {
                    background-color: #ffffff !important;
                    border: 1px solid #d0d0d0 !important;
                    border-radius: 8px !important;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
                    overflow: hidden !important;
                    color-scheme: light !important;
                    scrollbar-gutter: auto !important;
                    padding-right: 0 !important;
                    scrollbar-width: thin !important;
                    scrollbar-color: #9a9a9a #f0f0f0 !important;
                    -ms-overflow-style: auto !important;
                }
                /* Inner list container - remove scroll gutter/track */
                [data-baseweb="menu"] div[role="listbox"],
                [data-baseweb="menu"] ul[role="listbox"],
                [data-baseweb="popover"] div[role="listbox"],
                [data-baseweb="popover"] ul[role="listbox"] {
                    overflow-y: auto !important;
                    scrollbar-gutter: auto !important;
                    padding-right: 0 !important;
                    margin-right: 0 !important;
                }
                [data-baseweb="popover"]::-webkit-scrollbar,
                [data-baseweb="popover"] > div::-webkit-scrollbar,
                [data-baseweb="menu"]::-webkit-scrollbar,
                [data-baseweb="menu"] > div::-webkit-scrollbar,
                ul[role="listbox"]::-webkit-scrollbar,
                div[role="listbox"]::-webkit-scrollbar {
                    display: block !important;
                    width: 8px !important;
                    height: 8px !important;
                    background: #f0f0f0 !important;
                }
                [data-baseweb="popover"]::-webkit-scrollbar-thumb,
                [data-baseweb="popover"] > div::-webkit-scrollbar-thumb,
                [data-baseweb="menu"]::-webkit-scrollbar-thumb,
                [data-baseweb="menu"] > div::-webkit-scrollbar-thumb,
                ul[role="listbox"]::-webkit-scrollbar-thumb,
                div[role="listbox"]::-webkit-scrollbar-thumb {
                    background: #9a9a9a !important;
                    border-radius: 8px !important;
                }
                [data-baseweb="popover"]::-webkit-scrollbar-track,
                [data-baseweb="popover"] > div::-webkit-scrollbar-track,
                [data-baseweb="menu"]::-webkit-scrollbar-track,
                [data-baseweb="menu"] > div::-webkit-scrollbar-track,
                ul[role="listbox"]::-webkit-scrollbar-track,
                div[role="listbox"]::-webkit-scrollbar-track {
                    background: #f0f0f0 !important;
                }
                /* Items - NO margin, full width, clean */
                [data-baseweb="popover"] li, 
                [data-baseweb="menu"] li,
                ul[role="listbox"] li,
                li[role="option"] { 
                    color: #1a1a1a !important; 
                    background-color: #ffffff !important;
                    background: #ffffff !important;
                    outline: none !important;
                    border: none !important;
                    box-shadow: none !important;
                    margin: 0 !important;
                    border-radius: 0 !important;
                    padding: 10px 16px !important;
                    width: 100% !important;
                    box-sizing: border-box !important;
                    scrollbar-gutter: auto !important;
                }
                li[role="option"] span,
                li[role="option"] div {
                    color: #1a1a1a !important; 
                    background-color: transparent !important;
                    background: transparent !important;
                }
                /* Hover state - full width RED */
                li[role="option"]:hover,
                [data-highlighted="true"] {
                    background-color: #e50914 !important;
                    background: #e50914 !important;
                    color: #ffffff !important;
                    outline: none !important;
                    border-radius: 8px !important;
                }
                li[role="option"]:hover span,
                li[role="option"]:hover div,
                li[role="option"]:hover *,
                [data-highlighted="true"] span,
                [data-highlighted="true"] div,
                [data-highlighted="true"] * {
                    background-color: transparent !important;
                    background: transparent !important;
                    color: #ffffff !important;
                }
                /* Selected option - RED */
                li[role="option"][aria-selected="true"] {
                    background-color: #e50914 !important;
                    background: #e50914 !important;
                    color: #ffffff !important;
                    border-radius: 8px !important;
                }
                li[role="option"][aria-selected="true"] span,
                li[role="option"][aria-selected="true"] div {
                    color: #ffffff !important;
                    background: transparent !important;
                }
                
                /* ============================================
                   MULTISELECT TAGS - Red pill buttons
                   ============================================ */
                .stMultiSelect [data-baseweb="tag"],
                .stMultiSelect span[data-baseweb="tag"],
                .stMultiSelect div[data-baseweb="tag"] {
                    background-color: #e50914 !important;
                    background: #e50914 !important;
                    border: none !important;
                    border-radius: 16px !important;
                    padding: 4px 12px !important;
                    margin: 2px !important;
                    display: inline-flex !important;
                    align-items: center !important;
                    color: #ffffff !important;
                    box-shadow: none !important;
                }
                /* Tag text and children - white on transparent */
                .stMultiSelect [data-baseweb="tag"] span,
                .stMultiSelect [data-baseweb="tag"] div,
                .stMultiSelect [data-baseweb="tag"] * {
                    color: #ffffff !important;
                    background-color: transparent !important;
                    background: transparent !important;
                }
                /* Tag close button (X) - white */
                [data-baseweb="tag"] svg,
                [data-baseweb="tag"] path {
                    fill: #ffffff !important;
                    color: #ffffff !important;
                }
                /* Clear all button - gray */
                .stMultiSelect [data-baseweb="select"] > div > div:last-child svg {
                    fill: #666666 !important;
                }
                /* Multiselect input area - white background */
                .stMultiSelect [data-baseweb="select"] > div {
                    background-color: #ffffff !important;
                }
                
                /* ============================================
                   RADIO BUTTONS - Simple, clean styling
                   ============================================ */
                /* Container - always transparent */
                .stRadio label,
                .stRadio label * {
                    background-color: transparent !important;
                    background: transparent !important;
                }
                /* Use native radio input to ensure visibility */
                .stRadio input[type="radio"] {
                    appearance: auto !important;
                    -webkit-appearance: radio !important;
                    accent-color: #e50914 !important;
                    width: 16px !important;
                    height: 16px !important;
                    opacity: 1 !important;
                    position: static !important;
                    margin: 0 4px 0 0 !important;
                }
                /* Hide BaseWeb custom circle */
                .stRadio div[data-baseweb="radio"] > div:first-child {
                    display: none !important;
                }
                /* Align label text with native radio and tighten spacing */
                .stRadio label {
                    display: inline-flex !important;
                    align-items: center !important;
                    gap: 4px !important;
                }
                .stRadio [role="radiogroup"] {
                    gap: 8px !important;
                    row-gap: 4px !important;
                }
                
                /* ============================================
                   TOGGLE BUTTON - Dark gray track, white thumb
                   ============================================ */
                /* Track (background) - darker gray for visibility */
                div[data-baseweb="switch"],
                .stToggle div[data-baseweb="switch"] {
                    background-color: #2f2f2f !important;
                    border: 1px solid #5a5a5a !important;
                }
                /* Track when ON - red */
                div[data-baseweb="switch"][aria-checked="true"],
                .stToggle div[data-baseweb="switch"][aria-checked="true"] {
                    background-color: #e50914 !important;
                    border-color: #e50914 !important;
                }
                /* Thumb (the moving circle) - always white */
                div[data-baseweb="switch"] > div:last-child,
                .stToggle div[data-baseweb="switch"] > div:last-child {
                    background-color: #ffffff !important;
                }
                
                /* ============================================
                   TOOLTIP/HELP ICON - Make visible
                   ============================================ */
                .stTooltipIcon,
                [data-testid="stTooltipIcon"],
                .stToggle svg,
                [data-testid="tooltipHoverTarget"] svg {
                    fill: #666666 !important;
                    color: #666666 !important;
                }
                
                /* ============================================
                   ANALYTICS BUTTON - White text
                   ============================================ */
                .stButton > button {
                    background: #e50914 !important; 
                    color: #ffffff !important; 
                    border: none !important;
                }
                .stButton > button span,
                .stButton > button div,
                .stButton > button p {
                    color: #ffffff !important;
                }
                
                /* ============================================
                   HOW IT WORKS EXPANDER - Darker border
                   ============================================ */
                [data-testid="stExpander"],
                details {
                    border: 1px solid #999999 !important;
                    border-radius: 8px !important;
                    background: #e8e8e8 !important;
                }
                [data-testid="stExpander"] summary,
                details summary {
                    color: #1a1a1a !important;
                }
                
                .footer { text-align: center; color: #999999; padding: 3rem 0 1rem 0; }
            </style>
            <script>
                // Dynamic centering based on sidebar state (Light Theme)
                function centerMainContent() {
                    const sidebar = document.querySelector('section[data-testid="stSidebar"]');
                    const main = document.querySelector('section[data-testid="stMain"]');
                    const container = main?.querySelector('.block-container');
                    
                    if (!main || !container) return;
                    
                    // Check if sidebar is visible/expanded
                    const sidebarVisible = sidebar && window.getComputedStyle(sidebar).display !== 'none';
                    
                    if (sidebarVisible) {
                        // Sidebar is open - ensure content is centered in remaining space
                        container.style.marginLeft = 'auto';
                        container.style.marginRight = 'auto';
                    } else {
                        // Sidebar is closed - center in full width
                        container.style.marginLeft = 'auto';
                        container.style.marginRight = 'auto';
                    }
                }
                
                // Run on load and when sidebar state changes
                window.addEventListener('load', centerMainContent);
                setInterval(centerMainContent, 100);
                
                function enableSelectClearOnFocus() {
                    const selects = document.querySelectorAll(
                        '.stSelectbox [data-baseweb="select"], .stMultiSelect [data-baseweb="select"], [role="combobox"]'
                    );
                    selects.forEach((select) => {
                        if (select.dataset.clearOnFocus === 'true') return;
                        select.dataset.clearOnFocus = 'true';
                        const input = select.querySelector('input');
                        if (!input) return;
                        const clearValue = () => {
                            input.value = '';
                            input.placeholder = 'Type to search...';
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                        };
                        select.addEventListener('pointerdown', clearValue);
                        select.addEventListener('mousedown', clearValue);
                        input.addEventListener('focus', clearValue);
                        input.addEventListener('keydown', clearValue);
                    });
                }
                
                window.addEventListener('load', enableSelectClearOnFocus);
                setInterval(enableSelectClearOnFocus, 500);
                
                // Watch for sidebar toggle
                const observer = new MutationObserver(centerMainContent);
                const sidebar = document.querySelector('section[data-testid="stSidebar"]');
                if (sidebar) {
                    observer.observe(sidebar, { attributes: true, attributeFilter: ['style', 'class'] });
                }
            </script>
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
                poster_path = data.get("poster_path", "")
                if poster_path:
                    return f"https://image.tmdb.org/t/p/w500/{poster_path}"
        except:
            pass
        return ""
    
    @st.cache_data(show_spinner=False)
    def get_genres_from_df(movies_df):
        """Extract genres from DataFrame (fallback when no database)."""
        all_genres = set()
        for genres_str in movies_df['genres'].dropna():
            try:
                if isinstance(genres_str, str):
                    genres_list = literal_eval(genres_str)
                else:
                    genres_list = genres_str
                for genre in set(genres_list):
                    genre_clean = genre.strip().title()
                    if genre_clean and len(genre_clean) > 1:
                        all_genres.add(genre_clean)
            except:
                pass
        return sorted(list(all_genres))
    
    def imdb_url(imdb_id):
        return f'https://www.imdb.com/title/{imdb_id}/'
    
    def get_recommendations_pickle(titles, cosine_sim_mat, df, num_of_rec=16, genre_filter=None):
        """Get recommendations using pickle data (fallback method)."""
        combined = df.reset_index()
        indices = pd.Series(combined.index, index=combined['title'])
        
        if isinstance(titles, str):
            titles = [titles]
        
        valid_titles = [t for t in titles if t in indices]
        if not valid_titles:
            return None, None, None, "No valid movies found."
        
        all_sim_scores = None
        for title in valid_titles:
            idx = indices[title]
            sim_scores = cosine_sim_mat[idx]
            if all_sim_scores is None:
                all_sim_scores = sim_scores.copy()
            else:
                all_sim_scores = all_sim_scores + sim_scores
        
        if len(valid_titles) > 1:
            all_sim_scores = all_sim_scores / len(valid_titles)
        
        sim_scores_list = list(enumerate(all_sim_scores))
        sim_scores_list = sorted(sim_scores_list, key=lambda x: x[1], reverse=True)
        
        input_indices = [indices[t] for t in valid_titles]
        sim_scores_list = [s for s in sim_scores_list if s[0] not in input_indices]
        
        if genre_filter and len(genre_filter) > 0:
            filtered_scores = []
            for idx_score in sim_scores_list:
                movie_genres_raw = combined.iloc[idx_score[0]]['genres']
                try:
                    if isinstance(movie_genres_raw, str):
                        movie_genres = [g.strip().title() for g in literal_eval(movie_genres_raw)]
                    else:
                        movie_genres = [g.strip().title() for g in movie_genres_raw]
                    if any(g in movie_genres for g in genre_filter):
                        filtered_scores.append(idx_score)
                except:
                    pass
            sim_scores_list = filtered_scores
        
        sim_scores_list = sim_scores_list[:num_of_rec]
        
        if len(sim_scores_list) == 0:
            return None, None, None, "No movies found matching your criteria."
    
        recommended_movies = []
        recommended_movies_posters = []
        urls = []
    
        for i in sim_scores_list:
            movie_id = combined.iloc[i[0]].id
            imdb_id = combined.iloc[i[0]].imdb_id
            recommended_movies.append(combined.iloc[i[0]][['title', 'year', 'vote_average']])
            recommended_movies_posters.append(fetch_poster(movie_id))
            urls.append(imdb_url(imdb_id))
    
        return recommended_movies, recommended_movies_posters, urls, None
    
    # Provider name mapping to simple names
    PROVIDER_SIMPLE_NAMES = {
        # Netflix variations
        'netflix': 'Netflix',
        'netflix with ads': 'Netflix',
        'netflix (with ads)': 'Netflix',
        
        # Disney variations
        'disney': 'Disney+',
        'disney plus': 'Disney+',
        'disney+': 'Disney+',
        'disney plus with ads': 'Disney+',
        
        # Prime Video variations
        'amazon prime video': 'Prime Video',
        'prime video': 'Prime Video',
        'amazon prime': 'Prime Video',
        
        # HBO variations
        'hbo': 'HBO Max',
        'hbo max': 'HBO Max',
        'max': 'HBO Max',
        'hbo max with ads': 'HBO Max',
        
        # Paramount variations
        'paramount': 'Paramount+',
        'paramount plus': 'Paramount+',
        'paramount+': 'Paramount+',
        'paramount plus with ads': 'Paramount+',
        
        # Apple TV variations
        'apple tv': 'Apple TV+',
        'apple tv plus': 'Apple TV+',
        'apple tv+': 'Apple TV+',
        'apple tv plus with ads': 'Apple TV+',
        
        # Other common providers
        'hulu': 'Hulu',
        'peacock': 'Peacock',
        'crunchyroll': 'Crunchyroll',
        'showtime': 'Showtime',
        'starz': 'Starz',
        # Discovery - all variations
        'discovery': 'Discovery+',
        'discovery plus': 'Discovery+',
        'discovery+': 'Discovery+',
        'discovery channel': 'Discovery+',
        # ESPN - all variations
        'espn': 'ESPN+',
        'espn plus': 'ESPN+',
        'espn+': 'ESPN+',
        'espn network': 'ESPN+',
        # YouTube - all variations
        'youtube': 'YouTube',
        'youtube premium': 'YouTube',
        'youtube tv': 'YouTube',
        'youtube red': 'YouTube',
        # CBS - all variations
        'cbs': 'CBS',
        'cbs all access': 'CBS',
        'cbs network': 'CBS',
        'cbs.com': 'CBS',
        # fuboTV - all variations
        'fubotv': 'fuboTV',
        'fubo tv': 'fuboTV',
        'fubo': 'fuboTV',
        # Google Play - all variations
        'google play': 'Google Play',
        'google play movies': 'Google Play',
        'google play movies & tv': 'Google Play',
        'google play store': 'Google Play',
        # BBC - all variations
        'bbc': 'BBC',
        'bbc iplayer': 'BBC',
        'bbc one': 'BBC',
        'bbc two': 'BBC',
        # Circus - all variations
        'circus': 'Circus',
        'circus kino': 'Circus',
        'sling tv': 'Sling TV',
        'tubi': 'Tubi',
        'pluto tv': 'Pluto TV',
        'freevee': 'Freevee',
        'crackle': 'Crackle',
        'vudu': 'Vudu',
        'microsoft store': 'Microsoft Store',
        'itunes': 'iTunes',
        'rakuten tv': 'Rakuten TV',
    }
    
    def normalize_provider_name(provider: str) -> str:
        """
        Normalize provider name to simple form.
        Examples:
        - "Netflix with ads" → "Netflix"
        - "Disney Plus" → "Disney+"
        - "Amazon Prime Video" → "Prime Video"
        - "HBO Max" → "HBO Max"
        """
        if not provider:
            return ""
        
        # Convert to lowercase for matching
        provider_lower = provider.strip().lower()
        
        # Remove common suffixes first
        provider_lower = provider_lower.replace(' with ads', '')
        provider_lower = provider_lower.replace(' (with ads)', '')
        provider_lower = provider_lower.replace(' premium', '')
        provider_lower = provider_lower.replace(' plus', '')
        provider_lower = provider_lower.replace('+', '')
        provider_lower = provider_lower.strip()
        
        # Try exact match in mapping
        if provider_lower in PROVIDER_SIMPLE_NAMES:
            return PROVIDER_SIMPLE_NAMES[provider_lower]
        
        # Try partial match (e.g., "netflix" in "netflix with ads")
        # Check for common provider keywords first
        if 'discovery' in provider_lower:
            return 'Discovery+'
        if 'espn' in provider_lower:
            return 'ESPN+'
        if 'youtube' in provider_lower:
            return 'YouTube'
        if provider_lower.startswith('cbs') or 'cbs' in provider_lower:
            return 'CBS'
        if 'fubo' in provider_lower:
            return 'fuboTV'
        if 'google play' in provider_lower or 'googleplay' in provider_lower:
            return 'Google Play'
        if 'bbc' in provider_lower:
            return 'BBC'
        if 'circus' in provider_lower:
            return 'Circus'
        
        # Try other partial matches
        for key, simple_name in PROVIDER_SIMPLE_NAMES.items():
            if key in provider_lower or provider_lower in key:
                return simple_name
        
        # If no match, try to extract base name
        # Remove common words and keep the main brand
        words = provider_lower.split()
        if words:
            # Take first significant word (skip "the", "with", etc.)
            significant_words = [w for w in words if w not in ['the', 'with', 'and', 'or', 'ads']]
            if significant_words:
                base = significant_words[0].capitalize()
                # Add + if it was a streaming service
                if any(word in provider_lower for word in ['plus', '+', 'streaming']):
                    return f"{base}+"
                return base
        
        # Fallback: return capitalized original (cleaned)
        return provider.strip().title()
    
    # Provider name to logo filename mapping
    # Multiple variations map to the same logo file
    # Note: Filenames match what was actually downloaded
    PROVIDER_LOGO_MAP = {
        # Netflix
        'Netflix': 'netflix.png',
        
        # Disney variations
        'Disney+': 'disneyplus.png',
        'Disney Plus': 'disneyplus.png',
        'Disney': 'disneyplus.png',
        
        # Prime Video variations
        'Prime Video': 'prime-video.png',
        'Amazon Prime Video': 'prime-video.png',
        'Amazon Prime': 'prime-video.png',
        
        # HBO variations - try multiple filenames
        'HBO Max': 'hbo-max.png',
        'HBO': 'hbo-max.png',
        'Max': 'hbo-max.png',
        
        # Paramount variations
        'Paramount+': 'paramountplus.png',
        'Paramount Plus': 'paramountplus.png',
        'Paramount': 'paramountplus.png',
        
        # Apple TV variations
        'Apple TV+': 'apple-tvplus.png',
        'Apple TV Plus': 'apple-tvplus.png',
        'Apple TV': 'apple-tvplus.png',
        
        # Others
        'Hulu': 'hulu.png',
        'Peacock': 'peacock.png',
        'Crunchyroll': 'crunchyroll.png',
        'Showtime': 'showtime.png',  # May not exist
        'Starz': 'starz.png',
        'Discovery+': 'discovery-plus.png',  # May not exist
        'Discovery Plus': 'discovery-plus.png',
        'Discovery': 'discovery-plus.png',
        'ESPN+': 'espnplus.png',
        'ESPN Plus': 'espnplus.png',
        'ESPN': 'espnplus.png',
        'YouTube': 'youtube.png',
        'YouTube Premium': 'youtube.png',
        'CBS': 'cbs.png',
        'CBS All Access': 'cbs.png',
        'fuboTV': 'fubotv.png',
        'fubo TV': 'fubotv.png',
        'Sling TV': 'sling-tv.png',  # May not exist
        'Tubi': 'tubi.png',
        'Pluto TV': 'pluto-tv.png',
        'Freevee': 'freevee.png',
        'Crackle': 'crackle.png',  # May not exist
        'Vudu': 'vudu.png',
        'Google Play': 'google-play.png',
        'Google Play Movies': 'google-play.png',
        'BBC': 'bbc.png',  # May not exist yet
        'Circus': 'circus.png',  # May not exist yet
        'Microsoft Store': 'microsoft-store.png',  # May not exist
        'iTunes': 'itunes.png',
        'Rakuten TV': 'rakuten-tv.png',
    }
    
    def get_provider_logo_base64(provider_name: str) -> str:
        """
        Get local logo as base64 data URI for a provider.
        Tries multiple filename variations if exact match not found.
        Returns base64 data URI if logo exists, None otherwise.
        """
        import base64
        from pathlib import Path
        
        logos_dir = Path(__file__).parent / "data" / "provider_logos"
        
        # Try exact match first
        logo_file = PROVIDER_LOGO_MAP.get(provider_name)
        if logo_file:
            logo_path = logos_dir / logo_file
            if logo_path.exists():
                return _encode_logo_to_base64(logo_path)
        
        # Try alternative filename variations
        # Generate possible filenames from provider name
        variations = [
            provider_name.lower().replace(' ', '-').replace('+', 'plus') + '.png',
            provider_name.lower().replace(' ', '').replace('+', 'plus') + '.png',
            provider_name.lower().replace('+', 'plus') + '.png',
        ]
        
        for variation in variations:
            logo_path = logos_dir / variation
            if logo_path.exists():
                return _encode_logo_to_base64(logo_path)
        
        return None
    
    def _encode_logo_to_base64(logo_path: Path) -> str:
        """Helper to encode logo file to base64."""
        import base64
        try:
            image_bytes = logo_path.read_bytes()
            base64_str = base64.b64encode(image_bytes).decode('utf-8')
            ext = logo_path.suffix.lower()
            mime_type = 'image/png' if ext == '.png' else 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png'
            return f"data:{mime_type};base64,{base64_str}"
        except Exception:
            return None
    
    def get_provider_logo_url(provider_data: dict) -> str:
        """
        Get TMDB logo URL for a provider (fallback if local logo not available).
        provider_data can be:
        - dict with 'logo_path' key (from new format)
        - str (provider name, from old format - will return None)
        """
        if isinstance(provider_data, dict):
            logo_path = provider_data.get('logo_path')
            if logo_path:
                return f"https://image.tmdb.org/t/p/w45/{logo_path}"  # w45 is small logo size
        return None
    
    def get_provider_name(provider_data) -> str:
        """Extract provider name from provider_data (dict or string)."""
        if isinstance(provider_data, dict):
            return provider_data.get('name', '')
        return str(provider_data) if provider_data else ''
    
    def parse_watch_providers_from_json(watch_providers_json, region: str) -> list:
        """
        Parse watch providers from JSON string or dict.
        Returns list of provider dicts with 'name' and 'logo_path', or provider names (for backward compatibility).
        """
        import json
        
        if not watch_providers_json:
            return []
        
        try:
            # Handle both string and dict
            if isinstance(watch_providers_json, str):
                if not watch_providers_json.strip():
                    return []
                providers = json.loads(watch_providers_json)
            else:
                providers = watch_providers_json
            
            if isinstance(providers, dict):
                region_providers = providers.get(region, {})
                if isinstance(region_providers, dict):
                    flatrate = region_providers.get('flatrate', [])
                    if isinstance(flatrate, list) and len(flatrate) > 0:
                        # Check if new format (dicts with id, name, logo_path)
                        if isinstance(flatrate[0], dict) and 'name' in flatrate[0]:
                            # New format: normalize and deduplicate by normalized name
                            normalized = []
                            seen_normalized = set()
                            
                            for provider in flatrate[:10]:  # Check more to find best match
                                name = provider.get('name', '')
                                norm_name = normalize_provider_name(name)
                                
                                # Skip if we've already seen this normalized name
                                if norm_name and norm_name not in seen_normalized:
                                    # Keep the first occurrence (usually the main one)
                                    normalized.append({
                                        'id': provider.get('id'),
                                        'name': norm_name,  # Use normalized simple name
                                        'logo_path': provider.get('logo_path', '')
                                    })
                                    seen_normalized.add(norm_name)
                            
                            return normalized[:3]  # Return top 3 unique
                        else:
                            # Old format: just names (strings) - normalize and deduplicate
                            normalized = []
                            seen_normalized = set()
                            
                            for provider in flatrate[:10]:  # Check more to find best match
                                norm_name = normalize_provider_name(str(provider))
                                if norm_name and norm_name not in seen_normalized:
                                    normalized.append(norm_name)
                                    seen_normalized.add(norm_name)
                            
                            return normalized[:3]  # Return top 3 unique
        except (json.JSONDecodeError, AttributeError, TypeError):
            # Silently fail - providers data might be malformed
            pass
        return []
    
    
    def get_watch_providers_from_db(item_id: int, media_type: str, region: str) -> list:
        """Get watch providers for a movie/TV show from database (fallback method)."""
        import json
        from src.database import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        table = 'tv_shows' if media_type == 'tv' else 'movies'
        cursor.execute(f"SELECT watch_providers FROM {table} WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0]:
            return parse_watch_providers_from_json(row[0], region)
        return []
    
    
    def get_recommendations_db(titles, num_of_rec=16, genre_filter=None, media_type='movies'):
        """Get recommendations using SQLite database. Supports multi-title mode."""
        if isinstance(titles, str):
            titles = [titles]
        
        # Get all items and their recommendations
        all_recs = {}  # {item_id: score} to combine scores
        selected_ids = set()
        
        for title in titles:
            # Get item info based on media type
            if media_type == 'tv':
                item = get_tv_by_title(title)
                if not item:
                    continue
            else:
                item = get_movie_by_title(title)
                if not item:
                    continue
            
            selected_ids.add(item['id'])
            
            # Get recommendations for this item
            if media_type == 'tv':
                recs = get_tv_recommendations_from_cache(item['id'], limit=num_of_rec * 3)
            else:
                recs = get_recommendations_from_cache(item['id'], limit=num_of_rec * 3)
            
            if recs:
                # Combine scores (average if multiple titles)
                for rec in recs:
                    rec_id = rec['id']
                    score = rec.get('score', 0.0)
                    if rec_id not in selected_ids:  # Don't include selected items
                        if rec_id in all_recs:
                            # Average the scores for multi-mode
                            all_recs[rec_id] = (all_recs[rec_id] + score) / 2
                        else:
                            all_recs[rec_id] = score
        
        if not all_recs:
            return None, None, None, None, "No recommendations found."
        
        # Convert to list and sort by score
        recs_list = []
        # Get full details for each recommended item
        for rec_id, score in sorted(all_recs.items(), key=lambda x: x[1], reverse=True):
            if media_type == 'tv':
                from src.database import get_connection
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, imdb_id, title, year, vote_average, watch_providers
                    FROM tv_shows WHERE id = ?
                """, (rec_id,))
                row = cursor.fetchone()
                conn.close()
                if row:
                    rec_dict = dict(row)
                    rec_dict['score'] = score
                    recs_list.append(rec_dict)
            else:
                from src.database import get_connection
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, imdb_id, title, year, vote_average, watch_providers
                    FROM movies WHERE id = ?
                """, (rec_id,))
                row = cursor.fetchone()
                conn.close()
                if row:
                    rec_dict = dict(row)
                    rec_dict['score'] = score
                    recs_list.append(rec_dict)
        
        recs = recs_list[:num_of_rec * 2]  # Get more for filtering
        
        if len(recs) == 0:
            return None, None, None, None, "No recommendations found."
        
        # Apply genre filter if specified
        if genre_filter and len(genre_filter) > 0:
            filtered_recs = []
            for rec in recs:
                if media_type == 'tv':
                    tv_genres = get_tv_genres(rec['id'])
                    if any(g.title() in [tg.title() for tg in tv_genres] for g in genre_filter):
                        filtered_recs.append(rec)
                else:
                    movie_genres = get_movie_genres(rec['id'])
                    if any(g.title() in [mg.title() for mg in movie_genres] for g in genre_filter):
                        filtered_recs.append(rec)
            recs = filtered_recs
        
        recs = recs[:num_of_rec]
        
        if len(recs) == 0:
            return None, None, None, None, f"No {media_type} found matching your criteria."
        
        recommended_items = []
        recommended_posters = []
        urls = []
        providers_list = []
        
        for rec in recs:
            class ItemRec:
                def __init__(self, data):
                    self.title = data.get('title', 'Unknown')
                    self.year = data.get('year') or 0
                    self.vote_average = data.get('vote_average') or 0.0
            
            try:
                recommended_items.append(ItemRec(rec))
            except Exception as e:
                # Skip this recommendation if there's an error
                continue
            
            # Get poster from database or fetch
            poster_url = None
            if USE_DATABASE:
                table = 'tv_shows' if media_type == 'tv' else 'movies'
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute(f"SELECT poster_url FROM {table} WHERE id = ?", (rec['id'],))
                row = cursor.fetchone()
                conn.close()
                if row and row[0]:
                    poster_url = row[0]
            
            if not poster_url:
                poster_url = fetch_poster(rec['id']) if media_type == 'movies' else ""
            
            recommended_posters.append(poster_url)
            
            # Handle IMDb URL - make sure imdb_id exists
            imdb_id = rec.get('imdb_id', '')
            if imdb_id:
                urls.append(imdb_url(imdb_id))
            else:
                urls.append('#')
            
            # Get watch providers from recommendation result (more efficient)
            # COMMENTED OUT: Watch providers temporarily disabled
            providers = []  # Empty list for now
            providers_list.append(providers)
        
        return recommended_items, recommended_posters, urls, providers_list, None
    
    # ===== MAIN APPLICATION LOGIC =====
    
    # Get media type from session state (default to movies)
    media_type = st.session_state.get('media_type', 'movies')
    
    # Load data based on media type and available source
    if USE_DATABASE:
        if media_type == 'tv':
            all_titles = get_all_tv_titles()
            all_genres = get_all_genres()  # Genres are shared
            data_source = "SQLite Database (TV Shows)"
        else:
            all_titles = get_all_titles()
            all_genres = get_all_genres()
            data_source = "SQLite Database (Movies)"
        movies_df = None
        tfidf = None
    else:
        if media_type == 'tv':
            movies_df = load_pickle('data/tv_shows.pkl')
            tfidf = load_pickle('data/tv_similarity.pkl')
            data_source = "Pickle Files (TV Shows)"
        else:
            movies_df = load_pickle('data/movies.pkl')
            tfidf = load_pickle('data/similarity.pkl')
            data_source = "Pickle Files (Movies)"
        # Sort by vote_average descending
        sorted_df = movies_df.sort_values('vote_average', ascending=False)
        # Format titles with year: "Title (Year)" or just "Title" if year is None
        all_titles = []
        for _, row in sorted_df.iterrows():
            title = row['title']
            year = row.get('year')
            if pd.notna(year) and year is not None and year != '':
                try:
                    all_titles.append(f"{title} ({int(year)})")
                except (ValueError, TypeError):
                    all_titles.append(title)
            else:
                all_titles.append(title)
        all_genres = get_genres_from_df(movies_df)
    
    # Helper function to extract title from "Title (Year)" format
    def extract_title(title_with_year):
        """Extract just the title from 'Title (Year)' format."""
        if ' (' in title_with_year and title_with_year.endswith(')'):
            return title_with_year.rsplit(' (', 1)[0]
        return title_with_year
    
    # Default selection
    if media_type == 'tv':
        default_title = "Breaking Bad"
    else:
        default_title = "The Shawshank Redemption"
    
    # Find default index - check both with and without year format
    default_index = 0
    for i, title in enumerate(all_titles):
        if extract_title(title) == default_title or title == default_title:
            default_index = i
            break

    # ===== SIDEBAR =====
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        st.divider()
        
        # Media type toggle (Movies/TV)
        st.markdown("**Content Type**")
        media_type = st.radio(
            "",
            options=['movies', 'tv'],
            format_func=lambda x: '🎬 Movies' if x == 'movies' else '📺 TV Shows',
            key='media_type',
            horizontal=True,
            label_visibility="collapsed",
            index=0
        )
        
        st.divider()
        
        st.markdown("**Number of Results**")
        num_recommendations = st.slider(
            "Results",
            min_value=5,
            max_value=30,
            value=10,
            step=5,
            label_visibility="collapsed"
        )
        
        st.divider()
        
        st.markdown("**Genre Filter**")
        if all_genres:
            genre_filter = st.multiselect(
                "Genre",
                options=all_genres,
                default=[],
                placeholder="All genres",
                label_visibility="collapsed"
            )
        else:
            st.info("Loading genres…")
            genre_filter = []
        
        st.divider()
        
        st.markdown(f"**Multi-{media_type.capitalize()} Mode**")
        multi_mode = st.toggle(
            "Combine favorites", 
            value=False,
            help=f"Get recommendations based on multiple {media_type}"
        )
        
        st.divider()
        
        st.markdown("**Theme**")
        theme_choice = st.radio(
            "",
            options=['light', 'dark'],
            format_func=lambda x: '☀️ Light' if x == 'light' else '🌙 Dark',
            key='theme',
            horizontal=True,
            label_visibility="collapsed"
        )
        
        # Analytics button above How It Works (no divider above)
        if st.button("📊 Analytics Dashboard", use_container_width=True, key="analytics_btn"):
            st.session_state.show_analytics = True
        
        with st.expander("ℹ️ How It Works"):
            st.markdown(f"""
            {media_type.capitalize()} are matched by analyzing genres, cast, plot, and keywords using TF-IDF and cosine similarity.
            """)
            
            # Data source info inside expander
            st.markdown("---")
            st.caption(f"**Data Source:** {data_source}")
            if USE_DATABASE:
                stats = get_database_stats()
                if media_type == 'tv':
                    st.caption(f"TV Shows: {stats.get('total_tv_shows', 0):,}")
                else:
                    st.caption(f"Movies: {stats.get('total_movies', 0):,}")

    # Apply theme CSS
    is_dark = st.session_state.get('theme', 'light') == 'dark'
    st.markdown(get_theme_css(is_dark), unsafe_allow_html=True)

    # ===== MAIN HEADER =====
    header_title = "TV Show Recommender" if media_type == 'tv' else "Movie Recommender"
    header_subtitle = "Discover your next favorite show" if media_type == 'tv' else "Discover your next favorite film"
    st.markdown(f'<h1 class="main-title" id="main-title">{header_title}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="subtitle" id="main-subtitle">{header_subtitle}</p>', unsafe_allow_html=True)
    
    # JavaScript to keep title visible - scroll to top when recommendations load (Option 4: DISABLED)
    # st.markdown("""
    # <script>
    #     (function() {
    #         let hasScrolled = false;
    #         const titleElement = document.getElementById('main-title');
    #         
    #         function scrollToTitle() {
    #             if (titleElement && !hasScrolled) {
    #                 // Small delay to ensure DOM is ready
    #                 setTimeout(() => {
    #                     titleElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    #                     hasScrolled = true;
    #                     // Reset flag after a delay to allow re-scrolling if needed
    #                     setTimeout(() => { hasScrolled = false; }, 2000);
    #                 }, 100);
    #             }
    #         }
    #         
    #         // Watch for recommendations section appearing
    #         const observer = new MutationObserver((mutations) => {
    #             mutations.forEach((mutation) => {
    #                 mutation.addedNodes.forEach((node) => {
    #                     if (node.nodeType === 1) { // Element node
    #                         // Check if this is the recommendations header
    #                         if (node.classList && node.classList.contains('rec-header')) {
    #                             scrollToTitle();
    #                         }
    #                         // Also check children
    #                         const recHeader = node.querySelector && node.querySelector('.rec-header');
    #                         if (recHeader) {
    #                             scrollToTitle();
    #                         }
    #                     }
    #                 });
    #             });
    #         });
    #         
    #         // Start observing after page load
    #         if (document.readyState === 'loading') {
    #             document.addEventListener('DOMContentLoaded', () => {
    #                 observer.observe(document.body, { childList: true, subtree: true });
    #             });
    #         } else {
    #             observer.observe(document.body, { childList: true, subtree: true });
    #         }
    #         
    #         // Also check periodically for rec-header (fallback)
    #         setInterval(() => {
    #             const recHeader = document.querySelector('.rec-header');
    #             if (recHeader && recHeader.offsetParent !== null) {
    #                 scrollToTitle();
    #             }
    #         }, 500);
    #     })();
    # </script>
    # """, unsafe_allow_html=True)
    
    # ===== ANALYTICS (Dialog popup) =====
    if render_analytics:
        @st.dialog(" ", width="large")
        def analytics_dialog():
            render_analytics(is_dark, media_type=media_type)
        
        # Show dialog when button is clicked
        if st.session_state.get('show_analytics', False):
            analytics_dialog()
            # Reset flag after dialog is shown (dialog handles its own close)
            st.session_state.show_analytics = False
    
    # JavaScript for responsive scaling based on window/sidebar size
    st.markdown("""
    <script>
        function updateScaling() {
            const sidebar = document.querySelector('section[data-testid="stSidebar"]');
            const mainContent = document.querySelector('section[data-testid="stMain"] .block-container');
            const root = document.documentElement;
            
            if (!root) return;
            
            // Calculate available width (viewport width minus sidebar if visible)
            let availableWidth = window.innerWidth;
            if (sidebar) {
                const sidebarRect = sidebar.getBoundingClientRect();
                const isOnScreen = sidebarRect.left >= 0 && sidebarRect.left < window.innerWidth;
                if (isOnScreen && sidebarRect.width > 50) {
                    availableWidth = window.innerWidth - sidebarRect.width;
                }
            }
            
            // Calculate scale factor (based on available width, normalized to 1920px = 1.0)
            const baseWidth = 1920;
            const minWidth = 800; // Minimum width before scaling down
            let scaleFactor = 1.0;
            
            if (availableWidth < baseWidth) {
                // Scale down proportionally, but not below minWidth
                const effectiveWidth = Math.max(availableWidth, minWidth);
                scaleFactor = effectiveWidth / baseWidth;
            }
            
            // Update CSS custom properties
            root.style.setProperty('--scale-factor', scaleFactor);
            root.style.setProperty('--available-width', availableWidth + 'px');
            
            // Adjust main content margin for sidebar (using getBoundingClientRect to detect sidebar position)
            if (mainContent && sidebar) {
                const sidebarRect = sidebar.getBoundingClientRect();
                const isOnScreen = sidebarRect.left >= 0 && sidebarRect.left < window.innerWidth;
                if (isOnScreen && sidebarRect.width > 50) {
                    mainContent.style.marginLeft = sidebarRect.width + 'px';
                } else {
                    mainContent.style.marginLeft = 'auto';
                }
            }
        }
        
        // Run on load, resize, and periodically to catch sidebar changes
        window.addEventListener('load', updateScaling);
        window.addEventListener('resize', updateScaling);
        setInterval(updateScaling, 100);
        
        // Also watch for sidebar state changes
        const observer = new MutationObserver(updateScaling);
        observer.observe(document.body, { childList: true, subtree: true, attributes: true });
    </script>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        icon = "📺" if media_type == 'tv' else "🎬"
        if multi_mode:
            # For multiselect, find default with year format
            default_with_year = next((t for t in all_titles if extract_title(t) == default_title), default_title)
            selected_movies_with_year = st.multiselect(
                f"{icon} Select {media_type} (up to 5)",
                options=all_titles,
                default=[default_with_year] if default_with_year in all_titles else [],
                max_selections=5
            )
            # Extract just titles from "Title (Year)" format
            selected_movies = [extract_title(t) for t in selected_movies_with_year]
        else:
            selected_movie_with_year = st.selectbox(
                f"{icon} Select a {'TV show' if media_type == 'tv' else 'movie'}",
                options=all_titles,
                index=default_index
            )
            # Extract just the title from "Title (Year)" format
            selected_movie = extract_title(selected_movie_with_year) if selected_movie_with_year else None
            selected_movies = [selected_movie] if selected_movie else []
        
        st.text("")
        
        recommend_clicked = st.button(
            "🔍 Get Recommendations",
            type="primary",
            use_container_width=True
        )

    # ===== RESULTS =====
    if recommend_clicked and selected_movies:
        media_label = "TV shows" if media_type == 'tv' else "Movies"
        if len(selected_movies) == 1:
            st.markdown(f'<p class="rec-header">{media_label.capitalize()} like {selected_movies[0]}</p>', unsafe_allow_html=True)
        else:
            st.markdown(f'<p class="rec-header">Based on your selection</p>', unsafe_allow_html=True)
        
        if genre_filter:
            st.markdown(f'<p class="rec-subheader">Filtered: {", ".join(genre_filter)}</p>', unsafe_allow_html=True)
        
        with st.spinner(f"Finding {media_label}..."):
            # Use appropriate data source
            if USE_DATABASE:
                rec_movies, posters, urls, providers_list, error = get_recommendations_db(
                    selected_movies,
                    num_of_rec=num_recommendations,
                    genre_filter=genre_filter if genre_filter else None,
                    media_type=media_type
                )
            else:
                rec_movies, posters, urls, error = get_recommendations_pickle(
                    selected_movies,
                    cosine_sim_mat=tfidf,
                    df=movies_df,
                    num_of_rec=num_recommendations,
                    genre_filter=genre_filter if genre_filter else None
                )
                providers_list = None  # Not available in pickle mode yet
        
        if error:
            st.error(f"❌ {error}")
        elif rec_movies:
            num_movies = len(rec_movies)
            num_rows = (num_movies + 4) // 5
            
            # Handle providers_list (might be None for pickle mode)
            if providers_list is None:
                providers_list = [None] * num_movies
            
            for i in range(num_rows):
                cols = st.columns(5, gap='medium')
                for j in range(5):
                    idx = j + (i * 5)
                    if idx >= num_movies:
                        break
                    
                    rating = round(rec_movies[idx].vote_average, 1)
                    title = rec_movies[idx].title
                    year_val = rec_movies[idx].year
                    year = int(year_val) if year_val else 0
                    
                    provider_badges = ""  # Empty for now
                    
                    with cols[j]:
                        if posters[idx]:
                            st.markdown(f'''
                                <a href="{urls[idx]}" target="_blank" style="text-decoration:none;">
                                    <div class="poster-card">
                                        <img src="{posters[idx]}" alt="{title}" title="⭐ {rating}/10">
                                    </div>
                                </a>
                                <p class="movie-title">{title} <span class="movie-year">({year})</span></p>
                                {provider_badges}
                            ''', unsafe_allow_html=True)
                        else:
                            st.markdown(f'''
                                <div class="no-poster">🎬</div>
                                <p class="movie-title">{title} <span class="movie-year">({year})</span></p>
                                {provider_badges}
                            ''', unsafe_allow_html=True)
    
    elif recommend_clicked:
        st.warning(f"Please select at least one {'TV show' if media_type == 'tv' else 'movie'}.")

    st.markdown('<p class="footer">Made with ❤️</p>', unsafe_allow_html=True)


if __name__ == '__main__':
    main()
