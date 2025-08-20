from typing import Optional, Literal
from pydantic import BaseModel
from datetime import date

#Model for a user
class UserData(BaseModel):
    firebase_user_id: str
    user_name: Optional[str] = None
    name: Optional[str] = None
    email: str
    sign_up_method: str

#Model that contains an instance of a movie in a list
class ListItem(BaseModel):
    firebase_user_id: str
    movie_id: int
    status: Literal['Plan To Watch', 'Completed', 'Watching']
    startDate: Optional[date] = None
    endDate: Optional[date] = None

class RemoveFromWatchListRequest(BaseModel):
    firebase_user_id: str
    movie_id: int

#Model that contains an instance of genre
class Genre(BaseModel):
    genre_id: int
    genre_name: str

#Model for a preference request
class PreferenceRequest(BaseModel):
    firebase_user_id: str
    preferences: list[Genre]

#Model for a movie rating request
class RatingRequest(BaseModel):
    firebase_user_id: str
    movie_id: int
    rating: float