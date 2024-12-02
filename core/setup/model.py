from sqlalchemy import Column, Integer, String, Text, DateTime, URL, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()


class PDFDocument(Base):
    __tablename__ = "pdf_documents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    contents = Column(Text, nullable=True)
    url = Column(String(2083), nullable=False)
    length = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SummarisedContent(Base):
    __tablename__ = "summarised_contents"

    id = Column(Integer, primary_key=True, index=True)
    pdf_id = Column(Integer, ForeignKey("pdf_documents.id"))
    summary = Column(Text, nullable=False)
    model = Column(String(150), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ChatSystem(Base):
    __tablename__ = "chat_systems"

    id = Column(Integer, primary_key=True, index=True)
    pdf_id = Column(Integer, ForeignKey("pdf_documents.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # Relationship with Message
    messages = relationship(
        "Message",
        back_populates="chat_system",
        lazy="joined",
        order_by="Message.id.asc()",
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chat_systems.id"))
    type = Column(String(50), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    # Relationship with ChatSystem
    chat_system = relationship("ChatSystem", back_populates="messages")


DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"timeout": 30})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base.metadata.create_all(bind=engine)


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
