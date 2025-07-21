import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import re
import sqlite3
from contextlib import contextmanager
from utils.settings_manager import SettingsManager
from datetime import datetime
from dateutil.relativedelta import relativedelta
from resume_parser import extract_resume_info_from_pdf, extract_contact_number_from_resume, extract_education_from_resume, \
    extract_experience, suggest_skills_for_job, show_colored_skills, calculate_resume_score, extract_resume_info
import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading 'en_core_web_sm' model...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Function to create a table for PDFs in SQLite database if it doesn't exist
def create_table():
    conn = sqlite3.connect('data/user_pdfs.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_uploaded_pdfs (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            data BLOB NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = sqlite3.connect('data/user_pdfs.db')
        yield conn
    finally:
        if conn:
            conn.close()

# Function to insert PDF into the SQLite database
def insert_pdf(name, data):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO user_uploaded_pdfs (name, data) VALUES (?, ?)', (name, data))
        conn.commit()

def extract_date_range(text):
    """Extract date ranges from text using improved regex patterns"""
    # Pattern for various date formats
    date_pattern = r'(?:(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.,]?\s+\d{4})\s*(?:–|-|to)\s*(?:(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.,]?\s+\d{4}|Present|Current)'
    
    date_ranges = re.finditer(date_pattern, text, re.IGNORECASE)
    return [match.group(0) for match in date_ranges]

def calculate_experience_duration(date_range):
    """Calculate experience duration with improved handling of 'Present' dates"""
    try:
        # Split the date range into start and end dates
        if '–' in date_range:
            start_str, end_str = date_range.split('–')
        elif '-' in date_range:
            start_str, end_str = date_range.split('-')
        elif 'to' in date_range.lower():
            start_str, end_str = date_range.lower().split('to')
        else:
            return 0, 0

        # Clean up the date strings
        start_str = start_str.strip()
        end_str = end_str.strip()

        # Handle 'Present' or 'Current' in end date
        if 'present' in end_str.lower() or 'current' in end_str.lower():
            end_date = datetime.now()
        else:
            end_date = datetime.strptime(end_str, '%B %Y')

        # Convert start date
        start_date = datetime.strptime(start_str, '%B %Y')

        # Check if dates are valid
        if end_date < start_date:
            return 0, 0

        # Calculate the difference
        diff = relativedelta(end_date, start_date)
        return diff.years, diff.months

    except Exception as e:
        print(f"Error parsing date range {date_range}: {str(e)}")
        return 0, 0

def extract_work_experience(text):
    """Enhanced work experience extraction focusing only on Professional Experience section"""
    try:
        nlp = spacy.load("en_core_web_sm")
    except:
        st.error("Please install spacy model: python -m spacy download en_core_web_sm")
        return None

    # Convert text to string if it's a spaCy Doc object
    if hasattr(text, 'text'):
        text = text.text
    elif not isinstance(text, str):
        text = str(text)

    # Extract Professional Experience section
    experience_pattern = r'PROFESSIONAL EXPERIENCE.*?(?=\n\n[A-Z\s]+:|\Z)'
    experience_match = re.search(experience_pattern, text, re.DOTALL | re.IGNORECASE)
    
    if not experience_match:
        return None
        
    # Get only the professional experience text
    experience_text = experience_match.group(0)
    
    # Process text with spaCy
    doc = nlp(experience_text)
    experience_data = {
        'total_years': 0,
        'total_months': 0,
        'positions': [],
        'companies': [],
        'experience_details': [],
        'seniority': 'entry'
    }
    
    # Extract date ranges only from professional experience section
    date_ranges = extract_date_range(experience_text)
    total_months = 0
    
    # Calculate total experience
    for date_range in date_ranges:
        years, months = calculate_experience_duration(date_range)
        total_months += (years * 12) + months
    
    # Convert total months to years and remaining months
    total_years = total_months // 12
    remaining_months = total_months % 12
    
    experience_data['total_years'] = total_years
    experience_data['total_months'] = remaining_months
    
    # Extract companies and positions from professional experience section
    company_titles = []
    for ent in doc.ents:
        if ent.label_ == "ORG":
            experience_data['companies'].append(ent.text)
        elif ent.label_ == "TITLE" or any(term in ent.text.lower() for term in ['engineer', 'developer', 'manager']):
            company_titles.append(ent.text)
    
    # Filter out duplicates and add to positions
    experience_data['positions'] = list(set(company_titles))
    
    # Determine seniority level based on professional experience only
    total_experience_years = total_years + (remaining_months / 12)
    if total_experience_years >= 5 or any(term in experience_text.lower() for term in {'senior', 'lead', 'manager', 'director'}):
        experience_data['seniority'] = 'senior'
    elif total_experience_years >= 2 or any(term in experience_text.lower() for term in {'mid-level', 'intermediate'}):
        experience_data['seniority'] = 'mid'
    
    return experience_data

def extract_achievements(text):
    """Extract achievements, honors, and awards from resume text"""
    try:
        # Extract Honors and Awards section
        honors_pattern = r'(?:HONORS|AWARDS|ACHIEVEMENTS|HONORS AND AWARDS|HONORS & AWARDS).*?(?=\n\n[A-Z\s]+:|\Z)'
        honors_match = re.search(honors_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if not honors_match:
            return []
        
        honors_text = honors_match.group(0)
        
        # Split into individual achievements
        achievements = []
        for line in honors_text.split('\n'):
            # Remove bullet points and whitespace
            line = re.sub(r'^[•●⚫⭐▪■]\s*', '', line.strip())
            if line and not line.lower().startswith(('honor', 'award')):
                achievements.append(line)
        
        return achievements
    except Exception as e:
        print(f"Error extracting achievements: {str(e)}")
        return []

def calculate_score_components(resume_info, experience_info, education_info, pdf_text=None):
    """Calculate score components using NLP/NER enhanced extraction"""
    components = {
        'Skills': 0,
        'Experience': 0,
        'Education': 0,
        'Achievements': 0
    }
    
    try:
        nlp = spacy.load("en_core_web_sm")
    except:
        st.error("Please install spacy model: python -m spacy download en_core_web_sm")
        return components

    # Skills score (max 30)
    if resume_info and isinstance(resume_info, dict) and 'skills' in resume_info:
        skills = resume_info.get('skills', [])
        if isinstance(skills, list):
            components['Skills'] = min(len(skills) * 3, 30)

    # Experience score (max 30)
    if experience_info and isinstance(experience_info, dict):
        years = experience_info.get('total_years', 0)
        positions = len(experience_info.get('positions', []))
        seniority = experience_info.get('seniority', 'entry')
        
        years_score = min(years * 3, 15)
        position_score = min(positions * 2, 10)
        seniority_bonus = {'senior': 5, 'mid': 3, 'entry': 1}
        
        components['Experience'] = (
            years_score + 
            position_score + 
            seniority_bonus[seniority]
        )

    # Education score (max 25)
    if education_info and isinstance(education_info, list):
        components['Education'] = min(len(education_info) * 8, 25)

    # Achievements score (max 15)
    if pdf_text and isinstance(pdf_text, str):
        achievements = extract_achievements(pdf_text)
        if achievements:
            components['Achievements'] = min(len(achievements) * 3, 15)

    return components

def display_score_analysis(score_components):
    """Enhanced score visualization with white text"""
    total_score = sum(score_components.values())
    
    # Calculate percentages
    percentages = {k: round((v/total_score)*100, 1) if total_score > 0 else 0 
                  for k, v in score_components.items()}
    
    # Create pie chart with improved visibility
    fig = go.Figure(data=[go.Pie(
        labels=[f"{k}" for k in percentages.keys()],
        values=list(score_components.values()),
        hole=.3,
        marker=dict(
            colors=['#2ECC71', '#3498DB', '#F1C40F', '#E74C3C'],  # Brighter colors
            line=dict(color='#1E1E1E', width=1)  # Dark borders for contrast
        ),
        textinfo='label+percent',
        textposition='outside',
        textfont=dict(
            size=16, 
            color='#FFFFFF',  # White text for labels
            family='Arial'
        ),
        pull=[0.1 if v == max(score_components.values()) else 0 for v in score_components.values()]
    )])
    
    # Update layout with better visibility
    fig.update_layout(
        annotations=[dict(
            text=f"<b>{total_score}%</b>",  # Simplified center text
            x=0.5, y=0.5,
            font=dict(
                size=28,
                color='#FFFFFF',  # White text for total score
                family='Arial Black'
            ),
            showarrow=False
        )],
        width=500,
        height=400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
            font=dict(size=14, color='#FFFFFF'),  # White text for legend
            bgcolor='rgba(0,0,0,0)'  # Transparent legend background
        ),
        margin=dict(t=30, b=90, l=30, r=30),
        paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
        plot_bgcolor='rgba(0,0,0,0)'    # Transparent plot area
    )
    
    return fig, total_score

def display_enhanced_skills(skills):
    """Enhanced skills visualization with categories and ratings"""
    # Skill categories with their respective keywords
    skill_categories = {
        "Programming": ["python", "java", "javascript", "c++", "ruby", "php"],
        "Web Development": ["html", "css", "react", "angular", "node.js", "django"],
        "Database": ["sql", "mysql", "postgresql", "mongodb", "oracle"],
        "DevOps": ["docker", "kubernetes", "aws", "azure", "jenkins", "git"],
        "Data Science": ["machine learning", "tensorflow", "pytorch", "numpy", "pandas"],
        "Other": []
    }

    # Custom CSS for better visualization
    st.markdown("""
        <style>
        .skill-category {
            background-color: #1E1E1E;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
        }
        .category-header {
            color: #FFFFFF;
            font-size: 1.1em;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .skill-tag {
            display: inline-block;
            padding: 5px 12px;
            margin: 4px;
            border-radius: 15px;
            font-size: 0.9em;
            color: white;
            background: linear-gradient(135deg, #1E3D59 0%, #2E5E88 100%);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .skill-tag:hover {
            transform: translateY(-2px);
            transition: transform 0.2s;
        }
        .category-icon {
            margin-right: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Categorize skills
    categorized_skills = {cat: [] for cat in skill_categories.keys()}
    for skill in skills:
        skill_lower = skill.lower()
        categorized = False
        for category, keywords in skill_categories.items():
            if any(keyword in skill_lower for keyword in keywords):
                categorized_skills[category].append(skill)
                categorized = True
                break
        if not categorized:
            categorized_skills["Other"].append(skill)

    # Category icons
    category_icons = {
        "Programming": "💻",
        "Web Development": "🌐",
        "Database": "🗄️",
        "DevOps": "⚙️",
        "Data Science": "📊",
        "Other": "🔧"
    }

    # Display categorized skills
    col1, col2 = st.columns(2)
    categories = list(categorized_skills.keys())
    mid_point = len(categories) // 2

    for i, (category, skills_list) in enumerate(categorized_skills.items()):
        if skills_list:  # Only show categories with skills
            with col1 if i < mid_point else col2:
                st.markdown(f"""
                    <div class="skill-category">
                        <div class="category-header">
                            <span>
                                <span class="category-icon">{category_icons[category]}</span>
                                {category}
                            </span>
                            <span style="color: #4CAF50">{len(skills_list)}</span>
                        </div>
                        <div>
                            {"".join([f'<span class="skill-tag">{skill}</span>' for skill in sorted(skills_list)])}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

def process_user_mode():
    """Process user module functionality"""
    # Remove frontend dependency by using st directly
    st.title("Resume Analysis Dashboard")
    
    with st.sidebar:
        st.title("Smart NLP Resume Parser for Users")
        st.subheader("About")
        st.write("This comprehensive resume parsing solution empowers job seekers with advanced NLP capabilities to analyze their resume content, extract key skills and qualifications, and provide actionable insights for resume optimization. Users benefit from automatic extraction of contact information, education history, skills identification, and experience classification to maximize their job application success rates.")
        
        st.markdown("""
        - Resume Content Extraction
        - Skills and Qualifications Analysis
        - Experience Classification
        - Education History Parsing
        - Career Guidance Recommendations
        """)

    # File upload section
    uploaded_file = st.file_uploader("Upload your resume", type="pdf")

    if uploaded_file:
        try:
            with st.spinner("Processing your resume..."):
                # Extract PDF information
                pdf_name = uploaded_file.name
                pdf_data = uploaded_file.getvalue()
                pdf_text = extract_resume_info_from_pdf(uploaded_file)
                
                if not pdf_text:
                    st.error("Could not extract text from the PDF. Please ensure it's a text-based PDF.")
                    return

                # Extract all information at once
                resume_info = extract_resume_info(pdf_text)
                experience_info = extract_work_experience(pdf_text)
                education_info = extract_education_from_resume(pdf_text)
                
                # Calculate scores
                score_components = calculate_score_components(
                    resume_info=resume_info if resume_info else {},
                    experience_info=experience_info if experience_info else {},
                    education_info=education_info if education_info else [],
                    pdf_text=pdf_text
                )
                
                # Display extracted information in organized sections
                st.markdown("## Resume Analysis")
                
                # Basic Information Section
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("📋 Basic Information")
                    if resume_info.get('first_name'):
                        st.write(f"**First Name:** {resume_info['first_name']}")
                    if resume_info.get('last_name'):
                        st.write(f"**Last Name:** {resume_info['last_name']}")
                    if resume_info.get('email'):
                        st.write(f"**Email:** {resume_info['email']}")
                    contact_number = extract_contact_number_from_resume(pdf_text)
                    if contact_number:
                        st.write(f"**Phone:** +{contact_number}")

                with col2:
                    st.subheader("🎓 Education")
                    education_info = extract_education_from_resume(pdf_text)
                    if education_info:
                        for edu in education_info:
                            st.write(f"• {edu}")
                    else:
                        st.info("No education information found")

                # Technical Skills Section
                st.markdown("### 💡 Technical Skills")
                if resume_info and resume_info.get('skills'):
                    display_enhanced_skills(resume_info['skills'])
                else:
                    st.info("No technical skills detected in the resume")

                # Resume Score Analysis
                st.markdown("### 📊 Resume Score Analysis")
                
                if resume_info and isinstance(resume_info, dict):
                    # Get experience info if not already extracted
                    experience_info = extract_work_experience(pdf_text)
                    # Get education info if not already extracted
                    education_info = extract_education_from_resume(pdf_text)
                    
                    # Calculate score components
                    score_components = calculate_score_components(
                        resume_info,
                        experience_info if experience_info else {},
                        education_info if education_info else [],
                        pdf_text
                    )
                    
                    # Create two columns with adjusted ratios
                    score_col1, score_col2 = st.columns([3, 2])
                    
                    # Pie chart in first column
                    with score_col1:
                        fig, total_score = display_score_analysis(score_components)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Component breakdown in second column
                    with score_col2:
                        st.markdown("#### Component Breakdown")
                        st.markdown("<br>", unsafe_allow_html=True)
                        for component, score in score_components.items():
                            component_color = get_component_color(score)
                            st.markdown(f"""
                                <div style="
                                    background-color: #1E1E1E;
                                    padding: 10px;
                                    border-radius: 8px;
                                    margin: 5px 0;
                                    border-left: 5px solid {component_color};
                                ">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="color: #FFFFFF;">{component}</span>
                                        <span style="color: {component_color}; font-weight: bold;">{score}%</span>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        # Add score interpretation
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("**Score Interpretation:**")
                        interpretation_color = get_component_color(total_score)
                        st.markdown(f"""
                            <div style="
                                background-color: #1E1E1E;
                                padding: 15px;
                                border-radius: 8px;
                                margin: 5px 0;
                            ">
                                <div style="color: {interpretation_color}; font-weight: bold; text-align: center; font-size: 1.2em;">
                                    {total_score}% - {get_score_interpretation(total_score)}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                
                # Suggested Skills Section
                st.markdown("### 🎯 Suggested Skills for Career Growth")
                
                # Job role selector with improved styling
                job_roles = [
                    "Software Engineer",
                    "Data Scientist",
                    "Full Stack Developer",
                    "DevOps Engineer",
                    "Machine Learning Engineer",
                    "Cloud Architect",
                    "Business Analyst",
                    "Data Analyst",
                    "Frontend Developer",
                    "Backend Developer"
                ]
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    selected_role = st.selectbox(
                        "Select your target job role:",
                        options=[""] + job_roles,
                        format_func=lambda x: "Select a role" if x == "" else x
                    )
                
                if selected_role:
                    current_skills = set(resume_info.get('skills', []))
                    suggested_skills = suggest_skills_for_job(selected_role)
                    
                    if suggested_skills:
                        missing_skills = set(suggested_skills) - current_skills
                        matching_skills = current_skills.intersection(suggested_skills)
                        
                        # Skills Gap Analysis
                        st.markdown("#### Skills Gap Analysis")
                        stats_col1, stats_col2, stats_col3 = st.columns(3)
                        
                        with stats_col1:
                            st.markdown(f"""
                                <div style="
                                    background-color: #1E1E1E;
                                    padding: 15px;
                                    border-radius: 8px;
                                    text-align: center;
                                ">
                                    <h4 style="color: #4CAF50; margin: 0;">Required Skills</h4>
                                    <p style="color: #FFFFFF; font-size: 24px; margin: 5px;">{len(suggested_skills)}</p>
                                </div>
                            """, unsafe_allow_html=True)
                            
                        with stats_col2:
                            st.markdown(f"""
                                <div style="
                                    background-color: #1E1E1E;
                                    padding: 15px;
                                    border-radius: 8px;
                                    text-align: center;
                                ">
                                    <h4 style="color: #2196F3; margin: 0;">Skills Match</h4>
                                    <p style="color: #FFFFFF; font-size: 24px; margin: 5px;">{len(matching_skills)}</p>
                                </div>
                            """, unsafe_allow_html=True)
                            
                        with stats_col3:
                            st.markdown(f"""
                                <div style="
                                    background-color: #1E1E1E;
                                    padding: 15px;
                                    border-radius: 8px;
                                    text-align: center;
                                ">
                                    <h4 style="color: #FFC107; margin: 0;">Skills to Develop</h4>
                                    <p style="color: #FFFFFF; font-size: 24px; margin: 5px;">{len(missing_skills)}</p>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        # Display Skills Breakdown
                        st.markdown("#### Skills Breakdown")
                        if matching_skills:
                            st.markdown("**🎯 Skills You Have:**")
                            st.markdown(", ".join(f"<span style='background-color: #4CAF50; color: white; padding: 2px 8px; border-radius: 10px; margin: 2px; display: inline-block;'>{skill}</span>" 
                                                for skill in sorted(matching_skills)), unsafe_allow_html=True)
                        
                        if missing_skills:
                            st.markdown("**📚 Skills to Develop:**")
                            st.markdown(", ".join(f"<span style='background-color: #FFC107; color: black; padding: 2px 8px; border-radius: 10px; margin: 2px; display: inline-block;'>{skill}</span>" 
                                                for skill in sorted(missing_skills)), unsafe_allow_html=True)
                            
                            # Learning Resources
                            st.markdown("#### 📘 Learning Resources")
                            st.markdown("""
                                <div style="background-color: #1E1E1E; padding: 15px; border-radius: 8px;">
                                    <p style="color: #FFFFFF;">Recommended platforms to develop missing skills:</p>
                                    <ul style="color: #FFFFFF;">
                                        <li>Coursera - Professional certificates and courses</li>
                                        <li>Udemy - Hands-on practical courses</li>
                                        <li>LinkedIn Learning - Industry-focused training</li>
                                        <li>GitHub - Open source projects</li>
                                    </ul>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.warning("No skill suggestions available for this role.")
        except Exception as e:
            st.error(f"An error occurred while processing your resume: {str(e)}")
            st.info("Please try uploading a different PDF or ensure the current one is properly formatted.")
            st.stop()
    else:
        st.warning("Please upload a PDF resume to begin analysis.")

def get_component_color(score):
    """Return color code based on component score"""
    if score >= 80:
        return "#4CAF50"  # Green for excellent
    elif score >= 60:
        return "#2196F3"  # Blue for good
    elif score >= 40:
        return "#FFC107"  # Yellow for average
    elif score >= 20:
        return "#FF9800"  # Orange for below average
    else:
        return "#F44336"  # Red for poor

# Example usage in other modules
def process_pdf(file):
    settings = SettingsManager()
    max_size = settings.get_setting('parser', 'max_pdf_size')
    enabled_features = settings.get_setting('parser', 'enabled_features')
    deep_parsing = settings.get_setting('parser', 'deep_parsing')
    
    # Use settings in processing logic
    if file.size > max_size * 1024 * 1024:  # Convert MB to bytes
        raise ValueError(f"File size exceeds maximum allowed size of {max_size}MB")

def extract_personal_info(text):
    """Extract personal information using NER and regex patterns"""
    try:
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)
        
        personal_info = {
            'name': '',
            'email': '',
            'phone': '',
            'location': '',
            'linkedin': ''
        }
        
        # Extract email using regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            personal_info['email'] = email_match.group(0)
        
        # Extract phone using regex
        phone_pattern = r'\+\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phone_match = re.search(phone_pattern, text)
        if phone_match:
            personal_info['phone'] = phone_match.group(0)
        
        # Extract LinkedIn URL
        linkedin_pattern = r'(?:linkedin\.com/in/[A-Za-z0-9_-]+)|(?:www\.linkedin\.com/[A-ZaZ0-9_-]+)'
        linkedin_match = re.search(linkedin_pattern, text.lower())
        if linkedin_match:
            personal_info['linkedin'] = linkedin_match.group(0)
        
        # Extract name and location using NER
        for ent in doc.ents:
            if ent.label_ == "PERSON" and not personal_info['name']:
                personal_info['name'] = ent.text
            elif ent.label_ == "GPE" and not personal_info['location']:
                personal_info['location'] = ent.text
        
        return personal_info
    except Exception as e:
        print(f"Error extracting personal information: {str(e)}")
        return None

def extract_education_info(text):
    """Extract education information using NER and pattern matching"""
    try:
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)
        
        education_section = re.search(r'EDUCATION.*?(?=\n\n[A-Z\s]+:|\Z)', text, re.DOTALL | re.IGNORECASE)
        if not education_section:
            return []
            
        education_text = education_section.group(0)
        education_entries = []
        
        # Split into individual entries
        entries = re.split(r'\n\n(?=[A-Z])', education_text)
        
        for entry in entries:
            if not entry.strip():
                continue
                
            edu_entry = {
                'degree': '',
                'university': '',
                'duration': '',
                'gpa': ''
            }
            
            # Extract degree
            degree_patterns = [
                r'(?:Master|Bachelor|PhD|M\.S\.|B\.S\.|B\.Tech|M\.Tech)[^,\n]*',
                r'(?:of|in)\s+[^,\n]*(?:Engineering|Science|Technology|Business|Arts)[^,\n]*'
            ]
            
            for pattern in degree_patterns:
                degree_match = re.search(pattern, entry)
                if degree_match:
                    edu_entry['degree'] = degree_match.group(0).strip()
                    break
            
            # Extract university using NER
            doc = nlp(entry)
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    edu_entry['university'] = ent.text
                    break
            
            # Extract duration
            duration_pattern = r'(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.\s]+\d{4}\s*(?:–|-|to)\s*(?:Present|Current|(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[.\s]+\d{4})'
            duration_match = re.search(duration_pattern, entry)
            if duration_match:
                edu_entry['duration'] = duration_match.group(0)
            
            # Extract GPA
            gpa_pattern = r'(?:GPA|Grade Point Average|CGPA)[:\s]+([0-9.]+)'
            gpa_match = re.search(gpa_pattern, entry)
            if gpa_match:
                edu_entry['gpa'] = gpa_match.group(1)
            
            education_entries.append(edu_entry)
        
        return education_entries
    except Exception as e:
        print(f"Error extracting education information: {str(e)}")
        return []

def get_score_interpretation(score):
    """Return interpretation based on total score"""
    if score >= 80:
        return "Excellent Resume"
    elif score >= 60:
        return "Strong Resume"
    elif score >= 40:
        return "Good Resume - Minor Improvements Needed"
    elif score >= 20:
        return "Needs Improvement"
    else:
        return "Significant Improvements Required"
  
if __name__ == '__main__':
    process_user_mode()