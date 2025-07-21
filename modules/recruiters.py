import streamlit as st
import re
from typing import Set, List, Dict
from pathlib import Path
import sys
import os
from datetime import datetime
import sqlite3
from contextlib import contextmanager
import pandas as pd
import plotly.express as px
import base64  # For CSV export functionality
import csv  # For reading CSV files
import wordcloud  # For word cloud generation
import matplotlib.pyplot as plt

# Add project root to path to fix imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Remove the spacy import that's causing issues
# and replace with more resilient code

# Define a function to safely import optional dependencies
def safe_import(module_name):
    try:
        pass  # Add your code here
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return __import__(module_name)
    except ImportError:
        return None

# Safely import optional dependencies
fitz = safe_import('fitz')  # PyMuPDF
PyPDF2 = safe_import('PyPDF2')
spacy = safe_import('spacy')

# Initialize NLP if available
nlp = None
if spacy:
    try:
        try:
            # Try to load the model first
            nlp = spacy.load('en_core_web_sm')
        except OSError:
            # If model not found, install it
            st.info("Installing spaCy model. This may take a moment...")
            import subprocess
            subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], 
                          check=True, capture_output=True)
            
            # Try loading again
            try:
                nlp = spacy.load('en_core_web_sm')
                st.success("spaCy model installed successfully!")
            except Exception as e:
                st.warning(f"Could not load spaCy model after installation: {e}")
    except Exception as e:
        st.warning(f"Could not set up spaCy: {e}")
        
        # Try alternative installation method if first one fails
        try:
            import subprocess
            st.info("Trying alternative installation method...")
            subprocess.run([sys.executable, "-m", "pip", "install", "https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.0/en_core_web_sm-3.7.0-py3-none-any.whl"], 
                          check=True, capture_output=True)
            nlp = spacy.load('en_core_web_sm')
            st.success("spaCy model installed via alternative method!")
        except Exception as e2:
            st.warning(f"All spaCy installation attempts failed: {e2}")

# Simplified PDF text extraction that doesn't depend on external modules
def extract_text_from_pdf(file) -> str:
    try:
        if fitz:
            # Try PyMuPDF first
            pdf_document = fitz.open(stream=file.read(), filetype="pdf")
            file.seek(0)  # Reset file pointer
            text = ""
            for page_num in range(len(pdf_document)):
                page = pdf_document.load_page(page_num)
                text += page.get_text()
            return text
        elif PyPDF2:
            # Fall back to PyPDF2
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                text += pdf_reader.pages[page_num].extract_text()
            return text
        else:
            pass
            pass
            st.error("No PDF extraction library available. Please install PyMuPDF or PyPDF2.")
            return ""
    except Exception as e:
        st.error(f"Error extracting PDF text: {e}")
        return ""

# Cache skills parsing
@st.cache_data
def parse_all_skills() -> Set[str]:
    skills_list = set()
    try:
        pass  # Add your code here
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        pass  # Add your code here
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        pass  # Add your code here
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        pass  # Add your code here
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        pass  # Add the code to execute here
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        with open('data/UpdatedSkills.csv', 'r') as file:
            reader = csv.reader(file)
            skills_list = {str(item).lower() for row in reader for item in row}
    except FileNotFoundError:
        st.warning("Skills database not found. Creating new one.")
    return skills_list

# Import from resume_parser with backup implementations
try:
    from resume_parser import (
        extract_resume_info_from_pdf, extract_contact_number_from_resume,
        extract_education_from_resume, extract_experience,
        suggest_skills_for_job, show_colored_skills,
        calculate_resume_score, extract_resume_info
    )
    parser_imported = True
except ImportError as e:
    st.warning(f"Using simplified resume parsing: {str(e)}")
    parser_imported = False
    
    # Define backup implementations
    def extract_resume_info_from_pdf(pdf_file):
        return extract_text_from_pdf(pdf_file)
            
    def extract_resume_info(text):
        if not isinstance(text, str) or not text:
            return {}
        
        # Create result dictionary
        result = {
            'first_name': '',
            'last_name': '',
            'email': '',
            'phone': '',
            'skills': [],
            'education': []
        }
        
        # Extract sections from resume
        sections = extract_resume_sections(text)
        
        # Extract email with improved pattern
        email_pattern = r'[\w.+-]+@[\w-]+\.[\w.-]+'
        email_matches = re.findall(email_pattern, text)
        if email_matches:
            result['email'] = email_matches[0]
        
        # Extract phone with more comprehensive pattern
        phone_patterns = [
            r'(?:\+\d{1,3}\s?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # 123-456-7890
            r'\+\d{1,3}\s\d{10}',  # +1 1234567890
            r'\+\d{1,3}\s\d{1,4}\s\d{6,10}'  # +1 123 4567890
        ]
        
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                result['phone'] = phone_match.group(0)
                break
        
        # Extract name - using multiple techniques
        # 1. Try NLP named entity recognition if available
        name_from_nlp = extract_name_with_nlp(text)
        if name_from_nlp:
            name_parts = name_from_nlp.split()
            if len(name_parts) >= 2:
                result['first_name'] = name_parts[0]
                result['last_name'] = ' '.join(name_parts[1:])
        else:
            # 2. Try to find name at the beginning of the resume
            first_lines = text.strip().split('\n')[:5]  # Check first 5 lines
            for line in first_lines:
                # Look for name-like patterns (2-3 words, capitalized)
                line = line.strip()
                if 3 < len(line) < 40:  # Reasonable name length
                    name_pattern = r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})$'
                    name_match = re.match(name_pattern, line)
                    if name_match:
                        name_parts = name_match.group(0).split()
                        if len(name_parts) >= 2:
                            result['first_name'] = name_parts[0]
                            result['last_name'] = ' '.join(name_parts[1:])
                            break
        
        # Extract skills with improved detection
        result['skills'] = extract_skills(text, sections.get('skills', ''))
        
        # Extract education with better structure
        result['education'] = extract_education_from_resume(text, sections.get('education', ''))
        
        # Extract experience with improved detection
        result['experience'] = extract_experience(text, sections.get('experience', ''))
        
        return result

    # Helper function to extract resume sections
    def extract_resume_sections(text):
        sections = {}
        
        # Common section headers in resumes
        section_patterns = {
            'education': r'(?:EDUCATION|ACADEMIC|QUALIFICATION|DEGREE)',
            'experience': r'(?:EXPERIENCE|EMPLOYMENT|WORK|PROFESSIONAL|CAREER)',
            'skills': r'(?:SKILLS|TECHNICAL|TECHNOLOGIES|EXPERTISE|PROFICIENCY)',
            'projects': r'(?:PROJECTS|PROJECT EXPERIENCE)',
            'certifications': r'(?:CERTIFICATIONS|CERTIFICATES)',
            'summary': r'(?:SUMMARY|PROFILE|OBJECTIVE)'
        }
        
        # Find sections
        for section_name, pattern in section_patterns.items():
            section_matches = re.finditer(rf"^\s*{pattern}.*", text, re.IGNORECASE | re.MULTILINE)
            for match in section_matches:
                section_start = match.start()
                section_header = match.group(0).strip()
                
                # Find the start of the next section
                next_section_start = len(text)
                for other_pattern in section_patterns.values():
                    other_matches = re.finditer(f"{other_pattern}.*?(?:\n|\r|\r\n)", text[section_start+len(section_header):], re.IGNORECASE | re.MULTILINE)
                    for other_match in other_matches:
                        next_start = section_start + len(section_header) + other_match.start()
                        if next_start < next_section_start:
                            next_section_start = next_start
                
                # Extract the section content
                sections[section_name] = text[section_start:next_section_start].strip()
        
        return sections

    # Helper function to extract name using NLP
    def extract_name_with_nlp(text):
        if nlp:
            try:
                # Process only first few hundred chars for speed
                first_chunk = text[:500]
                doc = nlp(first_chunk)
                
                # Look for PERSON entities
                person_entities = [ent.text for ent in doc.ents if ent.label_ == 'PERSON']
                
                if person_entities:
                    # Typically the first person mentioned is the resume owner
                    return person_entities[0]
            except Exception as e:
                st.warning(f"NER extraction error: {e}")
        
        return None

    # Improved skills extraction
    def extract_skills(text, skills_section=None):
        skills = []
        
        # Common technical skills to look for
        common_skills = [
            # Programming Languages
            "python", "java", "javascript", "typescript", "c", "c\\+\\+", "c#", "ruby", "go", "rust", 
            "php", "swift", "kotlin", "r", "perl", "scala", "dart", "matlab", "bash", "powershell",
            
            # Web Technologies
            "html", "css", "react", "angular", "vue", "node", "express", "django", "flask", "spring", 
            "laravel", "asp\\.net", "wordpress", "bootstrap", "jquery", "redux", "graphql", "rest api",
            
            # Databases
            "sql", "mysql", "postgresql", "mongodb", "oracle", "sqlite", "nosql", "redis", "cassandra", 
            "dynamodb", "mariadb", "firebase", "elasticsearch",
            
            # Cloud & DevOps
            "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins", "ci/cd", "git", 
            "github", "gitlab", "bitbucket", "cloudformation", "ansible", "puppet", "chef",
            
            # Data Science & ML
            "machine learning", "deep learning", "pytorch", "tensorflow", "keras", "scikit-learn", 
            "pandas", "numpy", "matplotlib", "tableau", "power bi", "data visualization", "statistics",
            
            # Mobile
            "android", "ios", "react native", "flutter", "xamarin", "swift", "objective-c",
            
            # Other Tech Skills
            "aws", "restful", "graphql", "microservices", "agile", "scrum", "jira"
        ]
        
        # First try to extract from dedicated skills section if available
        if skills_section:
            # Look for skills separated by commas, bullets, or new lines
            skill_matches = re.findall(r'(?:^|\n|,|•|\*)\s*([A-Za-z0-9#\+\-\.]+(?: [A-Za-z0-9#\+\-\.]+){0,2})\s*(?:,|$|\n|•|\*)', skills_section)
            for match in skill_matches:
                skill = match.strip().lower()
                if len(skill) > 2 and skill not in skills:  # Avoid too short skills and duplicates
                    skills.append(skill)
        
        # Then look for common skills throughout the resume
        for skill in common_skills:
            if re.search(r'\b' + skill + r'\b', text.lower()):
                if skill not in skills:
                    skills.append(skill)
        
        return skills

    # Improved education extraction
    def extract_education_from_resume(text, education_section=None):
        education_entries = []
        
        # Use education section if available, otherwise use full text
        text_to_search = education_section if education_section else text
        
        # Common degree patterns
        degree_patterns = [
            r"(?:B\.?A\.?|Bachelor of Arts)",
            r"(?:B\.?S\.?|Bachelor of Science)",
            r"(?:M\.?A\.?|Master of Arts)",
            r"(?:M\.?S\.?|Master of Science)",
            r"(?:M\.?B\.?A\.?|Master of Business Administration)",
            r"(?:Ph\.?D\.?|Doctor of Philosophy)",
            r"(?:B\.?Tech\.?|Bachelor of Technology)",
            r"(?:M\.?Tech\.?|Master of Technology)",
            r"Associate(?:'s)? Degree",
            r"High School Diploma"
        ]
        
        combined_pattern = '|'.join(degree_patterns)
        
        # Find degrees
        degree_matches = re.finditer(combined_pattern, text_to_search, re.IGNORECASE)
        
        for match in degree_matches:
            degree = match.group(0)
            # Look for surrounding text to find university and dates
            surrounding_text = text_to_search[max(0, match.start() - 100):min(len(text_to_search), match.end() + 150)]
            
            # Try to extract university name
            university = extract_university(surrounding_text)
            
            # Try to extract dates
            dates = extract_dates(surrounding_text)
            
            # Try to extract field of study
            field_match = re.search(r'in\s+([A-Za-z\s]+?)(?:,|\.|from|\(|\)|\n|$)', surrounding_text, re.IGNORECASE)
            field = field_match.group(1).strip() if field_match else ""
            
            education_entries.append({
                'degree': degree,
                'university': university,
                'dates': dates,
                'field': field
            })
        
        # If no degrees found but we have education section, extract some basic info
        if not education_entries and education_section:
            lines = education_section.strip().split('\n')
            for i, line in enumerate(lines):
                if i > 0 and len(line.strip()) > 10:  # Skip first line (header) and empty lines
                    # Try to extract university and dates
                    university = extract_university(line)
                    dates = extract_dates(line)
                    if university:
                        education_entries.append({
                            'university': university,
                            'dates': dates
                        })
        
        return education_entries

    # Helper to extract university names
    def extract_university(text):
        # Common university/college indicators
        university_patterns = [
            r"(?:University|College|Institute|School) of [\w\s]+",
            r"[\w\s]+ (?:University|College|Institute)",
            r"[\w\s]+ (?:School)"
        ]
        
        for pattern in university_patterns:
            university_match = re.search(pattern, text, re.IGNORECASE)
            if university_match:
                return university_match.group(0).strip()
        
        return ""

    # Helper to extract dates
    def extract_dates(text):
        # Look for date patterns like MM/YYYY, MM-YYYY, YYYY, Month YYYY, etc.
        date_patterns = [
            r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[,\s]+\d{4}",  # Month Year
            r"\d{1,2}/\d{4}",  # MM/YYYY
            r"\d{1,2}-\d{4}",  # MM-YYYY
            r"\d{4}"  # YYYY
        ]
        
        for pattern in date_patterns:
            dates = re.findall(pattern, text)
            if dates:
                # If we found dates, try to find a range
                if len(dates) >= 2:
                    return f"{dates[0]} - {dates[1]}"
                else:
                    return dates[0]
        
        return ""

    # Improved experience extraction
    def extract_experience(text, experience_section=None):
        result = {
            'work_experiences': [],
            'total_years': 0
        }
        
        # Use experience section if available, otherwise use full text
        text_to_search = experience_section if experience_section else text
        
        # Try to extract experience entries
        experience_entries = extract_experience_entries(text_to_search)
        result['work_experiences'] = experience_entries
        
        # Calculate total years
        total_years = 0
        for entry in experience_entries:
            years = entry.get('duration_years', 0)
            total_years += years
        
        result['total_years'] = round(total_years)
        
        return result

    # Helper to extract work experience entries
    def extract_experience_entries(text):
        entries = []
        
        # Split the text by possible entry separators
        entry_splits = re.split(r'\n(?:\s*\n)+', text)
        
        for entry_text in entry_splits:
            if len(entry_text.strip()) < 20:  # Skip short entries
                continue
                 
            entry = {}
            
            # Try to extract job title
            title_match = re.search(r'((?:Senior|Junior|Lead|Principal|Chief)?\s*[\w\s]+?(?:Engineer|Developer|Designer|Manager|Director|Analyst|Consultant|Architect))', 
                                   entry_text, re.IGNORECASE)
            if title_match:
                entry['title'] = title_match.group(1).strip()
            
            # Try to extract company name
            company_patterns = [
                r'(?:at|with|for)\s+([\w\s&]+?)(?:,|\.|in|\(|\)|\n|$)',
                r'([\w\s&]+?)(?:,|\.|in|\(|\)|\n|$)'
            ]
            
            for pattern in company_patterns:
                company_match = re.search(pattern, entry_text, re.IGNORECASE)
                if company_match:
                    company = company_match.group(1).strip()
                    if len(company) > 3 and len(company) < 40:  # Reasonable company name length
                        entry['company'] = company
                        break
            
            # Try to extract dates and calculate duration
            dates = extract_dates(entry_text)
            entry['dates'] = dates
            
            # Calculate duration in years if we have dates
            if dates:
                duration_years = calculate_duration_years(dates)
                if duration_years > 0:
                    entry['duration_years'] = duration_years
                else:
                    entry['duration_years'] = 0.5  # Default to 6 months if we can't calculate
            
            # Only add entries that have at least some information
            if entry.get('title') or entry.get('company'):
                entries.append(entry)
        
        return entries

    # Helper to calculate duration in years
    def calculate_duration_years(date_string):
        # Extract start and end dates
        start_year = end_year = 0
        current_year = datetime.now().year
        
        # Check for date ranges
        if '-' in date_string or 'to' in date_string or '–' in date_string:
            # Split the date range
            date_parts = re.split(r'\s*(?:-|to|–)\s*', date_string)
            
            if len(date_parts) >= 2:
                # Extract years
                start_year_match = re.search(r'\b(19|20)\d{2}\b', date_parts[0])
                if start_year_match:
                    start_year = int(start_year_match.group(0))
                
                # Check if end date is "present" or similar
                if re.search(r'\b(?:present|current|now)\b', date_parts[1], re.IGNORECASE):
                    end_year = current_year
                else:
                    end_year_match = re.search(r'\b(19|20)\d{2}\b', date_parts[1])
                    if end_year_match:
                        end_year = int(end_year_match.group(0))
        
        # If we have both start and end years, calculate duration
        if start_year > 0 and end_year > 0:
            return end_year - start_year
        
        # Default if we can't calculate
        return 0

# Database utility functions
@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        DATA_DIR = Path(__file__).parent.parent / 'data'
        DATA_DIR.mkdir(exist_ok=True)
        conn = sqlite3.connect(DATA_DIR / 'user_pdfs.db')
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        if conn:
            conn.close()

def create_candidates_table():
    """Create candidates table if it doesn't exist"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                phone TEXT,
                skills TEXT,
                experience_years INTEGER DEFAULT 0,
                education TEXT,
                resume_score INTEGER DEFAULT 0,
                submission_date TEXT,
                status TEXT DEFAULT 'Active',
                shortlisted INTEGER DEFAULT 0
            )
        ''')
        conn.commit()

def update_candidates_table_schema():
    """Add shortlisted column to candidates table if it doesn't exist"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if shortlisted column exists
            cursor.execute("PRAGMA table_info(candidates)")
            columns = [column_info[1] for column_info in cursor.fetchall()]
            
            # Add shortlisted column if it doesn't exist
            if 'shortlisted' not in columns:
                cursor.execute('ALTER TABLE candidates ADD COLUMN shortlisted INTEGER DEFAULT 0')
                conn.commit()
                st.success("Database schema updated successfully")
            
            return True
    except Exception as e:
        st.error(f"Error updating database schema: {e}")
        return False

def get_all_candidates():
    """Get all candidates from database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM candidates')
        rows = cursor.fetchall()
        candidates = []
        for row in rows:
            candidate = dict(row)
            # Convert skills from string to list
            if 'skills' in candidate and candidate['skills']:
                try:
                    candidate['skills'] = candidate['skills'].split(',')
                except:
                    candidate['skills'] = []
            else:
                candidate['skills'] = []
            candidates.append(candidate)
        return candidates

def get_shortlisted_candidates():
    """Get all shortlisted candidates from database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM candidates WHERE shortlisted = 1')
        rows = cursor.fetchall()
        candidates = []
        for row in rows:
            candidate = dict(row)
            # Convert skills from string to list
            if 'skills' in candidate and candidate['skills']:
                try:
                    candidate['skills'] = candidate['skills'].split(',')
                except:
                    candidate['skills'] = []
            else:
                candidate['skills'] = []
            candidates.append(candidate)
        return candidates

def add_candidate(first_name, last_name, email, phone, skills, 
                 experience_years=0, education="", resume_score=0, 
                 submission_date=None, status="Active"):
    """Add new candidate to database"""
    if not submission_date:
        submission_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
    # Convert skills list to comma-separated string
    if isinstance(skills, list):
        skills = ','.join(skills)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO candidates 
            (first_name, last_name, email, phone, skills, experience_years, 
            education, resume_score, submission_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, email, phone, skills, experience_years,
              education, resume_score, submission_date, status))
        conn.commit()
        return cursor.lastrowid

# Updated delete_candidate function with better error handling
def delete_candidate(candidate_id):
    """Delete a candidate from the database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # First check if the candidate exists
            cursor.execute('SELECT id FROM candidates WHERE id = ?', (candidate_id,))
            if not cursor.fetchone():
                return False
            
            # Then delete the candidate
            cursor.execute('DELETE FROM candidates WHERE id = ?', (candidate_id,))
            conn.commit()
            return cursor.rowcount > 0  # Return True if a row was deleted
    except Exception as e:
        st.error(f"Database error during deletion: {e}")
        return False

def search_candidates(query=None, min_score=0, category="All", status="Active"):
    """Search candidates based on criteria with improved filtering"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        base_query = '''
            SELECT * FROM candidates 
            WHERE resume_score >= ? 
            AND status = ?
        '''
        params = [min_score, status]
        
        if query:
            # Split the query to support multiple search terms
            search_terms = [term.strip() for term in query.split(',')]
            
            if category == "All":
                # Search in all fields with OR between terms
                conditions = []
                for term in search_terms:
                    conditions.append("first_name LIKE ?")
                    conditions.append("last_name LIKE ?")
                    conditions.append("email LIKE ?")
                    conditions.append("skills LIKE ?")
                    # Add parameters for each condition
                    search_param = f'%{term}%'
                    params.extend([search_param, search_param, search_param, search_param])
                
                base_query += f" AND ({' OR '.join(conditions)})"
                
            elif category == "Skills":
                # For skills, we need to check if ANY of the terms match
                skill_conditions = []
                for term in search_terms:
                    skill_conditions.append("skills LIKE ?")
                    params.append(f'%{term}%')
                
                base_query += f" AND ({' OR '.join(skill_conditions)})"
                
            elif category == "Name":
                # For names, check both first and last name
                name_conditions = []
                for term in search_terms:
                    name_conditions.append("first_name LIKE ?")
                    name_conditions.append("last_name LIKE ?")
                    params.extend([f'%{term}%', f'%{term}%'])
                
                base_query += f" AND ({' OR '.join(name_conditions)})"
                
            elif category == "Email":
                # For email, we need exact matches or partial
                email_conditions = []
                for term in search_terms:
                    email_conditions.append("email LIKE ?")
                    params.append(f'%{term}%')
                
                base_query += f" AND ({' OR '.join(email_conditions)})"
        
        # Execute the query
        cursor.execute(base_query, params)
        rows = cursor.fetchall()
        candidates = []
        
        for row in rows:
            candidate = dict(row)
            # Convert skills from string to list
            if 'skills' in candidate and candidate['skills']:
                candidate['skills'] = candidate['skills'].split(',')
            else:
                candidate['skills'] = []
            candidates.append(candidate)
        
        return candidates

def sort_candidates(candidates, sort_option):
    """Sort candidates based on the selected option"""
    try:
        if sort_option == "Score (High to Low)":
            return sorted(candidates, key=lambda x: int(x.get('resume_score', 0)), reverse=True)
        elif sort_option == "Experience (High to Low)":
            return sorted(candidates, key=lambda x: int(x.get('experience_years', 0)), reverse=True)
        elif sort_option == "Recent First":
            return sorted(candidates, 
                         key=lambda x: pd.to_datetime(x.get('submission_date', '2000-01-01'), 
                                                     errors='coerce'), 
                         reverse=True)
        elif sort_option == "Name (A-Z)":
            return sorted(candidates, 
                         key=lambda x: f"{x.get('first_name', '')} {x.get('last_name', '')}")
        return candidates  # Return unsorted if no match
    except Exception as e:
        st.warning(f"Sorting error: {e}. Displaying unsorted results.")
        return candidates

def display_candidates(candidates, prefix):
    """Display candidates with unified formatting"""
    for idx, candidate in enumerate(candidates):
        # Extract candidate data
        candidate_id = candidate.get('id', 0)
        first_name = candidate.get('first_name', 'Unknown')
        last_name = candidate.get('last_name', 'Candidate')
        email = candidate.get('email', 'No email provided')
        phone = candidate.get('phone', 'No phone provided')
        experience_years = candidate.get('experience_years', 0)
        resume_score = candidate.get('resume_score', 0)
        submission_date = candidate.get('submission_date', 'Unknown date')
        skills = candidate.get('skills', [])
        education = candidate.get('education', 'No education data')
        shortlisted = candidate.get('shortlisted', 0)
        
        # Create a visual score indicator
        score_color = "#4CAF50" if resume_score >= 80 else "#FFC107" if resume_score >= 50 else "#F44336"
        
        # Add shortlisted indicator
        shortlist_indicator = "⭐ " if shortlisted else ""
        
        with st.expander(f"{shortlist_indicator}**{first_name} {last_name}** - Score: {resume_score}/100"):
            # Upper section with basic info and score
            cols = st.columns([3, 1])
            
            with cols[0]:
                # Contact information with icons
                st.markdown(f"📧 **Email:** {email}")
                st.markdown(f"📱 **Phone:** {phone}")
                st.markdown(f"🎓 **Education:** {education}")
                st.markdown(f"💼 **Experience:** {experience_years} years")
                st.markdown(f"📅 **Submitted:** {submission_date}")
            
            with cols[1]:
                # Visual score gauge
                st.metric("Resume Score", resume_score)
            
            # Skills section
            st.markdown("### 🛠️ Skills")
            if skills:
                cols = st.columns([1, 1, 1, 1, 1])
                for i, skill in enumerate(skills):
                    if skill:
                        col_index = i % 5
                        # Use a unique key that includes candidate_id, prefix, and skill index
                        unique_key = f"{prefix}_{candidate_id}_skill_{i}"
                        cols[col_index].button(skill, key=unique_key, disabled=True)
            else:
                st.info("No skills listed for this candidate")
            
            # Actions section with only shortlist and delete buttons
            st.markdown("### Actions")
            action_col1, action_col2 = st.columns(2)
            
            with action_col1:
                # Shortlist toggle button with current status reflected
                shortlist_label = "✓ Shortlisted" if shortlisted else "⭐ Shortlist"
                shortlist_type = "primary" if shortlisted else "secondary"
                if st.button(shortlist_label, key=f"{prefix}_shortlist_{candidate_id}_{idx}", type=shortlist_type):
                    # Toggle shortlist status
                    toggle_shortlist_candidate(candidate_id, not shortlisted)
                    st.success(f"{'Removed from' if shortlisted else 'Added to'} shortlist!")
                    st.rerun()
                    
            with action_col2:
                # Add delete button with confirmation
                delete_key = f"{prefix}_delete_{candidate_id}_{idx}"
                delete_button = st.button("🗑️ Delete", key=delete_key, type="secondary")
                
                # Handle delete confirmation and action
                if delete_button:
                    st.session_state[f"confirm_{delete_key}"] = True
                
                if st.session_state.get(f"confirm_{delete_key}", False):
                    st.markdown("---")
                    st.warning(f"Are you sure you want to delete {first_name} {last_name}?")
                    confirm_col1, confirm_col2 = st.columns(2)
                    
                    with confirm_col1:
                        if st.button("Yes, Delete", key=f"{prefix}_confirm_{candidate_id}_{idx}", type="primary"):
                            success = delete_candidate(candidate_id)
                            if success:
                                st.success(f"Candidate {first_name} {last_name} deleted successfully!")
                                if f"confirm_{delete_key}" in st.session_state:
                                    del st.session_state[f"confirm_{delete_key}"]
                                st.rerun()
                            else:
                                st.error(f"Failed to delete candidate {first_name} {last_name}.")
                    
                    with confirm_col2:
                        if st.button("Cancel", key=f"{prefix}_cancel_{candidate_id}_{idx}"):
                            if f"confirm_{delete_key}" in st.session_state:
                                del st.session_state[f"confirm_{delete_key}"]
                            st.rerun()

def toggle_shortlist_candidate(candidate_id, shortlist_status):
    """Toggle the shortlisted status of a candidate in the database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE candidates SET shortlisted = ? WHERE id = ?",
                (1 if shortlist_status else 0, candidate_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        st.error(f"Error updating shortlist status: {e}")
        return False

def provide_download_csv(df, filename="data.csv"):
    """Provide a download for a dataframe without using HTML anchors"""
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv_data,
        file_name=filename,
        mime="text/csv"
    )

def email_candidates(emails, subject, body):
    """Display email addresses for copying rather than using HTML anchors"""
    email_str = ", ".join(emails)
    st.code(email_str, language="text")
    st.info("Copy these email addresses and paste them into your email client")

def process_recruiters_mode():
    try:
        st.title("Recruiter Portal")
        
        # Create candidates table if it doesn't exist
        create_candidates_table()
        
        # Update table schema to add shortlisted column if needed
        update_candidates_table_schema()
        
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 Search Candidates", "⭐ Shortlisted", "➕ Add Candidate", "📊 Analytics"])
        
        # Search Candidates tab (existing code)
        with tab1:
            st.subheader("Search Candidates")
            
            # Add a stylish header
            st.markdown("<div style=\"text-align: center;\">### 🔍 Find the Perfect Candidate</div>", unsafe_allow_html=True)
            st.caption("Search by name, skills, or email to find suitable candidates")
            
            # Improved search interface with better layout
            col1, col2, col3 = st.columns([5, 3, 2])
            
            with col1:
                search_query = st.text_input("Search", placeholder="Java Developer, Python, john@example.com", 
                                             help="Enter skills, name or email")
            
            with col2:
                # Add categories to filter by
                search_category = st.selectbox(
                    "Filter by",
                    options=["All", "Skills", "Name", "Email"],
                    index=0,
                    help="Select a category to narrow your search"
                )
            
            with col3:
                min_score = st.slider("Min Score", min_value=0, max_value=100, value=0, step=10,
                                      help="Minimum resume score")
            
            # Search button with improved styling
            search_col1, search_col2, search_col3 = st.columns([4, 2, 4])
            with search_col2:
                search_button = st.button("🔍 Search Candidates", key="search_btn", use_container_width=True)
            
            # Always show Sort By options
            sort_col1, sort_col2 = st.columns([1, 3])
            with sort_col1:
                st.write("**Sort by:**")
            with sort_col2:
                sort_option = st.selectbox(
                    "",
                    options=["Score (High to Low)", "Experience (High to Low)", "Recent First", "Name (A-Z)"],
                    label_visibility="collapsed",
                    key="sort_option"
                )

            # Search logic
            if search_query or search_button:
                with st.spinner("Searching for candidates..."):
                    candidates = search_candidates(search_query, min_score, search_category)
    
                if not candidates:
                    # Provide more helpful feedback
                    filter_msg = f" in '{search_category}'" if search_category != "All" else ""
                    st.warning(f"No candidates found matching '{search_query}'{filter_msg}")
                    
                    # Offer suggestions based on the filter
                    if search_category == "Skills":
                        st.info("""
                        **Tips for skills search:**
                        - Separate multiple skills with commas: "python, java"
                        - Try using lowercase: "javascript" instead of "JavaScript"
                        - Use simpler terms: "js" instead of "javascript"
                        """)
                    elif search_category == "Name":
                        st.info("""
                        **Tips for name search:**
                        - Try searching for first name or last name separately
                        - Check spelling and try partial names
                        """)
                    elif search_category == "Email":
                        st.info("""
                        **Tips for email search:**
                        - Try searching for the domain: "@gmail.com"
                        - Or search for just part of the email: "john"
                        """)
                    else:
                        st.info("""
                        **Tips for better search results:**
                        - For multiple skills, separate them with commas: "python, java"
                        - Try using partial terms: "dev" instead of "developer"
                        - Check your spelling and try using lowercase
                        """)
                else:
                    # Show results with better formatting
                    st.success(f"Found {len(candidates)} candidate(s) matching your search in '{search_category}' category")
                    
                    # Sort candidates based on selection (moved code from below)
                    candidates = sort_candidates(candidates, sort_option)
                    
                    # Display candidates
                    display_candidates(candidates, "search")
            else:
                # Show a sampling of candidates
                candidates = get_all_candidates()
                if candidates:
                    st.info(f"Showing {min(5, len(candidates))} most recent candidates. Use search to find specific candidates.")
                    
                    # Sort the sample candidates too
                    candidates = sort_candidates(candidates[:5], sort_option)
                    
                    # Display candidates
                    display_candidates(candidates, "sample")
                else:
                    # Empty state with guidance
                    st.info("No candidates yet. Add candidates by uploading resumes or using the \"Add Candidate\" tab.")
                    st.markdown("🔍")
        
        # New Shortlisted tab
        with tab2:
            st.subheader("Shortlisted Candidates")
            
            # Add a stylish header
            st.header("Your Top Picks")
            st.caption("Review and manage your shortlisted candidates")
            
            # Get shortlisted candidates
            shortlisted_candidates = get_shortlisted_candidates()
            
            # Sort options for shortlisted candidates
            sort_col1, sort_col2 = st.columns([1, 3])
            with sort_col1:
                st.write("**Sort by:**")
            with sort_col2:
                shortlist_sort_option = st.selectbox(
                    "",
                    options=["Score (High to Low)", "Experience (High to Low)", "Recent First", "Name (A-Z)"],
                    label_visibility="collapsed",
                    key="shortlist_sort_option"
                )
            
            # Display shortlisted candidates or empty state
            if shortlisted_candidates:
                # Sort candidates based on selection
                sorted_candidates = sort_candidates(shortlisted_candidates, shortlist_sort_option)
                
                # Show count and candidate cards
                st.success(f"You have {len(shortlisted_candidates)} shortlisted candidates")
                display_candidates(sorted_candidates, "shortlist")
                
                # Add export options
                st.markdown("---")
                export_col1, export_col2 = st.columns(2)
                
                with export_col1:
                    # Prepare data for export
                    export_data = []
                    for candidate in shortlisted_candidates:
                        export_data.append({
                            'First Name': candidate.get('first_name', ''),
                            'Last Name': candidate.get('last_name', ''),
                            'Email': candidate.get('email', ''),
                            'Phone': candidate.get('phone', ''),
                            'Skills': ', '.join(candidate.get('skills', [])),
                            'Experience (years)': candidate.get('experience_years', 0),
                            'Education': candidate.get('education', ''),
                            'Resume Score': candidate.get('resume_score', 0),
                            'Submission Date': candidate.get('submission_date', '')
                        })

                    # Create DataFrame and use native Streamlit download button
                    df = pd.DataFrame(export_data)
                    provide_download_csv(df, "shortlisted_candidates.csv")

                with export_col2:
                    if st.button("✉️ Email Addresses", use_container_width=True):
                        # Show emails for copying instead of mailto link
                        emails = [c.get('email', '') for c in shortlisted_candidates if c.get('email')]
                        if emails:
                            email_candidates(emails, "Regarding Your Application", 
                                            "Dear Candidate,\n\nThank you for your interest in our position.\n\nBest regards,")
                        else:
                            st.warning("No email addresses found for shortlisted candidates.")
            else:
                # Import container and style it as needed
                with st.container():
                    st.info("No shortlisted candidates yet")
                    st.write("Click the \"⭐ Shortlist\" button on candidate cards to add them to your shortlist.")
                    st.markdown("⭐")
        
        # Add Candidate tab (existing code)
        with tab3:
            st.subheader("Add New Candidate")
            
            # Form for adding new candidate
            with st.form("add_candidate_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    first_name = st.text_input("First Name", placeholder="John")
                    last_name = st.text_input("Last Name", placeholder="Smith")
                    email = st.text_input("Email", placeholder="john.smith@example.com")
                    phone = st.text_input("Phone", placeholder="555-123-4567")
                
                with col2:
                    experience_years = st.number_input("Years of Experience", min_value=0, max_value=50, value=0)
                    education = st.text_input("Education", placeholder="Bachelor's in Computer Science")
                    skills_input = st.text_area("Skills (comma separated)", placeholder="python, java, javascript")
                    resume_score = st.slider("Resume Score", min_value=0, max_value=100, value=50)
                
                submit_button = st.form_submit_button("Add Candidate")
                
                if submit_button:
                    if not (first_name and last_name and email):
                        st.error("First name, last name, and email are required fields")
                    else:
                        # Convert skills to list
                        skills = [skill.strip() for skill in skills_input.split(',') if skill.strip()]
                        
                        try:
                            add_candidate(
                                first_name=first_name,
                                last_name=last_name,
                                email=email,
                                phone=phone,
                                skills=skills,
                                experience_years=experience_years,
                                education=education,
                                resume_score=resume_score
                            )
                            st.success(f"Successfully added {first_name} {last_name} to the database!")
                        except Exception as e:
                            st.error(f"Error adding candidate: {str(e)}")
            
            # PDF Upload option
            st.markdown("---")
            st.subheader("Or Upload Resume PDF")
            
            uploaded_file = st.file_uploader("Upload a PDF resume to extract candidate info", type="pdf")
            
            if uploaded_file:
                try:
                    with st.spinner("Extracting information from PDF..."):
                        pdf_text = extract_resume_info_from_pdf(uploaded_file)
                        
                        if not pdf_text:
                            st.error("Could not extract text from PDF. Please ensure it's a text-based PDF.")
                        else:
                            # Extract resume info
                            resume_info = extract_resume_info(pdf_text)
                            
                            # Extract experience with better handling
                            experience_data = resume_info.get('experience', {'work_experiences': [], 'total_years': 0})
                            experience_years = experience_data.get('total_years', 0)
                            
                            # Get education info
                            education_entries = resume_info.get('education', [])
                            education_formatted = []
                            for entry in education_entries:
                                degree = entry.get('degree', '')
                                university = entry.get('university', '')
                                field = entry.get('field', '')
                                dates = entry.get('dates', '')
                                
                                edu_parts = []
                                if degree:
                                    edu_parts.append(degree)
                                if field:
                                    edu_parts.append(f"in {field}")
                                if university:
                                    edu_parts.append(f"from {university}")
                                if dates:
                                    edu_parts.append(f"({dates})")
                                
                                if edu_parts:
                                    education_formatted.append(" ".join(edu_parts))
                
                            # If no structured education found, use the backup
                            if not education_formatted:
                                education_formatted = extract_education_from_resume(pdf_text)
        
                            # Calculate resume score
                            score_components = calculate_resume_score(resume_info)
                            score = sum(score_components.values())
        
                            # Display extracted info
                            st.success("Successfully extracted information from PDF!")
                            
                            # Create tabs for different sections of info
                            info_tab1, info_tab2, info_tab3 = st.tabs(["📋 Basic Info", "🎓 Education & Experience", "🛠️ Skills & Score"])
                            
                            with info_tab1:
                                # Basic info with better display
                                st.subheader("Contact Information")
                                
                                # Display name more prominently
                                first_name = resume_info.get('first_name', '')
                                last_name = resume_info.get('last_name', '')
                                full_name = f"{first_name} {last_name}".strip()
                                
                                if full_name:
                                    st.markdown(f"### {full_name}")
                                else:
                                    st.markdown("### Unknown Name")
                                    st.info("Could not extract name from resume. Please enter manually.")
                                
                                # Display contact info with better formatting
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    email = resume_info.get('email', '')
                                    if email:
                                        st.markdown(f"📧 **Email:** {email}")
                                    else:
                                        st.markdown("📧 **Email:** Not found")
                                
                                with col2:
                                    phone = resume_info.get('phone', '')
                                    if phone:
                                        st.markdown(f"📱 **Phone:** {phone}")
                                    else:
                                        st.markdown("📱 **Phone:** Not found")
                            
                            with info_tab2:
                                # Education info
                                st.subheader("Education")
                                if education_formatted:
                                    for i, edu in enumerate(education_formatted):
                                        st.markdown(f"🎓 {edu}")
                                else:
                                    st.info("No education information detected in the resume")
                                
                                # Experience info
                                st.subheader("Work Experience")
                                experiences = experience_data.get('work_experiences', [])
                                
                                if experiences:
                                    st.markdown(f"💼 **Total Experience:** {experience_years} years")
                                    
                                    for exp in experiences:
                                        title = exp.get('title', 'Position not specified')
                                        company = exp.get('company', '')
                                        dates = exp.get('dates', '')
                                        
                                        exp_header = title
                                        if company:
                                            exp_header += f" at {company}"
                                        
                                        st.markdown(f"**{exp_header}**")
                                        if dates:
                                            st.markdown(f"*{dates}*")
                                else:
                                    st.info("No detailed work experience detected in the resume")
                            
                            with info_tab3:
                                # Skills section with visual representation
                                st.subheader("Skills")
                                skills = resume_info.get('skills', [])
                                
                                if skills:
                                    cols = st.columns([1, 1, 1, 1, 1])
                                    for i, skill in enumerate(skills):
                                        if skill:
                                            col_index = i % 5
                                            cols[col_index].button(skill, key=f"pdf_skill_{i}", disabled=True)
                                else:
                                    st.info("No skills detected in the resume")
                                
                                # Score visualization
                                st.subheader("Resume Score")
                                
                                # Create a visual score gauge
                                score_color = "#4CAF50" if score >= 80 else "#FFC107" if score >= 50 else "#F44336"
                                
                                st.metric("Resume Score", score)
                                
                                # Show score breakdown
                                st.markdown("#### Score Breakdown")
                                for category, points in score_components.items():
                                    st.markdown(f"- **{category}:** {points} points")
                
                except Exception as e:
                    st.error(f"Error processing PDF: {str(e)}")
                # Add form to edit extracted info
                st.markdown("---")
                st.subheader("Edit and Add to Database")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    first_name_input = st.text_input("First Name", value=resume_info.get('first_name', ''))
                    last_name_input = st.text_input("Last Name", value=resume_info.get('last_name', ''))
                    email_input = st.text_input("Email", value=resume_info.get('email', ''))
                    phone_input = st.text_input("Phone", value=resume_info.get('phone', ''))
                
                with col2:
                    experience_years_input = st.number_input("Years of Experience", 
                                                          min_value=0, max_value=50, 
                                                          value=experience_years)
                    
                    # Join education entries for editing
                    education_text = ", ".join(education_formatted) if education_formatted else ""
                    education_input = st.text_input("Education", value=education_text)
                    
                    # Join skills for editing
                    skills_text = ", ".join(resume_info.get('skills', []))
                    skills_input = st.text_area("Skills (comma separated)", value=skills_text)
                    
                    score_input = st.slider("Resume Score", min_value=0, max_value=100, value=score)
                
                # Add to database button
                if st.button("Add candidate to database"):
                    try:
                        # Parse skills back to list
                        skills_list = [skill.strip() for skill in skills_input.split(',') if skill.strip()]
                        
                        add_candidate(
                            first_name=first_name_input,
                            last_name=last_name_input,
                            email=email_input,
                            phone=phone_input,
                            skills=skills_list,
                            experience_years=experience_years_input,
                            education=education_input,
                            resume_score=score_input
                        )
                        st.success("Successfully added candidate to database!")
                    except Exception as e:
                        st.error(f"Error adding candidate: {str(e)}")
        
        # Analytics tab (existing code)
        with tab4:
            st.subheader("Candidate Analytics")
            
            # Get all candidates for analysis
            all_candidates = get_all_candidates()
            
            if not all_candidates:
                st.info("No candidates in the database yet. Add some candidates to see analytics.")
            else:
                # Display overall statistics
                st.subheader("📊 Overall Statistics")
                
                # Calculate statistics
                total_candidates = len(all_candidates)
                avg_score = sum(c.get('resume_score', 0) for c in all_candidates) / total_candidates if total_candidates else 0
                avg_experience = sum(c.get('experience_years', 0) for c in all_candidates) / total_candidates if total_candidates else 0
                
                # Display stats in columns
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Candidates", total_candidates)
                
                with col2:
                    st.metric("Avg. Resume Score", f"{avg_score:.1f}")
                
                with col3:
                    st.metric("Avg. Experience", f"{avg_experience:.1f} years")
                
                with col4:
                    # Count high performers (score >= 80)
                    high_performers = sum(1 for c in all_candidates if c.get('resume_score', 0) >= 80)
                    st.metric("High Performers", high_performers)
                
                # Convert to pandas DataFrame for easier analysis
                df = pd.DataFrame(all_candidates)
                
                # Add experience categories
                def categorize_experience(years):
                    if years < 2:
                        return "Junior (0-2 years)"
                    elif years < 5:
                        return "Mid-level (2-5 years)"
                    elif years < 10:
                        return "Senior (5-10 years)"
                    else:
                        return "Expert (10+ years)"
                
                if 'experience_years' in df.columns:
                    df['experience_category'] = df['experience_years'].apply(categorize_experience)
                
                # Add score categories
                def categorize_score(score):
                    if score < 50:
                        return "Low (0-49)"
                    elif score < 70:
                        return "Medium (50-69)"
                    elif score < 90:
                        return "High (70-89)"
                    else:
                        return "Excellent (90+)"
                
                if 'resume_score' in df.columns:
                    df['score_category'] = df['resume_score'].apply(categorize_score)
                
                # Create visualizations
                analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs(["📊 Score Analysis", "💼 Experience", "🛠️ Skills Distribution"])
                
                with analysis_tab1:
                    st.subheader("Resume Score Distribution")
                    
                    if 'resume_score' in df.columns:
                        # Score histogram
                        fig = px.histogram(
                            df, 
                            x='resume_score',
                            nbins=10,
                            color_discrete_sequence=['#1E88E5'],
                            labels={'resume_score': 'Resume Score', 'count': 'Number of Candidates'},
                            title='Distribution of Resume Scores'
                        )
                        fig.update_layout(bargap=0.1)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Score by category pie chart
                        if 'score_category' in df.columns:
                            score_counts = df['score_category'].value_counts().reset_index()
                            score_counts.columns = ['Score Category', 'Count']
                            
                            fig_pie = px.pie(
                                score_counts, 
                                values='Count', 
                                names='Score Category',
                                color='Score Category',
                                color_discrete_map={
                                    'Low (0-49)': '#F44336',
                                    'Medium (50-69)': '#FFC107', 
                                    'High (70-89)': '#4CAF50',
                                    'Excellent (90+)': '#2196F3'
                                },
                                title='Candidates by Score Category'
                            )
                            st.plotly_chart(fig_pie, use_container_width=True)
                
                with analysis_tab2:
                    st.subheader("Experience Analysis")
                    
                    if 'experience_years' in df.columns:
                        # Experience distribution
                        fig = px.histogram(
                            df, 
                            x='experience_years',
                            nbins=10,
                            color_discrete_sequence=['#4CAF50'],
                            labels={'experience_years': 'Years of Experience', 'count': 'Number of Candidates'},
                            title='Distribution of Experience Years'
                        )
                        fig.update_layout(bargap=0.1)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Experience vs Score scatter plot
                        if 'resume_score' in df.columns:
                            fig_scatter = px.scatter(
                                df,
                                x='experience_years',
                                y='resume_score',
                                color='score_category' if 'score_category' in df.columns else None,
                                color_discrete_map={
                                    'Low (0-49)': '#F44336',
                                    'Medium (50-69)': '#FFC107', 
                                    'High (70-89)': '#4CAF50',
                                    'Excellent (90+)': '#2196F3'
                                },
                                size=[20] * len(df),  # Consistent point size
                                labels={
                                    'experience_years': 'Years of Experience',
                                    'resume_score': 'Resume Score',
                                    'score_category': 'Score Category'
                                },
                                title='Experience vs. Resume Score'
                            )
                            st.plotly_chart(fig_scatter, use_container_width=True)
                        
                        # Experience categories pie chart
                        if 'experience_category' in df.columns:
                            exp_counts = df['experience_category'].value_counts().reset_index()
                            exp_counts.columns = ['Experience Level', 'Count']
                            
                            fig_pie = px.pie(
                                exp_counts, 
                                values='Count', 
                                names='Experience Level',
                                title='Candidates by Experience Level'
                            )
                            st.plotly_chart(fig_pie, use_container_width=True)
                
                with analysis_tab3:
                    st.subheader("Skills Analysis")
                    
                    # Extract and count skills across all candidates
                    all_skills = {}
                    for candidate in all_candidates:
                        skills = candidate.get('skills', [])
                        for skill in skills:
                            if skill:
                                all_skills[skill.lower()] = all_skills.get(skill.lower(), 0) + 1
                    
                    if all_skills:
                        # Sort skills by frequency
                        sorted_skills = sorted(all_skills.items(), key=lambda x: x[1], reverse=True)
                        
                        # Create a DataFrame for visualization
                        skills_df = pd.DataFrame(sorted_skills, columns=['Skill', 'Count'])
                        
                        # Show top 20 skills
                        top_skills = skills_df.head(20)
                        
                        # Create bar chart of top skills
                        fig = px.bar(
                            top_skills,
                            x='Count',
                            y='Skill',
                            orientation='h',
                            color='Count',
                            color_continuous_scale='Viridis',
                            title='Top 20 Skills in Candidate Pool',
                            labels={'Count': 'Number of Candidates', 'Skill': ''}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Create a word cloud of skills (if matplotlib is available)
                        try:
                            from matplotlib import pyplot as plt
                            from wordcloud import WordCloud
                            
                            # Generate word cloud
                            skill_freq = {skill: count for skill, count in all_skills.items()}
                            
                            # Word cloud settings
                            wc = WordCloud(
                                background_color='white',
                                max_words=100,
                                width=800,
                                height=400,
                                colormap='viridis',
                                contour_width=1,
                                contour_color='steelblue'
                            )
                            
                            # Generate the word cloud
                            wc.generate_from_frequencies(skill_freq)
                            
                            # Display the word cloud
                            fig, ax = plt.subplots(figsize=(10, 5))
                            ax.imshow(wc, interpolation='bilinear')
                            ax.axis('off')
                            st.pyplot(fig)
                        except ImportError:
                            st.info("Install WordCloud and matplotlib for additional skill visualizations.")
                    else:
                        st.info("No skills data available for analysis.")
                
                # Additional analysis options
                st.markdown("---")
                st.subheader("Custom Analysis")
                
                # Let user select analysis dimensions
                custom_col1, custom_col2 = st.columns(2)
                with custom_col1:
                    if df.shape[0] > 0:
                        numeric_cols = [col for col in df.columns if df[col].dtype in ['int64', 'float64']]
                        if numeric_cols:
                            x_axis = st.selectbox("X-axis", options=numeric_cols, index=0)
                            chart_type = st.radio("Chart type", ["Bar", "Line", "Scatter"])
                
                with custom_col2:
                    if df.shape[0] > 0 and 'x_axis' in locals():
                        y_axis = st.selectbox("Y-axis (for scatter)", options=[None] + numeric_cols, index=0)
                        color_by = st.selectbox("Color by", options=[None, 'score_category', 'experience_category'], index=0)
                
                # Generate the custom chart based on user selection
                if df.shape[0] > 0 and 'x_axis' in locals() and 'chart_type' in locals():
                    st.subheader(f"Custom Chart: {x_axis}")
                    
                    if chart_type == "Bar":
                        custom_fig = px.bar(
                            df, 
                            x=x_axis,
                            color=color_by,
                            title=f'Distribution of {x_axis}'
                        )
                        st.plotly_chart(custom_fig, use_container_width=True)
                    
                    elif chart_type == "Line":
                        # For line charts, we need to aggregate data
                        grouped = df.groupby(x_axis).size().reset_index(name='count')
                        custom_fig = px.line(
                            grouped, 
                            x=x_axis, 
                            y='count',
                            title=f'Trend of {x_axis}'
                        )
                        st.plotly_chart(custom_fig, use_container_width=True)
                    
                    elif chart_type == "Scatter" and y_axis:
                        custom_fig = px.scatter(
                            df,
                            x=x_axis,
                            y=y_axis,
                            color=color_by,
                            title=f'{y_axis} vs {x_axis}'
                        )
                        st.plotly_chart(custom_fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error in Recruiters module: {str(e)}")
