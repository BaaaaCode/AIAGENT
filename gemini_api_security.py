# gemini_api_security.py
from dotenv import load_dotenv
import os
import sys
import textwrap

# 외부 라이브러리
try:
    import google.generativeai as genai
except Exception as e:
    print("❌ 'google-generativeai'가 설치되지 않았습니다. 먼저 다음을 실행하세요.")
    print("   pip install google-generativeai python-dotenv")
    sys.exit(1)

def mask_key(key: str) -> str:
    if not key or len(key) < 8:
        return "None"
    return f"{key[:8]}...{key[-4:]}"

def load_env():
    # .env 로드
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

    # 필수값 검증
    if not api_key:
        print(textwrap.dedent("""
        ❌ GEMINI_API_KEY가 설정되지 않았습니다.
           1) 프로젝트 루트에 .env 파일 생성
           2) .env에 다음 줄 추가:
              GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
           3) 다시 실행
        """).strip())
        sys.exit(1)

    return api_key, model

def configure_gemini(api_key: str):
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        print("❌ Gemini 구성 중 오류:", e)
        sys.exit(1)

def quick_test(model_name: str):
    """
    최소 호출 테스트. key 만료/무효, 요금제 문제 등은
    라이브러리에서 예외 메시지로 표출됩니다.
    """
    try:
        model = genai.GenerativeModel(model_name)
        prompt = "Say only the word: OK"
        resp = model.generate_content(prompt)
        text = getattr(resp, "text", "").strip()
        if text.upper() == "OK":
            print("✅ 연결 테스트 성공 (모델:", model_name, ")")
        else:
            print("⚠️ 응답은 받았지만 예상치와 다릅니다 ->", repr(text))
    except Exception as e:
        # 대표적인 오류: API key expired/invalid, 네트워크, 모델명 오타 등
        print("❌ 테스트 요청 중 오류 발생:")
        print("   ", e)
        # 추가 힌트
        print("\n🩹 점검 체크리스트")
        print(" - .env의 GEMINI_API_KEY 값이 올바른지")
        print(" - 모델명이 정확한지 (예: gemini-1.5-pro)")
        print(" - 네트워크/방화벽 문제 없는지")
        sys.exit(1)

def main():
    api_key, model = load_env()
    print("🔐 Loaded API key:", mask_key(api_key))
    print("🤖 Using model   :", model)

    configure_gemini(api_key)
    quick_test(model)

if __name__ == "__main__":
    main()
