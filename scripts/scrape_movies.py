"""
Movie Scraper - Optimized Version
=================================
Fetches movies from IMDb and enriches with TMDB data.

Features:
- INCREMENTAL MODE: Only downloads movies not already in database
- Rate limiting (respects TMDB API limits)
- Checkpoints (resume if interrupted)
- Combined API calls with append_to_response (3x fewer requests)
- Error handling with retries
- Progress tracking

Usage:
    python scripts/scrape_movies.py              # Incremental (default)
    python scripts/scrape_movies.py --full       # Full re-scrape

Configuration:
    Edit the CONFIG section below or use environment variables.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
import pandas as pd
import time
import json
from datetime import datetime

from bs4 import BeautifulSoup

# Try to import selenium (optional - only needed for IMDb scraping)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠ Selenium not installed. IMDb scraping disabled.")
    print("  Install with: pip install selenium webdriver-manager")

# Try to use webdriver-manager for auto chromedriver setup
try:
    from webdriver_manager.chrome import ChromeDriverManager
    USE_WEBDRIVER_MANAGER = True
except ImportError:
    USE_WEBDRIVER_MANAGER = False

# Try to load from .env
try:
    from src.config import Config
    TMDB_API_KEY = Config.TMDB_API_KEY
except:
    TMDB_API_KEY = None

# Try to load database functions for incremental mode
try:
    from src.database import get_existing_imdb_ids
    DATABASE_AVAILABLE = True
except:
    DATABASE_AVAILABLE = False


# ============================================================================
# CONFIGURATION
# ============================================================================

class ScrapeConfig:
    """Scraping configuration. Modify these values as needed."""
    
    # TMDB API Key (required)
    # Set via .env file or override here
    API_KEY = TMDB_API_KEY or "your_api_key_here"
    
    # IMDb search criteria
    MIN_RATING = 5.0          # Minimum IMDb rating (1-10)
    MIN_VOTES = 5000          # Minimum number of votes
    
    # Incremental mode (only download new movies)
    INCREMENTAL = True        # Set to False for full re-scrape
    
    # Limits
    MAX_MOVIES = None         # Set to a number to limit, or None for all
    
    # Rate limiting (TMDB allows ~40 requests per 10 seconds)
    REQUESTS_PER_SECOND = 5   # Faster rate: 5 requests/second (was 3)
    
    # Checkpoint settings  
    CHECKPOINT_EVERY = 500    # Save progress every N movies
    
    # Paths
    CHECKPOINT_DIR = project_root / "checkpoints"
    OUTPUT_DIR = project_root / "data"


# ============================================================================
# STEP 1: SCRAPE IMDB IDs
# ============================================================================

def scrape_imdb_ids(config: ScrapeConfig) -> list:
    """
    Scrape movie IDs from IMDb search results.
    Uses Selenium to handle JavaScript-loaded content.
    
    Returns:
        List of IMDb IDs (e.g., ['tt0111161', 'tt0068646', ...])
    """
    if not SELENIUM_AVAILABLE:
        print("❌ Selenium required for IMDb scraping")
        return []
    
    print(f"\n{'='*60}")
    print("📥 STEP 1: Scraping IMDb IDs")
    print(f"{'='*60}")
    print(f"   Criteria: rating >= {config.MIN_RATING}, votes >= {config.MIN_VOTES:,}")
    
    # Setup Chrome
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0")
    
    try:
        if USE_WEBDRIVER_MANAGER:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()), 
                options=chrome_options
            )
        else:
            driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"❌ Failed to start Chrome: {e}")
        print("   Make sure Chrome and chromedriver are installed")
        return []
    
    url = (
        f"https://www.imdb.com/search/title/"
        f"?title_type=feature"
        f"&user_rating={config.MIN_RATING},10"
        f"&sort=num_votes,desc"
        f"&num_votes={config.MIN_VOTES},"
        f"&count=250"
    )
    
    print(f"   URL: {url[:80]}...")
    driver.get(url)
    
    tt_set = set()
    page_count = 0
    
    while True:
        page_count += 1
        time.sleep(1)  # Reduced from 2 to 1 second
        
        # Extract movie IDs from current page
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        links = soup.select('a.ipc-title-link-wrapper[href*="/title/tt"]')
        
        for link in links:
            href = link.get('href', '')
            if '/title/tt' in href:
                tt_id = href.split('/title/')[-1].split('/')[0]
                tt_set.add(tt_id)
        
        print(f"   Page {page_count}: {len(tt_set)} unique movies found")
        
        # Check limit
        if config.MAX_MOVIES and len(tt_set) >= config.MAX_MOVIES:
            print(f"   ✓ Reached limit of {config.MAX_MOVIES} movies")
            break
        
        # Try to click "Show more"
        try:
            show_more = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".ipc-see-more__button"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", show_more)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", show_more)
        except:
            print("   ✓ No more pages")
            break
    
    driver.quit()
    
    tt_list = list(tt_set)
    if config.MAX_MOVIES:
        tt_list = tt_list[:config.MAX_MOVIES]
    
    # Save for resume capability
    config.CHECKPOINT_DIR.mkdir(exist_ok=True)
    pd.DataFrame({'imdb_id': tt_list}).to_csv(
        config.CHECKPOINT_DIR / "imdb_ids.csv", index=False
    )
    
    print(f"\n   ✅ Found {len(tt_list)} movies")
    print(f"   💾 Saved to checkpoints/imdb_ids.csv")
    
    return tt_list


# ============================================================================
# STEP 2: FETCH TMDB DATA
# ============================================================================

def fetch_movie_from_tmdb(imdb_id: str, api_key: str) -> dict:
    """
    Fetch movie data from TMDB using append_to_response.
    Uses /find endpoint to convert IMDb ID to TMDB ID, then fetches details.
    
    WHAT IS append_to_response?
    ---------------------------
    Normally you'd make 3 API calls per movie:
        GET /movie/{id}          → Basic info
        GET /movie/{id}/credits  → Cast & crew
        GET /movie/{id}/keywords → Keywords
    
    With append_to_response, you get ALL in ONE call:
        GET /movie/{id}?append_to_response=credits,keywords,watch/providers
    
    This reduces API calls by 66%!
    
    Returns:
        dict with movie data, or None if failed
    """
    # First, find the TMDB ID from IMDb ID
    find_url = (
        f"https://api.themoviedb.org/3/find/{imdb_id}"
        f"?api_key={api_key}"
        f"&external_source=imdb_id"
    )
    
    try:
        response = requests.get(find_url, timeout=15)
        if response.status_code != 200:
            if response.status_code == 429:
                return {"_error": "rate_limited"}
            return None
        
        data = response.json()
        movie_results = data.get('movie_results', [])
        
        if not movie_results:
            return None
        
        tmdb_id = movie_results[0]['id']
        
        # Now fetch full details with append_to_response
        details_url = (
            f"https://api.themoviedb.org/3/movie/{tmdb_id}"
            f"?api_key={api_key}"
            f"&language=en-US"
            f"&append_to_response=credits,keywords,watch/providers"
        )
        
        response = requests.get(details_url, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            result['imdb_id'] = imdb_id  # Preserve IMDb ID
            return result
        elif response.status_code == 429:
            return {"_error": "rate_limited"}
        elif response.status_code == 404:
            return None
        else:
            return {"_error": f"status_{response.status_code}"}
            
    except requests.exceptions.Timeout:
        return {"_error": "timeout"}
    except Exception as e:
        return {"_error": str(e)}


def parse_watch_providers(providers_data: dict, regions: list = ['US', 'DE', 'HR']) -> dict:
    """
    Parse watch providers from TMDB response.
    Extracts providers with IDs and logo paths for specified regions.
    
    Returns:
        dict: {region: {'flatrate': [{'id': int, 'name': str, 'logo_path': str}, ...], ...}}
    """
    result = {}
    results = providers_data.get('results', {})
    
    for region in regions:
        region_data = results.get(region, {})
        result[region] = {
            'flatrate': [
                {
                    'id': p.get('provider_id'),
                    'name': p.get('provider_name', ''),
                    'logo_path': p.get('logo_path', '')
                }
                for p in region_data.get('flatrate', [])
            ],
            'rent': [
                {
                    'id': p.get('provider_id'),
                    'name': p.get('provider_name', ''),
                    'logo_path': p.get('logo_path', '')
                }
                for p in region_data.get('rent', [])
            ],
            'buy': [
                {
                    'id': p.get('provider_id'),
                    'name': p.get('provider_name', ''),
                    'logo_path': p.get('logo_path', '')
                }
                for p in region_data.get('buy', [])
            ]
        }
    
    return result


def process_movie_data(raw: dict) -> dict:
    """Transform raw TMDB response into clean format."""
    if not raw or "_error" in raw:
        return None
    
    try:
        # Poster URL
        poster_path = raw.get('poster_path', '')
        poster_url = f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else None
        
        movie = {
            'id': raw.get('id'),
            'imdb_id': raw.get('imdb_id'),
            'title': raw.get('title'),
            'year': int(raw.get('release_date', '')[:4]) if raw.get('release_date') else None,
            'vote_average': raw.get('vote_average'),
            'vote_count': raw.get('vote_count'),
            'popularity': raw.get('popularity'),
            'runtime': raw.get('runtime'),
            'overview': raw.get('overview', ''),
            'tagline': raw.get('tagline', ''),
            'poster_url': poster_url,
        }
        
        # Genres
        movie['genres'] = [g['name'] for g in raw.get('genres', [])]
        
        # Actors (top 5)
        credits = raw.get('credits', {})
        cast = credits.get('cast', [])
        movie['actors'] = [
            c['name'] for c in sorted(cast, key=lambda x: x.get('order', 999))[:5]
        ]
        
        # Directors
        crew = credits.get('crew', [])
        movie['directors'] = [c['name'] for c in crew if c.get('job') == 'Director']
        
        # Keywords
        keywords_data = raw.get('keywords', {})
        movie['keywords'] = [k['name'] for k in keywords_data.get('keywords', [])]
        
        # Watch providers (US, DE, HR)
        watch_providers_data = raw.get('watch/providers', {})
        movie['watch_providers'] = parse_watch_providers(watch_providers_data)
        
        return movie
        
    except Exception as e:
        print(f"   ⚠ Error processing: {e}")
        return None


def fetch_all_movies(imdb_ids: list, config: ScrapeConfig) -> list:
    """
    Fetch all movies with rate limiting, retries, and checkpoints.
    """
    print(f"\n{'='*60}")
    print("📥 STEP 2: Fetching TMDB Data")
    print(f"{'='*60}")
    
    movies = []
    failed_ids = []
    
    # Load existing checkpoint
    checkpoint_file = config.CHECKPOINT_DIR / "movies_checkpoint.pkl"
    start_index = 0
    
    if checkpoint_file.exists():
        try:
            existing = pd.read_pickle(checkpoint_file)
            movies = existing.to_dict('records')
            # Find where we left off
            fetched_ids = {m['imdb_id'] for m in movies if m.get('imdb_id')}
            start_index = len([i for i in imdb_ids if i in fetched_ids])
            print(f"   📂 Resuming from checkpoint: {len(movies)} already fetched")
        except:
            pass
    
    remaining = len(imdb_ids) - start_index
    est_minutes = remaining / config.REQUESTS_PER_SECOND / 60
    
    print(f"   Movies to fetch: {remaining}")
    print(f"   Rate: {config.REQUESTS_PER_SECOND} requests/second")
    print(f"   Estimated time: {est_minutes:.1f} minutes")
    print()
    
    for i, imdb_id in enumerate(imdb_ids[start_index:], start=start_index):
        # Rate limiting
        time.sleep(1 / config.REQUESTS_PER_SECOND)
        
        # Fetch with retry
        result = None
        for attempt in range(3):
            result = fetch_movie_from_tmdb(imdb_id, config.API_KEY)
            
            if result and "_error" in result:
                if result["_error"] == "rate_limited":
                    print("   ⚠ Rate limited, waiting 5s...")
                    time.sleep(5)  # Reduced from 10 to 5 seconds
                elif result["_error"] == "timeout":
                    time.sleep(1)  # Reduced from 2 to 1 second
                else:
                    break
            else:
                break
        
        # Process result
        if result and "_error" not in result:
            processed = process_movie_data(result)
            if processed:
                movies.append(processed)
        else:
            failed_ids.append(imdb_id)
        
        # Progress
        if (i + 1) % 100 == 0:
            pct = (i + 1) / len(imdb_ids) * 100
            print(f"   Progress: {i + 1}/{len(imdb_ids)} ({pct:.1f}%) - ✓{len(movies)} ✗{len(failed_ids)}")
        
        # Checkpoint
        if (i + 1) % config.CHECKPOINT_EVERY == 0:
            df = pd.DataFrame(movies)
            df.to_pickle(checkpoint_file)
            print(f"   💾 Checkpoint: {len(movies)} movies saved")
    
    # Save failed IDs
    if failed_ids:
        pd.DataFrame({'imdb_id': failed_ids}).to_csv(
            config.CHECKPOINT_DIR / "failed_ids.csv", index=False
        )
        print(f"\n   ⚠ {len(failed_ids)} failed - saved to checkpoints/failed_ids.csv")
    
    print(f"\n   ✅ Fetched {len(movies)} movies successfully")
    
    return movies


# ============================================================================
# STEP 3: SAVE DATA
# ============================================================================

def save_data(movies: list, config: ScrapeConfig) -> pd.DataFrame:
    """Save movies to CSV and pickle files."""
    print(f"\n{'='*60}")
    print("💾 STEP 3: Saving Data")
    print(f"{'='*60}")
    
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    
    df = pd.DataFrame(movies)
    
    # Ensure list columns are proper lists
    for col in ['genres', 'actors', 'directors', 'keywords']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: x if isinstance(x, list) else [])
    
    # Save
    timestamp = datetime.now().strftime("%Y%m%d")
    
    df.to_csv(config.OUTPUT_DIR / f"movies_scraped_{timestamp}.csv", index=False)
    df.to_pickle(config.OUTPUT_DIR / "movies_scraped.pkl")
    
    print(f"   ✅ Saved {len(df)} movies:")
    print(f"      - data/movies_scraped_{timestamp}.csv")
    print(f"      - data/movies_scraped.pkl")
    
    # Summary stats
    print(f"\n   📊 Summary:")
    print(f"      Years: {df['year'].min()} - {df['year'].max()}")
    print(f"      Avg rating: {df['vote_average'].mean():.2f}")
    print(f"      Genres: {df['genres'].explode().nunique()} unique")
    
    return df


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point with incremental support."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape movies from IMDb/TMDB')
    parser.add_argument('--full', action='store_true', help='Full re-scrape (ignore existing)')
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("🎬 MOVIE SCRAPER - Optimized Version")
    print("=" * 60)
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    config = ScrapeConfig()
    
    # Check mode
    incremental = config.INCREMENTAL and not args.full
    print(f"   Mode: {'INCREMENTAL' if incremental else 'FULL'}")
    
    # Validate API key
    if not config.API_KEY or config.API_KEY == "your_api_key_here":
        print("\n❌ TMDB API key not set!")
        print("   Set TMDB_API_KEY in your .env file or edit ScrapeConfig.API_KEY")
        return
    
    # Get existing movie IDs from database (for incremental mode)
    existing_ids = set()
    if incremental and DATABASE_AVAILABLE:
        try:
            existing_ids = get_existing_imdb_ids()
            print(f"   Existing movies in database: {len(existing_ids)}")
        except Exception as e:
            print(f"   ⚠ Could not load existing IDs: {e}")
            existing_ids = set()
    
    # Check for existing IMDb IDs from previous scrape
    ids_file = config.CHECKPOINT_DIR / "imdb_ids.csv"
    if ids_file.exists():
        print(f"\n📂 Found existing IMDb IDs at {ids_file}")
        choice = input("   Use existing? [Y/n]: ").strip().lower()
        if choice != 'n':
            imdb_ids = pd.read_csv(ids_file)['imdb_id'].tolist()
            print(f"   ✓ Loaded {len(imdb_ids)} IDs from file")
        else:
            imdb_ids = scrape_imdb_ids(config)
    else:
        imdb_ids = scrape_imdb_ids(config)
    
    if not imdb_ids:
        print("❌ No IMDb IDs to process")
        return
    
    # INCREMENTAL: Filter out movies already in database
    if incremental and existing_ids:
        original_count = len(imdb_ids)
        imdb_ids = [id for id in imdb_ids if id not in existing_ids]
        skipped = original_count - len(imdb_ids)
        print(f"\n🔄 INCREMENTAL MODE:")
        print(f"   Total from IMDb: {original_count}")
        print(f"   Already in DB: {skipped} (skipping)")
        print(f"   New to fetch: {len(imdb_ids)}")
        
        if len(imdb_ids) == 0:
            print("\n✅ Database is up to date! No new movies to fetch.")
            return
    
    # Fetch from TMDB
    movies = fetch_all_movies(imdb_ids, config)
    
    if not movies:
        print("❌ No movies fetched")
        return
    
    # Save (merge with existing if incremental)
    new_df = pd.DataFrame(movies)
    
    # Load existing data and merge
    existing_pkl = config.OUTPUT_DIR / "movies_scraped.pkl"
    if incremental and existing_pkl.exists():
        try:
            existing_df = pd.read_pickle(existing_pkl)
            print(f"\n📦 Merging with existing data ({len(existing_df)} movies)")
            
            # Combine and remove duplicates by imdb_id
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['imdb_id'], keep='last')
            
            print(f"   Combined total: {len(combined_df)} movies")
            df = combined_df
        except Exception as e:
            print(f"   ⚠ Could not merge: {e}")
            df = new_df
    else:
        df = new_df
    
    # Save
    df = save_data(df.to_dict('records'), config)
    
    # Done
    print("\n" + "=" * 60)
    print("✅ SCRAPING COMPLETE!")
    print("=" * 60)
    print(f"   Total movies: {len(df)}")
    print(f"   New movies added: {len(movies)}")
    print(f"   Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n   Next steps:")
    print("   1. Run data_preprocessing.ipynb to compute similarity matrix")
    print("   2. Run python scripts/migrate_to_db.py to update database")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

