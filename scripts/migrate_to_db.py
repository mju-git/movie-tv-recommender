"""
ETL Script: Migrate Pickle/CSV Data to SQLite Database

This script:
1. Loads existing movie data from pickle/CSV files
2. Parses and normalizes genres, actors, directors
3. Inserts data into SQLite with proper relationships
4. Pre-computes and stores top similarity scores

Run from project root:
    python scripts/migrate_to_db.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pickle
import pandas as pd
import numpy as np
from ast import literal_eval
from tqdm import tqdm

from src.database import (
    get_connection,
    create_tables,
    insert_movie,
    insert_genre,
    insert_person,
    link_movie_genre,
    link_movie_person,
    insert_similarity,
    get_database_stats
)
from src.config import Config
import json

DATA_PATH = Path(Config.DATA_PATH)


def load_pickle(file_path: str):
    """Load data from a pickle file."""
    with open(file_path, 'rb') as f:
        return pickle.load(f)


def load_credits_data() -> dict:
    """
    Load movie credits from CSV and extract proper actor/director names.
    Returns a dict mapping movie_id -> {'actors': [...], 'directors': [...]}
    """
    credits_file = DATA_PATH / "movie_credits.csv"
    if not credits_file.exists():
        print(f"   ⚠ Credits file not found: {credits_file}")
        return {}
    
    print(f"   Loading credits from {credits_file}...")
    credits_df = pd.read_csv(credits_file)
    print(f"   ✓ Loaded {len(credits_df)} credit records")
    
    credits_lookup = {}
    
    for _, row in credits_df.iterrows():
        movie_id = row['id']
        actors = []
        directors = []
        
        # Parse cast column (JSON-like string)
        try:
            cast_str = row.get('cast', '[]')
            if pd.notna(cast_str) and cast_str:
                cast_list = literal_eval(cast_str)
                # Get top 5 actors by order
                for person in sorted(cast_list, key=lambda x: x.get('order', 999))[:5]:
                    name = person.get('name', '').strip()
                    if name:
                        actors.append(name)
        except Exception:
            pass
        
        # Parse crew column (JSON-like string)
        try:
            crew_str = row.get('crew', '[]')
            if pd.notna(crew_str) and crew_str:
                crew_list = literal_eval(crew_str)
                # Get directors
                for person in crew_list:
                    if person.get('job') == 'Director':
                        name = person.get('name', '').strip()
                        if name and name not in directors:
                            directors.append(name)
        except Exception:
            pass
        
        credits_lookup[movie_id] = {
            'actors': actors,
            'directors': directors
        }
    
    # Debug output
    sample_ids = list(credits_lookup.keys())[:3]
    for mid in sample_ids:
        print(f"   Sample credits [{mid}]: actors={credits_lookup[mid]['actors'][:2]}, directors={credits_lookup[mid]['directors']}")
    
    return credits_lookup


def parse_list_field(field_value) -> list:
    """Parse a stringified list field safely."""
    # Handle None
    if field_value is None:
        return []
    
    # Handle numpy arrays
    if isinstance(field_value, np.ndarray):
        return field_value.tolist()
    
    # Handle lists directly
    if isinstance(field_value, list):
        return field_value
    
    # Handle scalar NaN (check after array check to avoid ambiguous truth value)
    try:
        if pd.isna(field_value):
            return []
    except (ValueError, TypeError):
        pass  # pd.isna fails on arrays, but we already handled that
    
    # Handle strings
    if isinstance(field_value, str):
        try:
            parsed = literal_eval(field_value)
            if isinstance(parsed, list):
                return parsed
        except (ValueError, SyntaxError):
            pass
    
    return []


def clean_name(name: str) -> str:
    """Clean a person's name (remove extra spaces, etc.)."""
    if not name:
        return ""
    return name.strip().title()


def extract_unique_items(items_list) -> list:
    """Extract unique items from a list, preserving order."""
    # Handle numpy arrays
    if isinstance(items_list, np.ndarray):
        items_list = items_list.tolist()
    
    if not isinstance(items_list, list):
        return []
    
    seen = set()
    unique = []
    for item in items_list:
        if item is None:
            continue
        item_clean = item.strip().title() if isinstance(item, str) else str(item)
        if item_clean and item_clean.lower() not in seen:
            seen.add(item_clean.lower())
            unique.append(item_clean)
    return unique


def migrate_movies(movies_df: pd.DataFrame, credits_lookup: dict = None):
    """
    Migrate movies data to the database.
    
    ETL Steps:
    1. Extract - Read from DataFrame
    2. Transform - Parse genres, actors, directors
    3. Load - Insert into normalized tables
    
    Args:
        movies_df: DataFrame with movie data
        credits_lookup: Optional dict mapping movie_id -> {'actors': [...], 'directors': [...]}
                       If provided, uses proper names from credits instead of preprocessed ones.
    """
    conn = get_connection()
    use_credits = credits_lookup is not None and len(credits_lookup) > 0
    if use_credits:
        print(f"   Using credits lookup: {len(credits_lookup)} records")
    else:
        print("   Using actors/directors from scraped data (TMDB)")
    
    print("\n📦 Migrating movies to database...")
    print(f"   Total movies to process: {len(movies_df)}")
    print(f"   Columns: {list(movies_df.columns)}")
    print(f"   Index type: {type(movies_df.index)}")
    
    # Reset index if needed
    if 'index' in movies_df.columns:
        print("   Note: 'index' column found, using it")
    
    # Debug first row
    if len(movies_df) > 0:
        first_row = movies_df.iloc[0]
        print(f"   Sample row type: {type(first_row)}")
        print(f"   Sample ID: {first_row['id'] if 'id' in first_row.index else 'N/A'}")
        print(f"   Sample title: {first_row['title'] if 'title' in first_row.index else 'N/A'}")
        
        # Debug genres/actors/directors
        if 'genres' in first_row.index:
            genres_val = first_row['genres']
            print(f"   Sample genres type: {type(genres_val)}")
            print(f"   Sample genres value: {str(genres_val)[:100]}...")
        if 'actors' in first_row.index:
            actors_val = first_row['actors']
            print(f"   Sample actors type: {type(actors_val)}")
            print(f"   Sample actors value: {str(actors_val)[:100]}...")
        if 'directors' in first_row.index:
            director_val = first_row['directors']
            print(f"   Sample directors type: {type(director_val)}")
            print(f"   Sample directors value: {str(director_val)[:100]}...")
        elif 'director' in first_row.index:
            director_val = first_row['director']
            print(f"   Sample director type: {type(director_val)}")
            print(f"   Sample director value: {str(director_val)[:100]}...")
    
    # Track inserted genres and people for efficiency
    genre_cache = {}
    person_cache = {}
    movies_inserted = 0
    
    for idx, row in tqdm(movies_df.iterrows(), total=len(movies_df), desc="   Processing"):
        try:
            # ===== EXTRACT & TRANSFORM =====
            
            # Safe getter for row values (works with both dict and pandas Series)
            def safe_get(row, key, default=''):
                try:
                    if key not in row.index:
                        return default
                    val = row[key]
                    # Handle numpy arrays
                    if isinstance(val, np.ndarray):
                        return val.tolist() if len(val) > 0 else default
                    # Handle scalar NaN
                    if pd.isna(val):
                        return default
                    return val
                except:
                    return default
            
            # Handle overview and tagline (may be lists or strings)
            overview_raw = safe_get(row, 'overview', '')
            if isinstance(overview_raw, list):
                overview = ' '.join(str(x) for x in overview_raw)
            else:
                overview = str(overview_raw) if overview_raw else ''
            
            tagline_raw = safe_get(row, 'tagline', '')
            if isinstance(tagline_raw, list):
                tagline = ' '.join(str(x) for x in tagline_raw)
            else:
                tagline = str(tagline_raw) if tagline_raw else ''
            
            soup_raw = safe_get(row, 'soup', '')
            if isinstance(soup_raw, list):
                soup = ' '.join(str(x) for x in soup_raw)
            else:
                soup = str(soup_raw) if soup_raw else ''
            
            # Get ID - use 'id' column if exists, otherwise use index
            movie_id = safe_get(row, 'id', None)
            if movie_id is None or movie_id == '':
                movie_id = idx
            else:
                movie_id = int(movie_id)
            
            # Get year and vote safely
            year_val = safe_get(row, 'year', None)
            if year_val is not None and year_val != '':
                try:
                    year_val = int(float(year_val))  # Handle float years like 2020.0
                except (ValueError, TypeError):
                    year_val = None
            else:
                year_val = None
                
            vote_val = safe_get(row, 'vote_average', None)
            if vote_val is not None and vote_val != '':
                try:
                    vote_val = float(vote_val)
                except (ValueError, TypeError):
                    vote_val = None
            else:
                vote_val = None
            
            # Movie data
            # Get vote_count
            vote_count_val = safe_get(row, 'vote_count', None)
            if vote_count_val is not None and vote_count_val != '':
                try:
                    vote_count_val = int(vote_count_val)
                except (ValueError, TypeError):
                    vote_count_val = None
            else:
                vote_count_val = None
            
            # Get poster_url and watch_providers
            poster_url = safe_get(row, 'poster_url', None)
            watch_providers_raw = safe_get(row, 'watch_providers', {})
            
            # Handle watch_providers - could be dict, JSON string, or None
            watch_providers = {}
            if watch_providers_raw:
                if isinstance(watch_providers_raw, dict):
                    watch_providers = watch_providers_raw
                elif isinstance(watch_providers_raw, str):
                    try:
                        watch_providers = json.loads(watch_providers_raw)
                    except (json.JSONDecodeError, TypeError):
                        watch_providers = {}
            
            movie_data = {
                'id': movie_id,
                'imdb_id': str(safe_get(row, 'imdb_id', '')),
                'title': str(safe_get(row, 'title', '')),
                'year': year_val,
                'vote_average': vote_val,
                'vote_count': vote_count_val,
                'overview': overview,
                'tagline': tagline,
                'soup': soup,
                'poster_url': poster_url,
                'watch_providers': watch_providers
            }
            
            # Parse genres - get raw value directly from row
            try:
                genres_raw_val = row['genres'] if 'genres' in row.index else []
                genres_raw = parse_list_field(genres_raw_val)
                genres = extract_unique_items(genres_raw)
            except Exception:
                genres = []
            
            # Get actors and directors - prefer credits_lookup for proper names
            if use_credits and movie_id in credits_lookup:
                actors = credits_lookup[movie_id].get('actors', [])[:5]
                directors = credits_lookup[movie_id].get('directors', [])
            else:
                # Fallback to preprocessed data from movies.pkl
                try:
                    actors_raw_val = row['actors'] if 'actors' in row.index else []
                    actors_raw = parse_list_field(actors_raw_val)
                    actors = extract_unique_items(actors_raw)[:5]
                except Exception:
                    actors = []
                
                try:
                    # Check both 'directors' (new format) and 'director' (old format)
                    if 'directors' in row.index:
                        directors_raw_val = row['directors']
                    elif 'director' in row.index:
                        directors_raw_val = row['director']
                    else:
                        directors_raw_val = []
                    directors_raw = parse_list_field(directors_raw_val)
                    directors = extract_unique_items(directors_raw)
                except Exception:
                    directors = []
            
            # Debug first few
            if movies_inserted < 3:
                print(f"\n   DEBUG Movie {movies_inserted}: {movie_data['title']}")
                print(f"   Genres: {genres[:3] if genres else 'none'}")
                print(f"   Actors: {actors[:2] if actors else 'none'}")
                print(f"   Directors: {directors if directors else 'none'}")
            
            # ===== LOAD =====
            
            # Insert movie
            movie_id = movie_data['id']
            try:
                insert_movie(conn, movie_data)
                movies_inserted += 1
            except Exception as insert_err:
                print(f"\n   Error inserting movie {movie_data['title']}: {insert_err}")
                continue
            
            # Insert and link genres
            for genre_name in genres:
                if genre_name and len(genre_name) > 0:
                    if genre_name not in genre_cache:
                        genre_cache[genre_name] = insert_genre(conn, genre_name)
                    link_movie_genre(conn, movie_id, genre_cache[genre_name])
            
            # Insert and link actors
            for actor_name in actors:
                if actor_name and len(actor_name) > 0:
                    cache_key = (actor_name, 'actor')
                    if cache_key not in person_cache:
                        person_cache[cache_key] = insert_person(conn, actor_name, 'actor')
                    link_movie_person(conn, movie_id, person_cache[cache_key])
            
            # Insert and link directors
            for director_name in directors:
                if director_name and len(director_name) > 0:
                    cache_key = (director_name, 'director')
                    if cache_key not in person_cache:
                        person_cache[cache_key] = insert_person(conn, director_name, 'director')
                    link_movie_person(conn, movie_id, person_cache[cache_key])
        
        except Exception as e:
            print(f"\n   Warning: Error processing movie at index {idx}: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"   ✓ Movies inserted: {movies_inserted}")
    print(f"   ✓ Genres cached: {len(genre_cache)}")
    print(f"   ✓ People cached: {len(person_cache)}")


def migrate_similarities(movies_df: pd.DataFrame, similarity_matrix: np.ndarray, top_n: int = 30):
    """
    Migrate pre-computed similarity scores to the database.
    
    For each movie, stores the top N most similar movies.
    This allows recommendations to be fetched with a simple SQL query.
    """
    conn = get_connection()
    
    print(f"\n🔗 Caching top {top_n} similarities for each movie...")
    
    # Get movie IDs in order
    movie_ids = movies_df['id'].tolist()
    n_movies = len(movie_ids)
    
    total_inserted = 0
    
    for i in tqdm(range(n_movies), desc="   Processing"):
        movie_id_1 = movie_ids[i]
        
        # Get similarity scores for this movie
        sim_scores = similarity_matrix[i]
        
        # Get indices of top N similar movies (excluding itself)
        top_indices = np.argsort(sim_scores)[::-1][1:top_n+1]
        
        for j in top_indices:
            movie_id_2 = movie_ids[j]
            score = float(sim_scores[j])
            
            if score > 0:  # Only store positive similarities
                insert_similarity(conn, movie_id_1, movie_id_2, score)
                total_inserted += 1
        
        # Commit every 100 movies for efficiency
        if (i + 1) % 100 == 0:
            conn.commit()
    
    conn.commit()
    conn.close()
    
    print(f"   ✓ Similarities cached: {total_inserted:,} pairs")


def run_migration():
    """Run the full ETL migration process."""
    print("=" * 60)
    print("🚀 Movie Recommender Database Migration")
    print("=" * 60)
    
    # Step 1: Load source data
    print("\n📂 Loading source data...")
    print(f"   Data path: {DATA_PATH}")
    print(f"   Data path exists: {DATA_PATH.exists()}")
    
    movies_pickle = DATA_PATH / "movies.pkl"
    similarity_pickle = DATA_PATH / "similarity.pkl"
    
    print(f"   Movies pickle: {movies_pickle}")
    print(f"   Movies pickle exists: {movies_pickle.exists()}")
    
    if not movies_pickle.exists():
        print(f"   ❌ Error: {movies_pickle} not found!")
        return
    
    try:
        movies_df = load_pickle(str(movies_pickle))
        print(f"   ✓ Loaded {len(movies_df)} movies from pickle")
        print(f"   DataFrame shape: {movies_df.shape}")
    except Exception as e:
        print(f"   ❌ Error loading pickle: {e}")
        return
    
    similarity_matrix = None
    if similarity_pickle.exists():
        similarity_matrix = load_pickle(str(similarity_pickle))
        print(f"   ✓ Loaded similarity matrix: {similarity_matrix.shape}")
    else:
        print("   ⚠ Similarity matrix not found - skipping similarity cache")
    
    # Note: We use actors/directors directly from movies.pkl (scraped from TMDB)
    # The old movie_credits.csv is no longer needed since new data has proper names
    credits_lookup = {}  # Empty - use data from movies.pkl
    
    # Step 2: Reset and create tables (only movie tables, preserve TV shows)
    print("\n🗄️ Setting up database...")
    # Only drop movie tables, not TV tables
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS similarity_cache")
    cursor.execute("DROP TABLE IF EXISTS movie_people")
    cursor.execute("DROP TABLE IF EXISTS movie_genres")
    cursor.execute("DROP TABLE IF EXISTS movies")
    conn.commit()
    conn.close()
    # Create tables (will only create missing ones)
    create_tables()
    
    # Step 3: Migrate movies (with credits for proper names)
    migrate_movies(movies_df, credits_lookup)
    
    # Step 4: Migrate similarities
    if similarity_matrix is not None:
        migrate_similarities(movies_df, similarity_matrix, top_n=30)
    
    # Step 5: Show stats
    print("\n📊 Migration Complete!")
    print("-" * 40)
    stats = get_database_stats()
    for key, value in stats.items():
        print(f"   {key}: {value:,}")
    
    print("\n" + "=" * 60)
    print("✅ Database ready at: data/movies.db")
    print("=" * 60)


if __name__ == "__main__":
    run_migration()

