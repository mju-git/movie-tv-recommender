"""
Movie Analytics Dashboard
Visualizations and insights from the movie database.
Demonstrates: SQL queries, data analysis, Plotly visualizations.
Can be imported as a module or run standalone.
"""
import sys
from pathlib import Path

# Add project root to path (works both as module and standalone)
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from src.config import Config

# Check if database exists
DB_PATH = Path(Config.DATA_PATH) / "movies.db"
USE_DATABASE = DB_PATH.exists()

if USE_DATABASE:
    from src.database import (
        get_genre_counts,
        get_ratings_by_decade,
        get_top_directors,
        get_genre_rating_stats,
        get_rating_distribution,
        get_movies_per_year,
        get_database_stats,
        get_all_movies,
        # TV show analytics
        get_tv_genre_counts,
        get_tv_ratings_by_decade,
        get_top_creators,
        get_tv_genre_rating_stats,
        get_tv_rating_distribution,
        get_tv_shows_per_year
    )

# Only set page config when running standalone
if __name__ == '__main__':
    st.set_page_config(
        page_title="Movie Analytics", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )

# ============ THEME ============

def get_theme_colors(is_dark):
    """Get color scheme based on theme."""
    if is_dark:
        return {
            'bg': '#141414',
            'text': '#ffffff',
            'accent': '#e50914',
            'secondary': '#b81d24',
            'grid': '#333333',
            'paper': '#1a1a1a',
            'colors': ['#e50914', '#b81d24', '#831010', '#ff6b6b', '#ff8e8e', '#ffa5a5']
        }
    else:
        return {
            'bg': '#fafafa',
            'text': '#1a1a1a',
            'accent': '#e50914',
            'secondary': '#b81d24',
            'grid': '#e0e0e0',
            'paper': '#ffffff',
            'colors': ['#e50914', '#b81d24', '#ff6b6b', '#ff8e8e', '#ffa5a5', '#ffcccc']
        }

def get_theme_css(is_dark):
    """CSS for the analytics page."""
    if is_dark:
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
            .stApp { background-color: #141414; }
            #MainMenu, footer, header { visibility: hidden; }
            html, body, [class*="css"], p, span, label, div, h1, h2, h3 {
                font-family: 'Inter', sans-serif;
                color: #ffffff !important;
            }
            .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #e50914 !important; margin-bottom: 0.5rem; }
            .subtitle { text-align: center; color: #ffffff !important; opacity: 0.8; margin-bottom: 2rem; }
            .metric-card { background: #1a1a1a; border-radius: 12px; padding: 1.5rem; text-align: center; }
            .metric-value { font-size: 2.5rem; font-weight: 700; color: #e50914 !important; }
            .metric-label { font-size: 0.9rem; color: #ffffff !important; opacity: 0.7; }
            .section-title { color: #ffffff !important; font-size: 1.3rem; font-weight: 600; margin: 2rem 0 1rem 0; }
            .insight-box { background: #1a1a1a; border-left: 4px solid #e50914; padding: 1rem; border-radius: 0 8px 8px 0; margin: 1rem 0; }
            section[data-testid="stSidebar"] { background-color: #0d0d0d; }
            section[data-testid="stSidebar"] * { color: #ffffff !important; }
        </style>
        """
    else:
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
            .stApp { background-color: #fafafa; }
            #MainMenu, footer, header { visibility: hidden; }
            html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #1a1a1a; }
            .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #e50914 !important; margin-bottom: 0.5rem; }
            .subtitle { text-align: center; color: #666666; margin-bottom: 2rem; }
            .metric-card { background: #ffffff; border-radius: 12px; padding: 1.5rem; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            .metric-value { font-size: 2.5rem; font-weight: 700; color: #e50914 !important; }
            .metric-label { font-size: 0.9rem; color: #666666; }
            .section-title { color: #1a1a1a; font-size: 1.3rem; font-weight: 600; margin: 2rem 0 1rem 0; }
            .insight-box { background: #ffffff; border-left: 4px solid #e50914; padding: 1rem; border-radius: 0 8px 8px 0; margin: 1rem 0; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
            section[data-testid="stSidebar"] { background-color: #ffffff; }
        </style>
        """

# ============ CHART FUNCTIONS ============

def create_genre_bar_chart(genre_counts: dict, colors: dict, x_label: str = 'Count') -> go.Figure:
    """Create a horizontal bar chart of genre distribution."""
    df = pd.DataFrame(list(genre_counts.items()), columns=['Genre', 'Count'])
    df = df.sort_values('Count', ascending=True).tail(15)  # Top 15
    
    fig = px.bar(
        df, 
        x='Count', 
        y='Genre', 
        orientation='h',
        color='Count',
        color_continuous_scale=[[0, colors['colors'][4]], [1, colors['accent']]]
    )
    
    fig.update_layout(
        plot_bgcolor=colors['paper'],
        paper_bgcolor=colors['paper'],
        font_color=colors['text'],
        showlegend=False,
        coloraxis_showscale=False,
        xaxis=dict(gridcolor=colors['grid'], title=x_label),
        yaxis=dict(gridcolor=colors['grid'], title=''),
        margin=dict(l=0, r=0, t=20, b=0)
    )
    
    return fig


def create_ratings_line_chart(ratings_df: pd.DataFrame, colors: dict) -> go.Figure:
    """Create a line chart of ratings over decades."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=ratings_df['decade'],
        y=ratings_df['avg_rating'],
        mode='lines+markers',
        name='Avg Rating',
        line=dict(color=colors['accent'], width=3),
        marker=dict(size=10)
    ))
    
    fig.update_layout(
        plot_bgcolor=colors['paper'],
        paper_bgcolor=colors['paper'],
        font_color=colors['text'],
        xaxis=dict(
            gridcolor=colors['grid'], 
            title='Decade',
            tickmode='array',
            tickvals=ratings_df['decade'].tolist()
        ),
        yaxis=dict(gridcolor=colors['grid'], title='Average Rating', range=[6, 9]),
        margin=dict(l=0, r=0, t=20, b=0),
        hovermode='x unified'
    )
    
    return fig


def create_directors_bar_chart(people_df: pd.DataFrame, colors: dict) -> go.Figure:
    """Create a bar chart of top directors/creators."""
    df = people_df.head(10).copy()
    
    # Handle both director/creator and movie_count/show_count columns
    person_col = 'creator' if 'creator' in df.columns else 'director'
    count_col = 'show_count' if 'show_count' in df.columns else 'movie_count'
    
    fig = px.bar(
        df,
        x='avg_rating',
        y=person_col,
        orientation='h',
        color=count_col,
        color_continuous_scale=[[0, colors['colors'][4]], [1, colors['accent']]],
        hover_data=[count_col]
    )
    
    fig.update_layout(
        plot_bgcolor=colors['paper'],
        paper_bgcolor=colors['paper'],
        font_color=colors['text'],
        showlegend=False,
        coloraxis_showscale=False,
        xaxis=dict(gridcolor=colors['grid'], title='Average Rating', range=[7, 9]),
        yaxis=dict(gridcolor=colors['grid'], title=''),
        margin=dict(l=0, r=0, t=20, b=0)
    )
    
    return fig


def create_rating_histogram(rating_dist: pd.DataFrame, colors: dict, is_tv: bool = False) -> go.Figure:
    """Create a histogram of rating distribution."""
    # Handle both 'count' and 'show_count' columns
    count_col = 'show_count' if 'show_count' in rating_dist.columns else 'count'
    
    fig = px.bar(
        rating_dist,
        x='rating_bucket',
        y=count_col,
        color=count_col,
        color_continuous_scale=[[0, colors['colors'][4]], [1, colors['accent']]]
    )
    
    y_label = 'Number of TV Shows' if is_tv else 'Number of Movies'
    
    fig.update_layout(
        plot_bgcolor=colors['paper'],
        paper_bgcolor=colors['paper'],
        font_color=colors['text'],
        showlegend=False,
        coloraxis_showscale=False,
        xaxis=dict(gridcolor=colors['grid'], title='Rating', dtick=1),
        yaxis=dict(gridcolor=colors['grid'], title=y_label),
        margin=dict(l=0, r=0, t=20, b=0)
    )
    
    return fig


def create_genre_rating_box(genre_stats: pd.DataFrame, colors: dict) -> go.Figure:
    """Create a bar chart comparing genre ratings."""
    df = genre_stats.sort_values('avg_rating', ascending=True).tail(12)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['avg_rating'],
        y=df['genre'],
        orientation='h',
        marker_color=colors['accent'],
        text=df['avg_rating'].round(2),
        textposition='outside'
    ))
    
    fig.update_layout(
        plot_bgcolor=colors['paper'],
        paper_bgcolor=colors['paper'],
        font_color=colors['text'],
        xaxis=dict(gridcolor=colors['grid'], title='Average Rating', range=[6.5, 8.5]),
        yaxis=dict(gridcolor=colors['grid'], title=''),
        margin=dict(l=0, r=0, t=20, b=0)
    )
    
    return fig


def create_movies_per_year(items_year: pd.DataFrame, colors: dict) -> go.Figure:
    """Create an area chart of movies/TV shows per year."""
    # Filter to recent decades for cleaner visualization
    df = items_year[items_year['year'] >= 1970].copy()
    
    # Handle both movie_count and show_count columns
    count_col = 'show_count' if 'show_count' in df.columns else 'movie_count'
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['year'],
        y=df[count_col],
        fill='tozeroy',
        mode='lines',
        line=dict(color=colors['accent'], width=2),
        fillcolor=f"rgba(229, 9, 20, 0.3)"
    ))
    
    y_label = 'Number of TV Shows' if count_col == 'show_count' else 'Number of Movies'
    
    fig.update_layout(
        plot_bgcolor=colors['paper'],
        paper_bgcolor=colors['paper'],
        font_color=colors['text'],
        xaxis=dict(gridcolor=colors['grid'], title='Year'),
        yaxis=dict(gridcolor=colors['grid'], title=y_label),
        margin=dict(l=0, r=0, t=20, b=0),
        hovermode='x unified'
    )
    
    return fig


# ============ MAIN ============

def render_analytics(is_dark: bool = False, media_type: str = 'movies'):
    """Render analytics content. Can be called from main.py or run standalone.
    
    Args:
        is_dark: Whether to use dark theme colors for charts
        media_type: 'movies' or 'tv' to show appropriate analytics
    """
    colors = get_theme_colors(is_dark)
    
    # Title based on media type
    if media_type == 'tv':
        st.markdown('<h1 class="main-title">📊 TV Show Analytics</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Insights and trends from our TV show database</p>', unsafe_allow_html=True)
    else:
        st.markdown('<h1 class="main-title">📊 Movie Analytics</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Insights and trends from our movie database</p>', unsafe_allow_html=True)
    
    # Check if database exists
    if not USE_DATABASE:
        st.error("⚠️ Database not found. Please run the migration script first:")
        if media_type == 'tv':
            st.code("python scripts/migrate_tv_to_db.py", language="bash")
        else:
            st.code("python scripts/migrate_to_db.py", language="bash")
        st.info("This page requires the SQLite database to display analytics.")
        return
    
    # Get data based on media type
    try:
        stats = get_database_stats()
        
        if media_type == 'tv':
            genre_counts = get_tv_genre_counts()
            ratings_decade = get_tv_ratings_by_decade()
            top_creators = get_top_creators(min_shows=2, limit=15)
            genre_stats = get_tv_genre_rating_stats()
            rating_dist = get_tv_rating_distribution()
            items_year = get_tv_shows_per_year()
            top_people = top_creators  # For consistency in variable names
            people_label = "Creators"
            item_label = "TV Shows"
        else:
            genre_counts = get_genre_counts()
            ratings_decade = get_ratings_by_decade()
            top_directors = get_top_directors(min_movies=3, limit=15)
            genre_stats = get_genre_rating_stats()
            rating_dist = get_rating_distribution()
            items_year = get_movies_per_year()
            top_people = top_directors
            people_label = "Directors"
            item_label = "Movies"
    except Exception as e:
        st.error(f"Error loading data: {e}")
        if media_type == 'tv':
            st.info("Make sure you've run the migration script: `python scripts/migrate_tv_to_db.py`")
        else:
            st.info("Make sure you've run the migration script: `python scripts/migrate_to_db.py`")
        return
    
    # ===== KEY METRICS =====
    st.markdown('<p class="section-title">📈 Key Metrics</p>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if media_type == 'tv':
            total_key = "total_tv_shows"
            label = "Total TV Shows"
        else:
            total_key = "total_movies"
            label = "Total Movies"
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-value">{stats.get(total_key, 0):,}</div>
                <div class="metric-label">{label}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-value">{stats.get("total_genres", 0)}</div>
                <div class="metric-label">Genres</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        if media_type == 'tv':
            people_key = "total_creators"
            people_label = "Creators"
        else:
            people_key = "total_directors"
            people_label = "Directors"
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-value">{stats.get(people_key, 0):,}</div>
                <div class="metric-label">{people_label}</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-value">{stats.get("total_actors", 0):,}</div>
                <div class="metric-label">Actors</div>
            </div>
        ''', unsafe_allow_html=True)
    
    st.text("")
    st.text("")
    
    # ===== CHARTS ROW 1 =====
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<p class="section-title">🎭 Genre Distribution</p>', unsafe_allow_html=True)
        if genre_counts:
            x_label = f'Number of {item_label}' if media_type == 'tv' else 'Number of Movies'
            fig = create_genre_bar_chart(genre_counts, colors, x_label=x_label)
            st.plotly_chart(fig, use_container_width=True)
            top_genre = max(genre_counts, key=genre_counts.get)
            st.markdown(f'''
                <div class="insight-box">
                    <strong>💡 Insight:</strong> {top_genre} is the most common genre with {genre_counts[top_genre]:,} {item_label.lower()}.
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.info("No genre data available.")
    
    with col2:
        st.markdown('<p class="section-title">⭐ Ratings Over Decades</p>', unsafe_allow_html=True)
        if len(ratings_decade) > 0:
            fig = create_ratings_line_chart(ratings_decade, colors)
            st.plotly_chart(fig, use_container_width=True)
            best_decade = ratings_decade.loc[ratings_decade['avg_rating'].idxmax()]
            count_col = 'show_count' if media_type == 'tv' else 'movie_count'
            st.markdown(f'''
                <div class="insight-box">
                    <strong>💡 Insight:</strong> The {int(best_decade['decade'])}s had the highest average rating ({best_decade['avg_rating']:.2f}).
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.info("No ratings data available.")
    
    # ===== CHARTS ROW 2 =====
    col1, col2 = st.columns(2)
    
    with col1:
        title = f'🎬 Top {people_label} (by avg rating)' if media_type == 'tv' else '🎬 Top Directors (by avg rating)'
        st.markdown(f'<p class="section-title">{title}</p>', unsafe_allow_html=True)
        if len(top_people) > 0:
            fig = create_directors_bar_chart(top_people, colors)
            st.plotly_chart(fig, use_container_width=True)
            top_person = top_people.iloc[0]
            person_col = 'creator' if media_type == 'tv' else 'director'
            count_col = 'show_count' if media_type == 'tv' else 'movie_count'
            item_word = 'shows' if media_type == 'tv' else 'films'
            st.markdown(f'''
                <div class="insight-box">
                    <strong>💡 Insight:</strong> {top_person[person_col]} leads with {top_person['avg_rating']:.2f} avg rating across {int(top_person[count_col])} {item_word}.
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.info(f"No {people_label.lower()} data available.")
    
    with col2:
        st.markdown('<p class="section-title">📊 Rating Distribution</p>', unsafe_allow_html=True)
        if len(rating_dist) > 0:
            fig = create_rating_histogram(rating_dist, colors, is_tv=(media_type == 'tv'))
            st.plotly_chart(fig, use_container_width=True)
            count_col = 'show_count' if media_type == 'tv' else 'count'
            most_common = rating_dist.loc[rating_dist[count_col].idxmax()]
            st.markdown(f'''
                <div class="insight-box">
                    <strong>💡 Insight:</strong> Most {item_label.lower()} have a rating around {int(most_common['rating_bucket'])} ({most_common[count_col]:,} {item_label.lower()}).
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.info("No rating distribution data available.")
    
    # ===== CHARTS ROW 3 =====
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<p class="section-title">🏆 Genres by Average Rating</p>', unsafe_allow_html=True)
        if len(genre_stats) > 0:
            fig = create_genre_rating_box(genre_stats, colors)
            st.plotly_chart(fig, use_container_width=True)
            top_rated_genre = genre_stats.loc[genre_stats['avg_rating'].idxmax()]
            st.markdown(f'''
                <div class="insight-box">
                    <strong>💡 Insight:</strong> {top_rated_genre['genre']} movies have the highest average rating ({top_rated_genre['avg_rating']:.2f}).
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.info("No genre rating data available.")
    
    with col2:
        title = f'📅 {item_label} Per Year' if media_type == 'tv' else '📅 Movies Per Year'
        st.markdown(f'<p class="section-title">{title}</p>', unsafe_allow_html=True)
        if len(items_year) > 0:
            fig = create_movies_per_year(items_year, colors)
            st.plotly_chart(fig, use_container_width=True)
            count_col = 'show_count' if media_type == 'tv' else 'movie_count'
            peak_year = items_year.loc[items_year[count_col].idxmax()]
            item_word = 'shows' if media_type == 'tv' else 'films'
            st.markdown(f'''
                <div class="insight-box">
                    <strong>💡 Insight:</strong> {int(peak_year['year'])} had the most {item_label.lower()} in our database ({int(peak_year[count_col])} {item_word}).
                </div>
            ''', unsafe_allow_html=True)
        else:
            st.info("No yearly data available.")
    
    # ===== SQL SHOWCASE =====
    st.markdown('<p class="section-title">🔍 SQL Queries Used</p>', unsafe_allow_html=True)
    
    with st.expander("View SQL queries powering this dashboard"):
        st.markdown("**Genre Distribution Query:**")
        st.code("""
SELECT g.name, COUNT(mg.movie_id) as count
FROM genres g
JOIN movie_genres mg ON g.id = mg.genre_id
GROUP BY g.id, g.name
ORDER BY count DESC
        """, language="sql")
        
        st.markdown("**Ratings by Decade Query:**")
        st.code("""
SELECT 
    (year / 10) * 10 as decade,
    AVG(vote_average) as avg_rating,
    COUNT(*) as movie_count
FROM movies
WHERE year IS NOT NULL
GROUP BY decade
ORDER BY decade
        """, language="sql")
        
        st.markdown("**Top Directors Query:**")
        st.code("""
SELECT 
    p.name as director,
    AVG(m.vote_average) as avg_rating,
    COUNT(m.id) as movie_count
FROM people p
JOIN movie_people mp ON p.id = mp.person_id
JOIN movies m ON mp.movie_id = m.id
WHERE p.role = 'director'
GROUP BY p.id, p.name
HAVING COUNT(m.id) >= 3
ORDER BY avg_rating DESC
LIMIT 15
        """, language="sql")
    
    # Footer
    st.markdown('<p style="text-align:center; opacity:0.5; margin-top:3rem;">Analytics Dashboard • SQL + Plotly</p>', unsafe_allow_html=True)


def main():
    """Standalone entry point with its own theme selector."""
    # Theme toggle in sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        theme_choice = st.radio(
            "Theme",
            options=['light', 'dark'],
            format_func=lambda x: '☀️ Light' if x == 'light' else '🌙 Dark',
            key='analytics_theme',
            horizontal=True
        )
    
    is_dark = theme_choice == 'dark'
    
    # Apply CSS
    st.markdown(get_theme_css(is_dark), unsafe_allow_html=True)
    
    # Render analytics content
    render_analytics(is_dark)


if __name__ == '__main__':
    main()

