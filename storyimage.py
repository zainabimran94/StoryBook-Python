import asyncio
from typing import Optional
import fal_client
import os
from fastapi import HTTPException
from pydantic import BaseModel

FAL_KEY = os.environ.get('FAL_KEY')

class SendPreferencesDto(BaseModel):
    groupName: str
    themeName: str
    imageDesc: Optional[str] = None
    storyDesc: Optional[str] = None
    userId: str
    
async def generate_images(data: SendPreferencesDto) -> str:

    description = data.imageDesc if data.groupName.lower() == "toddler" else data.storyDesc
    prompt = f"Create a book cover image for a {'toddler' if data.groupName.lower() == 'toddler' else 'kid'} story in a Ghibli style, ensuring that no title or text is included on the cover. Description: {description}"

    try:
        # Step 1: Submit the request
        handler = await fal_client.submit_async(
            "fal-ai/flux/dev",
            arguments={
                "prompt": prompt,
                "image_size": "portrait_4_3",
                "num_images": 1,
                "enable_safety_checker": True,
                "num_inference_steps": 8,
                "guidance_scale": 3.5,
                "sync_mode": False,
            }
        )
        
        request_id = handler.request_id
        if not request_id:
            raise HTTPException(status_code=500, detail="Failed to get request ID")

        # Step 2: Poll for status
        max_attempts = 30  # Maximum number of polling attempts
        attempt = 0
        
        while attempt < max_attempts:
            try:
                status = await fal_client.status_async("fal-ai/flux/dev", request_id, with_logs=True)
                
                if isinstance(status, fal_client.Completed):
                    # Step 3: Get the result once completed
                    result = await fal_client.result_async("fal-ai/flux/dev", request_id)
                    
                    # Extract the image URL from the result
                    if result and "images" in result and len(result["images"]) > 0:
                        return result["images"][0]["url"]
                    raise HTTPException(status_code=500, detail="No image URL in response")
                    
                elif isinstance(status, fal_client.InProgress):
                    # Log progress if needed
                    if status.logs:
                        for log in status.logs:
                            print(f"Progress: {log.get('message', '')}")
                            
            except Exception as e:
                print(f"Error during status check: {str(e)}")
                
            attempt += 1
            await asyncio.sleep(2)  # Wait 2 seconds between checks
            
        raise HTTPException(status_code=500, detail="Timeout waiting for image generation")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")