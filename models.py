from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # Relationships
    papers = db.relationship('ResearchPaper', backref='user', lazy=True, cascade="all, delete-orphan")
    patents = db.relationship('Patent', backref='user', lazy=True, cascade="all, delete-orphan")
    notes = db.relationship('Note', backref='user', lazy=True, cascade="all, delete-orphan")
    reminders = db.relationship('Reminder', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def __repr__(self):
        return f'<User {self.username}>'

class ResearchPaper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    authors = db.Column(db.Text, nullable=True)
    publication = db.Column(db.String(255), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    doi = db.Column(db.String(100), nullable=True)
    url = db.Column(db.String(500), nullable=True)
    abstract = db.Column(db.Text, nullable=True)
    keywords = db.Column(db.String(255), nullable=True)
    read_status = db.Column(db.Boolean, default=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notes = db.relationship('Note', backref='paper', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Paper {self.title}>'

class Patent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    patent_number = db.Column(db.String(50), nullable=True)
    inventors = db.Column(db.Text, nullable=True)
    assignee = db.Column(db.String(255), nullable=True)
    filing_date = db.Column(db.Date, nullable=True)
    issue_date = db.Column(db.Date, nullable=True)
    url = db.Column(db.String(500), nullable=True)
    abstract = db.Column(db.Text, nullable=True)
    claims = db.Column(db.Text, nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    notes = db.relationship('Note', backref='patent', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Patent {self.patent_number}: {self.title}>'

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    paper_id = db.Column(db.Integer, db.ForeignKey('research_paper.id'), nullable=True)
    patent_id = db.Column(db.Integer, db.ForeignKey('patent.id'), nullable=True)
    
    def __repr__(self):
        return f'<Note {self.id}>'

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Reminder {self.title}>'
