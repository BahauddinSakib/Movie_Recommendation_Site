
from flask import Flask, request, jsonify, render_template
import pickle
import pandas as pd
import requests

app = Flask(__name__)

# Load pre-trained models
movies = pickle.load(open("movies_list.pkl", 'rb'))
similarity = pickle.load(open("similarity.pkl", 'rb'))


# TMDB API Key
API_KEY = "c7ec19ffdd3279641fb606d19ceb9bb1"


def fetch_movie_details(movie_id):
    #Fetch movie poster and rating from TMDB.
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}&language=en-US"
    data = requests.get(url).json()

    poster_path = data.get('poster_path', '')
    rating = data.get('vote_average', 'N/A')  # Get rating, default to 'N/A' if not found

    return {
        'poster': f"https://image.tmdb.org/t/p/w500/{poster_path}" if poster_path else "",
        'rating': rating
    }


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/suggest', methods=['GET'])
def suggest():
    query = request.args.get('query', '').strip().lower()
    if not query:
        return jsonify({'suggestions': []})

    # Filter movies whose title starts with the query
    suggestions = movies[movies['title'].str.lower().str.startswith(query)]['title'].tolist()

    return jsonify({'suggestions': suggestions[:10]})  # Limit suggestions to 10


@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    movie_name = data.get('movie', '').strip()

    if not movie_name:
        return jsonify({'message': 'Movie name is required'}), 400

    try:
        index = movies[movies['title'] == movie_name].index[0]
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])

        recommend_movies = []
        recommend_posters = []
        recommend_ratings = []

        for i in distances[1:7]:  # Get top 6 recommended movies
            movie_id = movies.iloc[i[0]].id
            movie_details = fetch_movie_details(movie_id)
            recommend_movies.append(movies.iloc[i[0]].title)
            recommend_posters.append(movie_details['poster'])
            recommend_ratings.append(movie_details['rating'])

        return jsonify({
            'movies': recommend_movies,
            'posters': recommend_posters,
            'ratings': recommend_ratings
        })

    except IndexError:
        return jsonify({'message': 'Movie not found'}), 404


if __name__ == '__main__':
    print(app.url_map)  # To check registered routes
    app.run(debug=True)  #auto run when code changes


