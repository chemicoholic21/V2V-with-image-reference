import os
import time
import requests
import base64
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Key
BASEDLABS_API_KEY = os.getenv("BASEDLABS_API_KEY")

# Configuration
BASE_URL = "https://modelslab.com/api/v1/enterprise/video/img2video"
REFERENCE_IMAGE_PATH = "reference image/tal.jpg"

def encode_image_to_base64(image_path):
    """Encodes a local image file to a base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string
    except FileNotFoundError:
        print(f"❌ Error: Image file not found at {image_path}")
        return None
    except Exception as e:
        print(f"❌ Error encoding image: {e}")
        return None

def generate_video_basedlabs(action_description):
    """Generates a video using BasedLabs API."""
    print(f"\n{'='*60}")
    print(f"GENERATING VIDEO WITH BASEDLABS (SVD)")
    print(f"{'='*60}")
    
    if not BASEDLABS_API_KEY:
        print("❌ ERROR: BASEDLABS_API_KEY not found in .env")
        return

    # 1. Encode Image
    print(f"📥 Loading reference image: {REFERENCE_IMAGE_PATH}...")
    init_image_b64 = encode_image_to_base64(REFERENCE_IMAGE_PATH)
    if not init_image_b64:
        return

    # 2. Prepare Payload
    # BasedLabs / ModelsLab SVD Endpoint Parameters
    payload = json.dumps({
        "key": BASEDLABS_API_KEY,
        "model_id": "svd", # Stable Video Diffusion
        "init_image": init_image_b64,
        "height": 512,
        "width": 512, # SVD often works best with 512x512 or 1024x576
        "num_frames": 25,
        "motion_bucket_id": 127, # Controls amount of motion
        "fps": 6,
        "seed": -1, # Random seed
        "output_type": "mp4",
        "instant_response": False # We want to wait or get a webhook, but let's try standard sync/async check
    })

    headers = {
        'Content-Type': 'application/json'
    }

    try:
        print("🚀 Sending request to BasedLabs...")
        response = requests.post(BASE_URL, headers=headers, data=payload)
        
        if response.status_code != 200:
            print(f"❌ API Error ({response.status_code}): {response.text}")
            return

        data = response.json()
        print(f"✅ Request sent successfully!")
        print(f"Response: {data}")
        
        # Check for output
        # The API might return the video URL directly or a job ID.
        # Based on typical ModelsLab responses:
        if data.get("status") == "success" and data.get("output"):
             video_urls = data.get("output", [])
             if video_urls:
                 print(f"\n🎉 Video Generated: {video_urls[0]}")
                 return video_urls[0]
        
        elif data.get("status") == "processing":
             id = data.get("id")
             print(f"⏳ Processing... Job ID: {id}")
             print("   (You may need to check the dashboard or implement polling if this API supports it)")
             # Simple polling if 'fetch_result' endpoint exists, but for now just reporting.
             if data.get("future_links"):
                 print(f"🔮 Future Link (check in a minute): {data['future_links'][0]}")
                 return data['future_links'][0]

    except Exception as e:
        print(f"❌ Error calling BasedLabs: {e}")

def main():
    print("🦊 TAL MEME GENERATOR (BASEDLABS EDITION)")
    
    if not os.path.exists(REFERENCE_IMAGE_PATH):
        print(f"❌ Reference image not found: {REFERENCE_IMAGE_PATH}")
        return

    # Get User Input
    print("\nDescribe the action for Tal to perform (e.g., 'dancing', 'waving', 'laughing').")
    action = input("Action: ")
    
    if not action:
        print("❌ No action provided.")
        return

    # Generate
    generate_video_basedlabs(action)

if __name__ == "__main__":
    main()
