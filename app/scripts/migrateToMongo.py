from app.utils.db_util import get_db
import json
from pathlib import Path
from app.env_loader import load_env
load_env()

db = get_db()
collection = db['movies']
jsonPath = Path(__file__).parent.parent / 'movies.json'
with open(jsonPath, 'r', encoding='utf-8') as f:
    jsonData = json.load(f)  # load directly from file
results = jsonData['results']
print(len(results))

count = 0
while count < len(results):
    try:
        print(f"Inserting movie {count}")
        collection.insert_one(results[count])
        count+=1
    except Exception as e:
        print(f"An error occurred: {e}")