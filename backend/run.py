import uvicorn
import os
import sys

# Add the current directory to sys.path to allow absolute imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("Starting Firestarter AI Backend...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
