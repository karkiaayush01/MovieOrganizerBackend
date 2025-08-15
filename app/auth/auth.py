from fastapi import Request

#Gets the token from the header and verifies the token to check if the request is valid. Need to modify to check firebase auth later.
def get_current_user(request: Request):
    return True