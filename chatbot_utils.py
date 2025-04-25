# chatbot_utils.py
import logging
import re
import difflib
from gemini_service import get_gemini_response

def generate_response(prompt):
    """
    Helper function to generate responses using the current AI model
    This function can be changed to use different models as needed
    """
    try:
        # We can use a special user_id for utilities, or use a system one
        utility_user_id = "system_utils"
        response = get_gemini_response(prompt, utility_user_id)
        return response
    except Exception as e:
        logging.error(f"Error generating response: {str(e)}")
        return "Unable to generate response at this time."

def summarize_paper(paper_text: str) -> dict:
    """
    Generate a concise summary of a scientific paper
    
    Args:
        paper_text: The text content of the paper
        
    Returns:
        Dictionary containing the summary
    """
    prompt = f"""
    You are an AI research assistant. Summarize the following scientific paper in under 150 words. 
    Focus on objectives, methods, key findings, and conclusion.

    Paper:
    {paper_text}
    """
    response = generate_response(prompt)
    return {
        "task": "summary",
        "summary": response.strip()
    }

def generate_citation(title: str, authors: str, journal: str, year: int, doi: str) -> dict:
    """
    Generate a citation in APA 7 format
    
    Args:
        title: Paper title
        authors: String of author names
        journal: Journal or publication name
        year: Publication year
        doi: DOI identifier
        
    Returns:
        Dictionary containing the formatted citation
    """
    prompt = f"""
    Format the following paper information into an APA 7 citation:

    Title: {title}
    Authors: {authors}
    Journal: {journal}
    Year: {year}
    DOI: {doi}
    """
    response = generate_response(prompt)
    return {
        "task": "citation",
        "citation_format": "APA",
        "citation": response.strip()
    }

def recommend_papers(topic: str) -> dict:
    """
    Recommend relevant papers on a given topic
    
    Args:
        topic: Research topic to find papers for
        
    Returns:
        Dictionary containing recommended papers
    """
    # Import models here to avoid circular imports - we'll use a different approach
    # that doesn't require the app context
    from models import ResearchPaper, db
    from flask_login import current_user
    import flask
    
    # First try to find papers in our database that match the topic
    try:
        # Use a simple keyword-based search
        topic_keywords = topic.lower().split()
        matching_papers = []
        
        # Get all papers from the database - we'll try to get papers that are shared by all users
        # This avoids needing current_user which requires the app context
        all_papers = ResearchPaper.query.all()
        
        for paper in all_papers:
            # Check if any keywords match in title, keywords, or abstract
            paper_text = f"{paper.title} {paper.keywords or ''} {paper.abstract or ''}".lower()
            
            # Calculate a simple relevance score based on keyword matches
            relevance = sum(1 for keyword in topic_keywords if keyword in paper_text)
            
            if relevance > 0:
                matching_papers.append({
                    'title': paper.title,
                    'authors': paper.authors,
                    'year': paper.year,
                    'publication': paper.publication,
                    'relevance': relevance,
                    'abstract': paper.abstract
                })
        
        # Sort by relevance score
        matching_papers.sort(key=lambda x: x['relevance'], reverse=True)
        
        if matching_papers:
            # Format the results
            recommendations = "Based on papers in your research library:\n\n"
            
            for i, paper in enumerate(matching_papers[:5], 1):
                # Create a brief description from the abstract if available
                description = ""
                if paper['abstract']:
                    description = f" - {paper['abstract'][:100]}..." if len(paper['abstract']) > 100 else f" - {paper['abstract']}"
                
                recommendations += f"{i}. \"{paper['title']}\" by {paper['authors']} ({paper['year']}), {paper['publication']}{description}\n\n"
            
            return {
                "task": "recommendation",
                "topic": topic,
                "recommendations": recommendations.strip(),
                "source": "database"
            }
    
    except Exception as e:
        print(f"Error searching database for papers: {str(e)}")
    
    # If no matching papers in database or on error, use the AI to generate recommendations
    prompt = f"""
    Recommend 5 recent scientific papers similar to the topic below. 
    Include title, author(s), year, and a one-line description.

    Topic: {topic}
    
    Important: My knowledge is limited to the data I was trained on. 
    Instead of generic disclaimers, provide a clear answer with likely papers in this research field.
    Focus on well-known, significant papers in the field if you're uncertain about the latest research.
    Format each paper with: Title, Author(s), Year, Publication, and a brief description.
    """
    response = generate_response(prompt)
    
    # Add a note to clarify these are AI suggestions
    ai_response = """These suggestions are based on the AI's knowledge and may not represent the most recent publications. For up-to-date research, consider searching:

1. Google Scholar (scholar.google.com)
2. PubMed (pubmed.ncbi.nlm.nih.gov)
3. arXiv (arxiv.org)
4. IEEE Xplore (ieeexplore.ieee.org)
5. ACM Digital Library (dl.acm.org)

Here are the recommended papers on this topic:

""" + response.strip()
    
    return {
        "task": "recommendation",
        "topic": topic,
        "recommendations": ai_response,
        "source": "ai"
    }

def suggest_next_milestone(current_status: str) -> dict:
    """
    Suggest the next research milestone based on current status
    
    Args:
        current_status: Current stage in the research process
        
    Returns:
        Dictionary containing suggested next steps
    """
    prompt = f"""
    The researcher has completed: {current_status}
    Suggest the next logical milestone in the research process.
    Also provide a motivational line.
    """
    response = generate_response(prompt)
    return {
        "task": "milestone",
        "current": current_status,
        "suggested_next": response.strip()
    }

def answer_research_question(question: str, context: str = "") -> dict:
    """
    Answer a research-related question with optional context
    
    Args:
        question: The research question to answer
        context: Optional background information
        
    Returns:
        Dictionary containing the answer
    """
    prompt = f"""
    You are a helpful AI assistant answering a research-related question.
    Context (optional): {context}

    Question: {question}
    Answer in 2-3 sentences.
    """
    response = generate_response(prompt)
    return {
        "task": "qa",
        "question": question,
        "answer": response.strip()
    }

# Application usage guide functions

def explain_add_paper() -> dict:
    """
    Provides step-by-step instructions for adding a research paper
    
    Returns:
        Dictionary containing the instructions
    """
    return {
        "task": "how_to_add_paper",
        "question": "How do I add a research paper?",
        "response": (
            "To add a research paper:\n\n"
            "1. Go to the **Papers** tab.\n"
            "2. Click the **+ Add Paper** button.\n"
            "3. Fill in the required fields:\n"
            "   - **Title**\n"
            "   - **Authors** (e.g., Smith, J.; Johnson, A.)\n"
            "   - **Publication** & **Year**\n"
            "   - **DOI** (optional but useful for citations)\n"
            "   - **URL** (if available)\n"
            "   - **Abstract** (summary of the paper)\n"
            "   - **Keywords** (comma-separated for searchability)\n\n"
            "4. Click **Save Paper** to submit it.\n\n"
            "Your paper will then appear in the list and be available for linking to notes."
        )
    }

def explain_add_patent() -> dict:
    """
    Provides step-by-step instructions for adding a patent
    
    Returns:
        Dictionary containing the instructions
    """
    return {
        "task": "how_to_add_patent",
        "question": "How do I add a patent?",
        "response": (
            "To add a patent:\n\n"
            "1. Go to the **Patents** tab.\n"
            "2. Click the **+ Add Patent** button.\n"
            "3. Fill in the required fields:\n"
            "   - **Title**\n"
            "   - **Patent Number** (e.g., US9876543B2)\n"
            "   - **Inventors** (e.g., Smith, J.; Johnson, A.)\n"
            "   - **Assignee** (company or individual)\n"
            "   - **Filing Date** & **Issue Date**\n"
            "   - **URL** (if available)\n"
            "   - **Abstract**\n"
            "   - **Claims** (brief overview of what the patent covers)\n\n"
            "4. Click **Save Patent** to store it.\n\n"
            "Your patent will appear in the list and can be linked to notes."
        )
    }

def explain_add_note() -> dict:
    """
    Provides step-by-step instructions for adding a research note
    
    Returns:
        Dictionary containing the instructions
    """
    return {
        "task": "how_to_add_note",
        "question": "How do I add a research note?",
        "response": (
            "To add a research note:\n\n"
            "1. Navigate to the **Notes** tab in the navigation bar.\n"
            "2. Click the **+ Add Note** button.\n"
            "3. Fill in the fields:\n"
            "   - **Note Content** (required)\n"
            "   - **Related Paper** (optional)\n"
            "   - **Related Patent** (optional)\n\n"
            "4. Click **Save Note** to submit.\n\n"
            "Once saved, your note will appear in **Your Notes**. "
            "You can also export or delete it anytime."
        )
    }

# Intent detection function

def detect_intent(user_message: str) -> tuple:
    """
    Detect the user's intent from their message and map it to an appropriate function
    
    Args:
        user_message: The message from the user
        
    Returns:
        Tuple containing (detected_intent, params, confidence_score)
        - detected_intent: String representing the detected intent/function
        - params: Dictionary of extracted parameters for the function
        - confidence_score: Float between 0-1 indicating confidence in the match
    """
    # Clean and normalize the message
    cleaned_message = user_message.lower().strip()
    
    # Dictionary of intents with their patterns and associated functions
    intent_patterns = {
        "summarize_paper": [
            r"(?:can you |please |)(?:summarize|summarise|create a summary of|give me a summary of)(?: this| the| a)? paper",
            r"paper summary",
            r"summarize (?:this|the) (?:research|scientific) (?:paper|article)",
            r"(?:create|generate|make)(?: a| me a)? (?:summary|overview) of (?:this|the) paper",
            r"!summarize"
        ],
        "generate_citation": [
            r"(?:can you |please |)(?:generate|create|make|give me)(?: a| the) citation for",
            r"(?:format|create|generate) (?:an?|the) citation",
            r"how (?:should I|do I|to) cite (?:this|the) paper",
            r"(?:what is|what's) the (?:correct|proper) citation for",
            r"!cite"
        ],
        "recommend_papers": [
            r"(?:can you |please |)(?:recommend|suggest|find|get)(?: me| some)? papers(?: on| about| related to| for)?",
            r"(?:what|which) papers (?:should I|would you) (?:read|look at)(?:(?: on| about| related to| for))?",
            r"(?:show|tell) me(?: some)? (?:papers|research)(?: on| about| related to| for)?",
            r"!recommend"
        ],
        "explain_add_paper": [
            r"(?:how|what's the (?:best|right) way) (?:do I|can I|to|should I) add(?: a)? (?:paper|research paper|scientific paper)",
            r"(?:help|guide) me(?: to)? add(?: a)? paper",
            r"(?:explain|tell me|show me) how to add(?: a)? paper"
        ],
        "explain_add_patent": [
            r"(?:how|what's the (?:best|right) way) (?:do I|can I|to|should I) add(?: a)? patent",
            r"(?:help|guide) me(?: to)? add(?: a)? patent",
            r"(?:explain|tell me|show me) how to add(?: a)? patent"
        ],
        "explain_add_note": [
            r"(?:how|what's the (?:best|right) way) (?:do I|can I|to|should I) add(?: a)? (?:note|research note)",
            r"(?:help|guide) me(?: to)? add(?: a)? note",
            r"(?:explain|tell me|show me) how to add(?: a)? note"
        ],
        "suggest_next_milestone": [
            r"(?:what|which|suggest)(?: should be)? (?:is|are) the next (?:step|steps|milestone)",
            r"(?:what|when) should I do next(?: in my research| in this project)?",
            r"(?:help|guide) me(?: with)? (?:planning|next steps|research planning)",
            r"!next"
        ],
        "answer_research_question": [
            r"(?:what is|what's|explain|define|how is|why is|how does|tell me about)",
            r"(?:can you |please |)(?:answer|explain|clarify|help with)(?: this| my| a)? (?:question|research question)",
            r"(?:question|query)(?::)?"
        ]
    }
    
    # Command pattern detection (like !summarize, !cite, etc)
    command_match = re.match(r'^!(\w+)\s*(.*)', cleaned_message)
    if command_match:
        command = command_match.group(1)
        param_text = command_match.group(2).strip()
        
        # Map commands to intents
        command_to_intent = {
            "summarize": "summarize_paper",
            "cite": "generate_citation",
            "recommend": "recommend_papers",
            "next": "suggest_next_milestone",
            "help": "answer_research_question",
            "add_paper": "explain_add_paper",
            "add_patent": "explain_add_patent",
            "add_note": "explain_add_note"
        }
        
        if command in command_to_intent:
            return (command_to_intent[command], {"text": param_text}, 1.0)
    
    # Check each intent pattern
    best_match = (None, {}, 0.0)
    
    for intent, patterns in intent_patterns.items():
        for pattern in patterns:
            # Check if the pattern matches the message
            if re.search(pattern, cleaned_message, re.IGNORECASE):
                confidence = 0.9  # High confidence for direct regex matches
                
                # Extract parameters based on intent
                params = {}
                
                if intent == "summarize_paper":
                    # Try to extract paper text if it's after a common separator
                    for separator in [":", "here's the paper", "here is the paper", "paper:"]:
                        if separator in cleaned_message.lower():
                            parts = user_message.split(separator, 1)
                            if len(parts) > 1 and len(parts[1].strip()) > 50:  # Assume paper text is substantial
                                params["text"] = parts[1].strip()
                                break
                
                elif intent == "recommend_papers":
                    # Try to extract topic
                    topic_patterns = [
                        r"(?:on|about|related to|regarding|concerning|for) ['\"']?([^'\"'.?!]+)['\"']?[.?!]?$",
                        r"^!recommend (.+)$"
                    ]
                    
                    for topic_pattern in topic_patterns:
                        topic_match = re.search(topic_pattern, cleaned_message)
                        if topic_match:
                            params["topic"] = topic_match.group(1).strip()
                            break
                
                # Update best match if this one has higher confidence
                if confidence > best_match[2]:
                    best_match = (intent, params, confidence)
                    # No need to check other patterns for this intent if we got a match
                    break
    
    # If no strong match, try semantic similarity as a fallback
    if best_match[0] is None or best_match[2] < 0.7:
        # Prepare reference intent phrases
        intent_phrases = {
            "summarize_paper": [
                "summarize this paper", 
                "create a summary of this research",
                "give me a brief overview of this paper"
            ],
            "generate_citation": [
                "create a citation for this paper",
                "how do I cite this article",
                "generate a citation in APA format"
            ],
            "recommend_papers": [
                "recommend papers on this topic",
                "suggest research articles about",
                "find similar papers to read"
            ],
            "explain_add_paper": [
                "how do I add a paper to the system",
                "guide me through adding a research paper",
                "what's the process for adding a paper"
            ],
            "explain_add_patent": [
                "how do I add a patent",
                "guide me through adding a patent",
                "what's the process for adding a patent"
            ],
            "explain_add_note": [
                "how do I add a research note",
                "guide me through adding a note",
                "what's the process for adding a note"
            ],
            "suggest_next_milestone": [
                "what should my next research step be",
                "suggest my next milestone",
                "help me plan the next step in my research"
            ],
            "answer_research_question": [
                "answer this research question",
                "help me understand this concept",
                "explain this research topic"
            ]
        }
        
        # Calculate semantic similarity using basic string similarity
        best_similarity = 0.0
        best_intent = None
        
        for intent, phrases in intent_phrases.items():
            for phrase in phrases:
                similarity = difflib.SequenceMatcher(None, cleaned_message, phrase).ratio()
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_intent = intent
        
        # If we found a reasonable semantic match
        if best_similarity > 0.6:
            confidence = min(best_similarity, 0.85)  # Cap confidence for semantic matches
            if confidence > best_match[2]:
                best_match = (best_intent, {}, confidence)
    
    return best_match

def execute_intent(intent: str, params: dict) -> dict:
    """
    Execute the detected intent using the appropriate function
    
    Args:
        intent: The detected intent
        params: Parameters extracted from the user message
        
    Returns:
        Dictionary containing the response
    """
    logging.info(f"Executing intent: {intent} with params: {params}")
    
    # Map intents to functions
    intent_functions = {
        "summarize_paper": summarize_paper,
        "generate_citation": generate_citation,
        "recommend_papers": recommend_papers,
        "suggest_next_milestone": suggest_next_milestone,
        "answer_research_question": answer_research_question,
        "explain_add_paper": explain_add_paper,
        "explain_add_patent": explain_add_patent,
        "explain_add_note": explain_add_note
    }
    
    if intent not in intent_functions:
        return {
            "task": "unknown_intent",
            "response": "I'm not sure how to help with that specific request."
        }
    
    func = intent_functions[intent]
    
    try:
        # Handle different function signatures
        if intent == "summarize_paper" and "text" in params:
            return func(params["text"])
        elif intent == "recommend_papers" and "topic" in params:
            return func(params["topic"])
        elif intent == "suggest_next_milestone" and "status" in params:
            return func(params["status"])
        elif intent == "answer_research_question" and "question" in params:
            context = params.get("context", "")
            return func(params["question"], context)
        elif intent == "generate_citation" and all(key in params for key in ["title", "authors", "journal", "year", "doi"]):
            return func(params["title"], params["authors"], params["journal"], params["year"], params["doi"])
        elif intent in ["explain_add_paper", "explain_add_patent", "explain_add_note"]:
            return func()
        else:
            # Default response for when we have the intent but missing parameters
            # This could trigger follow-up questions in a more sophisticated system
            return {
                "task": intent,
                "response": f"I can help with that. Could you provide more details?"
            }
    except Exception as e:
        logging.error(f"Error executing intent {intent}: {str(e)}")
        return {
            "task": "error",
            "response": f"I encountered an error while processing your request: {str(e)}"
        }