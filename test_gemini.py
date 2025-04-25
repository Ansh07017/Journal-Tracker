import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get the API key
api_key = os.environ.get("GOOGLE_API_KEY", "")
logger.info(f"API key is configured: {bool(api_key)}")
logger.info(f"API key length: {len(api_key)}")

try:
    # Import Gemini
    import google.generativeai as genai
    logger.info("Successfully imported google.generativeai")
    
    # Configure the API
    genai.configure(api_key=api_key)
    logger.info("Configured the API")
    
    # List models
    models = genai.list_models()
    logger.info("Available models:")
    for model in models:
        logger.info(f"- {model.name}")
    
    # Try models one by one
    test_models = [
        'models/gemini-1.5-pro',
        'models/gemini-1.5-flash',
        'models/gemini-pro-vision',
        'models/gemini-1.0-pro-vision-latest',
        'models/chat-bison-001',
        'models/text-bison-001',
        'models/embedding-gecko-001'
    ]
    
    success = False
    
    for model_name in test_models:
        try:
            logger.info(f"Testing model: {model_name}")
            model = genai.GenerativeModel(model_name)
            chat = model.start_chat()
            response = chat.send_message("Hello, can you help with research papers?")
            logger.info(f"Response from {model_name}: {response.text[:100]}...")
            success = True
            logger.info(f"Successfully used model: {model_name}")
            break
        except Exception as e:
            logger.error(f"Error with {model_name}: {str(e)}")
    
    if not success:
        logger.error("Could not use any of the predefined models")
        
        # Try the first available model
        available_models = [m.name for m in models]
        if available_models:
            try:
                model_name = available_models[0]
                logger.info(f"Trying first available model: {model_name}")
                model = genai.GenerativeModel(model_name)
                chat = model.start_chat()
                response = chat.send_message("Hello, can you help with research papers?")
                logger.info(f"Response from {model_name}: {response.text[:100]}...")
                logger.info(f"Successfully used model: {model_name}")
            except Exception as e:
                logger.error(f"Error with first available model: {str(e)}")
    
except Exception as e:
    logger.error(f"Exception: {str(e)}")