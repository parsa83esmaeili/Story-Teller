# AI Story Generator Web App

A Streamlit web application that generates creative stories with AI and creates accompanying images and PDFs.

## Features
- Generate 3-paragraph stories using OpenAI GPT
- Create images from the first paragraph using GapGPT (DALL-E 3)
- Export stories as formatted PDFs with custom typography
- User-friendly web interface

## Setup for Local Development
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create `.streamlit/secrets.toml` with your API keys
4. Run: `streamlit run app.py`

## Deployment to Streamlit Cloud
1. Upload all files to a GitHub repository
2. Connect to Streamlit Cloud
3. Set secrets in app settings using the TOML format
4. Deploy!

## Required Files
- `app.py` - Main application
- `requirements.txt` - Dependencies
- `Geom-VariableFont_wght.ttf` - Font file for PDFs