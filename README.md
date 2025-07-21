<div align="center">

# Resume Parser Using NLP & AI

A comprehensive resume parsing solution powered by Natural Language Processing and Google's Gemini AI

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit Version](https://img.shields.io/badge/streamlit-1.29.0-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

</div>

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Module Features](#module-features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Workflow](#workflow)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)
- [Team](#team)

## Overview

The **Resume NLP Parser** revolutionizes recruitment by combining advanced NLP with Google's Gemini AI for intelligent resume processing. It offers a comprehensive solution for candidates, recruiters, and administrators.

## System Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌───────────────┐
│  Web Interface  │────▶│  NLP Engine  │────▶│  Data Storage │
│   (Streamlit)   │     │ (spaCy/NLTK) │     │   (SQLite)    │
└─────────────────┘     └──────────────┘     └───────────────┘
         ▲                     ▲                     ▲
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────┐     ┌──────────────┐     ┌───────────────┐
│   User Auth     │     │  Gemini AI   │     │    Analytics  │
│    System       │     │ Integration  │     │    Engine     │
└─────────────────┘     └──────────────┘     └───────────────┘
```

## Module Features

### 1. User Module (`users.py`)

- Resume upload and parsing
- Skills assessment and visualization
- Career recommendations
- Education and experience analysis
- Resume scoring system

### 2. Recruiter Module (`recruiters.py`)

- Bulk resume processing
- Candidate shortlisting
- Skill gap analysis
- Advanced search filters
- Talent pool management

### 3. Job Matcher Module (`app.py`)

- AI-powered job matching
- Skills compatibility analysis
- Job requirement parsing
- Match percentage calculation
- Customized recommendations

### 4. Admin Module (`admin.py`)

- System configuration
- User management
- Performance monitoring
- Database management
- Analytics dashboard

### 5. Feedback Module (`feedback.py`)

- User feedback collection
- Sentiment analysis
- Bug reporting
- Feature requests
- System improvements

## Requirements

### Core Dependencies

```plaintext
streamlit>=1.29.0
spacy>=3.7.2
nltk>=3.8
google-cloud-aiplatform>=1.36.1
plotly>=5.18.0
pandas>=2.1.4
python-dotenv>=1.0.0
sqlite3
```

### Additional Requirements

- Python 3.8+
- 4GB RAM minimum
- Google Cloud API key
- Internet connection for AI features

## Installation

```bash
# Clone repository
git clone https://github.com/Jethreswar/LLM_NLP_Resume_Parser.git
cd LLM_NLP_Resume_Parser

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
copy .env.example .env
# Edit .env with your API keys

# Initialize database
python init_db.py

# Run application
streamlit run main.py
```

## Project Structure

```
Multi_Resume_LLM_Parser/
├── modules/
│   ├── admin.py        # Admin dashboard
│   ├── users.py        # User interface
│   ├── recruiters.py   # Recruiter tools
│   ├── feedback.py     # Feedback system
│   └── app.py         # Job matcher
├── data/
│   ├── user_pdfs.db   # SQLite database
│   ├── skills.csv     # Skills database
│   └── config.json    # Configuration
├── utils/
│   ├── parser.py      # Parser utilities
│   └── helpers.py     # Helper functions
├── models/
│   └── ner/           # NER models
├── tests/             # Unit tests
├── requirements.txt   # Dependencies
└── README.md         # Documentation
```

## Workflow

## Comprehensive Workflow

### 1. User Authentication & Navigation

#### Authentication Flow
- User login with role-based credentials (User/Recruiter/Admin)
- Session management and secure state preservation
- Role-specific dashboard presentation with available modules
- Centralized navigation system with module switching capabilities

#### Access Control
- Permission-based module visibility and access restrictions
- Admin-only functionality protection
- Session timeout and secure logout handling

### 2. Resume Processing Pipeline

#### Document Handling
- PDF upload with format validation and size restrictions
- Text extraction using multiple libraries (PyMuPDF, PyPDF2) with fallback mechanisms
- Document structure preservation and section identification
- Storage in SQLite database with blob handling

#### NLP Processing Engine
- Named Entity Recognition (NER) using spaCy for personal information extraction
- Pattern matching with regex for structured data (contact details, dates)
- Section classification and boundary detection
- Multiple extraction strategies with redundancy for reliability

#### Data Extraction & Structuring
- Contact information extraction (email, phone, LinkedIn)
- Education history with institution, degree, and timeline detection
- Experience calculation with duration analysis and position identification
- Skills categorization with technical vs. soft skills differentiation
- Achievement and certification extraction

### 3. Analysis & Scoring System

#### Resume Score Generation
- Multi-component weighted scoring algorithm (Skills, Experience, Education, Achievements)
- Industry-standard evaluation metrics
- Visual representation with component breakdown
- Score interpretation with actionable insights

#### Skills Analysis
- Technical skills identification from diverse categories
- Skill categorization by domain and relevance
- Skills gap analysis against job requirements
- Visualization with color-coded relevance indicators

#### Career Path Analysis
- Experience level determination (Entry, Mid, Senior)
- Industry alignment assessment
- Role suitability calculation
- Career progression path visualization

### 4. Job Matching Intelligence

#### Job Description Processing
- Text analysis of job requirements and responsibilities
- Key requirements extraction and prioritization
- Qualification and experience mapping
- Company and role context understanding

#### Compatibility Assessment
- Skills match percentage calculation
- Experience alignment evaluation
- Education requirements verification
- Overall match score generation with confidence level

#### Candidate Enhancement
- Skills gap identification with targeted recommendations
- Profile improvement suggestions with actionable items
- Learning resource recommendations for skill development
- Resume optimization guidance for specific positions

### 5. Recruiter Operations

#### Candidate Management
- Database creation and schema management
- Bulk resume processing and candidate import
- Advanced search with multi-faceted filtering
- Candidate sorting by various metrics (score, experience, date)

#### Shortlisting System
- Candidate shortlisting with persistent state
- Shortlist management with add/remove capabilities
- Shortlist visualization and comparison
- Export functionality for shortlisted candidates

#### Talent Analytics
- Candidate pool analytics with visualizations
- Skills distribution analysis across candidates
- Experience and qualification trend identification
- Score distribution insights and analytics

### 6. Admin Control Center

#### System Management
- Database initialization and maintenance
- Schema updates and migrations
- Performance monitoring and optimization
- System configuration management

#### Content Administration
- Resume database management with archive capabilities
- Feedback data processing and organization
- User account management and permissions
- System-wide settings control

#### Analytics Dashboard
- System usage metrics and visualization
- Feedback sentiment analysis with trend spotting
- User activity monitoring and reporting
- Performance benchmarking and tracking

### 7. Feedback & Improvement Loop

#### User Feedback Collection
- Role-specific feedback forms
- Structured feedback categorization
- Sentiment analysis on feedback content
- Issue tracking and enhancement requests

#### Continuous Improvement
- Feedback processing and prioritization
- Issue resolution tracking
- Feature enhancement based on user input
- System performance optimization from usage metrics

#### Report Generation
- Feedback trend analysis reports
- User satisfaction metrics
- Feature adoption analytics
- System health reports

## API Documentation

### Resume Parser API

```python
extract_resume_info(file_path: str) -> Dict
extract_skills(text: str) -> List[str]
calculate_experience(dates: List[str]) -> int
generate_score(resume_data: Dict) -> float
```

### Job Matcher API

```python
match_resume_to_job(resume: Dict, job: Dict) -> float
suggest_skills(current: List[str], required: List[str]) -> List[str]
calculate_compatibility(skills_match: float, exp_match: float) -> float
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/name`)
3. Commit changes (`git commit -am 'Add feature'`)
4. Push branch (`git push origin feature/name`)
5. Create Pull Request

## Tools and Technologies implemented

- **Backend Development & ML Models**
- **Frontend & UI/UX Design**
- **System Architecture & Integration**
- **Database & API Development**

<div align="center">

</div>
