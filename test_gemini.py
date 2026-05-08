import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("沒有讀到 GEMINI_API_KEY，請檢查 .env 是否在專案根目錄")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="請用一句話回答：你有成功連線嗎？"
)

print(response.text)