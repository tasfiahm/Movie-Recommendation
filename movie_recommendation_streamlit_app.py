# app.py
import streamlit as st
import pandas as pd
import pickle
import requests
import yaml
import random
from pathlib import Path

# -------------------------------------------------
# 1. CONFIG
# -------------------------------------------------
with open("config.yaml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

DATA_DIR = Path(cfg["data_dir"])

# -------------------------------------------------
# 2. LOAD PICKLES
# -------------------------------------------------
@st.cache_resource
def load_data():
    movies    = pickle.load(open("movies_ta.pkl",    "rb"))
    similarity = pickle.load(open("similarity_ta.pkl","rb"))
    return movies, similarity

movies, similarity = load_data()

# -------------------------------------------------
# 3. RANDOM POSTERS FOR BACKGROUND
# -------------------------------------------------
@st.cache_resource
def get_random_poster_urls(n=6):
    """Pick n random movies and return their TMDB poster URLs (w780)."""
    sample = movies.sample(n, replace=False)
    ids = sample["id"].tolist()
    urls = []
    for mid in ids:
        url = f"https://api.themoviedb.org/3/movie/{mid}?api_key=8265bd1679663a7ea12ac168da84d2e8"
        try:
            data = requests.get(url, timeout=5).json()
            path = data.get("poster_path")
            if path:
                urls.append(f"https://image.tmdb.org/t/p/w780{path}")
        except:
            continue
    # fallback placeholders
    while len(urls) < n:
        urls.append("https://via.placeholder.com/780x1170?text=Poster")
    return urls

random_posters = get_random_poster_urls(6)

# -------------------------------------------------
# 4. NEON RAINBOW TITLE (Animated Gradient + Glow)
# -------------------------------------------------
st.markdown(
    """
    <style>
    .neon-title {
        font-size: 4rem;
        font-weight: 900;
        font-family: 'Arial Black', sans-serif;
        background: linear-gradient(90deg,
            #ff00ff, #00ffff, #ffff00, #ff00ff,
            #00ff00, #ff00ff, #00ffff, #ffff00
        );
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        background-size: 300% 300%;
        animation: neonFlow 4s ease-in-out infinite, glow 1.5s ease-in-out infinite alternate;
        text-align: center;
        margin: 1rem 0;
        text-shadow: 
            0 0 10px rgba(255,0,255,0.8),
            0 0 20px rgba(0,255,255,0.8),
            0 0 30px rgba(255,255,0,0.8);
    }
    @keyframes neonFlow {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes glow {
        from { text-shadow: 
            0 0 10px #ff00ff, 0 0 20px #00ffff, 0 0 30px #ffff00;
        }
        to { text-shadow: 
            0 0 20px #ff00ff, 0 0 30px #00ffff, 0 0 40px #ffff00, 0 0 50px #ff00ff;
        }
    }
    </style>
    <h1 class="neon-title">Movie Recommendation System</h1>
    """,
    unsafe_allow_html=True,
)
st.caption("Powered by TMDB + cosine similarity")

# -------------------------------------------------
# 5. POSTER HELPER (cached)
# -------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8"
    try:
        data = requests.get(url, timeout=5).json()
        path = data.get("poster_path")
        return f"https://image.tmdb.org/t/p/w500{path}" if path else None
    except:
        return None

# -------------------------------------------------
# 6. RECOMMEND
# -------------------------------------------------
def recommend(title, n=5):
    title = title.strip()
    if not title:
        return None, None
    match = movies[movies["title"].str.contains(title, case=False, na=False)]
    if match.empty:
        return None, None
    idx = match.index[0]
    distances = sorted(enumerate(similarity[idx]), reverse=True, key=lambda x: x[1])
    rec_titles, rec_posters = [], []
    for i in distances[1:n+1]:
        rec_titles.append(movies.iloc[i[0]].title)
        poster = fetch_poster(movies.iloc[i[0]].id)
        rec_posters.append(poster or "https://via.placeholder.com/500x750?text=No+Poster")
    return rec_titles, rec_posters

# -------------------------------------------------
# 7. UI
# -------------------------------------------------
search = st.text_input("Enter a movie name (partial OK):", placeholder="e.g. Avatar, Iron Man")
if search:
    with st.spinner("Searching…"):
        rec_titles, rec_posters = recommend(search)
    if rec_titles:
        st.success(f"**Top 5 similar to:** *{search}*")
        cols = st.columns(5)
        for col, title, poster in zip(cols, rec_titles, rec_posters):
            with col:
                st.image(poster, use_container_width=True)
                st.caption(title)
    else:
        st.error("No match – try another spelling or partial name.")