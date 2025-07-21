import streamlit as st
from streamlit_option_menu import option_menu
import time
import hashlib
import os
import sys  # Add this import
from pathlib import Path

# This must be the first Streamlit command
st.set_page_config(
    page_title="Resume Parser",
    page_icon="✅",
    layout="wide"
)

# Initialize session state variables
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ''
if 'current_module' not in st.session_state:
    st.session_state.current_module = None
if 'typed_chars' not in st.session_state:
    st.session_state.typed_chars = 0
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()

# Create a CSS-only typing animation that doesn't rely on JavaScript
# This is more compatible with Streamlit's rendering approach
st.markdown("""
    <style>
    .main-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 2rem;
    }
    
    /* Typing animation styling using pure CSS */
    @keyframes typing {
        from { width: 0 }
        to { width: 100% }
    }
    
    @keyframes blink-caret {
        from, to { border-right-color: transparent }
        50% { border-right-color: #4CAF50 }
    }
    
    .typing-header {
        text-align: center;
        padding: 1rem;
        color: #FFFFFF;
        margin-bottom: 1.5rem;
        overflow: hidden;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .typing-text {
        display: inline-block;
        overflow: hidden;
        white-space: nowrap;
        font-size: 2.2rem;
        font-weight: 600;
        border-right: 3px solid transparent;  /* Start with transparent border */
        width: 0;
        animation: 
            typing 3.5s steps(40, end) forwards,
            blink-caret 0.75s step-end infinite;
        animation-delay: 0s, 3.5s;  /* Start blinking after typing completes */
        padding-right: 3px;  /* Add padding for cursor */
    }
    
    .welcome-text {
        text-align: center;
        color: #CCCCCC;
        margin-bottom: 2rem;
        font-size: 1.1em;
        max-width: 600px;
        margin: 0 auto;
    }
    .features-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
        margin-bottom: 2rem;
    }
    .feature-card {
        background-color: #1E1E1E;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        color: #FFFFFF;
        transition: transform 0.2s;
    }
    .feature-card:hover {
        transform: translateY(-5px);
    }
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        color: #4CAF50;
    }
    /* Style for login section without container */
    .login-section {
        max-width: 250px;
        margin: 2rem auto;
        text-align: center;
    }
    .login-title {
        color: #FFFFFF;
        font-size: 1.1em;
        margin-bottom: 1.2rem;
        text-align: center;
        font-weight: 500;
    }
    .credentials-info {
        text-align: center;
        color: #666666;
        margin-top: 1rem;
        font-size: 0.75em;
        padding: 0.4rem;
        background-color: #2C2C2C;
        border-radius: 5px;
        max-width: 250px;
        margin-left: auto;
        margin-right: auto;
    }
    /* Style for input fields */
    .custom-input {
        margin-bottom: 0.7rem;
    }
    .custom-input div[data-baseweb="input"] {
        width: 100%;
        max-width: 250px;
        margin: 0 auto;
    }
    .custom-input input {
        padding: 0.2rem 0.4rem !important;
        font-size: 0.8em !important;
        height: 1.6rem !important;
        border-radius: 4px !important;
        background-color: #252525 !important;
    }
    /* Style for login button */
    .login-button {
        margin-top: 0.8rem;
        margin-bottom: 1rem;
        display: flex;
        justify-content: center;
        width: 100%;
        text-align: center;
    }
    .login-button button {
        padding: 0 1rem !important;
        font-size: 0.8em !important;
        height: 1.6rem !important;
        width: auto !important;
        min-width: 100px !important;
        margin: 0 auto !important;
    }
    /* Copyright text */
    .copyright {
        text-align: center;
        color: #666666;
        font-size: 0.7em;
        padding: 0.8rem;
        margin-top: 2rem;
        position: fixed;
        z-index: 999;
        bottom: 0;
        width: 100%;
        left: 0;
        background-color: #121212;
    }
    /* Enhanced Module Card Styles */
    .module-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
        max-width: 900px;
        margin: 2rem auto;
    }
    
    /* Interactive Card Styling */
    .clickable-card {
        background-color: #1E1E1E;
        border-radius: 12px;
        padding: 1.8rem 1.2rem;
        height: 180px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: space-between;
        transition: all 0.2s ease;
        cursor: pointer;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        position: relative;
        overflow: hidden;
        margin-bottom: -35px; /* To compensate for the button height */
        z-index: 1;
    }
    
    /* Hide the button text but keep the button clickable */
    .clickable-overlay button {
        opacity: 0 !important;
        height: 30px !important;
        min-height: 0 !important;
        padding: 0 !important;
        margin-top: -10px !important;
        z-index: 10;
    }
    
    /* Make the button span the entire card */
    .clickable-overlay {
        position: relative;
        z-index: 5;
        height: 30px;
    }
    
    .clickable-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        background-color: #262626;
    }
    
    .clickable-card:active {
        transform: translateY(-2px);
        background-color: #2d2d2d;
    }
    
    .clickable-card::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, #4CAF50, #8BC34A);
        transform: scaleX(0);
        transition: transform 0.2s ease;
        transform-origin: bottom right;
    }
    
    .clickable-card:hover::after {
        transform: scaleX(1);
        transform-origin: bottom left;
    }
    
    .module-icon {
        font-size: 2.6rem;
        margin-bottom: 1rem;
        color: #4CAF50;
        text-shadow: 0 0 10px rgba(76, 175, 80, 0.3);
        transition: transform 0.2s ease;
    }
    
    .clickable-card:hover .module-icon {
        transform: scale(1.1);
    }
    
    .module-title {
        font-size: 1.1rem;
        color: #FFFFFF;
        margin-bottom: 0.6rem;
        font-weight: 500;
        text-align: center;
        transition: color 0.2s ease;
    }
    
    .clickable-card:hover .module-title {
        color: #8BC34A;
    }
    
    .module-desc {
        color: #CCCCCC;
        font-size: 0.85rem;
        text-align: center;
        line-height: 1.3;
        max-width: 100%;
        transition: color 0.2s ease;
    }
    
    .clickable-card:hover .module-desc {
        color: #E0E0E0;
    }
    
    /* Global button styling */
    .stButton > button {
        background-color: #4CAF50 !important;
        color: white !important;
        padding: 0.5rem 2rem !important;
        font-size: 0.9em !important;
        border-radius: 5px !important;
        border: none !important;
        cursor: pointer !important;
        transition: all 0.3s !important;
        display: inline-block !important;
        width: auto !important;
        min-width: 120px !important;
    }
    
    /* Center the login button container */
    .stButton {
        display: flex;
        justify-content: center;
        text-align: center;
    }
    
    .stButton > button:hover {
        background-color: #45a049 !important;
        transform: translateY(-2px);
    }
    
    /* Card hover effect optimization */
    @media (pointer: fine) {
        .clickable-card {
            transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), 
                        box-shadow 0.2s cubic-bezier(0.34, 1.56, 0.64, 1),
                        background-color 0.2s ease;
        }
        
        .clickable-card:hover {
            transform: translateY(-6px);
            box-shadow: 0 12px 24px rgba(0,0,0,0.25);
        }
        
        .clickable-card::after {
            transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        
        .module-icon, .module-title, .module-desc {
            transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

def hash_password(password):
    """Create a hashed version of password"""
    return hashlib.sha256(password.encode()).hexdigest()

def load_user_credentials():
    """Load user credentials from a secure source
    In a production environment, this would be a database or secure storage
    For demo purposes, we're using a simple dictionary
    """
    # Demo credentials with hashed passwords
    # In production, these would be stored in a secure database
    return {
        "admin": hash_password("admin123"),
        "user": hash_password("user123"),
        "recruiter": hash_password("recruiter123")
    }

def authenticate(username, password):
    """Authenticate user with secure password hashing"""
    credentials = load_user_credentials()
    return username in credentials and credentials[username] == hash_password(password)

# Streamlit-friendly approach to simulate typing animation
def animated_text_header():
    """Creates a pure CSS typing animation header"""
    st.markdown("""
        <div class="typing-header">
            <h1 class="typing-text">👋 Welcome to Resume Parsing App...</h1>
        </div>
    """, unsafe_allow_html=True)

def login_page():
    """Display the login page"""
    # Header Section with typing animation
    animated_text_header()
    
    st.markdown("""
        <div class="welcome-text">
            An intelligent resume parsing solution powered by NLP and Machine Learning
        </div>
    """, unsafe_allow_html=True)

    # Features Section
    st.markdown("### 🚀 Key Features")
    st.markdown("""
        <div class="features-grid">
            <div class="feature-card">
                <div class="feature-icon">🎯</div>
                <h3>Smart Analysis</h3>
                <p>Advanced NLP parsing</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">⚡</div>
                <h3>Instant Results</h3>
                <p>Quick insights</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h3>Detailed Reports</h3>
                <p>Visual analytics</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Login Section without container
    col1, login_col, col3 = st.columns([1, 2, 1])
    
    with login_col:
        st.markdown('<div class="login-section">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">Login to Continue</div>', unsafe_allow_html=True)
        
        # Login Fields with custom CSS class for easier styling
        with st.container():
            username = st.text_input("", placeholder="Username", key="username_input", 
                                    label_visibility="collapsed", help="Enter your username")
            st.markdown('<style>.stTextInput:nth-child(1) {margin-bottom: 8px;}</style>', unsafe_allow_html=True)
            
            password = st.text_input("", placeholder="Password", type="password", key="password_input", 
                                    label_visibility="collapsed", help="Enter your password")
        
        # Login button with exact center alignment
        # Create a custom container for the login button to ensure perfect centering
        st.markdown("""
            <style>
            .login-button-container {
                display: flex;
                justify-content: center;
                width: 100%;
                margin-top: 1rem;
                margin-bottom: 1rem;
            }
            </style>
            <div class="login-button-container">
        """, unsafe_allow_html=True)
        
        login_button = st.button("Login", type="primary", key="login_btn")
        
        st.markdown("</div>", unsafe_allow_html=True)

        # Handle login attempt
        if login_button:
            if authenticate(username, password):
                with st.spinner("Logging in..."):
                    time.sleep(0.5)
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.current_module = None
                st.rerun()
            else:
                st.error("Invalid username or password")
        
        st.markdown("""
            <div class="credentials-info">
                Demo Credentials:<br>
                user/user123 | admin/admin123 | recruiter/recruiter123
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Copyright text at bottom of page
    st.markdown("""
        <div class="copyright">
            © 2025 Resume Parser. All rights reserved.
        </div>
    """, unsafe_allow_html=True)

def navigate_to_module(module_name):
    """Function to handle module navigation"""
    st.session_state.current_module = module_name
    st.rerun()

def get_user_modules(username):
    """Return modules available for specific user types"""
    user_modules = {
        "user": {
            "Job Matcher": {
                "icon": "🎯", 
                "desc": "Match resumes with job requirements and find the best candidate fit"
            },
            "Users": {
                "icon": "👤", 
                "desc": "Resume analysis and skills assessment for candidate profiles"
            },
            "Feedback": {
                "icon": "📝", 
                "desc": "Provide feedback, suggestions, and report issues"
            }
        },
        "admin": {
            # Admin gets access to all modules
            "Job Matcher": {"icon": "🎯", "desc": "Match resumes with job requirements and find the best candidate fit"},
            "Users": {"icon": "👤", "desc": "Resume analysis and skills assessment for candidate profiles"},
            "Recruiters": {"icon": "🔍", "desc": "Candidate search, evaluation, and talent pool management"},
            "Admin": {"icon": "⚙️", "desc": "System administration, user management, and configuration settings"},
            "Feedback": {"icon": "📝", "desc": "Provide feedback, suggestions, and report issues"}
        },
        "recruiter": {
            "Job Matcher": {"icon": "🎯", "desc": "Match resumes with job requirements and find the best candidate fit"},
            "Recruiters": {"icon": "🔍", "desc": "Candidate search, evaluation, and talent pool management"},
            "Feedback": {"icon": "📝", "desc": "Provide feedback, suggestions, and report issues"}
        }
    }
    return user_modules.get(username, {})

def navigation_page():
    """Display the main navigation page after successful login"""
    # Get modules specific to the logged-in user
    modules = get_user_modules(st.session_state.username)

    # Header with logout button
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown(f"<h2 style='margin-bottom: 2rem;'>Welcome, {st.session_state.username}! 👋</h2>", unsafe_allow_html=True)
    with col2:
        if st.button("Logout", type="primary", key="nav_logout_btn", 
                    help="Click to logout", 
                    use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.current_module = None
            st.rerun()

    if st.session_state.current_module:
        # Add Job Matcher module handling
        if st.session_state.current_module == "Job Matcher":
            try:
                from modules.app import process_matcher_mode
                process_matcher_mode()
            except ImportError:
                st.error("Module not found. The Job Matcher module is still in development.")
                st.info("For demonstration purposes, you can explore other modules.")

        elif st.session_state.current_module == "Users":
            try:
                # Add project root to path
                project_root = Path(__file__).parent
                if str(project_root) not in sys.path:
                    sys.path.append(str(project_root))
                
                from modules.users import process_user_mode
                process_user_mode()
            except Exception as e:
                st.error(f"Error in Users module: {str(e)}")
               # col1, col2, col3 = st.columns([1, 1, 1])
               # with col2:
               #     if st.button("← Back to Dashboard", key="back_users_error_btn", type="primary"):
               #         st.session_state.current_module = None
               #         st.rerun()

        elif st.session_state.current_module == "Recruiters":
            try:
                # Add project root to path
                project_root = Path(__file__).parent
                if str(project_root) not in sys.path:
                    sys.path.append(str(project_root))
                
                from modules.recruiters import process_recruiters_mode
                process_recruiters_mode()
                
            except Exception as e:
                st.error(f"Error in Recruiters module: {str(e)}")
                #col1, col2, col3 = st.columns([1, 1, 1])
                #with col2:
                #    if st.button("← Back to Dashboard", key="back_recruiters_error_btn", type="primary"):
                #        st.session_state.current_module = None
                #        st.rerun()

        elif st.session_state.current_module == "Admin":
            try:
                # Add project root to path
                project_root = Path(__file__).parent
                if str(project_root) not in sys.path:
                    sys.path.append(str(project_root))
                
                from modules.admin import process_admin_mode
                process_admin_mode()
                
            except Exception as e:
                st.error(f"Error loading Admin module: {str(e)}")
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("← Back to Dashboard", key="back_admin_error_btn", type="primary"):
                        st.session_state.current_module = None
                        st.rerun()
                        
        elif st.session_state.current_module == "Feedback":
            try:
                from modules.feedback import process_feedback_mode
                process_feedback_mode()
            except ImportError:
                st.error("Module not found. The Feedback module is still in development.")
        
        # Add a back button to return to the dashboard
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("← Back to Dashboard", key="back_dashboard_btn", type="primary"):
                st.session_state.current_module = None
                st.rerun()

    else:
        # Add animation optimization 
        st.markdown("""
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                // Add touch support detection
                const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
                if (isTouchDevice) {
                    document.body.classList.add('touch-device');
                }
                
                // Add event listeners to cards with reduced latency
                const cards = document.querySelectorAll('.clickable-card');
                cards.forEach(card => {
                    card.addEventListener('mouseenter', () => {
                        requestAnimationFrame(() => {
                            card.classList.add('card-hover');
                        });
                    });
                    
                    card.addEventListener('mouseleave', () => {
                        requestAnimationFrame(() => {
                            card.classList.remove('card-hover');
                        });
                    });
                    
                    // Add ripple effect on click
                    card.addEventListener('mousedown', (e) => {
                        const ripple = document.createElement('div');
                        ripple.classList.add('ripple');
                        const rect = card.getBoundingClientRect();
                        ripple.style.left = `${e.clientX - rect.left}px`;
                        ripple.style.top = `${e.clientY - rect.top}px`;
                        card.appendChild(ripple);
                        
                        setTimeout(() => {
                            ripple.remove();
                        }, 600);
                    });
                });
            });
        </script>
        <style>
            .ripple {
                position: absolute;
                background: rgba(255,255,255,0.15);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple 0.6s linear;
                pointer-events: none;
                width: 100px;
                height: 100px;
                margin-left: -50px;
                margin-top: -50px;
            }
            
            @keyframes ripple {
                to {
                    transform: scale(4);
                    opacity: 0;
                }
            }
            
            .touch-device .clickable-card {
                transition: transform 0.3s ease, background-color 0.3s ease;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Create module grid
        st.markdown("<div class='module-grid'>", unsafe_allow_html=True)
        
        # Create columns for better spacing
        cols = st.columns(3)
        col_index = 0
        
        # Create interactive module cards only for authorized modules
        for module, details in modules.items():
            with cols[col_index]:
                card = st.container()
                with card:
                    st.markdown(f"""
                        <div class="clickable-card">
                            <div class="module-icon">{details['icon']}</div>
                            <div class="module-title">{module}</div>
                            <div class="module-desc">{details['desc']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown('<div class="clickable-overlay" style="position: relative;">', unsafe_allow_html=True)
                    if st.button(f"Open {module}", key=f"btn_{module.lower().replace(' ', '_')}"):
                        navigate_to_module(module)
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # Move to next column
            col_index = (col_index + 1) % 3
        
        st.markdown("</div>", unsafe_allow_html=True)

# Main app logic
def main():
    """Main application function"""
    # Add bottom margin to account for copyright footer
    st.markdown("""
        <style>
        .main .block-container {
            padding-bottom: 70px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if st.session_state.authenticated:
        navigation_page()
    else:
        login_page()

if __name__ == "__main__":
    main()