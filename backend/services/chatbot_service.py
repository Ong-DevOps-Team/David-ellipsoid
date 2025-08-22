from openai import OpenAI
import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import get_settings
from logging_system import error

# Get centralized default system prompt
settings = get_settings()
DEFAULT_SYSTEM_PROMPT = settings.DEFAULT_SYSTEM_PROMPT

class ChatbotService:
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.model = "gpt-4o"
    
    def chat(self, message: str, chat_history: list) -> str:
        """
        Chat with GIS Expert AI
        
        Note: user_id is not currently used in this service, but can be accessed 
        via request.state.user_id in the calling endpoint if needed for future features.
        """
        try:
            # Determine which system prompt to use
            # Priority: 1) System prompt from chat_history, 2) Default fallback prompt
            if chat_history and len(chat_history) > 0:
                first_msg = chat_history[0]
                if hasattr(first_msg, 'role') and first_msg.role == 'system':
                    # Use the system prompt provided by the frontend (from MongoDB)
                    system_prompt = first_msg.content
                else:
                    # No system message found in chat history, use default
                    system_prompt = DEFAULT_SYSTEM_PROMPT
            else:
                # No chat history provided, use default
                system_prompt = DEFAULT_SYSTEM_PROMPT
            
            # Prepare messages array for OpenAI API
            # Start with the system prompt
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                }
            ]
            
            # Add conversation history (excluding system messages to avoid duplication)
            for msg in chat_history:
                if hasattr(msg, 'role') and msg.role != "system":
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # Add the current user message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Send the complete conversation to OpenAI and return the response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            error(f"Error in chatbot service: {e}")
            raise Exception(f"Chat failed: {str(e)}")
