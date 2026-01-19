# 🎬 Movie & TV Show Recommender System

A professional content-based recommendation web application built with Streamlit, supporting both movies and TV shows. Uses TF-IDF vectorization and cosine similarity for intelligent recommendations.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ Features

- 🎥 **Content-based recommendations** for movies and TV shows
- 📺 **Dual mode**: Switch between Movies and TV Shows
- 🔍 **Multi-item recommendations**: Get recommendations based on multiple selections
- 📊 **Analytics dashboard**: Genre distributions, ratings by decade, top creators/directors
- 🎨 **Modern UI**: Light/dark theme support, responsive design
- 🖼️ **Poster display**: Beautiful movie/TV show posters from TMDB
- 🔗 **IMDB integration**: Direct links to IMDB pages
- 💾 **Database support**: SQLite database for efficient data storage
- 📈 **Weighted ratings**: Bayesian average for better recommendation quality

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- TMDB API key ([Get one here](https://www.themoviedb.org/settings/api))

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Recommender_old
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.template .env
   # Edit .env and add your TMDB_API_KEY
   ```

5. **Create sample database** (for deployment)
   ```bash
   python scripts/create_sample_database.py
   ```

6. **Run the app**
   ```bash
   streamlit run main.py
   ```

The app will open at `http://localhost:8501`

## 📖 Usage

### Basic Usage

1. **Select Media Type**: Choose Movies or TV Shows from the sidebar
2. **Select Item**: Pick a movie/TV show from the dropdown (supports search)
3. **Get Recommendations**: Click "Get Recommendations" to see similar items
4. **Multi-Mode**: Enable multi-mode to combine recommendations from multiple selections

### Features

- **Search**: Type in the dropdown to filter titles
- **Genre Filter**: Filter recommendations by genre (sidebar)
- **Analytics**: View detailed analytics in the sidebar
- **Posters**: Click posters to open IMDB page

## 🗄️ Database Setup

### For Development (Full Dataset)

1. **Scrape data**:
   ```bash
   python scripts/scrape_movies.py
   python scripts/scrape_tv_shows.py
   ```

2. **Migrate to database**:
   ```bash
   python scripts/migrate_to_db.py
   python scripts/migrate_tv_to_db.py
   ```

### For Deployment (Sample Dataset)

The sample database includes top-rated movies and TV shows for demo purposes:

```bash
python scripts/create_sample_database.py
```

This creates a small database (~1-2 MB) perfect for Streamlit Cloud deployment.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v
```

## 🚢 Deployment

### Streamlit Cloud (Recommended)

1. **Prepare for GitHub**:
   ```bash
   python scripts/cleanup_project.py
   python scripts/create_sample_database.py
   ```

2. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

3. **Deploy to Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Set environment variables:
     - `TMDB_API_KEY`: Your TMDB API key
     - `DATA_PATH`: `data/`
   - Main file: `main.py`
   - Deploy!

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

## 📁 Project Structure

```
Recommender_old/
├── app/                      # Streamlit application
│   ├── main.py              # Main UI and interaction
│   └── components/
│       └── analytics.py     # Analytics dashboard
├── src/                     # Core Python modules
│   ├── config.py           # Configuration management
│   ├── database.py         # Database operations
│   ├── data.py             # Data loading utilities
│   ├── recommend.py        # Recommendation algorithm
│   └── posters.py          # TMDB poster fetching
├── scripts/                 # Utility scripts
│   ├── scrape_movies.py    # Movie data scraping
│   ├── scrape_tv_shows.py  # TV show data scraping
│   ├── migrate_to_db.py    # Database migration
│   ├── create_sample_database.py  # Sample DB for deployment
│   └── cleanup_project.py  # Cleanup before GitHub
├── data/                    # Data files
│   ├── .gitkeep           # Keeps directory in Git
│   ├── movies.db         # SQLite database (gitignored)
│   └── provider_logos/    # Streaming service logos
├── tests/                   # Unit tests
├── .gitignore              # Git ignore rules
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🏗️ Architecture

### Recommendation Algorithm

The system uses **content-based filtering**:

1. **Feature Engineering**: Combines metadata (genres, overview, tagline), credits (actors, directors/creators), and keywords into a text "soup"
2. **Vectorization**: Uses TF-IDF to convert text features into numerical vectors
3. **Similarity Calculation**: Computes cosine similarity between all items
4. **Recommendation**: Returns top-N most similar items (excluding selected items)

### Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python 3.8+
- **Database**: SQLite
- **Data Processing**: Pandas, NumPy
- **ML/Similarity**: scikit-learn (TF-IDF, Cosine Similarity)
- **APIs**: TMDB API (posters, metadata), IMDB (scraping)
- **Visualization**: Plotly

## 📝 Data Processing

The system includes scripts for:
- **Scraping**: Collect movie/TV data from IMDB and TMDB
- **Preprocessing**: Create feature vectors and similarity matrices
- **Migration**: Load data into SQLite database

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- [TMDB](https://www.themoviedb.org/) for movie/TV data and poster images
- [IMDB](https://www.imdb.com/) for movie ratings and metadata
- [Streamlit](https://streamlit.io/) for the web framework

---

**Built with ❤️ using Python, Streamlit, and scikit-learn**
