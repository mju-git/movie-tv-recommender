"""
SQLite Database Module for Movie Recommender System.
Handles database connection, schema creation, and query operations.
"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import pandas as pd

from src.config import Config

# Database path
DB_PATH = Path(Config.DATA_PATH) / "movies.db"


@dataclass
class Movie:
    """Movie data class for type-safe movie objects."""
    id: int
    imdb_id: str
    title: str
    year: int
    vote_average: float
    overview: str = ""
    tagline: str = ""


def get_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def create_tables():
    """Create all database tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Movies table - main movie information
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY,
            imdb_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            year INTEGER,
            vote_average REAL,
            vote_count INTEGER,
            overview TEXT,
            tagline TEXT,
            soup TEXT,
            poster_url TEXT,
            watch_providers TEXT
        )
    """)
    
    # Genres table - normalized genres
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS genres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)
    
    # Movie-Genre junction table (many-to-many)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movie_genres (
            movie_id INTEGER,
            genre_id INTEGER,
            PRIMARY KEY (movie_id, genre_id),
            FOREIGN KEY (movie_id) REFERENCES movies(id),
            FOREIGN KEY (genre_id) REFERENCES genres(id)
        )
    """)
    
    # People table - actors and directors
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            UNIQUE(name, role)
        )
    """)
    
    # Movie-People junction table (many-to-many)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movie_people (
            movie_id INTEGER,
            person_id INTEGER,
            PRIMARY KEY (movie_id, person_id),
            FOREIGN KEY (movie_id) REFERENCES movies(id),
            FOREIGN KEY (person_id) REFERENCES people(id)
        )
    """)
    
    # Similarity cache - pre-computed similarity scores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS similarity_cache (
            movie_id_1 INTEGER,
            movie_id_2 INTEGER,
            score REAL NOT NULL,
            PRIMARY KEY (movie_id_1, movie_id_2),
            FOREIGN KEY (movie_id_1) REFERENCES movies(id),
            FOREIGN KEY (movie_id_2) REFERENCES movies(id)
        )
    """)
    
    # =========================================================================
    # TV SHOW TABLES
    # =========================================================================
    
    # TV Shows table - main TV show information
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tv_shows (
            id INTEGER PRIMARY KEY,
            imdb_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            year INTEGER,
            vote_average REAL,
            vote_count INTEGER,
            number_of_seasons INTEGER,
            number_of_episodes INTEGER,
            status TEXT,
            overview TEXT,
            tagline TEXT,
            soup TEXT,
            poster_url TEXT,
            watch_providers TEXT
        )
    """)
    
    # TV-Genre junction table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tv_genres (
            tv_id INTEGER,
            genre_id INTEGER,
            PRIMARY KEY (tv_id, genre_id),
            FOREIGN KEY (tv_id) REFERENCES tv_shows(id),
            FOREIGN KEY (genre_id) REFERENCES genres(id)
        )
    """)
    
    # TV-People junction table (actors, creators)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tv_people (
            tv_id INTEGER,
            person_id INTEGER,
            PRIMARY KEY (tv_id, person_id),
            FOREIGN KEY (tv_id) REFERENCES tv_shows(id),
            FOREIGN KEY (person_id) REFERENCES people(id)
        )
    """)
    
    # TV Similarity cache
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tv_similarity_cache (
            tv_id_1 INTEGER,
            tv_id_2 INTEGER,
            score REAL NOT NULL,
            PRIMARY KEY (tv_id_1, tv_id_2),
            FOREIGN KEY (tv_id_1) REFERENCES tv_shows(id),
            FOREIGN KEY (tv_id_2) REFERENCES tv_shows(id)
        )
    """)
    
    # Create indexes for faster queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_movies_title ON movies(title)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_movies_year ON movies(year)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_movies_rating ON movies(vote_average)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_genres_name ON genres(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_people_name ON people(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_similarity_score ON similarity_cache(score DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tv_title ON tv_shows(title)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tv_year ON tv_shows(year)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tv_similarity_score ON tv_similarity_cache(score DESC)")
    
    conn.commit()
    conn.close()
    print("Database tables created successfully.")
    
    # Run migration to add poster_url and watch_providers if needed
    migrate_add_poster_and_providers()


def migrate_add_poster_and_providers(quiet: bool = False):
    """
    Migration: Add poster_url and watch_providers columns to existing databases.
    Safe to run multiple times - checks if columns exist first.
    
    Args:
        quiet: If True, suppress print statements (useful for Streamlit)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if poster_url column exists in movies table
        cursor.execute("PRAGMA table_info(movies)")
        movies_columns = [col[1] for col in cursor.fetchall()]
        
        if 'poster_url' not in movies_columns:
            if not quiet:
                print("Adding poster_url and watch_providers columns to movies table...")
            cursor.execute("ALTER TABLE movies ADD COLUMN poster_url TEXT")
            cursor.execute("ALTER TABLE movies ADD COLUMN watch_providers TEXT")
            if not quiet:
                print("✓ Movies table updated")
        
        # Check if poster_url column exists in tv_shows table
        cursor.execute("PRAGMA table_info(tv_shows)")
        tv_columns = [col[1] for col in cursor.fetchall()]
        
        if 'poster_url' not in tv_columns:
            if not quiet:
                print("Adding poster_url and watch_providers columns to tv_shows table...")
            cursor.execute("ALTER TABLE tv_shows ADD COLUMN poster_url TEXT")
            cursor.execute("ALTER TABLE tv_shows ADD COLUMN watch_providers TEXT")
            if not quiet:
                print("✓ TV shows table updated")
        
        conn.commit()
        if not quiet:
            print("Migration completed successfully!")
        
    except Exception as e:
        if not quiet:
            print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()


def drop_tables():
    """Drop all tables (for resetting the database)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Movie tables
    cursor.execute("DROP TABLE IF EXISTS similarity_cache")
    cursor.execute("DROP TABLE IF EXISTS movie_people")
    cursor.execute("DROP TABLE IF EXISTS movie_genres")
    cursor.execute("DROP TABLE IF EXISTS movies")
    
    # TV tables
    cursor.execute("DROP TABLE IF EXISTS tv_similarity_cache")
    cursor.execute("DROP TABLE IF EXISTS tv_people")
    cursor.execute("DROP TABLE IF EXISTS tv_genres")
    cursor.execute("DROP TABLE IF EXISTS tv_shows")
    
    # Shared tables
    cursor.execute("DROP TABLE IF EXISTS people")
    cursor.execute("DROP TABLE IF EXISTS genres")
    
    conn.commit()
    conn.close()
    print("All tables dropped.")


# ============ INSERT FUNCTIONS ============

def insert_movie(conn: sqlite3.Connection, movie_data: Dict) -> int:
    """Insert a movie and return its ID."""
    import json
    cursor = conn.cursor()
    
    # Convert watch_providers dict to JSON string
    watch_providers = movie_data.get('watch_providers', {})
    watch_providers_json = json.dumps(watch_providers) if watch_providers else None
    
    cursor.execute("""
        INSERT OR REPLACE INTO movies (id, imdb_id, title, year, vote_average, vote_count, overview, tagline, soup, poster_url, watch_providers)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        movie_data.get('id'),
        movie_data.get('imdb_id'),
        movie_data.get('title'),
        movie_data.get('year'),
        movie_data.get('vote_average'),
        movie_data.get('vote_count'),
        movie_data.get('overview', ''),
        movie_data.get('tagline', ''),
        movie_data.get('soup', ''),
        movie_data.get('poster_url'),
        watch_providers_json
    ))
    return cursor.lastrowid


def insert_tv_show(conn: sqlite3.Connection, tv_data: Dict) -> int:
    """Insert a TV show and return its ID."""
    import json
    cursor = conn.cursor()
    
    # Convert watch_providers dict to JSON string
    watch_providers = tv_data.get('watch_providers', {})
    watch_providers_json = json.dumps(watch_providers) if watch_providers else None
    
    cursor.execute("""
        INSERT OR REPLACE INTO tv_shows 
        (id, imdb_id, title, year, vote_average, vote_count, number_of_seasons, 
         number_of_episodes, status, overview, tagline, soup, poster_url, watch_providers)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tv_data.get('id'),
        tv_data.get('imdb_id'),
        tv_data.get('title'),
        tv_data.get('year'),
        tv_data.get('vote_average'),
        tv_data.get('vote_count'),
        tv_data.get('number_of_seasons'),
        tv_data.get('number_of_episodes'),
        tv_data.get('status'),
        tv_data.get('overview', ''),
        tv_data.get('tagline', ''),
        tv_data.get('soup', ''),
        tv_data.get('poster_url'),
        watch_providers_json
    ))
    return cursor.lastrowid


def insert_genre(conn: sqlite3.Connection, name: str) -> int:
    """Insert a genre and return its ID."""
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", (name,))
    cursor.execute("SELECT id FROM genres WHERE name = ?", (name,))
    return cursor.fetchone()[0]


def insert_person(conn: sqlite3.Connection, name: str, role: str) -> int:
    """Insert a person (actor/director) and return their ID."""
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO people (name, role) VALUES (?, ?)", (name, role))
    cursor.execute("SELECT id FROM people WHERE name = ? AND role = ?", (name, role))
    return cursor.fetchone()[0]


def link_movie_genre(conn: sqlite3.Connection, movie_id: int, genre_id: int):
    """Link a movie to a genre."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO movie_genres (movie_id, genre_id) VALUES (?, ?)",
        (movie_id, genre_id)
    )


def link_movie_person(conn: sqlite3.Connection, movie_id: int, person_id: int):
    """Link a movie to a person."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO movie_people (movie_id, person_id) VALUES (?, ?)",
        (movie_id, person_id)
    )


def link_tv_genre(conn: sqlite3.Connection, tv_id: int, genre_id: int):
    """Link a TV show to a genre."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO tv_genres (tv_id, genre_id) VALUES (?, ?)",
        (tv_id, genre_id)
    )


def link_tv_person(conn: sqlite3.Connection, tv_id: int, person_id: int):
    """Link a TV show to a person (actor/creator)."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO tv_people (tv_id, person_id) VALUES (?, ?)",
        (tv_id, person_id)
    )


def insert_similarity(conn: sqlite3.Connection, movie_id_1: int, movie_id_2: int, score: float):
    """Insert a similarity score between two movies."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO similarity_cache (movie_id_1, movie_id_2, score) VALUES (?, ?, ?)",
        (movie_id_1, movie_id_2, score)
    )


def insert_tv_similarity(conn: sqlite3.Connection, tv_id_1: int, tv_id_2: int, score: float):
    """Insert a similarity score between two TV shows."""
    cursor = conn.cursor()
    # Ensure IDs are Python ints (not numpy ints) to avoid BLOB storage
    tv_id_1 = int(tv_id_1) if tv_id_1 is not None else None
    tv_id_2 = int(tv_id_2) if tv_id_2 is not None else None
    cursor.execute(
        "INSERT OR REPLACE INTO tv_similarity_cache (tv_id_1, tv_id_2, score) VALUES (?, ?, ?)",
        (tv_id_1, tv_id_2, float(score))
    )


# ============ QUERY FUNCTIONS ============

def search_movies(query: str, limit: int = 10) -> List[Dict]:
    """
    Search for movies by title (case-insensitive partial match).
    
    SQL: SELECT with LIKE clause
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, imdb_id, title, year, vote_average
        FROM movies
        WHERE title LIKE ?
        ORDER BY vote_average DESC
        LIMIT ?
    """, (f"%{query}%", limit))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_movie_by_title(title: str) -> Optional[Dict]:
    """
    Get a movie by exact title match.
    
    SQL: SELECT with WHERE clause
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, imdb_id, title, year, vote_average, overview, tagline
        FROM movies
        WHERE title = ?
    """, (title,))
    
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_movie_by_id(movie_id: int) -> Optional[Dict]:
    """Get a movie by its ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, imdb_id, title, year, vote_average, overview, tagline
        FROM movies
        WHERE id = ?
    """, (movie_id,))
    
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_movies() -> pd.DataFrame:
    """
    Get all movies as a DataFrame.
    
    SQL: SELECT all from movies table
    """
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM movies ORDER BY title", conn)
    conn.close()
    return df


def get_existing_imdb_ids() -> set:
    """
    Get all IMDB IDs currently in the database.
    Used for incremental scraping to skip already-downloaded movies.
    
    Returns:
        Set of IMDB IDs (e.g., {'tt0111161', 'tt0068646', ...})
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT imdb_id FROM movies WHERE imdb_id IS NOT NULL")
    ids = {row[0] for row in cursor.fetchall()}
    conn.close()
    return ids


def get_existing_tv_imdb_ids() -> set:
    """
    Get all TV show IMDB IDs currently in the database.
    Used for incremental scraping to skip already-downloaded shows.
    
    Returns:
        Set of IMDB IDs (e.g., {'tt0903747', 'tt0944947', ...})
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT imdb_id FROM tv_shows WHERE imdb_id IS NOT NULL")
        ids = {row[0] for row in cursor.fetchall()}
    except:
        ids = set()  # Table might not exist yet
    conn.close()
    return ids


def get_all_titles() -> List[str]:
    """
    Get all movie titles sorted by weighted rating (Bayesian average).
    Returns titles with year in format: "Title (Year)" for dropdown display.
    
    This prevents rating inflation from movies with few votes.
    Formula: weighted = (v/(v+m)) * R + (m/(v+m)) * C
    
    Where:
    - R = movie's vote_average
    - v = movie's vote_count
    - m = minimum votes threshold (1000)
    - C = mean rating across all movies (~6.5)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Calculate weighted rating in SQL
    # m = 1000 (minimum votes), C = 6.5 (approximate mean rating)
    cursor.execute("""
        SELECT title, year,
               (COALESCE(vote_count, 0) / (COALESCE(vote_count, 0) + 1000.0)) * COALESCE(vote_average, 0) +
               (1000.0 / (COALESCE(vote_count, 0) + 1000.0)) * 6.5 AS weighted_rating
        FROM movies 
        ORDER BY weighted_rating DESC, title ASC
    """)
    # Format as "Title (Year)" or just "Title" if year is None
    titles = []
    for row in cursor.fetchall():
        title = row[0]
        year = row[1]
        if year is not None and year != '':
            titles.append(f"{title} ({int(year)})")
        else:
            titles.append(title)
    conn.close()
    return titles


def get_all_tv_titles() -> List[str]:
    """
    Get all TV show titles sorted by weighted rating (Bayesian average).
    Returns titles with year in format: "Title (Year)" for dropdown display.
    Same formula as movies but for TV shows.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT title, year,
               (COALESCE(vote_count, 0) / (COALESCE(vote_count, 0) + 1000.0)) * COALESCE(vote_average, 0) +
               (1000.0 / (COALESCE(vote_count, 0) + 1000.0)) * 6.5 AS weighted_rating
        FROM tv_shows 
        ORDER BY weighted_rating DESC, title ASC
    """)
    # Format as "Title (Year)" or just "Title" if year is None
    titles = []
    for row in cursor.fetchall():
        title = row[0]
        year = row[1]
        if year is not None and year != '':
            titles.append(f"{title} ({int(year)})")
        else:
            titles.append(title)
    conn.close()
    return titles


def get_tv_by_title(title: str) -> Dict:
    """Get a TV show by its exact title."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, imdb_id, title, year, vote_average, vote_count,
               number_of_seasons, number_of_episodes, status, overview
        FROM tv_shows 
        WHERE title = ?
    """, (title,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_tv_recommendations_from_cache(tv_id: int, limit: int = 10) -> List[Dict]:
    """
    Get TV show recommendations from the pre-computed similarity cache.
    
    SQL: JOIN between tv_similarity_cache and tv_shows tables
    Includes watch_providers in the query for efficiency.
    Matches the structure of get_recommendations_from_cache() for movies.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Try JOIN first (most efficient)
    cursor.execute("""
        SELECT t.id, t.imdb_id, t.title, t.year, t.vote_average, 
               t.watch_providers, s.score
        FROM tv_similarity_cache s
        JOIN tv_shows t ON s.tv_id_2 = t.id
        WHERE s.tv_id_1 = ?
        ORDER BY s.score DESC
        LIMIT ?
    """, (tv_id, limit))
    
    results = [dict(row) for row in cursor.fetchall()]
    
    # If JOIN returns no results, try two-step approach (fallback)
    # This handles cases where IDs might not match exactly
    if len(results) == 0:
        # Get similarity scores
        cursor.execute("""
            SELECT tv_id_2, score
            FROM tv_similarity_cache
            WHERE tv_id_1 = ?
            ORDER BY score DESC
            LIMIT ?
        """, (tv_id, limit))
        
        sim_scores = cursor.fetchall()
        
        # Get TV show details for each recommended ID
        for other_id, score in sim_scores:
            cursor.execute("""
                SELECT id, imdb_id, title, year, vote_average, watch_providers
                FROM tv_shows
                WHERE id = ?
            """, (other_id,))
            tv_row = cursor.fetchone()
            if tv_row:
                result_dict = dict(tv_row)
                result_dict['score'] = score
                results.append(result_dict)
    
    conn.close()
    return results


def get_recommendations_from_cache(movie_id: int, limit: int = 10) -> List[Dict]:
    """
    Get movie recommendations from the pre-computed similarity cache.
    
    SQL: JOIN between similarity_cache and movies tables
    Includes watch_providers in the query for efficiency.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT m.id, m.imdb_id, m.title, m.year, m.vote_average, 
               m.watch_providers, s.score
        FROM similarity_cache s
        JOIN movies m ON s.movie_id_2 = m.id
        WHERE s.movie_id_1 = ?
        ORDER BY s.score DESC
        LIMIT ?
    """, (movie_id, limit))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def filter_by_genre(genre_name: str, limit: int = 50) -> List[Dict]:
    """
    Get movies filtered by genre.
    
    SQL: JOIN between movies, movie_genres, and genres tables
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT m.id, m.imdb_id, m.title, m.year, m.vote_average
        FROM movies m
        JOIN movie_genres mg ON m.id = mg.movie_id
        JOIN genres g ON mg.genre_id = g.id
        WHERE LOWER(g.name) = LOWER(?)
        ORDER BY m.vote_average DESC
        LIMIT ?
    """, (genre_name, limit))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_top_rated(limit: int = 10) -> List[Dict]:
    """
    Get top-rated movies.
    
    SQL: SELECT with ORDER BY and LIMIT
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, imdb_id, title, year, vote_average
        FROM movies
        ORDER BY vote_average DESC
        LIMIT ?
    """, (limit,))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_all_genres() -> List[str]:
    """
    Get all unique genres.
    
    SQL: SELECT DISTINCT from genres table
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM genres ORDER BY name")
    genres = [row[0] for row in cursor.fetchall()]
    conn.close()
    return genres


def get_movie_genres(movie_id: int) -> List[str]:
    """
    Get all genres for a specific movie.
    
    SQL: JOIN query
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT g.name
        FROM genres g
        JOIN movie_genres mg ON g.id = mg.genre_id
        WHERE mg.movie_id = ?
    """, (movie_id,))
    
    genres = [row[0] for row in cursor.fetchall()]
    conn.close()
    return genres


def get_tv_genres(tv_id: int) -> List[str]:
    """
    Get all genres for a specific TV show.
    
    SQL: JOIN query
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT g.name
        FROM genres g
        JOIN tv_genres tg ON g.id = tg.genre_id
        WHERE tg.tv_id = ?
    """, (tv_id,))
    
    genres = [row[0] for row in cursor.fetchall()]
    conn.close()
    return genres


# ============ ANALYTICS QUERIES ============

def get_genre_counts() -> Dict[str, int]:
    """
    Get count of movies per genre.
    
    SQL: GROUP BY with COUNT aggregation
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT g.name, COUNT(mg.movie_id) as count
        FROM genres g
        JOIN movie_genres mg ON g.id = mg.genre_id
        GROUP BY g.id, g.name
        ORDER BY count DESC
    """)
    
    results = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return results


def get_ratings_by_decade() -> pd.DataFrame:
    """
    Get average rating by decade.
    
    SQL: GROUP BY with AVG aggregation and arithmetic
    """
    conn = get_connection()
    
    df = pd.read_sql_query("""
        SELECT 
            (year / 10) * 10 as decade,
            AVG(vote_average) as avg_rating,
            COUNT(*) as movie_count
        FROM movies
        WHERE year IS NOT NULL
        GROUP BY decade
        ORDER BY decade
    """, conn)
    
    conn.close()
    return df


def get_top_directors(min_movies: int = 3, limit: int = 15) -> pd.DataFrame:
    """
    Get top directors by average rating (with minimum movie count).
    
    SQL: JOIN with GROUP BY, HAVING, and multiple aggregations
    """
    conn = get_connection()
    
    df = pd.read_sql_query("""
        SELECT 
            p.name as director,
            AVG(m.vote_average) as avg_rating,
            COUNT(m.id) as movie_count
        FROM people p
        JOIN movie_people mp ON p.id = mp.person_id
        JOIN movies m ON mp.movie_id = m.id
        WHERE p.role = 'director'
        GROUP BY p.id, p.name
        HAVING COUNT(m.id) >= ?
        ORDER BY avg_rating DESC
        LIMIT ?
    """, conn, params=(min_movies, limit))
    
    conn.close()
    return df


def get_genre_rating_stats() -> pd.DataFrame:
    """
    Get rating statistics per genre.
    
    SQL: JOIN with GROUP BY and multiple aggregations (AVG, MIN, MAX, COUNT)
    """
    conn = get_connection()
    
    df = pd.read_sql_query("""
        SELECT 
            g.name as genre,
            AVG(m.vote_average) as avg_rating,
            MIN(m.vote_average) as min_rating,
            MAX(m.vote_average) as max_rating,
            COUNT(m.id) as movie_count
        FROM genres g
        JOIN movie_genres mg ON g.id = mg.genre_id
        JOIN movies m ON mg.movie_id = m.id
        GROUP BY g.id, g.name
        ORDER BY avg_rating DESC
    """, conn)
    
    conn.close()
    return df


def get_rating_distribution() -> pd.DataFrame:
    """
    Get distribution of movie ratings.
    
    SQL: GROUP BY with ROUND for bucketing
    """
    conn = get_connection()
    
    df = pd.read_sql_query("""
        SELECT 
            ROUND(vote_average, 0) as rating_bucket,
            COUNT(*) as count
        FROM movies
        WHERE vote_average IS NOT NULL
        GROUP BY rating_bucket
        ORDER BY rating_bucket
    """, conn)
    
    conn.close()
    return df


def get_movies_per_year() -> pd.DataFrame:
    """
    Get count of movies per year.
    
    SQL: GROUP BY year with COUNT
    """
    conn = get_connection()
    
    df = pd.read_sql_query("""
        SELECT 
            year,
            COUNT(*) as movie_count,
            AVG(vote_average) as avg_rating
        FROM movies
        WHERE year IS NOT NULL AND year > 1900
        GROUP BY year
        ORDER BY year
    """, conn)
    
    conn.close()
    return df


# ============ TV SHOW ANALYTICS FUNCTIONS ============

def get_tv_genre_counts() -> Dict[str, int]:
    """Get count of TV shows per genre."""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT g.name, COUNT(tg.tv_id) as count
            FROM genres g
            JOIN tv_genres tg ON g.id = tg.genre_id
            GROUP BY g.id, g.name
            ORDER BY count DESC
        """)
        results = {row[0]: row[1] for row in cursor.fetchall()}
    except:
        results = {}
    
    conn.close()
    return results


def get_tv_ratings_by_decade() -> pd.DataFrame:
    """Get average rating by decade for TV shows."""
    conn = get_connection()
    
    try:
        df = pd.read_sql_query("""
            SELECT 
                (year / 10) * 10 as decade,
                AVG(vote_average) as avg_rating,
                COUNT(*) as show_count
            FROM tv_shows
            WHERE year IS NOT NULL
            GROUP BY decade
            ORDER BY decade
        """, conn)
    except:
        df = pd.DataFrame(columns=['decade', 'avg_rating', 'show_count'])
    
    conn.close()
    return df


def get_top_creators(min_shows: int = 2, limit: int = 15) -> pd.DataFrame:
    """Get top creators by average rating (with minimum show count)."""
    conn = get_connection()
    
    try:
        df = pd.read_sql_query("""
            SELECT 
                p.name as creator,
                AVG(t.vote_average) as avg_rating,
                COUNT(t.id) as show_count
            FROM people p
            JOIN tv_people tp ON p.id = tp.person_id
            JOIN tv_shows t ON tp.tv_id = t.id
            WHERE p.role = 'creator'
            GROUP BY p.id, p.name
            HAVING COUNT(t.id) >= ?
            ORDER BY avg_rating DESC
            LIMIT ?
        """, conn, params=(min_shows, limit))
    except:
        df = pd.DataFrame(columns=['creator', 'avg_rating', 'show_count'])
    
    conn.close()
    return df


def get_tv_genre_rating_stats() -> pd.DataFrame:
    """Get rating statistics per genre for TV shows."""
    conn = get_connection()
    
    try:
        df = pd.read_sql_query("""
            SELECT 
                g.name as genre,
                AVG(t.vote_average) as avg_rating,
                MIN(t.vote_average) as min_rating,
                MAX(t.vote_average) as max_rating,
                COUNT(t.id) as show_count
            FROM genres g
            JOIN tv_genres tg ON g.id = tg.genre_id
            JOIN tv_shows t ON tg.tv_id = t.id
            GROUP BY g.id, g.name
            ORDER BY avg_rating DESC
        """, conn)
    except:
        df = pd.DataFrame(columns=['genre', 'avg_rating', 'min_rating', 'max_rating', 'show_count'])
    
    conn.close()
    return df


def get_tv_rating_distribution() -> pd.DataFrame:
    """Get distribution of ratings for TV shows."""
    conn = get_connection()
    
    try:
        df = pd.read_sql_query("""
            SELECT 
                CAST(vote_average AS INTEGER) as rating_bucket,
                COUNT(*) as show_count
            FROM tv_shows
            WHERE vote_average IS NOT NULL
            GROUP BY rating_bucket
            ORDER BY rating_bucket
        """, conn)
    except:
        df = pd.DataFrame(columns=['rating_bucket', 'show_count'])
    
    conn.close()
    return df


def get_tv_shows_per_year() -> pd.DataFrame:
    """Get count of TV shows per year."""
    conn = get_connection()
    
    try:
        df = pd.read_sql_query("""
            SELECT 
                year,
                COUNT(*) as show_count,
                AVG(vote_average) as avg_rating
            FROM tv_shows
            WHERE year IS NOT NULL AND year > 1900
            GROUP BY year
            ORDER BY year
        """, conn)
    except:
        df = pd.DataFrame(columns=['year', 'show_count', 'avg_rating'])
    
    conn.close()
    return df


def get_database_stats() -> Dict[str, int]:
    """Get basic statistics about the database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    cursor.execute("SELECT COUNT(*) FROM movies")
    stats['total_movies'] = cursor.fetchone()[0]
    
    try:
        cursor.execute("SELECT COUNT(*) FROM tv_shows")
        stats['total_tv_shows'] = cursor.fetchone()[0]
    except:
        stats['total_tv_shows'] = 0
    
    cursor.execute("SELECT COUNT(*) FROM genres")
    stats['total_genres'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM people WHERE role = 'actor'")
    stats['total_actors'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM people WHERE role = 'director'")
    stats['total_directors'] = cursor.fetchone()[0]
    
    try:
        cursor.execute("SELECT COUNT(*) FROM people WHERE role = 'creator'")
        stats['total_creators'] = cursor.fetchone()[0]
    except:
        stats['total_creators'] = 0
    
    cursor.execute("SELECT COUNT(*) FROM similarity_cache")
    stats['cached_similarities'] = cursor.fetchone()[0]
    
    try:
        cursor.execute("SELECT COUNT(*) FROM tv_similarity_cache")
        stats['cached_tv_similarities'] = cursor.fetchone()[0]
    except:
        stats['cached_tv_similarities'] = 0
    
    conn.close()
    return stats


# Initialize database on import
if __name__ == "__main__":
    create_tables()
    print(f"Database initialized at: {DB_PATH}")

