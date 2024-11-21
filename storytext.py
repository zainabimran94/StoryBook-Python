from typing import Optional
import google.generativeai as genai
from pydantic import BaseModel
import os

genai.configure(api_key=os.environ["API_KEY"])

# Generation config
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel("gemini-1.5-flash-latest", generation_config=generation_config)
   

class SendPreferencesDto(BaseModel):
    groupName: str
    themeName: str
    imageDesc: Optional[str] = None
    storyDesc: Optional[str] = None


# Function to generate a story
def generate_story(themeName: str, groupName: str, imageDesc: str = None, storyDesc: str = None, max_words: int = 40):
    description = imageDesc if groupName.lower() == "toddler" else storyDesc
    full_prompt = f"Write a story for a {groupName.lower()} about '{themeName}' in {max_words} words. Description: {description}."
    response = model.generate_content(full_prompt)
    story_text = response.text if hasattr(response, 'text') else "No story generated"
    return story_text.strip()

# Function to generate a title
def generate_title(themeName: str, groupName: str, imageDesc: str = None, storyDesc: str = None):
    if groupName.lower() == "toddler":
        prompt = f"Generate one fun title for a toddler story about the theme '{themeName}'. Description: {imageDesc}"
    else:
        prompt = f"Generate one engaging title for a kids' story on the theme '{themeName}'. Description: {storyDesc}"
    response = model.generate_content(prompt)
    title_text = response.text if hasattr(response, 'text') else "No title generated"
    return title_text.strip()