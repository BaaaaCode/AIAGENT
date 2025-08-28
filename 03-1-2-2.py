# 03-1-2-2 (Multi-turn)
from dotenv import load_dotenv
import google.generativeai as genai
import os, sys

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("[Error] GEMINI_API_KEY가 없습니다. .env에 넣거나 세션에 설정하세요.", file=sys.stderr)
    sys.exit(1)

genai.configure(api_key=api_key)

model = genai.GenerativeModel(
    model_name="gemini-1.5-pro",
    system_instruction="너는 말하는 감자야. 감자처럼 답변해줘"
)

def safe_text(resp) -> str:
    if getattr(resp, "text", None):
        return resp.text.strip()
    if getattr(resp, "candidates", None):
        cand = resp.candidates[0]
        content = getattr(cand, "content", None)
        parts = getattr(content, "parts", None) if content else None
        if parts:
            first = parts[0]
            return getattr(first, "text", str(first)).strip()
    return "(응답을 파싱하지 못했어요)"

# 👉 멀티턴: 세션(대화 객체) 시작
# 필요하면 few-shot 히스토리를 미리 심을 수 있음 (예시는 주석 참고)
chat = model.start_chat(
    history=[
        # {"role":"user","parts":["참새"]},
        # {"role":"model","parts":["짹짹"]},
    ]
)

print("Type 'exit' to quit.  /reset 으로 대화 초기화")
while True:
    try:
        user_input = input("You: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nBye!")
        break

    if not user_input:
        continue
    if user_input.lower() == "exit":
        break
    if user_input.lower() == "/reset":
        chat = model.start_chat(history=[])  # 히스토리 초기화
        print("Gemini: 대화를 새로 시작할게요!")
        continue

    try:
        # 멀티턴: 같은 chat 객체에 누적 전송
        resp = chat.send_message(
            user_input,
            generation_config={
                "temperature": 0.7,
                # "max_output_tokens": 256,
            },
        )
        print("Gemini:", safe_text(resp))
    except Exception as e:
        print(f"[Error] {e}", file=sys.stderr)