# 03-1-2-2 (Multi-turn, improved)
from dotenv import load_dotenv
import google.generativeai as genai
import os, sys, time, argparse
from typing import Optional

def safe_text(resp) -> str:
    # 후보/파츠까지 넓게 커버
    if getattr(resp, "text", None):
        return (resp.text or "").strip()
    cand = getattr(resp, "candidates", None)
    if cand:
        content = getattr(cand[0], "content", None)
        parts = getattr(content, "parts", None) if content else None
        if parts:
            first = parts[0]
            txt = getattr(first, "text", None)
            if txt is not None:
                return txt.strip()
            return str(first).strip()
    return "(응답을 파싱하지 못했어요)"

def build_model(model_name: str, system_instruction: Optional[str]) -> genai.GenerativeModel:
    return genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_instruction or "You are a helpful assistant."
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gemini-2.5-pro", help="예: gemini-2.5-pro / gemini-2.5-flash")
    parser.add_argument("--temp", type=float, default=0.7)
    parser.add_argument("--persona", default="너는 말하는 감자야. 감자처럼 답변해줘")
    parser.add_argument("--stream", action="store_true", help="스트리밍 출력")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[Error] GEMINI_API_KEY가 없습니다. .env에 넣거나 세션에 설정하세요.", file=sys.stderr)
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = build_model(args.model, args.persona)

    # 멀티턴 세션 시작(히스토리 사전 주입 가능)
    chat = model.start_chat(history=[])

    print("Type 'exit' to quit.  /reset 대화 초기화  /sys {지시문} 시스템 인스트럭션 교체  /model {모델명} 모델 교체")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue
        low = user_input.lower()
        if low == "exit":
            break

        # 런타임 제어 명령
        if low.startswith("/reset"):
            chat = model.start_chat(history=[])
            print("Gemini: 대화를 새로 시작할게요!")
            continue
        if low.startswith("/sys"):
            # /sys 뒤의 내용으로 persona 교체
            new_sys = user_input[4:].strip() or args.persona
            model = build_model(args.model, new_sys)
            # 대화는 유지하되, 새 모델 인스트럭션으로 재시작 (원하면 히스토리 이관 가능)
            chat = model.start_chat(history=[])
            print("Gemini: 시스템 인스트럭션을 갱신했어요.")
            continue
        if low.startswith("/model"):
            new_model = user_input[6:].strip() or args.model
            args.model = new_model
            model = build_model(args.model, args.persona)
            chat = model.start_chat(history=[])
            print(f"Gemini: 모델을 '{args.model}'로 바꿨어요.")
            continue

        try:
            gen_cfg = {"temperature": args.temp}
            if args.stream:
                # 스트리밍 모드
                stream = chat.send_message(user_input, generation_config=gen_cfg, stream=True)
                print("Gemini: ", end="", flush=True)
                acc = []
                for chunk in stream:
                    txt = safe_text(chunk)
                    if txt:
                        acc.append(txt)
                        print(txt, end="", flush=True)
                print()
            else:
                resp = chat.send_message(user_input, generation_config=gen_cfg)
                print("Gemini:", safe_text(resp))
        except Exception as e:
            # 간단한 재시도 백오프
            msg = str(e)
            if "429" in msg or "rate" in msg.lower():
                print("[Warn] Rate limit 감지: 1.5초 후 재시도…", file=sys.stderr)
                time.sleep(1.5)
                try:
                    resp = chat.send_message(user_input, generation_config=gen_cfg)
                    print("Gemini:", safe_text(resp))
                except Exception as e2:
                    print(f"[Error] 재시도 실패: {e2}", file=sys.stderr)
            else:
                print(f"[Error] {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
