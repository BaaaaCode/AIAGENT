# 04-1-1-1.py (pdf to txt)
import os
import fitz  

pdf_file_path = r"C:\AIAGENT\data\2310.08754v4.pdf"   # raw string로 경로 안전하게
output_dir    = r"C:\AIAGENT\output"                 

os.makedirs(output_dir, exist_ok=True)

base = os.path.splitext(os.path.basename(pdf_file_path))[0]
txt_file_path = os.path.join(output_dir, base + ".txt")

with fitz.open(pdf_file_path) as doc:                  # 컨텍스트 매니저로 열고 닫기 자동
    with open(txt_file_path, "w", encoding="utf-8") as f:
        for page in doc:
            f.write(page.get_text("text"))             # 기본 텍스트 추출
            f.write("\n")                              # 페이지 구분용 줄바꿈

print("Saved:", txt_file_path)