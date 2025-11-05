# movie_recommendation_streamlit_app.py
import streamlit as st
import pandas as pd
import pickle
import requests
import base64
from pathlib import Path



BACKGROUND_IMAGE = "background_banner.jpg"   # ← Must be in same folder

# Fetching Variable from config.yaml
try:
    import yaml
    with open("config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    DATA_DIR = Path(cfg["data_dir"])
    DEVELOPER_NAME = Path(cfg["developer_name"])
    BACKGROUND_IMAGE = Path(cfg["background_img"])  # ← Must be in same folder background_img
except (FileNotFoundError, ImportError, KeyError):
    DATA_DIR = Path(".")  # Default: current folder

# ========================================
# 2. DATA LOADING
# ========================================
@st.cache_resource
def load_data():
    movies = pickle.load(open(DATA_DIR / "movies_ta.pkl", "rb"))
    similarity = pickle.load(open(DATA_DIR / "similarity_ta.pkl", "rb"))
    return movies, similarity

movies, similarity = load_data()

# ========================================
# 3. STYLES & BACKGROUND
# ========================================
def apply_theme_and_background():
    img_path = Path(BACKGROUND_IMAGE)
    if not img_path.exists():
        st.error(f"Background image `{BACKGROUND_IMAGE}` NOT FOUND in current folder!")
        bg_css = "background: #111 !important;"
    else:
        ext = img_path.suffix.lower()
        mime = "image/jpeg" if ext in {".jpg", ".jpeg"} else "image/png"
        b64 = base64.b64encode(img_path.read_bytes()).decode()
        bg_css = f"background: url('data:{mime};base64,{b64}') center/cover fixed !important;"

    st.markdown(
        f"""
        <style>
        /* Full app background */
        .stApp {{
            {bg_css}
        }}
        .stApp::before {{
            content: "";
            position: absolute;
            inset: 0;
            background: rgba(0,0,0,0.48);
            z-index: 0;
        }}
        .stApp > * {{ position: relative; z-index: 1; }}

        /* Light text */
        .text-light {{ color: #f0f0f0 !important; }}
        .text-caption {{ color: #e0e0e0 !important; font-style: italic; }}

        /* Search input */
        .input-search input {{
            background-color: rgba(255,255,255,0.12) !important;
            color: #ffffff !important;
            border: 1.5px solid rgba(255,255,255,0.3) !important;
            border-radius: 8px !important;
            padding: 0.6rem 1rem !important;
            font-size: 1.1rem !important;
        }}
        .input-search input::placeholder {{ color: rgba(255,255,255,0.7) !important; }}

        /* Success banner */
        .success-banner {{
            background: linear-gradient(90deg, #1a5f1a, #2e8b2e);
            color: white;
            padding: 0.8rem 1.2rem;
            border-radius: 8px;
            font-weight: 600;
            font-size: 1.15rem;
            text-align: center;
            margin: 1.2rem 0;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        }}

        /* Poster caption */
        .poster-title {{
            color: #f0f0f0;
            text-align: center;
            margin-top: 10px;
            font-size: 0.95rem;
            font-weight: 500;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        }}

        /* Developer credit */
        .dev-credit {{
            text-align: center;
            margin-top: 3rem;
            padding: 1rem;
            color: #a0a0a0;
            font-size: 0.9rem;
            font-family: 'Courier New', monospace;
            text-shadow: 0 1px 2px rgba(0,0,0,0.7);
            opacity: 0.8;
        }}
        .dev-credit strong {{ color: #00ffff; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

apply_theme_and_background()

# ========================================
# 4. NEON TITLE
# ========================================
def render_title():
    st.markdown(
        """
        <style>
        .neon-title {
            font-size: 5rem; font-weight: 900;
            font-family: 'Arial Black', sans-serif;
            background: linear-gradient(90deg, #ff00ff, #00ffff, #ffff00, #ff00ff, #00ff00, #ff00ff, #00ffff, #ffff00);
            -webkit-background-clip: text; background-clip: text; color: transparent;
            background-size: 300% 300%;
            animation: neonFlow 4s ease-in-out infinite, glow 1.5s ease-in-out infinite alternate;
            text-align: center; margin: 1rem 0;
            text-shadow: 0 0 10px rgba(255,0,255,0.8), 0 0 20px rgba(0,255,255,0.8), 0 0 30px rgba(255,255,0,0.8);
        }
        @keyframes neonFlow { 0%,100%{background-position:0% 50%} 50%{background-position:100% 50%} }
        @keyframes glow { 
            from { text-shadow: 0 0 10px #ff00ff, 0 0 20px #00ffff, 0 0 30px #ffff00; }
            to   { text-shadow: 0 0 20px #ff00ff, 0 0 30px #00ffff, 0 0 40px #ffff00, 0 0 50px #ff00ff; }
        }
        </style>
        <h1 class="neon-title">Movie Recommendation System</h1>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<p class="text-caption" style="text-align:center;margin-top:-10px;">Powered by TMDB + cosine similarity</p>', unsafe_allow_html=True)

render_title()

# ========================================
# 5. POSTER FETCHER
# ========================================
@st.cache_data(ttl=3600)
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=8265bd1679663a7ea12ac168da84d2e8" # as this is public demo key so I have not placed in .streamlit/secrets.toml
    try:
        data = requests.get(url, timeout=5).json()
        path = data.get("poster_path")
        return f"https://image.tmdb.org/t/p/w500{path}" if path else None
    except:
        return None

# ========================================
# 6. RECOMMENDATION ENGINE
# ========================================
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

# ========================================
# 7. UI COMPONENTS
# ========================================
def render_search_bar():
    st.markdown("<div class='input-search'>", unsafe_allow_html=True)
    search = st.text_input(
        "Enter a movie name (partial OK):",
        placeholder="e.g. Rambo, Spider Man",
        key="search",
        label_visibility="collapsed"
    )
    st.markdown("</div>", unsafe_allow_html=True)
    return search

def render_results(search):
    if not search:
        return
    with st.spinner("Searching…"):
        titles, posters = recommend(search)
    if titles:
        st.markdown(
            f'<div class="success-banner">Top 5 similar to: <em>{search}</em></div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(5)
        for col, title, poster in zip(cols, titles, posters):
            with col:
                st.image(poster, use_container_width=True)
                st.markdown(f'<p class="poster-title">{title}</p>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="background:#8B0000;color:white;padding:0.8rem;border-radius:8px;text-align:center;font-weight:500;">No match – try another spelling.</div>',
            unsafe_allow_html=True,
        )

# ========================================
# 8. DEVELOPER CREDIT (PARAMETERIZED)
# ========================================
def render_developer_credit():
    st.markdown(
        f"""
        <div class="dev-credit">
            Developed by <strong>{DEVELOPER_NAME}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ========================================
# 9. MAIN APP
# ========================================
def main():
    search = render_search_bar()
    render_results(search)
    render_developer_credit()  # ← Always at the bottom

if __name__ == "__main__":
    main()