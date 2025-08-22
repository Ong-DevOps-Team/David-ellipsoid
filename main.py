from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import uvicorn
import os
import sys
import datetime
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from auth.auth_service import AuthService, get_current_user
from models.user_models import User, UserLogin, UserResponse
from models.chat_models import ChatMessage, ChatRequest, ChatResponse, SavedChat, SavedChatList
from services.chatbot_service import ChatbotService
from services.rag_service import RAGService
from services.mongo_service import MongoService
from config.settings import get_settings
from logging_system import info, error, warning, critical

app = FastAPI(title="Ellipsoid Labs API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Initialize services
auth_service = AuthService()
chatbot_service = ChatbotService()
rag_service = RAGService()
mongo_service = MongoService()

# Phase 1: Request State Middleware for universal user_id access
@app.middleware("http")
async def user_context_middleware(request: Request, call_next):
    """Extract user_id from JWT and store in request.state for universal access"""
    try:
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
            # Verify token and extract user info
            try:
                token_data = auth_service.verify_token(token)
                if token_data:
                    # Store user_id and username in request.state
                    request.state.user_id = token_data.user_id
                    request.state.username = token_data.username
                else:
                    # Invalid token - set to None
                    request.state.user_id = None
                    request.state.username = None
            except Exception:
                # Token verification failed - set to None
                request.state.user_id = None
                request.state.username = None
        else:
            # No token - set to None
            request.state.user_id = None
            request.state.username = None
        
        # Continue with the request
        response = await call_next(request)
        return response
        
    except Exception as e:
        # If middleware fails, set defaults and continue
        request.state.user_id = None
        request.state.username = None
        response = await call_next(request)
        return response

# Helper functions for accessing user context from request state
def get_current_user_id(request: Request) -> int:
    """Get current user_id from request state"""
    if hasattr(request.state, 'user_id') and request.state.user_id is not None:
        return request.state.user_id
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User ID not available in request state"
    )

def get_current_username(request: Request) -> str:
    """Get current username from request state"""
    if hasattr(request.state, 'username') and request.state.username is not None:
        return request.state.username
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Username not available in request state"
    )

def require_authentication(request: Request):
    """Require authentication - raises appropriate error based on token status"""
    if not hasattr(request.state, 'user_id') or request.state.user_id is None:
        # Check if there was an Authorization header but token was invalid
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # Had token but it was invalid - return 401
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        else:
            # No token at all - return 403
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authenticated"
            )
    return True

def get_user_filter(request: Request) -> dict:
    """
    Get a MongoDB filter for the current user.
    This demonstrates how to use universal user_id access for database operations.
    """
    user_id = get_current_user_id(request)
    return {"user_id": user_id}

def get_user_sort_filter(request: Request, sort_field: str = "timestamp", sort_direction: int = -1) -> tuple:
    """
    Get a MongoDB filter and sort for the current user.
    This demonstrates how to use universal user_id access for database operations with sorting.
    """
    user_filter = get_user_filter(request)
    sort = [(sort_field, sort_direction)]
    return user_filter, sort

# Debug endpoint to verify middleware is working
@app.get("/debug/user-context")
async def debug_user_context(request: Request):
    """Debug endpoint to check user context in request state"""
    return {
        "has_user_id": hasattr(request.state, 'user_id'),
        "user_id": getattr(request.state, 'user_id', None),
        "has_username": hasattr(request.state, 'username'),
        "username": getattr(request.state, 'username', None),
        "state_attributes": list(request.state.__dict__.keys()) if hasattr(request.state, '__dict__') else []
    }

@app.get("/")
async def root():
    return {"message": "Ellipsoid Labs API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/auth/login", response_model=UserResponse)
async def login(user_credentials: UserLogin):
    """Authenticate user and return JWT token"""
    try:
        user = auth_service.authenticate_user(user_credentials.username, user_credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = auth_service.create_access_token(data={"sub": str(user.user_id), "username": user.username})
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            access_token=access_token,
            token_type="bearer"
        )
    except Exception as e:
        error_message = str(e)
        if "Database connection timeout" in error_message:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database connection timeout",
                headers={"X-Error-Type": "database_timeout"}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed"
            )

@app.get("/auth/me", response_model=User)
async def get_current_user_info(request: Request):
    """Get current user information"""
    try:
        # Require authentication
        require_authentication(request)
        
        # Use the new helper functions for universal user_id access
        user_id = get_current_user_id(request)
        username = get_current_username(request)
        return User(user_id=user_id, username=username)
    except HTTPException:
        # Re-raise HTTP exceptions (like 401/403) as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not retrieve user information"
        )

@app.post("/chat/gis", response_model=ChatResponse)
async def chat_gis(
    chat_request: ChatRequest,
    request: Request
):
    """Chat with GIS Expert AI"""
    try:
        # Require authentication
        require_authentication(request)
        
        # Note: user_id is available in request.state.user_id if needed for future features
        response = chatbot_service.chat(
            message=chat_request.message,
            chat_history=chat_request.chat_history
        )
        return ChatResponse(
            message=response,
            chat_history=chat_request.chat_history + [
                {"role": "user", "content": chat_request.message},
                {"role": "assistant", "content": response}
            ],
            session_id=chat_request.session_id
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like 401/403) as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )

@app.post("/chat/rag", response_model=ChatResponse)
async def chat_rag(
    chat_request: ChatRequest,
    request: Request
):
    """Chat with RAG AI"""
    try:
        # Require authentication
        require_authentication(request)
        
        user_id = get_current_user_id(request)
        response = rag_service.chat(
            message=chat_request.message,
            model_id=chat_request.model_id,
            session_id=chat_request.session_id,
            user_id=user_id
        )
        # Extract response text, enhanced user message, and sessionId from the RAG service
        response_text = response['text']
        enhanced_user_message = response.get('enhanced_user_message', chat_request.message)
        response_session_id = response['sessionId']
        return ChatResponse(
            message=response_text,
            chat_history=chat_request.chat_history + [
                {"role": "user", "content": enhanced_user_message},  # Use enhanced user message
                {"role": "assistant", "content": response_text}
            ],
            session_id=response_session_id,
            enhanced_user_message=enhanced_user_message
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like 401/403) as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG chat failed: {str(e)}"
        )

@app.get("/chats/saved", response_model=SavedChatList)
async def get_saved_chats(request: Request):
    """Get list of saved chats for current user"""
    try:
        # Require authentication
        require_authentication(request)
        
        # Use the new helper function for universal user_id access
        user_filter, sort = get_user_sort_filter(request, "timestamp", -1)
        chats = mongo_service.list_documents("saved_chats", query=user_filter, sort=sort)
        # Transform to match expected response format
        formatted_chats = [
            {"chatname": chat.get("chatname", "Untitled"), "chat_id": str(chat.get("_id"))} 
            for chat in chats
        ]
        return SavedChatList(chats=formatted_chats)
    except HTTPException:
        # Re-raise HTTP exceptions (like 401/403) as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve saved chats: {str(e)}"
        )

@app.get("/chats/saved/{chat_id}")
async def get_saved_chat(
    chat_id: str,
    request: Request
):
    """Get a specific saved chat"""
    try:
        # Require authentication
        require_authentication(request)
        
        # Use the new helper function for universal user_id access
        user_filter = get_user_filter(request)
        user_id = user_filter["user_id"]
        
        chat_doc = mongo_service.read_document("saved_chats", chat_id)
        if not chat_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        # Return just the messages array from the chat document
        return chat_doc.get("messages", [])
    except HTTPException:
        # Re-raise HTTP exceptions (like 401/403) as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat: {str(e)}"
        )

@app.post("/chats/save")
async def save_chat(
    saved_chat: SavedChat,
    request: Request
):
    """Save a new chat"""
    try:
        # Require authentication
        require_authentication(request)
        
        # Use the new helper function for universal user_id access
        user_filter = get_user_filter(request)
        user_id = user_filter["user_id"]
        
        # Convert ChatMessage objects to dictionaries for MongoDB storage
        chat_messages = []
        for msg in saved_chat.messages:
            if msg.role != "system":
                chat_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Create document for MongoDB
        document = {
            "chatname": saved_chat.chatname,
            "messages": chat_messages,
            "user_id": user_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc)
        }
        
        chat_id = mongo_service.create_document("saved_chats", document)
        return {"chat_id": chat_id, "message": "Chat saved successfully"}
    except HTTPException:
        # Re-raise HTTP exceptions (like 401/403) as-is
        raise
    except Exception as e:
        error(f"Error in save_chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save chat: {str(e)}"
        )

@app.put("/chats/saved/{chat_id}")
async def update_saved_chat(
    chat_id: str,
    saved_chat: SavedChat,
    request: Request
):
    """Update an existing saved chat"""
    try:
        # Require authentication
        require_authentication(request)
        
        # Use the new helper function for universal user_id access
        user_filter = get_user_filter(request)
        user_id = user_filter["user_id"]
        
        # Convert ChatMessage objects to dictionaries for MongoDB storage
        chat_messages = []
        for msg in saved_chat.messages:
            if msg.role != "system":
                chat_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Prepare update data
        update_data = {
            "chatname": saved_chat.chatname,
            "messages": chat_messages,
            "user_id": user_id
        }
        
        success = mongo_service.update_document("saved_chats", chat_id, update_data)
        if success:
            return {"message": "Chat updated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update chat"
            )
    except HTTPException:
        # Re-raise HTTP exceptions (like 401/403) as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update chat: {str(e)}"
        )

@app.delete("/chats/saved/{chat_id}")
async def delete_saved_chat(
    chat_id: str,
    request: Request
):
    """Delete a saved chat"""
    try:
        # Require authentication
        require_authentication(request)
        
        # Use the new helper function for universal user_id access
        user_filter = get_user_filter(request)
        user_id = user_filter["user_id"]
        
        success = mongo_service.delete_document("saved_chats", chat_id)
        if success:
            return {"message": "Chat deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete chat"
            )
    except HTTPException:
        # Re-raise HTTP exceptions (like 401/403) as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chat: {str(e)}"
        )

@app.get("/about")
async def get_about_info():
    """Get about page information"""
    return {
        "company_name": "Ellipsoid Labs",
        "description": "Ellipsoid Labs was founded in January 2025 by internet entrepreneur and AI expert David Warthen to apply recent advances in AI to GIS, and in particular to ArcGIS Pro.",
        "founder": "David Warthen",
        "background": "Warthen was the co-founder and CTO of Ask Jeeves (NASDAQ: ASKJ), which was the internet's first large scale Natural Language Question Answering System. At its peak, it was the thirteenth largest site on the internet in terms of monthly users. Ask Jeeves was acquired by internet conglomerate IAC for $1.85 billion, and was subsequently rebranded as Ask.com.",
        "gis_focus": "Warthen's interest in GIS developed during the 2020 COVID lockdown. His oldest daughter was majoring in Geography at UCLA and had to finish her last semester at home. During this time, she shared with her father the content and homework in her GIS classes. He became intensely interested and started enrolling in online GIS classes himself. He completed his GIS certificate from Diablo Valley College in 2022, and has shifted his professional focus to applying his expertise in AI to GIS.  (His oldest daughter graduated and is now a GIS professional, working as GIS Analyst for the City of Vallejo, CA.)",
        "contact": "david at ellipsoidlabs dot com"
    }

@app.get("/system-prompts")
async def get_system_prompts():
    """Get system prompts for different AI services"""
    try:
        # Try to retrieve system prompt from MongoDB
        gis_prompt = mongo_service.get_system_prompt("system")
        
        if gis_prompt:
            info(f"✅ Successfully retrieved system prompt from MongoDB (length: {len(gis_prompt)})")
            return {
                "gis_expert": gis_prompt
            }
        else:
            # Fallback to centralized default prompt if MongoDB retrieval fails
            fallback_prompt = mongo_service.settings.DEFAULT_SYSTEM_PROMPT
            warning(f"⚠️  MongoDB system prompt retrieval failed, using fallback prompt (length: {len(fallback_prompt)})")
            return {
                "gis_expert": fallback_prompt
            }
            
    except Exception as e:
        # Fallback to centralized default prompt if any error occurs
        fallback_prompt = mongo_service.settings.DEFAULT_SYSTEM_PROMPT
        error(f"❌ Error retrieving system prompt from MongoDB: {e}")
        warning(f"⚠️  Using fallback prompt (length: {len(fallback_prompt)})")
        return {
            "gis_expert": fallback_prompt
        }

if __name__ == "__main__":
    critical("Backend starting up", module="main")
    uvicorn.run(app, host="0.0.0.0", port=8000)
