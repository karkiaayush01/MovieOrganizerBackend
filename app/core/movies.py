from app.utils.db_util import get_db
from app.core.recommendation import generate_movie_recommendations

genre_cache = None

def get_genre_vectors(movieGenres:list):
    """
        Creates genre vectors from a particular movie's genre array. 
        A genre array is a list showing which genre_ids does a movie belong to e.g. [113, 28, 44]. 
    """
    global genre_cache
    vector = []

    if genre_cache is None:
        db = get_db()
        genres_coll = db['genres']
        genre_cache = list(genres_coll.find().sort('index', 1))

    for genre in genre_cache:
        if genre['id'] in movieGenres:
            vector.append(1)
        else:
            vector.append(0)

    return vector

def get_all_genres():
    """
        Returns all the genres from the genre cache or the database. 
    """
    global genre_cache

    if genre_cache:
        return genre_cache
    else: 
        db = get_db()
        genres_coll = db['genres']
        genre_cache = list(genres_coll.find().sort('index', 1))
        return genre_cache
    
def generate_recommendation_background(firebase_user_id: str):
    try:
        #Getting DB
        db = get_db()
        users_coll = db['users']
        movies_coll = db['movies']
        
        #Getting user data
        user_data = users_coll.find_one({'firebase_user_id': firebase_user_id})
        user_vector = user_data['genrePreferences']

        users_movie_list = user_data.get('moviesInList', [])
        
        #Getting Recommendation
        top_recommendations = generate_movie_recommendations(user_vector, users_movie_list)
        top_recommendations.sort(key=lambda x: x['rank'])

        #Getting genre data
        genres = get_all_genres()
        movies = []

        for result in top_recommendations:
            movie_id = result['movie_id']
            movie_data = movies_coll.find_one({'id': movie_id})

            if movie_data:
                movie_data.pop('_id', None)
                movie_data.pop('genre_vector', None)
                movie_genres = []
                for genre_id in movie_data['genre_ids']:
                    genre_obj = next((g for g in genres if g['id'] == genre_id), None)
                    if genre_obj:
                        movie_genres.append(genre_obj['name'])
                movie_data['genreNames'] = movie_genres
                movies.append(movie_data)
    
        users_coll.update_one(
            {'firebase_user_id': firebase_user_id},
            {
                "$set": {
                    "cachedRecommendedMovies": movies,
                    "cachedForVector": user_vector
                }
            }
        )

        print("Successfully updated recommendation in background")
    except Exception as e:
        print(str(e))
        raise Exception("Error: An error occurred: {str(e)}") 
