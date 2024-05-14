import streamlit as st
from PyPDF2 import PdfReader
import requests
import google.generativeai as genai

# Configurar a API do Google Generative AI
google_api_key = st.secrets["gemini"]["google_api_key"]
genai.configure(api_key=google_api_key)

# Função para extrair texto de um PDF


def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


def ask_google_ai(question, context):
    generation_config = {
        "candidate_count": 1,
        "temperature": 0.5,
    }
    prompt = f"Contexto: {context}\n\nPergunta: {question}"
    response = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest", generation_config=generation_config)

    if response and 'candidates' in response and len(response['candidates']) > 0:
        return response['candidates'][0]['output']
    else:
        return "Nenhuma resposta válida foi retornada pela API."


# Interface do Streamlit
st.title("Assistente de PDFs")
st.write("Faça upload de PDFs e faça perguntas sobre o conteúdo.")

# Upload de PDFs
uploaded_files = st.file_uploader(
    "Upload de PDFs", type=["pdf"], accept_multiple_files=True)

context = ""

if uploaded_files:
    for uploaded_file in uploaded_files:
        text = extract_text_from_pdf(uploaded_file)
        context += text

if "messages" not in st.session_state:
    st.session_state.messages = []

# Função para enviar mensagem


def send_message():
    user_message = st.session_state.user_input
    st.session_state.messages.append({"role": "user", "content": user_message})

    with st.spinner("O assistente está pensando..."):
        response = ask_google_ai(user_message, context)

    st.session_state.messages.append(
        {"role": "assistant", "content": response})
    st.session_state.user_input = ""


# Exibir mensagens
for message in st.session_state.messages:
    if message["role"] == "user":
        st.write(f"**Usuário:** {message['content']}")
    else:
        st.write(f"**Assistente:** {message['content']}")

# Campo de entrada de mensagem
st.text_input("Digite sua pergunta:", key="user_input", on_change=send_message)
