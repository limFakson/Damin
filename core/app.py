from fastapi import FastAPI
from sqlalchemy.orm import Session
from setup.model import get_db, PDFDocument, SummarisedContent
from setup import api

app = FastAPI()

app.include_router(api.router)


@app.get("/home")
async def home():
    return True
