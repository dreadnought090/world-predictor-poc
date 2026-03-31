import os
import uvicorn
from world_predictor.api.app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("world_predictor.api.app:app", host="0.0.0.0", port=port)
