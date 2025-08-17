from fastapi import APIRouter, Depends, HTTPException, status
from app.auth.auth import get_current_user
from app.models.models import *;
from app.utils.db_util import get_db
from app.core.movies import get_genre_vectors
from bson import ObjectId
import numpy as np
from datetime import datetime, timezone

_SHOW_NAME = 'user'

router = APIRouter(
    prefix= f'/{_SHOW_NAME}',
    tags = [_SHOW_NAME],
    responses={404: {'description': 'Not found'}}
)

@router.post('/add_movie_to_list')
def add_movie_to_list(data: ListItem, user_info = Depends(get_current_user)):
    try:
        #Getting database and required collections
        db = get_db()
        users_coll = db['users']
        movies_coll = db['movies']
        watch_list_coll = db['watchlist']

        #Finding Movie and User's data
        movie_data = movies_coll.find_one({'id': data.movie_id})
        user_data = users_coll.find_one({'_id': ObjectId(data.user_id)})

        if movie_data is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Error: Couldn't find requested movie data.")

        if user_data is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Error: Failed to retrieve user data.")

        #Calcuations and logic
        movie_genre_vector = np.array(movie_data['genre_vector'])
        user_average_genre_vector = np.array(user_data.get('genrePreferences'), get_genre_vectors([]))
        total_movies_in_list = user_data.get('moviesInList', [])
        movies_count_in_current_preference = user_data.get('moviesCountInCurrentPreference', 0)
        total_movies_count = len(total_movies_in_list)

        #Generating new user preference vector
        new_user_vector = list(((user_average_genre_vector * total_movies_count) + movie_genre_vector) / (total_movies_count + 1))
        total_movies_in_list.append(data.movie_id)
        movies_count_in_current_preference += 1

        #Updating MongoDB
        users_coll.update_one(
            {'_id': ObjectId(data.user_id)},
            {
                '$set': {
                    'genrePreferences': new_user_vector,
                    'moviesInList': total_movies_in_list,
                    'moviesCountInCurrentPreference': movies_count_in_current_preference
                }
            }
        )

        watch_list_coll.insert_one(
            {
                'user_id': data.user_id,
                'movie_id': data.movie_id,
                'type': data.status,
                'startDate': data.startDate,
                'endDate': data.endDate,
                'lastUpdated': datetime.now(timezone.utc)
            }
        )

        return {"message": "Movie added to list successfully"}

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error: An Error Occurred.")
    
@router.put('/update_movie_in_list')
def update_movie_in_list(data: ListItem, user_info = Depends(get_current_user)):
    try:
        #Getting database and required collections
        db = get_db()
        watch_list_coll = db['watchlist']

        #Getting existing item from watchlist collection
        existing_entry = watch_list_coll.find_one({
            'user_id': data.user_id,
            'movie_id': data.movie_id
        })

        if existing_entry is None:
            #Create a new entry if existing entry not found
            return add_movie_to_list(data, user_info)
        else:
            existing_entry_id = existing_entry['_id']
            watch_list_coll.update_one(
                {'_id': existing_entry_id},
                {
                    '$set': {
                        'user_id': data.user_id,
                        'movie_id': data.movie_id,
                        'type': data.status,
                        'startDate': data.startDate,
                        'endDate': data.endDate,
                        'lastUpdated': datetime.now(timezone.utc) 
                    }
                }
            )
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error: An Error Occurred.")
    
@router.post('/add_user_data')
def add_user_data(data: UserData):
    try:
            #Getting the database
        db = get_db()
        users_coll = db['users']

        #Checking if user already exists
        if users_coll.find_one({'firebase_user_id': data.firebase_user_id}):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Error: User with provided firebaseID already exists")
        
        users_coll.insert_one({
            'firebase_user_id': data.firebase_user_id,
            'name': data.name,
            'email': data.email,
            'user_name': data.user_name,
            'sign_up_method': data.sign_up_method,
            'createdAt': datetime.now(timezone.utc)
        })

        return {"message": "Added user data successfully"}
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {str(e)}")
    
@router.post('/update_user_preferences')
def update_user_preferences(data: PreferenceRequest, user_info=Depends(get_current_user)):
    try:
        db = get_db()
        users_coll = db['users'] 

        user = users_coll.find_one({
            "firebase_user_id": data.firebase_user_id
        })

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        genre_ids = [genre.genre_id for genre in data.preferences]
        updated_preference = get_genre_vectors(genre_ids)
        movies_count_in_current_preference = 0

        #Override the previoud user preference with a fresh start
        users_coll.update_one(
            {"firebase_user_id": data.firebase_user_id}, 
            {
                "$set": {
                    "initialPreference": genre_ids,
                    "genrePreferences": updated_preference,
                    "moviesCountInCurrentPreference": movies_count_in_current_preference
                }
            }
        )

        return {"message": "Success: Preference Updated Successfully"}
    except HTTPException:
        # Reraise HTTPExceptions
        raise
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {str(e)}")
    
@router.get('/get_user_preferences/{firebase_user_id}')
def get_user_preferences(firebase_user_id:str, user_info=Depends(get_current_user)):
    try:
        preferences = []
        db = get_db()
        users_coll = db['users']
        genres_coll = db['genres']

        user = users_coll.find_one({
            'firebase_user_id': firebase_user_id
        })

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        else:
            preference_ids = user.get('initialPreference', [])
            for id in preference_ids:
                genre = genres_coll.find_one({'id': id})
                preferences.append({'id': id, 'name': genre['name']})
        
        return {"preferences": preferences}
    except HTTPException:
        raise
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {str(e)}")
