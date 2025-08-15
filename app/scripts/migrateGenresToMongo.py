from app.utils.db_util import get_db
from pathlib import Path
import json

def migrateGenresToDb():
    print("Getting db")
    db = get_db()
    
    print("Getting collection")
    genre_coll = db['genres']

    genreJsonPath = Path(__file__).parent.parent / 'genres.json'
    with open(genreJsonPath, 'r',  encoding='utf-8') as f:
        genreJsonData = json.load(f)
    index = 1
    for genre in genreJsonData['genres']:
        genreData = genre
        genreData['index'] = index
        genre_coll.insert_one(genreData)
        index+=1

if __name__ == "__main__":
    migrateGenresToDb()

