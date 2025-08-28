# 04-1-1-1.py(pdf to txt)
import fitz
import os

pdf_file_path = r"C:\AIAGENT\data\2310.08754v4.pdf"
doc = fitz.open(pdf_file_path)

full_text = ''

for page in doc:
    text = page.get_text()
    full_text += text
    
pdf_file_name = os.path.basename(pdf_file_path)
pdf_file_name = os.path.splitext(pdf_file_name)[0]

txt_file_path = f"C:\AIAGENT\outpu/{pdf_file_name}.txt"
with open(txt_file_path, 'w', encoding='utf-8') as f:
    f.write(full_text)