from fastapi import APIRouter, Depends
from app.utils.db_util import get_db
from app.core.recommendation import generate_movie_recommendations
from app.auth.auth import get_current_user
from bson import ObjectId

_SHOW_NAME = 'movies'

router = APIRouter(
    prefix=f'/{_SHOW_NAME}',
    tags = [_SHOW_NAME],
    responses={404: {'description': 'Not found'}}
)

@router.get('/get_recommendation/{user_id}')
def generate_recommendation(user_id: str, user_data=Depends(get_current_user)):
    #Getting DB
    db = get_db()
    users_coll = db['users']

    #Getting user data
    user_data = users_coll.find_one({'_id': ObjectId(user_id)})
    user_vector = user_data['genrePreferences']
    users_movie_list = user_data['moviesInList']

    
    #Getting Recommendation
    top_recommendations = generate_movie_recommendations(user_vector, users_movie_list)

    return {'data': top_recommendations}

@router.get('/get_popular_titles')
def get_popular_titles(user_data=Depends(get_current_user)):
    try:
        #Getting Popular Movies From TMDB
        return
    except:
        return
    


if __name__ == "__main__":
    generate_recommendation("689702e482935a10904eb4d5")