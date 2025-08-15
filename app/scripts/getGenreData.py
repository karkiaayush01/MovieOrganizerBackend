from dotenv import load_dotenv
import os
import requests
import json
from app.env_loader import load_env

load_env()

def get_all_generes():
    
    API_AUTH_KEY=os.environ.get("TMDB_API_KEY",'')

    if API_AUTH_KEY=='':
        print("Error: API KEY NOT FOUND")
        raise ValueError("Missing TMDb API key in environment variables")

    url = "https://api.themoviedb.org/3/genre/movie/list"

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {API_AUTH_KEY}"
    }

    response = requests.get(url, headers=headers)

    data = response.json()

    if response.status_code == 200 and data:
        with open('genres.json', 'w') as f:
            json.dump(data,f,indent=4)
            print(f"Success: Successfully added genre data to genres.json")
    else:
        print("Error: An error occured while getting genre data.")
        raise requests.HTTPError(f"TMDb API returned status code {response.status_code}")
    
get_all_generes()



