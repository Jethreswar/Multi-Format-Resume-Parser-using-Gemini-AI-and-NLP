import re
import fitz as pymupdf_fitz
import streamlit as st
import spacy
import csv
import nltk
from datetime import datetime
import dateparser

# Additional libraries
nltk.download('punkt')

# Load the spaCy model for English
nlp = spacy.load('en_core_web_sm')

def load_keywords(file_path):
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        return set(row[0] for row in reader)

# ----------------------------------Extract Name----------------------------------
def extract_name(doc):
    # First approach: Look for name in the first few lines which is common in resumes
    first_lines = '\n'.join(doc.text.splitlines()[:10])
    first_line_doc = nlp(first_lines)
    
    # Try to find a person entity in the first few lines
    for ent in first_line_doc.ents:
        if ent.label_ == 'PERSON':
            names = ent.text.split()
            if len(names) >= 2:
                # Check for standard title case or ALL CAPS format
                if (all(name.istitle() for name in names) or 
                    all(name.isupper() for name in names)):
                    # Convert to title case if it's in all caps
                    first_name = names[0].title() if names[0].isupper() else names[0]
                    last_name = ' '.join(names[1:]).title() if names[1].isupper() else ' '.join(names[1:])
                    return first_name, last_name
    
    # Second approach: Look for a line that could be a name (standalone proper nouns)
    for line in doc.text.splitlines()[:15]:  # Check first 15 lines
        line = line.strip()
        if 2 <= len(line.split()) <= 4:  # Most names are 2-4 words
            # Check for all caps or title case
            all_title_case = all(word.istitle() for word in line.split())
            all_upper_case = all(word.isupper() for word in line.split())
            
            # Check if the line doesn't contain common resume headers
            not_header = not any(keyword in line.lower() for keyword in ['resume', 'cv', 'curriculum', 'education', 'experience', 'skills', 'email', 'phone', 'address'])
            
            if (all_title_case or all_upper_case) and not_header:
                names = line.split()
                # Convert to title case if it's in all caps
                first_name = names[0].title() if names[0].isupper() else names[0]
                last_name = ' '.join(names[1:]).title() if any(name.isupper() for name in names[1:]) else ' '.join(names[1:])
                return first_name, last_name
    
    # Third approach: Check if there's name after specific keywords
    name_patterns = [
        r"(?i)name\s*:\s*([A-Z][a-z]+ [A-Z][a-z]+)",
        r"^([A-Z][A-Z\s]+)$",  # Match ALL CAPS names
        r"^([A-Z][a-z]+ [A-Z][a-z]+)$"
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, doc.text[:1000])  # Search in first 1000 chars
        if match:
            full_name = match.group(1).strip()
            names = full_name.split()
            if len(names) >= 2:
                # Convert to title case if it's in all caps
                first_name = names[0].title() if names[0].isupper() else names[0]
                last_name = ' '.join(names[1:]).title() if any(name.isupper() for name in names[1:]) else ' '.join(names[1:])
                return first_name, last_name
    
    return "", ""
# --------------------------------------------------------------------------------

# ----------------------------------Extract Email---------------------------------
def extract_email(doc):
    matcher = spacy.matcher.Matcher(nlp.vocab)
    email_pattern = [{'LIKE_EMAIL': True}]
    matcher.add('EMAIL', [email_pattern])

    matches = matcher(doc)
    for match_id, start, end in matches:
        if match_id == nlp.vocab.strings['EMAIL']:
            return doc[start:end].text
    return ""
# --------------------------------------------------------------------------------

# ----------------------------------Extract Ph No---------------------------------
def extract_contact_number_from_resume(doc):
    contact_number = None
    text = doc.text  # Extract text from SpaCy doc object
    pattern = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
    match = re.search(pattern, text)
    if match:
        contact_number = match.group()
    return contact_number
# --------------------------------------------------------------------------------

# --------------------------------Extract Education-------------------------------
def extract_education_from_resume(doc):
    text = doc.text
    
    # Common education section headers
    education_headers = [
        r"EDUCATION", r"Education", r"ACADEMIC BACKGROUND", r"Academic Background",
        r"EDUCATIONAL QUALIFICATIONS", r"Educational Qualifications"
    ]
    
    # Find education section
    education_section = ""
    education_found = False
    
    # Try to find the education section based on headers
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if any(re.search(pattern, line) for pattern in education_headers) or "education" in line.lower():
            education_found = True
            start_idx = i
            
            # Find the end of the education section (next major section)
            for j in range(start_idx + 1, len(lines)):
                if re.match(r"^[A-Z\s]{5,}$", lines[j].strip()) and len(lines[j].strip()) > 5:  # Likely a new section header
                    end_idx = j
                    break
            else:
                end_idx = min(start_idx + 20, len(lines))  # Limit to 20 lines if no clear end
                
            education_section = '\n'.join(lines[start_idx:end_idx])
            break
    
    if not education_found:
        # Look for degree keywords throughout the document
        degree_keywords = [
            r"Bachelor", r"Master", r"PhD", r"B\.S\.", r"M\.S\.", r"B\.A\.", r"M\.A\.",
            r"B\.Tech", r"M\.Tech", r"BSc", r"MSc", r"BCA", r"MCA", r"Diploma",
            r"Certificate", r"Post Graduate", r"Postgraduate"
        ]
        
        degree_lines = []
        for line in lines:
            if any(re.search(f"\\b{keyword}\\b", line, re.IGNORECASE) for keyword in degree_keywords):
                degree_lines.append(line)
        
        education_section = '\n'.join(degree_lines)
    
    # Look for educational institutions
    universities = []
    
    # Common institution words
    institution_words = ["university", "college", "institute", "school", "academy"]
    
    # Process the education section
    education_doc = nlp(education_section) if education_section else doc
    
    # First try to find ORG entities
    for entity in education_doc.ents:
        if entity.label_ == "ORG" and any(word in entity.text.lower() for word in institution_words):
            universities.append(entity.text)
    
    # If no entities found, use regex pattern matching
    if not universities:
        for line in education_section.split('\n') if education_section else text.split('\n'):
            for word in institution_words:
                if word in line.lower():
                    # Try to extract the full institution name
                    universities.append(line.strip())
                    break
    
    # Remove duplicates and filter very short entries (likely false positives)
    universities = [uni for uni in set(universities) if len(uni) > 5]
    
    return universities
# --------------------------------------------------------------------------------

# ----------------------------------Extract Skills--------------------------------
def csv_skills(doc):
    skills_keywords = load_keywords('data/newSkills.csv')
    skills = set()

    for keyword in skills_keywords:
        if keyword.lower() in doc.text.lower():
            skills.add(keyword)

    return skills

nlp_skills = spacy.load('TrainedModel/skills')  # Load the trained NER model for skills

def extract_skills_from_ner(doc):
    non_skill_labels = {'DATE', 'TIME', 'PERCENT', 'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL', 'EMAIL'}
    
    skills = set()
    for ent in nlp_skills(doc.text).ents:
        if ent.label_ == 'SKILL':
            # Check if the entity text is not in the non-skill labels set
            if ent.label_ not in non_skill_labels and not ent.text.isdigit():
                # Filter out non-alphabetic characters
                skill_text = ''.join(filter(str.isalpha, ent.text))
                if skill_text:
                    skills.add(skill_text)
    return skills

def is_valid_skill(skill_text):
    # Define criteria for valid skills (modify/add criteria as needed)
    return len(skill_text) > 1 and not any(char.isdigit() for char in skill_text)

def extract_skills(doc):
    """Extract only technical and professional skills, excluding personal information"""
    skills_csv = csv_skills(doc)
    skills_ner = extract_skills_from_ner(doc)
    
    # Define filters for non-skill content
    non_skill_patterns = {
        r'@',                          # Filter email addresses
        r'\b[A-Z][a-z]+ [A-Z][a-z]+', # Filter full names
        r'University|College|School',   # Filter education institutions
        r'B\.|M\.|PhD|Bachelor|Master', # Filter education degrees
        r'\b\d{10}\b',                # Filter phone numbers
        r'linkedin\.com'              # Filter LinkedIn URLs
    }
    
    # Filter out personal information
    def is_valid_skill(skill):
        if not skill or len(skill) < 2:
            return False
        
        # Check against non-skill patterns
        for pattern in non_skill_patterns:
            if re.search(pattern, skill):
                return False
                
        # Additional validation for technical skills
        return (
            not skill.isdigit() and          # No pure numbers
            not any(char.isdigit() for char in skill) and  # No digits
            not any(char in '.,;:' for char in skill) and  # No punctuation
            skill.strip().lower() not in {'name', 'email', 'phone', 'address', 'education', 'university'}  # Exclude common personal info headers
        )
    
    filtered_skills_csv = {skill for skill in skills_csv if is_valid_skill(skill)}
    filtered_skills_ner = {skill for skill in skills_ner if is_valid_skill(skill)}
    
    # Combine and return only technical and professional skills
    combined_skills = filtered_skills_csv.union(filtered_skills_ner)
    return list(combined_skills)
# --------------------------------------------------------------------------------

# ----------------------------------Extract Major---------------------------------
def extract_major(doc):
    major_keywords = load_keywords('data/majors.csv')

    for keyword in major_keywords:
        if keyword.lower() in doc.text.lower():
            return keyword

    return ""
# --------------------------------------------------------------------------------

# --------------------------------Extract Experience------------------------------
def extract_experience_level(doc):
    """Extracts the level of experience based on the verbs used in the document."""
    verbs = [token.text for token in doc if token.pos_ == 'VERB']

    senior_keywords = ['lead', 'manage', 'direct', 'oversee', 'supervise', 'orchestrate', 'govern']
    mid_senior_keywords = ['develop', 'design', 'analyze', 'implement', 'coordinate', 'execute', 'strategize']
    mid_junior_keywords = ['assist', 'support', 'collaborate', 'participate', 'aid', 'facilitate', 'contribute']
    
    if any(keyword in verbs for keyword in senior_keywords):
        level_of_experience = "Senior"
    elif any(keyword in verbs for keyword in mid_senior_keywords):
        level_of_experience = "Mid-Senior"
    elif any(keyword in verbs for keyword in mid_junior_keywords):
        level_of_experience = "Mid-Junior"
    else:
        level_of_experience = "Entry Level"

    suggested_position = suggest_position(verbs)

    return {
        'level_of_experience': level_of_experience,
        'suggested_position': suggested_position
    }

def parse_date(date_str):
    """
    Parse dates in various formats and return a datetime object.
    Returns None if parsing fails.
    """
    if not date_str or date_str.lower() in ['present', 'current', 'now', 'today']:
        return 'Present'
    
    # Try to parse with dateparser which handles many formats
    try:
        parsed_date = dateparser.parse(date_str.strip())
        if parsed_date:
            return parsed_date
    except:
        pass
    
    return None

def extract_work_experience(doc):
    """
    Enhanced extraction of work experience that better handles different resume formats
    and specifically accounts for the format in Mahad's resume.
    """
    text = doc.text
    lines = text.split('\n')
    
    # Common work experience section headers (expanded to match more variations)
    work_exp_headers = [
        r"WORK EXPERIENCE", r"Work Experience", r"PROFESSIONAL EXPERIENCE", 
        r"Professional Experience", r"EMPLOYMENT HISTORY", r"Employment History",
        r"WORK HISTORY", r"Work History", r"EXPERIENCE", r"Experience",
        r"WORK", r"Work", r"EMPLOYMENT", r"Employment"
    ]
    
    # Find work experience section
    work_exp_section = []
    work_exp_found = False
    start_idx = -1
    end_idx = len(lines)
    
    # Try to find the work experience section based on headers
    for i, line in enumerate(lines):
        if any(re.search(pattern, line) for pattern in work_exp_headers):
            work_exp_found = True
            start_idx = i
            break
    
    # If we found a work experience section
    if work_exp_found and start_idx >= 0:
        # Find where the next section begins (looking for all caps section headers)
        for j in range(start_idx + 1, len(lines)):
            if re.match(r"^[A-Z][A-Z\s]+$", lines[j].strip()) and len(lines[j].strip()) > 3:
                if lines[j].strip() not in ["WORK EXPERIENCE", "EXPERIENCE", "EMPLOYMENT"]:
                    end_idx = j
                    break
        
        # Extract the work experience section
        work_exp_section = lines[start_idx:end_idx]
    
    # If we couldn't find a clear section by header, try to identify job entries directly
    if not work_exp_found or not work_exp_section:
        # Look for job title patterns and date ranges
        job_title_indicators = [
            "Content Writer", "Project Manager", "Manager", "Director", "Engineer",
            "Developer", "Analyst", "Consultant", "Specialist", "CSR", "Voice",
            "Representative", "Coordinator", "Assistant"
        ]
        
        for i, line in enumerate(lines):
            for indicator in job_title_indicators:
                if indicator in line:
                    # Check if there's a date pattern in this line or surrounding lines
                    context_start = max(0, i-3)
                    context_end = min(len(lines), i+4)
                    context = lines[context_start:context_end]
                    
                    if any(re.search(r"\d{2}/\d{4}", line) or 
                           re.search(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)", line) or
                           "Present" in line for line in context):
                        # Found a potential job entry
                        work_exp_section.extend(context)
                        break
    
    # Extract work experiences from the section or the entire document if no section found
    experiences = []
    
    # Use the entire document if no clear work experience section was found
    if not work_exp_section:
        work_exp_section = lines
    
    # Process lines to find position, company and dates
    i = 0
    while i < len(work_exp_section):
        line = work_exp_section[i].strip()
        
        # Look for lines that could be job titles (based on common job title indicators)
        job_title_match = False
        potential_job_titles = [
            "Content Writer", "Project Manager", "CSR-Voice", "Manager", "Director", 
            "Engineer", "Developer", "Analyst", "Consultant", "Specialist"
        ]
        
        for title in potential_job_titles:
            if title in line:
                job_title_match = True
                position = line.strip()
                
                # Company would typically be in the next line
                company = ""
                if i + 1 < len(work_exp_section):
                    company = work_exp_section[i + 1].strip()
                
                # Look for date range in the following lines
                start_date = ""
                end_date = ""
                date_found = False
                
                # Check next few lines for date information
                for j in range(i, min(i + 5, len(work_exp_section))):
                    date_line = work_exp_section[j].strip()
                    
                    # Different date formats we might encounter
                    date_patterns = [
                        r"(\d{2}/\d{4})\s*[-–—]\s*(\d{2}/\d{4}|Present)",
                        r"(\d{2}/\d{4})\s*to\s*(\d{2}/\d{4}|Present)",
                        r"(\d{2}/\d{4})\s+(\d{2}/\d{4}|Present)",
                        r"(\d{2}/\d{4})",
                        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4})\s*[-–—]\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}|Present)",
                        r"(\d{4})\s*[-–—]\s*(\d{4}|Present)",
                    ]
                    
                    for pattern in date_patterns:
                        date_match = re.search(pattern, date_line)
                        if date_match:
                            date_found = True
                            if len(date_match.groups()) >= 2:
                                start_date = date_match.group(1)
                                end_date = date_match.group(2)
                            else:
                                start_date = date_match.group(1)
                                # If only one date found, check if "Present" is in the line
                                if "Present" in date_line:
                                    end_date = "Present"
                                else:
                                    end_date = "Present"  # Default assumption
                            break
                    
                    if date_found:
                        break
                
                # If we found a complete job entry
                if position and (company or date_found):
                    # Parse the dates for calculation
                    start_date_obj = parse_date(start_date)
                    end_date_obj = parse_date(end_date)
                    
                    # Create experience entry
                    experiences.append({
                        'position': position,
                        'company': company,
                        'start_date': start_date,
                        'end_date': end_date,
                        'duration': calculate_duration(start_date_obj, end_date_obj) if start_date_obj and end_date_obj else ""
                    })
                
                # Move past this job entry
                i += 3
                job_title_match = True
                break
        
        if not job_title_match:
            i += 1
    
    # If we still haven't found experiences, try one more approach
    # Looking for lines with specific format in Mahad's resume
    if not experiences:
        for i, line in enumerate(lines):
            # Check for job roles like "Content Writer" followed by company on next line
            if any(title in line for title in potential_job_titles):
                position = line.strip()
                company = ""
                
                # Get company from the next line
                if i + 1 < len(lines) and len(lines[i + 1].strip()) > 0:
                    company = lines[i + 1].strip()
                
                # Look for date pattern in the next line
                date_line = ""
                if i + 2 < len(lines):
                    date_line = lines[i + 2].strip()
                
                start_date = ""
                end_date = "Present"  # Default
                
                # Try to extract dates
                date_match = re.search(r"(\d{2}/\d{4})\s*[-–—]\s*((?:\d{2}/\d{4})|(?:Present))", date_line)
                if date_match:
                    start_date = date_match.group(1)
                    end_date = date_match.group(2)
                else:
                    # Try simpler pattern just looking for MM/YYYY
                    date_match = re.search(r"(\d{2}/\d{4})", date_line)
                    if date_match:
                        start_date = date_match.group(1)
                
                # Create experience entry if we have position and either company or dates
                if position and (company or start_date):
                    # Parse dates
                    start_date_obj = parse_date(start_date) if start_date else None
                    end_date_obj = parse_date(end_date) if end_date else None
                    
                    experiences.append({
                        'position': position,
                        'company': company,
                        'start_date': start_date,
                        'end_date': end_date,
                        'duration': calculate_duration(start_date_obj, end_date_obj) if start_date_obj and end_date_obj else ""
                    })
    
    # Specific handling for Mahad's resume format
    # If we still don't have experiences, let's try looking for consecutive lines with job info
    if not experiences:
        for i in range(len(lines) - 2):
            line1 = lines[i].strip()
            line2 = lines[i+1].strip() if i+1 < len(lines) else ""
            line3 = lines[i+2].strip() if i+2 < len(lines) else ""
            
            # Check if first line looks like a position
            if any(title in line1 for title in potential_job_titles):
                position = line1
                company = line2
                
                # Try to find date in third line or surrounding lines
                date_line = line3
                for j in range(max(0, i-1), min(len(lines), i+5)):
                    potential_date_line = lines[j].strip()
                    if re.search(r"\d{2}/\d{4}", potential_date_line) or "Present" in potential_date_line:
                        date_line = potential_date_line
                        break
                
                start_date = ""
                end_date = "Present"  # Default assumption
                
                # Try different date patterns
                date_patterns = [
                    r"(\d{2}/\d{4})\s*[-–—]\s*(\d{2}/\d{4}|Present)",
                    r"(\d{2}/\d{4})\s*to\s*(\d{2}/\d{4}|Present)",
                    r"(\d{1,2}/\d{4})"  # Just single date
                ]
                
                for pattern in date_patterns:
                    date_match = re.search(pattern, date_line)
                    if date_match:
                        if len(date_match.groups()) >= 2:
                            start_date = date_match.group(1)
                            end_date = date_match.group(2)
                        else:
                            start_date = date_match.group(1)
                        break
                
                if position and (company or start_date):
                    # Parse dates for calculation
                    start_date_obj = parse_date(start_date) if start_date else None
                    end_date_obj = parse_date(end_date) if end_date else None
                    
                    experiences.append({
                        'position': position,
                        'company': company,
                        'start_date': start_date,
                        'end_date': end_date,
                        'duration': calculate_duration(start_date_obj, end_date_obj) if start_date_obj and end_date_obj else ""
                    })
    
    return experiences

def calculate_duration(start_date, end_date):
    """Calculate duration between two dates in months and years"""
    if isinstance(start_date, str) or isinstance(end_date, str):
        return ""
    
    if end_date == 'Present':
        end_date = datetime.now()
    
    delta_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    years = delta_months // 12
    months = delta_months % 12
    
    if years > 0 and months > 0:
        return f"{years} year{'s' if years > 1 else ''}, {months} month{'s' if months > 1 else ''}"
    elif years > 0:
        return f"{years} year{'s' if years > 1 else ''}"
    else:
        return f"{months} month{'s' if months > 1 else ''}"

def extract_experience(doc):
    """Combined function to extract both experience level and work history"""
    experience_level = extract_experience_level(doc)
    work_experiences = extract_work_experience(doc)
    
    return {
        'level_of_experience': experience_level['level_of_experience'],
        'suggested_position': experience_level['suggested_position'],
        'work_experiences': work_experiences
    }
# --------------------------------------------------------------------------------


# -----------------------------------Suggestions----------------------------------
def load_positions_keywords(file_path):
    positions_keywords = {}
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            position = row['position']
            keywords = [keyword.lower()
                        for keyword in row['keywords'].split(',')]
            positions_keywords[position] = keywords
    return positions_keywords


def suggest_position(verbs):
    positions_keywords = load_positions_keywords('data/position.csv')
    verbs = [verb.lower() for verb in verbs]
    for position, keywords in positions_keywords.items():
        if any(keyword in verbs for keyword in keywords):
            return position

    return "Position Not Identified"


def extract_resume_info_from_pdf(uploaded_file):
    doc = pymupdf_fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = ""
    for page_num in range(doc.page_count):
        page = doc[page_num]
        text += page.get_text()
    return nlp(text)


def show_colored_skills(skills):
    st.write(', '.join(skills))


def calculate_resume_score(resume_info):
    score = 0
    if resume_info['first_name'] and resume_info['last_name']:
        score += 25
    if resume_info['email']:
        score += 25
    if resume_info['degree_major']:
        score += 25
    if resume_info['skills']:
        score += 25
    return score


def extract_resume_info(doc):
    first_name, last_name = extract_name(doc)
    email = extract_email(doc)
    skills = extract_skills(doc)
    degree_major = extract_major(doc)
    experience = extract_experience(doc)
    education = extract_education_from_resume(doc)

    return {
        'first_name': first_name, 
        'last_name': last_name, 
        'email': email, 
        'degree_major': degree_major, 
        'skills': skills, 
        'experience': experience,
        'education': education
    }


def suggest_skills_for_job(desired_job):
    # Predefined skills mapping for key roles using existing NER/NLP datasets
    specialized_skills = {
        "full stack developer": [
            "JavaScript", "React.js", "Node.js", "Python", "Django",
            "HTML5", "CSS3", "MongoDB", "PostgreSQL", "RESTful APIs",
            "Git", "Docker", "AWS", "TypeScript", "GraphQL",
            "Redux", "Express.js", "SQL", "Bootstrap", "Webpack"
        ],
        "cloud architect": [
            "AWS", "Azure", "Google Cloud", "Kubernetes", "Docker",
            "Terraform", "CloudFormation", "Microservices", "Jenkins",
            "Python", "Linux", "CI/CD", "Security", "Networking",
            "Load Balancing", "Scalability", "Cloud Security"
        ],
        "machine learning engineer": [
            "Python", "TensorFlow", "PyTorch", "Scikit-learn", "Pandas",
            "NumPy", "Deep Learning", "NLP", "Computer Vision", "SQL",
            "Machine Learning Algorithms", "Data Preprocessing", "Neural Networks",
            "Model Deployment", "MLOps", "Statistics"
        ]
    }
    
    # First check specialized roles
    desired_job_lower = desired_job.lower()
    if desired_job_lower in specialized_skills:
        return specialized_skills[desired_job_lower]
        
    # If not in specialized roles, check CSV file for other roles
    job_skills_mapping = {}
    try:
        with open('data/suggestedSkills.csv', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                job_title = row[0].lower()
                skills = row[1:]
                job_skills_mapping[job_title] = skills
        
        if desired_job_lower in job_skills_mapping:
            return job_skills_mapping[desired_job_lower]
    except Exception as e:
        print(f"Error reading skills CSV: {str(e)}")
    
    return []