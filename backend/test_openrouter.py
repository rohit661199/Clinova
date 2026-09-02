import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def get_openrouter_client():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or api_key == "your_openrouter_api_key_here":
        raise ValueError("OPENROUTER_API_KEY is missing or invalid in .env")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

if __name__ == "__main__":
    try:
        client = get_openrouter_client()
        response = client.chat.completions.create(
            model="google/gemini-2.5-flash", # Or any other model available on OpenRouter
            messages=[
                {"role": "user", "content": "Say hello!"}
            ],
            max_tokens=200
        )
        print("OpenRouter API Test Successful:", response.choices[0].message.content)
    except Exception as e:
        print("OpenRouter API Test Failed:", e)
