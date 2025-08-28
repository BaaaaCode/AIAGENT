import os
import sys
import google.generativeai as genai

PROMPT = "2022년 월드컵 우승 팀은 어디야?"

def get_api_key():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "환경 변수 GEMINI_API_KEY가 설정되어 있지 않습니다.\n"
            "PowerShell에서 다음 중 하나를 먼저 실행하세요:\n"
            '  - 임시(현재 세션만):  $env:GEMINI_API_KEY = "YOUR_API_KEY"\n'
            '  - 영구(새 터미널부터): setx GEMINI_API_KEY "YOUR_API_KEY"\n'
        )
    return key

def extract_text(response) -> str:
    # SDK 버전별 안전 추출
    if hasattr(response, 'text') and response.text:
        return response.text
    if getattr(response, 'candidates', None):
        cand = response.candidates[0]
        parts = getattr(cand, 'content', getattr(cand, 'content', None))
        if parts and getattr(parts, 'parts', None):
            part0 = parts.parts[0]
            return getattr(part0, 'text', str(part0))
    return "응답을 파싱할 수 없습니다. SDK 버전을 확인하세요."

def main():
    try:
        api_key = get_api_key()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-pro")
        resp = model.generate_content(PROMPT)
        print(extract_text(resp))
        print('----')
        print("응답 완료")
        
    except Exception as e:
        print(f"오류 발생: {e}", file=sys.stderr)
        sys.exit(1)
        
if __name__ == "__main__":
    main()