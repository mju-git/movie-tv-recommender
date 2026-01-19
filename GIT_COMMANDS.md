# 📝 Git Commands for Deployment

Step-by-step Git commands to prepare and deploy your project to GitHub and Streamlit Cloud.

## 🔧 Initial Setup

### 1. Check Git Status

```bash
# See what files are tracked/untracked
git status
```

### 2. Initialize Git LFS (for Database Files)

```bash
# Install Git LFS first (if not installed)
# Windows: Download from https://git-lfs.github.com/
# macOS: brew install git-lfs
# Linux: sudo apt-get install git-lfs

# Initialize Git LFS in your repository
git lfs install

# Verify .gitattributes exists and is correct
cat .gitattributes
```

### 3. Clean Up Project

```bash
# Remove unnecessary files (keeps structure)
python scripts/cleanup_project.py

# Create sample database for deployment
python scripts/create_sample_database.py
```

## 📦 Stage Files for Commit

### Add All Files

```bash
# Add all files (respects .gitignore)
git add .

# Or add specific files/directories
git add app/
git add src/
git add scripts/
git add requirements.txt
git add README.md
git add .gitignore
git add .gitattributes
git add .streamlit/
git add .env.template
git add data/.gitkeep
git add data/provider_logos/
git add data/movies.db  # This will use Git LFS
```

### Verify What Will Be Committed

```bash
# Check staged files
git status

# See file sizes (important for LFS)
git lfs ls-files

# Preview changes
git diff --cached
```

## 💾 Commit Changes

```bash
# Initial commit
git commit -m "Initial commit: Movie & TV Recommender System

- Content-based recommendation engine
- Support for movies and TV shows
- SQLite database with Git LFS
- Streamlit web interface
- Analytics dashboard"

# Or for updates
git commit -m "Add feature: [description]"
```

## 🌐 Push to GitHub

### First Time Setup

```bash
# Create repository on GitHub first, then:

# Add remote (replace YOUR_USERNAME and REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

### Subsequent Pushes

```bash
# After making changes
git add .
git commit -m "Description of changes"
git push origin main
```

## 🔍 Verify Git LFS

```bash
# Check which files are tracked by LFS
git lfs ls-files

# Should show:
# data/movies.db
# data/movies.db-journal (if exists)
# data/movies.db-wal (if exists)
# data/movies.db-shm (if exists)

# Check LFS status
git lfs status
```

## 🧹 Clean Up Before Commit

```bash
# Remove untracked files (be careful!)
git clean -n  # Preview what will be removed
git clean -f  # Actually remove untracked files

# Remove cached files (if .gitignore changed)
git rm -r --cached .
git add .
```

## 📋 Pre-Commit Checklist

Before committing, verify:

- [ ] `.env` file is NOT committed (check `.gitignore`)
- [ ] Large data files (`.pkl`, `.csv`) are NOT committed
- [ ] `__pycache__/` directories are ignored
- [ ] Database file is tracked with Git LFS
- [ ] `.gitattributes` is committed
- [ ] `requirements.txt` is up to date
- [ ] `README.md` is updated
- [ ] No secrets or API keys in code

## 🔄 Common Workflows

### Update Dependencies

```bash
# Update requirements.txt
pip freeze > requirements.txt

# Review and clean up
# Then commit
git add requirements.txt
git commit -m "Update dependencies"
git push origin main
```

### Add New Feature

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes
# ...

# Commit
git add .
git commit -m "Add new feature: [description]"

# Push branch
git push origin feature/new-feature

# Create pull request on GitHub
# After merge, update main branch
git checkout main
git pull origin main
```

### Fix Bug

```bash
# Create bugfix branch
git checkout -b bugfix/issue-description

# Fix the bug
# ...

# Commit
git add .
git commit -m "Fix: [description of fix]"

# Push and create pull request
git push origin bugfix/issue-description
```

## 🚨 Troubleshooting

### Git LFS Not Working

```bash
# Re-track files
git lfs track "data/*.db"
git add .gitattributes
git commit -m "Fix Git LFS tracking"

# Migrate existing files to LFS
git lfs migrate import --include="data/*.db"
```

### Large File Warning

```bash
# If you get "file too large" error:
# 1. Ensure Git LFS is installed and initialized
# 2. Check .gitattributes includes the file pattern
# 3. Remove file from Git history if needed:
git rm --cached data/movies.db
git commit -m "Remove large file, will add with LFS"
git lfs track "data/*.db"
git add data/movies.db
git commit -m "Add database with Git LFS"
```

### Undo Last Commit

```bash
# Undo commit but keep changes
git reset --soft HEAD~1

# Undo commit and discard changes (careful!)
git reset --hard HEAD~1
```

## 📊 Check Repository Size

```bash
# See repository size
du -sh .git

# See largest files
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  sed -n 's/^blob //p' | \
  sort --numeric-sort --key=2 | \
  tail -10
```

---

**Next Steps:** After pushing to GitHub, follow [DEPLOYMENT.md](DEPLOYMENT.md) to deploy to Streamlit Cloud.


