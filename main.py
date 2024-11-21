from typing import Optional
from storyimage import generate_images
from dotenv import load_dotenv
from storytext import generate_title, generate_story
import aiohttp
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()
# FastAPI app initialization
app = FastAPI()

# CORS setup
origins = [
    "http://localhost:5044", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

class SendPreferencesDto(BaseModel):
    groupName: str
    themeName: str
    imageDesc: Optional[str] = None
    storyDesc: Optional[str] = None
    userId: str

class StoryGeneratedDto(BaseModel):
    storyGenTitle: str
    storyBook: str
    storyImageUrl: str
    userId: str


async def send_story_to_csharp(story_data: dict, api_url: str) -> dict:
    
    async with aiohttp.ClientSession() as session:
        try:
            headers = {
                "Content-Type": "application/json",
            }
            async with session.post(api_url, json=story_data, headers=headers) as response:
                 content_type = response.headers.get('Content-Type', '')
                 print(f"Response Status: {response.status}")
                 print(f"Response Content: {await response.text()}")

                 if response.status == 200 and 'application/json' in content_type:
                    return await response.json()
           
                 else:
                    error_text = await response.text()
                    print(f"Error from C# API: {error_text}")  # Log error details for debugging
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Error from C# API: {error_text}"
                    )
        except aiohttp.ClientError as e:
            print(f"Failed to communicate with C# API: {e}")  # Log the client error
            raise HTTPException(
                status_code=500,
                detail=f"Failed to communicate with C# API: {str(e)}"
            )

@app.post("/api/generate-story")
async def generate(data: SendPreferencesDto):
    max_words = 40 if data.groupName == "toddler" else 80

    title = generate_title(
        themeName=data.themeName,
        groupName=data.groupName,
        imageDesc=data.imageDesc,
        storyDesc=data.storyDesc

    )
    story = generate_story(
        themeName=data.themeName,
        groupName=data.groupName,
        imageDesc=data.imageDesc,
        storyDesc=data.storyDesc,
        max_words=max_words
    )
    image_url = await generate_images(data) 
    if not image_url:  
        raise HTTPException(status_code=400, detail="Image generation failed, image_url is required.")
   
    
    # Prepare story data to send to C# API for saving
    story_data = {
        "storyGenTitle": title,
        "storyBook": story,
        "storyImageUrl": image_url,
        "userId": data.userId
       
    }
    
    # Send story data to C# "CreatedStory" endpoint
    csharp_api_url = "http://localhost:5044/api/Story/create-story"
    csharp_response = await send_story_to_csharp(story_data, csharp_api_url)
    
    return {
        "title": title,
        "story": story,
        "image_url": image_url,
        "csharp_response": csharp_response
       
    }

