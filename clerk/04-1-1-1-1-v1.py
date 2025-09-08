# 04-1-1-1.py (pdf to txt + clean + chunk)
import re, unicodedata, os, pathlib

def clean_arxiv_text(text: str) -> str:
    # 1 유니코드 정규화
    text = unicodedata.normalize("NFKC", text)

    # 2 페이지 머리/바닥글, arXiv 라인, 단독 페이지 번호 제거
    lines = []
    for line in text.splitlines():
        if re.search(r'arXiv:\d{4}\.\d{5,}(v\d+)?', line):
            continue
        if re.match(r'^\s*\d+\s*$', line):  # standalone page number
            continue
        lines.append(line.rstrip())
    text = "\n".join(lines)

    # 3) 하이픈 줄바꿈(“토큰-\nization” → “토큰ization”)
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)

    # 4) 문장 내부 줄바꿈은 공백으로, 2줄 이상은 단락 구분 유지
    text = text.replace("\r", "")
    # 먼저 단락 경계를 보존하기 위해 빈 줄 2개 이상을 토큰으로 치환
    text = re.sub(r'\n{2,}', '<<<PARA>>>', text)
    # 남은 한 줄 개행은 공백으로
    text = re.sub(r'\n', ' ', text)
    # 단락 토큰 복원
    text = re.sub(r'\s*<<<PARA>>>\s*', '\n\n', text)

    # 5) 섹션 헤더에 줄바꿈 보강 (숫자 헤더/전형적 헤더 키워드)
    text = re.sub(r'\s*(^|\n)(\d+(\.\d+)*\s+[A-Z][^\n]{1,120})\s*',
                  lambda m: f"\n\n{m.group(2).strip()}\n\n", text)

    # 6) 그림/표 캡션 태깅
    text = re.sub(r'(Figure\s+\d+\s*:)', r'[FIGURE] \1', text, flags=re.IGNORECASE)
    text = re.sub(r'(Table\s+\d+\s*:)',  r'[TABLE] \1',  text, flags=re.IGNORECASE)

    # 7) 과도한 공백 정리
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text

def split_into_chunks(text: str, max_chars=2500):
    chunks, buf = [], []
    count = 0
    for para in text.split("\n\n"):
        p = para.strip()
        if not p:
            continue
        if count + len(p) + 2 > max_chars and buf:
            chunks.append("\n\n".join(buf))
            buf, count = [], 0
        buf.append(p)
        count += len(p) + 2
    if buf:
        chunks.append("\n\n".join(buf))
    return chunks

# 사용 예시
inp = r"C:\AIAGENT\output\2310.08754v4.txt"
out = r"C:\AIAGENT\output\2310.08754v4.cleaned.txt"

raw = pathlib.Path(inp).read_text(encoding="utf-8", errors="ignore")
cleaned = clean_arxiv_text(raw)
pathlib.Path(out).write_text(cleaned, encoding="utf-8")
print("Saved:", out, "| chunks:", len(split_into_chunks(cleaned)))