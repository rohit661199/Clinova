import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        raise ValueError("GEMINI_API_KEY is missing or invalid in .env")
    return genai.Client(api_key=api_key)

if __name__ == "__main__":
    try:
        client = get_gemini_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Say hello!"
        )
        print("Gemini API Test Successful:", response.text)
    except Exception as e:
        print("Gemini API Test Failed:", e)
