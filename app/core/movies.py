from app.utils.db_util import get_db

genre_cache = None

def get_genre_vectors(movieGenres:list):
    """
        Creates genre vectors from a particular movie's genre array. 
        A genre array is a list showing which genre_ids does a movie belong to e.g. [113, 28, 44]. 
    """
    global genre_cache
    vector = []

    if genre_cache is None:
        db = get_db()
        genres_coll = db['genres']
        genre_cache = list(genres_coll.find().sort('index', 1))

    for genre in genre_cache:
        if genre['id'] in movieGenres:
            vector.append(1)
        else:
            vector.append(0)

    return vector

def get_all_genres():
    """
        Returns all the genres from the genre cache or the database. 
    """
    global genre_cache

    if genre_cache:
        return genre_cache
    else: 
        db = get_db()
        genres_coll = db['genres']
        genre_cache = list(genres_coll.find().sort('index', 1))
        return genre_cache
