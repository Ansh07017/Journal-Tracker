import os
import google.generativeai as genai
from flask import session

# Configure the Gemini API
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
genai.configure(api_key=GOOGLE_API_KEY)

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
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        # Get chat history
        chat_history = get_chat_history(user_id)
        
        # Start a new chat session if none exists
        if not chat_history:
            chat = model.start_chat(history=[
                {"role": "system", "content": SYSTEM_PROMPT}
            ])
            # Initialize chat history with system prompt
            chat_history = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
        else:
            # Convert history format for the Gemini API
            formatted_history = []
            for message in chat_history:
                if message["role"] == "system":
                    formatted_history.append({"role": "system", "content": message["content"]})
                elif message["role"] == "user":
                    formatted_history.append({"role": "user", "content": message["content"]})
                elif message["role"] == "assistant" or message["role"] == "model":
                    formatted_history.append({"role": "model", "content": message["content"]})
            
            chat = model.start_chat(history=formatted_history)
        
        # Send user message to Gemini
        response = chat.send_message(user_message)
        
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
        print(f"Error with Gemini API: {str(e)}")
        return f"I'm sorry, I'm having trouble processing your request. Please try again later. Error: {str(e)}"
