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
    user_id: str
    movie_id: str
    status: Literal['Plan To Watch', 'Completed', 'Watching']
    startDate: Optional[date] = None
    endDate: Optional[date] = None