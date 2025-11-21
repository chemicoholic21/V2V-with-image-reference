import os
import json
import base64
import time
import requests
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.auth.transport import requests as google_requests
from google.cloud import aiplatform

# Load environment variables
load_dotenv()

# API Keys
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") # For Gemini analysis

# Vertex AI Configuration
CREDENTIALS_FILE = "vertex_credentials.json"
REFERENCE_IMAGE_PATH = "reference image/tal.jpg"
LOCATION = "us-central1"

def load_credentials():
    """Load service account credentials from JSON file."""
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ ERROR: {CREDENTIALS_FILE} not found!")
        return None, None
    
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            creds_data = json.load(f)
        
        project_id = creds_data.get('project_id')
        
        credentials = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        return credentials, project_id
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        return None, None

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

def download_gif(gif_url, output_path):
    """Download a GIF from URL."""
    print(f"\n📥 Downloading GIF for reference...")
    try:
        response = requests.get(gif_url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Downloaded to: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error downloading: {e}")
        return False

def analyze_gif_with_gemini(gif_path):
    """Analyze the GIF using Gemini Vision."""
    print(f"\n{'='*60}")
    print(f"ANALYZING GIF WITH GEMINI")
    print(f"{'='*60}")
    
    if not GOOGLE_API_KEY:
        print("⚠️ GOOGLE_API_KEY not found. Using fallback description.")
        return "A character performing an action."

    try:
        from PIL import Image
        
        # Extract a frame
        gif = Image.open(gif_path)
        gif.seek(gif.n_frames // 2) # Middle frame
        frame = gif.convert('RGB')
        
        temp_path = "temp_frame.jpg"
        frame.save(temp_path)
        
        with open(temp_path, 'rb') as f:
            frame_b64 = base64.b64encode(f.read()).decode()
            
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GOOGLE_API_KEY}"
        
        prompt = "Describe the ACTION in this image concisely. E.g. 'dancing', 'waving', 'laughing'."
        
        payload = {
            "contents": [{"parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": frame_b64}}
            ]}]
        }
        
        response = requests.post(api_url, json=payload)
        
        if response.status_code == 200:
            desc = response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            print(f"✅ Detected Action: {desc}")
            if os.path.exists(temp_path): os.remove(temp_path)
            return desc
        else:
            print(f"⚠️ Analysis failed: {response.status_code}")
            return "character moving"
            
    except Exception as e:
        print(f"⚠️ Error analyzing GIF: {e}")
        return "character moving"

def generate_veo_video(credentials, project_id, prompt, reference_image_path):
    """Generate video using Veo (Vertex AI)."""
    print(f"\n{'='*60}")
    print(f"GENERATING VIDEO WITH VEO (VERTEX AI)")
    print(f"{'='*60}")
    
    try:
        # Load reference image
        with open(reference_image_path, 'rb') as f:
            reference_image_b64 = base64.b64encode(f.read()).decode()
            
        # Get access token
        credentials.refresh(google_requests.Request())
        access_token = credentials.token
        
        # Endpoint
        # Available models: 
        # - veo-2.0-generate-001 (Stable, generally available)
        # - veo-3.0-generate-001 (Preview, very limited quota)
        MODEL_ID = "veo-3.1-generate" 
        
        endpoint = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{LOCATION}/publishers/google/models/{MODEL_ID}:predict"
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "instances": [{
                "prompt": prompt,
                "referenceImage": {
                    "bytesBase64Encoded": reference_image_b64
                },
                "parameters": {
                    "videoDurationSeconds": 5,
                    "aspectRatio": "16:9",
                    "guidanceScale": 8.0
                }
            }]
        }
        
        print(f"🚀 Sending request to Vertex AI ({endpoint})...")
        print("⏳ This may take 1-2 minutes...")
        
        response = requests.post(endpoint, headers=headers, json=payload, timeout=180)
        
        if response.status_code != 200:
            print(f"❌ API Error ({response.status_code}): {response.text}")
            return None
            
        result = response.json()
        predictions = result.get('predictions', [])
        
        if not predictions:
            print("❌ No predictions returned.")
            return None
            
        video_data = predictions[0]
        
        if 'videoBase64' in video_data:
            return base64.b64decode(video_data['videoBase64'])
        elif 'gcsUri' in video_data:
            print(f"⚠️ Video saved to GCS: {video_data['gcsUri']}")
            return None # Or handle GCS download if needed
            
        return None

    except Exception as e:
        print(f"❌ Error generating video: {e}")
        return None

def main():
    print("🦊 TAL MEME GENERATOR (VEO EDITION)")
    
    # 0. Check Credentials
    credentials, project_id = load_credentials()
    if not credentials: return
    
    if not os.path.exists(REFERENCE_IMAGE_PATH):
        print(f"❌ Reference image not found: {REFERENCE_IMAGE_PATH}")
        return

    # 1. Search Giphy
    query = input("Enter search query: ") or "funny"
    gifs = search_giphy(query)
    if not gifs: return
    
    choice = int(input("Select GIF (1-10): ")) - 1
    selected_gif = gifs[choice]
    
    # 2. Download & Analyze
    os.makedirs("downloads", exist_ok=True)
    gif_path = f"downloads/ref_{selected_gif['id']}.gif"
    download_gif(selected_gif['url'], gif_path)
    
    action = analyze_gif_with_gemini(gif_path)
    
    # 3. Generate
    prompt = f"A video of Tal the fox character, {action}. The character has smooth golden-brown fur, wearing a black tuxedo. High quality, 3d animation style."
    
    video_bytes = generate_veo_video(credentials, project_id, prompt, REFERENCE_IMAGE_PATH)
    
    if video_bytes:
        os.makedirs("output", exist_ok=True)
        output_path = f"output/tal_veo_{selected_gif['id']}.mp4"
        with open(output_path, 'wb') as f:
            f.write(video_bytes)
        print(f"\n✅ SUCCESS! Video saved to: {output_path}")
    else:
        print("\n❌ Failed to generate video.")

if __name__ == "__main__":
    main()
