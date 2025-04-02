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

# Home route
@app.route('/')
def index():
    if current_user.is_authenticated:
        papers_count = ResearchPaper.query.filter_by(user_id=current_user.id).count()
        patents_count = Patent.query.filter_by(user_id=current_user.id).count()
        notes_count = Note.query.filter_by(user_id=current_user.id).count()
        reminders = Reminder.query.filter_by(user_id=current_user.id, completed=False).order_by(Reminder.due_date).limit(5).all()
        return render_template('index.html', papers_count=papers_count, patents_count=patents_count, 
                              notes_count=notes_count, reminders=reminders)
    return render_template('index.html')

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
    data = request.get_json()
    user_message = data.get('message', '')
    
    # Get chatbot response
    response = get_gemini_response(user_message, current_user.id)
    
    return jsonify({'response': response})

# Research Papers routes
@app.route('/papers')
@login_required
def papers():
    papers = ResearchPaper.query.filter_by(user_id=current_user.id).order_by(ResearchPaper.date_added.desc()).all()
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
    patents = Patent.query.filter_by(user_id=current_user.id).order_by(Patent.date_added.desc()).all()
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
