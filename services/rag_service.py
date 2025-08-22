"""
RAGService: Retrieval Augmented Generation service using AWS Bedrock with GeoNER enhancement.
Mimics the logic and constants from the working Streamlit rag_chatbot.py, adapted for FastAPI backend.
"""

import boto3
from botocore.config import Config
import sys
from pathlib import Path
# Add the project root directory to the path to access geo_ner module
sys.path.append(str(Path(__file__).parent.parent.parent))
from geo_ner import text_to_geocoded_hypertext
from config.settings import get_settings

# Constants (from rag_chatbot.py)
MODEL_NAME = "assistant"
USER_NAME = "user"
AWS_REGION = "us-west-2"
AMAZON_NOVA_LITE_MODEL_ID = "arn:aws:bedrock:us-west-2:854669816847:inference-profile/us.amazon.nova-lite-v1:0"
ANTRHOPIC_CLAUDE_3_5_SONNET_MODEL_ID = "arn:aws:bedrock:us-west-2:854669816847:inference-profile/us.anthropic.claude-3-5-sonnet-20241022-v2:0"
CALIFORNIA_AREA_OF_INTEREST = {
    'min_lat': 32.50,
    'max_lat': 42.10,
    'min_lon': -124.50,
    'max_lon': -114.10,
}
BEDROCK_CONFIG = Config(
    retries={'max_attempts': 3},
    read_timeout=40,
    connect_timeout=5
)
NUMBER_OF_RESULTS = 25
KNOWLEDGE_BASE_ID = '7XICFRMU5Y'

class RAGService:
    def __init__(self):
        self.settings = get_settings()
        self.aws_access_key_id = self.settings.aws_access_key_id
        self.aws_secret_access_key = self.settings.aws_secret_access_key
        self.esri_api_key = getattr(self.settings, "esri_api_key", None)
        self.shipengine_api_key = getattr(self.settings, "shipengine_api_key", None)
        self.aws_region = AWS_REGION
        self.knowledge_base_id = KNOWLEDGE_BASE_ID
        self.amazon_nova_lite_model_id = AMAZON_NOVA_LITE_MODEL_ID
        self.anthropic_claude_model_id = ANTRHOPIC_CLAUDE_3_5_SONNET_MODEL_ID
        self.number_of_results = NUMBER_OF_RESULTS
        self.bedrock_config = BEDROCK_CONFIG

    def _geo_enhance_text(self, raw_text: str) -> str:
        """
        Enhance text by converting geographic named entities to map hyperlinks using GeoNER.
        Returns original text if enhancement fails or API keys are missing.
        """
        if not raw_text:
            return raw_text
        if not self.esri_api_key:
            return raw_text
        try:
            enhanced = text_to_geocoded_hypertext(
                text_input=raw_text,
                shipengine_api_key=self.shipengine_api_key,
                esri_api_key=self.esri_api_key,
                area_of_interest=CALIFORNIA_AREA_OF_INTEREST
            )
            return enhanced or raw_text
        except Exception as e:
            return raw_text

    def _get_bedrock_client(self):
        session = boto3.Session(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region
        )
        return session.client(
            "bedrock-agent-runtime",
            region_name=self.aws_region,
            config=self.bedrock_config
        )

    def chat(self, message: str, session_id: str = None, model_id: str = None, user_id: int = None) -> dict:
        """
        Main RAG chat method. Accepts user message, returns model response and sessionId.
        Mimics the working logic from rag_chatbot.py, including GeoNER enhancement.
        
        Args:
            message: User's input message
            session_id: Optional session ID for conversation continuity
            model_id: Optional model ID to override default
            user_id: Optional user ID for future user-specific features (available via request.state.user_id)
        """
        if not model_id:
            model_id = self.amazon_nova_lite_model_id
        enhanced_input = self._geo_enhance_text(message)
        bedrock_client = self._get_bedrock_client()
        try:
            if not session_id:
                response = bedrock_client.retrieve_and_generate(
                    input={'text': enhanced_input},
                    retrieveAndGenerateConfiguration={
                        'type': 'KNOWLEDGE_BASE',
                        'knowledgeBaseConfiguration': {
                            'knowledgeBaseId': self.knowledge_base_id,
                            'modelArn': model_id,
                            'retrievalConfiguration': {
                                'vectorSearchConfiguration': {
                                    'numberOfResults': self.number_of_results,
                                }
                            },
                        }
                    },
                )
            else:
                response = bedrock_client.retrieve_and_generate(
                    input={'text': enhanced_input},
                    retrieveAndGenerateConfiguration={
                        'type': 'KNOWLEDGE_BASE',
                        'knowledgeBaseConfiguration': {
                            'knowledgeBaseId': self.knowledge_base_id,
                            'modelArn': model_id,
                            'retrievalConfiguration': {
                                'vectorSearchConfiguration': {
                                    'numberOfResults': self.number_of_results,
                                }
                            },
                        }
                    },
                    sessionId=session_id,
                )

            generated_text = response['output']['text']
            enhanced_response = self._geo_enhance_text(generated_text)
            return {
                'text': enhanced_response,
                'enhanced_user_message': enhanced_input,  # Return the enhanced user message
                'sessionId': response.get('sessionId')
            }
        except Exception as e:
            return {
                'text': f"[ERROR] RAG chat failed: {str(e)}",
                'sessionId': None
            }

    def get_available_models(self):
        """
        Returns available model options for frontend selection.
        """
        return [
            {
                "id": self.amazon_nova_lite_model_id,
                "name": "Amazon Nova Lite"
            },
            {
                "id": self.anthropic_claude_model_id,
                "name": "Claude 3.5 Sonnet v2"
            }
        ] 
