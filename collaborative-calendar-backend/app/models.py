# app/models.py

from pydantic import BaseModel
from typing import List, Optional
import uuid

class User(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    userId: str = str(uuid.uuid4())  # Generate UUID
    calendars: List[str] = []
