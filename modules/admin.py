import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys
import os
from datetime import datetime

# Initialize paths
MODULE_DIR = Path(__file__).parent
PROJECT_DIR = MODULE_DIR.parent
DATA_DIR = PROJECT_DIR / 'data'
DATA_DIR.mkdir(exist_ok=True)

# Database initialization
def init_database():
    """Initialize SQLite database"""
    try:
        db_path = DATA_DIR / 'user_pdfs.db'
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_uploaded_pdfs (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    data BLOB NOT NULL,
                    archived INTEGER DEFAULT 0
                )
            ''')
            conn.commit()
    except Exception as e:
        st.error(f"Database initialization error: {str(e)}")
        # Add debug information
        st.write("Debug Info:")
        st.write(f"Database path: {db_path}")
        st.write(f"Data directory exists: {DATA_DIR.exists()}")

# Initialize feedback file
def init_feedback_file():
    """Initialize feedback CSV file"""
    try:
        feedback_file = DATA_DIR / 'feedback_data.csv'
        if not feedback_file.exists():
            feedback_file.write_text('User Name,Feedback,Role,Timestamp,Status\n')
    except Exception as e:
        st.error(f"Feedback file initialization error: {str(e)}")

# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    session_vars = {
        'admin_authenticated': False,
        'selected_pdfs': [],
        'show_archived': False,
        'show_archived_feedback': False,
        'selected_feedback': [],
        'feedback_action_taken': False,
        'pdf_action_performed': False,
        'checkbox_values': {}
    }
    
    for var, default in session_vars.items():
        if var not in st.session_state:
            st.session_state[var] = default

def process_admin_mode():
    """Main admin module function"""
    try:
        # Initialize components
        init_session_state()
        
        try:
            init_database()
        except Exception as e:
            st.warning(f"Database initialization warning: {e}")
            
        try:
            init_feedback_file()
        except Exception as e:
            st.warning(f"Feedback file initialization warning: {e}")
        
        st.title("Admin Dashboard")
        
        # Sidebar content
        with st.sidebar:
            st.title("Administrative Tools")
            st.markdown("About")
            st.markdown("Manage user-uploaded resumes and feedback data. This section tells about the system's performance and user experience. It is only accessible to authorized personnel. The resume database is used to store user-uploaded resumes, and the feedback database is used to store user feedback.")
            st.markdown("""
            ### Available Features:
            - User Management
            - System Configuration
            - Data Analytics
            - Security Controls
            - Feedback Management
            - Resume Management
            """)
        
        # Authentication check
        if not st.session_state.admin_authenticated:
            display_admin_login()
        else:
            display_admin_dashboard()
            
    except Exception as e:
        st.error(f"Error in admin module: {str(e)}")
        display_back_button()
        # Add debug information
        st.write("Debug Info:")
        st.write(f"Admin authenticated: {st.session_state.get('admin_authenticated', False)}")

def display_back_button():
    """Display back button"""
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("← Back to Dashboard", key="back_admin_btn", type="primary"):
            st.session_state.current_module = None
            st.rerun()

def display_admin_login():
    """Display admin login interface"""
    try:
        with st.container():
            st.subheader("Admin Authentication")
            col1, col2 = st.columns([1, 1])
            
            with col1:
                username = st.text_input("Username:", placeholder="Enter admin username")
            with col2:
                password = st.text_input("Password:", type="password", placeholder="Enter password")
            
            if st.button("Login", use_container_width=True, type="primary"):
                if authenticate_admin(username, password):
                    st.session_state.admin_authenticated = True
                    st.success("Authentication successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
    except Exception as e:
        st.error(f"Login error: {str(e)}")
        display_back_button()

def display_admin_dashboard():
    """Display admin dashboard after successful login"""
    try:
        # Add error boundary
        st.markdown("### Admin Dashboard")
        st.info("Successfully logged in as Administrator")
        
        # Create tabs with error handling for each tab
        tab1, tab2 = st.tabs(["📄 Resume Management", "💬 Feedback Analytics"])
        
        with tab1:
            try:
                display_uploaded_pdfs_enhanced()
            except Exception as e:
                st.error(f"Error loading Resume Management: {str(e)}")
                st.info("This section encountered an error. Please check the database connection.")
        
        with tab2:
            try:
                display_feedback_data_enhanced()
            except Exception as e:
                st.error(f"Error loading Feedback Analytics: {str(e)}")
                st.info("This section encountered an error. Please check the feedback data file.")
        
        # Add logout button with proper spacing
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Logout", type="primary", key="admin_logout_btn"):
                st.session_state.admin_authenticated = False
                st.rerun()
                
    except Exception as e:
        st.error(f"Dashboard error: {str(e)}")
        display_back_button()

def authenticate_admin(username: str, password: str) -> bool:
    """Authenticate admin credentials"""
    try:
        # You can replace this with your actual authentication logic
        is_valid = (username == "admin" and password == "admin123")
        if is_valid:
            st.session_state.admin_authenticated = True
            return True
        return False
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return False

def calculate_sentiment(feedback_data):
    """Calculate sentiment analysis from feedback records"""
    try:
        if feedback_data.empty:
            return "No Data Available"
        
        # Enhanced keyword lists for better sentiment detection
        positive_words = {
            'great', 'good', 'excellent', 'amazing', 'helpful', 'nice', 'perfect', 
            'love', 'awesome', 'fantastic', 'wonderful', 'best', 'satisfied', 
            'easy', 'impressive', 'efficient', 'effective', 'intuitive', 'useful',
            'clear', 'fast', 'reliable', 'accurate', 'smooth', 'responsive'
        }
        
        negative_words = {
            'bad', 'poor', 'terrible', 'worst', 'difficult', 'hard', 'confusing', 
            'hate', 'issue', 'problem', 'slow', 'complicated', 'frustrating', 
            'disappointing', 'buggy', 'unclear', 'error', 'broken', 'crash',
            'fail', 'wrong', 'annoying', 'inconsistent', 'unusable'
        }
        
        # Initialize counters
        total_score = 0
        valid_feedback_count = 0
        sentiment_scores = []
        
        for feedback in feedback_data['Feedback']:
            if isinstance(feedback, str):
                words = set(feedback.lower().split())
                pos_count = len(words.intersection(positive_words))
                neg_count = len(words.intersection(negative_words))
                
                # Calculate individual feedback score
                if pos_count > 0 or neg_count > 0:
                    score = (pos_count - neg_count) / (pos_count + neg_count)
                    sentiment_scores.append(score)
                    total_score += score
                    valid_feedback_count += 1
        
        # Calculate average sentiment if valid feedback exists
        if valid_feedback_count > 0:
            avg_sentiment = total_score / valid_feedback_count
            
            # Return detailed sentiment analysis
            return {
                'score': avg_sentiment,
                'label': get_sentiment_label(avg_sentiment),
                'emoji': get_sentiment_emoji(avg_sentiment),
                'total_analyzed': valid_feedback_count,
                'positive_ratio': len([s for s in sentiment_scores if s > 0]) / len(sentiment_scores) if sentiment_scores else 0,
                'negative_ratio': len([s for s in sentiment_scores if s < 0]) / len(sentiment_scores) if sentiment_scores else 0
            }
        
        return "Insufficient Data for Analysis"
    
    except Exception as e:
        st.error(f"Error in sentiment analysis: {str(e)}")
        return "Error in Analysis"

def get_sentiment_label(score):
    """Convert sentiment score to human-readable label"""
    if score > 0.5:
        return "Very Positive"
    elif score > 0.2:
        return "Positive"
    elif score > -0.2:
        return "Neutral"
    elif score > -0.5:
        return "Negative"
    else:
        return "Very Negative"

def get_sentiment_emoji(score):
    """Convert sentiment score to appropriate emoji"""
    if score > 0.5:
        return "😊"
    elif score > 0.2:
        return "🙂"
    elif score > -0.2:
        return "😐"
    elif score > -0.5:
        return "😕"
    else:
        return "☹️"

def display_feedback_data_enhanced():
    try:
        feedback_file = DATA_DIR / 'feedback_data.csv'
        if not feedback_file.exists():
            st.warning("No feedback data available.")
            return
            
        # Read the file directly as text first
        with open(feedback_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create a clean, structured format
        feedback_entries = []
        
        # Split by delimiter
        if "--" in content:
            entries = content.split("--")
        else:
            # Try comma-separated entries
            entries = [content]
        
        # Process each entry
        for entry_text in entries:
            if not entry_text.strip():
                continue
                
            # Create a new entry dictionary
            entry = {
                "User Name": "",
                "Feedback": "",
                "Role": "User",
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Status": "Active"
            }
            
            # Split by lines
            lines = entry_text.strip().split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Handle lines with key: value format
                if ':' in line:
                    # Split only on the first colon
                    parts = line.split(':', 1)
                    key = parts[0].strip()
                    
                    # Handle case where there's a comma in the value part
                    if len(parts) > 1:
                        value = parts[1].strip()
                        if ',' in value:
                            # Take only the part before the comma
                            value = value.split(',')[0].strip()
                    else:
                        value = ""
                    
                    # Map to standard fields
                    if "user name" in key.lower():
                        entry["User Name"] = value
                    elif "timestamp" in key.lower():
                        entry["Timestamp"] = value
                    elif "status" in key.lower():
                        entry["Status"] = value
                    elif "role" in key.lower():
                        entry["Role"] = value
                    elif "feedback" in key.lower():
                        entry["Feedback"] = value
            
            # Only add entries that have at least a name
            if entry["User Name"]:
                # Ensure Status is valid
                if entry["Status"] not in ["Active", "Archived"]:
                    entry["Status"] = "Active"
                    
                feedback_entries.append(entry)
        
        # Create DataFrame
        if feedback_entries:
            feedback_data = pd.DataFrame(feedback_entries)
        else:
            # Sample data if no entries found
            feedback_data = pd.DataFrame({
                'User Name': ['Sample User'],
                'Feedback': ['This is sample feedback data.'],
                'Role': ['User'],
                'Timestamp': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
                'Status': ['Active']
            })
            st.warning("No valid feedback entries found. Showing sample data.")
        
        # Save clean version
        clean_file = DATA_DIR / 'feedback_data_clean.csv'
        feedback_data.to_csv(clean_file, index=False, quoting=1)  # Use quoting to handle commas
        
        # Initialize session state for feedback selection using list
        if 'selected_feedback' not in st.session_state:
            st.session_state.selected_feedback = []
        if 'show_archived_feedback' not in st.session_state:
            st.session_state.show_archived_feedback = False
        if 'feedback_action_taken' not in st.session_state:
            st.session_state.feedback_action_taken = False

        # Filter data based on archive status
        filtered_data = feedback_data.copy()
        
        # Add toggle for showing archived feedback with proper state management
        previous_archived_state = st.session_state.show_archived_feedback
        show_archived = st.toggle(
            "Show Archived Feedback Records",
            value=previous_archived_state,
            key='archived_feedback_toggle'  # Make sure this key is unique
        )

        # Update session state and filter data based on toggle
        if previous_archived_state != show_archived:
            st.session_state.show_archived_feedback = show_archived
            st.session_state.selected_feedback = []  # Clear selection when toggle changes
            st.rerun()  # Changed from st.experimental_rerun()
        else:
            st.session_state.show_archived_feedback = show_archived

        # Filter data based on toggle
        if not st.session_state.show_archived_feedback:
            # Make sure 'Status' column exists before filtering
            if 'Status' in filtered_data.columns:
                filtered_data = filtered_data[filtered_data['Status'] != 'Archived']
        else:
            # When showing archived, show all records (both active and archived)
            pass  # No filtering needed when showing all

        # Move Sentiment Analysis Section to top
        if not feedback_data.empty:
            st.markdown("### 📊 Sentiment Analysis")
            
            # Calculate sentiment
            sentiment_results = calculate_sentiment(feedback_data)
            
            if isinstance(sentiment_results, dict):
                # Create metrics in columns
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(
                        f"""
                        <div style='text-align: center; padding: 10px;'>
                            <h4>Overall Sentiment</h4>
                            <p style='font-size: 24px;'>{sentiment_results['emoji']}</p>
                            <p style='font-size: 18px;'>{sentiment_results['label']}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                with col2:
                    positive_percentage = sentiment_results['positive_ratio'] * 100
                    st.metric(
                        "Positive Feedback",
                        f"{positive_percentage:.1f}%",
                        delta="positive" if positive_percentage > 50 else "negative"
                    )
                
                with col3:
                    st.metric(
                        "Total Analyzed",
                        sentiment_results['total_analyzed'],
                        help="Number of feedback entries analyzed"
                    )
                
                # Add sentiment score visualization
                score = sentiment_results['score']
                st.progress(
                    (score + 1) / 2,  # Convert score from [-1,1] to [0,1]
                    text=f"Sentiment Score: {score:.2f}"
                )
                
                # Add spacing after sentiment analysis
                st.markdown("<br>", unsafe_allow_html=True)

        # Display feedback records section
        st.markdown("### 📝 Feedback Records")
        
        if filtered_data.empty:
            st.info("No feedback entries match your criteria.")
            return

        # Create a container for the feedback entries to avoid rerendering
        feedback_container = st.container()
        
        # Cache the current selection state before display
        current_selection = st.session_state.selected_feedback.copy()
        
        # Display filtered feedback entries
        with feedback_container:
            # Keep track of valid indices for proper selection
            valid_indices = []
            
            for i, (index, row) in enumerate(filtered_data.iterrows()):
                valid_indices.append(index)
                col1, col2, col3, col4, col5 = st.columns([0.5, 2, 2, 1, 1])
                
                with col1:
                    # Create a unique key for each checkbox
                    checkbox_key = f"feedback_{index}_{row['User Name']}"
                    
                    # Check if this index is in the selected list
                    is_selected = index in st.session_state.selected_feedback
                    
                    if st.checkbox(
                        "", 
                        key=checkbox_key,
                        value=is_selected
                    ):
                        # Add to selected list if not already there
                        if index not in st.session_state.selected_feedback:
                            st.session_state.selected_feedback.append(index)
                    else:
                        # Remove from selected list if present
                        if index in st.session_state.selected_feedback:
                            st.session_state.selected_feedback.remove(index)
                
                with col2:
                    st.write(f"**From:** {row['User Name']}")
                    st.write(f"**Role:** {row.get('Role', 'N/A')}")
                
                with col3:
                    st.write(f"**Feedback:** {row['Feedback']}")
                
                with col4:
                    status = row.get('Status', 'Active')
                    status_color = "#FFA500" if status == "Archived" else "#28a745"
                    st.markdown(f"""
                        <span style="color: {status_color};">
                            {status}
                        </span>
                    """, unsafe_allow_html=True)

                with col5:
                    st.write(f"**Date:** {row['Timestamp'][:10]}")
                
                st.markdown("---")

        # Get current selection count
        selected_count = len(st.session_state.selected_feedback)
        
        # Display bulk actions section
        if filtered_data.shape[0] > 0:
            st.markdown("### Bulk Actions")            
            selected_count = len(st.session_state.selected_feedback)
            
            if selected_count > 0:
                st.write(f"Selected: {selected_count} feedback(s)")
                
                # Create action columns for the buttons
                col1, col2 = st.columns(2)
                
                # Create a form to avoid page refresh on button clicks
                with col1:
                    if st.button(
                        "Archive Selected",
                        use_container_width=True,
                        key="archive_feedback_btn",
                        help="Archive selected feedback records"
                    ):
                        # Get the actual indices from the current filtered data
                        selected_indices = st.session_state.selected_feedback
                        
                        if archive_feedback(selected_indices):
                            st.success(f"Successfully archived {selected_count} feedback(s)")
                            # Clear selection after action
                            st.session_state.selected_feedback = []
                            st.session_state.feedback_action_taken = True
                            st.rerun()
                
                with col2:
                    if st.button(
                        "Delete Selected",
                        use_container_width=True,
                        type="primary",
                        key="delete_feedback_btn",
                        help="Permanently delete selected feedback records"
                    ):
                        # Get the actual indices from the current filtered data
                        selected_indices = st.session_state.selected_feedback
                        
                        if delete_feedback(selected_indices):
                            st.success(f"Successfully deleted {selected_count} feedback(s)")
                            # Clear selection after action
                            st.session_state.selected_feedback = []
                            st.session_state.feedback_action_taken = True
                            st.rerun()
            else:
                st.info("Select one or more feedback entries to perform bulk actions")

        # Reset action taken flag if it was set
        if st.session_state.feedback_action_taken:
            st.session_state.feedback_action_taken = False

        # Move visualization section to the bottom
        st.markdown("### 📈 Feedback Trends")
        # Timeline of feedback submissions
        if not feedback_data.empty:
            # Convert timestamp to datetime 
            feedback_data['Timestamp'] = pd.to_datetime(feedback_data['Timestamp'])
            
            # Group by month and count
            feedback_data['Month'] = feedback_data['Timestamp'].dt.strftime('%Y-%m')
            monthly_counts = feedback_data.groupby('Month').size().reset_index(name='Count')
            
            # Create the line chart
            fig = px.line(monthly_counts, x='Month', y='Count', 
                         title='Feedback Submissions Over Time',
                         labels={'Count': 'Number of Submissions', 'Month': 'Month'},
                         markers=True)
            st.plotly_chart(fig, use_container_width=True)

    except FileNotFoundError:
        st.warning("No feedback data available.")
    except Exception as e:
        st.error(f"Error processing feedback data: {str(e)}")
        st.info("Please check the format of your feedback_data.csv file.")

def delete_feedback(feedback_indices):
    """Delete selected feedback from the CSV file"""
    try:
        # Use the clean file for consistent format
        clean_file = DATA_DIR / 'feedback_data_clean.csv'
        original_file = DATA_DIR / 'feedback_data.csv'
        
        # Use clean file if it exists, otherwise use original
        if clean_file.exists():
            target_file = clean_file
        elif original_file.exists():
            target_file = original_file
        else:
            st.warning("No feedback data file found.")
            return False
            
        # Read existing data
        try:
            feedback_data = pd.read_csv(target_file)
        except Exception as e:
            st.error(f"Error reading feedback data: {str(e)}")
            return False
            
        # Check if indices exist in the dataframe
        valid_indices = [idx for idx in feedback_indices if idx in feedback_data.index]
        
        if not valid_indices:
            st.warning("No valid feedback entries to delete")
            return False
        
        # Remove selected feedback
        feedback_data = feedback_data.drop(valid_indices)
        
        # Save updated feedback data to both files to keep them in sync
        feedback_data.to_csv(clean_file, index=False, quoting=1)
        
        # Also update the original file in the structured format
        with open(original_file, 'w', encoding='utf-8') as f:
            for _, row in feedback_data.iterrows():
                f.write(f"User Name: {row['User Name']}\n")
                if 'Role' in row and pd.notna(row['Role']):
                    f.write(f"Role: {row['Role']}\n")
                if 'Feedback' in row and pd.notna(row['Feedback']):
                    f.write(f"Feedback: {row['Feedback']}\n")
                if 'Timestamp' in row and pd.notna(row['Timestamp']):
                    f.write(f"Timestamp: {row['Timestamp']}\n")
                if 'Status' in row and pd.notna(row['Status']):
                    f.write(f"Status: {row['Status']}\n")
                f.write("-" * 50 + "\n")
        
        return True
        
    except Exception as e:
        st.error(f"Error deleting feedback: {str(e)}")
        return False

def archive_feedback(indices):
    """Archive selected feedback entries"""
    try:
        # Use clean file for consistent format
        clean_file = DATA_DIR / 'feedback_data_clean.csv'
        if not clean_file.exists():
            return False
        
        try:
            feedback_data = pd.read_csv(clean_file)
        except Exception as e:
            st.error(f"Error reading feedback data: {str(e)}")
            return False
        
        # Check if indices exist
        valid_indices = []
        for idx in indices:
            if idx in feedback_data.index:
                feedback_data.at[idx, 'Status'] = 'Archived'
                valid_indices.append(idx)
        
        if not valid_indices:
            st.warning("No valid feedback entries to archive")
            return False
            
        # Save back to files
        feedback_data.to_csv(clean_file, index=False, quoting=1)
        
        # Also fix the original file for consistency
        original_file = DATA_DIR / 'feedback_data.csv'
        with open(original_file, 'w', encoding='utf-8') as f:
            for _, row in feedback_data.iterrows():
                f.write(f"User Name: {row['User Name']}\n")
                if 'Role' in row and pd.notna(row['Role']):
                    f.write(f"Role: {row['Role']}\n")
                if 'Feedback' in row and pd.notna(row['Feedback']):
                    f.write(f"Feedback: {row['Feedback']}\n")
                f.write(f"Timestamp: {row['Timestamp']}\n")
                f.write(f"Status: {row['Status']}\n")
                f.write("-" * 50 + "\n")
        
        return True
    except Exception as e:
        st.error(f"Error archiving feedback: {str(e)}")
        return False

def display_uploaded_pdfs_enhanced():
    # Initialize session state variables
    if "selected_pdfs" not in st.session_state:
        st.session_state.selected_pdfs = []
    if "show_archived" not in st.session_state:
        st.session_state.show_archived = False
    if "pdf_action_performed" not in st.session_state:
        st.session_state.pdf_action_performed = False
    if "checkbox_values" not in st.session_state:
        st.session_state.checkbox_values = {}
    
    st.subheader("Resume Database")
    
    # Update toggle for archived resumes
    previous_state = st.session_state.show_archived
    current_state = st.toggle("Show Archived Resumes", previous_state)
    
    # Only trigger rerun if the toggle state changed
    if current_state != previous_state:
        st.session_state.show_archived = current_state
        st.session_state.selected_pdfs = []
        st.session_state.checkbox_values = {}
        st.rerun()
    
    # Get PDF data based on archived visibility setting
    uploaded_pdfs = get_uploaded_pdfs()
    
    # Add metrics with updated counts
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Resumes", len(uploaded_pdfs) if uploaded_pdfs else 0)
    with col2:
        active_count = sum(1 for _, _, archived in uploaded_pdfs if not archived)
        archived_count = sum(1 for _, _, archived in uploaded_pdfs if archived)
        metric_label = "Archived Resumes" if st.session_state.show_archived else "Active Resumes"
        metric_value = archived_count if st.session_state.show_archived else active_count
        st.metric(metric_label, metric_value)
    with col3:
        st.metric("Storage Used", f"{len(uploaded_pdfs)*0.5:.1f} MB" if uploaded_pdfs else "0 MB")
    
    # Search and filter options
    search_term = st.text_input("Search resumes:", placeholder="Enter name or ID")
    
    # Create a container for PDF list to improve performance
    pdf_list_container = st.container()
    
    if uploaded_pdfs:
        with pdf_list_container:
            # Create filtered PDFs list for display
            pdf_data_list = []
            
            for pdf_id, pdf_name, archived in uploaded_pdfs:
                if search_term and search_term.lower() not in pdf_name.lower() and search_term != str(pdf_id):
                    continue
                
                pdf_data_list.append({
                    "ID": pdf_id,
                    "Resume Name": pdf_name,
                    "Status": "Archived" if archived else "Active"
                })
            
            if pdf_data_list:
                # Create check box callback functions to update session state without rerunning
                def toggle_pdf_selection(pdf_id):
                    if pdf_id in st.session_state.selected_pdfs:
                        st.session_state.selected_pdfs.remove(pdf_id)
                    else:
                        st.session_state.selected_pdfs.append(pdf_id)
                    
                    # Update checkbox value in session state
                    key = f"pdf_{pdf_id}"
                    st.session_state.checkbox_values[key] = pdf_id in st.session_state.selected_pdfs
                
                # Display PDF list
                for row in pdf_data_list:
                    pdf_id = row["ID"]
                    pdf_name = row["Resume Name"]
                    status = row["Status"]
                    
                    col1, col2, col3, col4 = st.columns([1, 3, 1, 2])
                    
                    # Generate a unique key for this checkbox
                    checkbox_key = f"pdf_{pdf_id}"
                    
                    # Use the stored checkbox value if available
                    is_checked = pdf_id in st.session_state.selected_pdfs
                    
                    with col1:
                        # Create checkbox with current selection state
                        if st.checkbox(
                            "",
                            value=is_checked,
                            key=checkbox_key,
                            on_change=toggle_pdf_selection,
                            args=(pdf_id,)
                        ):
                            # This check is just for display - the actual state change happens in the callback
                            pass
    
                    with col2:
                        st.write(f"{pdf_name}")
                        
                    with col3:
                        status_color = "#FFA500" if status == "Archived" else "#28a745"
                        st.markdown(f"""
                            <span style="color: {status_color};">
                                {status}
                            </span>
                        """, unsafe_allow_html=True)
                    
                    with col4:
                        pdf_data = get_pdf_data(pdf_id)
                        if pdf_data:
                            # Single column for download button
                            st.download_button(
                                label="Download",
                                data=pdf_data[1],
                                file_name=pdf_name,
                                mime="application/pdf",
                                key=f"download_{pdf_id}"
                            )
                    
                    st.markdown("---")
                
                # Bulk actions section
                st.markdown("### Bulk Actions")
                selected_count = len(st.session_state.selected_pdfs)
                
                if selected_count == 0:
                    st.info("Select one or more resumes to perform bulk actions")
                else:
                    st.write(f"Selected: {selected_count} resume(s)")
                
                # Create columns for buttons
                col1, col2 = st.columns(2)
                
                # Archive button
                with col1:
                    if st.button(
                        "Archive Selected", 
                        use_container_width=True,
                        disabled=(selected_count == 0),
                        key="archive_pdf_button",
                        help="Archive the selected resumes"
                    ):
                        if archive_pdfs(st.session_state.selected_pdfs):
                            st.session_state.pdf_action_performed = True
                            st.success(f"Successfully archived {selected_count} resume(s)")
                            # Clear selection after action
                            st.session_state.selected_pdfs = []
                            st.session_state.checkbox_values = {}
                            st.rerun()
                
                # Delete button
                with col2:
                    if st.button(
                        "Delete Selected", 
                        use_container_width=True,
                        type="primary",
                        disabled=(selected_count == 0),
                        key="delete_pdf_button",
                        help="Permanently delete the selected resumes"
                    ):
                        if delete_pdfs(st.session_state.selected_pdfs):
                            st.session_state.pdf_action_performed = True
                            st.success(f"Successfully deleted {selected_count} resume(s)")
                            # Clear selection after action
                            st.session_state.selected_pdfs = []
                            st.session_state.checkbox_values = {}
                            st.rerun()
                
                # Reset action performed flag
                if st.session_state.pdf_action_performed:
                    st.session_state.pdf_action_performed = False
                
            else:
                st.info("No resumes match your search criteria.")
    else:
        st.warning("No uploaded resumes available.")
        st.info("Resumes will appear here once users upload them.")

def delete_pdfs(pdf_ids):
    """Delete selected PDFs from the database"""
    try:
        conn = sqlite3.connect('data/user_pdfs.db')
        cursor = conn.cursor()
        
        # Delete each PDF by ID
        for pdf_id in pdf_ids:
            cursor.execute("DELETE FROM user_uploaded_pdfs WHERE id=?", (pdf_id,))
        
        # Commit the changes
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error as e:
        st.error(f"Error deleting PDFs: {e}")
        return False

def archive_pdfs(pdf_ids):
    try:
        conn = sqlite3.connect('data/user_pdfs.db')
        cursor = conn.cursor()
        
        # First check if the archived column exists, if not, add it
        cursor.execute("PRAGMA table_info(user_uploaded_pdfs)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if "archived" not in column_names:
            cursor.execute("ALTER TABLE user_uploaded_pdfs ADD COLUMN archived INTEGER DEFAULT 0")
        
        # Update each PDF to set archived=1
        for pdf_id in pdf_ids:
            cursor.execute("UPDATE user_uploaded_pdfs SET archived=1 WHERE id=?", (pdf_id,))
        
        # Commit the changes
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        st.error(f"Error archiving PDFs: {e}")
        return False

def get_uploaded_pdfs():
    try:
        conn = sqlite3.connect('data/user_pdfs.db')
        cursor = conn.cursor()
        
        # Check if archived column exists
        cursor.execute("PRAGMA table_info(user_uploaded_pdfs)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if "archived" in column_names:
            if st.session_state.get('show_archived', False):
                # Get all PDFs with their archived status
                cursor.execute("SELECT id, name, archived FROM user_uploaded_pdfs")
            else:
                # Only get non-archived PDFs
                cursor.execute("SELECT id, name, archived FROM user_uploaded_pdfs WHERE archived=0 OR archived IS NULL")
        else:
            cursor.execute("SELECT id, name, 0 as archived FROM user_uploaded_pdfs")
            
        uploaded_pdfs = cursor.fetchall()
        conn.close()
        return uploaded_pdfs

    except sqlite3.Error as e:
        st.error(f"Error fetching uploaded PDFs: {e}")
        return []

def get_pdf_data(pdf_id):
    try:
        conn = sqlite3.connect('data/user_pdfs.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, data FROM user_uploaded_pdfs WHERE id=?", (pdf_id,))
        pdf_data = cursor.fetchone()
        conn.close()
        return pdf_data

    except sqlite3.Error as e:
        st.error(f"Error fetching PDF data: {e}")
        return None

def process_pdf(file):
    """Process uploaded PDF with default settings"""
    try:
        # Set default max size to 10MB
        max_size = 10
        
        if file.size > max_size * 1024 * 1024:  # Convert MB to bytes
            raise ValueError(f"File size exceeds maximum allowed size of {max_size}MB")
            
        return True
        
    except Exception as e:
        st.error(f"Error processing PDF: {str(e)}")
        return False

def get_db_connection():
    """Get database connection with proper path"""
    try:
        db_path = Path(__file__).parent.parent / 'data' / 'user_pdfs.db'
        return sqlite3.connect(str(db_path))
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None

def get_feedback_file_path():
    """Get feedback file path"""
    return Path(__file__).parent.parent / 'data' / 'feedback_data.csv'

if __name__ == "__main__":
    process_admin_mode()