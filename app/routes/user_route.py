from fastapi import APIRouter, Depends, HTTPException, status
from app.auth.auth import get_current_user
from app.models.models import ListItem, UserData
from app.utils.db_util import get_db
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
        user_average_genre_vector = np.array(user_data['genrePreferences'])
        total_movies_in_list = user_data['moviesInList']
        total_movies_count = len(total_movies_in_list)

        #Generating new user preference vector
        new_user_vector = list(((user_average_genre_vector * total_movies_count) + movie_genre_vector) / (total_movies_count + 1))
        total_movies_in_list.append(data.movie_id)

        #Updating MongoDB
        users_coll.update_one(
            {'_id': ObjectId(data.user_id)},
            {
                '$set': {
                    'genrePreferences': new_user_vector,
                    'moviesInList': total_movies_in_list
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
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error: An Error Occurred.")
