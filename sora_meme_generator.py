import os
import time
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

OPENAI_KEY = os.getenv("OPEN_AI_KEY")
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")

SORA_MODEL = "sora-1.1"  # official model

TAL_DESCRIPTION = """
A stylized anthropomorphic fox character named Tal. 
Chunky plush proportions, short legs, rounded limbs, oversized head. 
Golden brown smooth fur, velvety texture. 
Wearing a sleek black tuxedo and black bow tie.
High-end Pixar/DreamWorks style, expressive and cute.
"""


# -----------------------------
# GIPHY SEARCH
# -----------------------------

def search_giphy(query):
    url = "https://api.giphy.com/v1/gifs/search"
    params = {
        "api_key": GIPHY_API_KEY,
        "q": query,
        "limit": 10,
        "rating": "g"
    }

    print("\n============================================================")
    print("SEARCHING GIPHY")
    print("============================================================")
    print(f"Query: '{query}'")

    res = requests.get(url, params=params)
    data = res.json().get("data", [])

    if not data:
        print("❌ No results")
        return []

    print(f"✅ Found {len(data)} GIFs\n")

    results = []
    for i, gif in enumerate(data, start=1):
        title = gif.get("title", "Untitled")
        results.append({
            "id": gif["id"],
            "title": title,
            "url": gif["images"]["downsized"]["url"],
        })
        print(f"{i}. {title}")

    return results


# -----------------------------
# SORA VIDEO GENERATION
# -----------------------------

def sora_generate_video(action_text):
    print("\n============================================================")
    print(f"GENERATING VIDEO WITH SORA ({SORA_MODEL})")
    print("============================================================")

    # Encode reference image
    try:
        with open("reference image/tal.jpg", "rb") as f:
            ref_image = base64.b64encode(f.read()).decode()
            print("✅ Loaded reference image")
    except Exception as e:
        print("⚠️ No reference image found, continuing without it")
        ref_image = None

    # Build prompt
    prompt = f"{TAL_DESCRIPTION}\nACTION: {action_text}\nHigh quality 3D cinematic animation."

    payload = {
        "model": SORA_MODEL,
        "prompt": prompt,
        "max_output_tokens": 2048
    }

    if ref_image:
        payload["reference_images"] = [ref_image]

    headers = {
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json"
    }

    # Create Sora job
    print("🚀 Sending job to Sora...")
    job = requests.post("https://api.openai.com/v1/videos", json=payload, headers=headers)

    if job.status_code != 200:
        print(f"❌ Error ({job.status_code}): {job.text}")
        return None

    job_id = job.json()["id"]
    print(f"⏳ Job ID: {job_id}")

    # Poll job status
    poll_url = f"https://api.openai.com/v1/videos/{job_id}"

    while True:
        time.sleep(5)
        poll = requests.get(poll_url, headers=headers).json()
        status = poll.get("status")

        print(f"📡 Status: {status}")

        if status == "completed":
            video_url = poll["video"]["url"]
            print(f"\n🎉 VIDEO READY: {video_url}")
            return video_url

        if status == "failed":
            print("❌ Sora generation failed")
            return None


# -----------------------------
# MAIN
# -----------------------------

def main():
    print("🦊 TAL MEME GENERATOR (SORA EDITION)")

    query = input("Enter search query: ") or "funny"
    gifs = search_giphy(query)
    if not gifs: return

    choice = int(input("Select GIF (1-10): ")) - 1
    selected = gifs[choice]

    print(f"\nSelected: {selected['title']}")
    action = input("Action: ") or selected["title"]

    sora_generate_video(action)


if __name__ == "__main__":
    main()
