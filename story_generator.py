#!/usr/bin/env python3
# story_generator_final.py - Complete AI Story & Image Generator with PDF Export
import os
import textwrap
import requests
from openai import OpenAI
from dotenv import load_dotenv
from fpdf import FPDF
from fpdf.enums import XPos, YPos  # For modern positioning
from datetime import datetime

# ===================== INITIALIZATION =====================
load_dotenv()  # Load API keys from .env file

# Initialize clients
story_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
image_client = OpenAI(
    api_key=os.environ.get("GAPGPT_API_KEY"),
    base_url="https://api.gapgpt.app/v1"  # Routes images through GapGPT
)

# ===================== STORY GENERATION =====================
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

# ===================== IMAGE GENERATION =====================
def generate_and_save_image(prompt: str) -> str:
    """Generates an image using GapGPT's API."""
    if not image_client:
        return "Error: Image client not configured."

    try:
        print("    Generating image via GapGPT API...")
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
        
        filename = "generated_image.png"
        with open(filename, 'wb') as f:
            f.write(img_response.content)
        return os.path.abspath(filename)
    except Exception as e:
        return f"Error generating image: {e}"

# ===================== STORY FORMATTING =====================
def format_story(story_text: str, width: int = 70):
    """Formats the story and extracts paragraphs."""
    story_text = story_text.replace('\n \n', '\n\n').replace('\n\n\n', '\n\n')
    paragraphs = [p.strip() for p in story_text.split('\n\n') if p.strip()]
    
    if not paragraphs:
        return "Error: Could not parse story.", None, None
    
    # Console formatting
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

# ===================== PDF CREATION (WITH YOUR GEOM FONT) =====================
def create_story_pdf(story_paragraphs, image_path, user_prompt, pdf_filename="generated_story.pdf"):
    """Creates a PDF with the story and image using your Geom font."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # 1. ADD YOUR GEOM FONT (Remove the deprecated 'uni=True' parameter)
    pdf.add_font("Geom", "", "Geom-VariableFont_wght.ttf")  # <-- Removed 'uni=True'
    pdf.set_font("Geom", "", 12)  # Set as default font (regular style)

    # 2. TITLE PAGE
    pdf.add_page()
    pdf.set_font("Geom", '', 32)  # Style is now '' instead of 'B'
    pdf.cell(0, 50, "AI Generated Story", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(20)

    pdf.set_font("Geom", '', 24)  # Style is now '' instead of 'B'
    truncated_prompt = (user_prompt[:47] + "...") if len(user_prompt) > 50 else user_prompt
    pdf.multi_cell(0, 15, truncated_prompt, align='C')
    pdf.ln(30)

    pdf.set_font("Geom", '', 14)  # Already '', unchanged
    pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%B %d, %Y')}",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.cell(0, 10, "Created with OpenAI GPT & GapGPT DALL-E 3",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

    # 3. STORY PAGE(S)
    pdf.add_page()
    pdf.set_font("Geom", '', 22)  # Style is now '' instead of 'B'
    pdf.cell(0, 15, "The Story", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Geom", '', 12)  # Regular style for story body
    pdf.ln(10)

    for i, paragraph in enumerate(story_paragraphs):
        pdf.multi_cell(0, 8, paragraph)
        if i < len(story_paragraphs) - 1:
            pdf.ln(8)

    # 4. IMAGE PAGE (if image exists)
    if image_path and os.path.exists(image_path):
        pdf.add_page()
        pdf.set_font("Geom", '', 22)  # Style is now '' instead of 'B'
        pdf.cell(0, 15, "Story Illustration", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Geom", '', 12)  # Style is now '' instead of 'I'
        pdf.cell(0, 10, "Generated from the first paragraph",
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        try:
            pdf.image(image_path, x=10, w=pdf.w - 20)
        except Exception as e:
            pdf.set_font("Geom", '', 12)
            pdf.cell(0, 10, f"[Image could not be loaded: {e}]",
                     new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Save PDF
    pdf.output(pdf_filename)
    return os.path.abspath(pdf_filename)

# ===================== MAIN EXECUTION =====================
def main():
    print("✨ AI STORY GENERATOR WITH PDF EXPORT ✨")
    print("=" * 50)
    print("This script will:")
    print("1. Generate a 3-paragraph story using OpenAI")
    print("2. Create an image from the first paragraph using GapGPT")
    print("3. Compile everything into a formatted PDF (with your Geom font)")
    print("=" * 50)

    # Get prompt
    user_prompt = input("\nEnter your story prompt:\n> ").strip()
    if not user_prompt:
        print("Error: Prompt cannot be empty.")
        return

    # Step 1: Generate story
    print("\n🔄 Generating your story...")
    story_text = generate_story(user_prompt)
    if story_text.startswith("Error"):
        print(f"\n❌ {story_text}")
        return

    # Step 2: Format story
    formatted_story, story_paragraphs, first_paragraph = format_story(story_text)
    if not first_paragraph:
        print("Error: Could not extract paragraphs.")
        return
    print(formatted_story)

    # Step 3: Generate image
    print("\n🔄 Creating image from the first paragraph...")
    image_path = generate_and_save_image(first_paragraph)
    if image_path.startswith("Error"):
        print(f"\n⚠️  {image_path}")
        print("   Continuing to create PDF without image...")
        image_path = None
    else:
        print(f"    Image saved: {image_path}")

    # Step 4: Create PDF
    print("\n📄 Creating PDF document with Geom font...")
    pdf_path = create_story_pdf(story_paragraphs, image_path, user_prompt)
    
    if pdf_path.startswith("Error"):
        print(f"\n❌ {pdf_path}")
    else:
        # Final success message
        print("\n" + "=" * 50)
        print("✅ PROCESS COMPLETE!")
        print(f"📖 Story: Generated and displayed above")
        if image_path:
            print(f"🖼️  Image: {os.path.basename(image_path)}")
        print(f"📄 PDF: {pdf_path}")
        print("=" * 50)

# ===================== ENTRY POINT =====================
if __name__ == "__main__":
    # Pre-flight checks
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not found in .env file.")
    if not os.environ.get("GAPGPT_API_KEY"):
        print("⚠️  Warning: GAPGPT_API_KEY not found in .env file.")
        print("   Get one from: https://gapgpt.app/platform/quickstart")
    
    # Check for font file
    if not os.path.exists("Geom-VariableFont_wght.ttf"):
        print("\n⚠️  Warning: 'Geom-VariableFont_wght.ttf' not found in script folder.")
        print("   Please place it in the same folder as this script.")
        print("   Or update the filename in the create_story_pdf() function.")
    
    main()
    input("\nPress Enter to exit...")