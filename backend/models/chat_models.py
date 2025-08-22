from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    chat_history: List[ChatMessage]
    model_id: str = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    chat_history: List[ChatMessage]
    session_id: Optional[str] = None
    enhanced_user_message: Optional[str] = None

class SavedChat(BaseModel):
    chatname: str
    messages: List[ChatMessage]

class SavedChatList(BaseModel):
    chats: List[Dict[str, Any]]
