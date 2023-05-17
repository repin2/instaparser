import uvicorn
from fastapi import FastAPI

from routers.instagram import insta_router

app = FastAPI()
app.include_router(insta_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
