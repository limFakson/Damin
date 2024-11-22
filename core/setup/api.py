from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Depends,
    WebSocket,
    WebSocketException,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from setup.functions import FirebaseStorage, extract_content
from setup.model import PDFDocument, SummarisedContent, get_db, SessionLocal
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv


# load_dotenv(dotenv_path="../.env")


class pdf_upload(BaseModel):
    name: str = None


router = APIRouter()

genai.configure(api_key="AIzaSyCqIvSpnw86R0T51CMDSKHSMMfFgqFBIN0")
gemini = genai.GenerativeModel("gemini-1.5-flash")


@router.post("/upload/pdf")
async def pdf_upload(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    # file size check -
    if file.size > 300720:
        return HTTPException(detail="File size exceeds the minimum", status_code=413)

    # Firebase initialise
    firebase = FirebaseStorage(file=file)
    docs_url, filename, ext = firebase.store_document()

    # print(docs_url)
    content, doc_len = extract_content(file, ext)

    # Save to database
    new_pdf = PDFDocument(
        name=filename, contents=content, url=docs_url, length=int(doc_len)
    )

    with db as session:
        session.add(new_pdf)
        session.commit()
        session.refresh(new_pdf)

    return {"message": "PDF uploaded successfully", "pdf": new_pdf}


# @router.get("/pdf/<id>")
# async def pdf_retrive(id: id):
#     return


session = SessionLocal()


@router.get("/pdf/summarise/{pdf_id}")
async def pdf(pdf_id: int, db: AsyncSession = Depends(get_db)):
    pdf = session.query(PDFDocument).all()
    return pdf


async def pdf_search(pdf_id: int) -> dict[str:str]:
    pdf = session.query(PDFDocument, pdf_id).get()

    return pdf


@router.websocket("/chat/summarize")
async def pdf_chat(websocket: WebSocket):
    # if pdf_id is None:
    #     websocket.close(code=4001)

    # pdf = await pdf_search(pdf_id)
    await websocket.accept()
    try:
        while True:
            chat = gemini.start_chat(history=None)
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                print(message)
                user_message = message["text"]
                if not user_message:
                    await websocket.send_text("Invalid payload: Missing 'message' key")
                    continue
            except json.JSONDecodeError:
                await websocket.send_text("Invalid JSON format.")
                continue

            # Generate response
            print(f"User message: {user_message}")
            response = chat.send_message(user_message)
            print(f"Generated response: {response.text}")

            # Send response back to client
            await websocket.send_text(response.text)

    except WebSocketDisconnect:
        websocket.close(4000)

    return
