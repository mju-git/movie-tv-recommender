"""
TV Show Scraper - Incremental Version
======================================
Fetches TV shows from IMDb and enriches with TMDB data.

Features:
- INCREMENTAL MODE: Only downloads shows not already in database
- Rate limiting (respects TMDB API limits)
- Checkpoints (resume if interrupted)
- Combined API calls with append_to_response
- Error handling with retries

Usage:
    python scripts/scrape_tv_shows.py              # Incremental (default)
    python scripts/scrape_tv_shows.py --full       # Full re-scrape

Configuration:
    Edit the CONFIG section below.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
import pandas as pd
import time
from datetime import datetime

from bs4 import BeautifulSoup

# Try to import selenium
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
    from src.database import get_existing_tv_imdb_ids
    DATABASE_AVAILABLE = True
except:
    DATABASE_AVAILABLE = False


# ============================================================================
# CONFIGURATION
# ============================================================================

class ScrapeConfig:
    """Scraping configuration for TV shows."""
    
    API_KEY = TMDB_API_KEY or "your_api_key_here"
    
    # IMDb search criteria for TV shows
    MIN_RATING = 6.0          # TV shows - higher bar
    MIN_VOTES = 2000          # Minimum votes
    
    # Incremental mode
    INCREMENTAL = True
    
    # Limits
    MAX_SHOWS = None          # Set to limit, or None for all
    
    # Rate limiting
    REQUESTS_PER_SECOND = 5   # Faster rate: 5 requests/second (was 3)
    IMDB_DELAY = 2            # Seconds between IMDb page requests (reduced from 5 to 2)
    
    # Checkpoint settings  
    CHECKPOINT_EVERY = 500
    
    # Paths
    CHECKPOINT_DIR = project_root / "checkpoints"
    OUTPUT_DIR = project_root / "data"


# ============================================================================
# STEP 1: SCRAPE IMDB IDs FOR TV SHOWS
# ============================================================================

def scrape_imdb_tv_ids(config: ScrapeConfig) -> list:
    """
    Scrape TV show IDs from IMDb search results.
    """
    if not SELENIUM_AVAILABLE:
        print("❌ Selenium required for IMDb scraping")
        return []
    
    print(f"\n{'='*60}")
    print("📺 STEP 1: Scraping IMDb TV Show IDs")
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
        return []
    
    # TV shows use title_type=tv_series
    url = (
        f"https://www.imdb.com/search/title/"
        f"?title_type=tv_series,tv_miniseries"
        f"&user_rating={config.MIN_RATING},10"
        f"&sort=num_votes,desc"
        f"&num_votes={config.MIN_VOTES},"
        f"&count=250"
    )
    
    # Print FULL URL for verification
    print(f"   Full URL: {url}")
    print(f"   Criteria: rating >= {config.MIN_RATING}, votes >= {config.MIN_VOTES:,}")
    
    driver.get(url)
    time.sleep(config.IMDB_DELAY)  # Wait for page to fully load
    
    tt_set = set()
    page_count = 0
    
    while True:
        page_count += 1
        time.sleep(config.IMDB_DELAY)  # Delay to avoid 503 errors
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        links = soup.select('a.ipc-title-link-wrapper[href*="/title/tt"]')
        
        for link in links:
            href = link.get('href', '')
            if '/title/tt' in href:
                tt_id = href.split('/title/')[-1].split('/')[0]
                tt_set.add(tt_id)
        
        print(f"   Page {page_count}: {len(tt_set)} unique shows found")
        
        if config.MAX_SHOWS and len(tt_set) >= config.MAX_SHOWS:
            print(f"   ✓ Reached limit of {config.MAX_SHOWS} shows")
            break
        
        try:
            show_more = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".ipc-see-more__button"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", show_more)
            time.sleep(1)  # Reduced from 2 to 1 second
            driver.execute_script("arguments[0].click();", show_more)
            time.sleep(2)  # Reduced from 3 to 2 seconds
        except:
            print("   ✓ No more pages")
            break
    
    driver.quit()
    
    tt_list = list(tt_set)
    if config.MAX_SHOWS:
        tt_list = tt_list[:config.MAX_SHOWS]
    
    # Save for resume
    config.CHECKPOINT_DIR.mkdir(exist_ok=True)
    pd.DataFrame({'imdb_id': tt_list}).to_csv(
        config.CHECKPOINT_DIR / "tv_imdb_ids.csv", index=False
    )
    
    print(f"\n   ✅ Found {len(tt_list)} TV shows")
    
    return tt_list


# ============================================================================
# STEP 2: FETCH TMDB DATA FOR TV SHOWS
# ============================================================================

def fetch_tv_from_tmdb(imdb_id: str, api_key: str) -> dict:
    """
    Fetch TV show data from TMDB using append_to_response.
    Uses /find endpoint to convert IMDb ID to TMDB ID, then fetches details.
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
            return None
        
        data = response.json()
        tv_results = data.get('tv_results', [])
        
        if not tv_results:
            return None
        
        tmdb_id = tv_results[0]['id']
        
        # Now fetch full details with append_to_response
        details_url = (
            f"https://api.themoviedb.org/3/tv/{tmdb_id}"
            f"?api_key={api_key}"
            f"&language=en-US"
            f"&append_to_response=credits,keywords,watch/providers"
        )
        
        response = requests.get(details_url, timeout=15)
        if response.status_code == 200:
            result = response.json()
            result['imdb_id'] = imdb_id  # Preserve IMDb ID
            return result
        
        return None
        
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


def process_tv_data(raw: dict) -> dict:
    """Transform raw TMDB TV response into clean format."""
    if not raw or "_error" in raw:
        return None
    
    try:
        # Get first air date year
        first_air = raw.get('first_air_date', '')
        year = int(first_air[:4]) if first_air and len(first_air) >= 4 else None
        
        # Poster URL
        poster_path = raw.get('poster_path', '')
        poster_url = f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else None
        
        show = {
            'id': raw.get('id'),
            'imdb_id': raw.get('imdb_id'),
            'title': raw.get('name'),
            'year': year,
            'vote_average': raw.get('vote_average'),
            'vote_count': raw.get('vote_count'),
            'popularity': raw.get('popularity'),
            'number_of_seasons': raw.get('number_of_seasons'),
            'number_of_episodes': raw.get('number_of_episodes'),
            'status': raw.get('status'),  # Ended, Returning Series, etc.
            'overview': raw.get('overview', ''),
            'tagline': raw.get('tagline', ''),
            'poster_url': poster_url,
        }
        
        # Genres
        show['genres'] = [g['name'] for g in raw.get('genres', [])]
        
        # Actors (top 5 from cast)
        credits = raw.get('credits', {})
        cast = credits.get('cast', [])
        show['actors'] = [
            c['name'] for c in sorted(cast, key=lambda x: x.get('order', 999))[:5]
        ]
        
        # Creators (like directors for movies)
        show['creators'] = [c['name'] for c in raw.get('created_by', [])]
        
        # Keywords
        keywords_data = raw.get('keywords', {})
        show['keywords'] = [k['name'] for k in keywords_data.get('results', [])]
        
        # Watch providers (US, DE, HR)
        watch_providers_data = raw.get('watch/providers', {})
        show['watch_providers'] = parse_watch_providers(watch_providers_data)
        
        return show
        
    except Exception as e:
        print(f"   ⚠ Error processing: {e}")
        return None


def fetch_all_tv_shows(imdb_ids: list, config: ScrapeConfig) -> list:
    """Fetch all TV shows with rate limiting and checkpoints."""
    print(f"\n{'='*60}")
    print("📺 STEP 2: Fetching TMDB TV Data")
    print(f"{'='*60}")
    
    shows = []
    failed_ids = []
    
    # Load existing checkpoint
    checkpoint_file = config.CHECKPOINT_DIR / "tv_checkpoint.pkl"
    start_index = 0
    
    if checkpoint_file.exists():
        try:
            existing = pd.read_pickle(checkpoint_file)
            shows = existing.to_dict('records')
            fetched_ids = {s['imdb_id'] for s in shows if s.get('imdb_id')}
            start_index = len([i for i in imdb_ids if i in fetched_ids])
            print(f"   📂 Resuming from checkpoint: {len(shows)} already fetched")
        except:
            pass
    
    remaining = len(imdb_ids) - start_index
    est_minutes = remaining / config.REQUESTS_PER_SECOND / 60
    
    print(f"   Shows to fetch: {remaining}")
    print(f"   Estimated time: {est_minutes:.1f} minutes")
    print()
    
    for i, imdb_id in enumerate(imdb_ids[start_index:], start=start_index):
        time.sleep(1 / config.REQUESTS_PER_SECOND)
        
        result = None
        for attempt in range(3):
            result = fetch_tv_from_tmdb(imdb_id, config.API_KEY)
            
            if result and "_error" in result:
                time.sleep(1)  # Reduced from 2 to 1 second
            else:
                break
        
        if result and "_error" not in result:
            processed = process_tv_data(result)
            if processed:
                shows.append(processed)
        else:
            failed_ids.append(imdb_id)
        
        if (i + 1) % 100 == 0:
            pct = (i + 1) / len(imdb_ids) * 100
            print(f"   Progress: {i + 1}/{len(imdb_ids)} ({pct:.1f}%) - ✓{len(shows)} ✗{len(failed_ids)}")
        
        if (i + 1) % config.CHECKPOINT_EVERY == 0:
            df = pd.DataFrame(shows)
            df.to_pickle(checkpoint_file)
            print(f"   💾 Checkpoint: {len(shows)} shows saved")
    
    if failed_ids:
        pd.DataFrame({'imdb_id': failed_ids}).to_csv(
            config.CHECKPOINT_DIR / "tv_failed_ids.csv", index=False
        )
    
    print(f"\n   ✅ Fetched {len(shows)} TV shows successfully")
    
    return shows


# ============================================================================
# STEP 3: SAVE DATA
# ============================================================================

def save_tv_data(shows: list, config: ScrapeConfig) -> pd.DataFrame:
    """Save TV shows to pickle file."""
    print(f"\n{'='*60}")
    print("💾 STEP 3: Saving TV Data")
    print(f"{'='*60}")
    
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    
    df = pd.DataFrame(shows)
    
    for col in ['genres', 'actors', 'creators', 'keywords']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: x if isinstance(x, list) else [])
    
    timestamp = datetime.now().strftime("%Y%m%d")
    
    df.to_csv(config.OUTPUT_DIR / f"tv_shows_scraped_{timestamp}.csv", index=False)
    df.to_pickle(config.OUTPUT_DIR / "tv_shows_scraped.pkl")
    
    print(f"   ✅ Saved {len(df)} TV shows")
    
    if len(df) > 0:
        print(f"\n   📊 Summary:")
        print(f"      Years: {df['year'].min()} - {df['year'].max()}")
        print(f"      Avg rating: {df['vote_average'].mean():.2f}")
    
    return df


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point with incremental support."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape TV shows from IMDb/TMDB')
    parser.add_argument('--full', action='store_true', help='Full re-scrape')
    args = parser.parse_args()
    
    print("\n" + "=" * 60)
    print("📺 TV SHOW SCRAPER - Incremental Version")
    print("=" * 60)
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    config = ScrapeConfig()
    
    incremental = config.INCREMENTAL and not args.full
    print(f"   Mode: {'INCREMENTAL' if incremental else 'FULL'}")
    
    if not config.API_KEY or config.API_KEY == "your_api_key_here":
        print("\n❌ TMDB API key not set!")
        return
    
    # Get existing IDs from database
    existing_ids = set()
    if incremental and DATABASE_AVAILABLE:
        try:
            existing_ids = get_existing_tv_imdb_ids()
            print(f"   Existing shows in database: {len(existing_ids)}")
        except Exception as e:
            print(f"   ⚠ Could not load existing IDs: {e}")
    
    # Check for cached IMDb IDs
    ids_file = config.CHECKPOINT_DIR / "tv_imdb_ids.csv"
    if ids_file.exists():
        print(f"\n📂 Found existing TV IMDb IDs at {ids_file}")
        choice = input("   Use existing? [Y/n]: ").strip().lower()
        if choice != 'n':
            imdb_ids = pd.read_csv(ids_file)['imdb_id'].tolist()
            print(f"   ✓ Loaded {len(imdb_ids)} IDs from file")
        else:
            imdb_ids = scrape_imdb_tv_ids(config)
    else:
        imdb_ids = scrape_imdb_tv_ids(config)
    
    if not imdb_ids:
        print("❌ No TV show IDs to process")
        return
    
    # Filter for incremental
    if incremental and existing_ids:
        original_count = len(imdb_ids)
        imdb_ids = [id for id in imdb_ids if id not in existing_ids]
        print(f"\n🔄 INCREMENTAL: {original_count} total, {len(imdb_ids)} new")
        
        if len(imdb_ids) == 0:
            print("\n✅ Database is up to date!")
            return
    
    # Fetch from TMDB
    shows = fetch_all_tv_shows(imdb_ids, config)
    
    if not shows:
        print("❌ No TV shows fetched")
        return
    
    # Merge with existing
    new_df = pd.DataFrame(shows)
    existing_pkl = config.OUTPUT_DIR / "tv_shows_scraped.pkl"
    
    if incremental and existing_pkl.exists():
        try:
            existing_df = pd.read_pickle(existing_pkl)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['imdb_id'], keep='last')
            df = combined_df
        except:
            df = new_df
    else:
        df = new_df
    
    save_tv_data(df.to_dict('records'), config)
    
    print("\n" + "=" * 60)
    print("✅ TV SCRAPING COMPLETE!")
    print("=" * 60)
    print(f"   Total shows: {len(df)}")
    print(f"   New shows added: {len(shows)}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

