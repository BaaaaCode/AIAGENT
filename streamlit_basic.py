import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

st.set_page_config(page_title="Gemini Chat", page_icon="🤖", layout="centered")
st.title("🤖 Gemini Chat (Streamlit)")

with st.sidebar:
    st.header("⚙️ Settings")
    model_name = st.selectbox(
        "Model",
        options=["gemini-1.5-pro", "gemini-1.5-flash"],
        index=0,
        help="flash는 더 빠르고 저렴, pro는 품질 우수"
    )
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.05)
    max_output_tokens = st.slider(
        "Max output tokens", min_value=64, max_value=1024, value=256, step=32,
        help="모델이 한 번에 생성할 최대 토큰 수(응답 길이 상한)."
    )
    sys_inst_default = (
        "너는 유치원생이야. 유치원생처럼 1~2문장으로 쉽고 귀엽게 답해줘. "
        "불확실하면 모른다고 말해줘."
    )
    system_instruction = st.text_area("System instruction", value=sys_inst_default, height=100)
    reset = st.button("🔄 Reset chat")

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("환경 변수 GEMINI_API_KEY가 없습니다. .env 또는 st.secrets에 키를 설정하세요.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel(model_name=model_name, system_instruction=system_instruction)

if "messages" not in st.session_state or reset:
    st.session_state.messages = [{"role": "assistant", "content": "안녕! 채팅을 시작해볼까? 👇"}]

def to_gemini_history(messages):
    hist = []
    for m in messages:
        role = "model" if m["role"] == "assistant" else "user"
        hist.append({"role": role, "parts": [m["content"]]})
    return hist

def stream_gemini_text(resp_stream, placeholder):
    full = ""
    for chunk in resp_stream:
        if getattr(chunk, "text", None):
            full += chunk.text
            placeholder.markdown(full + "▌")
    placeholder.markdown(full.strip())
    return full.strip()

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

user_text = st.chat_input("무엇이 궁금해?")

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        history = to_gemini_history(st.session_state.messages[:-1])
        chat = model.start_chat(history=history)

        try:
            resp_stream = chat.send_message(
                user_text,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,  # ← 적용!
                },
                stream=True,
            )
            reply = stream_gemini_text(resp_stream, placeholder)
        except Exception as e:
            reply = f"죄송해요, 오류가 발생했어요: {e}"
            placeholder.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
