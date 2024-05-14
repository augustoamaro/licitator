import streamlit as st
from PyPDF2 import PdfReader
import requests


def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


def ask_chatgpt(question, context):
    api_key = st.secrets["openai"]["openai_key"]
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }
    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Context: {context}\n\nPergunta: {question}"}
        ]
    }
    response = requests.post(
        'https://api.openai.com/v1/chat/completions', headers=headers, json=data)

    if response.status_code == 200:
        response_json = response.json()
        if 'choices' in response_json and len(response_json['choices']) > 0:
            return response_json['choices'][0]['message']['content']
        else:
            return "Nenhuma resposta válida foi retornada pela API."
    else:
        return f"Erro ao chamar a API: {response.status_code} - {response.text}"


st.title("Assistente de PDFs")
st.write("Faça upload de PDFs e faça perguntas sobre o conteúdo.")


uploaded_files = st.file_uploader(
    "Upload de PDFs", type=["pdf"], accept_multiple_files=True)

context = ""

if uploaded_files:
    for uploaded_file in uploaded_files:
        text = extract_text_from_pdf(uploaded_file)
        context += text

if "messages" not in st.session_state:
    st.session_state.messages = []


def send_message():
    user_message = st.session_state.user_input
    st.session_state.messages.append({"role": "user", "content": user_message})
    response = ask_chatgpt(user_message, context)
    st.session_state.messages.append(
        {"role": "assistant", "content": response})
    st.session_state.user_input = ""


for message in st.session_state.messages:
    if message["role"] == "user":
        st.write(f"**Usuário:** {message['content']}")
    else:
        st.write(f"**Assistente:** {message['content']}")

st.text_input("Digite sua pergunta:", key="user_input", on_change=send_message)
