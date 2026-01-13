"""
Recommendation logic for the Movie Recommender System.

This module implements content-based filtering using cosine similarity
to recommend movies similar to a given input movie.
"""
import pandas as pd
from typing import Any
import numpy as np


def get_recommendations(
    title: str, 
    cosine_sim_mat: np.ndarray, 
    df: pd.DataFrame, 
    num_of_rec: int = 16
) -> pd.DataFrame:
    """
    Get movie recommendations based on cosine similarity.
    
    Uses a pre-computed cosine similarity matrix to find the most similar movies
    to the input title. Returns top-N recommendations excluding the input movie itself.
    
    Args:
        title (str): Exact movie title to find recommendations for
        cosine_sim_mat (np.ndarray): Pre-computed cosine similarity matrix 
                                     (shape: n_movies x n_movies)
        df (pd.DataFrame): Movie dataset with 'title' column and other metadata
        num_of_rec (int): Number of recommendations to return (default: 16)
        
    Returns:
        pd.DataFrame: Recommended movies with columns:
            - All original columns from df (title, year, vote_average, etc.)
            - similarity_score: Cosine similarity score (0-1)
            
    Raises:
        ValueError: If the movie title is not found in the dataset
        
    Example:
        >>> movies_df = load_movies()
        >>> similarity = load_similarity()
        >>> recs = get_recommendations("The Dark Knight", similarity, movies_df, num_of_rec=5)
        >>> print(recs[['title', 'similarity_score']])
    """
    combined = df.reset_index()
    indices = pd.Series(combined.index, index=combined['title'])
    if title not in indices:
        raise ValueError(f"Title '{title}' not found in database.")
    idx = indices[title]
    sim_scores = list(enumerate(cosine_sim_mat[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:num_of_rec+1]  # exclude the first (itself)
    movie_indices = [i[0] for i in sim_scores]
    recs = combined.iloc[movie_indices].copy()
    recs['similarity_score'] = [i[1] for i in sim_scores]
    return recs

