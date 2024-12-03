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
from sqlalchemy.ext.asyncio import AsyncSession
from core.setup.functions import FirebaseStorage, extract_content, make_audio
from core.setup.model import (
    PDFDocument,
    get_db,
    SessionLocal,
    ChatSystem,
    Message,
)
from core.setup.gemini import summarizer
from core.setup.session import MessageBase, ChatSystemBase
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

import ast
import os
import json

router = APIRouter()


@router.post("/upload/pdf")
async def pdf_upload(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    # file size check -
    if file.size > 20000480:
        raise HTTPException(detail="File size exceeds the minimum", status_code=413)

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


@router.get("/pdf")
async def pdf_retrive():
    pdf = session.query(PDFDocument).all()
    return pdf


session = SessionLocal()


@router.get("/pdf/retrieve/{pdf_id}")
async def pdf(pdf_id: int, db: AsyncSession = Depends(get_db)):
    db.connections.close_all()
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


async def create_chat(pdf_id: int, db):
    chat = ChatSystem(pdf_id=pdf_id)

    with db as db:
        db.add(chat)
        db.commit()
        db.refresh(chat)

    return chat.id


async def save_message(chat_id: int, type: str, text: str, db):
    message = Message(chat_id=chat_id, type=type, text=text)

    with db as db:
        db.add(message)
        db.commit()
        db.refresh(message)

    return message


async def check_chat(pdf_id: int):
    chat = (
        session.query(ChatSystem)
        .filter(ChatSystem.pdf_id == pdf_id)
        .options(joinedload(ChatSystem.messages))
        .first()
    )
    if chat:
        return ChatSystemBase.model_validate(chat)
    return False


@router.websocket("/chat/summarize")
async def pdf_chat(
    pdf_id: int, websocket: WebSocket, db: AsyncSession = Depends(get_db)
):
    if pdf_id is None:
        await websocket.close(code=4001)

    pdf = await pdf_search(pdf_id)
    chat_and_message = await check_chat(pdf_id)

    await websocket.accept()
    if chat_and_message:
        chat_id = chat_and_message.id
        if not chat_and_message.messages:
            # convert str into a dict then to str
            vdata_list = ast.literal_eval(pdf["contents"])
            contents = {}
            for i in range(len(vdata_list)):
                contents[f"passage {i+1}"] = vdata_list[i]

            pdf_content = "\n".join(
                [f"{key}: {value}" for key, value in contents.items()]
            )

            await save_message(chat_id, "sent", pdf_content, db)
            summarised = await summarizer(pdf_content)

            await save_message(chat_id, "received", summarised["model"], db)
            await websocket.send_text(summarised["model"])
        else:
            messages_data = [message.dict() for message in chat_and_message.messages]
            messages_json = json.dumps(messages_data)

            await websocket.send_text(messages_json)
    else:
        new_chat = await create_chat(pdf_id, db)

        # convert str into a dict then to str
        vdata_list = ast.literal_eval(pdf["contents"])
        contents = {}
        for i in range(len(vdata_list)):
            contents[f"passage {i +1}"] = vdata_list[i]

        pdf_content = "\n".join([f"{key}: {value}" for key, value in contents.items()])

        await save_message(new_chat, "sent", pdf_content, db)
        summarised = await summarizer(pdf_content)
        await save_message(new_chat, "received", summarised["model"], db)
        await websocket.send_text(summarised["model"])

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                chat = await check_chat(pdf_id)
                saved_message = await save_message(chat.id, "sent", message["text"], db)
            except Exception as e:
                await websocket.send_text(f"Error loading message - error{e}")
                continue
            except WebSocketDisconnect:
                await websocket.close(4000)

            messages_data = [message.dict() for message in chat.messages]
            response = await summarizer(message["text"], messages_data)
            saved_message = await save_message(
                chat.id, "received", response["model"], db
            )

            await websocket.send_text(response["model"])

    except WebSocketDisconnect:
        await websocket.close(4000)


@router.get("/pdf/audio/{pdf_id}")
async def pdf_audio(pdf_id: int):
    pdf = await pdf_search(pdf_id)
    await make_audio(pdf["contents"], [0])
