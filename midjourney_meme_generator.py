import os
import time
import requests
import json
from dotenv import load_dotenv

# Load environment variables (for Giphy)
load_dotenv()

# API Keys
LEGNEXT_API_KEY = "bc9a1574d1527a05215011f764891e352e50e1b57819c04b71288b2efd3d4503" 
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")

# Configuration
# Legnext requires a PUBLIC URL for the reference image.
# Using a high-quality demo fox image as default.
# REPLACE THIS with your own public URL (e.g. from Imgur) if you want to use your specific 'tal.jpg'.
TAL_IMAGE_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/16/Fox_-_British_Wildlife_Centre_%2817429406401%29.jpg/800px-Fox_-_British_Wildlife_Centre_%2817429406401%29.jpg"

TAL_DESCRIPTION = """
A stylized anthropomorphic fox character named Tal. 
He has the body proportions of a chunky, plush cartoon animal with short legs, rounded limbs, and a slightly oversized head. 
His fur is smooth, golden-brown, with soft shading and a velvety texture. 
He is dressed in a sleek, black tuxedo tailored to his short and round body, including a black bow tie.
The style is high-end 3D animation, similar to Pixar or DreamWorks character design—cute yet expressive.
"""

def search_giphy(query, limit=10):
    """Search Giphy for GIFs matching the query."""
    print(f"\n{'='*60}")
    print(f"SEARCHING GIPHY")
    print(f"{'='*60}")
    print(f"Query: '{query}'")
    
    if not GIPHY_API_KEY:
        print("❌ ERROR: GIPHY_API_KEY not found in .env")
        return []
    
    url = "https://api.giphy.com/v1/gifs/search"
    params = {
        'api_key': GIPHY_API_KEY,
        'q': query,
        'limit': limit,
        'rating': 'g'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        gifs = data.get('data', [])
        
        if not gifs:
            print("❌ No GIFs found for this query")
            return []
        
        print(f"✅ Found {len(gifs)} GIFs")
        
        results = []
        for i, gif in enumerate(gifs, 1):
            results.append({
                'id': gif.get('id'),
                'title': gif.get('title', 'Untitled'),
                'url': gif.get('images', {}).get('original', {}).get('url'),
            })
            print(f"{i}. {results[-1]['title'][:60]}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error searching Giphy: {e}")
        return []

def generate_video_with_legnext(action_description):
    """Generate video using Legnext API."""
    print(f"\n{'='*60}")
    print(f"GENERATING VIDEO WITH LEGNEXT (MIDJOURNEY)")
    print(f"{'='*60}")
    
    url = "https://api.legnext.ai/api/v1/video-diffusion"
    
    # Construct prompt
    # API REQUIRES an image URL at the start of the prompt for Image-to-Video
    full_prompt = f"{TAL_IMAGE_URL} {TAL_DESCRIPTION} ACTION: {action_description}. High quality, 3d render, 4k, cinematic lighting --ar 16:9"
    
    print(f"Prompt: {full_prompt[:150]}...")
    
    payload = {
        "prompt": full_prompt,
        "videoType": 0 # 0 usually implies normal generation or image-to-video if URL is present
    }
    
    headers = {
        "x-api-key": LEGNEXT_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        print("🚀 Sending request to Legnext API...")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return None
            
        data = response.json()
        print(f"✅ Job started successfully!")
        print(f"Response: {data}")
        
        job_id = data.get('jobId') or data.get('messageId')
        
        if job_id:
            print(f"\n🆔 Job ID: {job_id}")
            print(f"⏳ Video generation has started.")
            print(f"👉 Please check your Legnext Dashboard to view/download the video.")
            print(f"   (The API is asynchronous, so the video isn't returned immediately here)")
        else:
            print("⚠️ No Job ID returned, but request was successful.")
            
        return data
        
    except Exception as e:
        print(f"❌ Error calling Legnext: {e}")
        return None

def main():
    print("🦊 TAL MEME GENERATOR (MIDJOURNEY/LEGNEXT EDITION)")
    
    # 1. Search Giphy
    query = input("Enter search query (e.g., 'dancing', 'waving'): ") or "funny"
    gifs = search_giphy(query)
    if not gifs: return
    
    choice = int(input("Select GIF (1-10): ")) - 1
    selected_gif = gifs[choice]
    
    # 2. Get Description (User Input)
    print(f"\nSelected: {selected_gif['title']}")
    print("Describe the action for Tal to perform.")
    print(f"(Press Enter to use default: '{selected_gif['title']}')")
    action = input("Action: ") or selected_gif['title']
    
    # 3. Generate
    generate_video_with_legnext(action)
    
    print("\n✨ Done! Check your Legnext Dashboard.")

if __name__ == "__main__":
    main()
