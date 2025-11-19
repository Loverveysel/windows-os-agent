from dataclasses import dataclass
from datetime import datetime

@dataclass
class Message:
    sender: str  # "user" or "assistant"
    text: str
    timestamp: datetime = datetime.utcnow()