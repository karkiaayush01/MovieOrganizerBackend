import requests
import os
from app.utils.db_util import get_db

def get_extra_movie_details():
    db = get_db()
    movies_coll = db['movies']

    movies = list(movies_coll.find().sort('_id', -1))

    API_AUTH_KEY = os.environ.get('TMDB_API_KEY', None)

    if API_AUTH_KEY is None:
        raise ValueError("Error: TMDB_API_KEY not found in environment")
    
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {API_AUTH_KEY}'
    }

    count = 0
    while count < len(movies):
        movie = movies[count]
        id = movie['id']
        url = f"https://api.themoviedb.org/3/movie/{id}?language=en-US"

        try:
            print(f"Making request for movie {count+1} with id {id}")
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                for key, value in data.items():
                    if key not in movie:
                        movie[key] = value
                
                movies_coll.replace_one({"id": id}, movie)
                count+=1
            else:
                if(response.status_code==404):
                    print(f"404, skipping {id}")
                    count+=1
                else:
                    print(f"Error: {response.status_code} {response}")
        except Exception as e:
            print(f"An error has occurred: {str(e)}")

if __name__ == '__main__':
    get_extra_movie_details()


