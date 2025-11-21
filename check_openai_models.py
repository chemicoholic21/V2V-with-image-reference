import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPEN_AI_KEY")
if not api_key:
    print("❌ No OPEN_AI_KEY found in .env")
    exit()

client = OpenAI(api_key=api_key)

print("🔑 Checking available models for provided API key...")

try:
    models = client.models.list()
    video_models = [m.id for m in models if "sora" in m.id or "video" in m.id]
    
    if video_models:
        print(f"✅ Found video models: {video_models}")
    else:
        print("⚠️ No explicit 'sora' or 'video' models found in the public list.")
        print("Listing first 10 models to verify connection:")
        for m in list(models)[:10]:
            print(f" - {m.id}")
            
except Exception as e:
    print(f"❌ Error listing models: {e}")
