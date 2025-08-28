# 03-1-1-3 (one_prompting)

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

prompt = """규칙: 동물 이름을 주면 그 동물의 울음소리만 하늘 의성어로 한 줄로 답해
예시: 
입력: 참새
출력: 짹짹

입력: 오리
출력: """

try:
    response = model.generate_content(prompt, 
                                       generation_config = {"temperature":0.9} # 답변 설정 
    )
    print(response.text) 
except Exception as e:
    print(f"[Error] {e}", file=sys.stderr)
    sys.exit(1)