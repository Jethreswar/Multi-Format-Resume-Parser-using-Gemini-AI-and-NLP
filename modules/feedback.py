import streamlit as st
from datetime import datetime

def process_feedback_mode():
    """Process Feedback module functionality"""
    # Sidebar content
    with st.sidebar:
        st.title("Resume Parser Feedback System")
        st.subheader("About")
        st.write(
            "This interactive feedback collection system creates a continuous improvement loop by gathering user insights on parser accuracy, feature usability, and suggested enhancements. The module incorporates advanced sentiment analysis to categorize feedback themes, prioritize development efforts, and generate actionable reports for product management to ensure ongoing refinement of the resume parsing experience."
        )
        st.markdown(
            """
            - User Experience Feedback Collection
            - Parser Accuracy Reporting
            - Feature Request Management
            - Sentiment Analysis Dashboard
            - Continuous Improvement Metrics
            """
        )

    # Main feedback section
    st.title("Feedback Section")
    st.subheader("We value your feedback! Please share your thoughts on the resume parser.")

    # Feedback Form
    st.markdown(
        """
        <div style="background-color:#f9f9f9;padding:15px;border-radius:10px;box-shadow:0 4px 6px rgba(0,0,0,0.1);">
        <h4 style="color:#333;">Help us improve by sharing your thoughts below:</h4>
        </div>
        """,
        unsafe_allow_html=True,
    )
    user_name = st.text_input("👤 Your Name:")
    # Add role selection dropdown
    user_role = st.selectbox(
        "🎯 Select Your Role:",
        options=["User", "Recruiter"],
        help="Please select your role to help us better categorize feedback"
    )
    feedback = st.text_area("📝 Provide feedback on the resume parser:", height=150)
    if st.button("Submit Feedback"):
        if user_name.strip() and feedback.strip():
            add_feedback(user_name, feedback, user_role)
            st.success("🎉 Thank you for your feedback! It has been submitted successfully.")
            st.balloons()
        else:
            st.error("⚠️ Please fill out both your name and feedback before submitting.")

    # Update feedback display section
    st.markdown("### 📋 Recent Feedback")
    try:
        with open("data/feedback_data.csv", "r") as file:
            feedback_data = file.readlines()[-10:]  # Display the last 10 feedback entries
            if feedback_data:
                feedback_html = """
                <div style="
                    background-color:#1E3D59;
                    padding:20px;
                    border-radius:10px;
                    box-shadow:0 4px 6px rgba(0,0,0,0.1);
                    margin:10px 0;
                ">
                """
                for line in feedback_data:
                    # Style each line based on its content
                    if "User Name:" in line:
                        feedback_html += f'<p style="color:#7CFC00;margin:5px 0;font-weight:bold;">{line}</p>'
                    elif "Role:" in line:
                        feedback_html += f'<p style="color:#00CED1;margin:5px 0;font-style:italic;">{line}</p>'
                    elif "Feedback:" in line:
                        feedback_html += f'<p style="color:#FFFFFF;margin:5px 0;padding-left:15px;">{line}</p>'
                    elif "Timestamp:" in line:
                        feedback_html += f'<p style="color:#FFD700;margin:5px 0;font-size:0.9em;">{line}</p>'
                    feedback_html += '<hr style="border:1px solid #334B66;margin:10px 0;">'
                
                feedback_html += "</div>"
                st.markdown(feedback_html, unsafe_allow_html=True)
            else:
                st.info("No feedback available yet.")
    except FileNotFoundError:
        st.info("No feedback data found. Be the first to provide feedback! 🌟")
    
    # Add spacing before the back button
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Create three columns for centered button layout
    col1, col2, col3 = st.columns([1, 1, 1])
    
    # Place button in middle column
    # with col2:
    #    if st.button("← Back to Dashboard", key="back_feedback_btn", type="primary"):
    #        st.session_state.current_module = None
    #        st.rerun()

def add_feedback(user_name, feedback, role):
    """Updated function to include role in feedback data"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("data/feedback_data.csv", "a") as file:
        file.write(f"User Name: {user_name}\n")
        file.write(f"Role: {role}\n")
        file.write(f"Feedback: {feedback}\n")
        file.write(f"Timestamp: {timestamp}\n")
        file.write("-" * 50 + "\n")
