"""
Poster fetching utility for the Movie Recommender System.

This module handles fetching movie poster URLs from The Movie Database (TMDB) API.
"""
import requests
from src.config import Config


def fetch_poster(movie_id: int) -> str:
    """
    Fetch movie poster URL from TMDB API.
    
    Args:
        movie_id (int): TMDB movie ID (not IMDB ID)
        
    Returns:
        str: Full URL to the movie poster image (w154 size), or empty string if not found
        
    Raises:
        ValueError: If TMDB_API_KEY is not configured in environment
        
    Example:
        >>> poster_url = fetch_poster(550)
        >>> print(poster_url)
        'https://image.tmdb.org/t/p/w154/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg'
    """
    Config.validate()
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={Config.TMDB_API_KEY}&language=en-US"
    
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        
        if 'poster_path' not in data or not data['poster_path']:
            return ""
            
        poster_path = data['poster_path']
        return f"https://image.tmdb.org/t/p/w154/{poster_path}"
        
    except (requests.RequestException, KeyError):
        # Return empty string on any API error (network, invalid response, etc.)
        return ""

