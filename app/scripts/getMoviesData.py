from pathlib import Path
from app.env_loader import load_env
import os
import requests
import json

load_env()

class Movies:
    
    def __init__(self):
        filePath = Path(__file__)
        rootPath = filePath.parent.parent
        self.movieJsonPath = os.path.join(rootPath, 'movies2.json')
        self.genreJsonPath = os.path.join(rootPath, 'genres.json')
        with open(self.genreJsonPath, 'r') as f:
            self.genres = json.load(f)


    def get_genre_vectors(self, movieGenres:list):
        vector = []
        for genre in self.genres['genres']:
            if genre['id'] in movieGenres:
                vector.append(1)
            else:
                vector.append(0)

        return vector

    def getMovieData(self):
        print("entered")
        page = 1
        total_results = []
        API_AUTH_KEY=os.environ.get("TMDB_API_KEY",'')

        if API_AUTH_KEY=='':
            print("Error: API KEY NOT FOUND")
            raise ValueError("Missing TMDb API key in environment variables")
        
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {API_AUTH_KEY}"
        }

        # with open(self.movieJsonPath, 'r') as f:
        #     jsonData = json.load(f)  # load directly from file
        # total_results = jsonData.get('results', [])

        final = 501

        while page < final:
            url = f"https://api.themoviedb.org/3/discover/movie?include_adult=false&include_video=true&language=en-US&page={page}&sort_by=popularity.desc"
            try:
                print(f"making request {page}")
                response = requests.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    for result in data['results']:
                        genre_ids = result['genre_ids']
                        movieVectors = self.get_genre_vectors(genre_ids)
                        result['genre_vector'] = movieVectors

                    total_results.extend(data['results'])
                    
                else:
                    print('Error: Failed to get data from TMDB')
                    raise requests.HTTPError('Error: Failed to get data from TMDB')
            except Exception as e:
                print(f"Error: An error occurred {str(e)}")
                page -= 1
            finally:
                page += 1

        with open(self.movieJsonPath, 'w') as f:
            result_json = {'results': total_results}
            json.dump(result_json,f,indent=4)
            print(f"Success: Successfully added genre data to movies.json")
        
if __name__ == '__main__':
    movies = Movies()
    movies.getMovieData()