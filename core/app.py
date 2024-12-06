from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.setup import api

app = FastAPI()

app.include_router(api.router)
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:3000",
    "https://damin-tts.vercel.app/",
    "https://damin-tts.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/home")
async def home():
    return True
