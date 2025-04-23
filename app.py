import streamlit as st
import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Set Streamlit page config
st.set_page_config(
    page_title="Chatkick",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    body {
        background-color: #121212 !important;
        color: white !important;
    }
    [data-testid="stSidebar"] {
        background-color: #1e1e1e !important;
    }
    .chat-container {
        max-height: 70vh;
        overflow-y: auto;
        padding-bottom: 20px;
    }
    .chat-bubble {
        background-color: #4a4a4a;
        color: white;
        padding: 12px;
        border-radius: 12px;
        margin-bottom: 8px;
        max-width: 80%;
    }
    .user-bubble {
        margin-left: auto;
        background-color: #3a3a3a;
    }
    .ai-bubble {
        margin-right: auto;
        background-color: #2b2b2b;
    }
    .chat-input-container {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 80%;
        max-width: 800px;
        background: #2b2b2b;
        padding: 10px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    .stTextInput>div>div>input {
        color: white !important;
        background-color: #2b2b2b !important;
    }
    .stButton>button {
        border: 1px solid #4a4a4a;
        color: white !important;
        background-color: #2b2b2b !important;
    }
    .stButton>button:hover {
        border: 1px solid #5a5a5a;
        background-color: #3a3a3a !important;
    }
    </style>
""", unsafe_allow_html=True)

# Session state setup
if "messages" not in st.session_state:
    st.session_state.messages = []
if "audio_file" not in st.session_state:
    st.session_state.audio_file = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Gemini response generation
def generate_text(userinput):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(userinput)
        return response.text.replace("*", "")
    except Exception as e:
        st.error(f"❌ Gemini API Error: {e}")
        return None

# ElevenLabs Text-to-Speech
def generate_voice(response_text, voice_id):
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": ELEVENLABS_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "text": response_text,
            "voice_settings": {
                "stability": 0.75,
                "similarity_boost": 0.85
            }
        }
        r = requests.post(url, headers=headers, json=data)
        if r.status_code == 200:
            audio_path = Path("audiofile.mp3")
            with open(audio_path, "wb") as f:
                f.write(r.content)
            return audio_path
        else:
            st.error(f"❌ ElevenLabs Error: {r.status_code} - {r.text}")
            return None
    except Exception as e:
        st.error(f"❌ ElevenLabs Exception: {e}")
        return None

# Sidebar
with st.sidebar:
    st.title("Chatkick")
    st.markdown("---")

    st.subheader("🎙️ Voice Options")
    voice_options = {
        "Rachel (Default)": "EXAVITQu4vr4xnSDxMaL",
        "Domi": "AZnzlk1XvdvUeBnXmlld",
        "Bella": "EXAVITQu4vr4xnSDxMaL",
        "Antoni": "ErXwobaYiN019PkySvjV",
        "Elli": "MF3mGyEYCl7XYWbV9V6O"
    }
    selected_voice = st.selectbox("Select voice:", list(voice_options.keys()))

    st.markdown("---")
    st.subheader("Chat History")

    if st.button("New Chat", use_container_width=True):
        if st.session_state.messages:
            preview = st.session_state.messages[0]["content"][:50]
            st.session_state.chat_history.append({
                "title": preview,
                "messages": st.session_state.messages.copy()
            })
        st.session_state.messages = []
        st.session_state.audio_file = None

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []

    for i, chat in enumerate(st.session_state.chat_history):
        if st.button(f"💬 {chat['title']}", key=f"chat_{i}", use_container_width=True):
            st.session_state.messages = chat["messages"].copy()

# Main area
st.title("🤖 CHAT KICK...")

with st.container():
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for msg in st.session_state.messages:
        bubble_class = "user-bubble" if msg["role"] == "user" else "ai-bubble"
        emoji = "🧑" if msg["role"] == "user" else "🤖"
        st.markdown(
            f'<div class="chat-bubble {bubble_class}">{emoji} {msg["content"]}</div>',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

# Generate voice for last AI response
if st.session_state.messages and st.session_state.messages[-1]["role"] == "ai":
    if st.button("🔊 Generate Voice"):
        voice_id = voice_options[selected_voice]
        ai_text = st.session_state.messages[-1]["content"]
        with st.spinner("Generating voice..."):
            audio_path = generate_voice(ai_text, voice_id)
            if audio_path:
                st.session_state.audio_file = audio_path
                st.rerun()

# Play audio
if st.session_state.audio_file:
    st.audio(str(st.session_state.audio_file))

# Chat input form fixed at bottom
st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
with st.form("chat_form", clear_on_submit=True):
    col1, col2 = st.columns([6, 1])
    with col1:
        user_input = st.text_input("Message", label_visibility="collapsed", placeholder="Ask me anything...")
    with col2:
        submitted = st.form_submit_button("➤")

if submitted and user_input:
    st.session_state.audio_file = None  # Clear old audio
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Thinking..."):
        ai_reply = generate_text(user_input)
        if ai_reply:
            st.session_state.messages.append({"role": "ai", "content": ai_reply})
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
