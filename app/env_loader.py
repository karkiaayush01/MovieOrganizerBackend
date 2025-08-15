from dotenv import load_dotenv
from pathlib import Path

# Find the project root (where .env is located)
def load_env():
    # Traverse up until .env is found
    current_dir = Path(__file__).resolve()
    for parent in current_dir.parents:
        env_path = parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            return
    raise FileNotFoundError(".env file not found in any parent directories")