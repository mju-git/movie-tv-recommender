"""
Download Provider Logos from TMDB

This script downloads provider logos from TMDB API and saves them locally.
Run from project root:
    python scripts/download_provider_logos.py
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
import json
from src.config import Config

# Provider name to TMDB provider ID mapping
# Using multiple IDs for variations (e.g., HBO, Max, HBO Max)
PROVIDER_IDS = {
    # Netflix
    'Netflix': 8,
    
    # Disney - try multiple
    'Disney+': 337,
    'Disney Plus': 337,
    'Disney': 337,
    
    # Prime Video
    'Prime Video': 9,
    'Amazon Prime Video': 9,
    'Amazon Prime': 9,
    
    # HBO - try multiple variations
    'HBO Max': 31,
    'HBO': 31,
    'Max': 31,
    
    # Paramount
    'Paramount+': 531,
    'Paramount Plus': 531,
    'Paramount': 531,
    
    # Apple TV
    'Apple TV+': 350,
    'Apple TV Plus': 350,
    'Apple TV': 350,
    
    # Others
    'Hulu': 15,
    'Peacock': 386,
    'Crunchyroll': 283,
    'Showtime': 37,
    'Starz': 318,
    'Discovery+': 445,
    'Discovery Plus': 445,
    'Discovery': 445,
    'ESPN+': 190,
    'ESPN Plus': 190,
    'ESPN': 190,
    'YouTube': 192,
    'YouTube Premium': 192,
    'CBS': 258,
    'CBS All Access': 258,
    'fuboTV': 257,
    'fubo TV': 257,
    'Sling TV': 177,
    'Tubi': 73,
    'Pluto TV': 300,
    'Freevee': 119,
    'Crackle': 12,
    'Vudu': 7,
    'Google Play': 3,
    'Google Play Movies': 3,
    'Microsoft Store': 68,
    'iTunes': 2,
    'Rakuten TV': 35,
    # BBC
    'BBC': 531,  # BBC iPlayer
    'BBC iPlayer': 531,
    # Circus (may not be in TMDB, but adding for completeness)
    'Circus': None,  # Will need manual download
}

def get_provider_info(provider_id: int, api_key: str) -> dict:
    """Get provider info from TMDB API."""
    url = f"https://api.themoviedb.org/3/watch/providers/movie?api_key={api_key}&language=en-US"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            providers = response.json().get('results', [])
            for provider in providers:
                if provider.get('provider_id') == provider_id:
                    return provider
    except Exception as e:
        print(f"   Error fetching provider {provider_id}: {e}")
    
    return None

def download_logo(logo_path: str, save_path: Path) -> bool:
    """Download logo from TMDB CDN."""
    if not logo_path:
        return False
    
    url = f"https://image.tmdb.org/t/p/original{logo_path}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            save_path.write_bytes(response.content)
            return True
    except Exception as e:
        print(f"   Error downloading logo: {e}")
    
    return False

def main():
    """Download all provider logos."""
    print("=" * 60)
    print("Downloading Provider Logos from TMDB")
    print("=" * 60)
    
    api_key = Config.TMDB_API_KEY
    if not api_key:
        print("❌ TMDB_API_KEY not found in .env file!")
        return
    
    # Create logos directory
    logos_dir = project_root / "data" / "provider_logos"
    logos_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 Saving logos to: {logos_dir}")
    
    # Get all providers from TMDB
    print("\n📥 Fetching provider list from TMDB...")
    url = f"https://api.themoviedb.org/3/watch/providers/movie?api_key={api_key}&language=en-US"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            print(f"❌ Error fetching providers: {response.status_code}")
            return
        
        all_providers = response.json().get('results', [])
        print(f"   Found {len(all_providers)} providers on TMDB")
        
        # Create provider ID to info mapping
        provider_map = {}
        for provider in all_providers:
            provider_map[provider.get('provider_id')] = provider
        
        # Group providers by ID (multiple names can map to same logo)
        # Normalized names for final filenames
        NORMALIZED_NAMES = {
            8: 'netflix',
            337: 'disney-plus',
            9: 'prime-video',
            31: 'hbo-max',  # HBO, Max, HBO Max all use this
            531: 'paramount-plus',
            350: 'apple-tv-plus',
            15: 'hulu',
            386: 'peacock',
            283: 'crunchyroll',
            37: 'showtime',
            318: 'starz',
            445: 'discovery-plus',
            190: 'espn-plus',
            192: 'youtube',
            258: 'cbs',
            257: 'fubotv',
            177: 'sling-tv',
            73: 'tubi',
            300: 'pluto-tv',
            119: 'freevee',
            12: 'crackle',
            7: 'vudu',
            3: 'google-play',
            68: 'microsoft-store',
            2: 'itunes',
            35: 'rakuten-tv',
        }
        
        # Download logos for unique provider IDs
        print(f"\n📥 Downloading logos for unique providers...")
        downloaded = 0
        failed = 0
        seen_ids = set()
        
        # Process each provider name, but only download once per ID
        for provider_name, provider_id in PROVIDER_IDS.items():
            # Skip None IDs (like Circus which may not be in TMDB)
            if provider_id is None:
                print(f"   ⚠️  {provider_name} - not available in TMDB (needs manual download)")
                failed += 1
                continue
            
            # Skip if we already downloaded this ID
            if provider_id in seen_ids:
                continue
            
            provider_info = provider_map.get(provider_id)
            
            if not provider_info:
                print(f"   ⚠️  {provider_name} (ID: {provider_id}) not found in TMDB list")
                failed += 1
                seen_ids.add(provider_id)  # Mark as tried
                continue
            
            logo_path = provider_info.get('logo_path')
            if not logo_path:
                print(f"   ⚠️  {provider_name} (ID: {provider_id}) has no logo_path")
                failed += 1
                seen_ids.add(provider_id)  # Mark as tried
                continue
            
            # Use normalized filename
            normalized = NORMALIZED_NAMES.get(provider_id, provider_name.lower().replace(' ', '-'))
            filename = f"{normalized}.png"
            save_path = logos_dir / filename
            
            if save_path.exists():
                print(f"   ✓ {provider_name} → {filename} (already exists)")
                downloaded += 1
                seen_ids.add(provider_id)
                continue
            
            if download_logo(logo_path, save_path):
                print(f"   ✓ {provider_name} → {filename}")
                downloaded += 1
            else:
                print(f"   ❌ {provider_name} (download failed)")
                failed += 1
            
            seen_ids.add(provider_id)
        
        print(f"\n✅ Downloaded: {downloaded}")
        if failed > 0:
            print(f"⚠️  Failed: {failed}")
        
        print("\n" + "=" * 60)
        print("Download complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

