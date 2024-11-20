from sqlalchemy import Column, Integer, String, Text, DateTime, URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class PDFDocument(Base):
    __tablename__ = 'pdf_documents'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)  
    contents = Column(Text, nullable=True)  
    url = Column(String(2083), nullable=False)  
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())