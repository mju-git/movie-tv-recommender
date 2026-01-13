"""
Data loading utilities for the Movie Recommender System.

This module provides functions to load preprocessed movie data and similarity matrices
from pickle files stored in the data directory.
"""
import pickle
import pandas as pd
from typing import Any
from pathlib import Path

from src.config import Config


def load_pickle(path: str) -> Any:
    """
    Load a Python object from a pickle file.
    
    Args:
        path (str): Path to the pickle file
        
    Returns:
        Any: The unpickled Python object
        
    Raises:
        FileNotFoundError: If the pickle file doesn't exist
        pickle.UnpicklingError: If the file cannot be unpickled
    """
    with open(path, 'rb') as f:
        return pickle.load(f)


def load_movies() -> pd.DataFrame:
    """
    Load the processed movie dataset from pickle file.
    
    The dataset contains movie metadata including:
    - id, imdb_id, title, year, vote_average
    - genres, overview, tagline
    - actors, director, keywords
    - soup (combined feature text)
    
    Returns:
        pd.DataFrame: Movie dataset with all processed features
        
    Raises:
        FileNotFoundError: If movies.pkl doesn't exist in data directory
    """
    data_path = Path(Config.DATA_PATH) / 'movies.pkl'
    return load_pickle(str(data_path))


def load_similarity() -> Any:
    """
    Load the pre-computed cosine similarity matrix from pickle file.
    
    The similarity matrix is a 2D numpy array where each cell (i, j) represents
    the cosine similarity between movie i and movie j.
    
    Returns:
        np.ndarray: 2D similarity matrix (shape: n_movies x n_movies)
        
    Raises:
        FileNotFoundError: If similarity.pkl doesn't exist in data directory
    """
    data_path = Path(Config.DATA_PATH) / 'similarity.pkl'
    return load_pickle(str(data_path))

