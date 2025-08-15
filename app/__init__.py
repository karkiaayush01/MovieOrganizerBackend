from .env_loader import load_env

try:
    load_env()
except Exception as e:
    print(f"An error occured: {str(e)}")