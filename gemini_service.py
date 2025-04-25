import os
import logging
from flask import session

# Set up logging
logging.basicConfig(level=logging.INFO)

# Check for Google API Key
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# Log API key status (without revealing the key)
if GOOGLE_API_KEY:
    logging.info("Gemini API key is configured")
    # Mask the key for logging, showing only first two characters
    masked_key = GOOGLE_API_KEY[:2] + "****" if len(GOOGLE_API_KEY) > 2 else "****"
    logging.info(f"API key starts with: {masked_key}")
else:
    logging.warning("Gemini API key is not set")

# Import and configure the Gemini API
try:
    import google.generativeai as genai
    genai.configure(api_key=GOOGLE_API_KEY)
    GEMINI_AVAILABLE = True
    logging.info("Successfully imported and configured google.generativeai")
except ImportError as e:
    logging.error(f"Failed to import google.generativeai: {str(e)}")
    GEMINI_AVAILABLE = False
except Exception as e:
    logging.error(f"Error configuring Gemini API: {str(e)}")
    GEMINI_AVAILABLE = False

# The system prompt defines the assistant's behavior
SYSTEM_PROMPT = """
You are an intelligent research assistant specialized in helping with research papers, patents, 
and academic workflows. Your responsibilities include:

1. Research Paper Management: Help users track, find, and organize research papers.
2. Literature Search & Citation Management: Assist with finding relevant papers and generating citations.
3. Research Notes & Summarization: Summarize papers and help organize research notes.
4. Patent Search & Analysis: Find and analyze patents related to specific technologies.
5. Patent Filing & Best Practices: Provide guidance on patent filing procedures.
6. Research Workflow & Productivity: Help users manage their research workflow.
7. Collaboration & Exporting: Assist with sharing research information.
8. AI Insights & Trends: Identify emerging research trends.
9. Research Ethics & Compliance: Provide guidance on ethical research practices.

If asked about topics outside research, journals, or patents, politely redirect the conversation 
to relevant research topics.

Format your responses with clear headings and concise information. Use bullet points when appropriate 
for readability. Provide citations when referencing specific information.
"""

# Dictionary of fallback responses for different categories of queries
FALLBACK_RESPONSES = {
    "general": "I'm here to help with your research assistant needs, but I'm currently operating in offline mode. You can still use all features of the application that don't require AI assistance. How can I help you with managing your research papers, patents, or notes?",
    
    "paper_search": "To search for papers, you can use the Papers section of the application. While I can't perform AI-powered searches right now, you can manually search using keywords, authors, or DOIs through the search interface.",
    
    "citation": "You can generate citations for papers in the application by using the citation generator in the Papers section. Select a paper and click on 'Generate Citation' to create citations in various formats like APA, MLA, or Chicago.",
    
    "patent": "To find patents, use the Patents section of the application. You can search for patents by title, number, or inventor through the search interface.",
    
    "note": "The Notes section allows you to create, organize, and link notes to your papers and patents. This feature works fully without requiring AI assistance.",
    
    "summarize": "While I can't provide AI-powered summaries right now, you can create your own summaries in the Notes section and link them to specific papers or patents for better organization.",
    
    "export": "You can export your papers, patents, and notes using the export features in each section. This allows you to save your research data or share it with colleagues.",
    
    "help": "This Research Assistant application helps you manage papers, patents, and research notes. All core features are available even without AI capabilities. Navigate to the specific sections using the menu.",
    
    "error": "I apologize, but I'm currently operating without AI capabilities. You can still use all the core features of the Research Assistant application. If you need specific AI-powered analysis, please check back later when API connectivity is restored."
}

def generate_fallback_response(user_message):
    """
    Generate helpful fallback responses when API is unavailable
    Based on the user's message content, provide relevant information
    """
    user_msg = user_message.lower()
    
    # Check message content to determine most relevant response category
    if "search" in user_msg and ("paper" in user_msg or "article" in user_msg or "journal" in user_msg):
        return FALLBACK_RESPONSES["paper_search"]
    elif "citation" in user_msg or "cite" in user_msg or "reference" in user_msg:
        return FALLBACK_RESPONSES["citation"]
    elif "patent" in user_msg:
        return FALLBACK_RESPONSES["patent"]
    elif "note" in user_msg or "write" in user_msg or "record" in user_msg:
        return FALLBACK_RESPONSES["note"]
    elif "summarize" in user_msg or "summary" in user_msg:
        return FALLBACK_RESPONSES["summarize"]
    elif "export" in user_msg or "share" in user_msg or "download" in user_msg:
        return FALLBACK_RESPONSES["export"]
    elif "help" in user_msg or "guide" in user_msg or "how" in user_msg:
        return FALLBACK_RESPONSES["help"]
    elif any(error_term in user_msg for error_term in ["error", "problem", "issue", "not working", "fail"]):
        return FALLBACK_RESPONSES["error"]
    else:
        return FALLBACK_RESPONSES["general"]

def get_chat_history(user_id):
    """Retrieve chat history for the current user"""
    # Use a user-specific key for the session
    session_key = f'chat_history_{user_id}'
    if session_key not in session:
        session[session_key] = []
    return session[session_key]

def set_chat_history(user_id, history):
    """Save chat history for the current user"""
    session_key = f'chat_history_{user_id}'
    session[session_key] = history

def get_gemini_response(user_message, user_id):
    """Get response from Gemini API"""
    # Get chat history for tracking conversation regardless of API status
    chat_history = get_chat_history(user_id)
    
    # If Gemini is not available or API key is not configured, provide fallback
    if not GEMINI_AVAILABLE or not GOOGLE_API_KEY:
        if not GOOGLE_API_KEY:
            logging.warning("Gemini API key is not configured - using fallback mode")
        else:
            logging.warning("Gemini API is not available - using fallback mode")
        
        # Add user message to history for continuity
        chat_history.append({"role": "user", "content": user_message})
        
        # Provide helpful fallback response
        fallback_response = generate_fallback_response(user_message)
        
        # Add fallback response to history
        chat_history.append({"role": "assistant", "content": fallback_response})
        
        # Limit history size to prevent session bloat (keep last 20 messages)
        if len(chat_history) > 21:  # 1 system prompt + 20 messages
            chat_history = [chat_history[0]] + chat_history[-20:]
        
        # Save updated chat history
        set_chat_history(user_id, chat_history)
        
        return fallback_response
    
    try:
        logging.info(f"Sending message to Gemini API for user {user_id}")
        
        # Print API key validity status (without showing the key itself)
        logging.info(f"API key configured and its length is: {len(GOOGLE_API_KEY)}")
        
        # Log available models
        try:
            models = genai.list_models()
            logging.info(f"Available models: {[model.name for model in models]}")
        except Exception as e:
            logging.error(f"Could not list available models: {str(e)}")
        
        # Create Gemini model - use the latest available model
        logging.info("Creating Gemini model instance")
        
        # Try to use models with more free credits
        preferred_models = [
            'models/gemini-1.0-pro-vision-latest',  # More likely to have free credits
            'models/gemini-pro-vision',  # Another option with potential free credits
            'models/gemini-1.5-flash',  # Lighter model with potentially more free credits
            'models/chat-bison-001',  # Basic model with generous free quota
            'models/text-bison-001',  # Another basic model with generous free quota
            'models/gemini-1.5-pro'  # Fallback to original model
        ]
        
        # Try each model until one works
        success = False
        last_error = None
        
        for model_name in preferred_models:
            try:
                logging.info(f"Trying model: {model_name}")
                model = genai.GenerativeModel(model_name)
                # Test with a simple message
                test_chat = model.start_chat()
                test_chat.send_message("Test")
                logging.info(f"Successfully connected to model: {model_name}")
                success = True
                break
            except Exception as e:
                logging.warning(f"Failed to use model {model_name}: {str(e)}")
                last_error = e
        
        if not success:
            logging.error(f"Could not find a working model: {str(last_error)}")
            # Use the original model as last resort
            model_name = 'models/gemini-1.5-pro'
            model = genai.GenerativeModel(model_name)
        
        logging.info(f"Using model: {model_name}")
        # model has already been created in the loop above
                
        logging.info("Gemini model instance created successfully")
        
        # Start a new chat session if none exists
        if not chat_history:
            logging.info("Starting new chat session")
            # Gemini doesn't support system prompts in the same way as OpenAI
            # Initialize with empty history and send system prompt as first message
            chat = model.start_chat()
            # Add system prompt as the initial context
            chat.send_message(SYSTEM_PROMPT)
            
            # Initialize chat history with system message
            chat_history = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
        else:
            logging.info("Continuing existing chat session")
            # Create a new chat session without history
            chat = model.start_chat()
            
            # We'll replay the entire conversation
            first_message = True
            for message in chat_history:
                if message["role"] == "system" and first_message:
                    # Send system prompt first
                    chat.send_message(message["content"])
                    first_message = False
                elif message["role"] == "user":
                    # Send user messages
                    chat.send_message(message["content"])
                # Skip assistant messages in replay since they're responses
        
        # Send user message to Gemini
        logging.info("Sending message to Gemini API")
        response = chat.send_message(user_message)
        logging.info("Received response from Gemini API")
        
        # Update chat history
        chat_history.append({"role": "user", "content": user_message})
        chat_history.append({"role": "assistant", "content": response.text})
        
        # Limit history size to prevent session bloat (keep last 20 messages)
        if len(chat_history) > 21:  # 1 system prompt + 20 messages
            chat_history = [chat_history[0]] + chat_history[-20:]
        
        # Save updated chat history
        set_chat_history(user_id, chat_history)
        
        return response.text
        
    except Exception as e:
        logging.error(f"Error with Gemini API: {str(e)}")
        error_message = str(e)
        
        # Add user message to history for continuity
        chat_history.append({"role": "user", "content": user_message})
        
        # Generate appropriate error response based on the error
        if "API key not valid" in error_message or "authentication" in error_message.lower():
            error_response = "The Gemini API key appears to be invalid. Please contact the administrator to update the API key."
        elif "quota" in error_message.lower() or "rate limit" in error_message.lower():
            error_response = "You've hit the usage limits for the Gemini API. Please try again later."
        else:
            error_response = f"I'm sorry, I'm having trouble processing your request. Please try again later. You can still use all other features of the application."
        
        # Add error response to history
        chat_history.append({"role": "assistant", "content": error_response})
        
        # Limit history size and save
        if len(chat_history) > 21:
            chat_history = [chat_history[0]] + chat_history[-20:]
        set_chat_history(user_id, chat_history)
        
        return error_response
