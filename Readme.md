# FastAPI Backend

This is the backend server built using **FastAPI**.

## Setup

### Virtual Environment
- **Windows**
  python -m venv venv
  .\venv\Scripts\activate

- **Mac/Linux**
  python3 -m venv venv
  source venv/bin/activate

### Install Dependencies
pip install -r requirements.txt

### Run the Server
uvicorn app.main:app --reload

📚 API Documentation
FastAPI provides interactive API docs out of the box:
Swagger UI: http://127.0.0.1:8000/docs
ReDoc: http://127.0.0.1:8000/redoc