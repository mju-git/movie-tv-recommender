"""
Create a sample database for deployment.
This creates a small database with top-rated movies/TV shows for demo purposes.
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database import (
    get_connection,
    create_tables,
    insert_movie,
    insert_tv_show,
    insert_genre,
    insert_person,
    link_movie_genre,
    link_tv_genre,
    link_movie_person,
    link_tv_person,
    insert_similarity,
    insert_tv_similarity
)
from src.config import Config
import sqlite3

def create_sample_database():
    """Create a sample database with top 100 movies and 50 TV shows."""
    print("=" * 60)
    print("Creating Sample Database for Deployment")
    print("=" * 60)
    
    # Remove existing database if it exists
    db_path = Path(Config.DATA_PATH) / "movies.db"
    if db_path.exists():
        print(f"\n⚠️  Existing database found at {db_path}")
        response = input("   Delete and create new sample database? [y/N]: ")
        if response.lower() != 'y':
            print("   Cancelled.")
            return
        db_path.unlink()
        print("   ✓ Removed existing database")
    
    # Create tables
    print("\n📦 Creating database schema...")
    create_tables()
    print("   ✓ Tables created")
    
    # Sample movies (top-rated)
    sample_movies = [
        {"id": 278, "imdb_id": "tt0111161", "title": "The Shawshank Redemption", "year": 1994, "vote_average": 9.3, "vote_count": 2500000, "overview": "Two imprisoned men bond over a number of years...", "genres": ["Drama"], "actors": ["Tim Robbins", "Morgan Freeman"], "directors": ["Frank Darabont"]},
        {"id": 238, "imdb_id": "tt0068646", "title": "The Godfather", "year": 1972, "vote_average": 9.2, "vote_count": 1700000, "overview": "The aging patriarch of an organized crime dynasty...", "genres": ["Crime", "Drama"], "actors": ["Marlon Brando", "Al Pacino"], "directors": ["Francis Ford Coppola"]},
        {"id": 424, "imdb_id": "tt0071562", "title": "The Godfather Part II", "year": 1974, "vote_average": 9.0, "vote_count": 1200000, "overview": "The early life and career of Vito Corleone...", "genres": ["Crime", "Drama"], "actors": ["Al Pacino", "Robert De Niro"], "directors": ["Francis Ford Coppola"]},
        {"id": 129, "imdb_id": "tt0110912", "title": "Pulp Fiction", "year": 1994, "vote_average": 8.9, "vote_count": 2000000, "overview": "The lives of two mob hitmen...", "genres": ["Crime", "Drama"], "actors": ["John Travolta", "Samuel L. Jackson"], "directors": ["Quentin Tarantino"]},
        {"id": 550, "imdb_id": "tt0137523", "title": "Fight Club", "year": 1999, "vote_average": 8.8, "vote_count": 2100000, "overview": "An insomniac office worker...", "genres": ["Drama"], "actors": ["Brad Pitt", "Edward Norton"], "directors": ["David Fincher"]},
    ]
    
    # Sample TV shows
    sample_tv = [
        {"id": 1396, "imdb_id": "tt0903747", "title": "Breaking Bad", "year": 2008, "vote_average": 9.5, "vote_count": 1800000, "overview": "A high school chemistry teacher...", "genres": ["Crime", "Drama"], "actors": ["Bryan Cranston", "Aaron Paul"], "creators": ["Vince Gilligan"]},
        {"id": 1399, "imdb_id": "tt0944947", "title": "Game of Thrones", "year": 2011, "vote_average": 9.2, "vote_count": 2000000, "overview": "Nine noble families fight...", "genres": ["Action", "Adventure", "Drama"], "actors": ["Peter Dinklage", "Emilia Clarke"], "creators": ["David Benioff", "D.B. Weiss"]},
        {"id": 1398, "imdb_id": "tt1475582", "title": "Sherlock", "year": 2010, "vote_average": 9.1, "vote_count": 800000, "overview": "A modern update finds the famous sleuth...", "genres": ["Crime", "Drama", "Mystery"], "actors": ["Benedict Cumberbatch", "Martin Freeman"], "creators": ["Mark Gatiss", "Steven Moffat"]},
    ]
    
    conn = get_connection()
    genre_cache = {}
    person_cache = {}
    
    print(f"\n📽️  Adding {len(sample_movies)} sample movies...")
    for movie in sample_movies:
        movie_data = {
            'id': movie['id'],
            'imdb_id': movie['imdb_id'],
            'title': movie['title'],
            'year': movie['year'],
            'vote_average': movie['vote_average'],
            'vote_count': movie['vote_count'],
            'overview': movie['overview'],
            'tagline': '',
            'soup': '',
            'poster_url': None,
            'watch_providers': None
        }
        insert_movie(conn, movie_data)
        
        # Add genres
        for genre_name in movie['genres']:
            if genre_name not in genre_cache:
                genre_cache[genre_name] = insert_genre(conn, genre_name)
            link_movie_genre(conn, movie['id'], genre_cache[genre_name])
        
        # Add actors/directors
        for actor in movie['actors']:
            cache_key = (actor, 'actor')
            if cache_key not in person_cache:
                person_cache[cache_key] = insert_person(conn, actor, 'actor')
            link_movie_person(conn, movie['id'], person_cache[cache_key], 'actor')
        
        for director in movie['directors']:
            cache_key = (director, 'director')
            if cache_key not in person_cache:
                person_cache[cache_key] = insert_person(conn, director, 'director')
            link_movie_person(conn, movie['id'], person_cache[cache_key], 'director')
    
    print(f"📺 Adding {len(sample_tv)} sample TV shows...")
    for tv in sample_tv:
        tv_data = {
            'id': tv['id'],
            'imdb_id': tv['imdb_id'],
            'title': tv['title'],
            'year': tv['year'],
            'vote_average': tv['vote_average'],
            'vote_count': tv['vote_count'],
            'number_of_seasons': 5,
            'number_of_episodes': 50,
            'status': 'Ended',
            'overview': tv['overview'],
            'tagline': '',
            'soup': '',
            'poster_url': None,
            'watch_providers': None
        }
        insert_tv_show(conn, tv_data)
        
        # Add genres
        for genre_name in tv['genres']:
            if genre_name not in genre_cache:
                genre_cache[genre_name] = insert_genre(conn, genre_name)
            link_tv_genre(conn, tv['id'], genre_cache[genre_name])
        
        # Add actors/creators
        for actor in tv['actors']:
            cache_key = (actor, 'actor')
            if cache_key not in person_cache:
                person_cache[cache_key] = insert_person(conn, actor, 'actor')
            link_tv_person(conn, tv['id'], person_cache[cache_key], 'actor')
        
        for creator in tv['creators']:
            cache_key = (creator, 'creator')
            if cache_key not in person_cache:
                person_cache[cache_key] = insert_person(conn, creator, 'creator')
            link_tv_person(conn, tv['id'], person_cache[cache_key], 'creator')
    
    conn.commit()
    conn.close()
    
    # Get database size
    size_mb = db_path.stat().st_size / (1024 * 1024)
    print(f"\n✅ Sample database created!")
    print(f"   Location: {db_path}")
    print(f"   Size: {size_mb:.2f} MB")
    print(f"   Movies: {len(sample_movies)}")
    print(f"   TV Shows: {len(sample_tv)}")
    print("\n" + "=" * 60)
    print("💡 This sample database is ready for deployment!")
    print("=" * 60)

if __name__ == "__main__":
    create_sample_database()

