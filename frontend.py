"""
Frontend compatibility module.

This module provides compatibility functions for code that still depends on the
frontend module after refactoring to use Streamlit directly.
"""

import streamlit as st

# Common functions that might be imported from frontend
def display_message(message, message_type="info"):
    """Display a message using Streamlit"""
    if message_type == "info":
        st.info(message)
    elif message_type == "success":
        st.success(message)
    elif message_type == "warning":
        st.warning(message)
    elif message_type == "error":
        st.error(message)
    else:
        st.write(message)

def display_pdf(pdf_bytes):
    """Display a PDF using Streamlit"""
    import base64
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def show_skills(skills):
    """Display skills using Streamlit"""
    if skills:
        st.write("**Skills:**")
        for skill in skills:
            st.markdown(f"- {skill}")

# Add any other functions that might be imported from frontend
# This is a compatibility layer, so we're making educated guesses