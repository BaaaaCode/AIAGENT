# 03-1-2-1 (Non-multi-turn)
from dotenv import load_dotenv
import google.generativeai as genai
import sys
import os

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("[Error] 환경 변수 GEMINI_API_KEY가 없습니다. .env에 넣거나 세션에 설정하세요.", file=sys.stderr)
    sys.exit(1)
    
genai.configure(api_key=api_key)

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    system_instruction="너는 유치원생이야. 유치원생처럼 답변해줘."
)
def safe_text(resp) -> str:
    """SDK 버전 차이를 대비해 응답 텍스트를 안전하게 추출"""
    if getattr(resp, "text", None):
        return resp.text.strip()
    if getattr(resp, "candidates", None):
        cand = resp.candidates[0]
        content = getattr(cand, "content", None)
        parts = getattr(content, "parts", None) if content else None
        if parts and len(parts) > 0:
            first = parts[0]
            return getattr(first, "text", str(first)).strip()
    return "(응답을 파싱하지 못했어요)"

print("Type 'exit' to quit.")
while True:
    try:
        user_input = input("You: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nBye!")
        break

    if user_input.lower() == "exit":
        break
    if not user_input:
        continue  # 빈 입력은 무시

    try:
        # Non-multi-turn: 매 질문을 독립 호출
        resp = model.generate_content(
            user_input,
            generation_config={
                "temperature": 0.7,
                # 필요하면 아래 옵션도 사용 가능:
                # "max_output_tokens": 512,
                # "top_p": 0.9,
                # "top_k": 40,
            },
        )
        print("Gemini:", safe_text(resp))
    except Exception as e:
        print(f"[Error] {e}", file=sys.stderr)