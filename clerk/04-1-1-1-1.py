# 04-1-1-1.py (pdf to txt + clean + chunk)
# 04-1-1-all_in_one.py
# PDF → raw txt → cleaned txt → chunks → chunk summaries → final brief
import os, sys, re, unicodedata, pathlib, argparse, time
import fitz  # PyMuPDF
from dotenv import load_dotenv
import google.generativeai as genai

# ---------------- Utils ----------------
def clean_arxiv_text(text: str) -> str:
    # 1) 유니코드 정규화
    text = unicodedata.normalize("NFKC", text)

    # 2) arXiv 라인/단독 페이지 번호 제거
    lines = []
    for line in text.splitlines():
        if re.search(r'arXiv:\d{4}\.\d{5,}(v\d+)?', line):
            continue
        if re.match(r'^\s*\d+\s*$', line):  # standalone page number
            continue
        lines.append(line.rstrip())
    text = "\n".join(lines)

    # 3) 하이픈 줄바꿈 결합: "hyphen-\nation" -> "hyphenation"
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)

    # 4) 단락/개행 정리
    text = text.replace("\r", "")
    text = re.sub(r'\n{2,}', '<<<PARA>>>', text)   # 단락 토큰
    text = re.sub(r'\n', ' ', text)                # 문장 내부 개행 → 공백
    text = re.sub(r'\s*<<<PARA>>>\s*', '\n\n', text)  # 단락 복원

    # 5) 섹션 헤더 보강 (숫자 헤더/타이틀)
    text = re.sub(
        r'\s*(^|\n)(\d+(\.\d+)*\s+[A-Z][^\n]{1,120})\s*',
        lambda m: f"\n\n{m.group(2).strip()}\n\n",
        text
    )

    # 6) 그림/표 캡션 태깅
    text = re.sub(r'(Figure\s+\d+\s*:)', r'[FIGURE] \1', text, flags=re.IGNORECASE)
    text = re.sub(r'(Table\s+\d+\s*:)',  r'[TABLE] \1',  text, flags=re.IGNORECASE)

    # 7) 과도 공백 정리
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text

def split_into_chunks(text: str, max_chars=2500):
    chunks, buf, count = [], [], 0
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

def safe_text(resp) -> str:
    # SDK 버전 차이를 대비해 응답 텍스트 안전 추출
    if getattr(resp, "text", None):
        return resp.text.strip()
    if getattr(resp, "candidates", None):
        cand = resp.candidates[0]
        content = getattr(cand, "content", None)
        parts = getattr(content, "parts", None) if content else None
        if parts and len(parts) > 0:
            first = parts[0]
            return getattr(first, "text", str(first)).strip()
    return "(응답 파싱 실패)"

# ---------------- Gemini prompts ----------------
CHUNK_PROMPT_TMPL = """역할: 당신은 논문을 읽고 핵심을 뽑아내는 한국어 AI 연구원입니다.
규칙:
1) 아래 본문 범위 안에서만 요약하고 추정/환각 금지.
2) 핵심 주장(Claim), 방법(Method), 수치/증거(Evidence/Numbers), 한계(Limitations)를 항목별 bullet로.
3) 인용 번호([12])나 각주 마커는 제거.
입력(메타): section="{section}", pages="{pages}"
본문:
{body}

출력 형식(그대로 유지):
- Claim:
- Method:
- Evidence/Numbers:
- Limitations:
"""

FINAL_PROMPT_TMPL = """역할: 당신은 여러 섹션 요약을 통합해 '연구 브리프'를 쓰는 한국어 AI 연구원입니다.
규칙:
1) 아래 요약들을 교차검증하여 일관성 있게 통합.
2) 없는 사실을 만들지 말고, 숫자는 반올림 없이 그대로 유지.
3) 길이는 300~600자, 간결하고 구조적으로.
출력 섹션:
- TL;DR(3문장)
- 문제정의
- 방법 한 줄 요약
- 핵심 결과(숫자 포함, 2~4개 bullet)
- 한계/위협
- 실무적 시사점

[입력: 섹션 요약들]
{joined}
"""

def summarize_chunk(model, chunk_text, section="Unknown", pages="NA",
                    temperature=0.3, max_tokens=512):
    prompt = CHUNK_PROMPT_TMPL.format(section=section, pages=pages, body=chunk_text)
    resp = model.generate_content(
        prompt,
        generation_config={"temperature": temperature, "max_output_tokens": max_tokens}
    )
    return safe_text(resp)

def combine_summaries(model, summaries, temperature=0.25, max_tokens=768):
    joined = "\n\n---\n\n".join(summaries)
    prompt = FINAL_PROMPT_TMPL.format(joined=joined)
    resp = model.generate_content(
        prompt,
        generation_config={"temperature": temperature, "max_output_tokens": max_tokens}
    )
    return safe_text(resp)

# ---------------- Main ----------------
def main():
    parser = argparse.ArgumentParser(description="PDF→TXT→Clean→Chunk→Summarize pipeline")
    parser.add_argument("--pdf", required=True, help="PDF file path")
    parser.add_argument("--outdir", default="output", help="Output directory")
    parser.add_argument("--model", default="gemini-1.5-pro", help="Gemini model name")
    parser.add_argument("--max-chars", type=int, default=2500, help="Max chars per chunk")
    parser.add_argument("--keep-refs", action="store_true", help="Keep References section")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[Error] GEMINI_API_KEY가 없습니다. .env에 키를 넣으세요.", file=sys.stderr)
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=args.model,
        system_instruction="당신은 문서와 논문을 분석·요약하는 한국어 AI 연구원입니다. 정확하고 간결하게 답하세요."
    )

    pdf_path = pathlib.Path(args.pdf)
    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    stem = pdf_path.stem

    # 1) PDF → raw text
    print("[1/5] Extracting text from PDF ...")
    pages = []
    with fitz.open(str(pdf_path)) as doc:
        for pg in doc:
            pages.append(pg.get_text("text"))
    raw_text = "\n\n".join(pages)
    raw_file = outdir / f"{stem}.raw.txt"
    raw_file.write_text(raw_text, encoding="utf-8")
    print("  Saved:", raw_file)

    # 2) Clean
    print("[2/5] Cleaning text ...")
    cleaned = clean_arxiv_text(raw_text)
    if not args.keep_refs:
        cleaned = re.split(r'\n\s*References\s*\n', cleaned, maxsplit=1)[0]
    clean_file = outdir / f"{stem}.clean.txt"
    clean_file.write_text(cleaned, encoding="utf-8")
    print("  Saved:", clean_file)

    # 3) Chunk
    print("[3/5] Splitting into chunks ...")
    chunks = split_into_chunks(cleaned, max_chars=args.max_chars)
    chunks_file = outdir / f"{stem}.chunks.txt"
    with chunks_file.open("w", encoding="utf-8") as f:
        for i, ch in enumerate(chunks, 1):
            f.write(f"\n\n===== CHUNK {i}/{len(chunks)} =====\n\n")
            f.write(ch)
    print(f"  Chunks: {len(chunks)} | Saved:", chunks_file)

    # 4) Summarize each chunk
    print("[4/5] Summarizing chunks with Gemini ...")
    chunk_summaries = []
    for i, ch in enumerate(chunks, 1):
        print(f"   - chunk {i}/{len(chunks)} ...", end="", flush=True)
        try:
            s = summarize_chunk(model, ch, section=f"chunk-{i}", pages="NA",
                                temperature=0.25, max_tokens=512)
        except Exception as e:
            s = f"(요약 실패: {e})"
        chunk_summaries.append(s)
        print(" done")

    chunk_sum_file = outdir / f"{stem}.chunk_summaries.txt"
    chunk_sum_file.write_text("\n\n---\n\n".join(chunk_summaries), encoding="utf-8")
    print("  Saved:", chunk_sum_file)

    # 5) Combine into final brief
    print("[5/5] Composing final research brief ...")
    try:
        final = combine_summaries(model, chunk_summaries,
                                  temperature=0.25, max_tokens=768)
    except Exception as e:
        final = f"(최종 요약 실패: {e})"
    final_file = outdir / f"{stem}.summary.txt"
    final_file.write_text(final, encoding="utf-8")
    print("  Saved:", final_file)

    print("\nDone ✅")
    print("Files:")
    print(" -", raw_file)
    print(" -", clean_file)
    print(" -", chunks_file)
    print(" -", chunk_sum_file)
    print(" -", final_file)

if __name__ == "__main__":
    main()