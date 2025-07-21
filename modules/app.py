import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
import google.generativeai as genai
import os
import PyPDF2 as pdf
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def process_matcher_mode():
    # Get API key and configure
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        st.error("Google API key not found. Please create a .env file with GOOGLE_API_KEY")
        st.stop()

    genai.configure(api_key=api_key)

    def get_gemini_response(input_text):
        try:
            # Use the newer gemini-1.5-flash Generative AI model
            model = genai.GenerativeModel('gemini-1.5-flash')
        
            # Set generation config for better results
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
        
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
            ]
        
            response = model.generate_content(
                input_text,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
        
            return response.text
        except Exception as e:
            st.error(f"Error: {str(e)}")
            # If there's an error, try to list available models
            try:
                available_models = genai.list_models()
                model_names = [model.name for model in available_models]
                st.info(f"Available models: {', '.join(model_names)}")
            except:
                st.info("Unable to list available models")
                
            return f"Error generating response: {str(e)}"

    def input_pdf_text(uploaded_file):
        reader = pdf.PdfReader(uploaded_file)
        text = ""
        for page in range(len(reader.pages)):
            page = reader.pages[page]
            text += str(page.extract_text())
        return text

    # Add this helper function at the beginning of your process_matcher_mode function
    def clean_markdown_formatting(text):
        """Remove markdown formatting characters from text."""
        # Remove bold formatting
        text = text.replace('**', '')
        # Remove italic formatting
        text = text.replace('*', '')
        # Remove other markdown formatting if needed
        return text

    # Prompt Template
    input_prompt_template = """
    You are an expert ATS (Application Tracking System) with deep understanding of tech fields including software engineering, data science, data analysis, and big data engineering. 
    Analyze the provided resume against the job description below. The job market is highly competitive, so provide actionable feedback to improve the resume.
    
    Resume: {text}
    Job Description: {jd}
    
    Respond with the following sections using clear headings:
    
    ## JD MATCH
    Provide a percentage match between the resume and job description which should be reasonable.
    
    ## STRENGTH AREAS
    List 3-5 key strengths in the resume that align well with the job description.
    - Strength 1: [detailed explanation]
    - Strength 2: [detailed explanation]
    - Strength 3: [detailed explanation]
    
    ## MISSING KEYWORDS
    List specific technical skills, tools, or qualifications from the job description that are missing in the resume.
    - Keyword 1
    - Keyword 2
    - Keyword 3
    
    ## IMPROVEMENT SUGGESTIONS
    Provide 2-3 specific, actionable suggestions to improve the resume.
    1. [First suggestion with detailed explanation]
    2. [Second suggestion with detailed explanation]
    
    ## PROFILE SUMMARY
    A concise professional summary of the candidate based on their resume. Make sure the response is gender neutral.
    """

    ## streamlit app
    with st.sidebar:
        st.title("Smart ATS Generative AI Parser")
        st.subheader("About")
        st.write("This sophisticated ATS project, developed with Gen AI Gemini 1.5 Flash and Streamlit, seamlessly incorporates advanced features including resume match percentage, keyword analysis to identify missing criteria, and the generation of comprehensive profile summaries, enhancing the efficiency and precision of the candidate evaluation process for discerning talent acquisition professionals.")
    
        st.markdown("""
        - [Streamlit](https://streamlit.io/)
        - [Gemini](https://deepmind.google/technologies/gemini/#introduction)
        - [makersuit API Key](https://makersuite.google.com/)     
        """)
    
        add_vertical_space(5)
    
    st.title("ATS Resume Score Analyzer using Gemini Flash")
    st.text("Improve Your Resume ATS Score Here")
    jd = st.text_area("Paste the Job Description")
    uploaded_file = st.file_uploader("Upload Your Resume", type="pdf", help="Please upload the pdf")

    submit = st.button("Submit")

    if submit:
        if uploaded_file is not None:
            # Extract text from the PDF
            with st.spinner("Extracting text from resume..."):
                text = input_pdf_text(uploaded_file)
            
            # Format the input prompt with extracted text and job description
            formatted_prompt = input_prompt_template.format(text=text, jd=jd)
            
            with st.spinner("Analyzing your resume..."):
                response = get_gemini_response(formatted_prompt)

            # Extract sections using regex patterns
            import re

            # Define patterns to extract each section
            patterns = {
                "match_percentage": r"##\s*JD MATCH\s*(.*?)(?=##|\Z)",
                "strength_areas": r"##\s*STRENGTH AREAS\s*(.*?)(?=##|\Z)",
                "missing_keywords": r"##\s*MISSING KEYWORDS\s*(.*?)(?=##|\Z)",
                "improvement_suggestions": r"##\s*IMPROVEMENT SUGGESTIONS\s*(.*?)(?=##|\Z)",
                "profile_summary": r"##\s*PROFILE SUMMARY\s*(.*?)(?=##|\Z)"
            }

            # Extract content for each section
            sections = {}
            for key, pattern in patterns.items():
                match = re.search(pattern, response, re.DOTALL)
                if match:
                    sections[key] = match.group(1).strip()
                else:
                    sections[key] = "Information not found."

            # Extract match percentage with validation
            match_text = sections.get("match_percentage", "")
            match_percentage = "N/A"
            
            # Only try to extract percentage if both resume and job description are provided
            if uploaded_file and jd.strip():
                percentage_match = re.search(r"(\d+%|\d+\s*%)", match_text)
                if percentage_match:
                    match_percentage = percentage_match.group(1)

            # Create columns for layout
            col1, col2 = st.columns([1, 2])

            # Display match score in col1
            with col1:
                st.markdown(f"""
                <div style="background-color:#1E3D59;padding:15px;border-radius:10px;text-align:center;box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h3 style="color:white;margin-top:0;margin-bottom:8px;font-size:18px;">Match Score</h3>
                    <h1 style="color:{'#7CFC00' if match_percentage != 'N/A' and int(match_percentage.replace('%', '')) > 70 
                               else '#FFD700' if match_percentage != 'N/A' and int(match_percentage.replace('%', '')) > 40 
                               else '#FF6B6B'};
                               margin:0;
                               font-size:38px;
                               text-shadow: 1px 1px 2px rgba(0,0,0,0.2);">
                        {match_percentage if match_percentage != "N/A" else "N/A"}
                    </h1>
                    {f'<p style="color:#FF6B6B;margin:5px 0 0 0;font-size:12px;"></p>' if match_percentage == "N/A" else ''}
                </div>
                """, unsafe_allow_html=True)

            # Now col2 is defined when we use it
            with col2:
                st.markdown("### Professional Profile")
                st.markdown(f"*{sections.get('profile_summary', 'No summary available')}*")

            # Create tabs for the detailed analysis
            tab1, tab2, tab3 = st.tabs(["💪 Strengths", "🎯 Missing Keywords", "📝 Improvement Suggestions"])

            # Strengths Section
            with tab1:
                st.markdown("### Your Key Strengths")
                if not jd.strip():  # Check if job description is empty
                    st.warning("Please enter a job description to see the strengths.")
                else:
                    strength_text = sections.get("strength_areas", "")
                    # Extract bullet points
                    strengths = re.findall(r"- (.+?)(?=\n-|\n\n|\Z)", strength_text, re.DOTALL)
                    
                    # Remove duplicate strengths and clean titles
                    unique_strengths = []
                    seen_strengths = set()
                    for strength in strengths:
                        clean_str = clean_markdown_formatting(strength.strip())
                        # Remove any "Strength X:" prefix that might be in the text
                        clean_str = re.sub(r'^Strength\s+\d+:\s*', '', clean_str, flags=re.IGNORECASE)
                        
                        fingerprint = clean_str[:50]
                        if fingerprint not in seen_strengths:
                            seen_strengths.add(fingerprint)
                            unique_strengths.append(clean_str)
                    
                    if unique_strengths:
                        for i, strength in enumerate(unique_strengths, 1):
                            # Extract the title from the strength text
                            title = strength.split(':', 1)[0] if ':' in strength else strength[:40]
                            
                            # Display the expander with clean title
                            with st.expander(f"#{i}: {title}...", expanded=i == 1):
                                st.markdown(strength)
                    else:
                        st.info("No specific strengths identified.")

            # Keywords Section
            with tab2:
                st.markdown("### Keywords to Add")
                if not jd.strip():  # Check if job description is empty
                    st.warning("Please enter a job description to identify missing keywords.")
                else:
                    keywords_text = sections.get("missing_keywords", "")
                    keywords = re.findall(r"[-•*]\s*([^•\n]+)(?=\n[-•*]|\n\n|\Z)", keywords_text, re.DOTALL)
                    
                    if keywords:
                        keyword_html = ""
                        for keyword in keywords:
                            keyword = clean_markdown_formatting(keyword.strip())
                            if keyword:
                                keyword_html += f'<span style="background-color:#e6f3ff;margin:6px;padding:10px;border-radius:15px;display:inline-block;font-size:14px;box-shadow:0 1px 3px rgba(0,0,0,0.12);color:#333;">🔍 {keyword}</span>'
                        st.markdown(f"<div style='line-height:3.5;padding:10px;'>{keyword_html}</div>", unsafe_allow_html=True)
                    else:
                        st.info("No missing keywords identified.")

            # Suggestions Section
            with tab3:
                st.markdown("### Actionable Suggestions")
                if not jd.strip():  # Check if job description is empty
                    st.warning("Please enter a job description to see improvement suggestions.")
                else:
                    suggestions_text = sections.get("improvement_suggestions", "")
                    suggestions = re.findall(r"\d+\.\s*(.+?)(?=\n\d+\.|\n\n|\Z)", suggestions_text, re.DOTALL)
                    
                    if suggestions:
                        for i, suggestion in enumerate(suggestions, 1):
                            clean_suggestion = clean_markdown_formatting(suggestion.strip())
                            with st.container():
                                st.markdown(f"""
                                <div style="border-left:4px solid #FF7F50;padding-left:15px;margin-bottom:20px;">
                                <h4>Suggestion {i}</h4>
                                <p>{clean_suggestion}</p>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info("No specific improvement suggestions.")

            # Add option to view raw response in case users want to see everything
            with st.expander("View full analysis", expanded=False):
                st.markdown(response)
        else:
            st.error("Please upload a resume PDF and provide a job description.")
    else:
        st.info("Upload your resume and enter a job description, then click Submit.")
        
        # Add spacing before back button
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Add Back to Dashboard button below the info message
        # col1, col2, col3 = st.columns([2, 1, 2])
        # with col2:
        #    if st.button("← Back to Dashboard", key="matcher_back_btn", type="primary"):
        #        st.session_state.current_module = None
        #        st.rerun()

if __name__ == '__main__':
    process_matcher_mode()