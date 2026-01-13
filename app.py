"""
Minimal test file to verify Streamlit Cloud infrastructure.
If this works, we know the problem is in main.py.
"""
import streamlit as st

st.set_page_config(page_title="Movie Recommender", layout="wide")

st.title("Movie Recommender")

st.write("✅ If you see this, Streamlit Cloud is working!")
