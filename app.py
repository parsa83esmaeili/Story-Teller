# app.py - Streamlit Web App for AI Story & Image Generation
import os
import streamlit as st
from openai import OpenAI
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime
import requests
import base64

# ------------------------- SETUP & SECRETS -------------------------
# Initialize API clients using Streamlit's secrets management
# IMPORTANT: You will set these keys in the Cloud deployment
try:
    story_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    image_client = OpenAI(
        api_key=st.secrets["GAPGPT_API_KEY"],
        base_url="https://api.gapgpt.app/v1"
    )
except Exception as e:
    st.error(f"Error loading API keys: {e}. Please check your secrets configuration.")
    st.stop()

# ------------------------- STORY & IMAGE FUNCTIONS -------------------------
# (KEEP YOUR EXISTING 'generate_story', 'generate_and_save_image',
#  and 'format_story' FUNCTIONS HERE EXACTLY AS THEY ARE)
# ... [Paste your functions here without the command-line prints] ...

# ------------------------- MODIFIED PDF FUNCTION FOR WEB -------------------------
def create_story_pdf_bytes(story_paragraphs, image_bytes, user_prompt):
    """
    Creates a PDF in memory and returns the bytes.
    'image_bytes' should be the raw bytes of the generated PNG image.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Add your Geom font (ensure the .ttf file is in the same directory)
    pdf.add_font("Geom", "", "Geom-VariableFont_wght.ttf")
    pdf.set_font("Geom", "", 12)

    # 1. TITLE PAGE
    pdf.add_page()
    pdf.set_font("Geom", '', 32)
    pdf.cell(0, 50, "AI Generated Story", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(20)
    pdf.set_font("Geom", '', 24)
    truncated_prompt = (user_prompt[:47] + "...") if len(user_prompt) > 50 else user_prompt
    pdf.multi_cell(0, 15, truncated_prompt, align='C')
    pdf.ln(30)
    pdf.set_font("Geom", '', 14)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%B %d, %Y')}",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.cell(0, 10, "Created with OpenAI GPT & GapGPT DALL-E 3",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

    # 2. STORY PAGE(S)
    pdf.add_page()
    pdf.set_font("Geom", '', 22)
    pdf.cell(0, 15, "The Story", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Geom", '', 12)
    pdf.ln(10)
    for i, paragraph in enumerate(story_paragraphs):
        pdf.multi_cell(0, 8, paragraph)
        if i < len(story_paragraphs) - 1:
            pdf.ln(8)

    # 3. IMAGE PAGE (if image was generated)
    if image_bytes:
        pdf.add_page()
        pdf.set_font("Geom", '', 22)
        pdf.cell(0, 15, "Story Illustration", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Geom", '', 12)
        pdf.cell(0, 10, "Generated from the first paragraph",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        # Save image bytes to a temporary file for FPDF
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        try:
            pdf.image(tmp_path, x=10, w=pdf.w - 20)
        finally:
            os.unlink(tmp_path)  # Clean up temp file

    # Return PDF as bytes
    return pdf.output(dest="S").encode("latin-1")

# ------------------------- STREAMLIT APP UI -------------------------
st.set_page_config(page_title="AI Story Generator", layout="centered")
st.title("📖 AI Story & Image Generator")
st.markdown("Create a story with AI and get a custom illustration and PDF.")

# Input Section
user_prompt = st.text_area("Enter your story prompt:", 
                           placeholder="e.g., A robot learning to paint in a bustling city market...", 
                           height=100)

generate_button = st.button("✨ Generate Story & Image", type="primary")

# Main App Logic
if generate_button and user_prompt:
    if not user_prompt.strip():
        st.warning("Please enter a prompt.")
        st.stop()

    with st.spinner("🔄 Generating your three-paragraph story..."):
        story_text = generate_story(user_prompt)
        if story_text.startswith("Error"):
            st.error(f"Story generation failed: {story_text}")
            st.stop()

    # Format and display the story
    formatted_story, story_paragraphs, first_paragraph = format_story(story_text)
    if not first_paragraph:
        st.error("Could not extract story paragraphs.")
        st.stop()

    st.subheader("Your Generated Story")
    st.markdown(formatted_story)

    with st.spinner("🎨 Creating an image from the first paragraph..."):
        # Generate image and keep it in memory
        image_result = generate_and_save_image(first_paragraph)
        if isinstance(image_result, str) and image_result.startswith("Error"):
            st.warning(f"Image generation failed: {image_result}. Continuing without image.")
            image_bytes = None
        else:
            # 'image_result' should be the file path; read the image bytes
            with open(image_result, 'rb') as f:
                image_bytes = f.read()
            # Display the image in the app
            st.subheader("Story Illustration")
            st.image(image_bytes, use_container_width=True)

    with st.spinner("📄 Compiling your PDF..."):
        pdf_bytes = create_story_pdf_bytes(story_paragraphs, image_bytes, user_prompt)

    # Success Message and Download Button
    st.success("✅ All done! Download your storybook below.")
    st.download_button(
        label="📥 Download Story as PDF",
        data=pdf_bytes,
        file_name=f"AI_Story_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        mime="application/pdf",
    )
elif generate_button:
    st.info("Please enter a story prompt to begin.")