"""
Quick script to test if your TMDB API key or access token is valid.

TMDB supports two authentication methods:
1. Access Token (v4 API) - Bearer token (preferred)
2. API Key (v3 API) - Query parameter

Usage:
    python test_tmdb_api_key.py

Or set as environment variables:
    set TMDB_ACCESS_TOKEN=your_token_here  (Windows - Bearer token, preferred)
    set TMDB_API_KEY=your_key_here  (Windows - API key, fallback)
    export TMDB_ACCESS_TOKEN=your_token_here  (Linux/Mac - Bearer token)
    export TMDB_API_KEY=your_key_here  (Linux/Mac - API key)
    python test_tmdb_api_key.py
"""
import os
import requests
import sys

def test_tmdb_bearer_token(access_token: str) -> bool:
    """
    Test if a TMDB Bearer token (v4 API) is valid.
    
    Args:
        access_token: Your TMDB access token
        
    Returns:
        True if valid, False otherwise
    """
    if not access_token or access_token.strip() == "":
        print("❌ Access token is empty!")
        return False
    
    # Test with Bearer token authentication (v4 API)
    test_url = "https://api.themoviedb.org/3/movie/603?language=en-US"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "accept": "application/json"
    }
    
    try:
        response = requests.get(test_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Bearer token is VALID!")
            print(f"   Test movie: {data.get('title', 'Unknown')} ({data.get('release_date', 'Unknown')})")
            return True
        elif response.status_code == 401:
            print("❌ Bearer token is INVALID (401 Unauthorized)")
            print("   This usually means:")
            print("   - The token is incorrect or expired")
            print("   - The token has been revoked")
            return False
        elif response.status_code == 429:
            print("⚠️  Rate limit exceeded (429 Too Many Requests)")
            print("   Your token is valid, but you've made too many requests.")
            print("   Wait a few minutes and try again.")
            return True  # Token is valid, just rate limited
        else:
            print(f"❌ Unexpected error: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out. Check your internet connection.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_tmdb_api_key(api_key: str) -> bool:
    """
    Test if a TMDB API key is valid by making a simple API call.
    
    Args:
        api_key: Your TMDB API key
        
    Returns:
        True if valid, False otherwise
    """
    if not api_key or api_key.strip() == "":
        print("❌ API key is empty!")
        return False
    
    # Test with a simple API call - get movie details for a well-known movie (The Matrix)
    test_url = f"https://api.themoviedb.org/3/movie/603?api_key={api_key}&language=en-US"
    
    try:
        response = requests.get(test_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API key is VALID!")
            print(f"   Test movie: {data.get('title', 'Unknown')} ({data.get('release_date', 'Unknown')})")
            return True
        elif response.status_code == 401:
            print("❌ API key is INVALID (401 Unauthorized)")
            print("   This usually means:")
            print("   - The API key is incorrect")
            print("   - The API key has been revoked")
            print("   - The API key format is wrong")
            return False
        elif response.status_code == 429:
            print("⚠️  Rate limit exceeded (429 Too Many Requests)")
            print("   Your API key is valid, but you've made too many requests.")
            print("   Wait a few minutes and try again.")
            return True  # Key is valid, just rate limited
        else:
            print(f"❌ Unexpected error: HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out. Check your internet connection.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    """Main function to test TMDB authentication (Bearer token or API key)."""
    print("=" * 60)
    print("🔑 TMDB Authentication Tester")
    print("=" * 60)
    print()
    
    # Try to get access token first (preferred method)
    access_token = os.getenv("TMDB_ACCESS_TOKEN", "")
    api_key = os.getenv("TMDB_API_KEY", "")
    
    # If not in environment, ask user
    if not access_token and not api_key:
        print("No TMDB_ACCESS_TOKEN or TMDB_API_KEY found in environment variables.")
        print("\nWhich authentication method do you want to use?")
        print("1. Bearer Token (Access Token) - Recommended (v4 API)")
        print("2. API Key - Legacy method (v3 API)")
        choice = input("Enter 1 or 2 (or press Enter to skip): ").strip()
        
        if choice == "1" or not choice:
            access_token = input("Enter your TMDB Access Token (Bearer token): ").strip()
        elif choice == "2":
            api_key = input("Enter your TMDB API Key: ").strip()
        
        if not access_token and not api_key:
            print("\n⚠️  No authentication provided. Exiting.")
            print("\nTo get TMDB authentication:")
            print("1. Go to https://www.themoviedb.org/settings/api")
            print("2. Sign up or log in")
            print("3. For Bearer Token: Create an access token (v4 API)")
            print("4. For API Key: Request an API key (v3 API)")
            sys.exit(1)
    
    is_valid = False
    auth_type = ""
    
    # Test Bearer token first (preferred)
    if access_token:
        print(f"Testing Bearer token: {access_token[:8]}...{access_token[-4:] if len(access_token) > 12 else '****'}")
        print("(Using v4 API with Bearer token authentication)")
        print()
        is_valid = test_tmdb_bearer_token(access_token)
        auth_type = "Bearer token"
    # Fall back to API key
    elif api_key:
        print(f"Testing API key: {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else '****'}")
        print("(Using v3 API with query parameter authentication)")
        print()
        is_valid = test_tmdb_api_key(api_key)
        auth_type = "API key"
    
    print()
    if is_valid:
        print("=" * 60)
        print(f"✅ Your {auth_type} is working correctly!")
        print("=" * 60)
        print("\nTo use this in Streamlit Cloud:")
        print("1. Go to your Streamlit Cloud app settings")
        print("2. Click 'Secrets' or 'Environment variables'")
        if access_token:
            print("3. Add: TMDB_ACCESS_TOKEN = your_access_token_here")
        else:
            print("3. Add: TMDB_API_KEY = your_api_key_here")
        print("4. Save and redeploy")
    else:
        print("=" * 60)
        print(f"❌ {auth_type} test failed. Please check your credentials.")
        print("=" * 60)
        print("\nTo get new credentials:")
        print("1. Go to https://www.themoviedb.org/settings/api")
        print("2. Sign up or log in")
        if access_token:
            print("3. Create a new access token (v4 API)")
        else:
            print("3. Request a new API key (v3 API)")
        print("4. Make sure to copy the entire token/key")
    
    return 0 if is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
