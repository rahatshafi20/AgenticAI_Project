import os
import requests
from dotenv import load_dotenv
from groq import Groq
import chromadb
from langgraph.graph import StateGraph

load_dotenv()

# Test Groq LLM
print("Testing Groq...")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Say hello in one word."}]
)
print("Groq LLM:", response.choices[0].message.content)

# Test Pollinations (image generation - no key needed)
print("\nTesting Pollinations image generation...")
image_prompt = "a fantasy warrior, portrait, high quality"
url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(image_prompt)}?width=512&height=512&nologo=true"
img_response = requests.get(url, timeout=30)
if img_response.status_code == 200:
    with open("outputs/images/test_image.jpg", "wb") as f:
        f.write(img_response.content)
    print("Pollinations Image: Generated and saved to outputs/images/test_image.jpg")
else:
    print("Pollinations Image: Failed -", img_response.status_code)

# Test ChromaDB
print("\nTesting ChromaDB...")
chroma_client = chromadb.Client()
collection = chroma_client.create_collection("test")
print("ChromaDB: Working")

# Test LangGraph
print("\nTesting LangGraph...")
graph = StateGraph(dict)
print("LangGraph: Working")

print("\n✅ All systems go! Ready to build.")