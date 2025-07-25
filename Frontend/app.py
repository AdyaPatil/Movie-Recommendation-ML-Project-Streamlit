import streamlit as st
import requests
import pickle
import boto3
import io
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# AWS and TMDb credentials
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
MOVIE_PICKLE_KEY = os.getenv("MOVIE_PICKLE_KEY")
SIMILARITY_PICKLE_KEY = os.getenv("SIMILARITY_PICKLE_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# Setup boto3 S3 client
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

# Load pickled objects from S3
def load_pickle_from_s3(bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    return pickle.load(io.BytesIO(response["Body"].read()))

# Load files
movies = load_pickle_from_s3(S3_BUCKET_NAME, MOVIE_PICKLE_KEY)
similarity = load_pickle_from_s3(S3_BUCKET_NAME, SIMILARITY_PICKLE_KEY)

# TMDb Poster Fetch
def fetch_poster(movie_id):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get("poster_path")
        return f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
    except requests.exceptions.RequestException:
        return ""

# Recommend Logic
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []

    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].movie_id
        title = movies.iloc[i[0]].title
        recommended_movie_names.append(title)
        poster = fetch_poster(movie_id)
        recommended_movie_posters.append(poster)

    return recommended_movie_names, recommended_movie_posters

# UI
st.header("🎬 Movie Recommender System")

movie_list = movies['title'].values
selected_movie = st.selectbox("Type or select a movie from the dropdown", movie_list)

if st.button("Show Recommendation"):
    recommended_movie_names, recommended_movie_posters = recommend(selected_movie)

    if recommended_movie_names:
        cols = st.columns(5)
        for i in range(5):
            with cols[i]:
                st.text(recommended_movie_names[i])
                st.image(recommended_movie_posters[i])
