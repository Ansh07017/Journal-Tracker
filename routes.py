import os
import json
import csv
import io
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import app, db
from models import User, ResearchPaper, Patent, Note, Reminder
from gemini_service import get_gemini_response
from research_service import search_papers, search_patents, get_doi_metadata, format_citation
from chatbot_utils import (
    summarize_paper, generate_citation as ai_generate_citation, 
    recommend_papers, suggest_next_milestone, answer_research_question,
    explain_add_paper, explain_add_patent, explain_add_note,
    detect_intent, execute_intent
)

# Home route
@app.route('/')
def index():
    if current_user.is_authenticated:
        # Count all papers and patents in the system
        papers_count = ResearchPaper.query.count()
        patents_count = Patent.query.count()
        # Count only the user's notes and reminders - these remain private
        notes_count = Note.query.filter_by(user_id=current_user.id).count()
        reminders = Reminder.query.filter_by(user_id=current_user.id, completed=False).order_by(Reminder.due_date).limit(5).all()
        return render_template('index.html', papers_count=papers_count, patents_count=patents_count, 
                              notes_count=notes_count, reminders=reminders)
    return render_template('index.html')

# API Test route
@app.route('/api-test')
def api_test():
    import logging
    result = {
        'api_key_configured': bool(os.environ.get('GOOGLE_API_KEY')),
        'api_key_length': len(os.environ.get('GOOGLE_API_KEY', '')),
        'gemini_import': False,
        'gemini_models': [],
        'test_message': None,
        'errors': []
    }
    
    try:
        import google.generativeai as genai
        result['gemini_import'] = True
        
        # Configure API
        api_key = os.environ.get('GOOGLE_API_KEY', '')
        genai.configure(api_key=api_key)
        
        # List models
        try:
            models = genai.list_models()
            result['gemini_models'] = [model.name for model in models]
        except Exception as e:
            result['errors'].append(f"Error listing models: {str(e)}")
        
        # Test message
        try:
            model = genai.GenerativeModel('models/gemini-1.5-pro')
            chat = model.start_chat()
            response = chat.send_message("Hello, this is a test message")
            result['test_message'] = response.text[:100] + "..."
        except Exception as e:
            result['errors'].append(f"Error sending test message: {str(e)}")
        
    except ImportError as e:
        result['errors'].append(f"Import error: {str(e)}")
    except Exception as e:
        result['errors'].append(f"General error: {str(e)}")
    
    return jsonify(result)

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash('Logged in successfully!', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if password != password_confirm:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Chatbot route
@app.route('/chat', methods=['POST'])
@login_required
def chat():
    import logging
    try:
        logging.info("Chat endpoint accessed")
        
        # Get the message from the request
        data = request.get_json()
        if not data:
            logging.error("No JSON data in request")
            return jsonify({'response': "Error: Invalid request format"})
            
        user_message = data.get('message', '')
        if not user_message:
            logging.error("No message provided in request")
            return jsonify({'response': "Error: No message provided"})
            
        logging.info(f"User message received: {user_message[:30]}...")
        
        # Check API key
        api_key = os.environ.get("GOOGLE_API_KEY", "")
        logging.info(f"API key configured: {bool(api_key)}")
        if api_key:
            logging.info(f"API key length: {len(api_key)}")
        
        # Handle special case for paper ID summarization
        lower_msg = user_message.lower()
        if ("summarize" in lower_msg or "summary" in lower_msg) and ("with id" in lower_msg or "paper id" in lower_msg):
            try:
                # Extract paper ID
                paper_id = None
                words = lower_msg.split()
                for i, word in enumerate(words):
                    if word == "id" and i+1 < len(words) and words[i+1].isdigit():
                        paper_id = int(words[i+1])
                        break
                
                if paper_id:
                    paper = ResearchPaper.query.get(paper_id)
                    if paper:  # Allow summarizing any paper, regardless of who added it
                        if paper.abstract:
                            result = summarize_paper(paper.abstract)
                            return jsonify({'response': f"Summary of paper '{paper.title}':\n\n{result['summary']}"})
                        else:
                            return jsonify({'response': "I couldn't find an abstract for this paper to summarize."})
            except Exception as e:
                logging.error(f"Error processing paper ID: {str(e)}")
        
        # NEW: Use intent detection system
        logging.info("Using NLP intent detection for message")
        intent, params, confidence = detect_intent(user_message)
        
        logging.info(f"Detected intent: {intent} with confidence {confidence}")
        
        # Handle the intent if it's detected with sufficient confidence
        if intent and confidence >= 0.6:
            logging.info(f"Processing intent: {intent}")
            result = execute_intent(intent, params)
            
            # Format the response based on the task
            if 'task' in result:
                if result['task'] == 'summary':
                    return jsonify({'response': f"Here's a summary:\n\n{result['summary']}"})
                elif result['task'] == 'citation':
                    return jsonify({'response': f"Here's the citation:\n\n{result['citation']}"})
                elif result['task'] == 'recommendation':
                    return jsonify({'response': f"Here are some recommended papers on {result.get('topic', 'your topic')}:\n\n{result['recommendations']}"})
                elif result['task'] == 'milestone':
                    return jsonify({'response': f"Next milestone suggestion:\n\n{result['suggested_next']}"})
                elif result['task'] == 'qa':
                    return jsonify({'response': result['answer']})
                elif result['task'] in ['how_to_add_paper', 'how_to_add_patent', 'how_to_add_note']:
                    return jsonify({'response': result['response']})
                else:
                    # For other tasks or generic responses
                    response_text = result.get('response', 'I understand your request.')
                    return jsonify({'response': response_text})
        
        # Default: Get regular chatbot response if no intent was detected with high confidence
        logging.info(f"No specific intent detected with high confidence, sending to Gemini API")
        response = get_gemini_response(user_message, current_user.id)
        logging.info("Successfully received response from Gemini API")
        
        return jsonify({'response': response})
    except Exception as e:
        logging.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'response': f"An error occurred: {str(e)}"})

# Research Papers routes
@app.route('/papers')
@login_required
def papers():
    # Show all papers regardless of user_id
    papers = ResearchPaper.query.order_by(ResearchPaper.date_added.desc()).all()
    return render_template('papers.html', papers=papers)

@app.route('/papers/add', methods=['POST'])
@login_required
def add_paper():
    title = request.form.get('title')
    authors = request.form.get('authors')
    publication = request.form.get('publication')
    year = request.form.get('year')
    doi = request.form.get('doi')
    url = request.form.get('url')
    abstract = request.form.get('abstract')
    keywords = request.form.get('keywords')
    
    paper = ResearchPaper(
        title=title,
        authors=authors,
        publication=publication,
        year=year,
        doi=doi,
        url=url,
        abstract=abstract,
        keywords=keywords,
        user_id=current_user.id
    )
    
    db.session.add(paper)
    db.session.commit()
    
    flash('Research paper added successfully!', 'success')
    return redirect(url_for('papers'))

@app.route('/papers/<int:paper_id>/delete', methods=['POST'])
@login_required
def delete_paper(paper_id):
    paper = ResearchPaper.query.get_or_404(paper_id)
    
    if paper.user_id != current_user.id:
        flash('You do not have permission to delete this paper', 'danger')
        return redirect(url_for('papers'))
    
    db.session.delete(paper)
    db.session.commit()
    
    flash('Research paper deleted', 'success')
    return redirect(url_for('papers'))

@app.route('/papers/search', methods=['GET'])
@login_required
def search_paper():
    query = request.args.get('query', '')
    
    # If query is blank, return all papers from database
    if not query:
        papers = ResearchPaper.query.order_by(ResearchPaper.date_added.desc()).all()
        # Convert to JSON serializable format
        papers_list = [
            {
                'title': paper.title,
                'authors': paper.authors,
                'publication': paper.publication,
                'year': paper.year,
                'doi': paper.doi,
                'url': paper.url,
                'abstract': paper.abstract,
                'keywords': paper.keywords,
                'id': paper.id
            } for paper in papers
        ]
        return jsonify(papers_list)
    
    # Otherwise, search external API
    papers = search_papers(query)
    return jsonify(papers)

@app.route('/papers/doi/<path:doi>')
@login_required
def doi_metadata(doi):
    metadata = get_doi_metadata(doi)
    return jsonify(metadata)

@app.route('/papers/citation', methods=['POST'])
@login_required
def generate_citation():
    data = request.get_json()
    doi = data.get('doi')
    style = data.get('style', 'ieee')
    
    citation = format_citation(doi, style)
    return jsonify({'citation': citation})

# Patents routes
@app.route('/patents')
@login_required
def patents():
    # Show all patents regardless of user_id
    patents = Patent.query.order_by(Patent.date_added.desc()).all()
    return render_template('patents.html', patents=patents)

@app.route('/patents/add', methods=['POST'])
@login_required
def add_patent():
    title = request.form.get('title')
    patent_number = request.form.get('patent_number')
    inventors = request.form.get('inventors')
    assignee = request.form.get('assignee')
    filing_date_str = request.form.get('filing_date')
    issue_date_str = request.form.get('issue_date')
    url = request.form.get('url')
    abstract = request.form.get('abstract')
    claims = request.form.get('claims')
    
    filing_date = None
    if filing_date_str:
        filing_date = datetime.strptime(filing_date_str, '%Y-%m-%d').date()
    
    issue_date = None
    if issue_date_str:
        issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d').date()
    
    patent = Patent(
        title=title,
        patent_number=patent_number,
        inventors=inventors,
        assignee=assignee,
        filing_date=filing_date,
        issue_date=issue_date,
        url=url,
        abstract=abstract,
        claims=claims,
        user_id=current_user.id
    )
    
    db.session.add(patent)
    db.session.commit()
    
    flash('Patent added successfully!', 'success')
    return redirect(url_for('patents'))

@app.route('/patents/<int:patent_id>/delete', methods=['POST'])
@login_required
def delete_patent(patent_id):
    patent = Patent.query.get_or_404(patent_id)
    
    if patent.user_id != current_user.id:
        flash('You do not have permission to delete this patent', 'danger')
        return redirect(url_for('patents'))
    
    db.session.delete(patent)
    db.session.commit()
    
    flash('Patent deleted', 'success')
    return redirect(url_for('patents'))

@app.route('/patents/search', methods=['GET'])
@login_required
def search_patent():
    query = request.args.get('query', '')
    
    # If query is blank, return all patents from database
    if not query:
        patents = Patent.query.order_by(Patent.date_added.desc()).all()
        # Convert to JSON serializable format
        patents_list = [
            {
                'title': patent.title,
                'patent_number': patent.patent_number,
                'inventors': patent.inventors,
                'assignee': patent.assignee,
                'filing_date': patent.filing_date.strftime('%Y-%m-%d') if patent.filing_date else '',
                'issue_date': patent.issue_date.strftime('%Y-%m-%d') if patent.issue_date else '',
                'url': patent.url,
                'abstract': patent.abstract,
                'claims': patent.claims,
                'id': patent.id
            } for patent in patents
        ]
        return jsonify(patents_list)
    
    # Otherwise, search external API
    patents = search_patents(query)
    return jsonify(patents)

# Notes routes
@app.route('/notes')
@login_required
def notes():
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.date_updated.desc()).all()
    return render_template('notes.html', notes=notes)

@app.route('/notes/add', methods=['POST'])
@login_required
def add_note():
    content = request.form.get('content')
    paper_id = request.form.get('paper_id')
    patent_id = request.form.get('patent_id')
    
    note = Note(
        content=content,
        user_id=current_user.id,
        paper_id=paper_id if paper_id else None,
        patent_id=patent_id if patent_id else None
    )
    
    db.session.add(note)
    db.session.commit()
    
    flash('Note added successfully!', 'success')
    return redirect(url_for('notes'))

@app.route('/notes/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note(note_id):
    note = Note.query.get_or_404(note_id)
    
    if note.user_id != current_user.id:
        flash('You do not have permission to delete this note', 'danger')
        return redirect(url_for('notes'))
    
    db.session.delete(note)
    db.session.commit()
    
    flash('Note deleted', 'success')
    return redirect(url_for('notes'))

# Reminders routes
@app.route('/reminders', methods=['GET', 'POST'])
@login_required
def reminders():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        due_date_str = request.form.get('due_date')
        
        due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
        
        reminder = Reminder(
            title=title,
            description=description,
            due_date=due_date,
            user_id=current_user.id
        )
        
        db.session.add(reminder)
        db.session.commit()
        
        flash('Reminder added successfully!', 'success')
        return redirect(url_for('reminders'))
    
    reminders = Reminder.query.filter_by(user_id=current_user.id).order_by(Reminder.due_date).all()
    return jsonify([{
        'id': r.id,
        'title': r.title,
        'description': r.description,
        'due_date': r.due_date.strftime('%Y-%m-%d %H:%M'),
        'completed': r.completed
    } for r in reminders])

@app.route('/reminders/<int:reminder_id>/toggle', methods=['POST'])
@login_required
def toggle_reminder(reminder_id):
    reminder = Reminder.query.get_or_404(reminder_id)
    
    if reminder.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    reminder.completed = not reminder.completed
    db.session.commit()
    
    return jsonify({'success': True, 'completed': reminder.completed})

@app.route('/reminders/<int:reminder_id>/delete', methods=['POST'])
@login_required
def delete_reminder(reminder_id):
    reminder = Reminder.query.get_or_404(reminder_id)
    
    if reminder.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Not authorized'})
    
    db.session.delete(reminder)
    db.session.commit()
    
    return jsonify({'success': True})

# Export data routes
@app.route('/export/papers', methods=['GET'])
@login_required
def export_papers():
    papers = ResearchPaper.query.filter_by(user_id=current_user.id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Title', 'Authors', 'Publication', 'Year', 'DOI', 'URL', 'Abstract', 'Keywords'])
    
    for paper in papers:
        writer.writerow([
            paper.title,
            paper.authors,
            paper.publication,
            paper.year,
            paper.doi,
            paper.url,
            paper.abstract,
            paper.keywords
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='research_papers.csv'
    )

@app.route('/export/patents', methods=['GET'])
@login_required
def export_patents():
    patents = Patent.query.filter_by(user_id=current_user.id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Title', 'Patent Number', 'Inventors', 'Assignee', 'Filing Date', 'Issue Date', 'URL', 'Abstract', 'Claims'])
    
    for patent in patents:
        writer.writerow([
            patent.title,
            patent.patent_number,
            patent.inventors,
            patent.assignee,
            patent.filing_date.strftime('%Y-%m-%d') if patent.filing_date else '',
            patent.issue_date.strftime('%Y-%m-%d') if patent.issue_date else '',
            patent.url,
            patent.abstract,
            patent.claims
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='patents.csv'
    )

@app.route('/export/notes', methods=['GET'])
@login_required
def export_notes():
    notes = Note.query.filter_by(user_id=current_user.id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Content', 'Date Created', 'Date Updated', 'Paper Title', 'Patent Number'])
    
    for note in notes:
        paper_title = note.paper.title if note.paper else ''
        patent_number = note.patent.patent_number if note.patent else ''
        
        writer.writerow([
            note.content,
            note.date_created.strftime('%Y-%m-%d %H:%M'),
            note.date_updated.strftime('%Y-%m-%d %H:%M'),
            paper_title,
            patent_number
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='research_notes.csv'
    )

# Chatbot utility routes
@app.route('/chatbot/summarize-paper', methods=['POST'])
@login_required
def api_summarize_paper():
    """
    API endpoint to summarize a research paper
    Expects JSON with {'paper_text': 'text content of the paper'}
    """
    import logging
    try:
        logging.info("Paper summarization endpoint accessed")
        
        data = request.get_json()
        if not data or 'paper_text' not in data:
            return jsonify({'error': 'Missing paper text'}), 400
            
        paper_text = data.get('paper_text')
        logging.info(f"Summarizing paper, length: {len(paper_text)} characters")
        
        # Generate summary using AI
        result = summarize_paper(paper_text)
        logging.info("Successfully generated paper summary")
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error in paper summarization: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/chatbot/generate-citation', methods=['POST'])
@login_required
def api_generate_ai_citation():
    """
    API endpoint to generate a citation using AI
    Expects JSON with paper metadata
    """
    import logging
    try:
        logging.info("AI citation generation endpoint accessed")
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing paper data'}), 400
            
        title = data.get('title', '')
        authors = data.get('authors', '')
        journal = data.get('journal', '')
        year = data.get('year', 0)
        doi = data.get('doi', '')
        
        if not title or not authors:
            return jsonify({'error': 'Title and authors are required'}), 400
            
        logging.info(f"Generating citation for: {title}")
        
        # Generate citation using AI
        result = ai_generate_citation(title, authors, journal, year, doi)
        logging.info("Successfully generated citation")
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error in citation generation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/chatbot/recommend-papers', methods=['POST'])
@login_required
def api_recommend_papers():
    """
    API endpoint to recommend related papers on a topic
    Expects JSON with {'topic': 'research topic'}
    """
    import logging
    try:
        logging.info("Paper recommendation endpoint accessed")
        
        data = request.get_json()
        if not data or 'topic' not in data:
            return jsonify({'error': 'Missing topic'}), 400
            
        topic = data.get('topic')
        logging.info(f"Recommending papers for topic: {topic}")
        
        # Get paper recommendations
        result = recommend_papers(topic)
        logging.info("Successfully generated paper recommendations")
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error in paper recommendation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/chatbot/next-milestone', methods=['POST'])
@login_required
def api_next_milestone():
    """
    API endpoint to suggest next research milestone
    Expects JSON with {'current_status': 'current research progress'}
    """
    import logging
    try:
        logging.info("Next milestone suggestion endpoint accessed")
        
        data = request.get_json()
        if not data or 'current_status' not in data:
            return jsonify({'error': 'Missing current status'}), 400
            
        current_status = data.get('current_status')
        logging.info(f"Getting next milestone for status: {current_status[:30]}...")
        
        # Get milestone suggestion
        result = suggest_next_milestone(current_status)
        logging.info("Successfully generated milestone suggestion")
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error in milestone suggestion: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/chatbot/answer-question', methods=['POST'])
@login_required
def api_answer_question():
    """
    API endpoint to answer research questions
    Expects JSON with {'question': 'the question', 'context': 'optional context'}
    """
    import logging
    try:
        logging.info("Research question endpoint accessed")
        
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'Missing question'}), 400
            
        question = data.get('question')
        context = data.get('context', '')
        logging.info(f"Answering research question: {question[:30]}...")
        
        # Get answer to research question
        result = answer_research_question(question, context)
        logging.info("Successfully generated answer")
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error in answering question: {str(e)}")
        return jsonify({'error': str(e)}), 500
