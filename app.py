#!/usr/bin/env python3
# app.py - Streamlit Web App for AI Story & Image Generation
import os
import tempfile
import textwrap
import streamlit as st
from openai import OpenAI
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime
import requests

# ------------------------- SETUP & SECRETS -------------------------
# Initialize API clients using Streamlit's secrets management
@st.cache_resource
def setup_clients():
    try:
        story_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        image_client = OpenAI(
            api_key=st.secrets["GAPGPT_API_KEY"],
            base_url="https://api.gapgpt.app/v1"
        )
        return story_client, image_client
    except Exception as e:
        st.error(f"Error loading API keys: {e}. Please check your secrets configuration.")
        st.stop()

story_client, image_client = setup_clients()

# ------------------------- CORE FUNCTIONS -------------------------
@st.cache_data(ttl=3600)
def generate_story(prompt: str) -> str:
    """Generates a three-paragraph story using OpenAI."""
    if not story_client:
        return "Error: Story client not configured."

    try:
        system_instruction = (
            "You are a creative fiction writer. "
            "Generate a short story based on the user's prompt. "
            "The story must be exactly three paragraphs long. "
            "Ensure the narrative is cohesive and has clear flow."
        )
        response = story_client.responses.create(
            model="gpt-4o-mini",
            instructions=system_instruction,
            input=prompt,
            temperature=0.8,
        )
        return response.output_text
    except Exception as e:
        return f"Error generating story: {e}"

@st.cache_data(ttl=3600)
def generate_and_save_image(prompt: str):
    """Generates an image using GapGPT's API and returns image bytes."""
    if not image_client:
        return "Error: Image client not configured."

    try:
        response = image_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="standard",
            style="vivid"
        )
        image_url = response.data[0].url
        img_response = requests.get(image_url, timeout=30)
        img_response.raise_for_status()
        return img_response.content  # Return image bytes directly
    except Exception as e:
        return f"Error generating image: {e}"

def format_story(story_text: str):
    """Formats the story and extracts paragraphs."""
    story_text = story_text.replace('\n \n', '\n\n').replace('\n\n\n', '\n\n')
    paragraphs = [p.strip() for p in story_text.split('\n\n') if p.strip()]
    
    if not paragraphs:
        return "Error: Could not parse story.", None, None
    
    # Console formatting (for display in the app)
    width = 70
    border = "=" * width
    formatted_lines = [
        f"\n{border}",
        "YOUR GENERATED STORY".center(width),
        f"{border}\n"
    ]
    for i, paragraph in enumerate(paragraphs, 1):
        wrapped_para = textwrap.fill(paragraph, width=width)
        formatted_lines.append(f"Paragraph {i}:")
        formatted_lines.append(wrapped_para)
        formatted_lines.append("")
    formatted_lines.append(border)
    
    return "\n".join(formatted_lines), paragraphs, paragraphs[0]

def create_story_pdf_bytes(story_paragraphs, image_bytes, user_prompt):
    """Creates a PDF in memory and returns the bytes."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Add your Geom font (ensure the .ttf file is in the same directory)
    geom_font_available = os.path.exists("Geom-VariableFont_wght.ttf")
    
    if geom_font_available:
        try:
            pdf.add_font("Geom", "", "Geom-VariableFont_wght.ttf")
            pdf.set_font("Geom", "", 12)
        except:
            geom_font_available = False
            pdf.set_font("Helvetica", "", 12)
    else:
        pdf.set_font("Helvetica", "", 12)
    
    # 1. TITLE PAGE
    pdf.add_page()
    font_name = "Geom" if geom_font_available else "Helvetica"
    pdf.set_font(font_name, '', 32)
    pdf.cell(0, 50, "AI Generated Story", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(20)
    
    pdf.set_font(font_name, '', 24)
    truncated_prompt = (user_prompt[:47] + "...") if len(user_prompt) > 50 else user_prompt
    pdf.multi_cell(0, 15, truncated_prompt, align='C')
    pdf.ln(30)
    
    pdf.set_font(font_name, '', 14)
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%B %d, %Y')}", 
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.cell(0, 10, "Created with OpenAI GPT & GapGPT DALL-E 3", 
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

    # 2. STORY PAGE(S)
    pdf.add_page()
    pdf.set_font(font_name, '', 22)
    pdf.cell(0, 15, "The Story", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font(font_name, '', 12)
    pdf.ln(10)
    
    for i, paragraph in enumerate(story_paragraphs):
        pdf.multi_cell(0, 8, paragraph)
        if i < len(story_paragraphs) - 1:
            pdf.ln(8)

    # 3. IMAGE PAGE (if image was generated)
    if image_bytes:
        pdf.add_page()
        pdf.set_font(font_name, '', 22)
        pdf.cell(0, 15, "Story Illustration", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font(font_name, '', 12)
        pdf.cell(0, 10, "Generated from the first paragraph", 
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        
        # Save image bytes to a temporary file for FPDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name
        try:
            pdf.image(tmp_path, x=10, w=pdf.w - 20)
        finally:
            os.unlink(tmp_path)  # Clean up temp file

    # Return PDF as bytes (handles both fpdf and fpdf2 library versions)
    # FIX FOR AttributeError: This handles both string and bytes output
    pdf_output = pdf.output(dest="S")
    if isinstance(pdf_output, str):
        return pdf_output.encode("latin-1")
    else:
        # It's already bytes
        return pdf_output

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
    st.text(formatted_story)

    with st.spinner("🎨 Creating an image from the first paragraph..."):
        # Generate image and keep it in memory
        image_result = generate_and_save_image(first_paragraph)
        if isinstance(image_result, str) and image_result.startswith("Error"):
            st.warning(f"Image generation failed: {image_result}. Continuing without image.")
            image_bytes = None
        else:
            # 'image_result' contains the image bytes
            image_bytes = image_result
            # Display the image in the app
            st.subheader("Story Illustration")
            st.image(image_bytes, use_container_width=True)

    with st.spinner("📄 Compiling your PDF..."):
        pdf_bytes = create_story_pdf_bytes(story_paragraphs, image_bytes, user_prompt)

    # Success Message and Download Button
    st.success("✅ All done! Download your storybook below.")
    
    # Generate a nice filename with timestamp
    filename = f"AI_Story_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    
    # Provide download button
    st.download_button(
        label="📥 Download Story as PDF",
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
    )
elif generate_button:
    st.info("Please enter a story prompt to begin.")

# Footer
st.markdown("---")
st.caption("Built with OpenAI GPT, GapGPT DALL-E 3, and Streamlit")