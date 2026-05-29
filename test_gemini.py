from google import genai

from services.ai_service import get_gemini_api_key, get_gemini_model_candidates, get_gemini_setup_status

api_key = get_gemini_api_key()

if not api_key:
    raise ValueError("沒有讀到有效的 GEMINI_API_KEY，請檢查 .env 是否在專案根目錄")

client = genai.Client(api_key=api_key)

print("Gemini setup:", get_gemini_setup_status())

last_error = None
for model in get_gemini_model_candidates():
    try:
        response = client.models.generate_content(
            model=model,
            contents="請用一句話回答：你有成功連線嗎？"
        )
    except Exception as exc:
        last_error = exc
        print(f"{model} failed: {type(exc).__name__}: {str(exc)[:300]}")
        continue
    print(f"{model} ok:")
    print(response.text)
    break
else:
    raise RuntimeError(f"Gemini 測試失敗：{type(last_error).__name__}: {last_error}")
