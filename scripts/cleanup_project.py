"""
Cleanup script to remove unnecessary files before GitHub upload.
Run this before committing to GitHub.
"""
import os
from pathlib import Path
import shutil

def cleanup_project():
    """Remove unnecessary files for GitHub."""
    print("=" * 60)
    print("🧹 Project Cleanup for GitHub")
    print("=" * 60)
    
    project_root = Path(__file__).parent.parent
    
    # Files/directories to remove
    # Note: .pkl, .db, and .csv files are excluded via .gitignore
    # We only remove cache and temporary files here
    to_remove = [
        # Checkpoints (temporary files)
        project_root / "checkpoints",
        
        # Cache
        project_root / "__pycache__",
        project_root / "src" / "__pycache__",
        project_root / "app" / "__pycache__",
        project_root / "app" / "components" / "__pycache__",
        project_root / "scripts" / "__pycache__",
        project_root / "tests" / "__pycache__",
        
        # Large media
        project_root / "*.mp4",
        project_root / "ezgif.com-video-to-gif.gif",
    ]
    
    removed_count = 0
    
    # Remove files
    for pattern in to_remove:
        if pattern.is_dir():
            if pattern.exists():
                shutil.rmtree(pattern)
                print(f"   ✓ Removed directory: {pattern.name}")
                removed_count += 1
        elif '*' in str(pattern):
            # Handle glob patterns
            parent = pattern.parent
            glob_pattern = pattern.name
            for file in parent.glob(glob_pattern):
                if file.is_file():
                    file.unlink()
                    print(f"   ✓ Removed: {file.name}")
                    removed_count += 1
        else:
            if pattern.exists():
                if pattern.is_file():
                    pattern.unlink()
                    print(f"   ✓ Removed: {pattern.name}")
                    removed_count += 1
                elif pattern.is_dir():
                    shutil.rmtree(pattern)
                    print(f"   ✓ Removed directory: {pattern.name}")
                    removed_count += 1
    
    # Remove .pyc files
    for pyc_file in project_root.rglob("*.pyc"):
        pyc_file.unlink()
        print(f"   ✓ Removed: {pyc_file.relative_to(project_root)}")
        removed_count += 1
    
    print(f"\n✅ Cleanup complete! Removed {removed_count} items.")
    print("\n📋 Note: Data files (.pkl, .db, .csv) are excluded via .gitignore")
    print("   They won't be uploaded to GitHub but remain on your local machine.")
    print("\n📋 Next steps:")
    print("   1. Test: streamlit run app/main.py")
    print("   2. Commit: git add . && git commit -m 'Clean project'")
    print("   3. Push: git push origin main")

if __name__ == "__main__":
    response = input("\n⚠️  This will delete data files and cache. Continue? [y/N]: ")
    if response.lower() == 'y':
        cleanup_project()
    else:
        print("Cancelled.")

