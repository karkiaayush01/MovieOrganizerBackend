from sklearn.metrics.pairwise import cosine_similarity
from app.utils.db_util import get_db
import numpy as np

def generate_movie_recommendations(user_vector, exclude=[]):
    try:
        #converting user_vector array into numpy array
        user_vec = np.array(user_vector).reshape(1, -1)

        #getting db and appropirate collection
        db = get_db()
        movie_coll = db['movies']

        # Find all movies excluding those with ids in `exclude`
        all_movies_query = movie_coll.find(
            {"id": {"$nin": exclude}}
        )
        all_movies = list(all_movies_query)

        similarity = []

        count = 1
        for movie in all_movies:
            print(f"movie: {movie['id']}")
            count+=1
            movie_vec = np.array(movie['genre_vector']).reshape(1, -1)
            similarity_index = cosine_similarity(user_vec, movie_vec)[0][0]
            similarity.append({"movie_id": movie['id'], "similarity_index": similarity_index})

        # Sort in descending order (most similar first)
        similarity.sort(key=lambda x: x['similarity_index'], reverse=True)

        return similarity[:30]
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        

    
