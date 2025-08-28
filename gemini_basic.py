import google.generativeai as genai

api_key = "AIzaSyBh01BK__FDm4qDHoU45lIuxxYzUEsKI_I"
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-1.5-pro")

try:
    response = model.generate_content("2022년 월드컵 우승 팀은 어디야?")
    print(response.text)
    print('----')
    print("응답 완료!")
    
except Exception as e:
    print(f"오류 발생: {e}")
    