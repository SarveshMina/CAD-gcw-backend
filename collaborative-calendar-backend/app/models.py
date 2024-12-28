# app/models.py

from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime

# -----------------------
# Existing User Model
# -----------------------
class User(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    userId: str = str(uuid.uuid4())
    calendars: List[str] = []  # store calendarIds the user has

# -----------------------
# New Calendar Model
# -----------------------
class Calendar(BaseModel):
    calendarId: str = str(uuid.uuid4())
    name: str  # e.g., "John Doe's Personal Calendar"
    ownerId: str  # which user created/owns this calendar
    isGroup: bool = False  # personal vs. group
    members: List[str] = []  # for group calendars, store member userIds

# -----------------------
# New Event Model
# -----------------------
class Event(BaseModel):
    eventId: str = str(uuid.uuid4())
    calendarId: str  # which calendar this event belongs to
    title: str
    startTime: datetime
    endTime: datetime
    locked: bool = True  # personal events are locked by default
    description: Optional[str] = None
