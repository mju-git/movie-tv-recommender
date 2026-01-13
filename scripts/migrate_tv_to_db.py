"""
ETL Script: Migrate TV Show Data to SQLite Database

This script:
1. Loads TV show data from pickle files
2. Parses and normalizes genres, actors, creators
3. Inserts data into SQLite with proper relationships
4. Pre-computes and stores top similarity scores

Run from project root:
    python scripts/migrate_tv_to_db.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pickle
import pandas as pd
import numpy as np
import json
from tqdm import tqdm

from src.database import (
    get_connection,
    create_tables,
    insert_tv_show,
    insert_genre,
    insert_person,
    link_tv_genre,
    link_tv_person,
    insert_tv_similarity,
    get_database_stats
)
from src.config import Config

DATA_PATH = Path(Config.DATA_PATH)


def load_pickle(file_path: str):
    """Load data from a pickle file."""
    with open(file_path, 'rb') as f:
        return pickle.load(f)


def parse_list_field(field_value) -> list:
    """Parse a stringified list field safely."""
    if field_value is None:
        return []
    
    if isinstance(field_value, np.ndarray):
        return field_value.tolist()
    
    if isinstance(field_value, list):
        return field_value
    
    try:
        if pd.isna(field_value):
            return []
    except (ValueError, TypeError):
        pass
    
    if isinstance(field_value, str):
        try:
            parsed = eval(field_value) if field_value.startswith('[') else []
            if isinstance(parsed, list):
                return parsed
        except:
            pass
    
    return []


def extract_unique_items(items_list) -> list:
    """Extract unique items from a list, preserving order."""
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


def migrate_tv_shows(tv_df: pd.DataFrame):
    """Migrate TV shows data to the database."""
    conn = get_connection()
    
    print("\n📺 Migrating TV shows to database...")
    print(f"   Total shows to process: {len(tv_df)}")
    
    genre_cache = {}
    person_cache = {}
    shows_inserted = 0
    
    for idx, row in tqdm(tv_df.iterrows(), total=len(tv_df), desc="   Processing"):
        try:
            def safe_get(row, key, default=''):
                try:
                    if key not in row.index:
                        return default
                    val = row[key]
                    if isinstance(val, np.ndarray):
                        return val.tolist() if len(val) > 0 else default
                    if pd.isna(val):
                        return default
                    return val
                except:
                    return default
            
            # Extract data
            tv_id = int(safe_get(row, 'id', 0))
            if not tv_id:
                continue
            
            overview = safe_get(row, 'overview', '')
            if isinstance(overview, list):
                overview = ' '.join(str(x) for x in overview)
            
            tagline = safe_get(row, 'tagline', '')
            if isinstance(tagline, list):
                tagline = ' '.join(str(x) for x in tagline)
            
            year_val = safe_get(row, 'year', None)
            if year_val:
                try:
                    year_val = int(year_val)
                except:
                    year_val = None
            
            vote_val = safe_get(row, 'vote_average', None)
            if vote_val:
                try:
                    vote_val = float(vote_val)
                except:
                    vote_val = None
            
            vote_count_val = safe_get(row, 'vote_count', None)
            if vote_count_val:
                try:
                    vote_count_val = int(vote_count_val)
                except:
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
            
            # Create soup (for similarity - reuse from preprocessing if available)
            soup = safe_get(row, 'soup', '')
            
            tv_data = {
                'id': tv_id,
                'imdb_id': str(safe_get(row, 'imdb_id', '')),
                'title': str(safe_get(row, 'title', '')),
                'year': year_val,
                'vote_average': vote_val,
                'vote_count': vote_count_val,
                'number_of_seasons': safe_get(row, 'number_of_seasons'),
                'number_of_episodes': safe_get(row, 'number_of_episodes'),
                'status': safe_get(row, 'status', ''),
                'overview': overview,
                'tagline': tagline,
                'soup': soup,
                'poster_url': poster_url,
                'watch_providers': watch_providers
            }
            
            # Parse genres
            try:
                genres_raw_val = row['genres'] if 'genres' in row.index else []
                genres_raw = parse_list_field(genres_raw_val)
                genres = extract_unique_items(genres_raw)
            except:
                genres = []
            
            # Get actors and creators
            try:
                actors_raw_val = row['actors'] if 'actors' in row.index else []
                actors_raw = parse_list_field(actors_raw_val)
                actors = extract_unique_items(actors_raw)[:5]
            except:
                actors = []
            
            try:
                creators_raw_val = row['creators'] if 'creators' in row.index else []
                creators_raw = parse_list_field(creators_raw_val)
                creators = extract_unique_items(creators_raw)
            except:
                creators = []
            
            # Insert TV show
            try:
                insert_tv_show(conn, tv_data)
                shows_inserted += 1
            except Exception as insert_err:
                print(f"\n   Error inserting TV show {tv_data['title']}: {insert_err}")
                continue
            
            # Insert and link genres
            for genre_name in genres:
                if genre_name and len(genre_name) > 0:
                    if genre_name not in genre_cache:
                        genre_cache[genre_name] = insert_genre(conn, genre_name)
                    link_tv_genre(conn, tv_id, genre_cache[genre_name])
            
            # Insert and link actors
            for actor_name in actors:
                if actor_name and len(actor_name) > 0:
                    cache_key = (actor_name, 'actor')
                    if cache_key not in person_cache:
                        person_cache[cache_key] = insert_person(conn, actor_name, 'actor')
                    link_tv_person(conn, tv_id, person_cache[cache_key])
            
            # Insert and link creators
            for creator_name in creators:
                if creator_name and len(creator_name) > 0:
                    cache_key = (creator_name, 'creator')
                    if cache_key not in person_cache:
                        person_cache[cache_key] = insert_person(conn, creator_name, 'creator')
                    link_tv_person(conn, tv_id, person_cache[cache_key])
            
        except Exception as e:
            print(f"\n   Warning: Error processing TV show at index {idx}: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\n   ✅ Inserted {shows_inserted} TV shows")


def migrate_tv_similarities(tv_df: pd.DataFrame, similarity_matrix, top_n: int = 30):
    """Migrate TV similarity scores to database."""
    conn = get_connection()
    
    print("\n📊 Migrating TV similarity scores...")
    
    # Create title to ID mapping
    title_to_id = {}
    for idx, row in tv_df.iterrows():
        tv_id = row.get('id')
        title = row.get('title')
        if tv_id and title:
            title_to_id[title] = tv_id
    
    # Get ID to index mapping
    id_to_index = {}
    for idx, row in tv_df.iterrows():
        tv_id = row.get('id')
        if tv_id:
            id_to_index[tv_id] = idx
    
    inserted = 0
    for idx, row in tqdm(tv_df.iterrows(), total=len(tv_df), desc="   Processing"):
        tv_id = row.get('id')
        if not tv_id or tv_id not in id_to_index:
            continue
        
        matrix_idx = id_to_index[tv_id]
        sim_scores = list(enumerate(similarity_matrix[matrix_idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:top_n+1]
        
        for other_idx, score in sim_scores:
            other_id = tv_df.iloc[other_idx].get('id')
            if other_id:
                try:
                    insert_tv_similarity(conn, tv_id, other_id, float(score))
                    inserted += 1
                except:
                    pass
    
    conn.commit()
    conn.close()
    
    print(f"   ✅ Inserted {inserted} similarity scores")


def run_migration():
    """Main migration function."""
    print("🚀 TV Show Recommender Database Migration")
    print("=" * 60)
    
    # Step 1: Load source data
    print("\n📂 Loading source data...")
    tv_pickle = DATA_PATH / "tv_shows.pkl"
    similarity_pickle = DATA_PATH / "tv_similarity.pkl"
    
    if not tv_pickle.exists():
        print(f"   ❌ Error: {tv_pickle} not found!")
        print("   Run tv_preprocessing.ipynb first to create tv_shows.pkl")
        return
    
    try:
        tv_df = load_pickle(str(tv_pickle))
        print(f"   ✓ Loaded {len(tv_df)} TV shows from pickle")
    except Exception as e:
        print(f"   ❌ Error loading pickle: {e}")
        return
    
    similarity_matrix = None
    if similarity_pickle.exists():
        similarity_matrix = load_pickle(str(similarity_pickle))
        print(f"   ✓ Loaded similarity matrix: {similarity_matrix.shape}")
    else:
        print("   ⚠ Similarity matrix not found - skipping similarity cache")
    
    # Step 2: Ensure tables exist
    print("\n🗄️ Setting up database...")
    create_tables()
    
    # Step 3: Migrate TV shows
    migrate_tv_shows(tv_df)
    
    # Step 4: Migrate similarities
    if similarity_matrix is not None:
        migrate_tv_similarities(tv_df, similarity_matrix, top_n=30)
    
    # Step 5: Show stats
    print("\n📊 Migration Complete!")
    print("-" * 40)
    stats = get_database_stats()
    for key, value in stats.items():
        print(f"   {key}: {value:,}")
    
    print("\n" + "=" * 60)
    print("✅ TV Shows database ready at: data/movies.db")
    print("=" * 60)


if __name__ == "__main__":
    run_migration()

