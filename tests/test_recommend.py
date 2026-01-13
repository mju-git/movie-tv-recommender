"""
Pytest-based minimal tests for the recommendation system.
"""
import sys
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import pandas as pd
import numpy as np
from src.recommend import get_recommendations

# Dummy data for tests
def make_dummy_data():
    data = pd.DataFrame({
        'id': [1, 2, 3],
        'title': ['A', 'B', 'C'],
        'year': [2001, 2002, 2003],
        'vote_average': [7.1, 8.1, 6.9],
        'imdb_id': ['tt001', 'tt002', 'tt003']
    })
    sim = np.array([
        [1.0, 0.9, 0.1],
        [0.9, 1.0, 0.2],
        [0.1, 0.2, 1.0]
    ])
    return data, sim

def test_recommendations_basic():
    df, sim = make_dummy_data()
    rec = get_recommendations('A', cosine_sim_mat=sim, df=df, num_of_rec=2)
    assert not rec.empty
    assert all([title in ['B','C'] for title in rec['title']])

def test_missing_title_raises():
    df, sim = make_dummy_data()
    with pytest.raises(ValueError):
        get_recommendations('Nonexistent', cosine_sim_mat=sim, df=df, num_of_rec=2)

