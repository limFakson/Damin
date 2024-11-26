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
from setup.gemini import summarizer
import google.generativeai as genai
from sqlalchemy.future import select

import ast
import os
import json


# load_dotenv(dotenv_path="../.env")


class pdf_upload(BaseModel):
    name: str = None


router = APIRouter()


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
    result = db.execute(select(PDFDocument).filter_by(id=pdf_id))
    pdf_data = result.scalars().first()

    if pdf_data:
        return {
            "id": pdf_data.id,
            "name": pdf_data.name,
            "contents": pdf_data.contents,
            "url": pdf_data.url,
            "length": pdf_data.length,
        }
    return {"error": "PDF not found"}


async def pdf_search(pdf_id: int) -> dict[str:str]:
    pdf = session.query(PDFDocument).filter_by(id=pdf_id).first()

    if pdf:
        return {
            "id": pdf.id,
            "name": pdf.name,
            "contents": pdf.contents,
            "url": pdf.url,
            "length": pdf.length,
        }


async def save_summarised(content, pdf, model, db: AsyncSession = Depends(get_db)):
    summary = SummarisedContent(summary=content, pdf=pdf, model=model)

    with db as session:
        session.add(summary)
        session.commit()
        session.refresh(summary)

    return


@router.websocket("/chat/summarize")
async def pdf_chat(pdf_id: int, websocket: WebSocket):
    if pdf_id is None:
        websocket.close(code=4001)

    pdf = await pdf_search(pdf_id)
    print(pdf)
    summary = session.query(SummarisedContent).filter_by(pdf_id=pdf["id"]).first()

    if summary is not None:
        summarised = summary.summary
    else:
        vdata_list = ast.literal_eval(pdf["contents"])
        for i in range(vdata_list.length):
            contents = dict()
            contents[f"passage {i}"] = vdata_list[i]
        print(contents)
        summarised = await summarizer(contents, pdf["length"])
        await save_summarised(summarised, pdf["id"], "gemini")
    print(summarised)

    await websocket.accept()
    # try:
    #     while True:
    #         chat = gemini.start_chat(history=None)
    #         data = await websocket.receive_text()
    #         try:
    #             message = json.loads(data)
    #             print(message)
    #             user_message = message["text"]
    #             if not user_message:
    #                 await websocket.send_text("Invalid payload: Missing 'message' key")
    #                 continue
    #         except json.JSONDecodeError:
    #             await websocket.send_text("Invalid JSON format.")
    #             continue

    #         # Generate response
    #         response = chat.send_message(user_message)

    #         # Send response back to client
    #         await websocket.send_text(response.text)

    # except WebSocketDisconnect:
    websocket.close(4000)

    return
