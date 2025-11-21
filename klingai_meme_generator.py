import os
import time
import requests
import json
import base64
import jwt # pip install pyjwt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys (Provided by User)
ACCESS_KEY = "A3G4tbHnHYDyaTeQETbLYJH9RmFT8fmJ"
SECRET_KEY = "TTFdbLynPLdGgAGpQFtA9gGMmgydbart klingai" # Note: " klingai" might be a typo in copy-paste, assuming just the code part if it looks weird, but "TTF...klingai" could be the whole key. I'll use it as provided but strip whitespace.
# The user wrote "TTFdbLynPLdGgAGpQFtA9gGMmgydbart klingai". 
# "klingai" at the end looks like a label. I will strip it.
SECRET_KEY_CLEAN = "TTFdbLynPLdGgAGpQFtA9gGMmgydbart" 

GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")

# Configuration
# Endpoint from research: https://api.klingai.com/v1/videos/image2video
# Or https://api-singapore.klingai.com/v1/videos/image2video
BASE_URL = "https://api.klingai.com/v1" 

TAL_DESCRIPTION = """
A stylized anthropomorphic fox character named Tal. 
He has the body proportions of a chunky, plush cartoon animal with short legs, rounded limbs, and a slightly oversized head. 
His fur is smooth, golden-brown, with soft shading and a velvety texture. 
He is dressed in a sleek, black tuxedo tailored to his short and round body, including a black bow tie.
The style is high-end 3D animation, similar to Pixar or DreamWorks character design—cute yet expressive.
"""

def generate_jwt(ak, sk):
    """Generate JWT token for KlingAI authentication."""
    headers = {
        "alg": "HS256",
        "typ": "JWT"
    }
    payload = {
        "iss": ak,
        "exp": int(time.time()) + 1800, # 30 mins validity
        "nbf": int(time.time()) - 5
    }
    token = jwt.encode(payload, sk, algorithm="HS256", headers=headers)
    return token

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

def generate_video_with_kling(action_description):
    """Generate video using KlingAI API."""
    print(f"\n{'='*60}")
    print(f"GENERATING VIDEO WITH KLING AI")
    print(f"{'='*60}")
    
    # 1. Generate Token
    try:
        token = generate_jwt(ACCESS_KEY, SECRET_KEY_CLEAN)
        print("✅ JWT Token generated.")
    except Exception as e:
        print(f"❌ Error generating JWT: {e}")
        return

    # 2. Prepare Image
    image_data = ""
    try:
        with open("reference image/tal.jpg", "rb") as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
            print("✅ Loaded reference image: reference image/tal.jpg")
    except Exception as e:
        print(f"❌ Could not load reference image: {e}")
        return

    # 3. Call API
    url = f"{BASE_URL}/videos/image2video"
    
    full_prompt = f"{TAL_DESCRIPTION} ACTION: {action_description}. High quality, 3d render, 4k, cinematic lighting."
    print(f"Prompt: {full_prompt[:150]}...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model_name": "kling-v1", # Assuming default model name, might need adjustment
        "image": image_data,
        "prompt": full_prompt,
        "cfg_scale": 0.5
    }
    
    try:
        print(f"🚀 Sending request to KlingAI ({url})...")
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            print(f"❌ Error ({response.status_code}): {response.text}")
            return
            
        data = response.json()
        print(f"✅ Request successful!")
        print(f"Response: {data}")
        
        task_id = data.get('data', {}).get('task_id')
        if task_id:
            print(f"\n🆔 Task ID: {task_id}")
            print("⏳ Video generation started. Please check your KlingAI dashboard or query the status.")
            # Note: We could implement polling here if we knew the exact status endpoint.
        
    except Exception as e:
        print(f"❌ Error calling KlingAI: {e}")

def main():
    print("🦊 TAL MEME GENERATOR (KLING AI EDITION)")
    
    # 1. Search Giphy
    query = input("Enter search query (e.g., 'dancing', 'waving'): ") or "funny"
    gifs = search_giphy(query)
    if not gifs: return
    
    choice = int(input("Select GIF (1-10): ")) - 1
    selected_gif = gifs[choice]
    
    # 2. Get Description
    print(f"\nSelected: {selected_gif['title']}")
    action = input("Action: ") or selected_gif['title']
    
    # 3. Generate
    generate_video_with_kling(action)

if __name__ == "__main__":
    main()
