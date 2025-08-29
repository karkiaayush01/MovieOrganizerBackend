from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.movie_route import router as movie_router
from app.routes.user_route import router as user_router

app = FastAPI()

# from .env_loader import load_env

# load_env()

app.add_middleware( 
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(movie_router)
app.include_router(user_router)

@app.get("/")
async def main():
    """ this is the entry point of the application. """
    return {"Message" : "Application successfully loaded."}