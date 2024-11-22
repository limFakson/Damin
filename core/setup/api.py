from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from setup.functions import FirebaseStorage, extract_content
from setup.model import PDFDocument, SummarisedContent, get_db


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


@router.get("/pdf/<id>")
async def pdf_retrive(id: id):
    return
