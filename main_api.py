"""
EASP AI Microservice Runner
Run directly with: python main_api.py
Or with uvicorn: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
