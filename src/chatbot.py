"""
Chatbot Module
Integrates with OpenAI GPT or Google Gemini for conversational AI
"""
import logging
from typing import Optional, List, Dict
from enum import Enum


class ChatProvider(Enum):
    OPENAI = "openai"
    GEMINI = "gemini"


class Chatbot:
    """AI Chatbot using OpenAI or Gemini"""
    
    def __init__(self, config: dict):
        self.config = config['chatbot']
        self.logger = logging.getLogger(__name__)
        
        # Determine provider
        provider_name = self.config.get('provider', 'openai').lower()
        self.provider = ChatProvider.OPENAI if provider_name == 'openai' else ChatProvider.GEMINI
        
        # Initialize the appropriate client
        self.client = None
        if self.provider == ChatProvider.OPENAI:
            self._init_openai()
        elif self.provider == ChatProvider.GEMINI:
            self._init_gemini()
        
        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []
        
    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            import openai
            api_key = self.config['openai'].get('api_key')
            if not api_key or api_key == 'your-openai-api-key':
                self.logger.error("OpenAI API key not configured")
                return
            
            openai.api_key = api_key
            self.client = openai
            self.logger.info("OpenAI client initialized")
            
        except ImportError:
            self.logger.error("OpenAI library not installed")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI: {e}")
    
    def _init_gemini(self):
        """Initialize Google Gemini client"""
        try:
            import google.generativeai as genai
            
            api_key = self.config['gemini'].get('api_key')
            if not api_key or api_key == 'your-gemini-api-key':
                self.logger.error("Gemini API key not configured")
                return
            
            genai.configure(api_key=api_key)
            model_name = self.config['gemini'].get('model', 'gemini-pro')
            self.client = genai.GenerativeModel(model_name)
            self.logger.info("Gemini client initialized")
            
        except ImportError:
            self.logger.error("Google Generative AI library not installed")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini: {e}")
    
    def chat(self, user_message: str, use_history: bool = True) -> Optional[str]:
        """Send a message and get a response"""
        if not self.client:
            self.logger.error("Chatbot client not initialized")
            return "Sorry, the chatbot is not configured properly."
        
        try:
            self.logger.info(f"User: {user_message}")
            
            if self.provider == ChatProvider.OPENAI:
                response = self._chat_openai(user_message, use_history)
            elif self.provider == ChatProvider.GEMINI:
                response = self._chat_gemini(user_message, use_history)
            else:
                response = None
            
            if response:
                self.logger.info(f"Bot: {response}")
                
                # Update conversation history
                if use_history:
                    self.conversation_history.append({
                        'role': 'user',
                        'content': user_message
                    })
                    self.conversation_history.append({
                        'role': 'assistant',
                        'content': response
                    })
                    
                    # Limit history size
                    if len(self.conversation_history) > 20:
                        self.conversation_history = self.conversation_history[-20:]
            
            return response
            
        except Exception as e:
            self.logger.error(f"Chat error: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def _chat_openai(self, message: str, use_history: bool) -> Optional[str]:
        """Chat using OpenAI"""
        messages = []
        
        # System message
        messages.append({
            'role': 'system',
            'content': 'You are a helpful AI assistant on a Raspberry Pi reminder system. '
                      'Be concise and friendly. Help users with their reminders and answer questions.'
        })
        
        # Add conversation history
        if use_history:
            messages.extend(self.conversation_history[-10:])  # Last 10 messages
        
        # Add current message
        messages.append({
            'role': 'user',
            'content': message
        })
        
        # Get completion
        response = self.client.ChatCompletion.create(
            model=self.config['openai'].get('model', 'gpt-3.5-turbo'),
            messages=messages,
            max_tokens=self.config['openai'].get('max_tokens', 150),
            temperature=self.config['openai'].get('temperature', 0.7)
        )
        
        return response.choices[0].message.content.strip()
    
    def _chat_gemini(self, message: str, use_history: bool) -> Optional[str]:
        """Chat using Gemini"""
        # Build context from history
        context = ""
        if use_history and self.conversation_history:
            context = "Previous conversation:\n"
            for msg in self.conversation_history[-10:]:
                role = "User" if msg['role'] == 'user' else "Assistant"
                context += f"{role}: {msg['content']}\n"
            context += "\n"
        
        # Create prompt
        prompt = f"{context}User: {message}\nAssistant:"
        
        # Generate response
        response = self.client.generate_content(prompt)
        
        return response.text.strip()
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        self.logger.info("Conversation history cleared")
    
    def get_quick_response(self, query: str) -> str:
        """Get a quick response without history"""
        return self.chat(query, use_history=False) or "I couldn't process that."
