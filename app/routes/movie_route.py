from fastapi import APIRouter, Depends, HTTPException, status
from app.utils.db_util import get_db
from app.core.recommendation import generate_movie_recommendations
from app.core.movies import get_all_genres
from app.auth.auth import get_current_user
from bson import ObjectId
import requests
import os

_SHOW_NAME = 'movies'

router = APIRouter(
    prefix=f'/{_SHOW_NAME}',
    tags = [_SHOW_NAME],
    responses={404: {'description': 'Not found'}}
)

@router.get('/get_recommendation/{firebase_user_id}')
def generate_recommendation(firebase_user_id: str, user_data=Depends(get_current_user)):
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
                print(movie_data)
                movies.append(movie_data)

        return {'data': movies}
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: An error occurred: {str(e)}")                                    

@router.get('/get_popular_titles')
def get_popular_titles(user_data=Depends(get_current_user)):
    try:
        db = get_db()
        movies_coll = db['movies']
        movies = []

        #Get genres from genres.json instead of querying database

        #Get popular movies from TMDB 
        API_AUTH_KEY = os.environ.get('TMDB_API_KEY', None)
        if API_AUTH_KEY is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Error: API Key not found")
        
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {API_AUTH_KEY}"
        }

        url = f"https://api.themoviedb.org/3/discover/movie?include_adult=false&include_video=true&language=en-US&page=1&sort_by=popularity.desc"

        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                genres = get_all_genres()
                for result in data['results']:
                    movie_id = result['id']
                    movie_data = movies_coll.find_one({'id': movie_id})

                    if movie_data:
                        movie_data.pop('_id', None)
                        movie_data.pop('genre_vector', None)
                        movie_genres = []
                        for genre_id in movie_data['genre_ids']:
                            genre_obj = next((g for g in genres if g['id'] == genre_id), None)
                            if genre_obj:
                                movie_genres.append(genre_obj['name'])
                        movie_data['genres'] = movie_genres
                        movies.append(movie_data)
                        
                return {"data": movies}
            else:
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail='Error: Failed to get data from TMDB')
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error: An error occurred {str(e)}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: An error occurred {str(e)}")
    except Exception as e:
        print(f"Error: An error occurred {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: An error occurred {str(e)}")

if __name__ == "__main__":
    generate_recommendation("R25XrnV6qwcepxjqYizeZNEchiL2")