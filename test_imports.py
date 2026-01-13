"""
Test script to check if all imports work correctly.
Run this to identify which import is failing.
"""
import sys
from pathlib import Path

print("Testing imports...")
print("=" * 60)

# Test 1: Basic Python imports
try:
    import streamlit as st
    print("✅ streamlit")
except Exception as e:
    print(f"❌ streamlit: {e}")
    sys.exit(1)

try:
    import requests
    print("✅ requests")
except Exception as e:
    print(f"❌ requests: {e}")
    sys.exit(1)

try:
    import pandas as pd
    print("✅ pandas")
except Exception as e:
    print(f"❌ pandas: {e}")
    sys.exit(1)

# Test 2: Path setup
try:
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    print(f"✅ Path setup: {project_root}")
except Exception as e:
    print(f"❌ Path setup: {e}")
    sys.exit(1)

# Test 3: Config import
try:
    from src.config import Config
    print("✅ src.config")
    print(f"   DATA_PATH: {Config.DATA_PATH}")
except Exception as e:
    print(f"❌ src.config: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Database path check
try:
    DB_PATH = Path(Config.DATA_PATH) / "movies.db"
    USE_DATABASE = DB_PATH.exists()
    print(f"✅ Database check: {DB_PATH} exists={USE_DATABASE}")
except Exception as e:
    print(f"❌ Database check: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Database imports (if database exists)
if USE_DATABASE:
    try:
        from src.database import (
            get_all_titles,
            get_all_genres,
            get_movie_by_title,
            get_recommendations_from_cache,
            filter_by_genre,
            get_all_movies,
            get_database_stats,
            get_all_tv_titles,
            get_tv_by_title,
            get_tv_recommendations_from_cache,
            get_connection,
            migrate_add_poster_and_providers,
            get_movie_genres,
            get_tv_genres
        )
        print("✅ src.database imports")
    except Exception as e:
        print(f"❌ src.database imports: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
else:
    print("⚠️  Database not found, skipping database imports")

# Test 6: Analytics import
try:
    import importlib.util
    analytics_path = Path(__file__).parent / "app" / "components" / "analytics.py"
    if analytics_path.exists():
        spec = importlib.util.spec_from_file_location("analytics", analytics_path)
        analytics_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(analytics_module)
        print("✅ analytics module")
    else:
        print(f"⚠️  Analytics file not found: {analytics_path}")
except Exception as e:
    print(f"❌ analytics import: {e}")
    import traceback
    traceback.print_exc()
    # Don't exit - analytics is optional

print("=" * 60)
print("✅ All critical imports successful!")
