<<<<<<< HEAD
# Movie-Recommendation
Python Base Movie Recommendation System
# Movie-Recommendation

A **content-based movie recommender** (TMDB 5000) with:

* **Streamlit** UI + TMDB posters
* **CountVectorizer + cosine similarity**
* **YAML config** – no hard-coded paths
* **Pickled model** – instant load

---

## Live Demo (after you deploy)

https://movie-recommendation-ngepxaulnwj9rgwrsrah7c.streamlit.app/

*(Replace `YOUR-USERNAME` after deployment)*

---

## How to Run Locally

```bash
git clone https://github.com/tasfiahm/Movie-Recommendation.git
cd Movie-Recommendation

# Install
pip install -r requirements.txt

# 1. Generate model (downloads CSVs from Kaggle if missing)
python save_data.py

# 2. Run app
streamlit run movie_recommendation_streamlit_app.py
=======

