# 🚀 Deployment Guide: Streamlit Cloud

Complete guide to deploy the Movie & TV Recommender to Streamlit Cloud.

## 📋 Prerequisites

- GitHub account
- Streamlit Cloud account ([sign up here](https://share.streamlit.io))
- TMDB API key ([get one here](https://www.themoviedb.org/settings/api))
- Git installed locally

## 🔧 Step 1: Prepare Your Repository

### 1.1 Clean Up Project

Remove unnecessary files and create sample database:

```bash
# Clean up large files (keeps structure, removes data)
python scripts/cleanup_project.py

# Create sample database for deployment (~1-2 MB)
python scripts/create_sample_database.py
```

### 1.2 Verify Files to Commit

**Files that SHOULD be committed:**
- ✅ All Python files (`app/`, `src/`, `scripts/`)
- ✅ `requirements.txt`
- ✅ `README.md`
- ✅ `.gitignore`
- ✅ `.gitattributes` (for Git LFS)
- ✅ `.streamlit/config.toml`
- ✅ `.env.template`
- ✅ `data/.gitkeep`
- ✅ `data/provider_logos/*.png` (small logo files)
- ✅ Jupyter notebooks (for documentation)
- ✅ `data/movies.db` (via Git LFS - see Step 2)

**Files that should NOT be committed:**
- ❌ `.env` (contains secrets)
- ❌ `data/*.pkl` (large pickle files)
- ❌ `data/*.csv` (large CSV files)
- ❌ `__pycache__/` directories
- ❌ `checkpoints/` directory

## 📦 Step 2: Set Up Git LFS (for Database)

The database file is large and should be tracked with Git LFS:

```bash
# Install Git LFS (if not already installed)
# Windows: Download from https://git-lfs.github.com/
# macOS: brew install git-lfs
# Linux: sudo apt-get install git-lfs

# Initialize Git LFS
git lfs install

# Track database files with LFS
git lfs track "data/*.db"
git lfs track "data/*.db-journal"
git lfs track "data/*.db-wal"
git lfs track "data/*.db-shm"

# Verify tracking
git lfs ls-files
```

## 📝 Step 3: Initialize Git Repository

```bash
# Initialize repository (if not already done)
git init

# Add all files
git add .

# Check what will be committed
git status

# Commit
git commit -m "Initial commit: Movie & TV Recommender System"
```

## 🌐 Step 4: Push to GitHub

### 4.1 Create GitHub Repository

1. Go to [GitHub](https://github.com/new)
2. Create a new repository (e.g., `movie-tv-recommender`)
3. **DO NOT** initialize with README, .gitignore, or license (we already have these)

### 4.2 Push to GitHub

```bash
# Add remote (replace YOUR_USERNAME and REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Note:** If using Git LFS, the first push may take longer as it uploads the database file.

## ☁️ Step 5: Deploy to Streamlit Cloud

### 5.1 Connect Repository

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**
3. Sign in with GitHub
4. Select your repository
5. Choose the branch (usually `main`)

### 5.2 Configure App Settings

**Main file path:**
```
app/main.py
```

**Python version:**
```
3.8
```

### 5.3 Set Environment Variables

Click **"Advanced settings"** and add:

| Variable | Value | Description |
|----------|-------|-------------|
| `TMDB_API_KEY` | `your_api_key_here` | Your TMDB API key |
| `DATA_PATH` | `data/` | Path to data directory |

**Important:** Never commit your `.env` file or API keys to GitHub!

### 5.4 Deploy

Click **"Deploy"** and wait for the build to complete (usually 2-5 minutes).

## ✅ Step 6: Verify Deployment

1. **Check build logs** for any errors
2. **Test the app:**
   - Open the deployed URL
   - Try selecting a movie/TV show
   - Get recommendations
   - Check analytics dashboard
3. **Monitor performance:**
   - First load may be slower (database initialization)
   - Subsequent loads should be fast

## 🔄 Updating Your Deployment

When you make changes:

```bash
# Make your changes
# ...

# Commit changes
git add .
git commit -m "Description of changes"

# Push to GitHub
git push origin main
```

Streamlit Cloud will automatically redeploy when you push to the main branch.

## 🐛 Troubleshooting

### Build Fails

**Error: "Module not found"**
- Check `requirements.txt` includes all dependencies
- Verify import paths are correct

**Error: "TMDB_API_KEY not set"**
- Verify environment variable is set in Streamlit Cloud settings
- Check variable name matches exactly (case-sensitive)

**Error: "Database not found"**
- Ensure `data/movies.db` is committed (via Git LFS)
- Check `DATA_PATH` environment variable is set to `data/`

### App Runs But Shows Errors

**"No recommendations found"**
- Database may be empty or corrupted
- Re-run `create_sample_database.py` locally and push

**Slow performance**
- Sample database should be small (~1-2 MB)
- Check Streamlit Cloud logs for errors

### Git LFS Issues

**"Git LFS: file locked"**
- Run: `git lfs unlock`
- Or: `git lfs pull` to download LFS files

**Large file size warnings**
- Ensure `.gitattributes` is committed
- Verify files are tracked: `git lfs ls-files`

## 📊 Database Size Considerations

- **Sample database:** ~1-2 MB (recommended for Streamlit Cloud)
- **Full database:** Can be 100+ MB (may cause deployment issues)

For production with full dataset:
1. Use sample database for initial deployment
2. Consider external database (PostgreSQL, etc.) for larger datasets
3. Or use Streamlit Cloud's file system (limited to 1 GB total)

## 🔐 Security Best Practices

1. ✅ Never commit `.env` files
2. ✅ Use `.env.template` for documentation
3. ✅ Store secrets in Streamlit Cloud environment variables
4. ✅ Use Git LFS for large files (not for secrets!)
5. ✅ Review `.gitignore` before committing

## 📚 Additional Resources

- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-community-cloud)
- [Git LFS Documentation](https://git-lfs.github.com/)
- [TMDB API Documentation](https://developers.themoviedb.org/3)

---

**Need help?** Check the [README.md](README.md) or open an issue on GitHub.
