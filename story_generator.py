#!/usr/bin/env python3
# story_generator.py - Generates a story and an image using OpenAI and GapGPT
import os
import textwrap
import requests
from openai import OpenAI
from dotenv import load_dotenv

# ===================== INITIALIZATION =====================
# 1. Load environment variables from .env file
load_dotenv()

# 2. Initialize TWO separate API clients
# Client for OpenAI (Story Generation) - uses default OpenAI URL
story_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Client for GapGPT (Image Generation) - uses GapGPT's endpoint
image_client = OpenAI(
    api_key=os.environ.get("GAPGPT_API_KEY"),
    base_url="https://api.gapgpt.app/v1"  # Routes image requests through GapGPT
)

# ===================== STORY GENERATION (OpenAI) =====================
def generate_story(prompt: str) -> str:
    """Generates a three-paragraph story using OpenAI's GPT."""
    if not story_client:
        return "Error: Story generation client not configured."

    try:
        system_instruction = (
            "You are a creative fiction writer. "
            "Generate a short story based on the user's prompt. "
            "The story must be exactly three paragraphs long. "
            "Ensure the narrative is cohesive and has a clear flow between paragraphs."
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

# ===================== IMAGE GENERATION (GapGPT) =====================
def generate_and_save_image(prompt: str, filename: str = "story_image.png") -> str:
    """Generates an image using GapGPT's API (OpenAI-compatible endpoint)."""
    if not image_client:
        return "Error: Image generation client not configured."

    try:
        print("    Generating image via GapGPT API...")

        # Use the standard OpenAI images.generate() method via GapGPT
        response = image_client.images.generate(
            model="dall-e-3",      # Image model supported by GapGPT
            prompt=prompt,          # Description from the first paragraph
            n=1,                    # Generate one image
            size="1024x1024",       # Image resolution
            quality="standard",     # "standard" or "hd"
            style="vivid"           # "vivid" or "natural"
        )

        # Extract the image URL from the response
        image_url = response.data[0].url

        # Download the image from the URL
        img_response = requests.get(image_url, timeout=30)
        img_response.raise_for_status()  # Check for download errors

        # Save the image locally
        with open(filename, 'wb') as f:
            f.write(img_response.content)

        return os.path.abspath(filename)

    except requests.exceptions.RequestException as e:
        return f"Network error downloading image: {e}"
    except Exception as e:
        return f"Error generating image: {e}"

# ===================== STORY FORMATTING =====================
def format_story(story_text: str, width: int = 70):
    """
    Formats the story and extracts the first paragraph.
    Returns: (formatted_story_text, first_paragraph)
    """
    # Clean and split the story into paragraphs
    story_text = story_text.replace('\n \n', '\n\n').replace('\n\n\n', '\n\n')
    paragraphs = [p.strip() for p in story_text.split('\n\n') if p.strip()]

    if not paragraphs:
        return "Error: Could not parse story paragraphs.", None

    # Format the output with borders
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
        formatted_lines.append("")  # Blank line between paragraphs

    formatted_lines.append(border)
    return "\n".join(formatted_lines), paragraphs[0]

# ===================== MAIN EXECUTION =====================
def main():
    """Main function to run the story and image generator."""
    print("✨ AI STORY GENERATOR WITH IMAGE CREATION ✨")
    print("=" * 50)
    print("This script will:")
    print("1. Generate a 3-paragraph story using OpenAI")
    print("2. Create an image from the first paragraph using GapGPT")
    print("=" * 50)

    # Get user input
    user_prompt = input("\nEnter your story prompt (e.g., 'a robot learning to paint'):\n> ").strip()

    if not user_prompt:
        print("Error: Prompt cannot be empty.")
        return

    # Step 1: Generate the story
    print("\n🔄 Generating your story...")
    story_text = generate_story(user_prompt)

    if story_text.startswith("Error"):
        print(f"\n❌ {story_text}")
        return

    # Step 2: Format and display the story, extract first paragraph
    formatted_story, first_paragraph = format_story(story_text)

    if not first_paragraph:
        print("Error: Could not extract the first paragraph for image generation.")
        return

    print(formatted_story)

    # Step 3: Generate and save an image from the first paragraph
    print("\n🔄 Creating image from the first paragraph...")
    image_path = generate_and_save_image(first_paragraph)

    if image_path.startswith("Error"):
        print(f"\n❌ {image_path}")
        # Helpful hint for common configuration issues
        if "GAPGPT_API_KEY" in image_path or "not configured" in image_path:
            print("\n💡 Tip: Ensure your .env file has a line like:")
            print('   GAPGPT_API_KEY="your_actual_key_from_gapgpt_app"')
    else:
        print(f"\n✅ Image successfully generated!")
        print(f"📁 Saved to: {image_path}")

        # Show a small preview of the prompt used
        print("\n🖼️  Image Prompt Preview:")
        print("-" * 50)
        preview = (first_paragraph[:97] + "...") if len(first_paragraph) > 100 else first_paragraph
        print(preview)
        print("-" * 50)

# ===================== ENTRY POINT =====================
if __name__ == "__main__":
    # Quick check for essential API keys before running
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not found in environment.")
        print("   Make sure your .env file exists in the script's directory.")
        print("   It should contain: OPENAI_API_KEY=sk-...your_key_here")

    if not os.environ.get("GAPGPT_API_KEY"):
        print("⚠️  Warning: GAPGPT_API_KEY not found in environment.")
        print("   Get a key from: https://gapgpt.app/platform/quickstart")
        print("   Add it to .env as: GAPGPT_API_KEY=your_gapgpt_key_here")

    main()
    input("\nPress Enter to exit...")