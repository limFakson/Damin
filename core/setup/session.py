from typing import List
from datetime import datetime
from pydantic import BaseModel


class MessageBase(BaseModel):
    id: int
    chat_id: int
    type: str
    text: str

    model_config = {"from_attributes": True}  # Ensures Pydantic ORM compatibility


class ChatSystemBase(BaseModel):
    id: int
    pdf_id: int
    created_at: datetime
    updated_at: datetime
    messages: List[MessageBase] = []

    model_config = {"from_attributes": True}  # Ensures Pydantic ORM compatibility
