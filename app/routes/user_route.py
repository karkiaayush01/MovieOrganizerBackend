from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from app.auth.auth import get_current_user
from app.models.models import *;
from app.utils.db_util import get_db
from app.core.movies import get_genre_vectors
from bson import ObjectId
import numpy as np
from datetime import datetime, timezone
from app.core.movies import get_all_genres
from app.core.movies import generate_recommendation_background

_SHOW_NAME = 'user'

router = APIRouter(
    prefix= f'/{_SHOW_NAME}',
    tags = [_SHOW_NAME],
    responses={404: {'description': 'Not found'}}
)

@router.post('/add_movie_to_list')
def add_movie_to_list(data: ListItem, background_tasks: BackgroundTasks, user_info = Depends(get_current_user)):
    try:
        #Getting database and required collections
        db = get_db()
        users_coll = db['users']
        movies_coll = db['movies']
        watch_list_coll = db['watchlist']

        #Finding Movie and User's data
        movie_data = movies_coll.find_one({'id': data.movie_id})
        user_data = users_coll.find_one({'firebase_user_id': data.firebase_user_id})

        if movie_data is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Error: Couldn't find requested movie data.")

        if user_data is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Error: Failed to retrieve user data.")

        #Calcuations and logic
        movie_genre_vector = np.array(movie_data['genre_vector'])
        total_movies_in_list = list(user_data.get('moviesInList', []))
        initial_preference_vector = np.array(user_data.get("initialPreferenceVector", get_genre_vectors([])))
        user_average_movies_vector = np.array(user_data.get('moviePreferenceVector', get_genre_vectors([])))
        movies_in_current_preference = list(user_data.get('moviesInCurrentPreference', []))
        movies_count_in_current_preference = user_data.get('moviesCountInCurrentPreference', 0)

        #Generating new average movies vector and new user preference vector
        new_movie_vector = list(((user_average_movies_vector * movies_count_in_current_preference) + movie_genre_vector)/ (movies_count_in_current_preference + 1))
        new_user_vector = list(((initial_preference_vector + user_average_movies_vector * movies_count_in_current_preference) + movie_genre_vector) / (movies_count_in_current_preference + 2))
        total_movies_in_list.append(data.movie_id)
        movies_in_current_preference.append(data.movie_id)
        movies_count_in_current_preference += 1

        #Updating MongoDB
        users_coll.update_one(
            {'firebase_user_id': data.firebase_user_id},
            {
                '$set': {
                    'moviePreferenceVector': new_movie_vector,
                    'genrePreferences': new_user_vector,
                    'moviesInList': total_movies_in_list,
                    'moviesInCurrentPreference': movies_in_current_preference,
                    'moviesCountInCurrentPreference': movies_count_in_current_preference
                }
            }
        )

        watch_list_coll.insert_one(
            {
                'firebase_user_id': data.firebase_user_id,
                'movie_id': data.movie_id,
                'type': data.status,
                'startDate': data.startDate.isoformat() if data.startDate else None,
                'endDate': data.endDate.isoformat() if data.endDate else None,
                'lastUpdated': datetime.now(timezone.utc)
            }
        )

        print("Calling generate recommendation in background")
        background_tasks.add_task(generate_recommendation_background, data.firebase_user_id)

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
            'firebase_user_id': data.firebase_user_id,
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
                        'firebase_user_id': data.firebase_user_id,
                        'movie_id': data.movie_id,
                        'type': data.status,
                        'startDate': data.startDate.isoformat(),
                        'endDate': data.endDate.isoformat(),
                        'lastUpdated': datetime.now(timezone.utc) 
                    }
                }
            )

        return {"message": "Movie updated in watchlist successfully"}
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error: An Error Occurred.")

@router.delete('/remove_movie_from_list')
def remove_movie_from_list(data: RemoveFromWatchListRequest, user_info = Depends(get_current_user)):
    try:
        #Getting db and its collections
        db = get_db()
        users_coll = db['users']
        movies_coll = db['movies']
        watch_list_coll = db['watchlist']

        #Getting existing item from watchlist collection
        existing_entry = watch_list_coll.find_one({
            'firebase_user_id': data.firebase_user_id,
            'movie_id': data.movie_id
        })

        if existing_entry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Error: Couldn't find entry in watchlist ")

        #Finding the user and movie data
        user_data = users_coll.find_one({'firebase_user_id': data.firebase_user_id})
        movie_data = movies_coll.find_one({'id': data.movie_id})
        
        #Calcuations and logic
        movie_genre_vector = np.array(movie_data['genre_vector'])
        total_movies_in_list = list(user_data.get('moviesInList', []))
        initial_preference_vector = np.array(user_data.get("initialPreferenceVector", get_genre_vectors([])))
        user_average_movies_vector = np.array(user_data.get('moviePreferenceVector', get_genre_vectors([])))
        movies_in_current_preference = list(user_data.get('moviesInCurrentPreference', []))
        movies_count_in_current_preference = user_data.get('moviesCountInCurrentPreference', 0)

        #Generating new average movies vector and new user preference vector
        if data.movie_id in movies_in_current_preference:
            if movies_count_in_current_preference > 1:
                new_count = movies_count_in_current_preference - 1
                new_movie_vector = ((user_average_movies_vector * movies_count_in_current_preference) - movie_genre_vector)/ new_count
                new_user_vector = list((initial_preference_vector + new_movie_vector * new_count) / (new_count + 1))
                new_movie_vector = list(new_movie_vector)
            else:
                print("Entered else")
                new_movie_vector = get_genre_vectors([])
                new_user_vector = initial_preference_vector.tolist()
            
            movies_in_current_preference.remove(data.movie_id)
            movies_count_in_current_preference -= 1
        
        if data.movie_id in total_movies_in_list:
            total_movies_in_list.remove(data.movie_id)

        #Updating MongoDB
        users_coll.update_one(
            {'firebase_user_id': data.firebase_user_id},
            {
                '$set': {
                    'moviePreferenceVector': new_movie_vector,
                    'genrePreferences': new_user_vector,
                    'moviesInList': total_movies_in_list,
                    'moviesInCurrentPreference': movies_in_current_preference,
                    'moviesCountInCurrentPreference': movies_count_in_current_preference
                }
            }
        )

        #removing from watch list
        watch_list_coll.delete_one(
            {
                '_id': existing_entry['_id']
            }
        )

        return {"message": "Movie removed from list successfully"}
    except HTTPException:
        raise    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: An error occurred while removing movie: {str(e)}")
    
@router.get('/get_watchlist/{firebase_user_id}')
def get_watchlist(firebase_user_id: str, user_info = Depends(get_current_user)):
    try:
        #Getting db and collections
        db = get_db()
        watchlist_coll = db['watchlist']
        movies_coll = db['movies']
        genres = get_all_genres()

        watchlist_data = list(watchlist_coll.find(
            {'firebase_user_id': firebase_user_id}
        ).sort('lastUpdated', -1))
        for result in watchlist_data:
            result['_id'] = str(result['_id'])
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
                result['movie'] = movie_data
            
        return {'data': watchlist_data}
    except HTTPException:
        raise
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: An error occurred {str(e)}")
    
@router.get("/find_movie_in_watchlist/{firebase_user_id}/{movie_id}")
def find_movie_in_watchlist(firebase_user_id: str, movie_id: int, user_info = Depends(get_current_user)):
    try:
        db = get_db()
        watchlist_coll = db['watchlist']

        item = watchlist_coll.find_one({
            'firebase_user_id': firebase_user_id,
            'movie_id': movie_id
        })

        if item is not None:
            item['_id'] = str(item['_id'])

        return {'data': item}
    except HTTPException:
        raise
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: An error occurred {str(e)}")
    
    
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
            'moviesInList': [],
            'createdAt': datetime.now(timezone.utc)
        })

        return {"message": "Added user data successfully"}
    except HTTPException:
        raise
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
                    "initialPreferenceVector": updated_preference,
                    "moviePreferenceVector": get_genre_vectors([]),  #no movies while updating preference
                    "genrePreferences": updated_preference,
                    "moviesCountInCurrentPreference": movies_count_in_current_preference,
                    "moviesInCurrentPreference": []
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
    
@router.get('/get_user_statistics/{firebase_user_id}')
def get_user_statistics(firebase_user_id: str, user_info=Depends(get_current_user)):
    try:
        db = get_db()
        watchlist_coll = db['watchlist']
        movies_coll = db['movies']
        watchedRuntime = 0

        watchlist_data_completed = list(watchlist_coll.find(
            {
                'firebase_user_id': firebase_user_id,
                'type': 'Completed'
            }
        ))

        watchlist_count_completed = len(watchlist_data_completed)

        watchlist_count_planned = watchlist_coll.count_documents(
            {
                'firebase_user_id': firebase_user_id,
                'type': 'Plan To Watch'
            }
        )

        watchlist_count_watching = watchlist_coll.count_documents(
            {
                'firebase_user_id': firebase_user_id,
                'type': 'Watching'
            }
        )

        for item in watchlist_data_completed:
            movie_id = item['movie_id']
            movie_data = movies_coll.find_one({'id': movie_id})
            watchedRuntime += movie_data['runtime']
        
        return {'data': {
            'minutes_watched': watchedRuntime,
            'completed_count': watchlist_count_completed,
            'planned_count': watchlist_count_planned,
            'watching_count': watchlist_count_watching
        }}
    except HTTPException:
        raise
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {str(e)}")

    

    

    


