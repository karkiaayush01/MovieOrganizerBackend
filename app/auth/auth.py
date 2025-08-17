from fastapi import Request, HTTPException
from firebase_admin import auth, initialize_app

#Gets the token from the header and verifies the token to check if the request is valid. Need to modify to check firebase auth later.
def get_current_user(request: Request):
    #return true for now
    return True
    # 1. Get the Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid auth header")

    # 2. Extract token
    id_token = auth_header.split("Bearer ")[1]

    try:
        # 3. Verify token with Firebase Admin SDK
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token  # contains uid, email, etc.
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Firebase token: {e}")