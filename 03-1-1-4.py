# 03-1-1-4 (few_prompting)

from dotenv import load_dotenv
import google.generativeai as genai
import os
import sys

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("[Error] 환경 변수 GEMINI_API_KEY가 설정되어 있지 않습니다. .env에 넣거나 세션에 설정하세요", file=sys.stderr)
    sys.exit(1)
    
genai.configure(api_key = api_key)

model = genai.GenerativeModel("gemini-1.5-pro",
                              system_instruction="너는 유치원생이야. 유치원생처럼 답변해줘 ") # MODEL 설정

prompt = """규칙: 동물 이름의 마지막 글자로 시작하는 어린이 단어 1개만 출력.
제약: 한글 단어 1개, 6자 이내, 일반명사 느낌. 모르면 '모름'.

예시:
입력: 강아지
출력: 지구
입력: 코끼리
출력: 리본
입력: 참새
출력: 새싹
입력: 토끼
출력: 끼리끼리
입력: 드래곤
출력: 모름

입력: 곰
출력:"""

try:
    response = model.generate_content(prompt, 
                                       generation_config = {"temperature":0.9} # 답변 설정 
    )
    print(response.text) 
except Exception as e:
    print(f"[Error] {e}", file=sys.stderr)
    sys.exit(1)